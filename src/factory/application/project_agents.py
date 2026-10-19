"""A project's own agents, read at `origin/main` before the installed ones."""

from typing import override

from factory.application.agent_runtime import AgentDefinitionReader
from factory.application.git import Git
from factory.application.pipeline_loading import PIPELINE_REF
from factory.domain.agent_runs import AgentDefinition, check_agent_name
from factory.domain.errors import AgentDefinitionInvalid
from factory.domain.identifiers import is_name
from factory.domain.paths import AGENT_SUFFIX, PROJECT_AGENTS_DIRECTORY, project_agent_file


class ProjectAgentDefinitions(AgentDefinitionReader):
    """A project's own agents at `origin/main` first, the installed ones otherwise."""

    def __init__(self, git: Git, installed: AgentDefinitionReader, ref: str = PIPELINE_REF) -> None:
        """Read the project's agents through `git` at `ref`, and `installed` where it has none."""
        self._git = git
        self._installed = installed
        self._ref = ref

    @override
    def names(self) -> list[str]:
        return sorted(set(self._installed.names()) | set(self._project_names()))

    @override
    def read(self, name: str) -> AgentDefinition:
        # Checked before git is asked, so a name can never lead outside the agents folder.
        check_agent_name(name)
        path = project_agent_file(name)
        text = self._git.show_file(self._ref, path)
        if text is None:
            return self._installed.read(name)
        try:
            return self._installed.parse(name, text)
        except AgentDefinitionInvalid as error:
            # A faulty project file stays the fault: the installed agent would hide it.
            raise AgentDefinitionInvalid(
                name, f"{path} at {self._ref}: {error.fault}", error.key
            ) from error

    @override
    def parse(self, name: str, text: str) -> AgentDefinition:
        return self._installed.parse(name, text)

    def _project_names(self) -> list[str]:
        prefix = f"{PROJECT_AGENTS_DIRECTORY}/"
        names = []
        for path in self._git.list_files(self._ref, PROJECT_AGENTS_DIRECTORY):
            stem = path.removeprefix(prefix).removesuffix(AGENT_SUFFIX)
            # The round trip leaves out files in subfolders and with another suffix.
            if is_name(stem) and project_agent_file(stem) == path:
                names.append(stem)
        return names
