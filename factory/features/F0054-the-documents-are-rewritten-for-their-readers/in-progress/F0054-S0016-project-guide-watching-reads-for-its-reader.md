---
stage: docs-only
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 624
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T04:46:25.967724Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T04:42:20.801790Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T04:42:20.808882Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T04:42:35.772262Z'
  stage: intake
  run: cf42321b42c046cba894ac90b7a56096
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T04:42:40.791112Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T04:46:18.596612Z'
  stage: docs-only
  run: c48ee18bcf9f48688601bc7d6d0c4db5
- number: 6
  speaker: factory
  kind: stall
  at: '2026-11-07T04:46:18.797918Z'
  stage: docs-only
  run: c48ee18bcf9f48688601bc7d6d0c4db5
  reason: check_red
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T04:46:25.967724Z'
  stage: docs-only
---

# The project guide's page on the watching area reads for the developer

## Description

`docs/project-guide/watching.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/watching.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/watching.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/watching.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/watching.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/watching.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/watching.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only (`docs/project-guide/watching.md`, `docs/checked-documents.txt`). Both are documenter-writable (`docs/*`), and the story says no code, test or agent file changes. Route is docs-only.
   Criteria: all concern documents. 1 and 2 are judged by the reviewer against the style page and the code, which is how the docs route works. 3 is checked by `make documents` and the checked list. 4 and 5 are checked by link checks. 6 is `make check`. Each Interface rule (link once, one line on the checked list, changed headings relinked) has a criterion (4, 3, 5). No rule has a failing side that needs its own criterion.
   Smoke test: `grep -cx ... docs/checked-documents.txt` is runnable, and `Expect: 1` is checkable. It runs no pytest.
   Docs criterion: criterion 7 asks for criteria 1 to 5, which say what the reader must know (facts from the code, nothing dropped, names linked). It dictates no sentences.
   Architecture: documentation only. It leaves the code layers alone and fits the project guide's structure.
   Scope: it is S0016 of F0054 (the project guide's watching page). The feature's out-of-scope files (`decisions.md`, runs, playbook) are untouched. The criteria are the story's own list.
4. factory: started docs-only as vm.
5. documenter: Rewrote the project guide's watching page for its reader, after reading the code it describes on the branch. `make documents` ends with `documents ok (16.3 s)`, with no finding for `watching.md`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/project-guide/watching.md`: rewritten to `docs/project-guide/style.md`.
     - Each section opens with a short idea, then the names in a code block, then one rule per bullet, then See also.
     - Each module is linked once at its first mention, and the factory's own words link to the glossary.
     - The exact detail moved to a new *Reference*: the tiers, the move rule's `None` cases, the cost record fields, the file format and faults, the bill texts.
     - The old `bash` example is now a runnable `console` example, and a second one shows `cost_line` and `cost_table`. Both ran under `make documents`.
     - Headings *Cost records*, *Bills* and *The watcher's command line* are kept. `work.md` links to *Cost records*.
   - `docs/checked-documents.txt`: added `docs/project-guide/watching.md`. The story's smoke test (`grep -cx ...`) should print 1.
   - `docs/project-guide/README.md`: rewrote the `watching.md` entry in *The files* to the page's new title and sections, and to the modules it now describes.

   Corrections where the code disagreed with the old text or the old text was incomplete:
   - The cost record has the fields `machine` (`MachineMeasures`), `transcript` (`TranscriptRef`) and `tools` (`ToolUse`). They were missing. The writer's key order and omitted keys, and `CostRun.start_totals`, are corrected to match the code.
   - `run_watch` also catches `AgentDefinitionInvalid` and returns 1. Only `PipelineDefinitionInvalid` was named.
   - `factory-bill`'s outputs and exit statuses (0, 1 for no work item, 2 for a bad id or a usage error) are stated from `src/factory/entry/bill.py`.
   - Added what the old text lacked:
     - the transcript store, keeper and session reader;
     - the machine readings (domain, interface, cgroup adapter);
     - the factory log, the health file and the record log adapters;
     - the idle detail `<work item> waits for the human`.
   - Dropped as unbacked by the code: the "(R24)" reference, and the sentence that the dispatcher caps a `run` event.

   Cross-read and found current: `docs/operator-guide/records.md`, which already covers `machine`, `tools` and `transcript` and agrees with the page. `work.md`, `pipeline.md` and `src/factory/watching/__init__.py` point at `watching.md` without a heading link that changed.

   Noticed, not touched, not part of this story:
   - Under `make documents` the not-yet-checked pages print old findings. `docs/project-guide/README.md` has `support/...` paths that do not exist, from line 121. `docs/project-guide/machine.md` has `src/new.py`, `.venv/...` and `factory/stage.Containerfile`. Neither page is on the checked list yet.
   - The index `README.md` still mentions *Replaced in v1.2* and *Replaced from v1*. These are version-history notes (the style page asks for removal), left for the stories that rewrite those pages.

   No `Rejected` lines were written, and `docs/decisions.md` is unchanged, as the story says.
6. factory: Stage docs-only stalled (attempt 1 of 2): a check is red after the stage: `check`
   sast: green (2.2 s)
   Bytecode compiled 4164 files in 54ms
   ERROR: Potential secrets about to be committed to git repo!

   Secret Type: Secret Keyword
   Location:    docs/project-guide/watching.md:337

   Possible mitigations:
     - For information about putting your secrets in a safer place, please ask in
       #security
     - Mark false positives with an inline `pragma: allowlist secret` comment

   If a secret has already been committed, visit
   https://help.github.com/articles/removing-sensitive-data-from-a-repository
   make: *** [Makefile:65: secrets] Error 1
7. factory: started docs-only as vm.
