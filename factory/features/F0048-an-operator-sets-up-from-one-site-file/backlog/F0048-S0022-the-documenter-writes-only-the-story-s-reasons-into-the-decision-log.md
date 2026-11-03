# The documenter writes only the story's reasons into the decision log

<!-- proposed by feature acceptance of 2026-11-03; refine before starting -->

## Description

F0048-S0019's documenter wrote seven decision log entries with "Why" and "Rejected" lines it read from the scripts and the operator guide. Five of the rejected options were named by no decision and no journal, and later agents cite the log as the human's reasons (R4). Decision 27 of F0048 says the decision log holds only the human's reasons, and F0048-S0021 repaired those entries one by one. The rule itself is written nowhere an agent reads it: the shipped `claude/agents/documenter.md` says what to write and where, but not where a decision entry's reasons come from, and its stage forbids it to read `feature.md`. So the next feature's documenter can do the same again. This story adds one lesson to the shipped documenter: a "Why" or a "Rejected" in `docs/decisions.md` comes from the story itself (its Description, Interface, docs criterion or journal, where the human's answers stand), never from the documenter's own reading of the code. Where the story names no rejected option, the entry has no "Rejected" line, and the documenter's journal entry names the entry that lacks one. The other lessons, the role and the stage of the documenter stay as they are, and no other agent's text changes. Existing entries of the log stay as they are.

## Interface

- `claude/agents/documenter.md`, `## Lessons`: one new bullet, placed after the bullet on the project guide's size ("The project guide is an index plus one file for each domain ...") and before the temporary-directory bullet, so that the documents-only lesson stays last. Its text, word for word:

  ```text
  - In `docs/decisions.md`, write a "Why" or a "Rejected" only from what the story names: its Description, its Interface, its docs criterion and its journal, where the human's answers stand. Never add a reason or a rejected option of your own reading of the code or the documents. When the story names no rejected option for an entry, write no "Rejected" line, and name that entry in your journal entry.
  ```

- No module under `src/factory/` changes. The template's pipeline definition and the other six shipped agents stay as they are.
- `tests/test_claude_agent_texts_decision_log.py` (new) pins the bullet in the documenter's `## Lessons` section (`section_text(agent_body("documenter"), "Lessons")`, as `tests/test_claude_agent_texts_review_leave.py` does), its place between the two bullets named above, and its absence from every other shipped agent (`SHIPPED_NAMES` of `tests/shipped_agents.py`).

## Acceptance criteria

1. The `## Lessons` section of `claude/agents/documenter.md` holds the bullet of the Interface word for word; a body without it fails the test.
2. The bullet stands directly after the project guide's bullet and directly before the temporary-directory bullet, and the documents-only bullet is still the section's last; a body with the bullet elsewhere in the section fails the test.
3. No other shipped agent (`intake`, `tester`, `coder`, `reviewer`, `smoke-tester`, `acceptance-reviewer`) holds the bullet: one parametrized test, a row for each agent, the documenter's row holding it and the six others not.
4. `make check` stays green.
5. docs: `docs/decisions.md`: one entry for the rule (decision 27 of F0048: the decision log holds only the human's reasons), with S0019's five unsourced "Rejected" options as its reason and the rejected alternative of letting the documenter read `feature.md` (its stage keeps it to the story). `docs/project-guide/agents.md`: the paragraph on the `## Lessons` sections names the new documenter lesson. `README.md` and the operator guide: none, since they say nothing about the agents' lessons.

## Smoke test

```bash
grep -c 'write a "Why" or a "Rejected" only from what the story names' claude/agents/documenter.md
```
Expect: `1`

```bash
grep -l 'write a "Why" or a "Rejected" only from what the story names' claude/agents/*.md
```
Expect: one line, `claude/agents/documenter.md`

```bash
uv run pytest tests/test_claude_agent_texts_decision_log.py 2>&1 | tail -1
```
Expect: a line that ends `passed` with no `failed` in it, for example `8 passed in 0.31s`

## Journal
