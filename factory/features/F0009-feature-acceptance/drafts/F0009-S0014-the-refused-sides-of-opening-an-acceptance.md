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

Tests: one new module, `tests/application/test_acceptance_refusals.py`, for the first two rules, with the fixtures of `tests/conftest.py`. It brings a feature into each status as `tests/application/test_acceptance_service.py` and `tests/application/test_acceptance_reading.py` do. One new test in a new module, `tests/domain/test_acceptance_facts_limit.py`, for the third rule. No existing test module changes.

## Acceptance criteria

1. `open("F0002")` for the feature `F0002-todo` raises `CannotHandle` with kind `acceptance_due` and the reason `feature F0002 is <status>, not due` for each of the four statuses `in_flight` (A0001 opened on its branch), `merged_unrecorded` (A0001's report merged into `in-progress/` on `origin/main`, not booked), `accepted` and `refused` (A0001 booked in `done/` with that outcome and `stories` equal to the archived stories). The test is parametrized with one row per status, plus a row for `due` (the feature with its archived stories and no report) in which `open` returns `F0002-A0001` and its branch `work-item/F0002-A0001` exists on the remote.
2. For each refusing row of criterion 1, the remote's branches are the same before and after the call: no new branch `work-item/F0002-A000<n>`, and every existing branch is at the commit it had.
3. A feature whose only story file is `done/old/F0002-S0001-a.md` has the status `incomplete`, and `feature_files("F0002").done` does not contain `F0002-S0001-a.md`. With `done/F0002-S0001-a.md` directly in `done/` and `backlog/old/F0002-S0002-b.md` in a subdirectory of `backlog/`, the status is `due`. The test is parametrized over the two cases.
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
