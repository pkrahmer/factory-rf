# The shakedown's findings

## Goal

v1.1's shakedown run (plan step 4) built the todo demo on 2026-10-18: eight stories and three acceptances on `pkrahmer/factory-demo-todo`, instance `shakedown` under Docker Desktop, image built from factory-rf `0f617cde`. Everything was accepted at its first approval, with no stall, in 82 runs for $17.88 (the night log, `docs/runs/2026-10-12-overnight/night-log.md`, the rows of 2026-10-18 from 07:45 on and the section "2026-10-18, the shakedown run (plan step 4): result"). The engine held. The run found three things that v1 fixes here before the handover (plan step 5), as the human chose on 2026-10-18. (1) The rule "a test another story wrote only with the human's leave" in the template's `CLAUDE.md` was held by the agents' reading alone: in F0002-S0003 they changed F0001's tests unasked, and neither the reviewer nor the acceptance said so. (2) The same rule was costly: a story whose test needs a helper that an earlier story's test module holds either copies it, which the reviewer counts as a finding, or asks. Three stories paid review rounds and questions for that, about $6 above three clean passes. (3) The board showed an acceptance at `approval` about 25 seconds before its pull request's description held the report. A fourth finding, the demo's own story texts, is the human's change to `demo/` (see *The human's changes*). This feature is for every project the factory sets up and for the human who decides at its approvals. When it is done, the template's `CLAUDE.md` gives a standing leave to move a shared test helper, the shipped tester and coder say who makes that move, the reviewer names every earlier test it sees changed with the leave for it, the acceptance gathers those lists, and a pull request carries its full description from the moment the board shows the approval. Done when every story below is merged and `make check` is green.

## Scope

- A standing leave to move a shared test helper (findings 1 and 2): the template's `CLAUDE.md` gets the leave in its *Tests* section and a changed *Not without asking* line; the shipped tester's lesson on earlier tests is rewritten and gains a second one, and the coder gets a lesson that hands a copied helper to the tester (S0001).
- The reviewer names every earlier test it sees changed (finding 1): a sixth checklist item of the shipped reviewer, done in every review, and one sentence in the acceptance reviewer's check 6 that gathers the reviewers' lists (S0002).
- An approval's description is written before its push (finding 3): the stage that moves a work item to an approval writes the pull request's description after the result commit and before its push, for stories and acceptances alike (S0003).

## Out of scope

- The demo's story texts (finding 4): the human's change to `demo/`, drafted in `planning/overnight/demo-fixes-F0016.md`. No story of this feature reads `demo/`.
- A check in code of earlier tests changed (FEATURE decision 5): the factory could list the files, but whether a test still checks the same thing is a reading, so the reviewer judges it.
- The prompt line `Mode: a test change the human approved; ...` (`src/factory/domain/prompts.py`), which stays as it is (decision 2).
- The intake agent, which stays as it is (decision 3).
- Moving the ready flag, the cost table post or the `handed_over` record out of the hand-over (decision 7).
- factory-rf's own `CLAUDE.md`, which is the human's (the human's change 2) and v1, which this feature does not change.
- The other items of the shakedown: the `StarletteDeprecationWarning` of the demo's pinned `httpx` (the human's dependency) and the stories the acceptances proposed in the demo's backlogs.

## Stories

The build order is S0001, S0002, S0003. S0002 starts only after S0001 is merged: both change `tests/test_claude_agent_texts.py`, and S0002's reviewer item names the standing leave that S0001 writes into the template (decision 10). S0003 is independent of both and changes other files; it may start before them if it is the only story moved to `ongoing/`.

- S0001 — A standing leave to move a shared test helper
- S0002 — The reviewer names every earlier test it sees changed, started only after S0001 is merged
- S0003 — An approval's description is written before its push

## The human's changes

None is needed before any story of this feature. Checked on 2026-10-18 against `factory/stages.yml`: the coder writes `src/*`, `image/*`, `template/*` and `claude/*`; the tester `tests/*`; the documenter `README.md` and `docs/*`; no stage writes `demo/*`, `CLAUDE.md`, `Makefile`, `pyproject.toml` or `security/*`, and no story here needs any of them. No dependency, no `Makefile` target, no `factory/stages.yml` change, no `security/*` entry and no `.secrets.baseline` entry.

