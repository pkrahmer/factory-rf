# Operator guide

The guide for the person who runs the factory this repository implements: how to install and configure an instance, which stops it can reach and what to do about each. The machine of v1.2, a VM that runs the instance's stages in containers on a ZFS dataset, is described in "The machine" in [machine.md](machine.md). An operator of v1.1's long-lived container finds its guide at the tag `v1.1`; this guide describes the VM alone.

The guide is this index and one file per topic:

- [install.md](install.md): installing the factory, its configuration, a process that refuses to start, the loop and its pauses, and the project's make targets.
- [agent-runtime.md](agent-runtime.md): the agent runtime (Claude Code or opencode, the login, a proxy, a provider's limits) and the agent files.
- [machine.md](machine.md): the machine, the VM with ZFS and rootless Podman that runs every stage, its stage image, its service, its costs and its logs.
- [site.md](site.md): the site file, repeating a trial, and setting up an operator's machine from one site file.
- [cloud-run.md](cloud-run.md): running the factory in a Cloud Run job.
- [health.md](health.md): the preflight and the health check, the factory log and the health status file, and the transcripts.
- [stops.md](stops.md): the stops and what to do about each, what a stage run shows, stalls, the factory's own questions, an event that keeps failing and stops that cannot be done.
- [pipeline.md](pipeline.md): the pipeline definition and checking a story before it starts.
- [records.md](records.md): the records contract, what a work item cost (`factory-bill`) and looking at the remote (`factory-watch`).
- [work-items.md](work-items.md): a feature acceptance, the hand-over at the approval, merges, closes, stale branches, a stage changed by hand, a restart during a stage, an expired lease, and claims, leases and the clock.
- This index: what v1.2 and v1.1 replaced, under "Replaced in v1.2" and "Replaced from v1".

## Replaced in v1.2

What v1.1 did and the machine of v1.2 does not, so that a name you remember from v1.1's guide is not mistaken for a live one. The decision log keeps the reasons ("One snapshot instead of many layers").

- The kernel's write guard (F0044-S0001, F0044-S0002): the wrapper `factory-confine`, which put Landlock rules around every agent call, and the pipeline definition's `tool_paths` are gone. The container is the boundary, the dataset's rollback clears what the agent wrote, and the take copies out only the paths the role may write. A pipeline definition that still holds `tool_paths` is refused.
- The second user (F0044-S0005): the `agent` user, the `sudo` chain that started a call as it and `FACTORY_AGENT_USER` are gone. The agent's container runs as `factory` with `--userns=keep-id` and mounts the dataset only; the token is on the host, which alone pushes.
- The leftovers program (F0044-S0003): `factory.entry.leftovers`, which ended what a call left running, is gone. The end of the call's container ends everything in it.
- The fresh home (F0044-S0004): `factory.entry.fresh_home`, which emptied the agent's home before a call, is gone. The agent's home is `home/` on the dataset, and the rollback to the base clears it before every stage.
- The checkout's hygiene (F0044-S0006): the seal of `.git`, the removal of ignored paths and nested repositories, the re-clone and the stop `nested_repository` are gone. The checks run on a rolled-back copy of the dataset, and only the paths the role may write reach the checkout. The records contract rose to `3.0`.
- The inline environment (F0044-S0008): v1.1's way of running a stage in the factory's own container, and `FACTORY_STAGE_ENVIRONMENT`, which chose between it and the containers, are gone. `ContainerEnvironment` is the only environment; an instance without `FACTORY_DATASET`, `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE` is refused. An environment file that still holds the variable is harmless: nothing reads it.
- The undo (F0044-S0009): `UndoService`, which put back what a run wrote outside its write paths, is gone. The take leaves such changes out of the work tree, and the journal says `The factory left out changes outside the write paths: ...`.
- The Docker path (F0044-S0010): the Docker image, the compose file, the long-lived container with its entrypoint, its health check and `docker exec` are gone, and with them `image/`, apart from the credential helper that moved to `operator/vm/git-credential-factory`. The machine is the VM of "The machine" in [machine.md](machine.md); the stage image (`operator/vm/Dockerfile`) holds the tools alone.

## Replaced from v1

What v1 did and v1.1 does not, so that a file or an option you remember is not mistaken for a live one.

- `factory-watch` has no `--follow` mode and nothing writes the file `factory-last-line`: `--follow` is an unknown option. A file of that name left by v1 is not read and can be deleted.
- v1's leftover files in `.git/` (`factory-run.json`, `factory-tick.lock`, `factory-tick.json`) are neither read nor written; they change nothing and can be deleted.
- This repository's v1 history (v1's `stages.yml`, `TICKET.md`, `FEATURE.md` and its features F0001 to F0017) was `factory/v1/` and is kept at the tag `planning-history-2026-10-19`. Since the handover of 2026-10-18 v1.1 builds this repository from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`.
