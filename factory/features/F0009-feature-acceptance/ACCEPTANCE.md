---
stage: done
pr: 114
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0009-S0001, F0009-S0002, F0009-S0003, F0009-S0004, F0009-S0005, F0009-S0006, F0009-S0007, F0009-S0008, F0009-S0009, F0009-S0010, F0009-S0011]
outcome: accepted
---
# Acceptance of Feature acceptance

## Verdict

**accepted with drafts.** The feature does what `FEATURE.md` promises. The end-to-end demo below runs through the production `handler_factory` and real ticks over a real remote, and it is green: a feature with archived stories and a `.gitkeep` becomes due, its acceptance opens, the reviewer runs with its three facts, the hand-over builds the four-part description, a merge books it accepted and keeps the proposed story, a close books it refused with the human's reason, and another archived story opens `A0002`. Every scope item has its story and its code. `make check` is green, and a hand mutation pass killed 27 of 30 mutants.

There are three findings, and none of them breaks a promise:

- The project guide still says in one place that `acceptance_due` has no handler, and the README does not mention the feature acceptance at all.
- Opening an acceptance refuses a feature that is not due, but this is tested only for `incomplete`. Its other four refused statuses, and the "directly in the folder" rule, are pinned by nothing.
- The board shows a running acceptance only as `acceptance=in_flight`. It gives the acceptance no work item row, so the operator cannot see on the board that it waits for them.

One draft covers each finding.

## 1 Scope

None. Each scope item has its story and its code:

| Scope item | Stories | Code |
|---|---|---|
| Id `F0001-A0001`, report file name, `AcceptanceState` in the front matter | S0001 | `src/factory/domain/acceptance.py` (`acceptance_id`, `next_acceptance_id`, `acceptance_file_name`, `AcceptanceState`); `src/factory/adapters/work_item_markdown.py` |
| When an acceptance is due: story files only, six statuses, due features, reports on the remote | S0002 | `acceptance_status`, `story_file_ids` (domain); `AcceptanceReader.read`, `due_features` in `src/factory/application/acceptance_reading.py` |
| Watcher reads the due features and the reports, order after the stories, the board's column | S0008 | `AcceptanceReader.snapshots`, `fill_board`; `Watcher.evaluate`; `EvaluationInput.due` and `_due_order` in `src/factory/domain/evaluation.py`; `BoardReader.read` |
| The acceptance stage: opening with the head, the facts, write paths, its own cost line | S0003 | `AcceptanceService.open`/`facts`, `AcceptanceDueHandler` in `src/factory/application/acceptance.py`; `acceptance_facts`, `acceptance_head` |
| Through F0005's stage protocol | S0009 | `StoryFormChecker.findings` and `TaskComposer._prompt` in `src/factory/application/task.py` |
| At the approval: description by code, ready, cost table once, retry from state | S0004 | `AcceptanceHandOver`, `acceptance_description`, `cost_table_key` |
| Merge books `accepted`, close books `refused` with the reason first | S0005, S0007 | `AcceptanceMerged`, `AcceptanceClosed`, `book_merge`, `book_refusal`, `refusal_reason` |
| Merge before approval, repeated acceptances, handlers wired, `NOT_YET_HANDLED` empty | S0006, S0010, S0011 | `is_before_approval`; `build_handlers` and the `RunGate` splits in `src/factory/entry/wiring.py`; walks in `tests/application/test_acceptance_ticks_*.py` |

Each condition of the Goal's "Done when" is shown in the feature demo (section 2) or in S0011's walks:

- **Due with a `.gitkeep`:** demo step 1.
- **Sort order:** the demo's order line, and S0001 criteria 8 and 9 for the missing slug.
- **Merge accepted, close refused with the reason:** demo steps 1 and 2.
- **Merge before the approval:** S0011 criterion 1 (mutant 14 killed).
- **Repeated acceptance:** demo step 3 and S0011 criteria 7 to 10.
- **`NOT_YET_HANDLED` empty:** demo step 0.

No story went outside the scope. Out of scope stayed out: the report's sections and the proposed stories' form are not validated, there is no stopping rule, there are no reviewer instructions (F0010), and the reviewer may still overwrite a backlog story. Not promised, and so not a scope gap: the board gives a running acceptance no work item row. Draft S0012 proposes one.

## 2 Feature demo

This is the walk a user of the feature does, against the real entry points:

- `handler_factory` from `factory.entry.wiring`, one `Tick` per step, and `run_watch` (the `factory-watch` code);
- a real bare remote, a `GitCli` checkout and a human clone;
- `FakeHostingService` and `FakeAgentRuntime`. The scripted acceptance reviewer edits the report below its head, as a real one is told to, and writes one proposed story into the feature's backlog.

There are three features:

- **`F0002-2fa-login`** (its slug starts with a digit) is accepted with a draft.
- **`F0003-search`** is closed with a comment.
- **`F0003-search` again**, after another story is archived: the acceptance repeats.

The guard refuses files outside the repository, so the script ran from standard input and left no file. It is reproduced in full below the output.

```bash
uv run python - <<'EOF'   # the script below
```

```text
== 0. wiring and order ==
NOT_YET_HANDLED: ()
order: ['F0001-A0001', 'F0002-S0001', 'F0002-S0002', 'F0002-A0001', 'F0003-S0001']
== 1. feature F0002-2fa-login (slug starts with a digit): two archived stories and a .gitkeep ==
   status={'F0002': 'due'} due=['F0002']
   watch| event: acceptance_due:F0002  acceptance of F0002 is due
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=0  in-progress=0  done=2  acceptance=due
   watch| work items
tick 1 (opens the acceptance): event=acceptance_due:F0002 dispatch=handled agent runs so far=0
   branch: True | pull requests: 0
   report head: --- | stage: acceptance | blocked: null | round: 0 | attempts: 0 | crashes: 0 | pull_request: null | comments_read: [] | handed_over: null | claim: null | journal: [] | stories: [F0002-S0001, F0002-S0002] | outcome: null | --- |  | # Acceptance of Two-factor login |  | ## Journal | 
   status={'F0002': 'in_flight'} due=[]
tick 2 (the acceptance reviewer runs): event=run:F0002-A0001 dispatch=handled agent runs so far=1
   prompt's last three lines: ['Archived stories: F0002-S0001, F0002-S0002', 'Next free story number: F0002-S0003', 'Cost of the stories: 2 runs, 3.0 min, 3 turns, 30 tokens in (0 more from cache), 200 out, $1.50']
   pull request #1 draft=True title='F0002-A0001: Acceptance of Two-factor login'
   state on branch: ['stage: approval', 'blocked: null', 'pull_request: 1', 'handed_over: null', 'stories: [F0002-S0001, F0002-S0002]', 'outcome: null']
tick 3 (hand-over at the approval): event=hand_over:F0002-A0001 dispatch=handled agent runs so far=1
   pull request #1 draft=False; description:
      | ## Recommendation
      | 
      | **accepted with drafts.** The stories together do what the feature promised.
      | 
      | ## Findings in short
      | 
      | accepted with drafts; 1 drafts proposed
      | 
      | ## Proposed stories
      | 
      | - `F0002-S0003-lockout.md`: a gap the parts left.
      | 
      | Merge to accept the report and take the proposed stories into the feature's backlog, where you refine them before starting any. Close, with a comment saying why, to refuse: the report stays on the main branch as refused with your comment, the proposed stories are discarded, and the feature counts as not accepted until another story is archived and a new acceptance runs. Nobody answers comments while the acceptance waits here; they go into the report's journal.
   factory posts: ['Cost of this work item so far']
tick 4 (the human has not decided yet): event=idle:- dispatch=handled agent runs so far=1
tick 5 (still waiting: the hand-over is not repeated): event=idle:- dispatch=handled agent runs so far=1
   factory posts now: 1
   -- the human squash-merges --
   status={'F0002': 'merged_unrecorded'} due=[]
tick 6 (the merge is booked): event=merged:F0002-A0001 dispatch=handled agent runs so far=1
   booked state: ['stage: done', 'stories: [F0002-S0001, F0002-S0002]', 'outcome: accepted']
   last journal line: 3. factory: done (pull request merged); cost: 1 runs, 3.0 min, 12 turns, 0 tokens in (0 more from cache), 0 out, $0.42
   on main: ['factory/features/F0002-2fa-login/backlog/.gitkeep', 'factory/features/F0002-2fa-login/backlog/F0002-S0003-lockout.md', 'factory/features/F0002-2fa-login/done/F0002-A0001-acceptance.costs.jsonl', 'factory/features/F0002-2fa-login/done/F0002-A0001-acceptance.md', 'factory/features/F0002-2fa-login/done/F0002-S0001-totp.costs.jsonl', 'factory/features/F0002-2fa-login/done/F0002-S0001-totp.md', 'factory/features/F0002-2fa-login/done/F0002-S0002-recovery-codes.md', 'factory/features/F0002-2fa-login/feature.md']
   branch gone: True
   status={'F0002': 'incomplete'} due=[]
tick 7 (the proposed story waits for the human): event=idle:- dispatch=handled agent runs so far=1
== 2. feature F0003-search: reviewed, handed over, closed with a reason ==
tick 8 (opens the acceptance): event=acceptance_due:F0003 dispatch=handled agent runs so far=1
tick 9 (the acceptance reviewer runs): event=run:F0003-A0001 dispatch=handled agent runs so far=2
tick 10 (hand-over): event=hand_over:F0003-A0001 dispatch=handled agent runs so far=2
   -- the human comments on #2 and closes it --
tick 11 (the close is booked): event=closed:F0003-A0001 dispatch=handled agent runs so far=2
   booked state: ['stage: done', 'outcome: refused']
   recommendation section: Refused by the human on 2026-10-16: The ranking belongs to another feature. / **not accepted.** Ranking is missing.
   on main: ['factory/features/F0003-search/done/F0003-A0001-acceptance.costs.jsonl', 'factory/features/F0003-search/done/F0003-A0001-acceptance.md', 'factory/features/F0003-search/done/F0003-S0001-index.md', 'factory/features/F0003-search/feature.md']
   status={'F0002': 'incomplete', 'F0003': 'refused'} due=[]
tick 12 (refused rests): event=idle:- dispatch=handled agent runs so far=2
== 3. another story archived in F0003: due again, a new acceptance A0002 ==
   status={'F0002': 'incomplete', 'F0003': 'due'} due=['F0003']
tick 13 (opens the repeated acceptance): event=acceptance_due:F0003 dispatch=handled agent runs so far=2
   branch work-item/F0003-A0002: True | A0001 report unchanged: True
   A0002: ['stage: acceptance', 'stories: [F0003-S0001, F0003-S0003]']
   watch| event: run:F0003-A0002
   watch| 
   watch| features
   watch| F0001  Example feature  backlog=1  in-progress=0  done=0  acceptance=incomplete
   watch| F0002  Two-factor login  backlog=1  in-progress=0  done=2  acceptance=incomplete
   watch| F0003  Search  backlog=0  in-progress=0  done=2  acceptance=in_flight
   watch| work items
exit 0
```

