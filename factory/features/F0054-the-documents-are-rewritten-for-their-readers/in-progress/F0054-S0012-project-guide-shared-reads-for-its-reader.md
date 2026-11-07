---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 620
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T03:02:16.514770Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T02:57:18.942573Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T02:57:18.950448Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T02:57:33.384305Z'
  stage: intake
  run: 64a688050a464c798e3238f9457573f8
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T02:57:38.933244Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T03:02:11.236237Z'
  stage: docs-only
  run: 7d1f87ec827442e2abf3c7e8d5d413ac
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T03:02:16.514770Z'
  stage: docs-review
---

# The project guide's page on the shared area reads for the developer

## Description

`docs/project-guide/shared.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/shared.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/shared.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/shared.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/shared.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/shared.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/shared.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete files only (`docs/project-guide/shared.md`, `docs/checked-documents.txt` with one exact line); no code, test or agent file changes, so every path is one the documenter may write.
   - Criteria: 1 to 6 are checkable by reading or running (style judged by the reviewer, old-versus-new comparison, `make documents` printing `documents ok`, no broken link, `make check` green). The link rule and the checked-list line each have a criterion (4, 3). Criterion 5 covers links to changed headings. The failing side is `make documents` finding a broken link or a name that does not resolve.
   - Smoke test: `grep -cx "docs/project-guide/shared.md" docs/checked-documents.txt` is runnable, and `Expect: 1` is checkable. It runs no pytest.
   - Docs criterion: criterion 7 points at criteria 1 to 5 (reader's knowledge: the style, the old file's facts kept, working examples, links). It quotes no sentences to write.
   - Architecture: the change touches only documents, matching CLAUDE.md's Docs section. It keeps `docs/decisions.md` unchanged and writes nothing to `factory/`, `planning/` or `docs/runs/`.
   - Scope: this is S0012 of F0054's list (the project guide's page on the shared area), within Scope and outside Out of scope.
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `docs/project-guide/shared.md`: rewritten for its reader in the form of `style.md`. Each section opens with a short idea and the signatures in an indented block, then one rule per bullet, then See also. Every module and test file it names is linked once by a relative link, and no link sits in a code block. A *Reference* section at the end holds the exact detail: the `ProcessResult` fields, the 0.05 s read step and the `WNOWAIT` check, the private `_start` and `_kill_session`, the suppression markers, the test files and helpers, and the types of the check. I kept the headings "Starting a process", "The duplicates report", "The document check" (with the name check, settings check and "How the check is tested") and the section "How the check is tested", which `style.md` links by name. I also kept the two index sections the project guide's index names.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/shared.md`.

   Corrections from the code:
   - The old text said eight modules import `process.py`. The guard (`tests/guards/test_wrapper_search.py`) and the source list nine. The ninth is `factory.shared.adapters.document_examples`, which the old text never named. The new text says nine and names it with the `run_process` users.
   - I cut the story and feature IDs and the version history ("from F0020-S0004", "since v1.2", "Today's operator guide…" as history). I kept the current-state fact that the operator guide has no `Default` column and no refusal table.
   - The old text said "Decision: *The process group is killed*". That line is not an entry heading. It sits under *A command stopped at its time limit loses every process of its session*, and the new See also names that title.
   - Two old "Tests:" paragraphs, the test-timing paragraph and the double heading sentences are merged into the bullets and the Reference.

   Run and verified:
   - `make documents` ended with `documents ok (13.7 s)`, and no finding mentions `shared.md`.
   - The smoke test `grep -cx "docs/project-guide/shared.md" docs/checked-documents.txt` prints `1`.
   - The page's code blocks are indented, not `console` blocks. The only runnable-looking commands in them are the call forms and one `run_process(...)` line, which cannot run on their own. So the page has no example to run and none marked for the VM, GitHub or a model.
   - Nothing else links to a changed heading: the only link into `shared.md` is `style.md` → *How the check is tested*, which is kept.
   - I did not run `make check`, because I changed only documents.

   Cross-read and found current against this diff: `docs/project-guide/README.md` (its line on `shared.md` still matches the page's sections), `docs/project-guide/style.md`.

   Stale text I saw and did not touch:
   - In `docs/project-guide/README.md`, the line on `shared.md` says it covers only "the one module that starts processes" and lists the other `shared` content as described elsewhere. That is still true, but the index is not part of this story.
   - The test docstring in `tests/guards/test_wrapper_search.py` says "the three wrappers", while the set lists nine modules. That is a test comment and the coder's or tester's to fix, not mine.
   - `Style rule 2` (at most one parenthesis per sentence) is not met everywhere in the Reference and in a few bullets of the name check. I kept the exact wording of the old text where shortening it risked dropping a rule. The reviewer may name any sentence to split.
   - `docs/decisions.md` has no "Rejected" line to write: the docs criterion says none.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (13.7 s)
6. factory: started docs-review as vm.
