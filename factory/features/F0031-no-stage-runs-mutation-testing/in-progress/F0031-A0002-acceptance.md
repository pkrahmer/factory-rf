---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 298
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T23:07:30.909326Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T23:11:24.130124Z'
  stage: acceptance
  run: 61ca1cdf633c49c1ba48f8b83b1d2b8b
stories: [F0031-S0001, F0031-S0002]
outcome: null
---

# Acceptance of No stage runs mutation testing

## Recommendation

`accepted with stories`. The two stories together meet the feature's goal. No shipped agent runs or reads mutation testing. Check 3 is the one line `By sweep, not run here.`. The template's `Makefile` no longer calls `mutants` a report (S0002). The human's changes 2 and 3 have been applied: `mutants/*` is out of `tool_paths`, and the acceptance reviewer runs at 40/60. `make check` is green. The feature smoke test's 25 behavioural lines are green. Its one red line is a docs example: the operator guide still shows a stopped `mutants` report line, which no stage can write any more. That example is an illustration, not a broken promise, so I propose a docs repair (F0031-S0003).

## 1 Scope

None. Every Scope item has its story, and both stories built what they name:
- `claude/agents/acceptance-reviewer.md` (check 3 at line 55, check 7 at line 59) and `claude/agents/reviewer.md`: S0001. The smoke test (section 2) reads them through the factory's own agent reader.
- `template/CLAUDE.md` and `template/Makefile`: S0001 wrote line 103 and `CLAUDE.md`. S0002 wrote the header at lines 4-5 (`` `duplicates` is a report outside `check`; `mutants` is for a sweep by hand, never a stage.``), which the first acceptance proposed.
- The tests: S0001 rewrote `tests/test_claude_agent_texts_mutants.py` and changed `TEMPLATE_RULES_LINES`. S0002 added `tests/test_template_makefile_header.py`.
- The docs: `docs/operator-guide.md` *Mutation testing by sweep*, `docs/project-guide/processes-and-checks.md` *Mutation testing*, `docs/project-guide/agents.md:299` and the `docs/decisions.md` entry (S0001).

Nothing was built outside the scope, and no module under `src/` changed. S0002 is the first acceptance's proposal. It changes one line of a template file, which falls within the scope item "`template/Makefile`: `make mutants` is for a sweep by hand". The goal's last part, the shorter time limit, has now been met by the human's change 3 (commit `f5f572ae`). This acceptance runs under it, with a lease of 60.

## 2 Feature smoke test

The walk-through checks the feature's purpose end to end through the factory's own readers. It reads every shipped agent the way an agent run gets it (`FrontmatterAgentDefinitionReader` over `claude/`) and every pipeline definition the way the factory loads it (`RuamelPipelineDefinitionReader`). It then checks what a project made from the template and an operator read. Compared with the first acceptance, it adds the template header (S0002), `tool_paths`, the acceptance reviewer's limits (the human's changes 2 and 3), and one docs check: no example in the operator guide shows a `mutants` report line. The script lived in a `mktemp -d` folder that removed itself.

```
$ uv run python -I "$d/smoke.py" "$PWD"; echo "exit $?"
ok   acceptance-reviewer: every mutation line forbids it (2 lines)
     checks: ['1 Scope against what was built.', "2 The feature's smoke test.", '3 Mutation testing.', '4 What the stories noticed.', '5 The documentation as a whole.', '6 Decisions taken for the human.', '7 The slow checks.', '8 Cost.']
ok   acceptance-reviewer: checks 1 to 8 in order
ok   acceptance-reviewer: check 3 is Mutation testing
ok   acceptance-reviewer: the one line of check 3
ok   acceptance-reviewer: the report keeps sections 1 to 8
ok   acceptance-reviewer: the entry has no mutants score
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
ok   decision log: the sweep entry
FAIL operator guide: no example shows a `mutants` report line
feature smoke: red (1 failed)
exit 1
```