1. **The demo's story texts (finding 4)**, any time, independent of F0016: the changes listed in `planning/overnight/demo-fixes-F0016.md` to the stories and `feature.md` files under `demo/todo-service/features/` and to `demo/todo-service/project/CLAUDE.md`. After them, `make test` must stay green: `tests/test_demos.py` runs the demo check over the shipped demo, so every changed story must still pass the story form (its two closing criteria last).
2. **factory-rf's own `CLAUDE.md`**, optional, at the handover (after F0016, decision 11): the standing leave for factory-rf itself, once v1.1 builds it with the agents S0001 changes. In `## Not without asking (end the stage with `question`)`, the first bullet's words

   ```
   change to a test you did not write,
   ```

   become

   ```
   change to a test you did not write beyond the standing leave under *Tests*,
   ```

   and `## Tests` gets as its last bullet, after the one that starts `- Test data and test helpers obey the code already built`, the template's bullet of S0001's Interface, word for word:

   ```
   - The standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier test module still holds as a copy of a shared one, may be moved to one shared place under `tests/` (a module at its root, or `tests/conftest.py` for a fixture), and the earlier tests that held it changed to use it from there, without asking, as long as every earlier test keeps its name and checks the same thing. The tester makes the move, never the coder, and its entry names each earlier test file it changed. Any other change to a test another story wrote still needs the human's leave.
   ```

   Not before F0016's stories are built: v1 builds them with its own skills, which know no standing leave, so the leave would reach v1's tester without the reviewer's item that watches it. No test reads factory-rf's own `CLAUDE.md`.

## Decisions taken for the human

Product decisions taken while writing the stories, for the human to review in one place. Each names where it was taken. Source of all: the drafting brief `planning/overnight/briefs/draft-F0016.md` (the session's proposals, chosen by the human on 2026-10-18; the details here are the drafting agent's, to confirm) and the night log's rows of 2026-10-18.

1. The standing leave covers one kind of change only: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier module still holds as a copy of a shared one, moved to one shared place under `tests/` (a module at its root, or `tests/conftest.py` for a fixture), with the earlier tests changed to use it, every earlier test keeping its name and checking the same thing. It is the demo run's decision 13 (the human's answer on demo #4) made a rule of the template. Any other change to another story's test still asks. (S0001)
   - Rejected: a question every time, as today. At the shakedown the duplicated-helper rule cost three stories a review round each and often a question ($8.85 for the three, about $6 above three clean passes), and the answer was the same each time.
   - Rejected: a leave for any refactoring of earlier tests. "Checks the same thing" can be judged for a moved helper; for a rewritten assertion it is the question the rule exists for.
   - Rejected: the leave in the shipped agents alone. Whether earlier tests may change is a project's rule, and `CLAUDE.md` is where a project says what needs asking; the agents say only who makes the move.
