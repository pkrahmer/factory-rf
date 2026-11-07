---
stage: docs
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 635
comments_read: [6706893353, 6707004049]
handed_over: null
claim: null
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
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-07T12:31:32.861611Z'
  stage: docs-only
  run: d17907cc9efa47e78df8e785b548a2dd
- number: 9
  speaker: factory
  kind: stall
  at: '2026-11-07T12:31:33.409387Z'
  stage: docs-only
  run: d17907cc9efa47e78df8e785b548a2dd
  reason: check_red
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T12:31:40.039399Z'
  stage: docs-only
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-07T12:31:56.433846Z'
  stage: docs-only
  run: 073086758e7a4dfa8e4780dd2d9600ce
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T12:32:01.567807Z'
  stage: tests
- number: 13
  speaker: tester
  kind: question
  at: '2026-11-07T12:32:27.391326Z'
  stage: tests
  run: 196af7c5c2954d50a07b35be4417314d
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-11-07T12:36:18.120009Z'
  stage: tests
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-07T12:36:20.614121Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-07T12:38:50.612279Z'
  stage: tests
  run: bd83cfd6c625471d8b10795cf9d254ab
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-07T12:38:57.965701Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-07T12:43:12.480560Z'
  stage: doing
  run: 7a62c1c1d89a45279281d2438c1e6df2
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-07T12:43:17.562965Z'
  stage: review
- number: 20
  speaker: reviewer
  kind: result
  at: '2026-11-07T12:44:43.522047Z'
  stage: review
  run: 3e974a85d0fe4da3869c2029e40cdf98
---

# The package and its areas say what they hold

## Description

This story writes the READMEs of the package `src/factory/` and its eight packages (`agents`, `entry`, `hosting`, `machine`, `pipeline`, `shared`, `watching`, `work`), in the form of feature decision 2: one sentence on what the folder holds, links to the guide pages that explain it, and one line per subfolder. Each is added to `docs/checked-documents.txt`, so that its names and links are checked from now on, and the guard of the folder READMEs turns green for these folders. The facts come from the code and from the files' own docstrings and header comments, not from memory. No code changes; the one test change is the human's leave (journal 14): `tests/guards/test_old_layer_packages_removed.py` gains `README.md` in the expected entries of `src/factory/`, its test renamed to say so.

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
- No code changes. One test change, with the human's leave (journal 14): `tests/guards/test_old_layer_packages_removed.py` adds `"README.md"` to the expected entries of `src/factory/`, renames `test_the_package_holds_only_its_init_the_areas_entry_and_contract` to `test_the_package_holds_only_its_init_its_readme_the_areas_entry_and_contract`, and its module docstring says the same. The story takes the docs route.

## Acceptance criteria

1. Each file of the Interface exists, opens with one sentence on what its folder holds, links to at least one guide page or document that explains it, and names every direct subfolder of its folder in one line ``- `<name>/` <one sentence>.``. The guard `tests/guards/test_folder_readmes.py` passes for each and skips none of them.
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
8. documenter: Wrote the nine folder READMEs and put them on the document check. `make documents` ends with `documents ok (75.1 s)`. `tests/guards/test_folder_readmes.py` passes for all nine and skips none of them.

   Files changed:
   - `src/factory/README.md`: one opening sentence and a link to `docs/project-guide/README.md`, *The code's layout*. One line each for the seven areas, `entry/` and `contract/`; the `contract/` line says it is generated and never edited by hand.
   - `src/factory/entry/README.md`: one sentence on what `entry` holds (the commands and the wiring), a link to `docs/project-guide/README.md`, and no subfolder lines.
   - `src/factory/{agents,hosting,machine,pipeline,shared,watching,work}/README.md`: one sentence on what the area holds, a link to the guide page its `__init__.py` docstring names (`docs/project-guide/<area>.md`), and one line each for `adapters/`, `application/` and `domain/`. I wrote each layer line from the modules in that layer on the branch. The reviewer judges whether the layer lines are right; the human left that to the reviewer.
   - `docs/checked-documents.txt`: the nine new paths.

   Deviation from the story: the Interface writes the subfolder line as ``- `<name>/`: <sentence>.``, with a colon after the name. The guard (`readme_problems` in `src/factory/shared/domain/folder_readmes.py`) and `docs/project-guide/style.md`, *Folder READMEs*, say ``- `<name>/` <sentence>.``, with no colon. A line with the colon is not recognised as naming the subfolder, so every README failed the guard. I followed the guard and the style guide and left out the colon. If the human wants the colon, the guard and the style guide change, which is outside this story. I did not change the story text, since the Interface is not mine to edit.

   Cross-read and found current:
   - `docs/project-guide/README.md`, *The code's layout* and *The files*, against the nine READMEs. It names no folder README, so I added no link there.
   - The `Guide:` lines in the `__init__.py` docstrings, against the links I wrote.

   Stale text noticed and left alone: none. Every sentence in `docs/decisions.md` stays as it was, and I wrote no "Why" or "Rejected" line.

   I did not run `make check`, since I changed only documents and the factory runs it after this stage.
