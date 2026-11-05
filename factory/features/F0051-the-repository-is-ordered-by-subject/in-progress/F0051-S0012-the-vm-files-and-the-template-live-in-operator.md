---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 567
comments_read: [6654125104, 6654318355, 6654469893]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T08:59:42.818138Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T08:59:42.824976Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T09:00:05.522735Z'
  stage: intake
  run: 22cd5b210a134e3ea1696066d353c085
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T09:00:10.647564Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-11-05T09:03:05.798695Z'
  stage: tests
  run: 706ecf4afd194a41b681f451faf2159d
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-11-05T09:11:03.026835Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T09:11:05.575525Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-05T09:11:42.280398Z'
  stage: tests
  run: e1857675163d4947b9cd22a5f0a4e4d1
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T09:11:47.842115Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-05T09:17:27.032473Z'
  stage: doing
  run: 62a57642e4f04879b338ddff91a90939
- number: 11
  speaker: factory
  kind: stall
  at: '2026-11-05T09:17:27.375654Z'
  stage: doing
  run: 62a57642e4f04879b338ddff91a90939
  reason: check_red
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T09:17:35.780424Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-05T09:23:12.498231Z'
  stage: doing
  run: 2f0cfa3461ad4bee88ef4d7b8e835f3e
- number: 14
  speaker: factory
  kind: stall
  at: '2026-11-05T09:23:12.850374Z'
  stage: doing
  run: 2f0cfa3461ad4bee88ef4d7b8e835f3e
  reason: check_red
- number: 15
  speaker: factory
  kind: question
  at: '2026-11-05T09:23:22.458658Z'
  stage: doing
  blocked: attempts_cap
- number: 16
  speaker: human
  kind: comment
  at: '2026-11-05T09:23:31.403965Z'
  stage: doing
- number: 17
  speaker: human
  kind: comment
  at: '2026-11-05T09:29:18.719471Z'
  stage: doing
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-05T09:29:21.207040Z'
  stage: doing
- number: 19
  speaker: coder
  kind: result
  at: '2026-11-05T09:29:48.495394Z'
  stage: doing
  run: 1b1622da5a2f46f6970d6dc2c9fbfd4b
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-05T09:29:53.888879Z'
  stage: tests
- number: 21
  speaker: tester
  kind: result
  at: '2026-11-05T09:30:47.473536Z'
  stage: tests
  run: b5e7a726bce34f95ab65b19a61566641
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-05T09:30:52.954804Z'
  stage: doing
- number: 23
  speaker: coder
  kind: result
  at: '2026-11-05T09:36:05.336231Z'
  stage: doing
  run: e97d04f17b12445cb7a6f07c13e4638c
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-05T09:36:10.854734Z'
  stage: review
- number: 25
  speaker: reviewer
  kind: result
  at: '2026-11-05T09:37:56.876551Z'
  stage: review
  run: 3eeb57bf46064a0393286e56aa418d05
---

# The VM's files and the project template live in `operator/`

## Description

Two folders at the root of the repository belong to the operator: `vm/` holds what sets up and runs an instance on a VM (`setup.sh`, `job-start.sh`, `factory.service`, `git-credential-factory`) and the base image's `Dockerfile`, and `template/` holds what the operator copies into a new project (`CLAUDE.md`, `Makefile`, `factory/`). `operator/` already holds the operator's other tools, among them `operator/job/` for Cloud Run. This story moves `vm/` to `operator/vm/` and `template/` to `operator/template/`, so that everything about where an instance runs and how a project starts sits in one place (the human, 2026-11-04). `demo/` stays at the root, since it is runnable code that `make check` checks. The files do not change, except the paths inside them that name each other.

## Interface

- `vm/` → `operator/vm/` and `template/` → `operator/template/`, with `git mv`.
- Every place under `src/`, `tests/`, `operator/`, `agents/`, `docs/` other than `docs/decisions.md` and `docs/runs/`, and `README.md` that names `vm/<file>` or `template/<file>` names the new path. A build command that names the Dockerfile (`podman build -f vm/Dockerfile`, in `operator/vm/job-start.sh`, the guide and the tests) names `operator/vm/Dockerfile`.
- The coder's write paths `vm/*` and `template/*` in `factory/pipeline.yml`, a name in `Makefile` and the names in `CLAUDE.md` are the human's changes, made at this story's start. The VM's installed copies (the systemd unit, the credential helper) are the human's change on factory-vm after the merge.

