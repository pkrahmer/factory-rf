"""The process runner of a document's examples: one folder per document, the limit, the env."""

import os
import time
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path

import pytest

from factory.shared.adapters.document_examples import ProcessExampleRunner
from factory.shared.application.document_examples import Fixture
from factory.shared.domain.documents import examples
from factory.shared.domain.errors import FixtureError
from support.document_texts import FENCE

DOCUMENT = "docs/project-guide/shared.md"
FIXTURE_VARIABLE = "EXAMPLE_FIXTURE"
SHORT_LIMIT_SECONDS = 1
# What the stand-in waits is far longer than the bound, so a missed kill fails.
SLEEP_SECONDS = 30
ELAPSED_BOUND_SECONDS = 15


class EmptyFixture(Fixture):
    """A fixture that leaves the folder it is given empty and gives one variable."""

    def prepare(self, folder: Path) -> dict[str, str]:
        """Check the folder is there and give the one variable."""
        assert folder.is_dir()
        return {FIXTURE_VARIABLE: "set"}


class FailingFixture(Fixture):
    """A fixture that cannot build its starting point."""

    def prepare(self, folder: Path) -> dict[str, str]:
        """Refuse, as a fixture whose source is missing does."""
        raise FixtureError(f"nothing to copy into {folder}")


def _block(*lines: str, info: str = "console") -> list[str]:
    return [f"{FENCE}{info}", *lines, FENCE, ""]


def _document(*blocks: list[str]) -> str:
    return "\n".join(["# A guide", "", *(line for block in blocks for line in block)])


@pytest.fixture
def fixtures() -> Mapping[str, Fixture]:
    return {"checkout": EmptyFixture()}


@pytest.fixture
def runner() -> ProcessExampleRunner:
    return ProcessExampleRunner(time_limit=timedelta(seconds=SHORT_LIMIT_SECONDS))


def test_the_blocks_of_one_document_share_a_folder_and_the_next_document_starts_fresh(
    runner: ProcessExampleRunner, fixtures: Mapping[str, Fixture]
) -> None:
    first = _document(
        _block("$ printf 'kept\\n' > note.txt"),
        _block("$ cat note.txt", "kept"),
    )
    second = _document(_block("$ test -e note.txt && echo there || echo gone", "gone"))

    first_findings = runner.run_document(DOCUMENT, examples(first).runnable, fixtures)
    second_findings = runner.run_document("README.md", examples(second).runnable, fixtures)

    assert first_findings == []
    assert second_findings == []


@pytest.mark.parametrize(
    ("expected", "findings"),
    [
        pytest.param(["hi"], [], id="matches"),
        pytest.param(["hello"], [f"{DOCUMENT}:4: the example printed hi"], id="differs"),
        pytest.param(
            ["one", "two"], [f"{DOCUMENT}:4: the example printed hi"], id="first-differing-line"
        ),
        pytest.param(
            ["hi", "more"],
            [f"{DOCUMENT}:4: the example printed nothing more"],
            id="fewer-lines-than-expected",
        ),
    ],
)
def test_a_command_whose_output_differs_gives_one_finding_and_one_that_matches_none(
    runner: ProcessExampleRunner,
    fixtures: Mapping[str, Fixture],
    expected: list[str],
    findings: list[str],
) -> None:
    text = _document(_block("$ echo hi", *expected))

    assert runner.run_document(DOCUMENT, examples(text).runnable, fixtures) == findings


def test_the_output_compared_holds_stderr_too(
    runner: ProcessExampleRunner, fixtures: Mapping[str, Fixture]
) -> None:
    text = _document(_block("$ echo out; echo err >&2", "out", "err"))

    assert runner.run_document(DOCUMENT, examples(text).runnable, fixtures) == []


def test_a_command_past_its_limit_gives_one_finding_and_the_later_blocks_do_not_run(
    runner: ProcessExampleRunner, fixtures: Mapping[str, Fixture]
) -> None:
    text = _document(
        _block(f"$ sleep {SLEEP_SECONDS}"),
        _block("$ echo later", "not what it prints"),
    )
    started = time.monotonic()

    findings = runner.run_document(DOCUMENT, examples(text).runnable, fixtures)

    assert time.monotonic() - started < ELAPSED_BOUND_SECONDS
    assert findings == [f"{DOCUMENT}:4: the example did not end in {SHORT_LIMIT_SECONDS} s"]


def test_a_block_naming_an_unknown_fixture_gives_a_finding(
    runner: ProcessExampleRunner, fixtures: Mapping[str, Fixture]
) -> None:
    text = _document(_block("$ echo hi", "hi", info="console fixture=nowhere"))

    findings = runner.run_document(DOCUMENT, examples(text).runnable, fixtures)

    assert findings == [f"{DOCUMENT}:3: no fixture nowhere"]


def test_the_commands_never_run_in_the_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runner: ProcessExampleRunner,
    fixtures: Mapping[str, Fixture],
) -> None:
    here = tmp_path / "here"
    here.mkdir()
    (here / "marker").write_text("here\n", encoding="utf-8")
    monkeypatch.chdir(here)
    text = _document(
        _block(
            "$ test -e marker && echo inside || echo outside",
            "outside",
            "$ printf 'x\\n' > written.txt",
        )
    )

    findings = runner.run_document(DOCUMENT, examples(text).runnable, fixtures)

    assert findings == []
    assert sorted(entry.name for entry in here.iterdir()) == ["marker"]


def test_env_in_a_block_shows_the_fixed_variables_and_the_fixtures_and_not_the_callers(
    monkeypatch: pytest.MonkeyPatch,
    runner: ProcessExampleRunner,
    fixtures: Mapping[str, Fixture],
) -> None:
    monkeypatch.setenv("FROM_THE_TEST", "leaked")
    home = os.environ.get("HOME", "")
    text = _document(
        _block(
            f'$ env | grep "^{FIXTURE_VARIABLE}="',
            f"{FIXTURE_VARIABLE}=set",
            '$ env | grep "^TZ="',
            "TZ=UTC",
            '$ env | grep "^LANG="',
            "LANG=C.UTF-8",
            '$ env | grep -c "^PATH="',
            "1",
            f'$ env | grep "^HOME=" | grep -v -x -c "HOME={home}"',
            "1",
            "$ env | grep -c FROM_THE_TEST",
            "0",
        )
    )

    assert runner.run_document(DOCUMENT, examples(text).runnable, fixtures) == []


def test_a_fixture_that_cannot_be_prepared_gives_one_finding_and_runs_no_command(
    tmp_path: Path, runner: ProcessExampleRunner
) -> None:
    marker = tmp_path / "ran"
    text = _document(
        _block(f"$ touch {marker}"),
        _block(f"$ touch {marker}", "not what it prints"),
    )

    findings = runner.run_document(
        DOCUMENT, examples(text).runnable, {"checkout": FailingFixture()}
    )

    assert findings == [f"{DOCUMENT}:3: fixture checkout could not be prepared"]
    assert not marker.exists()
