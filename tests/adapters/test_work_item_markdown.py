"""The work item file: its reader and writer, front matter notation, body and faults."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from frontmatter.default_handlers import YAMLHandler

from factory.adapters.work_item_markdown import (
    FrontmatterWorkItemReader,
    FrontmatterWorkItemWriter,
    RuamelYamlHandler,
)
from factory.application.files import WorkItemReader, WorkItemWriter
from factory.domain.errors import WorkItemFormatError
from factory.domain.journal import JournalRecord
from factory.domain.work_item import Claim, WorkItemDocument, WorkItemState, initial_state
from source_search import imports, modules

STARTED_AT = datetime(2026, 10, 13, 8, 30, tzinfo=UTC)
CLAIM_LINES = (
    "claim:\n  instance: factory-1\n  stage: tests\n  started_at: '2026-10-13T08:30:00Z'\n"
)


def _full_state() -> WorkItemState:
    return WorkItemState(
        stage="doing",
        blocked="question",
        round=1,
        attempts=2,
        crashes=0,
        pull_request=12,
        comments_read=[4, 9],
        handed_over="approval",
        claim=Claim(instance="factory-1", stage="doing", started_at=STARTED_AT, lease_duration=60),
        journal=[
            JournalRecord(number=1, speaker="human", kind="created"),
            JournalRecord(number=2, speaker="factory", kind="started"),
        ],
    )


def _fault_of_parse(text: str) -> str:
    with pytest.raises(WorkItemFormatError) as caught:
        FrontmatterWorkItemReader().parse(text)
    return caught.value.fault


def test_render_writes_a_full_state_in_the_fixed_notation() -> None:
    document = WorkItemDocument(state=_full_state(), body="# T\n")

    text = FrontmatterWorkItemWriter().render(document)

    started_at = STARTED_AT.isoformat().removesuffix("+00:00") + "Z"
    assert text == (
        "---\n"
        "stage: doing\n"
        "blocked: question\n"
        "round: 1\n"
        "attempts: 2\n"
        "crashes: 0\n"
        "pull_request: 12\n"
        "comments_read: [4, 9]\n"
        "handed_over: approval\n"
        "claim:\n"
        "  instance: factory-1\n"
        "  stage: doing\n"
        f"  started_at: '{started_at}'\n"
        "  lease_duration: 60\n"
        "journal:\n"
        "- number: 1\n"
        "  speaker: human\n"
        "  kind: created\n"
        "- number: 2\n"
        "  speaker: factory\n"
        "  kind: started\n"
        "---\n"
        "\n"
        "# T\n"
    )


def test_render_of_an_initial_state_writes_all_ten_keys() -> None:
    document = WorkItemDocument(state=initial_state("intake"), body="# T\n")

    text = FrontmatterWorkItemWriter().render(document)

    assert text == (
        "---\n"
        "stage: intake\n"
        "blocked: null\n"
        "round: 0\n"
        "attempts: 0\n"
        "crashes: 0\n"
        "pull_request: null\n"
        "comments_read: []\n"
        "handed_over: null\n"
        "claim: null\n"
        "journal: []\n"
        "---\n"
        "\n"
        "# T\n"
    )


def test_render_quotes_names_a_yaml_reader_could_read_as_null_or_boolean() -> None:
    state = WorkItemState(
        stage="doing",
        handed_over="true",
        claim=Claim(instance="null", stage="doing", started_at=STARTED_AT, lease_duration=60),
    )
    document = WorkItemDocument(state=state, body="# T\n")

    text = FrontmatterWorkItemWriter().render(document)

    lines = text.splitlines()
    assert "handed_over: 'true'" in lines
    assert "  instance: 'null'" in lines
    assert "stage: doing" in lines
    assert FrontmatterWorkItemReader().parse(text).state == state
    approval = WorkItemDocument(
        state=initial_state("doing").model_copy(update={"handed_over": "approval"}), body=""
    )
    assert "handed_over: approval" in FrontmatterWorkItemWriter().render(approval).splitlines()


@pytest.mark.parametrize(
    ("body", "ending"),
    [
        ("# T\n", "---\n\n# T\n"),
        ("# T", "---\n\n# T\n"),
        ("\n\n# T\n\n\n", "---\n\n# T\n"),
        ("", "journal: []\n---\n"),
        ("\n\n", "journal: []\n---\n"),
    ],
    ids=["one-newline", "no-newline", "blank-lines-around", "empty", "only-blank-lines"],
)
def test_render_writes_the_body_stripped_after_an_empty_line(body: str, ending: str) -> None:
    document = WorkItemDocument(state=initial_state("intake"), body=body)

    text = FrontmatterWorkItemWriter().render(document)

    assert text.endswith(ending)
    if body.strip() == "":
        assert not text.endswith("\n\n")


def test_render_refuses_a_document_without_state() -> None:
    document = WorkItemDocument(state=None, body="# T\n")

    with pytest.raises(WorkItemFormatError) as caught:
        FrontmatterWorkItemWriter().render(document)

    assert caught.value.fault == "the document has no state"


def test_round_trip_splits_only_at_the_closing_line_of_the_front_matter() -> None:
    body = "# T\n\nabove\n\n---\n\nbelow\n\n```\n---\nfenced\n---\n```\n"
    document = WorkItemDocument(state=_full_state(), body=body)

    back = FrontmatterWorkItemReader().parse(FrontmatterWorkItemWriter().render(document))

    assert back == document


@pytest.mark.parametrize(
    ("text", "body"),
    [
        ("---\nstage: t\n---\n\n\n  # T\n\nx  \n\n\n", "# T\n\nx\n"),
        ("---\nstage: t\n---\n", ""),
        ("---\nstage: t\n---", ""),
        ("---\nstage: t\n---\n\n\n\n", ""),
    ],
    ids=["text", "nothing-after-newline", "nothing-after", "only-blank-lines"],
)
def test_parse_strips_the_body_and_keeps_one_final_newline(text: str, body: str) -> None:
    assert FrontmatterWorkItemReader().parse(text).body == body


def test_parse_gives_initial_values_to_keys_left_out() -> None:
    document = FrontmatterWorkItemReader().parse("---\nstage: tests\n---\n# T\n")

    assert document.state == initial_state("tests")
    assert document.ignored_keys == []


@pytest.mark.parametrize(
    "text",
    [
        "# T\n",
        "--- x\nstage: tests\n---\n# T\n",
        "- - -\nstage: tests\n---\n# T\n",
        "# T\n\n---\nstage: tests\n---\n\nmore\n",
        "---\nstage: tests\n# T\n",
        "---\nstage: tests\n ---\n# T\n",
    ],
    ids=[
        "heading",
        "boundary-with-text",
        "spaced-dashes",
        "two-thematic-breaks",
        "never-closed",
        "closing-line-indented",
    ],
)
def test_parse_reports_no_front_matter(text: str) -> None:
    assert _fault_of_parse(text) == "no front matter"


def test_parse_reports_front_matter_that_is_not_valid_yaml() -> None:
    assert _fault_of_parse("---\nstage: [\n---\n") == "front matter is not valid YAML"


def test_parse_reports_front_matter_that_is_not_a_mapping() -> None:
    assert _fault_of_parse("---\n- a\n- b\n---\n# T\n") == "front matter is not a mapping"


@pytest.mark.parametrize(
    "text",
    [
        "\n\n  ---\nstage: tests\n---\n# T\n",
        "----\nstage: tests\n-----\n# T\n",
        "---  \nstage: tests\n---\t\n# T\n",
        "---\r\nstage: tests\r\n---\r\n# T\r\n",
    ],
    ids=["leading-whitespace", "longer-boundaries", "trailing-whitespace", "crlf"],
)
def test_parse_finds_the_front_matter_as_python_frontmatter_does(text: str) -> None:
    document = FrontmatterWorkItemReader().parse(text)

    assert document.state == initial_state("tests")
    assert document.body == "# T\n"


@pytest.mark.parametrize(
    ("front_matter", "fault"),
    [
        ("stage: tests\ncolour: 2\n", "unknown key: colour"),
        (
            "stage: tests\n" + CLAIM_LINES + "  lease_duration: 60\n  extra: 1\n",
            "unknown key: claim.extra",
        ),
        (
            "stage: tests\njournal:\n- number: 1\n  speaker: human\n  kind: created\n  extra: 1\n",
            "unknown key: journal[0].extra",
        ),
        ("colour: 2\nattempts: 1\n", "unknown key: colour"),
    ],
    ids=["top-level", "in-claim", "in-journal-record", "before-missing-stage"],
)
def test_parse_reports_an_unknown_key(front_matter: str, fault: str) -> None:
    assert _fault_of_parse(f"---\n{front_matter}---\n# T\n") == fault


@pytest.mark.parametrize(
    ("front_matter", "fault"),
    [
        ("attempts: 1\n", "missing key: stage"),
        ("stage: tests\n" + CLAIM_LINES, "missing key: claim.lease_duration"),
    ],
    ids=["stage", "claim-lease-duration"],
)
def test_parse_reports_a_missing_key(front_matter: str, fault: str) -> None:
    assert _fault_of_parse(f"---\n{front_matter}---\n# T\n") == fault


def test_parse_reports_a_missing_key_before_an_invalid_value() -> None:
    assert _fault_of_parse("---\nattempts: -1\n---\n# T\n") == "missing key: stage"


@pytest.mark.parametrize(
    ("front_matter", "fault"),
    [
        ("stage: tests\nattempts: -1\n", "invalid attempts"),
        ("stage: tests\nblocked: asked\n", "invalid blocked"),
        ("stage: tests\n" + CLAIM_LINES + "  lease_duration: 0\n", "invalid claim.lease_duration"),
        ("stage: tests\ncomments_read: [0]\n", "invalid comments_read[0]"),
        (
            "stage: tests\njournal:\n- number: 1\n  speaker: human\n  kind: note\n",
            "invalid journal[0].kind",
        ),
        ("stage: tests\nattempts: -1\nblocked: asked\n", "invalid blocked"),
    ],
    ids=[
        "attempts",
        "blocked",
        "claim-lease-duration",
        "comments-read-item",
        "journal-kind",
        "first-in-field-order",
    ],
)
def test_parse_reports_the_first_invalid_value(front_matter: str, fault: str) -> None:
    assert _fault_of_parse(f"---\n{front_matter}---\n# T\n").startswith(fault)


@pytest.mark.parametrize(
    ("front_matter", "fault"),
    [
        ("stage: tests\ncomments_read: [5, 3]\n", "invalid comments_read"),
        (
            "stage: tests\njournal:\n"
            "- number: 1\n  speaker: human\n  kind: created\n"
            "- number: 3\n  speaker: factory\n  kind: started\n",
            "invalid journal",
        ),
        ("stage: doing\n" + CLAIM_LINES + "  lease_duration: 60\n", "invalid state"),
        ("stage: doing\n" + CLAIM_LINES + "  lease_duration: 0\n", "invalid claim.lease_duration"),
    ],
    ids=["comments-read-order", "journal-numbering", "claim-stage", "invalid-value-first"],
)
def test_parse_reports_broken_rules_of_a_field_and_across_keys(
    front_matter: str, fault: str
) -> None:
    assert _fault_of_parse(f"---\n{front_matter}---\n# T\n").startswith(fault)


@pytest.mark.parametrize(
    "front_matter", ["", "null\n", "# none\n"], ids=["empty", "null", "comment"]
)
def test_front_matter_that_loads_as_nothing_is_an_empty_mapping(front_matter: str) -> None:
    text = f"---\n{front_matter}---\n# T\n"
    reader = FrontmatterWorkItemReader()

    assert _fault_of_parse(text) == "missing key: stage"
    assert reader.parse_specification(text) == WorkItemDocument(
        state=None, body="# T\n", ignored_keys=[]
    )


@pytest.mark.parametrize(
    ("front_matter", "ignored_keys"),
    [
        ("stage: tests\nattempts: 1\n", ["stage", "attempts"]),
        ("1: x\nstage: tests\n", ["1", "stage"]),
    ],
    ids=["state-keys", "number-key"],
)
def test_parse_specification_drops_the_front_matter_and_names_its_keys(
    front_matter: str, ignored_keys: list[str]
) -> None:
    text = f"---\n{front_matter}---\n\n\n# T\n\n"

    document = FrontmatterWorkItemReader().parse_specification(text)

    assert document == WorkItemDocument(state=None, body="# T\n", ignored_keys=ignored_keys)


@pytest.mark.parametrize(
    ("text", "body"),
    [
        ("\n\n# T\n\nx  \n\n", "# T\n\nx\n"),
        ("# T\n\n---\nstage: tests\n---\n\nmore\n", "# T\n\n---\nstage: tests\n---\n\nmore\n"),
        ("---\nstage: tests\n# T\n", "---\nstage: tests\n# T\n"),
    ],
    ids=["plain", "two-thematic-breaks", "never-closed"],
)
def test_parse_specification_of_a_text_without_front_matter_keeps_it_whole(
    text: str, body: str
) -> None:
    document = FrontmatterWorkItemReader().parse_specification(text)

    assert document == WorkItemDocument(state=None, body=body, ignored_keys=[])


@pytest.mark.parametrize(
    ("text", "fault"),
    [
        ("---\nstage: [\n---\n", "front matter is not valid YAML"),
        ("---\n- a\n- b\n---\n# T\n", "front matter is not a mapping"),
    ],
    ids=["invalid-yaml", "not-a-mapping"],
)
def test_parse_specification_refuses_front_matter_it_cannot_read(text: str, fault: str) -> None:
    with pytest.raises(WorkItemFormatError) as caught:
        FrontmatterWorkItemReader().parse_specification(text)

    assert caught.value.fault == fault


def test_read_returns_what_parse_returns_for_the_file_text(tmp_path: Path) -> None:
    text = "---\nstage: tests\nattempts: 1\n---\n\n# T\n\nbody\n"
    path = tmp_path / "item.md"
    path.write_text(text, encoding="utf-8")

    reader = FrontmatterWorkItemReader()

    assert reader.read(path) == reader.parse(text)


@pytest.mark.parametrize("content", [None, b"\xff\xfe"], ids=["missing", "not-utf-8"])
def test_read_reports_a_file_it_cannot_read(tmp_path: Path, content: bytes | None) -> None:
    path = tmp_path / "item.md"
    if content is not None:
        path.write_bytes(content)

    with pytest.raises(WorkItemFormatError) as caught:
        FrontmatterWorkItemReader().read(path)

    assert caught.value.fault.startswith("cannot read")
    assert caught.value.path == str(path)


def test_read_reports_a_fault_of_the_file_with_its_path(tmp_path: Path) -> None:
    path = tmp_path / "item.md"
    path.write_text("---\nstage: tests\ncolour: 2\n---\n# T\n", encoding="utf-8")

    with pytest.raises(WorkItemFormatError) as caught:
        FrontmatterWorkItemReader().read(path)

    assert caught.value.fault == "unknown key: colour"
    assert caught.value.path == str(path)


def test_write_replaces_the_file_with_the_rendered_text(tmp_path: Path) -> None:
    path = tmp_path / "item.md"
    path.write_text("old text\r\n", encoding="utf-8")
    document = WorkItemDocument(state=_full_state(), body="# T\n\nbody\n")

    FrontmatterWorkItemWriter().write(path, document)

    data = path.read_bytes()
    assert data == FrontmatterWorkItemWriter().render(document).encode("utf-8")
    assert b"\r\n" not in data
    assert FrontmatterWorkItemReader().read(path) == document


def test_reader_and_writer_implement_abstract_interfaces() -> None:
    assert WorkItemReader.__abstractmethods__ == {"parse", "parse_specification", "read"}
    assert WorkItemWriter.__abstractmethods__ == {"render", "write"}
    assert issubclass(FrontmatterWorkItemReader, WorkItemReader)
    assert issubclass(FrontmatterWorkItemWriter, WorkItemWriter)


def test_handler_keeps_the_boundary_and_delimiters_of_the_yaml_handler() -> None:
    assert issubclass(RuamelYamlHandler, YAMLHandler)
    assert RuamelYamlHandler.FM_BOUNDARY is YAMLHandler.FM_BOUNDARY
    assert RuamelYamlHandler.START_DELIMITER == YAMLHandler.START_DELIMITER
    assert RuamelYamlHandler.END_DELIMITER == YAMLHandler.END_DELIMITER


def test_only_the_work_item_adapter_imports_frontmatter_and_ruamel() -> None:
    trees = modules()
    adapter = trees["factory.adapters.work_item_markdown"]
    others = [
        name
        for name, tree in trees.items()
        if name.split(".")[1:2] in (["domain"], ["application"], ["entry"])
        and (imports(tree, "frontmatter") or imports(tree, "ruamel.yaml"))
    ]

    assert imports(adapter, "frontmatter")
    assert imports(adapter, "ruamel.yaml")
    assert others == []
