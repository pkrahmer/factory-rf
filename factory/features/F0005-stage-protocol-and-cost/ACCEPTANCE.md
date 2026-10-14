---
stage: accept
pr: 71
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0005-S0001, F0005-S0002, F0005-S0003, F0005-S0004, F0005-S0005, F0005-S0006, F0005-S0007, F0005-S0008, F0005-S0009, F0005-S0010, F0005-S0011]
---
# Acceptance of Stage protocol and cost

## Verdict

**accepted with drafts.** This is the second acceptance of F0005. S0010 and S0011, the two drafts of the first acceptance, are built and archived. Both findings of that acceptance are closed: a red check's note now fences its output, a stall writes its `stage:` label, and the operator guide's opening and stop sections describe what F0005 built.

The feature demo is green end to end over eleven stages and three work items. `make check` is green at 99.35 %. A hand-mutation pass killed 12 of 13 mutants, and the one survivor is equivalent.

One finding remains, and it is not a broken promise. "A stall by a red check" in the operator guide says that "a failing report adds no line to the entry". The code adds one, and a test asserts it (demo step 2: `` `test`: 1 failed ``). I propose one documentation draft, S0012.

## 1 Scope

None. The scope mapping of the first acceptance still holds:

- S0001 covers the prompt and the decisions.
- S0002 covers the opening.
- S0003 covers the claim first.
- S0004 covers stalls.
- S0005 covers the steps after the agent.
- S0006 and S0007 cover the decision rules, the checks, the reports, the result commit and the labels.
- S0008 covers the cost records.
- S0009 covers the bills.

The two new stories close the one partial item it found:

- **S0010** (`src/factory/domain/post_texts.py` `stall_note`, `src/factory/application/stalls.py:86`). "Labels written as a projection of the stage" now holds for stalls as well as result commits. In the demo, step 11's first-stage stall left `['stage:intake']` on a new pull request.
- **S0011** (documentation only, `README.md` and `docs/operator-guide.md`). It is within scope, because it documents what F0005 built and names what F0006 and F0007 will add.

The Goal's clauses hold as section 2 shows:

- The claim is on the remote before every run.
- The rules move, stall or ask as decided.
- A stall costs one attempt with the undo applied.
- The bill comes from the cost records in a fresh clone alone.

Out of scope stays out. There is no tick, no hand-over, no crash handling and no image.

## 2 Feature demo

The walk-through is the same operator's walk as in the first acceptance, extended for what S0010 changed:

- Step 2 now has a red `test` report.
- Every stall note is printed in full.
- Story S0003 has a first stage that stalls.

It runs against the real entry points:

- `StageRunner` on `GitCli`, with a bare remote and a human clone (`tests/human_clone.py`);
- `MakeProjectCommands` on a real `Makefile`, whose `check` turns red while a flag file exists and whose `test` does the same with another flag file;
- `FakeAgentRuntime`, wrapped in an `AgentRuntime` that prints what the remote holds when each run starts;
- `FakeHostingService`;
- the installed `factory-bill`, run in a fresh clone.

The pipeline is intake → tests (`lint` check, `test` report) → doing (`check`) → review (`round_cap: 1`) → done, with `attempts_cap: 3`.

Run from the repository root, with the script outside the repository:

```bash
uv run python /tmp/f5demo/demo.py; echo "exit $?"
```

The script, `/tmp/f5demo/demo.py`:

````python
import subprocess, sys, tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "/work/factory-rf/tests")
from git_support import TEST_IDENTITY, commit_all, install_agents, run_git, write_files
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
from factory.application.stage import StageRunner
from factory.domain.agent_runs import AgentRunRequest, AgentRunResult, TokenCounts
from factory.domain.git import GitOptions
from factory.domain.paths import cost_records_path

