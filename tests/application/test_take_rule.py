"""The take's refusal rule on the snapshots' changes: what it leaves out, takes and restores."""

from pathlib import Path

import pytest

from factory.adapters.fake_snapshots import FakeSnapshots
from factory.application.boundaries import Boundaries
from factory.application.take import TakeService
from human_clone import HumanClone
from take_support import AGENT_TEXT, make_dataset, write_dataset
from undo_support import PATH, start_stage
from work_item_support import checkout_text

MOUNTED = "checkout"


@pytest.mark.parametrize(
    ("write_paths", "path", "outcome"),
    [
        pytest.param(["*"], ".claude/settings.json", "left", id="claude-folder"),
        pytest.param(["*"], "src/.claude/skills/x/SKILL.md", "left", id="nested-claude-folder"),
        pytest.param(
            ["*"],
            "factory/features/F0001-example/in-progress/F0001-S0002-other.md",
            "left",
            id="other-in-progress-file",
        ),
        pytest.param(["*"], "src/.claudex/notes.md", "taken", id="claude-lookalike"),
        pytest.param(["tests/*"], "src/b.py", "left", id="outside-the-write-paths"),
        pytest.param(["tests/*"], "tests/test_x.py", "taken", id="inside-the-write-paths"),
        pytest.param(["*"], PATH, "restored", id="work-item"),
    ],
)
def test_the_take_leaves_out_what_the_rule_refuses_and_restores_the_work_item(
    boundaries: Boundaries,
    human: HumanClone,
    tmp_path: Path,
    *,
    write_paths: list[str],
    path: str,
    outcome: str,
) -> None:
    start = start_stage(boundaries, human, write_paths=write_paths)
    snapshots = FakeSnapshots(make_dataset(boundaries, tmp_path), tmp_path / "base")
    snapshots.advance()
    before = checkout_text(boundaries, path)
    at_start = boundaries.git.show_file(start.commit, PATH)
    assert at_start is not None
    baseline = boundaries.work_item_reader.parse(at_start)
    if outcome == "restored":
        target = snapshots.mount_point / MOUNTED / PATH
        edited = target.read_text(encoding="utf-8").replace("Original.", "Changed by the agent.")
        assert "stage: intake" in edited
        target.write_text(edited.replace("stage: intake", "stage: done"), encoding="utf-8")
    else:
        write_dataset(snapshots.mount_point, {f"{MOUNTED}/{path}": AGENT_TEXT})

    report = TakeService(boundaries, snapshots.mount_point).take(
        start, PATH, snapshots.changed_paths()
    )

    if outcome == "left":
        assert report.left == [path]
        assert checkout_text(boundaries, path) == before
    elif outcome == "taken":
        assert report.left == []
        assert checkout_text(boundaries, path) == AGENT_TEXT
    else:
        assert report.left == []
        assert report.restored_work_item is True
        host = boundaries.work_item_reader.read(boundaries.checkout / PATH)
        assert host.state == baseline.state
        assert host.body == baseline.body.replace("Original.", "Changed by the agent.")
