---
stage: done
pr: 57
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0004-S0001, F0004-S0002, F0004-S0003, F0004-S0004, F0004-S0005]
outcome: accepted
---
# Acceptance of Claim and write paths

## Verdict

**accepted with drafts.** Every scope item and every clause of the Goal is built. The feature demo is green end to end: two instances race for one stage, the lease clock, a rewrite of the pipeline definition in the work tree, the real `factory-guard` command and the undo. It shows that the guard and the undo give the same verdict on each path. `make check` is green at 99.68 %. The one finding of weight is the documentation as a whole. `README.md` still lists the built parts without anything from F0004 and calls `factory-check-story` "the one command so far". The operator guide's opening list also misses the claim and the undo. Neither is a broken promise, so I propose one documentation draft (S0006).

## 1 Scope

None. Each scope item maps to one story and its code:

- The stage-start commit, `PushFailed` on a rejected or unreachable push, and no claim on the remote: S0001, `src/factory/application/claims.py` (`ClaimService.claim`, `StageStart`, `started_text`) and `PushFailed` in `src/factory/domain/errors.py`.
- The lease clock as pure functions (`src/factory/domain/lease.py`: `lease_age`, `lease_expired`, `claim_status`), `ClaimService.status` and `release`, `lease_duration` copied into the claim, and the source-search tests (`tests/test_claim_ownership.py`): S0001 and S0002.
- The matching rule, the two placeholders, `PROTECTED_PATHS` (ten patterns), the one `refusal`, and `WritePathService.at`, which parses `factory/pipeline.yml` at the stage-start commit: S0003, `src/factory/domain/write_paths.py` and `src/factory/application/write_paths.py`.
- `factory-guard --settings <file>`: S0004, `src/factory/entry/guard.py` (re-exported through `factory.entry.wiring`) and `src/factory/adapters/claude_guard.py`. It is registered in `pyproject.toml`, and `ClaudeCodeRuntime` hooks it on `Edit|Write`.
- The undo and restore: S0005, `src/factory/application/undo.py`.

The Goal's done-condition holds, as section 2 shows:

- A claim reaches the remote only through its push.
- `own`, `held` and `expired` are told apart by the one service.
- A rewrite of `factory/pipeline.yml` in the work tree widens nothing and breaks neither the guard nor the undo.

Out of scope stays out. Nothing in `factory.entry` wires `ClaimService`, `WritePathService` or `UndoService`: starting the agent run and the timing of the undo belong to F0005. No first-look recognition (F0006), no rerun (F0008) and no fail-closed guard were built.

## 2 Feature demo

This is the walk of a factory operator, end to end, against the real entry points. It uses a bare remote and two clones, `GitCli`, two `ClaimService` instances with a `ManualClock`, `WritePathService`, the installed `factory-guard` command (run as a subprocess with real Claude Code `PreToolUse` payloads), `UndoService` and the domain's `refusal`. It has five steps:

1. Two instances race for one stage. The push decides.
2. One service tells `own`, `held` and `expired` apart at the edge of a 45-minute lease, and `release` clears the claim.
3. The agent rewrites `factory/pipeline.yml` in the work tree to `write_paths: ["*"]`. The settings still come from the stage-start commit, and the guard refuses outside them, including through `..` and outside the checkout.
4. The agent writes anyway, as a shell command would. The undo reverts the definition and another work item in progress, and deletes a new file outside the write paths and a cost record. It restores the work item's state and keeps its section edit. A second undo finds nothing.
5. The guard and the undo agree on each path.

A first attempt with `lease_duration: 30` was refused at parse: `role coder at stage doing: 40 min exceed lease_duration 30 min`. That is F0003's lease rule working (GH1.4), so the demo uses 45.

Run from the repository root, with the script outside the repository:

```bash
uv run python /tmp/f4demo/demo.py; echo "exit $?"
```

The script, `/tmp/f4demo/demo.py`:

