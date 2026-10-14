---
stage: done
pr: 52
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0003-S0001, F0003-S0002, F0003-S0003, F0003-S0004, F0003-S0005, F0003-S0006, F0003-S0007, F0003-S0008, F0003-S0009, F0003-S0010]
outcome: accepted
---
# Acceptance of Stops and the pipeline definition

## Verdict

**accepted.** This is the feature's second acceptance, run after the three stories the first one proposed (S0008 to S0010). Each of the first acceptance's findings is closed in code and in the documentation:

- the schema takes values only as written;
- the two kinds of stage that could not move are refused;
- the operator guide now describes the file the operator writes.

The feature demo is green end to end, with the new refusals each becoming one reported stop, and `make check` is green at 99.72 %. What is left is one item that two acceptances noticed and no story owned: the fault of an unreadable YAML text spans several log lines and ends with ruamel's hint to suppress the check. It is a noticed item, not a broken promise, and it gets one draft (S0011).

## 1 Scope

None. Every scope item and every clause of the Goal maps to a story and to code:

- S0001 and S0002: the health status, the clock, the log and `Boundaries`.
- S0003: a work item's stop posted once.
- S0004: the schema and its reader.
- S0005: the agent reader.
- S0006: the loader and its stop.
- S0007: the nine rules across keys.

The first acceptance's section 1 has the module-by-module mapping. The three later stories stay inside the scope item "load-time validation" and the documentation:

- S0008 (`src/factory/domain/pipeline_definition.py`: `strict=True` on the four models, `WritePath`).
- S0009 (same module: rules 10 and 11, through `_moving_stages`).
- S0010 (README, operator guide, project guide; no code).

The first acceptance observed that "a definition that cannot work" still let two stage shapes through. That is closed by S0009. Out of scope stays out:

- `factory.entry.wiring` builds no stop or loader.
- No handler, health-check command or definition writer was built.
- The agent reader still reads its four keys only.

## 2 Feature demo

The walk of an operator, end to end, against the real entry points: a bare remote and a clone, `GitCli`, `PipelineLoader`, `RuamelPipelineDefinitionReader`, `FrontmatterAgentDefinitionReader` on a real agent home, `TimestampedFactoryLog`, `JsonHealthStatusFile` and `StopService`, with the fake hosting service. It is the first acceptance's script with three changes:

- It also checks that the operator guide's example definition loads (1b).
- Step 2 adds six refusals that S0008 and S0009 brought: a limit written `true`, `approval: 'off'`, a blank write path, a stage with neither role nor approval, a stage with an empty `next`, and `done:` written as null.
- The clock starts a day later.

The steps:

1. A good definition on `origin/main` loads. The work tree's edit is not read.
2. Each refusal the Goal names, pushed by the human, becomes one stop that names the fault. A repeat tick keeps it one stop.
3. Fixing `main` clears the stop. A broken branch changes nothing.
4. Stops of two reasons live side by side.
5. A work item's stop opens a draft and posts once, also after a kill after the post.

Run from the repository root, with the script outside the repository:

```bash
uv run python /tmp/f3demo2/demo.py; echo "exit $?"
```

The script, `/tmp/f3demo2/demo.py`:

