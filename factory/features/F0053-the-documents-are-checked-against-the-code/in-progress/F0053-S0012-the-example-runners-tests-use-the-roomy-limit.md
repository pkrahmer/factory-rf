---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-06T12:54:40.010596Z'
  lease_duration: 60
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
---

# The example runner's tests use the roomy limit
## Description

`tests/shared/adapters/test_document_examples.py` gives every command one second (`SHORT_LIMIT_SECONDS = 1`), also the commands that must write or print before the limit, such as the `pwd > record` command of the folder-removal test. It bounds the elapsed time by a local `ELAPSED_BOUND_SECONDS = 15`. `CLAUDE.md`, *Tests*, asks a child that must act before its limit for `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS` of `tests/support/time_limits.py`, because `make test` runs on every core and a stand-in once needed more than three seconds to start. The S0003 reviewer named this as a note in the last round, and nobody took it up. In the same F0053 tests, three test modules write a production constant again instead of importing it. These are `CHECKED_LIST` and `REPORT_HEADING` in `tests/entry/test_check_documents_checked_files.py`, with `REPORT_HEADING` repeated in two more entry tests, and `SETTINGS_FILE` in `tests/hosting/adapters/test_instance_fixture.py`. The S0004 and S0006 reviewers noted them. This story is a test-only repair: the code stays as it is.

## Interface

- `tests/shared/adapters/test_document_examples.py`: a command that must start, write or print before its limit runs under `ROOMY_LIMIT`, and its elapsed time is bounded by `ROOMY_BOUND_SECONDS`. A command that must be killed (`sleep` past the limit) may keep a short limit. The local `ELAPSED_BOUND_SECONDS` goes.
- `REPORT_HEADING`: one constant in `tests/support/check_documents_support.py`, used by `tests/entry/test_check_documents_checked_files.py`, `tests/entry/test_check_documents_operator_guide.py` and `tests/entry/test_check_documents_references.py` (standing leave to move a shared test helper).
- `CHECKED_LIST` imports `CHECKED_DOCUMENTS` from `factory.shared.domain.documents`, and `SETTINGS_FILE` imports `factory.hosting.adapters.instance_fixture.SETTINGS_FILE`, unless the human prefers that a test keep the criterion's own literal (the S0006 tester's reason, journal 23 of that story).
- Changing the limits in tests that F0053-S0003 wrote is beyond the standing leave. Feature decision 6 gives the leave. The leave also covers any other earlier test, whichever story wrote it, whose only failure is the effect this Interface describes; every changed test keeps its name and what it checks, and the entry names each one. Every changed test keeps its name and what it checks.
- No module under `src/` changes.

## Acceptance criteria

1. In `tests/shared/adapters/test_document_examples.py`, every runner whose commands must print or write before their limit is built with `ROOMY_LIMIT`, and every elapsed-time assertion uses `ROOMY_BOUND_SECONDS`. `grep -c ELAPSED_BOUND_SECONDS` on the file prints `0`.
2. The text `Report (not checked yet):` is written once under `tests/`, in `tests/support/check_documents_support.py`.
3. Every test of the three changed modules keeps its name, and `uv run pytest` over them passes.
4. `make check` stays green.
5. docs: none, the change is to tests only and no reader-facing behaviour changes.

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
