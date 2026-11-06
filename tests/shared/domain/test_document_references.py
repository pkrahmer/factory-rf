"""The backticked names, paths and relative links one document's text names."""

from typing import Literal

import pytest

from factory.shared.domain.documents import Reference, named_references

TOP_LEVEL = frozenset({"operator", "src", "tests", "docs", "README.md"})
DOCUMENT = "README.md"
Kind = Literal["module", "path", "link"]
OLD_AGENT_FILE = "claude" + "/agents/reviewer.md"


def _text(body: str) -> str:
    return f"# Title\n\n{body}\n\nThe end.\n"


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        pytest.param("See `factory.a.b` here.", [(3, "factory.a.b", "module")], id="module"),
        pytest.param(
            "See `factory.a.b.C.method` here.",
            [(3, "factory.a.b.C.method", "module")],
            id="attribute",
        ),
        pytest.param(
            "Run `operator/vm/setup.sh` once.",
            [(3, "operator/vm/setup.sh", "path")],
            id="repository-path",
        ),
        pytest.param(
            f"Read `{OLD_AGENT_FILE}` first.",
            [(3, OLD_AGENT_FILE, "path")],
            id="path-with-extension-outside-top-level",
        ),
        pytest.param("Edit `operator/<instance>/site.env` then.", [], id="placeholder-path"),
        pytest.param("See `factory.<area>.domain` there.", [], id="placeholder-module"),
        pytest.param("Every `tests/*.py` runs.", [], id="glob"),
        pytest.param("It lives in `/srv/factory` now.", [], id="absolute-srv"),
        pytest.param("It reads `/etc/factory/site.env` too.", [], id="absolute-etc"),
        pytest.param("Compare with `origin/main` first.", [], id="git-ref"),
        pytest.param("Python's `os.path` joins.", [], id="not-factory-module"),
        pytest.param("```\n`factory.a.b` and `operator/vm/setup.sh`\n```", [], id="fenced-block"),
        pytest.param("See [x](a.md#h) for it.", [(3, "a.md", "link")], id="link-with-fragment"),
        pytest.param("Run `make -C operator/vm` once.", [], id="whitespace"),
        pytest.param("It reads `~/.config/factory/site.env` too.", [], id="home"),
        pytest.param("Open `https://example.org/a.md` there.", [], id="web-address-in-backticks"),
        pytest.param("See [x](/srv/a.md) for it.", [], id="absolute-link"),
        pytest.param("See [x](mailto:a@example.org) for it.", [], id="mailto-link"),
        pytest.param("See [x](<instance>.md) for it.", [], id="placeholder-link"),
        pytest.param("See [x](*.md) for it.", [], id="glob-link"),
        pytest.param("Set it in `factory.env` once.", [], id="file-name-env"),
        pytest.param("Set it in `factory.local.env` once.", [], id="file-name-local-env"),
        *[
            pytest.param(f"Read `factory.x.{extension}` once.", [], id=f"file-name-{extension}")
            for extension in ("service", "yml", "yaml", "json", "toml", "md", "txt")
        ],
        pytest.param(
            "See `factory.shared.domain.yml_reader` here.",
            [(3, "factory.shared.domain.yml_reader", "module")],
            id="module-ending-like-an-extension",
        ),
        pytest.param(
            "Run `tests/x.py::test_y` once.", [(3, "tests/x.py", "path")], id="pytest-node-id"
        ),
        pytest.param("Run `tests/x.py` once.", [(3, "tests/x.py", "path")], id="path-without-node"),
        pytest.param("It reads `$HOME/a/b.txt` too.", [], id="shell-expression"),
        pytest.param("It reads `$HOME/factory.nothing.here` too.", [], id="shell-expression-whole"),
    ],
)
def test_named_references_finds_backticked_names_paths_and_links(
    body: str, expected: list[tuple[int, str, Kind]]
) -> None:
    references = named_references(DOCUMENT, _text(body), TOP_LEVEL)

    assert references == [
        Reference(document=DOCUMENT, line=line, name=name, kind=kind)
        for line, name, kind in expected
    ]
