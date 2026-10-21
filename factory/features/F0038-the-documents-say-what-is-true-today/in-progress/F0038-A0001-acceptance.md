---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 399
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-21T08:27:34.921258Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T08:35:48.563561Z'
  stage: acceptance
  run: 88ace239d80c4b93895d9fd2e373179b
stories: [F0038-S0001, F0038-S0002, F0038-S0003, F0038-S0004, F0038-S0005, F0038-S0006, F0038-S0007, F0038-S0008, F0038-S0009, F0038-S0010]
outcome: null
---

# Acceptance of The documents say what is true today

## Recommendation

**accepted.** Every Scope item of `feature.md` has its story in `done/`, and every promise of the Goal holds on `main`. The README and the operator guide open with what they are. The operator guide's contents list matches its 39 `##` headings. Each of the 15 stop ids of `STOP_TABLE` is in exactly one table row. The project guide indexes all 133 modules and names no planning code. No document says "left for v2", apart from the new entry that retires v2. `make documents` and `make check` are green. Two of the walk's checks found leftovers that the feature's Goal also covers but that its stories did not list: one planning code `(R29)` and one internal class `RepositoryUnsealed` in the operator guide. Neither misleads an operator, so one small documents story is proposed for them and for three dated observations that the stories noticed.

## 1 Scope

None. Each Scope bullet maps to its story: `README.md` → S0002; `docs/operator-guide.md` → S0001 (template and demo under the guard), S0006 (opening, contents, current rule, `### The init`), S0007 (class names, the hypothetical handler case), S0008 (one stop table); `docs/project-guide/` → S0003 (template pointer, `factory-health`), S0004 (planning codes, v1 ids), S0010 (v1.1's own passages in the shipped agents); `docs/decisions.md` → S0005 (superseded marks, `factory/v1/`, the header sentence on codes) and S0009 (*v2 is retired; nothing is left for v2*, the renamed entry *The project commands first ran as the factory's user; replaced*, the settled kill under `sudo`). No story goes outside the scope. Every story changed only `README.md` or `docs/`, and each reviewer and smoke tester confirmed an empty diff under `src tests image template demo claude`. The Out of scope items are untouched: L1 to L10, S1 to S5, the F0032 mutation passages, and the playbook. I read the code the stories cite: `pyproject.toml` `[project.scripts]` for the README's table, `src/factory/domain/stop_table.py` for the stop table, both pipeline definitions and Makefiles for the guard paragraph, and `src/factory/application/dispatcher.py` and `scheduler.py` for the seal. The documents agree with them.

## 2 The feature's smoke test

The feature's purpose is that a newcomer, an operator and an agent each read documents that are true today and point to nothing gone. I wrote one walk over the real files and the real document check (`$TMPDIR/walk.py`, stdlib only, run with `python3 -I`). It runs these checks:

- the README's opening and that its command table equals `pyproject.toml`'s scripts;
- that every document the README points to exists;
- that the operator guide's contents list equals its `##` headings, in order;
- planning codes and internal names in the operator guide;
- that every stop id of `STOP_TABLE` is in exactly one table row;
- the guard paragraph against the template and the demo;
- that every module under `src/factory` is named in the project guide's index;
- the decision log's v2 entry, its cited titles and "left for v2" across all documents;
- `make documents`.

Command: `cd /work/checkout && python3 -I "$TMPDIR/walk.py"; echo "exit $?"`

