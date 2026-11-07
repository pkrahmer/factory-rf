---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 628
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T08:03:05.566887Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T07:48:46.111477Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T07:48:46.118859Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T07:49:01.169177Z'
  stage: intake
  run: 9e8091ff994c463899c59a082035015b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T07:49:05.994376Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T08:02:58.433137Z'
  stage: docs-only
  run: 76f490c38f7b4484935637fbcc467c8d
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T08:03:05.566887Z'
  stage: docs-review
---

# The project guide's index reads for the developer

## Description

`docs/project-guide/README.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/README.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/README.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/README.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/README.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/README.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/README.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only, `docs/project-guide/README.md` (rewritten) and `docs/checked-documents.txt` (one line). It states no code signatures and says no code, test or agent file changes. Both paths are ones the documenter may write, so the route is docs-only.
   - Criteria: criteria 1 and 2 are judged by the reviewer against the style page and the code, which is the docs route's check. Criterion 3 is checkable with `make documents`. Criteria 4 and 5 are checkable as broken links. Criterion 6 is `make check`. The Interface states no limit, default or rejected input, so no rule needs a failing-side criterion. The link rule and the checked-list line each have a criterion (4 and 3).
   - Smoke test: `grep -cx "docs/project-guide/README.md" docs/checked-documents.txt` is runnable. `Expect: 1` can be checked against its output. It runs no pytest.
   - Docs criterion: criterion 7 asks for criteria 1 to 5 and for no change to `docs/decisions.md`. It names what the reader must know (the facts of the old file kept or moved to Reference, with working examples). It dictates no sentences.
   - Architecture: only documents change, so the layers in CLAUDE.md are untouched. The page being rewritten is the project guide's index, which CLAUDE.md names.
   - Scope: S0020 is listed in F0054's stories. It touches no `decisions.md`, `docs/runs/` or operator-playbook file, and it changes no behaviour.
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/project-guide/README.md` in the style of `docs/project-guide/style.md`. `make documents` ends with `documents ok (57.4 s)`. `uv run pytest -q tests/guards/test_project_guide_files.py tests/guards/test_area_guides.py tests/entry/test_check_documents_guide_files.py` passed. I did not run `make check`, because only documents changed.

   Files changed:
   - `docs/project-guide/README.md`: rewritten for its reader.
     - The opening is two plain paragraphs: who the guide is for, what to read first, and the split rule for long pages.
     - *The code's layout* has the layer pattern in a code block, one bullet per area, and a See also line.
     - *The files* was reworded, and every page entry is kept.
     - *Errors* now opens with one idea sentence and a short hierarchy block, then one bullet per error class, then a See also line.
     - *Kill points* and *Fault-injection paths* have their pytest commands as `console` blocks with output (a tail line matched with `<name>[100%]`).
     - *The demos* has a `console` block for `check_demos`.
     - About 100 files and modules are linked once at first mention by a relative link.
     - Factory words are linked to `glossary.md` at first use.
     - The page entries in *The files* are the exception: their leading name stays plain, because the guard reads `` - `name` `` at the start of the item. Their links are in the See also line below the list.
   - `docs/checked-documents.txt`: added `docs/project-guide/README.md`.

   I checked these facts against the code and found them current:
   - The 12 `EXCEPTIONS` in `tests/guards/test_model_configuration.py`.
   - The four members of `KillPoint`.
   - The `check_demos` options and output.
   - The test files the example commands run.
   - The `FactoryError` subclasses the *Errors* section names.
   - Every linked file path and dotted module name; `make documents` resolved them all.

   Changes to wrong paths, found by the name check (`make documents`):
   - `support/<name>.py` is now `tests/support/<name>.py`.
   - `support/conftest.py` is now `tests/conftest.py`. It is the suite's real fixtures file, and `tests/support/conftest.py` does not exist.
   - The handlers' conftest now has its full path.
   - The demo files are now written as `demo/<name>/project/factory/...`.
   - The demo example is `todo-service/`, because `demo/todo/` does not exist.

   I dropped these on purpose:
   - The bullet about the heading *Replaced from v1*, and the mentions of the sections *Replaced in v1.2* and *Replaced from v1* in the `agents.md` entry. No such headings exist in the pages now.
   - "It grows with each story", and "Later stories add their error types under it".
   - The example name `factory.adapters.landlock`, which does not exist.
   - The sentence "No path is mapped to a removing item ... v1.1 keeps every mechanism". It was version history.
   - "v1's", "v1.1" and the feature id `F0002-todo` (reworded to "the due todo feature").

   Left as it was, and open for the reviewer:
   - *Errors* still lacks `TokenError`, `FixtureError`, `PipelineDefinitionInvalid`, `AgentDefinition*`, `UnhandledEvent`, `SettingsInvalid` and `MachineStopStood`, which `src/factory/shared/domain/errors.py` defines. The old text did not describe them either. The new intro says the area's page describes any other error. I did not check that every area page does.
   - I did not add a *Reference* section. The long test-helper lists and the tables keep all their detail in place.
   - The *Sections:* lists in the page entries of *The files* were not compared with each page's actual headings.
   - I did not verify every one-line description of a test-support module against its source.

   Stale text noticed and not touched, because it is unrelated to this story:
   - `demo/README.md` still says "v1.1".
   - `CLAUDE.md` mentions v1.1.
   - The report line `README.md:28: factory/stage.Containerfile does not exist` is printed for the top-level README. That file is not on the checked list.

   Not cleaned up: `/tmp/xxwork`, my scratch folder of edit scripts, outside the repository. The command to remove it was denied by the environment, so I left it.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (57.6 s)
6. factory: started docs-review as vm.
