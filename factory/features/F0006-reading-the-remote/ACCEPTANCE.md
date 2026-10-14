---
stage: accept
pr: 78
blocked: null
comments_seen: 1
round: 0
attempts: 0
stories: [F0006-S0001, F0006-S0002, F0006-S0003, F0006-S0004, F0006-S0005, F0006-S0006, F0006-S0007]
---
# Acceptance of Reading the remote

## Verdict

**accepted with drafts.** The feature does what `FEATURE.md` promised. Every clause of the Goal shows in one feature demo, run end to end against the real entry points, and the demo is green. Each scope item has its story, and nothing outside the scope was built. `make check` is green at 99.33 %. A hand-mutation pass killed 24 of 25 mutants.

Two findings are worth stories, and neither is a broken promise:

- The documentation lags behind what F0006 built. The worst case is in the operator guide. It says an unreadable work item file is cleared by closing the pull request (it is not). It also says a `reject` event "is only recorded", when it is in fact a counted error: one report after three ticks, and then it holds back all new work.
- The one surviving mutant shows that a report failing with something other than a hosting-service error has no criterion.

I do not count the documentation finding as "not accepted". No command runs the tick yet, because `factory-run` arrives with F0010, so no operator can reach the misdescribed behaviour today. It must be repaired before F0010 makes the tick runnable. Drafts S0008 and S0009.

## 1 Scope

None. Every scope item has a story that built it:

| Scope item (`FEATURE.md`) | Story | Where |
|---|---|---|
| Reading work items (R18, ST6.1) | S0001 | `src/factory/application/work_items.py` `RemoteWorkItems.read`/`list_stories`; `WorkItemSnapshot`, `StoryFile` in `src/factory/domain/work_item.py` |
| The evaluation in four tiers | S0002 | `src/factory/domain/evaluation.py` `evaluate`, `src/factory/domain/events.py`, `src/factory/application/watcher.py` |
| The dispatcher and the tick status (R28, SI2.4, GH5.4) | S0003 | `src/factory/application/dispatcher.py`, `src/factory/domain/tick_status.py` |
| The tick (GH5.2, GH5.3, GH5.5, GH1.5) | S0004 | `src/factory/application/tick.py` |
| The move rule (ST2.3, ST2.4) | S0005 | `src/factory/domain/move_rule.py`, `RemoteWorkItems.last_stage_change`, `reject` in `evaluate` |
| The command line (SI3.1, SI3.2) | S0006 | `src/factory/entry/watch.py`, `src/factory/domain/board.py`, `src/factory/application/board.py` |
| The production wiring (Q20) | S0007 | `src/factory/entry/wiring.py` `build_handlers`, `handler_factory`, `NOT_YET_HANDLED`, `agent_environment`; `src/factory/application/handlers/run.py` |

The Goal's "Done when" clauses, each seen in section 2:

- **A hand push is seen past a stale local branch.** Step 3: the checkout stood on a local `work-item/F0001-S0001` at `doing`. The tick's event carried the human's pushed commit, and the local branch was gone afterwards.
- **A failed fetch is a reported repository stop.** Step 5: `fetch_failed` appeared in the health status with stamped log lines, and the next tick cleared it.
- **A rejected push is judged from the remote's state, with at most one report.** Step 7: ticks 7–12 gave `error`, then `crash` with `error`, `error`, `reported`, `capped`, `capped`. Exactly one factory post was made.
- **A fresh clone continues every work item.** Step 2: both clones evaluated the same event at the same remote state, and the fresh clone's tick ran the stage.
- **An event kind without a handler is a counted error.** Steps 3, 6, 7 and 9: `UnhandledEvent: no handler for event kind …`.
- **No merge method is misread.** Step 6: merge, squash and rebase each gave `merged`. Step 9 shows the rule still fires on a real hand change.
- **The watcher's command line has no `--follow`.** Step 0: the installed `factory-watch` exits 2 on `--follow`, and its help has no `follow`.
- **Every handler built is registered, and the rest are in `NOT_YET_HANDLED`.** Step 0 prints the eleven kinds. Step 1 runs a stage through `handler_factory` with `production_environment()`.

Out of scope stays out: there are no human-act, crash or acceptance handlers, no preflight, no scheduler loop and no `build_boundaries`. One consequence lies outside this feature: until F0007 and F0008 register their handlers, the first work item to reach an approval stage gives `hand_over`. That event is counted, reported once and then capped, and it holds back all new work (step 3 onward). This is the design (decision 14), but the operator guide does not say it (section 5).

## 2 Feature demo

The walk-through is the operator's view of one factory instance working through a feature. It uses the production handler factory, a real bare remote with a human clone (`tests/human_clone.py`), `GitCli`, `FakeHostingService` and `FakeAgentRuntime`. The runtime is wrapped so that one run can let the human push during it. The installed `factory-watch` is called as a process. The pipeline is intake → doing → approval → done, with three stories started by the human.

Steps:

0. The command line.
1. A tick in the operator's checkout runs the first stage.
2. A fresh clone sees the same event and runs the next stage.
3. The human pushes while the operator's checkout holds a stale local branch.
4. `run_watch` prints its view.
5. A fetch fails, then recovers.
6. Merges by the three methods, each on a copy of the remote, then the human's squash merge on the real one.
7. The human archives S0001. During S0002's run the human pushes to its branch, so the result push is rejected. The ticks after it show how that is judged, then the human pushes again.
8. A branch created by hand at `approval` (an observation, see section 6).
9. A hand-made stage change on a branch the factory wrote.

