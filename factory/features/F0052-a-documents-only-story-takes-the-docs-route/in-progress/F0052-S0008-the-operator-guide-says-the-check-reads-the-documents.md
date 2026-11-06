---
stage: docs-only
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 582
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T01:29:00.528242Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T01:29:00.534908Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T01:29:16.805324Z'
  stage: intake
  run: ab9062fcb97d4c248f6f1e8be4ba1a2a
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T01:29:21.777039Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T01:32:30.300201Z'
  stage: docs-only
  run: 66dbc02f03014a8188a8924851a6b6a2
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T01:32:35.735638Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-06T01:33:28.010574Z'
  stage: docs-review
  run: 5f0f9f5f840d4223bb7ab5fe6a4c053a
---

# The operator guide says that the check reads the documents
## Description

`factory/pipeline.yml` leaves `README.md` and `docs/*.md` out of the tree that keys a passed `make check` (`not_read`). But `make test` reads those files: the guide guards (`tests/guards/test_project_guide_files.py`, `test_operator_guide_files.py`, `test_root_operator_folders_removed.py`, `test_agent_folder_names.py`), `tests/entry/test_check_documents_operator_guide.py` and `tests/operator_scripts/test_operator_site_check.py` all read the real documents. So a documents-only change that turns `make check` red keeps the same key, and the factory reuses an earlier pass. On the docs route this is the normal case. In F0052-S0007 the first docs-only run broke the guide guard, and only a changed stage image made the check run and catch it. The fix of the key is the human's: `check`'s `not_read` loses `README.md` and `docs/*.md` and keeps only `docs/runs/*` of `docs/`, which no test reads. The human names that change in `feature.md` under *The human's changes* when refining this story, and makes it before the story starts. This story then brings the operator guide in line with it. The guide quotes the old `not_read` as the project's own and says that it leaves out only files that `make check` does not read. The rest of `pipeline.md`, including the rewrite of *The docs route*, stays for the next feature.

## Interface

- `docs/operator-guide/pipeline.md`, the paragraph that starts "kumpel-factory's own definition" and the `yaml` block under it: the block quotes `check` as `factory/pipeline.yml` holds it after the human's change. The paragraph says that `README.md` and `docs/` stay in the key because tests under `make test` read the documents, and that only `docs/runs/*` of `docs/` is left out. The wording is the documenter's, by `docs/project-guide/style.md`.
- `docs/operator-guide/pipeline.md`, *The docs route*: one sentence saying that `make check` runs after `docs-only`, or is reused only when no document that a test reads changed. Nothing else in that section changes.
- No code and no test changes.

## Acceptance criteria

1. The `yaml` block under "kumpel-factory's own definition" in `docs/operator-guide/pipeline.md` holds the same `check:` line as `factory/pipeline.yml`, character for character. A block that still lists `"README.md"` or `"docs/*.md"` fails this criterion.
2. The paragraph above the block names the tests that read the documents (the guide guards under `tests/guards/` at least) as the reason why `README.md` and `docs/` are not left out. It no longer says that the definition leaves out every Markdown file.
3. *The docs route* in `docs/operator-guide/pipeline.md` says in one sentence that a documents-only change runs `make check` again. The rest of the section is unchanged.
4. `make documents` prints `documents ok`.
5. `make check` stays green.
6. docs: `docs/operator-guide/pipeline.md`, as above. `docs/decisions.md`: a line under the known results' entry saying that a test reads the documents, so the check's `not_read` keeps them in, with a `Rejected:` line for moving the guide guards into `make documents`. `docs/project-guide/`: none, because it does not quote the definition.

## Smoke test

```bash
grep -c '"docs/\*.md"' docs/operator-guide/pipeline.md
```
Expect: `0`

```bash
diff <(grep -o 'check: {time_limit: 8, not_read: \[.*\]}' factory/pipeline.yml) <(grep -o 'check: {time_limit: 8, not_read: \[.*\]}' docs/operator-guide/pipeline.md) && echo same
```
Expect: `same`

```bash
make documents 2>&1 | tail -1
```
Expect: `documents ok`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete places, all documenter paths (`docs/operator-guide/pipeline.md`, its "kumpel-factory's own definition" paragraph and yaml block, and *The docs route*; `docs/decisions.md`). No code or test changes, so the route is docs-only.
   - Criteria: criteria 1 to 3 are each checkable by reading the document. Criterion 1 compares the `check:` line character for character with `factory/pipeline.yml`, and a block that still lists `"README.md"` or `"docs/*.md"` fails it, so both sides are covered. Criterion 2 has the positive side (names the tests) and the negative side (no longer says every Markdown file is left out). Criterion 3 is one sentence plus "rest unchanged". Criteria 4 and 5 are the gates.
   - Smoke test: the commands are runnable. The grep expects `0` and the diff expects `same` against the real `check:` line, which `factory/pipeline.yml:10` already holds after the human's change; the guide still has the old block at line 62. `make documents` expects `documents ok`. No pytest command is involved.
   - Architecture: documents only, inside the documenter's write paths. `docs/project-guide/` is rightly left alone.
   - Scope: it matches `feature.md` *The human's changes* ("Before S0008's start"). The rewrite of the rest of `pipeline.md` is expressly left for the next feature.
   - Note for the documenter: the live `check:` line is `{time_limit: 8, not_read: [...]}` and also lists `factory/archive/*`. The guide's block must copy the line exactly.
