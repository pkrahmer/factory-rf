"""A whole stage names what the take left out in the entry's closing sentence."""

from pathlib import Path

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.domain.journal import entry_text
from factory.domain.paths import cost_records_path
from human_clone import HumanClone
from stage_run_support import PATH, completed, open_story, pushed, run_stage
from take_support import AGENT_TEXT

KEPT = "tests/test_new.py"
FORBIDDEN = "src/forbidden.py"
KEPT_TEXT = "def test_new() -> None:\n    assert True\n"
FORBIDDEN_TEXT = "FORBIDDEN = 1\n"
SIDECAR = cost_records_path(PATH)


def test_a_stage_names_the_left_out_paths_and_commits_only_the_taken_ones(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    remote: Path,
) -> None:
    open_story(boundaries, human, agent_home)
    writes = {KEPT: KEPT_TEXT, FORBIDDEN: FORBIDDEN_TEXT, SIDECAR: AGENT_TEXT}
    agent_runtime.queue(ScriptedRun(writes=writes, result=completed("doing")))

    report = run_stage(boundaries)

    document = pushed(boundaries, remote)
    assert document.state is not None
    [record] = [record for record in document.state.journal if record.speaker == "tester"]
    text = entry_text(document, record.number)
    # The checks' lines follow the agent's entry as a paragraph of their own.
    *_, closing, checks = text.split("\n\n")
    assert closing == "The factory left out changes outside the write paths: src/forbidden.py."
    assert checks.startswith("`lint`: ")
    assert ".costs.jsonl" not in text
    git = boundaries.git
    assert git.show_file(report.commit, KEPT) == KEPT_TEXT
    assert git.show_file(report.commit, FORBIDDEN) is None
    sidecar = git.show_file(report.commit, SIDECAR)
    assert sidecar is not None
    assert AGENT_TEXT not in sidecar
    [cost_record] = boundaries.cost_reader.parse(sidecar)
    assert cost_record.status == "completed"
