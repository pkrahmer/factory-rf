# The reviewer names every earlier test it sees changed

## Assignment (as of log entry 1)

At the shakedown of 2026-10-18 (the night log's row of 09:36 and its result section, finding 1), F0002-S0003 changed three test files of F0001's stories without asking. The changes were harmless helper moves, but the reviewer did not flag them and F0002's acceptance did not mention them. The rule "a test another story wrote only with the human's leave" was held by the agents' reading alone. This story gives the shipped reviewer a sixth checklist item, done in every review whatever group failed before it. The reviewer lists each test file that `main` already holds and the diff changes, renames or deletes, and gives for each the leave it was changed under. There are three: the standing leave to move a shared test helper that `CLAUDE.md` gives (S0001); the human's leave, by the story's text or by a journal entry; or no leave needed, when the change only adds tests. A change under none of them, or one beyond its leave, is a finding. The acceptance reviewer does not repeat the check over the whole feature; its check 6 gathers the reviewers' lists for the human and names an earlier test changed with no leave as a finding (FEATURE decisions 5 and 6). It starts after S0001 is merged (FEATURE decision 10). The tester adds three anchors to one test of an earlier story by the human's leave (FEATURE decision 9). Nothing under `src/` changes.

## Interface

`claude/agents/reviewer.md`, `## Role`, two changes and no other.

The sentence before the checklist, today

```text
Checklist, in this order. Stop at the first failing group and report it; do not pad the report.
```

becomes exactly

```text
Checklist, in this order. Stop at the first failing group of 1 to 5 and report it; do not pad the report. Item 6 is part of every review, whichever group failed.
```

and the checklist gains a sixth item after item 5 (**Work item hygiene**), one line in the file:

```text
6. **Earlier tests**: every test file that `main` already holds and the diff changes, renames or deletes (`git diff --name-status main...HEAD`, any status but `A`) was written by another story. Name each in your entry after the findings, or after `no findings`, one line each: its path and the leave it was changed under. That is the standing leave to move a shared test helper that `CLAUDE.md` gives, when the change only moves a helper, constant or fixture to the shared place and makes the earlier tests use it, every earlier test keeping its name and what it checks; or the human's leave, the story naming that test with the human's word, or the human's answer in the journal, by its entry number; or none needed, when the change only adds tests and leaves every test the file held as it was. A change under none of these, or beyond its leave, is a finding.
```

`claude/agents/acceptance-reviewer.md`, `## Role`: check 6, today

```text
6. **Decisions taken for the human.** `feature.md` may list them, and story journals record answers and defaults; gather them in one list for the human to accept or revisit.
```

becomes exactly (one line in the file)

```text
6. **Decisions taken for the human.** `feature.md` may list them, and story journals record answers and defaults; gather them in one list for the human to accept or revisit. Add the earlier tests the reviewers' entries name as changed, each with the leave it was changed under; an earlier test changed with no leave named is a finding.
```

Nothing else in the two files changes: the boundary and entry sentences, `## Rules`, `## Stage` and `## Lessons` stay as they are (FEATURE decision 5).

Tests, by the human's leave (FEATURE decision 9), and no other change to an earlier story's test: `tests/test_claude_agent_texts.py` (F0010-S0017): `ROLE_AND_STAGE_ANCHORS` gains two anchors for `reviewer`, `"Item 6 is part of every review, whichever group failed."` and `"6. **Earlier tests**: every test file that `main` already holds"` (the backticks around `main` as in the file), and one for `acceptance-reviewer`, `"Add the earlier tests the reviewers' entries name as changed"`. `test_role_and_stage_sections_carry_the_texts_of_the_role` itself stays as it is.

## Acceptance criteria

1. The `## Role` section of `reviewer` holds the new sentence before the checklist and the sixth item, as the Interface gives them: the existing `test_role_and_stage_sections_carry_the_texts_of_the_role`, row `reviewer`, with its two new anchors and its two old ones.
2. The `## Role` section of `acceptance-reviewer` holds the new sentence of check 6: the same test, row `acceptance-reviewer`, with its new anchor and its two old ones.
3. The old sentence before the checklist is gone: the reviewer's body does not hold `Stop at the first failing group and report it`. A new test, `test_the_reviewer_no_longer_stops_before_the_earlier_tests`, in `tests/test_claude_agent_texts.py`.
4. What must still hold: every other test of `tests/test_claude_agent_texts.py`, `tests/test_claude_files.py` and `tests/adapters/test_shipped_agents_effect.py` passes. The new text uses no word the rename table replaces, the bodies keep their sections in order, both bodies still open with their boundary and entry sentences, and their `## Lessons` sections are unchanged.
5. `make check` stays green.
6. docs: the project guide, section *The shipped agents, settings and template*, *The seven agents*, says that the reviewer's checklist has a sixth item of v1.1's own, *Earlier tests*, done in every review: the reviewer lists each test file that `main` holds and the diff changes, renames or deletes, with the leave for each (the standing leave of `CLAUDE.md`, the human's leave, or none needed when tests are only added), and a change under none of them is a finding. It says that the acceptance reviewer's check 6 gathers those lists, and that these two passages and the sentence before the reviewer's checklist are v1.1's text, not v1's, so the sentence that v1's texts are renamed but not rewritten names them as the exception. The operator guide, where it says what the human reads at the approval, gets one sentence: the reviewer's entry, shown under *Review* in the pull request's description, ends with the earlier tests the story changed and the leave for each. The decision log gets an entry, "The reviewer names every earlier test the diff changes", with the reason (at the shakedown of 2026-10-18 on the todo demo, one story changed three earlier test files unasked, and neither its reviewer nor the feature's acceptance said so) and the rejected alternatives with their reasons: a check in code (the factory can list the files but cannot judge whether a test still checks the same thing); the same diff check over the whole feature by the acceptance reviewer (it repeats every reviewer's reading at every acceptance, for what the reviewers' lists already give); and a change of the reviewer's entry sentence (FEATURE decision 5). No other document changes, no word that the document check refuses is used outside a `## Replaced from v1` section, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "Earlier tests" claude/agents/reviewer.md claude/agents/acceptance-reviewer.md
grep -c "earlier tests the reviewers' entries name" claude/agents/acceptance-reviewer.md claude/agents/reviewer.md
```
Expect: `claude/agents/reviewer.md:1` and `claude/agents/acceptance-reviewer.md:0`; then `claude/agents/acceptance-reviewer.md:1` and `claude/agents/reviewer.md:0`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_claude_agent_texts.py tests/test_claude_files.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-18 human: created.
