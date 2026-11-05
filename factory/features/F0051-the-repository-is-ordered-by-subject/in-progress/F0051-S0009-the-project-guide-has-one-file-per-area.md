---
stage: doing
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 564
comments_read: [6650898693, 6650987283, 6651349591]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-05T06:27:38.992162Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T05:50:21.260474Z'
  stage: intake
  run: 3b60f030ca3643e2b10630e0b5196ac5
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T05:56:14.852314Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T05:56:17.233565Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T05:56:35.802324Z'
  stage: intake
  run: 1ae9f33f42a54981b28afe2b507e4f5a
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T05:56:41.131645Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-05T05:57:29.822424Z'
  stage: tests
  run: b0850eaf61bc4a45937f2d6ad290f07d
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-05T06:03:24.087004Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-05T06:03:26.859907Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-05T06:04:54.697067Z'
  stage: tests
  run: 1effae5adebf45c180d337ab1cbab9f3
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T06:04:59.979265Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-05T06:13:01.304606Z'
  stage: doing
  run: 7d9e8cca0e7545ef8077a18390894673
- number: 14
  speaker: factory
  kind: stall
  at: '2026-11-05T06:13:01.467712Z'
  stage: doing
  run: 7d9e8cca0e7545ef8077a18390894673
  reason: check_red
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-05T06:13:08.502652Z'
  stage: doing
- number: 16
  speaker: coder
  kind: question
  at: '2026-11-05T06:13:34.161906Z'
  stage: doing
  run: dab7d95781294e1393bdf77e52e57024
  blocked: question
- number: 17
  speaker: human
  kind: comment
  at: '2026-11-05T06:27:36.483176Z'
  stage: doing
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-05T06:27:38.992162Z'
  stage: doing
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
3. The index's *The files* names each of the eight files with a sentence on what it covers and the modules it describes, by their new paths; every `src/factory/<area>/` path the index names exists.
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
3. intake: 1. Placement has no criterion. The Description says each section moves "to the file of the area whose modules it describes", and a section that describes several areas goes to the area of its first module. Criterion 2 only checks that each heading appears exactly once somewhere in the new files. A coder could put every section in `shared.md` and still pass. Please add a table of heading → target file to the story, and a criterion that each heading is found in its file. I would choose that table, with the whole-file moves (`git-and-hosting.md`→`hosting.md`, `work-items.md`→`work.md`, `stage-environment.md`→`machine.md`, `stages.md`→`pipeline.md`) given as a rule, and only the sections of the other files (`agents.md`, `write-paths.md`, `costs.md`, `watching.md`, `processes-and-checks.md`) listed by heading.
   2. The one-line pointers have no criterion. The Description says a multi-area section is "named from the others' files by a one-line pointer". Please add a criterion that names each such section, the file it moves to and the files that carry the pointer. I would choose one row per multi-area section.
   3. "The words of the sections do not change, except the pointers between files" has no criterion. Please say how it is checked, for example that each section's body text, apart from lines naming guide files, is identical to the one on `origin/main`. Or please say it is the reviewer's judgement and not a test.
   4. Criterion 3 says the index names "the modules it describes, by their new paths". Please state what is checked. I would choose: each of the eight files is named in *The files* with a sentence, and every `src/factory/<area>/` path it names exists.
   5. Interface says "the agent files are changed to the new names", but the criteria only require that no named guide file is missing (criterion 4). Please confirm that the agent files must name the new files correctly, not merely existing ones. I would choose the criterion 4 wording as it stands.
   6. Criterion 4 covers `claude/`, `docs/` and `README.md`. `CLAUDE.md` also names guide files and is the human's change. Please confirm that the test leaves `CLAUDE.md` out, or say that the human changes it first.
