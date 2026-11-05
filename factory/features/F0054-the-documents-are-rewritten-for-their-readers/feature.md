# The documents are rewritten for their readers

## Goal

The documents read hard and do not all hold the truth (the human, 2026-11-05). F0052 gives documents-only stories their own route, and F0053 makes names, settings and examples checkable and lets each rewritten file be checked from then on. This feature rewrites every file of the operator guide, the project guide and the README, one story per file, in the style the human chose on 2026-11-05 (`docs/project-guide/style.md`, from `planning/doc-style-drafts.md`; samples in `planning/doc-style-samples.md`). Each story takes its facts from the code, keeps every fact of the old file or moves it to a *Reference* section, makes its examples runnable, and adds its file to `docs/checked-documents.txt`. When the last story is merged, every document is checked. Done when every story below is merged and `make check` is green.

## Before it starts

F0052 (the docs route) and F0053 (the checks) are merged, and `docs/project-guide/style.md` and `glossary.md` exist (F0052-S0003).

## Scope

- Each of the 22 files, rewritten and on the checked list (one story each).

## Out of scope

- `docs/decisions.md` (history), `docs/runs/` and `docs/operator-playbook.md` (the human's).
- Any change of behaviour: a wrong claim is corrected in the document; a fault in the code it reveals is a question, and becomes its own story.

## Stories

The operator guide first, since a person reads it; then the project guide; the README last, since it points into both.

- S0001: The operator guide's installing and running an instance reads for the operator
- S0002: The operator guide's the site file and an operator's machine reads for the operator
- S0003: The operator guide's the machine reads for the operator
- S0004: The operator guide's on cloud run reads for the operator
- S0005: The operator guide's the agent runtime reads for the operator
- S0006: The operator guide's the preflight, the health check and the log reads for the operator
- S0007: The operator guide's the stops reads for the operator
- S0008: The operator guide's the pipeline definition reads for the operator
- S0009: The operator guide's the records, the bill and the watch reads for the operator
- S0010: The operator guide's work items, approval and merges reads for the operator
- S0011: The operator guide's index reads for the operator
- S0012: The project guide's page on the shared area reads for the developer
- S0013: The project guide's page on the hosting area reads for the developer
- S0014: The project guide's page on the work area reads for the developer
- S0015: The project guide's page on the agents area reads for the developer
- S0016: The project guide's page on the watching area reads for the developer
- S0017: The project guide's page on the machine area reads for the developer
- S0018: The project guide's page on the pipeline area reads for the developer
- S0019: The project guide's page on the operator's scripts reads for the developer
- S0020: The project guide's index reads for the developer
- S0021: The README reads for a newcomer
- S0022: The operator folder's README reads for its reader

## The human's changes

None planned.

## Decisions taken for the human

1. **One story per file.** A review can read one file against the code whole; a fault stops one file only.
2. **The reviewer checks the facts.** On the docs route the reviewer reads the old and the new file against the code; a fact dropped without a reason is a finding.
3. **A wrong claim is fixed in the document.** If the code, not the document, is wrong, the story asks the human; the fix to the code is another story.
