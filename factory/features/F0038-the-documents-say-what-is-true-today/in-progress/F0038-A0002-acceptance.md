---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 402
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-21T09:07:54.399366Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-21T09:12:57.106549Z'
  stage: acceptance
  run: 638d8c5a6d494858a52a9c87c10c40fc
stories: [F0038-S0001, F0038-S0002, F0038-S0003, F0038-S0004, F0038-S0005, F0038-S0006, F0038-S0007, F0038-S0008, F0038-S0009, F0038-S0010, F0038-S0011]
outcome: null
---

# Acceptance of The documents say what is true today

## Recommendation

**accepted.** This is the second acceptance of F0038. The first (F0038-A0001, merged) accepted S0001 to S0010 and proposed S0011 for the two leftovers its walk found (`(R29)` and `RepositoryUnsealed` in the operator guide) and three dated observations. S0011 is now merged, and the feature's walk over the real documents is green on all 28 checks, including the two that were red. `make check` and `make documents` are green. No finding has weight, and I propose no story.

## 1 Scope

None. Every Scope bullet of `feature.md` has its story in `done/`, as A0001 mapped them:

- `README.md`: S0002.
- `docs/operator-guide.md`: S0001, S0006, S0007, S0008.
- `docs/project-guide/`: S0003, S0004, S0010.
- `docs/decisions.md`: S0005, S0009.

S0011 is the one story beyond that list. A0001 proposed it and the human started it. It stays inside the Goal ("the operator guide names what the operator sees", "the project guide and the decision log point to nothing that left the tree") and inside S0007's kept names (feature decision 7). It changed only `docs/operator-guide.md` (`git diff --stat origin/main -- README.md docs src tests` is empty on this branch, and S0011's smoke tester saw only that file against its base). The Out of scope items are untouched. I read the code S0011's new sentence names: `src/factory/application/scheduler.py:101` writes `cloning the checkout again: {error}`, as the guide now says. The section it points to is the heading at `docs/operator-guide.md:104`.

## 2 The feature's smoke test

The walk reads the real documents the way a newcomer, an operator and an agent would. It checks:

- for the newcomer, `README.md` against `pyproject.toml`;
- for the operator, `docs/operator-guide.md` against `STOP_TABLE` and the two pipeline definitions;
- for the agents, the project guide against `src/factory` and `git log`;
- the decision log;
- `make documents`.

It is stdlib Python in `$TMPDIR/walk.py`, run with `python3 -I`. It extends A0001's walk with three more checks:

- the README's "An instance runs in the container";
- the absence of the made-up handler case;
- that every story id `agents.md` cites as a passage's source appears in a commit subject on `origin/main`.

My first runs went red only on mistakes in the walk itself, which I corrected:

- shell commands the operator types (`python -m factory.entry.health`) counted as module names;
- example ids (`F0001-S0001`, `FEATURE=F0012`) counted, although feature decision 6 keeps them;
- the title "nothing is left for v2" matched as "left for v2";
- a too-narrow context window around `` `feature F0001 is incomplete, not due` ``;
- one `STOP_TABLE` row built with `id=` was missed.

Each of these, read in context, is text the feature keeps on purpose.

Command: `cd /work/checkout && python3 -I "$TMPDIR/walk.py"; echo "exit $?"`