```
ok   README opens with what the factory is: 529 chars
ok   README has no build inventory
ok   README's command table is the console scripts: 6 rows
ok   every document README points to exists: docs/operator-guide.md, docs/project-guide/README.md, docs/decisions.md, docs/operator-playbook.md, CLAUDE.md, demo/
ok   operator guide's contents list is its ## headings in order: 39 listed, 39 headings
ok   operator guide's opening says what it is
ok   operator guide names no planning history
FAIL operator guide cites no requirement number CLAUDE.md lacks: ['(R29)']
ok   each of the 15 stop ids of STOP_TABLE is in exactly one table row: {}
FAIL operator guide names only the kept classes: ['RepositoryUnsealed']
ok   operator guide names no application, adapter or entry module: []
ok   guide: template and demo run under the guard
ok   both pipeline definitions name .reports/* in tool_paths
ok   project guide's index names every module (133): []
ok   watching.md describes factory-health
ok   agents.md holds no copy of the template's pipeline definition
ok   project guide names no planning code or v1 feature id: {}
ok   decision log has the entry on v2's retirement
ok   the v2 entry names the open gap 'open and not planned'
ok   every title the v2 entry cites is a heading of the log: []
ok   no document says 'left for v2' outside that entry
ok   the renamed entry exists and the old title is cited nowhere
ok   factory/v1/ is named only as gone (was/removed/tag)
ok   make documents: documents ok
walk: 2 failed
exit 1
```

The walk is red on two checks, and both are stricter than the feature's criteria:

- `docs/operator-guide.md:374` says "Nothing in it floats (R29):". This requirement number is not in `CLAUDE.md`. Only the decision log's header sentence resolves it, and the operator guide does not point there. The review of 2026-10-20 did not list it, and M6's part in the stories covered the project guide and the decision log only.
- `docs/operator-guide.md:475` says "A seal that does not hold is the same `RepositoryUnsealed` error as after an agent run." F0040-S0002 wrote this sentence after the review, so S0007's list of names did not include it. What the operator sees is the line `cloning the checkout again: <reason>` (`scheduler.py:101`).

Neither misleads an operator about behaviour, and both are proposed as F0038-S0011. Every promise the Goal names is green.

Separately, I checked that every section the documents cite by name in the operator guide exists, as a heading or a bold paragraph title: all of them resolve. Of the paths cited in backticks, the ones that do not exist are examples (`docs/a.txt`, `src/x.claude/a`), files the operator creates (`image/secrets/*`, `factory/agents/coder.md`), or dated history in the decision log (`factory/stages.yml`, `docs/project-guide.md`). None is a live pointer to something that left the tree.

`make check`, run in the foreground as I found the branch: `lint: green (0.2 s)`, `types: green (4.3 s)`, `layers: green (0.1 s)`, `sast: green (2.1 s)`, `secrets: green (0.2 s)`, `licenses: green (0.2 s)`, `Total coverage: 99.14%`, `test: green (66.2 s)`, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0004's documenter: `agents.md` cites the story ids "(F0021-S0005)", "(F0034-S0001)" and the v1 commit `f8bc9d2`. S0010 has since made per-passage story ids the form of that list, so these are now by design. No story.
- S0006's documenter: dated observations remain in the operator guide: "(seen at the first start of 2026-10-17 under Docker Desktop and Podman)" (line 275), and also "(seen at the first start in PowerShell)" (575) and "(tested on 2026-10-17)" (585). The review did not list them. They are taken into F0038-S0011, as a bullet the human may strike.
- S0007's documenter and reviewer: "The handlers of the human's acts ... are registered: every kind of event has a handler" still speaks of handlers. The criterion kept it on purpose (feature decision 7 and S0007's Description). No story.
- S0008's documenter: *The stops* writes ids with hyphens (`fetch-failed`), while the rest of the guide and the health status use underscores. The paragraph under the table says so, and it is the review's S1 question, which is the human's. No story.
- S0009, from intake, coder, documenter and smoke tester: `docs/decisions.md` still says "morning observation" at lines 320 and 519 (and "closed on 2026-10-20 by ..." at two places). These are dated entries of the log and are history, not pointers. Line 519's citation (operator guide, "A `time_limit` under `sudo`") resolves to a bold paragraph title at `docs/operator-guide.md:295`. No story.
- S0001, S0002, S0003, S0005 and S0010: nothing noticed.

## 5 The documentation as a whole

I read `README.md`, the operator guide's opening and its stop sections, the project guide's index and the decision log's header and v2 entry as a newcomer.

