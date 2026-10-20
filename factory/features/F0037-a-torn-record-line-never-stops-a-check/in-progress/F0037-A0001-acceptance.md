---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 346
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T09:45:01.582737Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T09:51:29.242644Z'
  stage: acceptance
  run: 05f94b0e90d543a8957ce45fb4757a74
stories: [F0037-S0001]
outcome: null
---

# Acceptance of A torn record line never stops a check

## Recommendation

accepted. The one story, S0001, delivers the goal. `JsonLinesRecordLog.read` reads bytes, splits at `\n` alone and skips a line that does not decode, and the four record files are all wired through it. With real `make` and the production wiring, a torn `known-results.jsonl` line no longer stops a check. `make check` is green. The only finding is in the operator guide: its *The records* section now speaks of "the four record files" before it names three of them. Next to that sentence stands an older claim that nothing reads the records to decide anything. I propose one documentation story for that. It is not a broken promise of the feature.

## 1 Scope

None. Every Scope item has its change on `main`, all from S0001 (commits `b7cd4d55`..`a2200ce6`):
- `src/factory/adapters/record_log_jsonl.py`: `read` reads bytes, splits at `b"\n"` and decodes each line strictly in `_parse`.
- `src/factory/application/files.py`: the `RecordLog.read` docstring is the Interface's text.
- The two new test modules, plus a shared helper module `tests/torn_record_support.py`.
- The three documents.

Out of scope was kept. `KnownResults._read`, `DiskRecorder.last`, `StopPublisher.publish`, `append`, `JsonLinesCostRecordReader` and `parse_stop_records` are unchanged.

`parse_stop_records` still uses `str.splitlines`. `StopRecord` holds no free text (enums, a time, a `Name`), so U+2028 cannot occur there, and the feature was right to leave it.

The wiring (`src/factory/entry/wiring.py:264`, `:282`, `:283`, `:285`) builds all four records as `JsonLinesRecordLog`, so the one fix covers the four files. The goal "telemetry can no longer halt the factory" is reached for the decode fault. An `OSError` still propagates to `DiskRecorder.last` unguarded, as before. That is a different fault and outside this feature.

## 2 Feature smoke test

The walk-through of an operator's instance:
- a real git checkout whose `make check` prints non-ASCII text;
- `build_boundaries` from `factory.entry.wiring` with the fake hosting service and no confinement;
- the repository's real `factory/pipeline.yml`;
- `KnownResults.run("check")` three times, with a kill-torn line put into `known-results.jsonl` (cut inside `✓`) and into `project-commands.jsonl` after the first run;
- `DiskRecorder` on a `disk.jsonl` that holds a non-UTF-8 line in the middle and a torn last line;
- a torn `stops.jsonl` read through the wired log.

No paid call.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/smoke.py" <<'PY'
import os, subprocess, sys
from pathlib import Path
from factory.adapters.fake_hosting import FakeHostingService
from factory.application.disk_records import DiskRecorder
from factory.application.known_results import KnownResults
from factory.domain.command_records import CommandRecord
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries

root = Path(sys.argv[1]); checkout = root / "checkout"; state = root / "state"
checkout.mkdir(); (state / "records").mkdir(parents=True)
count = root / "runs"
(checkout / "Makefile").write_text(f"check:\n\t@echo run >> {count}\n\t@echo 'check: green ✓ – “done”'\n")
env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_AUTHOR_NAME": "s", "GIT_AUTHOR_EMAIL": "s@x",
       "GIT_COMMITTER_NAME": "s", "GIT_COMMITTER_EMAIL": "s@x"}
for argv in (["git", "init", "-q", "-b", "main"], ["git", "add", "."], ["git", "commit", "-qm", "seed"]):
    subprocess.run(argv, cwd=checkout, env=env, check=True)

settings = InstanceSettings(repository_url="https://github.com/o/r", instance="smoke",
                            checkout=checkout, state_directory=state)
b = build_boundaries(settings, "unused", hosting=FakeHostingService(), confine_executable=None)
definition = b.pipeline_reader.parse(Path(sys.argv[2]).read_text(encoding="utf-8"))
known = KnownResults(b, definition)
records = state / "records"

def tear(name: str, line: bytes, inside: str) -> None:
    cut = line.index(inside.encode()) + 1
    with (records / name).open("ab") as f:
        f.write(line[:cut])

def runs() -> int:
    return len(count.read_text().splitlines()) if count.exists() else 0

first = known.run("check")
print("1 run:", first.status, repr(first.last_line), "reused" if first.reused else "ran", "make runs", runs())
last = b.result_records.read()[-1]
tear("known-results.jsonl", last.model_dump_json().encode(), "✓")
tear("project-commands.jsonl", b"{\"command\":\"check\",\"note\":\"\xe2\x9c\x93\"}", "✓")
second = known.run("check")
print("2 run after a torn known-results line:", second.status, repr(second.last_line),
      "reused" if second.reused else "ran", "make runs", runs())
