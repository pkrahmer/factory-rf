---
stage: accept
pr: 206
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The cost records are left out of the secrets scan

## Assignment (as of log entry 1)

The tiny story of 2026-10-18 (F0099-S0001 on `pkrahmer/factory-demo-todo`, the night log's rows of 05:56 and 06:09) found that every agent run turns a project's `make check` red. `CostRecorder.begin` writes each run's cost record into the sidecar beside the work item (`<work item>.costs.jsonl`). The record's `run` is a new `uuid4` as 32 lowercase hexadecimal characters, a JSON string, and detect-secrets reads such a string as a high-entropy secret. The template's `make secrets` scans the files changed against `origin/main`, the uncommitted ones included, so the coder's own `make check` and every stage's check are red from the first run of every work item on. The cost records hold run metadata and no secret. The human fixed the live demo by leaving them out of the scan (`83eaa11`) and changes the todo demo's source the same way before this story (FEATURE, the human's change 1). This story puts the same line into `template/Makefile`, the starting point of every new Python project, and adds a test that keeps the demo's `secrets` recipe equal to the template's, so the two cannot drift apart again. The run ids stay as they are (FEATURE decision 1). The tester extends one test of F0012-S0029 with the human's leave (FEATURE decision 4).

## Interface

`template/Makefile`, target `secrets`: the line that filters the file list, today

```
	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline)$$' || true)
```

becomes exactly (one tab at the start, as the recipe's other lines)

```
	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline|.*\.costs\.jsonl)$$' || true)
```

It is the line of `demo/todo-service/project/Makefile` after the human's change. Nothing else in the file changes: no comment, no other target. The effect: a path that ends `.costs.jsonl` (the factory's `COST_RECORDS_SUFFIX`), in any folder, is not handed to `detect-secrets-hook`. That holds on a branch, whether the file is committed on the branch, changed in the work tree or new and untracked, and on `main`, where every tracked file is scanned. `uv.lock` and `.secrets.baseline` are still left out. Every other path is scanned as before, among them `costs.jsonl` (no dot before `costs`) and `docs/a.costs.jsonl.txt` (the suffix not at the end). When nothing is left, `detect-secrets-hook` is not called and the target is green, as today.

Tests:

- `tests/test_template_makefile.py` (F0012-S0029), with the human's leave (FEATURE decision 4): `test_secrets_scans_the_changed_files_or_every_tracked_file` gains four rows, after its five existing ones. The module gains two constants, `SIDECAR = "factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl"` and `SECOND_SIDECAR = "factory/features/F0001-todo/in-progress/F0001-S0002-list.costs.jsonl"`, and four setup functions beside `_branch_with_code` and the others, each `(folder: Path) -> None` and built from the module's own `_on_main`, `_branch`, `write_files` and `commit_all`. The rows are written as (setup, status, files):
  - `sidecar-on-main`: `_on_main_with_a_sidecar` writes `SIDECAR` with the text `{}` and a newline, commits it (`commit_all(folder, "sidecar")`), then calls `_on_main(folder)`; status 0; files `["Makefile", "README.md", "src/todo/a.py"]`.
  - `sidecars-on-branch`: `_branch_with_code_and_sidecars` writes and commits `SIDECAR` as above, calls `_branch(folder, {"src/todo/a.py": "x = 2\n"})`, and then, staging neither, rewrites `SIDECAR` in the work tree with the text `{"run": 1}` and a newline and writes the new, untracked `SECOND_SIDECAR` with the text `{}` and a newline (the states an agent's `make check` sees after `begin`: on a later run of a work item, and on its first); status 0; files `["src/todo/a.py"]`.
  - `sidecar-only`: `_branch_with_a_sidecar_only` calls `_branch(folder, {SIDECAR: "{}\n"})`; status 0; files `None` (no call).
  - `look-alikes`: `_branch_with_look_alikes` calls `_branch(folder, {"costs.jsonl": "{}\n", "docs/a.costs.jsonl.txt": "{}\n"})`; status 0; files `["costs.jsonl", "docs/a.costs.jsonl.txt"]`.

  The test's name, signature and body and its five existing rows stay. With today's template, the first three rows are red (the sidecars are in the call) and `look-alikes` is green. After the change all nine rows are green.
- New module `tests/test_demo_makefile_secrets.py`: `test_the_todo_demos_secrets_target_is_the_templates`. It reads `template/Makefile` and `demo/todo-service/project/Makefile` from the repository root (`Path(__file__).parent.parent`). Of each it takes the recipe of `secrets`: the lines after the one line that matches `^secrets\s*:`, up to the first line that does not start with a tab. The test asserts that each file has exactly one such head line, that the two recipes are equal, and that the template's recipe holds the filter line of the Interface. It is red until the coder's change, because the demo has the line after the human's change and the template does not.

## Acceptance criteria

1. On `main`, `make secrets` of the template hands every tracked file except `uv.lock`, `.secrets.baseline` and a tracked `SIDECAR` to `detect-secrets-hook` (`Makefile`, `README.md`, `src/todo/a.py`) and is green. Row `sidecar-on-main` of `test_secrets_scans_the_changed_files_or_every_tracked_file`.
2. On a branch, the changed files are handed on without any path that ends `.costs.jsonl`: a sidecar changed and unstaged in the work tree and a new, untracked sidecar are both left out, and the changed code file is scanned. Row `sidecars-on-branch` of the same test.
3. On a branch whose only change is a sidecar committed on the branch, `detect-secrets-hook` is not called and the target is green. Row `sidecar-only` of the same test.
4. A path that contains `.costs.jsonl` but does not end with it, and a path `costs.jsonl` without a dot before `costs`, are still scanned. Row `look-alikes` of the same test.
5. The todo demo's `secrets` recipe is the template's, line for line, and holds the filter line of the Interface: `test_the_todo_demos_secrets_target_is_the_templates` in `tests/test_demo_makefile_secrets.py`.
6. What must still hold: the five existing rows of `test_secrets_scans_the_changed_files_or_every_tracked_file` (`main`, `no-origin`, `branch`, `lock-only`, `secret-found`) and the other tests of `tests/test_template_makefile.py` pass.
7. `make check` stays green.
8. docs: the project guide's *The template* says, in its bullet on `template/Makefile`, that `make secrets` leaves out `uv.lock`, `.secrets.baseline` and every file ending `.costs.jsonl`. These are the factory's cost records: they hold run metadata and no secret, and their 32-character hexadecimal run ids read to detect-secrets as high-entropy secrets, which made the coder's `make check` red at the tiny story of 2026-10-18 (F0099-S0001 on the todo demo). The bullet also says that the todo demo's `secrets` recipe is the template's and that a test keeps them equal. The operator guide's *The project's make targets* gets a sentence: a project whose `check` scans for secrets, with the template's `make secrets` or a scanner of its own, must leave out the factory's cost records (`*.costs.jsonl`, beside each work item), or the first agent run of every work item makes `check` red. The decision log gets an entry, "A project's secrets scan leaves out the cost records; run ids stay hexadecimal". It says why (no secret in a cost record; a scan rule holds for any id and any scanner) and names the rejected alternatives with their reasons: a prefix on the run id, a baseline entry per finding, a pragma in each line (FEATURE decision 1); the narrower pattern under `factory/features/` (decision 2); and why the demo's recipe is pinned to the template's (decision 3). No other document changes, the documents use no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -cF '.*\.costs\.jsonl' template/Makefile demo/todo-service/project/Makefile
```
Expect: two lines, `template/Makefile:1` and `demo/todo-service/project/Makefile:1`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_template_makefile.py tests/test_demo_makefile_secrets.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-18 human: created.
2. intake: accepted
   - Interface: names the exact one-line change to the `secrets` target of `template/Makefile`, the two new constants and four setup functions in `tests/test_template_makefile.py` (with their helpers `_on_main`, `_branch`, `write_files` and `commit_all`), and the new test module and function. I checked the repo: the template has 0 matches of the new pattern and the demo has 1, so the human's change 1 is in. `secrets:` is at line 59 in both Makefiles. `_branch` and `_on_main` exist. The Interface states no behaviour that lacks a criterion.
   - Criteria: each one is covered by one row or one test function. Rows: `sidecar-on-main`, `sidecars-on-branch`, `sidecar-only`, `look-alikes`. Test: `test_the_todo_demos_secrets_target_is_the_templates`. Both sides of the rule are covered. The excluded side is the sidecar rows. The scanned side is `look-alikes` (`costs.jsonl`, `docs/a.costs.jsonl.txt`) and the five existing rows. The "nothing left" case is the `sidecar-only` row. Criterion 8 (docs) is specific enough to check.
   - Demo: both commands are runnable. Each `Expect:` line is checkable. The `grep` expectation is `template/Makefile:1` and `demo/todo-service/project/Makefile:1`, and the pytest expectation is a `<n> passed` last line with no `failed`, `error` or `skipped` count.
   - Architecture: the change is only in the template Makefile, tests and docs. No layer or interface is touched.
   - Scope: it is within FEATURE scope (finding 1, S0001). It does not touch the Out of scope items (run id form, `template/CLAUDE.md`). The edit to the earlier test F0012-S0029 has the human's leave (FEATURE decision 4).
3. tester: the red tests for the coder are written.
   - criterion 1: tests/test_template_makefile.py::test_secrets_scans_the_changed_files_or_every_tracked_file[sidecar-on-main]
   - criterion 2: tests/test_template_makefile.py::test_secrets_scans_the_changed_files_or_every_tracked_file[sidecars-on-branch]
   - criterion 3: tests/test_template_makefile.py::test_secrets_scans_the_changed_files_or_every_tracked_file[sidecar-only]
   - criterion 4: tests/test_template_makefile.py::test_secrets_scans_the_changed_files_or_every_tracked_file[look-alikes]
   - criterion 5: tests/test_demo_makefile_secrets.py::test_the_todo_demos_secrets_target_is_the_templates
   - criterion 6: the five existing rows (main, no-origin, branch, lock-only, secret-found) and the other tests of tests/test_template_makefile.py, all unchanged.
   - criteria 7 and 8: the factory's `make check` and the docs stage cover these. No test.

   Files: I changed tests/test_template_makefile.py, with the human's leave (FEATURE decision 4). It gains the constants `SIDECAR` and `SECOND_SIDECAR`, four setup functions (`_on_main_with_a_sidecar`, `_branch_with_code_and_sidecars`, `_branch_with_a_sidecar_only`, `_branch_with_look_alikes`) and four rows after the five existing ones. The test's name, signature and body did not change. I created tests/test_demo_makefile_secrets.py. It has a private `_secrets_recipe` helper that reads the recipe of `secrets:` and asserts there is exactly one head line, and a `FILTER` constant that holds the Interface's line with its leading tab.

   `make test`: as the Interface predicts, four tests fail: the rows sidecar-only, sidecar-on-main and sidecars-on-branch, and the demo/template equality test. Row look-alikes is already green. There were no import errors, because no new module is under test. `make lint` is green.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_template_makefile.py::test_secrets_scans_the_changed_files_or_every_tracked_file[sidecars-on-branch]
4. coder: built. One line in `template/Makefile` (target `secrets`, line 66) is now exactly the Interface's filter line: `grep -vE '^(uv\.lock|\.secrets\.baseline|.*\.costs\.jsonl)$$'`. I copied that line byte for byte from `demo/todo-service/project/Makefile`, so the two `secrets` recipes are now identical, and I checked that with a diff of lines 59–70. Nothing else in the file changed. Commit d8d94628 (`ticket F0015-S0001: fix(template): leave the cost records out of make secrets`). `make check` passed (`check: green`), including the four new rows of `test_secrets_scans_the_changed_files_or_every_tracked_file` and `test_the_todo_demos_secrets_target_is_the_templates`.
      - Design: copying the demo's line rather than retyping the regex rules out a tab or escaping mismatch between the two Makefiles. I rejected a narrower pattern limited to `factory/features/`, as FEATURE decision 2 does.
      - Refactor: the diff is one line, so there was nothing to clean up and there is no refactor commit.
      - Open: the docs for criterion 8 (project guide, operator guide, decision log) are the documenter's job. I did not touch them.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Criteria: the change to `template/Makefile` (line 66) is exactly the Interface's filter line. Every criterion has a test that tests what it is named after. The sidecar rows (`sidecar-on-main`, `sidecars-on-branch`, `sidecar-only`) cover the left-out side. On the scanned side there is `look-alikes` (`costs.jsonl`, `docs/a.costs.jsonl.txt`) and the five existing rows, which are unchanged. `sidecar-only` covers the case where nothing is left. `sidecars-on-branch` builds an unstaged changed sidecar and a new untracked one, as the Interface asks. `test_the_todo_demos_secrets_target_is_the_templates` checks that each Makefile has exactly one `secrets` head line, that the two recipes are equal and that the template holds the filter line. A diff of the two `secrets` recipes shows they are identical. The coder's entry records `make check` green.
      - Architecture and security: no `src/factory` code changed. There is no suppression marker and no baseline entry. The test data is low-entropy (`{}`, `{"run": 1}`).
      - Quality: the new setup functions reuse the module's `_branch`, `_on_main`, `write_files` and `commit_all`, and the new module's helper is private and small.
      - Hygiene: Assignment matches what was built, and the coder's entry gives the main decision and the alternative it rejected. Criterion 8 still says what the documenter must write.
6. documenter: wrote what criterion 8 asks.
   - docs/project-guide.md, *The template*, bullet on `template/Makefile`: `make secrets` leaves out `uv.lock`, `.secrets.baseline` and every `*.costs.jsonl`, with the reason (run metadata, hexadecimal run ids read as secrets, F0099-S0001), and the demo's recipe equals the template's, kept by `tests/test_demo_makefile_secrets.py`.
   - docs/operator-guide.md, *The project's make targets*: one paragraph telling a project that scans for secrets to leave out the cost records.
   - docs/decisions.md: new entry "A project's secrets scan leaves out the cost records; run ids stay hexadecimal", with the rejected alternatives (run id prefix, baseline entry per finding, pragma per line, narrower `factory/features/` pattern) and why the demo's recipe is pinned.
   - `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check` because I changed only docs.
   - Cross-read: the diff (one Makefile line plus tests) against the project guide's template section and the operator guide's make-targets section. Both were otherwise current. The code matches the Interface (template line 66 is the Interface's line), so there are no findings.
   - Stale prose unrelated to this story: none seen.

   `make check`: check: green
   `make documents`: documents ok
7. demo: both commands met their `Expect:` lines, and nothing contradicts a criterion.

   Command 1: `grep -cF '.*\.costs\.jsonl' template/Makefile demo/todo-service/project/Makefile`
   ```
   template/Makefile:1
   demo/todo-service/project/Makefile:1
   ```
   Met: two lines, each count 1.

   Command 2: `uv run pytest --no-header -p no:cacheprovider tests/test_template_makefile.py tests/test_demo_makefile_secrets.py`
   ```
   ................................................                         [100%]
   =============================== warnings summary ===============================
   .venv/lib/python3.12/site-packages/_pytest/pathlib.py:95
     …: PytestWarning: (rm_rf) error removing /tmp/pytest-of-factory/garbage-…/test_seal_takes_the_group_and_0/checkout
     <class 'OSError'>: [Errno 39] Directory not empty: …
   …
   -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
   48 passed, 15 warnings in 2.35s
   ```
   Met: the last line says `48 passed` and has no `failed`, `error` or `skipped` count. The 15 warnings come from pytest's own cleanup of old basetemp folders in `/tmp`, which earlier runs of another test (`test_seal_takes_the_group_and_0`) left behind. They are not from this story, and the Expect line does not exclude warnings.

   Criteria check: the `secrets` recipes in the two Makefiles (lines 59–70) are identical when diffed. `git diff origin/main --stat -- template/` shows one changed line in `template/Makefile`, which fits "nothing else in the file changes". Criteria 1–6 are covered by the passing rows and the passing equality test. Criteria 7 and 8 (`make check`, docs) were recorded green by the coder and the documenter, and nothing in the demo contradicts them.
