---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 337
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T04:55:11.487230Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T04:58:49.526752Z'
  stage: acceptance
  run: 7a8a16c50f034a4e94ac0229cdc0612b
stories: [F0028-S0001, F0028-S0002, F0028-S0003, F0028-S0004, F0028-S0005, F0028-S0006, F0028-S0007, F0028-S0008, F0028-S0009, F0028-S0010, F0028-S0011, F0028-S0012]
outcome: null
---

# Acceptance of The tests pin what mutation testing found

## Recommendation

accepted. This is F0028's third acceptance. Since the second one (F0028-A0002, accepted with stories), one story was archived: S0012, the documentation story A0002 proposed. The guide's *Shared test helpers* section now names all 25 fixtures of `tests/conftest.py` and all 5 of `tests/application/handlers/conftest.py`, and their descriptions match the fixtures' docstrings. The feature smoke test is green (88 tests pass, five hand-made breaks each turn their story's module red, the guide's lists match the tree), and `make check` is green. No finding has weight, and no story is proposed.

## 1 Scope

None. S0001 to S0011 are unchanged since A0002. A0001 found every Scope line of `feature.md` built (23 test modules, 88 tests, three new shared modules, nothing under `src/`), and A0002 found S0010 and S0011 within their Descriptions.

S0012 (#336) changed only `docs/project-guide/README.md`, 5 lines (`git diff 61913d5e^1 61913d5e --stat`, besides its work item and sidecar):

- the `conftest.py` line now names all 25 root fixtures, grouped by use, with `reopened_tmp_path` marked autouse;
- a new line `application/handlers/conftest.py` names its 5 fixtures, says they serve only the handlers' tests, and says its `work_item` is a published work item, not the root's started story;
- the opening paragraph has the one added sentence its criterion asked for.

Like S0010 and S0011, S0012 is outside `feature.md`'s *Stories* list and its line "every story's docs criterion is `none`". It is an acceptance follow-up the human started, and its intake recorded that. It touched no `src/`, `tests/`, `README.md`, `docs/operator-guide.md` or `docs/decisions.md`.

## 2 Feature smoke test

The walk-through checks the feature's purpose end to end:

- the feature's 23 test modules pass on a throwaway copy of today's `src/`;
- a hand-made break of a behaviour that a story pinned turns that story's module red. This run samples the stories A0002 did not sample (S0002, S0003, S0005, S0007, S0009). The breaks are hand-made, not mutmut and not `make mutants`;
- the three documentation stories hold against the tree: the guide's recovery subjects (S0010), a line for every helper module (S0011), and every fixture of both conftests named in its line (S0012).

The script ran from the repository's `.venv` Python with `PYTHONPATH` set to the copy, in a `mktemp -d` under this run's `$TMPDIR`. It changed nothing in the checkout. A first run had a syntax error in my own S0009 break, because a comment swallowed the argument's comma. I removed the comment, and the output below is from the rerun.

Command: `bash "$TMPDIR/smoke/feature-smoke.sh" /work/checkout`

```
== unchanged code: the feature's 23 test modules
   factory imported from <copy>/src/factory/__init__.py
   88 passed in 5.41s
== S0002 breaks domain/sections.py: range(opening + 1, len(lines)) -> range(opening + 2, len(lines))
   2 failed, 4 passed in 0.05s
== S0003 breaks domain/board.py: return _ABSENT if value is None else str(value) -> return "" if value is None else str(value)
   3 failed in 0.04s
== S0005 breaks application/acceptance.py:     return stage.role ->     return "reviewer"
   2 failed, 3 passed in 2.05s
== S0007 breaks application/recovery.py: n=str(expiry.number) -> n=str(state.crashes)
   2 failed in 0.33s
== S0009 breaks application/dispatcher.py: pull_request=None if state is None else state.pull_request -> pull_request=state.pull_request
   1 failed in 0.12s
== S0010: the guide's recovery step names the subjects the code commits
   found: work item <id>: crash of stage <stage> recorded
   found: work item <id>: expiry of stage <stage> recorded
== S0011/S0012: every helper module and every conftest fixture is named in the guide
   helper modules: 37, without a line of their own: 0
   conftest.py: 25 fixtures, not named: 0
   application/handlers/conftest.py: 5 fixtures, not named: 0
```

Green:

- Every break was caught.
- Together with A0002's four samples (S0001, S0004, S0006, S0008), each of the nine test stories has now had one behaviour broken by hand and caught.
- The 19 fixtures that A0002 found missing are all named now.
- I also compared each fixture's description in the guide with its docstring (an `ast` listing of both conftests): all 30 agree, including `clock` (noon UTC on 2026-10-12), `definition` (the acceptance stage `acceptance`) and `walk` (`F0002-todo`, due with two archived stories).

`make check` was green on the committed state as I found it (`check: green`, total coverage 99.14 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0012: the coder noticed only that the story's first smoke test would print 19 `missing:` lines until the documenter's edit, which was expected. The documenter found no stale text. The reviewer and the smoke-tester had no remarks.
- Mine, from check 2: the section covers only `tests/*.py` at the root, by its own words. Three shared stand-ins live below it, in `tests/adapters/`:
  - `claude_stand_in.py`, used by test modules under `tests/entry/`, `tests/application/` and `tests/adapters/`;
  - `opencode_stand_in.py`, used under `tests/entry/` and `tests/adapters/`;
  - `pygithub_stand_ins.py`, used by one module.

  The section's opening says a helper that more than one test module uses "lives in a module at the root of `tests/`". The first two do not. Each is named in its domain file (`agents.md:89` and `:138`, `git-and-hosting.md:36`), which a tester touching that domain reads, so nobody is misled into a copy. I propose no story: moving them is churn, and a pointer line would be one more documentation story on a feature of tests.
- Still open, carried over from A0001 and A0002, none proposed again:
  - the docstring of `tests/settings_support.py` names only the environment, not `raising`;
  - the `make duplicates` baseline lags behind `main`: `5 new, 33 known, 3 gone` in S0012's coder entry, all in `factory.adapters`. This is for the human;
  - the uncovered lines `recovery.py:126` and `:200` and `stage.py:467` (out of scope, decision 11). They are still listed as missing in this run's coverage table.

## 5 Documentation as a whole

I read `docs/project-guide/README.md` from the top, through *Shared test helpers* into *Errors*.

- No contradiction. The new opening sentence about fixtures matches the sentence before it about modules. The `conftest.py` line keeps S0011's one-line form, and every other helper line is unchanged.
- `work_item` appears twice, once in each conftest, and the handlers' line says how the two differ. That is the one ambiguity the section could have had.
- `CLAUDE.md` (*Tests*) still names only `tests/conftest.py` for shared fixtures. The guide now also names the handlers' conftest. These are two places, not a contradiction. `CLAUDE.md` is the human's file in any case.
- The remark on the stand-ins under `tests/adapters/` is under check 4.

## 6 Decisions taken for the human

`feature.md`'s decisions 1 to 14 are unchanged. A0001 listed them, and the human accepted that report by merging it. Two items still have no recorded answer: decision 4 (the three domain guards stay), which remains a recommended answer, and the S0003 time-zone survivor ("equivalent in a container that runs in UTC"), which has no decision in `feature.md`.

New with S0012:

1. The opening paragraph now asks every story that adds a fixture to either conftest to name it through its docs criterion. As with A0002's item 1 for modules, this puts the duty on whoever writes the story, and no check enforces it. The alternative is still a structural test that compares the list with `tests/`. S0011's and S0012's testers rejected it because their Interfaces excluded a test module.
2. S0012's documenter kept each conftest's fixtures on one line, grouped by use ("Every test", "Doubles and time", "Git", ...), because the story's smoke test reads a single line. The line for the root conftest is now long. One line per fixture would read better, but it would break that smoke test's form.
3. S0012 is a third override of `feature.md`'s "every story's docs criterion is `none`", as an acceptance follow-up. `feature.md` was not changed, since it is the human's.

Earlier tests changed: none. S0012's reviewer confirmed that the diff changes, renames or deletes no test file. No finding.

## 7 Slow checks

Nothing beyond `make check` applies here (`make mutants` is check 3). `make duplicates` is a record and was not run again here (check 4).

Disk: the Disk now line (`/work` 0.5 GB used, `/state` 0.0 GB, `/tmp` 0.0 GB, 970.1 GB free on each) equals the previous record line, which was also taken at an acceptance. No growth, as expected from a story that changed only documents.

From `.reports/junit.xml` of my `make check` run (6,094 tests, 453 s of test time on every core):

- The slowest tests are still the adapters' time-limit tests, none of them the feature's: `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` at 5.0 s, `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` at 5.0 s, and `test_opencode_sudo_time_limit` at 4.5 s twice.
- The feature's 23 modules took 5.4 s together in the smoke test.

## 8 Cost

All twelve stories: 84 runs, 54.0 min, 451 turns, 1,611,289 tokens in (8,029,688 more from cache), 148,292 out, $15.16. A0002 counted 78 runs, 50.7 min and $14.35 for S0001 to S0011.

- S0012 took 6 runs, the minimum: $0.80 in 3.3 min. It sits beside S0010 ($0.69) and S0011 ($0.83) as one of the feature's cheapest stories.
- Its tester, coder and reviewer found an empty diff by design, about $0.39 of its $0.80. As A0002 said, this is the pipeline's fixed cost for a story whose only change is in the documents.
- The outliers are still the ones A0001 named: S0001, S0002 and S0009 took 10 runs each, because of review rounds over copied helpers. S0009 was the costliest at $1.84.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

None. The one remark (check 4, the stand-ins under `tests/adapters/`) is already documented in its domain files and does not justify a story.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: none. Since A0002, one story was archived. S0012 changed only 5 lines of `docs/project-guide/README.md`, within its Description: the guide now names all 25 root conftest fixtures, a new line names the 5 fixtures of the handlers' conftest, and the opening paragraph gained one sentence. It touched no `src/`, `tests/` or other document.
   2 Feature smoke test: green. On a throwaway copy, the feature's 23 modules pass (88 passed). Five hand-made breaks (S0002, S0003, S0005, S0007, S0009) each turn their story's module red; with A0002's four, every test story has now had one break caught. The guide's recovery subjects match the code, every one of the 37 helper modules has its own line, and 0 of the 30 conftest fixtures are missing. All 30 fixture descriptions match their docstrings. `make check` green (99.14 %).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0012's stages noticed nothing new. My own remark: three shared stand-ins live in `tests/adapters/`, not at the root that the section's rule names. Each is documented in its domain file, so no story. Still open and not proposed again: the `tests/settings_support.py` docstring, the `make duplicates` baseline lagging behind `main` (5 new, all in adapters), and the uncovered internal-guard lines.
   5 Docs: no contradiction. The handlers' line tells its `work_item` apart from the root's. `CLAUDE.md` naming only `tests/conftest.py` for shared fixtures is two places, not a contradiction.
   6 Decisions: feature.md's decisions 1 to 14 are unchanged. Decision 4 and the S0003 UTC survivor still have no recorded answer. New: keeping the fixture list current is the story writer's duty, and no check enforces it. Each conftest's fixtures stay on one line, which is now long. S0012 is a third override of "docs criterion `none`". No earlier test changed.
   7 Slow checks: nothing beyond `make check`. Disk is unchanged since the previous acceptance record. The slowest tests are the adapters' time-limit tests at 5.0 s; the feature's 23 modules take 5.4 s together.
   8 Cost: 84 runs, 54.0 min, $15.16 for the 12 stories. S0012 cost $0.80 in 6 runs, about half of it the empty-diff walk through the stages. S0009 is still the costliest at $1.84 in 10 runs. 0 questions to the human, 0.0 h waited.