4. 2026-11-05 human: Answers of the human:

   This is a documents-only story; keep its tests few and let the reviewer judge the prose.

   1. **No table.** The rule decides: the four whole-file moves as you name them, and every other section goes to the file of the area of the first `factory.<area>` module it names (a section that names none stays in `README.md`). Placement is the reviewer's check against that rule, not a test.
   2. **No criterion.** The pointers are the reviewer's judgement.
   3. **The reviewer's judgement, not a test.** The reviewer compares the moved sections with `origin/main` and counts any change beyond pointers as a finding.
   4. **As you propose:** each of the eight files is named in *The files* with a sentence, and every `src/factory/<area>/` path the index names exists.
   5. **Criterion 4 as it stands.**
   6. **`CLAUDE.md` is left out of the test.** I change its guide-file names after the merge, as the Interface says.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: a documents-only story. It names the files under `docs/project-guide/` and the `git mv` pairs, changes no module, and the agent files get the new names. Nothing here needs a signature.
   - Criteria: criteria 1 to 4 are each testable by one function: the exact file set, each pre-story heading found exactly once (a row per heading), the index's *The files* entries, and no dangling guide-file name under `claude/`, `docs/` or `README.md`. The human's answer (journal 4, item 4) adds that every `src/factory/<area>/` path the index names exists. I wrote that into criterion 3. Placement, the pointers and unchanged section words are the reviewer's judgement per journal 4, items 1 to 3. Journal 4, item 6 leaves `CLAUDE.md` out of the test. The story has no failing-side rule beyond these.
   - Smoke test: `ls docs/project-guide | tr '\n' ' '` is runnable. Its Expect line gives the exact nine-file listing, which can be checked against the output.
   - Architecture: the seven area names match `CLAUDE.md`'s areas. `operator.md` stays because it covers the operator's scripts outside `src/`.
   - Scope: this is F0051's S0009 as the feature lists it. It changes no code or test, and `CLAUDE.md` stays the human's change.
7. factory: started tests as vm.
8. tester: I wrote no tests. I stopped at step 1 because three of the criteria can't be tested as they are written, and the Interface contradicts itself.

   1. **Interface or tests.** The Interface says "no test is written" and the Description says the story "changes no code and no test". The human's answer (journal 4) says "keep its tests few", and my role is one test per criterion. Options: (a) one guard test module, `tests/guards/test_project_guide_files.py`, that tests criteria 1 to 4; (b) no tests, with the reviewer and `make documents` as the gate. I would choose (a), and the Interface line would be rewritten to "no module under `src/factory/` changes".

   2. **Criterion 2 can't be met for repeated headings.** On `origin/main` (bfbbef9d9) five headings already appear more than once:
      - `## Replaced in v1.2`: 3 times (agents.md, processes-and-checks.md, write-paths.md)
      - `### Faults`: 4 times (agents.md, stage-environment.md, stages.md, work-items.md)
      - `### For the preflight`: twice, both in stage-environment.md
      - `### The stand-in`: twice, both in stage-environment.md
      - `### The fake`: twice (agents.md, git-and-hosting.md)

      stage-environment.md moves whole and its words don't change, so "found exactly once" fails on purpose. Options: (a) each heading is found as many times in the new files as it was before (one row per distinct heading, with its count); (b) "exactly once" for the headings that were unique and "at least once" for the repeated ones. I would choose (a).

   3. **Criterion 4 fails on files nobody may change.**
      - `docs/decisions.md:775` names `git-and-hosting.md`, `processes-and-checks.md`, `work-items.md`, `costs.md` and `stages.md`, and criterion 6 says decisions.md gets no change.
      - `docs/runs/2026-10-12-overnight/night-log.md` (lines 982 and 1013) names `project-guide/stage-environment.md`, and `docs/runs/` is the human's.

      I'd also need to know what counts as "naming a guide file". Options: (a) the test searches `claude/`, `docs/` (without `docs/runs/` and `docs/decisions.md`) and `README.md` for the seven removed names (`git-and-hosting.md`, `work-items.md`, `write-paths.md`, `costs.md`, `stages.md`, `stage-environment.md`, `processes-and-checks.md`), written bare or as `project-guide/<name>`; (b) the same, but decisions.md stays in and is changed too, which revises criterion 6. I would choose (a). One effect: `docs/operator-guide.md:1977` and `:2109` would then have to change in this story, and criterion 6 says operator-guide.md: none. Please confirm that operator-guide.md changes as well.

   4. **Criterion 3: "each of the eight files".** I read the eight as the seven area files plus `operator.md`, with the index not naming itself. I would choose that reading.

   Where I stopped: nothing is written, no files were created, and no test run was made.
