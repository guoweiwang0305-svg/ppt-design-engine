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


def test_pending_expert_labels_are_excluded_from_metrics():
    cases=[
        VisualBenchmarkCase(case_id="reviewed",slide_type="cover",
            expected_issue_codes=["weak_visual_hierarchy"],
            observed_issue_codes=["weak_visual_hierarchy"],review_status="reviewed"),
        VisualBenchmarkCase(case_id="pending",slide_type="chart",
            expected_issue_codes=[],observed_issue_codes=["chart_encoding_unclear"],
            review_status="pending_expert_review"),
    ]
    score=score_visual_benchmark(cases)
    assert score.cases==1
    assert score.pending_cases==1
    assert score.false_positive==0
    assert score.recall==1.0


def test_benchmark_splits_identical_slide_types_by_source_family():
    cases = [
        VisualBenchmarkCase(
            case_id="gcl-cover", source_family="GCL", slide_type="cover",
            expected_issue_codes=["weak_visual_hierarchy"],
            observed_issue_codes=["weak_visual_hierarchy"],
        ),
        VisualBenchmarkCase(
            case_id="aia-cover", source_family="AIA", slide_type="cover",
            expected_issue_codes=["chart_encoding_unclear"],
            observed_issue_codes=[],
        ),
    ]
    score = score_visual_benchmark(cases)
    assert score.by_source_and_slide_type["GCL::cover"]["f1"] == 1.0
    assert score.by_source_and_slide_type["AIA::cover"]["fn"] == 1
