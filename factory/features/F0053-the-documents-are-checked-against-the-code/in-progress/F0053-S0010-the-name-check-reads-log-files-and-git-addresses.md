---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 594
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T12:13:03.775964Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T12:13:03.783092Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T12:13:22.192908Z'
  stage: intake
  run: fc5f74f32ac742b9830380b8b4643f75
---

# The name check reads log files and git addresses
## Description

The name check's report on today's documents still holds texts that are no repository name, and the rewrite cannot put a page on the checked list while they remain. S0004 taught the check that `factory.env` is a file name. It did not cover the other file names the operator guide writes, `factory.log` (`docs/operator-guide/machine.md`) and the state's `.jsonl` records. A scp-style git address, `git@github.com:owner/project.git` (`docs/operator-guide/install.md`, `docs/operator-guide/cloud-run.md`), is read as a repository path. The feature acceptance listed `docs/operator-guide/install.md` in a copy, and the address blocked it. This story widens the file-name rule by two extensions and reads a text with a `:` before its first `/` as no path. Every other rule of S0001 and S0004 stays. Placeholders (`<state>/records/disk.jsonl`) stay the writer's way to name a path outside the repository.

## Interface

- `factory.shared.domain.documents`: `_FILE_NAME_EXTENSIONS` gains `.log` and `.jsonl`, so that `factory.log` and `factory.records.jsonl` are file names and no module.
- `named_references`: a backticked text whose first `:` comes before its first `/` (`git@github.com:owner/project.git`, `host:path/x.md`) is no path reference. A pytest node id (`tests/a/test_b.py::test_c`) keeps its first `/` before `::`, and is checked as S0004 says.
- Tests: rows in `tests/shared/domain/test_document_references.py`.

## Acceptance criteria

1. `factory.log` and `factory.x.jsonl` in backticks give no reference, and `factory.shared.domain.nothing_here` still gives a module reference (rows of the criterion 1 test of the name check).
2. `git@github.com:owner/project.git` and `git@host:owner/name.git` give no reference. `tests/x.py::test_y` still gives the path reference `tests/x.py`, and `docs/a:b.md` (a `:` after the first `/`) is still a path (rows of one test).
3. On today's documents, `make documents` prints no finding for `factory.log` (`docs/operator-guide/machine.md`) and none for the two git addresses (`docs/operator-guide/install.md`, `docs/operator-guide/cloud-run.md`).
4. `make check` stays green.
5. docs: `docs/project-guide/shared.md`, *The name check*: the reader learns which file names and addresses the check leaves out. `docs/project-guide/style.md`, rule 8: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | grep -c "git@\|factory.log does not exist"
```
Expect: `0`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `factory.shared.domain.documents` with `_FILE_NAME_EXTENSIONS` (exists, line 104) and `named_references`, plus the test file; the colon rule is stated exactly (first `:` before first `/`), so it is concrete.
   - Criteria: 1 covers `.log` and `.jsonl` with the module case still passing; 2 covers both sides of the colon rule (git addresses give none, `tests/x.py::test_y` and `docs/a:b.md` stay paths); 3 is checkable on today's documents; each is testable by one test function.
   - Smoke test: `factory.entry.check_documents` exists and the command is runnable. The `Expect: 0` line is checkable. Note that the grep pattern is loose, but it is the human's wording.
   - Docs criterion: names what the reader must know (which file names and addresses the check leaves out) in `docs/project-guide/shared.md`, and dictates no sentences.
   - Architecture: the change stays in the `shared` domain layer, pure rules with no I/O, so it fits.
   - Scope: it is inside F0053's name check (S0001/S0004 follow-up) and does not touch rewriting the documents or anything under Out of scope. Route is `tests`, since the Interface changes source code.
