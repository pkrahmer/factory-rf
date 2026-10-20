---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 335
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T04:40:33.436999Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T04:45:32.917644Z'
  stage: acceptance
  run: 80df6fd3301a41fbaa835869ee729db2
stories: [F0034-S0001, F0034-S0002]
outcome: null
---

# Acceptance of The reviewer may correct a stale story Description

## Recommendation

accepted with stories. The feature does what `feature.md` promised. Only the shipped reviewer carries the rule. A Description correction survives the factory's undo while edits to the journal and the state are dropped. The guard lets the reviewer write its story and nothing else, and ending with `docs` costs no round. `make check` is green and the feature smoke test passed. F0034-S0002 repaired the playbook passages that A0001 found. One documentation finding remains, and it is worth a small story but breaks no promise of this feature. The project guide's count "Six passages are v1.1's own text", which S0002 wrote, is still short by at least four passages that earlier features added to the agent texts.

## 1 Scope

None. The three Scope items are built by F0034-S0001 (`claude/agents/reviewer.md:70`, `tests/test_claude_agent_texts_description.py`, and the operator guide, decision log and playbook from its docs criterion). F0034-S0002 is outside the Scope list of `feature.md`. Its Stories list names only S0001, and S0002's `docs/project-guide/agents.md` is not named there either. But F0034-A0001 proposed S0002, and the human merged and started it, so it counts as the human's scope. Intake (S0002 entry 3) and the coder (entry 7) noted this, and `feature.md` is the human's to update. Out of scope holds: neither story touched `src/`, `factory/pipeline.yml`, another agent text or an archived story, and no paid call was made. As A0001 said, no real reviewer run has corrected a Description yet. The first stale Description after this merge will be its first use.

## 2 Feature smoke test

The walk-through follows a review with a stale Description end to end through the factory's real entry points. First it reads the reviewer the runtime gets (`FrontmatterAgentDefinitionReader` over `claude/`). Then it takes the archived F0034-S0001 as a story at `review`, round 0, and corrects one Description sentence the way the reviewer would, also tampering with the journal and the round. That edit goes through the factory's undo (`restore_state_and_journal`, which `factory.application.undo` applies after every stage) and the work item writer. Next it asks the write guard (`expand_write_paths` and `refusal` with the review role of `factory/pipeline.yml`) what the reviewer may write. It moves the story with `decide` for `docs` and for `doing`, and it counts the entry line in the four documents. The script ran from a self-removing `mktemp -d` folder as `uv run python "$d/smoke.py"` from the root of the checkout:

```python
agents = FrontmatterAgentDefinitionReader(root / "claude")
role = section_text(agents.read("reviewer").instructions, "Role") or ""
para = next((p for p in role.split("\n\n") if p.startswith("When the work item's `## Description`")), "")
# ... count of 'description corrected:' per agent ...
archived = reader.read(root / feature / "done/F0034-S0001-the-reviewer-corrects-a-stale-description-itself.md")
state = archived.state.model_copy(update={"stage": "review", "round": 0})
baseline = archived.model_copy(update={"state": state})
edited_body = baseline.body.replace(old, new).replace("1. 2026-10-20 human: created.", "1. tampered.")
edited = baseline.model_copy(update={"body": edited_body, "state": state.model_copy(update={"round": 5})})
kept = restore_state_and_journal(edited, baseline)
# ... kept Description, dropped journal and state, rest unchanged, writer round trip ...
paths = expand_write_paths([str(p) for p in review.write_paths], work_item_path=story, feature_path=feature)
guard = GuardSettings(root=root, write_paths=paths, protected_paths=list(PROTECTED_PATHS))
# ... refusal() for the story, src/, feature.md, docs/; decide(pipeline, state, "docs" / "doing") ...
```

Output:

```
reviewer Role holds the rule: True
  acceptance-reviewer: 0
  coder: 0
  documenter: 0
  intake: 0
  reviewer: 1
  smoke-tester: 0
  tester: 0
