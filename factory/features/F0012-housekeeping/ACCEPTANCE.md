---
stage: accept
pr: 181
blocked: null
comments_seen: 1
round: 0
attempts: 1
stories: [F0012-S0001, F0012-S0002, F0012-S0003, F0012-S0004, F0012-S0005, F0012-S0006, F0012-S0007, F0012-S0008, F0012-S0009, F0012-S0010, F0012-S0011, F0012-S0012, F0012-S0013, F0012-S0014, F0012-S0016, F0012-S0017, F0012-S0018, F0012-S0019, F0012-S0021, F0012-S0022, F0012-S0023, F0012-S0024, F0012-S0025, F0012-S0026, F0012-S0027, F0012-S0028, F0012-S0029, F0012-S0030]
---
# Acceptance of Housekeeping

## Verdict

**accepted with drafts.** Every scope item 1.1 to 1.10 has a merged story or a human change. The feature walk-through runs green on the real entry points, and `make check` is green: `make test` takes 29.9 s, against the 177 s of 2026-10-17. Nothing breaks a promise. Two things are worth stories: the acceptance handlers' no-state refusals, which no test reaches (the same gap S0007 closed for five other calls), and the backlog path that S0023's review deferred (decision 55). One finding is for the human alone, because it concerns the `Makefile`: `make mutants FEATURE=F0012` runs, but on this machine it cannot finish within the stage's 60-minute lease. The first acceptance run stalled on it. This run resumed it, and it covered 4,173 of the feature's 5,285 mutants.

## 1 Scope

None. Every scope line has its stories, and they are all in `done/`. 1.1: S0001 and H1. 1.2: S0002 to S0007, with H2 to H4. 1.3: S0008 and H5. 1.4: S0009 to S0014, S0016 and S0017. 1.5: S0018, S0019 and S0021. 1.6: S0022. 1.7: S0023 and H6, and `demo/README.md` is present. 1.8: S0024. 1.9: H3 and S0003's docs criterion. 1.10: S0025 to S0027. The template's lessons and `Makefile`: S0028 and S0029. The commit prefix: S0030. S0015 and S0020 are not in `FEATURE.md`'s list, so the gaps in the numbering are not missing stories. No story goes beyond the scope. The goal's done-line, measured here:
- `make check` is green, and `make test` takes 29.9 s (it was 177 s).
- `make duplicates` prints `duplicates: 0 new, 39 known, 0 gone`.
- `make documents` prints `documents ok`.
- `make mutants FEATURE=F0012` runs, but it does not finish within one stage run (see 3).

Two scope items can only be observed on the real machine, as their stories say: the kill under `sudo` (S0024) and the sticky bit of the agent home (S0025). Neither was run in a container here.

## 2 Feature demo

The walk-through a human makes before the first start covers: the timed targets and their parsed times, the three reports and checks, the low-disk stop and the disk record on the real file system, an answer at the round cap, the commit prefix, the template's targets, and `make mutants` picking its feature from the acceptance branch. The script below was written to `/tmp/f12demo/demo.sh` and run with `bash` from there:

```bash
#!/usr/bin/env bash
# F0012 feature walk-through: what the human needs before the first start and the todo run.
set -u
cd /work/factory-rf
echo "## 1. make check is timed per target (1.1, 1.4)"
make lint types 2>&1 | tail -2
echo "## 2. the factory reads those lines as each target's time (S0012)"
make lint 2>&1 | uv run python -c "import sys; from factory.domain.checks import target_times; print(target_times(sys.stdin.read()))"
echo "## 3. duplicates against its baseline (1.2), documents (1.9), demos (1.7)"
make duplicates 2>&1 | tail -1
make documents 2>&1 | tail -1
uv run python -m factory.entry.check_demos
echo "## 4. the low-disk stop (S0009, S0010), the disk record line (S0016), on the real file system"
uv run python - <<'PY'
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.disk_space import ShutilDiskSpace
from factory.domain.disk import DiskRecord, DiskUse, disk_line, disk_low_detail
from factory.domain.stop_table import STOP_TABLE
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder)
    (path / "a.bin").write_bytes(b"x" * 2_000_000)
    disk = ShutilDiskSpace()
    free = disk.free_bytes(path)
    print("min 5 GB:", disk_low_detail({path: free}, 5))
    print("min 100000 GB:", (disk_low_detail({path: free}, 100000) or "").replace(folder, "<tmp>"))
    record = DiskRecord(at=datetime.now(UTC), occasion="start", folders=[DiskUse(path="<tmp>", free_bytes=free, used_bytes=disk.used_bytes(path))])
    print(disk_line(record).split(" free")[0], "...", disk.used_bytes(path), "bytes used")
print([row.id for row in STOP_TABLE if row.id == "disk-low"])
PY
echo "## 5. an answer at the round cap grants the rounds again (S0021); the commit prefix (S0030)"
uv run python - <<'PY'
from factory.domain.answers import unblock
from factory.domain.work_item import WorkItemState
from factory.application.handlers.recording import commit_subject
state = WorkItemState(stage="review", blocked="round_cap", round=3)
print(unblock(state).blocked, unblock(state).round)
print(commit_subject("F0001-S0001", "doing ends: review"))
PY
echo "## 6. the template's Makefile, from which a project's starts (S0029)"
make -n -f template/Makefile help >/dev/null 2>&1; make -pn -f template/Makefile 2>/dev/null | grep -E '^(check|lint|types|layers|sast|secrets|licenses|test|duplicates|mutants):' | sort | tr '\n' ' '; echo
echo "## 7. make mutants without FEATURE off an acceptance branch"
git -C /work/factory-rf rev-parse --abbrev-ref HEAD
make -n mutants 2>&1 | head -c 300; echo
```

