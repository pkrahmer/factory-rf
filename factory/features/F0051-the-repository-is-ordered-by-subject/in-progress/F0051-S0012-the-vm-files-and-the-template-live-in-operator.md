---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 567
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-05T09:00:10.647564Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T08:59:42.818138Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T08:59:42.824976Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T09:00:05.522735Z'
  stage: intake
  run: 22cd5b210a134e3ea1696066d353c085
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T09:00:10.647564Z'
  stage: tests
---

# The VM's files and the project template live in `operator/`

## Description

Two folders at the root of the repository belong to the operator: `vm/` holds what sets up and runs an instance on a VM (`setup.sh`, `job-start.sh`, `factory.service`, `git-credential-factory`) and the base image's `Dockerfile`, and `template/` holds what the operator copies into a new project (`CLAUDE.md`, `Makefile`, `factory/`). `operator/` already holds the operator's other tools, among them `operator/job/` for Cloud Run. This story moves `vm/` to `operator/vm/` and `template/` to `operator/template/`, so that everything about where an instance runs and how a project starts sits in one place (the human, 2026-11-04). `demo/` stays at the root, since it is runnable code that `make check` checks. The files do not change, except the paths inside them that name each other.

## Interface

- `vm/` → `operator/vm/` and `template/` → `operator/template/`, with `git mv`.
- Every place under `src/`, `tests/`, `operator/`, `agents/`, `docs/` other than `docs/decisions.md`, and `README.md` that names `vm/<file>` or `template/<file>` names the new path. A build command that names the Dockerfile (`podman build -f vm/Dockerfile`, in `operator/vm/job-start.sh`, the guide and the tests) names `operator/vm/Dockerfile`.
- The coder's write paths `vm/*` and `template/*` in `factory/pipeline.yml`, a name in `Makefile` and the names in `CLAUDE.md` are the human's changes, made at this story's start. The VM's installed copies (the systemd unit, the credential helper) are the human's change on factory-vm after the merge.

- The tester makes every test change the rename needs in its first run, before the files move: every path and name of the old folders in `tests/`, under the leave of feature decision 5. The coder changes `src/`, the renamed folders and the documents it may write; its write paths do not hold `tests/`, so a test change it makes is dropped.

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

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: a pure move (`vm/` → `operator/vm/`, `template/` → `operator/template/`, `git mv`). The Interface names the folders, the files and the path rewrite rule, and lists the human's own changes (pipeline.yml, Makefile, CLAUDE.md) and the tester/coder split. There are no signatures to name, and none are needed.
   - Criteria: each is testable by one test function. 1 checks that the old folders are gone and lists the files by row. 2 is the existing VM-script and stage-image tests reading the new place. 3 is a source search, with both sides: the old root paths are absent, and 1 and 2 cover the new ones. 4 and 5 are the closing criteria. The Interface's Dockerfile build command is covered by 3 (`vm/Dockerfile`). In 3 I read "names `vm/setup.sh`…" as a name at the root of the repository, not as the tail of `operator/vm/setup.sh`. The tester must anchor the search so it does not match the new paths.
   - Smoke test: three runnable commands, with no pytest. Each `Expect:` (`0`, `moved`, `parsed`) can be checked against the output.
   - Architecture: it moves operator-side files only. `src/factory` and its areas are untouched, except for any paths named in source. `demo/` stays at the root, as CLAUDE.md and feature.md say.
   - Scope: it matches the feature's scope line for S0012 and its "The human's changes" entry for S0012. It leaves `docs/decisions.md`'s old entries and the `operator/claude` and `operator/opencode` folders alone, as the Out of scope section requires.
4. factory: started tests as vm.