What it shows, against the Goal:

- **Opening.** The feature is due with a `.gitkeep` and two story files. The acceptance opens with no pull request and with `stories` set.
- **The run and the hand-over.** The reviewer's prompt ends with the three facts. The facts' cost is the archived stories' only: S0001's sidecar, and none for S0002. The pull request is opened as a draft and turned ready at the hand-over. The description has its four parts, and the cost table is posted once. It is not posted again on later ticks.
- **The merge.** A squash merge gives `merged_unrecorded`, then one tick books it `accepted`. Its cost line counts its own run only ($0.42), the proposed story stays in the backlog, the branch is gone, and the feature is `incomplete`.
- **The close.** It books `refused`, with `Refused by the human on <date>: <comment>` first under the recommendation, and drops the proposed story.
- **The repeat.** One more archived story makes the feature due again. `A0002` opens with the new story set, and A0001's report stays byte for byte.
- **No loop.** No tick yields `reject`, and every waiting tick is `idle`.

Two observations from the walk:

- **The board.** In the last board, `F0003-A0002` is running, but the `work items` list is empty. The operator guide is consistent with this ("a work item row exists for each story in `in-progress/`"), so it is not a contradiction, but the operator cannot see a running or waiting acceptance there. Draft S0012.
- **A report written without its front matter.** My first run had the scripted reviewer write the report from scratch, without the front matter. The undo then found the report unreadable and restored it whole from the stage start (`UndoService._restore_work_item`). The reviewer's body was lost without a word in its journal entry, and the hand-over description read `none` under Recommendation and Proposed stories. This is F0005's rule for any work item and is not a defect of this feature. F0010, which writes the acceptance reviewer's instructions, should tell it to edit below the head and keep the front matter. Listed again under 4.

<details><summary>The demo script (run from the repository root as <code>uv run python - &lt;&lt;'EOF' … EOF</code>)</summary>

