---
stage: accept
pr: 178
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The lessons since F0010-S0017 in the shipped agents and the template

## Assignment (as of log entry 1)

The human decided on 2026-10-17 that what v1 learns while it builds v1.1 must also reach what v1.1 ships, so that a new project (first the todo demo) starts with it. F0010-S0017 put the lessons of `planning/lessons-for-the-skills.md` known on 2026-10-16 into the `## Lessons` sections of the seven agents under `claude/agents/`, and F0010-S0012 put its Python rows into `template/CLAUDE.md`. Three rows came after F0010-S0017 and are in neither:

- "Give a long project command (`make check`, over two minutes) the shell tool's largest timeout" (general, every role, 2026-10-16): a second bullet in every agent, right after the first one, which it extends.
- "A stage whose change the factory checks right after it (the documenter's documents) does not run the same check itself" (general, documenter, 2026-10-17): the last bullet of `documenter`. It takes the place of step 3 of the documenter's stage text for a change of documents only; v1's stage text itself stays as it is.
- "A test that waits for a time limit leaves the started process room to start" (Python, tester, 2026-10-17): the last bullet of `tester`, and, because its kind is Python, a bullet of the *Tests* section of `template/CLAUDE.md`, after the bullet on low-entropy test values.

The project rows stay out. The Python row on mutation testing (2026-10-17, H5) belongs to the template's *Checks* beside `make mutants`, which the template gets only with S0029, so S0029 carries it. S0011 adds two lessons of its own (the temporary directory, the JUnit report) and this story does not repeat them; it starts after S0011 is merged, and its lists below include S0011's bullets. The agent texts and the template are in the coder's write paths. The two tests that pin these texts change by the human's leave (FEATURE decision 48).

## Interface

The new bullets, each one line in the file:

```text
- Give a project command that can take minutes, such as `make check`, the shell tool's largest timeout (600000 ms), so that the tool does not move it to the background.
```

```text
- When every file you changed is a document (`README.md` or a file under `docs/`), end without running `make check`, in place of step 3 of the stage: the factory runs the stage's checks right after you, and that run decides. When you changed any other file, run it as step 3 says.
```

```text
- A test that waits for a time limit gives the process it starts room to start: the tests may run on every core at once, so a child can need more than a second before it does anything. Give it a limit of a few seconds and an upper bound on the elapsed time with room above it; never check that a one-second limit is met to the tenth.
```

The `## Lessons` section of each body, after this story (the timeout bullet is the second everywhere; `[S0011]` marks the bullets S0011 added):

| Agent | Bullets in order |
|---|---|
| `intake` | foreground, timeout, the three of today |
| `tester` | foreground, timeout, the three of today, time limit |
| `coder` | foreground, timeout, the two of today |
| `reviewer` | foreground, timeout, the two of today |
| `documenter` | foreground, timeout, project guide, temporary directory [S0011], documents only |
| `smoke-tester` | foreground, timeout, temporary directory [S0011] |
| `acceptance-reviewer` | foreground, timeout, temporary directory [S0011], JUnit report [S0011] |

