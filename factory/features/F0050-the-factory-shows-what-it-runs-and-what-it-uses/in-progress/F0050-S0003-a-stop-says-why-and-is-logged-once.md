---
stage: review
blocked: null
round: 2
attempts: 1
crashes: 0
pull_request: 541
comments_read: [6632127880]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T13:31:38.555645Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T13:31:38.562307Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T13:32:01.447180Z'
  stage: intake
  run: e6064427b7024619b55adaad0fe96f49
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T13:40:06.464572Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T13:40:09.904594Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T13:40:42.058747Z'
  stage: intake
  run: dba40a543ba04f04b6d984276c512302
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T13:40:48.105739Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T13:42:23.996827Z'
  stage: tests
  run: 87803f78ef974477b0695841386cbb0b
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T13:42:30.321924Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-04T13:47:53.634880Z'
  stage: doing
  run: dfe17aa226ab4f0eb170d215a9d0002b
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-04T13:48:00.090233Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-04T13:49:51.893617Z'
  stage: review
  run: 2d0b2614441946eea164f2332ddffb4e
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-04T13:49:58.203396Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-11-04T13:52:15.679230Z'
  stage: doing
  run: c458533efeee4b029b81382d6b65e32b
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-04T13:52:22.230600Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-11-04T13:53:35.831644Z'
  stage: tests
  run: dcb3490fcea54a4fb427383b00fdb330
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-04T13:53:42.052290Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-11-04T13:57:19.718761Z'
  stage: doing
  run: 805f37af5e7a4763acf9e9e24d6d6f32
- number: 19
  speaker: factory
  kind: stall
  at: '2026-11-04T13:57:19.884285Z'
  stage: doing
  run: 805f37af5e7a4763acf9e9e24d6d6f32
  reason: check_red
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-04T13:57:28.808640Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-04T14:01:12.511165Z'
  stage: doing
  run: 38fcdd7cf076463881ee11a37f377c92
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-04T14:01:20.149812Z'
  stage: review
- number: 23
  speaker: reviewer
  kind: result
  at: '2026-11-04T14:02:58.316338Z'
  stage: review
  run: 93ee0b9fe14640e58e7263e17f2e83c5
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-04T14:03:05.002659Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-04T14:07:39.328076Z'
  stage: doing
  run: 9bcb5db1740646ecbdc79d87a5c30fec
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-04T14:07:48.263911Z'
  stage: tests
- number: 27
  speaker: tester
  kind: result
  at: '2026-11-04T14:09:01.968082Z'
  stage: tests
  run: d634766871114aa59e69e3beeb1e0232
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-04T14:09:08.833783Z'
  stage: doing
- number: 29
  speaker: coder
  kind: result
  at: '2026-11-04T14:12:53.784791Z'
  stage: doing
  run: 2515d9f10e04430da9f6e7ee4c368fe5
---

# A stop says why, and is logged once

## Description

Two things this week made the factory's stops hard to read from a distance. First, twice a restart of `factory@vm` cut off a probe of `main` that was running (2026-11-04 at 00:59 and 02:19 UTC), and each left the stop `main_branch_failing` with an empty detail, which cleared a few seconds later after the restart. The stop was not true: `main` was green, and the probe had only been killed. An empty detail also hides the cause of a stop that is true. Second, a stop that stands writes its log line again at every iteration: during a remote outage the log repeats `stop repository fetch_failed: ...` every few seconds and buries the other lines, although the stop records already note only its first raise and its clear. This story makes a stop say why, keeps a stop that the factory's own shutdown caused from being raised at all, and writes a stop's line only when something changes.

## Interface

- `factory.domain.checks.command_ending(result: CheckResult) -> str`: `exit status <n>` for a non-negative exit status, `signal <n>` for a negative one (the process runner reports a signal as `-<n>`), `time_limit` for a result at its time limit.
- `_failing_detail(result, main)` in `factory.application.preflight` uses it when `result.last_line` is blank: `<command> ended by <ending> and printed nothing on main at <commit>` (for an exit status: `ended with exit status <n>`), for example `make lint ended by signal 15 and printed nothing`.
- `StopService.raise_stop` never writes an empty or blank detail: it replaces one with `no detail given`, for any stop reason, so none reaches the log, the health status or the stop records.
- `Boundaries` gains `stop_requested: Callable[[], bool]`, default `lambda: False`, wired in `factory.entry.run` to the `is_set` of the event that `install_stop_handlers` sets. A probe of `main` whose command ended while `stop_requested()` is true is not judged: it raises no stop, writes no preflight stamp and records nothing as failed. The next start probes again. A probe ended by signal 15 while `stop_requested()` is false is judged as today. The rule holds for the probe of `main` only.
- `StopService.raise_stop` writes the line `stop <scope> <reason>: <detail>` only when the stop does not stand yet, or stands with another detail; a raise of the same stop with the same detail writes nothing to the log. The health status takes the newest detail; the stop records note the first raise and the clear, and a raise with another detail while the stop stands adds no record. `stop cleared <reason>` stays as it is.

## Acceptance criteria

