---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 435
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T07:31:02.886621Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T07:31:02.891950Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T07:31:19.327397Z'
  stage: intake
  run: 33354200d4ea46099677878ccdb64883
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T07:31:39.418977Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T07:39:21.246335Z'
  stage: tests
  run: bbed04612da24a04803e179da953d5c3
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T07:39:41.385849Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T07:47:25.095485Z'
  stage: doing
  run: f6e60d0b845e432097d548edaf88b0f2
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T07:47:46.047615Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-25T07:48:33.060683Z'
  stage: review
  run: 845813b550fc4982bc7af8cffbf121f5
---

# The dataset's checkout knows origin/main

## Description

The sync container (F0042's S0007) brings the dataset's checkout to the stage's commit by fetching every branch of the host's repository as a local branch (`git fetch -q --prune --update-head-ok "$3" '+refs/heads/*:refs/heads/*'` in `_SYNC_SCRIPT` of `factory.application.stage_environment`). The checkout so has `main` and the work item's branch, but no remote-tracking ref `origin/main`. The project's `make secrets` reads `origin/main` to limit itself to the files a branch changed; without it, it scans every tracked file. On the first stage on the VM (2026-10-25, F0043-S0004 on #434, the instance `vm`), the coder's `make check` stopped at `make secrets` on "Hex High Entropy String" findings in finished acceptance reports the branch never touched (`F0023-A0001`, `F0023-A0002`, `F0042-A0002`), and the coder reported `git diff origin/main` failing with "unknown revision". Every stage on a `container` instance would end the same way, the factory's own check after a stage included, since it runs `make check` in a check container on the same dataset. This story makes the sync also fetch the host's branches as the remote-tracking refs of `origin`, so the dataset's checkout knows `origin/main` (and `origin/<branch>` for every branch) at the host's commit, as a clone of the host's repository would; the `make secrets` of a branch then scans only its changed files, as on `self`. What stays: the local branches are fetched as today, `--prune` removes a branch gone from the host from both, the checkout and the reset to the stage's commit are unchanged, the script's text names no container path (every path comes as an argument), and nothing changes for an `inline` instance. Decision 18 of `feature.md`.

## Interface

`factory.application.stage_environment` (`application`): `_SYNC_SCRIPT`'s fetch line becomes one `git fetch -q --prune --update-head-ok "$3"` with two refspecs, `'+refs/heads/*:refs/heads/*'` and `'+refs/heads/*:refs/remotes/origin/*'`. The comment above the script says why the second one is there (the project's commands read `origin/main`). Nothing else in the script or the module changes.

Tests (the tester writes them): new rows in a new test module, for example `tests/application/test_container_sync_origin.py`, running `ContainerEnvironment.prepare` on `FakeSnapshots` and `FakeContainerRuns` over a real host repository, as `tests/application/test_container_environment.py` runs it. No earlier test changes.

## Acceptance criteria

1. After `prepare` at a work item's branch whose host repository has `main` and that branch, in the dataset's checkout `git rev-parse origin/main` equals the host's `main` commit and `git rev-parse origin/<branch>` equals the host's branch commit, and `git rev-parse main` equals the host's `main` commit as before (rows of one parametrized test).
2. A branch deleted on the host between two `prepare` calls is gone after the second from both `refs/heads/` and `refs/remotes/origin/` of the dataset's checkout (one test).
3. After `prepare`, `git merge-base HEAD origin/main` in the dataset's checkout succeeds and names the host's `main` commit when the branch was made from it (one test): the condition `make secrets` uses to scan only the changed files.
4. `_SYNC_SCRIPT` holds both refspecs on its one fetch line, and no container path (`/work`, `/upstream`) (one test).
5. `make check` stays green.
6. docs: `docs/project-guide/stage-environment.md`, the section on the sync container: one sentence that the sync also fetches the host's branches as `origin/<branch>`, because the project's commands (`make secrets`) read `origin/main`, and what happened on the first VM stage without it. `docs/decisions.md`: none. `README.md`: none.

## Smoke test

```bash
grep -c "'+refs/heads/\*:refs/remotes/origin/\*'" src/factory/application/stage_environment.py
```
Expect: `1`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names the concrete module `factory.application.stage_environment` and the one line to change. I checked `_SYNC_SCRIPT` at line 36 and its fetch line at line 42; it matches the story's description of today's line. The target is exact: one `git fetch` with two refspecs, plus a comment saying why.
   Criteria: each is testable by one test function. 1 is parametrized: origin/main, origin/<branch> and main each equal the host's commit. 2 covers a branch deleted on the host and gone from both `refs/heads/` and `refs/remotes/origin/` (the prune side). 3 covers merge-base HEAD origin/main. 4 covers both refspecs on the one fetch line and no `/work` or `/upstream`. 5 and 6 are the closing criteria. The Interface states no limit, validation or error, so no failing side is missing. The "nothing else changes" clauses (the checkout and reset, inline instances) are existing behaviour that earlier tests already pin, and the story changes no earlier test.
   Smoke test: the `grep -c` command is runnable and does not run pytest. Its `Expect: 1` is checkable, because the refspec appears once in the file.
   Architecture: the change is inside `factory.application`, in the existing sync script. It adds no tool, dependency or layer crossing.
   Scope: this matches decision 18 of `feature.md`, and the story is not under the feature's "Out of scope". The sync is F0042's code, and decision 18 explicitly lets this story change it. `feature.md` says the story is built on `self` while the instance `vm` is stopped.
4. factory: started tests as vm.
5. tester: I wrote the tests for criteria 1 to 4 in a new module. No earlier test changed.

   - criterion 1: tests/application/test_container_sync_origin.py::test_the_dataset_checkout_holds_the_host_branches_as_origin_refs. It is parametrized with the rows `origin-main`, `origin-branch` and `local-main`. Each row checks that `git rev-parse --verify <ref>` in the dataset's checkout equals the host's `refs/heads/<branch>`. The host's branch is made from `main` with one commit of its own, so the two commits differ.
   - criterion 2: tests/application/test_container_sync_origin.py::test_a_branch_deleted_on_the_host_is_gone_from_local_and_origin_refs. After the first `prepare`, both `refs/heads/gone` and `refs/remotes/origin/gone` must exist. After the host deletes the branch and `prepare` runs again, neither must remain.
   - criterion 3: tests/application/test_container_sync_origin.py::test_the_merge_base_of_head_and_origin_main_is_the_host_main_commit
   - criterion 4: tests/application/test_container_sync_origin.py::test_the_sync_script_fetches_both_refspecs_on_one_line_and_names_no_container_path. It checks that exactly one line of `_SYNC_SCRIPT` starts with `git fetch`, that this line holds both refspecs, and that the script names neither `/work` nor `/upstream`. It imports `_SYNC_SCRIPT` directly, because the criterion names it.
   - criteria 5 and 6: these are the coder's `make check` and the documenter's work; they have no tests.

   The tests run `ContainerEnvironment.prepare` on `FakeSnapshots` and `FakeContainerRuns` over the real host repository. They use the helpers in `tests/container_support.py`, as `test_container_environment.py` does.

   File created: tests/application/test_container_sync_origin.py

   Modules the test runner could not import: none, because `factory.application.stage_environment` already exists. The tests fail on wrong results: `origin/main` and `origin/<branch>` are unknown revisions, the `origin/gone` ref is missing, `merge-base HEAD origin/main` fails, and the script lacks the second refspec. The `local-main` row passes already, since the fetch into local branches is today's behaviour. `make lint` is green. I skipped the type check as the stage says.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/application/test_container_sync_origin.py::test_the_sync_script_fetches_both_refspecs_on_one_line_and_names_no_container_path - assert "'+refs/heads/*:refs/remotes/origin/*'" in 'git f...
6. factory: started doing as vm.
7. coder: I added the second refspec to the sync script's fetch. `make check` is green, and the new tests in tests/application/test_container_sync_origin.py pass.

   Built: in src/factory/application/stage_environment.py, `_SYNC_SCRIPT`'s one fetch is now `git fetch -q --prune --update-head-ok "$3" '+refs/heads/*:refs/heads/*' '+refs/heads/*:refs/remotes/origin/*'`. With this, the dataset's checkout gets `origin/<branch>` at the host's commit, the way a clone does, and `--prune` removes a branch deleted on the host from both namespaces. The comment above the script now says why: the project's commands read `origin/main`. Nothing else in the script or the module changed.

   Main choice: the one fetch line is 109 characters, and ruff's E501 limit is 100. I split the source line with a Python backslash-newline inside the triple-quoted string. Python removes that line break, so the script's value keeps the fetch on one line, which the criterion 4 test checks. One sentence in the comment explains the escaped line end.
   Rejected:
   - a shell line continuation (`\\`): it would split the fetch over two script lines and fail the one-line test;
   - a `# noqa: E501`;
   - moving the refspecs into a separate constant that is formatted into the script: that changes the module beyond what the Interface allows.

   Refactor: I read the diff; there was nothing to change. The smoke test's grep finds the refspec once, on the fetch line.

   Noticed, not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
8. factory: started review as vm.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`: one change in `src/factory/application/stage_environment.py` and one new test module. The src change is correct. The backslash-newline inside the non-raw triple-quoted string is removed by Python, so `_SYNC_SCRIPT` has one fetch line with both refspecs. The comment says why the second refspec is there. Nothing else in the module changed. I read criteria 1 to 4 against their tests in `tests/application/test_container_sync_origin.py` and each test checks what its criterion says. The Interface states no rejected input and no limit. The journal (entry 7) records `make check` green after the coder. The Description, Interface and docs criterion still match what was built. Round 0, so points about the quality of the added test file count as findings:

   1. `tests/application/test_container_sync_origin.py:49` `_environment`: this is a second copy of `_environment` in `tests/application/test_container_environment.py:57`. Fix: under the standing leave, the tester moves it once to `tests/container_support.py` as a public helper (for example `container_environment(dataset)`). Both modules then use it, and every earlier test keeps its name and what it checks.
   2. `tests/application/test_container_sync_origin.py:26-29` fixture `dataset` (and the constant `GONE` at line 23): this is a second copy of the `dataset` fixture and of `GONE` in `tests/application/test_container_environment.py:38,42-45`. Fix: under the standing leave, the tester moves the fixture to `tests/conftest.py` and `GONE` to `tests/container_support.py`, and changes `test_container_environment.py` to use them from there, every earlier test keeping its name and what it checks.

   Earlier tests: none. The only test file in the diff is `tests/application/test_container_sync_origin.py`, which is new (status `A`). No test file that `main` already holds was changed, renamed or deleted.