Output:

```
## 1. make check is timed per target (1.1, 1.4)
Success: no issues found in 435 source files
types: green (0.3 s)
## 2. the factory reads those lines as each target's time (S0012)
[TargetTime(target='lint', seconds=0.0)]
## 3. duplicates against its baseline (1.2), documents (1.9), demos (1.7)
duplicates: 0 new, 39 known, 0 gone
documents ok
demos ok
## 4. the low-disk stop (S0009, S0010), the disk record line (S0016), on the real file system
min 5 GB: None
min 100000 GB: <tmp> has 986.4 GB free, less than the 100000 GB FACTORY_MIN_FREE_GB asks for
disk start: <tmp> 986.4 GB ... 2000000 bytes used
['disk-low']
## 5. an answer at the round cap grants the rounds again (S0021); the commit prefix (S0030)
None 0
work item F0001-S0001: doing ends: review
## 6. the template's Makefile, from which a project's starts (S0029)
check: lint types layers sast secrets licenses test duplicates: layers: licenses: lint: mutants: sast: secrets: test: types:
## 7. make mutants without FEATURE off an acceptance branch
acceptance/F0012-housekeeping
if [ -z "F0012" ]; then echo "mutants: set FEATURE, as in make mutants FEATURE=F0012"; exit 2; fi
if [ -z "src/factory/adapters/claude_runtime.py src/factory/adapters/disk_space.py ...
```

Green. Every step shows what its story promised. `make check` ran in full beforehand and ended with `test: green (29.9 s)` and `check: green`, at 99.50 % branch coverage.

## 3 Mutation score

`make mutants FEATURE=F0012` selects 42 modules and 5,285 mutants (mutmut 3.8.0 generates 11,898 for the whole package). Neither run could finish:
- The first acceptance run stalled at its 60-minute lease after 4,173 checked mutants.
- This run resumed from mutmut's state: `timeout 570 make mutants FEATURE=F0012` listed the tests, ran the clean suite, and then stood at `4173/11898` for its remaining 7 minutes without one more result.

The 1,112 unchecked mutants are in modules whose functions most of the suite covers, so each mutant runs hundreds of git tests on one core. They are: `application.stage` (470), `application.tick` (132), `application.claims` (130), `entry.wiring` (111), `application.costs` (82), `domain.git` (64), `domain.acceptance` (58), `domain.hosting` (27), `application.stalls` (14), `application.acceptance` (10) and a few in five other modules.

Partial score over the checked 4,173: **3,911 killed, 258 survived, 4 timeout (93.7 %)**.

Survivors by module: `application.acceptance` 48, `adapters.claude_runtime` 24, `domain.stop_table` 22, `entry.wiring` 21, `application.preflight` 19, `domain.settings` 18, `domain.acceptance` 16, `entry.watch` 12, `adapters.pipeline_yaml` 11, `entry.check_duplicates` 10, `domain.duplicates` 9, `entry.run` 9, `application.stage` 8, `application.stalls` 7, `entry.check_story` 6, and fewer elsewhere. Read with `mutmut show`, they fall into these groups:
- **The acceptance handlers' no-state refusals**: `AcceptanceHandOver.handle`, `AcceptanceMerged._book` and `AcceptanceClosed._record_close` (`src/factory/application/acceptance.py:219`, `:292`, `:353`). `no_state = None` survives at each of them, and no test names their messages. This is the gap S0007 closed for five other callers of `require_state`. Draft S0031.
- **Pass-throughs in the wiring**: `run_instance` hands `build_boundaries` the token, `build_boundaries` hands `machine_log` the clock, and `watch.main` writes to its out stream. `token → None`, `clock → None` and `out_stream = None` all survive, so the tests build these with defaults that hide a dropped argument. This is a small group; it is left for the restructure (plan step 8), which rewires `entry`.
- **Artefacts**: the 22 in `domain.stop_table` (`_health(id=None, ...)`) build `STOP_TABLE` at import time, before mutmut switches the mutant on, so no test can kill them. The same holds for the module-level constants of `domain.settings`.
- **Messages and boundaries**: error texts (`ValueError(None)` in `domain.duplicates._pylint_messages`), `partition` against `rpartition` in `settings._holds_password` for a URL with two `://`, and `left <= 0` against `< 0` in `claude_runtime._resume`. The last is decision 19's untested line 384, which was left open on purpose. No draft: each is a single line, and none has a user-visible rule behind it that a criterion missed.

