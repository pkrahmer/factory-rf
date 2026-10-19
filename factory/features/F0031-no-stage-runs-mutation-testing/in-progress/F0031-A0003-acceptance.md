---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 303
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T23:43:33.331788Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T23:46:25.183609Z'
  stage: acceptance
  run: 93629201354c4d49b6ef4d343b04da52
stories: [F0031-S0001, F0031-S0002, F0031-S0003]
outcome: null
---

# Acceptance of No stage runs mutation testing

## Recommendation

`accepted`. The three stories together reach the feature's goal:
- No shipped agent runs or reads mutation testing.
- Check 3 is the one line `By sweep, not run here.`, and the report keeps its eight sections.
- The template, the documents and the pipeline definition say that mutation testing runs by sweep.
- The acceptance reviewer runs at 40/60.

S0003 repaired the one red line of the second acceptance's smoke test. All 29 lines of the feature smoke test are now green, and `make check` is green. What is left lies in the human's files and drafts (section 6), and F0032 and F0038 already cover the stale document passages, so I propose no story.

## 1 Scope

None. Every Scope item has its story, and all three stories built what they name:
- `claude/agents/acceptance-reviewer.md`: check 3 at line 55, check 7 at line 59. `claude/agents/reviewer.md`: the paragraph is gone. Both are S0001's.
- `template/CLAUDE.md` and `template/Makefile:103`: S0001. The header at `template/Makefile:4`: S0002, proposed by the first acceptance.
- `tests/test_claude_agent_texts_mutants.py`, rewritten, and `TEMPLATE_RULES_LINES` of `tests/test_claude_files.py`: S0001. `tests/test_template_makefile_header.py`: S0002.
- The four documents: S0001. S0003, proposed by the second acceptance, replaced the stopped-report example in `docs/operator-guide.md:703`. It now reads `` `test`: ........ [ 87%] (stopped at its time limit after 600 s) ``, and that is the guide's only change.

Nothing was built outside the scope, and no module under `src/` changed. S0003 is documents only: its tester, coder and reviewer each changed nothing (entries 5, 7 and 9). The goal's shorter time limit is in `factory/pipeline.yml:29-31`, at 40/60, the human's change 3. This acceptance runs under it.

## 2 Feature smoke test

The walk-through is the second acceptance's, extended for S0003. It reads every shipped agent the way an agent run gets it (`FrontmatterAgentDefinitionReader` over `claude/`). It reads the three pipeline definitions the way the factory loads them (`RuamelPipelineDefinitionReader`). Then it checks the template, the operator guide and the decision log. Four lines are new:
- No example in the guide shows a `mutants` report line.
- The stopped example is the tests stage's `test` report.
- `test` is that stage's report, at 600 s.
- `make test` runs pytest with `-q`, so a stopped run's last line is a progress line, as the example shows.

The script lived in a `mktemp -d` folder that removed itself.

```
$ uv run python -I "$d/smoke.py" "$PWD"; echo "exit $?"
ok   acceptance-reviewer: every mutation line forbids it (2 lines)
     checks: ['1 Scope against what was built.', "2 The feature's smoke test.", '3 Mutation testing.', '4 What the stories noticed.', '5 The documentation as a whole.', '6 Decisions taken for the human.', '7 The slow checks.', '8 Cost.']
ok   acceptance-reviewer: checks 1 to 8 in order
ok   acceptance-reviewer: check 3 is Mutation testing
ok   acceptance-reviewer: the one line of check 3
ok   acceptance-reviewer: the report keeps sections 1 to 8
ok   acceptance-reviewer: no score, no survivors
ok   coder: names no mutation testing
ok   documenter: names no mutation testing
ok   intake: names no mutation testing
ok   reviewer: names no mutation testing
ok   smoke-tester: names no mutation testing
ok   tester: names no mutation testing
ok   factory/pipeline.yml: no mutants command, no stage names one
ok   factory/pipeline.yml: mutants/* not in tool_paths
ok   factory/pipeline.yml: acceptance-reviewer 40/60, as every other role [(40, 60)]
ok   template/factory/pipeline.yml: no mutants command, no stage names one
ok   demo/todo-service/project/factory/pipeline.yml: no mutants command, no stage names one
ok   template/Makefile:4: mutants for a sweep by hand
ok   template/Makefile: FEATURE comment
ok   template/CLAUDE.md: mutants for a sweep by hand
ok   template: no acceptance runs mutants
ok   template: mutants is no report
ok   operator guide: no stage runs make mutants
ok   operator guide: no example shows a `mutants` report line
ok   operator guide: the stopped example is the tests stage's test report
ok   pipeline: test is the tests stage's report, 600 s, as the example says
ok   Makefile: make test runs pytest -q, so its last line is a progress line
ok   decision log: the sweep entry
feature smoke: green (0 failed)
exit 0
```

