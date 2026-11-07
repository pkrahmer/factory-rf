# kumpel-factory

kumpel-factory builds software from [stories](docs/project-guide/glossary.md). You describe a [feature](docs/project-guide/glossary.md) as a few short stories. The factory hands each story to AI agents in turn: one writes the tests, one the code, one reviews it and one updates the docs. A last one runs a smoke test. Each story gets a draft pull request when its work starts. When the agents are done, you approve it or send it back.

It runs on a Linux VM or as a Cloud Run job, with Claude Code or opencode as the agents. It builds this repository too.

## License

kumpel-factory is licensed under the Apache License 2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE). Each file of code and each script of the operator names its license in its first line, `SPDX-License-Identifier: Apache-2.0`, so that a copied file says so too.

## Try it

Install the packages with `uv sync`, then run the checks. `make check` runs lint, types, layers, sast, secrets, licenses and tests. The last line must be `check: green`:

```console
$ make check
...
check: green
```

To run a factory [instance](docs/project-guide/glossary.md) you need a prepared machine. [The machine](docs/operator-guide/machine.md) in the operator guide takes you from a fresh VM to a running service. *On Cloud Run* in [docs/operator-guide/cloud-run.md](docs/operator-guide/cloud-run.md) does the same for a Cloud Run job.

## Where to read next

- [docs/operator-guide/](docs/operator-guide/README.md): install, configure, the [stops](docs/project-guide/glossary.md) and what to do about each, one file per topic. *Setting up an operator's machine* in [site.md](docs/operator-guide/site.md) takes a new machine to a running job.
- [docs/project-guide/README.md](docs/project-guide/README.md): the guide for agents and developers who change this code, an index of its files by domain.
- [docs/project-guide/glossary.md](docs/project-guide/glossary.md): the words the factory gives its own meaning.
- [docs/decisions.md](docs/decisions.md): lasting decisions and what was rejected.
- [docs/operator-playbook.md](docs/operator-playbook.md): how the human runs the factory day to day.
- [CLAUDE.md](CLAUDE.md): the rules every change follows (architecture, tests, checks).
- [operator/README.md](operator/README.md): the map of the operator's scripts.
- [demo/README.md](demo/README.md): the demos the factory ships, one folder each.
- `agents/`: the agent files the factory ships (`agents/agents/<role>.md` and `agents/settings.json`), written in Claude Code's format and read by both runtimes. The stage image copies them to `/etc/factory/agents`.

## The folders

- `agents/` The agent files the factory ships, one per [role](docs/project-guide/glossary.md), with their settings; see [its README](agents/README.md).
- `demo/` The demo projects the factory builds from an empty repository; see [its README](demo/README.md).
- `docs/` The operator guide, the project guide, the decision log and the playbook; see [its README](docs/README.md).
- `factory/` The human's: the [pipeline definition](docs/project-guide/glossary.md), the forms and the features with their stories that this factory builds.
- `operator/` What an operator runs next to an instance: the skill, the scripts and the VM setup; see [its README](operator/README.md).
- `planning/` The human's working files, which no [stage](docs/project-guide/glossary.md) reads or writes; see [its README](planning/README.md).
- `security/` The semgrep rules and the accepted duplicate findings; see [its README](security/README.md).
- `session-logs/` The human's local copies of session transcripts, kept out of git.
- `src/` The `factory` package, ordered by area; see [its README](src/factory/README.md).
- `tests/` The pytest suite, mirroring the package; see [its README](tests/README.md).

## Reference

### Console commands

`uv sync` installs these five commands. The operator guide's topic files give the exit status of each.

| Command | What it does |
| --- | --- |
| `factory-run` | runs one instance, one [tick](docs/project-guide/glossary.md) per iteration, until a signal stops it |
| `factory-check-story <path>...` | checks a story against the story form before it starts |
| `factory-bill [<work item id>]` | shows what a [work item](docs/project-guide/glossary.md) cost |
| `factory-watch` | shows what the next tick would do and the board of features and work items; it changes nothing |
| `factory-health` | prints `healthy`, or one line per stop in force |

### Modules run with `uv run python -m`

- `factory.entry.contract [<folder>]` regenerates the schemas of the records contract. A story that changes a model the contract covers runs it.
- `factory.entry.check_documents` checks the documents and prints one finding per line.
- `factory.entry.check_demos` checks the demos in `demo/`. `make check` runs the same check through `tests/entry/test_demos.py`.

### The document check

The check finds a document that is missing or that does not say what the factory does in its own words. It finds a stop whose row in the operator guide's stops file does not name its destination. It finds an operator guide that lacks *Install*, *Configuration* or *The stops*. It finds a project guide that lacks *Kill points* or *Fault-injection paths*. It also finds one whose tables there leave out a case the code tests. These findings block in every file.

Three more checks run on the documents:

- The name check finds a module, a repository path or a link that a document writes and that does not exist.
- The settings check compares the *Configuration* tables of the operator guide with the settings the code reads.
- The example check runs the examples of the README and the guides and compares what they print with what they show. [docs/project-guide/style.md](docs/project-guide/style.md) describes the examples.

The findings of these three block only in a file listed in `docs/checked-documents.txt`. The findings of every other file are printed under `Report (not checked yet):`. The command ends with `documents ok (<seconds> s)` when nothing blocks. It is no console script, and `make check` does not run it; `make documents` does.

### The machine

The factory runs as a service on a Linux VM with ZFS and rootless Podman. Every [stage](docs/project-guide/glossary.md) runs in throwaway containers on one ZFS [dataset](docs/project-guide/glossary.md). `operator/vm/setup.sh` prepares the VM.

In a Cloud Run job, `operator/vm/job-start.sh` builds the instance at every start; see *On Cloud Run* in [cloud-run.md](docs/operator-guide/cloud-run.md).

A project can add tools to its stage image with a file `<project>/factory/stage.Containerfile` on its `main`; see *The project's stage file* in [machine.md](docs/operator-guide/machine.md).

### How it is built

The instance of this factory builds this repository from `factory/pipeline.yml`, with its features and stories under `factory/features/`, one folder for each feature. One stage agent at a time takes a story through tests, code, review, docs and smoke test. A story's pull request carries the whole story, and merging it accepts the story. The planning history is kept at the tag `planning-history-2026-10-19`; [decisions.md](docs/decisions.md) says what the tag holds.