- No contradiction between stories. The README's six commands match the operator guide and `pyproject.toml`. *The stops* and *The stops of the tick* now say the same thing once: the second points to the first.
- The README's "`docs/operator-guide.md`: install, configure, the stops and what to do about each" matches the guide's own opening.
- The decision log's header sentence explains every code its entries use, R29 included.
- Gaps: the two leftovers of check 2, the planning code `(R29)` and the internal class `RepositoryUnsealed` in the operator guide, and the three dated parentheticals of check 4. All five are in F0038-S0011.
- No example that no longer runs: the README's `make check` ran green (its `uv sync` I did not run by itself; `uv run` synced the environment), and `uv run factory-check-story` ran on the proposed story (`ok`).

## 6 Decisions taken for the human

From `feature.md` (*Decisions taken for the human*), to accept or revisit:

1. Re-checked on `main` of 2026-10-20 and dropped what was already fixed: H5, and five of M5's six modules.
2. Every story started after F0032-S0001 was merged.
3. The review's seven stories were cut to ten documenter-sized ones: S0003 and S0004 split, S0007 and S0008 split, and S0010 folded in.
4. H6 is worded "Open, not planned". By the human's answer, only gap 3 (the clone's working folder and the environment git is started with) stays open.
5. S0009 also points the stale "Open: the kill of a timed-out agent under `sudo`" to its settling entry.
6. S0004 keeps the requirement numbers that `CLAUDE.md` names (R5, R8) and the agents' rule numbers (R10, R14, R15).
7. S0007 keeps `SettingsInvalid`, `CannotHandle`, `PushFailed`, `HostingServiceError`, `STOP_TABLE` and `factory.domain.settings.read_settings`.
8. S0008 moves, rather than drops, the detail forms that only the six-row table held.
9. S0006 takes L9 with M4, and also " (R2)" and "as before".
10. The smoke tests use `make documents | tail -n 1` and `git diff --name-only origin/main`.
11. The number and the name F0038.

From the story journals, defaults taken without asking (no question was asked in any story):

- S0001 to S0010: every tester wrote no test, because criterion 1 forbids changes under `tests/`. Every coder built nothing and left the docs criterion to the documenter.
- S0007, round 1: the coder confirmed the smoke tester's finding (a lost blank line joined two paragraphs). The coder chose not to end with `question` and passed the fix on. The reviewer then sent the work item to `docs`, not back to `doing`, because the coder's write paths do not cover `docs/`.
- S0009, round 1: the same route for the missing `Date:` line of the new entry. The documenter wrote `Date: 2026-10-21 (F0038-S0009).`
- S0009: the new entry's first closed gap reads "the project commands ran as the factory's user", where the criterion paraphrased "run". The smoke tester judged this no contradiction.

Earlier tests changed: none. Every reviewer entry states that the diff changes, renames or deletes no test file, so no leave was needed and none is missing.

## 7 The slow checks

The project offers nothing beyond `make check` today, apart from `make mutants` (check 3) and `make duplicates`. The coders recorded `duplicates` as `0 new, 38 known, 0 gone` throughout.

Slowest tests in `.reports/junit.xml` (6464 tests):

| Time | Test |
| --- | --- |
| 11.5 s | `tests.adapters.test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[status-1-past-the-limit]` |
| 11.5 s | `...[sigkill-past-the-limit]` (same test) |
| 10.1 s | `tests.adapters.test_process_session::test_process_the_kill_cannot_reach_does_not_hold_the_call[ended-in-between]` |
| 10.1 s | `test_time_limit_of_a_make_target_ends_what_timeout_started[own-group]` |
| 10.1 s | `test_time_limit_ends_every_process_of_the_session[run_streaming-own-group]` |

The `ROOMY_LIMIT` of ten seconds accounts for all of these. The feature added none.

