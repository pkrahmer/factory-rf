---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 634
comments_read: [6706635920]
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-07T12:10:51.841718Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T11:55:25.620871Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T11:55:25.628230Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-07T11:55:44.841915Z'
  stage: intake
  run: 755291ad19934da1a32655fb68c05bd9
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-07T11:59:33.905227Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-07T11:59:36.195542Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-07T11:59:53.679905Z'
  stage: intake
  run: 164af4b33f924f108633b22a8d827554
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T11:59:58.674977Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-07T12:04:59.487917Z'
  stage: tests
  run: c7b363cb206347039870f4cf14bbb03b
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-07T12:05:04.397035Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-07T12:09:35.764233Z'
  stage: doing
  run: fd49649adaed431b9e5a016a81f48903
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-07T12:09:40.960507Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-07T12:10:46.925133Z'
  stage: review
  run: c1058f0ae7354e18b403021ae233ccf6
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-07T12:10:51.841718Z'
  stage: docs
---

# Every file of code and every script names its license

## Description

The factory is licensed under the Apache License 2.0 (the human changed `LICENSE`, `NOTICE` and `pyproject.toml` on 2026-11-07). A file copied out of the repository does not say so today. This story adds the line `SPDX-License-Identifier: Apache-2.0`, as a comment, to every Python module under `src/factory/` and to every script under `operator/` outside `operator/template/`. The copyright and the author stand once, in `NOTICE`, not in each file. It adds a guard that fails when such a file lacks the line, so that every new file carries it. The tests, `operator/template/`, `demo/`, the documents and the agent files get no header. The code's behaviour does not change.

## Interface

- The header is the comment line `# SPDX-License-Identifier: Apache-2.0`:
  - in each Python module under `src/factory/` (186 files today), as its first line, before the module docstring;
  - in each script under `operator/` outside `operator/template/` (18 files today: `operator/bin/sanitise`, `operator/bin/site`, `operator/job/job.sh`, `operator/lib/hosting.sh`, `operator/lib/site.sh`, the nine scripts under `operator/skill/kumpel/scripts/`, `operator/vm/Dockerfile`, `operator/vm/git-credential-factory`, `operator/vm/job-start.sh` and `operator/vm/setup.sh`), as the line right after the shebang, or as the first line where there is none (`operator/vm/Dockerfile`).
  - The coder adds the headers, by a script it runs once, and changes nothing else in those files.
- `tests/guards/test_license_headers.py` (new): every tracked file in that scope carries the header on its first line, or on the line after its shebang. The scope is read from `git ls-files`: the `*.py` files under `src/factory/`, and the files under `operator/` outside `operator/template/` that are a `*.sh` file, a Dockerfile, or start with `#!`. A file that lacks it gives its path in the failure. One more test shows that a file under `tests/` or `operator/template/` is outside the scope.
- The human's leave: an earlier test whose only failure is the one added header line, for example a test that reads a script's first lines or its header comment, may be changed so far as that line requires; every changed test keeps its name and what it checks, and the entry names each one. The tester makes these changes in its first run, before the coder adds the headers.
- `src/factory/contract/*.schema.json` are JSON and get no header; the contract's generation does not change.

## Acceptance criteria

1. The guard passes on the branch: every file in its scope carries the header in its place.
2. The guard fails, naming the file, for a Python module under `src/factory/` without the header, for a Python module whose header is on line 2 (after a docstring or another line), for a script with a shebang whose header stands before the shebang, and for a Dockerfile and a `*.sh` file without a shebang whose first line is not the header; it passes for a script with a shebang and the header on the line after it, and for a script without a shebang with the header on its first line (rows of one test on files the test writes under `tmp_path`).
3. A file under `tests/`, one under `operator/template/` and a non-script file under `operator/` (a `README.md`, a `.json` without a shebang) are outside the guard's scope; a Dockerfile and a `*.sh` file without a shebang are inside it (rows of one test).
4. Every script still runs: `bash -n` on each script in the scope with a bash shebang (`#!/bin/bash` or `#!/usr/bin/env bash`) and `sh -n` on each with an sh shebang and on each `*.sh` file without a shebang exits 0 (one test); a Dockerfile is not syntax-checked.
5. `make check` stays green.
6. docs: `README.md`: the reader learns that the factory is licensed under the Apache License 2.0, and that each file of code names its license, with a link to `LICENSE` and `NOTICE`. `docs/project-guide/README.md`: the guard among the guards, and that a new module or script carries the header. `docs/decisions.md`: one entry for feature decisions 7 to 9, with the rejected options of a copyright line with the author's name or a project name in every file.