Run from the repository root, with the script outside the repository:

```bash
uv run python /tmp/f6demo/demo.py; echo "exit $?"
```

The script, `/tmp/f6demo/demo.py`:

````python
"""Feature demo of F0006: the factory reads the remote, tick after tick, through its real entry points."""

import io
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "/work/factory-rf/tests")
from git_support import STORY_FORM, TEST_IDENTITY, commit_all, install_agents, run_git, write_files
from human_clone import HumanClone

from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime, ScriptedRun
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.agent_runtime import AgentRuntime
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick
from factory.application.watcher import Watcher
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult, TokenCounts
from factory.domain.git import GitOptions
from factory.entry.watch import run_watch
from factory.entry.wiring import NOT_YET_HANDLED, handler_factory, production_environment

root = Path(tempfile.mkdtemp())
PIPELINE = """contract: "1.0"
attempts_cap: 3
project_commands:
  check: {time_limit: 5}
  lint: {time_limit: 5}
  test: {time_limit: 5}
roles:
  intake: {write_paths: ["{work_item}"], time_limit: 10}
  coder: {write_paths: ["src/*"], time_limit: 10}
stages:
  intake: {role: intake, next: [doing]}
  doing: {role: coder, next: [approval]}
  approval: {approval: true, next: [done, doing]}
  done: {}
"""
STORY = """# {title}

## Description

Say hello.

## Interface

`src/hello.py`: `hello() -> str`.

## Acceptance criteria

1. `hello()` returns `hello`.
2. make check stays green.
3. docs: none, nothing changes.

## Smoke test

```bash
true
```
Expect: nothing.
"""
FEAT = "factory/features/F0001-demo"
P = {n: f"{FEAT}/in-progress/F0001-S000{n}-s{n}.md" for n in (1, 2, 3)}
B = {n: f"work-item/F0001-S000{n}" for n in (1, 2, 3)}

run_git(root, "init", "-q", "--initial-branch=main", "seed")
files = {"factory/pipeline.yml": PIPELINE, "factory/story-form.md": STORY_FORM, f"{FEAT}/feature.md": "# Demo feature\n"}
for n in (1, 2, 3, 4):
    files[f"{FEAT}/backlog/F0001-S000{n}-s{n}.md"] = STORY.format(title=f"Story {n}")
write_files(root / "seed", files)
commit_all(root / "seed", "seed")
run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
remote = root / "remote.git"
run_git(root / "seed", "push", "-q", str(remote), "main")
human = HumanClone(root / "human", remote)
for n in (1, 2, 3):
    human.start(f"{FEAT}/backlog/F0001-S000{n}-s{n}.md")

agent_home = root / "agents"
install_agents(agent_home, ["intake", "coder"])
clock = ManualClock(datetime(2026, 10, 14, 9, 0, tzinfo=UTC))
hosting, fake = FakeHostingService(), FakeAgentRuntime()
interfere = {"on": False}


class Interfering(AgentRuntime):
    """The fake agent runtime; when switched on, the human pushes to the branch during the run."""

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        if interfere["on"]:
            human.push_file(B[2], "notes/s2.md", "the human was here\n")
        return fake.run(request)

    def version(self) -> str:
        return "fake"


def boundaries(checkout, state, hosting_service=hosting):
    return Boundaries(git=GitCli(checkout, GitOptions(identity=TEST_IDENTITY)), hosting=hosting_service,
        agent_runtime=Interfering(), project_commands=MakeProjectCommands(checkout),
        work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(),
        cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(),
        pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(agent_home),
        clock=clock, log=TimestampedFactoryLog(root / state / "factory.log", clock),
        health=JsonHealthStatusFile(root / state / "health.json"), checkout=checkout)


def done(decision, entry):
    return ScriptedRun(result=AgentRunResult(end_reason="completed", decision=decision, entry=entry,
        duration=timedelta(minutes=2), turns=5, tokens=TokenCounts(input=100, output=20), cost_usd=Decimal("0.10")))


def remote_head(branch):
    return run_git(remote, "rev-parse", f"refs/heads/{branch}").strip()


def show(label, tick):
    clock.advance(timedelta(minutes=5))
    outcome = tick.run()
    event = outcome.event
    where = ""
    if event is not None and event.work_item is not None:
        branch = event.work_item.branch
        where = f" at {event.remote_state[:8]} (after the tick, remote {branch} at {remote_head(branch)[:8]})"
    errors = [(e.event_key, e.remote_state[:8], e.count, e.reported, e.last_error)
              for e in tick.status.errors if event is not None and e.event_key == event.key]
    print(f"{label}: stopped={outcome.stopped} event={event.key if event else None}{where} dispatch={outcome.dispatch}")
    if errors:
        print(f"   count: {errors[0]}")


environment = production_environment()
print("== 0. the command line ==")
watch = Path(sys.executable).parent / "factory-watch"
for args in (["--follow"], ["--help"], []):
    r = subprocess.run([str(watch), *args], capture_output=True, text=True)
    print(f"$ factory-watch {' '.join(args)} -> exit {r.returncode}; stdout {r.stdout.strip().splitlines()[:1]}; "
          f"stderr {r.stderr.strip().splitlines()[-1:] if r.stderr else []}; 'follow' in help: {'follow' in r.stdout}")
