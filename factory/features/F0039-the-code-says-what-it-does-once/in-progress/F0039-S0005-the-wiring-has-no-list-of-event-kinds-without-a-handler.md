---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 384
comments_read: [6306079635]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-21T01:59:44.200914Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T01:53:58.582622Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T01:53:58.588297Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-21T01:54:15.514844Z'
  stage: intake
  run: fc8ab75cc0294e95af850cf25b5e6a28
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-21T01:55:33.124345Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-21T01:55:51.349620Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-21T01:56:06.453717Z'
  stage: intake
  run: fe35aa9fceec4cf7b8262c655861bb80
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-21T01:56:26.749375Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-21T01:59:23.594121Z'
  stage: tests
  run: f0735f3ce93947bcaea3a76acd9df5b5
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-21T01:59:44.200914Z'
  stage: doing
---

# The wiring has no list of event kinds without a handler

## Description

`NOT_YET_HANDLED` in `factory.entry.wiring` lists the event kinds that `build_handlers` has no handler for. It was added while the handlers were being built, so that a growing build named what was missing (the decision log's *The handlers are built from the loaded definition on every tick, and a constant lists the kinds still unhandled*). Every kind has had a handler since the acceptance handlers landed, so the constant is always `()`, and five tests compare it with an empty set under names that claim more. A new `EventKind` without a handler is already caught by `test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance`, which compares the handlers' keys with every kind. This story removes the constant and its export. The tester first removes its uses from the five tests, under the human's leave (the feature's decision 7): one line goes from the acceptance test, two tests that only repeat it go, and two keep their other checks under shorter names. Unchanged: `build_handlers`, the dispatcher's error for a kind without a handler (`UnhandledEvent`), and `unhandled_kinds` with its test and its line in `security/duplicates-baseline.txt`.

## Interface

`src/factory/entry/wiring.py` (`entry`):

- `NOT_YET_HANDLED`, its comment and its entry in `__all__` are removed. Nothing else in the module changes.