- The tester makes every test change the rename needs in its first run, before the files move: every path and name of the old folders in `tests/`, under the leave of feature decision 5. The coder changes `src/`, the renamed folders and the documents it may write; its write paths do not hold `tests/`, so a test change it makes is dropped.

## Acceptance criteria

1. `vm/` and `template/` do not exist; `operator/vm/` and `operator/template/` hold the same files (one row per file, from `origin/main` before the story).
2. The tests of the VM's scripts and of the stage image pass against the files at their new place (they read `operator/vm/`).
3. No file under `src/`, `tests/`, `operator/`, `agents/`, `docs/` other than `docs/decisions.md` and `docs/runs/`, or `README.md` names `vm/setup.sh`, `vm/job-start.sh`, `vm/Dockerfile`, `vm/factory.service`, `vm/git-credential-factory` or `template/` at the root.
4. `make check` stays green.
5. docs: the new paths in `README.md`, the operator guide's topic files and the project guide's `operator.md`, whose *The layout* names the two new folders. `docs/decisions.md`: one entry for the move, naming F0051-S0012.

## Smoke test

```bash
ls -d vm template 2>/dev/null | wc -l
```
Expect: `0`

```bash
test -f operator/vm/Dockerfile && test -f operator/template/Makefile && echo moved
```
Expect: `moved`

```bash
bash -n operator/vm/setup.sh && bash -n operator/vm/job-start.sh && echo parsed
```
Expect: `parsed`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: a pure move (`vm/` → `operator/vm/`, `template/` → `operator/template/`, `git mv`). The Interface names the folders, the files and the path rewrite rule, and lists the human's own changes (pipeline.yml, Makefile, CLAUDE.md) and the tester/coder split. There are no signatures to name, and none are needed.
   - Criteria: each is testable by one test function. 1 checks that the old folders are gone and lists the files by row. 2 is the existing VM-script and stage-image tests reading the new place. 3 is a source search, with both sides: the old root paths are absent, and 1 and 2 cover the new ones. 4 and 5 are the closing criteria. The Interface's Dockerfile build command is covered by 3 (`vm/Dockerfile`). In 3 I read "names `vm/setup.sh`…" as a name at the root of the repository, not as the tail of `operator/vm/setup.sh`. The tester must anchor the search so it does not match the new paths.
   - Smoke test: three runnable commands, with no pytest. Each `Expect:` (`0`, `moved`, `parsed`) can be checked against the output.
   - Architecture: it moves operator-side files only. `src/factory` and its areas are untouched, except for any paths named in source. `demo/` stays at the root, as CLAUDE.md and feature.md say.
   - Scope: it matches the feature's scope line for S0012 and its "The human's changes" entry for S0012. It leaves `docs/decisions.md`'s old entries and the `operator/claude` and `operator/opencode` folders alone, as the Out of scope section requires.
