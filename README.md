# factory-rf

The factory, reimplemented by v1 of itself. The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time (the agents run on Claude Code, or on opencode when the operator chooses it for an instance), with the human approving each story on its pull request. This repository is the second implementation (v1.1): it was built by the first (github.com/pkrahmer/factory) until the handover of 2026-10-18 and is built by v1.1 itself since then, and it is under construction. What is built so far is the groundwork the pipeline will run on: the wrappers for the outside tools, the work item and its files, the stops and the health status, the pipeline definition, the claim of a stage with its write paths, guard and undo, the stage protocol (one stage run from the pushed claim to the result commit, with stalls and v1's decision rules), and the cost records with the bill, and the records the human can read from outside: the cause recorded on a blocking question and on a stall, the `Human:` line under the cost table (questions answered and hours waited), the stop records published to `factory/stops.jsonl` on `main`, and the records contract of generated JSON Schemas under `src/factory/contract/` (see "The records contract" in `docs/operator-guide.md`). It also reads the remote: the evaluation that picks the next event, the tick with its stops, the dispatcher with its handlers, and `factory-watch`. The handlers start a stage and answer the human's acts on the pull request: comments are copied into the journal, questions are recorded and then posted, a merge archives the story, a close discards it or sends it back, an illegal stage change is moved back, and the pull request is handed over at the approval. After a crash, a restart reruns the dead stage, an expired lease of another instance is taken over, the crash cap asks the human, and the tick deletes a stale branch. The feature acceptance is wired too: a feature whose stories are all archived becomes due, an acceptance reviewer runs on the acceptance's own work item, and the human's merge of its pull request books it accepted while a close books it refused (see "When a feature acceptance is due" in `docs/operator-guide.md`). `factory-run` runs one instance: it reads the settings, prepares the checkout and makes one tick per iteration until a signal stops it. The preflight (with its probe of one agent run) runs in every tick; the repository waiter and the container are built, and the image was built and started once under rootless Podman (the probe of 2026-10-17, without the pins) up to the stop `repository_unavailable`. The first start of 2026-10-17 then brought two instances (Docker Desktop and rootless Podman) up healthy on an empty project, the preflight's probe agent run included. A stage's agent run end to end and a `time_limit` under `sudo` were observed on 2026-10-18, on the todo demo. `docs/project-guide/` describes each part.

## Getting started

```bash
uv sync                       # install
make check                    # everything the pipeline checks: lint, types, layers, sast, secrets, licenses, tests
```

When it works, `make check` ends with the line `check: green`. Six commands exist: you run `uv run factory-run` (with the settings in the environment, see `docs/operator-guide.md`; with an invalid environment it ends with status 2 and a machine stop, or with two lines on standard error when the state directory cannot be written), `uv run factory-check-story <path>...` to check a story before it starts, `uv run factory-bill [<work item id>]` to see what a work item cost and `uv run factory-watch` to see what the next tick would do and the board of features and work items (it reads the last fetch, changes nothing; it reads the same environment as `factory-run`, and with an invalid one it ends with status 2 and a `settings invalid` line on standard error), `uv run factory-health` to read the stops in force (it prints `healthy` and exits 0, or prints one line per stop and exits 1; outside the image, before `factory-run` has started, it prints `no health status: <path> is missing` and exits 1; `--state-directory <path>` names the state directory), and the agent runtime runs `factory-confine` to start every agent run with its writes confined by the kernel (see `docs/operator-guide.md`).

Beside the seven console commands, `uv run python -m factory.entry.contract [<folder>]` regenerates the records contract's schemas (a story that changes a model the contract covers runs it), and `uv run python -m factory.entry.check_documents` checks these documents (they exist, say what v1.1 does in its own words, and name every stop, kill point and fault-injection path); it prints `documents ok` or one finding per line. It is no console script, and `make check` does not run it.

## Where to look next

- `docs/operator-guide.md`: install, configure, the stops and what to do about each
- `docs/project-guide/README.md`: the guide for agents working on this code, an index of its files by domain
- `docs/decisions.md`: lasting decisions and what was rejected
- `CLAUDE.md`: the rules every change follows (architecture, tests, checks)
- `demo/`: the demos v1.1 ships, one folder each; `uv run python -m factory.entry.check_demos` checks them (`make check` runs the same check through `tests/test_demos.py`)

## How it is built

Since the handover of 2026-10-18, v1.1's instance builds this repository from `factory/pipeline.yml`, with its features and stories under `factory/features/`, one folder per feature; one stage agent at a time takes a story through tests, code, review, docs and smoke test. A story's pull request carries the whole story; merging it accepts the story. v1's history (its stages, its forms and its features F0001 to F0017) is kept at the tag `planning-history-2026-10-19`.

## Replaced from v1

`factory-watch` has no `--follow` mode; v1's option is an unknown option here.