print("NOT_YET_HANDLED:", NOT_YET_HANDLED)
print("agent PATH:", environment["PATH"], "| factory-guard found:",
      shutil.which("factory-guard", path=environment["PATH"]) is not None)

print("== 1. tick 1 in the operator's checkout, production handlers ==")
work = root / "work"
b = boundaries(work, "state")
b.git.clone(str(remote))
definition = b.pipeline_reader.parse(PIPELINE)
tick = Tick(b, "factory-1", handler_factory(b, "factory-1", environment))
fake.queue(done("doing", "intake: clear."))
show("tick 1", tick)
print("   agent request environment == production environment:", fake.requests()[-1].environment == environment)

print("== 2. a fresh clone sees the same and continues ==")
fresh = root / "fresh"
fb = boundaries(fresh, "fresh-state")
fb.git.clone(str(remote))
b.git.fetch()
mine, theirs = Watcher(b, "factory-1").evaluate(definition), Watcher(fb, "factory-1").evaluate(definition)
print("   original:", mine.key, mine.remote_state[:8], mine.work_item.document.state.stage if mine.work_item else None)
print("   fresh:   ", theirs.key, theirs.remote_state[:8], theirs.work_item.document.state.stage if theirs.work_item else None)
fresh_tick = Tick(fb, "factory-1", handler_factory(fb, "factory-1", environment))
fake.queue(done("approval", "coder: built."))
show("tick 2 (fresh clone)", fresh_tick)

print("== 3. a hand push past a stale local branch ==")
human.push_file(B[1], "notes/s1.md", "a note by hand\n")
print("   operator's checkout is on", b.git.status().branch, "; local", B[1], "at", (b.git.resolve(B[1]) or "")[:8],
      "says stage", FrontmatterWorkItemReader().parse(b.git.show_file(B[1], P[1]) or "").state.stage)
show("tick 3", tick)
print("   local branch after the tick:", b.git.resolve(B[1]), "| checkout on:", b.git.status().branch)

print("== 4. factory-watch's view (run_watch on the same boundaries) ==")
out, err = io.StringIO(), io.StringIO()
code = run_watch(b, "factory-1", out, err)
print(f"   exit {code}")
print("\n".join("   | " + line for line in out.getvalue().splitlines()))

print("== 5. a failed fetch is a repository stop ==")
remote.rename(root / "away.git")
show("tick 4", tick)
print("   health stops:", [(s.scope, s.reason) for s in b.health.read().stops])
(root / "away.git").rename(remote)
show("tick 5", tick)
print("   health stops:", [(s.scope, s.reason) for s in b.health.read().stops])

print("== 6. no merge method is misread as an illegal stage change ==")
pr = FrontmatterWorkItemReader().parse(b.git.show_file(f"origin/{B[1]}", P[1]) or "").state.pull_request
for method in ("merge", "squash", "rebase"):
    copy = root / f"copy-{method}.git"
    shutil.copytree(remote, copy)
    copy_hosting = FakeHostingService()
    view = copy_hosting.create_pull_request(B[1], "t", "b", draft=False)
    assert view.number == pr
    HumanClone(root / f"human-{method}", copy).merge(B[1], method)
    copy_hosting.merge_by_human(pr, run_git(copy, "rev-parse", "refs/heads/main").strip())
    cb = boundaries(root / f"clone-{method}", f"state-{method}", copy_hosting)
    cb.git.clone(str(copy))
    event = Watcher(cb, "factory-1").evaluate(definition)
    print(f"   merged by {method}: event {event.key}")
human.merge(B[1], "squash")
hosting.merge_by_human(pr, remote_head("main"))
show("tick 6", tick)

print("== 7. a rejected push is judged from the remote's state ==")
run_git(root / "human", "checkout", "-q", "main")
run_git(root / "human", "pull", "-q", "origin", "main")
(root / "human" / FEAT / "done").mkdir(exist_ok=True)
run_git(root / "human", "mv", P[1], P[1].replace("in-progress", "done"))
run_git(root / "human", "commit", "-q", "-m", "archive S0001")
run_git(root / "human", "push", "-q", "origin", "main")
interfere["on"] = True
fake.queue(done("doing", "intake: clear."))
show("tick 7", tick)
interfere["on"] = False
for n in range(8, 13):
    show(f"tick {n}", tick)
s2 = FrontmatterWorkItemReader().parse(b.git.show_file(f"origin/{B[2]}", P[2]) or "").state
print("   S0002 on the remote: stage", s2.stage, "| claim", s2.claim.instance if s2.claim else None, "| pr", s2.pull_request)
posts = hosting.factory_posts(s2.pull_request) if s2.pull_request else []
print("   factory posts on its pull request:", len(posts))
for post in posts:
    print("   >", post.body.splitlines()[0])
human.push_file(B[2], "notes/s2.md", "the human pushes again\n")
show("tick 13 (after the human's push)", tick)

