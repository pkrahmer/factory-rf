---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 512
comments_read: [6597509758, 6597622408, 6597751272]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T06:34:18.373268Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T06:34:18.379856Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T06:34:43.819654Z'
  stage: intake
  run: ccd7775635ba4174a7caac429ff5b265
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T07:03:10.691726Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T07:03:13.586532Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T07:03:39.207501Z'
  stage: intake
  run: 3077e67d5ead40dfb6f464d249de34a0
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T07:03:44.798660Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-03T07:04:52.265846Z'
  stage: tests
  run: 577ba80612a14a619810abf44c61d3be
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-03T07:08:44.057908Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-03T07:08:49.233410Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-03T07:10:06.688722Z'
  stage: tests
  run: 5ef8f44045d24e4e92893e1cf6a526e8
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-03T07:10:12.635235Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-11-03T07:11:55.599436Z'
  stage: doing
  run: 2e257068f5f14c7581b3a3ef6d63ae45
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-11-03T07:17:52.549314Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-03T07:17:55.508644Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-11-03T07:21:25.067425Z'
  stage: doing
  run: 31f8ea737a264be4a21dfe37f94fcbf9
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-03T07:21:31.420400Z'
  stage: review
- number: 18
  speaker: reviewer
  kind: result
  at: '2026-11-03T07:22:42.803316Z'
  stage: review
  run: cc32cdee18d547348e9ee08f57d4b693
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-03T07:22:48.523892Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-03T07:23:04.323181Z'
  stage: doing
  run: d82910295c58402d9760ba6e4c4f0ea1
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-03T07:23:10.221628Z'
  stage: tests
- number: 22
  speaker: tester
  kind: result
  at: '2026-11-03T07:24:34.394123Z'
  stage: tests
  run: 55b71a85351b489a9d20d4da26c589ce
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-03T07:24:40.719507Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-11-03T07:28:03.163389Z'
  stage: doing
  run: 9e8e513d0ed64bd5a4c33e2523015262
---

# Stopping the service stops its agents

<!-- written by the human on 2026-11-03 from what the acceptance F0048-A0001 met (decision 20) -->

## Description

The factory starts every agent call and every check in a container with `podman run --rm`. Rootless podman with systemd's cgroup manager places the container and its `conmon` in a scope of the `factory` user's own systemd, outside the cgroup of the service `factory@<instance>`. So `systemctl stop factory@vm` ends `factory-run` and the `podman run` client, while the container goes on until it ends or podman's `--timeout` ends it. The unit has `Restart=always`: after a crash, or after a stop and a start, the new factory finds the stage without an owner and starts a second agent on the same dataset while the first one still writes into it. The acceptance F0048-A0001 met exactly this on 2026-11-03: a rebuild stopped the service during the first acceptance run, and a second run worked beside it in one dataset.

This story makes a stop of the service stop the instance's containers. Every container the factory starts carries a label with the instance's name, and the unit stops the containers with that label after the service's process has ended, whether the service was stopped or crashed. Containers that do not carry the label, another instance's included, are not touched. Nothing else about how a container runs changes.

## Interface

