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
  instance: self
  stage: intake
  started_at: '2026-10-21T01:53:58.588297Z'
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
3. The changed tests keep what they check: `test_crash_is_handled`, `test_expired_shares_the_crash_handler`, the other tests of the five modules and `tests/application/test_dispatcher.py` pass, and no module under `tests/` names `NOT_YET_HANDLED`.
4. `make check` stays green.
5. docs: `docs/project-guide/watching.md`, the paragraph on `NOT_YET_HANDLED`: removed; in its place one sentence that every `EventKind` has a handler in `build_handlers`, that a new kind adds its handler there, that `test_every_kind_has_a_handler_and_acceptance_due_opens_the_acceptance` fails until it does, and that the dispatcher counts an event of a kind without a handler as an error (`UnhandledEvent`). `docs/operator-guide.md`, the sentence that names `NOT_YET_HANDLED` as empty: "every kind of event has a handler" stays, the clause on `NOT_YET_HANDLED` goes. `docs/decisions.md`, the entry *The handlers are built from the loaded definition on every tick, and a constant lists the kinds still unhandled*: one line, dated with the story, that the constant was removed once every kind had a handler, because the comparison of the handlers' keys with every kind catches a new kind without it. `README.md`: none.

## Smoke test

```bash
uv run python -c 'import factory.entry.wiring as w; print(hasattr(w, "NOT_YET_HANDLED"), "NOT_YET_HANDLED" in w.__all__)'
grep -rl --include='*.py' 'NOT_YET_HANDLED' src tests | wc -l
```
Expect: two lines, `False False` and `0` (before the story, `True True` and `6`)

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
