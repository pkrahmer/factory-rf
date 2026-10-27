"""The `claude -p` runtime names the file a refused tool call named, when it named one."""

import json
from pathlib import Path

import pytest

from adapters.claude_stand_in import Step
from claude_resume_support import _reply, _request, _runtime
from factory.domain.agent_runs import PermissionDenial


@pytest.mark.parametrize(
    ("tool", "tool_input", "path"),
    [
        ("Write", {"file_path": "src/a.py"}, "src/a.py"),
        ("NotebookEdit", {"notebook_path": "n.ipynb"}, "n.ipynb"),
        ("Edit", {"file_path": "src/a.py", "notebook_path": "n.ipynb"}, "src/a.py"),
        ("Bash", {"command": "git push"}, None),
        ("Write", {"file_path": 3}, None),
        ("NotebookEdit", {"file_path": 3, "notebook_path": "n.ipynb"}, "n.ipynb"),
        ("Write", "src/a.py", None),
    ],
    ids=[
        "file-path",
        "notebook-path",
        "both",
        "no-path",
        "file-path-not-a-string",
        "file-path-not-a-string-notebook-path",
        "input-a-string",
    ],
)
def test_a_denial_names_the_file_or_notebook_path_of_its_call(
    tmp_path: Path, tool: str, tool_input: object, path: str | None
) -> None:
    denial = {"tool_name": tool, "tool_input": tool_input}
    runtime = _runtime(tmp_path, [Step(stdout=_reply(permission_denials=[denial]))])

    result = runtime.run(_request(tmp_path))

    detail = json.dumps(tool_input, sort_keys=True)
    assert result.permission_denials == [PermissionDenial(tool=tool, detail=detail, path=path)]