```python
"""Feature acceptance end to end: due, opened, reviewed, handed over, merged / closed, booked."""
import io, sys, tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "tests"))
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
from factory.application.acceptance_reading import AcceptanceReader
from factory.application.boundaries import Boundaries
from factory.application.tick import Tick
from factory.domain.agent_runs import AgentRunResult
from factory.domain.git import GitOptions
from factory.domain.identifiers import work_item_order
from factory.domain.kill_points import KillPoints
from factory.entry.watch import run_watch
from factory.entry.wiring import NOT_YET_HANDLED, handler_factory
from git_support import CHECKOUT, PIPELINE_YAML, TEST_IDENTITY, clone, install_agents, make_remote, remote_commit
from human_clone import HumanClone
from bill_support import completed_records, sidecar_text

ENV = {"PATH": "/usr/bin:/bin", "HOME": "/home/factory"}
root = Path(tempfile.mkdtemp(prefix="f9acc-"))
kp = KillPoints()
remote = make_remote(root / "origin")
git = GitCli(clone(remote, root / CHECKOUT), GitOptions(kill_points=kp, identity=TEST_IDENTITY))
human = HumanClone(root / "human", remote)
hosting = FakeHostingService(kp)
runtime = FakeAgentRuntime(kp)
clock = ManualClock(datetime(2026, 10, 16, 9, 0, tzinfo=UTC))
b = Boundaries(
    git=git, hosting=hosting, agent_runtime=runtime,
    project_commands=MakeProjectCommands(root / CHECKOUT, kp),
    work_item_reader=FrontmatterWorkItemReader(), work_item_writer=FrontmatterWorkItemWriter(),
    cost_reader=JsonLinesCostRecordReader(), cost_writer=JsonLinesCostRecordWriter(),
    pipeline_reader=RuamelPipelineDefinitionReader(),
    agent_definitions=FrontmatterAgentDefinitionReader(root / "home"),
    clock=clock, log=TimestampedFactoryLog(root / "state/factory.log", clock),
    health=JsonHealthStatusFile(root / "state/health.json"), checkout=root / CHECKOUT,
)
definition = b.pipeline_reader.parse(PIPELINE_YAML)
install_agents(root / "home", definition.roles)
n = 0

def tick(label):
    global n
    n += 1
    clock.advance(timedelta(minutes=5))
    out = Tick(b, "factory-1", handler_factory(b, "factory-1", ENV)).run()
    key = out.event.key if out.event else None
    print(f"tick {n} ({label}): event={key} dispatch={out.dispatch} agent runs so far={len(runtime.requests())}")

def watch():
    git.fetch(); o = io.StringIO(); run_watch(b, "factory-1", o, io.StringIO())
    for line in o.getvalue().splitlines():
        print("   watch| " + line)

def status():
    git.fetch(); r = AcceptanceReader(b, definition)
    return f"status={ {e.feature: e.status for e in r.read() if e.feature != 'F0001'} } due={r.due_features()}"

def show(ref, path):
    git.fetch(); return git.show_file(ref, path)

def files(ref, prefix):
    git.fetch(); return git.list_files(ref, prefix)

def keys(text, names):
    return [l for l in (text or "").split("\n---", 1)[0].splitlines() if l.split(":")[0] in names]

SECTIONS = "## Recommendation\n\n**{verdict}.** {why}\n\n## 1 Scope\n\nnone\n\n## Proposed stories\n\n{proposed}\n\n"
STORY = "# C\n\n## Description\n\nText.\n\n## Interface\n\nNone.\n\n## Acceptance criteria\n\n1. It works.\n\n## Smoke test\n\n```bash\ntrue\n```\nExpect: nothing.\n\n## Journal\n"

def review(work_item, path, verdict, why, proposed):
    """The reviewer edits the report below its head (front matter and title kept) and writes drafts."""
    head = show(f"origin/work-item/{work_item}", path)
    ptext = "\n".join(f"- `{p.rsplit('/', 1)[1]}`: a gap the parts left." for p in proposed) or "none"
    report = head.replace("## Journal", SECTIONS.format(verdict=verdict, why=why, proposed=ptext) + "## Journal", 1)
    runtime.queue(ScriptedRun(writes={path: report, **proposed}, result=AgentRunResult(
        end_reason="completed", decision="approval", entry=f"{verdict}; {len(proposed)} drafts proposed",
        duration=timedelta(minutes=3), turns=12, cost_usd=Decimal("0.42"))))

print("== 0. wiring and order ==")
print("NOT_YET_HANDLED:", NOT_YET_HANDLED)
print("order:", sorted(["F0002-A0001", "F0002-S0002", "F0003-S0001", "F0002-S0001", "F0001-A0001"], key=work_item_order))

print("== 1. feature F0002-2fa-login (slug starts with a digit): two archived stories and a .gitkeep ==")
F2 = "factory/features/F0002-2fa-login"
human.push_file("main", f"{F2}/feature.md", "# Two-factor login\n")
human.push_file("main", f"{F2}/backlog/.gitkeep", "\n")
human.push_file("main", f"{F2}/done/F0002-S0001-totp.md", "# TOTP\n")
human.push_file("main", f"{F2}/done/F0002-S0001-totp.costs.jsonl", sidecar_text(completed_records("F0002-S0001", 2)))
human.push_file("main", f"{F2}/done/F0002-S0002-recovery-codes.md", "# Recovery codes\n")
print("  ", status())
watch()
tick("opens the acceptance")
B2 = "origin/work-item/F0002-A0001"
R2 = f"{F2}/in-progress/F0002-A0001-acceptance.md"
print("   branch:", remote_commit(remote, "work-item/F0002-A0001") is not None, "| pull requests:", len(hosting.pull_requests()))
print("   report head:", (show(B2, R2) or "").replace("\n", " | "))
print("  ", status())
review("F0002-A0001", R2, "accepted with drafts", "The stories together do what the feature promised.", {f"{F2}/backlog/F0002-S0003-lockout.md": STORY})
tick("the acceptance reviewer runs")
print("   prompt's last three lines:", runtime.requests()[-1].prompt.splitlines()[-3:])
pr = hosting.pull_requests()[0]
print(f"   pull request #{pr.number} draft={pr.draft} title={pr.title!r}")
print("   state on branch:", keys(show(B2, R2), ("stage", "blocked", "pull_request", "stories", "outcome", "handed_over")))
tick("hand-over at the approval")
pr = hosting.pull_requests()[0]
print(f"   pull request #{pr.number} draft={pr.draft}; description:")
print("\n".join("      | " + l for l in hosting.description(pr.number).splitlines()))
print("   factory posts:", [c.body.splitlines()[0][:90] for c in hosting.factory_posts(pr.number)])
tick("the human has not decided yet")
tick("still waiting: the hand-over is not repeated")
print("   factory posts now:", len(hosting.factory_posts(pr.number)))
human.merge("work-item/F0002-A0001", "squash")
hosting.merge_by_human(pr.number, remote_commit(remote, "main"))
print("   -- the human squash-merges --")
print("  ", status())
tick("the merge is booked")
booked = show("origin/main", f"{F2}/done/F0002-A0001-acceptance.md") or ""
print("   booked state:", keys(booked, ("stage", "outcome", "stories")))
print("   last journal line:", [l for l in booked.splitlines() if l.strip()][-1])
print("   on main:", files("origin/main", F2))
print("   branch gone:", remote_commit(remote, "work-item/F0002-A0001") is None)
print("  ", status())
tick("the proposed story waits for the human")

print("== 2. feature F0003-search: reviewed, handed over, closed with a reason ==")
F3 = "factory/features/F0003-search"
human.push_file("main", f"{F3}/feature.md", "# Search\n")
human.push_file("main", f"{F3}/done/F0003-S0001-index.md", "# Index\n")
tick("opens the acceptance")
R3 = f"{F3}/in-progress/F0003-A0001-acceptance.md"
review("F0003-A0001", R3, "not accepted", "Ranking is missing.", {f"{F3}/backlog/F0003-S0002-ranking.md": STORY})
tick("the acceptance reviewer runs")
tick("hand-over")
pr3 = hosting.pull_requests()[-1]
hosting.add_human_comment(pr3.number, "The ranking belongs to another feature.")
hosting.close_by_human(pr3.number)
print(f"   -- the human comments on #{pr3.number} and closes it --")
tick("the close is booked")
booked3 = show("origin/main", f"{F3}/done/F0003-A0001-acceptance.md") or ""
print("   booked state:", keys(booked3, ("stage", "outcome")))
print("   recommendation section:", booked3.split("## Recommendation", 1)[1].split("\n## ", 1)[0].strip().replace("\n\n", " / "))
print("   on main:", files("origin/main", F3))
print("  ", status())
tick("refused rests")

print("== 3. another story archived in F0003: due again, a new acceptance A0002 ==")
human.push_file("main", f"{F3}/done/F0003-S0003-filters.md", "# Filters\n")
print("  ", status())
tick("opens the repeated acceptance")
print("   branch work-item/F0003-A0002:", remote_commit(remote, "work-item/F0003-A0002") is not None,
      "| A0001 report unchanged:", show("origin/main", f"{F3}/done/F0003-A0001-acceptance.md") == booked3)
print("   A0002:", keys(show("origin/work-item/F0003-A0002", f"{F3}/in-progress/F0003-A0002-acceptance.md"), ("stage", "stories")))
watch()
```

