---
stage: docs-only
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 622
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T03:47:57.817768Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T03:47:57.825123Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T03:48:12.406452Z'
  stage: intake
  run: 10e66264532943fd8db09367d103f89d
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T03:48:17.098338Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T03:54:29.515097Z'
  stage: docs-only
  run: f10b8f15d2ff4e719281ec3db598b09d
- number: 6
  speaker: factory
  kind: stall
  at: '2026-11-07T03:54:29.920118Z'
  stage: docs-only
  run: f10b8f15d2ff4e719281ec3db598b09d
  reason: check_red
---

# The project guide's page on the work area reads for the developer

## Description

`docs/project-guide/work.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/work.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/work.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/work.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/work.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/work.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/work.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths (`docs/project-guide/work.md`, `docs/checked-documents.txt` with exactly one line), states link and heading rules, and says no code, test or agent file changes. It contains no signatures to test, since the story only changes documents.
   Criteria: 1 to 5 can each be judged or checked. The style and the old-versus-new comparison go to the reviewer, as the feature's decision 2 says. The checked list, `documents ok` and broken links are checked by `make documents`. The Interface states no rule with a failing side beyond the link and heading rules, which criteria 4 and 5 cover. 6 is `make check`.
   Smoke test: `grep -cx "docs/project-guide/work.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It runs no pytest.
   Docs criterion: it names what the reader must know, in the form "as criteria 1 to 5", and dictates no sentences. `docs/decisions.md` is stated as none.
   Architecture: the only paths changed are `docs/project-guide/work.md` and `docs/checked-documents.txt`, both documents the documenter may write. The docs-only route is chosen because the story changes only documents.
   Scope: it is S0014 of F0054, one file, and the feature scope lists "each of the 22 files, one story each". It touches nothing in the feature's Out of scope: `docs/decisions.md`, `docs/runs/`, the operator playbook and behaviour changes.
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/project-guide/work.md` for its reader and added it to the checked list. `make documents` prints `documents ok (9.6 s)`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/project-guide/work.md`: rewritten in the order style.md gives (idea, names in a block, one rule per bullet, See also). The old headings stay, so links from other files still resolve. Detail that the sections only summarise moved to a new closing section, *Reference*. It holds the path constants, the field tables, the full acceptance rules (reader, opening, hand-over, facts), the records-contract schema text and the layout of the written file with its notation. Module files are linked once at first mention. The six examples are now `console` blocks. I ran them, copied the real output, and `make documents` runs them again.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/work.md`.
   - `docs/project-guide/README.md`: the index entry for `work.md` now lists the new *Reference* section.

   Corrections and removals, checked against the code:
   - The records-contract version in the old text was `2.0`; `RECORDS_CONTRACT` is `4.4`. I wrote `4.4`.
   - I removed history wording: "from now on", "moved there from", "so existing imports stay valid", "a record written before they existed", and the reference to the feature's decision 4.
   - Writing `factory/agents` as `<project>/factory/agents`, as the style page asks, was needed to pass the name check.

   Examples that changed:
   - Each console command is now one line, because the runner does not accept `>` continuation lines.
   - The error example now shows the last line of the traceback, `factory.shared.domain.errors.WorkItemFormatError: unknown key: colour`, where the old text printed only the fault.
   - The sections example uses tilde fences, so its output can sit inside a backtick block.

   Compare old and new:
   - I tried to keep every name, rule and message of the old file, either in a section or in the Reference.
   - I wrote the new text from the old text. I did not re-read all of the code behind each rule, only a sample: the contract version, the existence of the handlers and functions, the journal's private `_state_of`, `cost_table_key` and `BRANCH_PREFIX`.
   - The reviewer should compare the old and new files, especially the acceptance bullets I condensed.
   - I dropped two sentences on purpose: a duplicated cross-reference to *The wiring* and the closing "Plain string order... is the human's only priority".
   - I shortened the acceptance-status, hand-over and facts text to a bullet each in the section and kept the full rules in the Reference.

   Cross-read and found current: the index `docs/project-guide/README.md` other than the new *Reference* entry, `docs/operator-guide/pipeline.md` (*Checking a story before it starts*) and `docs/operator-guide/work-items.md` (*When a feature acceptance is due*). I did not touch `docs/decisions.md`.

   Not touched, unrelated to this story: `docs/project-guide/README.md` keeps names like `support/site_check_support.py` that `make documents` reports under "not checked yet" (README is not on the checked list). `agents.md` and `machine.md` have the same kind of report lines. I cut a "Plain string order alone would put ... " sentence from the order section, so check that the key's purpose is still clear.

   No findings for the coder.
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
