---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-06T01:29:00.534908Z'
  lease_duration: 60
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
