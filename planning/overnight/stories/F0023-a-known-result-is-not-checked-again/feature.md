# A known result is not checked again

## Goal

After every doing and docs stage the factory runs the stage's project commands, above all `make check`, on whatever the work tree holds, even when it ran the same command on the same code minutes before. The docs stage is the plain case: the documenter cannot change code, yet the factory runs the full gate again on the coder's code. Measured first, from the journals of F0019 and F0021 (17 stories, F0021-S0005 still in progress; `main` at b52caa39, 2026-10-19): the factory ran its own `check` 51 times, and 23 of those runs were on code that an earlier passed `check` had already passed. That is every one of the 18 docs-stage checks, plus 5 doing-stage checks on a tree already passed (after a review or a send-back that changed no code, and once the tree of the story before, F0019-S0009, in the docs-only F0019-S0010). The comparison left out the work items' files (`factory/features/`), `README.md`, `docs/`, `planning/` and `session-logs/`, which no test reads. If only the work item's own files are left out, 5 of 51 repeat; if nothing is left out, none does, because every stage adds a journal entry. v1.1's own records put a factory `check` at 45.9 s on average (51 runs on 2026-10-18), so the 23 repeats are about 18 of 39 minutes. That is roughly one minute and one check per story, at no model cost; the agents' own `make check` runs inside their runs are not touched by this feature. This feature lets the factory skip a stage's project command whose passed result for the same input is already known. The input is a key: the command, the tree of the files the command reads, the pipeline definition and the image. A failed result is never reused. A project says per command which paths it does not read (`not_read` in its pipeline definition), so the engine learns no target names, no stage names and no paths. A skipped command is recorded as skipped, with the run it reused, in the journal and in a record per run; so no check is silenced, and the count of runs on one tree can be read from the records. It is for the operator who waits on the factory and for the measurement of the lever the plan names. Done when every story below is merged and `make check` is green. The real check is the human's change 3 after the feature: one ordinary story of factory-rf whose docs stage reuses the doing stage's `check`.

## Scope