print("== 8. a stage changed by hand is an illegal change ==")
human.push_file(B[3], "notes/s3.md", "opening\n")
text = (root / "human" / P[3]).read_text()
human.push_file(B[3], P[3], "---\nstage: approval\n---\n" + text)
b.git.fetch()
event = Watcher(b, "factory-1").evaluate(definition)
print("   event:", event.key, "|", event.detail)
from factory.application.work_items import RemoteWorkItems
snaps = {s.id: s for s in RemoteWorkItems(b.git, b.work_item_reader).read(definition)}
print("   S0003 on its branch: stage", snaps["F0001-S0003"].document.state.stage,
      "| last_stage_change:", RemoteWorkItems(b.git, b.work_item_reader).last_stage_change(snaps["F0001-S0003"]))
print("   pull requests:", [(p.number, p.branch, p.draft, len(hosting.factory_posts(p.number))) for p in hosting.pull_requests()])
for p in hosting.pull_requests():
    for post in hosting.factory_posts(p.number):
        print(f"   > #{p.number}:", post.body.splitlines()[0])

print("== 9. a hand stage change on a branch the factory wrote ==")
reader, writer = FrontmatterWorkItemReader(), FrontmatterWorkItemWriter()
doc = reader.parse(b.git.show_file(f"origin/{B[2]}", P[2]) or "")
assert doc.state is not None
good = doc.model_copy(update={"state": doc.state.model_copy(update={"stage": "approval", "claim": None})})
human.push_file(B[2], P[2], writer.render(good))
b.git.fetch()
event = Watcher(b, "factory-1").evaluate(definition)
print("   event:", event.key, "|", event.detail)
show("tick 15", tick)
````

Output:

````text
== 0. the command line ==
$ factory-watch --follow -> exit 2; stdout []; stderr ['factory-watch: error: unrecognized arguments: --follow']; 'follow' in help: False
$ factory-watch --help -> exit 0; stdout ['usage: factory-watch [-h]']; stderr []; 'follow' in help: False
$ factory-watch  -> exit 2; stdout []; stderr ['factory-watch: no instance settings are wired yet']; 'follow' in help: False
NOT_YET_HANDLED: ('comment', 'ask', 'merged', 'closed', 'reject', 'hand_over', 'crash', 'expired', 'duplicate', 'pull_request_lookup', 'acceptance_due')
agent PATH: /work/factory-rf/.venv/bin:/usr/local/bin:/usr/bin:/bin | factory-guard found: True
== 1. tick 1 in the operator's checkout, production handlers ==
tick 1: stopped=None event=run:F0001-S0001 at 5698b170 (after the tick, remote work-item/F0001-S0001 at 70f30bca) dispatch=handled
   agent request environment == production environment: True
== 2. a fresh clone sees the same and continues ==
   original: run:F0001-S0001 70f30bca doing
   fresh:    run:F0001-S0001 70f30bca doing
tick 2 (fresh clone): stopped=None event=run:F0001-S0001 at 70f30bca (after the tick, remote work-item/F0001-S0001 at b70980af) dispatch=handled
== 3. a hand push past a stale local branch ==
   operator's checkout is on work-item/F0001-S0001 ; local work-item/F0001-S0001 at 70f30bca says stage doing
tick 3: stopped=None event=hand_over:F0001-S0001 at f305825d (after the tick, remote work-item/F0001-S0001 at f305825d) dispatch=error
   count: ('hand_over:F0001-S0001', 'f305825d', 1, False, 'UnhandledEvent: no handler for event kind hand_over')
   local branch after the tick: None | checkout on: main
== 4. factory-watch's view (run_watch on the same boundaries) ==
   exit 0
   | event: hand_over:F0001-S0001
   | 
   | features
   | F0001  Demo feature  backlog=1  in-progress=3  done=0  acceptance=-
   | work items
   | F0001-S0001  Story 1  in-progress  stage=approval  blocked=-  claim=-  running_since=-  pull_request=1
   | F0001-S0002  Story 2  in-progress  stage=intake  blocked=-  claim=-  running_since=-  pull_request=-
   | F0001-S0003  Story 3  in-progress  stage=intake  blocked=-  claim=-  running_since=-  pull_request=-
== 5. a failed fetch is a repository stop ==
2026-10-14T09:20:00Z stop repository fetch_failed: git fetch --prune origin failed (exit 128): fatal: '/tmp/tmp1w0g04cq/remote.git' does not appear to be a git repository
2026-10-14T09:20:00Z fatal: Could not read from remote repository.
2026-10-14T09:20:00Z 
2026-10-14T09:20:00Z Please make sure you have the correct access rights
2026-10-14T09:20:00Z and the repository exists.
tick 4: stopped=fetch_failed event=None dispatch=None
   health stops: [('repository', 'fetch_failed')]
2026-10-14T09:25:00Z stop cleared fetch_failed
tick 5: stopped=None event=hand_over:F0001-S0001 at f305825d (after the tick, remote work-item/F0001-S0001 at f305825d) dispatch=error
   count: ('hand_over:F0001-S0001', 'f305825d', 2, False, 'UnhandledEvent: no handler for event kind hand_over')
   health stops: []
== 6. no merge method is misread as an illegal stage change ==
   merged by merge: event merged:F0001-S0001
   merged by squash: event merged:F0001-S0001
   merged by rebase: event merged:F0001-S0001
tick 6: stopped=None event=merged:F0001-S0001 at f305825d (after the tick, remote work-item/F0001-S0001 at f305825d) dispatch=error
   count: ('merged:F0001-S0001', 'f305825d', 1, False, 'UnhandledEvent: no handler for event kind merged')
