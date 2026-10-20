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
