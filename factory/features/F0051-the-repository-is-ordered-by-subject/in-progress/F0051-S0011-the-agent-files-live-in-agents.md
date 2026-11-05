---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 566
comments_read: [6652891790, 6653046965]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-05T08:13:12.507882Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T07:58:12.339856Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T07:58:12.346437Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T07:58:35.523773Z'
  stage: intake
  run: fda051d1f6c74d9490e464490e4bf6db
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T07:58:41.038765Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-11-05T08:00:55.659696Z'
  stage: tests
  run: e3dd099e841440a2b851e9b58e45b1fb
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-11-05T08:01:43.366131Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T08:01:46.052042Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-05T08:02:16.171759Z'
  stage: tests
  run: eebe2efb96234aa68b00d232462a8da2
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T08:02:22.380627Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-05T08:05:45.888117Z'
  stage: doing
  run: 32cd3c49e86740268d39dd58bba12c03
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-05T08:11:54.187330Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T08:11:56.765939Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-05T08:12:24.166753Z'
  stage: doing
  run: 7cc6803e6c794ff1b2f52aba09ee611c
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-05T08:12:30.289221Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-05T08:13:06.773925Z'
  stage: tests
  run: b7948b2218624f6aaac2b124643d26aa
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-05T08:13:12.507882Z'
  stage: doing
---

# The agent files live in `agents/`

## Description

The factory's agent files and their settings live in `claude/` (`claude/agents/*.md`, `claude/settings.json`), and the image copies them to `/etc/factory/claude`. They are written in Claude Code's format, but the opencode runtime reads them too and translates them per run (the decision of 2026-10-19, F0020-S0004), so the name says one runtime where there are two (F0051 candidates, item 38). This story renames the folder to `agents/` and the image's folder to `/etc/factory/agents`. The format of the files does not change, and `operator/claude/` and `operator/opencode/`, which are the operator's commands for each runtime, keep their names.

## Interface