4. factory: started tests as vm.
5. tester: Question on criterion 3. It searches every file under `docs/` other than `docs/decisions.md`. But `docs/runs/` still names the old paths: `2026-10-12-overnight/night-log.md` (30 lines), `report.md`, `s0006-morning-answer.md` and `2026-11-04-f0050/log.md`. `CLAUDE.md` says `docs/runs/` is the human's and no stage edits it, so as worded the criterion can never pass. Options:
   (a) Leave `docs/runs/` out of the search, as the existing guards `tests/guards/test_agent_folder_names.py` and `test_operator_guide_files.py` do. This is my choice, and the test is written this way.
   (b) Keep it in, and the human rewrites those logs.
   If (a), the Description's criterion 3 should say "other than `docs/decisions.md` and `docs/runs/`".

   Work done (tests are in the working tree, written as (a)):
   - criterion 1: tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone (rows vm, template) and ::test_the_moved_file_lies_under_operator (one row per file: operator/vm/{setup.sh, job-start.sh, Dockerfile, factory.service, git-credential-factory}, operator/template/{CLAUDE.md, Makefile, factory/pipeline.yml})
   - criterion 2: the existing VM-script and stage-image tests, now reading operator/vm/ through tests/support/vm_support.py (SETUP, SERVICE, HELPER, JOB_START), tests/support/dockerfile_support.py (STAGE_DOCKERFILE) and tests/machine/application/test_one_stage_environment.py (SETUP)
   - criterion 3: tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path (one row per old name). The search finds only names at the root: tests/guards/test_root_operator_folders_removed.py::test_the_search_finds_only_a_name_at_the_root checks this, as intake asked.
   - criteria 4 and 5: no tests (make check, docs).

   Created: tests/guards/test_root_operator_folders_removed.py.

   Changed, under the Interface's leave (feature decision 5), every old path in tests/:
   - support: support/{shipped_agents, template_make_support, dockerfile_support, vm_support, operator_job_support}.py. The git-clone stand-in now writes operator/vm/Dockerfile. make_job_repository now copies only operator/.
   - guards: guards/{test_pins, test_docker_path_removed} (HELPER), and guards/{test_agent_folder_names, test_operator_guide_files}, where ROOT/"vm" is dropped from the searched paths because operator/ covers it.
   - machine and pipeline: machine/application/test_one_stage_environment, pipeline/adapters/test_pipeline_yaml_tool_paths.
   - operator scripts: operator_scripts/test_operator_job. It expects operator/vm/job-start.sh in the repository and in job.sh's refusal message.
   - vm: vm/{__init__, test_stage_image, test_vm_job_start, test_vm_job_start_instance, test_vm_local_environment, test_vm_service_stop, test_vm_setup_install_hint}. These expect the new paths in the build command, the unit's comment and the setup hints.
   - agent files: agent_files/{__init__, test_claude_agent_texts_mutants, test_claude_files, test_demo_makefile_secrets, test_template_makefile_header, test_template_sync}.

   Test run: `uv run pytest` ran once over the changed and new files. The VM tests are red with errors, because operator/vm/ does not exist yet. That is the right reason; the run's last five lines were ERROR lines, so neither its summary line nor the errors' text was seen. No module failed to import. make lint is green.
6. 2026-11-05 human: Answer of the human:

   **(a)**, as you wrote it: `docs/runs/` is left out of the search (my run logs, history), and criterion 3 reads "other than `docs/decisions.md` and `docs/runs/`". The playbook names none of the old paths, so it needs no change.
