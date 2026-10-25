"""The machine's checks: every item runs and is reported, whatever the others found."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.boundaries import Boundaries
from factory.application.preflight import MachineChecks, tool_item
from factory.domain.preflight import PreflightItem
from factory.domain.settings import InstanceSettings

PINNED = "2.1.289"
FIVE = [
    "tool:git",
    "tool:uv",
    "hosting-service",
    "agents",
    "agent-runtime-version",
]
ALL_TOOLS = {
    "git": "/usr/bin/git",
    "uv": "/usr/local/bin/uv",
}


class DictionaryWhich:
    """A `which` that answers from a dictionary and remembers what it was asked."""

    def __init__(self, paths: dict[str, str]) -> None:
        self.paths = paths
        self.asked: list[str] = []

    def __call__(self, name: str) -> str | None:
        self.asked.append(name)
        return self.paths.get(name)


def _install_agents(directory: Path) -> Path:
    (directory / "agents").mkdir(parents=True)
    (directory / "agents" / "intake.md").write_text(
        "---\nname: intake\n---\nRead the story.\n", encoding="utf-8"
    )
    return directory


def _settings(agent_home: Path, **fields: object) -> InstanceSettings:
    return InstanceSettings.model_validate(
        {
            "repository_url": "/srv/project.git",
            "instance": "factory-1",
            "agent_home": agent_home,
            "pinned_agent_version": PINNED,
            **fields,
        }
    )


@pytest.fixture
def installed(tmp_path: Path) -> Path:
    """Return an agent home other than the user's home that holds `agents/intake.md`."""
    return _install_agents(tmp_path / "installed-agents")


@pytest.fixture
def ready(boundaries: Boundaries, installed: Path) -> Boundaries:
    """Return boundaries whose agents are installed and whose runtime reports the pin."""
    return replace(
        boundaries,
        agent_runtime=FakeAgentRuntime(version=PINNED),
        agent_definitions=FrontmatterAgentDefinitionReader(installed),
    )


def _item(checks: MachineChecks, name: str) -> PreflightItem:
    return next(item for item in checks.run().items if item.name == name)


def test_a_tool_on_the_path_passes() -> None:
    item = tool_item("git", DictionaryWhich(ALL_TOOLS))

    assert item == PreflightItem(name="tool:git", passed=True, detail="")


def test_a_tool_missing_from_the_path_fails_and_says_to_add_it_to_the_image() -> None:
    item = tool_item("make", DictionaryWhich({}))

    assert item.name == "tool:make"
    assert not item.passed
    assert item.detail == "make is not on the PATH; add it to the image"


def test_a_ready_machine_passes_every_item_in_order(ready: Boundaries, installed: Path) -> None:
    report = MachineChecks(ready, _settings(installed), DictionaryWhich(ALL_TOOLS)).run()

    assert [item.name for item in report.items] == FIVE
    assert report.passed


def test_every_item_is_reported_whatever_the_others_found(
    ready: Boundaries, installed: Path, hosting: FakeHostingService
) -> None:
    hosting.fail_next("find_open_pull_request")
    which = DictionaryWhich({})
    boundaries = replace(ready, agent_runtime=FakeAgentRuntime(version="2.1.290"))

    report = MachineChecks(boundaries, _settings(installed), which).run()

    assert [item.name for item in report.items] == FIVE
    assert [item.name for item in report.failed()] == [
        "tool:git",
        "tool:uv",
        "hosting-service",
        "agent-runtime-version",
    ]
    assert not report.passed


@pytest.mark.parametrize("fails", [False, True], ids=["answers", "fails"])
def test_the_hosting_service_item_reports_a_failed_call(
    ready: Boundaries, installed: Path, hosting: FakeHostingService, fails: bool
) -> None:
    if fails:
        hosting.fail_next("find_open_pull_request")

    item = _item(
        MachineChecks(ready, _settings(installed), DictionaryWhich(ALL_TOOLS)), "hosting-service"
    )

    assert item.passed is not fails
    if fails:
        assert item.detail == (
            "the hosting service failed find_open_pull_request: injected failure; "
            "check the token and the network"
        )