A finding for the human, not a story, because the `Makefile` is the human's file: as it is, `make mutants` over a feature of 42 modules does not fit one acceptance run. Options I see are:
- cap mutmut's run time per mutant, or select the tests per mutant more narrowly;
- run the mutants outside the stage and hand the acceptance their results;
- let the acceptance read a partial result and say so.

I would choose the last one, as this report does, plus a time limit in the target (for example `timeout` around `mutmut run`), so that the stage ends with a result and does not stall.

## 4 What the stories noticed

- S0002: a failed write of the duplicates baseline (`OSError`) is not exit status 2, and a `==` line after the code is read as code. Both are minor; no draft.
- S0006: a ruamel `problem` holding a line break would reach the one-line fault. No ruamel text does so today.
- S0009 and S0016: `ShutilDiskSpace.used_bytes` lets a `FileNotFoundError` through when a file is removed during the walk (`src/factory/adapters/disk_space.py:28`, `lstat`). The disk recorder turns any `OSError` into `unknown`. So a folder in use, such as the work directory while an agent runs, can record `unknown used` rather than a number. This is worth watching in the todo run's disk records before a story.
- S0004: `domain/board.py` still calls `astimezone` itself, outside `UtcDatetime`.
- S0012: `target_times` uses `splitlines`, which also breaks on `\r`, `\x85` and similar characters. This is harmless for make's output.
- S0001 and S0019: two tests failed once under the parallel load of `make test` and passed alone: `tests/adapters/test_make_commands.py::test_command_reaching_its_time_limit_is_killed` and `tests/application/test_acceptance_ticks_closed.py::test_a_close_before_the_approval_runs_through_the_gate_and_is_booked_refused`. Nobody kept a traceback. This run's `make check` was green. If either recurs, it is a story.
- S0023, decision 55: `check_demos._story_findings` builds the backlog path by hand rather than through `work_item_path`. Draft S0032.
- S0025: the header comment of `image/entrypoint.sh:4` ("so either can remove the other's") is no longer true for the factory's files in the agent home. The draft S0032 does not take it in, because it is another module. It is a one-line fix for whichever story next touches the entrypoint.
- S0027: the S0009 entry of the decision log keeps its "Open:" text. The log is a history, and S0027's entry answers it. Nothing to do.
- S0029: the human's commit b642dd31 (the pins of Claude Code and the base image) travelled on S0029's branch. This is only noted.

## 5 Documentation

No contradiction found; I checked these, not a full cover-to-cover read:
- `README.md` (30 lines) names `make check` and points to the guides.
- In `docs/project-guide.md` I checked the sections the feature changed: the shipped agents' lessons (line 1296, which now matches the agent files, so S0028's remark is fixed), the template (line 1349, which matches `template/Makefile`), the duplicates report and the document check.

`make documents` prints `documents ok`. The project guide is 1,719 lines. That is under decision 44's mark of about 1,800 lines for bringing the split forward, but close to it.

## 6 Decisions taken for the human

`FEATURE.md` lists 55 decisions:
- 1 to 13 and 47 and 51 are the human's own answers.
- 14 to 46, 48 to 50 and 52 to 55 were taken by the session and are to be confirmed. The ones with lasting weight:
  - 14: `duplicates` is a record of `doing`.
  - 15: line-independent baseline keys.
  - 17: `sudo` is found on the `PATH`.
  - 20: `disk_low` is a machine stop at 5 GB, checked every tick.
  - 21: telemetry is JSON lines in the state directory, not in git.
  - 22: model time from `duration_api_ms`; no per-command split.
  - 23: disk record at the start and per acceptance prompt.
  - 25: the six `extra="ignore"` models.
  - 27: under `sudo`, the time limit plus 30 s of grace.
  - 28: the agent home's mode `3775`; the other writable files stay open.
  - 29: an empty health status written at start; a damaged file still reads as healthy.
  - 31: the demo check's shape.
  - 50, 53, 54: the template `Makefile`'s choices (no `documents`; `duplicates` without a baseline; the squash-merge `--grep`; exit status 5 accepted).
  - 55: S0023 past the cap, with the `work_item_path` fix deferred; S0032 proposes it now.
  - The leaves to change tests (32 to 43, 45, 46, 48, 49, 52) were each used as written, as their stories' reviewers checked.
