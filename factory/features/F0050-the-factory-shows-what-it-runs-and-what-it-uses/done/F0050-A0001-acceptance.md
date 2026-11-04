---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 546
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T20:50:16.505539Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-11-04T20:51:59.833506Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-11-04T20:52:01.427505Z'
  stage: acceptance
- number: 4
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-04T21:05:11.697260Z'
  stage: acceptance
  run: d838ec979f1b447a9f2008cabc6ede12
- number: 5
  speaker: factory
  kind: done
  at: '2026-11-04T21:15:18.589309Z'
  stage: done
stories: [F0050-S0001, F0050-S0002, F0050-S0003, F0050-S0004, F0050-S0005, F0050-S0006, F0050-S0007, F0050-S0008]
outcome: accepted
---

# Acceptance of The factory shows what it runs and what it uses

## Recommendation

**accepted with stories.** All eleven scope items have their story, `make check` is green, and the feature's walk-through is green end to end: two refused result pushes are retried, and the record carries `machine`, `tools` and a `transcript` that matches its file. The records factory-vm wrote since S0003 show the machine's nine measures on every completed run, and a base image of 0.63 GB. Four findings are worth stories, and none of them breaks a promise. (1) In real Claude Code 2.1.318 transcripts the tool reader takes `tool_use` items from `api-request-blob` lines. Those lines carry `"timestamp": null`, so almost every tool's `seconds` is `null` on GitHub. (2) S0008's strict xfail: a hosting failure after the claim charges a crash for a stage in which no agent ran. (3) A push's reason spends two of its three lines on porcelain's `To <url>` and `Done`, and drops the server's `remote:` line. (4) The decision log still says a VM's `tmpfiles.d` rule removes transcripts, which feature decision 11 dropped.

## 1 Scope

Every scope item has a story, and every story stays inside the scope. I read the Descriptions and Interfaces of S0001 to S0008 and then the code they name.

- **One runtime per image (S0001).** `vm/Dockerfile` has an `install` stage and a final stage, each with `ARG AGENT_RUNTIME` and no default. The `case` at `vm/Dockerfile:15-19` refuses an empty or unknown value (run by hand, see 2). The final stage copies only `/opt/runtime/${AGENT_RUNTIME}` (`vm/Dockerfile:50`). The pins are 2.1.318 and 1.19.5. `vm/job-start.sh` builds with the instance's runtime. On factory-vm every record since S0003 has `base_image_bytes` 625 251 559 (0.63 GB, claude), which is under the 0.7 GB of S0001's criterion 9. The goal's "about 0.58 GB" is near.
- **The machine (S0002).** `MachineMeasures` holds the nine fields, read through `CgroupMachineReadings` (`src/factory/adapters/machine_files.py`) and `CostRecorder` (`src/factory/application/costs.py:120-121`). The contract went 4.1 → 4.2 → 4.3 → 4.4 over S0002, S0005 and S0006. All nine values are non-null in every completed record of S0005 to S0008 (75 runs). Example: peak 8.67 GB of 16.8 GB, waits close to zero.
- **Stops (S0003), one fetch (S0004), retries (S0008).** In the code as the Interfaces name them: `command_ending`, `NO_DETAIL`, `_same_line` in `StopService.raise_stop`, `Tick.run(fetched=...)`, `push_with_retries` (`src/factory/application/pushes.py`), `push_reason`, and `hosting_retry()` (`src/factory/adapters/pygithub_hosting.py:160`).
- **Transcripts (S0005, S0007) and tool calls (S0006).** `FileTranscriptStore`, `TranscriptKeeper`, `read_transcript` and `tool_uses` on both wrappers. `vm/setup.sh` has the step `transcripts`, and `vm/job-start.sh:85-90` checks the folder.
- **A goal the parts do not fully reach.** S0006 promises "the seconds they took" for each tool, so that the records show "where a run spent its time". In practice that part is lost for Claude Code. In the 21 records of S0007, every `Bash`, `Read`, `Edit` and `Write` entry has `seconds: null`, and only `StructuredOutput` is timed. The cause, found on this stage's own Claude Code 2.1.318 transcript: `claude_tool_uses` (`src/factory/domain/tool_uses.py:25-45`) reads `tool_use` items from every line. The `api-request-blob` lines repeat the conversation with `"timestamp": null` and overwrite the time of the `assistant` line, keyed by the same id. On that transcript, all lines give `Bash calls=49 seconds=None`. Only the `assistant` and `user` lines give `Bash calls=49 seconds=123.326`. The Interface allows `null` ("when the runtime gives no times"), so the contract holds, but the purpose does not. This is proposed story F0050-S0009.
- **Not yet on the machine.** No record of S0005 to S0008 has a `transcript`. `FACTORY_TRANSCRIPT_DIR` is not set on factory-vm yet, which needs a second run of `vm/setup.sh` after S0007. `feature.md`'s *The human's changes* does not name that step (listed under 6).
- **Out of scope** was respected: there is no retention code (decisions 10 and 11), nothing is created in a cloud, nothing about transcripts goes to GitHub, and there are no limits on the new measures.

