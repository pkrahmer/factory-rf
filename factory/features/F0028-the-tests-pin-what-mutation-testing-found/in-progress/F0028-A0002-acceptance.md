---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 334
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T04:32:56.843738Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T04:37:52.807294Z'
  stage: acceptance
  run: e56568a9fd0a47f19772b661868b997c
stories: [F0028-S0001, F0028-S0002, F0028-S0003, F0028-S0004, F0028-S0005, F0028-S0006, F0028-S0007, F0028-S0008, F0028-S0009, F0028-S0010, F0028-S0011]
outcome: null
---

# Acceptance of The tests pin what mutation testing found

## Recommendation

accepted with stories. This is the second acceptance of F0028. Since the first one (F0028-A0001, accepted), two stories were archived: S0010 and S0011, the two documentation stories that A0001 proposed. Both did what they promised. The feature smoke test is green and `make check` is green. One finding is worth a story: the new *Shared test helpers* section names every helper module, but its `conftest.py` line lists only 11 of the 25 root fixtures and reads as if the list were complete. It also leaves out the handlers' conftest. These are exactly the helpers whose copies the section is meant to prevent, so S0012 is proposed. No promise of `feature.md` is broken.

## 1 Scope

None. S0001 to S0009 are unchanged since A0001, which found every Scope line built (23 test modules, 88 tests, three new shared modules, nothing under `src/`). The two new stories lie outside `feature.md`'s *Stories* list and its line "The documents: every story's docs criterion is `none`". They are the follow-ups A0001 proposed and the human started, and S0011's intake recorded that. Neither goes beyond its own Description:

- S0010 (#332) changed one line of `docs/project-guide/watching.md`. Step 4 of *A crash is discarded and the stage is rerun* (line 103) now names `work item <id>: crash of stage <stage> recorded` and `work item <id>: expiry of stage <stage> recorded`, which matches `src/factory/application/recovery.py:102-104`.
- S0011 (#333) added *Shared test helpers* to `docs/project-guide/README.md`, with one line for each of the 37 modules `tests/*.py` whose name does not start with `test_`, and named the section in *The files*.
- Neither touched `src/`, `tests/`, `README.md`, `docs/operator-guide.md` or `docs/decisions.md`.

## 2 Feature smoke test

The walk-through checks three things. The feature's 23 test modules must pass on a throwaway copy of today's `src/`. One hand-made break per sampled story (S0001, S0004, S0006, S0008) must turn that story's module red. And the two documentation stories must hold against the code: the guide's recovery subjects must match what `commit_subject` builds, and the helper list must name every helper module and every conftest fixture. The breaks are hand-made, not mutmut and not `make mutants`. The script ran from the repository's `.venv` Python with `PYTHONPATH` set to the copy, in this run's `$TMPDIR`, and changed nothing in the checkout. A first run lost pytest's summary line because I had passed `-q` on top of `addopts`. The output below is from the run after that fix.

Command: `bash "$TMPDIR/smoke/feature-smoke.sh" /work/checkout`

```
== unchanged code: the feature's 23 test modules
   factory imported from <copy>/src/factory/__init__.py
   88 passed in 5.34s
== S0001 breaks domain/settings.py: authority.rpartition("@") -> authority.partition("@")
   1 failed, 11 passed in 0.04s
== S0004 breaks domain/provider_limits.py: if seconds > 0 else None -> if seconds >= 0 else None
   2 failed, 2 passed in 0.04s
== S0006 breaks application/recovery.py: {entry_kind} of stage {target.state.stage} recorded -> {entry_kind} of stage recorded
   3 failed in 0.48s
== S0008 breaks application/tick.py: self._stop("fetch_failed", str(error)) -> self._stop("fetch_failed", "")
   1 failed, 2 passed in 0.21s
== S0010: the guide's recovery step names the subjects the code commits
   found: work item <id>: crash of stage <stage> recorded
   found: work item <id>: expiry of stage <stage> recorded
   code gives: work item F0001-S0001: crash of stage doing recorded
   code gives: work item F0001-S0001: expiry of stage doing recorded
== S0011: every shared helper module and every conftest fixture is named in the guide's index
   modules missing: 0
   fixture not named: reopened_tmp_path
   fixture not named: group_umask
   fixture not named: local_settings
   fixture not named: probe_settings
   fixture not named: compose_service
   fixture not named: hosted_environment
   fixture not named: boundaries
   fixture not named: definition
   fixture not named: installed_agents
   fixture not named: walk
   fixture not named: layout
   fixture not named: image_layout
   fixture not named: records
   fixture not named: recorder
   conftest fixtures not named: 14
   not named: tests/application/handlers/conftest.py
```

The tests pass and every break is caught. The S0010 subjects in the guide match the code. Every helper module is named, as S0011's criterion asked. The fixture lines are my addition, beyond S0011's literal criterion. They show that the `conftest.py` line names 11 of 25 fixtures, and that `tests/application/handlers/conftest.py`, the one conftest below the root, appears nowhere in `docs/`. That conftest holds `snapshot_of`, `state_with`, `event_of`, `pull_request` and `work_item`. This is a gap in the guide, not a red result for the feature's purpose, and S0012 closes it. `make check` was green on the committed state as I found it (`check: green`, total coverage 99.14 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0010: no coder, reviewer, documenter or smoke-tester entry noticed anything.
- S0011: intake found that the Description's count of helper modules was off by one (35 instead of 36 besides `conftest.py`). The reviewer corrected it in the Description. Nothing else was noticed. No stage checked the `conftest.py` line against the fixtures (check 2, S0012).
- Carried over from A0001 and still open, none of them proposed again:
  - `tests/settings_support.py:1`: the docstring still names only the environment, not `raising`. The guide's new line for the module now names both.
  - `make duplicates` still reports `5 new, 33 known, 3 gone`, all of it in `factory.adapters` (the four claude/opencode runtime blocks and `ManualWaiter`). The baseline lags behind `main` outside this feature, and this is still for the human.
  - The uncovered `recovery.py:126` and `:200` and `stage.py:467` are still uncovered (out of scope, decision 11).

## 5 Documentation as a whole

I read `docs/project-guide/README.md` from the top and `watching.md` around the recovery.

- No contradiction found. Step 4 now names its subject in the same form as the other handlers' subjects. `pull request opened` is still named once, in the `ask_crash_cap` bullet, and step 4b is unchanged.
- The index is 188 lines, well under the guide's 600-line split rule.
- The new section's spot-checked lines match their modules: `tick_support.py` (`handlers_of`, and `Failing` with `ValueError("boom")`), `probe_support.py` (`opencode_died`, `opencode_sso_hint`), `acceptance_support.py` (`report_of`) and `settings_support.py` (`BASE`, `raising`).
- One gap. The `conftest.py` line names `kill_points`, `agent_runtime`, `hosting`, `remote_template`, `remote`, `checkout`, `human`, `clock`, `agent_home`, `world` and `work_item`, and calls them "the fixtures of the whole suite". It leaves out 14 more, among them `walk`, `installed_agents` and `boundaries`, which F0028's decision 13 names as the shared ground of S0005 to S0009. `tests/application/handlers/conftest.py`, also named in decision 13, has no line. A tester who trusts the list could write a second `walk` or `event_of`. Proposed as S0012.

## 6 Decisions taken for the human

`feature.md`'s decisions 1 to 14 are unchanged and were listed in A0001's report, which the human accepted by merging it. Decision 4 (the three domain guards stay) is still a recommended answer, with no answer from the human recorded. The S0003 time-zone survivor ("equivalent in a container that runs in UTC") still has no decision in `feature.md`.

New with S0010 and S0011:

1. S0011's Description and its section say that keeping the helper list current is the job of each later story's docs criterion. That puts the duty on whoever writes the story, which is the human, and no check enforces it. S0012 would extend the same duty to fixtures. The alternative is a structural test that compares the list with `tests/`. The S0011 tester rejected that test because the Interface excluded test modules.
2. S0011's documenter chose to list fixtures in one parenthesis per conftest rather than one line per fixture. S0012 keeps that form.
3. S0010 and S0011 overrode `feature.md`'s "every story's docs criterion is `none`" as follow-ups proposed by acceptance. S0011's intake recorded this, and `feature.md` was not changed (it is the human's).

Earlier tests changed: none. Both stories' reviewers confirmed that the diff changes, renames or deletes no test file. No finding.

## 7 Slow checks

Nothing beyond `make check` applies here (`make mutants` is check 3). `make duplicates` is a record, not a check, and it is unchanged at `5 new, 33 known, 3 gone` (check 4).

Disk: the Disk now line (`/work` 0.5 GB used, `/state` 0.0 GB, `/tmp` 0.0 GB, 970.1 GB free on each) equals the previous record line, which was also taken at an acceptance. No growth, as expected from two document-only stories.

From `.reports/junit.xml` of my `make check` run (6,094 tests, 441 s of test time on every core):

- The slowest tests are still the adapters' time-limit tests, none of them the feature's: `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` at 5.0 s, `test_claude_runtime_resume::...[resume ended by the time limit]` at 5.0 s, and `test_opencode_sudo_time_limit` at 4.5 s twice.
- The feature's 23 modules took 5.3 s together in the smoke test.

## 8 Cost

All eleven stories: 78 runs, 50.7 min, 421 turns, 1,512,832 tokens in (7,591,361 more from cache), 139,999 out, $14.35. A0001 counted 66 runs, 45.9 min and $12.84 for S0001 to S0009.

- The two new stories took 6 runs each, the minimum: S0010 $0.69 in 2.1 min, and S0011 $0.83 in 2.6 min. They are the cheapest of the feature.
- The tester, coder and reviewer runs of both stories found an empty diff and had nothing to do, as their Interfaces said. About $0.30 per story goes to that walk through the stages. For a story whose only criterion is `docs:` this is the pipeline's fixed cost, not waste.
- The outliers are still the ones A0001 named: S0001, S0002 and S0009 took 10 runs each, because of review rounds for copied helpers. S0009 was the costliest at $1.84.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

- `F0028-S0012-the-guide-s-list-of-shared-test-helpers-names-every-fixture.md`: the *Shared test helpers* section's `conftest.py` line names all 25 root fixtures, and a new line names the five fixtures of `tests/application/handlers/conftest.py`. Without this, the list S0011 wrote to prevent copied helpers leaves out `walk`, `boundaries`, `installed_agents` and `event_of`.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 story proposed
   1 Scope: none. Since A0001, two documentation stories were archived. S0010 named the two recovery commit subjects in `watching.md` step 4, and they match `recovery.py:102-104`. S0011 added *Shared test helpers* to the guide's index, naming all 37 helper modules. Neither touched `src/`, `tests/` or the other documents.
   2 Feature smoke test: green. On a throwaway copy, the feature's 23 modules pass (88 passed). Four hand-made breaks (S0001, S0004, S0006, S0008) each turn their story's module red. The guide's recovery subjects match `commit_subject`. The fixture check beyond S0011's criterion found two gaps: the `conftest.py` line names 11 of 25 fixtures, and `tests/application/handlers/conftest.py` is named nowhere.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0010 and S0011 noticed nothing beyond S0011's helper count, which the reviewer corrected. Still open from A0001 and not proposed again: the `tests/settings_support.py` docstring, the `make duplicates` baseline lagging behind `main` (5 new findings, all in adapters), and the uncovered internal-guard lines.
   5 Docs: no contradiction. The helper list leaves out `walk`, `boundaries`, `installed_agents` and 11 more root fixtures, and the whole handlers' conftest, which are the helpers a tester would otherwise copy (S0012).
   6 Decisions: feature.md's decisions 1 to 14 were listed in A0001; decision 4 and the S0003 UTC survivor still have no recorded answer. New: keeping the helper list current is left to each later story's docs criterion, with no check enforcing it. No earlier test changed.
   7 Slow checks: nothing beyond `make check`. Disk is unchanged since the previous acceptance record. The slowest tests are the adapters' time-limit tests (5.0 s); the feature's 23 modules take 5.3 s together.
   8 Cost: 78 runs, 50.7 min, $14.35 for the 11 stories. S0010 ($0.69) and S0011 ($0.83) took 6 runs each, the cheapest of the feature. S0009 ($1.84, 10 runs) is still the costliest. 0 questions to the human, 0.0 h waited.
