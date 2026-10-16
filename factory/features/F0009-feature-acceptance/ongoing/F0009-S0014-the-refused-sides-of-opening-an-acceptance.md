---
stage: doing
pr: 117
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The refused sides of opening an acceptance

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

The feature acceptance of F0009 ran a hand mutation pass of 30 mutants over the feature's modules. Three survived, and each one is a rule that no test holds on its refused side:

- `AcceptanceService.open` (`src/factory/application/acceptance.py`) refuses a feature whose status is not `due`. Only `incomplete` is tested. With the guard weakened to "refuse only `incomplete`", every test passes, although `open` would then start a second acceptance next to one `in_flight`, one `merged_unrecorded`, or one already `accepted` or `refused` for the same stories.
- `AcceptanceReader` counts only the file names directly in `backlog/`, `in-progress/` and `done/` (decision 3 of the feature: "a name that reads as a story id, directly in ..."). With the "directly" dropped, every test passes, although a story file in a subdirectory such as `done/old/` would then count as archived.
- `acceptance_facts` raises `ValueError` with the message `feature <id> has no free story number after 9999` when the highest story number is 9999. The test checks only for a `ValueError`. With the limit moved by one, pydantic's own `ValidationError` (a `ValueError`) is raised instead, with another message, and the test still passes.

This story pins those three refused sides. The code already behaves as the criteria say: the tester writes the tests, and the coder expects to change nothing in `src/`. If a test fails, the code is wrong and the coder fixes it within the Interface below.

## Interface

No new or changed names. The behaviour pinned:

- `AcceptanceService(boundaries, definition).open(feature)`: for a feature whose status is `in_flight`, `merged_unrecorded`, `accepted` or `refused`, it raises `CannotHandle` with kind `acceptance_due` and the reason `feature <feature> is <status>, not due`. It creates no branch, makes no commit on any remote branch and pushes nothing.
- `AcceptanceReader(boundaries, definition).read()` and `.feature_files(feature)`: a file below a subdirectory of a lifecycle folder (`<feature directory>/done/old/F0002-S0003-c.md`) is not among the folder's names, so it neither archives a story nor keeps a feature incomplete.
- `acceptance_facts(files, cost_line)` (`src/factory/domain/acceptance.py`): with `F0002-S9999-z.md` among the files, it raises `ValueError` whose `str` is `feature F0002 has no free story number after 9999`, and not a pydantic `ValidationError`.

Tests: one new module, `tests/application/test_acceptance_refusals.py`, for the first two rules, with the fixtures of `tests/conftest.py`. For criteria 1 and 2 the `walk` fixture pushes `F0002-todo` with its two archived stories; the test brings it into each status (`in_flight`: `AcceptanceService(boundaries, walk.definition).open("F0002")` after a fetch; `merged_unrecorded`: that, then `human.merge("work-item/F0002-A0001", "merge")`; `accepted` and `refused`: the report `done/F0002-A0001-acceptance.md` pushed to `main` with `AcceptanceState(stage="done", outcome=<status>, stories=["F0002-S0001", "F0002-S0002"])`) and checks the status with `walk.status()` before calling `open`. Criterion 3 pushes its own `F0002-todo` files with `human.push_file` and does not use `walk`. One new test in a new module, `tests/domain/test_acceptance_facts_limit.py`, for the third rule. No existing test module changes.

## Acceptance criteria

