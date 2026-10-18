---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 225
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-18T17:16:18.720421Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T17:09:40.571619Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T17:09:40.577308Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T17:09:58.504010Z'
  stage: intake
  run: 64e6fc2a36e84a77af5bf10a96488ff5
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T17:10:18.406142Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T17:12:11.482586Z'
  stage: tests
  run: ccb4ccde93db446b86296049af820e1b
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T17:12:31.498808Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T17:14:24.190370Z'
  stage: doing
  run: ad57b57cace84bcaa14cc48e2ffe84aa
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T17:14:44.213731Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T17:15:21.082615Z'
  stage: review
  run: 13fd501ffaf7403e928f60972e35612c
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T17:15:41.145276Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-18T17:15:58.715122Z'
  stage: doing
  run: 782bdc28dbe04ee6a25cb42762ccaff0
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T17:16:18.720421Z'
  stage: tests
---

# The agents' instructions explain a refused write

## Description

Under the kernel's write guard (S0004) an agent that writes outside its write paths, by any tool or command, gets the system's `Permission denied`, and one that writes to `/tmp` itself gets it too. Its instructions today say only that a hook refuses an edit and that the factory undoes other writes, so an agent may read the refusal as a fault of the machine and work around it, or end the stage `question` about a broken `/tmp`. This story rewrites the closing sentence of rule R14 in all seven shipped agents (`claude/agents/*.md`): the kernel refuses every other write, the hook still refuses an edit (it stays as the cross-check, feature decision 16), the factory undoes the rest; a refused write is `Permission denied` and the guard, never retried another way, and a `question` when the work needs that path; temporary files go to `$TMPDIR`, the run's own folder (feature decision 14). The first sentence of R14 and every other rule stay as they are; the hook's clause goes with the hook, in the later feature that removes it.

## Interface

No module under `src/factory/` changes. The coder changes the seven files `claude/agents/acceptance-reviewer.md`, `coder.md`, `documenter.md`, `intake.md`, `reviewer.md`, `smoke-tester.md` and `tester.md`: in each, the text of R14 after "You write only within your write paths in the pipeline definition (`{work_item}` there is your own work item, outside its front matter and journal), nothing else: " is replaced, so that R14 reads in full:

```markdown
R14. The pipeline's own files — `factory/pipeline.yml`, `factory/story-form.md`, every feature's `feature.md`, `backlog/`, `done/` and `.claude/` — change only with the human's commit or on their explicit instruction. You write only within your write paths in the pipeline definition (`{work_item}` there is your own work item, outside its front matter and journal), nothing else: the kernel refuses every other write, by any tool and any command you run, a hook also refuses an edit outside the write paths, and the factory undoes any other write after the stage. A refused write fails with `Permission denied` (`EACCES`, `PermissionError: [Errno 13]`, `cannot create ...: Permission denied`): that is the write guard, not a fault of the machine; never retry it by another route, and when the work needs that path, end with `question` and name it. Make temporary files only in `$TMPDIR` (`mktemp`, `tempfile`), the run's own folder, which the factory removes after the run; `/tmp` itself is refused.
```

- The paragraph is one line in each file, as R14 is today; nothing else in the files changes.

Tests (the tester writes them): `tests/test_claude_agent_refusal.py`, reading the shipped agents through `tests/shipped_agents.py`.

## Acceptance criteria

