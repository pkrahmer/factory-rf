---
stage: done
pr: 210
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# A standing leave to move a shared test helper

## Assignment (as of log entry 1)

v1.1's shakedown run of 2026-10-18 (the todo demo on `pkrahmer/factory-demo-todo`, the night log's rows of 08:21, 08:48 and 09:36 and its result section, findings 1 and 2) showed the cost of one rule. Every project's `CLAUDE.md` puts "change to a test you did not write" behind a question, and the reviewer counts a second copy of an existing helper as a finding. So a story whose new test needs a helper, a constant or a fixture that an earlier story's test module holds either copies it (a finding) or changes the earlier module (a question). Three of the eight stories paid a review round and often a question each time: $8.85 for three stories, about $6 above three clean passes. In F0002-S0003 the agents moved the helpers without asking, and nobody noticed. This story turns the human's answer of that run (the demo's F0001 decision 13) into a standing rule of the template's `CLAUDE.md`, the rules file every Python project starts from: a shared helper may be moved to one place under `tests/`, and the earlier tests changed to use it, without asking, as long as every earlier test keeps its name and checks the same thing. Any other change to a test another story wrote still needs the human's leave. The tester makes the move, never the coder. When the reviewer finds a copy, the coder hands the move to the tester by ending with `tests` (FEATURE decisions 1 to 3). The shipped tester and coder get one lesson each to match, and the tester's lesson on earlier tests is rewritten to name the new leave. The tester changes two tests of earlier stories by the human's leave (FEATURE decision 9). Nothing under `src/` changes.

## Interface

`template/CLAUDE.md`, two changes and no other.

The last bullet of `## Not without asking (end the stage with `question`)`, today

```text
- New dependency, new top-level package, change to `factory/`, change to a test you did not write, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
```

becomes exactly

```text
- New dependency, new top-level package, change to `factory/`, change to a test you did not write beyond the standing leave under *Tests*, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
```

and `## Tests` gains one bullet at its end, after the bullet that starts `- A test that waits for a time limit`, one line in the file:

```text
- The standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier test module still holds as a copy of a shared one, may be moved to one shared place under `tests/` (a module at its root, or `tests/conftest.py` for a fixture), and the earlier tests that held it changed to use it from there, without asking, as long as every earlier test keeps its name and checks the same thing. The tester makes the move, never the coder, and its entry names each earlier test file it changed. Any other change to a test another story wrote still needs the human's leave.
```

`claude/agents/tester.md`, `## Lessons`: the bullet

```text
- You change a test another story wrote only when the story names that test and the human has given their word; you make that change, the coder never does.
```

is replaced by these two bullets, in this order and in its place (before the time-limit bullet, which stays last), each one line in the file:

```text
- You change a test another story wrote only when the story names that test and the human has given their word, or to move a shared test helper under a standing leave that `CLAUDE.md` gives; you make that change, the coder never does, and your entry names each earlier test file you changed and the leave for it.
- When the prompt says `Mode: a test change the human approved` and the coder's entry names a move of a shared test helper under that standing leave instead of an answer of the human's, make exactly that move, as step 0 of the stage says for an approved change.
```

`claude/agents/coder.md`, `## Lessons`: one bullet at its end, after the bullet that starts `- You never change a test`, one line in the file:

```text
- A reviewer's finding of a copied test helper is a change to tests: when `CLAUDE.md` gives a standing leave to move a shared test helper, end with `tests` and an entry naming the move (the helper, the shared place, the earlier test files), and the tester makes it; without that leave, it is a question.
```

Nothing else in the three files changes: no `## Rules`, `## Role` or `## Stage` text, no other bullet. `src/factory/domain/prompts.py` and its `Mode: a test change the human approved; ...` line stay as they are (FEATURE decision 2). The intake agent stays as it is (FEATURE decision 3).

Tests, by the human's leave (FEATURE decision 9), and no other change to an earlier story's test:

