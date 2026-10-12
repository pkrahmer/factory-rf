"""The hosting service is reached through PyGithub in one module and by no other route."""

import pytest

from source_search import imports, modules, string_literals

FORBIDDEN = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "urllib.request",
    "http.client",
    "socket",
    "git",
    "pygit2",
    "dulwich",
    "githubkit",
)


def test_only_the_pygithub_client_imports_github() -> None:
    importers = {name for name, tree in modules().items() if imports(tree, "github")}

    assert importers == {"factory.adapters.pygithub_hosting"}


@pytest.mark.parametrize("module", FORBIDDEN)
def test_no_module_imports_another_route_to_the_hosting_service(module: str) -> None:
    importers = {name for name, tree in modules().items() if imports(tree, module)}

    assert importers == set()


def test_no_module_names_the_gh_tool() -> None:
    naming = {name for name, tree in modules().items() if "gh" in string_literals(tree)}

    assert naming == set()
