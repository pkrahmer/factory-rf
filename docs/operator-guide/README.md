# Operator guide

The guide for the person who runs an [instance](../project-guide/glossary.md) of the factory this repository implements. It shows how to install and configure an instance, how to watch it, and what to do when it [stops](../project-guide/glossary.md).

An instance usually runs on a VM with ZFS and rootless Podman, where every [stage](../project-guide/glossary.md) runs in throwaway containers on one ZFS [dataset](../project-guide/glossary.md). It can also run without ZFS, in a Cloud Run job ([cloud-run.md](cloud-run.md)). "The machine" in [machine.md](machine.md) describes that VM. You know Linux, git and a terminal; you do not need to read the code.

## Where to start

1. Prepare the machine and install the factory: read "The machine" in [machine.md](machine.md), then [install.md](install.md).
2. Set the instance's settings: read "Configuration" in [install.md](install.md).
3. Check that the instance is healthy: read [health.md](health.md).
4. When the instance stops, look the stop up in "The stops" in [stops.md](stops.md).

## The files of the guide

The guide is this index and one file per topic:

| File | What it covers |
| --- | --- |
| [install.md](install.md) | Installing the factory, its configuration, a process that refuses to start, the loop and its pauses, and the project's make targets. |
| [agent-runtime.md](agent-runtime.md) | The agent runtime (Claude Code or opencode), the login, a proxy, a provider's limits and the agent files. |
| [machine.md](machine.md) | The VM with ZFS and rootless Podman that runs every stage, its stage image, its service, its costs and its logs. |
| [site.md](site.md) | The site file, repeating a trial, and setting up an operator's machine from one site file. |
| [cloud-run.md](cloud-run.md) | Running the factory in a Cloud Run job. |
| [health.md](health.md) | The preflight and the health check, the factory log and the health status file, and the transcripts. |
| [stops.md](stops.md) | The stops and what to do about each, what a stage run shows, [stalls](../project-guide/glossary.md), the factory's own questions, an event that keeps failing and stops that cannot be done. |
| [pipeline.md](pipeline.md) | The [pipeline definition](../project-guide/glossary.md) and checking a [story](../project-guide/glossary.md) before it starts. |
| [records.md](records.md) | The records contract, what a [work item](../project-guide/glossary.md) cost (`factory-bill`) and looking at the remote (`factory-watch`). |
| [work-items.md](work-items.md) | A [feature](../project-guide/glossary.md) [acceptance](../project-guide/glossary.md), the hand-over at the [approval](../project-guide/glossary.md), merges, closes, stale branches, a stage changed by hand, a restart during a stage, an expired [lease](../project-guide/glossary.md), and [claims](../project-guide/glossary.md), leases and the clock. |

The reasons behind the factory's design are in the decision log, [decisions.md](../decisions.md).

## Reference

How the [stage environment](../project-guide/glossary.md) works and what the instance refuses.

### What the stage environment is

- Every stage runs in containers. The stage environment is the containers. An instance without `FACTORY_WORKSPACE` or `FACTORY_STAGE_IMAGE` is refused. With `zfs` snapshots it also needs `FACTORY_DATASET`. With `FACTORY_SNAPSHOTS=copy` it needs `FACTORY_SNAPSHOT_BASE` instead and runs without a dataset. A setting file that holds a variable the factory does not read, such as `FACTORY_STAGE_ENVIRONMENT`, is harmless: nothing reads it.
- The container is the boundary. On the VM the agent's container runs as the user `factory` with `--userns=keep-id`; a Cloud Run job runs without the user namespace (see [cloud-run.md](cloud-run.md)). The dataset is the only writable mount; the login files are mounted read-only at their own paths. The token is on the host, which alone pushes.
- The agent's home is `home/` on the dataset. The rollback to the [base](../project-guide/glossary.md) clears it before every stage, and it clears whatever else a run left on the dataset.
- The factory ends everything an agent's call started by ending the call's container.
- The checks run on a rolled-back copy of the dataset. After a run, the [take](../project-guide/glossary.md) copies into the work tree only the changed paths the [role](../project-guide/glossary.md) may write. The [journal](../project-guide/glossary.md) records what it left out as `The factory left out changes outside the write paths: ...`.
- A pipeline definition that holds `tool_paths` is refused: no tool call is judged, and the [write paths](../project-guide/glossary.md) are the only rule.
- The stage image ([Dockerfile](../../operator/vm/Dockerfile)) holds the tools alone. The credential helper is [git-credential-factory](../../operator/vm/git-credential-factory), which [setup.sh](../../operator/vm/setup.sh) installs as `/usr/local/bin/git-credential-factory`.

### Command-line options

- `factory-watch` takes no options but `--help`; it has no follow mode.

### This repository's own history

The planning history of this repository (the first pipeline's forms and its first features) is kept at the tag `planning-history-2026-10-19`. The factory builds this repository from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`.
