"""The fixture `instance`: a valid instance, its settings, state folder and bare remote."""

from collections.abc import Mapping
from pathlib import Path

import pytest

from factory.hosting.adapters.git_cli import GitCli
from factory.hosting.adapters.instance_fixture import InstanceFixture
from factory.shared.adapters.document_examples import ProcessExampleRunner
from factory.shared.application.document_examples import Fixture
from factory.shared.domain.documents import INSTANCE_FIXTURE, examples
from factory.shared.domain.errors import FixtureError
from factory.shared.domain.settings import (
    INSTANCE_VARIABLE,
    REPOSITORY_URL_VARIABLE,
    SNAPSHOTS_VARIABLE,
    STATE_VARIABLE,
)
from factory.watching.adapters.health_file import HEALTH_FILE_NAME
from support.document_texts import FENCE
from support.git_support import run_git

SETTINGS_FILE = "factory.env"
FIRST_DOCUMENT = "docs/operator-guide/health.md"
SECOND_DOCUMENT = "docs/operator-guide/configure.md"
MARKER = "marker"


class RecordingFixture(Fixture):
    """The instance fixture, with the folders it was prepared in kept in order."""

    def __init__(self, fixture: Fixture) -> None:
        """Prepare through `fixture`."""
        self._fixture = fixture
        self.folders: list[Path] = []

    def prepare(self, folder: Path) -> dict[str, str]:
        """Keep `folder` and prepare the instance in it."""
        self.folders.append(folder)
        return self._fixture.prepare(folder)


def _document(*lines: str) -> str:
    return "\n".join(["# A guide", "", f"{FENCE}console fixture={INSTANCE_FIXTURE}", *lines, FENCE])


def _paths(root: Path) -> set[Path]:
    return set(root.rglob("*"))


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    made = tmp_path / "example"
    made.mkdir()
    return made


@pytest.fixture
def environment(checkout: GitCli, folder: Path) -> dict[str, str]:
    return InstanceFixture(checkout).prepare(folder)


@pytest.mark.parametrize(
    "lines",
    [
        pytest.param(
            ['$ factory-health --state-directory "$FACTORY_STATE"', "healthy"],
            id="healthy",
        ),
        pytest.param(
            [
                f'$ {INSTANCE_VARIABLE}=Factory-1 factory-run; echo "exit $?"',
                f"<time> settings invalid: {INSTANCE_VARIABLE}: is not a name",
                "exit 2",
            ],
            id="a-wrong-instance-name-is-refused",
        ),
    ],
)
def test_the_commands_of_a_block_on_the_instance_print_what_a_valid_instance_prints(
    checkout: GitCli, lines: list[str]
) -> None:
    fixtures: Mapping[str, Fixture] = {INSTANCE_FIXTURE: InstanceFixture(checkout)}

    findings = ProcessExampleRunner().run_document(
        FIRST_DOCUMENT, examples(_document(*lines)).runnable, fixtures
    )

    assert findings == []


def test_the_environment_names_the_instance_docs_with_copied_snapshots_and_folders_inside(
    environment: dict[str, str], folder: Path
) -> None:
    assert environment[INSTANCE_VARIABLE] == "docs"
    assert environment[SNAPSHOTS_VARIABLE] == "copy"
    folders = [Path(value) for value in environment.values() if value.startswith("/")]
    assert folders
    for path in folders:
        assert path.resolve().is_relative_to(folder.resolve()), path


def test_the_state_folder_holds_the_health_file_factory_health_reads(
    environment: dict[str, str],
) -> None:
    assert (Path(environment[STATE_VARIABLE]) / HEALTH_FILE_NAME).is_file()


def test_each_document_gets_a_fresh_instance_in_a_folder_of_its_own(checkout: GitCli) -> None:
    recording = RecordingFixture(InstanceFixture(checkout))
    fixtures: Mapping[str, Fixture] = {INSTANCE_FIXTURE: recording}
    runner = ProcessExampleRunner()
    first = _document(f'$ touch "$FACTORY_STATE/{MARKER}"; echo written', "written")
    second = _document(
        f'$ test -e "$FACTORY_STATE/{MARKER}" && echo present || echo absent', "absent"
    )

    first_findings = runner.run_document(FIRST_DOCUMENT, examples(first).runnable, fixtures)
    second_findings = runner.run_document(SECOND_DOCUMENT, examples(second).runnable, fixtures)

    assert first_findings == []
    assert second_findings == []
    assert len(recording.folders) == 2
    assert recording.folders[0] != recording.folders[1]


def test_the_fixture_creates_no_path_outside_its_folder(
    tmp_path: Path, checkout: GitCli, folder: Path
) -> None:
    before = _paths(tmp_path)

    InstanceFixture(checkout).prepare(folder)

    created = _paths(tmp_path) - before
    assert created
    outside = [path for path in created if not path.is_relative_to(folder)]
    assert outside == []


def test_the_instance_s_remote_is_a_bare_repository_under_the_folder(
    environment: dict[str, str], folder: Path
) -> None:
    remote = Path(environment[REPOSITORY_URL_VARIABLE])

    assert remote.resolve().is_relative_to(folder.resolve())
    assert run_git(remote, "rev-parse", "--is-bare-repository").strip() == "true"


def test_the_settings_file_holds_one_line_for_each_variable_of_the_environment(
    environment: dict[str, str], folder: Path
) -> None:
    lines = (folder / SETTINGS_FILE).read_text(encoding="utf-8").splitlines()

    assert sorted(lines) == sorted(f"{name}={value}" for name, value in environment.items())


def test_the_instance_fixture_outside_a_git_repository_raises_a_fixture_error(
    tmp_path: Path, folder: Path
) -> None:
    outside = tmp_path / "not-a-repository"
    outside.mkdir()

    with pytest.raises(FixtureError):
        InstanceFixture(GitCli(outside)).prepare(folder)
