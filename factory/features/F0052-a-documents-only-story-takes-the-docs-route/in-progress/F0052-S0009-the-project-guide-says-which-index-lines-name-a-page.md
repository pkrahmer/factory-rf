---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 583
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T01:39:43.565974Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T01:39:43.573036Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T01:40:08.668839Z'
  stage: intake
  run: 57eae0b55273448ab6ddfa4eca45b712
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T01:40:16.004706Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T01:43:08.202628Z'
  stage: docs-only
  run: e3f717bf302b421b8000f4becd4666fd
---

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

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: the only path changed is `docs/project-guide/README.md`, section `## The files`, the paragraph naming the guard. It states what to say (which lines read as a page entry, and that other list items start with a word). No code or test changes. The path is one the documenter may write, so the route is docs-only.
   - Criteria: criterion 1 (the rule is in the section) is checkable by reading the text. Criterion 2 (guard still passes) names a command. Criterion 3 (`make documents` prints `documents ok`) names a command. Both sides of the rule are covered: a backtick-led item is a page entry, and any other item starts with a word. The closing `make check` and `docs:` criteria are last.
   - Smoke test: all three commands are runnable. The pytest command passes no `-q` and `pyproject.toml` `addopts` already sets `-q`, so `tail -1` shows the summary line and `grep -c " passed"` gives `1`. Each `Expect:` line is checkable: a count of at least 1, `1`, and `documents ok`.
   - Architecture: documents only, and the project guide is kept by the documenter. The guard and `INDEX_LINE` stay untouched.
   - Scope: it falls inside F0052's goal (the next feature's rewrite of the index takes the docs route). Nothing in "Out of scope" is touched.
4. factory: started docs-only as vm.
5. documenter: Changed `docs/project-guide/README.md`, `## The files`: the paragraph that names the guard now also says which lines the guard reads as a page entry (a list item that starts with a name in backticks and goes on to a sentence ending in a full stop) and that every other list item in the section must start with a word, with `## The files` as the example of what goes wrong. The rule matches `INDEX_LINE` in `tests/support/guide_files_support.py`; neither it nor the guard was touched. I ran `tests/guards/test_project_guide_files.py` and it passes. I did not run `make documents`; the factory runs it after this stage. The existing list items in that section all start with a word or an italic title, so they stay valid. Cross-read: the rest of `docs/project-guide/README.md` against the story. Nothing else is stale, and I saw no unrelated stale text. No decisions.md entry was written, so there is no Why or Rejected line to flag.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok
