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
