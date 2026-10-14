# factory-rf

The factory, reimplemented by v1 of itself. The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time, with the human approving each story on its pull request. This repository is the second implementation (v1.1): it is built by the first (github.com/pkrahmer/factory), and it is under construction. What is built so far is the groundwork the pipeline will run on: the wrappers for the outside tools, the work item and its files, the stops and the health status, the pipeline definition, and the claim of a stage with its write paths, guard and undo. The pipeline itself does not run yet. `docs/project-guide.md` describes each part.

## Getting started

```bash
uv sync                       # install
make check                    # everything the pipeline checks: lint, types, layers, sast, secrets, licenses, tests
```

When it works, `make check` ends with the line `check: green`. Three commands exist so far: you run `uv run factory-check-story <path>...` to check a story before it starts and `uv run factory-bill [<work item id>]` to see what a work item cost, and the agent runtime runs `factory-guard` to refuse writes outside a role's write paths (see `docs/operator-guide.md`).

## Where to look next

- `docs/operator-guide.md`: install, configure, the stops and what to do about each
- `docs/project-guide.md`: the guide for agents working on this code
- `docs/decisions.md`: lasting decisions and what was rejected
- `CLAUDE.md`: the rules every change follows (architecture, tests, checks)

## How it is built

Built by the factory (github.com/pkrahmer/factory): features and their user stories live under `factory/features/`, one folder per feature, and one stage agent at a time takes a story through tests, code, review, docs and smoke test. A story's pull request carries the whole story; merging it accepts the story.
