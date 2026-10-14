---
stage: done
pr: 67
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0005-S0001, F0005-S0002, F0005-S0003, F0005-S0004, F0005-S0005, F0005-S0006, F0005-S0007, F0005-S0008, F0005-S0009]
outcome: accepted
---
# Acceptance of Stage protocol and cost

## Verdict

**accepted with drafts.** Every scope item maps to a story and its code, and the Goal's done-condition holds. The feature demo is green end to end. It runs ten stages through `StageRunner` against a real bare remote, real `make` targets, the fake hosting service and `factory-bill` run from a fresh clone, and it touches each of rules 1 to 6 and the stall reasons `died`, `check_red` and `decision_not_allowed`. `make check` is green at 99.43 %. There are two findings of weight, and neither is a broken promise:

- The stall note pastes a red check's output inline, as Markdown, with the follow-up sentence glued to make's error line. A stall also writes no `stage:` label.
- The operator guide's opening and its "Stops of one work item" no longer describe what F0005 does.

I propose two drafts, S0010 and S0011.

## 1 Scope

None. Each scope item maps to the stories and their code:

- Agent definitions, the prompt, the allowed decisions (one list for the prompt, the request and the validation), the environment passed unchanged, and the form check before and after: S0001, `src/factory/domain/prompts.py`, `src/factory/application/task.py` (`TaskComposer`, `StoryFormChecker`).
- Opening the branch, preparing a later stage (reset to the remote, merging `main`, aborting on a conflict), and the draft pull request, reusing only an open one: S0002, `src/factory/application/opening.py`.
- The stage start: claim first, guard settings from the stage-start commit, `time_limit`: S0003, `StageLauncher` in `src/factory/application/stage.py`.
- Stalls: attempts + 1, the stall entry, kept writes, undo and restore whatever the end, claim released, the stall note: S0004, `src/factory/domain/decisions.py` (`StallReason`, `stall_reason_of`), `src/factory/domain/post_texts.py`, `src/factory/application/stalls.py`.
- After the agent: the branch test, the undo, the entry by code, the form checked again, only a new finding stalls: S0005, `AfterAgent` and `agent_entry`.
- Decision rules 1 to 7, the result commit and push, labels: S0006 (`decide`, `StageMove`, the question texts) and S0007 (`StageFinisher`, `StageRunner`, `src/factory/domain/labels.py`).
- Cost records: S0008, `src/factory/application/costs.py` (`CostRecorder`).
- Bills, the cost table and line, `factory-bill`, and the search that no code reads journal text: S0009, `src/factory/domain/bills.py`, `BillService`, `src/factory/entry/bill.py`, `tests/test_no_journal_reading.py`.

The Goal's clauses hold, as section 2 shows:

- A stage starts only after its claim is pushed. At every run start the remote held the claim and the `started` record.
- A stage moves, stalls or asks as the rules say.
- A stall costs one attempt, with the undo applied. The died run's partial write inside `src/*` was kept.
- The bill is read from the cost records on the remote alone, here from a fresh clone.

Out of scope stays out:

- Nothing wires `StageRunner` into a tick (F0006).
- Nothing posts the hand-over or the cost table (F0007).
- Nothing handles a crash (F0008).
- `image` stays `None` (F0010).

One partial item sits inside the scope's "labels written as a projection of the stage": only the result commit writes labels, so a work item whose first stage stalls has a pull request without a label. Section 4 has the detail and draft S0010 the fix.

## 2 Feature demo

This is the walk of an operator through the feature's purpose: two stories run stage by stage, then their bill. One story goes from intake to a round-cap question, and the other has a broken form. It runs against the real entry points:

- `StageRunner` (the stage protocol's one entry point) on `GitCli` with a bare remote and a human clone (`tests/human_clone.py`);
- `MakeProjectCommands` running a real `Makefile` whose `check` turns red while a flag file exists;
- `FakeAgentRuntime` scripted runs, wrapped in an `AgentRuntime` that prints what the remote holds when the run starts;
- `FakeHostingService`;
- the installed `factory-bill` command, run in a fresh clone.

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

run_git(root, "init", "-q", "--initial-branch=main", "seed")
write_files(root / "seed", {"factory/pipeline.yml": PIPELINE, "factory/story-form.md": FORM,
    "Makefile": MAKEFILE, f"{FEAT}/feature.md": "# Demo\n",
    f"{FEAT}/backlog/F0001-S0001-greeting.md": STORY,
    f"{FEAT}/backlog/F0001-S0002-broken.md": "# Broken\n\nNo sections.\n"})
commit_all(root / "seed", "seed")
run_git(root, "init", "-q", "--bare", "--initial-branch=main", "remote.git")
remote = root / "remote.git"
run_git(root / "seed", "push", "-q", str(remote), "main")
human = HumanClone(root / "human", remote)
human.start(f"{FEAT}/backlog/F0001-S0001-greeting.md")
human.start(f"{FEAT}/backlog/F0001-S0002-broken.md")

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
        path = P1 if "S0001" in request.prompt.split("\n")[1] else P2
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
        print("   note:", hosting.factory_posts(report.pull_request)[-1].body.split("\n")[0][:240])
    clock.advance(timedelta(minutes=5))
    return report


print("== story S0001 ==")
stage("1. intake moves forward (rule 6)", "F0001-S0001", P1, ScriptedRun(result=done("tests", "intake: The story is clear.")))
stage("2. tests: writes a test and, outside its write paths, docs/evil.md; lint green, test reported",
      "F0001-S0001", P1, ScriptedRun(writes={"tests/test_a.py": "def test_a(): pass\n", "docs/evil.md": "x\n"},
                                     result=done("doing", "Wrote tests/test_a.py.")))
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

print("== factory-bill from a fresh clone ==")
run_git(root, "clone", "-q", str(remote), "fresh")
for args in (["F0001-S0001"], []):
    r = subprocess.run(["/work/factory-rf/.venv/bin/factory-bill", *args], cwd=root / "fresh", capture_output=True, text=True)
    print(f"$ factory-bill {' '.join(args)}  (exit {r.returncode})")
    print(r.stdout.rstrip())
print("pull requests:", [(p.number, p.title, p.draft) for p in hosting.pull_requests()])
````

Output:

```
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
2. tests: writes a test and, outside its write paths, docs/evil.md; lint green, test reported
   at run start: remote claim=factory-1, last record=started, pushed cost records=1, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['doing', 'question']
   report: tests -> doing, rule=6, stall=None, pushed=True
   state: stage=doing blocked=None round=0 attempts=0 crashes=0 claim=None pr=1 labels=['stage:doing']
   last record: 5 tester result
   journal tail:
     
        The factory undid changes outside the write paths: docs/evil.md.
     
        `lint`: lint: green
        `test`: 1 passed
   docs/evil.md on the remote: None
3. doing: the run dies (cost unknown)
   at run start: remote claim=factory-1, last record=started, pushed cost records=2, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['review', 'tests', 'question']
   report: doing -> doing, rule=None, stall=died, pushed=True
   state: stage=doing blocked=None round=0 attempts=1 crashes=0 claim=None pr=1 labels=['stage:doing']
   last record: 7 factory stall
   journal tail:
     
        `lint`: lint: green
        `test`: 1 passed
     6. factory: started doing as factory-1.
     7. factory: Stage doing stalled (attempt 1 of 3): the agent run died without a result
   note: Stalled (attempt 1 of 3): the agent run died without a result. Retrying on the next tick.
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
         make: *** [Makefile:6: check] Error 1
   note: Stalled (attempt 2 of 3): a check is red after the stage: `check`
5. doing: check green, moves forward (rule 6)
   at run start: remote claim=factory-1, last record=started, pushed cost records=4, env={'PATH': '/opt/guard:/usr/bin', 'HOME': '/home/factory'}, decisions=['review', 'tests', 'question']
   report: doing -> review, rule=6, stall=None, pushed=True
   state: stage=review blocked=None round=0 attempts=2 crashes=0 claim=None pr=1 labels=['stage:review']
   last record: 12 coder result
   journal tail:
         make: *** [Makefile:6: check] Error 1
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
   note: Stalled (attempt 3 of 3): the agent's decision is not an allowed one: decision 'done' is not one of review, tests, question. The attempts cap is reached; the factory asks you next.
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
pull requests: [(1, 'F0001-S0001: Greeting', True), (2, 'F0001-S0002: Broken', True)]
exit 0
```

All ten steps met the Goal:

- **Claim first.** Every `at run start` line shows the remote holding this instance's claim and a `started` record. The pushed sidecar holds only earlier runs' records (0, 1, 2 … 8), so no record is pushed before its run. The environment arrives unchanged, and the allowed decisions are `next` plus `question`.
- **Step 2.** The tester's `docs/evil.md` is gone from the remote, the entry names it, and the `lint` check and `test` report lines follow.
- **Step 3.** The died run costs attempt 1, keeps `src/hello.py` and says "Retrying".
- **Step 4.** Rule 5 is a stall whose journal entry ends with make's error line and holds 15 lines of output.
- **Step 7.** At the cap the note drops "Retrying".
- **Steps 6 and 9.** Rules 3 and 4 count rounds, and attempts are left alone.
- **Step 10.** Rule 1 turns a forward decision on a broken form into the factory's findings question.
- **Bills.** Both `factory-bill` calls read only the fresh clone's remote refs. The died run counts as a run with its 3 minutes, and its cost shows as `+ 1 unknown`, not as $0.

Two observations from the demo:

- **The red check's note.** Step 4's note, printed in full with `stall_note`, is the first line `` Stalled (attempt 2 of 3): a check is red after the stage: `check` ``, then 15 bare lines, the last of them `make: *** [Makefile:6: check] Error 1. Retrying on the next tick.` The follow-up sentence is glued onto make's line, and GitHub would render the output as Markdown (`<module>` dropped, `__init__` turned bold). Draft S0010.
- **Step 8 ran after the attempts cap.** It ran although the note at step 7 said "the factory asks you next". That is by design: `StageRunner` does not gate, and F0006-S0002's tier 4 turns `attempts >= attempts_cap` into an `ask` event. The operator guide promises the gate as if it were built (section 5).

## 3 Mutation score

No score. The project has no `make mutants` target, by the recorded decision "No `mutants` target, no mutmut" (`docs/decisions.md`), so there are no survivors to group.

I wanted to hand-mutate key lines in a throwaway copy, but the copy was refused in this run, so I checked the tests by reading instead:

- The round cap is tested on both sides: rounds 0 to 2 against round 3 (S0006 reviewer).
- The 15-line tail is tested with outputs of 20 and 10 lines, with `line 6` absent (S0007 reviewer).
- Half-up rounding is tested with `0.125` and 3 seconds (`tests/domain/test_bills.py:157`).
- The `crashes` reset is tested for rule 6 against rules 3 and 5 (`test_stage_finish.py:683`).
- The "first equal finding is old" rule was pinned only after the S0005 review round.

The reviewers' mutation reasoning was closed in the stories: S0003 round 1 (the copied role check) and S0005 round 1 (criterion 17).

Coverage is 99.43 %. The 13 missed lines are all defensive refusals the coders reported (section 4): `stage.py` 114, 410 and 417, `stalls.py` 136, `costs.py` 53, and `task.py` 108 and 120, plus older lines outside F0005.

## 4 What the stories noticed

None of these needs a story except the two marked as seen in this review.

- **S0001, coder and reviewer.** `compose` raises `WorkItemFormatError` for a document without a state (`task.py:120`). The Interface does not describe this, and no test reaches it. An unknown stage was a `KeyError`; S0003 round 1 made it a `ValueError` (`task.py:108`), also untested.
- **S0002, coder.** A state without `pull_request` and a document without a state both fall through to the branch lookup. That is harmless.
- **S0003, reviewer (a finding, fixed in round 1).** The launcher copied `TaskComposer._role_name`'s refusal word for word. The copy came back later as `_role_of` in `stage.py:414`, written for S0005 and S0008's `begin` with the same message. That is the duplication S0003 removed, now in a private helper. It is a small refactor, not a defect, so I made no draft.
- **S0004, tester, coder and documenter.** Criterion 8 names `comments_read` 3 and `handed_over` 2, which the types refuse; the test uses `[3]` and `"tester"`. The archived story text is the only place that is wrong. The documenter added that "the factory asks you next" describes intent: the cap question is F0007's.
- **S0005, coder.** `AfterAgent._entry`'s refusal of a stage without a role is unreachable. The `decision is None` check exists only for mypy.
- **S0007, coder.** `claims.py`, `stalls.py` and `stage.py` each have a private `_state_of`, and `journal.py` has a fourth. `costs.py`, `task.py` and `StageLauncher` inline the same check. The copies raise three different errors (`ValueError` with three messages, and `WorkItemFormatError`). Merging them would change F0004's tested `ValueError` (F0004 decision 2), so this is a question for the human, not a quiet refactor. Most of the missed lines in section 3 are these copies.
- **S0008, intake and coder.** No test checks that a `StallContext` with `cost=None` writes no sidecar. The code does not write one.
- **S0009, reviewer.** `_is_work_item_id` in `src/factory/entry/bill.py` rebuilds the id pattern from `STORY_ID|ACCEPTANCE_ID`, because the domain has no public predicate. The `Name` and `WorkItemId` patterns on `StageBill` and `WorkItemBill` have no refused-side tests. They are existing domain types.
- **Seen in this review: the stall note of a red check** (section 2). The detail `` `check`\n<tail> `` goes into the note inline, so the follow-up sentence is glued to the tail's last line, and the tail is rendered as Markdown on GitHub. Draft S0010.
- **Seen in this review: a stall writes no label.** `set_labels` is called only in `StageFinisher` (`stage.py:289`). A new work item whose first stage stalls therefore has a draft pull request without `stage:<first stage>` until its first result commit. Draft S0010.
- **Seen in this review: attempts are never reset by a move.** `StageFinisher` keeps `attempts`, as v1 does: only the human's answer at the cap resets it (F0007-S0007). The attempts cap therefore counts every stall of the work item across all its stages, not per stage. The demo shows it: three stalls at `doing` reach 3 of 3, and a stall at intake would have counted too. This matches v1 (precheck F0005-1) and is listed in section 6 for the human to confirm.

## 5 The documentation as a whole

The project guide's F0005 sections agree with each other and with the demo. I checked "The prompt and the request for a stage", "Opening a work item", "Starting a stage", "Stalls", "After the agent run", "The decision rules", "The stage protocol", "Cost records" and "Bills". So did the operator guide's "A stall by a red check", "The factory's own questions" and "What a work item cost: `factory-bill`" (its table and line formats match the demo's `factory-bill` output), and the decision log's F0005 entries. I found four findings, all in the operator's view:

- **The opening lists are stale.** `README.md` says what is built is the groundwork "and the claim of a stage with its write paths, guard and undo". The operator guide's opening ends at "the stall with its note". Neither names the stage protocol, the decision rules and the factory's questions, the checks and reports, or the cost records. Both do name `factory-bill`.
- **"Stops of one work item" contradicts the stall's behaviour.** For "a question, a stall, a cap reached" it says:
  - a missing pull request is opened with the description `The factory opened this draft pull request to report a stop on <work item>…`;
  - a stop is posted on a recorded pull request even when it is closed.

  That is `StopService`'s rule. `StallService` goes through `WorkItemOpening.ensure_pull_request` (`stalls.py:74`), which reuses only an open pull request and opens a new draft titled `<id>: <title>` with the work item's text. No operator meets this yet, because nothing runs a stage on its own, so it misleads nobody today.
- **No section says what a stage run shows to the operator.** That covers the draft pull request opened at the first stage, its title and description, the `factory: started <stage> as <instance>.` entry, one factory commit per stage, and the `stage:` label. Each story documented its own part in the project guide; the operator guide has no overview.
- **"A stall: the stall note" is inaccurate in two places.**
  - Its first sentence names four causes, and its list names nine.
  - Its cap paragraph says "The factory does not run the stage again until you have". Nothing built does that yet: demo step 8 ran after the cap. The gate is F0006-S0002's and the question F0007-S0002's. The S0004 documenter noted it as intent.

Draft S0011 repairs all four. It is documentation only, and the human may prefer to make the edit by hand.

## 6 Decisions taken for the human

The 32 decisions in `FEATURE.md` stand as built. I checked each against the code, and these against the demo:

- 4: entry 1 is dated by the clock, and an empty `## Journal` is added.
- 5: the title is `<id>: <title>`.
- 7: the pull request number is recorded in the next commit.
- 9: a stall releases the claim.
- 11: the note's wording.
- 16: rule 1 is a `factory` question entry.
- 17: `crashes` resets on rule 6 only.
- 18 and 19: the tail and the check lines.
- 21 and 22: the cost line and table formats.
- 27: the sidecar is left out of the undo paragraph.
- 32: no record is pushed before its run.

No story changed a decision. The other decisions, in short:

1. The prompt's lines.
2. The Format check line goes to the first stage.
3. The Mode line comes from the last `result` record.
6. Only an open pull request is reused.
8. A boundary error after the claim leaves it for F0008.
10. The note comes after the push.
12. When the agent left the branch, nothing it left is kept.
13. Only a new form finding stalls.
14. A blank entry is `no_result`.
15. The undo paragraph.
20. The sidecar is rewritten after every undo.
23. The environment is the caller's.
24. There is no `stuck`.
25. The branch is reset to the remote.
26. A rework counts by `next`, not by position.
28. Findings are compared with their digits masked.
29. A `HostingServiceError` during a stall propagates.
30. The factory adds one commit per stage.
31. The work tree is committed whole.

Answers given on the stories' pull requests, all accepted as built:

- **S0004, entry 5:** option (a), the test asserts `stall_reason_of(result) == end_reason`.
- **S0005, entry 7:** option (a), criterion 17 names which of two equal findings is new.
- **S0007, entry 5:** option (a), the test definition gives the tester `lease_duration: 70`.

Open for the human to accept or revisit:

- **Two pull-request rules.** `StopService` (F0003) posts a stop on the recorded pull request even when it is closed, and opens a draft with the stop description. `WorkItemOpening` (F0005 decision 6) never reuses a closed one and opens a draft with the work item's text. Stalls take the second path. Both are as decided, but they are different rules for "the work item's pull request". F0007's close handler may make the difference moot. Accept the two rules, or say which should win.
- **Attempts across stages.** As in v1, a move never resets `attempts`. The attempts cap counts stalls over the work item's whole life, not per stage, until the human answers at the cap. Confirm this, or ask for a reset on a forward move like `crashes` has (that would be a change to S0007's tested rule).
- **The `_state_of` copies** (section 4). Four private copies of "the document has a state" raise three kinds of error. Unifying them would change F0004's tested `ValueError`. Leave them, or ask for one helper with a stated error.
- **Tester stages that cannot see `make types`.** Three of nine stories went to the human because a test was right in substance but could not pass `make check`:
  - S0004: a wider `Literal` assigned to a narrower annotation.
  - S0005: arithmetic on an `int | None` field without narrowing.
  - S0007: a test pipeline definition that broke F0003's lease rule.

  The tester runs `make lint` only. `CLAUDE.md` has since gained the load-time rule (commit 295e6bd); the two mypy traps are not in it yet. Adding them to `CLAUDE.md`'s test traps is yours to decide (see section 8).

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: no `make mutants` (see section 3), no image scan and no SBOM.

## 8 Cost

The nine stories cost 69 runs, 91.6 min and $21.49. Per story:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 | 6 | 7.3 | $1.95 |
| S0002 | 6 | 7.0 | $1.65 |
| S0003 | 8 | 8.8 | $2.35 |
| S0004 | 9 | 12.8 | $2.94 |
| S0005 | 13 | 14.5 | $3.40 |
| S0006 | 6 | 5.3 | $1.17 |
| S0007 | 9 | 16.6 | $3.53 |
| S0008 | 6 | 10.3 | $2.19 |
| S0009 | 6 | 9.0 | $2.31 |

Five stories went straight through in 6 runs: S0001, S0002, S0006, S0008 and S0009. Three stand out, and the logs say why:

- **S0005: 13 runs, $3.40.** The reviewer found an Interface rule with no criterion (which of two equal findings is new), and that cost a human round-trip (entries 5 to 8). The tester's new assertion then failed `mypy` on an `int | None` (entry 10), which cost a second coder and tester pair (entries 10 to 12). No code changed in round 1.
- **S0007: 9 runs, $3.53, 16.6 min, the most minutes.** The tests' own pipeline definition broke F0003's lease rule (40 + 5 + 10 + 10 + 3 = 68 > 60 min), so every finish test failed before it reached the code (entry 4). That cost one human round-trip. The minutes also come from real `make` targets in 28 finish tests.
- **S0004: 9 runs, $2.94.** A test could not pass `mypy --strict` against the Interface (entry 4), which cost one human round-trip and a tester run.

These three account for $9.87 of the $21.49. Their extra runs went into tests that could not pass the gate, which the tester stage cannot see, not into code. S0003's two extra runs were one review round that removed a copied refusal.

## Proposed stories

- `drafts/F0005-S0010-what-a-stall-shows-on-the-pull-request.md`: the note of a red check puts its output in a fenced `text` block and keeps the follow-up sentence on its first line, and a stall writes the `stage:` label after its note. Both gaps were found in the feature demo and by reading `StallService` (sections 2 and 4).
- `drafts/F0005-S0011-documentation-after-the-stage-protocol.md`: the README's and the operator guide's opening lists, a section on what a stage run shows, and "Stops of one work item" and "A stall: the stall note" corrected against the stall's behaviour and the not-yet-built cap gate (section 5). Documentation only.

## Log (append only)

1. acceptor: accepted with drafts; 2 drafts proposed; make mutants n/a (no target, by the decision in docs/decisions.md)
      1 Scope: none. Every scope item maps to S0001–S0009 and the code they name, and the Goal's done-condition holds. Nothing out of scope was built: no tick, hand-over, crash handling or image. One partial item: only the result commit writes labels, so a first stage that stalls leaves its pull request without a label (fix in S0010).
      2 Feature demo: green, exit 0. Ten stages ran through `StageRunner` on a real remote with real make targets:
         - The claim and the `started` record were on the remote before every run, and no cost record was pushed before its run.
         - The undo removed `docs/evil.md` and named it in the entry; lint and test lines followed.
         - A died run stalled with its partial write kept. A red check stalled under rule 5 with a 15-line tail. A decision that is not allowed hit the cap, and the "Retrying" wording dropped.
         - Rules 3 and 4 counted rounds, rule 1 asked the findings question, and rule 6 moved and reset crashes.
         - `factory-bill` in a fresh clone printed the table and line with `+ 1 unknown`.
         - Observed: the red-check note glues ". Retrying on the next tick." onto make's error line and posts the output as Markdown (S0010).
      3 Mutation score: no `make mutants` target, so no score. The hand-mutation copy was refused in this run, so I read the tests instead: the round cap, the 15-line tail, half-up rounding and the crash reset are each tested on both sides. Coverage is 99.43 %, and every missed F0005 line is a defensive refusal.
      4 Noticed: no story needed for the stories' items:
         - untested no-state and unknown-stage refusals;
         - four private `_state_of` copies raising three kinds of error;
         - the role refusal copied again as `stage.py` `_role_of`;
         - S0004 criterion 8's values do not fit the types;
         - `_is_work_item_id` rebuilds the id pattern.
        Seen in this review: the red-check note format and the missing stall label (S0010), and attempts never reset by a move (listed in 6).
      5 Documentation: the project guide's F0005 sections are current. Four findings in the operator's view, all for S0011:
         - The README and operator-guide opening lists stop at F0004 and the stall.
         - "Stops of one work item" gives `StopService`'s rule for stalls, which really use `WorkItemOpening`.
         - No section says what a stage run shows to the operator.
         - The stall-note section names four of nine causes and promises a gate at the cap that is not built (F0006/F0007).
      6 Decisions: the 32 FEATURE decisions stand as built. The three pull-request answers (S0004 entry 5, S0005 entry 7, S0007 entry 5) stand. Open for the human:
         - two pull-request rules (`StopService` against `WorkItemOpening`);
         - attempts counted over the work item's whole life;
         - whether to unify the `_state_of` copies;
         - adding the two mypy traps the testers hit to `CLAUDE.md`.
      7 Slow checks: none. No mutants target, no image scan, no SBOM.
      8 Cost: 69 runs, 91.6 min, $21.49. Three stories stand out:
         - S0005: 13 runs, $3.40; a criteria gap and a mypy error in a changed test.
         - S0007: 9 runs, $3.53, 16.6 min; the test definition broke the lease rule.
         - S0004: 9 runs, $2.94; a test could not pass mypy.
        Together they are $9.87, spent on tests the tester stage cannot type-check, not on code.
2. done (pull request merged); cost: 1 runs, 11.1 min, 62 turns, 192k tokens in (7148k more from cache), 51k out, $4.00