7. factory: started tests as vm.
8. tester: The human's answer (a) is what the tests already do. `docs/runs/` is left out of the criterion 3 search, the same as `docs/decisions.md` (`NOT_SEARCHED` in the new guard). I changed no files in this run: the tests from the first run were committed and match the answer.

   Criteria → tests:
   - criterion 1: tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone (rows vm, template) and ::test_the_moved_file_lies_under_operator (one row per file: operator/vm/{setup.sh, job-start.sh, Dockerfile, factory.service, git-credential-factory}, operator/template/{CLAUDE.md, Makefile, factory/pipeline.yml})
   - criterion 2: the existing VM-script and stage-image tests, which now read operator/vm/ through tests/support/vm_support.py, tests/support/dockerfile_support.py and tests/machine/application/test_one_stage_environment.py (SETUP). The first run's entry lists every test file changed under the Interface's leave (feature decision 5).
   - criterion 3: tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path (one row per old name). It skips docs/decisions.md and docs/runs/. ::test_the_search_finds_only_a_name_at_the_root checks that the search matches only a name at the root, not the tail of operator/vm/.
   - criteria 4 and 5: no tests (make check, docs).

   Files created (first run): tests/guards/test_root_operator_folders_removed.py.

   Check this run: a grep of tests/ finds no old root path left outside the guard. `tmp_path / "template"` in tests/guards/test_git_support.py is a temporary folder, not the repository's template/, so it stays.

   Test run: `uv run pytest -q tests/guards/test_root_operator_folders_removed.py` is red for the right reason. The folders have not moved yet, so test_no_file_names_the_old_root_path fails on every old name, because src/, operator/, agents/, docs/ and README.md still name the old paths. No module failed to import. make lint is green.

   Open: the human asked for criterion 3 to read "other than `docs/decisions.md` and `docs/runs/`". The work item's Description is outside the tester's write paths (`tests/*`), so I did not rewrite it. The next stage that may write the work item should make that change.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I moved `vm/` to `operator/vm/` and `template/` to `operator/template/` with `git mv`, and pointed every old root path at the new place. `make check` is green: every test passed, coverage is 99.26 %, and the last line is `check: green`.

    What changed besides the move:
    - **Scripts:**
      - `operator/vm/setup.sh` reads `$checkout/operator/vm/{Dockerfile,git-credential-factory,factory.service}`.
      - `operator/vm/job-start.sh` reads `$code/operator/vm/...` and builds with `-f operator/vm/Dockerfile`.
      - `operator/job/job.sh` reads `$SITE_CODE_REF:operator/vm/job-start.sh` and uses that path in its refusal message.
      - The header comments of `operator/vm/Dockerfile` and `operator/vm/factory.service` name the new paths.
    - **Docs:**
      - `README.md`.
      - The operator guide: `docs/operator-guide/{README,agent-runtime,cloud-run,health,install,machine,records}.md`.
      - The project guide: `docs/project-guide/{README,agents,hosting,machine,operator,pipeline}.md`. This includes the `tests/vm/` line in its README, which now says the tests cover the files under `operator/vm/`.
    - `src/` named none of the old paths, so it is unchanged.

    Main choice: I made the rewrite with one perl substitution that uses the same anchored pattern as the new guard test. It does not touch names that only look like the old paths, such as `/srv/factory/vm/...`, `/proc/sys/vm/...` and `tests/vm/`. I rejected a plain `s|vm/|operator/vm/|`, which would have damaged those instance and system paths.

    Refactor: nothing to change. The diff is the move and the path rewrites.

    Noticed but not touched:
    - Criterion 5 belongs to the documenter, so I left it alone: *The layout* in `docs/project-guide/operator.md` does not yet list `operator/vm/` and `operator/template/`, and `docs/decisions.md` has no entry for the move yet (outside my write paths).
    - Criterion 3 in the Description still lacks the human's wording "other than `docs/decisions.md` and `docs/runs/`". The work item is not in the coder's write paths, so I could not rewrite it. The tests already leave out both paths.
11. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
    ERROR tests/agent_files/test_template_makefile.py::test_duplicates_counts_similar_and_dead_code[none] - FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout/operator/template/Mak...
    ERROR tests/agent_files/test_template_makefile.py::test_duplicates_counts_similar_and_dead_code[findings] - FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout/operator/template...
    ERROR tests/agent_files/test_template_makefile.py::test_duplicates_counts_similar_and_dead_code[vulture-fails] - FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout/operator/tem...
    ERROR tests/agent_files/test_template_makefile.py::test_duplicates_counts_similar_and_dead_code[pylint-fails] - FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout/operator/temp...
    ERROR tests/agent_files/test_template_makefile.py::test_mutants_runs_mutmut_over_the_modules_the_feature_changed[acceptance-branch] - FileNotFoundError: [Errno 2] No such file or directory: '/work/...
    ERROR tests/agent_files/test_template_makefile.py::test_mutants_runs_mutmut_over_the_modules_the_feature_changed[no-module] - FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout...
    ERROR tests/agent_files/test_template_makefile.py::test_mutants_runs_mutmut_over_the_modules_the_feature_changed[story-branch] - FileNotFoundError: [Errno 2] No such file or directory: '/work/check...
    ERROR tests/agent_files/test_template_makefile.py::test_mutants_runs_mutmut_over_the_modules_the_feature_changed[no-repository] - FileNotFoundError: [Errno 2] No such file or directory: '/work/chec...
    ERROR tests/work/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework[docs-first-rework] - FileNotFoundError: [Errno 2] No such file or directory: '/w...
    ERROR tests/work/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework[docs-at-the-cap] - FileNotFoundError: [Errno 2] No such file or directory: '/wor...
    ERROR tests/work/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework[docs-past-the-cap] - FileNotFoundError: [Errno 2] No such file or directory: '/w...
    ERROR tests/work/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework[doing-rework] - FileNotFoundError: [Errno 2] No such file or directory: '/work/c...
    ERROR tests/work/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework[approval-forward] - FileNotFoundError: [Errno 2] No such file or directory: '/wo...
    ERROR tests/work/domain/test_decide_docs_slip.py::test_the_smoke_test_sends_a_slip_in_a_document_to_docs_as_a_rework[review-outside-next] - FileNotFoundError: [Errno 2] No such file or directory: '...
    make: *** [Makefile:89: test] Error 1
