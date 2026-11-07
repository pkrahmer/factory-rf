---
stage: docs-review
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 624
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T04:57:21.471305Z'
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
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-07T04:49:16.675721Z'
  stage: docs-only
  run: 0773bed63c7043aab99141c304123f6c
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-07T04:49:21.672538Z'
  stage: docs-review
- number: 10
  speaker: reviewer
  kind: result
  at: '2026-11-07T04:51:57.079467Z'
  stage: docs-review
  run: 0cca5f9d25bc451985a97df360d69da0
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-07T04:52:02.538601Z'
  stage: docs-only
- number: 12
  speaker: documenter
  kind: result
  at: '2026-11-07T04:57:16.479412Z'
  stage: docs-only
  run: a56bc5d397c24bd6a36e4a947a64a232
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-07T04:57:21.471305Z'
  stage: docs-review
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
8. documenter: Fixed the red `make secrets` that stalled the first run. detect-secrets flagged `docs/project-guide/watching.md:337` as a Secret Keyword, because the `login` row of the cost-record table named the literal values `api_key`, `subscription` and `none`.

   Files changed:
   - `docs/project-guide/watching.md`: in that row I wrote the three login kinds in words ("an API key, a subscription or none"). The meaning is unchanged. I added no `pragma: allowlist secret`. detect-secrets now passes on the file, and `make documents` ends with `documents ok (16.7 s)`.

   The rest of the first entry stands:
   - `docs/checked-documents.txt` has the `watching.md` line.
   - `docs/project-guide/README.md` has the new `watching.md` entry.
   - I cross-read `docs/operator-guide/records.md` and found it current.
   - I changed only documents, so I did not run `make check`.

   Stale text I saw and did not touch, because it is unrelated to this story:
   - `docs/project-guide/README.md` has `support/...` paths that do not exist, from line 121.
   - `docs/project-guide/machine.md` has `src/new.py`, `.venv/...` and `factory/stage.Containerfile`.
   - The index `README.md` still has version-history notes ("Replaced in v1.2", "Replaced from v1").

   I wrote no `Rejected` lines, and `docs/decisions.md` is unchanged.

   `check`: check: green
   `secrets`: secrets: green (0.5 s)
   `documents`: documents ok (16.3 s)
9. factory: started docs-review as vm.
10. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the work item, `docs/project-guide/style.md`, the old page on `main` and the code on the branch. Most claims hold. I checked the move rule, the tiers, `run_watch` and its exit codes 0/1/2, `factory-bill`'s outputs and exit codes, the writer's key order and left-out keys (`machine` null only when asked), `CostRun.start_totals`, `complete`'s signature, the started-record validator, the transcript store and keeper, the machine readings, the factory log, the health file, `JsonLinesRecordLog`, the interfaces in `watching/application/machine.py` and every linked heading. Findings:

    1. `docs/project-guide/watching.md` throughout, criterion 1: only "work item" links to the glossary, and not at its first use (line 17; the link is at line 29). These words are used and never linked: tick (l.3), claim and lease (l.21), stage and pipeline definition (l.23), feature (l.36), acceptance and story (l.58), approval (l.49), journal (l.76), cost record (l.124), instance and role (l.164), dataset (l.167), stall (l.168), take and write paths (l.169), attempts cap (l.297), stop (l.97). Fix: link each at its first use, as `work.md` and `agents.md` do.
    2. `watching.md:21`, criterion 2: a rule of the old page is dropped. With `observer=True`, a claim at or past its lease is `own` again. The code is `observed_claim_status`, called from `ClaimService.observed_status` in `src/factory/pipeline/application/claims.py`. The tick's `ClaimService.status` is not named either (`watcher.py:49`). Fix: add both.
    3. `watching.md:13-22`, criterion 2: the source of `due` is dropped. It is `AcceptanceReader.due_features()` (`src/factory/watching/application/watcher.py:45`). Fix: name it in the `Watcher.evaluate` bullet.
    4. `watching.md:196,207-208`, criterion 2: the old rules that `total(stage_bills)` sums the stage bills field by field and that `one_decimal` gives one decimal, rounded half up, are gone. Fix: add a bullet for each.
    5. `watching.md:165` and the `model_seconds` row at l.325, criterion 2: the page drops what `complete` sets apart from turns, tokens and cost. It sets `duration_seconds` from the result's duration, `model_seconds` from `model_duration` in seconds (`None` when unknown) and `end_reason` (`src/factory/watching/application/costs.py`, `_completed`). Fix: state it in that bullet or in the table row.
    6. `watching.md:331`, criterion 2: the module of `Name` was dropped. Fix: link `src/factory/shared/domain/identifiers.py` there.
    7. `watching.md:337`: "an API key, a subscription or none" reads as if `none` were `None`, but the code has the literal value `"none"` (`Login = Literal["api_key", "subscription", "none"]`, `src/factory/agents/domain/agent_runs.py:44`). The literal names were dropped on purpose to keep detect-secrets green. Fix: link `agent_runs.py` and say that `Login` is one of three literal values, one of them the string `none`, apart from `None` when there is no login file.
    8. `watching.md:339`: "none of the measures from `duration_seconds` on" also covers `image` and `instance`, which follow it in field order, but a started record carries both (`cost_records.py`, `_measures_only_when_completed`). Fix: "from `duration_seconds` to `cost_usd`".
    9. `watching.md:237`: "one block for each work item in flight" is not quite true. `_all_in_flight` (`src/factory/entry/bill.py:39-46`) skips a work item whose `for_work_item` returns `None`. Fix: "for each work item in flight that has a bill".
    10. `watching.md`, criterion 4 (Interface: each file linked once): `costs.py` is linked at l.155 and again at l.192, `watching/application/machine.py` at l.182 and again at l.264, and `records.md` at l.90, l.186 and l.207. The modules named in prose at l.272-274 (`factory.work.domain.journal`, `factory.hosting.domain.hand_over`, `factory.pipeline.application.handlers.questions`, `factory.pipeline.application.recovery`, `factory.work.domain.acceptance`, `factory.shared.domain.sections`, `factory.work.domain.story_form`, `factory.work.adapters.work_item_markdown`, `factory.hosting.application.opening`) are not linked at all. Fix: keep one link per file, and link each of those modules once by a relative path.
    11. `watching.md:174-184` and `:257-264`, style page (project guide): these two sections list their classes and functions in bullets and have no signature block. Bullets such as l.178 and l.182 are lists of names, not rules a test could check. Fix: put the names and signatures in a code block after the opening sentences, then the rules (e.g. `TranscriptKeeper(store, log).keep(work_item, run, transcript) -> TranscriptRef | None`, `session_transcripts(store, log, runtime, workspace) -> SessionTranscripts`, `CgroupMachineReadings(slice_folder, meminfo)`, `TimestampedFactoryLog(path, clock)`, `JsonHealthStatusFile(path)`, `JsonLinesRecordLog(path, model)`).
    12. `watching.md:82`, `:210` and `:272`, style rule 2: l.82 has a sentence of about 40 words. l.210 has two parentheses in one sentence, and l.272 has three. Fix: split them.
    13. `docs/project-guide/README.md:33`: the "Sections:" list leaves out subsections the page has, *The event*, *The four tiers*, *The watcher's command line*, *When a record is created, completed and committed*, *Transcripts and the machine's readings* and *The bill command*, while it names *The move rule* and *The board*. It also names `factory.watching.application.transcripts` but not the adapters the page describes (`transcript_files`, `machine_files`, `factory_log`, `health_file`, `record_log_jsonl`). Fix: list the top-level sections, then "Subsections other files refer to:" as the other entries do, and name those adapters.

    Dropped on purpose, and accepted as unbacked by the code: the "(R24)" reference, the sentence about the dispatcher's cap on a `run` event, and the explanation "an unknown stage never reaches the definition's accessors". The `Login` literals are covered under 7.

    Smoke test: `grep -cx "docs/project-guide/watching.md" docs/checked-documents.txt` holds by reading the file: the line is there once. I did not run it.