4. factory: started docs-only as vm.
5. documenter: Changed files:
   - `docs/operator-guide/pipeline.md`: the paragraph "kumpel-factory's own definition" now says that only Markdown and JSON Lines files no test reads are left out. It names the guide guards under `tests/guards/` and the other `make test` tests as the reason `README.md` and `docs/` stay in the key, and says only `docs/runs/*` of `docs/` is left out. The `yaml` block now holds the `check:` line copied from `factory/pipeline.yml`.
   - `docs/operator-guide/pipeline.md`, *The docs route*: one sentence added saying `make check` runs after `docs-only`, or is reused only when no document a test reads changed. The rest of the section is unchanged.
   - `docs/operator-guide/pipeline.md`, the generic `not_read` example above the paragraph: it listed `"docs/*.md"`, which the smoke test's grep (expects 0) counts, and it would have read as advice to leave the documents out. I changed it to `["notes/*.md", "docs/runs/*"]`. This goes slightly beyond the Interface, so the reviewer should check it.
   - `docs/decisions.md`: under *A known result is not checked again*, a Decision line that a test reads the documents so `not_read` keeps them in, and a `Rejected:` line for moving the guide guards into `make documents`. Both come from the criterion 6 text. The story gives no reason beyond that, so I wrote no "Reasons" line.

   Checks run:
   - The smoke test's grep returns 0.
   - The diff of the `check:` line returns `same`.
   - `make documents` prints `documents ok`.
   - I did not run `make check`, as only documents changed.

   Cross-read and found current: the other operator-guide files were not searched beyond a grep for `not_read` and `documents`. `docs/project-guide/` was not touched, as the criterion says it does not quote the definition.

   Stale text I noticed but did not touch: the "Two warnings" bullet in `pipeline.md` says the docs stage runs `secrets` with nothing left out. The rewrite of the docs route is left for the next feature, so I did not check whether that bullet is still accurate.

   `check`: check: green
   `secrets`: secrets: green (1.3 s)
   `documents`: documents ok
6. factory: started docs-review as vm.
7. reviewer: Docs review, round 0. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, then checked the text against `factory/pipeline.yml`, `git ls-files` of the folders `not_read` names, and `docs/project-guide/style.md`.

   What holds:
   - Criterion 1: the `yaml` block under "kumpel-factory's own definition" matches `factory/pipeline.yml:10` character for character, and `"docs/*.md"` no longer appears in `pipeline.md`.
   - Criterion 2: the paragraph names the guide guards under `tests/guards/` as the reason, and it no longer says that every Markdown file is left out.
   - Criterion 3: *The docs route* gains one true sentence. `docs-only` lists `check` among its checks, and every other sentence of the section is unchanged.
   - `docs/decisions.md`: the Decision line and the `Rejected:` line meet criterion 6.
   - The documenter also changed the generic example, beyond the Interface. That was needed, because the smoke test's grep for `"docs/*.md"` expects `0`. Finding 3 is about its new content.

   Findings:
   1. `docs/operator-guide/pipeline.md`, paragraph "kumpel-factory's own definition", first sentence. It says that the definition leaves out "only the Markdown and JSON Lines files that no test reads". That is false: `docs/runs/*` also leaves out a `.json` file and a `.log` file (`git ls-files docs/runs` lists 7 md, 3 jsonl, 1 json, 1 log). The sentence also runs to about 33 words, over style rule 2. Fix: say that the definition leaves out the Markdown and JSON Lines files no test reads, plus folders that hold no code and that no test reads (`docs/runs/`, `planning/`, `session-logs/`, `factory/archive/`). Split this into two sentences, keeping the `make lint` reason.
   2. `docs/operator-guide/pipeline.md`, same paragraph, the sentence "`README.md` and `docs/` stay in the key: the guide guards … can turn `make check` red." It runs to about 31 words, over style rule 2. Fix: split it after "stay in the key", for example "… stay in the key. The guide guards under `tests/guards/` and other tests of `make test` read the real documents, so a documents-only change can turn `make check` red."
   3. `docs/operator-guide/pipeline.md`, the generic `not_read` example, now `["notes/*.md", "docs/runs/*"]`. The whole-folder pattern `docs/runs/*` contradicts the advice two lines below it: "leave out file types it does not read, never a whole folder". Fix: give the example file-type patterns only, for example `["notes/*.md", "notes/*.jsonl"]`. Do not bring back `"docs/*.md"`, which the smoke test counts.

   Open, outside this story's scope:
   - The documenter flagged the "Two warnings" bullet about `secrets` as possibly stale. Its rewrite belongs to the next feature, so I did not judge it.
   - The general advice "never a whole folder" already sat beside the project's own whole-folder patterns (`planning/*`, `session-logs/*`) before this diff. That is not a finding here.
