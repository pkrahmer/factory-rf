"""The PyGithub client built for one repository and token, without a request."""

from collections.abc import Callable

import github
import pytest

from factory.adapters.pygithub_hosting import PyGithubHostingService, pygithub_service

CREDENTIAL = "example-value"


def test_pygithub_service_is_built_lazily_for_the_repository_and_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built: list[dict[str, object]] = []
    repositories: list[tuple[object, ...]] = []
    original_init: Callable[..., None] = github.Github.__init__
    original_get_repo: Callable[..., object] = github.Github.get_repo

    def recording_init(self: github.Github, *args: object, **kwargs: object) -> None:
        built.append(dict(kwargs))
        original_init(self, *args, **kwargs)

    def recording_get_repo(self: github.Github, *args: object, **kwargs: object) -> object:
        repositories.append((*args, *kwargs.values()))
        return original_get_repo(self, *args, **kwargs)

    monkeypatch.setattr(github.Github, "__init__", recording_init)
    monkeypatch.setattr(github.Github, "get_repo", recording_get_repo)

    service = pygithub_service("owner/project", CREDENTIAL)

    assert isinstance(service, PyGithubHostingService)
    assert len(built) == 1
    assert built[0]["lazy"] is True
    auth = built[0]["auth"]
    assert isinstance(auth, github.Auth.Token)
    assert auth.token == CREDENTIAL
    assert repositories == [("owner/project",)]
