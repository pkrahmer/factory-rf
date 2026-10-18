---
stage: done
pr: 213
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0016-S0001, F0016-S0002, F0016-S0003]
outcome: accepted
---
# Acceptance of The shakedown's findings

## Verdict

**accepted with drafts.** All three promises of `FEATURE.md` are built and work together. In one walk-through on the real tick (a real git remote, the shipped agent files installed), a reviewer's finding of a copied helper goes to the tester through `doing` → `tests` without spending a round. The tester's prompt carries the approved-change mode line, and the reviewer has its *Earlier tests* item. The pull request already holds its full description, with the earlier-tests list, on the first tick that shows `approval`, while it is still a draft. `make check` is green, and the one survivor in the feature's new code is near-equivalent. The one finding worth a story is a documentation repair: two of S0002's sentences in the project guide point the wrong way, and an older sentence misstates what `make mutants` lists. Apart from the stories, the human should know that `make mutants` never ends before its time limit (section 3).

## 1 Scope

None. Each scope item has its story, and each story stays inside the scope:
- **Standing leave (findings 1 and 2) → S0001.** `template/CLAUDE.md` has the new *Not without asking* line ("... beyond the standing leave under *Tests*, ...") and the leave as the last bullet of `## Tests`. `claude/agents/tester.md` has its two lessons in place of the old one, before the time-limit lesson. `claude/agents/coder.md` ends with the lesson that sends a copied helper to the tester with `tests`.
- **Reviewer names earlier tests (finding 1) → S0002.** `claude/agents/reviewer.md:51` has the new sentence before the checklist, and `:58` has item 6, *Earlier tests*. `claude/agents/acceptance-reviewer.md`'s check 6 gathers the reviewers' lists.
- **Description before the push (finding 3) → S0003.** `StageFinisher._commit_and_push` (`src/factory/application/stage.py`, commit `5adbe416`) calls `_describe` between `git.commit` and `git.push` when the move's stage is an approval. `_describe` logs a `HostingServiceError` and does not raise it.

The goal's chain only works if the coder's `tests` hand-off really reaches the tester as an approved change. The code confirms it does. `doing: {next: [review, tests]}` is in `template/factory/pipeline.yml`. `TaskComposer._test_change_entry` (`src/factory/application/task.py:148`) gives the tester the `Mode:` line whenever the last `result` record is the coder's. The demo shows the round unchanged across the hand-off. Out of scope was respected: `src/factory/domain/prompts.py` and the intake agent are unchanged, and nothing under `demo/` was touched (`git diff --name-status` of merges #210, #211 and #212).

## 2 Feature demo

The feature's purpose, end to end, in one story. Its reviewer finds a test helper copied from an earlier module. The coder hands the move to the tester. The tester makes it under the standing leave, and the reviewer then lists the changed earlier test with its leave. When the smoke test moves the story to `approval`, the pull request must already hold the full description. The script runs against the proof world of `tests/proof_support.py`. That world is the real `Tick` with every real adapter except the fake hosting service and the fake agent runtime, and it uses a real bare remote. The shipped `claude/agents/*.md` files are installed as the agents, and the template's `CLAUDE.md` is pushed to the project's `main`. The agents' results are scripted; their instructions and prompts are the factory's.

Command, from the repository root (the script lives in a scratch directory outside the repository):

```bash
PYTHONPATH=tests uv run python /tmp/f0016-demo/feature_demo.py
```

Output:

```text
template CLAUDE.md, Not without asking, says: True
template CLAUDE.md, Tests, ends with the leave: - The standing leave to move a shared test helper: a helper,...
1. at review
2. reviewer found a copy -> at doing round 1
3. coder ended with tests -> at tests round 1
4. tester prompt mode line: ["Mode: a test change the human approved; the coder's journal entry 11 names it."]
   tester's lesson present: True
   -> at doing round 1
5. reviewer agent has item 6: True -> at docs
6. first tick at approval: stage approval handed_over None draft True
   description is the full hand-over text: True
   it lists the earlier tests: True
   it holds the smoke report: True
7. next tick: handed_over approval draft False description unchanged: True
acceptance-reviewer check 6 gathers the lists: True
```

Green. Step 3 shows that `doing` → `tests` spends no round (round 1 before and after), as FEATURE decision 2 says. Step 6 is finding 3's fix seen from the human's side. On the first tick at which the remote shows `approval`, before any hand-over, the description equals `hand_over_description` of the pushed document and commits, and its *Review* section holds the reviewer's earlier-tests list.

<details><summary>The script</summary>