- `claude/` → `agents/` with `git mv` (`agents/agents/*.md` and `agents/settings.json`).
- `vm/Dockerfile`: the copy and the permissions of the agent files use `agents/` and `/etc/factory/agents`.
- Every place under `src/`, `tests/`, `vm/`, `operator/`, `docs/` and `README.md` that names the folder `claude/` of the agent files, or `/etc/factory/claude`, names the new one; a name of the runtime Claude Code (`claude_runtime`, the `claude` command, `.claude/` in an agent's home) does not change.
- The coder's write path `claude/*` in `factory/pipeline.yml` and the names in `CLAUDE.md` are the human's changes, made at this story's start.

- The tester makes every test change the rename needs in its first run, before the files move: every path and name of the old folders in `tests/`, under the leave of feature decision 5. The coder changes `src/`, the renamed folders and the documents it may write; its write paths do not hold `tests/`, so a test change it makes is dropped.

## Acceptance criteria

1. `claude/` does not exist, and `agents/agents/` holds the same agent files that `claude/agents/` held before (one row per file name).
2. The image built from `vm/Dockerfile` holds the agent files in `/etc/factory/agents/agents/` and none in `/etc/factory/claude` (a test of the Dockerfile's copy and permission lines, as the stage image's tests check them today).
3. The factory finds the agent files at their new place: a stage run in the fake world reads its agent's file from `agents/agents/<role>.md`.
4. No file under `src/`, `tests/`, `vm/`, `operator/`, `docs/` other than `docs/decisions.md`, or `README.md` names `claude/agents/`, `claude/settings.json` or `/etc/factory/claude`.
5. `make check` stays green.
6. docs: the new folder in `README.md`, the operator guide's topic file on the agent files, and the project guide's `agents.md`. `docs/decisions.md`: an entry for the rename with its reason, naming F0051-S0011.

## Smoke test

```bash
test -d claude && echo still there || echo renamed
```
Expect: `renamed`

```bash
test -f agents/settings.json && test -f agents/agents/coder.md && echo found
```
Expect: `found`

```bash
grep -c '/etc/factory/agents' vm/Dockerfile | awk '{print ($1>=1)}'
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: a rename, so it has no signatures. It names the moves (`claude/` → `agents/` by `git mv`), `vm/Dockerfile`'s copy and permission lines, and the places that name the folder. Code that holds the old path: `AGENT_FILES = "/etc/factory/claude"` in `src/factory/machine/application/stage_environment.py:30`, and `vm/Dockerfile:58-59`. The Interface's behaviour is only the new path, and criteria 1 to 4 cover it.
   - Criteria: each is testable by one test function. 1: folder gone and same file names under `agents/agents/`. 2: Dockerfile copy and permission lines, as the stage image's tests check them today. 3: the fake-world stage reads `agents/agents/<role>.md`. 4: a scan that excludes `docs/decisions.md`. The rename adds no rule with a failing side beyond criteria 1 (old folder absent) and 4 (no old name). Criterion 3 does not name the constant, so the tester should pin `AGENT_FILES` and the host-side read.
   - Smoke test: three runnable commands, each with an `Expect:` that can be checked (`renamed`, `found`, `1`). None runs pytest.
   - Architecture: this only moves a folder and updates paths. No layer, wrapper or interface changes. The runtime names (`claude_runtime`, the `claude` command, `.claude/`) are explicitly left alone.
   - Scope: it matches feature.md's Scope line "`claude/` becomes `agents/`" and is not in Out of scope; `operator/claude/`, `operator/opencode/` and `docs/decisions.md` are excluded as the feature says. The write path and `CLAUDE.md` changes are the human's, made at the story's start, as the feature's "The human's changes" says.
4. factory: started tests as vm.
5. tester: I wrote every test and every test change the rename needs, and they pass `make lint`. I stopped at one case in criterion 4 that I had to interpret. Criterion 4 says no file under `docs/` other than `docs/decisions.md` may name `claude/agents/`, `claude/settings.json` or `/etc/factory/claude`. Two such files under `docs/` are ones no stage of this story may change:
   - `docs/runs/2026-10-12-overnight/night-log.md` (lines 252 and 590) is the human's file and outside every write path (CLAUDE.md, *The human's files*).
   - `docs/operator-playbook.md:21` names `claude/agents/intake.md`. No stage keeps the playbook unless the docs criterion names it, and criterion 6 does not name it.

   As criterion 4 is worded, its test can never go green on this branch. Options:
   (a) Exclude `docs/runs/` from criterion 4, since it is history, and add `docs/operator-playbook.md` to criterion 6 so the documenter updates its path.
   (b) Exclude both `docs/runs/` and `docs/operator-playbook.md` from criterion 4.
   (c) The human changes both files themselves.
   I would choose (a). The test as written already leaves out `docs/decisions.md` and `docs/runs/`, and still checks the playbook. For (b) I add one path to `NOT_SEARCHED`; for (c) I remove `docs/runs` from it.

   Mapping as written:
   - criterion 1: tests/agent_files/test_agent_folder.py::test_the_old_agent_folder_is_gone, ::test_the_agent_folder_holds_each_agent_file (one row per file name), ::test_the_agent_folder_holds_no_other_agent_file
   - criterion 2: tests/vm/test_stage_image.py::test_the_agent_files_are_copied_read_only_to_their_place (constants `AGENT_FILES_COPY`/`AGENT_FILES_MODES` changed to `agents /etc/factory/agents`), tests/vm/test_stage_image_agent_folder.py::test_the_image_names_no_agent_file_at_the_old_place
   - criterion 3: tests/entry/test_tick_shipped_agent_file.py::test_a_stage_run_reads_its_agent_from_the_agent_folder (a fake-world tick runs the coder with the shipped `agents/agents/coder.md`), tests/machine/application/test_container_environment.py::test_the_sync_container_gets_container_paths_mounts_environment_and_limit (mount and argument now `/etc/factory/agents`)
   - criterion 4: tests/guards/test_agent_folder_names.py::test_no_file_names_the_old_agent_folder (one row per old name)

   Files created: tests/agent_files/test_agent_folder.py, tests/vm/test_stage_image_agent_folder.py, tests/entry/test_tick_shipped_agent_file.py, tests/guards/test_agent_folder_names.py.

   Earlier test files changed, under the Interface's leave (feature decision 5), for the paths only:
   - tests/support/shipped_agents.py (`AGENT_HOME = ROOT / "agents"`)
   - tests/guards/test_operator_guide_files.py and tests/guards/test_project_guide_files.py (searched folder `agents`)
   - tests/vm/test_stage_image.py
   - tests/machine/application/test_container_environment.py
   - tests/machine/domain/test_containers.py (sample mount target)
   - tests/agents/domain/test_nested_claude_paths.py (row `agents/agents/coder.md`)
   - tests/agent_files/__init__.py (docstring)

   Test file names such as `test_claude_agent_*.py` stay: they name the Claude Code format, not the folder.

   One run of the touched files: the expected tests fail, among them the guard rows, the stage image copy test and the container mount test. The output was cut at five lines, so I did not see whether the other new tests (folder, tick, Dockerfile) failed too. All of them read `agents/`, which does not exist yet, so they fail on a missing file, not on an import. Every module imported.
6. 2026-11-05 human: Answer of the human:

   `docs/runs/` is left out of criterion 4 (history, mine). The playbook is mine too: I changed its line on `main` to `agents/agents/intake.md`, and the next stage merges it in. So the test keeps checking the playbook and leaves out `docs/decisions.md` and `docs/runs/`, as you wrote it; criterion 6 stays as it is.

   `CLAUDE.md`'s two lines that name the agent files change after the merge; they are mine and outside your search.
7. factory: started tests as vm.
8. tester: The human's answer leaves criterion 4's test as it was written: it leaves out `docs/decisions.md` and `docs/runs/` and still checks `docs/operator-playbook.md`. The branch now has the human's playbook line through the merge of `origin/main` (commit 9676aff05), so I did not need to change any test. The tests from the previous run were already committed, and I left them as they were.

   Mapping:
   - criterion 1: tests/agent_files/test_agent_folder.py::test_the_old_agent_folder_is_gone, ::test_the_agent_folder_holds_each_agent_file (one row per file name), ::test_the_agent_folder_holds_no_other_agent_file
   - criterion 2: tests/vm/test_stage_image.py::test_the_agent_files_are_copied_read_only_to_their_place, tests/vm/test_stage_image_agent_folder.py::test_the_image_names_no_agent_file_at_the_old_place
   - criterion 3: tests/entry/test_tick_shipped_agent_file.py::test_a_stage_run_reads_its_agent_from_the_agent_folder, tests/machine/application/test_container_environment.py::test_the_sync_container_gets_container_paths_mounts_environment_and_limit
   - criterion 4: tests/guards/test_agent_folder_names.py::test_no_file_names_the_old_agent_folder (one row per old name)

   Files created, all in the previous run: tests/agent_files/test_agent_folder.py, tests/vm/test_stage_image_agent_folder.py, tests/entry/test_tick_shipped_agent_file.py, tests/guards/test_agent_folder_names.py. Earlier test files I changed under the leave of feature decision 5, all in the previous run (entry 5 lists them): tests/support/shipped_agents.py, tests/guards/test_operator_guide_files.py, tests/guards/test_project_guide_files.py, tests/vm/test_stage_image.py, tests/machine/application/test_container_environment.py, tests/machine/domain/test_containers.py, tests/agents/domain/test_nested_claude_paths.py, tests/agent_files/__init__.py.

   I ran the touched test files once. They fail as expected: the tick test, the three guard rows and the container mount test show in the last five lines. The others read `agents/`, which does not exist yet. Every module imported, so no module was missing. `make lint` is green.

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
10. coder: I stopped before `make check` because three test problems are outside my write paths, and I may not edit tests (R9). Work so far, left in the working tree:
    - `git mv claude agents`
    - `src/factory/machine/application/stage_environment.py:30`: `AGENT_FILES = "/etc/factory/agents"`
    - `vm/Dockerfile:58-59`: copies to and sets modes on `/etc/factory/agents`
    - `vm/job-start.sh:68`: `"$code/agents"`
    - `vm/setup.sh:427`: `FACTORY_CLAUDE_HOME=$base/factory/agents`. The two scripts must change because the clone's `claude/` folder no longer exists.
    - The old paths in `docs/project-guide/{README,agents,machine}.md` and `docs/operator-guide/{agent-runtime,install,machine}.md`. I left every `.claude/` mention alone.

    With these changes, the targeted tests show the problems below.

    1. `tests/guards/test_agent_folder_names.py::test_no_file_names_the_old_agent_folder[claude/settings.json]` fails on `.claude/settings.json`. That is the human's `.claude/` folder, which the Interface says keeps its name. It appears as test data in `tests/agents/domain/test_nested_claude_paths.py:14,18,42,43`, `tests/agents/domain/test_write_paths.py:115,148` and `tests/pipeline/application/test_take_rule.py:19`. A substring check cannot tell the two apart.
       Options:
       (a) The guard matches only where no `.` or word character comes before the name, e.g. `re.search(r"(?<![\w.])" + re.escape(old_name), text)`. I would choose this.
       (b) Those test files change their sample paths.

    2. `tests/entry/test_tick_shipped_agent_file.py::test_a_stage_run_reads_its_agent_from_the_agent_folder` fails with `assert 'intake' == 'coder'`. A story started from the backlog runs the first stage, `intake`, so the coder never runs in one tick.
       Options:
       (a) `ROLE = "intake"`, which still reads a shipped file from `agents/agents/`. I would choose this.
       (b) Move the work item to `doing` before the tick.

    3. Two tests still pin the old folder of the factory's clone. The Interface says every place under `vm/` changes, and the instance would point at a folder that is gone:
       - `tests/vm/test_vm_job_start.py:82` (`f"{root}/factory/claude"`), which fails `test_factory_run_gets_the_derived_settings_where_the_job_gave_none[derived]`
       - `tests/support/vm_support.py:51` (`"$base/factory/claude"`), which fails `tests/vm/test_vm_setup_text.py::test_the_environment_file_holds_each_name_once_with_its_value[10-FACTORY_CLAUDE_HOME-...]`

       I would choose to change both to `factory/agents`. The alternative is to keep the scripts on `factory/claude`, but that breaks every instance.

    I would choose 1(a), 2(a) and 3 as changed. If you agree, the next doing run ends with `tests` naming exactly these changes, then finishes once the tester has made them.

    Main choice so far: keep the variable name `FACTORY_CLAUDE_HOME` and change only its path, because renaming the variable is outside this story. I rejected renaming it.

    Noticed but not touched: `operator/README.md:31` names `claude/commands/kumpel.md` (that is `operator/claude/`, so it is correct).
11. 2026-11-05 human: Answers of the human: 1(a), 2(a) and 3 as you propose.

    1. The guard matches a name only where no `.` or word character comes before it (`(?<![\w.])`), so `.claude/settings.json` does not count.
    2. `ROLE = "intake"`.
    3. Both test lines change to `factory/agents`; `FACTORY_CLAUDE_HOME` keeps its name.

    Leave for the tester for exactly these three changes. End with `tests` naming them.

    For me after the merge, on factory-vm, before its restart: the `FACTORY_CLAUDE_HOME` line of `factory.env` names `factory/agents`, the stage image is rebuilt (the Dockerfile's new `/etc/factory/agents`), and `image-id` is renewed.
12. factory: started doing as vm.
13. coder: The human's answer (entry 11) gives leave for three test changes. Following that answer, I changed no code in this run. The tester should make exactly these changes:
    1. `tests/guards/test_agent_folder_names.py::test_no_file_names_the_old_agent_folder`: count an old name only where no `.` or word character comes before it, e.g. `re.search(r"(?<![\w.])" + re.escape(old_name), text)`. Then `.claude/settings.json` no longer counts.
    2. `tests/entry/test_tick_shipped_agent_file.py`: `ROLE = "intake"` instead of `"coder"`.
    3. `tests/vm/test_vm_job_start.py:82`: `f"{root}/factory/claude"` becomes `f"{root}/factory/agents"`. `tests/support/vm_support.py:51`: `"$base/factory/claude"` becomes `"$base/factory/agents"`. `FACTORY_CLAUDE_HOME` keeps its name.

    The last doing run's commit does not include the folder move. On the branch, `claude/` still exists and `agents/` does not. The path edits from that run were committed: `src/factory/machine/application/stage_environment.py:30`, `vm/Dockerfile:58-59`, `vm/job-start.sh:68`, `vm/setup.sh:427` and the files under `docs/project-guide/` and `docs/operator-guide/`. I did not redo the move in this run so that it changes no code. The next doing run moves `claude/` to `agents/` and checks that the take records both the deletion and the new files. Both `claude/*` and `agents/*` are in the coder's write paths.

    Main choice: end with `tests` now and leave the move for after the test changes. I rejected making the move in this run, because this step should change no code.

    Noticed but not touched: nothing new beyond entry 10.
14. factory: started tests as vm.
15. tester: I made the three test changes the human approved in entry 11, as the coder listed them in entry 13. Nothing else changed.

    1. `tests/guards/test_agent_folder_names.py::test_no_file_names_the_old_agent_folder` now counts an old name only where no `.` or word character comes before it: `re.search(r"(?<![\w.])" + re.escape(old_name), text)`, with `import re` added. So `.claude/settings.json` no longer counts. ruff format then rewrapped the condition over several lines.
    2. `tests/entry/test_tick_shipped_agent_file.py`: `ROLE = "intake"` replaces `"coder"`, because the first tick runs the intake stage.
    3. `tests/vm/test_vm_job_start.py:82` now expects `f"{root}/factory/agents"`, and `tests/support/vm_support.py:51` expects `"$base/factory/agents"`. `FACTORY_CLAUDE_HOME` keeps its name.

    Mapping, unchanged from entry 8:
    - criterion 1: tests/agent_files/test_agent_folder.py::test_the_old_agent_folder_is_gone, ::test_the_agent_folder_holds_each_agent_file, ::test_the_agent_folder_holds_no_other_agent_file
    - criterion 2: tests/vm/test_stage_image.py::test_the_agent_files_are_copied_read_only_to_their_place, tests/vm/test_stage_image_agent_folder.py::test_the_image_names_no_agent_file_at_the_old_place
    - criterion 3: tests/entry/test_tick_shipped_agent_file.py::test_a_stage_run_reads_its_agent_from_the_agent_folder, tests/machine/application/test_container_environment.py::test_the_sync_container_gets_container_paths_mounts_environment_and_limit
    - criterion 4: tests/guards/test_agent_folder_names.py::test_no_file_names_the_old_agent_folder

    I created no new files in this run. Files changed: the four named above. All four are under the human's leave in entry 11; `tests/support/vm_support.py` and `tests/vm/test_vm_job_start.py` were written by other stories.

    I ran `uv run pytest -q` once over the guard, tick, job-start and setup-text test files. Only one failure showed in the summary. The tick test fails with `FileNotFoundError: .../agents/agents/intake.md` because the coder has not moved `claude/` to `agents/` yet (entry 13). That is the expected red. Every module imported. `make lint`: lint: green (0.1 s).

    `lint`: lint: green (0.2 s)
16. factory: started doing as vm.
