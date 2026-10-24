---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-24T22:14:25.153110Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T22:14:25.147163Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T22:14:25.153110Z'
  stage: intake
---

# The guides say what is true after the wiring

<!-- proposed by feature acceptance of 2026-10-24; refine before starting -->

## Description

The stories of F0042 were documented one at a time, and some sentences were true only while a later story was still to come. Since S0010, `build_boundaries` wires a `container` instance: `ContainerMakeCommands` behind `RecordingProjectCommands`, and the runtimes with their `PodmanRuns`. Since the human's change 1, this repository's own `Makefile` and `factory/pipeline.yml` have `sync`. Three passages still say otherwise. Three more describe only the inline environment where the container environment behaves differently:

- the cost sidecar is rewritten after the undo, which under `container` is the take;
- a stall "undoes the rest";
- `Boundaries.project_commands` is described as the inline chain alone.

This story corrects those six passages and nothing else. The inline environment's own descriptions stay, because F0044 removes them. For the operator and for the agents who read the project guide.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template or an agent file. The documenter changes `docs/project-guide/processes-and-checks.md`, `docs/project-guide/stage-environment.md`, `docs/project-guide/watching.md`, `docs/project-guide/costs.md` and `docs/operator-guide.md`, as the docs criterion says. No test reads the documents; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: the documenter makes the following true, each passage checked against the code on `main`:
   - `docs/project-guide/processes-and-checks.md`, *Project commands*: the sentence "This repository's own `Makefile` and `factory/pipeline.yml` do not have it yet: that is the human's change." is gone. In its place, this repository's `Makefile` has the target `sync` (`uv sync --frozen`) and `factory/pipeline.yml` has the command `sync` with `time_limit: 5`.
   - `docs/project-guide/processes-and-checks.md`, the paragraph on `ContainerMakeCommands`: the sentence "The wiring that puts it behind `RecordingProjectCommands` for a `container` instance is a later story; until then nothing builds it." is gone. In its place, `build_boundaries` puts it behind `RecordingProjectCommands` for a `container` instance (see `stage-environment.md`, *The settings and the wiring*).
   - `docs/project-guide/stage-environment.md`, *The agent's container*: the sentence "The wiring that gives a `container` instance's runtimes their `PodmanRuns` is a later story's." is gone. In its place, `build_boundaries` gives the runtime of `FACTORY_AGENT_RUNTIME` its `PodmanRuns` for a `container` instance (*The settings and the wiring*).
   - `docs/project-guide/watching.md`, *Boundaries*: the sentence on `build_boundaries`' `project_commands` names both cases. For `inline` it is `RecordingProjectCommands` around `SealedProjectCommands`, as now. For `container` it is `RecordingProjectCommands` around `ContainerMakeCommands`.
   - `docs/project-guide/costs.md`: the bullets "Until the stage's commit, the running run's record is uncommitted" and "Rewritten after every undo" say that the sidecar is rewritten after the take, which is the undo under `inline`. They say that under `container` the agent works on the dataset, where the sidecar is the one committed at the stage-start commit, and that the factory rewrites the host's copy after the take as it does after the undo. The bullet's title becomes "Rewritten after every take".
   - `docs/operator-guide.md`, *A stall: the stall note*: "undoes the rest" becomes a sentence true of both environments. The factory keeps what the agent wrote inside the stage's write paths and leaves out the rest: an `inline` instance undoes it, and a `container` instance does not take it from the dataset.
   - `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c 'do not have it yet' docs/project-guide/processes-and-checks.md; grep -c 'until then nothing builds it' docs/project-guide/processes-and-checks.md; grep -c "is a later story's" docs/project-guide/stage-environment.md; grep -c 'Rewritten after every undo' docs/project-guide/costs.md; grep -c 'undoes the rest' docs/operator-guide.md
```
Expect: five lines, each `0`

```bash
grep -c 'Rewritten after every take' docs/project-guide/costs.md; grep -c 'ContainerMakeCommands' docs/project-guide/watching.md
```
Expect: two lines, `1` and a number of at least `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
