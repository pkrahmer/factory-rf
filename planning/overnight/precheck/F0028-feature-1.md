# Pre-check F0028, round 1: the feature, its human's changes and its decisions

I checked `F0028-the-tests-pin-what-mutation-testing-found` and its four stories against these sources:

- v1.1's roles and forms;
- `factory/pipeline.yml`, `CLAUDE.md`, the `Makefile` (`mutants`), `pyproject.toml` (ruff's `PLR2004` is ignored and `tests/**` has `S101` off);
- the sweep's report `planning/overnight/mutation-sweep-2026-10-19.md`;
- today's thirteen modules under `src/factory/domain/`.

The code moved since the drafts:

- F0022 is merged.
- F0023 is being built. Its Scope (`git`, `pipeline_definition`, `write_paths`, `confinement`, `contract`, `checks`, `known_results`, the application and wiring) touches none of F0028's thirteen modules.
- No backlog story of F0020, F0022, F0025 or F0026 changes those modules or the test modules S0003 and S0004 move helpers from.

The stories' results are in `F0028-S0001-1.md` to `F0028-S0004-1.md`.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 settings | accepted | none; edit 1 recommended ("each refusal" read as criterion 2's) |
| S0002 section edges | accepted | none |
| S0003 refusal and board | accepted | none |
| S0004 seven rules | accepted | none; edit 1 recommended (`resumed_result` wording) |

## What I ran

Throwaway containers of `factory-self-factory` (`--network none --cpus 1`, a copy with LF line endings, pytest on `PYTHONPATH`).

- **Every criterion as a prototype test, on today's code.** All rows pass, with exactly the values in the criteria. Decision 2's claim that the expected values are today's still holds after F0022's merge.
- **The two helper moves (S0003, S0004).** I made both. `test_acceptance_booking.py` and `test_evaluation.py` pass whole afterwards. A bare import from those modules fails, because `tests/domain` is a package, so the moves are needed.
- **`tests/domain` with every prototype in it, and every root-level test module.** Green, but for three environment failures that have nothing to do with these stories: the demo test (the copy had no `demo/`) and the two `test_tmp_path_reopening` rows, known from earlier pre-checks.
- **The rebuilt mutants of decisions 2 and 4, each applied alone to a copy of today's `src/`.** All 47 that the stories target are killed by the prototype of their story. Three survive, all equivalent:
  - `split("/", 2)` in `settings` (as decision 2 says);
  - `split("/")` without a limit (equivalent for the same reason);
  - `_item_text`'s `"XX\nXX"` joiner (decision 3).
- **Every smoke test.** Each prints exactly its `Expect:` lines.
- **detect-secrets 1.5.0, with the baseline's plugins and filters, over both features' story files and the settings prototype.** It reports nothing, and decision 6 holds. A literal `https://u@x:y@...` is not taken for basic auth, because the user part before the `:` holds an `@`. The basic-auth plugin itself works: a probe line with a plain `user:<value>@` was reported.

I did not run ruff or mypy on the prototypes. They were written for the check, not in the tester's final form.

## The human's changes

"None" is right. Every story writes only under `tests/`. The coder has nothing to change, and the documenter writes nothing. `make mutants` prints `mutants: no module under src/factory changed by F0028` and exits 0 (Makefile line 104), as the feature says, so the acceptance sees no score. The check after the feature (mutmut over the thirteen modules in a throwaway container) is the only place the kills show. Expect the survivors above, plus the guard at `acceptance.py:332`, whose mutant stays.

## Decisions

- **1, 5, 7:** confirmed. Tests only; new modules; the moves under the standing leave; S0004 is sized to split at criteria 7 to 9 if needed.
- **2:** confirmed. Every expected value is today's, and every targeted rebuilt mutant fails its row.
- **3:** confirmed. The `_item_text` joiner changes no finding: `make check` and `green` are found within one line, and `docs:` is read from the item's start.
- **4:** confirmed by the mutants.
  - `acceptance.py:332` is unreachable: `last_record` at line 330 raises first for a document without a state.
  - `evaluation.py:66` and `evaluation.py:228` are reachable. S0004's criterion 8 and the `none` row of criterion 9 now pin them, and both kill a mutant of their guard.
- **6:** confirmed by detect-secrets.

## Points for the human, with recommended answers

1. **The guard at `acceptance.py:332` (decision 4):** (a) keep it, its mutant recorded as equivalent; (b) a fifth story, "`refusal_reason` reads the state once" (`require_state(...)`, with a row that a document without a state raises). Recommended: (a). One branch is not worth a coder story.
2. **The check after the feature:** (a) run mutmut over the thirteen modules once all four stories are merged, as *The human's changes* says; (b) skip it. Recommended: (a). It is the only place the kills show. If mutmut numbers a mutant differently from the rebuilt ones, its `show` output settles it.
3. **The two recommended story edits** (S0001 edit 1, S0004 edit 1): (a) make them before starting the stories; (b) leave them. Recommended: (a). Neither blocks, and both remove a reading that two people would read two ways.

## Verdict

The feature is ready as drafted: no change to `feature.md`. The four stories are accepted at intake as drafted. Two one-line edits are recommended; their exact texts are in `F0028-S0001-1.md` (edit 1) and `F0028-S0004-1.md` (edit 1).
