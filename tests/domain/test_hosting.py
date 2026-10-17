"""The hosting-service DTOs, the factory's marker and the post key."""

import ast
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, get_args

import pytest
from pydantic import ValidationError

import factory
from factory.domain.hosting import (
    FACTORY_MARKER,
    PostKey,
    PostKind,
    PullRequestComment,
    PullRequestView,
    parse_post_key,
    render_post,
)
from factory.domain.paths import LABEL_PREFIX, MAIN_BRANCH

KINDS = (
    "question",
    "attempts_cap",
    "round_cap",
    "crash_cap",
    "send_back",
    "stall",
    "expiry",
    "correction",
    "error",
    "cost_table",
)
COMMIT = "a" * 40
CREATED = datetime(2026, 10, 12, 9, 30, tzinfo=UTC)
SRC = Path(factory.__file__).parent


def _key(kind: str = "question") -> PostKey:
    return PostKey.model_validate({"work_item": "F0001-S0001", "kind": kind, "n": "7"})


def _view(**changes: Any) -> PullRequestView:
    fields: dict[str, Any] = {
        "number": 3,
        "branch": "work-item/F0001-S0001",
        "title": "t",
        "state": "open",
        "draft": False,
        "url": "https://example.invalid/pull/3",
    }
    fields.update(changes)
    return PullRequestView.model_validate(fields)


def test_constants_have_their_values() -> None:
    assert MAIN_BRANCH == "main"
    assert LABEL_PREFIX == "stage:"
    assert FACTORY_MARKER == "<!-- factory -->"


def test_post_key_comment_names_work_item_kind_and_n() -> None:
    key = PostKey(work_item="F0001-S0001", kind="question", n="7")

    assert key.comment() == "<!-- factory key=F0001-S0001:question:7 -->"


def test_post_kind_lists_exactly_the_ten_kinds() -> None:
    assert set(get_args(PostKind)) == set(KINDS)


@pytest.mark.parametrize(
    ("work_item", "kind", "n"),
    [("F0001-S0001", kind, "7") for kind in KINDS]
    + [
        ("F0001-A0001", "question", "7"),
        ("F0001-S0001", "question", "0a1f"),
    ],
)
def test_post_key_accepts_valid_values(work_item: str, kind: str, n: str) -> None:
    key = PostKey.model_validate({"work_item": work_item, "kind": kind, "n": n})

    assert (key.work_item, key.kind, key.n) == (work_item, kind, n)


@pytest.mark.parametrize(
    ("work_item", "kind", "n"),
    [
        ("F001-S0001", "question", "7"),
        ("F0001-X0001", "question", "7"),
        ("F0001-S0001", "other", "7"),
        ("F0001-S0001", "question", ""),
        ("F0001-S0001", "question", "G1"),
        ("F0001-S0001", "question", "ABC"),
    ],
)
def test_post_key_rejects_invalid_values(work_item: str, kind: str, n: str) -> None:
    with pytest.raises(ValidationError):
        PostKey.model_validate({"work_item": work_item, "kind": kind, "n": n})


def test_render_post_strips_trailing_whitespace_and_ends_with_the_key() -> None:
    key = _key("stall")

    body = render_post("Stage tests stalled.\n\n", key)

    assert body == f"Stage tests stalled.\n\n<!-- factory -->\n{key.comment()}"


@pytest.mark.parametrize("kind", KINDS)
def test_parse_post_key_reads_back_a_rendered_post(kind: str) -> None:
    key = _key(kind)

    assert parse_post_key(render_post("Some text.", key)) == key


def _key_line(work_item: str = "F0001-S0001", kind: str = "question", n: str = "7") -> str:
    return f"text\n\n{FACTORY_MARKER}\n<!-- factory key={work_item}:{kind}:{n} -->"


@pytest.mark.parametrize(
    "body",
    [
        "",
        f"Just text.\n\n{FACTORY_MARKER}",
        _key_line() + "\nmore text",
        "See <!-- factory key=F0001-S0001:question:7 --> above.",
        _key_line(kind="other"),
        _key_line(work_item="F001-S0001"),
        _key_line(n="G"),
        _key_line(n=""),
    ],
    ids=[
        "empty",
        "no-key-line",
        "text-after-key",
        "quoted-in-sentence",
        "kind-other",
        "bad-work-item",
        "n-not-hex",
        "n-empty",
    ],
)
def test_parse_post_key_returns_none_without_a_valid_last_key_line(body: str) -> None:
    assert parse_post_key(body) is None


