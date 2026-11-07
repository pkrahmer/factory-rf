---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 635
comments_read: [6706893353]
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T12:26:06.429980Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T12:21:29.573435Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T12:21:29.580752Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-07T12:21:51.979758Z'
  stage: intake
  run: e7c07b6c0abf486b80bf7d19d917283b
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-07T12:25:41.033588Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-07T12:25:43.662489Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-07T12:26:01.486847Z'
  stage: intake
  run: 18301998e4064d46ab73c1c038e3fc69
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T12:26:06.429980Z'
  stage: docs-only
---

# The package and its areas say what they hold

## Description

This story writes the READMEs of the package `src/factory/` and its eight packages (`agents`, `entry`, `hosting`, `machine`, `pipeline`, `shared`, `watching`, `work`), in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code and no test changes.

## Interface

- New files, each in the form of feature decision 2 (`docs/project-guide/style.md`, *Folder READMEs*):
  - `src/factory/README.md`
  - `src/factory/agents/README.md`
  - `src/factory/entry/README.md`
  - `src/factory/hosting/README.md`
  - `src/factory/machine/README.md`
  - `src/factory/pipeline/README.md`
  - `src/factory/shared/README.md`
  - `src/factory/watching/README.md`
  - `src/factory/work/README.md`
- `src/factory/README.md` names each area and `entry` in one line and links to `docs/project-guide/README.md`, *The code's layout*. Each area's README says what the area holds in one sentence, links to the area's guide page (the one its `__init__.py` docstring names), and names its three layers (`domain/`, `application/`, `adapters/`) with one line each that says what that layer holds in this area. `contract/` is named in `src/factory/README.md` as generated, never edited by hand.
- `src/factory/entry/README.md` is not an area's: it is one sentence on what `entry` holds (the commands and the wiring) and a link to `docs/project-guide/README.md`, the guide its `__init__.py` names, with no subfolder lines, since `entry` has none.
- `docs/checked-documents.txt` gains each new path.
- No code and no test changes. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/`: <one sentence>.``. The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
2. Every name, path and link in these files exists (the document check finds nothing), and each file is on `docs/checked-documents.txt`.
3. `src/factory/README.md` links to `docs/project-guide/README.md`, *The code's layout*, and says that `contract/` is generated and never edited by hand; each area's README (`agents`, `hosting`, `machine`, `pipeline`, `shared`, `watching`, `work`) links to the guide page its `__init__.py` docstring names; `src/factory/entry/README.md` has one sentence on what `entry` holds, a link to `docs/project-guide/README.md` and no subfolder lines.
4. `make documents` ends with `documents ok (<seconds> s)`.
5. `make check` stays green.
6. docs: the files of the Interface. The project guide's area pages: none, unless one of them names a folder README; then it links to it. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | tail -1
```
Expect: `documents ok (<seconds> s)`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface behaviours with no criterion. Criterion 1 only checks what the guard checks: the opening sentence, one relative link and the subfolder lines. Four Interface statements are tested by nothing, and a coder could miss them and still pass:
      a. `src/factory/README.md` links to `docs/project-guide/README.md`, *The code's layout*.
      b. Each area's README links to the guide page its `__init__.py` docstring names (agents.md, hosting.md, machine.md, pipeline.md, shared.md, watching.md, work.md).
      c. `src/factory/README.md` says `contract/` is generated and never edited by hand.
      d. Each area's three layer lines say what that layer holds in this area.
      I would add one criterion for a to c, in words a reviewer can check, and keep d to the reviewer's judgment. Do you agree, or should I leave all four to the reviewer?
   2. `src/factory/entry/README.md` is in the Interface. The Interface says "each area's README names its three layers", but `entry` is not an area and has no subfolders (it has no `domain/`, `application/` or `adapters/`). I would take it as one sentence plus a link to `docs/project-guide/README.md` (the guide its `__init__.py` names), with no subfolder lines. Please confirm, and say so in the Interface.
   3. Docs criterion (5) is fine as to sentences: it names the files and dictates no text.
   The format check passed. The smoke test is runnable, and its `Expect:` line is checkable. The scope fits the feature, which puts S0002 in group 1 with no code change. The architecture is unaffected, since it only adds READMEs.
4. 2026-11-07 human: 1. Agreed: add one criterion for a to c in words a reviewer can check; d stays to the reviewer's judgment.
   2. Confirmed: src/factory/entry/README.md is one sentence on what entry holds (the commands and the wiring) and a link to docs/project-guide/README.md, the guide its __init__.py names, with no subfolder lines since entry has none. Say so in the Interface.
5. factory: started intake as vm.
6. intake: accepted, with the human's answer (journal 4) written into the story.
   - Interface: names nine concrete README paths and `docs/checked-documents.txt`. Per journal 4, item 2, I added the line that `src/factory/entry/README.md` is one sentence on what `entry` holds plus a link to `docs/project-guide/README.md`, with no subfolder lines. All paths are ones the documenter may write, so the route is docs-only.
   - Criteria: per journal 4, item 1, I added the new criterion 3, before the two closing ones. It covers the layout link and the `contract/` note in `src/factory/README.md`, each area's link to the guide page its `__init__.py` names, and the `entry` shape. The old 3 to 5 are now 4 to 6. Criterion 1 covers the opening sentence and the subfolder lines, including the failing side through the guard. The criterion on what each layer line says stays with the reviewer, as the human decided. The story states no limit, default or error beyond the guard's, so no rule is left without a failing side.
   - Smoke test: `uv run python -m factory.entry.check_documents | tail -1` is runnable and has no pytest `-q` problem. Its `Expect:` line is checkable.
   - Docs criterion: it names the files and what the reader must know, and dictates no sentences.
   - Architecture: only READMEs are added, so no code or layer is touched.
   - Scope: within feature F0055, group 1 (S0002), no code change. It is not in the feature's "Out of scope".
7. factory: started docs-only as vm.