def test_the_agents_item_finds_the_agents_where_the_agent_home_points(
    ready: Boundaries, installed: Path
) -> None:
    item = _item(MachineChecks(ready, _settings(installed), DictionaryWhich(ALL_TOOLS)), "agents")

    assert item.passed


@pytest.mark.parametrize("creates_directory", [True, False], ids=["no-agent-file", "missing"])
def test_the_agents_item_fails_naming_the_agent_home_without_agents(
    ready: Boundaries, tmp_path: Path, creates_directory: bool
) -> None:
    empty = tmp_path / "empty-agent-home"
    if creates_directory:
        (empty / "agents").mkdir(parents=True)
    boundaries = replace(ready, agent_definitions=FrontmatterAgentDefinitionReader(empty))

    item = _item(MachineChecks(boundaries, _settings(empty), DictionaryWhich(ALL_TOOLS)), "agents")

    assert not item.passed
    assert str(empty) in item.detail


def test_the_version_item_passes_when_the_first_word_is_the_pinned_version(
    ready: Boundaries, installed: Path
) -> None:
    boundaries = replace(ready, agent_runtime=FakeAgentRuntime(version="2.1.289 (Claude Code)"))

    item = _item(
        MachineChecks(boundaries, _settings(installed), DictionaryWhich(ALL_TOOLS)),
        "agent-runtime-version",
    )

    assert item.passed


def test_the_version_item_fails_with_its_detail_when_the_versions_differ(
    ready: Boundaries, installed: Path
) -> None:
    boundaries = replace(ready, agent_runtime=FakeAgentRuntime(version="2.1.290"))

    item = _item(
        MachineChecks(boundaries, _settings(installed), DictionaryWhich(ALL_TOOLS)),
        "agent-runtime-version",
    )

    assert not item.passed
    assert item.detail == (
        "the agent runtime reports 2.1.290, the image pins 2.1.289; "
        "rebuild the image or change the pinned version"
    )


def test_the_version_item_fails_when_the_image_pins_no_version(
    ready: Boundaries, installed: Path
) -> None:
    settings = _settings(installed, pinned_agent_version=None)

    item = _item(
        MachineChecks(ready, settings, DictionaryWhich(ALL_TOOLS)), "agent-runtime-version"
    )

    assert not item.passed
    assert item.detail == "the image does not pin a version: FACTORY_CLAUDE_VERSION is not set"


def test_the_version_item_fails_with_the_runtime_error_when_the_version_cannot_be_read(
    ready: Boundaries, installed: Path, tmp_path: Path
) -> None:
    runtime = ClaudeCodeRuntime(str(tmp_path / "nowhere" / "claude"), tmp_path / "state")
    boundaries = replace(ready, agent_runtime=runtime)

    item = _item(
        MachineChecks(boundaries, _settings(installed), DictionaryWhich(ALL_TOOLS)),
        "agent-runtime-version",
    )

    assert not item.passed
    assert "cannot start" in item.detail


def test_the_extra_items_run_last_in_order_and_are_reported_with_the_others(
    ready: Boundaries, installed: Path
) -> None:
    failing = PreflightItem(name="probe", passed=False, detail="main is failing")
    extra: list[Callable[[], PreflightItem]] = [
        lambda: PreflightItem(name="stamp", passed=True),
        lambda: failing,
    ]

    report = MachineChecks(ready, _settings(installed), DictionaryWhich(ALL_TOOLS), extra).run()

    assert [item.name for item in report.items] == [*FIVE, "stamp", "probe"]
    assert report.failed() == [failing]
    assert not report.passed


def test_the_items_read_the_settings_given_and_not_those_of_the_boundaries(
    ready: Boundaries, installed: Path
) -> None:
    settings = _settings(installed)
    assert ready.settings != settings

    report = MachineChecks(ready, settings, DictionaryWhich(ALL_TOOLS)).run()

    assert report.failed() == []
