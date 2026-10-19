---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 287
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T21:12:07.469189Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T21:16:41.705935Z'
  stage: acceptance
  run: 6d12626ee2244accb4c9cbb0b4aad88b
stories: [F0031-S0001]
outcome: null
---

# Acceptance of No stage runs mutation testing

## Recommendation

`accepted`. The one story reaches the feature's goal. No shipped agent runs or reads mutation testing, check 3 is the one line `By sweep, not run here.` under a report that keeps its eight sections, the template and the documents say that mutation testing is done by sweep, and `make check` and the feature's smoke test are green. What is left is one wording line in `template/Makefile` that three stages noticed (proposed as F0031-S0002) and the human's own changes 2, 3 and 6, which are still open (section 6).

## 1 Scope

None. Every Scope item has its story, and S0001 built each one:
- `claude/agents/acceptance-reviewer.md`: check 3 (line 55), check 7's start (line 59), the recommendation's and the proposals' words, and steps 1 and 3 hold the new texts.
- `claude/agents/reviewer.md`: the mutation-report paragraph is gone.
- `template/CLAUDE.md` and `template/Makefile:103`: `mutants` is for a sweep by hand.
- The tests: `tests/test_claude_agent_texts_mutants.py` was rewritten, and the `TEMPLATE_RULES_LINES` sentence of `tests/test_claude_files.py` was changed.
- The docs: `docs/operator-guide.md` (*Mutation testing by sweep*), `docs/project-guide/processes-and-checks.md` (*Mutation testing*), `docs/project-guide/agents.md` and `docs/decisions.md` (*Mutation testing runs only as sweeps outside the factory*).

Nothing was built outside the scope. No module under `src/` changed, and a search finds no use of `mutant` in `src/factory` outside `factory.domain.mutants` and `factory.entry.check_mutants`, which stay for the sweeps (Out of scope). The goal's last part, the acceptance reviewer's shorter time limit, is the human's change 3, not a story. It is still open (section 6). This acceptance itself ran on the new text, under the old lease of 100 minutes, without running `make mutants`.

## 2 Feature smoke test

The walk-through of the feature's purpose, run against the factory's own readers. It reads every shipped agent the way an agent run gets it (`FrontmatterAgentDefinitionReader`) and every pipeline definition the way the factory loads it (`RuamelPipelineDefinitionReader`), then checks what a project made from the template and an operator read. The script was kept in `$TMPDIR` and removed after the run.

```
$ uv run python -I "$d/smoke.py" "$PWD"
ok   acceptance-reviewer: every mutation line forbids it (2 lines)
ok   coder: names no mutation testing
ok   documenter: names no mutation testing
ok   intake: names no mutation testing
ok   reviewer: names no mutation testing
ok   smoke-tester: names no mutation testing
ok   tester: names no mutation testing
     checks: ['1 Scope against what was built.', "2 The feature's smoke test.", '3 Mutation testing.', '4 What the stories noticed.', '5 The documentation as a whole.', '6 Decisions taken for the human.', '7 The slow checks.', '8 Cost.']
ok   acceptance-reviewer: checks 1 to 8 in order
ok   acceptance-reviewer: check 3 is Mutation testing
ok   acceptance-reviewer: the one line of check 3
ok   acceptance-reviewer: the report keeps sections 1 to 8
ok   acceptance-reviewer: the entry has no mutants score
ok   factory/pipeline.yml: no mutants command, no stage names one
ok   template/factory/pipeline.yml: no mutants command, no stage names one
ok   demo/todo-service/project/factory/pipeline.yml: no mutants command, no stage names one
ok   template/CLAUDE.md: mutants for a sweep by hand
ok   template/Makefile: mutants for a sweep by hand
ok   template: no acceptance runs mutants
ok   operator guide: no stage runs make mutants
ok   decision log: the sweep entry
feature smoke: green (0 failed)
exit 0
```