```python
"""F0016 feature demo: a story whose reviewer finds a copied test helper, end to end."""

import tempfile
from pathlib import Path

from factory.domain.hand_over import hand_over_description
from factory.domain.identifiers import branch_name
from git_support import write_agent
from proof_support import (
    PASSING_TEST,
    build_world,
    completed,
    drive_to,
    head_state,
    pull_request_of,
    work_item_file,
)

REPO = Path.cwd()
REVIEW = (
    "No findings.\n"
    "Earlier tests:\n"
    "- `tests/test_example.py` (M): the standing leave to move a shared test helper"
)
SMOKE = "The smoke test passed."

root = Path(tempfile.mkdtemp())
world = build_world(root)
for agent in (REPO / "claude" / "agents").glob("*.md"):
    write_agent(root / "agent-home", agent.stem, agent.read_text(encoding="utf-8"))
world.human.push_file("main", "CLAUDE.md", (REPO / "template" / "CLAUDE.md").read_text())
claude_md = (REPO / "template" / "CLAUDE.md").read_text()
print("template CLAUDE.md, Not without asking, says:",
      "beyond the standing leave under *Tests*" in claude_md)
print("template CLAUDE.md, Tests, ends with the leave:",
      claude_md.split("## Tests")[1].split("\n## ")[0].strip().splitlines()[-1][:60] + "...")

from proof_support import start_story  # noqa: E402

item = start_story(world, "Uses a shared helper")
drive_to(world, item, "review")
print("1. at", head_state(world, item).stage)

# The reviewer finds a copied helper: rework.
world.agent_runtime.queue(completed("doing", "1. `tests/test_two.py` copies `make_item` from `tests/test_one.py`."))
world.tick.run()
print("2. reviewer found a copy -> at", head_state(world, item).stage, "round", head_state(world, item).round)

# The coder hands the move to the tester (doing -> tests, no round spent).
world.agent_runtime.queue(completed("tests", "Move `make_item` to `tests/helpers.py` under the standing leave; earlier file `tests/test_one.py`."))
world.tick.run()
state = head_state(world, item)
print("3. coder ended with tests -> at", state.stage, "round", state.round)

world.agent_runtime.queue(completed("doing", "Moved `make_item`; changed earlier test file `tests/test_one.py` under the standing leave.",
                                    writes={"tests/test_example.py": PASSING_TEST + "\n"}))
world.tick.run()
tester = world.agent_runtime.requests()[-1]
print("4. tester prompt mode line:", [l for l in tester.prompt.splitlines() if l.startswith("Mode:")])
print("   tester's lesson present:", "a move of a shared test helper under that standing leave" in tester.agent.instructions)
print("   -> at", head_state(world, item).stage, "round", head_state(world, item).round)

world.agent_runtime.queue(completed("review", "Done."))
world.tick.run()
world.agent_runtime.queue(completed("docs", REVIEW))
world.tick.run()
reviewer = world.agent_runtime.requests()[-1]
print("5. reviewer agent has item 6:", "6. **Earlier tests**" in reviewer.agent.instructions, "-> at", head_state(world, item).stage)

world.agent_runtime.queue(completed("smoke-test", "Docs written."))
world.tick.run()
world.agent_runtime.queue(completed("approval", SMOKE))
world.tick.run()
number = pull_request_of(world, item).number
state = head_state(world, item)
git = world.boundaries.git
git.fetch()
branch = f"origin/{branch_name(item)}"
document = world.boundaries.work_item_reader.parse(git.show_file(branch, work_item_file(world, item)) or "")
expected = hand_over_description(document, git.log(branch, since="origin/main"))
description = world.hosting.description(number)
print("6. first tick at approval: stage", state.stage, "handed_over", state.handed_over,
      "draft", pull_request_of(world, item).draft)
print("   description is the full hand-over text:", description == expected)
print("   it lists the earlier tests:", "Earlier tests:\n- `tests/test_example.py` (M)" in description)
print("   it holds the smoke report:", SMOKE in description)
world.tick.run()
state = head_state(world, item)
print("7. next tick: handed_over", state.handed_over, "draft", pull_request_of(world, item).draft,
      "description unchanged:", world.hosting.description(number) == description)
print("acceptance-reviewer check 6 gathers the lists:",
      "Add the earlier tests the reviewers' entries name as changed" in (REPO / "claude/agents/acceptance-reviewer.md").read_text())
```

</details>

What the demo cannot show: whether a real Claude agent follows the new texts. The texts reach the agents (steps 4 and 5). Following them is the next shakedown's question, and this repository's own stories already did it: S0002's reviewer, which runs on v1's skills, ended its entry with an *Earlier tests* list.

## 3 Mutation score