Red on one line, a documentation check. Every behavioural line is green: the agents, the three pipeline definitions, the template, and the operator guide's and decision log's statements. The red line is `docs/operator-guide.md:703` (*What a stage run shows*, point 3). It illustrates a report stopped at its time limit with `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) ``, the line of the coder's old `mutants` report. No stage has a `mutants` report since 2026-10-19, so an entry can no longer hold that line. The rule it illustrates is still true, and the guide says plainly at line 82 that no stage runs the target. So this is a stale example, not a broken promise. Proposed as F0031-S0003. `make check` was green when I found it (`check: green`, coverage 99.13 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0001 (coder entries 7, 11 and 15, reviewer entry 17, documenter entry 19): `template/Makefile:4` called `mutants` a report. The first acceptance proposed this, and S0002 built it. Closed.
- S0002 (coder entry 7, reviewer entry 9, documenter entry 11, smoke tester entry 13): the todo demo's `Makefile:4` still reads ``# `duplicates` and `mutants` are reports outside `check`; `openapi` writes docs/openapi.json.``. The file is outside every write path, so it goes to the human (section 6).
- S0001's documenter (entry 19): the older `docs/decisions.md` entries on the acceptance's `make mutants` are history and are marked superseded. No story.
- S0001's documenter: `factory/pipeline.yml:29` still had the old comment. The human's change 3 has since fixed it. Closed.
- S0001's reviewer: the docstring of `tests/test_claude_agent_texts_mutants.py:1` uses a backslash continuation. That is correct, and the text is decision 7's. No story.
- S0002 noticed nothing else.

## 5 The documentation as a whole

Read as a newcomer: `README.md` does not name mutation testing. The operator guide's *Mutation testing by sweep*, the project guide's *Mutation testing* and `CLAUDE.md`'s *Checks* agree: no stage runs `make mutants`, and sweeps do. Three findings:
- `docs/operator-guide.md:703`: the stopped-report example is a `mutants` report line (section 2). Proposed as F0031-S0003, which replaces it with a stopped `test` report of the tests stage. The tests that use `mutants` as sample data stay, under decision 7.
- `docs/project-guide/processes-and-checks.md:160-162` and `docs/project-guide/agents.md:299` still describe how the recipe reads an acceptance's branch, and say that "each acceptance run shortens its list". That is true of the recipe, but it reads as if acceptances ran it. The first acceptance found the same. The human's draft F0032 (`planning/overnight/stories/F0032-mutation-testing-keeps-only-its-sweep-form/`, its decision 5) removes that branch mode and rewrites those sections, so I propose no story here.
- `docs/operator-playbook.md:34` still says "F0031 ... takes it out of the acceptance reviewer's text; until it is merged, `CLAUDE.md` already says so". F0031 is now merged. No stage keeps the playbook, so this goes to the human (section 6).

No example runs `make mutants` from a stage.

## 6 Decisions taken for the human

The feature's decisions, as built:
1. No shipped agent runs or reads mutation testing, for the template's projects too. Built.
2. Check 3 stays as one line and is not dropped. Built. The human may still choose to drop it.
3. "Never run `make mutants` or mutmut" is written in the text. Built.
4. The entry has no mutants score. Built.
5. The reviewer's paragraph goes. Built.
6. The template's words change: `template/CLAUDE.md`, `template/Makefile:103`, and since S0002 the header at `template/Makefile:4`. Built. `template/factory/pipeline.yml` keeps `mutants/*` in its `tool_paths`, as decided.
7. The leave to change two earlier tests. Used as given (see below).
8. F0024-S0005 is removed and its true parts moved. Done. F0024 now has no `backlog/` folder.
9. `mutants` and `mutants/*` leave `factory/pipeline.yml` (change 2). Done now. The project command and the `tool_paths` entry are both gone (`f5f572ae`), and `CLAUDE.md` says "six targets".
10. The acceptance reviewer goes to 40/60 (change 3). Done (`f5f572ae`). This acceptance is the first one under it. Revisit only if an acceptance meets the 40 minutes.
11. The order with F0030 (change 6). The criterion 9 sentence of the F0030 draft has been rewritten as given, and the removed paragraph of the operator guide is no longer named. Still stale in the draft's `feature.md` (the human's): line 5 says the fault matters "for the acceptance's `make mutants`", and its change 1 still edits F0024-S0005, which no longer exists.
12. and 13. One story planned, and the number and name. S0002 was added from the first acceptance.

Open for the human, outside every write path:
- The todo demo's `Makefile:4` still calls `mutants` a report. If the demo is to follow the template, the human makes the matching change.
- `docs/operator-playbook.md:34`: the "until it is merged" clause is stale.
- The F0030 draft's `feature.md`, as listed under item 11.

Earlier tests changed, as the reviewers' entries name them:
- S0001 (reviewer entry 17): `tests/test_claude_agent_texts_mutants.py` (rewritten) and `TEMPLATE_RULES_LINES` of `tests/test_claude_files.py`, both under the feature's decision 7.
- S0002 (reviewer entry 9): none. It only added `tests/test_template_makefile_header.py`.

No earlier test was changed without a named leave.

## 7 The slow checks

Nothing beyond `make check` (no image scan, no SBOM), and `make mutants` is not run (check 3). In `.reports/junit.xml` (6016 tests, `make test` 46.0 s), the slowest tests are:
- `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`: 5.0 s
- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s
- the `status-1` and `sigkill` rows of `tests/adapters/test_opencode_sudo_time_limit.py`: 4.5 s each

All four are time-limit tests, and none of them belongs to this feature. Disk: `/work` was at 0.5 GB used both now and at the previous record, and `/state` and `/tmp` at 0.0 GB. Free space fell by 0.1 GB on all three at once (970.4 to 970.3 GB). They share one volume, and the feature's own usage did not grow. Nothing is left to explain.

## 8 Cost

16 runs, 11.3 min, 93 turns, 327229 tokens in (1652209 more from cache), 30122 out, $3.07, for two stories:
- S0001: 10 runs, 8.0 min, $2.30.
- S0002: 6 runs, 3.3 min, $0.77, each stage once, with no rework.

S0001 stands out, and the first acceptance gave the cause. Its rework round 1 cost about $0.83, 36 % of the story, for one test-module docstring that the tester paraphrased where decision 7 gave the text word for word. 0 questions were answered by the human and 0.0 h were waited, so no story needed the human.

## Proposed stories

- `F0031-S0003-the-operator-guide-s-stopped-report-example-is-a-report-a-stage-runs.md`: the operator guide's example of a report stopped at its time limit is a `mutants` report line, which no stage can write any more. It is the one red line of the feature smoke test. A docs-only repair that switches the example to the tests stage's `test` report.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 story proposed
   1 Scope: none. Every Scope item has its story. S0001 built the agent, template, test and docs changes, and S0002 built the `template/Makefile:4` header that the first acceptance proposed. No module under `src/` changed. The goal's shorter time limit has been applied by the human's change 3 (`f5f572ae`), and this acceptance runs at 40/60.
   2 Feature smoke test: 25 ok, 1 FAIL. The walk-through reads the seven shipped agents and the three pipeline definitions through the factory's own readers, then the template and the docs, and every behavioural line is green. The one red line is a docs check: `docs/operator-guide.md:703` gives `` `mutants`: 1718/1858 mutants (stopped at its time limit after 600 s) `` as its example of a stopped report, a line no stage can write any more. This is a stale example, not a broken promise, and is proposed as F0031-S0003. `make check` was green when I found it (coverage 99.13 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0002 closed the template header from S0001's notes, and the human's change 3 closed the stale pipeline comment. Still open is the todo demo's `Makefile:4`, which every stage of S0002 noticed; it is the human's file. The superseded decision-log entries and the docstring continuation need no story.
   5 Documentation: the operator guide, the project guide and `CLAUDE.md` agree that mutation testing runs by sweep. Three stale spots: the operator-guide example (S0003); `processes-and-checks.md:160-162` and `agents.md:299` on the acceptance branch mode, which the human's draft F0032 rewrites, so no story; and `docs/operator-playbook.md:34`, which still says "until it is merged" and is the human's.
   6 Decisions: decisions 1 to 10 are built or applied, including changes 2 and 3 (`mutants/*` out of `tool_paths`, the acceptance reviewer at 40/60). Change 6 is applied in the F0030 draft's criterion 9, but the draft's `feature.md` still names the acceptance's `make mutants` and F0024-S0005, which is gone. Also open for the human: the demo's `Makefile:4` and the playbook line. Earlier tests: S0001's two were changed under decision 7, S0002 changed none, and none was changed without a leave.
   7 Slow checks: nothing beyond `make check`. The slowest tests are time-limit tests at 4.5 to 5.0 s, none of them this feature's. Disk use is unchanged (`/work` 0.5 GB). Free space fell by 0.1 GB on the shared volume, which the feature's own usage does not explain and does not need to.
   8 Cost: 16 runs, 11.3 min, $3.07 (S0001 $2.30, S0002 $0.77). S0001 stands out with a $0.83 rework round over a paraphrased docstring. 0 questions, 0.0 h waited.