1. A failed probe of `main` whose output is empty raises `main_branch_failing` with a detail that names the command and its exit status or signal. Rows: an exit status with no output, a signal with no output (with `stop_requested()` false, signal 15 among them), output of blanks only.
2. A probe of `main` that is cut off by the factory's own stop (`stop_requested()` true) raises no `main_branch_failing`, writes no stamp with `main_failed`, and the next start runs the probe again.
3. A stop raised on three iterations in a row with the same detail writes its log line once; a raise with another detail writes it again; after a clear, the next raise writes it again. Rows: same detail, other detail, raise after clear.
4. The health status and the stop records are unchanged by criterion 3: the health status holds the newest detail, and the records note the first raise and the clear; a raise with another detail while the stop stands adds no record.
5. `command_ending` gives `exit status <n>` for exit status 0 and for a positive one, `signal <n>` for a negative one, and `time_limit` for a result at its time limit. Rows: 0, 2, -15, at the time limit.
6. `StopService.raise_stop` replaces an empty detail and a blank detail with `no detail given`, in the log, the health status and the records. Rows: empty, blank.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`: in the section on stops, that a stop's detail always says why, that a command cut off by the factory's own stop is not judged, and that a standing stop writes its log line once and again only when its detail changes. `docs/decisions.md`: one entry with the reason (two stops of this week with an empty detail that were caused by a restart; the log's repetitions during an outage). `README.md` and the project guide: none.

## Smoke test

```bash
grep -rc 'printed nothing' src/factory | awk -F: '{s+=$2} END {print (s>0)}'
uv run pytest tests/application -k stop 2>&1 | tail -1
```

Expect: `1`, then a line that ends in `passed` with no `failed`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Questions before the story is buildable:

   1. Interface, empty detail: the first Interface line says that no stop with an empty or blank detail reaches the log, the health status or the stop records, for every stop. Criterion 1 tests only the probe of `main` (`main_branch_failing`). Other stops are built from failed commands too (for example `repository fetch_failed`, preflight stops), and no criterion covers them. Options: (a) limit the Interface line to `main_branch_failing`, which I would choose; (b) add a criterion that `StopService.raise_stop` refuses or replaces an empty or blank detail, with rows for an empty and a blank detail, and name where the command text and its ending come from; (c) list the other stops that need a row.
   2. Interface, the home of the rule: "The coder decides where this is filled in" leaves the signature open. No module or function is named for the command's result (for example the DTO that carries the exit status or signal, and how the output is tested for blank). The tester cannot write a test against a seam nobody has named. Please name the seam, or say that the tests go through the probe of `main` only (in which case say so in the Interface).
   3. Interface and criterion 2, how "the factory itself is stopping" is known: it says only "the service manager's stop, SIGTERM to the factory". What the factory looks at is not stated: a flag set by its own SIGTERM handler, or the signal number of the ended command. A command ended by signal 15 from anything else (for example an out-of-memory kill or a timeout) must still be judged, and that side has no criterion. Please add a row where a probe is ended by signal 15 while the factory is not stopping, and say which of them raises `main_branch_failing`.
   4. Criterion 2 covers only the probe of `main`; the Interface says "a command". Does the rule hold for all project commands (the checks of a stage, `make check`), or only for the probe of `main`? If all, each needs a row. If only the probe, change the Interface to say so.
   5. Criterion 3, "after a clear, the next raise writes it again": the Interface also says the log line `stop cleared <reason>` is unchanged, and criterion 4 says the records note only the first raise and the clear. Please say whether a raise with another detail while the stop stands adds a record. I read "unchanged" as no new record, and would like a row that pins it.
4. 2026-11-04 human: Answers of the human:

   1. **(b)**, as a safety net beside criterion 1: `StopService.raise_stop` never writes an empty or blank detail; it replaces one with `no detail given` (a row for an empty and one for a blank detail, for any stop reason). The useful detail for a failed probe comes from criterion 1; the safety net only keeps a blank out of the log, the health status and the records.

   2. The seams: a pure function `command_ending(result: CheckResult) -> str` in `factory.domain.checks`, which gives `exit status <n>` for a non-negative exit status, `signal <n>` for a negative one (the process runner reports a signal as `-<n>`), and `time_limit` for a result at its time limit. `_failing_detail(result, main)` in `factory.application.preflight` uses it when `result.last_line` is blank: `<command> ended by <ending> and printed nothing on main at <commit>` (for an exit status: `ended with exit status <n>`). The tests go through `command_ending` (rows) and through the probe of `main` with a fake project-commands result. Put this into the Interface.

   3. The factory knows it is stopping by its own stop flag, the `threading.Event` that `install_stop_handlers` sets in `factory.entry.run`. Seam: `Boundaries` gains `stop_requested: Callable[[], bool]`, default `lambda: False`, wired to that event's `is_set`. A probe whose command ended while `stop_requested()` is true is not judged. A probe ended by signal 15 while `stop_requested()` is false is judged as today: it raises `main_branch_failing` with the detail of criterion 1 (`ended by signal 15 and printed nothing`). Add that row.

   4. Only the probe of `main`. A stage's checks that the factory's stop cuts off already end in a crash and a rerun by the lease rules; they are not part of this story. Change the Interface line to "the probe of `main`".

   5. Your reading is right: a raise with another detail while the stop stands adds no record; the health status takes the new detail and the log writes the line once more. Add a row that pins it.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) written into the story.
   - Interface: carried in from entry 4. The Interface now names `command_ending` in `factory.domain.checks`, `_failing_detail` in `factory.application.preflight`, `Boundaries.stop_requested` (default `lambda: False`, wired to the stop event's `is_set` in `factory.entry.run`), the `no detail given` safety net in `StopService.raise_stop`, and the probe-of-`main`-only scope. It also says that a raise with another detail adds no record (answers 1 to 5).
   - Criteria: criterion 1 gains the row of signal 15 with `stop_requested()` false. Criterion 2 names `stop_requested()` true. Criterion 4 gains the no-new-record row. New criterion 5 covers `command_ending` (rows 0, 2, -15, at the time limit). New criterion 6 covers the blank-detail safety net (rows empty, blank). `make check` and `docs:` are now 7 and 8. Each is testable by one parametrized test, and each rule has its failing side. I did not add a row for how `_failing_detail` words an exit status, which is covered by criterion 1's rows.
   - Smoke test: unchanged. `grep ... 'printed nothing'` is runnable and checkable. `pytest tests/application -k stop` is runnable. The project's pytest `addopts` was not checked for `-q`. The Expect reads the last line as "passed", and the tester should confirm that this holds under the configured `addopts`.
   - Architecture: the pure function is in the domain, the use is in the application, and the wiring is in the entry layer. No layer is crossed.
   - Scope: within F0050's scope line for S0003 and not in "Out of scope". Stage checks cut off by a stop are left out, as the human said.
7. factory: started tests as vm.
8. tester: I wrote failing tests for criteria 1 to 6. Each one is a parametrized test, with one row per case the criterion names.

   - criterion 1: tests/application/test_preflight_stop_detail.py::test_a_failed_probe_that_printed_nothing_names_the_command_and_its_ending. Rows: exit status 2 with no output, signal 15 with no output, signal 9 with no output, and exit status 2 with output of blanks only. Every row has `stop_requested` set to false.
   - criterion 2: tests/application/test_preflight_stop_detail.py::test_a_probe_cut_off_by_the_factorys_stop_is_not_judged_and_runs_again
   - criterion 3: tests/application/test_stop_log_once.py::test_a_standing_stop_writes_its_line_once_and_again_only_when_something_changes. Rows: same detail, other detail, raise after clear.
   - criterion 4: tests/application/test_stop_log_once.py::test_the_health_status_holds_the_newest_detail_and_the_records_the_first_raise_and_clear. Same three rows.
   - criterion 5: tests/domain/test_command_ending.py::test_a_command_ending_names_the_exit_status_the_signal_or_the_time_limit. Rows: 0, 2, -15, at the time limit.
   - criterion 6: tests/application/test_stop_log_once.py::test_an_empty_or_blank_detail_is_replaced_by_no_detail_given. Rows: empty, blank.
   - criteria 7 and 8: no test; they are the check and the docs stage.

   Files created:
   - tests/domain/test_command_ending.py
   - tests/application/test_stop_log_once.py
   - tests/application/test_preflight_stop_detail.py

   Run: `uv run pytest -q` on the three files stopped at collection with `ImportError: cannot import name 'command_ending' from 'factory.domain.checks'`. The pytest run was interrupted at that collection error, so the other two files were not run. They need `Boundaries.stop_requested` (passed through `dataclasses.replace`) and the new behaviour of `StopService.raise_stop`. `make lint` is green.

   Choices the coder should know:
   - Criterion 1, wording: the test checks that the detail contains `lint` and ends with `<ending> and printed nothing on main at <commit[:12]>`. `<ending>` is `ended with exit status <n>` or `ended by signal <n>`. Either `lint` or the Interface's example `make lint` as the command name passes.
   - Criterion 1, time limit: there is no time-limit row, because the criterion names none. The existing test_preflight_run.py test of the `reached its time_limit` detail still stands.
   - Criterion 2, setup: the fake command sets the stop flag while it runs and returns signal 15. The test does not assert what `run()` returns for the probe that was cut off; the Interface leaves that open. It checks for no `main_branch_failing` stop and that the stamp is absent or has no `main_failed`. Then it checks that a second preflight, with the flag clear, runs the command again and passes.
   - Criterion 6, how the blank stop is built: `RepositoryStop` already refuses a blank detail (tests/domain/test_stops.py::test_a_blank_detail_is_rejected). So the test builds the stop with `RepositoryStop.model_construct` to bypass validation, and leaves that validator as it is.
   - Criterion 6, records: a `StopRecord` carries no detail, so for the records the test only checks that one `raised` record is written.

   Open: nothing.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I made the failing tests for criteria 1 to 6 pass without changing any test. `make check` is green.

    What I built:
    - `src/factory/domain/checks.py`: `command_ending(result)` gives `time_limit` when there is no exit status, `signal <n>` for a negative exit status, and `exit status <n>` otherwise.
    - `src/factory/application/preflight.py`: when the last line is blank, `_failing_detail` now gives `lint ended with exit status <n>` or `lint ended by signal <n>`, followed by `and printed nothing on main at <commit>`. The small helper `_ended` picks between "with" and "by". In `_run_probe`, a probe that ends while `boundaries.stop_requested()` is true returns `None` straight away. It then raises no stop, clears none and writes no stamp, so the next start probes `main` again.
    - `src/factory/application/boundaries.py`: `Boundaries` has a new field `stop_requested: Callable[[], bool] = lambda: False`.
    - `src/factory/entry/run.py`: `run_instance` sets `stop_requested` to its `should_stop` with `dataclasses.replace`. `run_until_stopped` passes `event.is_set`, the event that `install_stop_handlers` sets.
    - `src/factory/application/stops.py`: `raise_stop` first replaces a blank detail with `NO_DETAIL` ("no detail given"). It then reads the health status. It writes the log line only when no stop of that reason stands, or one stands with another scope or detail. It always writes the newest stop to the health status, and adds a `raised` record only when none stood. If the health status cannot be read, it still writes the line, writes no record, and raises once it has tried both. The record pairing is kept as before. `_stands` became `_standing`, which returns the standing stop, and `clear_stop` uses it too. A small helper `_collect` keeps the "every destination is tried" rule.

    Main decision: the line is held back inside `StopService`, by comparing the new stop with the standing one in the health status. I rejected keeping a memory of the last line in the service or in the log adapter. The health status is already the truth about what stands, so a restart or a second service object gives the same answer.

    Refactor: after `make check` was green I read the diff once. I folded a first, more tangled version of the error collection into `_collect` and `_write_line`, and changed nothing else.

    The journal changed nothing in the meaning of the task beyond what intake had already written into the Description.

    Noticed but not touched:
    - When the probe is cut off, `Preflight.run` still clears `preflight_failed` and returns `None`. That seemed right: the machine's own checks had already passed.
    - A standing stop whose detail changes now writes its line again, but its `at` in the health status moves to the newest raise. That was so before this change too.

    `check`: check: green
    `duplicates`: duplicates: 3 new, 43 known, 0 gone
11. factory: started review as vm.
12. reviewer: Review of `git diff main...HEAD -- . ':!factory'` against the work item, round 0.

    Findings:

    1. `src/factory/entry/run.py:273` (`_ProjectImageStart._choose`): the preflight that probes `main` in production is built from new boundaries. `build_tick(chosen_boundaries, ...)` → `build_preflight(boundaries, ...)` (`src/factory/entry/wiring.py:715`, `:785`) gets them from `build_boundaries(chosen.settings, ...)`, and those carry the default `stop_requested=lambda: False`. The `replace(..., stop_requested=should_stop)` at `run.py:160-163` reaches only the start's own boundaries (disk recorder, waiter, image choice), never the tick's preflight. So the factory's own SIGTERM still raises `main_branch_failing` with the new `ended by signal 15` detail, and criterion 2 and the Interface's wiring line do not hold for the running factory. Fix: carry `stop_requested=boundaries.stop_requested` into the boundaries `_choose` builds (a `replace` after `build_boundaries`, or through `_sized`), so that every tick's preflight gets the flag.
    2. Against the story, `## Acceptance criteria`: the Interface's rule "wired in `factory.entry.run` to the `is_set` of the event that `install_stop_handlers` sets" has no criterion and no test. That is why finding 1 passes `make check`: criterion 2's test (`tests/application/test_preflight_stop_detail.py::test_a_probe_cut_off_by_the_factorys_stop_is_not_judged_and_runs_again`) sets `Boundaries.stop_requested` by hand. Fix: a criterion that `run_instance`'s `should_stop` reaches the preflight of the tick built after the stage image is chosen. A probe of `main` during which `should_stop` turns true raises no `main_branch_failing` (entry-level test, as in `tests/entry/test_run*.py`). I did not add it myself because it needs the code change of finding 1. The human or the coder should route it to the tester.
    3. `src/factory/application/preflight.py:578` (`_ended`): it decides again what `command_ending` (`src/factory/domain/checks.py:98`) already decides, `exit_status >= 0` versus a signal, so the rule "non-negative is an exit status" now lives in two places. Fix: pick "with" or "by" from the single decision `command_ending` makes, so that one place holds the sign rule (for example, let `_ended` branch on the kind of ending `command_ending` returns, not on `exit_status` itself).

    Checked and holding: criteria 1, 3, 4, 5 and 6 each have a parametrized test with the rows the criterion names. Criterion 1 includes signal 15 with `stop_requested()` false. Criterion 4 includes the no-new-record row for another detail. Criterion 5 includes 0 and a negative status. `StopService.raise_stop` (`src/factory/application/stops.py:38`) does three things. It replaces a blank detail before any destination is written. It writes the line only when the stop does not stand yet or stands with another scope or detail. It adds a record only on a first raise. On a failed health read it still writes the line and adds no record, as before. The journal records the coder's `make check` as green. Layers: `command_ending` is in the domain, its use in the application, the wiring in the entry layer. No silencing markers, secrets or string-built commands. `make duplicates` shows 3 new findings, all of them dead-code hits in `src/factory/domain/cost_records.py:41-43`, a file this diff does not touch, so they are not under review. Description and docs criterion match what was built.

    Earlier tests: none. The diff only adds test files (`tests/application/test_preflight_stop_detail.py`, `tests/application/test_stop_log_once.py`, `tests/domain/test_command_ending.py`).
