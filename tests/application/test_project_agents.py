"""A project's own agents at `origin/main` first, the installed ones otherwise."""

from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import pytest

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.application.boundaries import Boundaries
from factory.application.project_agents import ProjectAgentDefinitions
from factory.domain.errors import (
    AgentDefinitionError,
    AgentDefinitionInvalid,
    AgentDefinitionMissing,
    GitError,
)
from git_support import AGENT_FILE, COLOURED_AGENT_FILE, install_agents
from human_clone import HumanClone

PROJECT_CODER = "---\nmodel: opus\ntools: [Read]\nbudget_usd: 2\n---\nThe project's coder.\n"
CODER_FILE = "factory/agents/coder.md"
BRANCH = "work-item/F0001-S0001"


@pytest.fixture
def installed(agent_home: Path) -> FrontmatterAgentDefinitionReader:
    """The installed agents `coder` and `tester` in the agent home."""
    install_agents(agent_home, ["coder", "tester"])
    return FrontmatterAgentDefinitionReader(agent_home)


@pytest.fixture
def project(
    boundaries: Boundaries, installed: FrontmatterAgentDefinitionReader
) -> ProjectAgentDefinitions:
    """The project's agents over the test's checkout and the installed agents."""
    return ProjectAgentDefinitions(boundaries.git, installed)


def _push(human: HumanClone, boundaries: Boundaries, files: dict[str, str]) -> None:
    human.push_files("main", files)
    boundaries.git.fetch()


@pytest.mark.parametrize(
    ("files", "model", "tools", "budget", "instructions"),
    [
        pytest.param(
            {CODER_FILE: PROJECT_CODER},
            "opus",
            ["Read"],
            Decimal(2),
            "The project's coder.",
            id="project-file",
        ),
        pytest.param({}, "sonnet", ["Read", "Write"], Decimal(1), "Do the work.", id="none"),
        pytest.param(
            {"factory/agents/tester.md": PROJECT_CODER},
            "sonnet",
            ["Read", "Write"],
            Decimal(1),
            "Do the work.",
            id="other-role-only",
        ),
    ],
)
def test_the_project_file_replaces_the_installed_agent_of_its_role(
    project: ProjectAgentDefinitions,
    boundaries: Boundaries,
    human: HumanClone,
    *,
    files: dict[str, str],
    model: str,
    tools: list[str],
    budget: Decimal,
    instructions: str,
) -> None:
    if files:
        _push(human, boundaries, files)

    agent = project.read("coder")

    assert agent.name == "coder"
    assert (agent.model, agent.tools, agent.budget_usd) == (model, tools, budget)
    assert agent.instructions == instructions


@pytest.mark.parametrize("ref", ["origin/main", "origin/none"])
@pytest.mark.parametrize("name", ["Coder", "../coder"])
def test_a_name_that_is_not_an_agent_name_is_refused_before_git_is_read(
    boundaries: Boundaries, installed: FrontmatterAgentDefinitionReader, *, ref: str, name: str
) -> None:
    project = ProjectAgentDefinitions(boundaries.git, installed, ref)

    with pytest.raises(AgentDefinitionMissing) as caught:
        project.read(name)

    assert caught.value.name == name
    assert caught.value.fault == f"not an agent name: {name}"


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda project: project.read("coder"), id="read"),
        pytest.param(lambda project: project.names(), id="names"),
    ],
)
def test_a_ref_that_does_not_exist_is_a_git_error(
    boundaries: Boundaries,
    installed: FrontmatterAgentDefinitionReader,
    call: Callable[[ProjectAgentDefinitions], object],
) -> None:
    project = ProjectAgentDefinitions(boundaries.git, installed, "origin/none")

    with pytest.raises(GitError):
        call(project)


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        pytest.param("branch", "The project's coder.", id="checked-out-branch"),
        pytest.param("edit", "The project's coder.", id="uncommitted-edit"),
        pytest.param("main", "The new coder.", id="new-main-fetched"),
    ],
)
def test_the_agent_is_read_at_the_ref_at_every_call_never_from_the_work_tree(
    project: ProjectAgentDefinitions,
    boundaries: Boundaries,
    human: HumanClone,
    *,
    change: str,
    expected: str,
) -> None:
    _push(human, boundaries, {CODER_FILE: PROJECT_CODER})
    assert project.read("coder").instructions == "The project's coder."
    branch_coder = PROJECT_CODER.replace("The project's coder.", "The branch's coder.")
    human.push_file(BRANCH, CODER_FILE, branch_coder)
    boundaries.git.fetch()
    boundaries.git.checkout(BRANCH, start_point=f"origin/{BRANCH}")
    if change == "edit":
        (boundaries.checkout / CODER_FILE).write_text(
            PROJECT_CODER.replace("The project's coder.", "The edited coder."), encoding="utf-8"
        )
    if change == "main":
        human.push_file(
            "main", CODER_FILE, PROJECT_CODER.replace("The project's coder.", "The new coder.")
        )
        boundaries.git.fetch()

    assert project.read("coder").instructions == expected


@pytest.mark.parametrize(
    ("text", "fault", "key"),
    [
        pytest.param(
            COLOURED_AGENT_FILE,
            "factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour",
            "colour",
            id="unapplied-key",
        ),
        pytest.param(
            "Do the work.\n",
            "factory/agents/coder.md at origin/main: no front matter",
            "",
            id="no-front-matter",
        ),
    ],
)
def test_a_faulty_project_file_is_refused_naming_the_file_never_replaced(
    project: ProjectAgentDefinitions,
    boundaries: Boundaries,
    human: HumanClone,
    *,
    text: str,
    fault: str,
    key: str,
) -> None:
    _push(human, boundaries, {CODER_FILE: text})

    with pytest.raises(AgentDefinitionInvalid) as caught:
        project.read("coder")

    assert (caught.value.name, caught.value.fault, caught.value.key) == ("coder", fault, key)


PROJECT_FILES = {
    "factory/agents/coder.md": PROJECT_CODER,
    "factory/agents/designer.md": PROJECT_CODER,
    "factory/agents/README.md": "# Agents\n",
    "factory/agents/Designer.md": PROJECT_CODER,
    "factory/agents/notes.txt": "Notes.\n",
    "factory/agents/sub/reviewer.md": PROJECT_CODER,
}


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        pytest.param(PROJECT_FILES, ["coder", "designer", "tester"], id="project-agents"),
        pytest.param({}, ["coder", "tester"], id="no-project-agents"),
    ],
)
def test_names_are_the_sorted_union_of_installed_and_project_agents(
    project: ProjectAgentDefinitions,
    boundaries: Boundaries,
    human: HumanClone,
    *,
    files: dict[str, str],
    expected: list[str],
) -> None:
    if files:
        _push(human, boundaries, files)

    assert project.names() == expected


def test_names_without_an_installed_agents_folder_is_an_error(
    boundaries: Boundaries, tmp_path: Path
) -> None:
    project = ProjectAgentDefinitions(
        boundaries.git, FrontmatterAgentDefinitionReader(tmp_path / "empty-home")
    )

    with pytest.raises(AgentDefinitionError):
        project.names()


def test_parse_is_the_installed_readers_parse(
    project: ProjectAgentDefinitions, installed: FrontmatterAgentDefinitionReader
) -> None:
    assert project.parse("coder", AGENT_FILE) == installed.parse("coder", AGENT_FILE)