third = known.run("check")
print("3 run:", "reused" if third.reused else "ran", "make runs", runs())
print("known-results records read:", len(b.result_records.read()))
cmd = state / "records" / "project-commands.jsonl"
print("project-commands lines on disk:", cmd.read_bytes().count(b"\n") + 1,
      "records read:", [r.command for r in __import__("factory.adapters.record_log_jsonl", fromlist=["x"]).JsonLinesRecordLog(cmd, CommandRecord).read()])

recorder = DiskRecorder(b)
rec = recorder.record("acceptance")
with (records / "disk.jsonl").open("ab") as f:
    f.write(b"\xff\xfe torn\n")
recorder.record("start")
tear("disk.jsonl", rec.model_dump_json().encode().replace(b'"acceptance"', '"acceptance é"'.encode()), "é")
print("disk last occasion:", recorder.last().occasion, "records read:", len(b.disk_records.read()))

with (records / "stops.jsonl").open("ab") as f:
    f.write('{"event":"started","scope":"repository","reason":"é'.encode()[:-1])
print("stop records read:", b.stop_records.read())
log = (state / "factory.log")
print("factory log lines naming known results or decode:",
      [l for l in log.read_text(encoding="utf-8").splitlines() if "known results" in l or "decode" in l] if log.exists() else "no log")
