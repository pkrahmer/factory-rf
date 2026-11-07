# kumpel-factory

The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time (on Claude Code, or on opencode when the operator chooses it for an instance), and the human approves each story on its pull request. This repository is its second implementation, v1.1. The first (github.com/pkrahmer/factory) built it until the handover of 2026-10-18; since then v1.1 builds this repository itself (see *How it is built*). `docs/project-guide/README.md` maps every part of the code.

## Getting started

```bash
uv sync                       # install
make check                    # everything the pipeline checks: lint, types, layers, sast, secrets, licenses, tests
```

When it works, `make check` ends with the line `check: green`. An instance runs on a VM that `operator/vm/setup.sh` prepares: see *The machine* in `docs/operator-guide/machine.md`; the guide's topic files also give the exit statuses of the commands you run.

| Command | What it does |
| --- | --- |
| `factory-run` | runs one instance, one tick per iteration, until a signal stops it |
| `factory-check-story <path>...` | checks a story against the story form before it starts |
| `factory-bill [<work item id>]` | shows what a work item cost |
| `factory-watch` | shows what the next tick would do and the board of features and work items; it changes nothing |
| `factory-health` | prints `healthy`, or one line per stop in force |

Beside the five console commands, `uv run python -m factory.entry.contract [<folder>]` regenerates the records contract's schemas. A story that changes a model the contract covers runs it.

`uv run python -m factory.entry.check_documents` checks the documents and prints one finding per line. The document checks find a document that is missing, does not say what the factory does in its own words, or leaves a stop, kill point or fault-injection path unnamed. The name check finds a module, a repository path or a link that a document writes and that does not exist. The settings check compares the operator guide's *Configuration* tables with the settings the code reads. The example check runs the examples of the README and the guides and compares what they print with what they show (see `docs/project-guide/style.md`).

The document checks block in every file. A finding of the name, settings or example check blocks only in a file listed in `docs/checked-documents.txt`. The findings of every other file are printed under `Report (not checked yet):`. The command ends with `documents ok (<seconds> s)` when nothing blocks. It is no console script, and `make check` does not run it.

The factory runs as a service on a Linux VM with ZFS and rootless Podman, and every stage runs in throwaway containers on one ZFS dataset. `operator/vm/setup.sh` prepares the VM; *The machine* in `docs/operator-guide/machine.md` takes you there, and `docs/operator-guide/README.md` is the guide's index. It also runs in a Cloud Run job, whose command `operator/vm/job-start.sh` builds the instance at every start: see *On Cloud Run* in `docs/operator-guide/cloud-run.md`. A project can add tools to its stage image with a file `factory/stage.Containerfile` on its `main`: see *The project's stage file* in `docs/operator-guide/machine.md`.

## Where to look next

- `docs/operator-guide/`: install, configure, the stops and what to do about each, an index `README.md` and one file per topic; *Setting up an operator's machine* in `site.md` takes a new machine to a running job, and `operator/README.md` is the map of the operator's scripts
- `docs/project-guide/README.md`: the guide for agents working on this code, an index of its files by domain
- `agents/`: the agent files the factory ships (`agents/agents/<role>.md` and `agents/settings.json`), written in Claude Code's format and read by both runtimes; the stage image copies them to `/etc/factory/agents`
- `docs/decisions.md`: lasting decisions and what was rejected
- `docs/operator-playbook.md`: how the human runs the factory day to day
- `CLAUDE.md`: the rules every change follows (architecture, tests, checks)
- `demo/`: the demos v1.1 ships, one folder each; `uv run python -m factory.entry.check_demos` checks them (`make check` runs the same check through `tests/entry/test_demos.py`)

## How it is built

Since the handover of 2026-10-18, v1.1's instance builds this repository from `factory/pipeline.yml`, with its features and stories under `factory/features/`, one folder per feature; one stage agent at a time takes a story through tests, code, review, docs and smoke test. A story's pull request carries the whole story; merging it accepts the story. v1's history (its stages, its forms and its features F0001 to F0017) is kept at the tag `planning-history-2026-10-19`.

## Replaced from v1

`factory-watch` has no `--follow` mode; v1's option is an unknown option here.