12. factory: started doing as vm.
13. coder: The last run stalled because only part of its move reached the commit. Commit f81bcff1c holds `operator/vm/{Dockerfile,factory.service,job-start.sh,setup.sh}` and every rewritten path in the docs and scripts. It does not hold the files that moved without a change: `vm/git-credential-factory` and the whole of `template/` (`CLAUDE.md`, `Makefile`, `factory/pipeline.yml`). So `tests/agent_files/test_template_makefile.py` and `tests/work/domain/test_decide_docs_slip.py` could not find `operator/template/...`.

    The cause is outside this story. `git mv vm operator/vm` renames a folder. `zfs diff` reports that as one rename line for a directory, and `ZfsSnapshots._read_diff_line` (`src/factory/machine/adapters/zfs_snapshots.py`) skips directory lines. So a file inside a renamed folder reaches the take only if its contents also changed. Every file under `vm/` and `template/` is in the coder's write paths, so the write paths are not why they were dropped.

    What I did this run: I moved each remaining file with its own `git mv`: `vm/git-credential-factory` → `operator/vm/git-credential-factory`, and `template/{CLAUDE.md,Makefile,factory/pipeline.yml}` → `operator/template/...`. Then I removed the empty `vm/` and `template/` folders. A file-by-file move gives the take one rename line per file.

    None of the moved files names an old root path, so they are unchanged, as the Description asks. The rest of the work (the rewrites in `operator/vm/*.sh`, `operator/job/job.sh`, `README.md`, `docs/operator-guide/*` and `docs/project-guide/*`) is in commit f81bcff1c from the last run.

    `make check` is green: coverage 99.26 %, last line `check: green`.

    Main choice: moving file by file, rejected alternatives:
    - A second `git mv template operator/template` would have been lost the same way.
    - Fixing the zfs adapter so it lists the files under a renamed directory is a change to the factory beyond this story (R13).

    Refactor: nothing to change. This run's diff is four file renames.

    Noticed but not touched:
    - The directory-rename gap in `ZfsSnapshots.changed_paths` / `_read_diff_line`. Any story that renames a folder with unchanged files in it loses them in the take. This is worth a story of its own.
    - Criterion 3 in the Description still lacks the human's wording "other than `docs/decisions.md` and `docs/runs/`" (journal entry 6). The work item is not in the coder's write paths, so I could not rewrite it. The tests already leave out both paths.
    - The rest of criterion 5 is the documenter's: *The layout* in `docs/project-guide/operator.md` does not yet list the two new folders, and `docs/decisions.md` needs an entry for the move.
14. factory: Stage doing stalled (attempt 2 of 2): a check is red after the stage: `check`
    src/factory/watching/domain/board.py                    55      0      4      1    98%   77->75
    src/factory/watching/domain/machine.py                  52      3     18      5    89%   44->42, 47, 59, 77->75, 79
    src/factory/watching/domain/transcripts.py              10      2      0      0    80%   20-21
    src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   239
    src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
    src/factory/work/domain/acceptance.py                  186      1     46      1    99%   356
    ------------------------------------------------------------------------------------------------
    TOTAL                                                10644     49   2122     46    99%

    154 files skipped due to complete coverage.
    Required test coverage of 90.0% reached. Total coverage: 99.26%
    ======================================================================================= short test summary info ========================================================================================
    FAILED tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone[vm] - AssertionError: assert not True
    FAILED tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone[template] - AssertionError: assert not True
    make: *** [Makefile:89: test] Error 1