Tests (the tester changes them first, under the feature's decision 7; each test keeps every line not named here, and each module drops the imports nothing uses any more, such as `get_args`, `EventKind` and `unhandled_kinds`):

- `tests/entry/test_wiring_acceptance.py::test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance`: the line `assert NOT_YET_HANDLED == ()` and the import of `NOT_YET_HANDLED` go; the test keeps its name and its checks that `set(handlers) == set(get_args(EventKind))`, that `unhandled_kinds(handlers) == []` and that `acceptance_due` has an `AcceptanceDueHandler`.
- `tests/entry/test_wiring_handlers.py::test_the_kinds_without_a_handler_are_exactly_those_not_yet_handled`: removed, with the import of `NOT_YET_HANDLED` (and of `unhandled_kinds` when nothing else in the module uses it).
- `tests/entry/test_wiring_human_handlers.py::test_the_kinds_not_yet_handled_are_exactly_the_kinds_without_a_handler`: removed, likewise.
- `tests/entry/test_wiring_recovery.py::test_crash_is_handled_and_the_kinds_not_yet_handled_are_the_kinds_without_a_handler`: renamed `test_crash_is_handled`; it keeps `assert "crash" in handlers` and loses its two `NOT_YET_HANDLED` lines and the `every` tuple.
- `tests/entry/test_wiring_recovery_expired.py::test_expired_shares_the_crash_handler_and_is_no_longer_listed_as_unhandled`: renamed `test_expired_shares_the_crash_handler`; it keeps its two `RecoveryHandler` checks and loses its two `NOT_YET_HANDLED` lines and the `every` tuple.
- `tests/entry/test_wiring_constants.py` (new): criteria 1 and 2.

## Acceptance criteria

1. `factory.entry.wiring` no longer offers the constant (rows of one parametrized test): `hasattr(factory.entry.wiring, "NOT_YET_HANDLED")` is `False`, and `"NOT_YET_HANDLED"` is not in `factory.entry.wiring.__all__`; each of the 23 other names of `__all__` on `main` of 2026-10-20 (`CREDENTIAL_HELPER`, `agent_environment`, `agent_run_environment`, `boundaries_from_environment`, `build_bill_service`, `build_boundaries`, `build_handlers`, `build_preflight`, `build_tick`, `build_work_item_reader`, `git_environment`, `git_options`, `handler_factory`, `health_store`, `leftovers_command`, `machine_extras`, `machine_log`, `production_environment`, `project_command_environment`, `read_environment_settings`, `read_hosting_token`, `repository_name`, `system_clock`) is still in it and an attribute of the module; a name another story adds to `__all__` after that needs no row.
2. A kind without a handler is still caught: `test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance` passes, and with the `acceptance_due` handler left out of the mapping, the same comparison `set(handlers) == set(get_args(EventKind))` is `False` and `unhandled_kinds(handlers)` is `["acceptance_due"]` (rows of one parametrized test in `tests/entry/test_wiring_constants.py`: the built mapping, and the built mapping without `acceptance_due`).
3. The changed tests keep what they check: `test_crash_is_handled`, `test_expired_shares_the_crash_handler`, the other tests of the five modules and `tests/application/test_dispatcher.py` pass, and no module under `tests/` except `tests/entry/test_wiring_constants.py` names `NOT_YET_HANDLED`.
4. `make check` stays green.
5. docs: `docs/project-guide/watching.md`, the paragraph on `NOT_YET_HANDLED`: removed; in its place one sentence that every `EventKind` has a handler in `build_handlers`, that a new kind adds its handler there, that `test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance` fails until it does, and that the dispatcher counts an event of a kind without a handler as an error (`UnhandledEvent`). `docs/operator-guide.md`, the sentence that names `NOT_YET_HANDLED` as empty: "every kind of event has a handler" stays, the clause on `NOT_YET_HANDLED` goes. `docs/decisions.md`, the entry *The handlers are built from the loaded definition on every tick, and a constant lists the kinds still unhandled*: one line, dated with the story, that the constant was removed once every kind had a handler, because the comparison of the handlers' keys with every kind catches a new kind without it. `README.md`: none.

## Smoke test

```bash
uv run python -c 'import factory.entry.wiring as w; print(hasattr(w, "NOT_YET_HANDLED"), "NOT_YET_HANDLED" in w.__all__)'
grep -rl --include='*.py' 'NOT_YET_HANDLED' src tests | wc -l
```
Expect: two lines, `False False` and `1` (before the story, `True True` and `6`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: 1. Criterion 1 and criterion 3 contradict each other, and so do criterion 1 and the smoke test. Criterion 1 has the new `tests/entry/test_wiring_constants.py` check `hasattr(factory.entry.wiring, "NOT_YET_HANDLED")` and `"NOT_YET_HANDLED" not in __all__`. That module has to contain the string `NOT_YET_HANDLED`. Criterion 3 says "no module under `tests/` names `NOT_YET_HANDLED`", and the smoke test expects `grep -rl --include='*.py' 'NOT_YET_HANDLED' src tests | wc -l` to print `0`. It would print `1`, because of the new module. Options:
      (a) Allow the new module as the one exception. Criterion 3 becomes "no module under `tests/` except `tests/entry/test_wiring_constants.py` names it", and the smoke test expects `1` (before the story: `6`). I would choose this.
      (b) Keep the `0` and have the test build the name without spelling it, for example from `"NOT_YET_" + "HANDLED"`. The test is then harder to read for no gain.
      (c) Drop the `NOT_YET_HANDLED` row from criterion 1 and keep only the check on the 23 other names. Nothing then tests that the constant is gone.
      Please say which, and I will carry it into criterion 3 and the smoke test's `Expect:` line.

   The other checks found nothing else:
   - The Interface is concrete: one module, one removal.
   - Every other criterion is testable by one test function.
   - The failing side of the handler-coverage rule has its own row (criterion 2).
   - The smoke test commands run.
   - The architecture is respected: `factory.entry.wiring` only loses a constant.
   - The scope is within F0039, and `unhandled_kinds` stays as the feature's Out of scope says.
   - The test changes are covered by decision 7, which the human granted.
4. 2026-10-21 human: Answer (2026-10-21): (a). Criterion 3 reads "no module under `tests/` except `tests/entry/test_wiring_constants.py` names `NOT_YET_HANDLED`", and the smoke test expects `1` (before the story, `6`).
5. factory: started intake as self.
6. intake: accepted. The human's answer (a) in journal entry 4 is carried in: criterion 3 now reads "no module under `tests/` except `tests/entry/test_wiring_constants.py` names `NOT_YET_HANDLED`", and the smoke test's `Expect:` line now says `False False` and `1` (before the story, `True True` and `6`). That is the only change to the story.
   - Interface: concrete. It names one module, `src/factory/entry/wiring.py`, and one removal (the constant, its comment and its `__all__` entry). It names each of the five tests to change with the exact lines and the new names, and the new module `tests/entry/test_wiring_constants.py`.
   - Criteria: each is testable by one test function, or by one parametrized test where the story says so. Criterion 1 has rows for the removed name and for each of the 23 others. Criterion 2 covers both sides of the handler-coverage rule: the built mapping, and the mapping without `acceptance_due`, which gives `["acceptance_due"]`. Criterion 3 keeps the changed tests' checks. Criteria 4 and 5 are the two closing ones. The Interface states no behaviour beyond the removal.
   - Smoke test: both commands run. The `Expect:` line is now consistent with criterion 3. It does not run pytest, so the `-q` rule does not apply.
   - Architecture: respected. `factory.entry.wiring` only loses a constant, and no layer or interface changes.
   - Scope: within F0039's scope for S0005. `unhandled_kinds`, `UnhandledEvent` and the duplicates baseline line stay, as the feature's Out of scope says. The test changes are covered by the feature's decision 7, which the human granted.
7. factory: started tests as self.
8. tester: Changed the five earlier test modules as the Interface says, under the feature's decision 7. Then wrote the new module for criteria 1 and 2.

   - criterion 1: tests/entry/test_wiring_constants.py::test_the_wiring_offers_its_names_but_no_list_of_kinds_without_a_handler. It is parametrized: one row for `NOT_YET_HANDLED`, which must be neither an attribute nor in `__all__`, and one row for each of the 23 names that must stay. The names that came into `__all__` later (`FRESH_HOME_MODULE`, `UV_CACHE_FOLDER`, `agent_home_of`, `fresh_home_command`) have no row, as the criterion allows.
   - criterion 2: tests/entry/test_wiring_constants.py::test_a_kind_without_a_handler_is_caught_by_comparing_the_handlers_with_every_kind. Rows `built` (comparison true, `[]`) and `no-acceptance-due` (comparison false, `["acceptance_due"]`). It also relies on tests/entry/test_wiring_acceptance.py::test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance passing.
   - criterion 3: tests/entry/test_wiring_recovery.py::test_crash_is_handled, tests/entry/test_wiring_recovery_expired.py::test_expired_shares_the_crash_handler, and the rest of the five modules and of tests/application/test_dispatcher.py. Only tests/entry/test_wiring_constants.py under `tests/` still names `NOT_YET_HANDLED` (checked with grep).
   - criteria 4 and 5: no test (`make check`, docs).

   Files created: tests/entry/test_wiring_constants.py.

   Earlier test files changed (feature decision 7, as the Interface names them):
   - tests/entry/test_wiring_acceptance.py: removed the `NOT_YET_HANDLED` line and its import.
   - tests/entry/test_wiring_handlers.py: removed `test_the_kinds_without_a_handler_are_exactly_those_not_yet_handled` and the imports of `NOT_YET_HANDLED` and `unhandled_kinds`.
   - tests/entry/test_wiring_human_handlers.py: removed `test_the_kinds_not_yet_handled_are_exactly_the_kinds_without_a_handler` and the imports of `NOT_YET_HANDLED`, `unhandled_kinds` and `get_args`.
   - tests/entry/test_wiring_recovery.py: renamed the test to `test_crash_is_handled`, removed its two `NOT_YET_HANDLED` lines and the `every` tuple, and dropped `get_args`.
   - tests/entry/test_wiring_recovery_expired.py: renamed the test to `test_expired_shares_the_crash_handler`, removed its two `NOT_YET_HANDLED` lines and the `every` tuple, and dropped `get_args` and `EventKind`.

   `make test` result: every module imports. The one failure is the `NOT_YET_HANDLED` row of criterion 1 (`assert True is False`), which fails for the right reason because the constant still exists. The other rows pass already, since this story only removes the constant. `make lint` is green.

   `lint`: lint: green (0.5 s)
   `test`: FAILED tests/entry/test_wiring_constants.py::test_the_wiring_offers_its_names_but_no_list_of_kinds_without_a_handler[NOT_YET_HANDLED] - AssertionError: assert True is False
9. factory: started doing as self.