```python
import json, os, subprocess, tempfile
from dataclasses import replace
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
from factory.application.claims import ClaimService
from factory.application.undo import UndoService
from factory.application.write_paths import WritePathService
from factory.domain.errors import PushFailed
from factory.domain.journal import JournalRecord
from factory.domain.work_item import WorkItemDocument, initial_state
from factory.domain.write_paths import refusal

for k in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"): os.environ[k] = "demo"
for k in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"): os.environ[k] = "demo@example.invalid"
os.environ["GIT_CONFIG_GLOBAL"] = "/dev/null"

PIPELINE = """contract: "1.0"
roles:
  coder: {write_paths: ["src/*", "{work_item}"], lease_duration: 45}
stages:
  doing: {role: coder, next: [done]}
  done: {}
"""
WIDE = PIPELINE.replace('["src/*", "{work_item}"]', '["*"]')
FEAT = "factory/features/F0009-demo"
PATH = f"{FEAT}/in-progress/F0009-S0001-demo.md"
OTHER = f"{FEAT}/in-progress/F0009-S0002-other.md"
BRANCH = "work-item/F0009-S0001"
BODY = "# Demo\n\n## Assignment\n\nOriginal.\n\n## Journal\n\n1. 2026-10-14 human: created.\n"

root = Path(tempfile.mkdtemp())
remote, seed, w1, w2 = root / "remote.git", root / "seed", root / "w1", root / "w2"
def sh(*a, cwd=None): return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout
state = initial_state("doing").model_copy(update={"journal": [JournalRecord(number=1, speaker="human", kind="created")]})
writer = FrontmatterWorkItemWriter()
sh("init", "-q", "--bare", "-b", "main", str(remote)); sh("clone", "-q", str(remote), str(seed))
(seed / "factory").mkdir(); (seed / "factory/pipeline.yml").write_text(PIPELINE)
(seed / "src").mkdir(); (seed / "src/app.py").write_text("x = 1\n")
(seed / PATH).parent.mkdir(parents=True)
(seed / PATH).write_text(writer.render(WorkItemDocument(state=state, body=BODY)))
(seed / OTHER).write_text(writer.render(WorkItemDocument(state=initial_state("doing"), body="# Other\n")))
sh("add", "-A", cwd=seed); sh("commit", "-qm", "seed", cwd=seed); sh("push", "-q", "origin", "HEAD:main", cwd=seed)

clock = ManualClock(datetime(2026, 10, 14, 9, 0, tzinfo=UTC))
g1, g2 = GitCli(w1), GitCli(w2)
for g in (g1, g2):
    g.clone(str(remote)); g.checkout(BRANCH, start_point="origin/main")
b1 = Boundaries(git=g1, hosting=FakeHostingService(), agent_runtime=FakeAgentRuntime(), project_commands=MakeProjectCommands(w1),
    work_item_reader=FrontmatterWorkItemReader(), work_item_writer=writer, cost_reader=JsonLinesCostRecordReader(),
    cost_writer=JsonLinesCostRecordWriter(), clock=clock, log=TimestampedFactoryLog(root / "log", clock),
    health=JsonHealthStatusFile(root / "health.json"), pipeline_reader=RuamelPipelineDefinitionReader(),
    agent_definitions=FrontmatterAgentDefinitionReader(root / "claude"), checkout=w1)
b2 = replace(b1, git=g2, project_commands=MakeProjectCommands(w2), checkout=w2)
definition = b1.pipeline_reader.parse(PIPELINE)
one, two = ClaimService(b1, "factory-1", definition), ClaimService(b2, "factory-2", definition)

print("1. the push is the claim")
start = one.claim(BRANCH, PATH, b1.work_item_reader.read(w1 / PATH), "doing")
print("  ", start.claim.instance, start.claim.stage, start.claim.lease_duration, g1.resolve("origin/" + BRANCH) == start.commit)
try:
    two.claim(BRANCH, PATH, b2.work_item_reader.read(w2 / PATH), "doing")
except PushFailed as e:
    print("   factory-2:", type(e).__name__, e.outcome, "| remote still factory-1's:", sh("--git-dir", str(remote), "rev-parse", BRANCH).strip() == start.commit)

print("2. one service tells own, held and expired apart")
g2.fetch()
remote_state = b2.work_item_reader.parse(g2.show_file("origin/" + BRANCH, PATH)).state
clock.advance(timedelta(minutes=44, seconds=59))
print("   at 44:59:", one.status(remote_state), two.status(remote_state))
clock.advance(timedelta(seconds=1))
print("   at 45:00:", one.status(remote_state), two.status(remote_state))
released = one.release(b1.work_item_reader.read(w1 / PATH))
print("   released:", two.status(released.state))

print("3. the agent widens its write paths in the work tree; nothing reads that")
(w1 / "factory/pipeline.yml").write_text(WIDE)
settings = WritePathService(b1).at(start, PATH)
print("   write paths:", settings.write_paths)
guard_file = root / "guard.json"; guard_file.write_text(settings.model_dump_json())
def guard(file_path):
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})
    r = subprocess.run(["factory-guard", "--settings", str(guard_file)], input=payload, capture_output=True, text=True)
    return r.returncode, r.stderr.strip()
CASES = ["src/new.py", PATH, "docs/evil.md", "factory/pipeline.yml", OTHER, f"{FEAT}/feature.md", "src/../Makefile", "../outside.txt"]
for p in CASES:
    print(f"   guard {p}: {guard(str(w1 / p))}")

print("4. the agent writes anyway (as if through Bash); the undo puts it back")
(w1 / "src/new.py").write_text("ok\n")
(w1 / "docs").mkdir(); (w1 / "docs/evil.md").write_text("evil\n")
(w1 / OTHER).write_text("hijacked\n")
(w1 / f"{FEAT}/in-progress/F0009-S0001.cost.jsonl").write_text("{}\n")
doc = b1.work_item_reader.read(w1 / PATH)
doc = doc.model_copy(update={"state": doc.state.model_copy(update={"stage": "done", "claim": None}),
                             "body": doc.body.replace("Original.", "Edited by the agent.")})
writer.write(w1 / PATH, doc)
report = UndoService(b1).undo(start, PATH)
print("   reverted:", report.reverted)
print("   deleted:", report.deleted)
print("   restored work item:", report.restored_work_item)
after = b1.work_item_reader.read(w1 / PATH)
print("   state back:", after.state.stage, after.state.claim == start.claim, "| section edit kept:", "Edited by the agent." in after.body)
print("   src/new.py kept:", (w1 / "src/new.py").exists(), "| pipeline.yml is main's:", (w1 / "factory/pipeline.yml").read_text() == PIPELINE)
print("   second undo:", UndoService(b1).undo(start, PATH))
print("5. guard and undo agree: same refusal over the same settings")
for p in ["src/new.py", "docs/evil.md", "factory/pipeline.yml", OTHER]:
    print(f"   {p}: guard={guard(str(w1 / p))[0]} refusal={refusal(p, settings) is not None}")
```

