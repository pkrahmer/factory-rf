"""The rule on write paths that every shipped agent carries explains what a refused write is."""

import pytest

from factory.domain.sections import section_text
from shipped_agents import SHIPPED_NAMES, agent_body

_WRITE_PATHS_RULE = (
    "R14. The pipeline's own files — `factory/pipeline.yml`, `factory/story-form.md`, every "
    "feature's `feature.md`, `backlog/`, `done/` and `.claude/` — change only with the human's "
    "commit or on their explicit instruction. You write only within your write paths in the "
    "pipeline definition (`{work_item}` there is your own work item, outside its front matter and "
    "journal), nothing else: the kernel refuses every other write, by any tool and any command you "
    "run, and the factory undoes any other write after the stage. A refused write fails with "
    "`Permission denied` (`EACCES`, `PermissionError: [Errno 13]`, `cannot create ...: Permission "
    "denied`): that is the write guard, not a fault of the machine; never retry it by another "
    "route, and when the work needs that path, end with `question` and name it. Make temporary "
    "files only in `$TMPDIR` (`mktemp`, `tempfile`), the run's own folder, which the factory "
    "removes after the run; `/tmp` itself is refused."
)

_OLD_ENDING = (
    "a hook refuses an edit outside the write paths, and the factory undoes any other write "
    "after the stage."
)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_rules_hold_the_write_paths_rule_as_one_line(name: str) -> None:
    rules = section_text(agent_body(name), "Rules") or ""

    assert _WRITE_PATHS_RULE in rules.splitlines()


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_old_ending_of_the_write_paths_rule_is_gone(name: str) -> None:
    assert _OLD_ENDING not in agent_body(name)


@pytest.mark.parametrize("name", SHIPPED_NAMES)
def test_write_paths_rule_appears_once(name: str) -> None:
    lines = [line for line in agent_body(name).splitlines() if line.startswith("R14. ")]

    assert len(lines) == 1