1. The `Rules` section of each of the seven shipped agents holds the R14 paragraph of the Interface exactly, as one line (seven rows of one parametrized test over the shipped agents' names).
2. No shipped agent's body holds the old ending "a hook refuses an edit outside the write paths, and the factory undoes any other write after the stage." (seven rows of one parametrized test).
3. Each shipped agent's body holds the line that starts `R14. ` exactly once (seven rows of one parametrized test).
4. `make check` stays green.
5. docs: `docs/project-guide.md`, section *The shipped agents, settings and template*, says in one sentence that R14 tells every agent what a refused write looks like (`Permission denied`), that it is the guard and a `question` when the work needs the path, and that temporary files belong in `$TMPDIR`.

## Smoke test

```bash
grep -l 'A refused write fails with `Permission denied`' claude/agents/*.md | wc -l
```
Expect: `7`

```bash
grep -L 'a hook refuses an edit outside the write paths, and the factory undoes any other write after the stage' claude/agents/*.md | wc -l
```
Expect: `7`

```bash
grep -c 'Make temporary files only in `$TMPDIR`' claude/agents/coder.md
```
Expect: `1`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names the seven concrete files under `claude/agents/` and gives the full R14 paragraph verbatim, as one line. No `src/` module changes. `tests/shipped_agents.py` exists, and each agent has exactly one `R14. ` line today.
   - Criteria: 1 pins the full paragraph exactly, so every clause of it is covered: the kernel refusing, the hook staying, the undo, `Permission denied` and its three spellings, no retry by another route, `question` naming the path, `$TMPDIR`, and `/tmp` refused. 2 covers the failing side: the old ending is gone. 3 says R14 appears exactly once. Each of the three is a parametrized test over seven agents. 4 is `make check` and 5 is the docs criterion. Each is testable by one test function.
   - Smoke test: the three `grep` commands can be run as written. The expected values (`7`, `7`, `1`) can be checked against the output.
   - Architecture: this is prompt text only, in the coder's `claude/*` write path. Nothing crosses a layer, and the first sentence of R14 and the other rules stay as they are.
   - Scope: matches the feature's scope line for `claude/agents/*.md` (S0006) and decision 14. It does not remove the hook, which is out of scope.
4. factory: started tests as self.
5. tester: Wrote the tests for the new R14 paragraph. Each test is parametrized over the seven shipped agents, using `SHIPPED_NAMES` and `front_matter_and_body` from `tests/shipped_agents.py`.
   - criterion 1: tests/test_claude_agent_refusal.py::test_rules_hold_the_write_paths_rule_as_one_line. It checks that the Interface's R14 paragraph is one line under `## Rules`, read with `factory.domain.sections.section_text`.
   - criterion 2: tests/test_claude_agent_refusal.py::test_old_ending_of_the_write_paths_rule_is_gone
   - criterion 3: tests/test_claude_agent_refusal.py::test_write_paths_rule_appears_once
   - criterion 4: `make check`, run by the factory. No test of its own.
   - criterion 5: the docs criterion, for the documenter stage. No test.
   Files created: tests/test_claude_agent_refusal.py. I changed no earlier test file. No earlier test pins the old R14 text.
   Import errors: none. No module under `src/` is new, so all modules imported. `make test` failed as intended: the tests for criteria 1 and 2 fail on all seven agents because the agents still hold the old text. The test for criterion 3 already passes: each agent has exactly one `R14. ` line today, and the coder's change must keep it that way. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/test_claude_agent_refusal.py::test_rules_hold_the_write_paths_rule_as_one_line[intake]
6. factory: started doing as self.
7. coder: Replaced the ending of R14 in all seven shipped agents. The files are `claude/agents/acceptance-reviewer.md`, `coder.md`, `documenter.md`, `intake.md`, `reviewer.md`, `smoke-tester.md` and `tester.md`. Everything after "nothing else: " is now the Interface's paragraph word for word, still on one line. Nothing else in the files changed, and no module under `src/` changed.
   - Main choice: I made the change with one exact string replacement. The script checked that the old ending appeared exactly once in each file before it replaced it. That way all seven files get identical text, and a file that had drifted would have stopped the change. I rejected editing each file by hand, because seven copies of a long paragraph typed separately can drift apart.
   - Refactor: I read the diff and found nothing to change. It is the same one-line replacement in seven files.
   - Description: the journal did not change the meaning of the task, so I did not rewrite it.
   - Checks: `make check` is green (`check: green`). The tests in `tests/test_claude_agent_refusal.py` pass. The first smoke-test grep (`A refused write fails with \`Permission denied\``) finds 7 files.
   - Noticed, not touched: nothing outside the work item. The docs criterion (`docs/project-guide.md`) is left to the documenter.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: 1. `tests/test_claude_agent_refusal.py:29` (`_body`): this is a second copy of the `_body` helper at `tests/test_claude_agent_texts.py:140`. Both wrap `front_matter_and_body(name)` and return the body, word for word. Fix: under the standing leave, the tester moves `_body` into `tests/shipped_agents.py`, next to `front_matter_and_body`, as a public helper (for example `body(name)`). Both modules then import it. Every earlier test in `tests/test_claude_agent_texts.py` keeps its name and what it checks. Since the coder never edits tests, the coder ends with `tests` and names this change.

   Groups 1 to 3 pass:
   - The three criterion tests are rows over `SHIPPED_NAMES`. The test for criterion 1 pins the Interface's paragraph exactly, as one line under `## Rules`. Criterion 2 covers the failing side. The factory's `make check` was green after the coder (entry 7).
   - The seven agent files change only the R14 line, and the new text matches the Interface's paragraph exactly.
   - No `src/` change and no check is silenced.

   Group 4 fails on the item above, so group 5 was not reviewed.

   Earlier tests: none. The diff changes no test file that `main` already holds; `tests/test_claude_agent_refusal.py` is new (status `A`).
10. factory: started doing as self.
11. coder: Round 1: the reviewer's only finding is a change to the tests, so it goes to the tester. I changed nothing in this round.
    - The change for the tester, under the standing leave to move a shared test helper: move the private `_body(name)` helper into `tests/shipped_agents.py` as a public `body(name: str) -> str`, next to `front_matter_and_body`. It returns the body from `front_matter_and_body(name)`. Then change the two files that copy it to import it from there: `tests/test_claude_agent_refusal.py` (line 29) and `tests/test_claude_agent_texts.py` (line 140). Every test in both files keeps its name and checks the same thing.
    - I confirmed the two copies are identical, word for word. A search of `tests/` found no other `_body` that wraps `front_matter_and_body`. The `_body` helpers in `tests/application/test_acceptance_merged.py`, `tests/domain/test_hand_over.py` and `tests/domain/test_story_form.py` do something else. They are not copies and are not part of the move.
    - Main choice: end with `tests` and name the move, as the role requires. I rejected editing the test files myself: the coder never edits tests.
    - Not touched: the seven agent files under `claude/agents/` stay as round 0 left them. The reviewer found they match the Interface. No `src/` change. The docs criterion (`docs/project-guide.md`) is left to the documenter.
12. factory: started tests as self.