- New from this acceptance, for the human: how `make mutants` should fit the acceptance stage (see 3).

## 7 Slow checks

Beyond `make check` and `make mutants`, the project offers `make duplicates` (a record: `0 new, 39 known, 0 gone`) and `make documents` (`documents ok`). There is no image scan or SBOM. The JUnit report `.reports/junit.xml` is written by `make test`.

## 8 Cost

The stories cost 194 runs, 148.0 min and $36.28 together. The median story is 6 runs and about $1.1.

Stories that stand out:
- S0023 (13 runs, 11.8 min, $2.59): three review rounds, past the send-back cap, over the hand-built backlog path (decision 55).
- S0006 (11 runs, $1.96): a review round over a duplicate-key fault that carried a line break.
- S0014 (10 runs, $2.14): the model time in the record and in the cost table, the widest change to existing tests (decisions 37 and 38).
- S0016 (9 runs, $1.86).
- S0021 (9 runs).
- S0029 (7 runs, 8.5 min, $2.10): the largest diff, the template `Makefile`, after two pre-checks.

The acceptance itself has cost one stalled run of 60 minutes so far, spent on `make mutants`.

## Proposed stories

- `drafts/F0012-S0031-the-no-state-refusals-of-the-acceptance-handlers.md`: pins the three refusals that mutmut showed no test reaches. This is S0007's pattern, applied to the acceptance handlers.
- `drafts/F0012-S0032-the-demo-checks-backlog-path-through-work-item-path.md`: the one-call fix that decision 55 deferred out of S0023.

## Log (append only)

1. stage feature stalled: timed out after 60 min; partial work committed
2. acceptor: accepted with drafts; 2 drafts proposed; make mutants 3911/4173 (partial: 1112 of the feature's 5285 mutants unchecked, see 3)

   The previous run stalled on `make mutants`. This run resumed mutmut's state with `timeout 570 make mutants FEATURE=F0012`. After its clean run, mutmut stayed at 4173/11898 and checked no further mutant. The killed and survived counts are therefore partial.

   1 Scope: none. Every item 1.1 to 1.10 has a merged story or a human change.
      - The done-line holds: `make check` is green with `make test` at 29.9 s (it was 177 s), `duplicates: 0 new, 39 known, 0 gone`, and `documents ok`.
      - `make mutants` runs but does not finish within one stage run.
      - The kill under sudo (S0024) and the sticky bit (S0025) are left to the real machine.
   2 Feature demo: green. One script ran against the real entry points:
      - the target times and `target_times`;
      - `duplicates`, `documents` and `check_demos`;
      - the low-disk detail and the disk line on the real file system;
      - the `disk-low` row and the round-cap answer setting the round to 0;
      - the commit prefix;
      - the template's targets;
      - `make mutants` picking F0012 from the branch.
   3 Mutants: 3911 killed, 258 survived, 4 timeout of the 4173 checked (93.7 %).
      - The 1112 unchecked mutants are in `stage`, `tick`, `claims`, `wiring`, `costs`, `domain.git` and others, where each mutant runs most of the suite.
      - Survivor groups:
        - The acceptance handlers' no-state refusals are untested (draft S0031).
        - Some wiring pass-throughs are untested: token, clock, out stream.
        - The import-time `STOP_TABLE` survivors are artefacts.
        - The rest are single-line messages and boundaries.
      - Human finding: as the Makefile stands, `make mutants` does not fit the 60-minute lease. I would put a time limit in the target and accept partial results.
   4 Noticed:
      - `used_bytes` can fail on files removed during the walk, so the record shows `unknown used`. Watch for this in the todo run.
      - Two tests flaked once under xdist (S0001, S0019).
      - `board.py` calls `astimezone` itself.
      - The `image/entrypoint.sh:4` comment is stale.
      - The `work_item_path` fix was deferred (draft S0032).
      - The baseline write `OSError` is not mapped to an exit status.
   5 Documentation: no contradiction in the sections the feature changed. The project guide is 1719 lines, close to decision 44's 1800.
   6 Decisions: 55 in FEATURE.md, with the lasting session decisions listed for the human to confirm. New for the human: how `make mutants` should fit the acceptance stage.
   7 Slow checks: only `duplicates` and `documents` beyond `check` and `mutants`. No image scan or SBOM.
   8 Cost: 194 runs, 148.0 min, $36.28. Stories that stand out:
      - S0023 (13 runs, $2.59): past the send-back cap.
      - S0006 (11 runs): a review round.
      - S0014 (10 runs).
      - S0029 ($2.10, 8.5 min).
      - The acceptance also cost one stalled 60-minute run, spent on mutants.

   Open: `/tmp/f12demo/demo.sh` and four small files in `/tmp` from this run are left; the sandbox refused their removal.
