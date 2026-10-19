"""The agent files in the agent home: which agents are installed and what each one says."""

from pathlib import Path
from typing import override

from pydantic import ValidationError

from factory.adapters.validation_faults import first_error, first_fault
from factory.adapters.work_item_markdown import RuamelYamlHandler, split_front_matter
from factory.application.agent_runtime import AgentDefinitionReader
from factory.domain.agent_runs import APPLIED_AGENT_KEYS, KEY_NOT_APPLIED, AgentDefinition
from factory.domain.errors import (
    AgentDefinitionError,
    AgentDefinitionInvalid,
    AgentDefinitionMissing,
    WorkItemFormatError,
)
from factory.domain.identifiers import is_name

_BUDGET_KEY = "budget_usd"
_AGENT_SUFFIX = ".md"


def _check_name(name: str) -> None:
    if not is_name(name):
        raise AgentDefinitionMissing(name, f"not an agent name: {name}")


def _invalid(name: str, error: ValidationError) -> AgentDefinitionInvalid:
    details = first_error(error)
    key = str(details["loc"][0]) if details["loc"] else ""
    if key == _BUDGET_KEY and details["type"] != "missing":
        return AgentDefinitionInvalid(name, f"{_BUDGET_KEY} must be greater than 0", key)
    return AgentDefinitionInvalid(name, first_fault(error, "agent"), key)


def _refuse_unapplied_keys(name: str, values: dict[str, object]) -> None:
    # Before validation: a dead key is the fault to fix even when an applied key is wrong too.
    for key in values:
        if key not in APPLIED_AGENT_KEYS:
            raise AgentDefinitionInvalid(name, f"{KEY_NOT_APPLIED}: {key}", key)


class FrontmatterAgentDefinitionReader(AgentDefinitionReader):
    """Reads the agent files `<agent_home>/agents/<name>.md` with python-frontmatter."""

    def __init__(self, agent_home: Path) -> None:
        """Read the agents installed under `agent_home`."""
        self._agents = agent_home / "agents"
        self._handler = RuamelYamlHandler()

    @override
    def names(self) -> list[str]:
        if not self._agents.is_dir():
            raise AgentDefinitionError("", f"no agents directory at {self._agents}")
        return sorted(
            path.stem
            for path in self._agents.iterdir()
            if path.suffix == _AGENT_SUFFIX and path.is_file() and is_name(path.stem)
        )

    @override
    def read(self, name: str) -> AgentDefinition:
        # Checked before any path is built, so a name can never lead outside the agents directory.
        _check_name(name)
        path = self._agents / f"{name}{_AGENT_SUFFIX}"
        if not path.is_file():
            raise AgentDefinitionMissing(name, f"no agent file {path}")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise AgentDefinitionInvalid(name, f"cannot read: {error}", "") from error
        return self.parse(name, text)

    @override
    def parse(self, name: str, text: str) -> AgentDefinition:
        _check_name(name)
        values, instructions = self._front_matter_and_body(name, text)
        _refuse_unapplied_keys(name, values)
        try:
            return AgentDefinition.model_validate(
                {**values, "name": name, "instructions": instructions}
            )
        except ValidationError as error:
            raise _invalid(name, error) from error

    def _front_matter_and_body(self, name: str, text: str) -> tuple[dict[str, object], str]:
        split = split_front_matter(self._handler, text)
        if split is None:
            raise AgentDefinitionInvalid(name, "no front matter", "")
        front_matter, body = split
        try:
            values = self._handler.load(front_matter)
        except WorkItemFormatError as error:
            raise AgentDefinitionInvalid(name, error.fault, "") from error
        return values, body.strip()