== 7. a rejected push is judged from the remote's state ==
tick 7: stopped=None event=run:F0001-S0002 at c623f0e3 (after the tick, remote work-item/F0001-S0002 at b69f0d46) dispatch=error
   count: ('run:F0001-S0002', 'c623f0e3', 1, False, 'PushFailed: push of work-item/F0001-S0002 failed: rejected')
tick 8: stopped=None event=crash:F0001-S0002 at b69f0d46 (after the tick, remote work-item/F0001-S0002 at b69f0d46) dispatch=error
   count: ('crash:F0001-S0002', 'b69f0d46', 1, False, 'UnhandledEvent: no handler for event kind crash')
tick 9: stopped=None event=crash:F0001-S0002 at b69f0d46 (after the tick, remote work-item/F0001-S0002 at b69f0d46) dispatch=error
   count: ('crash:F0001-S0002', 'b69f0d46', 2, False, 'UnhandledEvent: no handler for event kind crash')
tick 10: stopped=None event=crash:F0001-S0002 at b69f0d46 (after the tick, remote work-item/F0001-S0002 at b69f0d46) dispatch=reported
   count: ('crash:F0001-S0002', 'b69f0d46', 3, True, 'UnhandledEvent: no handler for event kind crash')
tick 11: stopped=None event=crash:F0001-S0002 at b69f0d46 (after the tick, remote work-item/F0001-S0002 at b69f0d46) dispatch=capped
   count: ('crash:F0001-S0002', 'b69f0d46', 3, True, 'UnhandledEvent: no handler for event kind crash')
tick 12: stopped=None event=crash:F0001-S0002 at b69f0d46 (after the tick, remote work-item/F0001-S0002 at b69f0d46) dispatch=capped
   count: ('crash:F0001-S0002', 'b69f0d46', 3, True, 'UnhandledEvent: no handler for event kind crash')
   S0002 on the remote: stage intake | claim factory-1 | pr None
   factory posts on its pull request: 0
tick 13 (after the human's push): stopped=None event=crash:F0001-S0002 at 2a73de7c (after the tick, remote work-item/F0001-S0002 at 2a73de7c) dispatch=error
   count: ('crash:F0001-S0002', '2a73de7c', 1, False, 'UnhandledEvent: no handler for event kind crash')
== 8. a stage changed by hand is an illegal change ==
   event: ask:F0001-S0003 | no pull request
   S0003 on its branch: stage approval | last_stage_change: None
   pull requests: [(1, 'work-item/F0001-S0001', True, 0), (2, 'work-item/F0001-S0002', True, 1)]
   > #2: The factory failed 3 times on `crash:F0001-S0002` and has stopped retrying it. Last error: UnhandledEvent: no handler for event kind crash. A new commit on the work item's branch (now at b69f0d464353) makes the factory try again.
== 9. a hand stage change on a branch the factory wrote ==
   event: reject:F0001-S0002 | stage changed from intake to approval, which the pipeline definition does not allow
tick 15: stopped=None event=reject:F0001-S0002 at ffbdc1ea (after the tick, remote work-item/F0001-S0002 at ffbdc1ea) dispatch=error
   count: ('reject:F0001-S0002', 'ffbdc1ea', 1, False, 'UnhandledEvent: no handler for event kind reject')
exit 0
````

Reading the output:

- **Step 1.** The `run` event of a started story without a branch carries the head of `origin/main` (`5698b170`). The stage pushed `70f30bca`. The agent got exactly `production_environment()`, whose `PATH` begins with the interpreter's scripts directory, where `factory-guard` is found.
- **Step 2.** Both checkouts evaluate `run:F0001-S0001` at `70f30bca` with stage `doing`. The fresh clone's tick runs the stage to `approval`.
- **Step 3.** The operator's checkout stood on the stale local `work-item/F0001-S0001` at `70f30bca` (`doing`). The tick read the human's `f305825d` with stage `approval` and gave `hand_over`. The local branch is deleted, and the checkout is on `main`.
- **Step 4.** `run_watch` prints the event line, a blank line and the board, and exits 0.
- **Step 5.** The fetch failure is a repository stop with stamped lines. The next tick clears it, and the same event's count goes on to 2 on the same remote state.
- **Step 6.** None of the three merge methods gives `reject`.
- **Step 7.** The rejected result push raises `PushFailed` (tick 7). From then on the remote holds the instance's own claim, so the evaluation gives `crash`, which has no handler before F0008. It errs twice, is reported once (on draft pull request #2, which the report opened, see the extra lines of step 8) and is then capped. The human's push at tick 13 starts the count again at 1.
- **Step 8.** This is an observation, not a failure: the branch made by hand at `approval` is not judged. The move rule's `last_stage_change` is `None` because the previous version of the file (main's text, without front matter) cannot be read. Since `approval` waits, the work item gives `ask` (no pull request). Section 6 lists this for the human.
- **Step 9.** A hand change on top of the factory's commit gives `reject:F0001-S0002` with the detail naming both stages. Tier 1 comes before the capped `crash`.

Green: every step matches what `FEATURE.md` promised.

## 3 Mutation score

There is no `make mutants` target, by the recorded decision "No `mutants` target, no mutmut" (`docs/decisions.md`). So no score from that target.

