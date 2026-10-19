# Pre-check F0023, round 1: the feature, its human's changes and its decisions

The feature `F0023-a-known-result-is-not-checked-again`, its two stories and the drafter's brief, checked against v1.1's roles and forms, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml` (ruff, mypy, pytest, `[tool.mutmut]`), the `Makefile`, `.gitignore`, `image/Dockerfile`, the plan's step 7 and "The time `make check` takes", the code the stories touch, F0020's and F0022's drafted stories and F0021's state (all six stories archived in `done/`, the acceptance open). Both stories were prototyped in a copy of the repository and the whole test suite run in a throwaway container of v1.1's image. The stories' own results are in `F0023-S0001-1.md` and `F0023-S0002-1.md`.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 the git wrapper names the tree, `not_read` | question (2) | four edits (two rows, the copied index, no second copy of `is_inside_checkout`) |
| S0002 a known passed result is not run again | question (4) | the coder stops on one unleaved test; nine edits |

## Order and sizing

- The order is right: S0002 keys on S0001's `work_tree_id` and `not_read`. Neither story needs a human's change before it.
- Time is no risk. `work_tree_id` costs 0.03 to 0.08 s on factory-rf's own checkout (1,431 tracked files, measured in a copy in a throwaway container; 0.075 s with factory-rf's `not_read`). S0002's tester carries the most work (five modules, 13 behavioural criteria, a three-stage run) at a 2 USD budget: it fits, with little room. No split.
- The leaves: decision 15 is exact for S0001 (in the prototype the two git-interface tests and the contract literal are the only earlier tests the story touches). It is wrong for S0002: `tests/domain/test_checks.py::test_fields_are_exactly_the_generic_seven` pins `CheckResult`'s fields and turns red, the only failure S0002 causes. Without a leave the coder ends with `question` (fix below).

## The measured times (`/state/records/project-commands.jsonl`, read-only, 305 lines, 2026-10-18 12:22 to 2026-10-19 00:13)

`check` passed 54 times, 45.9 s on average, 59.4 s at most (`test` 40.2 s of it; `secrets` 0.93 s on average, 2.5 s at most). `documents` 21 runs, 0.2 s on average, 0.3 s at most. `duplicates` 3.0 s. `lint` 0.1 s. The feature's figures (45.9 s, 0.9 s, 0.2 s) agree.

## The human's changes

- Write paths: correct as stated. The coder's `src/*` holds the regenerated schemas; the tester's `tests/*`; the documenter's `README.md` and `docs/*`. Neither story needs `claude/*` or `image/*`. No `Makefile`, `pyproject.toml`, `factory/`, `security/` or `.secrets.baseline` change, and no structural test, so `[tool.mutmut]` stays.
- Change 1, the leases: every stage stays within its lease. Docs: 40 + 15 + 3 + 2 = 60 of 60. Doing: 40 + 15 + 5 = 60. Tests: 40 + 5 + 10 = 55. The prototype's loader accepts the block; with `documents: {time_limit: 3}` it refuses with `role documenter at stage docs: 61 min exceed lease_duration 60 min` (seen). Against the measured times, `secrets` at 3 minutes and `documents` at 2 minutes leave a margin of about 70 and 400 times.
- Change 1, the order: right. After S0002 and the rebuild, since the running factory must know `not_read` before its definition uses it.
- Change 1, `not_read`: one fault. `make check` reads more of those paths than `make secrets`: `make lint` runs `ruff check .` and `ruff format --check .`, which read every Python file of the tree (`.py`, `.pyi`, `.ipynb`) outside `planning/` (`extend-exclude = ["*.md", "planning"]`). Seen in a copy: a `docs/example.py` and a `factory/features/F9/x.py` each gave ruff findings. With `docs/*` and `factory/features/*` left out, a documenter who adds `docs/example.py` with a lint fault gets a reused green `check`, and the fault reaches `main`; the next preflight's `lint` probe of `main` then stops the factory (`main_branch_failing`). Today only Markdown lies there (`docs/`: 5 `.md`; `factory/features/`: 30 `.md`, 25 `.jsonl`). Fix: leave out only those kinds (text below). Nothing else of `make check` reads the listed paths: `mypy` reads `src` and `tests`, `layers`, `sast` and `bandit` read `src`, pytest's `testpaths` is `tests`, and the whole suite passed in a copy from which `README.md`, `docs/`, `factory/features/` and `planning/` were removed (seen: the same five environment failures as with them). `README.md` is read by hatchling only when uv rebuilds the project, which it does when `pyproject.toml` changes, and that file is in the key. `session-logs/` is ignored and never in a tree; the entry is harmless.
- Change 2 (`CLAUDE.md`): right; the texts read well and no test pins `CLAUDE.md`'s *Checks* bullets.
- Change 3: right as a check, with one wording to match the fix: step 2's "changed only `README.md` or `docs/`" becomes "changed only `README.md` or Markdown files under `docs/`". The expected lines are what the prototype gives (`"duration_seconds":0.0`, `"reused"` the doing stage's `at` with its microseconds).

## The decisions

1. The key: right. Command, tree, definition, image; not the commit, not the stage. The image id is a fresh UUID written by the Dockerfile's last `RUN` (line 52), so any changed layer of a rebuild gives a new id, and a fully cached rebuild, which is the same image, keeps it.
2. `not_read` as a list left out, refused forms: right. `./docs/*` loads and never matches a git path (seen): it costs a run, never a silenced check, so no rule is needed for it.
3. The tree as the factory's commit would record it: right, and the copied index is needed for more than speed. A tracked file that a later `.gitignore` matches stays in the commit; an index started empty would leave it out of the key, and a change to it would then reuse a stale pass. Today factory-rf has no such file (seen); S0001's edit 3 pins it. "The tools stand behind the image" needs one precision: `.venv/*` and `~/.cache/*` are tool paths every agent may write, so an agent can change the installed packages `make check` runs with. That route exists today for every run of the factory's `check`, and a reuse returns only a pass the factory itself saw on the same tree, so the feature does not widen it.
4. What invalidates: right. One more input outside the tree, `make secrets` inside `check` scans the files changed against the merge base with `origin/main`. A moved `origin/main` that the branch merged changes the tree when it brought a read file, and otherwise leaves the branch's own changes the same set. Only the left-out files differ, and the docs stage's `secrets` scans them. So no secret scan is lost before the approval.
5. A failed result never reused, the last run deciding: right. A flaky test that passed is still reused on the same key until a run fails; that is the rule, and the operator guide should say it (S0002's criterion 15 does, in "the last run of a key decides").
6. Recorded as skipped: right.
7. A store of its own: right. `/state` is outside every agent's write paths and tool paths.
8. Checks and reports through `KnownResults`: right, but S0002 has no criterion for a report (S0002, edit 4). With factory-rf's definition, `duplicates` and the tests stage's `lint` have no `not_read`, and every stage changes the journal, so they will in practice never be reused. That costs 3 s and 0.1 s and needs nothing.
9. Only the factory's own runs: right.
10. `result_records` optional and last: right, but "after `stop_records`" is out of date once F0020-S0007 adds `Boundaries.waiter`, last (text below).
11. The twenty-fourth operation: right; F0020 and F0022 add no git operation (checked), so the count holds.
12. factory-rf's `not_read` and `secrets` at the docs stage: right about `secrets`, wrong in "`make check` reads the documents and the work items only through `make secrets`": `make lint` reads their Python files (above). Fixed with the list of change 1.
13. The template and the demos stay: right.
14. The records contract: right. The condition "If F0021-S0006 is not on `main`" is settled: S0006 is archived in `done/`. `RECORDS_CONTRACT` is `"1.0"` today; F0020-S0001 makes it `"1.1"` and S0005 `"1.2"`, so S0001 makes it `"1.3"`. The literal sits in `tests/domain/test_contract.py`, line 54 (and wherever F0020's tests pin it), which the leave covers.
15. The leaves: S0001's are exact. S0002's "none" misses `tests/domain/test_checks.py` (text below).
16. Where F0023 touches F0020, F0021 and F0022: right as far as it goes. Add F0020-S0007's `Boundaries.waiter` (decision 10). F0022-S0001's wiring line and S0002's sit side by side without overlap. No F0020 or F0022 story changes `CheckResult`, `StageFinisher`'s checks, the pipeline definition's models or the git interface (checked).
17. Testing: right; no story or smoke test makes a paid call.

## Can a reused check silence a check that should have failed?

- A file the command reads that `not_read` leaves out: yes, as drafted, through `make lint` and a Python file under `docs/` or `factory/features/` (seen). Closed by the list below. Tests read none of the listed paths (seen).
- A tracked file that `.gitignore` matches: no, once S0001 pins the copied index (its edit 3); a coder who starts the temporary index empty would open that route.
- Tools outside the tree: the image (its id), `uv.lock` (in the tree; `uv run` installs the locked versions), `.secrets.baseline` and `security/` (in the tree): no. The packages in `.venv` and the caches in `~/.cache`, which agents may write: an existing route of every run, not widened (decision 3).
- `origin/main` read by `make secrets`: no; the left-out files are scanned by the docs stage's `secrets` before every approval, as every path to the approval passes the docs stage.

## Where F0023 touches F0020, F0021 and F0022

- F0020: S0007's `Boundaries.waiter` (decision 10); S0001 and S0005 raise the contract to `"1.2"` before S0001 raises it to `"1.3"` (decision 14). No story of F0020 needs a note.
- F0021: all six stories are on `main`; S0003's `factory/stops.jsonl` is in factory-rf's `not_read`; S0006's schemas are regenerated by S0001. No note.
- F0022: S0001's wiring line beside S0002's; nothing else. No note.
- The project guide holds 1,903 lines today, and F0020's eight and F0022's two stories add to it before F0023. The documenter's lesson says to split a file before it grows past 2,000 lines, while the plan puts the guide's split by domain at step 8, after F0023. If the guide is past about 1,950 lines when F0023 starts, a documenter may split it on its own in S0001 or S0002.

## Points for the human, with recommended answers

1. factory-rf's `not_read` (the human's change 1): (a) leave out only the Markdown and JSON Lines files: `["README.md", "docs/*.md", "factory/features/*.md", "factory/features/*.jsonl", "factory/stops.jsonl", "planning/*", "session-logs/*"]`; (b) keep `docs/*` and `factory/features/*` and add `lint` to the docs stage's checks; (c) as drafted. Recommended: (a). It closes the route at no cost, and a Python file there, which nothing expects, then costs one run.
2. The leave for S0002 (`tests/domain/test_checks.py`): (a) give it; (b) carry the reuse outside `CheckResult`. Recommended: (a) (see `F0023-S0002-1.md`).
3. The copied index as part of the rule (S0001, edit 3): (a) pin it; (b) leave it as a speed note. Recommended: (a).
4. `is_inside_checkout` (S0001, edit 4): (a) move it into `pipeline_definition`; (b) accept a second copy. Recommended: (a).
5. The project guide's length: (a) look at its line count when F0022 is archived; past about 1,950 lines, build step 8 (the guide split by domain) before F0023; (b) leave it to F0023's documenter. Recommended: (a); a split is a docs-only story of its own, not a side effect of a docs criterion.

## Verdict

Feature accepted with edits: replace change 1's `not_read` and the reason in decision 12 (required: as drafted a reused `check` can pass a lint fault); give S0002's leave in decision 15 (required: the coder stops without it); update decisions 3, 10, 14 and 16 and change 3's wording.

Edit, *The human's changes*, change 1, the `check` line of the first code block, replace with:

```yaml
     check: {time_limit: 15, not_read: ["README.md", "docs/*.md", "factory/features/*.md", "factory/features/*.jsonl", "factory/stops.jsonl", "planning/*", "session-logs/*"]}
```

and in the paragraph "The reasons: ...", replace its first sentence "The reasons: `make check` reads none of those paths except through `make secrets`, which scans the changed files, the documents and the work item's journal among them." with:

```markdown
The reasons: `make check` reads those files only through `make secrets`, which scans the changed files, the documents and the work item's journal among them. Only Markdown and JSON Lines files are left out, because `make lint` (ruff over `.`) reads every Python file of the tree wherever it lies, `docs/` and `factory/features/` included; a Python file there costs one run.
```

Edit, change 3, step 2: replace "when the documenter changed only `README.md` or `docs/`" with "when the documenter changed only `README.md` or Markdown files under `docs/`".

Edit, decision 12, replace "`make check` reads the documents and the work items only through `make secrets` over the changed files." with:

```markdown
`make check` reads the documents and the work items' Markdown and JSON Lines files only through `make secrets` over the changed files; `make lint` reads every Python file of the tree, so factory-rf's `not_read` names only `.md` and `.jsonl` files there.
```

Edit, decision 15, replace the S0002 bullet with:

```markdown
    - S0002: `tests/domain/test_checks.py`, the test `test_fields_are_exactly_the_generic_seven`, renamed `test_fields_are_exactly_the_generic_eight`, whose expected set gains `"reused"`; it keeps what it checks. The stage tests run with `result_records` left at `None`, and no other earlier test pins `CheckResult`'s fields or a journal line of a reused result.
```

Edit, decision 3, append:

```markdown
The temporary index starts as a copy of the checkout's index, so a tracked file that `.gitignore` matches counts, as it does in the commit. `.venv/*` and `~/.cache/*` are tool paths that agents may write; that a changed installed package can change what `make check` does is true of every run today, and a reuse returns only a pass the factory saw on the same tree, so this feature does not widen it.
```

Edit, decision 10, replace "**`Boundaries.result_records` is optional and last**, as `stop_records` is (F0021-S0003):" with "**`Boundaries.result_records` is optional and last** (after F0020-S0007's `waiter`), as `stop_records` was (F0021-S0003):".

Edit, decision 14, replace "by F0021's decision 15. The pipeline definition's own" with "by F0021's decision 15: `"1.0"` today, `"1.2"` after F0020-S0001 and S0005, so `"1.3"`. The pipeline definition's own", and drop its last sentence ("If F0021-S0006 is not on `main` when S0001 starts, this part of S0001 falls away."): F0021-S0006 is archived in `done/`.

Edit, decision 16, append: "F0020-S0007 adds `Boundaries.waiter`, last; S0002's `result_records` comes after it."