`make check` was green when I started (`check: green`; coverage 99.47 %).

`make mutants FEATURE=F0016` selects one module, `src/factory/application/stage.py`, the only module under `src/factory` that F0016's story commits changed (`5adbe416`). Plain `make mutants` would have taken the id from the branch name. My first call passed the folder name (`FEATURE=F0016-the-shakedown-findings`) and got `mutants: no module under src/factory changed by F0016-the-shakedown-findings`, exit 0. That was my mistake: the project guide says `<id>`.

**Score for `stage.py`: 667 killed, 38 survived, 0 timeouts, out of 705 (94.6 %).** It took three steps to get there:
- The first `make mutants FEATURE=F0016` and a second one each ended with `mutants: stopped after 540 s; the results below are partial, run it again to go on`. At that point `stage.py` stood at 502 killed, 30 survived and 173 not checked. The second run's counter stayed at `5745/12267` for its whole mutation phase: it made no progress at all.
- Run by name, the 169 mutants still unchecked finished in 237 s: `timeout 540 uv run mutmut run <the 169 ids>`, `real 3m56.953s`.
- A third `make mutants FEATURE=F0016`, with no unchecked mutant of `stage.py` left, again ran its full 540 s at a frozen counter (`5918/12267 🎉 5634 … 🙁 280`) and printed `stopped after 540 s`.

So the target never ends inside its limit, even when nothing is left to do, and "run it again to go on" does not hold for this module. F0014's acceptance also saw a 540-s run. This is the human's `Makefile` (no stage writes it), so it is no draft: an observation for the human.

The target's list holds more than this feature's survivors. It also shows the survivors that `mutants/` keeps from earlier features' runs (`settings`, `git_cli`, `claude_runtime`, `work_item_markdown`, `cost_records_jsonl`, ...), whatever module `FEATURE` selects. `docs/project-guide.md` says otherwise (section 5 and the draft).