Output:

```
1. the push is the claim
   factory-1 doing 45 True
   factory-2: PushFailed rejected | remote still factory-1's: True
2. one service tells own, held and expired apart
   at 44:59: own held
   at 45:00: own expired
   released: none
3. the agent widens its write paths in the work tree; nothing reads that
   write paths: ['src/*', 'factory/features/F0009-demo/in-progress/F0009-S0001-demo.md']
   guard src/new.py: (0, '')
   guard factory/features/F0009-demo/in-progress/F0009-S0001-demo.md: (0, '')
   guard docs/evil.md: (2, 'docs/evil.md is outside the write paths of this stage.')
   guard factory/pipeline.yml: (2, 'factory/pipeline.yml is owned by the human; a change there is a question.')
   guard factory/features/F0009-demo/in-progress/F0009-S0002-other.md: (2, 'factory/features/F0009-demo/in-progress/F0009-S0002-other.md is outside the write paths of this stage.')
   guard factory/features/F0009-demo/feature.md: (2, 'factory/features/F0009-demo/feature.md is owned by the human; a change there is a question.')
   guard src/../Makefile: (2, 'Makefile is owned by the human; a change there is a question.')
   guard ../outside.txt: (2, '/tmp/tmpggt5upsm/w1/../outside.txt is outside the checkout.')
4. the agent writes anyway (as if through Bash); the undo puts it back
   reverted: ['factory/features/F0009-demo/in-progress/F0009-S0002-other.md', 'factory/pipeline.yml']
   deleted: ['docs/evil.md', 'factory/features/F0009-demo/in-progress/F0009-S0001.cost.jsonl']
   restored work item: True
   state back: doing True | section edit kept: True
   src/new.py kept: True | pipeline.yml is main's: True
   second undo: reverted=[] deleted=[] restored_work_item=False
5. guard and undo agree: same refusal over the same settings
   src/new.py: guard=0 refusal=False
   docs/evil.md: guard=2 refusal=True
   factory/pipeline.yml: guard=2 refusal=True
   factory/features/F0009-demo/in-progress/F0009-S0002-other.md: guard=2 refusal=True
exit 0
```

