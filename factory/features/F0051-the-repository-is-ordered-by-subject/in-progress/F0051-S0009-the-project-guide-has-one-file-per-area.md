---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 564
comments_read: [6650898693, 6650987283]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-05T06:03:26.859907Z'
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
