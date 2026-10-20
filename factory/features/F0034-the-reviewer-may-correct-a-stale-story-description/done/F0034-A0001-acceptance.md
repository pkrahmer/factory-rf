---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 329
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T04:04:01.821310Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T04:07:53.541844Z'
  stage: acceptance
  run: b365b1900fb14a7f92342173a02dc934
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-20T04:09:11.857798Z'
  stage: done
stories: [F0034-S0001]
outcome: accepted
---

# Acceptance of The reviewer may correct a stale story Description

## Recommendation

accepted with stories. The feature does what `feature.md` promised. The shipped reviewer, read through the factory's own agent reader, carries the rule, only the reviewer carries it, checklist item 5 is unchanged, and the reviewer's write guard lets it write its own work item and nothing under `src/`. `make check` is green and the feature smoke test passed. One finding is worth a story and none is a broken promise. Three passages of `docs/operator-playbook.md` still say the edit is "a story to draft", and `docs/project-guide/agents.md` still counts three passages of v1.1's own, although the reviewer now holds three more.

## 1 Scope

None. The three Scope items are built by F0034-S0001: the paragraph in `claude/agents/reviewer.md:70` (*Role*, after the added-criterion paragraph, before `## Stage`), the new `tests/test_claude_agent_texts_description.py` (criteria 1 to 4), and the operator guide, decision log and playbook from its docs criterion. The merge `2499748a` changes exactly those five files (`git diff --stat 2499748a^1 2499748a -- . ':!factory'`: 64 insertions, 2 deletions). Everything listed as Out of scope stays untouched: nothing under `src/`, no other agent text (the count of `description corrected:` is 0 in the six others), no `factory/pipeline.yml` (the reviewer's `write_paths` were already `["{work_item}"]`), no archived story, no paid call. The Goal ("the human's answer or a criterion that settles the meaning reaches the Description in the review stage, with no send-back and no question") is reached as far as the instructions can promise it. No reviewer run has corrected a real Description yet. That would take a paid run, which the feature rules out, so the first story with a stale Description is the first real use.

## 2 Feature smoke test

The walk-through follows the path the factory takes. It reads the shipped reviewer as the runtime gets it, through `FrontmatterAgentDefinitionReader` (`src/factory/adapters/agent_files.py`) over `claude/`. It checks each clause of the rule and that only the reviewer has it. Then it loads `factory/pipeline.yml` through `RuamelPipelineDefinitionReader`, expands the review role's write paths for a story, and asks the guard's `refusal` whether the reviewer may write that story, `src/` and a `feature.md`. The script was in a self-removing `mktemp -d` folder and run from the root of the checkout with `uv run python "$d/smoke.py"`:

```python
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.agent_runs import GuardSettings
from factory.domain.sections import section_text
from factory.domain.write_paths import PROTECTED_PATHS, expand_write_paths, refusal

root = Path.cwd()
agents = FrontmatterAgentDefinitionReader(root / "claude")
role = section_text(agents.read("reviewer").instructions, "Role") or ""
para = next(p for p in role.split("\n\n") if p.startswith("When the work item's `## Description`"))
# ... five clauses checked in `para`, item 5 counted in `role`, `description corrected:` counted per agent ...
pipeline = RuamelPipelineDefinitionReader().parse((root / "factory/pipeline.yml").read_text())
story = "factory/features/F9999-x/in-progress/F9999-S0001-x.md"
paths = expand_write_paths([str(p) for p in pipeline.role_of("review").write_paths],
                           work_item_path=story, feature_path="factory/features/F9999-x")
guard = GuardSettings(root=root, write_paths=paths, protected_paths=list(PROTECTED_PATHS))
# ... refusal(story / src / feature.md, guard) printed ...
```

Output:

```
reviewer Role holds the rule: True
  clause 'rewrite the stale sentences of the Description you': True
  clause 'change nothing else in the work item': True
  clause 'description corrected: <what it said> -> <what it ': True
  clause 'A correction is not a finding: with no other findi': True
  clause 'stays a finding, or a question when no stage can f': True
item 5 kept: True
  acceptance-reviewer: 0
  coder: 0
  documenter: 0
  intake: 0
  reviewer: 1
  smoke-tester: 0
  tester: 0
review stage next: ['docs', 'doing']
reviewer may write its story: None
reviewer may write src: src/factory/x.py is outside the write paths of this stage.
reviewer may write feature.md: factory/features/F9999-x/feature.md is owned by the human; a change there is a question.
```

Green. The reviewer gets the rule, may write its story's Description, may end with `docs` (a next stage of `review`), and cannot reach the code or the feature.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- Coder (entry 7): "noticed but not touched" names only the docs criterion, which belongs to the documenter. Nothing to own.
- Reviewer (entry 9) and smoke tester (entry 13): no remarks beyond their findings, which were none.
- Documenter (entry 11): "Stale text noticed and not touched: none." It cross-read `README.md` and `docs/project-guide/` and judged them current, as the docs criterion said ("neither describes the reviewer's checklist"). That judgement missed `docs/project-guide/agents.md:244-248`, which does describe the checklist's sixth item and counts "Three passages" of v1.1's own text. It also missed the playbook's neighbouring passages (check 5). Both go into F0034-S0002.
- One record nobody commented on: the coder's `duplicates: 5 new, 33 known, 3 gone`, from a story that changes nothing under `src/`. A rerun here gives the same: four similar-code pairs between `claude_runtime` and `opencode_runtime` (`call_refusal`, `cleanup_launch`, `version_printed`, the `confine_executable` branch) and the dead-code finding `ManualWaiter` in `src/factory/adapters/clock.py:45`. Earlier features left these against `security/duplicates-baseline.txt`, which is the human's. This feature does not own them and proposes no story for them. They are listed for the human.

## 5 Documentation as a whole

`docs/operator-guide.md:806-808` (*The reviewer's notes and added criteria*, now "Three things") and `docs/decisions.md:861-867` agree with each other and with `claude/agents/reviewer.md:70`. Two places contradict the shipped reviewer:

- `docs/operator-playbook.md`. Line 50 says "Until a story gives the reviewer that edit, the correction goes into your answer". Line 127 says "the reviewer is to rewrite a stale Description (a story to draft)". Line 148 gives the state "a small story to draft" for what F0034 built. Line 61, two bullets further on, already tells the operator to read `description corrected:` lines at the approval. So the same section both says the edit exists and says it does not. Following line 50 does no harm, because an answer that settles the meaning is just what lets the reviewer correct the text, so this does not mislead badly. But the playbook now contradicts itself. Line 173 (item 17 of *What changed against the draft*) records the draft and stays as it is.
- `docs/project-guide/agents.md:248` and `:305` count "Three passages" / "the three passages" of v1.1's own text. The reviewer's *Role* now also holds the `Notes:` paragraph and the added-criterion paragraph (both `4c115657`, F0021-S0005) and the Description paragraph (`28c5331c`, F0034-S0001). The count was already stale after F0021, and this feature adds to it.

`README.md` needs nothing from this feature. No example in the documents runs code this feature changed. Proposed: F0034-S0002.

## 6 Decisions taken for the human

From `feature.md`, carried out as written. Accept or revisit:

1. The Description is corrected only when the human's answers, the Interface or the criteria settle what it should say. The coder's or tester's own account is not enough.
2. A correction is not a finding: with no other finding the reviewer ends with `docs`. It costs no round and no question, and it shows as `description corrected: <what it said> -> <what it says now>` in the entry.
3. The reviewer changes only the stale sentences of the Description. Checklist item 5 keeps its words.
4. The paragraph's tests are in their own module, `tests/test_claude_agent_texts_description.py`, so `tests/test_claude_agent_texts_review_leave.py` stays unchanged.

The story's journal holds no human answer and no default taken by an agent. Earlier tests changed: none. The reviewer's item 6 (entry 9) finds only the added file (status `A`).

## 7 Slow checks

The project has nothing beyond `make check` but `make documents` (a check of the docs stage, green in entry 11) and the `make duplicates` record (check 4). `make mutants` was not run (check 3). `make check` is green here (`check: green`, `test: green (46.1 s)`, coverage 99.14 %). The slowest tests in `.reports/junit.xml` are the time-limit tests of the runtimes, none from this feature. Two take 5.01 s each: `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` and `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`. Two `test_opencode_sudo_time_limit` rows take 4.52 s each. The feature's eleven tests take about 0.001 s each. Disk: `/work` holds 0.5 GB used and 970.1 GB free, as at the previous record (`disk start`). `/state` and `/tmp` are unchanged at 0.0 GB used. No growth.

## 8 Cost

One story: 6 runs, 3.7 min, 36 turns, 104297 tokens in (557574 more from cache), 9432 out, $0.95. Every stage ran once, on its first attempt, with no round and no stall. By run: intake $0.07 (12 s), tester $0.22 (73 s), coder $0.17 (67 s), reviewer $0.22 (26 s), documenter $0.11 (22 s), smoke tester $0.16 (20 s). The tester and the coder are the longest, because each runs a project command (`make lint` and `make test`, then `make check`). Nothing stands out. Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `F0034-S0002-the-playbook-and-the-project-guide-say-the-reviewer-corrects-a-stale-description.md`: a documentation repair. Three playbook passages still call the reviewer's edit "a story to draft", and the project guide's count of the agents' v1.1 passages leaves out the reviewer's three new ones (check 5). `factory-check-story` says `ok`.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 story proposed
   1 Scope: none. F0034-S0001 built all three Scope items (`claude/agents/reviewer.md:70`, `tests/test_claude_agent_texts_description.py`, three docs) and touched nothing that is Out of scope. No paid reviewer run has corrected a real Description yet, which the feature itself rules out.
   2 Feature smoke test: green. The factory's agent reader gives the reviewer the rule with all five clauses, only the reviewer carries it (6 × 0, 1 × 1), and item 5 is kept. The review role's expanded write paths let it write its story and refuse `src/` and `feature.md`.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the documenter missed `docs/project-guide/agents.md:244-248` and the playbook's neighbouring passages (in F0034-S0002). Nobody commented on `duplicates: 5 new` from a story with no `src/` change: four runtime similar-code pairs and `ManualWaiter` (`clock.py:45`), all from earlier features. Listed for the human, no story.
   5 Documentation: `docs/operator-playbook.md:50,127,148` still call the reviewer's edit "a story to draft", against line 61. `docs/project-guide/agents.md:248,305` count three v1.1 passages and leave out the reviewer's Notes, added-criterion and Description paragraphs. Proposed: F0034-S0002.
   6 Decisions: feature decisions 1 to 4 listed for the human. The story has no answers and no defaults. Earlier tests changed: none.
   7 Slow checks: none beyond `make check` (green, 99.14 %, test 46.1 s). The slowest tests are runtime time-limit tests (5.01 s), none from this feature. Disk unchanged at 0.5 GB used on `/work`.
   8 Cost: 6 runs, 3.7 min, $0.95, every stage on its first attempt. The tester ($0.22, 73 s) and the coder ($0.17, 67 s) take longest because they run the project commands. 0 questions, 0.0 h waited.
3. factory: done (pull request merged); cost: 1 runs, 3.8 min, 23 turns, 61346 tokens in (1084302 more from cache), 14792 out, $1.00
