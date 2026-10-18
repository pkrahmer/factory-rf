# Pre-check F0021, round 1: the feature, its human's changes and its decisions

The feature `F0021-the-factory-records-what-the-human-did`, its four stories and the drafter's brief, checked against v1.1's roles, forms, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml`, `Makefile`, the code they touch, F0019's archived journals and cost records, and F0020's drafted stories (read only). The stories' own results are in `F0021-S0001-1.md` to `F0021-S0004-1.md`.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 the causes, the waits, the human line | accepted | three recommended edits; split recommended |
| S0002 the stop records on `main`, the refused tool calls | question (4) | fixes given; place in the tick and split for the human |
| S0003 the reviewer's notes and leave, the operator's rule | accepted | the tester's sentence and the lesson conflict, recommended |
| S0004 the records contract | question (3) | fixes given; the version rule for the human |

## Order and sizing

- The order S0001, S0002, S0003, S0004 is right: S0003's acceptance-reviewer sentence names S0001's facts line; S0004's schemas need S0001's and S0002's fields.
- Time is no risk: F0019's slowest runs took 6 minutes (tester) and 3 minutes (coder) against a 40-minute `time_limit`. Money is: the tester's budget is 2 USD, F0019-S0004's tester spent 1.50 USD on a smaller job, and S0001 and S0002 each give the tester 9 new modules and 17 behavioural criteria. Each splits along a seam with no shared code (S0001: the records' causes | the waits and the human line; S0002: the stops on `main` | the refused tool calls). Recommended: split both, six stories in this order: causes, waits and line, stops, refusals, texts, contract.
- One story touches another's tests: S0001 under decision 13, S0002 under decision 14. Decision 13 says "the two expected stall records" of `tests/application/test_stalls.py`; the file holds three (fix in `F0021-S0001-1.md`). Decision 14 is exact (`tests/adapters/test_claude_runtime_resume.py`, the `Write` denial).

## The human's changes

- Change 1 (`[tool.mutmut]`, the deselection of `tests/entry/test_contract.py::test_the_committed_schemas_are_the_generated_ones`) is on `main` (`pyproject.toml` line 134). mutmut 3.8.0 copies every file of `src/factory/`, the JSON schemas included, so the test would pass in its copy anyway; the line is harmless.
- Write paths: the coder's `src/*` and `claude/*` cover `src/factory/contract/*.json` and the agent texts; the tester's `tests/*`; the documenter's `README.md`, `docs/*`. `factory/stops.jsonl` is written by the factory process, which no write path confines. Nothing a stage writes is outside its role's paths. Correct as stated.
- Missing, the image: the agents and the factory's own code run from the image, not from the checkout. S0001's facts and post lines, S0002's records and S0003's texts take effect only after `make`/compose rebuilds `self` from a `main` that holds them. The feature names the rebuild only after S0002. Add after the numbered change: "After S0001, S0002 and S0003 are each merged, rebuild the image of `self` before the next story's run that should use them; S0003's texts reach the reviewer, the coder and the acceptance reviewer only through the rebuilt image."
- Recommended, a new numbered change 2, before S0004 is merged: a line in `CLAUDE.md`, *Checks*, so that every later coder knows why a schema test is red:

  ```markdown
  - The records contract: `src/factory/contract/*.schema.json` are generated from the models `factory.domain.contract.CONTRACT` names. A change to one of those models, its docstrings included, regenerates them with `uv run python -m factory.entry.contract` in the same story; the coder writes them through that command and never by hand, and the reviewer checks the contract's version rule (`docs/decisions.md`).
  ```

- Recommended for the human's own process: the session's push guard (`safe_to_push.sh`) fetches before it checks, and every planning push pulls first, since the factory now pushes `main` after a stop event (decision 1).

## The decisions

1. Stops on `main` (decision 1). The commits do not collide with the factory's own pushes: the publish pushes `main` before the evaluation, `git push` moves `origin/main`, and the archive, an acceptance's booking or a discard in the same tick check `main` out at the new `origin/main` and fast-forward. A running story's next stage start merges `main` cleanly (no branch holds `factory/stops.jsonl`); the reviewer's diff excludes `factory/`; `make secrets` on a branch reads only the files changed since the merge base, and on `main` the records hold nothing it flags (decision 2); `make mutants` selects commits by their `work item <feature>-S...` subject. The rule never to push between a merge and its archive concerns the session's planning pushes, and the factory's own push cannot fall between them, since the archive follows in the same tick. Three effects decision 1 does not name:
   - The place in the tick (S0002's point 2): drafted before the load and the restore, the publisher's `check_out(main)` discards a killed stage's leftovers before the restore can log them, and commits on a checkout not yet restored. Recommended: publish right after the restore, before the preflight; definition and restore stops then reach `main` once the tick gets past the restore.
   - The preflight's stale-stop rule: while `preflight_failed` stands, `_clear_stale_failing_stop` (`application/preflight.py`) clears a standing `main_branch_failing` when `origin/main` is a commit other than the failing one. The factory's own `stops recorded` commit is such a commit: recording `preflight_failed` clears `main_branch_failing` and writes a false `cleared` record, though `main` is still red; it is raised again once the machine's items pass. Recommended: accept it for now and say it in S0002's docs (operator guide, *The stamp and the probe of the main branch*: "a `stops recorded` commit counts as a new `main`: the probe runs again, and while the machine's items fail it clears `main_branch_failing`"); a later story may make the stale-stop rule ignore a commit that changes only `factory/stops.jsonl`. Not recommended now: a separate branch for the records (decision 1's rejected alternative), which would avoid all three effects but needs an orphan branch the git wrapper cannot make yet.
   - Every stop event costs one preflight `lint` probe (decision 1 says so) and one more merge commit in each running story's branch at its next stage start. A stop that flaps from tick to tick makes a commit per tick. Acceptable.
2. No detail in the published record (decision 2): right.
3. Two events per stop (decision 3): right; with the recommended place in the tick its sentence "A standing stop also reaches `main` without waiting for its end" holds for every stop raised after the restore, and the others reach it at the first tick past the restore.
4. No reason on crash or expiry (decision 4): right; the crash is found without its cause.
5. A wait ends at the next record the human spoke (decision 5). One more imprecision to name: a comment's record carries the time the factory copied it (`CommentCopier.append` stamps `clock.now()`), not the time the human wrote it, so a wait ends up to one tick late. Recommended: add that sentence to the decision and to S0001's docs line.
6. Only a question with `blocked` is a wait (decision 6): right.
7. One cause `question` for rules 1 and 2 (decision 7): right. Also worth a sentence: a close past the round cap records the round-cap question with `blocked: send_back`, since `ClosedHandler` blocks every question it records that way; the viewer cannot tell it from a send-back without a reason.
8. The refused tool calls (decision 8): right. Its last reason is nearly true only: a budget stop resumed into a `time_limit` keeps the first call's denials in the result, and the cost record still gives `None` by its end reason. Harmless.
9. F0020's waits as optional fields (decision 9): right; see the notes for F0020 below.
10. "From round 1 on" (decision 10): right, but the reviewer's pinned lessons still count a copied helper and split test functions as findings; the new paragraph must say that it wins (S0003's edit 2).
11. The added criterion goes through `doing` (decision 11): the pipeline allows it (`review` next `[docs, doing]`, `doing` next `[review, tests]`; doing has no `round_cap`, so the coder's `tests` counts no round). But the tester then gets the line `Mode: a test change the human approved` and a step 0 written for the human's answer; it will likely ask. S0003's edit 1 adds one sentence to `tester.md`. Also, an added criterion costs a round, so at round 2 the cap may still ask the human.
12. The operator guide pinned by the smoke test only (decision 12): right.
13. The leave of S0001 (decision 13): three stall records, not two (S0001's edit 1).
14. The leave of S0002 (decision 14): right.
15. The records contract (decision 15): place and the separate version are right. The version rule contradicts itself: the minor never rises, so it carries no information, and `additionalProperties: false` makes a validating reader refuse a newer record of the same version. Recommended: the minor rises for an added optional field or closed-set value (S0004's replacement text).
16. No validator library (decision 16): right; criterion 7 compares `required` and `properties` instead, and the four models already generate cleanly (checked).

## Where F0021 and F0020 touch, and the notes F0020's stories need

F0020 is built after F0021. Its drafted stories were written against today's code; after F0021 they need these notes (for the human to carry into F0020's stories, or for F0020's pre-check):

- F0020-S0001 (`CostRecord.login`, "its last field, after `instance`"): after F0021-S0002 the record's last fields are `instance`, `denials`, `denied_paths`; `login` goes after `denied_paths`, and the line's key order becomes `..., "instance", "denials", "denied_paths", "login"`. Its criterion 15 (`login` the line's last key) still holds. It changes `CostRecord`, so it regenerates `cost-record.schema.json` (F0021-S0004) and, by the recommended rule, raises the contract's minor.
- F0020-S0002 (`resumed_result` moves into `factory.domain.agent_runs`): it carries `permission_denials` as today; the new `PermissionDenial.path` (F0021-S0002) moves with it unchanged.
- F0020-S0004 (opencode's `permission_denials`, `PermissionDenial(tool=..., detail=...)`): after F0021-S0002 the model also has `path`. The story should fill it from the refused call's input, using the key opencode's own file tools use (check it against opencode-ai 1.19.3's events; its write and edit tools name it `filePath`, not `file_path`), and add a criterion for it; otherwise every opencode run records `denials` with an empty `denied_paths`.
- F0020-S0005 (`EndReason` and `StallReason` gain `provider_limit`): after F0021-S0001 `StallReason` lives in `factory.domain.journal` (`decisions` keeps it by assignment), so the value goes there; F0021-S0001's criterion 7 (every value of `StallReason` a row) then covers it without a change. `CostRecorder.complete` gives `denials` for a `provider_limit` run (the runtime replied); the story should say so in a row of its cost criterion. It changes `CostRecord` and the journal record's `reason`, so it regenerates `cost-record`, `work-item-state` and `acceptance-state` schemas.
- F0020-S0007 (the waits and `limit_wait`): optional fields left out when absent, as decision 9 says; a change to `CostRecord` regenerates its schema.
- The run record, the stall reasons and `permission_denials` are the three meeting points the brief names; none conflicts in meaning, only in field order and in the module that holds `StallReason`.

## Verdict

Feature accepted with edits: the human's change 1 is in place; add the image rebuilds to *The human's changes*, add the `CLAUDE.md` line as change 2 (recommended), fix decisions 13 and 15, extend decisions 1, 5, 7 and 11 as below, and decide the two splits and the place of the publish in the tick.

Edit, *The human's changes*, replace the paragraph "After S0002 is merged and the image rebuilt, expect one commit `stops recorded` on `main` after each stop that is raised or cleared (decision 1)." with:

```markdown
After S0001, S0002 and S0003 are each merged, rebuild the image of `self` before the next story starts: the factory's code and the agents' texts run from the image. After S0002 is merged and the image rebuilt, expect one commit `stops recorded` on `main` after each tick that records a stop raised or cleared (decision 1); pull `main` before you push to it.

2. Before S0004 is merged: in `CLAUDE.md`, *Checks*, a new bullet after the one on `make duplicates`:

   ```markdown
   - The records contract: `src/factory/contract/*.schema.json` are generated from the models `factory.domain.contract.CONTRACT` names. A change to one of those models, its docstrings included, regenerates them with `uv run python -m factory.entry.contract` in the same story; the coder writes them through that command and never by hand, and the reviewer checks the contract's version rule (`docs/decisions.md`).
   ```
```

Edit, decision 1, append a fourth bullet after "The cost: ...":

```markdown
   - Two more effects: a running story merges `main` at its next stage start once more for each such commit (always cleanly: no branch holds the file); and while `preflight_failed` stands, a `stops recorded` commit is a new `main` to the preflight's stale-stop rule, which then clears `main_branch_failing` although `main` is still red, until the machine's items pass and the probe raises it again. Accepted for now; a later story may make that rule ignore a commit that changes only `factory/stops.jsonl`.
```

Edit, decision 5, append: `A comment's record carries the time the factory copied it from the pull request, not the time the human wrote it, so a wait ends up to one tick late.`

Edit, decision 7, append: `A close past the round cap records the round-cap question under `send_back` as well, as the closed handler blocks every question it records.`

Edit, decision 11, append: `The tester, which then runs in the mode for an approved test change, writes the added criterion's test (S0003 adds that sentence to its step 0). An added criterion counts a round like any send-back, so the round cap may still ask the human at the next review.`

Edit, decision 13: as in `F0021-S0001-1.md`, edit 1. Edit, decision 15: as in `F0021-S0004-1.md`.