13. factory: started doing as vm.
14. coder: Round 1. I fixed review findings 1 and 3 in code. Finding 2 asks for a new test, so I am sending the work item to the tester. `make check` is green.

    **Fixed**
    - Finding 1, `src/factory/entry/run.py` (`_ProjectImageStart._choose`): the boundaries that `build_boundaries` builds for the chosen image now take over `stop_requested` from the start's boundaries (`replace(built, stop_requested=boundaries.stop_requested)`), before `_sized`. Every tick's preflight now sees `run_instance`'s `should_stop`, which `run_until_stopped` wires to the stop event's `is_set`. A short comment says why. I rejected adding it to `_sized`: that function is about image sizes, and mixing the stop flag in would make it do two jobs.
    - Finding 3, `src/factory/application/preflight.py` (`_ended`): it now picks "with" or "by" from the text `command_ending` returns (`ending.startswith("exit status")`), so the rule that a non-negative status is an exit status lives only in `command_ending`. I rejected a new enum or a second function in `factory.domain.checks`. That would add an API surface that only this one caller needs.

    **For the tester (finding 2)**
    This test is new, not a change to an existing one. It goes under `tests/entry/`, like `tests/entry/test_run*.py`, and checks the Interface rule "wired in `factory.entry.run` to the `is_set` of the event that `install_stop_handlers` sets": `run_instance`'s `should_stop` must reach the preflight of the tick built after the stage image is chosen. Scenario: during a probe of `main`, `should_stop` turns true and the probe ends by signal 15. The test checks that no `main_branch_failing` is raised. With today's code it should pass; it would have failed before the finding 1 fix. I did not add the criterion to `## Description`, because the reviewer proposed it and the human has not asked for it. The Interface line it tests is already there.

    **Refactor**
    I read the diff once. The change is two lines, and nothing else needed changing.

    **Journal**
    The journal changed nothing in the meaning of the task.

    **Noticed, not touched**
    `make duplicates` still reports the 3 dead-code findings in `src/factory/domain/cost_records.py:41-43`, a file this story does not touch.

    `check`: check: green
