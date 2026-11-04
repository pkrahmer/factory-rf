---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 551
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T23:11:57.171834Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-11-04T23:13:48.429173Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-11-04T23:13:50.081285Z'
  stage: acceptance
- number: 4
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-04T23:21:49.353432Z'
  stage: acceptance
  run: 15edd6ea0ecb4eef9cffcbeb9e5ba5bf
stories: [F0050-S0001, F0050-S0002, F0050-S0003, F0050-S0004, F0050-S0005, F0050-S0006, F0050-S0007, F0050-S0008, F0050-S0009, F0050-S0010, F0050-S0011, F0050-S0012]
outcome: null
---

# Acceptance of The factory shows what it runs and what it uses

## Recommendation

**accepted with stories.** All ten scope items and the four follow-up stories from A0001 (S0009 to S0012) are built. `make check` is green, and the feature's walk-through is green end to end. Claude Code tool times now survive the `api-request-blob` replays. A refused push's reason keeps the server's `remote:` line. A hosting outage after the claim charges no crash, and the stage runs once the service is back. The decision log and the contract history are repaired. Two small findings are worth stories, and neither breaks a promise. (1) Real git writes `error: failed to push some refs to '<url>'`, which S0011's examples did not hold. That line takes one of the reason's three places, so a server that writes two `remote:` lines loses its first (S0013). (2) The decision log still says that the time per tool command is not recorded, which S0006 superseded (S0014).

## 1 Scope

The first acceptance (F0050-A0001, `done/`) went through S0001 to S0008 against every scope item and found each one built and inside the scope. I did not repeat that reading. This acceptance checks the four stories that came from it, and whether the whole now reaches the Goal.

- **S0009, tool times from their own lines.** `claude_tool_uses` (`src/factory/domain/tool_uses.py:39-47`) now takes a `tool_use` only from an `assistant` line and a `tool_result` only from a `user` line. It keeps the first of two copies of an id through `setdefault`. This closes A0001's "goal the parts do not fully reach": the walk-through's transcript has two `api-request-blob` replays with `"timestamp": null`, and still gives `Bash seconds 2.0` and `Read seconds 0.5` (see 2).
- **S0010, no crash for a hosting failure after the claim.** `StageLauncher._start` (`src/factory/application/stage.py`) catches only a `HostingServiceError` from `ensure_pull_request`, releases the claim in one commit (`<id>: claim released: hosting failed`), pushes it through `push_with_retries`, and re-raises with a bare `raise`. S0008's strict xfail is gone. The human chose a consequence (S0010 journal 9): each release moves the branch, so every failing tick counts its handler error from 1 and an outage never reaches the cap. The walk-through shows that.
- **S0011, the server's words.** `push_reason` (`src/factory/domain/git.py:156-176`) drops `To <url>` and `Done` and collapses whitespace. The walk-through's retry lines now begin with `remote: Internal Server Error`. One line that real git writes was not in S0011's examples, see 2 and proposed story S0013.
- **S0012, the documents.** `docs/decisions.md:1545` has the entry for feature decision 11. The S0005 entry no longer promises a VM `tmpfiles.d` rule. The contract list in `docs/operator-guide.md:2072` names `4.1`.
- **The Goal as a whole.** The image is built for one runtime (0.63 GB on factory-vm per A0001). The pins are current. Every completed record carries `machine`, `tools` and, when the folder is set, `transcript`. A stop says why and is logged once. There is one fetch per iteration. Refused pushes and hosting calls are retried and logged. Nothing is left outside the scope. **Out of scope** is respected: there is no retention code, no cloud resource, no transcript on GitHub, no limit on the new measures, and the cap of three stays (S0010 changed how the count restarts, not the cap).

Finding: none of weight.

## 2 The feature's smoke test

The operator's walk-through after the merge, on the real code, in two parts. (a) A stage of a story runs on a real local remote. The fake runtime leaves a Claude Code 2.1.318-shaped session file, with `api-request-blob` replays whose `timestamp` is `null`, and the real `ClaudeCodeRuntime` reads it. The machine is a real `CgroupMachineReadings`, the folder a real `FileTranscriptStore`. The remote's `pre-receive` hook refuses the second and third push with `Internal Server Error`. After the stage the script validates the records against the contract schema, raises one stop three times and reads the hosting retry. (b) In the recovery proof's world, three ticks in a row meet a hosting failure right after the claim, and then a tick meets none.