</details>

## 3 Mutation score

The project has no `make mutants` target, by the decision "No `mutants` target, no mutmut" in `docs/decisions.md`. As earlier acceptances did, I ran a hand pass instead, set up like this:

- **Mutants:** 30, chosen on the feature's rules:
  - 16 in `src/factory/domain/acceptance.py`;
  - 10 in `src/factory/application/acceptance.py`;
  - 2 in `src/factory/application/acceptance_reading.py`;
  - one each for the due ranking in `src/factory/domain/evaluation.py` and the facts' gate in `src/factory/application/task.py`.
- **How each was applied:** in memory only. A meta-path finder compiled the mutated source in place of the module, with `PYTHONDONTWRITEBYTECODE=1`, so no file in the checkout changed. `git status` afterwards showed only this report and the drafts.
- **Tests run:** the feature's 30 test modules: every `tests/*/test_*acceptance*.py`, plus `test_evaluation_due.py`, `test_board_reader.py`, `test_split_by_work_item_kind.py`, `test_wiring_handlers.py` and `test_wiring_human_handlers.py`. Each mutant ran with `pytest -x`.

**Score: 27 of 30 killed.**

Every mutant of the status rules was killed: in flight, merged unrecorded, incomplete, the covering set, the highest id, and story files only. So were the facts, the description's `none` and the result-only findings, the refusal reason (after the result, blank comments skipped), the before-approval boundary, the cleared `blocked`, the push check, the hand-over guard (`handed_over`, approval stage), the merged and closed guards, the single `close` record, the "already in `done/`" guard, the empty-records copy, the kind split, the branch's document in snapshots, the rank after the stories and the facts only at the acceptance stage.