Instead I hand-mutated a throwaway copy (`/tmp/f6mut2`, run with the project's venv and `PYTHONPATH` set to the copy; `/tmp/f6demo/mutate.py`). Each mutant runs the test modules of its story. **24 of 25 killed:**

| Module | Mutant | Result |
|---|---|---|
| `evaluation.py` | the merge test reads `closed` | killed |
| `evaluation.py` | a merge skips the illegal change of every work item, not only the waiting one | killed |
| `evaluation.py` | human signals before `reject` | killed |
| `evaluation.py` | attempts cap `>=` → `>` | killed |
| `evaluation.py` | `hand_over` ignores `handed_over` | killed |
| `evaluation.py` | `remote_state` always `main_commit` | killed |
| `evaluation.py` | a held claim falls through to new work | killed |
| `tick_status.py` | `at_cap` `>=` → `>` | killed |
| `tick_status.py` | another remote state keeps the key's old entries | killed |
| `dispatcher.py` | every hosting failure of a report becomes a log line | killed |
| `dispatcher.py` | a success does not clear the counts | killed |
| `dispatcher.py` | a reported entry is reported again instead of `capped` | killed |
| `dispatcher.py` | a report failing with a non-hosting error is marked reported | **survived** |
| `work_items.py` | a merge commit is judged | killed |
| `work_items.py` | the opening commit is judged | killed |
| `move_rule.py` | approval → done is not legal | killed |
| `tick.py` | the fetch stop is never cleared | killed |
| `tick.py` | the restore stop is never cleared | killed |
| `tick.py` | only branches on the remote are deleted | killed |
| `tick.py` | no clean before the switch to `main` | killed |
| `tick.py` | the status is not kept across ticks | killed |
| `tick.py` | the discard line's paths are reordered | killed |
| `watcher.py` | comments are listed for every pull request state | killed |
| `board.py` | `running_since` is not converted to UTC | killed |
| `wiring.py` | the `PATH` tail is reordered | killed |

The one survivor forms one group: `src/factory/application/dispatcher.py`, the `except Exception` branch of `_report` (line 105, the only uncovered line of the module). The rule of S0003 is "a report that raises any `Exception` leaves the entry unreported and returns `"error"`". Criterion 19 tests that rule only with `HostingServiceError`. `StopService.post` also raises `GitError` (from `git.resolve` in `_require_commit_beyond_main`, reached for a work item without a pull request), and no test reaches that branch. A dispatcher that marked such a report as done would lose it silently. This needs one missing criterion, in draft S0009.

Coverage is 99.33 %. The missed lines from F0006 are:

- `dispatcher.py:105`, the survivor;
- `work_items.py:119` and `:149`, defensive lines that narrow types for mypy;
- `board.py` 72→70, a branch that cannot be reached for a `StoryFile` built by `RemoteWorkItems`;
- `watch.py:65` and `:69`, the wired call and the `__main__` line, which are reached once F0010-S0001 wires the boundaries.

## 4 What the stories noticed

Collected from the coder's "noticed, not touched", the documenter's "stale but unrelated" and the reviewer's remarks:

- **S0001 coder.** Two uncovered defensive lines in `work_items.py`. They narrow types for mypy, so there is nothing to do.
- **S0002 documenter.** `docs/operator-guide.md` (lines 108 and 131) says the evaluation "arrives with F0006". It is built now, and at the cap it makes `ask` (`attempts cap`), which is a counted error until F0007. **Still stale**, draft S0008.
- **S0002 reviewer.** `_duplicate` compares by identity, and a `"none"` claim status falls through to tier 4. Neither can happen with the real inputs, so there is nothing to do.
- **S0003 coder and reviewer.** `dispatcher.py:105` is not covered. This is the mutation survivor, draft S0009.
- **S0003 reviewer.** The dispatcher drops the number of the pull request the report opened (decision 9). The demo shows the effect: S0002's state says `pr None` while #2 is open. It is harmless, because `WorkItemOpening` and `StopService` both look for an open pull request by branch first (`src/factory/application/opening.py:107`, `src/factory/application/stops.py:67`). Nothing to do.
- **S0003 documenter.** The operator guide's opening paragraph does not mention the dispatcher; it was to be extended when the tick and handlers arrived. **Still stale**: it names neither the evaluation, the tick nor the dispatcher. Draft S0008.
- **S0004 documenter.** The project guide's table "`status`, `reset_to` — F0006: the tick …" is now true as written. Nothing to do.
- **S0005 coder.** "No branch" is decided by `branch_commit is None`. Nothing to do.
- **S0006 coder.** The `feature_rows` partial branch, and the uncovered `__main__` and wired call in `watch.py` (until F0010-S0001). Nothing to do now.
- **S0006 reviewer.** `run_watch` repeats `Watcher._main_commit`'s resolve-or-`GitError`. `_MAIN_REF = f"{REMOTE}/{MAIN_BRANCH}"` is now defined five times (`watcher.py:16`, `tick.py:24`, `work_items.py:29`, `board.py:14`, and as `PIPELINE_REF` in `pipeline_loading.py:10`). It is a small duplication that does no harm, so no draft. A story that touches these modules could move it to `factory.domain.paths`.
- **S0006 reviewer.** The default of `main`'s `err` has no test. It only matters on the path F0010-S0001 replaces, so nothing to do.
- **S0006 documenter.** The operator guide's `factory-watch` sample uses placeholders, because the installed command exits 2 until F0010. Nothing to do.
- **S0007 coder and reviewer.** No command-line entry point builds a `Tick` yet. `pyproject.toml` declares `factory-run` (`factory.entry.run:main`) and `factory-health`, and both are installed, but their modules do not exist: `uv run factory-run` ends with `ModuleNotFoundError: No module named 'factory.entry.run'`. `README.md` lists only the four existing commands, but it does not warn about the two declared ones. That warning goes into draft S0008.
- **Seen in this acceptance.** `TickStatus` keeps the entries of other event keys until a success clears them. After S0001 was archived, its `hand_over` and `merged` entries stayed in memory (they reset on restart). This is harmless at this size, so no draft.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md`, the F0006 sections of `docs/project-guide.md` and `docs/decisions.md` from the top. The project guide's sections match the code and the demo: the remote's work items, the evaluation, the move rule, the watcher's command line, the tick and the handlers of the events. `docs/decisions.md` holds the six F0006 entries.

Findings, all in `README.md` and `docs/operator-guide.md`:

1. **The summaries of what is built stop before F0006.**
   - `README.md` line 3 still says "The pipeline itself does not run on its own yet: nothing starts a stage before F0006." It names none of reading the remote, the evaluation, the tick, the dispatcher or the run handler.
   - The opening paragraph of the operator guide lists the built parts up to the cost records and says "there is nothing else to start". It does not say what F0006 added, or that no command runs ticks before F0010.
2. **An unreadable work item file is not cleared by closing the pull request.** `docs/operator-guide.md:179` says the tick fails "until a human repairs the file … or closes the pull request". `RemoteWorkItems.read` reads every story in `in-progress/` on `origin/main` before any pull request is looked at, so closing the pull request changes nothing. The ways out are to repair the file or to move the story out of `in-progress/` on `main`. This sentence would mislead an operator.
3. **A `reject` is not "only recorded".** `docs/operator-guide.md:407` says "Handling the event … is not built yet; until it is, the event is only recorded." In fact the event has no handler. It is a counted error, reported once on the pull request after three ticks and then capped, and a capped event holds back all new work (step 9 and decision 14).
4. **The kinds without a handler are not explained to the operator.** "An event that keeps failing" says that a kind without a handler counts. It does not name the kinds (`NOT_YET_HANDLED`) or what that means today. Every story that reaches an approval stage gives `hand_over`, and every merge gives `merged`. Each becomes one error report and then stops all other work, until F0007 and F0008 register their handlers.
5. **`StopService.post` is called now.** `docs/operator-guide.md:70` says it is something "which nothing built calls yet". The dispatcher's error report calls it, and opens a draft pull request when there is none (step 7).
6. **The attempts cap.** Lines 108 and 131 say "the evaluation arrives with F0006". It has arrived, and the cap's `ask` is a counted error until F0007.
7. **A branch made by hand.** "A stage changed by hand" lists the opening commit as exempt ("a story started at `review` is not rejected"). It does not say the consequence step 8 shows: a work item branch created by hand is never judged, whatever stage it writes. This depends on the human's answer under section 6, item A. The draft documents today's behaviour.

There are no contradictions between stories within the project guide. No example that I ran failed.

## 6 Decisions taken for the human

Decisions 1–16 of `FEATURE.md` were built as written. The demo showed 4 (waiting holds back new work), 8 (one keyed report per work item and remote state), 9 (the report opens a draft pull request whose number is not recorded), 10 and 11 (the tick's order, no lock, stops cleared by the next good tick), 13 (`factory-watch`) and 14 (a capped event holds back all new work). Decisions 2 and 14 still name an alternative for the human:

- decision 2: a repository stop `work_item_unreadable` instead of an error on every tick;
- decision 14: skip a capped work item in tier 4.

Answers given during the stories (questions answered on the pull requests on 2026-10-14):

- S0002: criterion 25 added. The `idle` events of tiers 2 and 3 are at `main_commit`, and `duplicate`, `crash`, `expired` and `ask` are at their branch commit.
- S0004: the discard line's paths are in `Git.status()` order. A started story's local branch is deleted even without a remote branch. Two test repairs (the recorded head in criterion 9, and a non-empty push in criterion 19).
- S0005: a newest commit that deleted the file gives `None`. A stage change with an unchanged journal length is never a correction.
- S0007: `PATH` is exactly `<scripts>:/usr/local/bin:/usr/bin:/bin`.

New, for the human to accept or revisit:

- **A. A work item branch created by hand is never judged by the move rule** (demo step 8). The opening commit is exempt, and so is a commit whose previous version cannot be read, such as main's text without front matter. So a human, or anyone who can push, who creates `work-item/<id>` with `stage: approval` puts the story at approval without a `reject`. The factory's own opening always writes the first stage (ST6.1). The options I see:
  - (a) accept the gap, as decision 12 implies;
  - (b) judge the opening commit as a change from the first stage, so that an opening at any other stage is illegal.

  I would choose (b) as a story of F0007, next to the `reject` handler (F0007-S0006). Until then, draft S0008 documents (a).
- **B. Order of F0007, F0008 and F0010.** With the current wiring, the first story to reach an approval stage stops the whole pipeline after three ticks (`hand_over` is unhandled, then capped). So does a crash (`crash`). F0010 makes `factory-run` exist, so F0007 and F0008 must be merged before F0010's scheduler is used for real. Please confirm the order.
- **C. Still open from the F0005 acceptance** and not touched by F0006: the two pull-request rules, the attempts counted over a work item's whole life, and the `_state_of` copies. The fourth item, the two mypy traps, is closed: `CLAUDE.md`'s Tests section now has both.

## 7 The slow checks

None. Beyond `make check`, the project offers no slow check: no `make mutants` (section 3 has the hand pass instead), no image scan and no SBOM.

## 8 Cost

The seven stories cost 57 runs, 88.9 min and $18.76:

| Story | Runs | Minutes | Dollars | Why |
|---|---|---|---|---|
| S0001 | 6 | 9.2 | $1.84 | straight through |
| S0002 | 15 | 21.9 | $4.57 | intake question, then two review rounds |
| S0003 | 6 | 7.9 | $1.98 | straight through |
| S0004 | 10 | 16.9 | $3.29 | intake question, two wrong tests sent back through the human |
| S0005 | 7 | 13.2 | $2.87 | intake question |
| S0006 | 6 | 12.6 | $2.64 | straight through |
| S0007 | 7 | 7.2 | $1.57 | intake question |

**S0002 stands out.** It took 15 runs and a quarter of the feature's cost. Each of its two review rounds found one missing assertion in a test (a `match="origin/main"`, then an `assert hosting.factory_posts(number) == []`). Under R9 each one-line test change took four runs: coder → tester → coder → reviewer.

**S0004** cost three extra runs. Two of its tests could not pass: one compared against a head that its own handler had moved on, and one fell into the empty-commit trap `CLAUDE.md` describes. The coder asked the human, and the tester then made the two changes.

Four of the seven intakes asked one question each, and every question was the same kind: an Interface value with no criterion (the order of the discard line, the exact `PATH` tail, `remote_state` for some kinds, two `last_stage_change` cases). That costs one human round-trip and one more intake run per story. It is cheapest to catch when the stories are written.

## Proposed stories

- `drafts/F0006-S0008-documentation-after-reading-the-remote.md`: repairs the seven findings of section 5 in `README.md` and `docs/operator-guide.md`. The most important are the wrong way out of an unreadable work item file, the "only recorded" `reject`, and what the kinds without a handler do today. Documentation only; the human may prefer to make the edit by hand.
- `drafts/F0006-S0009-a-report-that-fails-with-a-git-error.md`: adds the missing criterion behind the one mutation survivor. A report that fails with `GitError` stays unreported, is not counted and is made again, and it never becomes a log line.

## Log (append only)

1. acceptor: accepted with drafts; 2 drafts proposed; make mutants n/a (no target, by the decision in docs/decisions.md; a hand pass killed 24 of 25 mutants)
      1 Scope: none. All seven scope items were built (S0001–S0007), and every Goal clause shows in the demo. Nothing out of scope was built. Until F0007 and F0008, `hand_over`, `merged` and `crash` are counted errors that cap and then hold back all new work. That is the design (decision 14), but it is not documented.
      2 Feature demo: green, exit 0. The script was `/tmp/f6demo/demo.py`, with the production `handler_factory` and `production_environment` on a real remote and a human clone. In it:
         - `factory-watch --follow` exits 2;
         - a run in the operator's checkout, then the same event in a fresh clone, which ran the next stage;
         - a hand push seen past a stale local branch, which was then deleted;
         - `fetch_failed` raised and then cleared;
         - merge, squash and rebase each give `merged`;
         - a rejected result push leads to `crash` with error, error, reported, capped and exactly one post, and a human push starts the count again;
         - a hand stage change gives `reject`.
        Observed: a branch created by hand at `approval` is never judged (step 8).
      3 Mutation score: no target. A hand pass over the evaluation, tick status, dispatcher, move rule, `last_stage_change`, tick, watcher, board and wiring killed 24 of 25. The survivor: a report failing with a non-hosting error (`GitError`) is not covered (`dispatcher.py:105`). Draft S0009. Coverage is 99.33 %.
      4 Noticed: still stale are the operator guide's mentions of the attempts cap "arrives with F0006" and its opening paragraph (draft S0008). `factory-run` and `factory-health` are declared but missing (`ModuleNotFoundError`). `_MAIN_REF` is defined five times. `TickStatus` keeps entries of other keys. The pull request number dropped by the dispatcher is harmless, because it is looked up by branch.
      5 Documentation: the project guide is current. Seven findings in `README.md` and the operator guide (draft S0008):
         - the built-parts summaries stop before F0006;
         - "closes the pull request" is given as a way out of an unreadable file, which is wrong;
         - `reject` is said to be "only recorded";
         - the unhandled kinds are not explained;
         - `StopService.post` is said to be called by nothing;
         - the attempts cap is said to arrive with F0006;
         - a branch created by hand is not mentioned.
      6 Decisions: 1–16 were built as written, and the story answers of 2026-10-14 are gathered in the report. For the human:
         - A: a branch created by hand is never judged. I recommend judging the opening commit against the first stage, in F0007.
         - B: confirm that F0007 and F0008 come before F0010 makes `factory-run` real.
         - C: the F0005 leftovers.
      7 Slow checks: none (no mutants target, no image scan, no SBOM).
      8 Cost: 57 runs, 88.9 min, $18.76.
         - S0002 stands out at 15 runs and $4.57: two review rounds, each a one-line test assertion costing 4 runs under R9.
         - S0004 took 10 runs: two impossible tests went back through the human.
         - Four intakes each asked about an Interface value that had no criterion.
