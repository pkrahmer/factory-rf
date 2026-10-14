---
stage: done
pr: 47
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0003-S0001, F0003-S0002, F0003-S0003, F0003-S0004, F0003-S0005, F0003-S0006, F0003-S0007]
outcome: accepted
---
# Acceptance of Stops and the pipeline definition

## Verdict

**accepted with drafts.** Every clause of the Goal has a story and code, and the feature demo shows each one end to end. It runs against a real bare remote and clone, the real loader, readers, log and health file, and the fake hosting service. Every refusal the Goal names becomes exactly one `pipeline_definition_invalid` stop that names the fault. The stop clears itself once `main` is fixed. A work item's stop survives a kill after the post with one draft pull request and one post. `make check` is green at 99.71 % coverage. The findings are worth stories but break no promise:

- The schema coerces values silently: `time_limit: true` is read as 1 minute, and `approval: 'off'` as false.
- Two kinds of stage that cannot move pass the rules.
- The documentation has three gaps. The operator guide does not describe the file the operator configures, the project guide's `Boundaries` list misses a field, and the README's status leaves out F0003.

## 1 Scope

None. Every scope item maps to a story and code, and no story strays into Out of scope:

- Health status, `RepositoryStop`, `HealthStatus`, the health file, one stop per reason: S0001 (`factory.domain.stops`, `factory.adapters.health_file`) and S0002 (`factory.application.stops.StopService.raise_stop` and `clear_stop`).
- The clock, the stamped factory log and `Boundaries`, with ABCs that their implementations inherit: S0001 (`factory.application.machine`, `factory.adapters.clock`, `factory.adapters.factory_log`) and S0002 (`factory.application.boundaries`).
- A work item's stop on its pull request, a draft opened first, a repeat after a kill posting nothing: S0003 (`WorkItemStop`, `StopPosted`, `StopService.post`, `factory.domain.post_texts`).
- The schema with defaults and its ruamel.yaml reader, faults spelled by `validation_faults`: S0004 (`factory.domain.pipeline_definition`, `factory.adapters.pipeline_yaml`, `all_faults`).
- Load-time validation, each refusal a reported stop: S0006 (missing file, installed agents, the stop) and S0007 (the nine rules across keys).
- `PipelineLoader` at a git ref, and the agent definition reader: S0006 (`factory.application.pipeline_loading`) and S0005 (`factory.adapters.agent_files`).

Out of scope stays out. No handler, no wiring (`factory.entry.wiring` still builds only the work item reader), no health-check command and no writer of the definition were built. The agent reader reads its four keys and ignores the rest, as F0010 is to decide.

One observation, not a gap: S0007's Assignment says "a definition that is well formed but cannot work is refused when it loads". Two such shapes still pass (see 2, and draft S0009). The Goal lists its validations one by one, and every one of them is built.

## 2 Feature demo

This is the walk a user of the feature takes, from the operator's side:

1. A project has `factory/pipeline.yml` on `origin/main`, the factory has a clone, and the agents are installed. The definition loads at `origin/main`, and the work tree is not read.
2. The human pushes, one after another, each broken definition the Goal names. Every tick after a fetch raises one stop that names the fault, and the same fault on the next tick stays one stop.
3. `main` is fixed and the stop clears itself. A broken definition on a branch is refused without touching the health status.
4. Stops of two reasons live side by side.
5. A work item's stop opens a draft pull request and posts once. A kill after the post, a repeat with the recorded number, another key, and a branch that is not on the remote are each handled.

Run from the repository root, with the script outside the repository:

```bash
uv run python /tmp/f3demo/demo.py; echo "exit $?"
```

The script, `/tmp/f3demo/demo.py`:

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
clock = ManualClock(datetime(2026, 10, 14, 9, 0, 0, 500000, tzinfo=UTC))
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

