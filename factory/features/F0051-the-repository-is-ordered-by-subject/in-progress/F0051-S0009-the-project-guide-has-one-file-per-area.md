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
  instance: vm
  stage: intake
  started_at: '2026-11-05T05:50:02.002233Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T05:50:01.995292Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T05:50:02.002233Z'
  stage: intake
---

# The project guide has one file per area

## Description

The project guide under `docs/project-guide/` has one file per domain today (`git-and-hosting.md`, `work-items.md`, `agents.md`, `write-paths.md`, `costs.md`, `stages.md`, `watching.md`, `stage-environment.md`, `processes-and-checks.md`, `operator.md`). After the moves its files should follow the seven areas, so that an agent whose story touches an area reads exactly one file. This story regroups the guide's sections into one file per area: `shared.md`, `hosting.md`, `work.md`, `agents.md`, `watching.md`, `machine.md` and `pipeline.md`; `operator.md` stays, since it covers the operator's scripts outside `src/`. Each section moves as it is to the file of the area whose modules it describes; a section that describes several areas goes to the area of its first module and is named from the others' files by a one-line pointer. The index `README.md` names the new files and what each covers. The words of the sections do not change, except the pointers between files. It changes no code and no test.

## Interface

- No module under `src/factory/` changes and no test is written; the document check of the docs stage (`make documents`) and `make check` are the gate.
- `docs/project-guide/`: the seven area files and `operator.md`, and the index `README.md`; the old files that are not among them are removed with `git mv` into the new ones where a file maps whole (`git-and-hosting.md` → `hosting.md`, `work-items.md` → `work.md`, `stage-environment.md` → `machine.md`, `stages.md` → `pipeline.md`), and their sections are moved by hand otherwise.
- `claude/agents/*.md` and `CLAUDE.md` name guide files by name; the agent files are changed to the new names; `CLAUDE.md` is the human's change.

## Acceptance criteria

1. `docs/project-guide/` holds exactly `README.md`, `operator.md` and the seven area files named in the Description.
2. Every section heading (`##` and `###`) that the guide had before this story is found exactly once in the new files (one row per heading, from the guide on `origin/main` before the story), except the index's own *The files*.
3. The index's *The files* names each of the eight files with a sentence on what it covers and the modules it describes, by their new paths.
4. No file under `claude/`, `docs/` or `README.md` names a guide file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4, in the project guide. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none.

## Smoke test

```bash
ls docs/project-guide | tr '\n' ' '
```
Expect: `README.md agents.md hosting.md machine.md operator.md pipeline.md shared.md watching.md work.md `

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
