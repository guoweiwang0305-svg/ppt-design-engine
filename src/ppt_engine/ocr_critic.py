"""Optional Tesseract OCR adapter for rendered-slide text verification.

Tesseract is an optional system executable. The core engine remains usable without
it; when unavailable, the report says so rather than pretending OCR was performed.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import Field
from .models import DesignIR, StrictModel
from .ledger import DataLedger


class OCRWord(StrictModel):
    text: str
    confidence: float
    box: tuple[int, int, int, int]


class OCRRegionResult(StrictModel):
    node_id: str
    expected_text: str
    recognized_text: str
    token_coverage: float
    words_found: int
    words_outside_region: int
    status: Literal["matched", "partial", "missing", "outside_region"]


class OCRCritique(StrictModel):
    available: bool
    engine: str = "tesseract"
    image_path: str
    regions: list[OCRRegionResult] = Field(default_factory=list)
    findings: list[dict] = Field(default_factory=list)
    limitation: str = "OCR can misread stylized fonts, small text, Chinese text without language packs, charts and decorative typography."


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[\w%.,+-]+", text, flags=re.UNICODE) if token.strip()]


def _coverage(expected: str, actual: str) -> float:
    wanted = _tokens(expected)
    if not wanted:
        return 1.0
    found = set(_tokens(actual))
    return sum(1 for token in wanted if token in found) / len(wanted)


def critique_rendered_text(ir: DesignIR, image_path: str | Path,
                           language: str = "eng", ledger: DataLedger | None = None) -> OCRCritique:
    path = Path(image_path)
    executable = shutil.which("tesseract")
    if not executable:
        return OCRCritique(available=False, image_path=str(path),
            findings=[{"code":"ocr_unavailable","severity":"info","node_ids":[],
                "diagnosis":"Tesseract executable is not installed; rendered wording was not OCR-verified.",
                "recommendation":"Install Tesseract and the required language packs to enable optional OCR checks."}])
    if not path.exists():
        raise FileNotFoundError(path)
    result = subprocess.run(
        [executable, str(path), "stdout", "-l", language, "tsv"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return OCRCritique(available=False,image_path=str(path),
            findings=[{"code":"ocr_failed","severity":"minor","node_ids":[],
                "diagnosis":(result.stderr or "Tesseract OCR failed.")[:500],
                "recommendation":"Check Tesseract language data and rerun OCR."}])
    lines=result.stdout.splitlines()
    words=[]
    for line in lines[1:]:
        cols=line.split("\t")
        if len(cols)<12 or not cols[11].strip():
            continue
        try:
            confidence=float(cols[10])
            x,y,w,h=(int(cols[i]) for i in (6,7,8,9))
        except (ValueError,IndexError):
            continue
        if confidence >= 15:
            words.append(OCRWord(text=cols[11].strip(),confidence=confidence,box=(x,y,x+w,y+h)))
    from PIL import Image
    image=Image.open(path)
    sx,sy=image.width/ir.canvas.width,image.height/ir.canvas.height
    regions=[]
    findings=[]
    for node in ir.nodes:
        if node.geometry is None or node.visual_type!="text":
            continue
        expected_text=node.text
        if node.data_ref:
            if ledger is None:
                findings.append({"code":"ocr_metric_skipped","severity":"info","node_ids":[node.id],
                    "diagnosis":"Metric text is rendered from DataLedger; OCR comparison skipped because no ledger was supplied.",
                    "recommendation":"Pass the same DataLedger used for rendering to enable metric text verification."})
                continue
            entry=ledger.resolve(node.data_ref)
            expected_text=f"{entry.value} {entry.unit}".strip()
        if not expected_text.strip():
            continue
        g=node.geometry
        box=(round(g.x*sx),round(g.y*sy),round((g.x+g.width)*sx),round((g.y+g.height)*sy))
        inside=[]
        outside=0
        for word in words:
            x1,y1,x2,y2=word.box
            center=((x1+x2)/2,(y1+y2)/2)
            if box[0] <= center[0] <= box[2] and box[1] <= center[1] <= box[3]:
                inside.append(word.text)
            elif x1 < box[2] and x2 > box[0] and y1 < box[3] and y2 > box[1]:
                outside += 1
        recognized=" ".join(inside)
        coverage=_coverage(expected_text,recognized)
        status="matched" if coverage>=0.8 else ("partial" if coverage>0 else "missing")
        if outside:
            status="outside_region"
        regions.append(OCRRegionResult(node_id=node.id,expected_text=expected_text,
            recognized_text=recognized,token_coverage=round(coverage,3),
            words_found=len(inside),words_outside_region=outside,status=status))
        if status=="missing":
            findings.append({"code":"ocr_expected_text_missing","severity":"major","node_ids":[node.id],
                "diagnosis":"No expected words were recognized inside this DesignIR text region.",
                "recommendation":"Check font embedding, text color, rendering, language pack and clipping."})
        elif status=="partial":
            findings.append({"code":"ocr_text_partial","severity":"minor","node_ids":[node.id],
                "diagnosis":f"Only {coverage:.0%} of expected tokens were recognized in this text region.",
                "recommendation":"Inspect the rendered text manually; OCR may fail on stylized or small type."})
        if outside:
            findings.append({"code":"ocr_words_cross_region","severity":"major","node_ids":[node.id],
                "diagnosis":f"{outside} OCR word boxes overlap the region boundary.",
                "recommendation":"Check text-box dimensions and adjacent content for overflow."})
    return OCRCritique(available=True,image_path=str(path),regions=regions,findings=findings)