print("2. Each refusal of the Goal, pushed to main by the human, is one reported stop naming the fault")
cases = {
    "missing key without default": GOOD.replace("contract: '1.0'\n", ""),
    "unknown key": GOOD + "lease_minutes: 60\n",
    "next naming no stage": GOOD.replace("next: [review, tests]", "next: [review, ship]"),
    "role without write paths": GOOD.replace("{write_paths: ['src/*']}", "{write_paths: []}"),
    "role without installed agent": GOOD.replace("roles:\n", "roles:\n  designer: {write_paths: ['ui/*']}\n"),
    "unknown major contract": GOOD.replace("'1.0'", "'2.0'"),
    "time_limits beyond lease": GOOD.replace("{write_paths: ['src/*']}", "{write_paths: ['src/*'], time_limit: 51}"),
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
2. Each refusal of the Goal, pushed to main by the human, is one reported stop naming the fault
2026-10-14T09:01:00Z stop repository pipeline_definition_invalid: missing key: contract
  [missing key without default] refused: 'missing key: contract'
      health: ['pipeline_definition_invalid: missing key: contract']
2026-10-14T09:01:30Z stop repository pipeline_definition_invalid: unknown key: lease_minutes
  [unknown key] refused: 'unknown key: lease_minutes'
      health: ['pipeline_definition_invalid: unknown key: lease_minutes']
2026-10-14T09:02:00Z stop repository pipeline_definition_invalid: stage doing: next names unknown stage ship
  [next naming no stage] refused: 'stage doing: next names unknown stage ship'
      health: ['pipeline_definition_invalid: stage doing: next names unknown stage ship']
2026-10-14T09:02:30Z stop repository pipeline_definition_invalid: role coder: write_paths is empty
  [role without write paths] refused: 'role coder: write_paths is empty'
      health: ['pipeline_definition_invalid: role coder: write_paths is empty']
2026-10-14T09:03:00Z stop repository pipeline_definition_invalid: role designer: agent is not installed
  [role without installed agent] refused: 'role designer: agent is not installed'
      health: ['pipeline_definition_invalid: role designer: agent is not installed']
2026-10-14T09:03:30Z stop repository pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1)
  [unknown major contract] refused: 'contract major 2 is not supported (this factory reads major 1)'
      health: ['pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1)']
2026-10-14T09:04:00Z stop repository pipeline_definition_invalid: role coder at stage doing: 61 min exceed lease_duration 60 min
  [time_limits beyond lease] refused: 'role coder at stage doing: 61 min exceed lease_duration 60 min'
      health: ['pipeline_definition_invalid: role coder at stage doing: 61 min exceed lease_duration 60 min']
2026-10-14T09:04:30Z stop repository pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship
  [two faults at once] refused: 'contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship'
      health: ['pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship']
  the same fault on the next tick: still one stop
2026-10-14T09:05:00Z stop repository pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship
  [again] refused: 'contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship'
      health: ['pipeline_definition_invalid: contract major 2 is not supported (this factory reads major 1); stage doing: next names unknown stage ship']
3. Fixed on main: the stop clears itself; a broken definition on a branch changes no stop
2026-10-14T09:05:30Z stop cleared pipeline_definition_invalid
  [fixed] loaded: first stage tests, health healthy
  origin/try-out refused, first line of the fault: not valid YAML: while parsing a flow node
  health: healthy
4. Repository stops: one per reason, replaced in place, the pipeline stop's clear leaves others
2026-10-14T09:05:30Z stop repository fetch_failed: origin unreachable
2026-10-14T09:05:30Z stop repository fetch_failed: origin unreachable (2)
2026-10-14T09:06:00Z stop repository pipeline_definition_invalid: missing key: contract; missing key: stages
  [broken] refused: 'missing key: contract; missing key: stages'
      health: ['fetch_failed: origin unreachable (2)', 'pipeline_definition_invalid: missing key: contract; missing key: stages']
2026-10-14T09:06:30Z stop cleared pipeline_definition_invalid
  [fixed] loaded: first stage tests, health ['fetch_failed: origin unreachable (2)']
2026-10-14T09:06:30Z stop cleared fetch_failed
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
  factory.log lines: 15