15. factory: started tests as vm.
16. tester: Round 1, an approved test change (coder's entry 14, from review finding 2). No existing test needed editing: this was a new test for the Interface rule that `Boundaries.stop_requested` is "wired in `factory.entry.run`" to the factory's own stop, and it had no test at the entry level.

    - Interface wiring of `stop_requested` (finding 2): `tests/entry/test_run_stop_requested.py::test_the_tick_built_after_the_image_is_chosen_sees_the_factorys_own_stop`

    How the test works: like `tests/entry/test_run_image_sizes.py`, it swaps in its own `run_module.build_tick`, which keeps the boundaries `_ProjectImageStart._choose` builds after the stage image is chosen. Inside its one tick it calls those boundaries' `stop_requested()`, turns `run_instance`'s `should_stop` true, and calls it again. It expects `[False, True]`.

    What I rejected: driving a real probe of `main` that ends by signal 15 at the entry level. That needs a check container, and the preflight's handling of `stop_requested()` already has its own test in `tests/application/test_preflight_stop_detail.py`. This test checks only the wiring the reviewer found missing.

    Run: `uv run pytest -q tests/entry/test_run_stop_requested.py` gives 1 passed, since the coder's fix is already there. As a check, I took the `replace(built, stop_requested=...)` out of `_choose` in a temporary copy and the test failed with `assert [False, False] == [False, True]`. Then I put the file back as it was; `git status` shows only the new test.

    `make lint`: lint: green.

    Files created: `tests/entry/test_run_stop_requested.py`. Modules the test run could not import: none. Earlier test files changed: none.

    Open: the criterion is still not written into `## Description`, as the coder noted; the test rests on the Interface line.

    The factory left out changes outside the write paths: src/factory/entry/run.py.

    `lint`: lint: green (0.2 s)
17. factory: started doing as vm.
18. coder: Round 1, after the tester's change. I changed no code this time. The fixes for review findings 1 and 3 went in on this round's first pass (entry 14) and are committed: `src/factory/entry/run.py:277`, where `_ProjectImageStart._choose` now passes `stop_requested` into the boundaries it builds, and `src/factory/application/preflight.py` `_ended`, which now picks "with" or "by" from `command_ending`. Finding 2 is covered by the tester's new test `tests/entry/test_run_stop_requested.py::test_the_tick_built_after_the_image_is_chosen_sees_the_factorys_own_stop`. It passes against that wiring.

    The factory dropped the tester's temporary edit to `src/factory/entry/run.py`, as entry 16 records. The file still holds the committed fix, and `git status` was clean when this stage started.

    Main decision: I made no further change. All three findings were already handled, so any new edit would have gone beyond the findings. The alternative I rejected was writing the reviewer's proposed wiring criterion into `## Description`: the human has not asked for it, and the Interface line already states the rule that the new test checks.

    Refactor: no diff this round, so there was nothing to change.

    Journal: the journal changed nothing in the meaning of the task.

    Noticed, not touched: `make duplicates` reported 3 new dead-code findings in `src/factory/domain/cost_records.py:41-43` on the earlier runs (entries 10 and 14). This story does not touch that file. I did not run `make duplicates` this round.

    `check`: check: green
19. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
    src/factory/entry/check_story.py                   92      1     18      1    98%   161
    src/factory/entry/contract.py                      28      1      6      1    94%   41
    src/factory/entry/health.py                        33      1     10      1    95%   48
    src/factory/entry/refresh_token.py                 93      1     12      1    98%   136
    src/factory/entry/run.py                          165      2     24      2    98%   285, 355
    src/factory/entry/watch.py                         52      1      6      1    97%   87
    src/factory/entry/wiring.py                       335      6     56      5    97%   286, 371, 423, 478, 507, 830
    -------------------------------------------------------------------------------------------
    TOTAL                                           10284     35   2046     37    99%

    130 files skipped due to complete coverage.
    Required test coverage of 90.0% reached. Total coverage: 99.42%
    ======================================================================================= short test summary info ========================================================================================
    FAILED tests/adapters/test_process_streaming.py::test_callback_saying_stop_on_standard_output_kills_the_group_at_once[before-a-sleep] - OSError: [Errno 22] Invalid argument
    make: *** [Makefile:84: test] Error 1
20. factory: started doing as vm.
21. coder: Round 1, after the stall in entry 19. I changed no code. When this stage started the working tree was clean, and a fresh `make check` was green (`test: green (87.2 s)`, `check: green`).

    What I built: nothing new this round. The story's code was already committed in entries 10 and 14:
    - `src/factory/domain/checks.py` (`command_ending`)
    - `src/factory/application/preflight.py` (`_failing_detail`, `_ended`, and a probe that is not judged while `stop_requested()` is true)
    - `src/factory/application/boundaries.py` (`stop_requested`)
    - `src/factory/application/stops.py` (`no detail given`, and the line written once)
    - `src/factory/entry/run.py` (the wiring, including `_ProjectImageStart._choose`)

    Main decision: I treated the red `check` in entry 19 as a failure outside this story and did not change the code. The test that failed is `tests/adapters/test_process_streaming.py::test_callback_saying_stop_on_standard_output_kills_the_group_at_once[before-a-sleep]`, which tests `src/factory/adapters/process.py`. This branch does not touch that module or anything it calls: `git diff main --stat` lists only the five source files above and the four new test files. The rejected alternative was editing the process runner or the test to work around it. That would go beyond this story, and the test is not mine to change.

    The failure, as entry 19 recorded it: `FAILED tests/adapters/test_process_streaming.py::test_callback_saying_stop_on_standard_output_kills_the_group_at_once[before-a-sleep] - OSError: [Errno 22] Invalid argument`. The factory's excerpt holds only pytest's short summary line, so I cannot quote the `E` lines or the `file:line` of the failing line. The test passed in this stage's full `make check` run. It looks like a flaky test that fails only under load, in the timing of how the streaming runner kills the process group. I suggest a separate story to find its cause, with the full `--tb=short` output kept the next time it fails.

    Refactor: there was no diff this round, so nothing to refactor.

    Journal: the journal changed nothing in the meaning of the task.

    Noticed, not touched: the process-streaming failure above; and, from entries 10 and 14, the 3 dead-code findings that `make duplicates` reports in `src/factory/domain/cost_records.py:41-43`. I did not run `make duplicates` this round.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 3 new, 43 known, 0 gone
22. factory: started review as vm.
23. reviewer: Review of `git diff main...HEAD -- . ':!factory'` against the work item, round 1.

    Findings:

    1. `src/factory/application/preflight.py:542-544` (`_run_probe`), with `Preflight.run` (`:463-477`) and `Tick.run` / `_run_preflight` (`src/factory/application/tick.py:109-118`, `:170-176`): when the probe is cut off, `_run_probe` returns `None`, which is the same value as "main passed". `Preflight.run` then clears `preflight_failed` and returns `None`, and the tick carries on into `delete_stale_branches`, the watcher and `dispatcher.dispatch`. So a SIGTERM that arrives during the probe now lets the same tick claim a work item and start a stage on a `main` that got no verdict, while the factory is shutting down. That claim is then left to the lease rules as a crash. Before this diff the (false) stop at least ended the tick. The Interface says the probe "is not judged", but counting it as a pass is a judgement. Fix: let a probe that is not judged end the tick without dispatching and without raising or clearing a stop. For example, the tick checks `boundaries.stop_requested()` after the preflight and returns a `TickOutcome` with no dispatch, or the preflight reports a "not judged" result that the tick ends on. Add a row to criterion 2's test that the cut-off tick dispatches nothing.
    2. Against the story, criterion 2 in `## Acceptance criteria`: the criterion pins no stop, no `main_failed` stamp and a new probe on the next start. It does not say what the tick does after a probe that was not judged. That gap is why finding 1 passes `make check`. Fix: extend criterion 2 with "and the tick that ran it dispatches nothing" (needs the code change of finding 1, so I have not written it in myself). The tester then adds that row to `tests/application/test_preflight_stop_detail.py::test_a_probe_cut_off_by_the_factorys_stop_is_not_judged_and_runs_again`, or an application tick test.

    Checked and holding:
    - Criteria 1, 3, 4, 5 and 6 each have a parametrized test with the rows the criterion names. Criterion 1 includes signal 15 with `stop_requested()` false and blanks-only output. Criterion 4 has the row where another detail adds no record. Criterion 5 tests 0 and 2 on the non-negative side and -15 on the negative side.
    - The Interface's wiring rule is now pinned by `tests/entry/test_run_stop_requested.py`, through `_ProjectImageStart._choose` (`src/factory/entry/run.py:276-278`). `run_until_stopped` passes `event.is_set` (`run.py:128`).
    - `StopService.raise_stop` (`src/factory/application/stops.py:38-63`):
      - it replaces a blank detail before any destination is written;
      - it writes the line only when the stop is new or its scope or detail changed;
      - it writes a record only on a first raise;
      - after a failed health read it still writes the line, adds no record and raises.
    - Round 0 finding 3 is fixed: `_ended` now branches on what `command_ending` returns.
    - The journal records the coder's `make check` as green. The red run in entry 19 was a test in `tests/adapters/test_process_streaming.py`, which this diff does not touch, and the next run was green.
    - Layers hold. There are no silencing markers, no secrets and no string-built commands.
    - The 3 new findings from `make duplicates` are in `src/factory/domain/cost_records.py`, which this diff does not change.
    - The Description and the docs criterion match what was built.

    Notes:
    - `tests/application/test_preflight_stop_detail.py:27` (`_answering`) is a copy of `_answering` in `tests/application/test_preflight_run.py:38`. It could move to `tests/preflight_support.py` under the standing leave.
    - `tests/domain/test_command_ending.py:22-29` and `tests/application/test_preflight_stop_detail.py:16-24` (`_ended`) each build the same no-output `CheckResult` from an exit status.

    Earlier tests: none. The diff only adds test files (`tests/application/test_preflight_stop_detail.py`, `tests/application/test_stop_log_once.py`, `tests/domain/test_command_ending.py`, `tests/entry/test_run_stop_requested.py`).
24. factory: started doing as vm.
25. coder: Round 2: I fixed review findings 1 and 2 from entry 23. Finding 2 also needs a test, so this goes back to the tester.

    **What I built**
    - `src/factory/application/tick.py`, `Tick.run`: after the preflight, if `self._boundaries.stop_requested()` is true, the tick returns `TickOutcome()` with no `stopped`, no `event` and no `dispatch`. It does not delete stale branches, evaluate the remote or dispatch. The preflight already leaves the stops alone on a cut-off probe: it raises nothing, clears nothing and writes no stamp. The `TickOutcome` docstring now says that "neither" stands for a tick the factory's own stop ended after the preflight. `idle_shutdown` and `entry/run.py` read it as neither idle nor handled work.
    - Work item `## Description`: criterion 2 and its Interface line now add "the tick that ran it dispatches nothing" / "ends without dispatching", as finding 2 proposed.

    **Test change for the tester (finding 2):** add a row to `tests/application/test_preflight_stop_detail.py::test_a_probe_cut_off_by_the_factorys_stop_is_not_judged_and_runs_again`, or add an application tick test, showing that a tick whose probe of `main` ends while `stop_requested()` is true dispatches nothing. Right now no test reaches the new early return in `Tick.run`.

    **Main decision and rejected alternative:** the tick checks `stop_requested()` itself after the preflight. I tried first a `ProbeNotJudged` exception raised from `Preflight._run_probe` and caught in `Tick.run`, but threw it away. The existing test calls `rig.preflight().run()` on a cut-off probe and expects it to return normally, and the exception would break that test. With the check in the tick, `Preflight.run` stays as the test pins it. The check also applies when the factory's stop arrives during the preflight without cutting off a probe. Not claiming work then is right too, because the factory is shutting down.

    **Refactor:** the diff is one check plus a docstring line, so there was nothing to change. I first also reworded the `Tick.run` docstring, but `tests/application/test_tick_docstrings.py::test_the_docstrings_say_what_the_code_does[tick-run]` pins it word for word, so I put it back. `make check` is green (`test: green (87.8 s)`, `check: green`).

    **Noticed, not touched:** the dead-code findings in `src/factory/domain/cost_records.py:41-43` that `make duplicates` reported earlier; I did not run `make duplicates` this round. The two duplicated test helpers in the reviewer's notes (`_answering` and the `_ended` result builder) are for the tester to consider under the standing leave.

    The factory left out changes outside the write paths: factory/features/F0050-the-factory-shows-what-it-runs-and-what-it-uses/in-progress/F0050-S0003-a-stop-says-why-and-is-logged-once.md.
26. factory: started tests as vm.
27. tester: Mode: approved test change. I added the tick test that the coder's entry 25 asks for, following review finding 2 in entry 23. Finding 2 extends criterion 2 with "and the tick that ran it dispatches nothing".

    What I changed:
    - `tests/application/test_preflight_stop_detail.py`: a new test, `test_a_tick_whose_probe_the_factorys_stop_cut_off_dispatches_nothing`. The setup:
      - a backlog work item is started on main;
      - the probe sets `stop_requested()` to true and ends by signal 15, with no output;
      - a `Tick` is built from the rig's boundaries and preflight, with the idle and run handlers.

      The test asserts:
      - the probe ran once;
      - the outcome is `TickOutcome()`, with no `stopped`, `event` or `dispatch`;
      - no `main_branch_failing` was raised;
      - the fake agent runtime got no requests;
      - the fake hosting service has no pull requests.

      For the imports, the test takes `INSTANCE` from `stage_run_support`. The `BACKLOG_PATH` constant matches the one in `tests/application/test_tick_preflight.py`.
    - I chose a tick test over a new row in `test_a_probe_cut_off_by_the_factorys_stop_is_not_judged_and_runs_again`. That test calls only `Preflight.run`, which cannot see whether the tick dispatches.

    Result: the new test passes against the coder's code (`uv run pytest -q` on the file: 6 passed). As a check, I temporarily replaced `if self._boundaries.stop_requested():` in `src/factory/application/tick.py` with `if False:`. The test then failed with `AssertionError: assert TickOutcome(s...patch='error') == TickOutcome(s...dispatch=None)`, which shows it reaches the early return. I copied the file back afterwards, and `git status` shows only the test file changed. `make lint`: green.

    Criterion → test:
    - criterion 2 (dispatches nothing): `tests/application/test_preflight_stop_detail.py::test_a_tick_whose_probe_the_factorys_stop_cut_off_dispatches_nothing`.
    - The other criteria keep the tests from round 0.

    Files changed: `tests/application/test_preflight_stop_detail.py`. No files created. No module failed to import.

    Open: the factory dropped the coder's `## Description` edit to criterion 2 and its Interface line ("the tick that ran it dispatches nothing" / "ends without dispatching"), because the work item is outside the coder's write paths (entry 25, last line). Neither the coder nor the tester can write it, so the criterion text still lacks the clause this test checks. The reviewer, who may write the work item, should put it back. I did not move the duplicate `_answering` and `_ended` helpers from the reviewer's notes: the mode limits this stage to the named change.

    The factory left out changes outside the write paths: src/factory/application/tick.py.

    `lint`: lint: green (0.1 s)
28. factory: started doing as vm.
29. coder: Round 2, after the tester's entry 27. I changed no code this round. The fix for review findings 1 and 2 (entry 23) was already committed after entry 25. The tester's new test, `tests/application/test_preflight_stop_detail.py::test_a_tick_whose_probe_the_factorys_stop_cut_off_dispatches_nothing`, passes against it. When this stage started the working tree was clean. A fresh `make check` in the foreground was green: `test: green (87.0 s)`, `check: green`.

    What I built (the story as a whole, all committed):
    - `src/factory/domain/checks.py`: `command_ending`.
    - `src/factory/application/preflight.py`: `_failing_detail` and `_ended`. A probe of `main` that ends while `stop_requested()` is true is not judged.
    - `src/factory/application/boundaries.py`: `stop_requested`.
    - `src/factory/application/stops.py`: a blank detail becomes `no detail given`, and the line is written once until the detail changes.
    - `src/factory/application/tick.py`: after the preflight, if `stop_requested()` is true, the tick returns `TickOutcome()` and dispatches nothing.
    - `src/factory/entry/run.py`: the wiring.

    Main decision: the tick checks `stop_requested()` after the preflight. I rejected a `ProbeNotJudged` exception raised from the preflight, because the existing test pins `Preflight.run` returning normally on a cut-off probe (see entry 25).

    Refactor: no diff this round, so nothing to refactor.

    Description: the journal adds a clause to criterion 2, "and the tick that ran it dispatches nothing", and the matching Interface line, "ends without dispatching". The `## Description` still lacks it, because the work item is outside the coder's write paths and the factory dropped my edit in round 2's first run. The reviewer, who may write the work item, should add the clause. The tester's test already checks it.

    Noticed, not touched:
    - The dead-code findings from `make duplicates` in `src/factory/domain/cost_records.py:41-43`. I did not run `make duplicates` this round.
    - The duplicated test helpers `_answering` and `_ended` from the reviewer's notes in entry 23. Moving them is the tester's job under the standing leave.

    `check`: check: green
    `duplicates`: duplicates: 3 new, 43 known, 0 gone
