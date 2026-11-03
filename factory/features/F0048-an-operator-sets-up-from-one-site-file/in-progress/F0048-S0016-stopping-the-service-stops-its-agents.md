---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-03T06:34:18.379856Z'
  lease_duration: 60
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
---

# Stopping the service stops its agents

<!-- written by the human on 2026-11-03 from what the acceptance F0048-A0001 met (decision 20) -->

## Description

The factory starts every agent call and every check in a container with `podman run --rm`. Rootless podman with systemd's cgroup manager places the container and its `conmon` in a scope of the `factory` user's own systemd, outside the cgroup of the service `factory@<instance>`. So `systemctl stop factory@vm` ends `factory-run` and the `podman run` client, while the container goes on until it ends or podman's `--timeout` ends it. The unit has `Restart=always`: after a crash, or after a stop and a start, the new factory finds the stage without an owner and starts a second agent on the same dataset while the first one still writes into it. The acceptance F0048-A0001 met exactly this on 2026-11-03: a rebuild stopped the service during the first acceptance run, and a second run worked beside it in one dataset.

This story makes a stop of the service stop the instance's containers. Every container the factory starts carries a label with the instance's name, and the unit stops the containers with that label after the service's process has ended, whether the service was stopped or crashed. Containers that do not carry the label, another instance's included, are not touched. Nothing else about how a container runs changes.

## Interface

- Every container the factory starts, for an agent run and for a project command, carries the label `factory.instance=<FACTORY_INSTANCE>`.
- `vm/factory.service` gains `ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i`, so that systemd runs it as the user `factory` after every end of `factory-run` (a stop, a crash before the restart). Its failure, or no container to stop, never fails the unit. Every other line of the unit stays.
- `vm/setup.sh` installs the new unit as it installs it today (a machine whose installed unit differs from the checkout gets the existing message, which names the operator guide's *The rebuild after a merge*).

## Acceptance criteria

1. The argument list of a container start, for an agent run and for a project command, holds `--label` `factory.instance=<instance>` with the instance of the factory's settings. Rows: the two kinds of start, and two instance names.
2. `vm/factory.service` holds the `ExecStopPost` line of the Interface exactly once, after `ExecStart`, and every line it held before is unchanged.
3. `make check` stays green. No test starts a real container: the tests run inside a check container. The human checks the stop on the machine after the merge (decision 20).
4. docs: `docs/operator-guide.md`: where it describes stopping or rebuilding the service, one paragraph saying that a stop ends the instance's running agent and check containers, that a stage cut off this way is taken up again by the next start, and that a machine set up before this story installs the new `vm/factory.service` by hand (`install -m 0644` to `/etc/systemd/system/factory@.service`, then `systemctl daemon-reload`). `docs/decisions.md`: one entry stating that the instance's containers carry a label and the unit stops them after every end of the service, and why (rootless podman puts the containers outside the service's cgroup), with the rejected alternatives (`KillMode`, which cannot reach a scope of another systemd; a stop handler in `factory-run`, which does not run after a crash). `README.md` and the project guide: none.

## Smoke test

```bash
grep -c '^ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i$' vm/factory.service
grep -rn 'factory.instance' src/factory | head -1 | cut -d: -f1
```

Expect: `1`, then the path of the module that adds the label.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