- `tests/test_claude_files.py` (F0010-S0012; changed since by F0012-S0028 and F0012-S0029): in `TEMPLATE_RULES_LINES`, the line of the `Not without asking` bullet becomes the new text above, and the standing-leave bullet is added as a new item after the time-limit bullet, before the empty line that ends `## Tests`. `test_template_rules_file_is_the_python_project_text` itself stays as it is.
- `tests/test_claude_agent_texts.py` (F0010-S0017; changed since by F0012-S0011 and F0012-S0028): in `LESSONS`, the `tester` list has the two new bullets in place of the old one, so that it reads: the first lesson, the second lesson, the both-sides bullet, the test-data bullet, the two new bullets, `_TIME_LIMIT_LESSON`. The `coder` list gains the new coder bullet as its last entry. `test_lessons_section_is_last_and_holds_exactly_the_role_bullets` itself stays as it is.

## Acceptance criteria

1. `template/CLAUDE.md` is the text of `TEMPLATE_RULES_LINES` with the new `Not without asking` line and with the standing-leave bullet as the last bullet of `## Tests`: the existing `test_template_rules_file_is_the_python_project_text`.
2. The `## Lessons` section of `tester` holds exactly the bullets of the Interface, in the order the Interface gives: the old bullet on earlier tests is gone, the two new bullets stand in its place, and the time-limit bullet is still last. The existing `test_lessons_section_is_last_and_holds_exactly_the_role_bullets`, row `tester`.
3. The `## Lessons` section of `coder` ends with the new bullet, after the bullet that starts `- You never change a test`: the same test, row `coder`.
4. The `## Lessons` sections of the other five agents are unchanged: the same test, its other five rows.
5. What must still hold: every other test of `tests/test_claude_agent_texts.py`, `tests/test_claude_files.py` and `tests/adapters/test_shipped_agents_effect.py` passes. The new bullets use no word the rename table replaces (`test_body_uses_no_word_the_rename_table_replaces`), the coder's body still holds both phrases of `test_coder_sends_a_wrong_test_back_to_the_tester`, and each body keeps its sections in order.
6. `make check` stays green.
7. docs: the project guide, section *The shipped agents, settings and template*, says in *The template*, in the bullet on `template/CLAUDE.md`, that the file gives a standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier module still holds as a copy, may be moved to one shared place under `tests/`, and the earlier tests changed to use it, without asking, as long as every earlier test keeps its name and checks the same thing; the tester makes the move, never the coder; any other change to another story's test still needs the human's leave. In *The seven agents*, the `## Lessons` bullet names the tester's two lessons on earlier tests (the standing leave, and the move a coder's entry names in the mode `a test change the human approved`) and the coder's last lesson (a reviewer's finding of a copied test helper goes to the tester with `tests`), and says that `tester` still ends with the time-limit lesson. The decision log gets an entry, "A standing leave to move a shared test helper". It gives the reason: at the shakedown of 2026-10-18 on the todo demo, three of eight stories paid review rounds and questions for copied test helpers ($8.85 for the three, about $6 above three clean passes), and in one of them the agents moved the helpers without asking and nobody noticed. It gives the rule's bounds (only a move of a shared helper, every earlier test keeping its name and what it checks; anything else still asks; the tester alone makes it) and the rejected alternatives with their reasons: a question every time (the cost above); the coder making the move (the coder never edits tests); a leave for any refactoring of earlier tests (too wide to judge "checks the same thing"); the leave in the shipped agents alone (it is a project's rule, and `CLAUDE.md` is where the project says what needs asking); and a new prompt line for the tester (FEATURE decision 2). No other document changes, no word that the document check refuses is used outside a `## Replaced from v1` section, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "standing leave" template/CLAUDE.md claude/agents/tester.md claude/agents/coder.md
```
Expect: three lines, in this order: `template/CLAUDE.md:2`, `claude/agents/tester.md:2` and `claude/agents/coder.md:1`.

```bash
grep -c "the story names that test and the human has given their word; you make that change" claude/agents/tester.md
```
Expect: `0` (the old bullet is gone).

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_claude_files.py tests/test_claude_agent_texts.py tests/adapters/test_shipped_agents_effect.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-18 human: created.
2. intake: accepted
   - Interface: names concrete files (`template/CLAUDE.md`, `claude/agents/tester.md`, `claude/agents/coder.md`) with the exact old and new text, position and order of every bullet, and the two constants of the earlier tests to change (`TEMPLATE_RULES_LINES`, `LESSONS`). Nothing is left to decide, and it states no behaviour that lacks a criterion.
   - Criteria: 1 to 4 are each decided by an existing test (`test_template_rules_file_is_the_python_project_text`, `test_lessons_section_is_last_and_holds_exactly_the_role_bullets` by row). The failing side of each rule is covered: the old tester bullet must be gone (criterion 2), the other five agents must be unchanged (criterion 4), and the time-limit bullet must stay last. Criterion 5 pins what must still hold, 6 is `make check`, and 7 is the docs criterion with its content spelled out.
   - Demo: three runnable commands, and each `Expect:` line is checkable (grep counts 2/2/1, count 0, pytest with only passed).
   - Architecture: text-only change to the template and shipped agents. Nothing under `src/` changes, and no layer is touched.
   - Scope: within FEATURE findings 1 and 2 and decisions 1 to 3 and 9. The earlier-test changes are named and carry the human's leave (decision 9). The prompt line and the intake agent stay as they are, as the FEATURE's out-of-scope list says.
3. tester: Changed the expected texts in two earlier tests, by the human's leave (FEATURE decision 9) and exactly as the Interface says. I added no new test function: every criterion is checked by an existing test that the story names.
   - `tests/test_claude_files.py`: in `TEMPLATE_RULES_LINES`, the `Not without asking` line now reads "... change to a test you did not write beyond the standing leave under *Tests*, ...". The standing-leave bullet is added after the time-limit bullet, before the empty line that ends `## Tests`. I did not touch the test function itself.
   - `tests/test_claude_agent_texts.py`: in `LESSONS["tester"]`, the old bullet on earlier tests is replaced, in its place, by the two new bullets. `_TIME_LIMIT_LESSON` stays last. `LESSONS["coder"]` gains the copied-test-helper bullet as its last entry. I did not touch the test function itself.
   I checked each new string against the Interface text by printing the joined constants; they match word for word.

   Criterion to test:
   - criterion 1: tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text
   - criterion 2: tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[tester]
   - criterion 3: tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[coder]
   - criterion 4: the same test, rows intake, reviewer, documenter and the other two agents (unchanged, still green)
   - criterion 5: the other tests in tests/test_claude_agent_texts.py, tests/test_claude_files.py and tests/adapters/test_shipped_agents_effect.py (unchanged)
   - criterion 6: `make check`, checked by the factory
   - criterion 7: docs, for the documenter stage; no test

   Files created: none. Files changed: the two above.

   `make test` run: exactly three tests fail, because the shipped files still hold the old text: `test_lessons_section_is_last_and_holds_exactly_the_role_bullets[coder]`, `[tester]` and `test_template_rules_file_is_the_python_project_text`. Every import worked; nothing is missing. `make lint` is green.

   For the coder: edit `template/CLAUDE.md`, `claude/agents/tester.md` and `claude/agents/coder.md` to the Interface text. Nothing under `src/` changes.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text