## 2 The feature's smoke test

The walk-through of an operator after the merge, on the real code: one stage of a story on a real local remote. It uses the project's own fixtures (`tests/conftest.py`, loaded as a plugin) and the fake hosting service. The runtime is the fake one, but it leaves a Claude Code session file in the agent's home on the dataset and reads it through the real `ClaudeCodeRuntime.read_transcript` and `tool_uses`. The machine is a real `CgroupMachineReadings` on a slice folder whose totals rise during the run. The transcript folder is a real `FileTranscriptStore`. The remote's `pre-receive` hook refuses the second and third push with `Internal Server Error`, as GitHub did on 2026-11-04. After the stage the walk-through validates the pushed records against `src/factory/contract/cost-record.schema.json`, raises one stop three times, and reads the hosting retry.

Command (the module in a `mktemp -d` folder, removed by `trap`):

```bash
PYTHONPATH=tests uv run pytest -p conftest -s -q "$d/test_feature_walk.py" --rootdir "$PWD" -c pyproject.toml
```

The module:

```python
"""F0050 walk-through: one stage on a machine, with a transcript folder and two refused pushes."""
import gzip, hashlib, json, stat
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import jsonschema

from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.machine_files import CgroupMachineReadings
from factory.adapters.pygithub_hosting import hosting_retry
from factory.adapters.transcript_files import FileTranscriptStore
from factory.application.stops import StopService
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult
from factory.domain.stops import RepositoryStop
from stage_run_support import open_story, pushed_cost_records, pushed_cost_text, run_stage

SESSION = "0b7c4a1e-5d2f-4c3a-9e8b-1a2b3c4d5e6f"
PRESSURE = "some avg10=0.00 avg60=0.00 avg300=0.00 total={}\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"


def _event(kind, at, content):
    return {"type": kind, "timestamp": f"2026-11-04T10:00:{at}Z", "message": {"role": kind, "content": content}}


class ClaudeShaped(FakeAgentRuntime):
    """A scripted run that leaves a Claude Code session file and raises the slice's totals."""

    def __init__(self, claude, home, slice_folder):
        super().__init__()
        self._claude, self._home, self._slice = claude, home, slice_folder

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        folder = self._home / ".claude" / "projects" / "-work-checkout"
        folder.mkdir(parents=True, exist_ok=True)
        events = [
            _event("user", "00.000", "go"),
            _event("assistant", "10.000", [{"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "/work/checkout/SECRET_PATH.py"}}]),
            _event("user", "10.500", [{"type": "tool_result", "tool_use_id": "t1", "content": "x"}]),
            _event("assistant", "20.000", [{"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "make SECRET_COMMAND"}}]),
            _event("user", "22.000", [{"type": "tool_result", "tool_use_id": "t2", "is_error": True, "content": "boom"}]),
        ]
        (folder / f"{SESSION}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
        (self._slice / "cpu.stat").write_text("usage_usec 13500000\n")
        (self._slice / "cpu.pressure").write_text(PRESSURE.format(2250000))
        (self._slice / "memory.peak").write_text("8100000000\n")
        return super().run(request)

    def read_transcript(self, home, session):
        return self._claude.read_transcript(home, session)

    def tool_uses(self, transcript):
        return self._claude.tool_uses(transcript)


def test_walk(boundaries, human, agent_home, remote, tmp_path):
    slice_folder = tmp_path / "slice"
    slice_folder.mkdir()
    (slice_folder / "cpu.stat").write_text("usage_usec 1500000\n")
    (slice_folder / "cpu.pressure").write_text(PRESSURE.format(250000))
    (slice_folder / "memory.pressure").write_text(PRESSURE.format(0))
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemTotal:       15625000 kB\n")
    workspace, folder = tmp_path / "workspace", tmp_path / "transcripts"
    runtime = ClaudeShaped(ClaudeCodeRuntime("claude", tmp_path / "cs"), workspace / "home", slice_folder)
    staged = replace(
        boundaries, agent_runtime=runtime, transcripts=FileTranscriptStore(folder),
        machine=CgroupMachineReadings(slice_folder, meminfo),
        base_image_bytes=580_000_000, project_layer_bytes=0,
        settings=boundaries.settings.model_copy(update={"workspace": workspace, "transcript_dir": folder}),
    )
    open_story(staged, human, agent_home)
    # The remote lets the claim through, then refuses two pushes as GitHub did on 2026-11-04.
    hook, count = remote / "hooks" / "pre-receive", tmp_path / "pushes"
    hook.write_text(
        f'#!/bin/sh\nn=$(cat {count} 2>/dev/null || echo 0); echo $((n+1)) > {count}\n'
        'if [ "$n" -eq 1 ] || [ "$n" -eq 2 ]; then echo "Internal Server Error" >&2; exit 1; fi\n'
    )
    hook.chmod(0o755)
    runtime.queue(ScriptedRun(result=AgentRunResult(
        end_reason="completed", decision="doing", entry="tests written.",
        duration=timedelta(seconds=5), session=SESSION)))

    report = run_stage(staged)

    print("\nstage: next", report.next_stage, "| stall", report.stall)
    log = (tmp_path / "state" / "factory.log").read_text().splitlines()
    for line in log:
        if "push:" in line:
            print("log:", line.split(" ", 1)[1])
    print("waits:", [w.total_seconds() for w in staged.waiter.waits])
    [record] = pushed_cost_records(staged, remote)
    print("machine:", record.machine.model_dump() if record.machine else None)
    print("tools:", [t.model_dump() for t in record.tools or []])
    print("transcript:", record.transcript.model_dump() if record.transcript else None)
    kept = folder / record.transcript.path
    data = kept.read_bytes()
    print("file mode", oct(stat.S_IMODE(kept.stat().st_mode)),
          "| sha256 matches", hashlib.sha256(data).hexdigest() == record.transcript.sha256,
          "| lines", gzip.decompress(data).count(b"\n"))
    text = pushed_cost_text(staged, remote)
    print("SECRET in pushed records:", "SECRET" in text)
    schema = json.loads(Path("src/factory/contract/cost-record.schema.json").read_text())
    for line in text.splitlines():
        jsonschema.validate(json.loads(line), schema)
    print("records valid against contract", schema["x-records-contract"])

    stops = StopService(staged)
    for _ in range(3):
        stops.raise_stop(RepositoryStop(scope="repository", reason="fetch_failed",
                                        detail="fatal: unable to access", at=staged.clock.now()))
    log = (tmp_path / "state" / "factory.log").read_text().splitlines()
    print("stop lines after three raises:", sum("stop repository fetch_failed" in l for l in log))
    retry = hosting_retry()
    print("hosting retry: total", retry.total, "backoff", retry.backoff_factor, "PATCH", "PATCH" in retry.allowed_methods)
```

