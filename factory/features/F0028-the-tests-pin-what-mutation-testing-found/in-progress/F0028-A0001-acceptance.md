---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 321
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T02:56:09.662793Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T03:05:27.341161Z'
  stage: acceptance
  run: c908bf64217d465c8a8e8c7fc633f015
stories: [F0028-S0001, F0028-S0002, F0028-S0003, F0028-S0004, F0028-S0005, F0028-S0006, F0028-S0007, F0028-S0008, F0028-S0009]
outcome: null
---

# Acceptance of The tests pin what mutation testing found

## Recommendation

accepted. All nine stories delivered what `feature.md` asked for: every test module the Scope names exists, and none of them changed anything under `src/`. The feature smoke test broke one pinned rule per story in a throwaway copy, and each break turned its story's tests red. `make check` is green. What the stories left behind is minor: two gaps in the project guide, proposed as stories S0010 and S0011, and a few small notes in tests. None of it is a broken promise.

## 1 Scope

None. Every Scope line has its story, and the files it names exist on `main`: 23 new test modules (88 tests) and the three new shared modules `tests/acceptance_support.py`, `tests/evaluation_support.py` and `tests/tick_support.py`. No story went outside the Scope. The nine merges (#312 to #320) change only `tests/` and the stories' own files. Nothing under `src/`, `docs/`, `README.md`, the `Makefile` or `pyproject.toml` changed, as *Out of scope* and *The human's changes* require. The Goal ("the change that breaks one of these rules now turns a test red") is reached for the samples in check 2. The full proof, a hand run of mutmut over the feature's 25 modules, is the human's, as `feature.md` says, and it has not been run here (check 3). Two Interfaces no longer match what was built: S0001 and S0009 say "No earlier test changes", but each ended up moving a helper under the standing leave after a review finding (check 6). The story text was not rewritten for that. It is a small blemish in the archive, not a scope gap.

## 2 Feature smoke test

The feature's purpose is that tests now pin behaviour that mutants left alive. So the walk-through has two parts. First it runs the feature's 23 test modules, plus the 7 earlier modules whose helpers were moved, against a copy of today's `src/`. Then it applies, in a fresh copy each time, one hand-made break of a rule that each story pins, and runs that story's test module. This is not mutmut and not `make mutants`. It uses the repository's own `.venv` Python with `PYTHONPATH` set to the copy, and it changes nothing in the checkout. The script was `$TMPDIR/smoke/feature-smoke.sh`, in this run's own temporary folder, which the factory removes. Beside it was a small `replace.py` that replaces a text occurring exactly once.

Command: `bash "$TMPDIR/smoke/feature-smoke.sh" /work/checkout`

```
== unchanged code: the feature's 23 test modules and the 7 earlier ones whose helpers moved
   factory imported from the copy: w/src/factory/__init__.py
   265 passed in 9.93s
== S0001 breaks domain/settings.py: authority.rpartition("@") -> authority.partition("@")
   1 failed, 11 passed in 0.04s
== S0002 breaks domain/sections.py: [found.start + 1 : found.end] -> [found.start + 2 : found.end]
   1 failed, 5 passed in 0.05s
== S0003 breaks domain/acceptance.py: last_result = last_record(document, speaker=role, kind="result")
    after -> last_result = last_record(document, kind="result")
    after
   2 failed, 3 passed in 0.04s
== S0004 breaks domain/provider_limits.py: if seconds > 0 else None -> if seconds >= 0 else None
   2 failed, 2 passed in 0.04s
== S0005 breaks application/acceptance.py: "close recorded" -> "XXclose recordedXX"
   1 failed, 4 passed in 1.89s
== S0006 breaks application/recovery.py: {entry_kind} of stage {target.state.stage} recorded -> {entry_kind} of stage recorded
   3 failed in 0.48s
== S0007 breaks application/recovery.py: kind="expiry", n=str(expiry.number) -> kind="expiry", n=str(expiry.number + 1)
   2 failed in 0.33s
== S0008 breaks application/tick.py: self._stop("fetch_failed", str(error)) -> self._stop("fetch_failed", "")
   1 failed, 2 passed in 0.21s
== S0009 breaks application/preflight.py: {settings.agent_user or 'the factory user'} with the opencode -> {settings.agent_user or 'XXthe factory userXX'} with the opencode
   1 failed, 1 passed in 0.11s
```

Green: the unchanged code passes, and each of the nine breaks is caught by the story that targeted it. On the first run the S0003 break was refused, because its text occurs twice in `acceptance.py` (lines 269 and 330). I narrowed it to the line in `refusal_reason` and ran the script again; the output above is from that second run. `make check` was green on the committed state as I found it (`check: green`, coverage 99.14 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- `tests/settings_support.py:1`: the module docstring names only the environment, not the shared reader `raising` that S0001 moved there. The S0001 reviewer, documenter and smoke tester all noted it, and nobody fixed it. It is a one-line docstring in a test module, so it can wait for the next story that changes the module. No story proposed.
- S0002 imports `FORM`, `SMOKE` and the private `_state` from `tests/domain/test_story_form.py`, and `TICKS` from `tests/domain/test_sections.py`. Its reviewer chose this over a move under the standing leave. The repository already does the same in twelve other modules (for example `tests/application/test_cost_instance.py` imports `_launch` and `_settings`), so it is house style rather than a defect. No story proposed.
- S0006's documenter: no document names the recovery's crash and expiry commit subjects. `pull request opened` and `comments from the pull request` are in `docs/project-guide/watching.md` (lines 113 and 234). Proposed as S0010.
- S0007's coder: the coverage report leaves `recovery.py:126`, `recovery.py:200` and `stage.py:467` uncovered. Line 200 is the dead code of decision 11. Lines 126 and 467 raise the internal-guard messages that *Out of scope* leaves out (the `CannotHandle` of a missing expiry entry, and `_role_of`'s `ValueError`). No story.
- S0008: `tests/application/test_tick.py` keeps its own `Failing`, which takes no arguments, records `.events` and raises `RuntimeError`. It does something different from the shared `Failing`, so it is not a copy. S0009's coder: `tests/application/test_agent_run_probe_api_login.py:22` keeps its own `DIED`, the `claude -p` text rather than opencode's. Not a copy either.
- Every coder entry reports `duplicates: 5 new, 33 known, 3 gone`, and the reviewers of S0005 and S0009 noted that this cannot come from their diffs. I confirmed it with `make duplicates`. The new findings are four similar-code blocks between `factory.adapters.claude_runtime` and `opencode_runtime`, and an unused `ManualWaiter` in `src/factory/adapters/clock.py:45`. The ones gone are `ManualClock` and its `advance`, and `data` in `work_item_markdown`. So `security/duplicates-baseline.txt` lags behind `main`, which is outside this feature. For the human: update the baseline, or open a story on the runtimes' similar blocks.
- The cost of copied helpers (check 8): three stories each needed a review round because a new test copied a shared helper. Proposed as S0011.

## 5 Documentation as a whole

The feature changed no document, as its docs criteria said. Read for what it touches: `docs/operator-guide.md` (*Mutation testing by sweep*), `docs/project-guide/processes-and-checks.md` (*Mutation testing*), `docs/operator-playbook.md` and the latest entries of `docs/decisions.md` all say the same thing: no stage runs `make mutants`, and sweeps run on a fresh copy. The passages the documenters cross-read all match the behaviour the new tests pin: the password rule, the refusal reason, the board line, the stop details, the error-cap log line, the expiry key and the login hint. No contradiction found. Two gaps a newcomer would hit:

- (a) `watching.md`'s recovery step 4 gives no commit subject, while every other handler's subject is spelled out (S0010).
- (b) No section of the project guide lists the 35 shared helper modules at the `tests/` root. The guide names 11 of them, each in its domain, and none of the three this feature added (S0011).

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit:

1. Tests only: no story changes `src/` (decision 1).
2. Each criterion was re-checked against today's code with rebuilt mutants. `settings` line numbers are mapped to today's. `split("/", 2)` was found equivalent (decisions 2 and 9).
3. `story_form._item_text` 2 is equivalent (decision 3).
4. The three domain guards stay; two of them are pinned by S0004 criteria 8 and 9 (decision 4). This was a recommended answer, and no answer from the human is recorded.
5. Only new test modules; helpers move only under the standing leave (decisions 5 and 13).
6. Credential URLs are built by concatenation (decision 6).
7. How the stories were cut, with split points for S0004 and S0008 (decisions 7, 8 and 14).
8. Three application survivors are equivalent: `StageFinisher._description` 3, `AcceptanceService._waits` 6 and `_with_journal_section` 5 (decision 10).
9. The application's dead code stays (decision 11; the human, 2026-10-19: keep both).
10. `Tick`'s unused `status` parameter stays until the next story that changes `tick.py` (decision 12; the human, 2026-10-19: (a)).

From the stories:

11. S0003's Description declares `_work_item_line`'s time-zone survivor "equivalent in a container that runs in UTC". It is not among `feature.md`'s decisions or in its *Out of scope* list. It holds only while the container runs in UTC, so the human's hand run should expect it alive, and a host outside UTC would make it a real gap.
12. S0002's reviewer chose to import the constants from the earlier test modules rather than move them to a shared module (check 4).
13. S0009's tester split the login hint into `opencode_died(user)` and `opencode_sso_hint(user)`, because an earlier row checks the first sentence alone.

Earlier tests changed, each named by its reviewer with its leave:

- S0001: `tests/domain/test_settings.py` and `tests/settings_support.py`. Standing leave: `_raising` moved as `raising` after a review finding. `feature.md` did not foresee this.
- S0003: `tests/domain/test_acceptance_booking.py`. Standing leave, as decision 5 foresaw: `_document` moved as `report_of` to `tests/acceptance_support.py`.
- S0004: `tests/domain/test_evaluation.py`. Standing leave, as decision 5 foresaw.
- S0008: `tests/application/test_tick.py`, `test_tick_stale_branch.py` and `test_dispatcher.py`. Standing leave, as decision 13 foresaw.
- S0009: `tests/application/test_agent_run_probe_opencode.py` and `tests/probe_support.py`. Standing leave, after a review finding. Decision 13 said S0009 moves nothing.

No earlier test was changed without a named leave. No finding.

## 7 Slow checks

Nothing beyond `make check` applies here (`make mutants` is check 3). `make duplicates`, a record and not a check, gives `5 new, 33 known, 3 gone`, all of it in adapters this feature did not touch (check 4). Disk: the Disk now line (`/work` 0.5 GB used, `/state` 0.0 GB, `/tmp` 0.0 GB, 970.2 GB free on each) equals the previous record line, also written at an acceptance. No growth.

From `.reports/junit.xml` of my `make check` run (6,061 tests, 437 s of test time on every core):

- The slowest tests are the adapters' time-limit tests: `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` at 5.0 s, `test_claude_runtime_resume::...[resume ended by the time limit]` at 5.0 s, and `test_opencode_sudo_time_limit` at 4.5 s twice. None of them is the feature's.
- The feature's 88 tests take 7.8 s together. Its slowest module is `tests/application/test_acceptance_reviewer_role.py` (3.1 s for 5 tests), then `test_stall_edges.py` (1.3 s) and `test_after_agent_edges.py` (1.1 s).

## 8 Cost

66 runs, 45.9 min, 366 turns, 1,323,390 tokens in (6,849,791 more from cache), 125,641 out, $12.84 for the nine stories.

- Six stories ran six times each, between $1.04 (S0003) and $1.65 (S0008).
- Three stories ran ten times, each with one review round for a copied test helper: S0009 ($1.84, 7.2 min, the most expensive), S0002 ($1.66, 6.0 min) and S0001 ($1.58, 6.5 min). Those rounds cost about 12 of the 66 runs, and S0011 is meant to prevent them.
- S0008 is the costliest of the six-run stories, from its 1.3 million cached tokens: three modules plus a helper move across three earlier files.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human. The answers recorded in `feature.md` (decisions 11 and 12, 2026-10-19) were given before the stories started.

## Proposed stories

- `F0028-S0010-the-project-guide-names-the-recovery-s-commit-subjects.md`: `watching.md`'s recovery step 4 gets the crash and expiry commit subjects that S0006 pinned. These are the only handler subjects the guide does not name.
- `F0028-S0011-the-project-guide-names-the-shared-test-helpers.md`: the guide's index lists the shared helper modules at the `tests/` root, so that a tester finds them before copying one. Three of this feature's nine stories paid a review round for such a copy.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 2 stories proposed
   1 Scope: none. Every test module the Scope names exists (23 new modules, 88 tests, 3 new shared modules), and none of the nine merges changed `src/`, `docs/`, the `Makefile` or `pyproject.toml`. The Interfaces of S0001 and S0009 still say "No earlier test changes", though each moved a helper under the standing leave after a review finding.
   2 Feature smoke test: green. On a throwaway copy, the 23 feature modules and the 7 earlier modules whose helpers moved give 265 passed. One hand-made break per story turns its story's tests red, nine out of nine (not mutmut).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the stale docstring of `tests/settings_support.py`; S0002 imports constants and the private `_state` from earlier test modules, as twelve other modules already do; the recovery's crash and expiry commit subjects are named in no document (S0010); copied helpers cost three stories a review round (S0011); `make duplicates` reports 5 new findings in adapters that this feature did not touch, so the baseline lags behind `main` (for the human).
   5 Docs: no contradiction found. Two gaps in the project guide: no commit subject in recovery step 4 (S0010), and no list of the 35 shared helper modules under `tests/` (S0011).
   6 Decisions: `feature.md`'s decisions 1 to 14 are listed. Decision 4 is a recommended answer with no answer from the human recorded. S0003's time-zone survivor counts as "equivalent in UTC" without a decision in `feature.md`. Every earlier test that changed has its leave named by its reviewer.
   7 Slow checks: nothing beyond `make check`. Disk unchanged since the previous record. The slowest tests (about 5 s) are the adapters' time-limit tests. The feature's 88 tests take 7.8 s together.
   8 Cost: 66 runs, 45.9 min, $12.84. S0001, S0002 and S0009 took 10 runs each instead of 6 because of review rounds for copied helpers; S0009 cost the most ($1.84). 0 questions to the human, 0.0 h waited.
