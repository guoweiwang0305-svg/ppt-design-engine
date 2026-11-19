from ppt_engine.repair_validation import compare_repair_reports


def test_repair_is_accepted_only_when_issues_decrease_without_severe_regression():
    before={"findings":[
        {"code":"overflow","severity":"major","node_ids":["a"]},
        {"code":"crowding","severity":"minor","node_ids":["b"]},
    ]}
    after={"findings":[
        {"code":"crowding","severity":"minor","node_ids":["b"]},
    ]}
    result=compare_repair_reports(before,after)
    assert result.accepted
    assert result.improved_issue_codes == ["overflow"]
    assert result.candidate_score < result.baseline_score


def test_repair_rolls_back_on_new_major_issue_even_if_minor_issues_drop():
    before={"findings":[
        {"code":"crowding","severity":"minor","node_ids":["b"]},
    ]}
    after={"findings":[
        {"code":"new_overlap","severity":"major","node_ids":["c"]},
    ]}
    result=compare_repair_reports(before,after)
    assert not result.accepted
    assert "new_overlap" in result.regressed_issue_codes


def test_equal_diagnostic_score_is_not_accepted():
    report={"findings":[{"code":"same","severity":"major","node_ids":["a"]}]}
    result=compare_repair_reports(report,report)
    assert not result.accepted
    assert result.baseline_score == result.candidate_score
