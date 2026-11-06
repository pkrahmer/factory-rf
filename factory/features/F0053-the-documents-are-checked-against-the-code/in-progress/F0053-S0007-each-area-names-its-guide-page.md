---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 591
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T11:13:30.775476Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T11:13:30.781987Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T11:13:49.366381Z'
  stage: intake
  run: 9fc7b7e1998f464cad270c1c652d12b7
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T11:13:54.628446Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-06T11:14:39.687114Z'
  stage: tests
  run: 53ac4abac9b64dbab9fe2f64a1086e6b
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T11:14:45.150527Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-06T11:18:55.067845Z'
  stage: doing
  run: 7672f638a29a4d12a9013b0e575046f3
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T11:19:00.306254Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-06T11:19:38.884641Z'
  stage: review
  run: 77973e9090354003ab33dd69ed1c84b7
---

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

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names the seven area `__init__.py` files, `entry`'s, and the new `tests/guards/test_area_guides.py`. The line text is exact. All seven guide pages and `README.md` exist under `docs/project-guide/`.
   - Criteria: criterion 1 is testable by one function, one row per package. Criterion 2 covers both failing sides, a missing line and a line naming a missing page, as rows of one test. Every Interface behaviour has a criterion. The Interface's "reads the docstring without importing it" has no criterion of its own, but it is an implementation detail and not a behaviour, so I did not ask about it.
   - Smoke test: the `grep -l ... | wc -l` command is runnable and `Expect: 8` is checkable. It counts the 7 areas plus `entry`, and nothing else under `src/factory/*/__init__.py` carries such a line.
   - Docs criterion: it names what the reader must know, namely that each area's package names its page. It dictates no sentences, and `docs/decisions.md` is explicitly untouched.
   - Architecture: the change touches only package docstrings and a guard test in `tests/guards/`, which fits the layout in `CLAUDE.md`. There is no new dependency and no change to `factory/`.
   - Scope: this is the feature's S0007 and decision 5, and it is not in "Out of scope". Module docstrings stay unchanged.
   - Route: `tests`, because the Interface changes `src/` and `tests/` paths, which the documenter may not write.
4. factory: started tests as vm.
5. tester: Wrote the guard `tests/guards/test_area_guides.py`, the one file in the Interface. It reads each package's `__init__.py` with `ast` and does not import it. It names no work item or criterion.

   - criterion 1: tests/guards/test_area_guides.py::test_each_package_names_its_existing_guide_page. It has eight rows: `shared`, `hosting`, `work`, `agents`, `watching`, `machine` and `pipeline` each expect `Guide: docs/project-guide/<area>.md`, and `entry` expects `Guide: docs/project-guide/README.md`.
   - criterion 2: tests/guards/test_area_guides.py::test_the_guard_fails_for_a_missing_line_or_page. It runs on a copy under `tmp_path` with three rows: `line-missing` and `page-missing` must fail, and `line-and-page` must pass, so a guard that always fails does not pass this test.
   - criterion 3 (`make check` green) and criterion 4 (docs): no test, as is usual for these two.

   How the check works: the helper `guide_problems(root, package, page)` sits in the test module, because no other module uses it. It reports a problem when no line of the docstring is exactly the expected line, or when the page it names is not a file under `root`. I did not add a separate case for a line that names a different page: criterion 1 fixes each package's exact line, and a different page fails the check for a missing line.

   Run: `uv run pytest -q tests/guards/test_area_guides.py` shows the eight rows of the first test failing for the right reason: the guide line is not yet in any package's docstring. The three copy rows pass, because they only test the guard. `make lint` is green.

   Files created: tests/guards/test_area_guides.py. Modules the test run could not import: none (the guard imports nothing of `factory`). Nothing was interpreted, so there is no open question.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: I added a guide line to the package docstring of all seven areas and of `entry`. Each docstring keeps its first sentence and gains a second paragraph of one line, `Guide: docs/project-guide/<area>.md`. For `entry` the line names `docs/project-guide/README.md`. The closing quotes go on a line of their own, as the multi-line docstring rule requires.

   Files changed: `src/factory/{shared,hosting,work,agents,watching,machine,pipeline,entry}/__init__.py`. No test was touched.

   - **Main choice:** the line starts at column 0 inside the docstring, so the smoke test's `grep -l "^Guide: docs/project-guide/"` finds it. I ran that command and it gives `8`. I rejected indenting the line, or putting it inline after the first sentence: both would break the exact-line match that `tests/guards/test_area_guides.py` and the smoke test expect.
   - **Refactor:** I read the diff once. It is only the docstring lines and needs no change.
   - **Description:** the journal did not change the task's meaning, so the Description stays as it is.
   - **Noticed, not touched:** the `README.md` sentence in criterion 4 (docs) is the documenter's.
   - **Check:** `make check` is green: `test: green (104.1 s)`, `check: green`.

   `check`: check: green
   `duplicates`: duplicates: 6 new, 39 known, 4 gone
8. factory: started review as vm.
9. reviewer: no findings

   What I checked, from reading `git diff main...HEAD -- . ':!factory'` and the work item:
   - Acceptance criteria: criterion 1 is tested by `tests/guards/test_area_guides.py::test_each_package_names_its_existing_guide_page`, with eight rows (the seven areas and `entry`). Each row expects the exact line `Guide: docs/project-guide/<page>`. Criterion 2 is tested by `test_the_guard_fails_for_a_missing_line_or_page`, three rows of one parametrized test on a copy under `tmp_path`: `line-missing` and `page-missing` must fail, and `line-and-page` must pass, so a guard that always fails cannot pass this test. Both failing sides the Interface states (a missing line, a missing page) have a row. The Interface states no numeric limit. The guard reads the docstring with `ast` and imports nothing, as the Interface asks. The coder's journal entry 7 records `make check` green.
   - Code: all eight `src/factory/*/__init__.py` keep their first sentence and gain the second paragraph `Guide: docs/project-guide/<area>.md` at column 0; `entry`'s names `README.md`. Every page they name exists under `docs/project-guide/`. The smoke test's `grep -l "^Guide: docs/project-guide/" src/factory/*/__init__.py` matches these eight lines.
   - Architecture: only docstrings changed under `src/`. There is no new import, layer or dependency. The guard sits in `tests/guards/` and imports nothing of `factory`.
   - Security: no secrets, no silencing markers, no shell or string-built commands.
   - Quality: the names say what they are and the test module has its docstring. `ROOT = Path(__file__).parents[2]` is the usual repository-root idiom; `tests/support/*` uses the same line, so it is not a copied helper. Building a list of the lines that start with `Guide: ` before checking for the expected line adds nothing to the result, but it is harmless, so I did not count it as a finding.
   - Work item hygiene: the Description matches what was built. The coder's entry names the main choice (the line at column 0) and what it rejected. The docs criterion (one sentence in `docs/project-guide/README.md`, none in `docs/decisions.md`) still describes what the reader must know.
   - Earlier tests: the diff changes no test file that `main` already holds. Its only test file, `tests/guards/test_area_guides.py`, is new (status `A`).
   - Documents: the diff changes none.