Command (the module in a `mktemp -d` folder removed by `trap`, run from the checkout's root):

```bash
PYTHONPATH=tests uv run pytest -p conftest -s -q "$d/test_feature_walk.py" --rootdir "$PWD" -c pyproject.toml -p no:cacheprovider 2>&1 | grep -v '^Bytecode'
```

The module:

```python
"""F0050 walk-through: one stage with a transcript folder, refused pushes, and a hosting outage after the claim."""
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
from git_support import PIPELINE_YAML
from log_support import state_log_lines
from proof_support import STAGE, branch_state, completed, head_state, run_ticks
from stage_run_support import open_story, pushed_cost_records, pushed_cost_text, run_stage

SESSION = "0b7c4a1e-5d2f-4c3a-9e8b-1a2b3c4d5e6f"
PRESSURE = "some avg10=0.00 avg60=0.00 avg300=0.00 total={}\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"


def _event(kind, at, content):
    return {"type": kind, "timestamp": None if at is None else f"2026-11-04T10:00:{at}Z",
            "message": {"role": "assistant" if kind == "api-request-blob" else kind, "content": content}}


class ClaudeShaped(FakeAgentRuntime):
    """A scripted run that leaves a Claude Code 2.1.318-shaped session file and raises the slice's totals."""

    def __init__(self, claude, home, slice_folder):
        super().__init__()
        self._claude, self._home, self._slice = claude, home, slice_folder

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        folder = self._home / ".claude" / "projects" / "-work-checkout"
        folder.mkdir(parents=True, exist_ok=True)
        read = [{"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "/work/checkout/SECRET_PATH.py"}}]
        bash = [{"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "make SECRET_COMMAND"}}]
        events = [
            _event("user", "00.000", "go"),
            _event("assistant", "10.000", read),
            _event("api-request-blob", None, read),  # the replay that erased times before S0009
            _event("user", "10.500", [{"type": "tool_result", "tool_use_id": "t1", "content": "x"}]),
            _event("assistant", "20.000", bash),
            _event("api-request-blob", None, read + bash),
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


def test_outage_after_claim(world, work_item):
    for tick in (1, 2, 3):
        world.hosting.fail_next("create_pull_request")
        run_ticks(world)
        state = branch_state(world, work_item)
        print(f"\noutage tick {tick}: claim", state.claim, "| crashes", state.crashes,
              "| agent runs", len(world.agent_runtime.requests()))
    for line in state_log_lines(world.state):
        if "handler error" in line or "error cap" in line:
            print("log:", line.split(" ", 1)[1][:110])
    definition = world.boundaries.pipeline_reader.parse(PIPELINE_YAML)
    world.agent_runtime.queue(completed(definition.stages[STAGE].next[0]))
    run_ticks(world)
    head = head_state(world, work_item)
    print("after the outage: crashes", head.crashes,
          "| crash entries", [(r.speaker, r.kind) for r in head.journal].count(("factory", "crash")),
          "| agent runs", len(world.agent_runtime.requests()), "| stage", head.stage)
```

What it printed (the stage's own log lines are interleaved):

```
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
2026-10-12T12:00:00Z push: retry 1 of 3 in 5 s: remote: Internal Server Error | error: failed to push some refs to '/tmp/pytest-of-factory/pytest-0/test_walk0/origin/remote.git' | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)
2026-10-12T12:00:05Z push: retry 2 of 3 in 15 s: remote: Internal Server Error | error: failed to push some refs to '/tmp/pytest-of-factory/pytest-0/test_walk0/origin/remote.git' | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)

stage: next doing | stall None
log: push: retry 1 of 3 in 5 s: remote: Internal Server Error | error: failed to push some refs to '/tmp/pytest-of-factory/pytest-0/test_walk0/origin/remote.git' | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)
log: push: retry 2 of 3 in 15 s: remote: Internal Server Error | error: failed to push some refs to '/tmp/pytest-of-factory/pytest-0/test_walk0/origin/remote.git' | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)
waits: [5.0, 15.0]
machine: {'base_image_bytes': 580000000, 'project_layer_bytes': 0, 'store_free_bytes': None, 'dataset_free_bytes': None, 'memory_peak_since_boot_bytes': 8100000000, 'memory_total_bytes': 16000000000, 'cpu_seconds': 12.0, 'cpu_wait_seconds': 2.0, 'memory_wait_seconds': 0.0}
tools: [{'tool': 'Bash', 'calls': 1, 'failed': 1, 'seconds': 2.0}, {'tool': 'Read', 'calls': 1, 'failed': 0, 'seconds': 0.5}]
transcript: {'path': 'F0001-S0001/2910a9b15dbd489398151b3d40d12c8c.jsonl.gz', 'sha256': '6507a668cc0d4e5405e8ed36fde842b288929dff957cc42e13802f9a387ae406'}
file mode 0o600 | sha256 matches True | lines 7
SECRET in pushed records: False
records valid against contract 4.4
2026-10-12T12:00:20Z stop repository fetch_failed: fatal: unable to access
stop lines after three raises: 1
hosting retry: total 5 backoff 2 PATCH True
.2026-10-12T12:00:00Z handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injected failure

outage tick 1: claim None | crashes 0 | agent runs 0
2026-10-12T12:00:00Z handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injected failure

outage tick 2: claim None | crashes 0 | agent runs 0
2026-10-12T12:00:00Z handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injected failure

outage tick 3: claim None | crashes 0 | agent runs 0
log: handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injecte
log: handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injecte
log: handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injecte
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
after the outage: crashes 0 | crash entries 0 | agent runs 1 | stage tests
.
```

**Green.** Part (a): the stage finished (`next doing`, no stall) after two retries, with waits of 5 s and 15 s. The record has the nine machine measures, and the two tool entries are timed despite the replayed lines (S0009). The transcript is a `0600` gzip file whose SHA-256 matches the record, and no call's content reached the record. A stop raised three times was logged once. The two free-space values are `None` only because the fixture's `FakeDiskSpace` does not know the path (as in A0001). Part (b): three failing ticks leave no claim and charge no crash. Each logs `1 of 3`, and no error cap is reached, as the human chose (S0010 journal 9). The fourth tick runs the agent once, still with no crash.

**One finding from the walk-through.** The retry reason is `remote: Internal Server Error | error: failed to push some refs to '<url>' | ! <ref> [remote rejected] (pre-receive hook declined)`. Git 2.39 adds the `error: failed to push some refs to` line. It is not in S0011's examples (S0011 criterion 1), and its end-to-end test checks only that `remote:` and `[remote rejected]` are present. The line repeats what the ref line says and takes one of the three places. With two `remote:` lines, today's code gives `remote: request id 1234 | error: failed to push some refs to '/srv/project.git' | ! refs/heads/b:refs/heads/b [remote rejected] (pre-receive hook declined)`, so the server's first line is lost. I ran that by hand: it is the smoke command of proposed story S0013. This is no broken promise: a one-line server message, like GitHub's of 2026-11-04, stays in. The image build and `vm/setup.sh` were not run, because podman is not in this container (as in A0001).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

The items of S0001 to S0008 are collected in A0001's section 4. Of those, S0009, S0010 and S0012 closed the tool times, the xfail and the two document texts. These are still open:
- the vulture false positives on `MachineMeasures` (see 7);
- the test-helper copies, which a later story can move under the standing leave;
- the `.job-start-probe` name shared by two jobs on one bucket;
- the `0700` mode of the store's subfolders, which no Interface states.

New from S0009 to S0012:

- **S0009.** A malformed `tool_use` or `tool_result` item on a line of another type is now skipped. Before, it made the whole transcript unreadable (`None`). The coder (journal 10), the reviewer and the documenter judged this as the Interface wants. The first copy now wins for results as well as uses. That went beyond the Interface, and the reviewer added criterion 7 for it. The documenter saw that `docs/decisions.md:407`, the F0012 entry "The time per tool command inside a run is not recorded", is stale since S0006, and left it (proposed story S0014).
- **S0010.** When the release push fails, the release commit stays unpushed in the factory's local checkout (the coder, journals 13, 20 and 28). The next tick starts from the remote, so this is harmless. The coder and the tester could not carry the human's answers into the work item's criteria: those edits were dropped from the take as outside their write paths (journals 11, 24 and 26). The reviewer made the edits in journal 30. This is a property of `factory/pipeline.yml`, which is the human's, so it is listed under 6 and no story is proposed.
- **S0011.** No row has a `To ` line with leading spaces. The code strips before it checks (the reviewer's note, and intake). This is not proposed: the reviewer read the code, and it handles that case.
- **S0012.** Nothing noticed.

## 5 The documentation as a whole

- **Contradiction inside the decision log.** `docs/decisions.md:407` says that the time per tool command inside a run is not recorded. `docs/decisions.md:1537` (S0006) says every completed record has `tools` with the `seconds` of each tool, and the operator guide (`docs/operator-guide.md:2222`) describes how they are read. The old entry has no `Superseded` line, unlike the log's other superseded entries (for example `:152` and `:291`). A reader of the log is told two things (proposed story S0014).
- **A detail of the push reason.** `docs/operator-guide.md:2502` says that the frame is left out "so the server's own `remote:` lines stay in". With two of them that is not true today, because git's `error: failed to push some refs to` line takes a place. That is the behaviour S0013 fixes, and its docs criterion corrects the paragraph. Its example on the `unreachable` reason is still right.
- **S0010's text** (`docs/operator-guide.md:2512` and the decision log's `:1511`) matches the walk-through: the claim is released, each failing tick counts from 1, no error stop is posted, and the factory retries every tick.
- **S0012's repairs hold.** `tmpfiles.d` appears only in the new entry for decision 11 (`docs/decisions.md:1549`), which says there is none, and in the guide's matching sentence (`:1641`). The version list names `4.1`.
- `README.md` needed nothing for this feature. Every other text I read agrees with the code.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit: decisions 1 to 12. A0001's section 6 already lists 1 to 11 and the journal defaults of S0001 to S0008. Decision 12: S0010 releases the claim on a `HostingServiceError` after it. Opening the pull request before the claim was rejected, because it would open a race between two instances.

From the journals of S0009 to S0012:

1. S0009: the first copy of an id wins, for `tool_result` items on `user` lines as well (the coder's reading; criterion 7 was added in review). The new tests are in a module of their own, and no earlier test changed (the human, journal 4).
2. S0010: approach (a) (the human, journal 4). A long outage after the claim never reaches the error cap and posts no error stop: the factory retries every tick (the human, journal 9, option A). **To revisit later:** the claim and release commits that such an outage adds to the branch, two per tick. The human accepted them "for this story" and noted them for later planning (journal 9). A failed release push is logged, the original error is raised, and the claim stays, so a crash follows as before (the human, journal 14).
3. S0011: only an exact `Done` and the `To ` prefix count as the frame. Each run of whitespace becomes one space (the coder's choice: collapse after the filter).
4. S0012: the docs-only story ran through the coder and the reviewer with an empty diff, as the pipeline requires.
5. **Open for the human, pipeline:** the coder's and the tester's write paths do not include their own work item's Description. A human answer that changes a criterion is carried in only by intake or the reviewer (S0010 journals 11, 24, 26 and 30). R5 says the Description is rewritten when the journal changes it. Whether `factory/pipeline.yml` should give the coder that path is the human's.
6. **Still open from A0001, as far as this repository shows:**
   - a second run of `vm/setup.sh` on factory-vm, for `FACTORY_TRANSCRIPT_DIR`. I cannot see the machine from here.
   - a refresh of `security/duplicates-baseline.txt` (see 7).

Earlier tests changed in S0009 to S0012, each with the leave the reviewers name:

- S0009: none (`tests/domain/test_tool_uses_replayed_lines.py` is new).
- S0010: `tests/application/test_hosting_failure_after_claim.py`. The `xfail` mark came off (the human's leave, journal 4, feature decision 12). `test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run` was deleted, with its now unused `branch_state` import (the human's leave, journal 14). Feature decision 12 names only the first of the two leaves, while journal 14 holds the second. The fixture `failed_after_claim` moved to `tests/conftest.py` under the standing leave (journal 26).
- S0011: `tests/application/test_push_retry.py`. Helpers moved to the new `tests/push_retry_support.py` under the standing leave, and every test keeps its name (reviewer, journal 9).
- S0012: none.

No earlier test was changed without a named leave.

## 7 The slow checks

The project offers nothing beyond `make check` but the records `make duplicates` and `make documents`. Both ran today.
- `make documents`: `documents ok`.
- `make duplicates`: `4 new, 41 known, 2 gone`, and it exits 1. The four new findings are the same through every story since S0002: three vulture false positives on `MachineMeasures` fields (`src/factory/domain/cost_records.py:45-47`) and the moved `version_launch` similarity between the two runtimes. The baseline is the human's (item 6 under 6).

`make test`: 9153 tests, 947 s of test time on every core, 117.9 s wall. The slowest, about 10 s each, are the tests that wait out `ROOMY_LIMIT`: `tests/adapters/test_podman_timeout_status.py` (both rows), `test_opencode_resume_session`, `test_claude_runtime_resume`, and two rows of `test_process_session`. None of them is new in this feature's last four stories.

Disk: `disk acceptance` (1.3 GB used under `/srv/factory/vm`, 0.0 GB under state and `/tmp`) equals `disk start` exactly. There is no growth.

## 8 Cost

The stories cost 188 runs, 325.0 min, 1802 turns and $69.91, which is about $5.83 a story. The early stories were the heavy ones:
- **S0002** ($11.83, 52.4 min, 21 runs): the nine measures, three contract seams, five human answers and two crashes up to the crash cap.
- **S0005** ($9.77, 41.5 min): the transcript keeper, four answers.
- **S0004** (45.4 min for a small change): four answers about the seam `Tick.run(fetched=...)`.

The four follow-ups from A0001 were cheap: S0009 $2.12, S0010 $4.33, S0011 $1.37, S0012 $0.82 (together $8.64).

Human interventions: 28 questions answered (25 questions, 2 at the round cap, 1 at the crash cap), and 3.4 h of waiting. By answers in the journals:
- S0002 needed the human most: five answers, and the crash cap. Its seams and contract pins needed leaves (feature decisions 7 and 8).
- S0004 and S0005 had four answers each.
- S0010 had three. One was a conflict that only the tester found, between the count per remote state and "three failing ticks reach the cap" (journal 8). The other was a leave to delete an S0008 test (journal 13).
- S0006 and S0007 each reached the round cap once.

## Proposed stories

- `backlog/F0050-S0013-a-push-reason-leaves-out-gits-failed-to-push-line.md`: git's own `error: failed to push some refs to '<url>'` line takes one of the reason's three places, so a second `remote:` line of the server pushes the first one out (sections 2 and 5).
- `backlog/F0050-S0014-the-decision-log-marks-the-tool-time-entry-superseded.md`: the F0012 entry "The time per tool command inside a run is not recorded" contradicts S0006's entry and has no `Superseded` line (sections 4 and 5).

## Journal

1. factory: started acceptance as vm.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit b3db17e4e86a4f6081415ef1d65e51a3dc80fdaa.
3. factory: started acceptance as vm.
4. acceptance-reviewer: accepted with stories; 2 stories proposed (F0050-S0013, F0050-S0014). `make check` is green and the feature's walk-through is green. Two small findings are worth stories, and neither breaks a promise.
   1 Scope: every scope item is built. S0009 to S0012 close A0001's findings: tool times from their own lines, no crash after a hosting failure, the server's `remote:` line, the two document repairs. Nothing is outside the scope or against Out of scope.
   2 Smoke test: green. One stage with two refused pushes keeps its transcript, its nine machine measures and its tool times, despite `api-request-blob` replays with a null timestamp; the records are valid against contract 4.4. Three hosting failures after the claim leave no claim, charge no crash and each log `1 of 3`; the next tick runs the agent. Finding: git 2.39's `error: failed to push some refs to '<url>'` line takes one of the reason's three places, so a second `remote:` line pushes the server's first one out (S0013).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: in S0009, a malformed item on a foreign line is now skipped. In S0010, an unpushed release commit stays local, which is harmless, and the coder and tester could not write criterion edits into their own work item. In S0011, there is no indented `To ` row, and the code handles that case. The open items of A0001 carry on (vulture false positives, test-helper copies, `.job-start-probe`, subfolder mode 0700).
   5 Documentation: `docs/decisions.md:407` (F0012, "time per tool command is not recorded") contradicts S0006's entry and has no Superseded line (S0014). The guide's "`remote:` lines stay in" is not true with two of them (S0013). Everything else agrees with the code.
   6 Decisions: feature decisions 1 to 12 and the journal defaults are listed for the human. To revisit: two branch commits per tick during an outage. Open for the human: the coder's write paths and the work item's Description in `factory/pipeline.yml`; a second run of `vm/setup.sh` for `FACTORY_TRANSCRIPT_DIR`; the duplicates baseline. Every earlier test change has a named leave, though S0010's deletion leave is in journal 14 and not in feature decision 12.
   7 Slow checks: `make documents` is ok. `make duplicates` gives `4 new, 41 known, 2 gone` (the same four since S0002; the baseline is the human's). The slowest tests are about 10 s each, the `ROOMY_LIMIT` waits. Disk at acceptance equals disk at start, with no growth.
   8 Cost: 188 runs, 325.0 min, $69.91. S0002 was the most expensive ($11.83, five answers, crash cap) and needed the human most. The four follow-ups cost $8.64 together. 28 questions answered (25 questions, 2 at the round cap, 1 at the crash cap), 3.4 h waited.
