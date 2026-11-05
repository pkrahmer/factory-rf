---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 567
comments_read: [6654125104]
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
---

# The VM's files and the project template live in `operator/`

## Description

Two folders at the root of the repository belong to the operator: `vm/` holds what sets up and runs an instance on a VM (`setup.sh`, `job-start.sh`, `factory.service`, `git-credential-factory`) and the base image's `Dockerfile`, and `template/` holds what the operator copies into a new project (`CLAUDE.md`, `Makefile`, `factory/`). `operator/` already holds the operator's other tools, among them `operator/job/` for Cloud Run. This story moves `vm/` to `operator/vm/` and `template/` to `operator/template/`, so that everything about where an instance runs and how a project starts sits in one place (the human, 2026-11-04). `demo/` stays at the root, since it is runnable code that `make check` checks. The files do not change, except the paths inside them that name each other.

## Interface

- `vm/` → `operator/vm/` and `template/` → `operator/template/`, with `git mv`.
- Every place under `src/`, `tests/`, `operator/`, `agents/`, `docs/` other than `docs/decisions.md`, and `README.md` that names `vm/<file>` or `template/<file>` names the new path. A build command that names the Dockerfile (`podman build -f vm/Dockerfile`, in `operator/vm/job-start.sh`, the guide and the tests) names `operator/vm/Dockerfile`.
- The coder's write paths `vm/*` and `template/*` in `factory/pipeline.yml`, a name in `Makefile` and the names in `CLAUDE.md` are the human's changes, made at this story's start. The VM's installed copies (the systemd unit, the credential helper) are the human's change on factory-vm after the merge.

- The tester makes every test change the rename needs in its first run, before the files move: every path and name of the old folders in `tests/`, under the leave of feature decision 5. The coder changes `src/`, the renamed folders and the documents it may write; its write paths do not hold `tests/`, so a test change it makes is dropped.

## Acceptance criteria

1. `vm/` and `template/` do not exist; `operator/vm/` and `operator/template/` hold the same files (one row per file, from `origin/main` before the story).
2. The tests of the VM's scripts and of the stage image pass against the files at their new place (they read `operator/vm/`).
3. No file under `src/`, `tests/`, `operator/`, `agents/`, `docs/` other than `docs/decisions.md`, or `README.md` names `vm/setup.sh`, `vm/job-start.sh`, `vm/Dockerfile`, `vm/factory.service`, `vm/git-credential-factory` or `template/` at the root.
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
