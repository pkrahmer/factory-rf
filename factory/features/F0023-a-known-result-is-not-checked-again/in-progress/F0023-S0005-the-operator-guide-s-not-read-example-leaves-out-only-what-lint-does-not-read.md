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
