"""The block an opencode agent ends with: the instructions for it and its strict reading."""

import pytest

from factory.adapters.opencode_runtime import parse_result_block, result_instructions

ALLOWED = ["doing", "question"]
BLOCK = "<factory-result>\ndecision: doing\nentry:\nBuilt it.\n</factory-result>"


def test_the_result_instructions_name_the_allowed_decisions_and_the_entry() -> None:
    assert result_instructions(ALLOWED) == (
        "End your final message with this block, and nothing after it:\n"
        "<factory-result>\n"
        "decision: <one of: doing, question>\n"
        "entry:\n"
        "<your journal entry, without its number or your name: "
        "everything your instructions say the entry contains>\n"
        "</factory-result>"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param(BLOCK, ("doing", "Built it."), id="block"),
        pytest.param(f"Done.\nAll of it.\n{BLOCK}", ("doing", "Built it."), id="text-before"),
        pytest.param(f"{BLOCK}  \n\n", ("doing", "Built it."), id="trailing-whitespace"),
        pytest.param(
            BLOCK.replace("decision: doing", "decision:   doing  "),
            ("doing", "Built it."),
            id="spaces-around-decision",
        ),
        pytest.param(
            f"{BLOCK.replace('doing', 'question').replace('Built it.', 'Earlier.')}\n{BLOCK}",
            ("doing", "Built it."),
            id="later-of-two",
        ),
        pytest.param(f"{BLOCK}\nOne more thing.", None, id="text-after"),
        pytest.param(BLOCK.removesuffix("\n</factory-result>"), None, id="no-closing-line"),
        pytest.param(BLOCK.removeprefix("<factory-result>\n"), None, id="no-opening-line"),
        pytest.param(BLOCK.replace("decision: doing\n", ""), None, id="no-decision-line"),
        pytest.param(BLOCK.replace("entry:\n", ""), None, id="no-entry-line"),
        pytest.param(
            BLOCK.replace("decision: doing\nentry:", "entry:\ndecision: doing"),
            None,
            id="lines-in-other-order",
        ),
        pytest.param(BLOCK.replace("doing", "review"), None, id="decision-not-allowed"),
        pytest.param(BLOCK.replace("Built it.", "   "), None, id="blank-entry"),
    ],
)
def test_the_result_block_gives_its_decision_and_entry_only_when_it_ends_the_text_whole(
    text: str, expected: tuple[str, str] | None
) -> None:
    assert parse_result_block(text, ALLOWED) == expected