Disk: now `/work 968.8 GB free, 0.0 GB used`. At the previous record (occasion: acceptance) it was `/work 968.2 GB free, 0.5 GB used`, and `/state` and `/tmp` went from 968.2 to 968.8 GB free with 0.0 used. There is no growth: free space rose by 0.6 GB and `/work`'s use fell by 0.5 GB. This fits a documents-only feature.

## 8 Cost

68 runs, 39.6 min, 345 turns, $10.49 for ten stories, about $1 a story.

Eight stories took the minimum of six runs each, between $0.74 and $1.02. Two stand out:

- **S0007:** 10 runs, 4.9 min, $1.66.
- **S0009:** 10 runs, 7.1 min, $1.83, the most expensive story.

Each had one rework round started by the smoke tester:

- S0007: the edit removed the blank line before "After three errors ...", which joined two paragraphs.
- S0009: the new entry had no `Date:` line.

In each case the round went smoke-test → doing → review → docs, which is four extra runs. The coder and the reviewer could only confirm the finding and pass it on, because only the documenter can write `docs/`.

For documents-only stories, a smoke-test finding takes two runs (doing, review) that cannot act on it. That is a pipeline question for the human (`factory/pipeline.yml` is the human's file, so I propose no story for it).

Human interventions: 0 questions answered and 0.0 h waited. No story needed the human.

## Proposed stories

- `backlog/F0038-S0011-the-operator-guide-names-no-planning-code-internal-class-or-dated-observation.md`: removes the operator guide's last planning code `(R29)` and the class name `RepositoryUnsealed`, replacing it with what the operator sees, and three dated first-observation parentheticals. This is the walk's two red checks and S0006's noticed item, in one documenter run.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed (F0038-S0011)
   1 Scope: none. Every Scope bullet has its story in `done/`, no story goes outside the scope, and every story changed only `README.md` or `docs/`.
   2 Smoke test: my walk over the real documents (in `$TMPDIR`) checked:
      - the README's opening and its command table against `pyproject.toml`;
      - the operator guide's contents list against its 39 headings;
      - that each of the 15 `STOP_TABLE` ids is in exactly one table row;
      - that all 133 modules are in the project guide's index;
      - the decision log's v2 entry and its cited titles;
      - "left for v2" across all documents;
      - `make documents`.
      Every promise of the Goal is green. Two checks stricter than the criteria are red: `(R29)` at `docs/operator-guide.md:374` and `RepositoryUnsealed` at `:475`. Both are taken into S0011. `make check`: green, coverage 99.14 %.
   3 Mutation testing: by sweep, not run here.
   4 Noticed items:
      - S0006 found dated first-observation parentheticals; I added them to S0011, as a bullet the human may strike.
      - The rest need no story: the story ids in `agents.md` are now by design, the handler sentence was kept on purpose, the hyphenated stop ids are the review's S1 question, and "morning observation" in the decision log is dated history.
   5 Documentation as a whole: no contradiction between stories. Every operator-guide section the documents cite by name resolves. The gaps are the five passages in S0011.
   6 Decisions for the human: feature decisions 1 to 11, plus the defaults in the story journals:
      - every tester wrote no test and every coder built nothing;
      - in S0007 and S0009, the reviewer sent round 1 straight to `docs`, not `doing`;
      - S0009 says "ran" where its criterion said "run".
      No earlier test was changed.
   7 Slow checks: there is nothing beyond `make check` today. The slowest tests are the `sudo` time-limit tests at 11.5 s and the `test_process_session` tests at 10.1 s, set by `ROOMY_LIMIT`. Disk shows no growth: `/work` went from 0.5 GB used to 0.0, with 0.6 GB more free than at the previous acceptance record.
   8 Cost: 68 runs, 39.6 min, $10.49.
      - S0009 ($1.83, 10 runs) and S0007 ($1.66, 10 runs) stand out. In each, the smoke tester found one formatting slip: a missing `Date:` line in S0009, a lost blank line in S0007.
      - Each fix took four extra runs, because a docs-only finding goes through doing and review, which cannot write `docs/`. That is a pipeline question for the human.
      - 0 questions answered, 0.0 h waited.
