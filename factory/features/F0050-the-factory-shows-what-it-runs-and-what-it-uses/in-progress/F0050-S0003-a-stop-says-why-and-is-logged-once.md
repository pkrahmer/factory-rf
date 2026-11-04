---
stage: intake
blocked: null
round: 0
attempts: 0
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
---

# A stop says why, and is logged once

## Description

Two things this week made the factory's stops hard to read from a distance. First, twice a restart of `factory@vm` cut off a probe of `main` that was running (2026-11-04 at 00:59 and 02:19 UTC), and each left the stop `main_branch_failing` with an empty detail, which cleared a few seconds later after the restart. The stop was not true: `main` was green, and the probe had only been killed. An empty detail also hides the cause of a stop that is true. Second, a stop that stands writes its log line again at every iteration: during a remote outage the log repeats `stop repository fetch_failed: ...` every few seconds and buries the other lines, although the stop records already note only its first raise and its clear. This story makes a stop say why, keeps a stop that the factory's own shutdown caused from being raised at all, and writes a stop's line only when something changes.

## Interface

- A stop's detail is never empty. Where a failed command gave no text, the detail names the command and how it ended: its exit status, or the signal that ended it, and that it printed nothing (for example `make lint ended by signal 15 and printed nothing`). The coder decides where this is filled in; no stop with an empty or blank detail reaches the log, the health status or the stop records.
- A command that is ended because the factory itself is stopping (the service manager's stop, `SIGTERM` to the factory) is not judged: it raises no stop, writes no preflight stamp and records nothing as failed. The next start probes again.
- `StopService.raise_stop` writes the line `stop <scope> <reason>: <detail>` only when the stop does not stand yet, or stands with another detail; a raise of the same stop with the same detail writes nothing to the log. The health status and the stop records behave as today. `stop cleared <reason>` stays as it is.

## Acceptance criteria

1. A failed probe of `main` whose output is empty raises `main_branch_failing` with a detail that names the command and its exit status or signal. Rows: an exit status with no output, a signal with no output, output of blanks only.
2. A probe of `main` that is cut off by the factory's own stop raises no `main_branch_failing`, writes no stamp with `main_failed`, and the next start runs the probe again.
3. A stop raised on three iterations in a row with the same detail writes its log line once; a raise with another detail writes it again; after a clear, the next raise writes it again. Rows: same detail, other detail, raise after clear.
4. The health status and the stop records are unchanged by criterion 3: the health status holds the newest detail, and the records note the first raise and the clear.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`: in the section on stops, that a stop's detail always says why, that a command cut off by the factory's own stop is not judged, and that a standing stop writes its log line once and again only when its detail changes. `docs/decisions.md`: one entry with the reason (two stops of this week with an empty detail that were caused by a restart; the log's repetitions during an outage). `README.md` and the project guide: none.

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
