---
stage: docs
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
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T12:57:32.795776Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T12:58:55.146723Z'
  stage: tests
  run: 0463c8ac98944f2ead4689f376367908
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T12:59:00.475682Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-06T13:03:11.550596Z'
  stage: doing
  run: 8e33431235fc4d56b56e39a67634d09c
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-06T13:03:17.277849Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-06T13:03:59.149679Z'
  stage: review
  run: 79202f18656848c4a15a2868058a6ad2
---

# The example runner's tests use the roomy limit
## Description

`tests/shared/adapters/test_document_examples.py` gives every command one second (`SHORT_LIMIT_SECONDS = 1`), also the commands that must write or print before the limit, such as the `pwd > record` command of the folder-removal test. It bounds the elapsed time by a local `ELAPSED_BOUND_SECONDS = 15`. `CLAUDE.md`, *Tests*, asks a child that must act before its limit for `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS` of `tests/support/time_limits.py`, because `make test` runs on every core and a stand-in once needed more than three seconds to start. The S0003 reviewer named this as a note in the last round, and nobody took it up. In the same F0053 tests, three test modules write a production constant again instead of importing it. These are `CHECKED_LIST` and `REPORT_HEADING` in `tests/entry/test_check_documents_checked_files.py`, with `REPORT_HEADING` defined again in `tests/entry/test_check_documents_copies.py` and written inline in two more entry tests, and `SETTINGS_FILE` in `tests/hosting/adapters/test_instance_fixture.py`. The S0004 and S0006 reviewers noted them. This story is a test-only repair: the code stays as it is.

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
7. factory: started tests as vm.
8. tester: This story changes tests only, so the tester did the repair itself and the tests are green, not red. The code stays as it is, and the coder's step is `make check`. Every test kept its name and what it checks. No test module was added or removed.

   Criteria:
   - criterion 1: `tests/shared/adapters/test_document_examples.py`. The shared `runner` fixture is now built with `ROOMY_LIMIT`. It is used by every test except the time-limit one: test_the_blocks_of_one_document_share_a_folder_and_the_next_document_starts_fresh, test_a_command_whose_output_differs_gives_one_finding_and_one_that_matches_none, test_the_output_compared_holds_stderr_too, test_a_block_naming_an_unknown_fixture_gives_a_finding, test_the_commands_never_run_in_the_current_directory, test_env_in_a_block_shows_the_fixed_variables_and_the_fixtures_and_not_the_callers, test_a_fixture_that_cannot_be_prepared_gives_one_finding_and_runs_no_command, test_the_folder_and_the_home_are_gone_once_the_document_has_run (its past-the-limit row is now killed at 10 s; `sleep 30` still outlasts it) and test_a_fixtures_variable_does_not_replace_a_fixed_one.
     - Only test_a_command_past_its_limit_gives_one_finding_and_the_later_blocks_do_not_run builds its own runner with `SHORT_LIMIT_SECONDS` (1 s), because its command must be killed.
     - That test's elapsed-time check now uses `ROOMY_BOUND_SECONDS`.
     - `ELAPSED_BOUND_SECONDS` is removed, and `grep -c` on the file prints 0.
   - criterion 2: `REPORT_HEADING` now lives in `tests/support/check_documents_support.py`. The local copies in `tests/entry/test_check_documents_checked_files.py` and `tests/entry/test_check_documents_copies.py` are removed and those files import the shared one. The inline literals in `tests/entry/test_check_documents_operator_guide.py` (the filter in the output comparison) and `tests/entry/test_check_documents_references.py` (the expected head lines) are replaced by the constant. The smoke grep prints only `tests/support/check_documents_support.py:1`.
   - criterion 3: `tests/entry/test_check_documents_checked_files.py`. `CHECKED_LIST` is removed. The test imports `CHECKED_DOCUMENTS` from `factory.shared.domain.documents` and uses it wherever `CHECKED_LIST` was used.
   - criterion 4: `tests/hosting/adapters/test_instance_fixture.py`. The local `SETTINGS_FILE = "factory.env"` is removed, and `SETTINGS_FILE` is imported from `factory.hosting.adapters.instance_fixture`.
   - criterion 5: I ran `uv run pytest -q` once over the six changed test modules. Every test passed, and none was renamed.
   - criteria 6 and 7: these are the coder's `make check` and a docs-only criterion, so there is no test for them.

   Files changed: tests/shared/adapters/test_document_examples.py (written by F0053-S0003; changed under the leave of feature decision 6), tests/entry/test_check_documents_checked_files.py, tests/entry/test_check_documents_copies.py, tests/entry/test_check_documents_operator_guide.py, tests/entry/test_check_documents_references.py, tests/hosting/adapters/test_instance_fixture.py and tests/support/check_documents_support.py (the `REPORT_HEADING` move falls under the standing leave in CLAUDE.md, *Tests*). I created no new files.

   Every module imported. `make lint` is green. I did not run the type check, as the stage says.

   Still open: `tests/entry/test_check_documents_copies.py:20` still writes the literal path `docs/checked-documents.txt`. No criterion covers it, so I left it.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I built nothing. The story only repairs tests, and the tester already made every change (journal 8). The Interface says no module under `src/` changes. `git diff main -- src` is empty and the working tree is clean.

    I ran `make check` in the foreground and it is green: `test: green (104.8 s)`, `check: green`, with total coverage at 99.22 %. I spot-checked criterion 1: `grep -c ELAPSED_BOUND_SECONDS tests/shared/adapters/test_document_examples.py` prints `0`. I also spot-checked criterion 2: the smoke grep prints only `tests/support/check_documents_support.py:1`.

    Main choice: I left the tests exactly as the tester wrote them and changed no code. The alternative I rejected was touching `src/` to tidy anything, which the Interface forbids.

    Refactor step: there is no diff of mine to refactor, so nothing changed.

    The journal did not change the meaning of the task after intake rewrote the Description, so I left the Description as it is.

    Noticed but not touched: as the tester said, `tests/entry/test_check_documents_copies.py:20` still writes the literal `docs/checked-documents.txt`. No criterion covers it, and coders never edit tests.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
