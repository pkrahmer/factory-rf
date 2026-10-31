# Answering the factory

The factory posts on a work item's pull request when it needs the human. Each post ends with `<!-- factory key=<id>:<kind>:<n> -->`. Your answer is a plain comment on the same pull request, written after the post; it is what the factory reads on its next tick. A comment written before the post ends no wait.

## By kind

- **`question`** (a stage asks): read the question, every journal entry it names (`git show origin/work-item/<id>:<the work item's path>`), the story's Interface and criteria, and the code it is about. Answer each numbered point by its number. When the asker offers options and recommends one that fits the decisions, say "(a), as you propose" and add only what it needs.
- **`round_cap`** (sent back more times than the cap): read the review rounds. If each round found something real and the story converges, answer "Go on" and fold the remaining findings into the answer, so that the next round is the last: name the exact fix, the test rows, and that from now on the review sends back only for a criterion without a test or a failing test, further edge cases becoming notes. If the rounds circle without progress, that is for the human.
- **`crash_cap`**, **`attempts_cap`**: read the factory's own lines about the crashes or attempts. A known cause (a restart, a fault fixed since) is answered "Go on, the cause was <...>". An unknown cause is for the human.
- **`stall`**, **`expiry`**, **`error`**: report to the human with the post's text; answer only when the cause is clear and the fix is yours (a file on `main`).
- **`send_back`**, **`correction`**, **`cost_table`**: information, no answer needed.

## What you may decide

- Within the feature's *Decisions* and the story's Interface: always (switch `answer` on or off).
- A fault in the story's own text that blocks the stage (for example a layer rule the Interface breaks, a smoke test that no longer fits the code): fix it in the answer and say so.
- A change outside every role's write paths that the stage needs (`pyproject.toml`'s per-file ignores, `.secrets.baseline`, `security/`): make it on `main` yourself, with the reason in the file and the commit, and name it in the answer: the stage merges `origin/main` at its next start.
- A leave to change an earlier test of another story: give it when the feature's decisions already imply it (for example a structural test that forbids what the feature decided), narrowly (the one module, the one import), with a row that keeps catching everything else.
- Beyond all that: switch `answer` on, your best answer marked **For the morning**; switch `answer` off, wait for the human.

## How to post

Write the answer to a temporary file and post it: `gh pr comment <n> --repo <owner/name> --body-file <file>`. Then log it.
