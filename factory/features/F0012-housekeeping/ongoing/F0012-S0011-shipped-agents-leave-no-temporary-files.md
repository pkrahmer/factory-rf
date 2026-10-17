---
stage: accept
pr: 163
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The shipped agents leave no temporary files and read the test times

## Assignment (as of log entry 1)

The disk filled twice in two days. Part of it was what agents and the session left in `/tmp`: about 150 clones with their `.venv`, 153 folders of `tempfile.mkdtemp()` examples, and 8.4 GB of pytest's own folders (the human's change H1 lets pytest keep only those of failed tests). The factory's own code makes no temporary file that it does not remove (FEATURE decision 24). What is left are the agents that run scripts outside the repository: the smoke tester, the acceptance reviewer and the documenter (who runs the examples it writes). Each of these three gets one more lesson at the end of its `## Lessons` section: make such files in a temporary directory that removes itself, and leave nothing in `/tmp`. The acceptance reviewer gets a second lesson: the JUnit report that `make test` now writes (H1) holds the time of every test; it reads it for its slow checks and its cost check, which is where the human's telemetry asks for it ("Telemetry in v1.1"). The agent texts are under `claude/agents/`, in the coder's write paths. The test that pins each agent's lessons changes by the human's leave (FEATURE decision 35).

## Interface

The bodies of `claude/agents/smoke-tester.md`, `claude/agents/acceptance-reviewer.md` and `claude/agents/documenter.md` each end their `## Lessons` section with the bullet

```text
- Make every file you need outside the repository in a temporary directory that removes itself: `tempfile.TemporaryDirectory()` in Python, or `d=$(mktemp -d)` followed by `trap 'rm -rf "$d"' EXIT` in the shell. Leave nothing behind in `/tmp` when you end.
```

and `claude/agents/acceptance-reviewer.md` adds, after it, the bullet

```text
- When `make test` writes a JUnit report (the `--junit-xml` file its `Makefile` names), read the time of each test from it, and name the slowest tests in the slow checks and in the cost.
```

Nothing else in the three files changes, and the other four agents do not change.

By the human's leave (FEATURE decision 35), and no other change to an earlier story's test: `LESSONS` in `tests/test_claude_agent_texts.py` gains the first bullet as the last entry of `documenter` and `smoke-tester`, and both bullets, in that order, as the last two of `acceptance-reviewer`.

## Acceptance criteria