11. factory: started docs-only as vm.
12. documenter: Round 1: fixed the reviewer's 13 findings. `make documents` ends with `documents ok (15.9 s)`. I changed only documents, so I did not run `make check`.

    Files changed:
    - `docs/project-guide/watching.md`:
      - 1: Glossary links at first use for tick, work items, acceptances, claim, lease, stage, pipeline definition, feature, approval, stories, journal, stop, instance, cost record, role, dataset, stall, take, write path, attempts cap and backlog. The earlier link on "work item" in *The event* is now plain.
      - 2: Named `ClaimService.status` and `observed_claim_status` (`lease.py`, `claims.py` linked). An own claim at or past its lease is `own` again.
      - 3: `due` comes from `AcceptanceReader.due_features()`, with `acceptance_reading.py` linked there.
      - 4: Added a bullet each for `total` (sums the stage bills field by field) and `one_decimal` (one decimal, rounded half up).
      - 5: `complete` also sets `duration_seconds`, `model_seconds` (from `model_duration`, `None` when unknown) and `end_reason`.
      - 6: `Name` links to `identifiers.py`.
      - 7: Added a bullet on `Login`, linking `agent_runs.py`. It is one of three literal values, one of them the string `none`, apart from the `None` of a run with no login file. I did not write the literals, because the secrets scan flagged the first draft.
      - 8: "from `duration_seconds` to `cost_usd`", so `image` and `instance` are not covered.
      - 9: "that has a bill" added for the no-argument `factory-bill`.
      - 10: Each file is now linked once. `costs.py`, the application-layer `machine.py` and `records.md` were repeated and are plain after the first link. The nine modules of the journal guard are linked once, as relative paths.
      - 11: *Transcripts and the machine's readings* and *The factory log and the health file* now have a signature block and rule bullets. I took the signatures from the code. `SessionTranscripts.read(result)` and `SessionTranscripts.keep(...)` are both shown, and `machine_differences` returns `MachineTotals`.
      - 12: Split the long sentences in the move rule and the human's waits. `for_work_item` and the guard bullets are split too.
    - `docs/project-guide/README.md` (13): the `watching.md` entry lists the top-level sections and then "Subsections other files refer to". It names the adapters the page describes.

    Cross-read and found current: `docs/operator-guide/records.md`, `work.md` and `pipeline.md` (their links to *Cost records* and the other headings are unchanged).

    Stale text I saw and did not touch, because it is unrelated to this story:
    - `docs/project-guide/README.md` has `support/...` paths that do not exist (from line 121) and `project/factory/...` at line 283.
    - `docs/project-guide/machine.md` has `src/new.py`, `.venv/...` and `factory/stage.Containerfile`.
    - The index still has "Replaced in v1.2" and "Replaced from v1" notes in the agents entry.
    - None of these pages is on the checked list yet.

    I wrote no `Rejected` lines. `docs/decisions.md` is unchanged.

    `check`: check: green
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok (16.1 s)
13. factory: started docs-review as vm.