PY
uv run python "$d/smoke.py" "$d" "$PWD/factory/pipeline.yml"; echo "exit: $?"
```

Output. The two `disk` lines are the factory log's own output on standard output. I shortened the run folder's name in them to `…`:

```
1 run: passed 'check: green ✓ – “done”' ran make runs 1
2 run after a torn known-results line: passed 'check: green ✓ – “done”' reused make runs 1
3 run: reused make runs 1
known-results records read: 2
project-commands lines on disk: 2 records read: ['check']
2026-10-20T09:48:58Z disk acceptance: /tmp/factory-run-…/tmp.Pu3E5ALb9a 970.6 GB free, 0.0 GB used; /tmp/factory-run-…/tmp.Pu3E5ALb9a/state 970.6 GB free, 0.0 GB used
2026-10-20T09:48:58Z disk start: /tmp/factory-run-…/tmp.Pu3E5ALb9a 970.6 GB free, 0.0 GB used; /tmp/factory-run-…/tmp.Pu3E5ALb9a/state 970.6 GB free, 0.0 GB used
disk last occasion: start records read: 2
stop records read: []
factory log lines naming known results or decode: []
exit: 0
```

Green.
- The check after the tear is reused, not run and not raised. `make` ran once in all.
- "known-results records read: 2" shows decision 4 as documented: the reuse record of run 2 landed on the torn line and was lost with it, and run 3 reused the first record again.
- A non-UTF-8 line in the middle of `disk.jsonl` and a torn last line cost only themselves.
- No factory log line was written about the tear.

A second block confirmed decision 5 on the real log. Three `ResultRecord`s appended with `last_line` `a b`, `a b` and `a\x85b` gave a file with exactly 3 line feeds and read back as `['a b', 'a b', 'a\x85b']`.

`make check` on this branch as found: `check: green`. Coverage was 99.17 %, and `test: green (155.2 s)`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- Coder (entry 7): a record appended after a torn line is skipped with it. That is the feature's decision 4, open for the human; see 6.
- Coder (entry 7): `KnownResults._read` still catches only `OSError`. That is the feature's decision 2 and needs no change now that `read` keeps its promise.
- Reviewer (entry 9): `make duplicates` reported 5 new findings, none in this feature's files. I ran it again here: `duplicates: 5 new, 33 known, 3 gone`.
  - Four similar-code blocks between `claude_runtime` and `opencode_runtime`.
  - An unused `ManualWaiter` in `src/factory/adapters/clock.py`.

  They belong to the features that wrote those modules, not to F0037, so I propose nothing for them here.
- Documenter (entry 11): nothing stale. `parse_stop_records` takes text, not bytes, and stays correct.
- Tester (entry 5): the known-results rig (`Rig`, `_rig`, `_answering`, `_result`) is imported from the test module `tests/application/test_known_results.py`, not moved to a shared module. That is allowed, and other test modules already import that way.
- My own: `MakeProjectCommands._last_line` (`src/factory/adapters/make_commands.py:72`) splits the output with `str.splitlines`. A tool's last line that holds U+2028 would be recorded only from that character on. That is cosmetic: the record still validates and reads back whole. No story.

## 5 Documentation

I read `README.md` (nothing on records, as the docs criterion said), the operator guide's *The records* and its three subsections, the project guide's `processes-and-checks.md` (the `RecordLog[R]` paragraph) and `watching.md` (*Stop records*), and the decision log's new entry *A record line that is not UTF-8 is skipped*. The three documents agree with each other and with the code. The decision entry carries decisions 1, 2, 3 and 5, rejects the wider `except` and the decoding with replacement, and leaves decision 4 open.

One finding, in `docs/operator-guide.md`, *The records*:
- The section opens with `project-commands.jsonl` alone. The new sentence "A line of any of the four record files that a kill cut, or that is not UTF-8, is skipped…" stands at the end of that file's paragraph, before the guide has named `known-results.jsonl`, `stops.jsonl` and `disk.jsonl` (in its subsections further down).
- That sentence now speaks of all four files. Beside it, "The records are telemetry … nothing reads them to decide anything" therefore reads as true of all four, and it is not. `KnownResults` reads `known-results.jsonl` to skip a check, and `StopPublisher.publish` reads `stops.jsonl` to push it to `main`.
- *The disk record* repeats "Like the other records it is not committed and nothing reads it to decide anything".

The telemetry claim predates F0037: it was written for `project-commands.jsonl`, and the disk line came with F0012. F0037's sentence makes it read wider. No example in these sections stopped working: both `python3 -c` one-liners still read files the factory writes. Proposed as S0002.

## 6 Decisions taken for the human

From `feature.md`, for the human to accept or revisit:
1. The fix is in the reader (`JsonLinesRecordLog.read`), not in its callers.
2. `KnownResults._read` keeps catching `OSError` alone.
3. A line that does not decode is skipped whole, never decoded with replacement.
4. **Open:** whether a later feature makes `append` start a new line when the file does not end in one, so that a torn line stops taking the next record with it. The feature smoke test above shows the cost: one record per kill. This is a product question; I leave it with the human and propose no story for it.
5. Lines split at `\n` alone, and a `\r` before it stays part of the line.

From the story's journal: no question was asked, and no default was taken beyond the Interface. The tester kept the rig in `tests/application/test_known_results.py` and imported it rather than moving it under the standing leave. That is their choice and changed no earlier test.

Earlier tests changed: none. The story's commits add `tests/adapters/test_record_log_jsonl_torn.py`, `tests/application/test_known_results_torn.py` and `tests/torn_record_support.py`, and change no test that `main` held. The reviewer's entry 9 says the same.

## 7 Slow checks

The project offers nothing beyond `make check` for this feature: no image scan, no SBOM target. `make mutants` is not run (check 3).

Disk now and at the previous record are identical (`/work` 970.6 GB free, 0.5 GB used; `/state` 0.0 GB; `/tmp` 0.0 GB), so there is no growth to explain.

From `.reports/junit.xml`, `make test` ran 6170 tests, 660.2 s of test time summed over the workers. The slowest are not F0037's:
- `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`: 11.5 s each for two rows.
- `test_process_session`: 10.1 s each for three time-limit tests.

The feature's 19 new test cases take 0.12 s together, at most 0.04 s each.

## 8 Cost

6 runs, 5.6 min, 35 turns, 190240 tokens in (608205 more from cache), 17239 out, $1.72 for the one story. No stage stands out:
- The tester's run is the largest ($0.51, 125 s, 10 turns). It wrote 19 parametrized cases and a shared helper module.
- The reviewer was next ($0.42).
- No rework round, no retry, no crash.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `F0037-S0002-the-operator-guide-s-records-section-names-its-four-files.md`: *The records* in `docs/operator-guide.md` gets an opening paragraph that names the four files and states the damage rule once. The "nothing reads them to decide anything" claims are corrected for `known-results.jsonl`, `stops.jsonl` and `disk.jsonl`. Documents only.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed
   1 Scope: none. Every Scope item is on `main` from S0001, and the Out of scope items are unchanged. All four record files are wired through the one fixed `JsonLinesRecordLog`, so the goal is reached.
   2 Feature smoke test: green. I used real `make`, `build_boundaries` and the repository's `factory/pipeline.yml`, and tore lines in all four record files. After a `known-results.jsonl` line torn inside `✓`, the check was reused, not raised: one `make` run in all, and no factory log line. A torn and a non-UTF-8 line in `disk.jsonl` cost only themselves. A torn `stops.jsonl` read as `[]`. Records holding U+2028, U+2029 or U+0085 read back whole. `make check` is green as found.
   3 Mutation testing: by sweep, not run here.
   4 Noticed:
      - Decision 4 (a record appended after a torn line is lost with it) is open; see 6.
      - `KnownResults._read` catches `OSError` only, by decision 2.
      - `make duplicates` shows 5 new findings in `claude_runtime`/`opencode_runtime` and `clock.py`. They belong to other features, so no story here.
      - `MakeProjectCommands._last_line` uses `splitlines`. That is cosmetic, so no story.
   5 Documentation: one finding. In `docs/operator-guide.md`, *The records* speaks of "the four record files" before naming three of them. Its claim that "nothing reads them to decide anything" now reads as covering `known-results.jsonl` and `stops.jsonl`, which the factory does read to decide; the disk section repeats the claim. The claim predates F0037. Proposed as S0002.
   6 Decisions for the human: feature decisions 1, 2, 3 and 5 as taken. Decision 4 (`append` starting a new line after a torn one) is open and is a product question for you. No earlier test was changed.
   7 Slow checks: nothing beyond `make check` is offered. Disk use is unchanged since the previous record. The slowest tests are 10–11.5 s time-limit tests from other features; the feature's 19 new test cases take 0.12 s together.
   8 Cost: 6 runs, 5.6 min, $1.72. The tester's run was the largest ($0.51), with no rework round. 0 questions, 0.0 h waited.