```
ok   README opens with what the factory is: 529 chars
ok   README's command table is pyproject's console scripts: 6 rows
ok   README says an instance runs in the container
ok   every document README points to exists, the playbook among them: docs/operator-guide.md, docs/project-guide/README.md, docs/decisions.md, docs/operator-playbook.md, CLAUDE.md, demo/
ok   operator guide's contents list is its ## headings in order: 39 listed, 39 headings
ok   operator guide opens with what it is
ok   operator guide has the init's own heading
ok   operator guide cites no planning code: []
ok   operator guide names no planning history or dated observation: []
ok   operator guide names only the four kept error classes: ['CannotHandle', 'HostingServiceError', 'PushFailed', 'SettingsInvalid']
ok   operator guide names no internal module outside a command the operator runs: []
ok   operator guide holds no made-up handler case
ok   each of the 15 stop ids of STOP_TABLE is in exactly one table row: {}
ok   guide: template and demo run under the write guard
ok   template/factory/pipeline.yml names .reports/* as the guide says
ok   demo/todo-service/project/factory/pipeline.yml names .reports/* as the guide says
ok   project guide's index names every module (132): []
ok   watching.md describes factory-health and the index names it
ok   agents.md points to the template's pipeline definition
ok   project guide names no planning code and no bare v1 feature id (example ids kept, decision 6): {}
ok   every story id agents.md cites as a passage's source is in a commit subject on origin/main (8): []
ok   decision log has the entry on v2's retirement
ok   the v2 entry names the open gap open and not planned
ok   every title the v2 entry cites is a heading of the log: []
ok   the replaced entry is renamed and the old title is cited nowhere
ok   no document says 'left for v2' outside the v2 entry and its title: []
ok   factory/v1/ is named only as gone: []
ok   make documents: documents ok
walk: 0 failed
exit 0
```

The two checks that were red at A0001 (`(R29)` and `RepositoryUnsealed`) are green now. My walk counts 132 modules (every `.py` under `src/factory` but the `__init__.py` files), where A0001's walk said 133. No module was added or removed under `src/factory` between A0001's merge (`0597f99e`) and `origin/main`, so the two walks count differently. Every module my walk counts is indexed.

`make check`, run in the foreground on the branch as I found it: `Total coverage: 99.14%`, `test: green (68.1 s)`, `check: green`.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

None new. S0011's coder, documenter and smoke tester each noted nothing ("Noticed, not touched: nothing"; "I saw no stale text outside this story's passages"; "Nothing is open"). The reviewer had no remarks beyond its findings. A0001 already collected and judged the noticed items of S0001 to S0010. The one it took up, S0006's dated observations, S0011 has done. The rest stand as A0001 judged them, each without a story:

- the handler sentence kept on purpose;
- the hyphenated stop ids in *The stops*, which belong to the human's S1;
- the "morning observation" lines, which are dated history in the decision log.

## 5 The documentation as a whole

None. I read the README, the operator guide's opening, its contents and the passages S0011 changed, the project guide's index and `agents.md`'s list of v1.1's own passages, and the decision log's v2 entry. S0011's new sentence agrees with the code and with the section it cites. Its three removals left whole sentences: the walk and S0011's smoke tester found no broken sentence. No story contradicts another. The README's six commands, its pointers and `make documents` are consistent with the code. The only example the README runs is `make check`, and it ran green.

## 6 Decisions taken for the human

The feature's decisions 1 to 11, as A0001 listed them, to accept or revisit:

1. The re-check on `main` of 2026-10-20 dropped what was already fixed.
2. Every story started after F0032-S0001.
3. The review's seven stories were cut into documenter-sized ones.
4. H6 is worded "open, not planned", for gap 3 only.
5. S0009 points the settled kill under `sudo` to its entry.
6. S0004 keeps the requirement numbers `CLAUDE.md` names (R5, R8), the agents' rule numbers and the example ids.
7. S0007 keeps four error names, `STOP_TABLE` and `read_settings`.
8. S0008 moved the detail forms rather than dropping them.
9. S0006 took L9 with M4.
10. The smoke-test commands.
11. The number and the name F0038.

New since A0001:

- **S0011's dated observations were removed.** The story's Description left the human free to strike that bullet if the occasions should stay as evidence. The bullet was not struck, so the three parentheticals are gone. They remain in git history.
- **`agents.md` cites v1-numbered story ids as provenance.** These are "(F0012-S0017)", "(F0016-S0002)" and others. F0012 and F0016 fall in v1's range F0001 to F0017, which S0004 removed as pointers. S0010 made a per-passage story id the form of that list on purpose, and the walk shows that all 8 ids resolve in commit subjects on `origin/main` (R4: git links work to work items through the commit subject). I read this as by design. If the human wants v1's range out of the guide entirely, that would be a story.
- **Defaults in S0011's journal.** The tester wrote no test, and the coder built nothing, because criterion 1 forbids changes under `tests/` and `src/`. No question was asked.

