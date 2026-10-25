"""The write paths and the shared test helpers carry no name of a removed layer."""

import inspect
import re
from collections.abc import Callable
from dataclasses import fields
from pathlib import Path

import pytest

from factory.domain import agent_runs, write_paths
from module_names import has_name
from run_layout_support import Layout, build_layout

SOURCE = Path(__file__).parents[1] / "src" / "factory"
TESTS = Path(__file__).parent


def _import_of(module: str) -> str:
    return rf"^\s*(?:from|import)\s+{module}\b"


def _files_holding(root: Path, pattern: str) -> list[str]:
    found = re.compile(pattern, re.MULTILINE)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.py")
        if found.search(path.read_text(encoding="utf-8"))
    )


def _planted(tmp_path: Path) -> Path:
    root = tmp_path / "src" / "factory"
    root.mkdir(parents=True)
    (root / "planted.py").write_text(
        "from factory.domain.agent_runs import GuardSettings\n", encoding="utf-8"
    )
    return root


@pytest.mark.parametrize(
    ("check", "expected"),
    [
        pytest.param(
            lambda: has_name("factory.domain.agent_runs", "WritePathSettings"), True, id="new-name"
        ),
        pytest.param(
            lambda: has_name("factory.domain.agent_runs", "GuardSettings"), False, id="old-name"
        ),
        pytest.param(
            lambda: list(agent_runs.WritePathSettings.model_fields),
            ["root", "write_paths", "protected_paths"],
            id="fields",
        ),
        pytest.param(
            lambda: list(inspect.signature(write_paths.refusal).parameters),
            ["path", "settings"],
            id="refusal-parameters",
        ),
        pytest.param(
            lambda: "guard" in inspect.signature(write_paths.refusal).parameters,
            False,
            id="refusal-no-guard",
        ),
    ],
)
def test_the_write_paths_carry_their_new_names(
    check: Callable[[], object], expected: object
) -> None:
    assert check() == expected


@pytest.mark.parametrize(
    ("root_of", "pattern", "expected"),
    [
        pytest.param(lambda _: SOURCE, r"GuardSettings", [], id="source-guard-settings"),
        pytest.param(lambda _: TESTS, _import_of("confine_support"), [], id="tests-confine"),
        pytest.param(lambda _: TESTS, _import_of("sealed_run_support"), [], id="tests-sealed"),
        pytest.param(_planted, r"GuardSettings", ["planted.py"], id="planted-is-found"),
    ],
)
def test_no_file_holds_a_removed_layer_s_name(
    root_of: Callable[[Path], Path], pattern: str, expected: list[str], tmp_path: Path
) -> None:
    assert _files_holding(root_of(tmp_path), pattern) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        pytest.param("src/a.py", None, id="writable"),
        pytest.param(
            "docs/a.md", "docs/a.md is outside the write paths of this stage.", id="outside"
        ),
        pytest.param(
            "factory/pipeline.yml",
            "factory/pipeline.yml is owned by the human; a change there is a question.",
            id="protected",
        ),
    ],
)
def test_the_rule_of_the_write_paths_is_unchanged(path: str, expected: str | None) -> None:
    settings = agent_runs.WritePathSettings(
        root=Path("/work/checkout"),
        write_paths=["src/*"],
        protected_paths=["factory/pipeline.yml"],
    )
    assert write_paths.refusal(path, settings) == expected


def test_the_run_layout_has_no_temporary_root(tmp_path: Path) -> None:
    build_layout(tmp_path)
    assert [field.name for field in fields(Layout)] == [
        "checkout",
        "home",
        "state",
        "stand_in",
        "shell_bin",
    ]
    assert not (tmp_path / "tmp").exists()