## Smoke test

```bash
git ls-files 'src/factory/*.py' | xargs -I{} head -1 {} | grep -vcx '# SPDX-License-Identifier: Apache-2.0'
```
Expect: `0`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: 1. Scope rule has an uncovered clause. The Interface says the scope under `operator/` is files that are a `*.sh` file, a Dockerfile, or start with `#!`. Criterion 3 only covers `tests/` and `operator/template/` as outside the scope. Nothing tests that a non-script under `operator/` (for example a `README.md` or a `.json` file without a shebang) is outside the scope, or that a Dockerfile and a `*.sh` file without a shebang are inside it. I would add rows to criterion 3 (a non-script file under `operator/` is outside) and to criterion 2 (a Dockerfile or a `*.sh` file without the header on its first line fails, naming the file).
   2. Criterion 2's failing sides are incomplete. The Interface also puts the header "as its first line, before the module docstring" for Python modules. Criterion 2 only has a module with no header. I would add a row for a Python module whose header is on line 2, after a docstring or another line, and fails. I would also add the second branch for scripts: a script with a shebang and the header on the line after it passes, and one without a shebang takes the header on the first line.
   3. Criterion 4 says `bash -n` runs on each `#!/bin/bash` script. Scripts under `operator/` with another shebang, such as `#!/usr/bin/env bash` or `#!/bin/sh` with no `.sh` suffix, are not named. Say which interpreter each shebang needs, or whether `sh -n` should cover them.
   My choice: add the rows above to criteria 2 and 3, and for criterion 4 check by shebang (`bash` shebangs with `bash -n`, `sh` shebangs and `*.sh` files with `sh -n`).
   Checked and fine: the Interface names concrete files and modules, and the smoke test is runnable with a checkable `Expect: 0` (no pytest `-q` involved). The docs criterion names what the reader must know and dictates no sentences. The architecture and the scope fit the feature: S0007 is in the feature's Scope and Decisions 7 to 9, and the tests are excluded as the feature says.
