---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 340
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T06:50:18.115344Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T06:50:18.121511Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T06:50:48.639266Z'
  stage: intake
  run: 1ccb9a95cc1c4c2f8b18c2d3576c5ae8
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T06:51:09.726987Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T06:54:00.969251Z'
  stage: tests
  run: 017dbe23c36140e587951ca6d78a8e38
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T06:54:21.832751Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T06:56:37.354158Z'
  stage: doing
  run: 69b77b7222704902846825ffcd88754c
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T06:56:57.703171Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T06:57:36.764380Z'
  stage: review
  run: 8cb2159dd2e148b7be694d3336358a3c
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T06:57:57.825993Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T06:58:16.758120Z'
  stage: docs
  run: 750024268d8d459fb715560b3ba8527f
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T06:58:37.774868Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T06:58:53.796304Z'
  stage: smoke-test
  run: 73b6ab34029d498da157358562b75548
- number: 14
  speaker: factory
  kind: done
  at: '2026-10-20T07:09:28.492350Z'
  stage: approval
---

# The opencode tests take their reply and waiting steps from the stand-in module

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0020's opencode runtime tests write the stand-in's ordinary reply, a `step_start`, a result block in a `text` event and a `step_finish`, as a module constant of their own. Nine modules hold the same line, and S0013 moved one copy into `tests/adapters/opencode_stand_in.py` as `REPLY`. Its reviewer and coder both noted that the earlier copies remain. The step that prints a `step_start` and then waits `WAIT_SECONDS` is written inline the same way in three modules. A change to the stand-in's reply (a new required event field, for example) would now have to be made nine times, and a copy that is missed would test something else unnoticed. This story moves both steps to the stand-in module, under the standing leave of `CLAUDE.md` (*Tests*) to move a shared test helper, and adds one structural test that keeps them there. It changes no code, and no earlier test changes its name or what it checks.

## Interface

No module under `src/factory/` changes.

`tests/adapters/opencode_stand_in.py` (test helper) holds the shared steps:

```python
REPLY_EVENTS: str  # stdout(step_start(), text(result_text()), step_finish())
REPLY: Step        # Step(stdout=REPLY_EVENTS), as S0013 wrote it
WAITING: Step      # Step(stdout_before_wait=stdout(step_start()), wait_seconds=WAIT_SECONDS)
```

- The earlier modules that hold their own copy drop it and import the shared name: `tests/adapters/test_opencode_confinement.py`, `test_opencode_left_out_tools.py`, `test_opencode_provider_limit.py`, `test_opencode_resumed_words.py`, `test_opencode_runtime.py`, `test_opencode_runtime_folders.py` and `test_opencode_runtime_launch.py`, and `tests/entry/test_wiring_opencode.py` (the reply), and `test_opencode_confinement.py`, `test_opencode_provider_limit.py` and `test_opencode_limit_wait_on_stderr.py` (the waiting step). A module that uses the reply only as `Step(stdout=REPLY)` may use `REPLY`; one that uses the text itself (in a `Step` with other fields, in `Played` of `tests/confine_support.py`, as a test parameter) uses `REPLY_EVENTS`. The imports a module no longer needs once its copy is gone (`text`, `result_text`, `step_finish`, `step_start`, `WAIT_SECONDS`) go with it. The reply's copies fall under the standing leave of `CLAUDE.md` (*Tests*), as copies of the shared `REPLY`. The waiting step has no shared copy yet, so its move has the feature's leave (`feature.md`, decision 19, S0016). Every test keeps its name and checks the same thing, and the tester's entry names each file it changed.
- New test module, at the `tests/` root beside `tests/test_shared_test_helpers.py` and in its style: `tests/test_opencode_shared_steps.py`. It searches every `*.py` under `tests/` except itself, and the texts it searches for are split so that it does not find itself.

## Acceptance criteria

1. One parametrized test. A search of `tests/` for each step's text finds it written in exactly one module, `adapters/opencode_stand_in.py`:
   - row `reply`: the text `stdout(step_start(), text(result_text()), step_finish())`;
   - row `waiting`: the text `Step(stdout_before_wait=stdout(step_start()), wait_seconds=WAIT_SECONDS)`.
   On the branch before the move, the `reply` row finds nine modules and the `waiting` row three, so both rows fail.