```python
import dataclasses, json, os, subprocess, tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.clock import ManualClock
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader, JsonLinesCostRecordWriter
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.fake_agent_runtime import FakeAgentRuntime
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.git_cli import GitCli
from factory.adapters.health_file import JsonHealthStatusFile
from factory.adapters.make_commands import MakeProjectCommands
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader, FrontmatterWorkItemWriter
from factory.application.boundaries import Boundaries
from factory.application.pipeline_loading import PipelineLoader
from factory.application.stops import StopService
from factory.domain.errors import HostingServiceError, PipelineDefinitionInvalid
from factory.domain.hosting import PostKey
from factory.domain.kill_points import InjectedKill, KillPoint, KillPoints
from factory.domain.stops import RepositoryStop, WorkItemStop

ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_AUTHOR_NAME": "Human", "GIT_AUTHOR_EMAIL": "h@example.invalid",
       "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "h@example.invalid"}
def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, check=True, capture_output=True, text=True).stdout

GOOD = """\
contract: '1.0'
project_commands:
  check: {}
  lint: {time_limit: 5}
roles:
  tester: {write_paths: ['tests/*']}
  coder: {write_paths: ['src/*']}
  reviewer: {write_paths: ['{work_item}']}
stages:
  tests: {role: tester, next: [doing], checks: [lint]}
  doing: {role: coder, next: [review, tests], checks: [check]}
  review: {role: reviewer, next: [approval, doing], round_cap: 2}
  approval: {approval: true, next: [done, doing]}
  done: {}
"""
root = Path(tempfile.mkdtemp())
origin, human, work = root / "origin.git", root / "human", root / "checkout"
git(root, "init", "-q", "--bare", "-b", "main", str(origin))
git(root, "clone", "-q", str(origin), str(human))
git(human, "checkout", "-q", "-b", "main")
(human / "factory").mkdir()
def push_main(text, message):
    (human / "factory/pipeline.yml").write_text(text)
    git(human, "add", "-A"); git(human, "commit", "-qm", message); git(human, "push", "-q", "origin", "HEAD:main")
push_main(GOOD, "the pipeline definition")
git(root, "clone", "-q", str(origin), str(work))
(work / "factory/pipeline.yml").write_text("work tree edits are never read\n")

home = root / "agent-home"; (home / "agents").mkdir(parents=True)
for role in ("tester", "coder", "reviewer"):
    (home / "agents" / f"{role}.md").write_text("---\nmodel: sonnet\ntools: [Read]\nbudget_usd: 1\n---\nWork.\n")
kills = KillPoints()
clock = ManualClock(datetime(2026, 10, 15, 9, 0, 0, 500000, tzinfo=UTC))
state = root / "state"
checkout = GitCli(work)
hosting = FakeHostingService(kills)
b = Boundaries(git=checkout, hosting=hosting, agent_runtime=FakeAgentRuntime(kills),
               project_commands=MakeProjectCommands(work, kills), work_item_reader=FrontmatterWorkItemReader(),
               work_item_writer=FrontmatterWorkItemWriter(), cost_reader=JsonLinesCostRecordReader(),
               cost_writer=JsonLinesCostRecordWriter(), pipeline_reader=RuamelPipelineDefinitionReader(),
               agent_definitions=FrontmatterAgentDefinitionReader(home), clock=clock,
               log=TimestampedFactoryLog(state / "factory.log", clock), health=JsonHealthStatusFile(state / "health.json"),
               checkout=work)
loader, stops = PipelineLoader(b), StopService(b)
def health():
    status = b.health.read()
    return "healthy" if status.healthy else [f"{s.reason}: {s.detail}" for s in status.stops]
def tick(label):
    clock.advance(timedelta(seconds=30)); checkout.fetch()
    try:
        d = loader.load()
        print(f"  [{label}] loaded: first stage {d.first_stage()}, health {health()}")
        return d
    except PipelineDefinitionInvalid as error:
        print(f"  [{label}] refused: {error.fault!r}")
        print(f"      health: {health()}")

print("1. A good definition on origin/main loads (the work tree's edit is not read); defaults filled in")
d = tick("good")
print("  coder lease/time_limit:", d.roles["coder"].lease_duration, d.roles["coder"].time_limit,
      "| commands:", {n: c.time_limit for n, c in d.project_commands.items()}, "| caps:", d.attempts_cap, d.crash_cap)

print("1b. The operator guide's example definition loads")
import re as _re
guide = Path("docs/operator-guide.md").read_text()
example = _re.search(r"## The pipeline definition\n.*?```yaml\n(.*?)```", guide, _re.S).group(1)
print("  stages:", list(b.pipeline_reader.parse(example).stages))

print("2. Each refusal of the Goal, pushed to main by the human, is one reported stop naming the fault")
cases = {
    "missing key without default": GOOD.replace("contract: '1.0'\n", ""),
    "unknown key": GOOD + "lease_minutes: 60\n",
    "next naming no stage": GOOD.replace("next: [review, tests]", "next: [review, ship]"),
    "role without write paths": GOOD.replace("{write_paths: ['src/*']}", "{write_paths: []}"),
    "role without installed agent": GOOD.replace("roles:\n", "roles:\n  designer: {write_paths: ['ui/*']}\n"),
    "unknown major contract": GOOD.replace("'1.0'", "'2.0'"),
    "time_limits beyond lease": GOOD.replace("{write_paths: ['src/*']}", "{write_paths: ['src/*'], time_limit: 51}"),
    "limit not written as integer": GOOD.replace("{write_paths: ['src/*']}", "{write_paths: ['src/*'], time_limit: true}"),
    "approval not written as boolean": GOOD.replace("approval: true", "approval: 'off'"),
    "blank write path": GOOD.replace("['src/*']", "['  ']"),
    "stage nobody works in": GOOD.replace("  done: {}", "  limbo: {next: [done]}\n  done: {}"),
    "stage that cannot move": GOOD.replace("next: [review, tests]", "next: []"),
    "done written as null": GOOD.replace("done: {}", "done:"),
    "two faults at once": GOOD.replace("next: [review, tests]", "next: [review, ship]").replace("'1.0'", "'2.0'"),
}
for label, text in cases.items():
    push_main(text, label)
    tick(label)
print("  the same fault on the next tick: still one stop")
tick("again")

print("3. Fixed on main: the stop clears itself; a broken definition on a branch changes no stop")
push_main(GOOD, "fixed")
tick("fixed")
git(human, "checkout", "-q", "-b", "try-out"); (human / "factory/pipeline.yml").write_text("contract: [\n")
git(human, "commit", "-qam", "broken"); git(human, "push", "-q", "origin", "try-out"); git(human, "checkout", "-q", "main")
checkout.fetch()
try:
    loader.load("origin/try-out")
except PipelineDefinitionInvalid as error:
    print("  origin/try-out refused, first line of the fault:", error.fault.splitlines()[0])
print("  health:", health())

print("4. Repository stops: one per reason, replaced in place, the pipeline stop's clear leaves others")
stops.raise_stop(RepositoryStop(scope="repository", reason="fetch_failed", detail="origin unreachable", at=clock.now()))
stops.raise_stop(RepositoryStop(scope="repository", reason="fetch_failed", detail="origin unreachable (2)", at=clock.now()))
push_main("roles: {}\n", "broken again"); tick("broken")
push_main(GOOD, "fixed again"); tick("fixed")
stops.clear_stop("fetch_failed"); print("  after clearing fetch_failed:", health())

print("5. A work item stop: a draft pull request opened first, posted once, also after a kill")
git(human, "checkout", "-q", "-b", "work-item/F0009-S0001"); (human / "note.txt").write_text("x")
git(human, "add", "-A"); git(human, "commit", "-qm", "work"); git(human, "push", "-q", "origin", "work-item/F0009-S0001")
git(human, "checkout", "-q", "main"); checkout.fetch()
head_before, status_before = checkout.resolve("HEAD"), checkout.status()
stop = WorkItemStop(key=PostKey(work_item="F0009-S0001", kind="stall", n="1"), branch="work-item/F0009-S0001",
                    title="F0009-S0001: stage tests stalled", pull_request=None,
                    text="Stage tests stalled twice. Comment to retry; close the pull request to stop.")
kills.arm(KillPoint.AFTER_POST)
try:
    stops.post(stop)
except InjectedKill as kill:
    print("  killed at", kill.point.value, "before the number was recorded")
again = stops.post(stop)
prs = hosting.pull_requests()
print("  restart:", again.outcome, "opened", again.opened, "| pull requests:", [(p.number, p.draft, p.branch) for p in prs])
print("  description:", hosting.description(again.pull_request))
posts = hosting.factory_posts(again.pull_request)
print("  factory posts:", len(posts), "| key:", posts[0].key.model_dump())
recorded = stops.post(stop.model_copy(update={"pull_request": again.pull_request}))
other = stops.post(stop.model_copy(update={"key": PostKey(work_item="F0009-S0001", kind="stall", n="2"), "pull_request": again.pull_request}))
print("  recorded number again:", recorded.outcome, "| another n:", other.outcome, "| posts now:", len(hosting.factory_posts(again.pull_request)))
lonely = WorkItemStop(key=PostKey(work_item="F0009-S0002", kind="stall", n="1"), branch="work-item/F0009-S0002",
                      title="t", pull_request=None, text="Comment to retry.")
try:
    stops.post(lonely)
except HostingServiceError as error:
    print("  branch not on the remote:", error, "| pull requests:", len(hosting.pull_requests()))
print("  checkout untouched by the posts:", checkout.resolve("HEAD") == head_before and checkout.status() == status_before)

print("6. What the operator sees at the end: health.json, and the factory log file (every line above that starts with a stamp)")
print("  health.json:", (state / "health.json").read_text())
print("  factory.log lines:", len((state / "factory.log").read_text().splitlines()))
```

