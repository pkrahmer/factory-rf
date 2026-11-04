# The VM's files and the project template live in `operator/`

## Description

Two folders at the root of the repository belong to the operator: `vm/` holds what sets up and runs an instance on a VM (`setup.sh`, `job-start.sh`, `factory.service`, `git-credential-factory`) and the base image's `Dockerfile`, and `template/` holds what the operator copies into a new project (`CLAUDE.md`, `Makefile`, `factory/`). `operator/` already holds the operator's other tools, among them `operator/job/` for Cloud Run. This story moves `vm/` to `operator/vm/` and `template/` to `operator/template/`, so that everything about where an instance runs and how a project starts sits in one place (the human, 2026-11-04). `demo/` stays at the root, since it is runnable code that `make check` checks. The files do not change, except the paths inside them that name each other.

## Interface

- `vm/` → `operator/vm/` and `template/` → `operator/template/`, with `git mv`.
- Every place under `src/`, `tests/`, `operator/`, `agents/`, `docs/` other than `docs/decisions.md`, and `README.md` that names `vm/<file>` or `template/<file>` names the new path. A build command that names the Dockerfile (`podman build -f vm/Dockerfile`, in `operator/vm/job-start.sh`, the guide and the tests) names `operator/vm/Dockerfile`.
- The coder's write paths `vm/*` and `template/*` in `factory/pipeline.yml`, a name in `Makefile` and the names in `CLAUDE.md` are the human's changes, made at this story's start. The VM's installed copies (the systemd unit, the credential helper) are the human's change on factory-vm after the merge.

## Acceptance criteria

1. `vm/` and `template/` do not exist; `operator/vm/` and `operator/template/` hold the same files (one row per file, from `origin/main` before the story).
2. The tests of the VM's scripts and of the stage image pass against the files at their new place (they read `operator/vm/`).
3. No file under `src/`, `tests/`, `operator/`, `agents/`, `docs/` other than `docs/decisions.md`, or `README.md` names `vm/setup.sh`, `vm/job-start.sh`, `vm/Dockerfile`, `vm/factory.service`, `vm/git-credential-factory` or `template/` at the root.
4. `make check` stays green.
5. docs: the new paths in `README.md`, the operator guide's topic files and the project guide's `operator.md`, whose *The layout* names the two new folders. `docs/decisions.md`: one entry for the move, naming F0051-S0012.

## Smoke test

```bash
ls -d vm template 2>/dev/null | wc -l
```
Expect: `0`

```bash
test -f operator/vm/Dockerfile && test -f operator/template/Makefile && echo moved
```
Expect: `moved`

```bash
bash -n operator/vm/setup.sh && bash -n operator/vm/job-start.sh && echo parsed
```
Expect: `parsed`

## Journal