11. factory: started review as vm.
12. reviewer: no findings

    I read the diff (tests only, `git diff main...HEAD -- src` is empty) against the seven criteria and the Interface:
    - Criterion 1: `tests/shared/adapters/test_document_examples.py:60`. The shared `runner` fixture now uses `ROOMY_LIMIT`. Only the time-limit test at `:113` builds its own runner with `SHORT_LIMIT_SECONDS`, and its elapsed check at `:125` uses `ROOMY_BOUND_SECONDS`. `ELAPSED_BOUND_SECONDS` is gone. The past-the-limit row of the folder-removal test (`sleep 30`) is still killed, now at 10 s, and it has no elapsed bound of its own. `test_a_runner_built_with_its_defaults_gives_each_command_60_seconds` builds no runner.
    - Criterion 2: `Report (not checked yet):` now appears under `tests/` only at `tests/support/check_documents_support.py:22`. The four entry modules import `REPORT_HEADING` from there.
    - Criterion 3: `CHECKED_LIST` is replaced by `CHECKED_DOCUMENTS` (`src/factory/shared/domain/documents.py:558`, the same string). The file holds no `docs/checked-documents.txt` literal.
    - Criterion 4: `SETTINGS_FILE` is imported from `factory.hosting.adapters.instance_fixture` (`:25`, `"factory.env"`). No local literal remains.
    - Criterion 5: no test was renamed. The tester's run and the coder's `make check` passed (journal 8, journal 10: `check: green`).
    - Architecture and security: no code under `src/` changed, and no marker that silences a check was added. Quality: nothing found. Hygiene: journals 8 and 10 explain the work, and `docs: none` fits a story that changes only tests.
    - Out of scope: `tests/entry/test_check_documents_copies.py:20` still writes the literal `docs/checked-documents.txt`. No criterion covers it. The tester and the coder both named it.

    description corrected: "with `REPORT_HEADING` repeated in two more entry tests" -> "with `REPORT_HEADING` defined again in `tests/entry/test_check_documents_copies.py` and written inline in two more entry tests"

    Earlier tests:
    - tests/shared/adapters/test_document_examples.py: the human's leave, feature decision 6 (S0012: the example runner's tests take `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS`)
    - tests/entry/test_check_documents_checked_files.py: the standing leave to move a shared test helper (`REPORT_HEADING`), plus the human's leave in feature decision 6 and journal 4 answers 1 and 2 (the `CHECKED_DOCUMENTS` import)
    - tests/entry/test_check_documents_copies.py: the standing leave to move a shared test helper (`REPORT_HEADING`), plus journal 4 answer 3
    - tests/entry/test_check_documents_operator_guide.py: the human's leave, journal 4 answer 3 and feature decision 6 (inline literal replaced by the shared constant)
    - tests/entry/test_check_documents_references.py: the human's leave, journal 4 answer 3 and feature decision 6 (inline literal replaced by the shared constant)
    - tests/hosting/adapters/test_instance_fixture.py: the human's leave, journal 4 answer 1 and feature decision 6 (`SETTINGS_FILE` imported)
    - tests/support/check_documents_support.py: the standing leave to move a shared test helper (`REPORT_HEADING` added as the shared place)