The survivors, grouped by rule:

| # | Module | Mutant | Missing criterion |
|---|---|---|---|
| 16 | `application/acceptance.py` `AcceptanceService.open` | `if acceptance.status != "due"` → `if acceptance.status == "incomplete"` | `open` refusing `in_flight`, `merged_unrecorded`, `accepted` and `refused`. Only `incomplete` is tested (S0003 criterion 11). The weakened guard would start a second acceptance beside a running one. |
| 26 | `application/acceptance_reading.py` `_names` | `if len(path.parts) == 1` dropped | Decision 3's "directly in `backlog/`, `in-progress/` or `done/`": a story file in a subdirectory counts with the mutant, and no test sees it. |
| 8 | `domain/acceptance.py` `acceptance_facts` | `number > _LAST_NUMBER` → `number > _LAST_NUMBER + 1` | Near-equivalent. Pydantic then refuses `F0002-S10000` with a `ValidationError`, which is a `ValueError`, so the test's `pytest.raises(ValueError)` passes with the wrong message. Pinning the exact type and message closes it. |

Draft S0014 covers all three. Line coverage is 99.53 %. The lines it misses in the feature's modules are two defensive branches: `acceptance_reading.py:238`, a report listed but missing at its ref, and `domain/acceptance.py:320`, trailing blank lines of a hand-edited report without a journal.

## 4 What the stories noticed

These are collected from the coder, reviewer and documenter entries of the eleven stories, each checked against today's code:

- **Fixed since by a later story:**
  - The project guide's "`FeatureRow.acceptance` is always `None` until F0009-S0001" (S0001, S0002 documenters) was fixed by S0008.
  - The operator guide's "`acceptance_due` is not yet handled" (S0002 documenter) was fixed by S0010.
  - The three "not yet registered in `build_handlers`" sentences of the operator guide were fixed by S0011.
  - `AcceptanceService._feature_title` and `_records` resembled private helpers of the board and the bill (S0003 coder). Both now go through the shared `read_feature_file` and `read_cost_records`.
- **Still stale:** the project guide still says in two places that the acceptance is not wired. This is S0002's remark, not fully repaired. Draft S0013.
- **Defensive branches in `acceptance_reading.py`:**
  - A branch report whose feature directory is missing on main (S0008 coder) is now pinned, along with a report on main in another feature's directory, by S0008 criterion 20 (the human's answer, entry 7).
  - A report listed but missing at its ref (S0002 coder and reviewer) is still uncovered (`acceptance_reading.py:238`). Low weight.
- **No-state refusals untested:** `AcceptanceMerged._book` raises `CannotHandle("the report on the main branch has no state")` with no test (S0006 coder, counted by no reviewer). The hand-over and close handlers' no-state refusals (`application/acceptance.py:205` and `:339`) are in the same position. This is the same class as the open draft F0008-S0007, "The no-state refusals of require_state's callers". The human may extend that draft with these three calls rather than start a new one, so I wrote none.
- **Story `MergedHandler` (F0007) has no "already in `done/`" guard,** so a second run fails in `git mv` (S0005 coder). Today this is harmless. After a kill between the push of main and the branch deletion, the story is in `done/` on main, so no `merged` event is raised again, and the tick's stale-branch deletion (F0008-S0004) removes the branch. It is worth a kill-point case in F0011. No draft.
- **One-line duplicates, too small for a story:**
  - "Today in UTC" is written twice, in `handlers/closed.py:93` and `AcceptanceClosed._today` (S0007 coder).
  - `entry/check_story.py` builds the feature file's path by hand instead of with `feature_file_path` (S0003 coder and documenter).
- **An empty cost-records file is not copied to `main` on a close** (S0007 coder). It is pinned (mutant 24 killed). It is a choice, not a defect.
- **`SplitByWorkItemKind` sends every id that is not an acceptance to the story handler** (S0004 coder). This is by design: the id is already validated.
- **Mine, from the demo:**
  - The board has no row for a running acceptance. Draft S0012.
  - A reviewer that drops the report's front matter loses its whole report silently (section 2). For F0010's reviewer instructions.

## 5 The documentation as a whole

I read `README.md`, the acceptance sections of `docs/operator-guide.md` ("When a feature acceptance is due", "The hand-over of an acceptance" with merge, close, merged before approval, accepted again, no loop and a close handled again), the project guide's "The feature acceptance", "Events" and "The handlers of the events", and the three F0009 entries of `docs/decisions.md`.

The operator guide agrees with the demo, word for word where it quotes:

- the four description parts and the closing text;
- `Refused by the human on <date>: <comment>` first under the recommendation;
- `done (pull request merged); cost: ...` with the acceptance's own cost;
- `merged_unrecorded` before the booking, `incomplete` after a merge that brought proposed stories, and due again after another archive.

