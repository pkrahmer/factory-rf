"""The checkout's hygiene is gone: the seal, its error, the nested-repository stall."""

import importlib.util
import typing
from collections.abc import Callable

import pytest

from factory.adapters.git_cli import GitCli
from factory.application.git import Git
from factory.application.stage import LaunchedStage
from factory.domain import errors
from factory.domain.journal import StallReason
from factory.domain.post_texts import stall_cause, stall_note

REMOVED_OPERATIONS = {
    "seal",
    "check_seal",
    "remove_nested_repositories",
    "remove_ignored",
    "discard",
}


def _no_stall_text_mentions_a_nested_repository() -> bool:
    texts = [
        text
        for reason in typing.get_args(StallReason)
        for text in (
            stall_cause(reason),
            stall_cause(reason, "sub/.git"),
            stall_note(reason, 1, 2),
            stall_note(reason, 2, 2, detail="sub/.git"),
        )
    ]
    return not [text for text in texts if "git repository" in text or "nested" in text]


@pytest.mark.parametrize(
    "holds",
    [
        pytest.param(
            lambda: importlib.util.find_spec("factory.application.sealed_runs") is None,
            id="sealed-runs-module",
        ),
        pytest.param(lambda: not REMOVED_OPERATIONS & Git.__abstractmethods__, id="git-operations"),
        pytest.param(lambda: len(Git.__abstractmethods__) == 21, id="git-twenty-one"),
        pytest.param(
            lambda: [name for name in REMOVED_OPERATIONS if hasattr(GitCli, name)] == [],
            id="git-cli-operations",
        ),
        pytest.param(lambda: not hasattr(errors, "RepositoryUnsealed"), id="repository-unsealed"),
        pytest.param(
            lambda: "nested_repository" not in typing.get_args(StallReason),
            id="stall-reason",
        ),
        pytest.param(
            lambda: "nested_repositories" not in LaunchedStage.model_fields,
            id="launched-stage-field",
        ),
        pytest.param(_no_stall_text_mentions_a_nested_repository, id="stall-texts"),
    ],
)
def test_the_names_of_the_checkouts_hygiene_are_gone(holds: Callable[[], bool]) -> None:
    assert holds()