Green. The two lines of the acceptance reviewer that name mutation testing are check 3's prohibition and check 7's `but not make mutants (check 3)`. `make check` was green when I found it (`check: green`, coverage 99.12 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- `template/Makefile:4` says that "`duplicates` and `mutants` are reports outside `check`". The coder noticed it (S0001 entries 7, 11 and 15), the reviewer too (entry 17, notes) and the documenter (entry 19). In this factory, "report" is a stage's `reports:` command (`factory/pipeline.yml`). `mutants` is now for a sweep by hand, so the header contradicts line 103 of the same file. Proposed as F0031-S0002. The todo demo's `Makefile:4` has the same line. It is outside every write path, so it is listed for the human under section 6.
- `docs/decisions.md` keeps older entries in which the acceptance runs `make mutants` (for example *Mutation testing is limited to one feature's modules*). The documenter's entry 19 noted them. They are history, and each one is marked superseded. No story.
- `factory/pipeline.yml:29` still says that `make mutants` re-runs inside the acceptance agent's run. The documenter noted it. It is the human's change 3 (section 6).
- The reviewer's note on `tests/test_claude_agent_texts_mutants.py:1`: the docstring is held under 100 columns by a backslash continuation inside the string. It is unusual but correct (the docstring's value is decision 7's text). No story.

## 5 The documentation as a whole

Read as a newcomer: `README.md` does not name mutation testing. `docs/operator-guide.md` *Mutation testing by sweep* and `docs/project-guide/processes-and-checks.md` *Mutation testing* agree with each other and with `CLAUDE.md`'s *Checks*: no stage runs the target, and sweeps do. One remark, with no story from this feature. `processes-and-checks.md:160-162` still describe the recipe's reading of an acceptance's branch (`work-item/<feature id>-A<n>`) and say that "each acceptance run shortens its list by what it kills and goes on". The recipe still does this when it runs on such a branch, so it is true of the target. But it reads as if acceptances ran it, which the sentence before it rules out. `docs/project-guide/agents.md:299` (`FEATURE` is taken from an acceptance's branch) has the same leftover. The human's draft F0032 (`planning/overnight/stories/F0032-mutation-testing-keeps-only-its-sweep-form/`) removes that branch mode and rewrites this section with it, so a story here would edit text that F0032 replaces. No contradiction misleads a user: no example runs `make mutants` from a stage.

## 6 Decisions taken for the human

The feature's decisions, as built:
1. No shipped agent runs or reads mutation testing, for the template's projects too. Built.
2. Check 3 stays as one line, `By sweep, not run here.`, and is not dropped. Built. The human may still choose the drop.
3. "Never run `make mutants` or mutmut" is in the text, not only left out. Built.
4. The entry loses `make mutants <killed>/<total>`. Built.
5. The reviewer's paragraph goes. Built.
6. The template's words change; `template/factory/pipeline.yml` keeps `mutants/*` in its `tool_paths`. Built.
7. The leave to change two earlier tests. Used as given (see below).
8. F0024-S0005 removed and its true parts moved into S0001's docs criterion. Done: F0024's backlog holds only S0004, and the operator guide holds the 439 s and 12 s runs and the copy of the other files under `src/`.
9. **Open, the human's:** `mutants` and `mutants/*` leave `factory/pipeline.yml` (change 2). Half done. The `mutants` project command is gone and `CLAUDE.md` says "six targets", but `"mutants/*"` is still in `tool_paths` (`factory/pipeline.yml:18`). Accept by removing it, or keep it on purpose.
10. **Open, the human's:** the acceptance reviewer's `time_limit` 90 / `lease_duration` 100 becomes 40 / 60, after S0001 is merged and `self` is rebuilt (change 3). Not yet done: `factory/pipeline.yml:29-30` still hold the old comment and limits. This acceptance is the first run on the new text.
11. The order with F0030. F0031 was merged first, so the human's change 6 applies, and it is not yet done. The F0030 draft's S0001 criterion 9 still names the operator guide's *The mutation report of a story* and its `Permission denied` paragraph, which no longer exist. It also still says "the factory's KILL of a report reaches mutmut", and no report runs `make mutants` any more.
12. One story. As planned.
13. Number and name. As planned.

The human's changes not yet listed: change 1 (`CLAUDE.md`, *Checks*) is done. Change 4 (the todo demo's `CLAUDE.md` and `Makefile:103`) is done. Change 5 (F0024-S0005 removed) is done. New, from section 4: the todo demo's `Makefile:4` holds the same "`duplicates` and `mutants` are reports" header as the template. If F0031-S0002 is taken, the demo line would follow it as a human's change.

