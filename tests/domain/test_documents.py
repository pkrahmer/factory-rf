"""The check of the four documents: sections, table rows, replaced phrases and v1 words."""

import pydantic
import pytest
from pydantic import BaseModel

from document_texts import (
    PATH_7_TEST,
    clean_texts,
    decision_log,
    operator_guide,
    project_guide,
    readme,
)
from factory.domain.documents import (
    DECISION_LOG,
    DOCUMENT_PATHS,
    OPERATOR_GUIDE,
    OPERATOR_GUIDE_SECTIONS,
    PROJECT_GUIDE,
    PROJECT_GUIDE_SECTIONS,
    README,
    REPLACED_PHRASES,
    DocumentFinding,
    check_documents,
)
from factory.domain.fault_paths import FAULT_PATHS, FaultPath
from factory.domain.kill_point_cases import KILL_POINT_CASES, KillPointCase
from factory.domain.stop_table import STOP_TABLE, StopRow

FENCE = "```"
PATH_7_FINDING = f"fault-injection path 7 has no table row naming '{PATH_7_TEST}'"
TEXT_GUIDES = (README, OPERATOR_GUIDE, PROJECT_GUIDE)


def _with(**documents: str | None) -> dict[str, str | None]:
    names = {
        "readme": README,
        "operator": OPERATOR_GUIDE,
        "project": PROJECT_GUIDE,
        "decisions": DECISION_LOG,
    }
    texts = clean_texts()
    for name, text in documents.items():
        texts[names[name]] = text
    return texts


def _guide(document: str, *, prefix: str = "", suffix: str = "") -> str:
    if document == README:
        return readme(prefix=prefix, suffix=suffix)
    if document == OPERATOR_GUIDE:
        return operator_guide(prefix=prefix, suffix=suffix)
    return project_guide(prefix=prefix, suffix=suffix)


def _finding(document: str, message: str) -> DocumentFinding:
    return DocumentFinding(document=document, message=message)


def test_four_clean_documents_give_no_finding() -> None:
    assert check_documents(clean_texts()) == []


@pytest.mark.parametrize("absent", [False, True], ids=["none", "absent-key"])
@pytest.mark.parametrize("document", DOCUMENT_PATHS)
def test_a_missing_document_gives_one_missing_finding(document: str, absent: bool) -> None:
    texts = clean_texts()
    if absent:
        del texts[document]
    else:
        texts[document] = None

    assert check_documents(texts) == [_finding(document, "missing")]


@pytest.mark.parametrize("blank", [" \n\t \n", ""], ids=["whitespace", "empty-string"])
@pytest.mark.parametrize("document", DOCUMENT_PATHS)
def test_a_blank_document_gives_one_empty_finding(document: str, blank: str) -> None:
    texts = clean_texts()
    texts[document] = blank

    assert check_documents(texts) == [_finding(document, "empty")]


def _without_section(document: str, name: str, *, fenced: bool) -> dict[str, str | None]:
    fence = f"{FENCE}\n## {name}\n{FENCE}" if fenced else ""
    if document == OPERATOR_GUIDE:
        kept = [section for section in OPERATOR_GUIDE_SECTIONS if section != name]
        return _with(operator=operator_guide(sections=kept, suffix=fence))
    kept = [section for section in PROJECT_GUIDE_SECTIONS if section != name]
    return _with(project=project_guide(sections=kept, suffix=fence))


REQUIRED_SECTIONS = [(OPERATOR_GUIDE, name) for name in OPERATOR_GUIDE_SECTIONS] + [
    (PROJECT_GUIDE, name) for name in PROJECT_GUIDE_SECTIONS
]


@pytest.mark.parametrize(("document", "name"), REQUIRED_SECTIONS)
def test_an_absent_required_section_is_a_finding_for_that_name_only(
    document: str, name: str
) -> None:
    texts = _without_section(document, name, fenced=False)

    assert check_documents(texts) == [_finding(document, f"section '{name}' is missing")]


@pytest.mark.parametrize(("document", "name"), REQUIRED_SECTIONS)
def test_a_required_heading_only_inside_a_code_fence_does_not_count(
    document: str, name: str
) -> None:
    texts = _without_section(document, name, fenced=True)

    assert check_documents(texts) == [_finding(document, f"section '{name}' is missing")]


@pytest.mark.parametrize(
    "replacement",
    [
        f"{FENCE}\n| `fetch-failed` | health status and factory log |\n{FENCE}",
        "| fetch-failed | health status and factory log |",
        "`fetch-failed` goes to the health status and the factory log.",
        "  | `fetch-failed` | health status and factory log |",
    ],
    ids=["fenced", "no-backticks", "prose", "indented"],
)
def test_a_stop_without_its_table_row_is_a_finding(replacement: str) -> None:
    texts = _with(operator=operator_guide(without_stop="fetch-failed", suffix=replacement))

    assert check_documents(texts) == [
        _finding(OPERATOR_GUIDE, "stop 'fetch-failed' has no table row with its destination")
    ]