The survivors of `stage.py`, by group (read with `uv run mutmut show`):
- **The feature's new code: one survivor, near-equivalent.** Every mutant of `_describe` (10 of 10) and of the `describe` path in `finish` and `_commit_and_push` is killed. Among them are `finish__mutmut_74`/`_79` (`approval = None`, `describe=None`), which the S0003 tests catch. The one survivor is `_description__mutmut_3`, `acceptance_description(moved, None)`. `last_record(speaker=None, kind="result")` matches any speaker, and in an acceptance only the acceptance reviewer writes a `result`, so the text is the same. Re-running it in `mutants/` against `test_stage_run_acceptance.py`, `test_acceptance_hand_over.py`, `test_approval_description.py` and `test_stage_finish.py` passes every test. No draft.
- **`PushFailed`'s arguments** (`_commit_and_push__mutmut_18`/`_19`: `PushFailed(None, outcome)`, `PushFailed(started.branch, None)`). The `raise` line is older than F0016. No test reads the branch or the outcome of the error the result push raises. It is small and only reaches the log, so no draft.
- **No-state and no-role messages** (`_no_state` 1–3, `_role_of__mutmut_3`, `_launchable_stage` 1–3 and 5, `finish` 12 and 90, `_moved__mutmut_3`, `StageRunner.run__mutmut_8`): the text of a `ValueError` for a state that the readers already refuse. These are the same group as in earlier acceptances.
- **Stall-context pass-throughs** (`AfterAgent._stall` 1, 10 and 18; `_stall_red` 20, 22 and 30; `StageRunner.run` 16, 22 and 23; `StageLauncher.__init__` 12; `StageFinisher.__init__` 4 and 6): fields of a report or a constructor that the tests do not read back. Same group as before.
- **`_early_stall` 6–9 and 12, `process` 45 and 55, `_first_denial__mutmut_2`.** F0014's acceptance showed that mutmut's test map for `_early_stall` is stale and that 6, 7, 9 and 12 are killed when run against the right tests. `_early_stall__mutmut_8` (the left-branch stall's empty detail) is the one F0014 left without a draft.
- **`_masked__mutmut_8` and `_new_findings__mutmut_11`** (the story-form check's masking and counting): older than F0016 (F0014). The `-= 2` case needs three equal findings before and after to show.

No group points to a missing criterion of this feature. No draft.

## 4 What the stories noticed

- **S0001**: nothing noticed by the coder, the reviewer or the documenter ("nothing stale that is unrelated to this story").
- **S0002**: the coder noticed only that the docs criterion was the documenter's. The documenter saw nothing stale. The reviewer had no remarks and ended its entry with an *Earlier tests* list. That is item 6 in practice, in a reviewer that runs on v1's skills, which do not have the item.
- **S0003**: the coder noticed that the description text is now built in two places, the finisher and the two hand-over handlers, from the same domain functions. Only the `git.log` ref differs (`HEAD` before the push, `origin/<branch>` after it). I read both. Each is one call, `hand_over_description(document, commits)` or `acceptance_description(document, role)`, and `test_a_work_item_at_its_approval_shows_the_full_description_before_its_hand_over` pins that the two texts are equal. It is not a second copy of a helper, so no draft. The documenter saw nothing stale.

## 5 The documentation as a whole

I read `README.md`, the operator guide's *What a stage run shows* and *The hand-over at the approval* (with its acceptance part), the project guide's *The shipped agents, settings and template*, *`StageFinisher.finish`*, *The hand-over at the approval*, *Mutation testing* and *Replaced from v1*, and the three new decision-log entries. The three stories' texts agree with each other and with the code, and `make documents` prints `documents ok`. Three passages say something untrue (draft S0004):
- `docs/project-guide.md:1337` (S0002) names the three passages that are v1.1's own text and then says "(described below):". They are described above it, in the `## Role` bullet at `:1333`. The colon introduces nothing: the next line is the parenthesis about the table of renamed words.
- `docs/project-guide.md:1740`, the opening of `## Replaced from v1`, says again that "the sentences are not rewritten in other words", without the exception that `:1337` now names. A reader who starts there takes the reviewer's item 6 for v1's text.
- `docs/project-guide.md:1734` (older, F0012) says that "the target lists only the mutants it checked". It lists every survivor and timeout that `mutants/` holds, including earlier features' modules (section 3).

A smaller point, left as it is: in the operator guide's *The hand-over at the approval*, step 1, "Replaces the pull request description. What you or the factory wrote there before is gone.", is still true, because the hand-over writes again. Read after the new paragraph above it, the reader knows the first write was the stage's.

## 6 Decisions taken for the human

FEATURE's decisions, all built as written. Confirm or revisit:
1. The standing leave covers only a move of a shared helper, constant or fixture to one shared place under `tests/`, with every earlier test keeping its name and what it checks; anything else still asks (S0001).
2. The tester alone makes the move. The coder hands a reviewer's copy finding over with `tests`, which spends no round (demo step 3), and the tester's prompt reuses the existing `Mode: a test change the human approved` line (S0001).
3. The intake agent is unchanged (S0001).
4. The leave is a *Tests* bullet in the template's `CLAUDE.md`, and the tester's and coder's rules are `## Lessons` bullets. The reviewer's rule is a checklist item in `## Role`, a departure from v1's text that the project guide names (S0001, S0002).
5. The reviewer's item 6 is done in every review, works from `git diff --name-status main...HEAD`, knows three leaves and follows the findings. The entry sentence is unchanged, and there is no check in code (S0002).
6. The acceptance reviewer gathers the reviewers' lists in its check 6 and does not diff the whole feature (S0002).
7. The description is written after the result commit and before the push, and a failing write is logged, not fatal. The cost: if that push fails, a draft pull request shows reports for a stage the remote does not show yet (S0003).
8. The fix covers stories as well as acceptances (S0003).
9. The leaves for earlier stories' tests (S0001 to S0003).
10. Three stories, S0002 after S0001 (all).
11. factory-rf's own `CLAUDE.md` stays unchanged by this feature (feature).
12. Finding 4, the demo's story texts, is the human's change to `demo/` (feature).

No story asked a question; the logs record no answers and no defaults beyond the coders' own choices. S0003's coder put the write inside `_commit_and_push` behind a `describe` keyword argument. The Interface left that split to the coder.

The earlier tests the stories changed, with the leave for each. I checked each against `git diff --name-status` of its merge, and none has no leave:
- `tests/test_claude_files.py` (M, S0001): `TEMPLATE_RULES_LINES`, by FEATURE decision 9.
- `tests/test_claude_agent_texts.py` (M, S0001 and S0002): `LESSONS`, then `ROLE_AND_STAGE_ANCHORS` and one new test, by FEATURE decision 9.
- `tests/test_stop_table.py` (M, S0003): one line moved (`fail_next("set_description", times=3)`), by FEATURE decision 9.
- `tests/application/test_stage_run_acceptance.py` (M, S0003): one new test and its import only, by FEATURE decision 9.

Still open, and the human's: **change 1** (the demo's story texts and `demo/todo-service/project/CLAUDE.md`, drafted in `planning/overnight/demo-fixes-F0016.md`) is not made yet. `demo/` is unchanged since F0015, and the demo project's `CLAUDE.md` does not give the standing leave yet, so a second shakedown run before change 1 would not test it. **Change 2** (factory-rf's own `CLAUDE.md`) is due at the handover, as planned.

