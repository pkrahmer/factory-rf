---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 288
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T21:22:58.315978Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T21:22:58.323204Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T21:23:20.190763Z'
  stage: intake
  run: aa86554ae37d48f79ed12866f9547c41
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T21:23:40.918296Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T21:25:31.585696Z'
  stage: tests
  run: d5b7f7e4d46c4738972f45b9fb672ea4
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T21:25:52.253507Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T21:27:48.648851Z'
  stage: doing
  run: 1194e1a9265a493ba57a42be13de4489
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T21:28:09.390325Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T21:28:34.001214Z'
  stage: review
  run: 9eda14e9c0e14ebdaabb97d50a48e2b1
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T21:28:54.588487Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T21:29:15.705431Z'
  stage: docs
  run: 159181129cdb41c5afc18d749f3309db
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T21:29:36.229926Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-19T21:29:52.738194Z'
  stage: smoke-test
  run: d7691e770ec94de48c9bf12feb090a57
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-19T21:31:12.077831Z'
  stage: approval
---

# The git wrapper leaves out a path that starts with a dash

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`GitCli.work_tree_id(left_out)` (S0001) removes the left-out paths from its temporary index with `git update-index --force-remove -- <paths>`. The `--` is what makes git read a path that starts with `-` as a path and not as an option. No test has such a path, so the feature acceptance's `make mutants` found a surviving mutant that replaces `--` with another word: every test still passes. The acceptance ran the case by hand on today's code and it works, so this story adds the missing criterion and its test, and expects no code change. It is for the operator whose project holds a file such as `-notes.md` in a folder its `not_read` names: without the `--`, the key would fail and the command would run every time. Nothing else of `work_tree_id` changes; S0001's tests stay as they are.

## Interface

No module under `src/factory/` changes. `factory.adapters.git_cli` (`adapters`): `GitCli.work_tree_id(left_out=())` as S0001 built it. The rule this story pins:

- A left-out path that starts with `-` or `--` is removed from the tree as a literal path, as any other listed path is, and the call raises no error.

Tests (the tester writes them): `tests/adapters/test_git_cli_work_tree_dash.py`, with the `checkout` fixture of `tests/conftest.py` and `CHECKOUT`, `run_git` and `write_files` of `tests/git_support.py`, as `tests/adapters/test_git_cli_work_tree.py` uses them. No earlier test changes.

## Acceptance criteria

1. On a work tree whose root holds `a.md`, `-x.md` and `--y.md` (rows of one parametrized test): `work_tree_id(["-x.md", "--y.md"])` equals `work_tree_id()` after `-x.md` and `--y.md` are removed from the work tree. `work_tree_id(["-x.md"])` equals `work_tree_id()` after only `-x.md` is removed, and `--y.md` still counts. `work_tree_id(["-*"])` equals `work_tree_id()` after `-x.md` and `--y.md` are removed, and `a.md` still counts. `work_tree_id(["a.md"])` equals `work_tree_id()` after only `a.md` is removed, and both dash files still count.
2. `make check` stays green.
3. docs: none. `docs/project-guide/git-and-hosting.md` already says that the left-out paths are removed as literal paths with `update-index --force-remove --`.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git init -q --initial-branch=main "$d/w"
printf 'a\n' > "$d/w/a.md"
printf 'x\n' > "$d/w/-x.md"
printf 'y\n' > "$d/w/--y.md"
uv run -q python - "$d/w" <<'EOF'
import sys
from pathlib import Path
from factory.adapters.git_cli import GitCli