@pytest.mark.parametrize("row", STOP_TABLE, ids=lambda row: row.id)
def test_every_stop_without_its_table_row_is_a_finding(row: StopRow) -> None:
    texts = _with(operator=operator_guide(without_stop=row.id))

    assert check_documents(texts) == [
        _finding(OPERATOR_GUIDE, f"stop '{row.id}' has no table row with its destination")
    ]


@pytest.mark.parametrize(
    ("stop", "row", "found"),
    [
        ("fetch-failed", "| `fetch-failed` | pull request |", True),
        ("duplicate", "| `duplicate` | health status |", True),
        ("later-stage-in-backlog-file", "| `later-stage-in-backlog-file` | pull request |", True),
        ("fetch-failed", "| `fetch-failed` | Health Status |", False),
        ("duplicate", "| `duplicate` | Pull Request |", False),
        ("later-stage-in-backlog-file", "| `later-stage-in-backlog-file` | No Stop |", False),
    ],
)
def test_a_stop_row_needs_its_destination_in_words_in_any_case(
    stop: str, row: str, found: bool
) -> None:
    texts = _with(operator=operator_guide(without_stop=stop, extra_rows=[row]))

    expected = (
        [_finding(OPERATOR_GUIDE, f"stop '{stop}' has no table row with its destination")]
        if found
        else []
    )
    assert check_documents(texts) == expected


@pytest.mark.parametrize(
    "replacement",
    ["| commit-push | tick |", "`commit-push` dies in the tick."],
    ids=["no-backticks", "prose"],
)
def test_a_kill_point_case_without_its_table_row_is_a_finding(replacement: str) -> None:
    texts = _with(project=project_guide(without_case="commit-push", suffix=replacement))

    assert check_documents(texts) == [
        _finding(PROJECT_GUIDE, "kill point case 'commit-push' has no table row")
    ]


@pytest.mark.parametrize("case", KILL_POINT_CASES, ids=lambda case: case.id)
def test_every_kill_point_case_without_its_table_row_is_a_finding(case: KillPointCase) -> None:
    texts = _with(project=project_guide(without_case=case.id))

    assert check_documents(texts) == [
        _finding(PROJECT_GUIDE, f"kill point case '{case.id}' has no table row")
    ]


@pytest.mark.parametrize(
    "replacement",
    [f"| 7 | {PATH_7_TEST} |", f"Path 7 is walked by `{PATH_7_TEST}`."],
    ids=["no-backticks", "prose"],
)
def test_a_fault_path_without_a_row_naming_its_test_is_a_finding(replacement: str) -> None:
    texts = _with(project=project_guide(without_path=7, suffix=replacement))

    assert check_documents(texts) == [_finding(PROJECT_GUIDE, PATH_7_FINDING)]


@pytest.mark.parametrize("path", FAULT_PATHS, ids=lambda path: str(path.number))
def test_every_fault_path_without_a_row_naming_its_test_is_a_finding(path: FaultPath) -> None:
    texts = _with(project=project_guide(without_path=path.number))

    assert check_documents(texts) == [
        _finding(
            PROJECT_GUIDE,
            f"fault-injection path {path.number} has no table row naming '{path.test}'",
        )
    ]


def test_the_replaced_phrases_are_the_nine_in_their_order() -> None:
    assert REPLACED_PHRASES == (
        "--follow",
        "factory-last-line",
        "tasks/.gitkeep",
        "factory-tick.lock",
        "factory-run.json",
        "recover_dirty_tree",
        "lease plus ten minutes",
        "local branch first",
        "run record",
    )


@pytest.mark.parametrize(
    ("written", "phrase"),
    [(phrase, phrase) for phrase in REPLACED_PHRASES] + [("Factory-Run.json", "factory-run.json")],
)
@pytest.mark.parametrize("document", TEXT_GUIDES)
def test_a_replaced_phrase_is_a_finding_for_its_document(
    document: str, written: str, phrase: str
) -> None:
    texts = clean_texts()
    texts[document] = _guide(document, suffix=f"It reads {written} here.")

    assert check_documents(texts) == [
        _finding(document, f"describes a replaced behaviour: '{phrase}'")
    ]


@pytest.mark.parametrize(
    ("line", "entry"),
    [
        ("A ticket is read.", "ticket"),
        ("A TICKET is read.", "ticket"),
        ("It reads the ticket.", "ticket"),
        ("It reads drafts/F0001-x.md first.", "drafts/"),
    ],
)
def test_a_v1_word_standing_alone_is_a_finding(line: str, entry: str) -> None:
    texts = _with(operator=operator_guide(suffix=line))

    assert check_documents(texts) == [_finding(OPERATOR_GUIDE, f"uses the v1 word '{entry}'")]


