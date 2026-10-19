# The stories proposed on 2026-10-19: which files they touch, and the order to run them

These are the six stories that F0020-A0001 and F0026-A0001 proposed, waiting in the backlogs. F0025-S0004 was pre-checked before (`F0025-S0004-1.md`). This was checked against today's checkout, with F0022-S0001 merged and F0022-S0002 in progress.

## The files each story touches

| Story | `src/` | Tests | Docs |
|---|---|---|---|
| F0020-S0009 (run_streaming; rename to S0012) | none | new `tests/adapters/test_process_streaming_reads.py`; with its edit 2, `Recorder` moves from `tests/adapters/test_process_streaming.py` to `tests/process_support.py` | `docs/project-guide/processes-and-checks.md` |
| F0020-S0010 | none | four new `tests/adapters/test_opencode_*.py`; imports only | none |
| F0020-S0011 | none | none | `docs/operator-guide.md` (six passages) |
| F0026-S0002 | none | new `tests/entry/test_watch_main.py` (and `tests/application/test_watcher_main_ref.py` unless its edit 3) | none |
| F0026-S0003 | none | new `tests/application/test_claims_refusals.py` | none |
| F0026-S0004 | none | `tests/conftest.py`, eleven `tests/application/test_*acceptance*.py` modules, `test_tick.py`, `test_tick_disk.py`, `test_tick_stop_records.py`, `test_pipeline_loading_agents.py`, `tests/entry/test_watch.py`, `test_watch_acceptance.py`, `test_watch_own_claim.py` (with its edit 1, also a new `tests/test_shared_fixtures.py`) | none |

## Where two of them meet

- **F0026-S0004 and F0026-S0002.**
  - They share no file. But S0002's new module installs the agents "as `tests/entry/test_watch.py` does".
  - Before S0004 that is a copy of the autouse `_agents`, which the reviewer counts at round 0. S0004 also forbids that copy in its criterion 2, so S0002 run first would make S0004 change S0002's module, which S0004 does not list.
  - After S0004 the same words point to `installed_agents` of `tests/conftest.py`.
  - **So S0004 runs before S0002.**
- **F0026-S0003 and F0026-S0004.** S0003 uses the `definition` of `tests/conftest.py`, which exists already. Independent; either order works.
- **The three F0020 stories.** They share no file. S0009 and S0010 add test modules only. S0011 edits only the operator guide. Either order works; the order below follows the feature's numbering.
- **F0020 and F0026.** No file in common.

## Against F0022, F0023 and F0024

- **F0022-S0002 (being built now).**
  - It changes `src/factory/adapters/opencode_runtime.py` (`LEFT_OUT_TOOLS` in the tool mapping). It adds `tests/adapters/test_opencode_left_out_tools.py` on the same stand-in, which it imports and does not change.
  - It edits `docs/operator-guide.md` (*The agent files*, *The shipped agents and settings*, *The agent runs as a second user*), and `docs/project-guide/agents.md` (*The seven agents*, *The opencode runtime*).
  - F0020-S0010 adds tests only, and pins behaviour that S0002's change leaves as it is (the tools are not among its criteria). No conflict.
  - F0020-S0011 edits other passages of the same `docs/operator-guide.md`. Run it after F0022-S0002 is merged, so that its branch starts from the guide with S0002's text.
- **F0023 (drafted).**
  - Its scope is `git.py`, `pipeline_definition.py`, `write_paths.py`, `confinement.py`, the contract, `known_results.py`, `checks.py`, `boundaries.py`, `stage.py` and `wiring.py`, with their tests.
  - It uses the `boundaries`, `checkout`, `human` and `clock` fixtures of `tests/conftest.py` and changes none of them. None of the six stories touches these.
  - Running F0026-S0004 first gives F0023's new tests the shared `definition` and `installed_agents`, should they need them.
- **F0024 (drafted).**
  - Its scope is `mutants.py`, `check_mutants.py`, `inputs.py`, `check_duplicates.py`, `checks.py`, `claude/agents/reviewer.md` and `acceptance-reviewer.md`. No overlap.
  - After F0024-S0003 the reviewer reads a story's surviving mutants. For these six test-only and docs-only stories that report has nothing to say, so the order does not matter.

## The recommended order

All of them come after F0022-S0002 is merged, and before F0023. They are small, and S0004 gives F0023's new tests the shared fixtures.

1. **F0026-S0004.** The shared fixtures. Apply its edit 1 first.
2. **F0026-S0003.** As drafted.
3. **F0026-S0002.** Edit 1 (required: the one-argument rows of criterion 4); edit 2 is moot after S0004; edit 3 optional. The F0026 acceptance A0002 is due after these three.
4. **F0020-S0009, renamed to F0020-S0012** (its edit 1: the id S0009 is the deferred spend window's in `feature.md`). Edit 2 recommended.
5. **F0020-S0010.** Edit 1 (required: criterion 6 through the real `factory-confine`), edits 2 to 4 recommended.
6. **F0020-S0011.** Edit 1 recommended. The F0020 acceptance A0002 is due after these three.

Then F0023 and F0024 as planned.

The two features can also swap (F0020's three first). The only firm rules are S0004 before S0002, and S0011 after F0022-S0002.
