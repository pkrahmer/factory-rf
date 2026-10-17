---
stage: doing
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