w = Path(sys.argv[1])
git = GitCli(w)
left = git.work_tree_id(["-x.md", "--y.md"])
(w / "-x.md").unlink()
(w / "--y.md").unlink()
print(left == git.work_tree_id())
EOF
```
Expect: `True`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no module changes. It names `GitCli.work_tree_id(left_out=())` in `factory.adapters.git_cli` and the one rule to pin. I read the code: `src/factory/adapters/git_cli.py:412-427` matches the left-out patterns with `matches_any` and passes the matched paths after `--` to `update-index --force-remove`. So a `-*` pattern works as a pattern, and the removed paths are literal.
   - Criteria: criterion 1 is one parametrized test with four rows, and each row compares two exact values. The rows are both dash files, `-x.md` alone, the `-*` pattern, and `a.md` alone. The failing side is covered: a path that is not left out still counts, and a missing `--` would make git read `-x.md` as an option and raise. "Raises no error" is checked by the call itself. The two closing criteria are in place: `make check` stays green, and docs: none with its reason.
   - Smoke test: the commands are runnable (git init, three files, a short python script via `uv run`). The `Expect: True` line is checkable against the printed output.
   - Architecture: adapter layer only, with tests under `tests/adapters/` using the shared fixtures `checkout`, `run_git` and `write_files`, as the CLAUDE.md test layout requires. No earlier test changes.
   - Scope: it is inside F0023 and S0001's `work_tree_id`, adds a test only, and touches nothing in the feature's Out of scope.
4. factory: started tests as self.
5. tester: Wrote the one test for criterion 1. It is a parametrized test with four rows, built the way `tests/adapters/test_git_cli_work_tree.py` builds its tests: the `checkout` fixture plus `CHECKOUT` and `write_files` from `tests/git_support.py`. Each row writes `a.md`, `-x.md` and `--y.md` at the work tree's root and takes `work_tree_id(left_out)`. It then deletes the files that row expects to be left out and checks that the result equals `work_tree_id()`. Because the two ids must be equal, every file that is not left out still counts.

   - criterion 1: tests/adapters/test_git_cli_work_tree_dash.py::test_a_left_out_path_that_starts_with_a_dash_is_removed_as_a_literal_path, with these rows:
     - both-dash-files: `["-x.md", "--y.md"]`
     - single-dash-file-only: `["-x.md"]`, so `--y.md` still counts
     - dash-pattern: `["-*"]`, so `a.md` still counts
     - plain-file-only: `["a.md"]`, so both dash files still count
   - criterion 2 (`make check` stays green): no test; the factory's check covers it.
   - criterion 3 (docs: none): no test.

   Files created: tests/adapters/test_git_cli_work_tree_dash.py. No earlier test file changed.

   Modules the test run could not import: none. The test is not red, and that is on purpose. The story expects no code change, because `GitCli.work_tree_id` already passes `--` to `update-index --force-remove`. One `make test` run was green ("test: green (41.0 s)"), with all four rows passing. `make lint` is green.

   I did not check by hand that this test kills the mutant that replaces `--`. Doing so would need a temporary edit under `src/`, which is outside my write paths. If the `--` were missing, git would read `-x.md` as an option and the call would raise, so the dash rows would fail.

   Open: nothing. The coder has no code to write; their `make check` is the remaining gate.

   `lint`: lint: green (0.0 s)
   `test`: test: green (40.5 s)
6. factory: started doing as self.
7. coder: I built nothing, as the story expects. No file under `src/factory/` changed. `GitCli.work_tree_id` (`src/factory/adapters/git_cli.py:412-427`) already passes `--` before the dropped paths to `update-index --force-remove`. The tester's `tests/adapters/test_git_cli_work_tree_dash.py` passes all four rows against the current code.

   - Mutant check: I changed the `--` to `XX` by hand and ran the new test alone. Three rows failed (both-dash-files, single-dash-file-only, dash-pattern), and plain-file-only passed, as it should. So the test kills the mutant the acceptance found surviving. I restored the file from a copy in `$TMPDIR`, and `git status` shows `src/` unchanged.
   - Main choice: I left the code alone. The alternative I rejected was hardening the call further, for example by passing the paths through `--stdin -z`. The description says no code changes, and the `--` is already correct.
   - Refactor: I made no changes, because there is no diff of mine to refactor.
   - `make check`: green (`check: green`, `test: green (44.7 s)`).
   - Noticed, not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'`. It adds one file, `tests/adapters/test_git_cli_work_tree_dash.py`, and changes nothing under `src/`. I read it against the work item and against `GitCli.work_tree_id` (`src/factory/adapters/git_cli.py:412-427`).

   1. Acceptance criteria: criterion 1 is `test_a_left_out_path_that_starts_with_a_dash_is_removed_as_a_literal_path`, one parametrized test with four rows: both dash files, `-x.md` alone, the `-*` pattern, and `a.md` alone. Each row writes `a.md`, `-x.md` and `--y.md` into the checkout. It takes `work_tree_id(left_out)`, deletes only the files that row expects to be left out, and asserts the result equals `work_tree_id()`. Because the two ids must be equal, every file that is not left out has to still count, so `--y.md` counts in the second row and `a.md` in the third. The `a.md` row fails if `left_out` is ignored altogether. The rule's failing side, `--` missing, would make git read `-x.md` as an option and raise. The coder reports that the three dash rows fail when `--` is replaced, and that matches how `update-index` handles its arguments. The rule states no limit with two sides. The factory's `make check` after the coder was green (entry 7).
   2. Architecture: only a test was added. It is under `tests/adapters/`, uses the shared `checkout` fixture plus `CHECKOUT` and `write_files` from `tests/git_support.py`, and fakes no git.
   3. Security: nothing silences a check, and there are no secrets.
   4. Quality: the test copies no helper, the four cases are rows of one parametrized test, and the module has its docstring.
   5. Work item hygiene: the journal explains that no code changed and why, and names the alternative the coder rejected (`--stdin -z`). The Description matches what was built: tests only. The docs criterion ("none") holds, because `docs/project-guide/git-and-hosting.md:124` already says the left-out paths are removed with `update-index --force-remove --` as literal paths.

   Earlier tests: none. The diff only adds a test file (status `A`), and no file that `main` already holds under `tests/` changed.