All five steps met what the Goal promises.

- Step 3: the `in-progress` work item `F0009-S0002` is refused by the guard only because `src/*` does not reach it. The guard does not know the undo's `in-progress` rule (FEATURE.md decision 13). With `write_paths: ["*"]` the guard would allow that write and only the undo would put it back, as documented.
- Step 4: the file I wrote as a "cost record" is named `.cost.jsonl`, not the real suffix `.costs.jsonl`. It is deleted under the rule's "any other file there" clause, so the outcome is the same. The real suffix is covered by `tests/application/test_undo.py`.

## 3 Mutation score

No score. The project has no `make mutants` target, by a recorded decision (`docs/decisions.md`, "No `mutants` target, no mutmut"). So there are no survivors to group. Two stories' reviewers did the mutation reasoning by hand, and both findings were closed with tests:

- S0003, entry 5: the "unsafe before protected" order was untested on its protected side. Two cases were added.
- S0005, entries 9 and 13: the allowed side of the "directly in an `in-progress` folder of a feature" rule was untested. Deleting the prefix check at `src/factory/application/undo.py` would have passed every test. Cases for `backlog/`, `in-progress/sub/` and `src/in-progress/` were added.

`make check` coverage is 99.68 %. `src/factory/entry/guard.py:56` (the `__main__` line, run only in a subprocess) is the one F0004 line not covered.

## 4 What the stories noticed

Nothing here needs a story.