The findings:

- **Contradiction inside the project guide.** "Events" (`docs/project-guide.md:505`) ends with "`build_handlers` registers every kind except `acceptance_due`, which belongs to F0009". "The handlers of the events" (`:579`, `:581`), the operator guide and the code all say that every kind has a handler and that `NOT_YET_HANDLED` is empty. This misleads an agent, not the operator.
- **Stale.** `docs/project-guide.md:459` says `SplitByWorkItemKind` is registered "by F0009-S0010; until then it is not in `build_handlers`".
- **Missing for the newcomer.** `README.md` lists what is built so far and does not mention the feature acceptance. Its only trace is in the operator guide's intro, as a parenthesis ("for an acceptance, a close books it refused").
- **Imprecise.** The operator guide says "Only story files count" but not "directly in the folder", which decision 3 and the project guide say. This is covered by S0014's docs criterion.

Draft S0013 repairs the first three. None of them is a contradiction between documentation and behaviour that misleads the user (the operator), so none weighs on the verdict.

## 6 Decisions taken for the human

From `FEATURE.md` (decisions 1 to 22), in short. Each is for the human to accept or revisit:

1. Every acceptance is a work item of its own (`F0001-A0001`, numbered per feature, gaps never filled), with its own report file and cost records. There is no single overwritten report.
2. `AcceptanceState` adds `stories` and `outcome` to the front matter. The F0002 reader and writer learn them.
3. Only story files directly in the lifecycle folders count. Two directories with one feature id: the first in name order counts.
4. Status precedence: in flight, merged unrecorded, incomplete, the recorded result, due. **Consequence:** after a merge that brought proposed stories, the feature is `incomplete` until they are archived, and then it is due again. Each accepted round of drafts leads to another acceptance. The stopping rule is out of scope (v2).
5. Without an `acceptance_stage` there are no acceptances. The handlers are still registered and refuse with `no acceptance stage`.
6. Opening pushes only the report's head. There is no `created` entry, no claim and no pull request.
7. The next free story number counts the backlog, in progress and done, with four digits.
8. The facts are three prompt lines computed by code. The cost counts the archived stories' records only.
9. The description has four parts, with `none` for a missing part. The findings are the reviewer's last `result` entry as written.
10. The closing text names no merge method, and says that comments while it waits are only journaled.
11. The cost table is posted once with F0007's key. A recorded hand-over does nothing.
12. **A merge books `accepted` whatever the recommendation says.**
13. The reason of a refusal is the human's comments after the last result, joined with one space (`no reason given` when there are none), placed first under the recommendation.
14. A refusal keeps the report and its costs at `done/` and drops the proposed stories. A merge keeps them. A `## Recommendation` is added when it is missing.
15. A merge before the approval is booked `accepted` with an entry that says so.
16. A repeated acceptance is a new work item. Earlier reports stay.
17. Acceptances run through F0005's stage protocol with two additions in `task.py`. **Alternative offered:** a separate stage runner.
18. `AcceptanceReader.snapshots()` feeds the watcher. `EvaluationInput.due` replaces `due_events()`.
19. A close at any stage books `refused`.
20. The close handler can be rerun after its branch is gone.
21. The handlers are named `Acceptance*`. Two F0007 helpers were made public (`cost_table_key`, `move_with_cost_records`). An acceptance ends at its first close.
22. Tests of other stories changed with leave, in three groups. **The third group** (`tests/application/test_board_reader.py`, granted "by the session for the human, 2026-10-14, night; for the human to confirm in the morning") **and the second** (`tests/test_no_journal_reading.py`) are still marked for the human's confirmation.

From the story logs (the human's answers, recorded there):

- S0004 entry 3: a criterion for a push race at the hand-over, tested through a `FakeHostingService` subclass that pushes in `set_description`.
- S0005 entry 3: `refusal_reason` strips each comment and skips blank ones, matching F0007's answer rule.
- S0008 entry 7: a criterion added for two skipped cases of `snapshots()`, with no code change.
- S0011 entry 3: the walk setup, with a proposed story pushed to the branch, two rows for the repeated merge, and `add_human_comment` before `close_by_human`.
- S0004 entry 7, S0007 entry 5 and S0011 entry 7: one-line test fixes approved (two type annotations and a full-path comparison).

Defaults I noticed that no decision names:

- The facts' cost line includes only stories with a sidecar, silently. The demo's `F0002-S0002` had none, and the line does not say that a story is missing.
- The reviewer's report is restored whole when its front matter is unreadable (F0005's rule), with no word in the journal.

## 7 The slow checks

None. The project offers nothing beyond `make check`: no image scan, no SBOM, no `make mutants` (by decision). `make check` was green as I found it: lint, types, layers, sast, secrets, licenses, and tests at 99.53 % coverage, in 3 min 00 s.

