# factory-rf

The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time (on Claude Code, or on opencode when the operator chooses it for an instance), and the human approves each story on its pull request. This repository is its second implementation, v1.1. The first (github.com/pkrahmer/factory) built it until the handover of 2026-10-18; since then v1.1 builds this repository itself (see *How it is built*). `docs/project-guide/README.md` maps every part of the code.

## Getting started

```bash
uv sync                       # install
make check                    # everything the pipeline checks: lint, types, layers, sast, secrets, licenses, tests
```

When it works, `make check` ends with the line `check: green`. An instance runs on a VM that `vm/setup.sh` prepares: see the chapter *The machine* in `docs/operator-guide.md`, which also gives the exit statuses of the commands you run.

| Command | What it does |
| --- | --- |
| `factory-run` | runs one instance, one tick per iteration, until a signal stops it |
| `factory-check-story <path>...` | checks a story against the story form before it starts |
| `factory-bill [<work item id>]` | shows what a work item cost |
| `factory-watch` | shows what the next tick would do and the board of features and work items; it changes nothing |
| `factory-health` | prints `healthy`, or one line per stop in force |

Beside the five console commands, `uv run python -m factory.entry.contract [<folder>]` regenerates the records contract's schemas (a story that changes a model the contract covers runs it), and `uv run python -m factory.entry.check_documents` checks these documents (they exist, say what v1.1 does in its own words, and name every stop, kill point and fault-injection path); it prints `documents ok` or one finding per line. It is no console script, and `make check` does not run it.

The factory runs as a service on a Linux VM with ZFS and rootless Podman, and every stage runs in throwaway containers on one ZFS dataset. `vm/setup.sh` prepares the VM; the chapter *The machine* of `docs/operator-guide.md` takes you there, and what v1.1 did differently is under *Replaced in v1.2* in the same guide.

## Where to look next

- `docs/operator-guide.md`: install, configure, the stops and what to do about each
- `docs/project-guide/README.md`: the guide for agents working on this code, an index of its files by domain
- `docs/decisions.md`: lasting decisions and what was rejected
- `docs/operator-playbook.md`: how the human runs the factory day to day
- `CLAUDE.md`: the rules every change follows (architecture, tests, checks)
- `demo/`: the demos v1.1 ships, one folder each; `uv run python -m factory.entry.check_demos` checks them (`make check` runs the same check through `tests/test_demos.py`)

## How it is built

Since the handover of 2026-10-18, v1.1's instance builds this repository from `factory/pipeline.yml`, with its features and stories under `factory/features/`, one folder per feature; one stage agent at a time takes a story through tests, code, review, docs and smoke test. A story's pull request carries the whole story; merging it accepts the story. v1's history (its stages, its forms and its features F0001 to F0017) is kept at the tag `planning-history-2026-10-19`.

## Replaced from v1

`factory-watch` has no `--follow` mode; v1's option is an unknown option here.