@pytest.mark.parametrize(
    "word",
    ["ticketing", "my-ticket", "_ticket", "ticket_1", "ticket1", "1ticket", "xticket", "ticket-x"],
)
def test_a_v1_word_inside_a_longer_word_is_no_finding(word: str) -> None:
    texts = _with(operator=operator_guide(suffix=f"It reads {word} here."))

    assert check_documents(texts) == []


EXEMPT_SECTIONS = [
    "## Replaced from v1\n\nNo --follow mode, and no ticket.",
    "## Replaced from v1\n\nNo --follow mode, and no ticket.\n\n## After\n\nClean text.",
    "## Replaced from v1\n\n### Older\n\nNo --follow mode, and no ticket.",
    f"## Replaced from v1\n\n{FENCE}\n## Inside\n{FENCE}\n\nNo --follow mode, and no ticket.",
]


@pytest.mark.parametrize(
    "section",
    EXEMPT_SECTIONS,
    ids=["to-the-end", "to-next-heading", "subheading", "fenced-heading"],
)
@pytest.mark.parametrize("document", TEXT_GUIDES)
def test_the_replaced_section_is_exempt_from_both_lists(document: str, section: str) -> None:
    texts = clean_texts()
    texts[document] = _guide(document, suffix=section)

    assert check_documents(texts) == []


@pytest.mark.parametrize(
    ("prefix", "suffix"),
    [
        ("No --follow mode, and no ticket.", "## Replaced from v1\n\nClean text."),
        ("", "## Replaced from v1\n\nClean text.\n\n## After\n\nNo --follow mode, and no ticket."),
        ("", f"{FENCE}\n## Replaced from v1\n{FENCE}\n\nNo --follow mode, and no ticket."),
    ],
    ids=["before", "after-next-heading", "fenced-replaced-heading"],
)
@pytest.mark.parametrize("document", TEXT_GUIDES)
def test_text_outside_the_replaced_section_is_checked(
    document: str, prefix: str, suffix: str
) -> None:
    texts = clean_texts()
    texts[document] = _guide(document, prefix=prefix, suffix=suffix)

    assert check_documents(texts) == [
        _finding(document, "describes a replaced behaviour: '--follow'"),
        _finding(document, "uses the v1 word 'ticket'"),
    ]


def test_the_decision_log_is_exempt_from_both_lists() -> None:
    texts = _with(decisions=decision_log(suffix="The --follow mode and the ticket are gone."))

    assert check_documents(texts) == []


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("# Decisions\n\nNothing decided yet.\n", True),
        (f"# Decisions\n\n{FENCE}\n## 001 One package\n{FENCE}\n", True),
        ("# Decisions\n\n## 001 One package\n", False),
    ],
    ids=["no-heading", "fenced-heading", "heading"],
)
def test_a_decision_log_needs_a_heading_outside_code_fences(text: str, found: bool) -> None:
    expected = [_finding(DECISION_LOG, "no decision recorded")] if found else []

    assert check_documents(_with(decisions=text)) == expected


def test_findings_follow_the_rule_order_and_the_list_order() -> None:
    sections = [name for name in OPERATOR_GUIDE_SECTIONS if name != "Install"]
    words = "A lane, another lane, a ticket, the factory-run.json and --follow."
    texts = _with(
        operator=operator_guide(sections=sections, without_stop="fetch-failed", suffix=words),
        project=project_guide(
            sections=[name for name in PROJECT_GUIDE_SECTIONS if name != "Kill points"],
            without_case="commit-push",
            without_path=7,
        ),
    )

    assert check_documents(texts) == [
        _finding(OPERATOR_GUIDE, "section 'Install' is missing"),
        _finding(OPERATOR_GUIDE, "stop 'fetch-failed' has no table row with its destination"),
        _finding(OPERATOR_GUIDE, "describes a replaced behaviour: '--follow'"),
        _finding(OPERATOR_GUIDE, "describes a replaced behaviour: 'factory-run.json'"),
        _finding(OPERATOR_GUIDE, "uses the v1 word 'ticket'"),
        _finding(OPERATOR_GUIDE, "uses the v1 word 'lane'"),
        _finding(PROJECT_GUIDE, "section 'Kill points' is missing"),
        _finding(PROJECT_GUIDE, "kill point case 'commit-push' has no table row"),
        _finding(PROJECT_GUIDE, PATH_7_FINDING),
    ]


def test_a_finding_is_a_closed_model() -> None:
    finding = _finding(README, "missing")
    field = "message"
    with pytest.raises(pydantic.ValidationError):
        setattr(finding, field, "empty")

    model: type[BaseModel] = DocumentFinding
    with pytest.raises(pydantic.ValidationError):
        model(document=README, message="missing", line=1)
