"""An agent definition error names its agent when it has one, else it is only its fault."""

import pytest

from factory.domain.errors import AgentDefinitionError


@pytest.mark.parametrize(
    ("name", "text"),
    [
        pytest.param("", "no agent files", id="no-name"),
        pytest.param("coder", "agent coder: no agent files", id="name"),
    ],
)
def test_an_agent_definition_error_names_its_agent_only_when_it_has_one(
    name: str, text: str
) -> None:
    error = AgentDefinitionError(name, "no agent files")

    assert str(error) == text
    assert error.name == name
    assert error.fault == "no agent files"
