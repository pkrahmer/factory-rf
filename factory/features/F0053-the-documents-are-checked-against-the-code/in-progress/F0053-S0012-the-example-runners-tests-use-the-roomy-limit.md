---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 596
comments_read: [6685329163]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T12:54:40.003496Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T12:54:40.010596Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T12:55:06.232263Z'
  stage: intake
  run: b20fd69000c547eaa43c284c74840480
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T12:56:56.861286Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T12:56:59.427354Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T12:57:27.674496Z'
  stage: intake
  run: 735dfc5f37ec4dcdbc623633c9db7098
---

# The example runner's tests use the roomy limit
## Description

`tests/shared/adapters/test_document_examples.py` gives every command one second (`SHORT_LIMIT_SECONDS = 1`), also the commands that must write or print before the limit, such as the `pwd > record` command of the folder-removal test. It bounds the elapsed time by a local `ELAPSED_BOUND_SECONDS = 15`. `CLAUDE.md`, *Tests*, asks a child that must act before its limit for `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS` of `tests/support/time_limits.py`, because `make test` runs on every core and a stand-in once needed more than three seconds to start. The S0003 reviewer named this as a note in the last round, and nobody took it up. In the same F0053 tests, three test modules write a production constant again instead of importing it. These are `CHECKED_LIST` and `REPORT_HEADING` in `tests/entry/test_check_documents_checked_files.py`, with `REPORT_HEADING` repeated in two more entry tests, and `SETTINGS_FILE` in `tests/hosting/adapters/test_instance_fixture.py`. The S0004 and S0006 reviewers noted them. This story is a test-only repair: the code stays as it is.

## Interface

- `tests/shared/adapters/test_document_examples.py`: every `ProcessExampleRunner` is built with `ROOMY_LIMIT` and its elapsed time is bounded by `ROOMY_BOUND_SECONDS`, except the runner of the time-limit test, whose command must be killed (`sleep` past the limit) and may keep a short limit (journal 4). The tester names each runner it changed. The local `ELAPSED_BOUND_SECONDS` goes.
- `REPORT_HEADING`: one constant in `tests/support/check_documents_support.py`, used by `tests/entry/test_check_documents_checked_files.py`, `tests/entry/test_check_documents_copies.py`, `tests/entry/test_check_documents_operator_guide.py` and `tests/entry/test_check_documents_references.py`; the inline literals of the last two become the constant (standing leave to move a shared test helper; journal 4).
- `CHECKED_LIST` imports `CHECKED_DOCUMENTS` from `factory.shared.domain.documents`, and `SETTINGS_FILE` imports `factory.hosting.adapters.instance_fixture.SETTINGS_FILE`. Both are imported (journal 4).
- Changing the limits in tests that F0053-S0003 wrote is beyond the standing leave. Feature decision 6 gives the leave. The leave also covers any other earlier test, whichever story wrote it, whose only failure is the effect this Interface describes; every changed test keeps its name and what it checks, and the entry names each one. Every changed test keeps its name and what it checks.
- No module under `src/` changes.

## Acceptance criteria

1. In `tests/shared/adapters/test_document_examples.py`, only the time-limit test builds a `ProcessExampleRunner` with a limit shorter than `ROOMY_LIMIT`, every elapsed-time assertion uses `ROOMY_BOUND_SECONDS`, and `grep -c ELAPSED_BOUND_SECONDS` on the file prints `0`.
2. The text `Report (not checked yet):` is written once under `tests/`, in `tests/support/check_documents_support.py` as `REPORT_HEADING`; `tests/entry/test_check_documents_checked_files.py`, `tests/entry/test_check_documents_copies.py`, `tests/entry/test_check_documents_operator_guide.py` and `tests/entry/test_check_documents_references.py` use that constant.
3. `tests/entry/test_check_documents_checked_files.py` holds no literal `docs/checked-documents.txt` and imports `CHECKED_DOCUMENTS` from `factory.shared.domain.documents`.
4. `tests/hosting/adapters/test_instance_fixture.py` holds no literal of the settings file's name and imports `SETTINGS_FILE` from `factory.hosting.adapters.instance_fixture`.
5. Every test of the changed modules (`tests/shared/adapters/test_document_examples.py`, `tests/entry/test_check_documents_checked_files.py`, `tests/entry/test_check_documents_operator_guide.py`, `tests/entry/test_check_documents_references.py`, `tests/entry/test_check_documents_copies.py`, `tests/hosting/adapters/test_instance_fixture.py`, `tests/support/check_documents_support.py`) keeps its name, and `uv run pytest` over them passes.
6. `make check` stays green.
7. docs: none, the change is to tests only and no reader-facing behaviour changes.

## Smoke test

```bash
grep -rc --include="*.py" "Report (not checked yet):" tests | grep -v ":0$"
```
Expect: `tests/support/check_documents_support.py:1`

