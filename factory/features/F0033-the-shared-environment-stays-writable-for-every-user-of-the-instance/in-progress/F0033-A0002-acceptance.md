---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 327
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T03:49:23.368958Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T03:53:04.506285Z'
  stage: acceptance
  run: 8bfb64ea8e944afc9c5e29b08c27a8ee
stories: [F0033-S0001, F0033-S0002]
outcome: null
---

# Acceptance of The shared environment stays writable for every user of the instance

## Recommendation

**accepted.** The feature's promise holds. A reinstall that `make test` triggers, started under the instance's umask `002`, leaves the project's `dist-info` as `2775`/`664`. The tests still run under `0o022`, both under the recipe and in a module run on its own with `uv run pytest`. `make check` is green as `agent` under `0002`. The one finding of the first acceptance (F0033-A0001) was the decision log's *Rejected* reasons, and S0002 has fixed it. Every item that acceptance left open is now closed on `main`, and no new finding came up.

## 1 Scope

None. The scope's three items come from S0001, as A0001 found: the `pytest_configure` hook with `TESTS_UMASK = 0o022` (`tests/conftest.py:50-55`), `tests/test_tests_umask.py`, and the three documents. S0002 was proposed by A0001. It stays inside the feature: the only change on its branch is to the entry *The tests set their own umask, and uv syncs under the caller's* (`docs/decisions.md:844-850`), whose reasons now match F0033's decisions 1 and 2. That entry also gains the reverse direction from the *Goal*. All three parts of "Done when" are met. S0001 and S0002 are merged. The human's change 1 is on `main` (`34e4d681`), with the one-line comment `feature.md` named added in `09255392` (`Makefile:77`). `make check` is green (check 2). The night log (`docs/runs/2026-10-12-overnight/night-log.md`, 05:19) records the human's change 2, the real check with two users, as met. Nothing outside the scope changed: no `src/`, and the `mutants` recipe keeps its `umask 022` (`Makefile:112`, decision 3).

## 2 Feature smoke test

What the feature promises, end to end, as one user can check it here (`agent`, uid 1001, group `factory-work`, umask `0002`; there is no `sudo` and no second user). The script makes a uv project in a setgid `mktemp -d` folder, removed on exit, and syncs it under `002`. It writes a `Makefile` from the repository's own `SHELL`, `.SHELLFLAGS` and `.ONESHELL` lines and its `test` recipe's `uv run pytest` line (without xdist, coverage and JUnit). It copies `TESTS_UMASK` and `pytest_configure` out of the repository's `tests/conftest.py`, and adds one test that asserts `umask == 0o022`. Next it changes a comment in `pyproject.toml` and runs `make test`, then changes it again and runs `make test-old` (the same recipe with the removed `umask 022` before it), as a control. Last, in the repository, it runs `uv run pytest tests/test_tests_umask.py` under `002`: the module run on its own that decision 2 promises. The run is offline (`UV_OFFLINE=1`; the agent's uv cache holds no wheels). The project builds with `uv_build`, and the demo venv borrows the repository's pytest through a `.pth` file and a `pytest` shim. The modification times show that each `make` call reinstalled the project.

My first run left out the `Makefile`'s `.ONESHELL`, so the control's `umask 022` did not reach the next line and the control showed `2775`/`664`. That was a fault of the script, not of the feature, and the run below has the setting.

Command, from the checkout's root: `bash "$s/smoke.sh" "$PWD" 2>&1 | grep -vE '^ +Buil|^(Uni|I)nstalled'` (uv's build and install lines left out):

```
recipe:	uv run pytest -q --no-header --tb=short -p no:cacheprovider
after uv sync under 0002:
drwxrwsr-x 2775 2026-10-20 03:52:02.500150879 +0000 demo-0.1.0.dist-info
-rw-rw-r-- 664 2026-10-20 03:52:02.500150879 +0000 demo-0.1.0.dist-info/INSTALLER
1 passed in 0.00s
after make test (recipe on main), started under 0002:
drwxrwsr-x 2775 2026-10-20 03:52:02.537087316 +0000 demo-0.1.0.dist-info
-rw-rw-r-- 664 2026-10-20 03:52:02.537087316 +0000 demo-0.1.0.dist-info/INSTALLER
1 passed in 0.00s
after make test-old (recipe before change 1), started under 0002:
drwxr-sr-x 2755 2026-10-20 03:52:02.763736051 +0000 demo-0.1.0.dist-info
-rw-r--r-- 644 2026-10-20 03:52:02.763736051 +0000 demo-0.1.0.dist-info/INSTALLER
a module run on its own with uv run pytest, started under 0002:
5 passed in 1.95s
exit 0
```

Green. With the recipe on `main`, the reinstall is group-writable and the test inside still ran under `0o022`. The old recipe reproduces the fault of 2026-10-19. The module run on its own passes its five rows, the one under `0o022` among them.

The seal's half of the feature is that the tests' checkouts stay acceptable without the recipe's umask. `make check`, run as `agent` under `0002` with the recipe on `main`, shows this: `test: green (39.6 s)`, coverage 99.14 %, `check: green`. The checkout's `.venv/.../factory-0.1.0.dist-info` is still `factory:factory-work`, `2775` with `664` files.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

None of weight. S0002's entries leave nothing open. The coder noticed nothing (entry 7). The reviewer had no remarks beyond the findings (entry 9). The documenter found no stale text (entry 11). The smoke tester left nothing open (entry 13). A0001's noticed items are all closed on `main`:

- The `mutants` recipe's stale comment "as for make test": fixed by the human (`14e9fa75`); `Makefile:112` now reads `# the seal refuses a group-writable checkout`.
- The one-line comment that change 1 left out: added (`09255392`).
- The documenter's unchecked reasons: S0002.

The coder's record `duplicates: 5 new, 33 known, 3 gone` appears in both stories' entries. Neither story changed anything under `src/`, so these findings come from earlier work. They are for the next baseline update, not for this feature.

## 5 Documentation as a whole

None. These texts agree with each other and with the code:

- the guide's paragraph (`docs/project-guide/processes-and-checks.md:31`)
- its `mutants` sentence (`:175`)
- the decision entry (`docs/decisions.md:844-850`)
- the sudoers entry's pointer to it (`docs/decisions.md:305`, whose title matches)
- the playbook's two rows (`docs/operator-playbook.md:117-118`)
- the operator guide's sudoers text (`docs/operator-guide.md:128-136`)

The decision entry now gives both directions of the fault and F0033's own reasons for the three rejected fixes. `README.md` needs nothing. No example stops working and no section is missing.

## 6 Decisions taken for the human

From `feature.md`, for the human to accept or revisit:

1. The cause is the `Makefile`'s `umask 022` before `uv run pytest`. Rejected: `UV_NO_SYNC` for agents, and a repair of modes after every agent call.
2. The umask moves into `pytest_configure` in `tests/conftest.py`, not into a shell wrapper in the recipe. The hook restores nothing.
3. The `mutants` recipe keeps its `umask 022`. F0032's change 1 owns that recipe and may drop the line.
4. S0001 changes nothing under `src/`, and the coder writes nothing.
5. The leave to change `tests/conftest.py` beyond the standing leave: add `TESTS_UMASK` and the hook, and nothing else.

From the journals, no question was asked and no default was taken in either story. S0002's coder left the decision-log edit to the documenter, as `CLAUDE.md` assigns it. That is a rule, not a choice.

Earlier tests changed: `tests/conftest.py` only, in S0001, under decision 5, and A0001 confirmed it. S0002's reviewer (entry 9) found that its diff changes no test file. No earlier test was changed without a named leave.

## 7 Slow checks

The project offers nothing beyond `make check` today, apart from `make mutants`, which is left out (check 3). The slowest of the 6083 tests in `.reports/junit.xml` from this run's `make check`:

- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`, 5.01 s
- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`, 5.01 s
- the two `test_opencode_sudo_time_limit` rows, 4.53 s each

None of them is this feature's. The feature's four child-pytest rows take 0.63 to 0.75 s each. Disk is unchanged: the record now and the previous one (both `disk acceptance`) show `/work` 970.1 GB free with 0.5 GB used, and `/state` and `/tmp` 970.1 GB free with 0.0 GB used.

## 8 Cost

The two stories cost 12 runs, 7.0 min, 62 turns and $1.77 in all. S0001 took 6 runs and $1.05; its tester was the largest single run at $0.28, because it wrote both the hook and the tests. S0002 took 6 runs and $0.72, for a docs-only change. By stage: intake $0.07, tester $0.12, coder $0.12, reviewer $0.12, documenter $0.11, smoke tester $0.17. The tester, coder and reviewer had nothing to build or review, and together they cost $0.37, about half the story, much of it in `make test` and `make check` runs of about 55 s each. That is the pipeline's shape for a docs-only story, not a fault of the story. I mention it, but the pipeline definition is the human's. Human interventions: 0 questions answered, 0.0 h waited. Neither story needed the human.

## Proposed stories

None. No finding calls for a change.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed

   1. Scope: none. S0001 covers the three scope items. S0002, which A0001 proposed, brings the decision log's reasons into line with F0033's decisions 1 and 2 and adds the reverse direction. "Done when" is met: both stories are merged, change 1 is on `main` (`34e4d681`, its comment line added in `09255392`), and `make check` is green.
   2. Feature smoke test: green. Under umask 002, the recipe on `main` reinstalls a demo project's `dist-info` as `2775`/`664`, and the test inside ran under `0o022`. The old recipe (the control) gives `2755`/`644`. `uv run pytest tests/test_tests_umask.py` run on its own under 002 gives `5 passed`. `make check` is green as `agent` under 0002. My first run left out `.ONESHELL`, which spoiled the control; that was a fault of the script, fixed and run again.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: nothing new. S0002's entries leave nothing open, and A0001's noticed items are closed on `main` (the mutants comment in `14e9fa75`, the change 1 comment, the reasons in S0002). The `duplicates: 5 new` record comes from earlier work.
   5. Documentation: the guide, the decision log, the playbook and the operator guide agree with each other and with the code.
   6. Decisions: the feature's decisions 1 to 5 are listed for the human. No question was asked and no default was taken. `tests/conftest.py` is the only earlier test changed, under decision 5.
   7. Slow checks: there is nothing beyond `make check`. The slowest tests are the 5.01 s time-limit tests, and the feature's rows take 0.63 to 0.75 s. Disk is unchanged.
   8. Cost: 12 runs, 7.0 min, $1.77 in all: S0001 $1.05, S0002 $0.72. In S0002, a docs-only story, the tester, coder and reviewer had nothing to do and still cost $0.37; that is the pipeline's shape, not the story's fault. 0 questions, 0.0 h waited.