Green, 29 of 29. The second acceptance's red line, the operator guide's `mutants` example, is now green. `make check` was green when I found it (`check: green`, coverage 99.13 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0003: none. Its coder, documenter, reviewer and smoke tester each wrote "nothing" or "none". The reviewer's one remark (entry 9) was that the coder's `duplicates: 5 new` could not come from this branch, because the branch changes no code. Those findings are on `main`, outside this feature, and the coder after them reads them. No story.
- Carried from the second acceptance and still open, both the human's:
  - The todo demo's `Makefile:4` still reads ``# `duplicates` and `mutants` are reports outside `check`; ...``, unlike the template's header. Every stage of S0002 noticed it.
  - `docs/operator-playbook.md:34` still says "until it is merged".

  Both are outside every write path, so they are listed in section 6.
- Closed earlier, as the second acceptance recorded: the template header (S0002), the comment at `factory/pipeline.yml:29` (change 3), the superseded decision-log entries (history; F0038-S0005 marks them), and the docstring continuation (correct as it stands).

## 5 The documentation as a whole

Read as a newcomer:
- `README.md` does not name mutation testing.
- These agree that no stage runs `make mutants` and that sweeps do: the operator guide's *Mutation testing by sweep*, the project guide's *Mutation testing*, `docs/decisions.md` and `CLAUDE.md`'s *Checks*.
- The guide's stop-note example (line 703) and its rule for reports (line 750) agree. The example matches what the tests stage's `test` report would print.

Still stale, with no story from here:
- `docs/project-guide/processes-and-checks.md:160-162` still describes how the recipe reads an acceptance's branch, and says "each acceptance run shortens its list". `docs/project-guide/agents.md:299` says "`FEATURE` is taken from an acceptance's branch". Both are true of the recipe, but they read as if acceptances ran it. The human's draft F0032 removes that branch mode and rewrites both passages. F0038's Out of scope leaves them to F0032.
- `docs/operator-playbook.md:34` is the human's playbook. F0038 lists it as the human's change (M7, M8), and F0032's change 6 covers the playbook's `make mutants` passages.

No contradiction misleads a user, and no example runs `make mutants` from a stage.

## 6 Decisions taken for the human

The feature's decisions, as built:
1. No shipped agent runs or reads mutation testing. Built (S0001).
2. Check 3 stays as one line. Built. The human may still choose to drop it.
3. "Never run `make mutants` or mutmut" is written in the text. Built.
4. The entry has no mutants score. Built.
5. The reviewer's paragraph goes. Built.
6. The template's words change. Built: `template/CLAUDE.md`, `template/Makefile:103`, and the header at line 4 (S0002).
7. The leave to change two earlier tests. Used as given (below).
8. F0024-S0005 is removed and its true parts moved. Done.
9. `mutants` and `mutants/*` leave `factory/pipeline.yml`. Done, and `CLAUDE.md` says "six targets".
10. The acceptance reviewer goes to 40/60. Done. This is the second acceptance under it, and it finished well inside the 40 minutes.
11. The order with F0030. Criterion 9 of the draft's S0001 was rewritten as change 6 gave it. The draft's `feature.md` (`planning/overnight/stories/F0030-.../feature.md`, the human's) still names the acceptance's `make mutants`:
    - Line 5 says "today the fault matters for the acceptance's `make mutants`".
    - Line 19 says "the acceptance's `make mutants` runs inside the acceptance reviewer's agent run".

    No acceptance runs it any more.
12. One story. The plan was one story. The feature took three: S0002 and S0003 are each the previous acceptance's proposal, and each changes one line.
13. The number and name. As planned.

S0003 itself took no decision for the human. The documenter wrote the Interface's text word for word.

Open for the human, outside every write path:
- The todo demo's `Makefile:4`: a matching change, if the demo is to follow the template's header.
- `docs/operator-playbook.md:34`: the stale "until it is merged" clause.
- The F0030 draft's `feature.md`, lines 5 and 19, as listed under decision 11.

Earlier tests changed, as the reviewers' entries name them:
- S0001 (reviewer entry 17): `tests/test_claude_agent_texts_mutants.py` (rewritten) and `TEMPLATE_RULES_LINES` of `tests/test_claude_files.py`. Both were changed under the feature's decision 7.
- S0002 (reviewer entry 9): none.
- S0003 (reviewer entry 9, item 6): none.

No earlier test was changed without a named leave.

## 7 The slow checks

Nothing beyond `make check` (no image scan, no SBOM), and `make mutants` is not run (check 3). In `.reports/junit.xml` (6016 tests, `make test` 43.1 s), the slowest tests are:
- `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`: 5.0 s
- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s
- the `status-1-past-the-limit` and `sigkill-past-the-limit` rows of `tests/adapters/test_opencode_sudo_time_limit.py`: 4.5 s each

All four are time-limit tests, and none of them belongs to this feature. Disk is unchanged from the previous record (the acceptance's): `/work` has 0.5 GB used, `/state` and `/tmp` 0.0 GB, and all three have 970.3 GB free. There is no growth to explain.

## 8 Cost

The three stories cost 22 runs, 13.5 min, 122 turns, 411535 tokens in (2031465 more from cache), 35883 out, $3.77:
- S0001: 10 runs, 8.0 min, $2.30.
- S0002: 6 runs, 3.3 min, $0.77.
- S0003: 6 runs, 2.2 min, $0.70. Each stage ran once, with no rework. The coder's run took 57 s of wall time for 9 s of model time, which was its own `make check`.

S0001 stands out. Its rework round 1, about $0.83, came from a test docstring that the tester paraphrased where decision 7 gave the exact text (see the first acceptance).

The two follow-up stories each cost about $0.70 for one changed line, roughly what six stage runs of a story with nothing to build cost. The three acceptances added $1.62 and $1.10, plus this one. Each found the next one-line leftover. Writing those lines into S0001's scope, where its stages noticed them, would have saved two stories and two acceptances.

The human answered 0 questions and the stories waited 0.0 h, so no story needed the human.

## Proposed stories

None. Every open item is either in the human's files (the todo demo's `Makefile:4`, `docs/operator-playbook.md:34`, the F0030 draft) or already covered by the human's drafts F0032 and F0038 (`processes-and-checks.md:160-162`, `agents.md:299`).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: none. Every Scope item has its story. S0001 built the agent texts, the template, the tests and the documents. S0002 built `template/Makefile:4`. S0003 replaced the operator guide's stopped-report example. Nothing under `src/` changed. The acceptance reviewer runs at 40/60 (the human's change 3).
   2 Feature smoke test: green, 29 ok and 0 failed. The walk-through reads the seven shipped agents and the three pipeline definitions through the factory's own readers, then the template, the operator guide and the decision log. The second acceptance's red line, the guide's `mutants` example, is green now: the example is the tests stage's `test` report, which matches the pipeline (600 s) and `make test -q`. `make check` was green when I found it (coverage 99.13 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: nothing new from S0003. Still open from S0002, and both the human's files: the todo demo's `Makefile:4`, which still calls `mutants` a report, and `docs/operator-playbook.md:34`, which still says "until it is merged".
   5 Documentation: the README, the operator guide, the project guide, the decision log and `CLAUDE.md` agree that mutation testing runs by sweep, and the stop-note example matches its rule. `processes-and-checks.md:160-162` and `agents.md:299` still describe the recipe reading an acceptance's branch. The human's draft F0032 rewrites them, so I propose no story.
   6 Decisions: decisions 1 to 10 and 13 are built or applied. Decision 12 planned one story, and the feature took three, two of them one-line follow-ups. Open for the human: the F0030 draft's `feature.md` (lines 5 and 19) still names the acceptance's `make mutants`, plus the demo's `Makefile:4` and the playbook line. Earlier tests: S0001's two were changed under decision 7, S0002 and S0003 changed none, and none was changed without a leave.
   7 Slow checks: nothing beyond `make check`. The slowest tests are four time-limit tests at 4.5 to 5.0 s, none of them this feature's. Disk is unchanged (`/work` 0.5 GB used, 970.3 GB free).
   8 Cost: 22 runs, 13.5 min, $3.77 (S0001 $2.30, S0002 $0.77, S0003 $0.70, with no rework in S0003). S0001 stands out with its $0.83 rework round over a paraphrased docstring. The two one-line follow-ups and their acceptances cost more than folding the noticed lines into S0001 would have. 0 questions, 0.0 h waited.
