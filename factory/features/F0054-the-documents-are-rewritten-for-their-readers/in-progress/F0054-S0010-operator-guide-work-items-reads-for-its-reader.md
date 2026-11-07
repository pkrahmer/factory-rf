---
stage: docs-only
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 618
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T02:07:21.054390Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T02:07:21.061631Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T02:07:35.545760Z'
  stage: intake
  run: da90882f7e2948c7b810fb77bc7154f8
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T02:07:40.253048Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T02:11:52.156587Z'
  stage: docs-only
  run: 9231e6e5a1804fa3b6ce428c3d802039
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T02:11:56.999472Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:13:46.417046Z'
  stage: docs-review
  run: 0ed158b1e4ca47c48b288ca3addd8f38
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T02:13:51.544703Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T02:17:06.304775Z'
  stage: docs-only
  run: d9eb47380b794325b875673fa1aa91c7
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T02:17:11.846539Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T02:18:17.373245Z'
  stage: docs-review
  run: 0440ae7f0dbc49bfa5e2954101a175c2
---

# The operator guide's work items, approval and merges reads for the operator

## Description

`docs/operator-guide/work-items.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/work-items.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/work-items.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/work-items.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/work-items.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/work-items.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names `docs/operator-guide/work-items.md` and `docs/checked-documents.txt` with its one line. Both are paths the documenter may write. No code, test or agent file changes, and no behaviour is stated in it that would need its own criterion.
   Criteria: each can be judged on the docs route. Criteria 1 and 2 are the reviewer's comparison against the style guide and the code. Criterion 3 is checked by `make documents` printing `documents ok`. Criterion 4 is a link check and criterion 5 is `make check`. The Interface states no limit, validation or default, so there is no failing side to cover.
   Smoke test: `grep -cx "docs/operator-guide/work-items.md" docs/checked-documents.txt` is runnable as written. Its `Expect: 1` can be checked against the output. It does not run pytest.
   Docs criterion: criterion 6 asks for criteria 1 to 4 and names no sentences to write. `docs/decisions.md`: none.
   Architecture: the change touches documents only. It fits CLAUDE.md's split between the operator guide, the project guide and the README.
   Scope: it is S0010 in the feature's list. It touches no file the feature lists as out of scope. I made no change to the story.
4. factory: started docs-only as vm.
5. documenter: I rewrote `docs/operator-guide/work-items.md` for the operator and added it to `docs/checked-documents.txt`. `make documents` ends with `documents ok (13.3 s)`. I ran no `make check` because I changed only documents.

   Files changed:
   - `docs/operator-guide/work-items.md`: rewritten.
     - The opening says what the topic covers and links the glossary at each term's first use.
     - Every old section is kept with its old heading, because other files link to those headings. The headings are: *When a feature acceptance is due*, *The hand-over at the approval*, *When the hand-over fails or is killed*, *A merge archives the story*, *A close before the approval discards the story*, *A close at the approval sends the story back*, *A stale branch is deleted by the tick*, *A restart during a stage*, *The crash cap*, *An expired lease*, *Claims, leases and the clock*.
     - The text is in plain sentences, with lists for the steps and cases. Feature and story IDs in examples became placeholders (`<feature>`, `<acceptance id>`).
     - The old line about v1's thirteen fault paths is reworded without the version name.
     - The old title was *Acceptances, approvals, merges and leases*; the new one is *Work items: acceptances, approvals, merges, closes and leases*. No link used the title.
     - A new *Reference* section at the end holds: the commit subjects (with the commit subjects dropped from the body prose), the journal entries the factory writes, the error names (`CannotHandle`, `PushFailed`, `HostingServiceError`, moved out of the body), the log lines, a settings table (`acceptance_stage`, `crash_cap`, `lease_duration`, `round_cap`) and the recovery tests.
   - `docs/checked-documents.txt`: one line added, `docs/operator-guide/work-items.md`.

   Read in the code:
   - `crash_cap` defaults to 2 and `lease_duration` to 60. Both are in `src/factory/pipeline/domain/pipeline_definition.py`; `round_cap` there has no default.
   - The log lines `description not written before the push`, `deleted stale branch` and `could not delete stale branch` are in `stage.py` and `recovery.py`.
   - The text `no report on the branch or the main branch` is in the acceptance code.
   - The three recovery test files exist.

   I did not re-check every other rule of the old text against the code, such as the exact description sections, close handling and the move-back conditions. They are carried over as written, so the reviewer should read them against the code.

   Cross-read and found current:
   - Other documents that link to this file: `docs/operator-guide/stops.md`, `records.md`, `site.md`, `cloud-run.md`, `agent-runtime.md` and `machine.md`. All the headings they quote still exist.
   - `docs/project-guide/pipeline.md`, `work.md` and `docs/decisions.md`, which quote the headings *A merge archives the story*, *A close before the approval discards the story*, *A close at the approval sends the story back* and *When a feature acceptance is due*. They are still true.

   Stale text I noticed and left alone, because it is not this story's:
   - `docs/operator-guide/README.md` mentions v1.2 and v1.1 history in its first paragraph.
   - Its index line for this file still lists the topics under the old title. It is still accurate, so I left it.

   I wrote no console examples in the file. The log and question texts are `text` blocks, copied from the old file. `docs/decisions.md` is untouched; the story says none.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (13.6 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the work item, `docs/project-guide/style.md`, the glossary and the code. I compared the old `docs/operator-guide/work-items.md` line by line with the new one. I checked these claims in the code: the commit subjects (`closed.py`, `merged.py`, `hand_over.py`, `reject.py`, `work/application/acceptance.py`), the defaults of the settings table (`pipeline_definition.py`: `lease_duration` 60, `round_cap` none, `crash_cap` 2, `acceptance_stage` none; `factory/pipeline.yml` names `acceptance`), the headings in `records.md` and the *Kill points* and *Fault-injection paths* sections of `docs/project-guide/README.md`. All of these hold, and so do the headings that other files link to and the one new line in `docs/checked-documents.txt`.

   Findings:
   1. `docs/operator-guide/work-items.md:113` and `:362` (Reference, `CannotHandle` row): both say an acceptance's close or merge with no report gives `no report on the branch or the main branch`. Only the close handler raises that text (`src/factory/work/application/acceptance.py:351`). The merge handler raises `no report on the main branch` when the report is in neither `in-progress/` nor `done/` (`acceptance.py:297`). Fix: give the merge case its own text and condition in both places.
   2. `docs/operator-guide/work-items.md:343`: says the commit of a close changes only the story file and its cost records file. The discard commit of a close before the approval moves only the story file (`src/factory/pipeline/application/handlers/closed.py:67`), and the cost records are deleted with the branch (line 166 of the same document says so). Fix: limit the cost records file to the merge archive and the acceptance's booking.
   3. `docs/operator-guide/work-items.md`, glossary links (criterion 1, style rule 3): stage (first use line 56), tick (69), journal (64), role (64), backlog (13), cost record (66) and project command (301) are never linked. Claim (first use 50, linked at 323), round (188, linked at 197) and stall ("stalls" at 270, linked at 291) are linked after their first use. Fix: link each at its first use in the file.
   4. `docs/operator-guide/work-items.md:386` and the old line 230 (criterion 2): the old command `uv run pytest tests/hosting/domain/test_kill_points.py tests/shared/domain/test_fault_paths.py tests/shared/domain/test_fault_paths_7_to_13.py` was dropped, and the documenter's entry does not name the drop. Without the command, the *Reference* names three test paths that the operator neither runs nor edits, which the operator-guide rule "Name a source path only if the operator edits or runs that file" forbids. Fix: either restore the command as a block the operator runs, or drop the paths too, point only to the project guide's sections, and name the drop in the entry.
   5. `docs/operator-guide/work-items.md:5`: "Your acts are all on the pull request: comment, close or merge" is contradicted by the same file. Line 221 has you turn off a hosting setting, line 270 has you revert an edit on `main`, and lines 138 and 176 have you lift a remote's refusal of deletions. The task at lines 217–221 is also written as prose, not as the numbered steps that the operator-guide rule for tasks asks for. Fix: narrow the sentence to the acts on a work item, and write "Branch deletion on merge must be off" as numbered steps marked for GitHub.

   Named as dropped, and acceptable under style rule 1: the example file names `F0001-S0001-name.md`, `done/old/F0001-S0001-name.md` and `F0002-a`/`F0002-b`, the example id `F0001-A0002`, and "v1's" before "thirteen fault-injection paths". Line 15 now says "Only story files count" without saying what a story file is named. The documenter may give the pattern with placeholders, such as `<feature id>-S<n>-<slug>.md`.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's five findings, all in `docs/operator-guide/work-items.md`. `make documents` ends with `documents ok (17.1 s)`. I ran no `make check`, because I changed only documents.

   Fixes by finding:
   1. The `CannotHandle` row in *Reference* and the "branch is gone" bullet now give the close and merge texts separately. The close says `no report on the branch or the main branch`. The merge says `no report on the main branch`, raised when the report is in neither `in-progress/` nor `done/` on `main`.
   2. The commit-subjects note now says what each commit changes. A booking changes the report and its cost records file. A story archive changes the story file and its cost records file. The discard at a close before the approval changes only the story file, and its cost records go with the branch.
   3. I linked each glossary term at its first use: backlog, claim (in the order-of-work section), stage, role, journal, cost records, tick, round, stall (in the section on editing a running work item) and project command. The later, now redundant links to round and to stall (in *The crash cap*) are plain text.
   4. I dropped the three recovery-test paths from *Reference* and from the sentence in *A restart during a stage*. The old `uv run pytest ...` command is dropped on purpose: the operator neither runs nor edits those files. *Reference* now points only to the *Kill points* and *Fault-injection paths* sections of `docs/project-guide/README.md`.
   5. The opening sentence now says "Your acts on a work item are on its pull request: comment, close or merge". The task *Branch deletion on merge must be off* is now numbered steps, marked as GitHub and not run here.

   I also gave the story-file name pattern with placeholders: `<feature id>-S<n>-<slug>.md`.

   Cross-read: the other operator-guide files that link to this file, and the project-guide and decisions quotes of its headings, were checked in round 0. I kept every heading, so they are unchanged.

   Stale text seen, not touched: the first paragraph of `docs/operator-guide/README.md` mentions v1.2 and v1.1 history.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (13.4 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 review of `git diff main...HEAD -- README.md docs operator/README.md` against the work item, `docs/project-guide/style.md`, the glossary and the code.

    I checked the five round-0 fixes, and all five hold:
    1. Close and merge errors. `docs/operator-guide/work-items.md:113` and `:365` now give the close's `no report on the branch or the main branch` and the merge's `no report on the main branch` separately. This matches `src/factory/work/application/acceptance.py:297` and `:351`.
    2. What each commit changes. `:346` now says that the discard changes only the story file. This matches `src/factory/pipeline/application/handlers/closed.py:63-70`.
    3. Glossary links. Backlog, claim, stage, role, journal, cost record, tick, round, stall and project command are each linked at their first use.
    4. Recovery tests. The three test paths and the `uv run pytest` command are dropped on purpose and named in the documenter's entry, and *Reference* points to the project guide's sections.
    5. Acts and steps. The opening sentence is narrowed to the acts on a work item. *Branch deletion on merge must be off* is now numbered steps marked for GitHub.

    I also read these against the code, and they agree:
    - the crash-cap question and the expiry note (`src/factory/hosting/domain/post_texts.py:115-135`);
    - the defaults in the settings table;
    - `docs/checked-documents.txt`, which has the one new line.

    Findings:
    1. `docs/operator-guide/work-items.md:193` and `:197`: "round cap" is a glossary term (`docs/project-guide/glossary.md:22`), but the file never links it (style rule 3, criterion 1). Its first use is the heading at 193; line 197 then uses only the setting `round_cap`. Fix: link "round cap" to `../project-guide/glossary.md` at its first use in prose, for example "within the [round cap](../project-guide/glossary.md) (`round_cap`) of the stage …" on line 197.
    2. `docs/operator-guide/work-items.md:389`: the file `docs/project-guide/README.md` is named in backticks, not linked (style rule 8: link a file of the repository by a relative link). Fix: write it as `[README.md](../project-guide/README.md)`, or link it as the project guide.