What it printed (the stage's own log lines first; tab characters as git wrote them):

```
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
2026-10-12T12:00:00Z push: retry 1 of 3 in 5 s: To /tmp/pytest-of-factory/pytest-1/test_walk0/origin/remote.git | !	refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001	[remote rejected] (pre-receive hook declined) | Done
2026-10-12T12:00:05Z push: retry 2 of 3 in 15 s: To /tmp/pytest-of-factory/pytest-1/test_walk0/origin/remote.git | !	refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001	[remote rejected] (pre-receive hook declined) | Done

stage: next doing | stall None
log: push: retry 1 of 3 in 5 s: To /tmp/pytest-of-factory/pytest-1/test_walk0/origin/remote.git | !	refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001	[remote rejected] (pre-receive hook declined) | Done
log: push: retry 2 of 3 in 15 s: To /tmp/pytest-of-factory/pytest-1/test_walk0/origin/remote.git | !	refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001	[remote rejected] (pre-receive hook declined) | Done
waits: [5.0, 15.0]
machine: {'base_image_bytes': 580000000, 'project_layer_bytes': 0, 'store_free_bytes': None, 'dataset_free_bytes': None, 'memory_peak_since_boot_bytes': 8100000000, 'memory_total_bytes': 16000000000, 'cpu_seconds': 12.0, 'cpu_wait_seconds': 2.0, 'memory_wait_seconds': 0.0}
tools: [{'tool': 'Bash', 'calls': 1, 'failed': 1, 'seconds': 2.0}, {'tool': 'Read', 'calls': 1, 'failed': 0, 'seconds': 0.5}]
transcript: {'path': 'F0001-S0001/80012c2a23d640b5879c0efa09a38d85.jsonl.gz', 'sha256': '1ab3b19bca210f47caa6cdf1f86043fbabaab4aae5e7ae0a373f203a51e31e98'}
file mode 0o600 | sha256 matches True | lines 5
SECRET in pushed records: False
records valid against contract 4.4
2026-10-12T12:00:20Z stop repository fetch_failed: fatal: unable to access
stop lines after three raises: 1
hosting retry: total 5 backoff 2 PATCH True
.
```

Green. The stage finished (`next doing`, no stall) after two retries with waits of 5 s and 15 s. The record has the nine measures (CPU 12.0 s and a CPU wait of 2.0 s, the differences of the slice's totals; memory 15 625 000 kB × 1024), two tool entries with failures and seconds, and no content of any call. The transcript is a gzip file with mode `0600` whose SHA-256 matches the record. A stop raised three times wrote its line once. The two free-space values are `None` here only because the fixture's `FakeDiskSpace` answers an unknown path with `FileNotFoundError` (`tests/disk_support.py:25`). On factory-vm they are filled (see 1).

Two more checks by hand:

```bash
snippet=$(sed -n 15,19p vm/Dockerfile | sed 's/^RUN //; s/\\$//'); for v in "" docker claude opencode; do AGENT_RUNTIME="$v" sh -c "$snippet"; echo "AGENT_RUNTIME='$v' -> exit $?"; done
```

```
AGENT_RUNTIME must be claude or opencode, not ''
AGENT_RUNTIME='' -> exit 1
AGENT_RUNTIME must be claude or opencode, not 'docker'
AGENT_RUNTIME='docker' -> exit 1
AGENT_RUNTIME='claude' -> exit 0
AGENT_RUNTIME='opencode' -> exit 0
```

The tool reader on a real Claude Code 2.1.318 transcript (this stage's own session file):

```
all lines:       [ToolUse(tool='Bash', calls=49, failed=3, seconds=None), ToolUse(tool='Read', calls=1, failed=0, seconds=None)]
assistant/user:  [ToolUse(tool='Bash', calls=49, failed=3, seconds=123.326), ToolUse(tool='Read', calls=1, failed=0, seconds=0.24)]
```

39 of the 42 lines with a `tool_use` item have `"timestamp": null`, and they are `api-request-blob` lines. The 21 records of S0007 show the same: every `Bash` entry has `seconds: null` (story F0050-S0009).

What the walk-through also shows: the reason in the retry lines is `To <url> | ! <ref>	[remote rejected] (pre-receive hook declined) | Done`. The hook's own message, which git prints as `remote: Internal Server Error` before the porcelain summary, falls out of the three lines (story F0050-S0011). The claim's push is not retried, by S0008's Interface: I first refused the first push and the stage ended in `PushFailed` from `src/factory/application/claims.py:70`. The image build and `vm/setup.sh` were not run: podman is not in this container, and both are the human's steps on factory-vm.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0001.** `curl` and `xz-utils` stay in the final stage (the human, entry 34: pinned by an earlier test, about 1 MB). The documenter noted `docs/operator-guide.md:337` ("opencode 1.19.3 asks `registry.npmjs.org`"), an observation not repeated on 1.19.5. It is dated by its version, so it is not wrong, only unconfirmed. Two statements rest on the coder's word, not on a run: the preflight's version check fails on an image of the other runtime, and the copied executable is self-contained. Both are in the human's build check.
- **S0002.** `make duplicates` has three vulture false positives on `MachineMeasures` fields (`src/factory/domain/cost_records.py:45-47`), carried as "new" through every later story. Today it reports `4 new, 41 known, 2 gone` and exits 1: the three, plus the claude/opencode `version_launch` similarity, which moved, and two gone entries. `security/duplicates-baseline.txt` is the human's (outside every write path), so this is no story: a refresh of the baseline is the human's. The image sizes are read once per choice (fixed in round 1). In the tests, `tests/cost_image_support.py` has a private `_launch` imported by another module, and the smaller-than-base case is tested twice in `tests/entry/test_wiring_stage_image_sizes.py`.
- **S0003.** A probe cut off by the factory's stop still clears `preflight_failed` (the coder judged it right: the machine's items had passed). A standing stop whose detail changes moves its `at` in the health status to the newest raise, as before. Test copies: `_answering` (`tests/application/test_preflight_stop_detail.py:37` and `tests/application/test_preflight_run.py:38`), the no-output `CheckResult` builder (`_ended` and `tests/domain/test_command_ending.py:22-29`), and `BACKLOG_PATH` (also in `tests/crash_support.py:31`). A process-streaming failure seen once in a red `make check` (entry 19); it passed on the rerun.
- **S0004.** The copy of `Outage` was moved into `tests/remote_outage_support.py` in the story itself. Reviewer notes on that module and on an `explicit` parameter name in `tests/application/test_tick_own_fetch.py:49-55`.
- **S0005.** The store makes missing subfolders with mode `0700`. This is documented as a fact of the code, but the Interface does not state it. The "one line" rule for `transcript: not kept` is pinned at the keeper's level only.
- **S0006.** `CostRecord` does not itself refuse an unsorted or duplicated `tools` list (the reading guarantees it). The fake runtime's `tool_uses` always returns `None`. `_events` in `src/factory/adapters/opencode_runtime.py:351` still uses `splitlines` (it skips a line it cannot read, so `tools` is not lost). `_staged` in `tests/application/test_stage_tool_uses.py` repeats `_with_transcripts` in `tests/application/test_stage_transcripts.py`.
- **S0007.** The fixed probe name `.job-start-probe` in `vm/job-start.sh:86`: two jobs that start at the same moment on one bucket share it (my reading, not a story's). The documenter left the `tmpfiles.d` sentence in `docs/decisions.md` (see 5).
- **S0008.** The xfail: a crash is charged for a stage in which no agent ran (story F0050-S0010). The stall push stays without a retry but carries git's reason. Reviewer notes on `tests/domain/test_push_reason.py:41-43` and `:85-89` (an overlapping row, constants in the middle of the module).

The test-helper copies (S0002, S0003, S0006, S0008) are not proposed as a story of their own. Each is a move under the standing leave, and the next story that touches those modules can make it.

## 5 The documentation as a whole

- **Contradiction:** `docs/decisions.md:1523`, the S0005 entry, says "The factory deletes no copy: a `tmpfiles.d` rule on a VM and a lifecycle rule on a bucket do (feature decision 10)". The operator guide (`docs/operator-guide.md:1641`) says "There is no `tmpfiles.d` rule", which is right by feature decision 11. Decision 11 has no entry in the log, because S0007's docs criterion said "none beyond S0005's". A reader of the log is told about a rule that does not exist (story F0050-S0012).
- **A gap in a history:** the records contract's version list (`docs/operator-guide.md:2072`) jumps from `4.0` to `4.2`. `4.1` (F0049-S0002, commit `4796912ee`) added the stop reason `stage_image_failed` to `stop-record`. The S0002 documenter saw this and could not find what it was (story F0050-S0012).
- **Otherwise one voice.** *Transcripts*, *The machine on the cost records* and *The tool calls on the cost records* read as one piece. They agree with each other and with the code, apart from the tool `seconds`, which the guide describes correctly from the line timestamps; the code reads them from the wrong lines (S0009). The pins (2.1.318, 1.19.5) agree in every place. `docs/project-guide/agents.md:102` uses 1.19.3 only as an example of output. `README.md` needed nothing.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit: decisions 1 to 11 (one runtime per image chosen at build; a throwaway install stage; the new pins; the slice's memory high-water mark; one `machine` object with the run's own CPU and waits; transcripts only inside the site, GitHub only numbers; the seams and contract pins of S0002 and S0008; no deletion by the factory; no retention on a VM).

From the journals:

1. S0001: the final stage copies only the resolved executable of the runtime (the human, entry 11). `curl` and `xz-utils` stay (entry 34). One `ARG AGENT_RUNTIME` per stage, none global (entry 34).
2. S0002: the job-profile sentence goes into the docs criterion, added by the reviewer under the human's leave (entry 38). `FakeDiskSpace` answers an unknown path with `FileNotFoundError` (entry 23). The vulture false positives were not put in the baseline (an agents' default; the baseline is the human's).
3. S0003: a tick whose probe was cut off by the factory's stop dispatches nothing. This came from a review finding, added to criterion 2 and the Interface by the coder and the reviewer. A cut-off probe still clears `preflight_failed` (the coder's default).
4. S0004: the seam `Tick.run(fetched=False)`. `scheduler.py:126` keeps its fetch (the human, entry 4).
5. S0005: the transcript is read from `settings.workspace / "home"`, not from `agent_home` (journal 18). opencode's transcript is its JSON event stream (journal 13). No deletion code (journal 9). Subfolders get `0700` (the code's default, not in the Interface).
6. S0006: one more narrow round at the round cap (entry 30). The fake runtime's `tool_uses` returns `None` (the coder's default).
7. S0007: no retention on a VM (entry 22). One more round at the round cap for two things (entry 35).
8. S0008: git's advice lines are dropped from the reason; `Git` gains `last_push_output()` (entry 14). Claims, stalls, acceptance and branch deletion carry git's reason but get no retry (the coder's reading of the Interface; the walk-through met it at the claim). Open: the strict xfail on the charged crash (S0010).
9. **Open for the human, not in `feature.md`'s *The human's changes*:** a second run of `vm/setup.sh` on factory-vm, so that `factory.env` gets `FACTORY_TRANSCRIPT_DIR` and the folder exists. Until then no transcript is kept (none of the 75 records of S0005 to S0008 has one).
10. **Open for the human:** refresh `security/duplicates-baseline.txt` (see 4).

Earlier tests changed, each with the leave the reviewers' entries name:

- S0001: `tests/test_stage_image.py` and `tests/test_vm_job_start.py` under `feature.md`'s S0001 leave, with the two lambda rows under entry 11. `tests/dockerfile_support.py` under the standing leave.
- S0002: `tests/conftest.py` (entry 18), `tests/disk_support.py` (entry 23), `tests/domain/test_contract.py` and `test_contract_version_4.py` (entry 9 and feature decision 7), `tests/entry/test_run_project_image_rebuild.py` (entry 18 and decision 8), `tests/test_docker_path_removed.py` (entry 23).
- S0004: six `run` signatures (entry 11), `recording_tick` in `tests/entry/test_run.py` (entry 18), `TICK_RUN` (entry 29), and `tests/application/test_tick.py` plus `test_run_fetch_before_tick.py` under the standing leave.
- S0005: five runtime doubles and `test_interfaces.py` (journal 18). Three contract pin files (journal 4).
- S0006: the same five and three pin files (entry 4). `test_stage_transcripts.py` and `stage_run_support.py` under the standing leave.
- S0008: `test_dispatcher.py`, `test_git_interface.py`, `test_interfaces.py`, `git_interface_support.py` and `test_checkout_hygiene_removed.py` (entry 14 and decision 9).
- S0003 and S0007: no earlier test changed.

No earlier test was changed without a named leave. No finding.

## 7 The slow checks

The project has no slow check beyond `make check` other than `make mutants` (see 3), and no image scan or SBOM. `make duplicates` is a record: `4 new, 41 known, 2 gone` (see 4). `make check` was green as I found it (`test: green (88.2 s)`, total coverage 99.25 %). From `.reports/junit.xml`: 9105 tests, 737 s summed over the workers. The slowest take 10.0 s each, the `ROOMY_LIMIT` time-limit tests (`tests/adapters/test_podman_timeout_status.py`, `test_make_commands.py::test_command_reaching_its_time_limit_is_killed`, `test_process_session.py::test_time_limit_ends_every_process_of_the_group`, `test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed`), as `CLAUDE.md` says they must.

Disk: at the acceptance, `/srv/factory/vm` has 28.3 GB free and 1.3 GB used. At the previous record (the acceptance's start) it had 28.3 GB free and 1.4 GB used. `state` and `/tmp` are unchanged at 0.0 GB used. There is no growth to explain: the use fell by 0.1 GB. Since S0002 the records show a free store of 28.4 to 29.6 GB and a free dataset of about 29.5 GB, steady.

## 8 Cost

The stories cost 150 runs, 287.2 min, 1537 turns, 4 885 822 tokens in (50 409 663 more from cache), 794 265 out, and $61.26.

Per story (completed runs, from the archived sidecars): S0001 19 runs and $7.72; S0002 21 and $11.83 (52.4 min); S0003 16 and $5.46; S0004 18 and $5.09 (45.4 min); S0005 16 and $9.77; S0006 20 and $7.54; S0007 21 and $6.01; S0008 19 and $7.84.

- **S0002 stands out at $11.83**, nearly twice the median. Its tests stage crashed twice after the tester had finished, most likely because the result push was refused during GitHub's incident of 2026-11-04 (entry 15). That cost the crash cap and is the very loss S0008 then fixed. On top of that came four rounds of questions on seams, contract pins and the docs criterion.
- **S0005 at $9.77** carried the human's correction that the factory deletes no transcripts (journal 9), which changed the story midway.
- **S0004** is cheap but slow (45.4 min): three questions, each about a test double that needed only the new `fetched` signature.

Human interventions: 24 questions answered, by cause question 21, round_cap 2 (S0006 entry 30, S0007 entry 35), crash_cap 1 (S0002 entry 15), with 2.8 h waited. The story that needed the human most is S0002, with six answers: the seams of the machine readings, the contract pins, the leaves for the conftest and `disk_support`, the retry after the crash cap, and the docs criterion's job-profile sentence (entry 38, after the reviewer found it missing and the human would not push to the branch). After it come S0005 (four answers and a correction) and S0007 (three, plus the closed and reopened pull request after the retention decision came in after review).

## Proposed stories

- `F0050-S0009-claude-codes-tool-calls-are-timed-from-their-own-lines.md`: the tool reader skips `api-request-blob` and other replay lines, so a real Claude Code record gets its tools' `seconds` (finding of 1 and 2).
- `F0050-S0010-a-hosting-failure-after-the-claim-charges-no-crash.md`: turns S0008's strict xfail into the fixed behaviour; the human picks the approach in the Description first (4 and 6).
- `F0050-S0011-a-push-reason-keeps-the-servers-words.md`: `push_reason` leaves out porcelain's `To <url>` and `Done` lines, so the server's `remote:` line is among the three (2).
- `F0050-S0012-the-decision-log-and-the-contract-history-match-the-feature.md`: a documentation repair: a decision-log entry for feature decision 11, the S0005 entry pointed at it, and `4.1` in the contract's version list (5).

## Journal

1. factory: started acceptance as vm.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit e2779058da94711faf7d42938951dd69e8efe50b.
3. factory: started acceptance as vm.
4. acceptance-reviewer: accepted with stories; 4 stories proposed (F0050-S0009 to F0050-S0012)

   1 Scope: every scope item has its story and no story goes beyond the scope. factory-vm's records show all nine machine values on all 75 runs of S0005 to S0008, and a 0.63 GB claude base image. One goal is missed in practice: in real Claude Code 2.1.318 transcripts, `claude_tool_uses` reads replayed `api-request-blob` lines (`"timestamp": null`), so nearly every tool's `seconds` is null (S0009). No transcript has been kept on factory-vm yet, because `vm/setup.sh` has not been run again.
   2 Smoke test: green. One stage on a real local remote whose hook refuses two pushes: retried after 5 s and 15 s, `next doing`, no stall. The record carries `machine`, `tools` and `transcript` (mode 0600, SHA-256 matches, no call content) and validates against contract 4.4. A stop raised three times logs once. The hosting retry is 5/2/PATCH. The Dockerfile's `AGENT_RUNTIME` check refuses '' and 'docker'. Seen in the walk: the push reason keeps porcelain's `To <url>` and `Done` and loses the server's `remote:` line (S0011).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0008's strict xfail, a crash charged for a stage in which no agent ran (S0010). `make duplicates` stays at 4 new / 2 gone, from vulture false positives on `MachineMeasures` (the baseline is the human's). Several test-helper copies remain, left to the standing leave. `curl` and `xz-utils` stay, by the human's word.
   5 Documentation: `docs/decisions.md:1523` still names a VM `tmpfiles.d` rule, which contradicts decision 11 and the operator guide, and decision 11 has no log entry. The contract's version list skips 4.1 (`stage_image_failed`). Both go into S0012. Otherwise the documents read as one voice.
   6 Decisions: feature decisions 1 to 11 plus the journals' answers and defaults are listed. Open for the human: run `vm/setup.sh` again for `FACTORY_TRANSCRIPT_DIR`, refresh the duplicates baseline, and pick S0010's approach. Every earlier test was changed under a named leave.
   7 Slow checks: nothing beyond `make check`, which was green (99.25 %). The slowest tests are the 10 s `ROOMY_LIMIT` ones. Disk went from 1.4 GB to 1.3 GB used, so there is no growth.
   8 Cost: 150 runs, 287.2 min, $61.26. S0002 stands out at $11.83: two tests-stage crashes from refused pushes during GitHub's incident reached the crash cap. 24 questions answered (question 21, round_cap 2, crash_cap 1), 2.8 h waited. S0002 needed the human most (six answers).
5. factory: done (pull request merged); cost: 1 runs, 13.1 min, 60 turns, 164029 tokens in (6331793 more from cache), 53600 out, $3.65