1. `open("F0002")` for the feature `F0002-todo` raises `CannotHandle` with kind `acceptance_due` and the reason `feature F0002 is <status>, not due` for each of the four statuses `in_flight` (A0001 opened on its branch), `merged_unrecorded` (A0001's report merged into `in-progress/` on `origin/main`, not booked), `accepted` and `refused` (A0001 booked in `done/` with that outcome and `stories` equal to the archived stories). The test is parametrized with one row per status, plus a row for `due` (the feature with its archived stories and no report) in which `open` returns `F0002-A0001` and its branch `work-item/F0002-A0001` exists on the remote.
2. For each refusing row of criterion 1, the remote's branches are the same before and after the call: no new branch `work-item/F0002-A000<n>`, and every existing branch is at the commit it had.
3. `AcceptanceReader(boundaries, definition)` counts a story file only directly in its folder, in one test parametrized over two cases of `F0002-todo` on `origin/main`: with `done/old/F0002-S0001-a.md` as its only story file, `read()` gives `F0002` the status `incomplete` and `feature_files("F0002").done` is `[]`; with `done/F0002-S0001-a.md` and `backlog/old/F0002-S0002-b.md`, the status is `due` and `feature_files("F0002").done` is `["F0002-S0001-a.md"]`.
4. `acceptance_facts` with `F0002-S9999-z.md` in `done` raises an exception whose type is exactly `ValueError` and whose `str` is `feature F0002 has no free story number after 9999`. With `F0002-S9998-y.md` as the highest, `next_story` is `F0002-S9999`. Both are rows of one parametrized test.
5. `make check` stays green.
6. docs: the operator guide's "When a feature acceptance is due" says that a story file counts only directly in `backlog/`, `in-progress/` or `done/`, not in a subdirectory, as the project guide's `FeatureFiles` item already does ("the names directly in"). The project guide already says that `open` refuses any status other than `due`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_acceptance_refusals.py tests/domain/test_acceptance_facts_limit.py
```
Expect: the last line is `<n> passed in <time>`, with n at least 9 (five rows of criterion 1, two of criterion 3, two of criterion 4).

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: names no new or changed names, only pinned behaviour of existing modules (`AcceptanceService.open`, `AcceptanceReader.read`/`feature_files`, `acceptance_facts`), each with the exact exception kind and message text. The test modules and fixtures (`walk`, `human.push_file`, `human.merge`) are named concretely.
   - Criteria: each is testable by one parametrized test function. Criterion 1 has the four refusing statuses plus the passing `due` row. Criterion 2 is the no-side-effect check for the refusing rows. Criterion 3 has a failing and a passing case. Criterion 4 has the 9999 and 9998 boundary rows. Every rule is covered on both its refused and accepted sides. The Interface states no behaviour that lacks a criterion.
   - Demo: one runnable pytest command. Its Expect line is checkable (last line `<n> passed`, n at least 9, with the row count explained).
   - Architecture: tests only, in `tests/application/` and `tests/domain/`, mirroring the package. No `src/` change is expected. No new dependency and no change to existing tests.
   - Scope: it is within F0009 (feature acceptance), a story proposed by the feature acceptance and listed in `FEATURE.md`. It touches nothing under Out of scope.
3. tester: Wrote the tests for the three refused sides. Each criterion maps to one parametrized test:
   - criterion 1: tests/application/test_acceptance_refusals.py::test_only_a_due_feature_is_opened. It has 5 rows: in_flight, merged_unrecorded, accepted and refused, which raise `CannotHandle` with kind `acceptance_due` and the reason `feature F0002 is <status>, not due`, and a due row, where `open` returns `F0002-A0001` and the branch `work-item/F0002-A0001` exists on the remote.
   - criterion 2: tests/application/test_acceptance_refusals.py::test_a_refused_opening_leaves_every_remote_branch_as_it_was. It has the 4 refusing rows. `for-each-ref refs/heads` on the bare remote is the same before and after, and there is no `work-item/F0002-A0002`.
   - criterion 3: tests/application/test_acceptance_refusals.py::test_a_story_file_counts_only_directly_in_its_folder. It has 2 rows: `done/old/` only gives incomplete with done `[]`; `done/` plus `backlog/old/` gives due with done `["F0002-S0001-a.md"]`.
   - criterion 4: tests/domain/test_acceptance_facts_limit.py::test_the_next_story_number_ends_at_9999. It has 2 rows: with 9998 as the highest, next_story is `F0002-S9999`; with 9999, `type(e) is ValueError` and the exact message.
   - criteria 5 and 6 are not tested (they are `make check` and docs).

   Setup: criteria 1 and 2 share the indirect-parametrized fixture `brought` in the new module. It uses `walk` and brings F0002 into each status the way the Interface says: open after a fetch; open, then `human.merge`; or push the done report with the outcome. It then checks `walk.status()`. Criterion 3 pushes its own feature file and story files with `human.push_file`.

   Files created: tests/application/test_acceptance_refusals.py and tests/domain/test_acceptance_facts_limit.py. No existing test changed.

   Run: `make test` is green; the new tests pass now. This is expected, because the assignment says the code already behaves as the criteria say, so these tests are not red. Every module imported. `make lint` is green. I skipped the type check as the stage says. The outcome is mapped through a typed `dict[AcceptanceStatus, AcceptanceOutcome]` so that `AcceptanceState(outcome=...)` passes `mypy --strict`. The coder's `make check` confirms this.

   `make lint`: lint: green
   `make test`: test: green