root = Path(tempfile.mkdtemp())
RED = root / "red-check"
RED_REPORT = root / "red-report"
PIPELINE = """contract: "1.0"
attempts_cap: 3
project_commands:
  check: {time_limit: 5}
  lint: {time_limit: 5}
  test: {time_limit: 5}
roles:
  intake: {write_paths: ["{work_item}"], time_limit: 10}
  tester: {write_paths: ["tests/*"], time_limit: 10}
  coder: {write_paths: ["src/*"], time_limit: 10}
  reviewer: {write_paths: ["{work_item}"], time_limit: 10}
stages:
  intake: {role: intake, next: [tests]}
  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}
  doing: {role: coder, next: [review, tests], checks: [check]}
  review: {role: reviewer, next: [done, doing], round_cap: 1}
  done: {}
"""
MAKEFILE = f"""lint:
\t@echo "lint: green"
test:
\t@if [ -f {RED_REPORT} ]; then echo "1 failed"; exit 1; fi
\t@echo "1 passed"
check:
\t@if [ -f {RED} ]; then for i in $$(seq 1 20); do echo "out $$i"; done; echo "FAILED tests/test_a.py"; exit 1; fi
\t@echo "check: green"
"""
FORM = "# Story title\n\n## Description\n\n## Interface\n\n## Acceptance criteria\n\n## Smoke test\n\n## Journal\n"
STORY = """# Greeting

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
P1 = f"{FEAT}/in-progress/F0001-S0001-greeting.md"
P2 = f"{FEAT}/in-progress/F0001-S0002-broken.md"
P3 = f"{FEAT}/in-progress/F0001-S0003-first-stall.md"

run_git(root, "init", "-q", "--initial-branch=main", "seed")
write_files(root / "seed", {"factory/pipeline.yml": PIPELINE, "factory/story-form.md": FORM,
    "Makefile": MAKEFILE, f"{FEAT}/feature.md": "# Demo\n",
    f"{FEAT}/backlog/F0001-S0001-greeting.md": STORY,
    f"{FEAT}/backlog/F0001-S0002-broken.md": "# Broken\n\nNo sections.\n",
    f"{FEAT}/backlog/F0001-S0003-first-stall.md": STORY.replace("# Greeting", "# First stall")})
commit_all(root / "seed", "seed")
run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
remote = root / "remote.git"
run_git(root / "seed", "push", "-q", str(remote), "main")
human = HumanClone(root / "human", remote)
human.start(f"{FEAT}/backlog/F0001-S0001-greeting.md")
human.start(f"{FEAT}/backlog/F0001-S0002-broken.md")
human.start(f"{FEAT}/backlog/F0001-S0003-first-stall.md")

checkout = root / "work"
git = GitCli(checkout, GitOptions(identity=TEST_IDENTITY))
git.clone(str(remote))
agent_home = root / "agents"
install_agents(agent_home, ["intake", "tester", "coder", "reviewer"])
clock = ManualClock(datetime(2026, 10, 14, 9, 0, tzinfo=UTC))
hosting, fake = FakeHostingService(), FakeAgentRuntime()


class Watching(AgentRuntime):
    """Prints what the remote holds at the moment the agent run starts."""

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        branch = git.status().branch
        run_git(checkout, "fetch", "-q", "origin")
        line = request.prompt.split("\n")[1]
        path = P1 if "S0001" in line else P3 if "S0003" in line else P2
        state = FrontmatterWorkItemReader().parse(git.show_file(f"origin/{branch}", path) or "").state
        sidecar = git.show_file(f"origin/{branch}", cost_records_path(path)) or ""
        print(f"   at run start: remote claim={state.claim.instance if state.claim else None}, "
              f"last record={state.journal[-1].kind}, pushed cost records={len(sidecar.splitlines())}, "
              f"env={request.environment}, decisions={request.allowed_decisions}")
        return fake.run(request)

    def version(self) -> str:
        return "watching"


b = Boundaries(git=git, hosting=hosting, agent_runtime=Watching(), project_commands=MakeProjectCommands(checkout),
    work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(),
    cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(),
    pipeline_reader=RuamelPipelineDefinitionReader(), agent_definitions=FrontmatterAgentDefinitionReader(agent_home),
    clock=clock, log=TimestampedFactoryLog(root / "state/log", clock), health=JsonHealthStatusFile(root / "state/h.json"),
    checkout=checkout)
definition = b.pipeline_reader.parse(PIPELINE)
runner = StageRunner(b, "factory-1", definition, {"PATH": "/opt/guard:/usr/bin", "HOME": "/home/factory"})


def done(decision, entry, minutes=2, cost="0.40"):
    return AgentRunResult(end_reason="completed", decision=decision, entry=entry, duration=timedelta(minutes=minutes),
        turns=10, tokens=TokenCounts(input=1000, output=200, cache_read=5000), cost_usd=Decimal(cost) if cost else None)


def stage(label, work_item, path, scripted):
    fake.queue(scripted)
    print(label)
    report = runner.run(work_item, path)
    run_git(checkout, "fetch", "-q", "origin")
    body = git.show_file(f"origin/work-item/{work_item}", path) or ""
    state = b.work_item_reader.parse(body).state
    stall = report.stall
    print(f"   report: {report.stage} -> {report.next_stage}, rule={report.rule}, "
          f"stall={stall.reason if stall else None}, pushed={git.resolve(f'origin/work-item/{work_item}') == report.commit}")
    print(f"   state: stage={state.stage} blocked={state.blocked} round={state.round} attempts={state.attempts} "
          f"crashes={state.crashes} claim={state.claim} pr={state.pull_request} labels={hosting.labels(report.pull_request)}")
    last = state.journal[-1]
    print(f"   last record: {last.number} {last.speaker} {last.kind}")
    tail = body.split("## Journal")[-1].strip().split("\n")
    print("   journal tail:", *("     " + line for line in tail[-5:]), sep="\n")
    if stall:
        note = hosting.factory_posts(report.pull_request)[-1].body
        print("   note:", *("     " + line for line in note.split("\n")), sep="\n")
    clock.advance(timedelta(minutes=5))
    return report


print("== story S0001 ==")
stage("1. intake moves forward (rule 6)", "F0001-S0001", P1, ScriptedRun(result=done("tests", "intake: The story is clear.")))
RED_REPORT.write_text("1")
stage("2. tests: writes a test and, outside its write paths, docs/evil.md; lint green, the test report red",
      "F0001-S0001", P1, ScriptedRun(writes={"tests/test_a.py": "def test_a(): pass\n", "docs/evil.md": "x\n"},
                                     result=done("doing", "Wrote tests/test_a.py.")))
RED_REPORT.unlink()
print("   docs/evil.md on the remote:", git.show_file("origin/work-item/F0001-S0001", "docs/evil.md"))
stage("3. doing: the run dies (cost unknown)", "F0001-S0001", P1,
      ScriptedRun(writes={"src/hello.py": "def hello(): ...\n"},
                  result=AgentRunResult(end_reason="died", duration=timedelta(minutes=3))))
print("   partial src/hello.py kept on the remote:", git.show_file("origin/work-item/F0001-S0001", "src/hello.py") is not None)
RED.write_text("1")
stage("4. doing: decides review, but check is red (rule 5)", "F0001-S0001", P1,
      ScriptedRun(writes={"src/hello.py": "def hello(): return 'hullo'\n"}, result=done("review", "Built hello.")))
RED.unlink()
stage("5. doing: check green, moves forward (rule 6)", "F0001-S0001", P1,
      ScriptedRun(writes={"src/hello.py": "def hello(): return 'hello'\n"}, result=done("review", "coder: Fixed hello.")))
stage("6. review: sends back (rule 3, round 1 of cap 1)", "F0001-S0001", P1, ScriptedRun(result=done("doing", "Rename it.")))
stage("7. doing: answers with a decision that is not allowed", "F0001-S0001", P1, ScriptedRun(result=done("done", "Done.")))
stage("8. doing: forward again (rule 6)", "F0001-S0001", P1, ScriptedRun(result=done("review", "Renamed.")))
stage("9. review: sends back again, past the cap (rule 4)", "F0001-S0001", P1, ScriptedRun(result=done("doing", "Still wrong.")))

print("== story S0002 (no sections) ==")
stage("10. intake decides forward on a broken form (rule 1)", "F0001-S0002", P2, ScriptedRun(result=done("tests", "Looks fine.")))

print("== story S0003 (its first stage stalls) ==")
stage("11. intake: the run dies; label written by the stall", "F0001-S0003", P3,
      ScriptedRun(result=AgentRunResult(end_reason="died", duration=timedelta(minutes=1))))

print("== factory-bill from a fresh clone ==")
run_git(root, "clone", "-q", str(remote), "fresh")
for args in (["F0001-S0001"], []):
    r = subprocess.run(["/work/factory-rf/.venv/bin/factory-bill", *args], cwd=root / "fresh", capture_output=True, text=True)
    print(f"$ factory-bill {' '.join(args)}  (exit {r.returncode})")
    print(r.stdout.rstrip())
print("pull requests:", [(p.number, p.title, p.draft) for p in hosting.pull_requests()])
````

Output:

````text
== story S0001 ==
1. intake moves forward (rule 6)
   at run start: remote claim=factory-1, last record=started, pushed cost records=0, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['tests', 'question']
   report: intake -> tests, rule=6, stall=None, pushed=True
   state: stage=tests blocked=None round=0 attempts=0 crashes=0 claim=None pr=1 labels=['stage:tests']
   last record: 3 intake result
   journal tail:
     1. 2026-10-14 human: created.
     2. factory: started intake as factory-1.
     3. intake: The story is clear.
2. tests: writes a test and, outside its write paths, docs/evil.md; lint green, the test report red
   at run start: remote claim=factory-1, last record=started, pushed cost records=1, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['doing', 'question']
   report: tests -> doing, rule=6, stall=None, pushed=True
   state: stage=doing blocked=None round=0 attempts=0 crashes=0 claim=None pr=1 labels=['stage:doing']
   last record: 5 tester result
   journal tail:
     
        The factory undid changes outside the write paths: docs/evil.md.
     
        `lint`: lint: green
        `test`: 1 failed
   docs/evil.md on the remote: None
3. doing: the run dies (cost unknown)
   at run start: remote claim=factory-1, last record=started, pushed cost records=2, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['review', 'tests', 'question']
   report: doing -> doing, rule=None, stall=died, pushed=True
   state: stage=doing blocked=None round=0 attempts=1 crashes=0 claim=None pr=1 labels=['stage:doing']
   last record: 7 factory stall
   journal tail:
     
        `lint`: lint: green
        `test`: 1 failed
     6. factory: started doing as factory-1.
     7. factory: Stage doing stalled (attempt 1 of 3): the agent run died without a result
   note:
     Stalled (attempt 1 of 3): the agent run died without a result. Retrying on the next tick.
     
     <!-- factory -->
     <!-- factory key=F0001-S0001:stall:7 -->
   partial src/hello.py kept on the remote: True
4. doing: decides review, but check is red (rule 5)
   at run start: remote claim=factory-1, last record=started, pushed cost records=3, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['review', 'tests', 'question']
   report: doing -> doing, rule=5, stall=check_red, pushed=True
   state: stage=doing blocked=None round=0 attempts=2 crashes=0 claim=None pr=1 labels=['stage:doing']
   last record: 10 factory stall
   journal tail:
         out 18
         out 19
         out 20
         FAILED tests/test_a.py
         make: *** [Makefile:7: check] Error 1
   note:
     Stalled (attempt 2 of 3): a check is red after the stage: `check`. Retrying on the next tick.
     
     ```text
     out 8
     out 9
     out 10
     out 11
     out 12
     out 13
     out 14
     out 15
     out 16
     out 17
     out 18
     out 19
     out 20
     FAILED tests/test_a.py
     make: *** [Makefile:7: check] Error 1
     ```
     
     <!-- factory -->
     <!-- factory key=F0001-S0001:stall:10 -->
5. doing: check green, moves forward (rule 6)
   at run start: remote claim=factory-1, last record=started, pushed cost records=4, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['review', 'tests', 'question']
   report: doing -> review, rule=6, stall=None, pushed=True
   state: stage=review blocked=None round=0 attempts=2 crashes=0 claim=None pr=1 labels=['stage:review']
   last record: 12 coder result
   journal tail:
         make: *** [Makefile:7: check] Error 1
     11. factory: started doing as factory-1.
     12. coder: Fixed hello.
     
         `check`: check: green
6. review: sends back (rule 3, round 1 of cap 1)
   at run start: remote claim=factory-1, last record=started, pushed cost records=5, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['done', 'doing', 'question']
   report: review -> doing, rule=3, stall=None, pushed=True
   state: stage=doing blocked=None round=1 attempts=2 crashes=0 claim=None pr=1 labels=['stage:doing']
   last record: 14 reviewer result
   journal tail:
     12. coder: Fixed hello.
     
         `check`: check: green
     13. factory: started review as factory-1.
     14. reviewer: Rename it.
7. doing: answers with a decision that is not allowed
   at run start: remote claim=factory-1, last record=started, pushed cost records=6, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['review', 'tests', 'question']
   report: doing -> doing, rule=None, stall=decision_not_allowed, pushed=True
   state: stage=doing blocked=None round=1 attempts=3 crashes=0 claim=None pr=1 labels=['stage:doing']
   last record: 16 factory stall
   journal tail:
         `check`: check: green
     13. factory: started review as factory-1.
     14. reviewer: Rename it.
     15. factory: started doing as factory-1.
     16. factory: Stage doing stalled (attempt 3 of 3): the agent's decision is not an allowed one: decision 'done' is not one of review, tests, question
   note:
     Stalled (attempt 3 of 3): the agent's decision is not an allowed one: decision 'done' is not one of review, tests, question. The attempts cap is reached; the factory asks you next.
     
     <!-- factory -->
     <!-- factory key=F0001-S0001:stall:16 -->
8. doing: forward again (rule 6)
   at run start: remote claim=factory-1, last record=started, pushed cost records=7, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['review', 'tests', 'question']
   report: doing -> review, rule=6, stall=None, pushed=True
   state: stage=review blocked=None round=1 attempts=3 crashes=0 claim=None pr=1 labels=['stage:review']
   last record: 18 coder result
   journal tail:
     16. factory: Stage doing stalled (attempt 3 of 3): the agent's decision is not an allowed one: decision 'done' is not one of review, tests, question
     17. factory: started doing as factory-1.
     18. coder: Renamed.
     
         `check`: check: green
9. review: sends back again, past the cap (rule 4)
   at run start: remote claim=factory-1, last record=started, pushed cost records=8, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['done', 'doing', 'question']
   report: review -> review, rule=4, stall=None, pushed=True
   state: stage=review blocked=round_cap round=2 attempts=3 crashes=0 claim=None pr=1 labels=['stage:review']
   last record: 21 factory question
   journal tail:
     
         `check`: check: green
     19. factory: started review as factory-1.
     20. reviewer: Still wrong.
     21. factory: This work item has now been sent back 2 times, more than 1. What should happen? Answer with a comment; close the pull request to discard the work item.
== story S0002 (no sections) ==
10. intake decides forward on a broken form (rule 1)
   at run start: remote claim=factory-1, last record=started, pushed cost records=0, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['tests', 'question']
   report: intake -> intake, rule=1, stall=None, pushed=True
   state: stage=intake blocked=question round=0 attempts=0 crashes=0 claim=None pr=2 labels=['stage:intake']
   last record: 4 factory question
   journal tail:
     1. 2026-10-14 human: created.
     2. factory: started intake as factory-1.
     3. intake: Looks fine.
     4. factory: The work item's form has findings, so the stage cannot move forward: 1. missing section: ## Description 2. missing section: ## Interface 3. missing section: ## Acceptance criteria 4. missing section: ## Smoke test. What should happen? Answer with a comment; the stage then runs again. Close the pull request to discard the work item.
== story S0003 (its first stage stalls) ==
11. intake: the run dies; label written by the stall
   at run start: remote claim=factory-1, last record=started, pushed cost records=0, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['tests', 'question']
   report: intake -> intake, rule=None, stall=died, pushed=True
   state: stage=intake blocked=None round=0 attempts=1 crashes=0 claim=None pr=3 labels=['stage:intake']
   last record: 3 factory stall
   journal tail:
     1. 2026-10-14 human: created.
     2. factory: started intake as factory-1.
     3. factory: Stage intake stalled (attempt 1 of 3): the agent run died without a result
   note:
     Stalled (attempt 1 of 3): the agent run died without a result. Retrying on the next tick.
     
     <!-- factory -->
     <!-- factory key=F0001-S0003:stall:3 -->
== factory-bill from a fresh clone ==
$ factory-bill F0001-S0001  (exit 0)
| stage | runs | min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| intake | 1 | 2.0 | 10 | 1000 | 5000 | 200 | 0.40 |
| tests | 1 | 2.0 | 10 | 1000 | 5000 | 200 | 0.40 |
| doing | 5 | 11.0 | 40 | 4000 | 20000 | 800 | 1.60 + 1 unknown |
| review | 2 | 4.0 | 20 | 2000 | 10000 | 400 | 0.80 |
| **total** | 9 | 19.0 | 80 | 8000 | 40000 | 1600 | 3.20 + 1 unknown |

Cost: 9 runs, 19.0 min, 80 turns, 8000 tokens in (40000 more from cache), 1600 out, $3.20 + 1 unknown
$ factory-bill   (exit 0)
F0001-S0001
| stage | runs | min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| intake | 1 | 2.0 | 10 | 1000 | 5000 | 200 | 0.40 |
| tests | 1 | 2.0 | 10 | 1000 | 5000 | 200 | 0.40 |
| doing | 5 | 11.0 | 40 | 4000 | 20000 | 800 | 1.60 + 1 unknown |
| review | 2 | 4.0 | 20 | 2000 | 10000 | 400 | 0.80 |
| **total** | 9 | 19.0 | 80 | 8000 | 40000 | 1600 | 3.20 + 1 unknown |

Cost: 9 runs, 19.0 min, 80 turns, 8000 tokens in (40000 more from cache), 1600 out, $3.20 + 1 unknown

F0001-S0002
| stage | runs | min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| intake | 1 | 2.0 | 10 | 1000 | 5000 | 200 | 0.40 |
| **total** | 1 | 2.0 | 10 | 1000 | 5000 | 200 | 0.40 |

Cost: 1 runs, 2.0 min, 10 turns, 1000 tokens in (5000 more from cache), 200 out, $0.40

F0001-S0003
| stage | runs | min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| intake | 1 | 1.0 | 0 | 0 | 0 | 0 | 0.00 + 1 unknown |
| **total** | 1 | 1.0 | 0 | 0 | 0 | 0 | 0.00 + 1 unknown |

Cost: 1 runs, 1.0 min, 0 turns, 0 tokens in (0 more from cache), 0 out, $0.00 + 1 unknown
pull requests: [(1, 'F0001-S0001: Greeting', True), (2, 'F0001-S0002: Broken', True), (3, 'F0001-S0003: First stall', True)]
exit 0
````

Every step met the Goal:

- **Claim first.** Every `at run start` line shows the remote holding this instance's claim and a `started` record. Every run sees only the earlier runs' cost records, none of its own. The environment arrives unchanged, and the allowed decisions are `next` plus `question`.
- **Step 2.** The undo removed `docs/evil.md`, and the entry names it. `lint` is green. The red `test` report holds nothing, and the stage still moves to `doing`.
- **Step 3.** The died run costs attempt 1 and keeps `src/hello.py`.
- **Step 4.** Rule 5 is a stall. Its note is the S0010 form: the sentence ends `` `check`. Retrying on the next tick. ``, and below it a `text` block holds the last 15 lines (`out 8` to make's error line). The journal still keeps the tail as continuation lines (FEATURE decision 34).
- **Step 7.** At the cap the note says "The attempts cap is reached; the factory asks you next." and has no "Retrying".
- **Steps 6 and 9.** Rules 3 and 4 count rounds.
- **Step 10.** Rule 1 asks the findings question.
- **Step 11.** The first-stage stall writes `stage:intake` on a pull request that the stall opened.
- **Bills.** `factory-bill` read the fresh clone only. The died runs count with their minutes and show as `+ 1 unknown`.

One observation from step 2. The red report's line `` `test`: 1 failed `` has the same form as a green line. That is what `docs/project-guide.md`, "The stage protocol", step 4 says ("for each green check and each report"), and `tests/application/test_stage_finish.py::test_each_green_check_and_each_report_adds_its_last_line_to_the_entry` asserts it. The operator guide says the opposite. See section 5 and draft S0012.

## 3 Mutation score

No `make mutants` score. The project has no target, by the recorded decision "No `mutants` target, no mutmut" (`docs/decisions.md`).

Instead I hand-mutated a throwaway copy (`/tmp/mut`, run with the project's venv and `PYTHONPATH` set to the copy). The mutants target S0010's new code and the rules the first acceptance could only read. The tests were `test_stall_note_block.py`, `test_stall_texts.py`, `test_stall_labels.py`, `test_stalls.py`, `test_stage_finish.py`, `test_stage_run.py`, `test_decisions.py` and `test_decision_rules.py`. **12 of 13 killed:**

| Module | Mutant | Result |
|---|---|---|
| `post_texts.py` | fence `max(3, run + 1)` → `max(3, run)` | killed |
| `post_texts.py` | fence `max(3, …)` → `max(4, …)` | killed |
| `post_texts.py` | trailing line breaks not stripped | killed |
| `post_texts.py` | `attempts < cap` → `<=` | killed |
| `post_texts.py` | empty line before the block dropped | killed |
| `post_texts.py` | info string `text` dropped | killed |
| `stalls.py` | `set_labels` call removed | killed |
| `stalls.py` | labels of the stage-start document instead of the stalled state | **survived** (equivalent: a stall never changes the stage) |
| `stage.py` | `crashes` never reset | killed |
| `stage.py` | `crashes` always reset | killed |
| `stage.py` | only passing reports get a line | killed |
| `stage.py` | `STALL_TAIL_LINES` 15 → 16 | killed |
| `decisions.py` | round cap `rounds <= cap` → `<` | killed |

No missing criterion follows from the one survivor. Coverage is 99.35 %. The missed F0005 lines are the same defensive refusals as before: `stage.py` 114, 410 and 417, `stalls.py` 138, `costs.py` 53, and `task.py` 108 and 120.

## 4 What the stories noticed

The first acceptance collected the observations of S0001 to S0009, and they stand unchanged:

- the untested no-state and unknown-stage refusals in `task.py`;
- `_role_of` in `stage.py`, which copies a role refusal;
- the four private `_state_of` copies that raise three kinds of error;
- S0004 criterion 8's values do not fit the types;
- `_is_work_item_id` rebuilds the id pattern.

None of them needs a story. These are new from S0010 and S0011:

- **S0010, coder.** The journal's stall entry keeps a red check's tail as unfenced continuation lines. That is FEATURE decision 34, the human's answer. When the work item file is viewed on GitHub, the journal renders the tail as Markdown. This is listed in section 6 and is not a finding.
- **S0010, documenter.** The documenter did not run the sample note in "A stall by a red check". Demo step 4 shows that the real note has that shape.
- **S0011, intake, reviewer and documenter.** The second demo `grep` pattern, `stop of one work item`, does not match the heading "Stops of one work item". It matches a sentence instead, so the demo still worked. This is in archived text only, so nothing needs doing.
- **Seen in this review: a failing report's line** (section 2). The operator guide contradicts the code and the project guide. Draft S0012.
- **Seen in this review: `Cost: 1 runs`.** The cost line keeps the plural for one run, as FEATURE decision 21's format `<n> runs` fixes it. This is cosmetic and as decided. I made no draft.

## 5 The documentation as a whole

I read `README.md` and `docs/operator-guide.md` from the top, and the F0005 parts of `docs/project-guide.md` and `docs/decisions.md`. The four findings of the first acceptance are repaired by S0011 and S0010:

- the opening lists;
- "Stops of one work item", which now names `StopService.post` and excludes stalls;
- the new section "What a stage run shows";
- "A stall: the stall note", which points to the nine causes and marks the cap's gate and question as not built yet (F0006, F0007).

S0010 documented the fenced note in three places, which agree with each other and with demo step 4:

- the operator guide, "A stall by a red check";
- the project guide, "Stalls";
- the decision log, "A stall note fences multi-line output, and the stall writes the stage label".

The sample note in the operator guide is the shape the code prints.

One finding. `docs/operator-guide.md:132`, "A stall by a red check", says of reports: "They are recorded and never hold a move: a failing report adds no line to the entry and stops nothing." The code adds a line for every report that ran (`src/factory/application/stage.py:312`). The project guide says so too, at line 1141 ("for each green check and each report"), and so does the operator guide's own "What a stage run shows", item 3. The S0007 documenter wrote the sentence (commit 0838abb), and S0011's cross-read did not catch it.

This misleads mildly. An operator who trusts the sentence reads a report's line in the journal as a passed report. Most reports' last lines say whether they passed (`1 failed`), but not all do (a coverage total, for example). I judge this a documentation repair and not a "not accepted": no step and no answer of the operator depends on it, and nothing runs a stage on its own before F0006. Draft S0012. The human may prefer to make the one-sentence edit by hand.

## 6 Decisions taken for the human

`FEATURE.md` now lists 34 decisions. Decisions 1 to 32 stand as built and were checked in the first acceptance. S0010 added two more, and both are built as stated:

- **33.** A multi-line detail goes in a fenced `text` block. The fence is one longer than any run of three or more backticks, and the journal keeps the tail unfenced. Demo step 4 and the mutants show this.
- **34.** A stall writes its label after the note. A failing note leaves the label unwritten. Demo step 11 and `test_stall_labels.py` show this.

Decision 34 also records that on 2026-10-14 "the session" took the pre-check answers as the reports recommended:

- the label is written in the stall, not when the draft is created;
- the journal's tail stays unfenced;
- S0011 is promoted after S0010.

That was a session's choice, not the human's own answer on a pull request, so it is listed here for the human to confirm.

Still open from the first acceptance. The repository records no answer to these:

- **Two pull-request rules.** `StopService.post` (F0003) posts on a recorded pull request even when it is closed, and opens a draft with the stop description. A stall goes through `WorkItemOpening` (decision 6), which reuses only an open pull request. S0011 now documents both, so nobody is misled. Accept the two rules, or say which should win when F0007 calls `StopService`.
- **Attempts across stages.** As in v1, no move resets `attempts`, so the attempts cap counts a work item's stalls over its whole life. Demo step 8 ran at 3 of 3 after a forward move. Confirm this, or ask for a reset on a forward move like `crashes` has.
- **The `_state_of` copies.** Leave them, or ask for one helper with one stated error. Unifying them would change F0004's tested `ValueError`.
- **mypy traps for testers.** `CLAUDE.md` now lists the `setattr` and `type[object]` traps, but not the two that S0004 and S0005 hit: a wider `Literal` assigned to a narrower annotation, and arithmetic on an `int | None` without narrowing. Adding them is yours to decide.

New:

- **A failing report's line.** It looks like a green line, and only its last line tells. Repairing the operator guide (S0012) keeps the behaviour. The alternative is to mark the failing report in the entry, for example `` `test` (failed): 1 failed ``. That would be a code change to S0007's tested criterion 8 and is the human's call. I recommend the documentation repair.

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: no `make mutants` (section 3 has the hand pass instead), no image scan and no SBOM.

## 8 Cost

The eleven stories cost 81 runs, 104.0 min and $23.74. The first nine cost 69 runs, 91.6 min and $21.49, and section 8 of the first acceptance broke that down. The first acceptance itself cost $4.00, which is not in the sum. The two new stories:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0010 | 6 | 7.9 | $1.56 |
| S0011 | 6 | 4.5 | $0.69 |

Both went straight through in the minimum of 6 runs, with no review round and no question.

S0011 is documentation only. Its tester and coder runs found nothing to do and cost about a third of its $0.69. That is the price of sending a documentation story through the full pipeline. A hand edit by the human would have saved it, and the same goes for S0012.

No story stands out beyond the three named in the first acceptance (S0004, S0005 and S0007, whose extra runs went into tests the tester stage cannot type-check).

## Proposed stories

- `drafts/F0005-S0012-a-failing-report-in-the-operator-guide.md`: corrects the reports bullet of "A stall by a red check". A report's line is added whether it passed or failed, and a failing report holds nothing (sections 2 and 5). Documentation only.

## Log (append only)

1. acceptor: accepted with drafts; 1 draft proposed; make mutants n/a (no target, by the decision in docs/decisions.md; a hand pass killed 12 of 13 mutants, and the survivor is equivalent)
      1 Scope: none. S0010 closes the first acceptance's one partial item: a stall now writes the `stage:` label. S0011 documents what F0005 built. Nothing out of scope was built.
      2 Feature demo: green, exit 0. Eleven stages over three work items ran through `StageRunner` on a real remote with real make targets:
         - the claim was pushed before every run;
         - the undo worked and was named in the entry;
         - a died run stalled and kept its partial write;
         - a red check's note puts the 15-line tail in a fenced `text` block, with "Retrying" on the first line;
         - at the attempts cap the note has no "Retrying";
         - rules 1, 3, 4 and 6 behaved as decided;
         - a first-stage stall wrote `stage:intake`;
         - `factory-bill` in a fresh clone showed `+ 1 unknown`.
        Observed: a red report adds `` `test`: 1 failed `` to the entry.
      3 Mutation score: there is no `make mutants` target, so I hand-mutated a /tmp copy instead:
         - `stall_note` (fence, strip, cap, block layout): all killed;
         - `set_labels` in the stall: killed;
         - the `crashes` reset both ways, the report-line filter and `STALL_TAIL_LINES`: all killed;
         - the round cap boundary: killed;
         - labels taken from the stage-start document instead of the stalled state: survived, and it is equivalent.
        Coverage is 99.35 %. The missed lines are the same defensive refusals as before.
      4 Noticed: the S0001–S0009 items stand and none needs a story. New: the journal keeps a red check's tail unfenced (decision 34); S0011's demo grep pattern does not match its heading (harmless, archived); `Cost: 1 runs` is fixed by decision 21. Seen in this review: the failing-report line contradiction (S0012).
      5 Documentation: the four findings of the first acceptance are repaired, and S0010's note docs match the demo. One finding: `docs/operator-guide.md:132` says a failing report adds no line to the entry. The code, its test and the project guide all add one. Draft S0012.
      6 Decisions: decisions 1–34 stand as built. For the human:
         - confirm the session's 2026-10-14 pre-check answers in decision 34;
         - still open from the first acceptance: the two pull-request rules (`StopService` against `WorkItemOpening`), attempts counted over the work item's whole life, the `_state_of` copies, and the two mypy traps missing from `CLAUDE.md`;
         - new: repair the docs for a failing report's line (recommended) or mark that line in the code.
      7 Slow checks: none. No mutants target, no image scan, no SBOM.
      8 Cost: 81 runs, 104.0 min, $23.74. S0010 (6 runs, $1.56) and S0011 (6 runs, $0.69) both went straight through. About a third of S0011's cost was tester and coder runs on a documentation-only story; a hand edit would save that for S0012 as well.