- **S0001, coder:** `_with_claim` gets the state through `_state_of` a second time. This is harmless, because the preconditions have already guaranteed the state. It is a style remark, not a defect.
- **S0004, intake, coder, reviewer and demo:** a `file_path` that resolves to the checkout root itself reaches `refusal(".")`. It is refused under narrow write paths and allowed under `["*"]`, and a write to a directory fails in the tool anyway. Four stages noted it, and none made it a finding. I agree.
- **S0005, coder:** writes to ignored paths and outside the checkout are not seen. That is v2 by the feature's Out of scope.
- **S0005, reviewer, coder and demo (entries 13, 16, 17, 19):** no acceptance criterion states the allowed side of the `in-progress` rule. The tests cover it now (`test_files_not_directly_in_an_in_progress_folder_follow_the_write_paths`), and the project guide states it ("Nested files … follow the write paths"). The archived story text is the only place it is missing, and that is history.
- **S0001 and S0005, coders:** the shared test helper `HumanClone.push_file` raises `NothingToCommit` when a test pushes the text `main` already holds. This sent both stories to the human for the same question. The human chose to leave the helper as it is both times, so it is not mine to reopen. A tester writing new tests against the fixture's definition will meet it again.
- **Seen in this review:**
  - The guard hooks `Edit|Write` (`GUARDED_TOOLS`, `src/factory/adapters/claude_runtime.py:46`). A tool that names a path in another key (`NotebookEdit`'s `notebook_path`) is not judged during the run. Neither is a shell command. The undo puts both back afterwards, and the scope promised `Edit` and `Write`.
  - The guard judges real paths and the undo judges git's paths. A symbolic link the agent makes inside `src/` through a shell command is therefore allowed to stay. A write through it to a protected file shows up in git under the target's name and is reverted. This is consistent, and links pointing outside the checkout are v2's sandbox.

## 5 The documentation as a whole

Two findings, both in the opening status sentences. The guides' F0004 sections are current and agree with each other and with the code:

- project guide: "The claim service", "The write paths", "The guard command" and "The undo";
- operator guide: "`factory-guard` on the agent run's `PATH`" and "Claims, leases and the clock";
- the four decisions of 2026-10-14 (F0004).

I checked them against the demo above and found no contradiction. The two findings:

- **`README.md`.** "The built parts so far are …" names nothing of F0004: not the claim service, the lease, the write paths, the guard or the undo. "The one command so far checks a story before it starts: `uv run factory-check-story`" contradicts the operator guide's "The commands to run so far are `factory-check-story` (you run it) and `factory-guard` (the agent runtime runs it)". This list has now gone stale after three features in a row. F0003-S0010 recorded the human's decision of 2026-10-14 that the README *summarises* the built parts instead of listing them, but the README still lists them.
- **`docs/operator-guide.md`, opening paragraph.** "Parts are built: …" lists the wrappers, the stops, the pipeline definition and the agent definition reader. It does not list the claim with its lease or the write paths with the undo, although the guide has a section on claims and one on `factory-guard`.

The S0001 and S0002 documenters wrote "README … does not mention claims" and found the README current for their story. Read as a whole, it is stale. Draft S0006 repairs both places.

## 6 Decisions taken for the human

The 18 decisions in `FEATURE.md` stand as built. I checked each one against the code or the demo, and none was changed by a story. In short:

1. The "started" text and the commit subject.
2. A claim only on the work item's own branch, checked out, for a stage with a role. Bad input is a `ValueError` that writes nothing.
3. A re-claim replaces the claim and appends a second entry.
4. After a failed push the local commit stays for the next tick's restore.
5. Expired at age ≥ `lease_duration`. A negative age is never expired.
6. An own claim is own at any age, and instances need synchronised clocks.
7. Expiry uses the claim's stored lease, not the current definition.
8. Ten fixed protected paths. `docs/project-guide.md`, `.git/` and `.gitignore` are not protected.
9. A `..`, absolute or empty path is never writable, and the four refusal texts are fixed.
10. Only the placeholders `{work_item}` and `{feature}` are allowed.
11. The guard refuses with status 2 on stderr and judges real paths.
12. The guard fails open on an unreadable payload and closed on a bad settings file.
13. The undo clears everything directly in `in-progress` except the own work item, and the guard does not know this rule.
14. A deleted or broken work item is restored whole, and its section edits are lost.
15. The undo makes no commit.
16. `WritePathService.at` parses directly and does not go through `PipelineLoader`.
17. Uncommitted changes become part of the stage-start commit.
18. The lease comes from the caller's definition, and the write paths from the stage-start commit.

Two questions for the human to accept or revisit:

- **Decision 16** says "F0003's `FEATURE.md` is to say the same". It does not: `factory/features/F0003-stops-and-pipeline-definition/FEATURE.md` does not mention `WritePathService` or a read at another commit. `docs/decisions.md` and the project guide say it, so only the feature text is missing it. That file is yours (R15). Either add the sentence or accept that the decision log carries it.
- **The two answers on pull requests.** S0001 entry 5 and S0005 entry 5 both chose option (a): the test skips its push when the text is unchanged, and `HumanClone.push_file` stays as it is. The same question came up twice. If you would rather have the helper skip an empty commit (S0005's option (b)), that would be a test-support story. I have not drafted it, because you decided against it twice.

Decisions the stages took within the story texts, recorded here so they are seen:

- S0004's documenter told the operator that nothing probes `factory-guard` on `PATH` until F0010.
- S0005's tests fixed that nested files, other lifecycle folders and `in-progress` folders outside `factory/features/` follow the write paths. That is the Interface's "directly", read strictly.

## 7 The slow checks

None. Beyond `make check` the project offers no slow check: no `make mutants` (see section 3), no image scan and no SBOM.

## 8 Cost

The five stories cost 50 runs, 42.0 min and $11.65. Per story:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 | 11 | 9.6 | $2.72 |
| S0002 | 6 | 4.2 | $1.13 |
| S0003 | 10 | 7.4 | $2.21 |
| S0004 | 6 | 6.0 | $1.51 |
| S0005 | 17 | 14.8 | $4.08 |

S0005 stands out at 35 % of the dollars. Its log tells why:

- The `NothingToCommit` setup failure sent it to the human (entries 4 to 7).
- The reviewer then found the allowed side of the `in-progress` rule untested twice, in two rounds (entries 9 to 16). Each round cost a coder hand-off and a tester run with no code change.

S0001 is second for the same two reasons on a smaller scale: the same `NothingToCommit` question (entries 4 to 7), and one review round on two refactor findings. S0002 and S0004 went straight through. S0001 and S0005 together are $6.80 of the $11.65. Their extra runs went into two human round-trips over one test helper and into review rounds that only added tests, not into code.

## Proposed stories

- `drafts/F0004-S0006-documentation-after-claim-and-write-paths.md`: the README's status and command sentence and the operator guide's opening list leave out F0004 and contradict each other on the commands. The draft carries out the human's earlier decision to summarise the README's built parts instead of listing them. It is documentation only: the human may prefer to make the edit by hand.

## Log (append only)

1. acceptor: accepted with drafts; 1 draft proposed; make mutants n/a (no target, by decision in docs/decisions.md)
      1 Scope: none. All five scope items map to S0001–S0005 and the code they name. The Goal's done-condition holds. Nothing out of scope was built (no wiring of the services, no fail-closed guard).
      2 Feature demo: green. Two instances race for a stage and the push decides (`PushFailed rejected`, remote unchanged). own/held/expired show at 44:59 and 45:00 of a 45-minute lease. A work-tree rewrite to `["*"]` widens nothing. The real `factory-guard` refuses `docs/`, protected paths, `src/../Makefile` and paths outside the checkout. The undo reverts and deletes what got through, restores the state and keeps the section edit. A second undo is empty. Guard and undo agree on every path tried.
      3 Mutation score: no `make mutants` target (recorded decision). The reviewers' hand-mutation findings in S0003 and S0005 were closed with tests. Coverage is 99.68 %.
      4 Noticed: no story needed. Items: the redundant `_state_of` call; `refusal(".")`; ignored paths left for v2; the in-progress rule's allowed side missing from S0005's criteria but now in tests and docs; `HumanClone.push_file`'s `NothingToCommit` hit twice; the guard hooks `Edit|Write` only, with the undo as the backstop.
      5 Documentation: the README lists the built parts without F0004 and says "the one command so far", which contradicts the operator guide's two commands. It also still lists parts against the human's decision to summarise them. The operator guide's opening list leaves out the claim and the undo. The F0004 sections themselves are current. Draft S0006.
      6 Decisions: the 18 decisions in FEATURE.md stand as built. Two open items: decision 16 promises a sentence in F0003's FEATURE.md that is not there (the human's file), and the same `push_file` question was answered (a) twice.
      7 Slow checks: none (no mutants target, no image scan, no SBOM).
      8 Cost: 50 runs, 42.0 min, $11.65. S0005 stands out at $4.08 and 17 runs: one human round-trip and two test-only review rounds. S0001 is second ($2.72) for the same reasons on a smaller scale.
2. done (pull request merged); cost: 1 runs, 5.2 min, 28 turns, 90k tokens in (1343k more from cache), 21k out, $1.40
