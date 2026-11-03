---
stage: tests
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 512
comments_read: [6597509758]
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
3. `make check` stays green. No test starts a real container: the tests run inside a check container. The human checks the stop on the machine after the merge (decision 20).
4. docs: `docs/operator-guide.md`: where it describes stopping or rebuilding the service, one paragraph saying that a stop ends the instance's running agent and check containers, that a stage cut off this way is taken up again by the next start, and that a machine set up before this story installs the new `vm/factory.service` by hand (`install -m 0644` to `/etc/systemd/system/factory@.service`, then `systemctl daemon-reload`). `docs/decisions.md`: one entry stating that the instance's containers carry a label and the unit stops them after every end of the service, and why (rootless podman puts the containers outside the service's cgroup), with the rejected alternatives (`KillMode`, which cannot reach a scope of another systemd; a stop handler in `factory-run`, which does not run after a crash). `README.md` and the project guide: none.

## Smoke test

```bash
grep -c '^ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i$' vm/factory.service
grep -rln 'factory.instance' src/factory
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