## 7 Slow checks

Nothing beyond `make check` and `make mutants` exists: no image scan, no SBOM. The other targets are records and gates of other stages, and both are clean: `make documents` → `documents ok`, `make duplicates` → `duplicates: 0 new, 39 known, 0 gone`. From `.reports/junit.xml` of my `make check`: 4,713 tests, 508 s of test time in all. The slowest are older than F0016 (`test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` 5.0 s, two fault-path tests and `test_an_answer_at_the_round_cap_starts_the_count_of_rounds_over` about 3.6 s each). The new `tests/test_approval_description.py` adds six tests of 1.5 to 2.5 s each, about 12 s of the 508.

## 8 Cost

18 runs, 13.0 minutes, $3.25 for the three stories:
- S0001: 6 runs, 3.9 min, $1.15.
- S0002: 6 runs, 3.5 min, $0.82.
- S0003: 6 runs, 5.6 min, $1.28.

Each story passed every stage at its first run: six runs, one per stage, no rework, no question, no stall. None stands out. S0003 cost most because it is the only story with code and a world-driven test module. The whole feature cost less than the copied-helper rule alone cost the shakedown (about $6 above three clean passes, finding 2).

## Proposed stories

- `drafts/F0016-S0004-the-project-guide-points-to-its-own-passages.md`: a documentation repair of `docs/project-guide.md`. S0002's sentence on v1.1's own passages points below instead of above, `## Replaced from v1` repeats the "not rewritten" rule without its exception, and *Mutation testing* says the target lists only the mutants it checked, when it also lists earlier features' survivors.

## Log (append only)

1. acceptor: accepted with drafts; 1 drafts proposed; make mutants 667/705
   1. Scope: none. S0001 covers the standing leave (template `CLAUDE.md`, tester and coder lessons), S0002 the reviewer's item 6 and the acceptance reviewer's check 6, S0003 the finisher's description write before the push (`5adbe416`). The coder's `tests` hand-off reaches the tester as an approved change (`TaskComposer._test_change_entry`). Nothing out of scope was touched.
   2. Feature demo: green. One story ran on the proof world's real tick with the shipped agent files installed. The reviewer found a copied helper; the coder handed it on with `doing` → `tests` (round unchanged at 1); the tester's prompt carried the `Mode:` line; the reviewer had item 6. On the first tick at `approval`, before the hand-over, the draft pull request already held the full `hand_over_description` with the earlier-tests list; the next tick handed it over and left the description unchanged.
   3. Mutation score: `stage.py` 667 killed, 38 survived of 705 (94.6 %). The one survivor in new code, `_description__mutmut_3`, is near-equivalent. The others belong to older groups (no-state messages, stall-context pass-throughs, `PushFailed` arguments, `_early_stall`'s stale test map). For the human: `make mutants` never ends inside its 540 s. It froze its counter for the whole run twice, including once with nothing left to check, while the 169 mutants run by name finished in 237 s.
   4. Noticed: only S0003's coder noticed something, that the description is built in two places. Each place is one call to the same domain function, and a test pins that the texts are equal, so no draft.
   5. Documentation: three passages of `docs/project-guide.md` are untrue. `:1337` says "described below" for passages described above. `:1740` repeats "not rewritten" without the exception. `:1734` says `make mutants` lists only the mutants it checked, but it also lists earlier features' survivors kept in `mutants/`. Draft S0004 repairs them.
   6. Decisions: FEATURE decisions 1–12 were built as written. No questions were asked. Every earlier test changed (`test_claude_files.py`, `test_claude_agent_texts.py`, `test_stop_table.py`, `test_stage_run_acceptance.py`) was within FEATURE decision 9. Open and the human's: change 1 (`demo/`, including the demo project's `CLAUDE.md` leave) is not made yet; change 2 is due at the handover.
   7. Slow checks: none beyond `make check` and `make mutants`. `make documents` → `documents ok`; `make duplicates` → `0 new, 39 known, 0 gone`. The new test module adds about 12 s of the suite's 508 s.
   8. Cost: 18 runs, 13.0 min, $3.25. Each story took six runs, one per stage, with no rework; S0003 cost most ($1.28) as the only code story.
   The demo's scratch directories under `/tmp` (`/tmp/f0016-demo`, the worlds' `tmp*` directories) are left behind: the command to remove them was denied.
2. done (pull request merged); cost: 1 runs, 46.4 min, 71 turns, 143k tokens in (5974k more from cache), 40k out, $3.14
