# Each area names its guide page

## Description

The project guide links into the code; this story gives the way back. Each of the seven areas has one page in the project guide, but nothing in the code says which: a reader who opens a module finds one sentence and no pointer to the page that explains the area. This story adds one line to the docstring of each area's package, `src/factory/<area>/__init__.py`, that names its page, and a guard test that keeps those lines true. It is one line per area and not one per module, so that a hundred docstrings do not have to be kept true (the human, 2026-11-05: links back to the documents, without making it complicated). The module docstrings stay as they are.

## Interface

- `src/factory/<area>/__init__.py` for the seven areas (`shared`, `hosting`, `work`, `agents`, `watching`, `machine`, `pipeline`): the docstring keeps its first sentence and gains a second paragraph of one line, `Guide: docs/project-guide/<area>.md`.
- `src/factory/entry/__init__.py`: the same line, naming `docs/project-guide/README.md`.
- `tests/guards/test_area_guides.py` (new): one row per area and `entry`, reading the package's docstring without importing it; the row fails when the line is missing or names a file that does not exist.

## Acceptance criteria

1. Each of the seven areas' `__init__.py` holds the line `Guide: docs/project-guide/<area>.md` in its docstring, and `entry`'s names `docs/project-guide/README.md`.
2. The guard test fails for a package whose docstring lacks the line, and for a line that names a missing page (rows of one test, on a temporary copy).
3. `make check` stays green.
4. docs: `docs/project-guide/README.md`: one sentence that each area's package names its page. `docs/decisions.md`: none.

## Smoke test

```bash
grep -l "^Guide: docs/project-guide/" src/factory/*/__init__.py | wc -l
```
Expect: `8`

## Journal
