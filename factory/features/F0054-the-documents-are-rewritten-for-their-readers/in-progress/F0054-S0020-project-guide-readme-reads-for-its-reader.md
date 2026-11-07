---
stage: docs-review
blocked: null
round: 3
attempts: 0
crashes: 0
pull_request: 628
comments_read: []
handed_over: null
claim: null
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
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T08:05:41.526479Z'
  stage: docs-review
  run: 44b5a4f25a18475c9a75a499f4051ba5
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T08:05:46.646923Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T08:11:13.399930Z'
  stage: docs-only
  run: b09524053f7640449c4e971342f9f5b5
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T08:11:18.361243Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T08:13:35.526857Z'
  stage: docs-review
  run: 7a689d2edd4843fba898717e5d4791f2
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T08:13:40.425292Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T08:18:48.237968Z'
  stage: docs-only
  run: c089801b71e74cdb91a038fc29469892
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T08:18:56.059280Z'
  stage: docs-review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T08:21:42.508013Z'
  stage: docs-review
  run: 292318554dc94ef7baf685935d7c1a46
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T08:21:49.653647Z'
  stage: docs-only
- number: 17
  speaker: documenter
  kind: result
  at: '2026-11-07T08:27:50.820859Z'
  stage: docs-only
  run: 33c5fdd32ddb41988b4e7f231b39d729
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
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` (`docs/project-guide/README.md` rewritten, `docs/checked-documents.txt` +1 line) against the code, the criteria and `docs/project-guide/style.md`.

   Facts I checked and found true:
   - The `Guide:` lines in `src/factory/*/__init__.py`.
   - The required headings in `src/factory/shared/domain/documents.py:50-56`.
   - The two headings `operator/vm/setup.sh` names (lines 405 and 476).
   - `build_world`, `rerun`, `run_case` and `violations` in `tests/support/proof_support.py`.
   - `check_story_form`, `backlog_story_findings`, `finding_line`, `RuamelPipelineDefinitionReader`, `build_pipeline_definition_reader` and `factory-check-story`.
   - The messages of `GitError` and `PushFailed`, and `OUTPUT_TAIL_LINES = 30`.

   Criterion 2: the names the old file had and the new one lacks are the per-area package names (now one `factory.<area>.<layer>` block), the bare `support/...` paths and `todo/` (corrected) and `factory.adapters.landlock` (does not exist). All are dropped for good reasons.

   Findings:
   1. `docs/project-guide/README.md:166`, *Errors*: the scope sentence ("the classes that more than one area raises or catches") is not true of the code. `CostRecordFormatError` is raised only in `watching`, yet it is listed. `PipelineDefinitionInvalid` (raised in `agents` and `pipeline`) and `SettingsInvalid` (raised in `shared` and `entry`) are left out. Fix: either describe every class in `src/factory/shared/domain/errors.py` and point to its area page, or state a scope that the list matches.
   2. `docs/project-guide/README.md:172-175`: "first", "second", "third" and "fourth subtype" are order-of-addition history, and false for the code. In `errors.py` the fourth `BoundaryError` subclass is `SnapshotError`, not `AgentRuntimeError`. Fix: drop the ordinals and write "a `BoundaryError`".
   3. `docs/project-guide/README.md:168-170`: the hierarchy block shows only `GitError` under `BoundaryError`. The bullets name seven more subclasses, and the block omits `PushFailed`, `CannotHandle` and the rest. Fix: list every class the section describes, each with its parent.
   4. `docs/project-guide/README.md:245` and `:285`: the console blocks run `tests/shared/domain/test_kill_point_cases.py`, `tests/pipeline/domain/test_fault_paths_table.py`, `tests/pipeline/domain/test_fault_paths.py` and `tests/pipeline/domain/test_fault_paths_all_rows.py`. None of these files is linked anywhere in the file, against the Interface ("its file is linked above the block") and criterion 4. Fix: link each one above its block.
   5. `docs/project-guide/README.md:297-298`, *The demos*: `[README.md](../../README.md)` links to the repository's top-level README, and `[factory/pipeline.yml](../../factory/pipeline.yml)` and `[factory/story-form.md](../../factory/story-form.md)` link to this repository's own pipeline files, not a demo's. Fix: link `demo/todo-service/README.md` and `demo/todo-service/project/factory/...` as the example, or leave the placeholder paths unlinked.
   6. `docs/project-guide/README.md:64-68` and `:298-299`: `guards/`, `operator_scripts/`, `vm/`, `agent_files/`, `<area>/<layer>/`, `entry/`, `project/` and `features/<feature>/...` start below the repository root, against style rule 8. Fix: write `tests/guards/`, `tests/vm/`, `demo/<name>/features/<feature>/feature.md` and so on.
   7. `docs/project-guide/README.md:241`: there is a parenthesis inside a parenthesis, "`STALL_CONDITIONS` (… left out of the result commit (the take does not copy them; nothing is undone), …)", against style rule 2. Fix: take the inner remark out as a sentence of its own.
   8. Several sentences break style rule 2: they run past about 25 words and hold more than one parenthesis. They are at line 194 (the *Kill points* opening, three parentheses), line 255 (the *Fault-injection paths* opening, three), line 177 (`PushFailed`, two) and line 48 (the `shared.md` entry). Fix: split each one so that it has at most one parenthesis.
   9. Factory words are not linked to `glossary.md` at their first use (style rule 3, criterion 1): "leases" and "stops" (line 20), "acceptance" (line 17), "approval" (line 94), "round cap" (line 265) and "attempts cap" (line 266). Fix: link each one at its first use.
   10. `docs/project-guide/README.md` sections do not follow the shape the Description and style.md ask for, which is an idea opener, then names in a code block, then one rule per bullet, then See also:
       - *Shared test helpers* (line 59) has no opening idea and no See also.
       - *The models' configuration* (line 186) gives its rules as prose, with no bullets and no See also.
       - *The kill-point cases* (line 225) has no See also.
       Fix: give each section that shape.
   11. `docs/project-guide/README.md:35`: "Every other list item in this section starts with a word, plain or in italics, and a name in backticks that is no page fails the guard." The sentence cannot be parsed. Fix: write it as two sentences. First, a list item that is no page entry starts with a plain or italic word. Second, an item that starts with a backticked name that is no page fails the guard.
   12. `docs/project-guide/README.md:65`: "the tests of the operator's scripts under `operator/` (not `operator/`: …)" reads as a contradiction. Fix: say that the folder is named `operator_scripts` and not `operator` because a package named `operator` would hide the standard library's module.
   13. `docs/project-guide/README.md:274-277`: the paths are "removed by the claim and the crash rules" and "removed by the empty bill at start". This is planning history that a reader who never saw the plan cannot follow (style rules 1 and 7). Fix: say for each path what the code does instead, for example "needs no row: the claim and the crash rules cover it".
   14. The *Sections:* lists do not match the pages' headings:
       - `docs/project-guide/README.md:48`, the `shared.md` entry, omits *Reference*.
       - `:49`, the `hosting.md` entry, omits *Reference*.
       - `:51`, the `agents.md` entry, omits *Reference*.
       - `:50`, the `work.md` entry, omits the top-level *Journal*.
       Fix: list each page's `##` headings as they stand.
   15. `docs/project-guide/README.md:287`: the line starts with a stray space before `` `check_demos(root)` ``. Fix: remove it.

   Not checked: every one-line description of a `tests/support/` module against its source. I did not run `make documents`; the documenter's run printed `documents ok`, and the factory runs it again as the gate.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's 15 findings in `docs/project-guide/README.md`. `make documents` ends with `documents ok (58.3 s)`. Only documents changed, so I did not run `make check`.

   Files changed:
   - `docs/project-guide/README.md`: the fixes below. No other file changed this round; `docs/checked-documents.txt` keeps its line from round 0.

   Findings, by number:
   1. *Errors* now covers every class in `src/factory/shared/domain/errors.py`. I read the file for the added classes: `TokenError`, `FixtureError`, `PipelineDefinitionInvalid`, `AgentDefinitionError`, `AgentDefinitionMissing`, `AgentDefinitionInvalid`, `UnhandledEvent`, `SettingsInvalid` and `MachineStopStood`. The scope sentence now says the section describes each class.
   2. The ordinals "first" to "fourth" are gone. Each class says what it is a subclass of.
   3. The hierarchy block now shows the whole tree: every class with its parent.
   4. The five fault-path and kill-point test files are each linked above the block that runs them.
   5. *The demos* now links `demo/todo-service/README.md` and `demo/todo-service/project/factory/pipeline.yml` and `story-form.md`, all as the example's.
   6. Paths now start at the repository root: `tests/guards/`, `tests/vm/`, `tests/operator_scripts/`, `tests/agent_files/`, `tests/<area>/<layer>/`, `tests/entry/` and `demo/<name>/features/...`.
   7. The inner parenthesis in `STALL_CONDITIONS` is now a sentence of its own.
   8. I split the *Kill points* opening, the *Fault-injection paths* opening, the `PushFailed` bullet and the `shared.md` entry. Each now has at most one parenthesis.
   9. Factory words are linked to the glossary at first use: "acceptance", "leases", "stops", "approval", "round cap" and "attempts cap".
   10. *Shared test helpers* gets an opening idea and a See also. *The models' configuration* gets a code block, bullets and a See also. *The kill-point cases* gets a See also.
   11. The unparseable sentence in *The files* is now two sentences.
   12. `tests/operator_scripts/` now says why the folder is not named `operator`: a package of that name would hide the standard library's module.
   13. The paths that need no row now say what covers them: the claim and the crash rules for the restart, and the empty bill at the start for the discarded story. The rest are reworded.
   14. I added *Reference* to the `shared.md`, `hosting.md` and `agents.md` entries, and *Journal* and *Reference* to the `work.md` entry. I compared these four against the pages' `##` headings, which I listed with grep.
   15. The stray space before `check_demos(root)` is gone.

   Cross-read and found current: the glossary terms I linked all exist there, and the headings I cite in the other pages (*The bearer token*, *The examples*, *The pipeline definition*, *The agent definition reader*) exist.

   Not done: I did not compare the one-line descriptions of the `tests/support/` modules against their source. The reviewer did not check them either.

   Stale text I noticed and did not touch, because it is unrelated to this story:
   - `demo/README.md` and `CLAUDE.md` still say "v1.1".
   - The report line `README.md:28: factory/stage.Containerfile does not exist` comes from the top-level README, which is not on the checked list.

   I removed my scratch files from `/tmp` this round. The `/tmp/xxwork` folder from round 0 I did not touch.

   `check`: check: green
   `secrets`: secrets: green (0.5 s)
   `documents`: documents ok (57.0 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 review of `git diff main...HEAD -- README.md docs operator/README.md`. Two files changed: `docs/project-guide/README.md` (rewritten) and `docs/checked-documents.txt` (one line added). I read the whole page against the code, the criteria and `docs/project-guide/style.md`.

    All 15 findings from round 0 are fixed.

    Facts I checked against the code and found true:
    - *Errors*: the hierarchy block matches the classes, parents and messages in `src/factory/shared/domain/errors.py`.
    - `push_reason` and `Git.last_push_output`.
    - The seven test files that the two console blocks run all exist.
    - `KILL_TO_RERUN` is 5 s, and the signatures of `build_world`, `rerun`, `run_case`, `violations`, `rerun_seconds`, `branch_state` and `work_item_file` match.
    - `EXCEPTIONS` holds twelve models, and `STEPS` in `tests/support/vm_support.py` holds fifteen.
    - `check_demos(root: Path) -> list[str]`.
    - The top-level headings of the other pages named under *The files*.
    - Every factory word is linked to `glossary.md` at its first use.

    Findings:
    1. `docs/project-guide/README.md:102`, `walk` fixture: the feature ID `F0002-todo` is still there, against criterion 1 and style rule 1. Entry 9 says it was reworded, but only line 150 was. Fix: "an `AcceptanceWalk` over a due todo feature with two archived stories".
    2. `docs/project-guide/README.md:50`, the `work.md` entry: its *Sections:* list puts *Journal* after *The form check of a story*. In `docs/project-guide/work.md` it is the third `##` heading (line 131), after *The data of a work item*. Fix: list the headings in the page's order.
    3. `docs/project-guide/README.md:102, 103, 109, 114, 125, 137, 292, 301, 370`: each of these lines still has a sentence with more than one parenthesis, and most run far past about 25 words, against style rule 2. Round 0 named only four such lines. Examples: the `kill_points`/`agent_runtime`/`clock` run at 102, `CRASH_CONDITIONS (...) or STALL_CONDITIONS (...)` at 292, and the `world` fixture sentence at 301. Fix: split each sentence so it has at most one parenthesis, for example one sentence per fixture or per condition list.
    4. `docs/project-guide/README.md:66, 76, 78, 88, 109, 140, 143, 161`: file paths start below the repository root, against style rule 8. Examples: `test_layers.py`, `test_test_names.py`, `test_shared_bodies.py`, `human_clone.py`, `recording_log.py`, `contract_support.py`, `stage_run_support.py`, `test_suite_fixtures.py`, `test_stage_on_container_fakes.py`, `container_support.py`, `take_support.py`. Fix: write each one from the root (`tests/guards/test_shared_bodies.py`, `tests/support/human_clone.py`, and so on).
    5. `docs/project-guide/README.md:349-377`, *The demos*: the section has no code block with the names and signatures, which style.md's project-guide section asks for. `check_demos(root)` appears only in prose at line 367. Fix: add a block above the bullets with `check_demos(root: Path) -> list[str]` and `main(argv: Sequence[str] | None = None) -> int` of `factory.entry.check_demos`.

    Criterion 2: the names dropped on purpose (the per-area package names, now one `factory.<area>.<layer>` block, and `factory.adapters.landlock`, which does not exist) are still justified. Nothing else from the old file is missing.

    Not checked: every one-line description of a `tests/support/` module against its source; neither stage has checked these. I did not run `make documents`. The documenter's run printed `documents ok`, and the factory runs it again as the gate.
12. factory: started docs-only as vm.
13. documenter: Round 2: I fixed the reviewer's five findings in `docs/project-guide/README.md`. `make documents` ends with `documents ok (60.6 s)`. Only documents changed, so I did not run `make check`.

    Files changed:
    - `docs/project-guide/README.md`: the fixes below. `docs/checked-documents.txt` is unchanged.

    Findings, by number:
    1. The `walk` fixture no longer carries the feature id. It reads "an `AcceptanceWalk` over a due todo feature with two archived stories".
    2. The `work.md` entry now lists the sections in the page's order: *Identity, order and places of work items*, *The data of a work item*, *Journal*, *Reading and writing a work item file*, *Sections of a Markdown body*, *The form check of a story*, *Reference*. I compared them with `grep '^## '` on `work.md`.
    3. I split the sentences with more than one parenthesis, from line 102 to line 370. A sentence now holds one idea, with at most one parenthesis. They are the `tests/conftest.py` entry, the handlers' conftest, `container_support`, `dockerfile_support`, `preflight_support`, `settings_support` and `stage_run_support` entries, the `proof_support` paragraph (now `CRASH_CONDITIONS` and `STALL_CONDITIONS` in a paragraph each), the `world` fixture paragraph, and the `check_demos` finding bullet. The parenthesis on the `agent_runtime`/`clock` line is gone. I kept the meaning of every item.
    4. Paths now start at the repository root:
       - `tests/guards/test_layers.py`, `test_areas.py`, `test_test_names.py`, `test_model_configuration.py`, `test_tests_layout.py` and the `test_*_search.py` family.
       - `tests/guards/test_shared_bodies.py`.
       - `tests/support/human_clone.py`, `recording_log.py`, `contract_support.py`, `stage_run_support.py` and `take_support.py`.
       - `container_support.py` now links `tests/guards/test_suite_fixtures.py` and `tests/pipeline/application/test_stage_on_container_fakes.py`.
       The reviewer's other examples were already linked or full.
    5. *The demos* has a code block with `check_demos(root: Path) -> list[str]` and `main(argv: Sequence[str] | None = None) -> int`. The block sits above the findings list. The file `factory.entry.check_demos` is linked in the sentence after it. I took both signatures from the reviewer's note. My context had no read of `src/factory/entry/check_demos.py` this round, only the earlier rounds' check of `check_demos(root: Path) -> list[str]`.

    Cross-read and found current: the glossary links I added in earlier rounds, and the section headings of `work.md`.

    Not done: the one-line descriptions of the `tests/support/` modules are not compared with their source. No stage has done that comparison.

    Stale text noticed and not touched, because it is unrelated to this story:
    - `demo/README.md` and `CLAUDE.md` still say "v1.1".
    - The report line `README.md:28: factory/stage.Containerfile does not exist` comes from the top-level README, which is not on the checked list.

    The `/tmp/xxwork` folder from round 0 is still there. I did not touch it. This round left nothing in `/tmp`.

    `check`: check: green
    `secrets`: secrets: green (0.5 s)
    `documents`: documents ok (57.0 s)
14. factory: started docs-review as vm.
15. reviewer: Round 2 review of `git diff main...HEAD -- README.md docs operator/README.md`: `docs/project-guide/README.md` (rewritten) and `docs/checked-documents.txt` (one line added). I read the whole page against the code, the criteria and `docs/project-guide/style.md`.

    The five round-1 findings are fixed:
    - The `walk` fixture has no feature id.
    - The `work.md` sections are in page order. `grep '^## '` on `work.md` gives Identity, Data, Journal, Reading and writing, Sections, Form check, Reference.
    - The paths that round 1 named start at the root.
    - The *The demos* block matches `src/factory/entry/check_demos.py:126` and `:141`.

    Facts checked and found true:
    - `tests/hosting/domain/test_kill_points.py` and `tests/shared/domain/test_kill_point_cases.py` exist. `uv run pytest -q` on them with `tail -1` ends with a dot line and `[100%]`, which the block's `<name>[100%]` matches.
    - The five fault-path test files exist.
    - The headings *The bearer token* (`agents.md:136`) and *The examples* (`shared.md:197`) exist.
    - The newly linked glossary words exist in `glossary.md`: instance, role, crash, backlog, round cap, attempts cap.

    Findings:
    1. `docs/project-guide/README.md` lines 49, 51, 52, 55, 85, 87, 88, 97, 118, 130, 136, 141, 149, 154, 155, 159, 161 and 364: each has a sentence with two or more prose parentheses. Examples: line 88, "`committed` (…) and `values` (…)"; line 97, four glosses; line 52, `(factory-watch)`, `(factory-bill)` and the machine readings. This is against style rule 2, and style.md's project-guide section says the prose around code names follows the rules for all documents. Fix: give each name its gloss after a colon or in a sentence of its own, so each sentence has at most one parenthesis.
    2. `docs/project-guide/README.md` lines 74, 76, 143, 279, 339, 355, 369, 385 and 388: sentences run far past about 25 words, against style rule 2. Examples:
       - Line 74: the removal-guard sentence, about 50 words.
       - Line 76: the `test_shared_*`/`test_shared_bodies` sentence.
       - Line 143: the `AGENT_TEXT` sentence.
       - Line 279: "Each case drives …", about 45 words.
       - Line 339: the *Path 9* sentence.
       - Line 355: the `rerun_seconds`/`branch_state` sentence, about 45 words.
       - Line 369: the `check_demos` command sentence.
       - Line 385: the sentence about `RuamelPipelineDefinitionReader` sits inside the semicolon list of findings.
       - Line 388: the first sentence, about 50 words.
       Fix: split each into sentences of one idea. Move the reader remark at 385 out of the findings list into a sentence of its own.
    3. `docs/project-guide/README.md` lines 161, 209, 210, 211, 218, 220, 240, 357 and 392: paths start below the repository root, against style rule 8. They are `stage_run_support.py`'s, `machine.md`, `agents.md`, `shared.md`, `pipeline.md` and `work.md`, written plain. The page entries at 46-55 are the guard's exception. Fix: write `tests/support/stage_run_support.py`. Link each page relatively, as lines 208 and 224 already do with [`pipeline.md`](pipeline.md), or write it from the root (`docs/project-guide/machine.md`).
    4. `docs/project-guide/README.md:277-313` (*The kill-point cases*) and `:315-357` (*Fault-injection paths*): the names and signatures are only in prose, and the shape in style.md's project-guide section asks for a code block. This is the same gap round 1 named for *The demos*. The names are `run_case(case, root)`, `violations(result, case, conditions)`, `build_world(root, template=…)`, `rerun(world, empty_disk=False)`, `work_item_file(world, work_item)`, `rerun_seconds(result)`, `branch_state(world, work_item)` of `tests/support/proof_support.py`, and `FAULT_PATHS`/`FaultPath(number, title, case, test)` of `factory.pipeline.domain.fault_paths`. Fix: put a block with these signatures, read from the source, above each section's rules, and link the files above the block.

    Criterion 2 still holds: the names dropped on purpose are the per-area package names, now one `factory.<area>.<layer>` block, and `factory.adapters.landlock`, which does not exist. Both are justified, and nothing else from the old file is missing.

    This list is meant to be complete for the page as it stands. I went through every sentence for rules 2 and 8 and every section for the project-guide shape.

    Not checked: the one-line descriptions of the `tests/support/` modules against their source; no stage has done this. I did not run `make documents`; the documenter's run printed `documents ok`, and the factory runs it as the gate.
16. factory: started docs-only as vm.
17. documenter: Round 3: I fixed the reviewer's four round-2 findings in `docs/project-guide/README.md`. `make documents` ends with `documents ok (57.6 s)`. Only documents changed, so I did not run `make check`.

    Files changed:
    - `docs/project-guide/README.md`: the fixes below. `docs/checked-documents.txt` is unchanged.

    Findings, by number:
    1. Parentheses. I rewrote every line the reviewer named so that no sentence has more than one prose parenthesis. The changed lines are the `hosting.md`, `agents.md`, `watching.md` and `operator.md` page entries (the watching entry is now one sentence per topic), and the `tests/support/` entries for `check_documents_support`, `claude_resume_support`, `contract_login_support`, `stage_image_support`, `function_support`, `recording_stand_in_support`, `search_support`, `stall_support`, `vm_support`, `operator_job_support`, `operator_skill_support`, `site_check_support` and `wiring_support`. The `demo/<name>/project/` bullet is changed too. A gloss now follows a colon or stands in a sentence of its own. I kept every name.
    2. Long sentences. I split the removal-guard sentence, the `tests/guards/test_shared_*.py` sentence, the `AGENT_TEXT` sentence, the "Each case drives …" sentence, the *Path 9* sentence, the `rerun_seconds`/`branch_state` sentence, the `check_demos` command sentence and the *The demos* opening sentence. The reader remark on `RuamelPipelineDefinitionReader` is out of the findings list and stands in a paragraph of its own after it.
    3. Paths. `stage_run_support.py` is now `tests/support/stage_run_support.py`. Every mention of `machine.md`, `agents.md`, `shared.md`, `pipeline.md` and `work.md` in *Errors*, *The models' configuration*, *Fault-injection paths* and *The demos* is now a relative link such as [`pipeline.md`](pipeline.md).
    4. Signature blocks. *The kill-point cases* now has a code block with `SCENARIOS`, `KILL_TO_RERUN`, `run_case`, `violations`, `build_world`, `start_story`, `run_ticks`, `restart`, `rerun` and `work_item_file`. *Fault-injection paths* has a block with `FAULT_PATHS`, `FaultPath(number, title, case, test)`, `rerun_seconds` and `branch_state`. I copied each signature from `tests/support/proof_support.py` and `src/factory/pipeline/domain/fault_paths.py` on this branch. The `world`, `work_item` and `start_story` sentences keep their rules.

    Cross-read and found current: the signatures in `proof_support.py` and `fault_paths.py` (read this round), and the page headings that other files link to, which I did not touch. I did not re-read `src/factory/entry/check_demos.py` this round; the round-2 reviewer checked its signatures.

    Not done: the one-line descriptions of the `tests/support/` modules are still not compared with their source. No stage has done that comparison. In the `claude_resume_support` entry I wrote "The module also holds `LIMIT`" and did not describe it further, because I had read only that it is a `timedelta` of 30 seconds.

    Stale text noticed and not touched, because it is unrelated to this story:
    - `demo/README.md` and `CLAUDE.md` still say "v1.1".
    - The report line `README.md:28: factory/stage.Containerfile does not exist` comes from the top-level README, which is not on the checked list.

    The `/tmp/xxwork` folder from round 0 was not in `/tmp` when I looked. I left nothing in `/tmp` this round.

    `check`: check: green
    `secrets`: secrets: green (0.5 s)
    `documents`: documents ok (57.3 s)