description correction kept after the undo: True
journal edit dropped: True | state edit dropped: True
rest of the body unchanged: True
writer round-trips it: True
  write F0034-S0001-the-reviewer-corrects-a-stale-description-itself.md: allowed
  write sections.py: src/factory/domain/sections.py is outside the write paths of this stage.
  write feature.md: factory/features/F0034-the-reviewer-may-correct-a-stale-story-description/feature.md is owned by the human; a change there is a question.
  write decisions.md: docs/decisions.md is outside the write paths of this stage.
  docs: stage docs, round 0, blocked None
  doing: stage doing, round 1, blocked None
  docs/operator-guide.md: 1
  docs/decisions.md: 1
  docs/operator-playbook.md: 2
  docs/project-guide/agents.md: 1
```

Green. The reviewer is told the rule, its correction of the Description survives the factory's undo while its edits to the journal and the state are dropped, it cannot reach the code, the feature or the documents, and `docs` moves the story on at round 0 where `doing` would cost round 1. The four documents name the entry line the operator reads at the approval.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- F0034-S0001: nothing open. A0001 already collected the noticed items, and F0034-S0002 fixed both documentation items.
- F0034-S0002, intake (entry 3) and coder (entry 7): the feature's Scope and Stories lists in `feature.md` do not name S0002 or `docs/project-guide/agents.md`. That is the human's file. It is listed here for the human to update or leave as it is, and no story is proposed for it.
- F0034-S0002, documenter (entry 11): the docs criterion's wording would have kept the count "Three passages" (it asked for the sentence to name the reviewer's passages "beside the three it lists"). The smoke test expected the count to be gone, so the documenter rewrote it to "Six". That followed the criterion, but it set a new closed count. Check 5 finds that count short.
- Both coders recorded `duplicates: 5 new, 33 known, 3 gone` from stories with no change under `src/`. These are the same four runtime similar-code pairs and `ManualWaiter` (`src/factory/adapters/clock.py:45`) that A0001 listed, all from earlier features against `security/duplicates-baseline.txt`, which is the human's. Listed again, with no story.
- Reviewers and smoke testers: no remarks beyond their findings, which were none.

## 5 Documentation as a whole

The reviewer's rule is now told consistently. `docs/operator-guide.md:804-808` ("Three things", with the paragraph on `description corrected:`), `docs/decisions.md:861-867`, and `docs/operator-playbook.md:48-50`, `:61`, `:127` and `:148` all agree with `claude/agents/reviewer.md:70` and with one another. Line 173 (item 17 of *What changed against the draft*) is a record of the draft and stays as it is. `README.md` needs nothing.

One finding. `docs/project-guide/agents.md:248` says "Six passages are v1.1's own text and not v1's", after "the sentences are not rewritten in other words". `:305` repeats "the six passages". `git log -- claude/agents/` after `830029c9` (F0010-S0017, which carried v1's texts in) shows at least four more passages of v1.1's own outside `## Lessons`:

- R14's write-guard sentences (`90afe2d7`, F0019-S0006).
- R15 (`df880a45`, F0022-S0002).
- The acceptance reviewer's comparison of the disk records in check 7 (`6c2ff0fb`, F0012-S0017).
- The acceptance reviewer's check 3 *Mutation testing*, "By sweep, not run here", and the words changed with it in check 7, the recommendation, the proposals paragraph and steps 1 and 3 (`6df05eea`, F0031-S0001).

The guide describes R14 (`:240`) and R15 (`:254`) but does not count them, and it does not mention the acceptance reviewer's check 3 or its disk comparison at all. These passages come from earlier features, but the count is this feature's text, from S0002. An agent that changes an agent text and trusts the count would take those sentences for v1's. Proposed: F0034-S0003. It names each passage with its story and drops the number that the next passage would make wrong.

## 6 Decisions taken for the human

From `feature.md`, carried out as written. Accept or revisit:

1. The Description is corrected only when the human's answers, the Interface or the criteria settle what it should say. The coder's or tester's own account is not enough.
2. A correction is not a finding: with no other finding the reviewer ends with `docs`. It costs no round and no question, and it shows in the entry as `description corrected: <what it said> -> <what it says now>`.
3. The reviewer changes only the stale sentences of the Description. Checklist item 5 keeps its words.
4. The paragraph's tests are in their own module, `tests/test_claude_agent_texts_description.py`, so `tests/test_claude_agent_texts_review_leave.py` stays unchanged.

