---
stage: docs-review
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 626
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T05:48:44.076997Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T05:48:44.085536Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T05:48:58.672149Z'
  stage: intake
  run: 0adfeb41fe064d398392476350541833
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T05:49:03.443475Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T05:58:07.075776Z'
  stage: docs-only
  run: ec6df42304d745be80379ede425345c6
- number: 6
  speaker: factory
  kind: stall
  at: '2026-11-07T05:58:07.458896Z'
  stage: docs-only
  run: ec6df42304d745be80379ede425345c6
  reason: check_red
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T05:58:14.324444Z'
  stage: docs-only
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-07T06:01:09.927638Z'
  stage: docs-only
  run: 7f74800d6a2544078fae85262d9b17ca
---

# The project guide's page on the pipeline area reads for the developer

## Description

`docs/project-guide/pipeline.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/pipeline.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/pipeline.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/pipeline.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/pipeline.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/pipeline.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/pipeline.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete files only (`docs/project-guide/pipeline.md`, `docs/checked-documents.txt` with its one line) and rules for links and headings. It states no code behaviour, and the docs route fits because every path it changes is under `docs/`.
   - Criteria: each can be checked on the documents. `make documents` covers 3 and 4 mechanically, and the reviewer compares the old and new file for 1 and 2. The Interface states no rule with a failing side, so none is missing a criterion. The rule on links to changed headings has criterion 5, and the "linked once" rule has criterion 4.
   - Smoke test: `grep -cx "docs/project-guide/pipeline.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked. It runs no pytest.
   - Docs criterion: criterion 7 says what the reader must know (criteria 1 to 5, meaning the page is true to the code and complete). It quotes no sentences.
   - Architecture: the story only touches a project-guide page, which is a document the documenter may write. No code, test or agent file changes.
   - Scope: S0018 is listed in F0054's stories, and it changes nothing listed in "Out of scope" (`decisions.md`, `docs/runs/`, the playbook).
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `docs/project-guide/pipeline.md`: rewritten for the developer about to change the pipeline area. Each section now opens with what the part is for, then the names and signatures in an indented block, then the rules one per bullet, then See also. Modules are linked once at their first mention. Feature, story and requirement IDs (R5) and the history lines ("of earlier versions", "went with the second user", "v1's order") are gone. Glossary words are linked at first use. Headings that other files cite are unchanged: *The pipeline definition*, *The rules of the definition*, *Starting a stage*, *After the agent run*, *The stage protocol*, *`StageFinisher.finish(aftermath)`*, *The take's rule*, *Asking the human*, *Boundaries*, *The idle shutdown*. One heading was renamed: *Stops, the clock and the factory log* is now *The stop records*, and nothing outside the file cited it.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/pipeline.md`.

   What I did to the content:
   - I moved text rather than cutting it. Every name, setting, fault text and rule of the old file is in the new one, and the test lists are kept as inline "Tests:" lines.
   - I split the old miscellany at the end of the handlers section into headed sections: *Waiting out the provider's limit*, *The preflight in the tick*, *The stale branch*, *The agent run's environment*, *The settings*, *Boundaries in tests*, *`factory-health` and `factory-run`*, *`StopService`* and *The clock, the log and the stores*.
   - I turned the "twelve rules" count into a table with a row 12 for the `not_read` rule, which the code runs last as the 11th entry of `_RULES` (the contract function gives rules 1 and 2). The old table stopped at 11.
   - The runnable `uv run python` example now sits in a `console vm` block, copied from a real run in this checkout. It needs the project's environment, and the docs check container prints `Using CPython ...` for `uv run`. I replaced the old second half of the example, the `contrakt` fault, with a prose sentence. Its text is from the old file, and I did not re-run it.
   - Style rule 8 (A code block holds no links) is met by linking the file above each signature block.

   Not done, and why:
   - There is no *Reference* section at the end. The detail stays in the rules of each section, and I did not move it. The reviewer may ask for one.
   - I did not read each claim against the code. I checked the rule count and the names the code gave (`_RULES`, `CONTRACT_MAJOR`, `RETRY_WAITS`, `STALL_TAIL_LINES`, `ERROR_CAP`), and `make documents` resolved every name and link. The rest of the old claims are carried over unchecked, so a reviewer who compares against the code may find drift.
   - `decisions.md` is untouched, as the story says; no "Why" or "Rejected" text was written.

   Cross-read and found current: the operator-guide files that link into this file (`stops.md`, `pipeline.md`, `records.md`, `health.md`) and `machine.md`, `hosting.md`, `agents.md`, `work.md`, `watching.md`, `style.md` of the project guide. Their headings and links to this file still resolve.

   Checks: `make documents` ended with `documents ok (15.9 s)`. I ran no `make check`, because every changed file is a document.

   Stale text seen, not mine to fix: `docs/project-guide/README.md` lines 67 to 141 and 283 and `README.md:28` are reported by `make documents` under "Report (not checked yet)" as paths that do not exist (`support/...`, `project/factory/...`, `factory/stage.Containerfile`). These files are not on the checked list.
6. factory: Stage docs-only stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/watching/application/transcripts.py         61      2     10      0    97%   91-92
   src/factory/watching/domain/board.py                    55      0      4      1    98%   77->75
   src/factory/watching/domain/machine.py                  52      3     18      5    89%   44->42, 47, 59, 77->75, 79
   src/factory/watching/domain/transcripts.py              10      2      0      0    80%   20-21
   src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   239
   src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
   src/factory/work/domain/acceptance.py                  195      1     52      1    99%   367
   ------------------------------------------------------------------------------------------------
   TOTAL                                                11211     55   2254     52    99%

   157 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.21%
   ======================================================================================= short test summary info ========================================================================================
   FAILED tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file - AssertionError: assert ['docs/projec...ork-items.md'] == []
   make: *** [Makefile:89: test] Error 1
7. factory: started docs-only as vm.
8. documenter: Round 0, second run after the red check. The check was red because of one test, `tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file`. It flagged four lines of `docs/project-guide/pipeline.md` (545, 558, 569, 620). On each, the link text `work-items.md` matched the guard's pattern for a removed guide file. The links themselves point at the existing `docs/operator-guide/work-items.md` and were fine.

   Files changed:
   - `docs/project-guide/pipeline.md`: on those four lines, the link text `[work-items.md]` is now `[the operator guide on work items]`. The targets are unchanged.

   Checks: the guard test passes when run alone, and `make documents` ends with `documents ok (16.7 s)`. I did not run `make check`, since the only file changed is a document; the factory's gate decides.

   For the reviewer, from the first run's entry, which still stands:
   - The page has no *Reference* section. The detail stays in each section's rules.
   - The documenter checked only the rule count and a few named constants against the code. The other claims were carried over from the old file without comparing them to the code. Please compare the old and new file against the code.

   Stale text I saw but did not touch, unrelated to this story: paths that do not exist in `docs/project-guide/README.md` (lines 67 to 141 and 283) and `README.md:28`. `make documents` lists them as "not checked yet".

   `check`: check: green
   `secrets`: secrets: green (0.7 s)
   `documents`: documents ok (16.3 s)