Nothing else in the seven bodies changes. `template/CLAUDE.md` gains the time-limit text as a bullet (`- A test that waits ...`, the same sentence as the agent's) at the end of its *Tests* section, after the bullet that starts `- Fake commit ids`; nothing else in it changes.

By the human's leave (FEATURE decision 48), and no other change to an earlier story's test:

- `tests/test_claude_agent_texts.py`: a constant `_SECOND_LESSON` with the timeout bullet, put second in every list of `LESSONS`; the time-limit bullet as the last entry of `tester`, the documents-only bullet as the last of `documenter`.
- `tests/test_claude_files.py`: the time-limit bullet in `TEMPLATE_RULES_LINES`, after the line that starts `- Fake commit ids`.

## Acceptance criteria

1. The `## Lessons` section of each of the seven agents holds exactly the bullets of the Interface's table, in that order: the timeout bullet second in all seven (the existing test over `LESSONS`).
2. The `## Lessons` section of `tester` ends with the time-limit bullet, and that of `documenter` with the documents-only bullet (the same test).
3. `template/CLAUDE.md` is the text of `TEMPLATE_RULES_LINES` with the time-limit bullet as the last bullet of *Tests* (the existing `test_template_rules_file_is_the_python_project_text`).
4. Every other test of `tests/test_claude_agent_texts.py`, `tests/test_claude_files.py` and `tests/adapters/test_shipped_agents_effect.py` still passes: the new bullets use no word the rename table replaces, and the bodies keep their sections in order.
5. `make check` stays green.
6. docs: in the project guide, section *The shipped agents, settings and template*, *The seven agents*, the `## Lessons` bullet says that the first two bullets (run make targets in the foreground; give a long one the shell tool's largest timeout) are in every body, and names the tester's time-limit lesson and the documenter's documents-only lesson; in *The template*, the bullet on `template/CLAUDE.md` names the time-limit lesson among the Python lessons it carries. No other document changes, no v1 word of the document check is used outside a `## Replaced from v1` section, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "the shell tool's largest timeout" claude/agents/*.md
```
Expect: seven lines, one for each file of `claude/agents/`, each ending in `:1`.

```bash
grep -c "room to start" claude/agents/tester.md template/CLAUDE.md claude/agents/coder.md
grep -c "every file you changed is a document" claude/agents/documenter.md claude/agents/tester.md
```
Expect: `claude/agents/tester.md:1`, `template/CLAUDE.md:1` and `claude/agents/coder.md:0`; then `claude/agents/documenter.md:1` and `claude/agents/tester.md:0`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_claude_agent_texts.py tests/test_claude_files.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: the three new bullets are given word for word, one line each. A table lists the exact bullet order of the seven `## Lessons` sections. The template gets the time-limit bullet at the end of *Tests*, after `- Fake commit ids`. The two test changes are named: `_SECOND_LESSON` in `LESSONS`, and the time-limit bullet in `TEMPLATE_RULES_LINES`.
   - Criteria: criteria 1 to 4 are each checked by an existing test (`LESSONS`, `test_template_rules_file_is_the_python_project_text`, the other tests in the three modules), so one test function can decide each. Criterion 5 is `make check`. Criterion 6 is the docs criterion and uses the document check.
   - Failing sides: the Interface states no limit, validation or rejected input. The bullets are text, and the exact-list comparison of `LESSONS` fails on a missing, extra or misordered bullet. The Demo also pins the negative cases: the time-limit bullet is not in `coder.md`, and the documents-only bullet is not in `tester.md`.
   - Demo: all three blocks are runnable (`grep -c`, `uv run pytest`). Each `Expect:` line gives exact counts or a last-line form that can be checked against the output.
   - Architecture: the change touches only `claude/agents/*.md` and `template/CLAUDE.md`, which are shipped text inside the coder's write paths. No layer or code is involved.
   - Scope: the story is inside F0012's "What v1.1 ships to new projects" item. The mutation-testing row is explicitly left to S0029, and S0011's bullets are assumed already merged. FEATURE decision 48 covers the human's leave to change the two tests.
3. tester: Changed the two existing tests the story names, as FEATURE decision 48 allows. No new test functions: criteria 1 to 4 are checked by tests that already exist.
   - criterion 1: tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets (parametrized over the seven agents). Added a new constant `_SECOND_LESSON` holding the timeout bullet word for word from the Interface. It is now second in all seven `LESSONS` lists, including smoke-tester's one-line list.
   - criterion 2: the same test. Added a new constant `_TIME_LIMIT_LESSON`, now the last entry of `tester`. The documents-only bullet is now the last entry of `documenter`. The list lengths now match the Interface's table: intake 5, tester 6, coder 4, reviewer 4, documenter 5, smoke-tester 3, acceptance-reviewer 4.
   - criterion 3: tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text. Added the time-limit bullet to `TEMPLATE_RULES_LINES` after the `- Fake commit ids` line, so it is the last bullet of *Tests*.
   - criterion 4: the other tests of tests/test_claude_agent_texts.py, tests/test_claude_files.py and tests/adapters/test_shipped_agents_effect.py. They are unchanged, and in this run they were not among the failures.
   - criteria 5 and 6: `make check` and the docs stage; no tests here.
   Files changed: tests/test_claude_agent_texts.py, tests/test_claude_files.py. No files created. No import failures: the two changed modules import fine, and the only failures are wrong results. In the `make test` run, these failed: the lessons test for documenter, smoke-tester and acceptance-reviewer (the last lines shown), and the template test. That is red for the right reason. `make lint` is green. I checked by evaluation that the three bullet strings match the Interface word for word. S0011's bullets were already in the agents and in `LESSONS`, so nothing else needed changing.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[acceptance-reviewer]
4. coder: Added the three lessons as the Interface states them. Commit 2abcfe0b.
   - `claude/agents/*.md` (all seven): the timeout bullet is now second in `## Lessons`, right after the foreground bullet. `claude/agents/tester.md` ends with the time-limit bullet and `claude/agents/documenter.md` with the documents-only bullet.
   - `template/CLAUDE.md`: the time-limit bullet comes right after `- Fake commit ids`, so it is the last bullet of *Tests*.
   - Each bullet is one line and matches the Interface word for word. These are the same strings as the tester's `_SECOND_LESSON`, `_TIME_LIMIT_LESSON` and `TEMPLATE_RULES_LINES`. Nothing else in the bodies or the template changed.
   - Design: I placed the bullets with a one-off script anchored on the first lesson line and on the `- Fake commit ids` line, so no other line could move. I did not hand-edit each file because it repeats the same work eight times. The script lived outside the repository and is deleted.
   - Tests: `tests/test_claude_agent_texts.py`, `tests/test_claude_files.py` and `tests/adapters/test_shipped_agents_effect.py` all pass, and `make check` is green.
   - Refactor: nothing to change. The diff is ten added text lines with no code.
   - Open: the docs criterion (6) is for the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: No findings.
   - Acceptance criteria: all four criteria are covered by tests that already existed. Criteria 1 and 2 are covered by `tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets`, which compares each agent's whole `LESSONS` list. Criterion 3 is covered by `tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text`. Criterion 4 is covered by the other tests in the three modules. The coder's entry records `make check` as green.
   - Test changes: the tester changed only what the Interface names under FEATURE decision 48. That is `_SECOND_LESSON`, now second in all seven lists; `_TIME_LIMIT_LESSON`, last in `tester`; the documents-only bullet, last in `documenter`; and the time-limit line in `TEMPLATE_RULES_LINES` after `- Fake commit ids`. No other test was changed.
   - Shipped text: I read `claude/agents/*.md` and `template/CLAUDE.md` in the diff against the Interface. Each new bullet is one line and matches the Interface word for word. The bullet order in each `## Lessons` section matches the table (intake 5, tester 6, coder 4, reviewer 4, documenter 5, smoke-tester 3, acceptance-reviewer 4). The template bullet is the last bullet of *Tests*. No other line in the bodies or the template changed.
   - Failing sides: the Interface states no limit or rejected input. Because the test compares the whole list exactly, a missing, extra or misplaced bullet fails it.
   - Architecture, security, quality: the change is shipped text and test constants only. There is no code under `src/`, no suppression marker and no new dependency. Inlining the documents-only bullet, which is used once, matches how the other single-use lessons are written.
   - Ticket hygiene: the Assignment matches what was built. The coder's log explains how the bullets were placed. Criterion 6 still says what the documenter must write in the project guide.
6. documenter: Changed only `docs/project-guide.md`, two edits in the section on the shipped agents, settings and template.
   - *The seven agents*, the `## Lessons` bullet: it now says the first two bullets (foreground, and the shell tool's largest timeout) are in every body. It names the tester's time-limit lesson and the documenter's documents-only lesson as their last bullets.
   - Same bullet: the old text said `documenter` ends with the temporary-directory lesson, which is no longer true. It now says `smoke-tester` and `acceptance-reviewer` end with it, and `documenter` carries it before its last bullet.
   - *The template*, the `template/CLAUDE.md` bullet: it now names the time-limit lesson among the Python lessons it carries.
   - Cross-read: the diff of `claude/agents/*.md`, `template/CLAUDE.md` and the two tests matches the Interface word for word. No other document mentions the lessons.
   - I ran `python -m factory.entry.check_documents`: it prints `documents ok`.
   - I did not run `make check`, because I changed only documents; the factory runs it next.
   - No code findings.
   - Stale but not touched: the same bullet says `acceptance-reviewer` "ends with" the temporary-directory lesson, and the next sentence says it ends with the JUnit lesson. That wording was there before this story, and I left it as it was.

   `make check`: check: green
   `make documents`: documents ok
7. demo: I ran the three Demo blocks from the repository root, in order. All three met their `Expect:` lines and I found nothing wrong.

   1. `grep -c "the shell tool's largest timeout" claude/agents/*.md`
   ```
   claude/agents/acceptance-reviewer.md:1
   claude/agents/coder.md:1
   claude/agents/documenter.md:1
   claude/agents/intake.md:1
   claude/agents/reviewer.md:1
   claude/agents/smoke-tester.md:1
   claude/agents/tester.md:1
   ```
   Met: seven lines, one for each agent, each ending in `:1`.

   2. `grep -c "room to start" claude/agents/tester.md template/CLAUDE.md claude/agents/coder.md`, then `grep -c "every file you changed is a document" claude/agents/documenter.md claude/agents/tester.md`
   ```
   claude/agents/tester.md:1
   template/CLAUDE.md:1
   claude/agents/coder.md:0
   claude/agents/documenter.md:1
   claude/agents/tester.md:0
   ```
   Met: these are exactly the counts the Expect line asks for.

   3. `uv run pytest --no-header -p no:cacheprovider tests/test_claude_agent_texts.py tests/test_claude_files.py`
   ```
   ........................................................................ [ 63%]
   ..........................................                               [100%]
   114 passed in 0.08s
   ```
   Met: the last line is `114 passed`, with no failed, error or skipped count.

   Checked against the criteria:
   - Criteria 1 to 3: the passing tests compare the whole `LESSONS` lists and the whole template text.
   - Criterion 6: `uv run python -m factory.entry.check_documents` prints `documents ok`. The `## Lessons` bullet and the template bullet in `docs/project-guide.md` say what criterion 6 asks for.
   - The working tree was clean when I started.

   Not a finding, but worth fixing in a later story: one sentence in the project guide says `acceptance-reviewer` "ends with" the temporary-directory lesson, but its last bullet is the JUnit lesson. The documenter noted this wording was there before this story, and no criterion covers it.
