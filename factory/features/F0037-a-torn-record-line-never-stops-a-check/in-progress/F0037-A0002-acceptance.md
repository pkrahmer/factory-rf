---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 375
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T23:56:00.583661Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T00:00:11.874582Z'
  stage: acceptance
  run: 2576e7e12fed4c238b1b9c5c0be85037
stories: [F0037-S0001, F0037-S0002]
outcome: null
---

# Acceptance of A torn record line never stops a check

## Recommendation

accepted with stories. Both stories are merged, and together they deliver what `feature.md` promised. `JsonLinesRecordLog.read` reads bytes, splits at `\n` alone and skips a line that does not decode. All four record files are wired through it, and a torn `known-results.jsonl` line no longer stops a check. The feature smoke test (real `make`, `build_boundaries`, the repository's pipeline definition) and `make check` are both green. One documentation finding is worth a small story: the decision log still calls decision 4 open and invites "a later story", but the human answered it "left, no later feature". That misleads the next agent, not a user, so it is not a broken promise.

## 1 Scope

None.
- S0001 built every Scope item: the reader, the `RecordLog.read` docstring, the two new test modules (plus `tests/torn_record_support.py`) and the three documents. A0001 checked this in detail, and the code on `main` (`src/factory/adapters/record_log_jsonl.py`) is unchanged since.
- S0002 is not in `feature.md`'s Stories list. A0001 proposed it and the human started it. It is documents only and stays within the goal: the operator guide's *The records* now names the four files and states the damage rule once.
- Out of scope was kept. `KnownResults._read`, `DiskRecorder.last`, `StopPublisher.publish`, `append`, `JsonLinesCostRecordReader` and `parse_stop_records` are unchanged. The wiring (`src/factory/entry/wiring.py:281`, `:299`, `:300`, `:302`) builds all four logs as `JsonLinesRecordLog`, so the goal is reached for every file.

## 2 Feature smoke test

The walk-through of an operator's instance:
- a real git checkout whose `make check` prints `✓`, curly quotes and `😀`;
- `build_boundaries` with the fake hosting service and no confinement, and the repository's `factory/pipeline.yml`;
- `KnownResults.run("check")` three times, with the known-results line torn inside `😀` after the first run;
- records holding U+2028, U+2029 and U+0085 appended through the wired log and read back;
- a non-UTF-8 line in `project-commands.jsonl`;
- `DiskRecorder` on a `disk.jsonl` with a damaged middle line (`0xc3 0x28`) and a last line torn inside `€`;
- a torn `stops.jsonl`.

No paid call.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cat > "$d/smoke.py" <<'PY'
import os, subprocess, sys
from pathlib import Path
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.record_log_jsonl import JsonLinesRecordLog
from factory.application.disk_records import DiskRecorder
from factory.application.known_results import KnownResults
from factory.domain.command_records import CommandRecord
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries

root = Path(sys.argv[1]); checkout = root / "checkout"; state = root / "state"
checkout.mkdir(); (state / "records").mkdir(parents=True)
count = root / "runs"
(checkout / "Makefile").write_text(f"check:\n\t@echo run >> {count}\n\t@echo 'check: green ✓ – “done” 😀'\n")
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

def tear(name, line, inside, keep=1):
    cut = line.index(inside.encode()) + keep
    with (records / name).open("ab") as f:
        f.write(line[:cut])

def runs():
    return len(count.read_text().splitlines()) if count.exists() else 0

first = known.run("check")
print("1 check:", first.status, repr(first.last_line), "reused" if first.reused else "ran", "| make runs", runs())
last = b.result_records.read()[-1]
tear("known-results.jsonl", last.model_dump_json().encode(), "😀", keep=3)
second = known.run("check")
print("2 check after a line torn inside 😀:", second.status, "reused" if second.reused else "ran", "| make runs", runs())
third = known.run("check")
print("3 check:", "reused" if third.reused else "ran", "| make runs", runs())
print("known-results records read:", len(b.result_records.read()))

for ch in (" ", " ", "\x85"):
    b.result_records.append(last.model_copy(update={"last_line": f"before{ch}after"}))
print("records with line separators read back:", [r.last_line for r in b.result_records.read()][-3:])

cmd_log = JsonLinesRecordLog(records / "project-commands.jsonl", CommandRecord)
with (records / "project-commands.jsonl").open("ab") as f:
    f.write(b"\xff\xfe not utf-8\n")
print("project-commands records read past a non-UTF-8 line:", [r.command for r in cmd_log.read()])

recorder = DiskRecorder(b)
rec = recorder.record("acceptance")
with (records / "disk.jsonl").open("ab") as f:
    f.write(b"\xc3\x28 damaged\n")
recorder.record("start")
tear("disk.jsonl", rec.model_dump_json().encode().replace(b'"acceptance"', '"accept€"'.encode()), "€", keep=2)
print("disk last occasion:", recorder.last().occasion, "| records read:", len(b.disk_records.read()))

with (records / "stops.jsonl").open("ab") as f:
    f.write('{"event":"raised","scope":"machine","reason":"é'.encode()[:-1])
print("stop records read:", b.stop_records.read())
log = state / "factory.log"
lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
print("factory log lines naming known results or decode:", [l for l in lines if "known results" in l or "decode" in l])
PY
uv run python "$d/smoke.py" "$d" "$PWD/factory/pipeline.yml" 2>&1 | sed "s#$d#…#g"; echo "exit: ${PIPESTATUS[0]}"
```

Output. The two `disk` lines are the factory log's own output on standard output. The `sed` shortens the run folder to `…`.

```
Bytecode compiled 4164 files in 99ms
1 check: passed 'check: green ✓ – “done” 😀' ran | make runs 1
2 check after a line torn inside 😀: passed reused | make runs 1
3 check: reused | make runs 1
known-results records read: 2
records with line separators read back: ['before after', 'before after', 'before\x85after']
project-commands records read past a non-UTF-8 line: ['check']
2026-10-20T23:58:51Z disk acceptance: … 968.5 GB free, 0.0 GB used; …/state 968.5 GB free, 0.0 GB used
2026-10-20T23:58:51Z disk start: … 968.5 GB free, 0.0 GB used; …/state 968.5 GB free, 0.0 GB used
disk last occasion: start | records read: 2
stop records read: []
factory log lines naming known results or decode: []
exit: 0
```

Green.
- After a line torn inside a 4-byte character, the check is reused, not raised and not run again: one `make` run in all, and no factory log line.
- "known-results records read: 2" is decision 4 as the documents describe it: the reuse record of run 2 landed on the torn line and was lost with it.
- Records holding U+2028, U+2029 and U+0085 read back whole.
- A non-UTF-8 line and a damaged line in the middle of a file cost only themselves.
- `DiskRecorder.last` gives the last whole record.

`make check` on this branch as found: `check: green`, coverage 99.14 %, `test: green (64.4 s)`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0001, coder (entry 7): a record appended after a torn line is lost with it (decision 4), and `KnownResults._read` still catches `OSError` alone (decision 2). The human has since answered decision 4 (left), and decision 2 needs no change. Nothing is open.
- S0001, reviewer and coder: `duplicates: 5 new, 33 known, 3 gone`. S0002's coder recorded `6 new` on an empty diff, so the new one comes from another feature merged between the two stories, not from F0037. No story here.
- S0002, coder (entry 7): intake had not checked the story's claims about `KnownResults`, `StopPublisher.publish` and the disk record against the code. The reviewer (entry 9) checked them (`known_results.py:33`, `stops.py:132`, `disk_records.py:42`) and found them true. Closed.
- S0002, documenter (entry 11): nothing stale.
- From A0001, still true: `MakeProjectCommands._last_line` (`src/factory/adapters/make_commands.py`) uses `str.splitlines`, so a tool's last line holding U+2028 is recorded from that character on. The record still validates. Cosmetic, so no story.

## 5 Documentation

I read `README.md`, the operator guide's *The records* and its three subsections, the `RecordLog[R]` and *Known results* paragraphs of `docs/project-guide/processes-and-checks.md`, and the decision log's entry *A record line that is not UTF-8 is skipped*. A0001's finding is repaired: *The records* now opens by naming the four files and states the damage rule once. The telemetry claim speaks of `project-commands.jsonl` alone (`docs/operator-guide.md:594`), and the disk record's sentence is corrected. The project guide and the operator guide agree with each other and with the code.

One finding, in `docs/decisions.md:890`. The entry's last bullet still reads "Open (decision 4): … A later story may start a new line first." The human answered decision 4 on 2026-10-20, after S0001's documenter wrote that bullet (commit `616116ac`, F0037's `feature.md`): left, no later feature. The answer is in no document. The decision log is what agents read before they change the architecture, so the bullet invites a story that the human turned down. Proposed as S0003.

No example in these sections stopped working. Both `python3 -c` one-liners still read files the factory writes.

## 6 Decisions taken for the human

From `feature.md`:
1. The fix is in the reader (`JsonLinesRecordLog.read`), not in its callers.
2. `KnownResults._read` keeps catching `OSError` alone.
3. A line that does not decode is skipped whole, never decoded with replacement.
4. Answered by the human (2026-10-20): left. A record appended after a torn line stays lost with it, and no later feature changes `append`. Not yet in `docs/decisions.md`; see S0003.
5. Lines split at `\n` alone, and a `\r` before it stays part of the line.

From the stories' journals: no question was asked, and no default was taken beyond the Interfaces. S0002 went through tester and coder stages that each wrote nothing, as its criterion 1 asked.

Earlier tests changed: none. S0001 only added test files. The reviewer's entry 9 says so, and S0001's tester imported the known-results rig instead of moving it. S0002 changed no file under `tests/` (reviewer, entry 9).

## 7 Slow checks

The project offers nothing beyond `make check` for this feature: no image scan, no SBOM target. `make mutants` is not run (check 3).

Disk: the previous record (occasion `acceptance`) had `/work` at 968.6 GB free and 0.5 GB used. Now it is 969.1 GB free and 0.0 GB used. `/state` and `/tmp` stay at 0.0 GB. Use went down, not up, so there is no growth to explain.

From `.reports/junit.xml`, `make test` ran 6407 tests, 733.7 s of test time summed over the workers. The slowest are not F0037's:
- `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`: 11.5 s each for two rows.
- `test_make_commands::test_command_reaching_its_time_limit_is_killed`: 10.1 s.
- `test_process_session::test_time_limit_of_a_make_target_ends_what_timeout_started[own-group]`: 10.1 s.

The feature's 19 test cases take 0.1 s together.

## 8 Cost

12 runs, 9.7 min, 64 turns, $2.50 in all.
- S0001: 6 runs, 5.6 min, $1.72. The tester's run was the largest ($0.51, 125 s, 10 turns: 19 parametrized cases and a shared helper module), then the reviewer ($0.42).
- S0002: 6 runs, 4.1 min, $0.79, for a one-file documents change. Its tester and coder runs ($0.13 each) wrote nothing and spent 80–90 s of wall time each, mostly on `make test` and `make check`, against 14–20 s of model time. That is the price of passing a documents-only story through every stage. Its smoke-tester run was its most expensive ($0.18).

No rework round, no retry, no crash in either story.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human. The human's answer on decision 4 came on the feature, outside the stories.

## Proposed stories

- `F0037-S0003-the-decision-log-records-the-answer-on-decision-4.md`: the decision log's entry *A record line that is not UTF-8 is skipped* replaces its "Open (decision 4)" bullet with the human's answer (left, no later feature) and its reason. Documents only.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 story proposed
   1 Scope: none. S0001 built every Scope item, and the Out of scope items are unchanged. S0002 came from A0001 and is documents only, within the goal. All four record logs are wired through the fixed `JsonLinesRecordLog`.
   2 Feature smoke test: green. I used real `make`, `build_boundaries` and the repository's `factory/pipeline.yml`. After a known-results line torn inside `😀`, the check was reused, with one `make` run in all and no log line. Records holding U+2028, U+2029 and U+0085 read back whole. A non-UTF-8 or damaged middle line costs only itself, `DiskRecorder.last` gives the last whole record, and a torn `stops.jsonl` reads as `[]`. `make check` is green as I found it (99.14 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: decisions 2 and 4 are closed. The 6th `make duplicates` finding comes from another feature (S0002's diff was empty). The `_last_line` `splitlines` issue A0001 noted is cosmetic, so no story. The reviewer verified S0002's unchecked code claims.
   5 Documentation: A0001's finding in *The records* is repaired. New finding: `docs/decisions.md:890` still calls decision 4 "Open" and suggests "a later story", but the human answered "left, no later feature" (`616116ac`). Proposed as S0003.
   6 Decisions for the human: feature decisions 1, 2, 3 and 5 as taken. Decision 4 was answered by the human but is not yet in the decision log. No question was asked, no default was taken, and no earlier test was changed.
   7 Slow checks: nothing beyond `make check`. Disk use went down since the previous acceptance record (`/work` from 0.5 to 0.0 GB used). The slowest tests are other features' time-limit tests at 10–11.5 s; F0037's 19 cases take 0.1 s together.
   8 Cost: 12 runs, 9.7 min, $2.50. S0001 cost $1.72 (largest run: the tester, $0.51). S0002 cost $0.79 for a one-file docs change, partly on tester and coder runs that wrote nothing. 0 questions, 0.0 h waited.