exit 0
```

Green, exit 0. Each clause of the Goal shows in the output:

- A missing key without a default, an unknown key, a `next` naming no stage, a role without write paths, a role without an installed agent, an unknown major contract, and `time_limit`s that do not fit inside `lease_duration`: step 2, one stop each, with the fault as the detail. Two faults in one text are reported together.
- A stop of the repository or machine sets the health status and writes a time-stamped line: steps 2 to 4. The fraction `.5` of the clock is dropped.
- A work item's stop reaches its pull request once, also after a kill between the post and the state write: step 5.

**Probes beyond the demo.** I parsed each change below through `RuamelPipelineDefinitionReader().parse` on a minimal valid definition (the script, `/tmp/f3demo/probe.py`, is not pasted). Each of these is accepted today without a fault:

| Text | Read as |
|---|---|
| `time_limit: true` | 1 minute |
| `time_limit: '30'` | 30 |
| `time_limit: 30.0` | 30 |
| `approval: 'yes'` | true |
| `approval: 'off'` | false |
| `write_paths: ['']` | one empty write path |
| a stage `limbo: {next: [done]}`, with no role and no approval | a stage nobody works in |
| `doing: {role: coder, next: [], ...}` | a stage with no move |

An unreadable YAML text gives a three-line fault. In the factory log it becomes three stamped lines, and only the first says `stop repository pipeline_definition_invalid:`. These are drafts S0008 and S0009, and 4.1.

`make check` was green as I found it: `check: green`, total coverage 99.71 %. The F0003 modules are all at 100 %. The three files that miss a line are from F0001 and F0002.

## 3 Mutation score

None to report: the project has no `make mutants` target, which is a recorded decision (`docs/decisions.md`, "No `mutants` target, no mutmut"). There is no score and there are no survivor groups.

The nearest evidence is the review history. There were three rework rounds in seven stories:

- One was a refused side that no criterion asked for. S0001's temp-file cleanup when `health.json` is a directory went to the human as a question, and they added criterion 25.
- Two were docstrings that no longer matched the code: S0003 `StopService.__init__` and S0005 `AgentDefinitionReader.names`.

The probes in section 2 show the kind of gap a mutant run would point at in `pipeline_definition.py`. No test feeds a boolean, a numeric string or a float where a limit is expected, so nothing would notice whether they are refused. They are not refused today. That is draft S0008.

## 4 What the stories noticed

Collected from the coder, reviewer and documenter entries of S0001 to S0007, and checked against the code today:

1. **The fault for unreadable YAML spans several lines** (S0004 coder: "S0006 may want to shorten it"; S0006 did not). For a repeated key it also carries ruamel's "To suppress this check see" hint. The detail in `health.json` is fine. In the log, the continuation lines carry a stamp but no `stop ...` prefix, so a `grep 'stop repository'` misses them. Low weight, no draft. It fits the next story that touches `pipeline_yaml.py` (S0008 could fold it in when the human refines it).
2. **Lax type coercion** (S0004 coder and reviewer): `true`, `'3'` and `3.0` are read as integer limits. The probes add `approval: 'yes'` and `'off'`. This is draft S0008.
3. `position()` of an unknown stage raises `ValueError`, while `role_of()` raises `KeyError` (S0004 coder and documenter). The project guide documents it as "not specified". Low weight, no draft. The tick (F0006) is its first caller and should settle it.
4. `first_stage()` on an empty `stages`, and `role_of()` on a stage whose role is undefined (S0004 reviewer and coder): both are now ruled out by S0007's rules 3 and 5 on any loaded definition. Closed.
5. The fault separator `"; "` exists three times: `_FAULT_SEPARATOR` in `domain/pipeline_definition.py:17` and in `adapters/pipeline_yaml.py:14`, and a literal in `application/pipeline_loading.py:60` (S0007 coder noticed two). All three join faults for the same reader, the operator. Low weight, no draft. A shared constant in the domain would do, for the next story that touches these modules.
6. `StopService` now serves two kinds of stop (S0003 coder: "splitting it would be a separate ticket"). It is 90 lines with one private helper each way, so no split is needed now.
7. `HealthStatusStore.read()` is documented as never raising. `raise_stop` reads inside its `try` and `clear_stop` lets a read error propagate (S0002 coder). This is consistent and needs nothing.
8. S0001's uncovered cleanup branch was closed by criterion 25. Closed.

The documenters of every story reported "nothing stale and unrelated". Section 5 finds three things that sit between the stories.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md`, the F0003 sections of `docs/project-guide.md` and the seven F0003 entries of `docs/decisions.md` from the top, as a newcomer. Both runnable examples in the project guide print what it says: `doing 60 ['check', 'lint', 'test']` / `unknown key: contrakt; missing key: contract`, and `['coder']` / `tools | invalid tools: ...`. The operator guide's fault tables match the demo's lines word for word. The decision log does not contradict the code. Three findings, all draft S0010:

1. **The operator guide never describes the file the operator configures.** It is "install, configure, the stops", and `factory/pipeline.yml` is the project's configuration (kept thing 7). Yet its keys, defaults, the quoted `contract`, `done: {}`, the replace-not-merge of `project_commands` and the lease rule are only in the project guide, the guide for agents. The operator guide's stop section points there for the rules list. An operator who writes the file has to read the agents' guide. The guide does have a section for the agent files, which is the precedent.
2. **The project guide's `Boundaries` list is wrong.** "The interfaces ...: `git`, ..., `pipeline_reader`, ..., `health`, and `checkout`" leaves out `agent_definitions`, which S0005 added (`src/factory/application/boundaries.py`). The section "The agent definition reader" names it, so the two sections disagree. This misleads an agent writing a test with `dataclasses.replace`.
3. **The README's status sentence leaves out all of F0003.** It does not mention the stops, health file, factory log, pipeline definition, loader or agent reader. The operator guide's opening list of built parts has the same gap, and it still lists only "git, build commands, `claude -p`, the hosting-service client". F0002's acceptance already said this enumeration grows with every feature. Each F0003 documenter judged the README "needs no change" for their own story, so nobody wrote the sentence for the feature.

A smaller remark, not a finding: the operator guide says "The factory loads it each cycle". Nothing loads it yet; F0006 calls the loader. The guide's intro says nothing starts the factory yet, so a careful reader is not misled.

## 6 Decisions taken for the human

`FEATURE.md` lists 19 decisions, all taken while writing the stories. The code follows each of them, and the demo shows 1, 4, 6, 7, 8, 11 and 16 directly. Decision 1 means a lasting fault writes one line per tick, visible in step 2 ("again").

Decisions taken in the story logs:

1. **S0001, your answer (log entry 7):** a directory at `health.json` is not replaced; `write` raises `OSError` and removes its temporary file (criterion 25 added).
2. **S0002, coder:** the replace-or-append rule of the health status is private to `application/stops.py`, not a public method of `HealthStatus`. It moves to the domain if a second user appears.
3. **S0003, coder:** `post` relies on the keyed `post_comment` alone. It does not list comments first to find an earlier post. Recorded in `docs/decisions.md`.
4. **S0004, coder:** the default `project_commands` is a `default_factory`, with no shared mutable default. A merging validator was rejected, as decision 10 requires.
5. **S0005, coder:** the reported `key` and the `fault` both come from `first_error`, so they name the same problem.
6. **S0006, coder:** the stop is raised in one place in `load`, not at each refusal site.
7. **S0007, coder:** each rule is a small module-level function, collected by one validator. The reader takes the message from `ctx["error"]`, not from a custom pydantic error type.
8. **S0007, tester (intake's note):** criterion 5's text renames `done` to `finished` everywhere. Draft S0009 would add faults to that test's text, so it needs your approval for one test change (see the draft).

Open product questions the drafts raise, for you to settle when you refine them:

- Should the definition take values only as written (S0008)?
- Is a stage with no role and no approval, or with an empty `next`, ever meant (S0009)?

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: no `make mutants` (see 3), no image scan and no SBOM.

## 8 Cost

51 runs, 46.6 min, $12.93 for 7 stories, about $1.85 and 7.3 runs per story. That is below F0002's $1.94 and 8.4.

| Story | Runs | Minutes | Cost | Rework rounds |
|---|---|---|---|---|
| S0001 | 11 | 8.1 | $2.49 | 1, with a question to you |
| S0002 | 6 | 5.6 | $1.33 | 0 |
| S0003 | 8 | 7.8 | $2.13 | 1 (a docstring) |
| S0004 | 6 | 6.9 | $1.93 | 0 |
| S0005 | 8 | 6.8 | $2.02 | 1 (a docstring) |
| S0006 | 6 | 5.0 | $1.52 | 0 |
| S0007 | 6 | 6.4 | $1.51 | 0 |

S0001 stands out with 11 runs. A refused side the criteria did not state (the temp-file cleanup) took a reviewer finding, a coder question, your answer, a tester run, a coder run and a second review. That is five extra runs for one test that passed against the unchanged code. The two docstring rounds (S0003, S0005) cost two runs each, for one line of text.

S0004 and S0007, the largest stories by criteria (25 and 26), went through without rework. Their Interfaces spelled out every refused side and the exact fault texts, which is the lesson of F0002's acceptance applied.

This acceptance is not in the sum.

## Proposed stories

- `drafts/F0003-S0008-strict-values-in-the-pipeline-definition.md`: limits, flags and write paths are taken as written. `true`, `'30'` and `30.0` are not read as integers, `'yes'` and `'off'` are not read as booleans, and a blank write path is refused (section 2 probes, 4.2).
- `drafts/F0003-S0009-stages-that-cannot-move.md`: a stage other than `done` with an empty `next`, or with neither a role nor approval, is refused at load (section 2 probes, section 1 observation).
- `drafts/F0003-S0010-documentation-of-the-pipeline-definition-and-stops.md`: the operator guide gets the pipeline definition as configuration, the project guide's `Boundaries` list gets `agent_definitions`, and the README's and operator guide's lists of built parts get F0003 (section 5).

## Log (append only)

1. acceptor: accepted with drafts; 3 drafts proposed; make mutants n/a (no target, by decision in docs/decisions.md)
      1 Scope: none. Every scope item and every Goal clause maps to a story and code (S0001–S0007), and nothing out of scope was built. Observation: S0007's "a definition that cannot work is refused" still lets two stage shapes through (draft S0009).
      2 Feature demo: green, exit 0. It used a real bare remote, a clone and an agent home, with the real loader, readers, log and health file and the fake hosting service. Each refusal the Goal names is one `pipeline_definition_invalid` stop whose detail is the fault: missing key, unknown key, unknown `next`, empty write paths, uninstalled agent, contract major 2, 61 min over a 60 min lease. Two faults are reported together, and a repeat tick keeps one stop. The stop clears once main is fixed, and a broken branch changes no stop. A work item stop killed after its post leaves one draft pull request and one post. Probes found lax coercion (`time_limit: true` gives 1, `'30'` and `30.0` give 30, `approval: 'off'` gives false), a blank write path accepted, and stages with no role or approval, or with an empty `next`, accepted. `make check` was green at 99.71 %.
      3 Mutation score: no `make mutants` target (recorded decision). There were 3 rework rounds in 7 stories: one refused side (S0001, your criterion 25) and two docstrings. The coercion probes are the untested sides a mutant run would point at.
      4 Noticed: the multi-line YAML fault becomes stamped continuation lines without the `stop` prefix; lax coercion (draft S0008); `position` raises ValueError where `role_of` raises KeyError; `"; "` is defined three times. `first_stage` on empty stages and `role_of` on an undefined role are now ruled out by S0007. No draft for the small items.
      5 Docs: both project-guide examples run as stated, and the operator-guide tables match the demo. Three gaps, all draft S0010: the operator guide does not describe `factory/pipeline.yml` (the file the operator configures); the project guide's `Boundaries` list lacks `agent_definitions`; the README status and operator-guide intro name nothing of F0003.
      6 Decisions: FEATURE.md's 19 decisions, which the code follows. Eight decisions came from the logs, including your S0001 answer, the keyed post alone, `default_factory`, and the rule functions with `ctx["error"]`. Open for you: strict values (S0008), whether either stage shape is ever meant, and running the new rules only when `done` exists so that no test changes (S0009).
      7 Slow checks: none offered.
      8 Cost: 51 runs, 46.6 min, $12.93 ($1.85/story, below F0002's $1.94). S0001 stands out at 11 runs and $2.49: one unstated refused side cost five extra runs for a test that passed against the unchanged code. S0004 and S0007, the largest stories, had no rework.
2. done (pull request merged); cost: 1 runs, 7.8 min, 51 turns, 163k tokens in (4538k more from cache), 37k out, $2.96
