---
stage: ready
pr: null
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
