"""A stage's checks run on a checkout without the ignored paths its agent left."""

from pathlib import Path

import pytest

from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.application.boundaries import Boundaries
from factory.domain.work_item import WorkItemState
from human_clone import HumanClone
from stage_run_support import CREATED, completed, open_story, run_stage

STANDIN = "standin\n"


def _makefile(path: str) -> str:
    return f".PHONY: check\n\ncheck:\n\ttest ! -e {path}\n"


@pytest.mark.parametrize(
    ("path", "green"),
    [
        pytest.param(".venv/standin.pth", True, id="ignored"),
        pytest.param("src/standin.txt", False, id="in-write-path"),
    ],
)
def test_the_checks_do_not_see_what_the_agent_hid(
    boundaries: Boundaries,
    *,
    human: HumanClone,
    agent_home: Path,
    agent_runtime: FakeAgentRuntime,
    path: str,
    green: bool,
) -> None:
    open_story(
        boundaries,
        human,
        agent_home,
        makefile=_makefile(path),
        main_files={".gitignore": ".venv/\n"},
        state=WorkItemState(stage="doing", journal=[CREATED]),
        roles=("coder",),
    )
    agent_runtime.queue(ScriptedRun(writes={path: STANDIN}, result=completed("review")))

    report = run_stage(boundaries)

    if green:
        assert report.stall is None
        assert report.rule == 6
        assert boundaries.git.show_file(report.commit, path) is None
    else:
        assert report.stall is not None
        assert report.stall.reason == "check_red"
