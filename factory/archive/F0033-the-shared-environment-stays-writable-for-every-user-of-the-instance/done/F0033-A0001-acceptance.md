---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 323
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T03:16:48.238554Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T03:21:01.445699Z'
  stage: acceptance
  run: 7e323492259f4332bf7d8d3186d941df
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-20T03:23:23.819244Z'
  stage: done
stories: [F0033-S0001]
outcome: accepted
---

# Acceptance of The shared environment stays writable for every user of the instance

## Recommendation

**accepted with stories.** The feature's promise holds. S0001's hook is on `main` and the human's change 1 is on `main` (`34e4d681`). `make check` is green as `agent` under umask `0002` with no umask in the recipe, and the feature smoke test shows that a reinstall inside `make test` now leaves the project's `dist-info` as `2775`/`664`, where the old recipe left `2755`/`644`. One finding is worth a story. The decision log's reasons for two of the three rejected fixes are the documenter's own guesses, and one of them is wrong. That misleads the next reader of the log, not a user of the factory.

## 1 Scope

None. The scope has three items, and S0001 covers all of them. `tests/conftest.py` gains `TESTS_UMASK = 0o022` and `pytest_configure()`, which calls only `os.umask(TESTS_UMASK)` (`tests/conftest.py:50-55`). `tests/test_tests_umask.py` is new, with criterion 1's test and criterion 2's four rows. The three documents were written: `docs/project-guide/processes-and-checks.md:31`, `docs/decisions.md:844-850` and `docs/operator-playbook.md:117-118`. Nothing outside the scope changed: no `src/`, and the `mutants` recipe keeps its `umask 022` (`Makefile:111`). The goal's "Done when" has three parts: the story is merged; the human's change 1 is on `main` (`34e4d681`, which removes the three lines exactly as `feature.md` gives them, except that the one-line replacement comment it named was not added); and `make check` is green (below). The human's change 2, the real check with two users in a throwaway container of the rebuilt image, is not in "Done when" and remains the human's. This run has only the user `agent` and no `sudo`, so the smoke test below checks one user.

## 2 Feature smoke test

The feature's purpose, end to end. A uv project in a setgid folder is synced under the instance's umask `002`. A comment changes in its `pyproject.toml`. Then `make test` runs from the repository's `test` recipe as it stands on `main` (its `uv run pytest` line, cut out of `Makefile`, without the xdist and coverage options), with the hook cut out of the repository's `tests/conftest.py`. For contrast, the same recipe runs with the `umask 022` that change 1 removed. The project uses uv's own build backend and the repository's pytest, because the run is offline and the agent's uv cache is empty. The modification times show that each `make` call reinstalled the project.

Command, from the checkout's root: `bash "$s/smoke.sh" "$PWD"`. The script lies in a `mktemp -d` folder and builds the project in another `mktemp -d`, removed on exit. It runs `umask 002`, `uv sync`, then `sed` on the comment and `make -s test`, then `sed` again and `make -s test-old`, printing `stat -c '%A %a %y %n'` of `demo-0.1.0.dist-info` and its `INSTALLER` after each step.

```
recipe:	uv run pytest -q --no-header --tb=short -p no:cacheprovider
after uv sync under 0002:
-rw-rw-r-- 664 2026-10-20 03:19:31.266067191 +0000 demo-0.1.0.dist-info/INSTALLER
drwxrwsr-x 2775 2026-10-20 03:19:31.266067191 +0000 demo-0.1.0.dist-info
1 passed in 0.00s
after make test (recipe on main), started under 0002:
-rw-rw-r-- 664 2026-10-20 03:19:31.305522851 +0000 demo-0.1.0.dist-info/INSTALLER
drwxrwsr-x 2775 2026-10-20 03:19:31.305522851 +0000 demo-0.1.0.dist-info
1 passed in 0.00s
after make test-old (recipe before change 1), started under 0002:
-rw-r--r-- 644 2026-10-20 03:19:31.550972046 +0000 demo-0.1.0.dist-info/INSTALLER
drwxr-sr-x 2755 2026-10-20 03:19:31.550972046 +0000 demo-0.1.0.dist-info
```

Green. Under the recipe on `main`, the reinstall is group-writable (`2775`/`664`), and the test inside still ran under `0o022` (`1 passed`, from its own assertion `umask == 0o022`). The old recipe reproduces the fault of 2026-10-19 (`2755`/`644`). The other half of the feature is that the seal still accepts the tests' checkouts without the recipe's umask. `make check` shows this, run as `agent` (uid 1001, group `factory-work`) under umask `0002` with the recipe on `main`: `test: green (46.0 s)`, coverage 99.14 %, `check: green`. The checkout's own `.venv/.../factory-0.1.0.dist-info` is still `factory:factory-work`, `2775`/`664`, after that run.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- The documenter (S0001, entry 11) asked for their one-clause reasons for the three rejected fixes in `docs/decisions.md:850` to be checked against the feature's decisions 1 and 2. The smoke tester (entry 13) passed the question on as open, and nobody answered it before the merge. Checked here. The `UV_NO_SYNC` reason matches the feature. The reason for repairing modes differs: the feature says it fixes the symptom, needs a new step as `agent`, and misses the factory's own `644` files. The shell-wrapper reason is wrong. A wrapper `uv run sh -c 'umask 022; exec pytest ...'` sets the umask after uv's sync, so "the fault would come back with the next recipe that calls `uv`" does not follow. The feature rejected it because a module run on its own would not get the umask. The entry also leaves out the reverse direction the feature's *Goal* names (the factory's `644` files, which an agent's `uv run` cannot replace). Proposed as S0002.
- The `Makefile`'s `mutants` recipe still comments `umask 022   # as for make test: ...` (`Makefile:111`), and `make test` no longer sets one. That is the human's file, and F0032's change 1 rewrites the recipe (feature decision 3). No story: it lies outside every write path.
- The coder (entry 7) recorded `duplicates: 5 new, 33 known, 3 gone`. This feature changed nothing under `src/`, so the new findings come from earlier work. They are not this feature's, but they are worth a look at the next baseline update.
- The reviewer (entry 9) made no remarks beyond the findings.

