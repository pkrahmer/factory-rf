"""No test sees the agent's login, whatever environment pytest was started with."""

import os
from pathlib import Path

import pytest

from factory.adapters.agent_launch import API_LOGIN_VARIABLE, LOGIN_VARIABLE

CONFTEST = Path(__file__).parent / "conftest.py"
VERSION_TEST = Path(__file__).parent / "adapters" / "test_opencode_runtime_launch.py"
NAMES = [
    pytest.param(LOGIN_VARIABLE, id="subscription"),
    pytest.param(API_LOGIN_VARIABLE, id="api-key"),
]


@pytest.mark.parametrize("name", NAMES)
def test_a_test_does_not_see_the_login(name: str) -> None:
    assert name not in set(os.environ)


@pytest.mark.parametrize("name", NAMES)
def test_a_test_that_sets_the_login_sees_its_own_value(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    monkeypatch.setenv(name, "x")

    assert os.environ.get(name) == "x"


@pytest.mark.parametrize(
    ("text", "present"),
    [
        pytest.param("monkeypatch.delenv", True, id="through-monkeypatch"),
        pytest.param("os.environ.pop", False, id="no-pop"),
        pytest.param("del os.environ", False, id="no-del"),
    ],
)
def test_the_login_is_removed_through_monkeypatch(text: str, present: bool) -> None:
    assert (text in CONFTEST.read_text(encoding="utf-8")) is present


def test_the_version_test_compares_variable_names_only() -> None:
    text = VERSION_TEST.read_text(encoding="utf-8")
    body = text.split("def test_the_version_is_the_first_word_of_a_call_without_login_words(")[1]
    body = body.split("\n\n\n")[0]

    assert (
        body.rstrip().splitlines()[-1]
        == "    assert API_LOGIN_VARIABLE not in set(call.environment)"
    )
