"""The operator's skill: what it tells the agent to do before anything else."""

from support.operator_support import ROOT

SKILL = ROOT / "operator" / "skill" / "kumpel" / "SKILL.md"
# The text after the first step of *Before anything*, through the loop, as it stands.
AFTER_FIRST_STEP = (
    "2. Read in the checkout: `CLAUDE.md`, `factory/pipeline.yml`, and the "
    "`feature.md` of every feature with a story in progress (`factory/featu"
    "res/*/in-progress/`). The feature's *Decisions* are what you may answe"
    "r within.\n"
    "3. Read `references/standing-orders.md`. It binds everything below.\n"
    "\n"
    "## The loop\n"
    "\n"
    "**The wait is always the only tool call of its message.** Calls in one"
    " message run in parallel, so a wait sent beside another call does not "
    "wait (it happened in the first trial).\n"
    "\n"
    "Repeat until the human stops you or the switches leave nothing to do:\n"
    "\n"
    "1. `sh scripts/status.sh` prints the state from GitHub: each open work"
    "-item pull request with its stage and what its newest comment is. Show"
    " the status bar (`references/standing-orders.md`) only when something "
    "changed since you last showed it.\n"
    "2. Act on what needs you, one thing at a time, by its kind:\n"
    "   - **A question, a cap, a send-back, a stall, an expiry or an error*"
    "* (`waits: <kind>`): `references/answering.md`. Switch `answer`.\n"
    "   - **An approval** (`stage:approval`, no verdict of yours yet): `ref"
    "erences/approving.md`. Switches `merge` and `start_next`.\n"
    "   - **A story archived and nothing in progress**: `sh scripts/next-st"
    "ory.sh` names the next story of the build order (`next: <id>`), or say"
    "s a work item is still in progress (`busy: <id>`) or that nothing is l"
    "eft (`none`). With `start_next` on, start the named story (`sh scripts"
    "/start-story.sh <id>`); otherwise tell the human it is ready.\n"
    "3. Post every comment with `sh scripts/comment.sh <n> <file>`, which s"
    "igns it; never another way.\n"
    "4. Log every act (`references/standing-orders.md`, *The log*).\n"
    "5. Wait: call `sh scripts/wait.sh 9` **as the only tool call of its me"
    "ssage**, with the shell tool's timeout set to 600000 ms. It returns on"
    "e line: `event: ...` (act on it, from step 1) or `continue: nothing ne"
    "w` (wait again). Calls in one message run in parallel, so a wait besid"
    "e another call would not wait.\n"
)


def first_step_and_rest() -> tuple[str, str]:
    """The first numbered step of *Before anything* and the text that follows it."""
    text = SKILL.read_text(encoding="utf-8")
    section = text[text.index("## Before anything") :]
    first = section[section.index("1. ") : section.index("\n2. ")]
    return first, section[section.index("\n2. ") + 1 :]


def test_the_first_step_names_the_site_file_and_the_rest_is_unchanged() -> None:
    first, rest = first_step_and_rest()

    assert "SITE_REPOSITORY" in first
    assert "SITE_CHECKOUT" in first
    assert "site file" in first
    assert rest.startswith(AFTER_FIRST_STEP)
