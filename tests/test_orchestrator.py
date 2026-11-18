import pytest
from ppt_engine.models import PageStatus
from ppt_engine.orchestrator import Orchestrator


def test_page_lifecycle_and_persistence(tmp_path):
    state_file = tmp_path / "project.json"
    flow = Orchestrator(state_file)
    flow.add_page("s1")
    for state in [PageStatus.CONTENT_APPROVED, PageStatus.DESIGN_APPROVED,
                  PageStatus.RENDERED, PageStatus.QA_PASSED, PageStatus.DELIVERED]:
        flow.transition("s1", state)
    reloaded = Orchestrator(state_file)
    assert reloaded.state.pages["s1"].status == PageStatus.DELIVERED


def test_illegal_transition_rejected(tmp_path):
    flow = Orchestrator(tmp_path / "state.json")
    flow.add_page("s1")
    with pytest.raises(ValueError):
        flow.transition("s1", PageStatus.RENDERED)