Earlier tests changed: none. S0011's reviewer states that the diff changes, renames or deletes no test file `main` already held. A0001 said the same for S0001 to S0010.

## 7 The slow checks

None beyond `make check`. The project offers `make duplicates` (S0011's coder recorded `0 new, 38 known, 0 gone`) and `make mutants` (check 3), and nothing else. The slowest of the 7062 tests in `.reports/junit.xml`:

- 11.5 s: `tests.adapters.test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[status-1-past-the-limit]` and `[sigkill-past-the-limit]`;
- 10.1 s: `tests.adapters.test_process_session::test_time_limit_of_a_make_target_ends_what_timeout_started[own-group]`, `test_process_the_kill_cannot_reach_does_not_hold_the_call[ended-in-between]` and `[may-not-signal]`.

`ROOMY_LIMIT` (ten seconds) accounts for all of them. The feature added no test.

Disk now and at the previous record (occasion: acceptance, A0001) are the same: `/work`, `/state` and `/tmp` each 968.8 GB free, 0.0 GB used. There is no growth, as fits a documents-only feature.

## 8 Cost

74 runs, 42.5 min, 371 turns, $11.24 for eleven stories, about $1 a story.

S0011 cost 6 runs, 2.9 min and $0.75, the minimum route with no rework. That is the difference from A0001's 68 runs, 39.6 min and $10.49. As A0001 reported, S0009 ($1.83, 10 runs) and S0007 ($1.66, 10 runs) stand out. In each, a smoke-test finding went through doing and review, which cannot write `docs/`, before the documenter fixed it. That pipeline question is the human's (`factory/pipeline.yml`).

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

None. The walk is green, and no story left an observation that nobody owns.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: none. Every Scope bullet has its story in `done/`. S0011, which A0001 proposed, stays within the Goal and changed only `docs/operator-guide.md`. Its new sentence matches `scheduler.py:101`, and it points to the heading at `docs/operator-guide.md:104`.
   2 Smoke test: green, all 28 checks of my walk over the real documents (`$TMPDIR/walk.py`). The walk covers the README against `pyproject.toml`, the operator guide against `STOP_TABLE` and both pipeline definitions, the project guide against `src/factory` and `git log`, the decision log, and `make documents`. A0001's two red checks (`(R29)` and `RepositoryUnsealed`) are green now. My first runs went red only on mistakes in the walk itself, which the report names. `make check` is green, with coverage at 99.14 %.
   3 Mutation testing: by sweep, not run here.
   4 Noticed items: none new. S0011's stages noticed nothing. A0001 already judged the earlier items, and S0011 did the one it took up.
   5 Documentation as a whole: none. No contradiction between stories, no broken sentence, and the README's commands and pointers hold.
   6 Decisions for the human: the feature's decisions 1 to 11. S0011's dated-observation bullet was kept, not struck. The v1-numbered story ids in `agents.md`, such as (F0012-S0017), are provenance by S0010's design: all 8 resolve in commit subjects. No earlier test was changed.
   7 Slow checks: nothing beyond `make check`. The slowest tests are the `sudo` time-limit tests at 11.5 s, set by `ROOMY_LIMIT`. Disk is unchanged since A0001's record: 968.8 GB free and 0.0 GB used on `/work`, `/state` and `/tmp`.
   8 Cost: 74 runs, 42.5 min, $11.24. S0011 took the minimum route: 6 runs, $0.75. S0009 and S0007 stand out at 10 runs each, as A0001 reported. 0 questions answered and 0.0 h waited.