## 8 Cost

The eleven stories cost 93 runs, 259.2 min and $29.71. That is an average of 8.5 runs, 23.6 min and $2.70 per story.

| Story | Runs | Min | $ | Why it stands out |
|---|---|---|---|---|
| S0008 | 11 | 27.2 | 4.12 | The highest cost in dollars. The reviewer found two refused sides of an Interface rule that no criterion named. The question to the human was followed by a test-only round. |
| S0005 | 9 | 22.6 | 3.75 | An intake question on `refusal_reason`, two quality findings, and one run whose lease expired (entry 8). |
| S0011 | 14 | 37.3 | 3.54 | The most runs. Two questions (three setup gaps at intake, then a mypy error in the tester's helper) and a review round on duplicated test helpers, with no change to `src/` at all. |
| S0009 | 10 | 37.0 | 2.09 | Long but cheap. A one-line test finding (`assert pull_request.draft`) went coder → tester → coder → reviewer. |

The other seven stories cost between $1.69 and $3.37.

A pattern across stories: S0004 and S0011 each spent a human round trip on a mypy error in a test that the tester stage cannot see, because by `stages.yml` it runs `make lint` and `make test` but not `make types`. S0007 did the same for a wrong assertion. That is a matter for the pipeline's own files (the human's), not for a story of this feature.

## Proposed stories

- `drafts/F0009-S0012-a-running-acceptance-on-the-board.md`: the board gives a running acceptance a work item row (stage, waits, pull request), placed after its feature's stories. Found in the feature demo.
- `drafts/F0009-S0013-the-documents-say-the-acceptance-is-wired.md`: repairs the project guide's contradiction about `acceptance_due` and its stale "until then", and adds the feature acceptance to the README.
- `drafts/F0009-S0014-the-refused-sides-of-opening-an-acceptance.md`: pins the three mutation survivors: `open` refusing every status other than `due`, story files only directly in the folders, and the exact error at story number 9999.

## Log (append only)

1. acceptor: accepted with drafts; 3 drafts proposed; make mutants 27/30 (hand pass: the project has no `make mutants` target by decision, so 30 mutants were applied in memory against the feature's 30 test modules)
   1 Scope: every scope item has its story and its code, and each "Done when" condition is shown. Nothing out of scope was built. Not promised, and not a gap: the board gives a running acceptance no work item row (S0012).
   2 Feature demo: green. It used the production `handler_factory`, 13 real ticks, a real remote and `run_watch`, with three features: one due with a `.gitkeep`, opened, reviewed, handed over, squash-merged and booked accepted with its proposed story kept; one closed with a comment and booked refused with the reason first; one due again after another archive, opening A0002 with A0001 unchanged. No `reject`. Observation: a reviewer that drops the report's front matter loses the whole report silently (F0005's restore rule), which matters for F0010's instructions.
   3 Mutation: 27/30 killed. Survivors: `open` is tested only against `incomplete`, not the other four non-due statuses; "story files directly in the folder" is unpinned; the 9999 limit's exact error is unpinned. All three go to S0014. Coverage is 99.53 %.
   4 Noticed: most items were fixed by later stories. Still open: the project guide's stale wiring sentences (S0013); the untested no-state refusals of the three acceptance handlers, which could extend the open draft F0008-S0007; the story `MergedHandler`'s missing done/ guard, harmless today and a case for F0011's kill points; two one-line duplicates.
   5 Docs: `docs/project-guide.md:505` says `acceptance_due` is not registered, contradicting `:579`, `:581`, the operator guide and the code. `:459` still says "until then". The README does not mention the feature acceptance. The operator guide matches the demo. All go to S0013.
   6 Decisions: FEATURE.md's 22 are listed. Flagged for the human: merge accepts whatever the recommendation says (12); the accepted-drafts loop that decision 4 implies, with no stopping rule; the separate-runner alternative (17); the test-change leave of decision 22, still "for the human to confirm"; and two silent defaults (the facts' cost skips stories without a sidecar, the report restored whole).
   7 Slow checks: none beyond `make check`, which was green as found (3 min, 99.53 %).
   8 Cost: 93 runs, 259.2 min, $29.71 (about $2.70 per story). S0008 is the top cost at $4.12 (a missing criterion caught in review led to a question and a test round). S0011 has the most runs (14, with no change to src). S0009 is long but cheap. Pattern: the tests stage does not run `make types`, so mypy errors in tests cost S0004 and S0011 a human round trip each. That is a matter for the pipeline's own files.
   Open: none for this stage. The drafts (S0012 board row, S0013 docs repair, S0014 refused sides) are the human's to refine and promote.
2. done (pull request merged); cost: 1 runs, 26.6 min, 89 turns, 221k tokens in (11408k more from cache), 77k out, $5.60