1. The `## Lessons` section of `smoke-tester` and of `documenter` holds exactly its earlier bullets followed by the temporary-directory bullet of the Interface, and that of `acceptance-reviewer` its earlier bullet followed by the two bullets of the Interface, in that order (the existing test over `LESSONS`).
2. The lessons of `intake`, `tester`, `coder` and `reviewer` are unchanged (the same test).
3. Every other test of `tests/test_claude_agent_texts.py`, `tests/test_claude_files.py` and `tests/adapters/test_shipped_agents_effect.py` still passes: the new bullets use no word the rename table replaces, and the bodies keep their sections in order.
4. `make check` stays green.
5. docs: the project guide's section *The shipped agents, settings and template* names the two lessons and which agents carry them; the project guide's own example that makes a folder with `tempfile.mkdtemp()` (*The agent definition reader*) uses `tempfile.TemporaryDirectory()` instead, and the word `mkdtemp` occurs in none of `README.md`, `docs/operator-guide.md` and `docs/project-guide.md`. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -c "temporary directory that removes itself" claude/agents/smoke-tester.md claude/agents/acceptance-reviewer.md claude/agents/documenter.md claude/agents/coder.md
grep -c "mkdtemp" docs/project-guide.md docs/operator-guide.md README.md
```
Expect: four lines `claude/agents/smoke-tester.md:1`, `claude/agents/acceptance-reviewer.md:1`, `claude/agents/documenter.md:1` and `claude/agents/coder.md:0`; then three lines, each ending in `:0`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_claude_agent_texts.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names three concrete files under `claude/agents/` (each has a `## Lessons` section, checked) with the exact bullet texts, their order, and the `LESSONS` change in `tests/test_claude_agent_texts.py`; no behaviour is left unstated.
   - Criteria: 1 to 3 are each testable by the existing `LESSONS` test and the named modules; 2 covers the agents that must not change. The Interface has no limit or rejection rule, so no failing side is missing. Criterion 5 is checkable by grep (`mkdtemp` is now in `docs/project-guide.md` once, in README and operator guide zero) and by `check_documents`.
   - Demo: both blocks are runnable grep/pytest commands, and each `Expect:` line gives exact counts or a last-line form that can be checked.
   - Architecture: only agent texts (coder's write path `claude/*`) and docs change. No layer is touched.
   - Scope: inside F0012 scope item 1.4 ("no temporary files left", S0011) and FEATURE decisions 24 and 35; nothing in Out of scope.
3. tester: Changed `LESSONS` in `tests/test_claude_agent_texts.py`, the one earlier-story test the Interface allows to change (FEATURE decision 35). Nothing else in that file changed, and I created no new test files.
   - criterion 1: tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[smoke-tester|documenter|acceptance-reviewer]. A new constant `_TEMPORARY_DIRECTORY_LESSON` holds the Interface's first bullet word for word. It is the last entry for `documenter` and `smoke-tester`. For `acceptance-reviewer`, it is followed by the JUnit-report bullet.
   - criterion 2: the same test with [intake|tester|coder|reviewer]. Their `LESSONS` entries are unchanged.
   - criterion 3: the existing tests in tests/test_claude_agent_texts.py, tests/test_claude_files.py and tests/adapters/test_shipped_agents_effect.py, unchanged. The banned-word and section-order tests already cover the new bullets once they are in the bodies.
   - criteria 4 and 5: `make check` and the docs stage cover these; no test was written for them.
   `make test` result: as intended, only the three parametrized cases for smoke-tester, acceptance-reviewer and documenter fail, because the agent bodies under `claude/agents/` don't have the new bullets yet. There are no import errors. `make lint` is green.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_claude_agent_texts.py::test_lessons_section_is_last_and_holds_exactly_the_role_bullets[smoke-tester]
4. coder: Added the lessons to three agent texts. Commit 1f83114.
      - `claude/agents/smoke-tester.md`, `claude/agents/documenter.md` and `claude/agents/acceptance-reviewer.md` now each end `## Lessons` with the Interface's temporary-directory bullet, word for word. `acceptance-reviewer.md` also has the JUnit-report bullet after it. The `## Lessons` section was already last in all three files, so I added the bullets at the end of each file and changed nothing else. The other four agents are untouched.
      - Design: these are text-only changes. There was no choice to make beyond keeping the exact wording and order that the `LESSONS` test pins. I rejected rewording the shell example, because the test compares the text byte for byte.
      - Refactor: nothing to change. The diff is three appended blocks of lines and has no code.
      - Open: criterion 5 (the project guide's section on the shipped agents, replacing `tempfile.mkdtemp()` with `TemporaryDirectory()` in *The agent definition reader* example) is left for the docs stage. I did not touch any documents.
      - Checks: `make check` is green (`check: green`), and the three named test modules pass.

   `make check`: check: green
   `make duplicates`: duplicates: 2 new, 39 known, 0 gone
5. reviewer: no findings.
      - Criterion 1: `claude/agents/smoke-tester.md`, `claude/agents/documenter.md` and `claude/agents/acceptance-reviewer.md` each end `## Lessons` with the Interface's temporary-directory bullet, matching the text exactly. `acceptance-reviewer.md` follows it with the JUnit-report bullet. The diff for each of the three files is only those appended lines. `LESSONS` in `tests/test_claude_agent_texts.py` pins both bullets word for word, in the stated order, through `_TEMPORARY_DIRECTORY_LESSON` and the inline JUnit string. `test_lessons_section_is_last_and_holds_exactly_the_role_bullets` compares the whole section, so a missing, extra or reordered bullet fails it.
      - Criterion 2: the `LESSONS` entries for `intake`, `tester`, `coder` and `reviewer` are untouched, and those four agent files are not in the diff.
      - Criterion 3: the other tests in the three named modules are unchanged and passed in the factory's `make check` after the coder (the coder's entry says `check: green`). The Interface has no limit or rejection rule, so it has no failing side to test.
      - Test changes: the only one is the `LESSONS` change, which FEATURE decision 35 allows.
      - Architecture and security: no code under `src/` changed, and no marker or baseline entry was added.
      - Duplicates: `make duplicates` reports 2 new findings, but `src/factory` is not in this diff, so this story did not cause them.
      - Criterion 5 (docs) is still open for the docs stage. It still describes what the reader needs: the project guide names the two lessons and which agents carry them, and `mkdtemp` is replaced in *The agent definition reader* example.
6. documenter: Changed only `docs/project-guide.md`; no code, so I did not run `make check`. The factory runs it next.
   - *The agent definition reader* example now uses `tempfile.TemporaryDirectory()` in a `with` block instead of `tempfile.mkdtemp()`. I ran it and it prints `['coder']`, then `tools | invalid tools: Input should be a valid list`, as the text says.
   - *The shipped agents, settings and template*, in the `## Lessons` bullet: it now names the temporary-directory lesson (carried by `smoke-tester`, `acceptance-reviewer` and `documenter`) and the JUnit-report lesson (carried by `acceptance-reviewer` only). It says no other agent carries either.
   - `mkdtemp` occurs 0 times in README, the operator guide, the project guide and `docs/decisions.md`. `uv run python -m factory.entry.check_documents` prints `documents ok`.
   - Cross-read against the diff: the claims about the `## Lessons` bullets and `tests/test_claude_agent_texts.py` in the shipped-agents section are now current. README and the operator guide don't mention agent lessons, and I left them unchanged.
   - Findings: none. The three agent texts match the Interface.
   - Stale text I saw but did not touch: none.

   `make check`: check: green
   `make documents`: documents ok
7. demo: I ran both demo blocks from the repository root, exactly as written. Both met their `Expect:` lines, and nothing I saw goes against any acceptance criterion.

   1. The grep for the lesson and the grep for `mkdtemp`:
   ```
   claude/agents/smoke-tester.md:1
   claude/agents/acceptance-reviewer.md:1
   claude/agents/documenter.md:1
   claude/agents/coder.md:0
   docs/project-guide.md:0
   docs/operator-guide.md:0
   README.md:0
   ```
   Met: the four agent lines have the expected counts (1, 1, 1, 0), and the three document lines each end in `:0`.

   2. `uv run pytest --no-header -p no:cacheprovider tests/test_claude_agent_texts.py`:
   ```
   ........................................................................ [ 76%]
   ......................                                                   [100%]
   94 passed in 0.06s
   ```
   Met: the last line is `94 passed in 0.06s`, with no failed, error or skipped count.

   Checked against the criteria:
   - Criterion 1: the ends of `claude/agents/smoke-tester.md`, `documenter.md` and `acceptance-reviewer.md` show the earlier bullets followed by the temporary-directory bullet. In `acceptance-reviewer.md` the JUnit bullet comes after it, as the Interface asks.
   - Criterion 2: the diff against `origin/main`, leaving out `factory/`, touches only those three agent files, `docs/project-guide.md` and `tests/test_claude_agent_texts.py`. The other four agents are unchanged.
   - Criterion 5: `mkdtemp` occurs in none of the three documents.
   - Criterion 3: I did not run `tests/test_claude_files.py` or `tests/adapters/test_shipped_agents_effect.py` myself. The coder and documenter entries report `make check` green, and that run includes those modules.
   - Criterion 4: `make check` is left to the factory's own check.

   Findings: none.