9. factory: Stage docs-only stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/watching/application/transcripts.py         61      2     10      0    97%   92-93
   src/factory/watching/domain/board.py                    55      0      4      1    98%   78->76
   src/factory/watching/domain/machine.py                  52      3     18      5    89%   45->43, 48, 60, 78->76, 80
   src/factory/watching/domain/transcripts.py              10      2      0      0    80%   21-22
   src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   240
   src/factory/work/application/work_items.py              90      2     24      2    96%   134, 170
   src/factory/work/domain/acceptance.py                  195      1     52      1    99%   368
   ------------------------------------------------------------------------------------------------
   TOTAL                                                11354     55   2296     53    99%

   158 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.21%
   ======================================================================================= short test summary info ========================================================================================
   FAILED tests/guards/test_old_layer_packages_removed.py::test_the_package_holds_only_its_init_the_areas_entry_and_contract - AssertionError: assert {'README.md',...hosting', ...} == {'__init__.py......
   make: *** [Makefile:89: test] Error 1
10. factory: started docs-only as vm.
11. documenter: I wrote no documentation this round, and I changed no file. The documents from the first round (the nine folder READMEs and the nine lines in `docs/checked-documents.txt`) are in the tree and stay as they are. The stage stalled on a red `make check`, and the cause is a test, not a document.

    The failing test is `tests/guards/test_old_layer_packages_removed.py::test_the_package_holds_only_its_init_the_areas_entry_and_contract`. It asserts that the entries of `src/factory/` equal `{"__init__.py", *AREAS, "entry", "contract"}`. The new `src/factory/README.md`, which this story's Interface requires, makes the set `{"README.md", ...}`, and the assertion fails.

    Change needed, for the tester to make: add `"README.md"` to the expected set on line 23 of that test, and rename the test so the name says the same (the package holds its init, its README, the areas, entry and contract). The test keeps its purpose, which is to keep old layer packages out of the package root. This is a test another story wrote, so it needs the human's leave beyond the standing leave. The story requires this README, and the guard can't pass without the change. I could not fix it myself: tests are outside my write paths, and a README in the package root is what the story asks for.

    The deviation from the first round still stands. The Interface writes the subfolder line with a colon, ``- `<name>/`: ...``. The guard (`readme_problems` in `src/factory/shared/domain/folder_readmes.py`) and `docs/project-guide/style.md`, *Folder READMEs*, say ``- `<name>/` ...``, with no colon. I followed the guard and the style guide.

    I cross-read `docs/project-guide/README.md` (*The code's layout*) against the READMEs in round 0 and found it current. I saw no stale text outside this story.
12. factory: started tests as vm.
13. tester: I wrote no test and changed no file. I stopped at step 1 because two things stand in the way, and I need your word on both.

    1. The existing guard conflicts with the Interface. `tests/guards/test_old_layer_packages_removed.py::test_the_package_holds_only_its_init_the_areas_entry_and_contract` asserts that the entries of `src/factory/` are exactly `{"__init__.py", *AREAS, "entry", "contract"}`. The Interface requires `src/factory/README.md`, so this guard is red and `make check` (criterion 5) cannot pass. The story says "No code and no test changes", and another story wrote this test. The change is not a move of a shared helper, so the standing leave in `CLAUDE.md` does not cover it. Options:
       a. You give leave. I add `"README.md"` to the expected set and rename the test to `test_the_package_holds_only_its_init_its_readme_the_areas_entry_and_contract`, and the module docstring says the same. It keeps its purpose, which is keeping old layer packages out of the package root. The story's "no test changes" line is then rewritten to name this one change. **I would choose a.**
       b. Leave the test as it is and drop `src/factory/README.md` from the story. The other eight READMEs stay, and criterion 3's part on `src/factory/README.md` goes.

    2. Criterion 1 and the Interface give the subfolder line as ``- `<name>/`: <one sentence>.``, with a colon. The guard (`readme_problems` in `src/factory/shared/domain/folder_readmes.py`) and `docs/project-guide/style.md`, *Folder READMEs*, expect ``- `<name>/` <sentence>.``, with no colon. The documenter followed the guard. Options:
       a. Correct the criterion's wording to the form with no colon, which matches the guard and the READMEs as written. **I would choose a.**
       b. Keep the colon. Then the guard and the style guide change too, which is outside this story.

    Other criteria: criteria 1 to 3 are checked by the existing guards (`tests/guards/test_folder_readmes.py`) and by the document check, so I see no new test to write for them. Criterion 4 is the docs stage's `make documents`. If you want a test for criterion 3 (the layout link, the `contract/` sentence, each area's guide link, and `entry` with no subfolder lines), say so, and I would add it under `tests/guards/`.

    Files created: none. Modules the test run could not import: none (no run was made).
14. 2026-11-07 human: 1. (a), with the human's leave: add "README.md" to the expected set, rename the test as you propose, and say the same in the module docstring; rewrite the story's 'no test changes' line to name this change. The leave also covers any other earlier guard whose only failure is a README.md of this story standing in its folder, changed the same way (the README added to the expected entries, the test keeping its name's purpose); the entry names each one.
    2. (a): the criterion's wording follows the guard and the style page, the form with no colon.
    No new test for criterion 3: the reviewer checks it.
15. factory: started tests as vm.
16. tester: I made the test change you gave leave for in journal 14, item 1, and rewrote the story to match. I wrote no new test, because you said the reviewer checks criterion 3.

    Test changed (an earlier story's test, under your leave in journal 14, item 1):
    - `tests/guards/test_old_layer_packages_removed.py`: the expected entries of `src/factory/` now include `"README.md"`. I renamed `test_the_package_holds_only_its_init_the_areas_entry_and_contract` to `test_the_package_holds_only_its_init_its_readme_the_areas_entry_and_contract`. The module docstring now says the same (the package holds its init, README, areas, entry and contract), cut down so it fits ruff's 100-character limit. The test still does its job: it keeps old layer packages out of the package root.
    - I found no other guard whose only failure is one of this story's READMEs. All of `tests/guards` passes, so nothing else changed under that leave.

    Story text, with your answers in journal 14:
    - Description and Interface: the "No code and no test changes" lines now name this one test change.
    - Criterion 1: the subfolder line is written ``- `<name>/` <one sentence>.``, without the colon, to match the guard and the style page (item 2a).

    Criterion → test:
    - criterion 1: `tests/guards/test_folder_readmes.py`, the existing guard. It passes for all nine READMEs and skips none of them; the 14 skips are other stories' folders not written yet.
    - criterion 2: the document check (`make documents`) and the existing `tests/guards/test_folder_readmes.py`. No new test.
    - criterion 3: no test, as you decided in journal 14; the reviewer checks it.
    - criterion 4: `make documents`, run by the docs stage. No test.
    - criterion 5: `make check`, including `tests/guards/test_old_layer_packages_removed.py::test_the_package_holds_only_its_init_its_readme_the_areas_entry_and_contract`.
    - criterion 6: docs, no test.

    Run: `uv run pytest -q tests/guards/test_old_layer_packages_removed.py tests/guards/test_folder_readmes.py` passes, with 14 skips (other stories' folders). The whole of `tests/guards` passes too. `make lint` is green. These tests are green, not red, because the documents already exist.

    Files created: none. Files changed: `tests/guards/test_old_layer_packages_removed.py` and this work item's Description. Modules the test run could not import: none.

    The factory left out changes outside the write paths: factory/features/F0055-every-folder-says-what-it-holds/in-progress/F0055-S0002-the-package-and-its-areas-say-what-they-hold.md.

    `lint`: lint: green (0.2 s)
17. factory: started doing as vm.
18. coder: I wrote no code and changed no file. This story takes the docs route, and the tester has already made the one test change the human allowed (journal 14). I ran `make check` on the branch as it stands, and it ends with `test: green (100.6 s)` and `check: green`. There was no failing test to implement against, so no diff of mine needed a refactor.

    What this round built: nothing new from me. On the branch, the documenter wrote the nine READMEs: `src/factory/README.md` and `src/factory/{agents,entry,hosting,machine,pipeline,shared,watching,work}/README.md`. It also added their paths to `docs/checked-documents.txt`. The tester changed `tests/guards/test_old_layer_packages_removed.py`.

    Main choice: I handed forward without touching any code. The rejected alternative was to add or adjust anything under `src/factory`, which the story rules out.

    Noticed, not touched:
    - The tester's rewrite of the work item's Description was left out by the factory because the path is outside the tester's write paths (journal 16). So the Description and Interface still say "No code and no test changes". Criterion 1 still shows the subfolder line with a colon, ``- `<name>/`: <one sentence>.``.
    - The human's answer in journal 14 changes both points. The story now carries one test change, the README added to that guard's expected entries. Criterion 1 should give the form without the colon, ``- `<name>/` <one sentence>.``, which matches the guard and the style page.
    - I did not rewrite the Description: I could not confirm that my write paths include the work item. Whoever may write it should apply those two changes.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
19. factory: started review as vm.
20. reviewer: no findings

    What I reviewed: `git diff main...HEAD -- . ':!factory'`, which is the nine new READMEs, `docs/checked-documents.txt` and `tests/guards/test_old_layer_packages_removed.py`. I read it against the work item, the `__init__.py` docstrings, the module listing of every layer, `docs/project-guide/README.md` (*The code's layout*, *The files*) and `docs/project-guide/style.md` (*Folder READMEs*).

    - Group 1, criteria:
      - Criteria 1 and 2: all nine files exist. Each opens with one sentence and links to a guide page. Every area README names `adapters/`, `application/` and `domain/` in the form with no colon. `src/factory/README.md` names all nine of its subfolders. All nine paths are on `docs/checked-documents.txt`. The guard `tests/guards/test_folder_readmes.py` and the document check cover these criteria. The tester reports the guard passing for all nine with none skipped, and the documenter reports `documents ok (75.1 s)`.
      - Criterion 3, which the human left to the reviewer:
        - `src/factory/README.md` links to `docs/project-guide/README.md`, *The code's layout*, and its `contract/` line says the schemas are generated and never edited by hand.
        - Each area README links to the `Guide:` page its `__init__.py` names. I checked all seven.
        - `src/factory/entry/README.md` is one sentence plus a link to `docs/project-guide/README.md`, with no subfolder lines.
      - Criterion 4 is the docs stage's gate. Criterion 5: the factory's `make check` after the coder was green (journal 18). The Interface states no limit beyond the guard's.
    - Layer lines (judged by the reviewer, per journal 4): I compared each one with the modules in its layer. Each names only modules that exist there. Some leave out a minor module, which is not wrong for a pointer README: for example `oauth_token`, `record_log_jsonl`, `preflight_stamp_file`, `stage_layer`, `machine_stop_exit`, `disk_records`. The hosting adapters' "test fixtures" are `checkout_fixture.py` and `instance_fixture.py`. The pipeline adapter is the one ruamel.yaml reader.
    - Group 2, architecture: no code changed and no layer was touched.
    - Group 3, security: no secrets and no markers.
    - Group 4, quality: nothing to report. The README prose ("The reader of the pipeline definition, YAML.", the `# entry` title next to "# The X area") is for docs-review to judge against the style page.
    - Group 5, hygiene: the journal explains the main choices. These are the form with no colon (journals 8 and 14) and the test change under the human's leave (journals 14 and 16). The docs criterion still describes what was built: no guide page names a folder README, so no link was needed.
    - Documents item: I checked every claim in the nine READMEs against the code on the branch and could find each one. They show no commands.

    I corrected the work item, because the factory dropped the tester's rewrite (journal 16) and the human's answer in journal 14 settles both points. I changed nothing else:
    - description corrected (Description): "No code and no test changes." -> "No code changes; the one test change is the human's leave (journal 14): `tests/guards/test_old_layer_packages_removed.py` gains `README.md` in the expected entries of `src/factory/`, its test renamed to say so."
    - description corrected (Interface): "- No code and no test changes." -> "- No code changes. One test change, with the human's leave (journal 14)", naming the test file, the added `"README.md"`, the rename and the docstring.
    - description corrected (criterion 1): ``- `<name>/`: <one sentence>.`` -> ``- `<name>/` <one sentence>.``, the form with no colon (journal 14, item 2a).

    Earlier tests:
    - `tests/guards/test_old_layer_packages_removed.py`: changed under the human's leave, journal 14, item 1. It adds `"README.md"` to the expected set and renames the test to `test_the_package_holds_only_its_init_its_readme_the_areas_entry_and_contract`, and the module docstring says the same. Nothing goes beyond that leave.