Output:

```
1. A good definition on origin/main loads (the work tree's edit is not read); defaults filled in
  [good] loaded: first stage tests, health healthy
  coder lease/time_limit: 60 40 | commands: {'check': 10, 'lint': 5} | caps: 2 2
1b. The operator guide's example definition loads
  stages: ['testing', 'doing', 'review', 'done']
2. Each refusal of the Goal, pushed to main by the human, is one reported stop naming the fault
2026-10-15T09:01:00Z stop repository pipeline_definition_invalid: missing key: contract
  [missing key without default] refused: 'missing key: contract'
      health: ['pipeline_definition_invalid: missing key: contract']
2026-10-15T09:01:30Z stop repository pipeline_definition_invalid: unknown key: lease_minutes
  [unknown key] refused: 'unknown key: lease_minutes'
      health: ['pipeline_definition_invalid: unknown key: lease_minutes']
2026-10-15T09:02:00Z stop repository pipeline_definition_invalid: stage doing: next names unknown stage ship
  [next naming no stage] refused: 'stage doing: next names unknown stage ship'
      health: ['pipeline_definition_invalid: stage doing: next names unknown stage ship']
2026-10-15T09:02:30Z stop repository pipeline_definition_invalid: role coder: write_paths is empty
  [role without write paths] refused: 'role coder: write_paths is empty'
      health: ['pipeline_definition_invalid: role coder: write_paths is empty']
2026-10-15T09:03:00Z stop repository pipeline_definition_invalid: role designer: agent is not installed
  [role without installed agent] refused: 'role designer: agent is not installed'
      health: ['pipeline_definition_invalid: role designer: agent is not installed']
2026-10-15T09:03:30Z stop repository pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1)
  [unknown major contract] refused: 'contract major 2 is not supported (this factory reads major 1)'
      health: ['pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1)']
2026-10-15T09:04:00Z stop repository pipeline_definition_invalid: role coder at stage doing: 61 min exceed lease_duration 60 min
  [time_limits beyond lease] refused: 'role coder at stage doing: 61 min exceed lease_duration 60 min'
      health: ['pipeline_definition_invalid: role coder at stage doing: 61 min exceed lease_duration 60 min']
2026-10-15T09:04:30Z stop repository pipeline_definition_invalid: invalid roles.coder.time_limit: Input should be a valid integer
  [limit not written as integer] refused: 'invalid roles.coder.time_limit: Input should be a valid integer'
      health: ['pipeline_definition_invalid: invalid roles.coder.time_limit: Input should be a valid integer']
2026-10-15T09:05:00Z stop repository pipeline_definition_invalid: invalid stages.approval.approval: Input should be a valid boolean
  [approval not written as boolean] refused: 'invalid stages.approval.approval: Input should be a valid boolean'
      health: ['pipeline_definition_invalid: invalid stages.approval.approval: Input should be a valid boolean']
2026-10-15T09:05:30Z stop repository pipeline_definition_invalid: invalid roles.coder.write_paths[0]: String should match pattern '\S'
  [blank write path] refused: "invalid roles.coder.write_paths[0]: String should match pattern '\\S'"
      health: ["pipeline_definition_invalid: invalid roles.coder.write_paths[0]: String should match pattern '\\S'"]
2026-10-15T09:06:00Z stop repository pipeline_definition_invalid: stage limbo: has neither a role nor approval
  [stage nobody works in] refused: 'stage limbo: has neither a role nor approval'
      health: ['pipeline_definition_invalid: stage limbo: has neither a role nor approval']
2026-10-15T09:06:30Z stop repository pipeline_definition_invalid: stage doing: next is empty
  [stage that cannot move] refused: 'stage doing: next is empty'
      health: ['pipeline_definition_invalid: stage doing: next is empty']
2026-10-15T09:07:00Z stop repository pipeline_definition_invalid: invalid stages.done: Input should be a valid dictionary or instance of StageDefinition
  [done written as null] refused: 'invalid stages.done: Input should be a valid dictionary or instance of StageDefinition'
      health: ['pipeline_definition_invalid: invalid stages.done: Input should be a valid dictionary or instance of StageDefinition']
2026-10-15T09:07:30Z stop repository pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship
  [two faults at once] refused: 'contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship'
      health: ['pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship']
  the same fault on the next tick: still one stop
2026-10-15T09:08:00Z stop repository pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship
  [again] refused: 'contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship'
      health: ['pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship']
3. Fixed on main: the stop clears itself; a broken definition on a branch changes no stop
2026-10-15T09:08:30Z stop cleared pipeline_definition_invalid
  [fixed] loaded: first stage tests, health healthy
  origin/try-out refused, first line of the fault: not valid YAML: while parsing a flow node
  health: healthy
4. Repository stops: one per reason, replaced in place, the pipeline stop's clear leaves others
2026-10-15T09:08:30Z stop repository fetch_failed: origin unreachable
2026-10-15T09:08:30Z stop repository fetch_failed: origin unreachable (2)
2026-10-15T09:09:00Z stop repository pipeline_definition_invalid: missing key: contract; missing key: stages
  [broken] refused: 'missing key: contract; missing key: stages'
      health: ['fetch_failed: origin unreachable (2)', 'pipeline_definition_invalid: missing key: contract; missing key: stages']
2026-10-15T09:09:30Z stop cleared pipeline_definition_invalid
  [fixed] loaded: first stage tests, health ['fetch_failed: origin unreachable (2)']
2026-10-15T09:09:30Z stop cleared fetch_failed
  after clearing fetch_failed: healthy
5. A work item stop: a draft pull request opened first, posted once, also after a kill
  killed at after-post before the number was recorded
  restart: already_posted opened True | pull requests: [(1, True, 'work-item/F0009-S0001')]
  description: The factory opened this draft pull request to report a stop on F0009-S0001. The stop is the comment below.
  factory posts: 1 | key: {'work_item': 'F0009-S0001', 'kind': 'stall', 'n': '1'}
  recorded number again: already_posted | another n: posted | posts now: 2
  branch not on the remote: hosting service create_pull_request failed: branch work-item/F0009-S0002 is not on the remote with a commit beyond main | pull requests: 1
  checkout untouched by the posts: True
6. What the operator sees at the end: health.json, and the factory log file (every line above that starts with a stamp)
  health.json: {"stops":[]}
  factory.log lines: 21
exit 0
```