15. factory: Stage doing stalled 2 times. The last time: Stage doing stalled (attempt 2 of 2): a check is red after the stage: `check`
    src/factory/watching/domain/board.py                    55      0      4      1    98%   77->75
    src/factory/watching/domain/machine.py                  52      3     18      5    89%   44->42, 47, 59, 77->75, 79
    src/factory/watching/domain/transcripts.py              10      2      0      0    80%   20-21
    src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   239
    src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
    src/factory/work/domain/acceptance.py                  186      1     46      1    99%   356
    ------------------------------------------------------------------------------------------------
    TOTAL                                                10644     49   2122     46    99%

    154 files skipped due to complete coverage.
    Required test coverage of 90.0% reached. Total coverage: 99.26%
    ======================================================================================= short test summary info ========================================================================================
    FAILED tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone[vm] - AssertionError: assert not True
    FAILED tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone[template] - AssertionError: assert not True
    make: *** [Makefile:89: test] Error 1

    Comment anything to retry: the attempts go back to 0 and the stage runs again. Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
16. 2026-11-05 human: Note of the human for the next doing run:

    The first stall is not in your work. The factory takes your result from `zfs diff`, which lists a renamed *directory* as one line and none of the unchanged files inside it; the take skips directory lines (`ZfsSnapshots._read_diff_line`). So every file that `git mv template operator/template` moved without editing was lost (all of `template/`, and `vm/git-credential-factory`), while the files you also edited came through.

    Move the files one by one instead: `mkdir -p operator/template/factory operator/vm`, then `git mv` each file to its new path (`template/CLAUDE.md`, `template/Makefile`, `template/factory/pipeline.yml`, `vm/git-credential-factory`, and any other unedited file), and remove the empty old folders. A file rename is a file line in `zfs diff`, and the take keeps it. Then end as before.
17. 2026-11-05 human: Answer of the human (this comment also retries the stage):

    The second stall's only red test is `tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone` (rows `vm`, `template`). It tests whether the folder exists, and the take can leave an empty folder in the check's tree, as in F0051-S0011. Git tracks files, not folders.

    1. Leave for the tester: the test asserts that git tracks no file under `vm/` and under `template/` (`git ls-files vm template` prints nothing), keeping its name and rows, as S0011's `test_the_old_agent_folder_is_gone` does now.
    2. Coder: make sure every file of the two folders is on the branch at its new path, moved one file at a time (my note of 09:20), then end with `tests` naming change 1.
18. factory: started doing as vm.
19. coder: Test change from the human's answer (entry 17, point 1): `tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone` (rows `vm`, `template`) should assert that git tracks no file under the folder (`git ls-files vm template` prints nothing) rather than that the folder is missing, keeping its name and rows. This matches what S0011's `test_the_old_agent_folder_is_gone` does now.

    Point 2 is already done on the branch, so this run changed no files. I checked the committed state (HEAD):
    - `git ls-files vm template` prints nothing, and neither folder exists in the checkout.
    - `git ls-files operator/vm operator/template` lists all eight files that `origin/main` held under `vm/` and `template/`: `operator/vm/{Dockerfile,factory.service,git-credential-factory,job-start.sh,setup.sh}` and `operator/template/{CLAUDE.md,Makefile,factory/pipeline.yml}`.
    - The four files that moved without edits (`template/CLAUDE.md`, `template/Makefile`, `template/factory/pipeline.yml`, `vm/git-credential-factory`) match their `origin/main` contents exactly (`git diff --quiet origin/main:<old> HEAD:operator/<old>`).
    - `git status --short` is empty.

    I did not run `make check` this run. The one red test from the last stall is the one this change rewrites, and the rest of the suite was green then (coverage 99.26 %).

    Main choice: end with `tests` and leave the code alone, as the human asked. The alternative was to look for an empty-folder cleanup in the check's tree, which I rejected: git tracks files, not folders, and the take can leave an empty folder there (as in F0051-S0011), so only the test can stop depending on it.

    Noticed but not touched (still open from entries 10 and 13):
    - The directory-rename gap in `ZfsSnapshots._read_diff_line` (`src/factory/machine/adapters/zfs_snapshots.py`) is worth a story of its own.
    - Criterion 3 in the Description still lacks the human's wording "other than `docs/decisions.md` and `docs/runs/`" (entry 6). The work item is outside the coder's write paths.
    - The rest of criterion 5 (*The layout* in `docs/project-guide/operator.md` and the `docs/decisions.md` entry) is the documenter's.
