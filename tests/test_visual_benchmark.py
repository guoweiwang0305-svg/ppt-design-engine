from ppt_engine.visual_benchmark import VisualBenchmarkCase, score_visual_benchmark


def test_benchmark_reports_precision_recall_and_false_positives():
    cases=[
        VisualBenchmarkCase(case_id="cover",slide_type="cover",
            expected_issue_codes=["rendered_text_near_region_edge"],
            observed_issue_codes=["rendered_text_near_region_edge","visual_mass_off_center"]),
        VisualBenchmarkCase(case_id="chart",slide_type="chart",
            expected_issue_codes=["rendered_region_low_contrast","ocr_text_partial"],
            observed_issue_codes=["rendered_region_low_contrast"]),
    ]
    score=score_visual_benchmark(cases)
    assert score.true_positive==2
    assert score.false_positive==1
    assert score.false_negative==1
    assert score.precision==round(2/3,4)
    assert score.recall==round(2/3,4)
    assert score.by_slide_type["chart"]["recall"]==0.5