```bash
uv run pytest tests/shared/adapters/test_document_examples.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so there are no form findings):
   1. The Interface says `CHECKED_LIST` imports `CHECKED_DOCUMENTS` and `SETTINGS_FILE` is imported from `factory.hosting.adapters.instance_fixture`. No criterion tests either. Criteria 1 to 4 cover only the roomy limit, the elapsed bound and `REPORT_HEADING`. Please add one criterion for each, for example "`tests/entry/test_check_documents_checked_files.py` holds no literal `CHECKED_LIST` and imports `CHECKED_DOCUMENTS`" and the same for `SETTINGS_FILE` in `tests/hosting/adapters/test_instance_fixture.py`. I would add them.
   2. The same line says "unless the human prefers that a test keep the criterion's own literal". That leaves two readings for the coder and the tester. Please decide now. I would choose to import both.
   3. The Interface lists three modules for `REPORT_HEADING`: checked_files, operator_guide and references. Criterion 2 says the text appears once under `tests/`. Today `tests/entry/test_check_documents_copies.py:14` also defines `REPORT_HEADING`. In `test_check_documents_operator_guide.py:93` and `test_check_documents_references.py:211` the text is an inline literal, not a constant. Criterion 2 and the smoke test need `copies` changed too. Please add `test_check_documents_copies.py` to the Interface, or confirm that the count should exclude it. I would add it.
   4. "A command that must be killed may keep a short limit" has no criterion, and neither does "every runner whose commands must print or write ... is built with `ROOMY_LIMIT`". The criterion cannot be checked by one test as written. Please name the tests or runners that take `ROOMY_LIMIT` (for example the folder-removal test with `pwd > record`) and the ones that keep a short limit.
   5. Criterion 3 says "the three changed modules", but the Interface changes more than three: the example-runner test, three or four entry tests, the instance-fixture test and the support module. Please list the modules.
4. 2026-11-06 human: 1. Yes, one criterion each: `tests/entry/test_check_documents_checked_files.py` holds no literal `docs/checked-documents.txt` and imports `CHECKED_DOCUMENTS`; `tests/hosting/adapters/test_instance_fixture.py` holds no literal of the settings file's name and imports `SETTINGS_FILE` from `factory.hosting.adapters.instance_fixture`.
   2. Import both. The sentence "unless the human prefers that a test keep the criterion's own literal" goes.
   3. Add `tests/entry/test_check_documents_copies.py`: its `REPORT_HEADING` and the inline literals in `test_check_documents_operator_guide.py` and `test_check_documents_references.py` all use the one constant in `tests/support/check_documents_support.py`, and the text `Report (not checked yet):` appears once under `tests/`.
   4. One checkable rule instead of a list: in `tests/shared/adapters/test_document_examples.py`, every `ProcessExampleRunner` is built with `ROOMY_LIMIT` and its elapsed time is bounded by `ROOMY_BOUND_SECONDS`, except the runner of the time-limit test, whose command must be killed and may keep a short limit. The criterion: only that one test builds a runner with a limit shorter than `ROOMY_LIMIT`, and no local `ELAPSED_BOUND_SECONDS` remains. The tester names each runner it changed.
   5. The modules: `tests/shared/adapters/test_document_examples.py`, `tests/entry/test_check_documents_checked_files.py`, `tests/entry/test_check_documents_operator_guide.py`, `tests/entry/test_check_documents_references.py`, `tests/entry/test_check_documents_copies.py`, `tests/hosting/adapters/test_instance_fixture.py` and `tests/support/check_documents_support.py`. Criterion 3 says "the changed modules" and names them.
5. factory: started intake as vm.
6. intake: accepted, after carrying in the human's answers of journal 4 (the human's edit, not mine): I rewrote the Interface lines (the "unless the human prefers" sentence went, `test_check_documents_copies.py` and the inline literals joined `REPORT_HEADING`, the one-rule form for the runners) and replaced the criteria with 7: one each for `CHECKED_DOCUMENTS` and `SETTINGS_FILE` (new 3 and 4), criterion 1 reworded as only the time-limit test having a short limit, criterion 2 naming the four modules, criterion 5 listing the seven modules, and `make check` and `docs:` last.
   - Interface: names concrete test modules, constants and import sources. `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS` exist in `tests/support/time_limits.py`, and `SETTINGS_FILE` exists in `src/factory/hosting/adapters/instance_fixture.py`. No module under `src/` changes.
   - Criteria: each is checkable. Every rule has its failing side: only one test may keep a short limit, no `ELAPSED_BOUND_SECONDS` remains, and the text is written once. Criterion 5 asks that test names stay and the tests pass.
   - Smoke test: both commands are runnable. The pytest addopts has a single `-q`, which prints the summary line, and the command passes no extra `-q`. Each Expect line is checkable.
   - Docs criterion: `docs: none`, which is right because only tests change. It dictates no sentences.
   - Architecture: test-only changes put shared helpers in `tests/support/`, as CLAUDE.md asks. No test module imports another.
   - Scope: within F0053 and not in its "Out of scope". Decision 6 gives the leave to change earlier tests, and the tester names each changed test. The route is `tests`.