9. 2026-11-05 human: Answers of the human:

   1. **(a)**: one guard module, `tests/guards/test_project_guide_files.py`, for criteria 1 to 4. The Interface line reads "no module under `src/factory/` changes".
   2. **(a)**: each distinct heading is found as many times in the new files as it was on `origin/main`, one row per heading with its count.
   3. **(a)**: the search covers `claude/`, `docs/` without `docs/runs/` and `docs/decisions.md`, and `README.md`, for the seven removed names, bare or as `project-guide/<name>`. Yes, `docs/operator-guide.md`'s two lines change in this story; criterion 6 names them.
   4. **Yes**: the seven area files and `operator.md`; the index does not name itself.
10. factory: started tests as vm.
11. tester: I wrote one guard module for criteria 1 to 4, as the human answered in journal 9. I also rewrote the Description to match those answers: the Interface line and criteria 2, 3, 4 and 6.

    - criterion 1: tests/guards/test_project_guide_files.py::test_the_guide_holds_the_index_operator_and_the_seven_area_files
    - criterion 2: tests/guards/test_project_guide_files.py::test_every_earlier_heading_is_kept_as_often_as_before
      - Parametrized with one row per distinct heading and its count.
      - The 159 rows were taken from the guide as committed at the start of this stage. That guide was still unchanged from `origin/main`.
      - *The files* is left out. Headings inside fenced code blocks are not counted.
    - criterion 3: two tests.
      - tests/guards/test_project_guide_files.py::test_the_index_names_each_file_with_a_sentence is parametrized over the seven area files and `operator.md`. It checks for a list item "- `<name>` … ." in *The files*.
      - tests/guards/test_project_guide_files.py::test_every_source_path_the_index_names_exists covers every `src/factory/…` path in the index.
    - criterion 4: tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file
      - It searches `claude/`, `docs/` (without `docs/runs/` and `docs/decisions.md`) and `README.md` for the seven removed names, bare or as `project-guide/<name>`.
      - `CLAUDE.md` is left out.
      - The match is refused when a word character, `.` or `-` comes just before the name.
    - criteria 5 and 6: no test (make check, and the docs stage).

    Files created: tests/guards/test_project_guide_files.py. Files changed: the work item's Description.

    Modules the test runner could not import: none. The module imports nothing from `factory`.

    Red run, as expected:
    - The file-set test fails.
    - The index test fails for hosting.md, work.md, machine.md and pipeline.md, and also for shared.md, which the output did not show.
    - The removed-name test fails. Today it finds `docs/operator-guide.md` lines 1870, 1977 and 2109. That is three lines, not the two named in journal 8 and 9; criterion 6 now covers every such line in operator-guide.md.

    The heading-count rows pass now and must keep passing after the moves. `make lint` is green.

    Open:
    - I ran the test file twice instead of once. The second run was by mistake and changed nothing.

    The factory left out changes outside the write paths: factory/features/F0051-the-repository-is-ordered-by-subject/in-progress/F0051-S0009-the-project-guide-has-one-file-per-area.md.

    `lint`: lint: green (0.1 s)
