---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 378
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-21T00:18:43.006803Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T00:22:32.782415Z'
  stage: acceptance
  run: c65d1805cfb547bba52895b5c9221e80
stories: [F0037-S0001, F0037-S0002, F0037-S0003]
outcome: null
---

# Acceptance of A torn record line never stops a check

## Recommendation

accepted. All three stories are merged, and together they deliver what `feature.md` promised:
- `JsonLinesRecordLog.read` reads bytes, splits at `\n` alone and skips a line that does not decode.
- All four record files are wired through it, so a torn `known-results.jsonl` line no longer stops a check.

The feature smoke test (real `make`, `build_boundaries`, the repository's pipeline definition) and `make check` are both green. A0002's one finding is repaired by S0003: the decision log now records the human's answer on decision 4. No finding of weight is left and no story is proposed.

## 1 Scope

None.
- S0001 built every Scope item: the reader, the `RecordLog.read` docstring, the two new test modules and the three documents. Its code on `main` (`src/factory/adapters/record_log_jsonl.py`) is unchanged since A0002 checked it. The commits after it touch other features.
- S0002 and S0003 are not in `feature.md`'s Stories list. A0001 and A0002 proposed them and the human started them. Both are documents only and stay within the goal:
  - S0002: the operator guide's *The records*.
  - S0003: the decision log's entry *A record line that is not UTF-8 is skipped*.
- Out of scope was kept. `KnownResults._read`, `DiskRecorder.last`, `StopPublisher.publish`, `append`, `JsonLinesCostRecordReader` and `parse_stop_records` are unchanged.
- The wiring builds all four logs as `JsonLinesRecordLog` (`src/factory/entry/wiring.py:281`, `:299`, `:300`, `:302`). F0040 has since added `end_leftovers` to `build_boundaries`, but it leaves those lines as they were.

## 2 Feature smoke test

The walk-through of an operator's instance:
- a real git checkout whose `make check` prints `✓`, curly quotes and `😀`;
- `build_boundaries` with the fake hosting service, no confinement and `end_leftovers=False`, and the repository's `factory/pipeline.yml`;
- `KnownResults.run("check")` three times, with the known-results line torn inside `😀` after the first run;
- records holding U+2028, U+2029 and U+0085 appended through the wired log and read back;
- a non-UTF-8 line in `project-commands.jsonl`;
- `DiskRecorder` on a `disk.jsonl` with a damaged middle line and a last line torn inside `€`;
- a torn `stops.jsonl`;
- the decision log's answer on decision 4 and the document check.

No paid call. The script is kept in its own folder, apart from the run folder it writes.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/scripts" "$d/run"
cat > "$d/scripts/smoke.py" <<'PY'
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
b = build_boundaries(settings, "unused", hosting=FakeHostingService(), confine_executable=None, end_leftovers=False)
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
uv run python "$d/scripts/smoke.py" "$d/run" "$PWD/factory/pipeline.yml" 2>&1 | sed "s#$d/run#…#g"; echo "exit: ${PIPESTATUS[0]}"
grep -c "Open (decision 4)" docs/decisions.md; grep -c "Answered (decision 4, the human, 2026-10-20)" docs/decisions.md; uv run python -m factory.entry.check_documents
```

Output. The two `disk` lines are the factory log's own output on standard output, and the `sed` shortens the run folder to `…`.

```
Bytecode compiled 4164 files in 95ms
1 check: passed 'check: green ✓ – “done” 😀' ran | make runs 1
2 check after a line torn inside 😀: passed reused | make runs 1
3 check: reused | make runs 1
known-results records read: 2
records with line separators read back: ['before after', 'before after', 'before\x85after']
project-commands records read past a non-UTF-8 line: ['check']
2026-10-21T00:21:02Z disk acceptance: … 968.6 GB free, 0.0 GB used; …/state 968.6 GB free, 0.0 GB used
2026-10-21T00:21:02Z disk start: … 968.6 GB free, 0.0 GB used; …/state 968.6 GB free, 0.0 GB used
disk last occasion: start | records read: 2
stop records read: []
factory log lines naming known results or decode: []
exit: 0
0
1
Bytecode compiled 4164 files in 97ms
documents ok
```

Green.
- After a line torn inside a 4-byte character, the check is reused, not raised and not run again: one `make` run in all, and no factory log line.
- "known-results records read: 2" is decision 4 as the documents now record it: the reuse record of run 2 landed on the torn line and was lost with it.
- Records holding U+2028, U+2029 and U+0085 read back whole. They are printed escaped, which shows the separator stayed inside the string.
- A non-UTF-8 line and a damaged line in the middle of a file cost only themselves.
- `DiskRecorder.last` gives the last whole record, and a torn `stops.jsonl` reads as `[]`.
- The decision log has no "Open (decision 4)" left, has the answer once, and the document check passes.

`make check` on this branch as found: `check: green`, coverage 99.14 %, `test: green (63.7 s)`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0003: the coder, the documenter and the smoke-tester each noticed nothing, and the reviewer had no remark.
- S0003, coder and reviewer: `duplicates: 6 new, 33 known, 3 gone` on an empty code diff. A0002 already traced the sixth finding to another feature on `main`, so it is not F0037's.
- From S0001 and S0002, as A0002 found: decision 2 needs no change. Decision 4 is now answered and recorded (S0003). The claims S0002 made about the code were checked by its reviewer.
- From A0001, still true: `MakeProjectCommands._last_line` (`src/factory/adapters/make_commands.py`) uses `str.splitlines`. A tool's last line holding U+2028 is therefore recorded from that character on. The record still validates and reads back whole (check 2), so this is cosmetic and gets no story.

## 5 Documentation

None.

I read the following as a newcomer would:
- `README.md`;
- the operator guide's *The records*;
- the `RecordLog[R]` paragraph of `docs/project-guide/processes-and-checks.md` (line 60);
- the decision log's entry *A record line that is not UTF-8 is skipped* (`docs/decisions.md:883`).

A0002's finding is repaired. Line 890 now reads "Answered (decision 4, the human, 2026-10-20): …", with the reason, and the date line names decisions 1 to 5.

The three documents agree with each other and with the code:
- The project guide says "A record appended after a torn line shares its line and is skipped with it".
- The decision log says the same and records that it stays.
- Check 2 shows it happen.

Since A0002, the other changes to `docs/` are other features' (F0040's rows in the operator guide's checks table, a sentence in *Running as another user*, `watching.md`). None of them touches the records sections.

## 6 Decisions taken for the human

From `feature.md`:
1. The fix is in the reader (`JsonLinesRecordLog.read`), not in its callers.
2. `KnownResults._read` keeps catching `OSError` alone.
3. A line that does not decode is skipped whole, never decoded with replacement.
4. Answered by the human (2026-10-20): left. A record appended after a torn line stays lost with it, and no later feature changes `append`. This is now in `docs/decisions.md:890` (S0003).
5. Lines are split at `\n` alone, and a `\r` before the `\n` stays part of the line.

From the stories' journals: no question was asked and no default was taken beyond the Interfaces. S0002 and S0003 passed through tester and coder stages that each wrote nothing, as their criterion 1 asked.

Earlier tests changed: none. S0001 only added test files. S0002 and S0003 changed nothing under `tests/` (S0003: reviewer, entry 9, "Earlier tests: none").

## 7 Slow checks

The project offers nothing beyond `make check` for this feature: no image scan and no SBOM target. `make mutants` is not run (check 3).

Disk: the previous record (occasion `acceptance`, A0002's start) had `/work` at 969.1 GB free and 0.0 GB used. Now it is 968.6 GB free and 0.5 GB used. `/state` and `/tmp` stay at 0.0 GB.
- The 0.5 GB is the checkout's uv virtual environment. `du` shows `.venv` at 511 MB, against `.git` at 27 MB and `.reports` at 1.9 MB.
- It is git-ignored, and it comes and goes with the runs that recreate it. A0002 saw the same 0.5 GB in the other direction.
- F0037's changes, three documents and one reader, explain none of it, and none is needed.

From `.reports/junit.xml`, `make test` ran 6407 tests, 728.3 s of test time summed over the workers. The slowest are not F0037's:
- `test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login`: 11.5 s each for its two rows.
- `test_process_session::test_time_limit_of_a_make_target_ends_what_timeout_started[own-group]`: 10.1 s.
- `test_process_session::test_time_limit_ends_every_process_of_the_session[run_process-own-group]`: 10.1 s.

The feature's 19 test cases take 0.1 s together.

## 8 Cost

18 runs, 12.5 min, 93 turns, $3.20 in all.

| Story | Runs | Time | Cost | Note |
|---|---|---|---|---|
| S0001 | 6 | 5.6 min | $1.72 | The code story. The largest runs were the tester ($0.51) and the reviewer ($0.42). |
| S0002 | 6 | 4.1 min | $0.79 | A one-file documents change. |
| S0003 | 6 | 2.8 min | $0.70 | A one-bullet documents change. |

No story stands out against what it did. In S0003:
- The smoke-tester was the most expensive run ($0.17). It created a fresh virtual environment before `check_documents`.
- The coder took 85 s of wall time against 15 s of model time. The time went on `make check` for an empty diff.

As in S0002, a documents-only story pays about $0.25 and over a minute for tester and coder runs that write nothing.

No rework round, no retry and no crash in any story.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human. The human's answer on decision 4 came on the feature, outside the stories.

## Proposed stories

None. Nothing found warrants a story. The one remaining noticed item, `_last_line`'s `splitlines`, is cosmetic.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: none. S0001 built every Scope item, and its reader code on `main` is unchanged. S0002 and S0003 are documents-only stories from A0001 and A0002 and stay within the goal. The Out of scope items are unchanged, and all four record logs are still wired through `JsonLinesRecordLog`.
   2 Feature smoke test: green. I used real `make`, `build_boundaries` (`end_leftovers=False`) and the repository's `factory/pipeline.yml`. After a known-results line torn inside `😀`, the check was reused, with one `make` run in all and no log line. Records holding U+2028, U+2029 and U+0085 read back whole. A non-UTF-8 or damaged middle line costs only itself, `DiskRecorder.last` gives the last whole record and a torn `stops.jsonl` reads as `[]`. The decision log has the answer on decision 4 once and `documents ok`. `make check` was green as I found it (99.14 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0003 had no remarks. Its `duplicates: 6 new` finding comes from another feature, as A0002 found. `_last_line`'s `splitlines` is still cosmetic, so no story.
   5 Documentation: none. A0002's finding is repaired (`docs/decisions.md:890` now says "Answered (decision 4, …)"), and the project guide, the operator guide and the decision log agree with the code.
   6 Decisions for the human: feature decisions 1, 2, 3 and 5 as taken. Decision 4 was answered by the human and is now recorded in the decision log. No question was asked, no default was taken and no earlier test was changed.
   7 Slow checks: nothing beyond `make check`. `/work` went from 0.0 to 0.5 GB used since A0002's record. That is the git-ignored `.venv` (511 MB), not this feature. The slowest tests are other features' time-limit tests at 10–11.5 s; F0037's 19 cases take 0.1 s together.
   8 Cost: 18 runs, 12.5 min, $3.20 (S0001 $1.72, S0002 $0.79, S0003 $0.70). No story stands out. The documents-only stories pay about $0.25 each for tester and coder runs that write nothing. 0 questions, 0.0 h waited.