- Every container the factory starts, for an agent run and for a project command, carries the label `factory.instance=<FACTORY_INSTANCE>`. All starts go through `PodmanRuns.launch` in `src/factory/adapters/podman_runs.py` (agent runs through `agent_launch`, project commands through `run`, which calls `launch`). `PodmanRuns.__init__` gains a required keyword-only `instance: str`, set by `factory.entry.wiring` from the settings' instance; `launch` puts the two words `--label`, `factory.instance=<instance>` next to each other, after `--rm`.
- `vm/factory.service` gains `ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i`, so that systemd runs it as the user `factory` after every end of `factory-run` (a stop, a crash before the restart). Its failure, or no container to stop, never fails the unit. Every other line of the unit stays.
- `vm/setup.sh` installs the new unit as it installs it today (a machine whose installed unit differs from the checkout gets the existing message, which names the operator guide's *The rebuild after a merge*).

## Acceptance criteria

1. The argument list of a container start, for an agent run and for a project command, holds the two words `--label`, `factory.instance=<instance>` next to each other, after `--rm`, with the instance given to `PodmanRuns`. Rows: `launch` with two instance names, and one row through `run`, to show that the project-command path carries the label too.
2. `vm/factory.service` holds the `ExecStopPost` line of the Interface exactly once, after `ExecStart`, and every line it held before is unchanged.
3. The wiring gives `PodmanRuns` the settings' instance: the container adapter that `factory.entry.wiring.build_boundaries` builds from settings whose `instance` is a given name starts containers whose argument list holds `--label`, `factory.instance=<that name>` next to each other.
4. `make check` stays green. No test starts a real container: the tests run inside a check container. The human checks the stop on the machine after the merge (decision 20).
5. docs: `docs/operator-guide.md`: where it describes stopping or rebuilding the service, one paragraph saying that a stop ends the instance's running agent and check containers, that a stage cut off this way is taken up again by the next start, and that a machine set up before this story installs the new `vm/factory.service` by hand (`install -m 0644` to `/etc/systemd/system/factory@.service`, then `systemctl daemon-reload`). `docs/decisions.md`: one entry stating that the instance's containers carry a label and the unit stops them after every end of the service, and why (rootless podman puts the containers outside the service's cgroup), with the rejected alternatives (`KillMode`, which cannot reach a scope of another systemd; a stop handler in `factory-run`, which does not run after a crash). `README.md` and the project guide: none.

## Smoke test

```bash
grep -c '^ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i$' vm/factory.service
grep -rlF 'factory.instance' src/factory
```

Expect: `1`, then the single line `src/factory/adapters/podman_runs.py`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: The format check passed. I have four questions before the story can move on:

   1. Interface: it names no Python module or signature for the label. `PodmanRuns.launch` in `src/factory/adapters/podman_runs.py` builds the `podman run` argument list. Its `__init__(executable, image, workspace, *, time_limit, profile)` has no instance. Please name how the instance reaches it. I would choose a new keyword-only `instance: str` on `PodmanRuns.__init__`, set by the wiring in `factory.entry` from the settings' `FACTORY_INSTANCE`, with `launch` adding `--label factory.instance=<instance>`. Should the parameter be required or have a default? Without this, two coders will write two different constructors and the tester cannot write the test.

   2. Criterion 1: "the two kinds of start, agent run and project command" is not testable as written. Does every agent call and every project command go through `PodmanRuns.launch`? If not, name the other construction sites. If so, say that. Then the rows would be two instance names against `launch`'s argv. Please also say which one word order is expected: `--label` followed by `factory.instance=<instance>` as separate words, or `--label=factory.instance=<instance>`.

   3. Smoke test: the second command's `Expect:` ("the path of the module that adds the label") is not checkable. It gives `head -1` of an unordered recursive grep, so the path is not fixed. I would choose `grep -rln 'factory.instance' src/factory` with `Expect:` the single line `src/factory/adapters/podman_runs.py`, or whichever module you intend.

   4. Rules without a failing side:
      - "Containers that do not carry the label, another instance's included, are not touched" has no criterion. Please say whether it is covered by criterion 2's exact line, or by a test of its own. Two instance names in criterion 1 would only show that the label differs.
      - "Its failure, or no container to stop, never fails the unit" rests on the `-` prefix in the pinned line. I would accept that criterion 2 pins it, but please confirm.
4. 2026-11-03 human: Answers to intake's four questions:

   1. Yes: a new keyword-only `instance: str` on `PodmanRuns.__init__`, set by the wiring in `factory.entry.wiring` from the settings' instance (`FACTORY_INSTANCE`).
   2. Yes: every container start goes through `PodmanRuns.launch`. It is the only `ContainerRuns` that starts podman, built once in the wiring; agent runs call `launch` through `agent_launch`, and project commands call `run`, which calls `launch`. So the rows are two instance names against `launch`'s argument list, plus one row through `run`, to show that the project-command path carries the label too. The expected word order is the two words `--label`, `factory.instance=<instance>` next to each other, after `--rm`.
   3. Take your proposal: `grep -rln 'factory.instance' src/factory`, with `Expect:` the single line `src/factory/adapters/podman_runs.py`.
   4. Both are covered by criterion 2's exact line. The filter names `label=factory.instance=%i`, so another instance's containers and unlabelled ones do not match it, and the `-` prefix is what keeps a failure or an empty match from failing the unit. No test of their own. The human checks both on vm after the merge (decision 20).

   — Kumpel, for the human who owns this project
   <!-- kumpel -->
5. factory: started intake as vm.
6. intake: accepted
   - Interface: after the human's answer (journal entry 4) it names `PodmanRuns.launch` in `src/factory/adapters/podman_runs.py`, a required keyword-only `instance: str` on `PodmanRuns.__init__` set by `factory.entry.wiring`, the word order (`--label`, `factory.instance=<instance>` after `--rm`), the unit line and the `vm/setup.sh` behaviour. I wrote the first two into the Interface from entry 4 (the human's edit carried in, not mine).
   - Criteria: 1 now has rows for `launch` with two instance names and one through `run`, each checkable against the argument list (also from entry 4). 2 pins the exact `ExecStopPost` line once, after `ExecStart`, with the other lines unchanged. That covers the Interface's rules that other instances' and unlabelled containers are untouched, and that a failure never fails the unit, both through the `-` prefix and the `label=…=%i` filter. Entry 4 says so, and the human checks both on vm after the merge (decision 20). Criterion 3 is the check, and 4 is the docs criterion.
   - Smoke test: commands are runnable. The second is now `grep -rln 'factory.instance' src/factory`, and its Expect is the single line `src/factory/adapters/podman_runs.py` (from entry 4). The first has Expect `1`.
   - Architecture: the label is added in the adapters layer, the one wrapper that starts podman. The instance comes from the entry-layer wiring, so the layers stay intact. The unit change is under `vm/`.
   - Scope: within F0048 (decision 20, built first). Nothing in "Out of scope" is touched, and no existing test is changed.
7. factory: started tests as vm.
8. tester: I wrote the tests for criteria 1 and 2. Both fail for the right reason. I stopped there: the Interface cannot be met unless tests written by other stories change. Intake's entry said "no existing test is changed", and that does not hold. CLAUDE.md says I may change those tests only with your leave, so I am asking.

   What breaks once the Interface is built:
   - A required keyword-only `instance` on `PodmanRuns.__init__` makes every call that leaves it out raise `TypeError`. There are 14 such calls: `tests/conftest.py:446` (fixture `runs`), `tests/container_extra_support.py:39`, `tests/adapters/test_podman_timeout_status.py:44`, `tests/adapters/test_podman_runs_fence.py:76`, `tests/adapters/test_podman_runs.py:130`, `tests/adapters/test_podman_runs_results.py:28,161,201,202`, and `tests/adapters/test_podman_runs_job_profile.py:29,44,45,159,206`.
   - Three tests pin the whole `podman run` argument list. The label words make each of them fail:
     - `test_podman_runs.py::test_launch_pins_the_podman_command_line`
     - the list at `test_podman_runs_fence.py:43`
     - the list at `test_podman_runs_job_profile.py:67`
   - Two tests pin the unit, and the `ExecStopPost` line fails both:
     - `tests/test_vm_service.py::test_each_section_holds_exactly_its_keys[service]` lists the Service keys exactly.
     - `tests/test_vm_local_environment.py::test_the_unit_reads_the_local_file_after_the_environment_file_and_nothing_else` asserts `text == UNIT`.

   Options:
   (a) You give me leave to change exactly these tests:
      - Pass `instance=` at each of the 14 calls. The value would be one shared constant `INSTANCE = "vm"` in `tests/podman_support.py`.
      - Put `"--label", "factory.instance=vm"` in the three pinned lists, directly after `"--rm"`.
      - Add `("ExecStopPost", "-/usr/bin/podman stop --filter label=factory.instance=%i")` after `RestartSec` in the Service row of `test_vm_service.py`.
      - Add the same line to `UNIT` in `test_vm_local_environment.py`, after the `RestartSec=15` line.
      The tests keep their names and check the same things otherwise. This also decides two exact positions:
      - The label goes directly after `--rm`, before the isolation words. The Interface only says "after `--rm`", but the pinned lists need one exact place.
      - The `ExecStopPost` line goes directly after `RestartSec=15`. The Interface only says "after `ExecStart`".
      Please confirm both positions or name others.
   (b) Make `instance` optional with a default. This contradicts the Interface ("required") and still leaves five pinned tests red.
   I would choose (a).

   Tests written so far:
   - Criterion 1: `tests/adapters/test_podman_runs_instance_label.py::test_a_container_start_carries_the_instance_label_after_rm`. Rows: `launch` with `vm`, `launch` with `night`, and `run` with `vm` (read from the stand-in podman's recorded call). It checks that `--label` comes after `--rm` and that the next word is `factory.instance=<instance>`.
   - Criterion 2: `tests/test_vm_service_stop.py::test_the_unit_stops_the_instances_containers_after_its_start_line`. It checks the exact `ExecStopPost` line once, after `ExecStart`, and that the remaining lines equal the unit's current lines in order.
   - Criterion 3 (`make check` green) and criterion 4 (docs) have no tests.

   Files created: `tests/adapters/test_podman_runs_instance_label.py`, `tests/test_vm_service_stop.py`.

   Run:
   - `uv run pytest -q` on the two files: 4 failed. Every module imports. The label rows fail because `instance` is not a parameter yet. The unit test fails because the line is missing.
   - `make lint`: green.
9. 2026-11-03 human: (a), granted as you wrote it. You have leave to change exactly these tests and nothing else in them:
   - `instance=` at the 14 calls, from one shared constant `INSTANCE = "vm"` in `tests/podman_support.py`;
   - `"--label", "factory.instance=vm"` in the three pinned lists;
   - the `ExecStopPost` row in `test_vm_service.py`, and the same line in `UNIT` of `test_vm_local_environment.py`.

   Both positions are confirmed: the label goes directly after `--rm`, before the isolation words, and the `ExecStopPost` line goes directly after `RestartSec=15`. The tests keep their names, and the tester's entry names each changed file.

   — Kumpel, for the human who owns this project
   <!-- kumpel -->
10. factory: started tests as vm.
11. tester: I made the test changes the human granted in entry 9, and only those. I kept the two tests from entry 8 unchanged.

    Criterion to test:
    - criterion 1: `tests/adapters/test_podman_runs_instance_label.py::test_a_container_start_carries_the_instance_label_after_rm`. Rows: `launch-vm`, `launch-night`, `run-vm`.
    - criterion 2: `tests/test_vm_service_stop.py::test_the_unit_stops_the_instances_containers_after_its_start_line`
    - criterion 3 (`make check` green): no test of its own.
    - criterion 4 (docs): no test of its own.

    Earlier test files I changed under the human's leave (entry 9):
    - `tests/podman_support.py`: new shared constant `INSTANCE = "vm"`.
    - `instance=INSTANCE` added at all 14 `PodmanRuns(...)` calls, in:
      - `tests/conftest.py` (fixture `runs`)
      - `tests/container_extra_support.py`
      - `tests/adapters/test_podman_timeout_status.py`
      - `tests/adapters/test_podman_runs_fence.py`
      - `tests/adapters/test_podman_runs.py`
      - `tests/adapters/test_podman_runs_results.py` (4 calls)
      - `tests/adapters/test_podman_runs_job_profile.py` (5 calls)
    - In `tests/conftest.py` the constant is imported as `INSTANCE as PODMAN_INSTANCE`. The name `INSTANCE` was already taken there by `stage_run_support.INSTANCE` ("factory-1"), and ruff flags the redefinition (F811). The value is the same shared constant.
    - `"--label", "factory.instance=vm"` added directly after `"--rm"` in the three pinned argument lists: `test_podman_runs.py::test_launch_pins_the_podman_command_line`, `test_podman_runs_fence.py`, and `test_podman_runs_job_profile.py`.
    - `("ExecStopPost", "-/usr/bin/podman stop --filter label=factory.instance=%i")` added after `RestartSec` in the Service row of `tests/test_vm_service.py`.
    - The same line added after `RestartSec=15` in `UNIT` of `tests/test_vm_local_environment.py`.
    - Every test keeps its name and otherwise checks the same things. A few calls were rewrapped by `ruff format`.

    Files created (in entry 8): `tests/adapters/test_podman_runs_instance_label.py`, `tests/test_vm_service_stop.py`.

    Modules the test run could not import: none. Every module imports.

    Run: one `uv run pytest -q` over the two new files and the seven changed test modules. It fails for the right reason. `PodmanRuns` does not accept `instance` yet, so the fixture and test calls raise `TypeError` (shown as errors in setup and failures in the tests). The unit tests fail because `vm/factory.service` has no `ExecStopPost` line yet.

    `make lint`: green. I skipped the type check, as the stage says.

    `lint`: lint: green (0.1 s)
12. factory: started doing as vm.
13. coder: I built the Interface and stopped before handing on: `make lint` fails on one rule, and its fix lies outside my write paths.

    Built (in the working tree):
    - `src/factory/adapters/podman_runs.py`: `PodmanRuns.__init__` gains a required keyword-only `instance: str`. `launch` puts `--label`, `factory.instance=<instance>` directly after `--rm`, with a comment on why: rootless podman places the containers outside the service's cgroup. Agent runs and project commands both go through `launch`, so both carry the label.
    - `src/factory/entry/wiring.py`: passes `instance=settings.instance`.
    - `vm/factory.service`: `ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i` directly after `RestartSec=15`. `vm/setup.sh` needs no change: its `cmp`/`install` already covers the new unit.

    Ran: `ruff format --check`, `mypy --strict` on the two modules, and pytest on the podman adapter tests, the unit tests and `tests/entry`: all green. `ruff check` has one finding left: `src/factory/adapters/podman_runs.py:56:9: PLR0913 Too many arguments in function definition (6 > 5)`. `make check` therefore stops at lint, and I have not run it to the end.

    Question: the Interface pins six constructor arguments (executable, image, workspace, instance, time_limit, profile), and `max-args = 5`. The four earlier cases (`claude_runtime.py`, `opencode_runtime.py`, `make_commands.py`, `oauth_token.py`) each have a per-file ignore in `pyproject.toml`. That file is not in the coder's write paths.
    - (a) You add `"src/factory/adapters/podman_runs.py" = ["PLR0913"]  # the instance label joins the constructor; no noqa in the source` under `[tool.ruff.lint.per-file-ignores]`. Nothing else changes. I would choose (a): it follows the four earlier cases.
    - (b) I put `# noqa: PLR0913` on the constructor. No module in `src` carries a noqa today except the allowed exception in `process.py`, and the existing entries say "no noqa in the source".
    - (c) I fold `time_limit` and `profile` into an options object. That changes the Interface and the tests' calls (a test change).

    Noticed, not touched: the smoke test's `grep -rln 'factory.instance' src/factory` is a regex, and its `.` matches any character. It also lists `src/factory/application/scheduler.py` and `src/factory/domain/settings.py`, whose module docstrings say "factory instance". The Expect (the single line `podman_runs.py`) therefore fails whatever this story does. `grep -rlnF` would print only `src/factory/adapters/podman_runs.py`. Please say whether the smoke test should change to `-F`.

    Refactor step not reached, because check is not green. Journal: entries 4 and 9 already carried into the Description by intake and tester; nothing further changed its meaning.
14. 2026-11-03 human: (a). The per-file ignore is on `main` as commit 6e00f08ce, exactly as you wrote it, with its reason: `"src/factory/adapters/podman_runs.py" = ["PLR0913"]`. The factory merges `main` into the branch when it reopens the work item, so your next run has it. Nothing else changes.

    The smoke test: yes, it changes to `grep -rlF 'factory.instance' src/factory`, with `Expect:` the single line `src/factory/adapters/podman_runs.py`. The coder may not write the work item, so the reviewer writes the `-F` into the smoke test and names it in its entry.

    — Kumpel, for the human who owns this project
    <!-- kumpel -->
15. factory: started doing as vm.
16. coder: `make check` is green, so the work item can go to review. The code is the same as in entry 13; this run did not change it. The human's per-file ignore (commit 6e00f08ce) is now merged into the branch. With it, the `PLR0913` finding is gone, and the whole check passed: lint, types, layers, sast, secrets, licenses and test, ending with `check: green`.

    What was built (already committed from the previous run):
    - `src/factory/adapters/podman_runs.py`: `PodmanRuns.__init__` has a new required keyword-only `instance: str`. `launch` puts `--label` and `factory.instance=<instance>` directly after `--rm`, before the isolation words. A comment there explains why: rootless podman puts the containers outside the service's cgroup. Agent runs and project commands both start through `launch`, so both carry the label.
    - `src/factory/entry/wiring.py`: passes `instance=settings.instance`.
    - `vm/factory.service`: `ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i`, directly after `RestartSec=15`.
    - `vm/setup.sh`: unchanged. It already compares the installed unit with the checkout and installs or reports as before.

    Main choice: the label is added in the one place that starts every container, `launch`, so no caller can forget it. I rejected passing the label in from each caller (`agent_launch` and `run`). That would give two places to keep in step, and a later way of starting a container could miss it.

    Refactor: I read the diff again and found nothing to change.

    Smoke test, run by hand:
    - The `grep -c` on the unit prints `1`.
    - `grep -rlF 'factory.instance' src/factory` prints only `src/factory/adapters/podman_runs.py`.
    - As the human said in entry 14, the reviewer still has to write the `-F` into the work item's smoke test.

    The journal did not change what the task means beyond what intake and the tester had already written into the Description, so I left the Description alone.

    Noticed, not touched: the per-file ignore's comment in `pyproject.toml:65` names the work item id (`F0048-S0016`). The repository's rule keeps work item ids out of code and configuration. It is the human's commit, so I left it.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
17. factory: started review as vm.
18. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. The code meets the Interface. `PodmanRuns.__init__` takes a required keyword-only `instance`. `launch` puts `--label`, `factory.instance=<instance>` directly after `--rm` and explains why in a comment. The wiring passes `settings.instance`. The unit has the `ExecStopPost` line after `RestartSec=15`. The coder's `make check` was green (entry 16). Architecture: the label lives in the one podman wrapper (adapters), and the wiring stays in entry. Security: the label is one argv word, with no shell and no silencing marker. Docs criterion: it still says what the documenter must write.

    Findings:
    1. criterion 3 added: it needs its test. The Interface says `factory.entry.wiring` sets the instance from the settings' instance, but no test checks it. A wiring that passed a constant or the wrong field would keep every test green, and the unit's `label=factory.instance=%i` filter would then match nothing. The test can follow `tests/entry/test_wiring_container_profile.py`: build settings with a given `instance`, call `build_boundaries(...).containers.launch(...)`, and assert `--label`, `factory.instance=<that instance>` in the argv. No change under `src/` is needed. The old criteria 3 and 4 are now 4 and 5.
    2. `tests/adapters/test_podman_runs_instance_label.py:13` `_launch_words` copies the helper `_launch_words` in `tests/adapters/test_podman_runs_job_profile.py:31` (`runs.launch(...).argv` with `working_directory="/work/checkout"`). Fix: the tester moves one helper to `tests/podman_support.py` under the standing leave, and both modules use it (the parametrized row can wrap it in a lambda).

    Smoke test corrected on the human's word (entry 14): `grep -rln 'factory.instance' src/factory` -> `grep -rlF 'factory.instance' src/factory`. The Expect is unchanged.

    Earlier tests:
    - `tests/adapters/test_podman_runs.py`: the human's leave, entry 9.
    - `tests/adapters/test_podman_runs_fence.py`: the human's leave, entry 9.
    - `tests/adapters/test_podman_runs_job_profile.py`: the human's leave, entry 9.
    - `tests/adapters/test_podman_runs_results.py`: the human's leave, entry 9.
    - `tests/adapters/test_podman_timeout_status.py`: the human's leave, entry 9.
    - `tests/conftest.py`: the human's leave, entry 9. The `INSTANCE as PODMAN_INSTANCE` import is the same shared constant, renamed only to avoid F811.
    - `tests/container_extra_support.py`: the human's leave, entry 9.
    - `tests/podman_support.py`: the human's leave, entry 9 (the shared constant `INSTANCE = "vm"`).
    - `tests/test_vm_local_environment.py`: the human's leave, entry 9.
    - `tests/test_vm_service.py`: the human's leave, entry 9.
19. factory: started doing as vm.
20. coder: Both of the reviewer's findings in entry 18 are test changes, so this round changes no code. The work goes back to the tester for two things:

    1. **Criterion 3 needs its test.** The reviewer added this criterion: the wiring gives `PodmanRuns` the settings' instance. No code change is needed, because `src/factory/entry/wiring.py` already passes `instance=settings.instance`. The new test follows `tests/entry/test_wiring_container_profile.py`. It builds settings with a given `instance`, calls `factory.entry.wiring.build_boundaries(...).containers.launch(...)`, and asserts that the argument list holds `--label`, `factory.instance=<that instance>` next to each other.
    2. **Move the copied helper.** `_launch_words` exists twice: in `tests/adapters/test_podman_runs_instance_label.py:13` and in `tests/adapters/test_podman_runs_job_profile.py:31`. The tester moves it to `tests/podman_support.py` and changes both modules to use it from there. CLAUDE.md's standing leave to move a shared test helper covers this. Both tests keep their names and check the same things.

    What I built is unchanged since entry 16:
    - `src/factory/adapters/podman_runs.py`: the label, placed in `launch`.
    - `src/factory/entry/wiring.py`: passes the instance.
    - `vm/factory.service`: the `ExecStopPost` line.

    The main choice also stands: the label goes in `launch`, the one place every container start passes through. I rejected adding it at each caller, because a later way of starting a container could miss it.

    There is no refactor and I did not run `make check` this round, because nothing under `src/` or `vm/` changed. The last full run (entry 16) ended `check: green`.

    The journal did not change the task's meaning beyond what the Description already holds. The reviewer has already written criterion 3 and the smoke test's `-F` into the Description.

    Noticed, not touched: the comment on the per-file ignore at `pyproject.toml:65` still names the work item id. That was the human's commit (entry 16).
21. factory: started tests as vm.
22. tester: I made the two test changes the coder named in entry 20, which come from the reviewer's findings in entry 18.

    1. **New test for criterion 3.** It follows `tests/entry/test_wiring_container_profile.py`. It builds `InstanceSettings` with a given `instance`, takes `build_boundaries(...).containers`, and checks two things: the adapter is a `PodmanRuns`, and its launch argv has `factory.instance=<instance>` directly after `--label`. It runs with two instance names (`factory-1`, `night`), so a wiring that passed a constant fails it.
    2. **Helper moved.** Under CLAUDE.md's standing leave to move a shared test helper, `_launch_words` now lives in `tests/podman_support.py` as `launch_words(runs, command, mounts)`. Its body is unchanged from the old copy in `test_podman_runs_job_profile.py`: environment `A=1`, a 90 s limit, working directory `/work/checkout`.
       - `test_podman_runs_job_profile.py` now calls `launch_words` and passes the same arguments as before.
       - In `test_podman_runs_instance_label.py`, the two `launch` rows wrap it in a lambda, as the reviewer suggested. They now launch with the environment and limit of the shared helper (before: `{}` and 30 s). The test checks only the label, so it checks the same thing.
       - Every test keeps its name.

    Criterion → test:
    - criterion 1: `tests/adapters/test_podman_runs_instance_label.py::test_a_container_start_carries_the_instance_label_after_rm` (unchanged in what it checks)
    - criterion 2: `tests/test_vm_service.py`, the test written earlier (unchanged)
    - criterion 3: `tests/entry/test_wiring_instance_label.py::test_the_container_adapter_labels_its_containers_with_the_setting_s_instance`

    Files created: `tests/entry/test_wiring_instance_label.py`.

    Earlier test files changed, under the standing leave to move a shared test helper:
    - `tests/podman_support.py` (gained `launch_words`)
    - `tests/adapters/test_podman_runs_job_profile.py`
    - `tests/adapters/test_podman_runs_instance_label.py`

    Test run: `uv run pytest -q` over the three test modules, all passed (23 passed). They pass because the code is already built. No module failed to import. `make lint`: green. As the stage says, I skipped the type check; the coder's `make check` covers it.

    `lint`: lint: green (0.1 s)
23. factory: started doing as vm.
24. coder: `make check` is green with the tester's new tests (it ended `test: green (80.9 s)`, then `check: green`). They are the criterion 3 test `tests/entry/test_wiring_instance_label.py` and the `launch_words` helper moved to `tests/podman_support.py`. Both pass against the code built earlier, so this round changed no code under `src/` or `vm/`.

    What was built (unchanged since entry 16):
    - `src/factory/adapters/podman_runs.py`: `PodmanRuns.__init__` takes a required keyword-only `instance: str`. `launch` puts `--label`, `factory.instance=<instance>` directly after `--rm`, with a comment on why.
    - `src/factory/entry/wiring.py`: passes `instance=settings.instance`.
    - `vm/factory.service`: `ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i`, directly after `RestartSec=15`.
    - `vm/setup.sh`: unchanged. Its existing compare-and-install already covers the new unit.

    Main choice: the label is added in `launch`, the one place every container start passes through. I rejected adding it at each caller (`agent_launch`, `run`): that is two places to keep in step, and a later way of starting a container could miss it.

    Refactor: I read the diff against `main` again and found nothing to change.

    Journal: entries 18 to 22 added criterion 3 and its test, and the smoke test's `-F`. The reviewer already wrote both into the Description, so I left it alone.

    Noticed, not touched: the comment on the per-file ignore at `pyproject.toml:65` still names the work item id. It is the human's commit.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
