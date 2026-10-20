# Story title

A story is one file, `factory/features/<F0018-slug>/backlog/<F0018-S0001-slug>.md`, without front matter. Its first line is its title, `# <what the story builds>`. It has the five sections below, in this order; the factory checks it against this form before a stage moves it forward (`factory-check-story <path>`). The human starts it by moving it to the feature's `in-progress/`; the factory archives it in `done/` when its pull request is merged.

## Description

What the story builds and why, for whom, in a paragraph: what changes, what stays as it is, and what the story leaves to a later one. Every behaviour named here has its own criterion.

## Interface

The modules under `src/factory/` (with their layer: `domain`, `application`, `adapters` or `entry`), the classes and functions the story adds or changes, with their signatures in a code block and their rules as bullets: each rule a sentence a test can check, with every limit on both sides. The test modules the tester writes, mirroring the package under `tests/`. A test another story wrote that this story changes, beyond the standing leave of `CLAUDE.md` (*Tests*), is named here with the leave the feature's `feature.md` gives for it. A change outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`) is the human's, named in `feature.md` under *The human's changes*, never here.

## Acceptance criteria

Numbered 1, 2, 3 and on; each one behaviour a test can check, with its input and its exact result. The sides of one rule (accepted and refused, below and at and above a limit) are one criterion, tested as rows of one parametrized test. The second-to-last criterion is `make check` stays green. The last starts with `docs:` and says what the documenter writes, in which of the four documents (`README.md`, `docs/operator-guide.md`, the project guide under `docs/project-guide/` (its index `README.md` and its files by domain), `docs/decisions.md`), or `none` with the reason.

## Smoke test

Shell blocks the smoke tester runs from the root of the checkout in the container (Linux, nothing listening), each followed by a line `Expect:` that says exactly what the built code prints. A block that needs a file, a repository or a process works in a temporary directory it removes (`d=$(mktemp -d); trap 'rm -rf "$d"' EXIT`) and stops what it started. A block that runs pytest never passes `-q`: `pyproject.toml` already sets it, and at `-qq` pytest prints no summary line.

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