10. factory: started docs as self.
11. documenter: Docs stage, no findings. I changed no file. The docs criterion says `none`, and I checked that.

    - The diff is one new test, `tests/adapters/test_git_cli_work_tree_dash.py`. Nothing under `src/` changed, so no behaviour, name or example moved.
    - Cross-read and found current: `docs/project-guide/git-and-hosting.md:124`. It says `work_tree_id` runs `update-index --force-remove --` for the left-out paths, as literal paths and never pathspecs. That is the rule this story pins, and `src/factory/adapters/git_cli.py:412-427` (read by the reviewer) agrees with it.
    - The other mentions of `--` in the README, `docs/operator-guide.md` and the other project-guide files are about other commands (`sudo`, `factory-confine`, cleanup). The story does not touch them.
    - Stale text noticed, not mine to fix: none.
    - I did not run `make check`, because I changed no file. The factory's checks after this stage decide.

    `check`: check: green (not run again: passed on tree ba5e71b10a03 at 2026-10-19T21:27:01Z)
    `secrets`: secrets: green (0.1 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test: no findings.

    I ran the `## Smoke test` block exactly as written, from the repository root, as one bash script. It made a temporary directory with `mktemp -d`, removed it on exit through its own `trap`, and left nothing behind.

    Command: the whole block. It runs `git init`, writes `a.md`, `-x.md` and `--y.md`, then runs the `uv run -q python -` script. The script compares `work_tree_id(["-x.md", "--y.md"])` with `work_tree_id()` after the two dash files are deleted.

    ```
    True
    exit=0
    ```

    Expect: `True`. Met. Both `work_tree_id` calls ran without an error, and the two ids are equal.

    Acceptance criteria, read again against the smoke test:
    1. Criterion 1: consistent. The smoke test is that criterion's first row, run outside the test suite on a fresh repository with no commits: the dash paths are removed as literal paths, and the call raises nothing. The smoke test does not exercise the other three rows (`-x.md` alone, `-*`, `a.md` alone), but nothing it showed contradicts them.
    2. Criterion 2 (`make check` stays green): the smoke test does not touch this. The factory's check after the coder was green (entry 7), and I did not run it again because this stage fixes nothing.
    3. Criterion 3 (docs: none): not contradicted.

    Findings: none.
14. factory: done (pull request merged); cost: 6 runs, 3.5 min, 32 turns, 106697 tokens in (492028 more from cache), 8188 out, $0.93