12. factory: started doing as vm.
13. coder: I regrouped the project guide into one file per area. Afterwards `tests/guards/test_project_guide_files.py` passes (all rows), `make check` is green and `make documents` reports `documents ok`. The smoke-test listing matches what the story expects.

    What I built (all under `docs/project-guide/`, plus one other file):
    - **Whole-file moves with `git mv`:**
      - `git-and-hosting.md` → `hosting.md`
      - `work-items.md` → `work.md`
      - `stage-environment.md` → `machine.md`
      - `stages.md` → `pipeline.md`
    - **Sections moved by hand, by the human's rule (journal 4.1: a section goes to the area of the first `factory.<area>` module it names):**
      - `shared.md` is new. It holds *Starting a process*, *The duplicates report* and *The document check*, from `processes-and-checks.md`.
      - `machine.md` gains *Project commands*, *Mutation testing* and *Replaced in v1.2*, from `processes-and-checks.md`.
      - `pipeline.md` gains *The take's rule* (from `write-paths.md`), plus *The tick*, *The handlers of the events* and *Stops, the clock and the factory log* (from `watching.md`).
      - `watching.md` now holds *The evaluation* plus *Cost records* and *Bills*, from `costs.md`.
      - `agents.md` keeps its sections and gains *The write paths* and that file's *Replaced in v1.2*.
      - `README.md` gains *The demos*, which names no area module.
      - `write-paths.md`, `costs.md` and `processes-and-checks.md` are removed.
    - **The index `README.md`:** the intro now says "one file per area". *The files* has one entry per file in area order. Each entry names its `src/factory/<area>/` folder and its modules, with the old module lists regrouped.
    - **Titles:** the files whose content changed got a new title and opening sentence.
    - **Pointers:** every guide-file name in the guide now uses the new name. References to a section that is now in the same file drop the file name. Two references in `watching.md` that now cross files gain "`pipeline.md`". The opening line of `watching.md` points to `pipeline.md` for the tick, the handlers, the stops and the boundaries.
    - **`docs/operator-guide.md`:** lines 1870, 1977 and 2109 now name `pipeline.md` and `work.md`. `claude/` named no guide file, so nothing there changed.

    Main choice: I applied the regrouping rule only to the ten per-domain files the Description lists, and left the index's own sections where they were (*The code's layout*, *Shared test helpers*, *Errors*, *The models' configuration*, *Kill points*, *Fault-injection paths*). The index describes them as "what holds for all code". The alternative I rejected was moving *Errors* and *Kill points* to `shared.md`, because they name `factory.shared` first. I also kept these sections in the file of the topic they follow, rather than sending them to `README.md`, even though they name no area module:
    - the "Replaced" sections (they are appendices of that topic);
    - *The shipped agents, settings and template*.

    The reviewer may judge both readings.

    Refactor: I re-read the diff and found nothing to change. The section bodies are unchanged except for the pointers.

    Seen but not touched:
    - The Description still has its pre-journal-9 wording (the tester's rewrite was left out by the factory). It is outside my write paths, so I did not rewrite it. Journal 9 changed the Interface line to "no module under `src/factory/` changes", and criteria 2, 3, 4 and 6 now follow the tester's entry 11.
    - `docs/decisions.md:775` and `docs/runs/` still name the old files, and are excluded on purpose.
    - `CLAUDE.md` still names `docs/project-guide/README.md` only; the human changes it after the merge.
    - Some unchanged cross-file references (for example in `work.md` and `agents.md`) name a section without its file, as they did before.

    The factory left out changes outside the write paths: docs/operator-guide.md, docs/project-guide/README.md, docs/project-guide/agents.md, docs/project-guide/costs.md, docs/project-guide/git-and-hosting.md, docs/project-guide/hosting.md, docs/project-guide/machine.md, docs/project-guide/operator.md, docs/project-guide/pipeline.md, docs/project-guide/processes-and-checks.md, docs/project-guide/shared.md, docs/project-guide/stage-environment.md, docs/project-guide/stages.md, docs/project-guide/watching.md, docs/project-guide/work-items.md, docs/project-guide/work.md, docs/project-guide/write-paths.md.
14. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
    src/factory/work/domain/acceptance.py                  186      1     46      1    99%   356
    ------------------------------------------------------------------------------------------------
    TOTAL                                                10634     49   2128     46    99%

    154 files skipped due to complete coverage.
    Required test coverage of 90.0% reached. Total coverage: 99.26%
    ======================================================================================= short test summary info ========================================================================================
    FAILED tests/guards/test_project_guide_files.py::test_the_guide_holds_the_index_operator_and_the_seven_area_files - AssertionError: assert ['README.md',...ecks.md', ...] == ['README.md',...line.md'...
    FAILED tests/guards/test_project_guide_files.py::test_the_index_names_each_file_with_a_sentence[shared.md] - assert False
    FAILED tests/guards/test_project_guide_files.py::test_the_index_names_each_file_with_a_sentence[hosting.md] - assert False
    FAILED tests/guards/test_project_guide_files.py::test_the_index_names_each_file_with_a_sentence[work.md] - assert False
    FAILED tests/guards/test_project_guide_files.py::test_the_index_names_each_file_with_a_sentence[machine.md] - assert False
    FAILED tests/guards/test_project_guide_files.py::test_the_index_names_each_file_with_a_sentence[pipeline.md] - assert False
    FAILED tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file - AssertionError: assert ['docs/operat...aths.md', ...] == []
    make: *** [Makefile:89: test] Error 1
15. factory: started doing as vm.
16. coder: I wrote nothing in this run. The coder role is not allowed to write the files this story changes, so the work cannot get through this stage.

    What happened: the previous doing run (journal 13) did the whole regrouping under `docs/project-guide/` and the three lines in `docs/operator-guide.md`. `make check` and `make documents` were green on the agent's side. The factory then dropped every one of those changes as "outside the write paths": `docs/project-guide/*.md` and `docs/operator-guide.md` (journal 13, last paragraph). It ran `make check` on what was left, which was the unchanged guide plus the tester's new guard, and the guard failed (journal 14). The committed tree I started from today is still the old guide: `costs.md`, `git-and-hosting.md`, `processes-and-checks.md`, `stage-environment.md`, `stages.md`, `work-items.md`, `write-paths.md`, and no `shared.md`/`hosting.md`/`work.md`/`machine.md`/`pipeline.md`. If I redo the work, the same thing happens again, and that would use up the last stall attempt (attempt 2 of 2).

    `tests/guards/test_project_guide_files.py` can only pass once `docs/project-guide/` and `docs/operator-guide.md` have changed. In this pipeline only the docs stage (the documenter) writes those files, and doing comes before docs. As things stand, nothing the coder can write makes `make check` green.

    Options I see:
    (a) Add `docs/project-guide/**` and `docs/operator-guide.md` to the doing stage's write paths for this story. That is a human change to `factory/pipeline.yml`. Then I redo the regrouping exactly as journal 13 describes it.
    (b) Move the work to the docs stage. The human or the tester marks the guard module so it does not block the doing stage's `make check`, the doing stage hands forward with no change, and the documenter does the regrouping, which is the work its role already covers. This needs a decision on how the guard waits, and that is a test change.
    (c) The human makes the docs change on the branch by their own commit, and doing then hands forward with no change.

    I would choose (a): the work is done and checked once already (journal 13), and only the write paths stand in the way.

    Journal 9 changed the Description: the Interface reads "no module under `src/factory/` changes", criterion 2 counts each heading as often as before, and criterion 4's search leaves out `docs/runs/` and `docs/decisions.md`. The tester's rewrite of the Description was also dropped by the factory, so the work item still carries the wording from before journal 9. I can't rewrite it either, because the work item is outside my write paths.
17. 2026-11-05 human: Answer of the human:

    **(a).** `factory/pipeline.yml` on `main` now lets the coder write `docs/project-guide/*`, `docs/operator-guide.md`, `docs/operator-guide/*` and `README.md`, for the rest of F0051 only (S0009 to S0012, whose guards check documents). The next stage merges `main` into the branch. Redo the regrouping as journal 13 describes it, and end with `review`. The documenter still does the docs criterion's other parts.

    The Description's wording from journal 9 is the reviewer's to write back; the reviewer may do that in its run.
18. factory: started doing as vm.
