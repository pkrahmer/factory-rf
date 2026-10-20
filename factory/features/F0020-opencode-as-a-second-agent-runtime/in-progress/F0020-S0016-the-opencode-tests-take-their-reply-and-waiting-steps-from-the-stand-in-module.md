---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 340
comments_read: []
handed_over: null
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
