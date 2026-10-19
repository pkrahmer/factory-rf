# The operator guide says the template and the todo demo run under the write guard

## Description

`docs/operator-guide.md`, *The pipeline definition*, says that a project made from `template/`, and the todo demo, "do not run under the guard as they are": their `licenses` recipe and coverage are said to write at the checkout's root, and "until then its `make check` ends with `Permission denied`". That has not been true since both were changed. `template/Makefile` and `demo/todo-service/project/Makefile` write `.reports/licenses-requirements.txt`, the template's `test` recipe sets `COVERAGE_FILE=.reports/.coverage`, the demo's `pyproject.toml` sets `data_file = ".reports/.coverage"`, and both pipeline definitions (`template/factory/pipeline.yml`, `demo/todo-service/project/factory/pipeline.yml`) name `tool_paths` with `.reports/*`. An operator who starts a project from the template is told to make a fix that is already made and to expect a red `make check` that does not happen. This story replaces that one paragraph (finding H1 of the documentation review of 2026-10-20). It changes no other passage.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes one paragraph of `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *The pipeline definition*: the paragraph that begins "A project made from `template/`, and the todo demo, do not run under the guard as they are." becomes exactly this paragraph, and no other passage changes:

   "A project made from `template/`, and the todo demo, run under the guard as they are: their tools keep their files under `.reports/` (the `licenses` recipe's requirements file, and coverage's data file), and their pipeline definitions name `.reports/*` in `tool_paths`. A project whose tools write anywhere else at the checkout's root moves those files into a folder its `tool_paths` names, the same way; until then its `make check` ends with `Permission denied`."

   `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F 'do not run under the guard as they are' docs/operator-guide.md || true
grep -c -F 'A project made from `template/`, and the todo demo, run under the guard as they are' docs/operator-guide.md
```
Expect: two lines, `0` and `1`

```bash
grep -c -F '.reports/licenses-requirements.txt' template/Makefile demo/todo-service/project/Makefile
grep -c -F '".reports/*"' template/factory/pipeline.yml demo/todo-service/project/factory/pipeline.yml
```
Expect: four lines, `template/Makefile:3`, `demo/todo-service/project/Makefile:3`, `template/factory/pipeline.yml:1`, `demo/todo-service/project/factory/pipeline.yml:1` (what the new paragraph says is what the files hold)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/operator-guide.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
