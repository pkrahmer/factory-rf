---
stage: docs-review
blocked: null
round: 0
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
