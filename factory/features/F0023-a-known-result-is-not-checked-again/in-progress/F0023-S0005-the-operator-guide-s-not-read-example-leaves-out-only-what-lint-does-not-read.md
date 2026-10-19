---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 290
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T21:54:26.942465Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T21:53:37.376883Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T21:53:37.383297Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T21:54:06.126508Z'
  stage: intake
  run: c4366d1b426f4c47b3948a9ee9ae396d
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T21:54:26.942465Z'
  stage: tests
---

# The operator guide's not_read example leaves out only what lint does not read

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`docs/operator-guide.md`, *The pipeline definition*, explains `not_read` with two examples that disagree. S0001's documenter wrote the first one, `lint: {time_limit: 10, not_read: ["factory/*", "docs/*"]}`, which leaves whole folders out of `lint`. S0002's documenter wrote, a few paragraphs further on, that factory-rf leaves out only Markdown and JSON Lines files because `make lint` reads every Python file of the tree, wherever it lies. An operator who copies the first example keeps a reused `lint` from seeing a Python file under `docs/`, which is the silenced check that the feature's decision 2 rules out. The same section also says, in the future tense, that factory-rf's definition "takes this after the story that built the key" and that its docs stage "will run `secrets`". That stopped being true when the human's change 1 of `feature.md` reached `main`. It is documentation only: no code, test, template or agent file changes.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *The pipeline definition*, makes these changes and no other passage changes:
   - The first `not_read` example leaves out files by their type, not whole folders. It becomes `check: {time_limit: 10, not_read: ["README.md", "docs/*.md"]}`.
   - After "List only what the command does not read at all", one sentence is added: a linter, formatter or type checker that walks the whole tree reads every source file in every folder, so leave out file types it does not read, never a whole folder.
   - The sentence that says factory-rf's own definition takes the example "after the story that built the key" becomes the present tense and names `factory/pipeline.yml`.
   - The `check` line of factory-rf's block below that sentence is the line `factory/pipeline.yml` holds on `main` when the story starts (its `time_limit` is `15` before F0024's change 2 and `8` after it).
   - The warning that factory-rf's docs stage "will run `secrets`" becomes "runs `secrets` as a check of its own, with nothing left out".
   - `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'not_read: \["factory/\*", "docs/\*"\]' docs/operator-guide.md
```
Expect: `0`

```bash
grep -c 'will run `secrets`' docs/operator-guide.md
```
Expect: `0`

```bash
grep -c 'not_read: \["README.md", "docs/\*.md"\]' docs/operator-guide.md
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documentation-only story. Nothing under `src/`, tests, image, template, demo or agent files changes. Only `docs/operator-guide.md` changes, and that is the documenter's write path.
   - Criteria: criterion 1 (nothing outside the docs changes) and criterion 2 (`make check` green) are checkable. Criterion 3 lists each passage change exactly, so each can be checked by grep or by reading the passage. Its failing side is covered: `documents ok` from the document check, and the smoke test greps for the old text being gone (`0`). Criterion 3 reads "the `check` line is the line `factory/pipeline.yml` holds on `main` when the story starts". That is deterministic. `factory/pipeline.yml` currently holds `time_limit: 8`, and the guide's line 909 has 15.
   - Smoke test: the four commands are runnable. Each `Expect:` line is a checkable value (`0`, `0`, `1`, `documents ok`). I confirmed in the guide that the old text exists: line 900 has `not_read: ["factory/*", "docs/*"]`, line 914 has "will run `secrets`", and line 905 has "after the story that built the key".
   - Architecture: not applicable beyond the write paths. The change is documentation in the operator guide, which the documenter stage keeps.
   - Scope: it stays within F0023, which covers the operator guide's `not_read` documentation and the feature's decisions 2 and 12. Nothing in "Out of scope" is touched.
4. factory: started tests as self.