2. Every test of the modules named in the Interface keeps its name and passes. The tester's entry gives the number of test ids each module collects before and after the move (86 in all on `main` before the story), and says that the two sorted lists of ids are the same.
3. `make check` stays green.
4. docs: none. The change is to test helpers only. `docs/project-guide/` names no test constant.

## Smoke test

```bash
grep -rlF --include='*.py' 'stdout(step_start(), text(result_text()), step_finish())' tests | sort
```
Expect: one line, `tests/adapters/opencode_stand_in.py`

```bash
grep -rlF --include='*.py' 'Step(stdout_before_wait=stdout(step_start()), wait_seconds=WAIT_SECONDS)' tests | sort
```
Expect: one line, `tests/adapters/opencode_stand_in.py`

```bash
uv run pytest --no-cov tests/test_opencode_shared_steps.py 2>&1 | tail -1
```
Expect: a line that starts `2 passed`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: concrete. It names the stand-in module `tests/adapters/opencode_stand_in.py` with `REPLY_EVENTS`, `REPLY` and `WAITING`, the eight modules that drop their copies, and the new `tests/test_opencode_shared_steps.py`. No `src/` change. I checked the current state with grep: the reply text is written in nine modules (the stand-in plus the eight named), and the waiting step in three (`test_opencode_confinement.py`, `test_opencode_limit_wait_on_stderr.py`, `test_opencode_provider_limit.py`), as the story says. The stand-in already holds `REPLY` (line 309) and `WAIT_SECONDS`.
   Criteria: criterion 1 is one parametrized test with two rows (`reply`, `waiting`), each a search for an exact text with an exact expected module. Both rows fail before the move. Criterion 2 is the tester's entry (id counts and equal sorted lists), a report and not a test function, but the existing tests already cover each behaviour. Criterion 3 is `make check`. Criterion 4 is docs: none. The story adds no rule with a failing side. The only rule is the one-module search, and a row that finds more than one module is the failing side.
   Smoke test: the greps are runnable and each `Expect:` is checkable. The pytest command passes no `-q`, and `pyproject.toml` sets `addopts = "-q --strict-markers"`. At a single `-q` pytest prints its summary line, so the `2 passed` expectation can be met. A step in the stand-in module differs from the searched text (`over_budget` uses `stdout(*lines)`), so it does not make the stand-in match twice.
   Architecture: this is test helpers only, within `tests/adapters/`, `tests/entry/` and the `tests/` root. It follows the pattern of `tests/test_shared_test_helpers.py` (`modules_matching`, split texts). It uses the standing leave of `CLAUDE.md` (*Tests*) for the reply. Decision 19 of the feature gives the human's leave for the waiting step.
   Scope: within F0020 (the decision 19 entry for S0016 exists) and outside "Out of scope". No test changes name or meaning.
4. factory: started tests as self.
5. tester: I wrote the structural test and made the move myself. This story changes test helpers only, and under the standing leave of `CLAUDE.md` (*Tests*) only the tester may move them. So the branch is not left red: `make test` is green (49.1 s) and `make lint` is green. The coder has no code to write. What's left for them is `make check` (criterion 3), which also covers `mypy --strict` on the changed tests; I did not run the type check, as this stage says.

   Criteria to tests:
   - criterion 1: tests/test_opencode_shared_steps.py::test_each_opencode_step_is_written_in_the_stand_in_module_alone (rows `reply`, `waiting`). It uses `search_support.modules_matching` and leaves out its own module, and its search texts are split. Before the move a grep found the reply text in 9 modules and the waiting step in 3, so both rows would have failed. I did not run the test before the move. After the move, both smoke-test greps print only `tests/adapters/opencode_stand_in.py`.
   - criterion 2: no new test. The existing tests of the 9 modules keep their names, and `make test` is green. Test ids collected per module, the same before and after the move: confinement 4, left_out_tools 14, limit_wait_on_stderr 5, provider_limit 12, resumed_words 2, runtime 23, runtime_folders 2, runtime_launch 14, wiring_opencode 10. That is 86 in all. The two sorted lists of ids (from `pytest --collect-only`) are identical (`diff` printed nothing).
   - criterion 3: `make check`, for the coder and the factory.
   - criterion 4: docs: none.

   Files created: tests/test_opencode_shared_steps.py.

   Files changed:
   - tests/adapters/opencode_stand_in.py: adds `REPLY_EVENTS` and `WAITING`, and `REPLY` is now `Step(stdout=REPLY_EVENTS)`.
   - These modules drop their own `REPLY` and use the shared one. Each `Step(stdout=REPLY)` became `REPLY`:
     - tests/adapters/test_opencode_confinement.py
     - tests/adapters/test_opencode_left_out_tools.py
     - tests/adapters/test_opencode_provider_limit.py
     - tests/adapters/test_opencode_runtime_folders.py
     - tests/adapters/test_opencode_resumed_words.py (its copy was already a `Step`)
   - These modules use the reply text itself (a `Step` with `exit_status`, `Played`, a test parameter), so they now import `REPLY_EVENTS`:
     - tests/adapters/test_opencode_runtime.py
     - tests/adapters/test_opencode_runtime_launch.py
     - tests/entry/test_wiring_opencode.py
   - These modules import `WAITING` in place of their inline waiting step:
     - tests/adapters/test_opencode_confinement.py
     - tests/adapters/test_opencode_provider_limit.py
     - tests/adapters/test_opencode_limit_wait_on_stderr.py

   Imports that were no longer needed were removed. The leave for the reply is the standing leave of `CLAUDE.md` (*Tests*). The leave for the waiting step is the feature's decision 19, which the Interface cites.

   Left alone on purpose: `test_opencode_runtime.py` has a waiting step with a literal `wait_seconds=30`. It is not the searched text and not named in the Interface, so I did not change it.

   No module failed to import. No `src/` change.

   `lint`: lint: green (0.0 s)
   `test`: test: green (45.5 s)