@pytest.mark.parametrize(
    "body",
    [
        _key_line() + "\n\n",
        _key_line() + "   ",
        _key_line() + "\r",
        _key_line().replace("\n", "\r\n"),
    ],
    ids=["blank-lines-after", "trailing-spaces", "trailing-cr", "crlf-throughout"],
)
def test_parse_post_key_tolerates_trailing_whitespace_and_crlf(body: str) -> None:
    assert parse_post_key(body) == _key()


@pytest.mark.parametrize(
    ("author", "body", "by_factory", "key"),
    [
        ("someone", render_post("Text.", _key()), True, _key()),
        ("someone", f"Text.\n\n{FACTORY_MARKER}", True, None),
        ("someone", "Text.\n\n<!-- factory key=F0001-S0001:question:7 -->", False, None),
        ("someone", "Just a comment.", False, None),
        ("factory", "Just a comment.", False, None),
    ],
    ids=["rendered", "marker-no-key", "key-no-marker", "plain", "factory-author"],
)
def test_comment_is_by_factory_exactly_when_it_carries_the_marker(
    author: str, body: str, by_factory: bool, key: PostKey | None
) -> None:
    comment = PullRequestComment.from_body(id=1, author=author, body=body, created_at=CREATED)

    assert comment.by_factory is by_factory
    assert comment.key == key
    assert comment.author == author
    assert comment.body == body


def _comment(**changes: Any) -> PullRequestComment:
    fields: dict[str, Any] = {
        "id": 1,
        "author": "someone",
        "body": "x",
        "created_at": CREATED,
        "by_factory": False,
        "key": None,
    }
    fields.update(changes)
    return PullRequestComment.model_validate(fields)


def test_comment_rejects_a_naive_created_at() -> None:
    with pytest.raises(ValidationError):
        _comment(created_at=datetime(2026, 10, 12, 9, 30))  # noqa: DTZ001


@pytest.mark.parametrize(("comment_id", "valid"), [(0, False), (1, True)])
def test_comment_id_must_be_positive(comment_id: int, valid: bool) -> None:
    if valid:
        assert _comment(id=comment_id).id == comment_id
    else:
        with pytest.raises(ValidationError):
            _comment(id=comment_id)


def test_comment_converts_created_at_to_utc() -> None:
    local = datetime(2026, 10, 12, 11, 30, tzinfo=timezone(timedelta(hours=2)))

    comment = _comment(created_at=local)

    assert comment.created_at == CREATED
    assert comment.created_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "merged", "merge_commit": COMMIT},
        {"state": "open"},
        {"state": "closed"},
        {"state": "open", "draft": True},
    ],
)
def test_pull_request_view_accepts_consistent_states(changes: dict[str, Any]) -> None:
    view = _view(**changes)

    assert view.state == changes["state"]
    assert view.merge_commit == changes.get("merge_commit")


@pytest.mark.parametrize(
    "changes",
    [
        {"state": "merged"},
        {"state": "open", "merge_commit": COMMIT},
        {"state": "closed", "merge_commit": COMMIT},
        {"state": "merged", "merge_commit": "a" * 39},
        {"state": "merged", "merge_commit": "A" + "a" * 39},
        {"number": 0},
    ],
    ids=["merged-without", "open-with", "closed-with", "39-chars", "uppercase", "number-0"],
)
def test_pull_request_view_rejects_inconsistent_values(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        _view(**changes)


def _resolve(module: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package = module.split(".")[: -node.level]
    return ".".join(package + ([node.module] if node.module else []))


def _imports(module: str) -> list[str]:
    path = SRC.joinpath(*module.split(".")[1:]).with_suffix(".py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(_resolve(module, node))
    return names


def _is_stdlib(name: str) -> bool:
    return name.split(".", 1)[0] in sys.stdlib_module_names


def _is_domain(name: str) -> bool:
    return name == "factory.domain" or name.startswith("factory.domain.")


@pytest.mark.parametrize(
    "module",
    [
        "factory.domain.hosting",
        "factory.domain.identifiers",
        "factory.domain.git",
        "factory.domain.paths",
    ],
)
def test_domain_modules_import_only_stdlib_pydantic_and_domain(module: str) -> None:
    for name in _imports(module):
        top = name.split(".", 1)[0]
        assert _is_stdlib(name) or top == "pydantic" or _is_domain(name), name


def test_application_hosting_imports_only_stdlib_and_domain() -> None:
    for name in _imports("factory.application.hosting"):
        assert _is_stdlib(name) or _is_domain(name), name