20. factory: started tests as vm.
21. tester: Test change the human approved (entry 17, point 1, named by the coder in entry 19). I changed only `tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone`. It keeps its name and its rows `vm` and `template`.

    - Before: the test asserted that the folder does not exist.
    - Now: it asserts that no file lies under the folder (`[path for path in (ROOT / folder).rglob("*") if path.is_file()] == []`). An empty folder that the take leaves in the check's tree no longer fails it.

    Why I wrote it this way: the human's answer says to do what S0011's `test_the_old_agent_folder_is_gone` does now, and I copied that form. I did not call `git ls-files` from the test. The check runs on the taken files before the factory commits, so git's index or `HEAD` there may still list the old paths. A file check on the tree being checked tests what the human asked for: no file left in either folder. If the human wants the literal `git ls-files vm template` call, that is a one-line follow-up.

    Mapping: the human's point 1 → tests/guards/test_root_operator_folders_removed.py::test_the_old_root_folder_is_gone (rows `vm`, `template`).

    Files changed: tests/guards/test_root_operator_folders_removed.py. No files created. No earlier test of another story touched.

    Test run: `uv run pytest -q tests/guards/test_root_operator_folders_removed.py`: all 22 tests pass, and every module imported. `make lint`: green.

    `lint`: lint: green (0.2 s)
22. factory: started doing as vm.
23. coder: The tester's change from entry 21 is in. Its `test_the_old_root_folder_is_gone` now checks that no file lies under `vm/` or `template/`. This run changed no files. The work is already on the branch from the earlier runs:
    - The moves: `operator/vm/{Dockerfile,factory.service,git-credential-factory,job-start.sh,setup.sh}` and `operator/template/{CLAUDE.md,Makefile,factory/pipeline.yml}`. The files that moved without edits were moved one at a time.
    - The path rewrites in `operator/vm/*.sh`, `operator/job/job.sh`, `README.md`, `docs/operator-guide/*` and `docs/project-guide/*`.

    What I checked in this run:
    - `git status --short` is empty.
    - Neither `vm/` nor `template/` exists in the checkout.
    - `git ls-files vm template` prints nothing.
    - `make check` is green: coverage 99.26 %, `test: green (130.9 s)`, last line `check: green`.

    Main choice: I hand forward as it is. I rejected adding anything to the change. The only red test was fixed on the test's side, as the human decided in entry 17.

    Refactor: nothing to change. The diff is the move and the path rewrites, already reviewed in entries 10 and 13.

    What the journal changed: criterion 3 should now read "other than `docs/decisions.md` and `docs/runs/`" (entry 6). The work item is outside the coder's write paths, so I did not rewrite the Description. The tests already leave out both paths.

    Noticed but not touched (still open):
    - A gap in the take, worth a story of its own: `ZfsSnapshots._read_diff_line` (`src/factory/machine/adapters/zfs_snapshots.py`) skips the directory lines that `zfs diff` gives for a renamed directory. So the take loses the unchanged files of a renamed folder.
    - The documenter's part of criterion 5 is still to do: *The layout* in `docs/project-guide/operator.md` must name `operator/vm/` and `operator/template/`, and `docs/decisions.md` needs an entry for the move.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