Green, exit 0. Every clause of the Goal shows:

- **The refusals.** A missing key without a default, an unknown key, a `next` naming no stage, a role without write paths or without an installed agent, an unknown major contract, and `time_limit`s beyond the lease are each one stop with the fault as its detail (step 2).
- **The new refusals.** S0008's strict values and S0009's two stage shapes take the same path: the stop is raised, then cleared at step 3.
- **Repository and machine stops.** They set the health status and write a stamped line, with the clock's `.5` second dropped (steps 2 to 4).
- **A work item's stop.** It reaches its pull request once, also after a kill between the post and the state write (step 5).
- **The operator guide's example** loads (1b).

**Probes beyond the demo.** This script parses each text through the reader on a small valid definition, then writes the stop of a repeated key through the real log:

```bash
uv run python /tmp/f3demo2/probe.py | grep -v '^$'
```

```python
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from factory.adapters.clock import ManualClock
from factory.adapters.factory_log import TimestampedFactoryLog
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid

GOOD = """\
contract: '1.0'
roles:
  coder: {write_paths: ['src/*']}
stages:
  doing: {role: coder, next: [gate], checks: [check]}
  gate: {approval: true, next: [done, doing]}
  done: {}
"""
reader = RuamelPipelineDefinitionReader()
cases = {
    "approval stage with checks": GOOD.replace("gate: {approval: true,", "gate: {approval: true, checks: [check, lint, test],"),
    "next names the stage itself": GOOD.replace("next: [gate]", "next: [doing]"),
    "next lists a stage twice": GOOD.replace("next: [gate]", "next: [gate, gate]"),
    "round_cap on approval stage": GOOD.replace("gate: {approval: true,", "gate: {approval: true, round_cap: 2,"),
    "write path listed twice": GOOD.replace("['src/*']", "['src/*', 'src/*']"),
    "unreachable cycle": GOOD.replace("  done: {}", "  x: {role: coder, next: [y]}\n  y: {role: coder, next: [x]}\n  done: {}"),
    "repeated key": GOOD.replace("  done: {}", "  done: {}\n  done: {}"),
    "unclosed list": GOOD.replace("next: [gate]", "next: [gate"),
}
for label, text in cases.items():
    try:
        reader.parse(text)
        print(f"{label}: accepted")
    except PipelineDefinitionInvalid as error:
        print(f"{label}: refused, {len(error.fault.splitlines())} line(s): {error.fault.splitlines()[0]}")
clock = ManualClock(datetime(2026, 10, 15, 9, 0, tzinfo=UTC))
path = Path(tempfile.mkdtemp()) / "factory.log"
try:
    reader.parse(cases["repeated key"])
except PipelineDefinitionInvalid as error:
    TimestampedFactoryLog(path, clock).line(f"stop repository pipeline_definition_invalid: {error.fault}")
print("--- factory.log after the repeated-key stop:")
print(path.read_text(), end="")
print("--- grep 'stop repository' finds", sum("stop repository" in l for l in path.read_text().splitlines()), "of", len(path.read_text().splitlines()), "lines")
```

