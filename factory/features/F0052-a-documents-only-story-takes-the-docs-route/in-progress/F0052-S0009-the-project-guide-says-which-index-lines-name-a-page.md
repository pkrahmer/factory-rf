# The project guide says which lines of its index name a page
## Description

The guard `tests/guards/test_project_guide_files.py` reads a line of `## The files` in `docs/project-guide/README.md` as a page entry when the line starts with `` - ` ``, a name in backticks, and goes on to a sentence with a full stop (`INDEX_LINE` in `tests/support/guide_files_support.py`). The index does not say so. In F0052-S0007 the documenter started a list item with `` `## The files` ``. The guard read it as a page named "## The files" and reported it missing, and the docs-only stage stalled and cost a second run. The next feature rewrites this index on the docs route, where no tester reads the guard first. This story adds that rule to the index, in one or two sentences next to the sentence on the guard, so that a writer starts every other list item in the section with a word. The guard and its pattern stay as they are.

## Interface

- `docs/project-guide/README.md`, `## The files`, the paragraph that names the guard: it also says which lines the guard reads as a page entry (a list item that starts with a name in backticks and goes on to a sentence ending in a full stop), and that any other list item in this section must start with a word. The wording is the documenter's, by `docs/project-guide/style.md`.
- No code and no test changes.

## Acceptance criteria

1. `## The files` in `docs/project-guide/README.md` says that a list item starting with a name in backticks is read as a page entry, and that other list items start with a word.
2. The guard still passes: every page entry and every exception list item in the section reads as it did before. `uv run pytest tests/guards/test_project_guide_files.py` passes.
3. `make documents` prints `documents ok`.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *The files*, as above. `docs/decisions.md`: none, because nothing is decided. `docs/operator-guide/`: none, because the operator does not run the guards.

## Smoke test

```bash
sed -n '/^## The files/,/^## /p' docs/project-guide/README.md | grep -c 'backticks'
```
Expect: a number of at least `1`.

```bash
uv run pytest tests/guards/test_project_guide_files.py 2>&1 | tail -1 | grep -c " passed"
```
Expect: `1`

```bash
make documents 2>&1 | tail -1
```
Expect: `documents ok`

## Journal