6. factory: started doing as self.
7. coder: I changed no files. This story changes test helpers only, and the tester already made the whole move. Their entry lists it: `REPLY_EVENTS`, `REPLY` and `WAITING` now live in `tests/adapters/opencode_stand_in.py`, eight earlier modules (`test_opencode_limit_wait_on_stderr.py` among them, for the waiting step) import them instead of keeping copies, and the structural test is `tests/test_opencode_shared_steps.py`. Nothing under `src/factory/` changes, as the Interface says, so the doing stage had nothing to build.

   What I checked:
   - `make check` ends with `check: green` (`test: green (46.3 s)`, coverage 99.16 %). That includes `mypy --strict` over the changed tests, which the tester left for this stage.
   - The diff against `main`, outside `factory/`, touches only the 11 files under `tests/` that the tester's entry lists.
   - Both smoke-test greps print one line each, `tests/adapters/opencode_stand_in.py`.

   Main choice: I left the tester's move as it is and did not change any test, since a coder never edits tests. I rejected re-deriving or tidying the move. Refactor: I made no diff of my own, so there was nothing to refactor.

   Noticed, not touched: the tester's note still stands. `tests/adapters/test_opencode_runtime.py` keeps an inline waiting step with a literal `wait_seconds=30`. It is not the searched text and the Interface does not name it.

   The journal did not change the meaning of the task, so `## Description` is unchanged.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I checked:
   - Scope: only test files changed, 11 under `tests/`. Nothing under `src/` changed, and the diff adds no silencing marker.
   - Criterion 1: `tests/test_opencode_shared_steps.py::test_each_opencode_step_is_written_in_the_stand_in_module_alone` is one parametrized test with the rows `reply` and `waiting`. It uses the shared `search_support.modules_matching`, leaves out its own module, splits its search texts and expects exactly `["adapters/opencode_stand_in.py"]`. A row that finds more than one module is the failing side, and the grep counts in the tester's entry and the intake's entry (nine and three before the move) show that side. I ran a grep after the move: each text is written in full only in `tests/adapters/opencode_stand_in.py`.
   - Criterion 2: the tester's entry (journal 5) gives the test-id count of each module, 86 in all, the same before and after, and says the two sorted id lists are identical. Each replacement checks the same thing as before. `REPLY` is `Step(stdout=REPLY_EVENTS)` with the same event text, and `WAITING` is the same step that each copy wrote.
   - The Interface's choice between `REPLY` and `REPLY_EVENTS` is kept. `test_opencode_runtime.py`, `test_opencode_runtime_launch.py` and `test_wiring_opencode.py` use the text in a `Step` with other fields, in `Played` or as a parameter, so they import `REPLY_EVENTS`. Their remaining plain `Step(stdout=REPLY_EVENTS)` uses are allowed by the Interface's "may".
   - Criterion 3: the coder's entry (journal 7) records `check: green`.
   - Description, Interface and the docs criterion match what was built. A pre-existing literal `wait_seconds=30` step in `tests/adapters/test_opencode_runtime.py:218` was left out on purpose: it is not the searched text and the Interface does not name it.

   Earlier tests:
   - tests/adapters/opencode_stand_in.py: standing leave to move a shared test helper (`REPLY` now built from `REPLY_EVENTS`), and the feature's decision 19 (S0016, the human, 2026-10-20) for `WAITING`.
   - tests/adapters/test_opencode_confinement.py: standing leave (reply copy) and feature decision 19 (waiting step, row `time-limit`).
   - tests/adapters/test_opencode_left_out_tools.py: standing leave (reply copy).
   - tests/adapters/test_opencode_limit_wait_on_stderr.py: feature decision 19 (module constant `WAITING` removed).
   - tests/adapters/test_opencode_provider_limit.py: standing leave (reply copy) and feature decision 19 (row `limit-line`).
   - tests/adapters/test_opencode_resumed_words.py: standing leave (reply copy).
   - tests/adapters/test_opencode_runtime.py: standing leave (reply copy).
   - tests/adapters/test_opencode_runtime_folders.py: standing leave (reply copy).
   - tests/adapters/test_opencode_runtime_launch.py: standing leave (reply copy).
   - tests/entry/test_wiring_opencode.py: standing leave (reply copy).
