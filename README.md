# kumpel-factory

kumpel-factory builds software from stories. You describe a feature as a few short [stories](docs/project-guide/glossary.md). The factory hands each story to AI agents in turn: one writes the tests, one the code, one reviews it, one updates the docs and one runs a smoke test. Then it opens a pull request, and you approve it or send it back.

It runs on a Linux VM or as a Cloud Run job, with Claude Code or opencode as the agents. It builds this repository too.

## Try it

Install the packages and run the checks. The last line must be `check: green`:

    uv sync
    make check

To run a factory instance you need a prepared machine. [The machine](docs/operator-guide/machine.md) in the operator guide takes you from a fresh VM to a running service. [docs/operator-guide/cloud-run.md](docs/operator-guide/cloud-run.md) does the same for a Cloud Run job.

## Where to read next

- [docs/operator-guide/](docs/operator-guide/README.md): install, configure, the stops and what to do about each, one file per topic. `site.md` there takes a new machine to a running job.
- [docs/project-guide/README.md](docs/project-guide/README.md): the guide for agents and developers who change this code, an index of its files by domain.
- [docs/project-guide/glossary.md](docs/project-guide/glossary.md): the words the factory gives its own meaning.
- [docs/decisions.md](docs/decisions.md): lasting decisions and what was rejected.
- [docs/operator-playbook.md](docs/operator-playbook.md): how the human runs the factory day to day.
- [CLAUDE.md](CLAUDE.md): the rules every change follows (architecture, tests, checks).
- [operator/README.md](operator/README.md): the map of the operator's scripts.
- [demo/README.md](demo/README.md): the demos the factory ships.
- `agents/`: the agent files the factory ships (`agents/agents/<role>.md` and `agents/settings.json`), written in Claude Code's format and read by both runtimes. The stage image copies them to `/etc/factory/agents`.

## Reference

### Console commands

`uv sync` installs these five commands. The operator guide's topic files give the exit status of each.

| Command | What it does |
| --- | --- |
| `factory-run` | runs one instance, one tick per iteration, until a signal stops it |
| `factory-check-story <path>...` | checks a story against the story form before it starts |
| `factory-bill [<work item id>]` | shows what a work item cost |
| `factory-watch` | shows what the next tick would do and the board of features and work items; it changes nothing |
| `factory-health` | prints `healthy`, or one line per stop in force |

### Modules run with `uv run python -m`

- `factory.entry.contract [<folder>]` regenerates the schemas of the records contract. A story that changes a model the contract covers runs it.
- `factory.entry.check_documents` checks the documents and prints one finding per line.
- `factory.entry.check_demos` checks the demos in `demo/`. `make check` runs the same check through `tests/entry/test_demos.py`.

### The document check

The check finds a document that is missing, does not say what the factory does in its own words, or leaves a stop, kill point or fault-injection path unnamed. These findings block in every file.

Three more checks run on the documents:

- The name check finds a module, a repository path or a link that a document writes and that does not exist.
- The settings check compares the *Configuration* tables of the operator guide with the settings the code reads.
- The example check runs the examples of the README and the guides and compares what they print with what they show. [docs/project-guide/style.md](docs/project-guide/style.md) describes the examples.

The findings of these three block only in a file listed in `docs/checked-documents.txt`. The findings of every other file are printed under `Report (not checked yet):`. The command ends with `documents ok (<seconds> s)` when nothing blocks. It is no console script, and `make check` does not run it; `make documents` does.

### The machine

The factory runs as a service on a Linux VM with ZFS and rootless Podman. Every stage runs in throwaway containers on one ZFS dataset. `operator/vm/setup.sh` prepares the VM.

In a Cloud Run job, `operator/vm/job-start.sh` builds the instance at every start; see [cloud-run.md](docs/operator-guide/cloud-run.md).

A project can add tools to its stage image with a file `<project>/factory/stage.Containerfile` on its `main`; see *The project's stage file* in [machine.md](docs/operator-guide/machine.md).

### How it is built

The instance of this factory builds this repository from `factory/pipeline.yml`, with its features and stories under `factory/features/`, one folder for each feature. One stage agent at a time takes a story through tests, code, review, docs and smoke test. A story's pull request carries the whole story, and merging it accepts the story. The history of the first implementation (github.com/pkrahmer/factory), which built this one until the handover of 2026-10-18, is kept at the tag `planning-history-2026-10-19`.