24. factory: started review as vm.
25. reviewer: no findings

    Reviewed `git diff -M main...HEAD -- . ':!factory'` against the work item.

    1. Acceptance criteria:
       - Criterion 1 is tested by `tests/guards/test_root_operator_folders_removed.py`. `test_the_old_root_folder_is_gone` has the rows `vm` and `template`, and now checks for files, as the human asked in entry 17. `test_the_moved_file_lies_under_operator` has one row for each of the 8 files that `main` held. The diff shows them as R100/R96/R85/R100/R94/R95 renames.
       - Criterion 2: the VM-script and stage-image tests read `operator/vm/` through `tests/support/{vm_support,dockerfile_support}.py` and `test_one_stage_environment.py`.
       - Criterion 3 is tested by `test_no_file_names_the_old_root_path`, one row per old name. Both sides of the anchored search are rows of `test_the_search_finds_only_a_name_at_the_root`: at-root, under-a-checkout and in-a-git-show match; moved, tests-folder and other-file do not.
       - Criterion 4: the coder's `make check` was green (entry 23).
       - Criterion 5 belongs to the documenter.
       - My own anchored grep over `src`, `tests`, `operator`, `agents`, `docs` (without `decisions.md` and `runs/`) and `README.md` found no old root path. It found none in `Makefile` or `CLAUDE.md` either.
    2. Architecture: `src/` is unchanged. The scripts' paths (`operator/vm/setup.sh`, `operator/vm/job-start.sh`, `operator/job/job.sh`) and the build command `-f operator/vm/Dockerfile` follow the move. Nothing else changes.
    3. Security: no new marker, secret or baseline entry. The shell changes are path literals only.
    4. Quality: the changes are path rewrites. Two strings are rewrapped for the line length (`test_vm_service_stop.py`, `test_operator_job.py`). The docstring of `run_job_start` is split, and its meaning is unchanged.
    5. Hygiene: the journal explains the file-by-file move and why the whole-folder move was rejected (the take drops the unchanged files of a renamed directory). Criterion 5 still describes what the documenter must write.

    Corrections (the human's answer, entry 6):
    - description corrected: Interface, second point, "`docs/` other than `docs/decisions.md`" -> "`docs/` other than `docs/decisions.md` and `docs/runs/`".
    - description corrected: criterion 3, "`docs/` other than `docs/decisions.md`" -> "`docs/` other than `docs/decisions.md` and `docs/runs/`".

    Open, for the human (outside the diff and every write path, so no stage can fix it):
    - `pyproject.toml:169`: `[tool.mutmut] also_copy` still lists `"template/"` and `"vm/"`, and it holds no `"operator/"`. The tests that now read `operator/vm/` and `operator/template/` cannot find those files in mutmut's copy during a sweep.
    - `"claude/"` in the same list already looked stale before this story.

    Earlier tests (item 6), every one changed under feature decision 5 (the tester may change the file paths of the moved files in any test module and the guards that pin the old layout). Each keeps its tests' names and what they check:
    - tests/agent_files/__init__.py: feature decision 5 (docstring path)
    - tests/agent_files/test_claude_agent_texts_mutants.py: feature decision 5
    - tests/agent_files/test_claude_files.py: feature decision 5
    - tests/agent_files/test_demo_makefile_secrets.py: feature decision 5
    - tests/agent_files/test_template_makefile_header.py: feature decision 5
    - tests/agent_files/test_template_sync.py: feature decision 5
    - tests/guards/test_agent_folder_names.py: feature decision 5 (guard; `ROOT / "vm"` dropped from SEARCHED, since `operator/` covers it)
    - tests/guards/test_docker_path_removed.py: feature decision 5
    - tests/guards/test_operator_guide_files.py: feature decision 5 (guard; `ROOT / "vm"` dropped, as above)
    - tests/guards/test_pins.py: feature decision 5
    - tests/machine/application/test_one_stage_environment.py: feature decision 5
    - tests/operator_scripts/test_operator_job.py: feature decision 5 (paths, message path, docstring)
    - tests/pipeline/adapters/test_pipeline_yaml_tool_paths.py: feature decision 5
    - tests/support/dockerfile_support.py: feature decision 5
    - tests/support/operator_job_support.py: feature decision 5 (copies only `operator/` now, since `vm/` is inside it)
    - tests/support/shipped_agents.py: feature decision 5
    - tests/support/template_make_support.py: feature decision 5
    - tests/support/vm_support.py: feature decision 5 (paths, the clone stand-in's Dockerfile path, docstring)
    - tests/vm/__init__.py: feature decision 5
    - tests/vm/test_stage_image.py: feature decision 5
    - tests/vm/test_vm_job_start.py: feature decision 5
    - tests/vm/test_vm_job_start_instance.py: feature decision 5
    - tests/vm/test_vm_local_environment.py: feature decision 5
    - tests/vm/test_vm_service_stop.py: feature decision 5
    - tests/vm/test_vm_setup_install_hint.py: feature decision 5