## 5 Documentation as a whole

The new guide paragraph (`docs/project-guide/processes-and-checks.md:31`), the decision entry (`docs/decisions.md:844-850`), the pointer to it in the sudoers entry (`docs/decisions.md:305`) and the playbook rows (`docs/operator-playbook.md:117-118`) agree with each other and with the code. With change 1 on `main`, they describe the current state. `processes-and-checks.md:175` (the mutants recipe sets `umask 022`) is still true. `README.md` and `docs/operator-guide.md` needed nothing, and the operator guide's sudoers text (lines 128-136) is still right. The one finding is the decision entry's *Rejected* reasons (check 4, S0002). No example stops working, and no section is missing.

## 6 Decisions taken for the human

From `feature.md`, for the human to accept or revisit:

1. The cause is the `Makefile`'s `umask 022` before `uv run pytest`. `UV_NO_SYNC` for agents and a repair of modes after every agent call were rejected.
2. The umask moves into `tests/conftest.py`'s `pytest_configure`, not a shell wrapper in the recipe. The hook restores nothing.
3. The `mutants` recipe keeps its `umask 022`. F0032's change 1 owns that recipe and may drop it.
4. The story changes nothing under `src/`, and the coder writes nothing. The tester's `tests/conftest.py` is the whole fix.
5. The leave to change `tests/conftest.py` beyond the standing leave: add `TESTS_UMASK` and the hook, and nothing else.

From the journals: no question was asked and no default was taken. The tester wrote the hook itself, in `tests/conftest.py`, under decisions 4 and 5. The documenter chose the reasons for the rejected fixes themselves and asked for a check (check 4). Change 1 on `main` dropped the three lines but did not add the one-line comment `feature.md` gave in their place. That is cosmetic and the human's.

Earlier tests changed: `tests/conftest.py`, under decision 5. The reviewer (entry 9) confirmed that the diff only adds `TESTS_UMASK` and `pytest_configure`. No earlier test was changed without a named leave.

## 7 Slow checks

The project offers nothing beyond `make check` today, except `make mutants`, which is left out (check 3). From `.reports/junit.xml` of this run's `make check` (6066 tests), the slowest are `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` and `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.01 s each), then the two `test_opencode_sudo_time_limit` rows (4.53 s each). None is this feature's. The feature's four child-pytest rows take 0.67 to 0.75 s each. Disk: no change between the previous record and now. Both show `/work` at 0.5 GB used and `/state` and `/tmp` at 0.0 GB, with 970.2 GB free each.

## 8 Cost

The one story cost 6 runs, 4.2 min, 34 turns and $1.05. By stage, from its `.costs.jsonl`: intake $0.07, tester $0.28, coder $0.15, reviewer $0.23, documenter $0.15 and smoke tester $0.17. The tester is the largest, as expected: it wrote both the hook and the tests, plus one red run and one check run. Nothing stands out. Human interventions: 0 questions answered, 0.0 h waited. No story needed the human. The documenter's request for a check (entry 11) was not a question and went unanswered (S0002).

## Proposed stories

- `backlog/F0033-S0002-the-decision-log-gives-the-feature-s-reasons-for-the-rejected-umask-fixes.md`: replaces the documenter's own guesses in the *Rejected* line of the new decision entry with F0033's reasons from decisions 1 and 2. One of the guesses is wrong. It also adds the reverse direction of the fault named in the feature's *Goal*.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 story proposed

   1. Scope: none. All three scope items come from S0001. The human's change 1 is on `main` (`34e4d681`). It removes the three lines but leaves out the one-line comment `feature.md` named in their place. Change 2, the check with two users, is the human's.
   2. Feature smoke test: green. In a uv project under umask 002, the recipe on `main` reinstalls the project's `dist-info` as `2775`/`664`, while the old recipe reproduces `2755`/`644`. The test inside ran under `0o022`. `make check` is green as `agent` under 0002 with no umask in the recipe.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the documenter's reasons for the rejected fixes in `docs/decisions.md:850` were never checked. One of them is wrong (the shell wrapper) and one differs from the feature (repairing modes); S0002. The `Makefile:111` comment "as for make test" is stale; it is the human's file and F0032 rewrites it. The coder's `duplicates: 5 new` comes from earlier work.
   5. Documentation: the guide, the decision log and the playbook agree with the code now that change 1 is in. The only finding is the decision entry's *Rejected* line (S0002).
   6. Decisions: the feature's decisions 1 to 5 are listed for the human. No question was asked and no default was taken. `tests/conftest.py` was changed under decision 5, and the reviewer confirmed it.
   7. Slow checks: there is nothing beyond `make check`. The slowest tests are the 5.01 s time-limit tests (opencode budget, claude resume); the feature's rows take 0.67 to 0.75 s. Disk is unchanged since the previous record.
   8. Cost: 6 runs, 4.2 min, $1.05; the tester was largest at $0.28, and nothing stands out. 0 questions, 0.0 h waited.
3. factory: done (pull request merged); cost: 1 runs, 4.2 min, 24 turns, 60305 tokens in (1122775 more from cache), 19573 out, $1.10
