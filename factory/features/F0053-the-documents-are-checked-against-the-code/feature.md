# The documents are checked against the code

## Goal

The documents the stages wrote are hard to read, and some of what they say is no longer true: the operator guide said `setup.sh` "makes the VM" when it prepares a fresh machine, and the acceptances of F0050 and F0051 found stale references and contradictions. Today only the tables of stops, kill points and fault paths are checked against the code. This feature makes most of what a document claims checkable, inside `make documents`, which the docs stages already run (the human, 2026-11-05):

- every code name and repository path a document writes in backticks exists;
- the settings, their defaults and their refusal messages in the operator guide agree with the settings code;
- a marked example (a command and its output) is run by the check, like a notebook that the test runner executes;
- the agents write and review documents by these rules.

Prose about behaviour stays the reviewer's to judge against the code. Today's documents will fail many of the new checks, so the checks report on every file but block only the files on a list of checked files; the rewrite (the next feature) adds each file to the list as it rewrites it. Done when every story below is merged and `make check` is green.

## Scope

- The name check: every backticked dotted name under `factory.` and every backticked repository path in the documents resolves (S0001).
- The settings check: the operator guide's settings tables agree with the settings code (S0002).
- Runnable examples: a marked block's commands run in a temporary checkout, and their output is compared (S0003).
- The checked-files list, and a report of every file's findings (S0004).
- The agents' rules: the documenter reads the code it describes and writes runnable examples; the reviewer judges facts against the code and counts an unchecked claim as a finding (S0005).

## Out of scope

- Rewriting the documents: the next feature.
- Checking prose about behaviour by a tool.
- Examples that need the VM, GitHub or a model: they are marked as such and not run.
- `docs/decisions.md` and `docs/runs/`: history, never checked for current truth.

## Stories

- S0001: Every name a document writes in backticks exists
- S0002: The operator guide's settings agree with the settings code
- S0003: A document's marked examples are run by the check
- S0004: The checks block the listed files and report on the others
- S0005: The agents write and review documents against the code

## The human's changes

- **At S0005's merge:** `factory/story-form.md`, the docs criterion: it names what the reader must know afterwards, not the sentences to write.

## Decisions taken for the human

1. **Checks live in `make documents`.** The docs stages already run it, and `make check` stays fast.
2. **Report everywhere, block where rewritten.** A list of checked files (`docs/checked-documents.txt`, a document so that a docs-route story can extend it) decides which findings fail the check; the others are printed as a report. Rejected: blocking at once, which would stop every docs stage until all files are rewritten.
3. **An example says where it runs.** A marked block runs in a temporary copy of the checkout, in a stage container; a block marked for the VM, GitHub or a model is skipped by the check and named in the report.
4. **History is exempt.** `docs/decisions.md` and `docs/runs/` keep old names and paths on purpose.
