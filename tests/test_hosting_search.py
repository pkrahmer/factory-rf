"""The hosting service is reached through PyGithub in one module and by no other route."""

import ast

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
# The token endpoint is not the hosting service: the refresher's HTTP is the standard library's.
ALLOWED = {"urllib.request": {"factory.adapters.oauth_token"}}
SECOND = {"factory.adapters.elsewhere": ast.parse("import urllib.request\n")}


def test_only_the_pygithub_client_imports_github() -> None:
    importers = {name for name, tree in modules().items() if imports(tree, "github")}

    assert importers == {"factory.adapters.pygithub_hosting"}


@pytest.mark.parametrize(
    ("module", "added", "caught"),
    [
        *(pytest.param(module, {}, set(), id=module) for module in FORBIDDEN),
        pytest.param(
            "urllib.request",
            SECOND,
            {"factory.adapters.elsewhere"},
            id="urllib.request-in-a-second-module",
        ),
    ],
)
def test_no_module_imports_another_route_to_the_hosting_service(
    module: str, added: dict[str, ast.Module], caught: set[str]
) -> None:
    found = modules() | added
    importers = {name for name, tree in found.items() if imports(tree, module)}

    assert importers - ALLOWED.get(module, set()) == caught


def test_no_module_names_the_gh_tool() -> None:
    naming = {name for name, tree in modules().items() if "gh" in string_literals(tree)}

    assert naming == set()