10. factory: started docs as self.
11. documenter: I changed no files. The docs criterion says `none`, and the diff (11 files, all under `tests/`) changes test helpers only. It adds no behaviour, name or interface that a reader of the docs would need.

    Cross-read: I grepped `README.md` and `docs/` for `REPLY`, `WAITING`, `WAIT_SECONDS` and `opencode_stand_in`. The only live hit is `docs/project-guide/agents.md:138`, which says tests use `tests/adapters/opencode_stand_in.py` in `tmp_path` and never run the real `opencode`. That is still true after the move, so I found it current. The other hit is a historical line in `docs/runs/2026-10-12-overnight/night-log.md`. That folder belongs to the human, so I left it alone.

    Findings against the code: none. The diff matches the Interface, since nothing under `src/factory/` changed.

    Stale text I noticed that is not mine to fix: nothing related to this story. Both the tester and the reviewer note that `tests/adapters/test_opencode_runtime.py` keeps an inline waiting step with a literal `wait_seconds=30`. It is not the searched text and the Interface does not name it.

    I did not run `make check`, as the stage says when only documents change, and I changed none.

    `check`: check: green (not run again: passed on tree 1dd3e18ccca0 at 2026-10-20T06:55:35Z)
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: I ran the three smoke-test commands from the repository root, exactly as written and in order. All three met their `Expect:` line, and I have no findings.

    1. Reply text search:
    ```bash
    grep -rlF --include='*.py' 'stdout(step_start(), text(result_text()), step_finish())' tests | sort
    ```
    ```
    tests/adapters/opencode_stand_in.py
    ```
    Met. Expected one line, `tests/adapters/opencode_stand_in.py`, and that is the only line printed.

    2. Waiting step search:
    ```bash
    grep -rlF --include='*.py' 'Step(stdout_before_wait=stdout(step_start()), wait_seconds=WAIT_SECONDS)' tests | sort
    ```
    ```
    tests/adapters/opencode_stand_in.py
    ```
    Met. Expected one line, `tests/adapters/opencode_stand_in.py`, and that is the only line printed.

    3. Structural test:
    ```bash
    uv run pytest --no-cov tests/test_opencode_shared_steps.py 2>&1 | tail -1
    ```
    ```
    2 passed in 0.02s
    ```
    Met. Expected a line that starts `2 passed`: these are the two rows, `reply` and `waiting`.

    Against the acceptance criteria:
    - Criterion 1: commands 1 and 2 show that each step's text is now written only in `adapters/opencode_stand_in.py`, and command 3 shows that the two-row test passes.
    - Criterion 2 is a count of test ids that the tester's entry reports. The smoke test does not touch it and nothing here contradicts it.
    - Criterion 3 (`make check`) is the factory's gate, not part of the smoke test, so I did not run it.
    - Criterion 4 (docs: none) is not contradicted.

    Findings: none.
14. factory: done (pull request merged); cost: 6 runs, 4.8 min, 39 turns, 132704 tokens in (740509 more from cache), 13610 out, $1.27