Earlier tests changed, as the reviewers' entries name them (S0001 entry 17):
- `tests/test_claude_agent_texts_mutants.py` (F0024-S0003): rewritten under the feature's decision 7.
- `tests/test_claude_files.py` (`TEMPLATE_RULES_LINES` only): changed under the feature's decision 7.

No earlier test was changed without a named leave.

## 7 The slow checks

Nothing beyond `make check` (no image scan, no SBOM), and `make mutants` is not run (check 3). The slowest tests in `.reports/junit.xml` (5999 tests, `make test` 45.7 s):
- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s
- `tests/adapters/test_opencode_budget.py::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`: 5.0 s
- the two `sigkill`/`status-1` rows of `tests/adapters/test_opencode_sudo_time_limit.py`: 4.5 s each

All of them are time-limit tests, and none of them is this feature's. Disk is the same at start and at acceptance: `/work` 0.5 GB used, `/state` 0.0 GB, `/tmp` 0.0 GB, 970.5 GB free on each. There is no growth to explain.

## 8 Cost

10 runs, 8.0 min, 65 turns, 235842 tokens in (1291433 more from cache), 23762 out, $2.30, for one story. 0 questions answered by the human and 0.0 h waited, so no story needed the human. No run stands out by itself. The largest was the first tester run, at $0.42 and 108 s. The rework round stands out by its cause. Round 1 (S0001 entries 11 to 17: coder $0.17, tester $0.24, coder $0.12, reviewer $0.30, about $0.83, 36 % of the story) existed only for the test module's docstring. The tester had written its own wording where decision 7 gave the exact text. The reviewer was right to hold the leave to its letter, so this is not a finding against the process. A feature that gives a test's docstring word for word buys a round when the tester paraphrases it.

## Proposed stories

- `F0031-S0002-the-template-makefile-header-calls-mutants-a-sweep-by-hand.md`: line 4 of `template/Makefile` still calls `mutants` a report, against line 103 of the same file and the feature's goal. Three stages of S0001 noticed it and none owned it.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed
   1 Scope: none. Every Scope item has its story, S0001 built each one, nothing was built outside the scope, and no module under `src/` changed. The goal's shorter time limit for the acceptance reviewer is the human's change 3, still open.
   2 Feature smoke test: green. The walk-through reads all seven shipped agents and all three pipeline definitions through the factory's own readers, then the template and the docs: 20 ok, 0 failed. `make check` was green when I found it (coverage 99.12 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: `template/Makefile:4` still calls `mutants` a "report" (noticed by S0001's coder, reviewer and documenter; proposed as F0031-S0002). The superseded entries in `docs/decisions.md` are history, and `factory/pipeline.yml:29` is the human's change 3.
   5 Documentation: consistent across `README.md`, the operator guide, the project guide and the decision log. `processes-and-checks.md:160-162` and `agents.md:299` still describe the recipe reading an acceptance's branch. That is true of the target, but it reads as if an acceptance runs it. The human's draft F0032 rewrites that section, so no story here.
   6 Decisions: decisions 1 to 8 and 11 to 13 are built as listed. Two are open, the human's: decision 9 is half done (the `mutants` command is gone, but `mutants/*` is still in `tool_paths`), and decision 10 (time limit 40, lease 60) is not applied yet. The human's changes 1, 4 and 5 are done. Change 6 (the F0030 draft still names the removed operator-guide paragraph) is not. The two earlier tests were changed under decision 7, and none was changed without a leave.
   7 Slow checks: nothing beyond `make check`. The slowest tests are the time-limit tests, at 5.0 s each. Disk is unchanged (0.5 GB used on `/work`).
   8 Cost: 10 runs, 8.0 min, $2.30. No questions to the human and 0 h waited. Round 1 cost about $0.83 (36 % of the story) for one test-module docstring, where the tester paraphrased the text that decision 7 gave word for word.