4. coder: Changed the three shipped texts to the Interface wording, and nothing else. Commit 0bbe1608.
      - `template/CLAUDE.md`: the `Not without asking` bullet now says "... change to a test you did not write beyond the standing leave under *Tests*, ...". The standing-leave bullet is added as the last bullet of `## Tests`, after the time-limit bullet.
      - `claude/agents/tester.md`, `## Lessons`: the old bullet on earlier tests is replaced, in the same place, by the two new bullets. The time-limit bullet is still last.
      - `claude/agents/coder.md`, `## Lessons`: the bullet on copied test helpers is added at the end, after `- You never change a test`.
      Main decision: I applied each change as an exact string replacement that must match once, so no other text could move. I considered editing by hand and rejected it, because each bullet has to match the tests' constants word for word.
      Nothing under `src/` changed. Refactor pass: the diff is three text edits, so there was nothing to refactor.
      Checks: the demo grep prints 2/2/1. The three named test modules all pass. `make check` is green (check: green).
      Docs for the documenter (criterion 7) are still to do: the project guide and the decision-log entry.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: No findings.
      - Acceptance criteria: I checked the diff word for word against the Interface. In `template/CLAUDE.md`, the `Not without asking` line is the exact new text, and the standing-leave bullet is the last bullet of `## Tests`, after the time-limit bullet. In `claude/agents/tester.md`, the old bullet on earlier tests is replaced in its place by the two new bullets, and `_TIME_LIMIT_LESSON` is still last. In `claude/agents/coder.md`, the new bullet comes last, after `- You never change a test`. No other line in the three files changes.
      - Tests: the tester changed only the constants the Interface names. `TEMPLATE_RULES_LINES` in `tests/test_claude_files.py` has the new `Not without asking` line and the new bullet before the empty line that ends `## Tests`. `LESSONS["tester"]` and `LESSONS["coder"]` in `tests/test_claude_agent_texts.py` match the Interface. Neither test function changed. These constants pin criteria 1 to 4: the two exact-text tests leave no room for the old tester bullet to stay or for another agent's lessons to drift. The coder's entry reports `make check` green and `duplicates: 0 new`.
      - Architecture and security: text files and test constants only. Nothing under `src/` changes, and the diff adds no markers or secrets.
      - Quality and ticket hygiene: the log gives the coder's main decision (exact single-match replacements) and what it rejected. `Assignment` matches what was built. Criterion 7 still describes what the documenter must write.
