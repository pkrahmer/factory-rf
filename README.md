# factory-rf

The factory, reimplemented by v1 of itself. The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time, with the human approving each story on its pull request. This repository is the second implementation (v1.1): it is built by the first (github.com/pkrahmer/factory), and it is under construction. The package is small so far: four layer packages, the error types, the kill points, the hosting-service interface with its PyGithub client and its fake, the process wrapper, the git wrapper (reading, clone, commit and push, branches and merge, and restoring the checkout with reset, revert and move), the project commands (the make class), the agent-runtime interface with its fake, the `claude -p` runtime (the call, the budget resume and the version query), the data types of a work item (its state, claim and journal records), the journal (append, read, restore), the reader and writer of the work item file, and the story check command.

## Getting started

```bash
uv sync                       # install
make check                    # everything the pipeline checks: lint, types, layers, sast, secrets, licenses, tests
```

When it works, `make check` ends with the line `check: green`. The one command so far checks a story before it starts: `uv run factory-check-story <path>...` (see `docs/operator-guide.md`).

## Where to look next

- `docs/operator-guide.md`: install, configure, the stops and what to do about each
- `docs/project-guide.md`: the guide for agents working on this code
- `docs/decisions.md`: lasting decisions and what was rejected
- `CLAUDE.md`: the rules every change follows (architecture, tests, checks)

## How it is built

Built by the factory (github.com/pkrahmer/factory): features and their user stories live under `factory/features/`, one folder per feature, and one stage agent at a time takes a story through tests, code, review, docs and smoke test. A story's pull request carries the whole story; merging it accepts the story.