- `src/factory/domain/git.py`: `TreeId` (S0001).
- `src/factory/application/git.py`: `Git.work_tree_id`, the interface's twenty-fourth operation (S0001).
- `src/factory/adapters/git_cli.py`: `GitCli.work_tree_id`, computed in a temporary index (S0001).
- `src/factory/domain/pipeline_definition.py`: `ProjectCommandDefinition.not_read` and its load rule (S0001).
- `src/factory/domain/contract.py` and `src/factory/contract/*.schema.json` (F0021-S0006's): the regenerated schemas and the records contract's minor version (S0001).
- `src/factory/domain/known_results.py` (new): `ResultKey`, `ResultRecord`, `definition_digest`, `known_result` (S0002).
- `src/factory/domain/checks.py`: `ReusedRun`, `CheckResult.reused`, `command_line` (S0002).
- `src/factory/application/boundaries.py`: the optional `result_records` (S0002).
- `src/factory/application/known_results.py` (new): `KnownResults`, which runs a stage's project command or reuses its known result (S0002).
- `src/factory/application/stage.py`: `StageFinisher` runs its checks and reports through `KnownResults` and writes each line with `command_line` (S0002).
- `src/factory/entry/wiring.py`: `result_records` at `<state directory>/records/known-results.jsonl` (S0002).
- The tests each story names, under `tests/`, and the earlier test modules named in decision 15.
- `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md`, from each story's docs criterion.

## Out of scope

- The agents' own `make check` runs inside an agent run (the coder's last one runs on the same tree as the factory's check right after it). The factory does not see those runs, and a result the agent could produce is not a known result (decision 9). That lever is for later, if the telemetry shows it is worth it.
- The preflight's probe of `main` (`lint`) and its stamp, which already remembers the probed commit: unchanged (decision 8).
- A positive list of what a command reads, a hash of the tools outside the image, and an expiry by age (decisions 2 to 4).
- The template's and the demos' pipeline definitions: they get no `not_read`, so their commands run as today (decision 13). A project opts in.
- Pruning `known-results.jsonl`: about five lines per story, never read by anything but the factory and the operator (decision 7).
- A counter, a report or a board column of the runs per tree: the records hold one line per run and per reuse, with the tree, so the count is a query (decision 6).
- Every paid call: no story and no smoke test makes one; the real check is the human's change 3.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The git wrapper names the tree a command reads, and the pipeline definition says what it does not read
- S0002: A stage's project command whose passed result is known for the same key is not run again

## The human's changes

Checked against `factory/pipeline.yml`: the coder writes `src/*`, `image/*`, `template/*` and `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. Both stories stay inside those write paths: the regenerated schemas under `src/factory/contract/` are the coder's. No new dependency, no `.secrets.baseline` entry, no `security/` change, no suppression marker, no `Makefile` or `pyproject.toml` change. No story adds a structural test that reads the source, so `[tool.mutmut]` stays as it is. What the feature needs outside the write paths is factory-rf's own pipeline definition and two sentences of `CLAUDE.md`:

1. After S0002 is merged and `self` is rebuilt (the running factory must know `not_read` before its pipeline definition uses it, or the next tick stops with `pipeline_definition_invalid`), one commit on `main`. In `factory/pipeline.yml`, the `project_commands` block becomes:

   ```yaml
   project_commands:
     # The gate; a passed result is reused while the files it reads, the pipeline definition and the image stay the same.
     check: {time_limit: 15, not_read: ["README.md", "docs/*", "factory/features/*", "factory/stops.jsonl", "planning/*", "session-logs/*"]}
     lint: {time_limit: 5}
     test: {time_limit: 10}
     duplicates: {time_limit: 5}   # similar and dead code against security/duplicates-baseline.txt, for the reviewer
     documents: {time_limit: 2}    # the four documents against the document check: a check of the docs stage only
     secrets: {time_limit: 3}      # detect-secrets over the files changed on the branch, the documents and journals that check's not_read leaves out
   ```

   and the `docs` stage becomes:

   ```yaml
     docs: {role: documenter, next: [smoke-test, doing], checks: [check, secrets, documents], round_cap: 2}
   ```

   The reasons: `make check` reads none of those paths except through `make secrets`, which scans the changed files, the documents and the work item's journal among them. So a reused `check` must not be the only scan of what the documenter wrote. `secrets` runs as its own command at the docs stage, with nothing left out, and stays cheap (0.9 s on average inside `check` on 2026-10-18). `documents` goes from 5 to 2 minutes (it takes 0.2 s) so that the documenter's 40 minutes plus 15, 3 and 2 stay within its `lease_duration` of 60. `factory/stops.jsonl` is in the list because the factory writes it on `main` (F0021-S0003), and a merge of `main` that brings only a stop record must not cost a `check`. `factory/pipeline.yml` itself is not in the list: it is read by no test, but a change to it changes the definition's digest anyway.

2. In the same commit, `CLAUDE.md`, *Checks*:
   - In the bullet on `make duplicates`, the last sentence, which names six targets, becomes:

     ```markdown
     The pipeline knows these seven targets (`check`, `lint`, `test`, `secrets`, `duplicates`, `documents`, `mutants`).
     ```

   - The bullet on the documenter becomes:

     ```markdown
     - The documenter runs `make check` only when it changed a file outside `README.md` and `docs/`: after changing only documents it ends without it, because the factory checks right after the docs stage: it runs `make check`, or reuses its passed result when nothing that `make check` reads has changed (`not_read` in `factory/pipeline.yml`), then `make secrets` over the changed files and `make documents`. Those are the gate.
     ```

3. The check after the feature, after change 1 and the rebuild of `self`: the next ordinary story of factory-rf (no extra cost; the plan's short smoke run). The todo demo's pipeline definition has no `not_read`, so a run there would show no skip.
   1. Let the story run to its docs stage as usual.
   2. Expected, when the documenter changed only `README.md` or `docs/`: the documenter's journal entry ends with three lines, `` `check`: check: green (not run again: passed on tree <12 characters> at <time>) ``, `` `secrets`: secrets: green (<seconds> s) `` and `` `documents`: documents ok ``. The tree and the time are those of the doing stage's `check`.
   3. In the container, `MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 tail -n 3 /state/records/known-results.jsonl` shows the docs stage's `check` line with `"reused"` set to the `at` of the doing stage's line, the same `key`, and `"duration_seconds":0.0`. `/state/records/project-commands.jsonl` has no `check` line for the docs stage.
   4. If `check` ran again although only documents changed, compare the `key` of the two `check` lines: another `tree` means a path outside `not_read` changed (`git diff --stat` between the two stage commits shows which); another `definition` means `factory/pipeline.yml` changed between them; another `image` means `self` was rebuilt between them. Each is the intended behaviour; only a tree that differs although no read file changed is a fault of the feature.
   5. After three or four stories, the count of `check` runs per tree, the most-run first (the operator guide's command from S0002's docs criterion), shows the lever as measured.

## Decisions taken for the human

1. **The key of a known result is the command, the tree it reads, the pipeline definition and the image** (`ResultKey`: `command`, `tree`, `definition`, `image`). `tree` is `Git.work_tree_id(not_read)`: the tree a commit of the work tree would record when the command starts, without the paths the command does not read. `definition` is the SHA-256 of the whole loaded pipeline definition's JSON. `image` is `InstanceSettings.image`, `None` outside the container. Not the commit: the checks run on the work tree before the result commit, `HEAD` is then the stage-start commit, and every stage's commit carries a new journal entry. Not the stage: the plan's rule, and a docs stage's `check` on the coder's code is the same input as the doing stage's. A result found under a key of another work item is reused too (F0019-S0010, a docs-only story, would have reused F0019-S0009's `check`), because the key holds everything the command reads. (S0001, S0002)
2. **What a command does not read is the project's to say, as a list of patterns left out (`not_read`)**, matched as write paths are (`matches_any`: case-sensitive, `*` crosses `/`). The default leaves nothing out. A pattern is refused when it starts with `/` or `~`, holds a `..` segment, or holds `{` or `}` (a placeholder would never match; nothing expands it here). Chosen over a positive list of what a command reads, where a forgotten input silently reuses a stale pass: with a list of what is left out, a forgotten path costs one run, never a silenced check. The engine leaves out nothing of its own accord, not even the work item's files: a project's secret scan reads the journal (decision 12). (S0001)
3. **The tree is the work tree as the factory's commit would record it**: tracked files with their content in the work tree, untracked files that are not ignored, no deleted ones. It is computed in a temporary index, so the checkout's index, `HEAD` and work tree stay as they are, and the temporary folder is removed. Ignored files (`.venv`, the caches, `.reports/`) are not part of the key. The tools stand behind the image, and the dependencies behind `uv.lock`, which is in the tree. (S0001)
4. **What invalidates a known result.** A file the command reads changing on the branch changes the tree. A merge of `main` changes it whenever `main` brought a file the command reads; a merge that brings only files left out, such as the human's night log under `planning/`, keeps the result, since the command reads the same files. A change to any value of the pipeline definition changes `definition`. That covers a changed `not_read`, `time_limit` or stage, and it is simpler than tracking which values a command depends on. A rebuilt image changes `image`. There is no expiry by age: a pass of the same input, definition and tools does not age. Deleting `known-results.jsonl` forgets every known result, at the cost of one run each. (S0002)
5. **A failed result is never reused, and the last run of a key decides.** Only a record of a run (`reused` is `None`) is a known result, and only when the last such record of that key passed. A key whose later run failed or reached its time limit has no known result until a new run passes, so a flaky test is not hidden by an earlier pass. `CheckResult` and `ResultRecord` refuse `reused` on any status but `passed`. (S0002)
6. **Recorded as skipped, never silenced.** A reused command adds a `ResultRecord` whose `reused` is the `at` of the run it took, with `duration_seconds` 0. Its journal line names the run: `` `check`: check: green (not run again: passed on tree 0123456789ab at 2026-10-18T15:20:01Z) ``. A reuse is not a run, so `project-commands.jsonl` (every real run, F0012's telemetry) gets no line for it, and the target times there stay true. The count of `check` runs on one tree, the telemetry line of the plan, is a query over `known-results.jsonl`, grouped by `key.tree`. No counter or report of its own. (S0002)
7. **A store of its own, `records/known-results.jsonl` in the state directory, per instance.** The state directory is outside every write path, so no agent can write a known result (the kernel's guard, F0019). Chosen over new fields on `CommandRecord`: `RecordingProjectCommands` sees no key, and its tests pin the record's fields. Another instance on the same repository keeps its own; a key match across instances is not worth a shared file. Never pruned: about five lines per story. A line that cannot be read or written is logged, and the command then runs as today. (S0002)
8. **Where: the checks and reports of a stage, through `KnownResults`.** Reports such as `duplicates` are reused like checks: a passed report on the same input prints the same line. The tests stage's red `test` report is a failed result and always runs. The preflight's probe of `main` is not changed: it has its own memory by commit in the stamp. `ProjectCommands`, `MakeProjectCommands` and `RecordingProjectCommands` are not changed. (S0002)
9. **Only the factory's own runs are known.** An agent's own `make check` inside its run is not a known result. The factory does not see that run, and everything an agent can write is outside the state directory, so its result would be the agent's word. The factory also does not tell an agent of a known result. The coder's last `make check` and the factory's `check` right after it on the same tree therefore stay two runs (Out of scope). (Feature)
10. **`Boundaries.result_records` is optional and last**, as `stop_records` is (F0021-S0003): `None` means no known results, every command runs as today and nothing is read or written. So every test that builds `Boundaries` stays valid, the stage tests among them. Only the wiring sets it. (S0002)
11. **`work_tree_id` is the git interface's twenty-fourth operation**, on the `Git` interface and its one implementation, since git is reached only through its wrapper (R5). Its default `left_out=()` lets other callers ask for the whole tree. (S0001)
12. **factory-rf's own `not_read`, and `secrets` as a command of its own at the docs stage** (the human's change 1). `make check` reads the documents and the work items only through `make secrets` over the changed files. Leaving them out of `check`'s key without another scan would let a secret in a document or a journal pass unscanned when the docs stage reuses `check`. So `secrets` runs at the docs stage with nothing left out (about a second), and `documents` gets 2 minutes instead of 5 to keep the documenter's stage within its lease. (Feature)
13. **The template and the demos stay as they are.** Without `not_read` their commands run as today, since the journal changes every stage's tree. A project opts in by declaring what its commands do not read. The operator guide says how, and that a project whose `check` scans for secrets keeps a scan of the left-out files, as factory-rf does. The todo demo's coder writes `docs/openapi.json`, which its tests read; that is an example of why the factory cannot guess the list. (Feature)
14. **The records contract (F0021-S0006).** `not_read` is an optional field added to the pipeline definition, so S0001 regenerates the committed schemas with `uv run python -m factory.entry.contract` and raises `RECORDS_CONTRACT`'s minor by one from the value it holds when S0001 starts (F0020 may have raised it already), by F0021's decision 15. The pipeline definition's own `contract` stays `"1.0"` in every file: the loader reads its major only. `ResultRecord` is the factory's own state-directory record, like `CommandRecord`, and is not part of the records contract. If F0021-S0006 is not on `main` when S0001 starts, this part of S0001 falls away. (S0001)
15. The leaves to change tests other stories wrote, beyond the standing leave of `CLAUDE.md`; the tester makes exactly these changes and nothing else in those modules:
    - S0001: `tests/application/test_git_interface.py`, whose `OPERATIONS` set gains `"work_tree_id"` and whose test `test_git_has_exactly_the_twenty_three_operations_and_git_cli_has_each` is renamed `test_git_has_exactly_the_twenty_four_operations_and_git_cli_has_each`. `tests/application/test_interfaces.py`, the test `test_git_abstract_methods_are_exactly_its_twenty_three_operations` renamed `test_git_abstract_methods_are_exactly_its_twenty_four_operations`. In the test modules of F0021-S0006 (`tests/domain/test_contract.py`, `tests/entry/test_contract.py`) and of any later story that pins the records contract's version as a literal, each such literal becomes the new value; nothing else changes there.
    - S0002: none. The stage tests run with `result_records` left at `None`, and no earlier test pins a journal line of a reused result.
16. **Where F0023 touches F0020, F0021 and F0022.** All three are built first. F0020-S0007 changes how `StageLauncher` runs the agent (`PatientRuns`); S0002 changes only `StageFinisher`'s checks and reports, after the run. F0020's preflight and runtime choice are untouched. F0022-S0001 changes the `agent_definitions` line of `build_boundaries`; S0002 adds the `result_records` line beside it. F0021-S0003 added `Boundaries.stop_records`, the pattern S0002 follows. F0021-S0006's contract is regenerated by S0001 (decision 14). F0021's `factory/stops.jsonl` is in factory-rf's `not_read` (the human's change 1). (Feature)
17. **Testing, and what only the real run shows.** The stories are tested with real local git repositories and remotes, the factory's fakes and Makefiles written into `tmp_path`, with no paid call; the smoke tests do the same in v1.1's container. Only the human's change 3 shows the saving on factory-rf's real `make check`, and that its `not_read` leaves out nothing `make check` reads. (Feature)