4. 2026-11-07 human: Yes to all three, as you propose.
   1. Add the rows: a non-script file under operator/ (a README.md, a .json without a shebang) is outside the scope; a Dockerfile and a *.sh file without a shebang are inside it and fail without the header on their first line, naming the file.
   2. Add the rows: a Python module whose header is on line 2 (after a docstring or another line) fails; a script with a shebang passes with the header on the line after it; a script without a shebang takes the header on its first line.
   3. Criterion 4 checks by shebang: a bash shebang (#!/bin/bash or #!/usr/bin/env bash) with bash -n, an sh shebang and a *.sh file without a shebang with sh -n. A Dockerfile is not syntax-checked.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete. Names the header line, the 186 modules under `src/factory/`, the 18 operator scripts and `tests/guards/test_license_headers.py`. The scope is read from `git ls-files`. Placement is given for each kind: first line of a module, the line after a shebang, the first line of the Dockerfile. The human's leave for earlier tests is stated.
   - Criteria: I carried in the human's answer (journal 4) as the three edits it approved. Criterion 2 now has the failing rows (module with no header, module with the header on line 2, header before the shebang, Dockerfile and `*.sh` file without the header first) and the passing rows (header after the shebang, header first where there is no shebang). Criterion 3 adds a non-script file under `operator/` as outside the scope, and a Dockerfile and a shebang-less `*.sh` file as inside it. Criterion 4 now checks by shebang: `bash -n` for bash shebangs, `sh -n` for sh shebangs and shebang-less `*.sh` files, with no syntax check for the Dockerfile. Each criterion is testable by one test function.
   - Smoke test: the command is runnable (`git ls-files | xargs head -1 | grep -vcx`, no pytest, so no `-q` issue). `Expect: 0` is checkable.
   - Docs criterion: names what the reader must know (license, the header in each file, links to `LICENSE` and `NOTICE`, the guard, the rejected options). It dictates no sentences.
   - Architecture: the guard sits in `tests/guards/` as the project's layout requires. The only code change is a comment line, so there is no layer or wrapper concern. The generated schemas are untouched.
   - Scope: S0007 is listed in the feature's Scope and in decisions 7 to 9. The tests, `operator/template/`, `demo/`, the documents and the agent files are excluded as the feature says. The route is `tests` because the Interface changes `src/` and `operator/` files, which the documenter may not write.
7. factory: started tests as vm.
8. tester: Wrote the guard and its tests. The guard's own scope and placement rules are test code in the new guard module, so the tests of criteria 2 and 3 already pass. The test of criterion 1 and the changed earlier test fail for the right reason: the headers are not there yet.

   - criterion 1: tests/guards/test_license_headers.py::test_every_file_in_scope_carries_the_license_header
   - criterion 2: tests/guards/test_license_headers.py::test_the_guard_names_a_file_without_the_header_in_its_place (rows that fail: module-without, module-header-after-docstring, module-header-after-another-line, header-before-shebang, dockerfile-without, sh-file-without; rows that pass: module-header-first, header-after-shebang, sh-file-header-first, dockerfile-header-first)
   - criterion 3: tests/guards/test_license_headers.py::test_the_scope_holds_package_modules_and_operator_scripts_only (outside: test-module, template-script, readme, json-without-shebang; inside: dockerfile, sh-file-without-shebang)
   - criterion 4: tests/guards/test_license_headers.py::test_every_operator_script_still_parses (`bash -n` for `#!/bin/bash` and `#!/usr/bin/env bash`; `sh -n` for sh shebangs and for `*.sh` files without a shebang; no check for the Dockerfile)
   - criteria 5 and 6: no test (`make check` and the docs).

   Files created: tests/guards/test_license_headers.py. It reads the tracked files with `run_git(ROOT, "ls-files")` from tests/support/git_support.py, and runs the shells through `run_process`.

   Earlier test changed under the human's leave in the Interface: tests/vm/test_stage_image.py::test_the_first_line_names_the_build_command_with_the_runtime. It now reads `splitlines()[1]`, the line right after the license header in operator/vm/Dockerfile, instead of `[0]`. Its name and what it checks are unchanged. To find which earlier tests the header breaks, I added the headers in a throwaway copy of the repository, ran tests/operator_scripts, tests/vm, tests/guards and tests/machine, then the rest of the suite. That test (both of its rows) was the only failure.

   One interpretation, within criterion 2's header-before-shebang row: a file starting with the header and then `#!` counts as a script for the scope (the scope looks at the line after a leading header), and it fails the guard. Without this, a script whose shebang was pushed down by the header would drop out of the scope by itself.

   My one run (`uv run pytest -q tests/guards/test_license_headers.py tests/vm/test_stage_image.py`) left three failures, all wrong results: the criterion 1 guard (the headers are missing) and both rows of the stage image test (line 2 is not yet the build command). All the modules imported. `make lint` is green.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: Added the line `# SPDX-License-Identifier: Apache-2.0` to every tracked Python module under `src/factory/` and to the 18 operator scripts the Interface names. A throwaway script (made with `mktemp`, not kept) did it in one run. It puts the line first in each module and in `operator/vm/Dockerfile`, and on the line right after the shebang in the scripts that have one. Nothing else in those files changed: 206 files, 206 insertions. File modes are kept. The contract schemas are untouched. `make check` is green.

    - Paths: `src/factory/**/*.py` (188 modules), `operator/bin/sanitise`, `operator/bin/site`, `operator/job/job.sh`, `operator/lib/hosting.sh`, `operator/lib/site.sh`, the nine scripts under `operator/skill/kumpel/scripts/`, `operator/vm/Dockerfile`, `operator/vm/git-credential-factory`, `operator/vm/job-start.sh` and `operator/vm/setup.sh`.
    - Main choice: I listed the operator scripts by name, after checking that the guard's scope rule finds exactly those 18 files. I rejected letting the one-off script work out the scope by itself: a copy of the guard's rule would be a second source of truth, and the Interface already names the files.
    - Refactor: none needed. The diff is only the added header lines.
    - Noticed, not touched: there are 188 modules under `src/factory/`, not the 186 the Interface says. The guard reads its scope from `git ls-files`, so the difference does not matter. The Interface's count could be updated.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
11. factory: started review as vm.
12. reviewer: no findings

    What I checked:
    - Group 1, acceptance criteria. Criterion 1: `test_every_file_in_scope_carries_the_license_header` reads the scope from `git ls-files` through `run_git`. I checked the branch myself: all 188 tracked `src/factory/*.py` files have the header as line 1, and the diff over `src/` is 188 one-line insertions at the top, nothing else. The 18 operator scripts get the line right after `#!/bin/sh`, or as line 1 in `operator/lib/hosting.sh`, `operator/lib/site.sh` and `operator/vm/Dockerfile`, which have no shebang. Criterion 2: one parametrized test with all the rows the criterion names, failing and passing, on files written under `tmp_path`. The check is `unlicensed(...) == [path]`, so a failure names the file. Criterion 3: one parametrized test covering `tests/`, `operator/template/`, a README, a `.json` without a shebang, a Dockerfile and a `*.sh` file without a shebang. Criterion 4: `test_every_operator_script_still_parses` picks `bash -n` or `sh -n` by shebang, uses `sh -n` for a `*.sh` file without one, and skips the Dockerfile. The coder's `make check` was green (journal 10). The schemas under `src/factory/contract/` are untouched and stay outside the scope (`in_scope` takes only `.py` under `src/factory/`).
    - Group 2, architecture: no change under `src/` beyond a comment line. The guard sits in `tests/guards/` and starts its shells through `run_process`, as `tests/vm/test_vm_setup.py` does.
    - Group 3, security: no secrets and no silencing markers. The shells are called with an argv list, not a string.
    - Group 4, quality: the guard uses the shared `run_git` from `tests/support/git_support.py` and copies no existing helper. I ran `make duplicates`; it reports `duplicates: 6 new, 39 known, 4 gone`. Two of the "new" entries are the existing claude/opencode and hand_over/acceptance similar-code findings, listed again under a shifted snippet and the module order swapped, and the matching "gone" lines are their old entries. The four new dead-code findings (`readme_problems` in `src/factory/shared/domain/folder_readmes.py:131`, and three fields in `src/factory/watching/domain/cost_records.py:46-48`) are in code this diff touches only with the header, so they come from earlier stories, not from this one.
    - Group 5, work item hygiene: the journal explains the main choice (scripts named, not found by a copied scope rule) and what was rejected. The Description matches what was built, and the docs criterion still says what the reader must know. One small slip: the Interface says "186 files today" but the branch holds 188. The coder noted this, and the guard reads its scope from git, so the count matters nowhere.
    - Documents: the diff changes none.

    Earlier tests:
    - tests/vm/test_stage_image.py: changed under the human's leave in the Interface ("an earlier test whose only failure is the one added header line ... may be changed so far as that line requires"). Only the line index in `test_the_first_line_names_the_build_command_with_the_runtime` changes, from `[0]` to `[1]`, plus a comment explaining why. Its name and what it checks are unchanged, and the tester's entry 8 names it.
13. factory: started docs as vm.