Taken in the stories:

5. F0034-S0002 intake (entry 3) took S0002 as approved scope although `feature.md` does not list it, because the human merged A0001's proposal. It did not ask.
6. F0034-S0002 documenter (entry 11) followed the smoke test over the docs criterion's wording and replaced "Three passages" with "Six passages" (see check 5).

No human answered a question in either story. Earlier tests changed: none. S0001's reviewer (entry 9) found only the added file (status `A`), and S0002's diff (entry 9) changes no test file.

## 7 Slow checks

The project offers nothing beyond `make check` but `make documents` (a check of the docs stage, green in both stories' entry 11) and the `make duplicates` record (check 4). `make mutants` was not run (check 3). `make check` is green here (`check: green`, `test: green (40.6 s)`, coverage 99.14 %, 6094 tests). The slowest tests in `.reports/junit.xml` are the runtimes' time-limit tests, and none of them is from this feature. Two take 5.01 s: `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` and `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`. Two `test_opencode_sudo_time_limit` rows take 4.53 s and 4.52 s. The feature's eleven tests take 0.001 to 0.002 s each. Disk now is the same as at the previous record (`disk acceptance`, A0001's): `/work` has 0.5 GB used and 970.1 GB free, and `/state` and `/tmp` have 0.0 GB used. No growth.

## 8 Cost

Two stories: 12 runs, 6.2 min, 64 turns, 200976 tokens in (940397 more from cache), 17159 out, $1.77. F0034-S0001 took 6 runs, 3.7 min and $0.95. F0034-S0002 took 6 runs, 2.5 min and $0.82. Every stage of both stories ran once, on its first attempt, with no round and no stall. Neither story stands out. S0002 was a documents-only story, and its tester and coder each ran a full stage to build nothing (entries 5 and 7). That is the pipeline's fixed cost for a story with only the closing criteria, about two of its six runs. Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `F0034-S0003-the-project-guide-names-every-passage-of-v1-1-s-own-in-the-shipped-agents.md`: a documentation repair. The project guide's "Six passages are v1.1's own text" leaves out R14's write-guard sentences, R15, and the acceptance reviewer's check 3 and disk comparison. The story names each passage with its story, with no count that goes stale (check 5). `factory-check-story` says `ok`.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 story proposed
   1 Scope: none. S0001 built all three Scope items. S0002 is outside the Scope and Stories lists of `feature.md`, but it was A0001's proposal and the human merged it; updating `feature.md` is left to the human. Nothing listed as Out of scope was touched.
   2 Feature smoke test: green. Only the reviewer carries the rule (6 × 0, 1 × 1). A Description correction on a story at review survives `restore_state_and_journal`, while the journal and state edits are dropped. The guard allows the story and refuses `src/`, `feature.md` and `docs/`. `docs` moves the story at round 0, where `doing` costs round 1.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the `feature.md` lists omit S0002 (the human's file). S0002's documenter turned "Three passages" into "Six" because its smoke test asked for that (see 5). `duplicates: 5 new` again comes from earlier features (the runtime pairs and `ManualWaiter`); listed, no story.
   5 Documentation: the rule is told consistently in the operator guide, decisions and playbook. `docs/project-guide/agents.md:248,305` count "six" v1.1 passages and leave out R14's write-guard sentences (F0019-S0006), R15 (F0022-S0002), and the acceptance reviewer's disk comparison (F0012-S0017) and check 3 (F0031-S0001). Proposed: F0034-S0003.
   6 Decisions: the feature's decisions 1 to 4, plus two taken in S0002 (intake took S0002 as approved scope; the documenter followed the smoke test over the criterion's wording). No human answers. Earlier tests changed: none.
   7 Slow checks: nothing beyond `make check`, which is green (99.14 %, test 40.6 s, 6094 tests). The slowest tests are runtime time-limit tests at 5.01 s, none from this feature. Disk is unchanged from the previous record (0.5 GB used on `/work`).
   8 Cost: 12 runs, 6.2 min, $1.77 (S0001 $0.95, S0002 $0.82). Every stage ran on its first attempt. In S0002 the tester and the coder each ran a full stage that built nothing, the fixed cost of a documents-only story. 0 questions, 0.0 h waited.