```
approval stage with checks: accepted
next names the stage itself: accepted
next lists a stage twice: accepted
round_cap on approval stage: accepted
write path listed twice: accepted
unreachable cycle: accepted
repeated key: refused, 7 line(s): not valid YAML: while constructing a mapping
unclosed list: refused, 4 line(s): not valid YAML: while parsing a flow sequence
2026-10-15T09:00:00Z stop repository pipeline_definition_invalid: not valid YAML: while constructing a mapping
2026-10-15T09:00:00Z   in "<unicode string>", line 5, column 3
2026-10-15T09:00:00Z found duplicate key "done" with value "{}" (original value: "{}")
2026-10-15T09:00:00Z   in "<unicode string>", line 8, column 3
2026-10-15T09:00:00Z 
2026-10-15T09:00:00Z To suppress this check see:
2026-10-15T09:00:00Z     https://yaml.dev/doc/ruamel.yaml/api/#Duplicate_keys
--- factory.log after the repeated-key stop:
2026-10-15T09:00:00Z stop repository pipeline_definition_invalid: not valid YAML: while constructing a mapping
2026-10-15T09:00:00Z   in "<unicode string>", line 5, column 3
2026-10-15T09:00:00Z found duplicate key "done" with value "{}" (original value: "{}")
2026-10-15T09:00:00Z   in "<unicode string>", line 8, column 3
2026-10-15T09:00:00Z 
2026-10-15T09:00:00Z To suppress this check see:
2026-10-15T09:00:00Z     https://yaml.dev/doc/ruamel.yaml/api/#Duplicate_keys
--- grep 'stop repository' finds 1 of 7 lines
exit 0
```