2. The tester makes the move, never the coder, as R9 says for every test change. In the tests stage it moves the helper when its new test needs it. When the reviewer finds a copy, the coder ends with `tests` and names the move; `doing` → `tests` is a rework without a round cap, so no question and no round is spent. The tester's prompt then carries the existing line `Mode: a test change the human approved; the coder's journal entry <n> names it.`, and the tester's new lesson says that this entry may name a move under the standing leave instead of an answer of the human's. (S0001)
   - Rejected: a new prompt line for this case. It changes `src/factory/domain/prompts.py`, the task composer and the two tests that pin the line (`tests/domain/test_prompts.py`, `tests/application/test_task.py`), for a mode whose step 0 already does the right thing once the lesson names it.
3. The intake agent is not changed. Its lesson "a story that changes a test another story wrote names that test and has the human's word" is about the changes a story plans; the standing leave covers moves that arise while the tests are written, which no story text can name in advance. (S0001)
4. Where the new texts go. The template's leave is a bullet of its *Tests* section, and the *Not without asking* line points to it, because a leave listed under "Not without asking" would read as its opposite. The tester's and the coder's rules are `## Lessons` bullets, v1.1's own part, which `LESSONS` already pins exactly. The reviewer's is a checklist item in its `## Role`, as the brief asks, so it is read with the other five; this departs from v1's text there, and the project guide says so (S0002's docs criterion). (S0001, S0002)
5. The reviewer's sixth item (S0002):
   - It is done in every review, whichever of groups 1 to 5 failed, because the list is what the human and the acceptance read.
   - It names the files by git's own status (`git diff --name-status main...HEAD`, any status but `A`): a test file `main` already holds was written by an earlier story or by the human, which needs no lookup of who.
   - It knows three leaves: the standing leave of `CLAUDE.md` (when a project's `CLAUDE.md` gives one), the human's leave (the story's text or a journal entry, by number), and none needed when the change only adds tests and leaves every test the file held as it was, as factory-rf's own stories have done ("new tests only").
   - The list follows the findings or `no findings` in the entry. The reviewer's entry sentence ("Your entry is the numbered findings, ..., or `no findings`.") is not changed: `tests/shipped_agents.py` and two tests pin it, and the list is an addition to the entry, not a second kind of entry.
   - Rejected: a check in code. The factory could list the changed test files, but whether a moved helper leaves each test checking the same thing is a reading.
6. The acceptance reviewer does not run the same check over the whole feature; its check 6 gathers the earlier tests the reviewers' entries name, with their leaves, and names one changed with no leave as a finding. The recommendation: the reviewer sees each story's diff once, and the acceptance already reads every journal for its checks 4 and 6, so the lists cost it nothing more; a second diff over the feature would repeat every reviewer's reading at every acceptance. At the shakedown, the acceptance did not mention F0002-S0003's changes because no entry listed them, which the reviewer's item now does. (S0002)
7. Finding 3, the fix: the stage that moves a work item to an approval writes the description after the result commit and before its push, from the document and the commits it pushes (`HEAD` since `origin/main`), the same text the hand-over writes. The hand-over stays as it is and writes it again on the next tick, then marks the pull request ready, posts the cost table and records `handed_over`. A failing write before the push is logged and not fatal: raised, it would lose the agent's unpushed result and cost a rerun of the stage, while the hand-over writes the description on the next tick anyway. (S0003)
   - The cause, as the code shows it: `StageFinisher.finish` pushes the move (from then on the remote, the board and `factory-watch` show `approval`) and writes the label; the description comes from the `hand_over` event, which the evaluation gives only on the next tick (`_signal_of_observation` in `factory.domain.evaluation`), after the scheduler's pause of 15 seconds (`FIRST_PAUSE`) and the next fetch. The pull request kept the description it was opened with: an acceptance's report head (its title and an empty journal), a story's own text.
   - Rejected: the whole hand-over in the finisher. Marking the pull request ready before the push would show a ready pull request for a stage whose push may fail; recording `handed_over` in the result commit would leave a failed ready flag or cost table post never retried, since the hand-over would no longer run.
   - Rejected: the description written after the push, in the same tick. It leaves a window, short but real, and a failing write would leave it open until the next tick.
   - Rejected: the board showing an approval only once it is handed over. It changes the board, not the pull request, which is what the human opens.
   - The cost of the fix: when the push after the description fails, the pull request, still a draft, shows the reports while the work item stays at its stage, until the stage runs again.
8. Stories have the same gap: `HandOverHandler` runs on the next tick as `AcceptanceHandOver` does, and for those seconds the story's pull request shows its text as opened, without the reports and the commits. It was less visible because that text is not empty. S0003's fix covers both. (S0003)
9. The human's leaves for the tests of earlier stories (taken by the session for the human, to confirm). Any other change to an earlier story's test is a question.
   - S0001: `tests/test_claude_files.py` (F0010-S0012; changed since by F0012-S0028 and F0012-S0029), in `TEMPLATE_RULES_LINES`, the *Not without asking* line changes and the standing-leave bullet is added after the time-limit bullet; `tests/test_claude_agent_texts.py` (F0010-S0017; changed since by F0012-S0011 and F0012-S0028), in `LESSONS`, the tester's bullet on earlier tests is replaced by the two new ones and the coder gains its new bullet. The tests that read these constants stay as they are.
   - S0002: `tests/test_claude_agent_texts.py`, `ROLE_AND_STAGE_ANCHORS` gains two anchors for `reviewer` and one for `acceptance-reviewer`, and the module gains one new test, `test_the_reviewer_no_longer_stops_before_the_earlier_tests`. No existing test function changes.
   - S0003: `tests/test_stop_table.py` (F0011-S0004), in `test_hand_over_that_fails_every_time_is_reported_once_after_the_error_cap`, the line `world.hosting.fail_next("set_description", times=3)` moves to right after the first `run_ticks(world)`, so that its three failures still reach the hand-over and not the finisher's new write; `tests/application/test_stage_run_acceptance.py` (F0009-S0009) gains one new test that uses the module's fixtures, and no existing test, fixture or constant there changes.
10. Three stories, one per item of the brief. S0001 and S0002 are text-only stories with tests; they stay apart because the reviewer's item is a rule of its own with its own anchors and docs, and S0002 starts after S0001 (both change `tests/test_claude_agent_texts.py`, and S0002 names S0001's leave). (All stories)
11. factory-rf's own `CLAUDE.md` is not changed by this feature: it is the human's, outside every write path. The leave there is the human's change 2, at the handover, when v1.1 starts building factory-rf with the agents of S0001 and S0002. (Feature)
12. Finding 4 is the human's change to `demo/` (the brief), drafted in `planning/overnight/demo-fixes-F0016.md`: for each demo story, the criteria that give both sides of every rule its Interface states a criterion, the decisions to add to the demo's `feature.md` files, and the demo `CLAUDE.md` lines matching S0001. (Feature)