6. documenter: Docs written for criterion 7. Only documents changed, so I did not run `make check`; the factory runs it next. `python -m factory.entry.check_documents` prints `documents ok`.
   - `docs/project-guide.md`: in *The template*, the `template/CLAUDE.md` bullet now states the standing leave and its bounds. In *The seven agents*, the `## Lessons` bullet names the tester's two lessons on earlier tests and the coder's last lesson, and says `tester` still ends with the time-limit lesson.
   - `docs/decisions.md`: new entry "A standing leave to move a shared test helper", with the reason ($8.85 for three stories, about $6 above clean passes), the bounds, and the five rejected alternatives with their reasons.
   Cross-read against the diff: the text of the three shipped files matches the Interface, and the rest of the project guide's section on the agents and template is current. I read no other document. No findings, and I saw nothing stale that is unrelated to this story.

   `make check`: check: green
   `make documents`: documents ok
7. demo: Demo run from the repository root. Each command was run as written, in order. Every command met its `Expect:` line. No findings.

   1. `grep -c "standing leave" template/CLAUDE.md claude/agents/tester.md claude/agents/coder.md`
   ```text
   template/CLAUDE.md:2
   claude/agents/tester.md:2
   claude/agents/coder.md:1
   ```
   Met: three lines in the expected order, with counts 2, 2 and 1.

   2. `grep -c "the story names that test and the human has given their word; you make that change" claude/agents/tester.md`
   ```text
   0
   ```
   Met: the old tester bullet is gone.

   3. `uv run pytest --no-header -p no:cacheprovider tests/test_claude_files.py tests/test_claude_agent_texts.py tests/adapters/test_shipped_agents_effect.py`
   ```text
   ........................................................................ [ 48%]
   ........................................................................ [ 96%]
   .....                                                                    [100%]
   149 passed in 0.57s
   ```
   Met: the last line is `149 passed`, with no failed, error or skipped count.

   Criteria check against the demo:
   - Criteria 1 to 5: the exact-text tests and the other tests of the three modules pass.
   - Criterion 6: the documenter's run reports `make check` green. The factory runs the gate again.
   - Criterion 7: `docs/decisions.md:506` has the entry "A standing leave to move a shared test helper". The `template/CLAUDE.md` bullet in the project guide (`docs/project-guide.md:1384`) states the leave and its bounds.
   - Scope: the branch diff touches only the three shipped texts, the two named test modules, the two documents and the ticket. Nothing under `src/` changes.

   Nothing contradicts a criterion. Nothing is open.
8. done (pull request merged); cost: 6 runs, 3.9 min, 31 turns, 139k tokens in (336k more from cache), 10k out, $1.15