What the probes show:

- **The YAML fault spans several lines** (the finding of 4.1). The stop of a repeated key writes seven stamped lines. The output shows them twice: once on standard output from the log, and once read back from the file. `grep 'stop repository'` finds only the first, which holds ruamel's context (`while constructing a mapping`) and not the problem. The last two lines tell the operator how to *suppress* the duplicate-key check, which the factory wants on purpose (decision 11). Draft S0011.
- **Shapes that are accepted**: an approval stage with `checks` or `round_cap`, a `next` naming its own stage or a stage twice, a write path listed twice, and a cycle no stage reaches.
  - The project guide states that there is no reachability rule (S0009's decision).
  - The others do no harm the loader can see. Whether `checks` on a stage where no agent runs mean anything is F0005's to decide (the checks after the agent). They are listed under 6 as open questions, with no draft.

`make check` was green as I found it: `check: green`, total coverage 99.72 %. The three files that miss lines are from F0001 and F0002; every F0003 module is at 100 %.

## 3 Mutation score

None to report. The project has no `make mutants` target, which is a recorded decision (`docs/decisions.md`, "No `mutants` target, no mutmut"), so there is no score and there are no survivor groups.

The nearest evidence:

- S0008 to S0010 went through without a rework round. Their reviewers found every Interface rule tested on both sides (S0008 criterion 2: six paths × three refused values plus the accepted integer; S0009: each rule refused and accepted, and the "only when `done` exists" condition on its other side).
- The probes in section 2 found no untested refused side in the rules that exist.

## 4 What the stories noticed

Collected from the coder, reviewer and documenter entries of S0001 to S0010, and checked against the code today. The items of S0001 to S0007 are those of the first acceptance's section 4. Their state now:

1. **The fault of unreadable YAML spans several lines.** First noticed by the S0004 coder, then by the first acceptance (4.1). FEATURE.md decision 20 kept it out of S0008, and no story took it since, so it is still open (section 2 probes). Draft S0011.
2. **Lax type coercion.** Closed by S0008.
3. **`position()` raises `ValueError` and `role_of()` raises `KeyError` for an unknown stage.** Still as documented ("not specified"). Low weight, no draft: the tick (F0006) is the first caller and should settle it.
4. **`first_stage()` on empty `stages`, `role_of()` on an undefined role.** Closed by S0007, as the first acceptance said.
5. **The fault separator `"; "` exists three times.** `_FAULT_SEPARATOR` in `src/factory/domain/pipeline_definition.py:24` and in `src/factory/adapters/pipeline_yaml.py:14`, and a literal in `src/factory/application/pipeline_loading.py:60`. Unchanged. Low weight, no draft; a shared domain constant fits the next story that touches these modules (S0011 touches `pipeline_yaml.py`, so the human may fold it in).
6. **`StopService` serves two kinds of stop.** No split needed. Unchanged.
7. **`HealthStatusStore.read()` never raises.** Consistent. Unchanged.

New from S0008 to S0010:

8. **S0008 reviewer:** a blank write path is refused with pydantic's message `String should match pattern '\S'`, which an operator may find hard to read. The demo shows a sibling: `done:` written as null gives `Input should be a valid dictionary or instance of StageDefinition`, which names a Python class. Both are documented as they are (project guide and operator guide). This is a product question, listed under 6, with no draft: the Interface of S0008 asked for pydantic's messages on purpose.
9. **S0010 documenter:** the README and the operator guide name `factory-check-story` as the only command. That is true. Nothing to do.
10. **S0008 and S0009 coders and reviewers:** nothing else noticed and not touched.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` and the F0003 parts of `docs/project-guide.md` from the top, as a newcomer, along with the decision log's entries from "A damaged health file reads as healthy" to "A stage other than done must be able to move". The three findings of the first acceptance are repaired:

- The operator guide has "The pipeline definition". Its example loads (demo step 1b), and its rules list matches the code: `done: {}`, contract major 1, the next-and-role-or-approval rule, the lease arithmetic, strict values, unknown keys, and replace-not-merge.
- The `Boundaries` list names `agent_definitions` in the dataclass's order.
- The README and the operator guide's opening list name the F0003 parts. The README now summarises the built parts instead of listing them.

`WritePathService` is gone from the docs. The project guide's sentence on F0004 now agrees with F0004's draft S0003, which parses directly and does not go through the loader. Both runnable examples in the project guide print what they say:

- `doing 60 ['check', 'lint', 'test']` and `unknown key: contrakt; missing key: contract`;
- `['coder']` and `tools | invalid tools: ...`.

The operator guide's fault rows match the demo's lines word for word.

Findings: none that misleads. Three remarks, not findings:

- **The key table is now written twice**, in the operator guide and in the project guide, as S0010 was asked to do. They agree today. A later story that adds a key must update both. The documenter's cross-read is what keeps them aligned.
- **Two places will change with draft S0011.** The operator guide's row "`not valid YAML: <problem>`" and the project guide's "ruamel's problem text can span several lines" describe the multi-line fault correctly today. S0011's docs criterion changes both.
- **"The factory loads it each cycle"** (operator guide) is still a statement about the future. The guide's opening says that nothing starts the factory yet, so a careful reader is not misled. The same holds for "F0005 uses `read`" and "F0010-S0006 extends `AgentDefinitionInvalid`" in the project guide, which name planned work (`planning/`).

## 6 Decisions taken for the human

`FEATURE.md` lists 20 decisions. The code follows each of them, and the demo shows 1, 4, 6, 7, 8, 9, 11 and 16 directly. The first acceptance's section 6 lists the eight decisions taken in the logs of S0001 to S0007 (among them your S0001 answer: a directory at `health.json` is not replaced).

**Decision 20 needs your confirmation.** The answers to the first acceptance's drafts were taken by the session for you on 2026-10-14, "for the human to overrule in the morning":

- strict values, not lax mode with a warning;
- the multi-line YAML fault kept out of S0008;
- the two stage rules apply only when `done` exists;
- the documentation repair ran through the pipeline;
- the README summarises the built parts.

All five are built. Merging this acceptance confirms them. Overruling one is a new story.

Decisions taken in the logs of S0008 to S0010:

1. **S0008, coder:** pydantic's own strict mode and a `StringConstraints(pattern=r"\S")` on `WritePath`. Rejected: an `AfterValidator` with the factory's own "must not be blank" message, because the Interface asked for pydantic's message.
2. **S0009, coder:** the condition "only when `done` exists" is written once, in `_moving_stages`. Rejected: checking for `done` inside each rule.
3. **S0010, tester and coder:** no tests and no code for a documentation story. Rejected: tests that grep the docs, which would put criteria in tests (R4).
4. **S0010, documenter:** the operator guide got its own key table and rules list, rather than only a pointer to the project guide (see the remark in 5).

Open product questions, for you to settle (no draft written for them):

- **Value faults in pydantic's words** (4.8): should a blank write path say "must not be blank", and `done:` say "a stage is a mapping, write `done: {}`"? I would keep pydantic's words: the docs explain both, and changing the message is a story for each spelling.
- **Approval stages with `checks`, `reports` or `round_cap`** (section 2 probes): they are accepted today and nothing runs those checks yet. F0005 decides what checks after a human's approval mean. Refuse them then, if they mean nothing.
- **Draft S0011** reduces ruamel's error to its problem and 1-based position. The context line (`while constructing a mapping`) and the context's position are dropped. If you want the context kept on the same line, say so when you refine the draft.

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: no `make mutants` (see 3), no image scan and no SBOM.

## 8 Cost

69 runs, 59.9 min and $15.28 for 10 stories: about $1.53 and 6.9 runs per story. Of this, the first seven stories took 51 runs, 46.6 min and $12.93. S0008 to S0010 took 18 runs, 13.3 min and $2.35.

| Story | Runs | Minutes | Cost | Rework rounds |
|---|---|---|---|---|
| S0001 | 11 | 8.1 | $2.49 | 1, with a question to you |
| S0002 | 6 | 5.6 | $1.33 | 0 |
| S0003 | 8 | 7.8 | $2.13 | 1 (a docstring) |
| S0004 | 6 | 6.9 | $1.93 | 0 |
| S0005 | 8 | 6.8 | $2.02 | 1 (a docstring) |
| S0006 | 6 | 5.0 | $1.52 | 0 |
| S0007 | 6 | 6.4 | $1.51 | 0 |
| S0008 | 6 | 6.3 | $0.96 | 0 |
| S0009 | 6 | 3.8 | $0.76 | 0 |
| S0010 | 6 | 3.2 | $0.63 | 0 |

S0001 still stands out with 11 runs: one refused side that no criterion stated cost five extra runs (the first acceptance has the detail).

The three stories this acceptance's predecessor proposed are the cheapest of the feature. Each had an exact Interface, a fault text per case and the human's answers already in the Assignment, and none needed a rework round.

S0010, a documentation-only story, cost six runs and $0.63 for three files. Four of those runs (intake, tester, coder, reviewer) only confirmed that there was nothing for them to do. F0002's acceptance predicted this, and the human chose to run it through the pipeline (decision 20). A documentation repair of this size by hand would have saved about $0.40.

This acceptance is not in the sum.

## Proposed stories

- `drafts/F0003-S0011-unreadable-yaml-fault-on-one-line.md`: the fault of a definition that is not valid YAML becomes one line, `not valid YAML: <problem> (line <l>, column <c>)`. That gives one stop, one log line that `grep 'stop repository'` finds whole, and no ruamel hint to suppress the duplicate-key check. Section 2 probes and 4.1: noticed by S0004 and by both acceptances, and owned by no story.

## Log (append only)

1. acceptor: accepted; 1 draft proposed; make mutants n/a (no target, by decision in docs/decisions.md)
         1 Scope: none. Every scope item and Goal clause maps to a story and code. S0008 to S0010 stay inside load-time validation and the docs. The first acceptance's "two stage shapes still pass" is closed by S0009. Nothing out of scope was built.
         2 Feature demo: green, exit 0. It ran against a real bare remote, a clone and an agent home, with the real loader, readers, log and health file, and the fake hosting service. Each refusal of the Goal is one `pipeline_definition_invalid` stop naming the fault, and so are S0008's strict values (`time_limit: true`, `approval: 'off'`, a blank write path) and S0009's stage shapes (`limbo`, `next: []`). The stop clears once main is fixed, and a broken branch changes no stop. A work item stop killed after its post leaves one draft PR and one post. The operator guide's example loads. Probes: a repeated YAML key writes a seven-line fault (draft S0011). An approval stage with checks or round_cap, a self `next`, a stage listed twice in `next` and an unreachable cycle are accepted (questions, no draft). `make check` green at 99.72 %.
         3 Mutation score: no `make mutants` target (recorded decision). S0008 to S0010 had no rework, and their reviewers found both sides of every rule tested.
         4 Noticed: the multi-line YAML fault is still open after two acceptances and decision 20 (draft S0011). Lax coercion is closed by S0008. Still open, low weight, no draft: `position` ValueError vs `role_of` KeyError (F0006's to settle) and `"; "` defined three times (could fold into S0011). New: pydantic's `'\S'` and "instance of StageDefinition" messages (S0008 reviewer, a question).
         5 Docs: the first acceptance's three findings are repaired. The operator guide has the pipeline definition section, `Boundaries` lists `agent_definitions`, the README summarises the parts and `WritePathService` is gone. Both project-guide examples run as stated. Remarks only: the key table now lives in two guides, and two doc lines will change with S0011.
         6 Decisions: FEATURE.md's 20 are followed. Decision 20, taken by the session for the human, needs confirmation, and merging confirms it. Log decisions: pydantic strict mode plus a pattern rather than custom validators (S0008), `_moving_stages` (S0009), and no tests or code for a docs story (S0010). Open: the operator-readable value messages, the meaning of checks on approval stages, and S0011 dropping ruamel's context line.
         7 Slow checks: none offered.
         8 Cost: 69 runs, 59.9 min, $15.28 ($1.53 per story). S0001 still stands out at 11 runs. S0008 to S0010 are the cheapest ($0.96, $0.76, $0.63) with no rework. The docs-only S0010 spent 4 of its 6 runs confirming there was nothing to do.
2. done (pull request merged); cost: 2 runs, 12.3 min, 89 turns, 267k tokens in (7035k more from cache), 62k out, $4.78
