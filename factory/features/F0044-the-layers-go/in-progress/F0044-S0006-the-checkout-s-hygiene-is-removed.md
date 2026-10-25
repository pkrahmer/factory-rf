---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 449
comments_read: [6399896604, 6399939221, 6400068325]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T16:01:43.278139Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T16:01:43.284686Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-25T16:02:01.481106Z'
  stage: intake
  run: 651421fbcf5d441390ae072b8393d807
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-25T16:04:22.002047Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-25T16:04:40.090155Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-25T16:05:02.326307Z'
  stage: intake
  run: 363cf665ed8c4d6399f729f331025633
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-25T16:05:22.900305Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-25T16:06:08.686996Z'
  stage: tests
  run: e5f30ecb38b34e03b3eac380154b7bbb
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-25T16:07:25.188012Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-25T16:07:43.249124Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-25T16:14:22.786274Z'
  stage: tests
  run: 189dd4e546554fe883a68e0ad1f73fb7
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-25T16:14:44.454755Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-10-25T16:18:10.042438Z'
  stage: doing
  run: 5ca76f4ec92d4dfba986a12ee2daba12
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-10-25T16:19:26.087694Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-25T16:19:43.850713Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-10-25T16:20:15.651004Z'
  stage: doing
  run: 962f5ca3c1a44ba6b393c66baf89ea2d
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-25T16:20:36.003413Z'
  stage: tests
- number: 18
  speaker: tester
  kind: result
  at: '2026-10-25T16:23:16.762856Z'
  stage: tests
  run: 0a992b28086d416489bb94493ddca4a7
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-25T16:23:37.679395Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-10-25T16:27:13.817877Z'
  stage: doing
  run: bdd004f93fe74a91a76e4ff6693c1ce6
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-25T16:27:34.433500Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-10-25T16:29:16.531850Z'
  stage: review
  run: bda3abe802c544df9f4898a0a6f14edf
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-25T16:29:37.198543Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-10-25T16:30:01.867501Z'
  stage: doing
  run: 5771daea11634d538f7c9953849799c8
- number: 25
  speaker: factory
  kind: started
  at: '2026-10-25T16:30:22.461374Z'
  stage: tests
- number: 26
  speaker: tester
  kind: result
  at: '2026-10-25T16:33:08.060853Z'
  stage: tests
  run: 6feb94f917fd4c1eba39b44d56423458
- number: 27
  speaker: factory
  kind: started
  at: '2026-10-25T16:33:30.113202Z'
  stage: doing
- number: 28
  speaker: coder
  kind: result
  at: '2026-10-25T16:36:36.030940Z'
  stage: doing
  run: a0c18e7c066444e1bf5c55c675b27c98
- number: 29
  speaker: factory
  kind: started
  at: '2026-10-25T16:36:57.809384Z'
  stage: review
- number: 30
  speaker: reviewer
  kind: result
  at: '2026-10-25T16:37:45.008872Z'
  stage: review
  run: 92fb6dc8da1146fc87f9c5032d154ec4
- number: 31
  speaker: factory
  kind: started
  at: '2026-10-25T16:38:05.840213Z'
  stage: docs
- number: 32
  speaker: documenter
  kind: result
  at: '2026-10-25T16:41:02.001139Z'
  stage: docs
  run: dad6a0f53e1642c2be02671b1651e60c
---

# The checkout's hygiene is removed

## Description

v1.1 keeps the factory's own checkout clean of what an agent could leave in it: the git folder is sealed (its group and others' write bits taken) before every run and every project command and checked after, a repository nested in the work tree is removed and stalls the stage as `nested_repository`, the git-ignored paths are removed after every run and at the tick's restore, a checkout whose `.git` fails the check is cloned again, and the tests set their own umask because the seal refuses a group-writable checkout. On a `container` instance no agent and no project command touches the host's checkout: the agent works on the dataset, the checks run on a rolled-back copy, and the take brings in only the role's paths, `.git` and the ignored ones never among them. After S0005 (the second user is removed) no other user can write the checkout either. This story removes the hygiene: the four git operations of the seal and the cleaning and `discard`, `RepositoryUnsealed` and the dispatcher's re-raise, the re-clone in `CheckoutPreparer`, the removal of ignored paths at the restore, `factory.application.sealed_runs` whole (`run_sealed`, `SealedRun`, `SealedProjectCommands`), the stall reason `nested_repository` and its note, the probe's nested-repository fault, and the tests' umask. `StageEnvironment.run_agent` returns the run's result itself, now that a sealed run carries nothing else (F0042's decision 2 named this move). Removing a value of the stall reasons narrows a contract model, so the records contract rises to 3.0 (decision 5 of `feature.md`); the pipeline definition's own `contract` stays `1.0` (decision 31). What stays: the tick's restore of the checkout (`reset_to("HEAD")`, the switch to `main`, the deletion of local work-item branches); the clone of a missing checkout; the factory's git environment (the credential helper, no hooks, no fsmonitor); the stall reason `left_branch` (decision 14); the take's ignore filter (`Git.ignored`).

## Interface

Removed whole: `src/factory/application/sealed_runs.py`.

`factory.application.git.Git` (`application`) loses the operations `seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored` and `discard`, which leaves twenty-one; `factory.adapters.git_cli.GitCli` loses them with `_check_git_folder`, `_raise_unsealed`, `_nested_repositories` and the helpers only they use.

`factory.domain.errors`: `RepositoryUnsealed` goes. `factory.application.dispatcher`: its `except RepositoryUnsealed: raise` goes (every handler error is counted).

`factory.application.scheduler.CheckoutPreparer.prepare()` (`application`): clones when `<checkout>/.git` does not exist; otherwise does nothing (no check, no log line, no clone again). Its docstring is exactly "Clone when the checkout holds no `.git`; keep any checkout that does." `CheckoutPreparer(git, settings, log=None)` keeps its signature; `_keep_or_clone_again` and `_write_log` go.

`factory.application.tick` (`application`): `_restore_checkout` removes no ignored paths.

`factory.application.stage_environment` (`application`):

```python
@abstractmethod
def run_agent(self, request: AgentRunRequest, *, run: Callable[[AgentRunRequest], AgentRunResult] | None = None) -> AgentRunResult: ...
```

- Both environments return `(run or boundaries.agent_runtime.run)(request)`; the inline one seals nothing.

`factory.application.stage` (`application`): `LaunchedStage.nested_repositories` and the branch of `_early_stall` that stalls `nested_repository` go. `factory.application.preflight.agent_run_probe_item`: the fault `the probe run left a git repository in the work tree, ...` goes.

`factory.domain.journal.StallReason` loses `nested_repository`; `factory.domain.post_texts` loses its stall sentence. `factory.domain.contract.RECORDS_CONTRACT = "3.0"`; the five schemas regenerated (`work-item-state` and `acceptance-state` lose the value).

`factory.entry.wiring`: unchanged; since S0005 it neither imports nor builds `SealedProjectCommands`, and `_project_commands` is gone.

Tests (the leave is decision 22 of `feature.md`):

- Deleted whole: `tests/adapters/test_git_cli_ignored.py`, `tests/adapters/test_git_cli_nested.py`, `tests/application/test_dispatcher_unsealed.py`, `tests/application/test_nested_repositories.py`, `tests/application/test_sealed_project_commands.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_sealed_runs_ignored.py`, `tests/application/test_stage_run_ignored.py`, `tests/application/test_tick_ignored.py`, F0044-S0004's `tests/application/test_sealed_runs_no_home.py`, `tests/test_tests_umask.py`. The helper module `tests/sealed_run_support.py` stays without `leave`: its `COMPLETED` and `run_request` serve `tests/application/test_container_environment.py`, `test_stage_environment.py` and `test_sealed_runs_runner.py`.
- `tests/adapters/test_git_cli_seal.py`: every test but `test_git_never_reaches_a_repository_above_a_working_copy_whose_git_folder_is_broken` is deleted (the two `discard` tests with the operation); its fixtures `headless` and `repository_above` and the helper `_head_or_none` stay.
- `tests/application/test_checkout_preparer_seal.py`: `test_a_missing_checkout_is_cloned_and_sealed` becomes `test_a_missing_checkout_is_cloned` (without `group_umask` and the check of a closed `.git`) and `test_a_sealed_checkout_is_kept_and_sealed_again_without_a_log_line` becomes `test_an_existing_checkout_is_kept_without_a_log_line` (the config's mode stays `0o664`); `test_a_checkout_whose_git_folder_fails_the_check_is_removed_and_cloned_again` and `test_a_checkout_that_cannot_be_discarded_is_the_repository_unavailable_stop` are deleted, with `_closed`, `_group_writable`, `_link_elsewhere` and `UNSEALED`.
- `tests/application/test_sealed_runs_runner.py`: `test_a_sealed_run_calls_its_runner_instead_of_the_runtime` is deleted with `Runner` and the module's imports from `tests/application/test_sealed_runs.py`; `test_the_probe_does_not_wait_out_a_provider_limit` stays.
- `tests/application/test_git_interface.py`: `OPERATIONS` loses the five names and `test_git_has_exactly_the_twenty_six_operations_and_git_cli_has_each` becomes `..._twenty_one_...`; `tests/application/test_interfaces.py::test_git_abstract_methods_are_exactly_its_twenty_six_operations` becomes `..._twenty_one_...`, the same assertion.
- `tests/application/test_stage_environment.py::test_run_agent_is_the_sealed_run_through_the_runtime_or_the_given_run` (the result itself; its checks of the git folder's modes go with `_open_git_folder`, `SEALED_MODES` and the imports of `NestingRuntime`, `ModeRecordingRuntime`, `OPEN_FILE`, `OPEN_FOLDER` and `Runner`, and the given run is a recording function of the test's own) and `::test_run_agent_removes_a_nested_repository_and_names_it` (deleted); `tests/application/test_container_environment.py::test_run_agent_runs_unsealed_through_the_runtime_or_the_given_run` and `::test_run_agent_leaves_nested_repositories_ignored_files_and_the_home` (they read the result itself); the stand-ins `RecordingEnvironment.run_agent` of `tests/application/test_stage_environment_calls.py` and `TakingEnvironment.run_agent` of `tests/application/test_stall_environment.py` return the result; `tests/application/test_stage_environment_calls.py::test_the_preflight_does_not_import_the_sealed_run` is deleted.
- `tests/domain/test_stall_texts.py::test_each_stall_cause_is_its_sentence_alone_or_with_the_detail`: the row `nested_repository` goes; `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` , `tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2` and F0044-S0002's `tests/domain/test_contract_version_2.py::test_the_records_contract_is_at_version_2_without_tool_paths` read `3.0`, each keeping its name.
- `tests/application/test_tick.py::test_the_restore_discards_changes_and_names_them_in_one_line`: the excluded `ignored.log` stays with its text; `tests/application/test_tick_docstrings.py::test_the_docstrings_say_what_the_code_does`: the row `checkout-preparer-prepare` reads the docstring the Interface gives; F0044-S0004's `tests/test_home_reset_removed.py::test_the_names_of_the_home_reset_are_gone`: the row `sealed-project-commands-parameters` goes with the import of `SealedProjectCommands`. Each test keeps its name, except the ones this list renames or deletes.
- `tests/conftest.py`: `pytest_configure`'s `os.umask`, `TESTS_UMASK` and the fixture `group_umask` go, with every use of `group_umask` (`tests/application/test_checkout_preparer_seal.py`).

## Acceptance criteria

1. The removed names (rows of one parametrized test): `importlib.util.find_spec("factory.application.sealed_runs")` is `None`; `Git.__abstractmethods__` holds none of `seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored`, `discard` and has exactly twenty-one names; `GitCli` has none of them; `RepositoryUnsealed` is no attribute of `factory.domain.errors`; `"nested_repository"` is not in `typing.get_args(StallReason)`; `LaunchedStage.model_fields` holds no `nested_repositories`; no post text built for a stall mentions a nested repository.
2. The preparer (rows of one parametrized test on a real bare remote): with no checkout, `prepare()` clones it and writes no log line; with a cloned checkout whose `.git` is group-writable, `prepare()` changes nothing (the mode stays, no clone, no log line); with a cloned checkout that holds a nested repository `sub/.git`, `prepare()` leaves it; `CheckoutPreparer.prepare.__doc__` equals "Clone when the checkout holds no `.git`; keep any checkout that does."
3. The restore keeps the ignored files: a tick's restore on a checkout that holds an ignored file `.venv/x` and an untracked changed file `src/a.py` discards `src/a.py` and logs `discarded uncommitted changes: src/a.py`, leaves `.venv/x`, and ends on `main` at `origin/main`.
4. `run_agent` returns the result (rows of one parametrized test over both environments with `FakeAgentRuntime`): the value is the queued run's `AgentRunResult`; with `run` given, `run` is called once and its result returned; and on the inline environment a run that writes `sub/.git/HEAD` and an ignored `.venv/x` into a checkout whose `.git` is at `0o2775` leaves both files and the mode as they are.
5. A stage whose agent leaves a nested repository no longer stalls for it (one test through `StageRunner` on the `boundaries` fixture, an intake stage, whose scripted run writes `sub/.git/HEAD` and decides `tests`): the work item moves to `tests`, and its journal's last entry is the intake's result, not a stall.
6. The dispatcher counts every error (one test): a handler that raises `GitError("seal", None, "x")` makes `dispatch` return `"error"` and counts one error for the event, as for any other `GitError`.
7. The contract (rows of one parametrized test): `RECORDS_CONTRACT == "3.0"`; each committed schema holds `"x-records-contract": "3.0"` and equals the generated one; no schema names `nested_repository`.
8. A test runs under the umask pytest was started with: no module under `tests/` calls `os.umask` (one test reading the files).
9. The probe ignores a nested repository (one test): `agent_run_probe_item`, run with a scripted agent that writes `sub/.git/HEAD`, reports no fault; the probe item passes.
10. `make check` stays green.
11. docs: `docs/project-guide/git-and-hosting.md`: the rows of `seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored` and `discard` go and the count says twenty-one, *Restoring the checkout* loses its bullet `remove_ignored()` and says three, and *Which part uses which operation* loses its row `remove_ignored`; `docs/project-guide/stage-environment.md`, *The container environment*, `run_agent`, and the row `project_commands` of the table in *The settings and the wiring*: no `SealedRun`, no `SealedProjectCommands`; `docs/project-guide/stages.md`, *The reasons* and *After the agent run*: no `nested_repository` and no rule for it; `docs/project-guide/write-guard.md`, *Limits*: no removal of ignored paths by `run_sealed`; `docs/project-guide/processes-and-checks.md`, *Rules of `run`* and *Mutation testing*: no tests' umask and no `umask 022` for the seal; `docs/project-guide/stage-environment.md`, *The stage environment*: `run_agent` returns the result; `docs/project-guide/stages.md` and `docs/project-guide/watching.md` (the dispatcher, the preparer, the restore): no seal, no re-clone, no removal of ignored paths, no `RepositoryUnsealed`; `docs/project-guide/processes-and-checks.md`, *Sealed project commands*: removed; `docs/project-guide/README.md`, *The files*: the lines follow, and *Shared test helpers*: the line of `conftest.py` loses `group_umask` and the line of `sealed_run_support.py` says the agent runs' completed result and request; `docs/operator-guide.md`: *The checkout is cloned again when it is missing or its `.git` is not the factory's alone* becomes *The checkout is cloned when it is missing* (a kept checkout is not checked), *A stall: the stall note*: the cause "the agent left a git repository in the work tree, which the factory removed (the detail lists the paths)" goes and the count says ten, and every sentence on the seal, the removal of ignored paths or the tests' umask goes; *The records contract*: `3.0` and why. `docs/decisions.md`: the entries "No nested repository in the work tree", "The factory removes the git-ignored paths after every agent run and at the restore", "The tests set their own umask, and uv syncs under the caller's", "The factory alone writes the checkout's `.git`", "A checkout whose clone was killed half-way is not recognised" and "The checkout is disposable and restored to `origin/main` at the start of every tick" each gain one closing line ("Replaced by the dataset's rollback, v1.2 F0044-S0006"; the last: "The seal, the re-clone and the removal of ignored paths went with v1.2 F0044-S0006; the restore stays"). `README.md`: none.

## Smoke test

```bash
uv run python -c 'import factory.application.sealed_runs' 2>/dev/null && echo present || echo gone
uv run python - <<'EOF'
import typing
from factory.application.git import Git
from factory.domain import errors
from factory.domain.contract import RECORDS_CONTRACT
from factory.domain.journal import StallReason

print(len(Git.__abstractmethods__), sorted({"seal", "check_seal", "remove_ignored", "discard"} & Git.__abstractmethods__))
print(hasattr(errors, "RepositoryUnsealed"), "nested_repository" in typing.get_args(StallReason), RECORDS_CONTRACT)
EOF
```
Expect: three lines: `gone`; `21 []`; `False False 3.0`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface says `factory.application.preflight.agent_run_probe_item` loses the fault `the probe run left a git repository in the work tree, ...`, and no criterion tests it. Criterion 5 runs through `StageRunner`, not the probe. Should a criterion be added that the probe, run with a scripted agent that writes `sub/.git/HEAD`, reports no fault? I would add it: one row, the probe item passes.
   2. The Interface gives `CheckoutPreparer.prepare()` the exact docstring "Clone when the checkout holds no `.git`; keep any checkout that does." Only the Description's test list covers it, as a changed row of `tests/application/test_tick_docstrings.py`, and no acceptance criterion pins it. Should criterion 2 or a new criterion state that the docstring equals that text? I would add it to criterion 2 as a further row.
   3. The Interface says `factory.domain.post_texts` loses the stall sentence for `nested_repository`. Criterion 1 tests the reason in `StallReason`, but nothing tests that the sentence is gone from the post texts. Should a criterion say that no post text built for a stall mentions a nested repository, or is the deleted row in `test_each_stall_cause_is_its_sentence_alone_or_with_the_detail` meant to be the whole test? I would add a row to criterion 1 for it.
   The format check passed. Everything else is in order:
   - The smoke test commands are runnable and its `Expect:` line is checkable. It runs no pytest, so the `-q` rule does not apply.
   - The architecture matches the layers.
   - The scope is inside feature S0006.
   - Every other Interface clause has a criterion on both sides.
4. 2026-10-25 human: Yes to all three, as you propose:
   1. Add a criterion: the probe, run with a scripted agent that writes `sub/.git/HEAD`, reports no fault (one row, the probe item passes).
   2. Add a row to criterion 2: `CheckoutPreparer.prepare`'s docstring equals "Clone when the checkout holds no `.git`; keep any checkout that does."
   3. Add a row to criterion 1: no post text built for a stall mentions a nested repository.
   New tests and rows need no leave beyond decisions 22 and 35(a).
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete modules and signatures throughout (removed module, the 21-operation Git, the exact `prepare()` docstring, the `run_agent` signature, StallReason, RECORDS_CONTRACT 3.0). The behaviours it states (docstring text, restore keeps ignored files, run_agent returns the result, the probe fault going) now each have a criterion.
   - Criteria: each is testable by one parametrized test or one test. Failing sides are covered: the removed names are absent, a kept group-writable `.git` and a nested repo are left alone, the dispatcher counts `GitError("seal", ...)` as any error, and the schemas must not name `nested_repository`. I carried in the human's answers from journal entry 4 as exactly three edits. Criterion 1 gains a row: no stall post text mentions a nested repository. Criterion 2 gains a row: `CheckoutPreparer.prepare.__doc__` equals the Interface text. New criterion 9: `agent_run_probe_item`, with a scripted agent that writes `sub/.git/HEAD`, reports no fault. The two closing criteria are now 10 (`make check`) and 11 (docs). I changed nothing else.
   - Smoke test: the python and import commands are runnable, and the `Expect:` line gives three lines that can be compared. It runs no pytest, so the `-q` rule does not apply.
   - Architecture: the removals follow the layers. The domain loses the error and the stall reason, the application loses `sealed_runs`, the Git operations and the preparer logic, and the adapter loses `GitCli`'s matching methods. No layer gains an import.
   - Scope: inside S0006 of `feature.md`. The tests listed are covered by the leave of decision 22 as corrected by 35(a), and the new criteria need no leave beyond decisions 22 and 35(a), per the human. `left_branch` stays, as decision 14 and the "What stays" list say.
7. factory: started tests as self.
8. tester: I can't write criterion 8 as it stands without changing a test I have no leave for. I wrote no tests and changed no files in this run.

   Criterion 8 says that no module under `tests/` calls `os.umask`, checked by one test that reads the files. Removing `pytest_configure`'s umask, `TESTS_UMASK`, `group_umask` and `tests/test_tests_umask.py` (all under the leave of decision 22) is not enough to make that true. `tests/adapters/test_calls_as_the_factory_user.py` is not on the Interface's test list, and it has a fixture `umask_of` (lines 156-161) that calls `os.umask(mask)` and then `os.umask(previous)`. `test_the_run_files_keep_the_mode_the_umask_gives` uses it to check that the runtimes' run files get the mode the umask gives, under `0o077` and `0o022`. The fixture puts the previous umask back afterwards, so every other test still runs under the umask pytest was started with. But it calls `os.umask`, so a test written to the letter of criterion 8 fails, and the coder can't make it pass because the coder never edits tests (R9).

   Options:
   (a) Narrow criterion 8: no module under `tests/` calls `os.umask`, except the fixture `umask_of` of `tests/adapters/test_calls_as_the_factory_user.py`, which puts the previous umask back. The test names that one exemption, and the earlier test file stays as it is.
   (b) Give leave to rewrite `umask_of` / `test_the_run_files_keep_the_mode_the_umask_gives` so that it sets the umask in a child process (`sh -c 'umask 077; exec …'`) and keeps its name and what it checks. That is a larger change to a test another story wrote.
   (c) Give leave to delete that test.

   I would choose (a). The criterion is about the run-wide umask the tests set, and a fixture that puts the umask back doesn't change the umask other tests run under.

   Everything else checked out. Criteria 1-7 and 9 are testable as written against the Interface. The edits to existing tests that the Interface lists are clear. One example: in `tests/application/test_tick.py::test_the_restore_discards_changes_and_names_them_in_one_line`, the assertion that `ignored.log` is gone becomes an assertion that it stays with its text. After your answer I will write all the tests and make the listed edits in one run.
9. 2026-10-25 human: (a). Criterion 8 means the run-wide umask the tests set. Its test names one exemption: the fixture `umask_of` of `tests/adapters/test_calls_as_the_factory_user.py` (F0044-S0005), which sets a umask for one test and puts the previous one back. That file stays as it is.
10. factory: started tests as self.
11. tester: I wrote the tests for criteria 1–9 and made the test changes the Interface lists. Criterion 8 follows the human's answer (a): its test exempts one fixture, `umask_of` in `tests/adapters/test_calls_as_the_factory_user.py`, and that file is unchanged. I made no other interpretation of the criteria.

    Criterion → test:
    - criterion 1: `tests/test_checkout_hygiene_removed.py::test_the_names_of_the_checkouts_hygiene_are_gone` (rows: sealed-runs-module, git-operations, git-twenty-one, git-cli-operations, repository-unsealed, stall-reason, launched-stage-field, stall-texts)
    - criterion 2: `tests/application/test_checkout_preparer_seal.py::test_the_preparer_clones_only_a_missing_checkout_and_checks_none` (rows: missing-is-cloned, group-writable-git-is-kept, nested-repository-is-left, docstring)
    - criterion 3: `tests/application/test_tick_restore_ignored.py::test_the_restore_discards_an_untracked_file_and_keeps_an_ignored_one`
    - criterion 4: `tests/application/test_stage_environment.py::test_run_agent_returns_the_runs_result` (rows: queued and given-run, each on inline and container) and `tests/application/test_stage_environment.py::test_the_inline_run_leaves_a_nested_repository_ignored_files_and_the_git_folders_mode` (`.git` at `0o2775`, with `sub/.git/HEAD` and `.venv/x`)
    - criterion 5: `tests/application/test_stage_nested_repository.py::test_a_nested_repository_left_by_the_agent_does_not_stall_the_stage`
    - criterion 6: `tests/application/test_dispatcher_counts_every_error.py::test_a_handlers_git_error_named_seal_is_counted_as_any_error`
    - criterion 7: `tests/domain/test_contract_version_3.py::test_the_records_contract_is_at_version_3_without_nested_repository` (rows: version, one per schema, no-nested-repository)
    - criterion 8: `tests/test_tests_run_under_the_starting_umask.py::test_no_module_under_tests_calls_os_umask_but_the_one_fixture_that_restores_it`
    - criterion 9: `tests/application/test_probe_nested_repository.py::test_a_probe_run_that_leaves_a_nested_repository_passes`
    - criteria 10 and 11 (`make check`, docs): no tests; they belong to the later stages.

    Files created: `tests/test_checkout_hygiene_removed.py`, `tests/test_tests_run_under_the_starting_umask.py`, `tests/application/test_tick_restore_ignored.py`, `tests/application/test_stage_nested_repository.py`, `tests/application/test_dispatcher_counts_every_error.py`, `tests/application/test_probe_nested_repository.py`, `tests/domain/test_contract_version_3.py`.

    Earlier test files changed under the Interface's list (decision 22 of `feature.md`):
    - Deleted the eleven listed modules.
    - `tests/adapters/test_git_cli_seal.py`: only the broken-git-folder test and its fixtures `headless` and `repository_above` and helper `_head_or_none` remain.
    - `tests/application/test_checkout_preparer_seal.py`: the two renamed tests; the config's mode stays `0o664`. The two deleted tests went with `_closed`, `_group_writable`, `_link_elsewhere`, `UNSEALED` and the `group_umask` use.
    - `tests/application/test_sealed_runs_runner.py`: `Runner` and its test are gone; the probe test stays.
    - `tests/sealed_run_support.py`: lost `leave`; its docstring now says "agent runs".
    - `tests/application/test_git_interface.py` and `tests/application/test_interfaces.py`: twenty-one operations.
    - `tests/application/test_stage_environment.py`: the given run is a `RecordingRun` of the test's own; the nested-repository test is deleted.
    - `tests/application/test_container_environment.py`: both tests read the result itself; one line of the module docstring changed.
    - `tests/application/test_stage_environment_calls.py` and `tests/application/test_stall_environment.py`: the stand-ins return `AgentRunResult`; the preflight-import test is deleted.
    - `tests/domain/test_stall_texts.py`: the `nested_repository` row is gone.
    - `tests/domain/test_contract.py`, `tests/domain/test_contract_provider_limit.py` and `tests/domain/test_contract_version_2.py`: read `3.0`.
    - `tests/application/test_tick.py`: `ignored.log` stays with its text.
    - `tests/application/test_tick_docstrings.py`: the new `PREPARE` text.
    - `tests/test_home_reset_removed.py`: the `sealed-project-commands-parameters` row and its import are gone.
    - `tests/conftest.py`: `pytest_configure`, `TESTS_UMASK`, `group_umask` and the `os` import are gone.

    Red run: `make lint` is green. In the one `make test` run, the failures come from code not yet changed:
    - The probe still reports the nested-repository fault.
    - The seal raises `RepositoryUnsealed` on a group-writable `.git`, and `run_agent` still returns a `SealedRun`.
    - The schemas and `RECORDS_CONTRACT` are still `2.0`, and the removed names still exist.
    - The preparer's docstring is still the old one.

    Unlisted tests also fail under the old seal: `tests/application/test_scheduler.py::test_an_existing_clone_is_kept_without_calling_git`, two tests in `tests/application/test_repository_waiter.py`, and the launch/take tests in `tests/application/test_stage_environment_calls.py`. The cause is that the tests now run under pytest's starting umask, so a clone's `.git` is group-writable. They should pass once the seal is removed. The new dispatcher test passes today, as the criterion expects: it guards behaviour that must not change.

    No test module failed to import; every module the run could not import is one this story deletes, and nothing imports them any more. I skipped the type check, as this stage says.

    `lint`: lint: green (0.7 s)
    `test`: FAILED tests/application/test_repository_waiter.py::test_a_failing_clone_or_fetch_is_one_stop_naming_the_git_error[_deleted_after_clone-cannot fetch: git fetch --prune origin failed] - assert False
12. factory: started doing as self.
13. coder: The code is done, but two of the new tests cannot pass against the code, so `make test` is red. I changed no test.

    **What I built.** All in the working tree:
    - `src/factory/application/sealed_runs.py` is deleted.
    - `src/factory/application/git.py` and `src/factory/adapters/git_cli.py` lose `seal`, `check_seal`, `remove_nested_repositories`, `discard` and `remove_ignored`. `GitCli` also loses `_check_git_folder`, `_raise_unsealed`, `_close`, `_nested_repositories`, `_remove_entry`, `SHARED_WRITE` and the `stat` import.
    - `src/factory/domain/errors.py` loses `RepositoryUnsealed`. `src/factory/application/dispatcher.py` loses its re-raise and the docstring's exception.
    - `src/factory/application/scheduler.py`: `CheckoutPreparer.prepare` only clones a missing checkout and has the docstring the Interface gives. `_keep_or_clone_again` and `_write_log` are gone; the signature is kept.
    - `src/factory/application/tick.py`: `_restore_checkout` no longer calls `remove_ignored`.
    - `src/factory/application/stage_environment.py`: both environments' `run_agent` return `(run or boundaries.agent_runtime.run)(request)` as an `AgentRunResult`.
    - `src/factory/application/stage.py`: `LaunchedStage.nested_repositories` and the `nested_repository` branch of `_early_stall` are gone.
    - `src/factory/application/preflight.py`: the probe's nested-repository fault is gone.
    - `src/factory/domain/journal.py` and `src/factory/domain/post_texts.py` lose `nested_repository`.
    - `src/factory/domain/contract.py` has `RECORDS_CONTRACT = "3.0"`. The five schemas were regenerated with `uv run python -m factory.entry.contract`.

    **Main choice.** Each environment calls the runtime itself in its own `run_agent`. I rejected a shared concrete helper on the abstract base: the Interface has `run_agent` as an `@abstractmethod`, and an interface carries no behaviour here.

    **Where I stopped.** `make lint types layers sast secrets licenses` are each green. `make test` fails only in these two new tests:

    1. `tests/application/test_probe_nested_repository.py::test_a_probe_run_that_leaves_a_nested_repository_passes` fails with `assert item.detail is None` (`AssertionError: assert '' is None`). `PreflightItem.detail` is typed `str = ""` and is never `None`. The probe passes (`passed` is true) with the detail `""`, which is what `_login_detail` returns for a run without a login. Options:
       - (a) The test asserts `item.detail == ""` (or drops that line). This is what I would choose: criterion 9 says only "reports no fault; the probe item passes".
       - (b) `PreflightItem.detail` becomes `str | None`. That is outside this story's Interface.

    2. `tests/application/test_tick_restore_ignored.py::test_the_restore_discards_an_untracked_file_and_keeps_an_ignored_one` fails with `assert not (directory / "src" / "a.py").exists()`. The tick never gets to the restore: it stops at the load with `stop repository pipeline_definition_invalid: agent home unavailable: no agents directory at …/agent-home/agents`. The module lacks the `installed_agents` fixture that `tests/application/test_tick.py` applies with `pytestmark = pytest.mark.usefixtures("installed_agents")`. Option: add the same `pytestmark` line to the test module. That is what I would choose. The same scenario in `test_tick.py::test_the_restore_discards_changes_and_names_them_in_one_line` already passes against this code, with `ignored.log` kept.

    I would answer (a) for 1 and the `pytestmark` for 2, then send both back to the tester as `tests`.

    **Refactor.** I read my diff and found nothing to change.

    **Noticed, not touched.**
    - `CheckoutPreparer` still stores `self._log` but no longer reads it. The Interface keeps the `log` parameter, so `make duplicates` (vulture) may list it as unused.
    - The comment in `src/factory/entry/wiring.py:156` about a child git started for a nested repository belongs to the factory's git environment, which stays.
    - The docs criterion is the documenter's.
14. 2026-10-25 human: Both as you propose; send them to the tester with `tests`:
    1. (a). In `tests/application/test_probe_nested_repository.py::test_a_probe_run_that_leaves_a_nested_repository_passes` the line becomes `assert item.detail == ""`. `PreflightItem.detail` stays `str`.
    2. Add `pytestmark = pytest.mark.usefixtures("installed_agents")` to `tests/application/test_tick_restore_ignored.py`, as in `tests/application/test_tick.py`.
    Both are new test modules of this story, so no leave is needed. `CheckoutPreparer`'s unread `self._log` stays as the Interface keeps the parameter.
15. factory: started doing as self.
16. coder: The human's answer in entry 14 asks for two test changes and no code change. I changed nothing in this run. The code from my previous run is committed in 0edf9d3f.

    Tester, please make exactly these two changes:
    1. In `tests/application/test_probe_nested_repository.py::test_a_probe_run_that_leaves_a_nested_repository_passes`, change `assert item.detail is None` to `assert item.detail == ""`. `PreflightItem.detail` stays `str`.
    2. Add `pytestmark = pytest.mark.usefixtures("installed_agents")` to `tests/application/test_tick_restore_ignored.py`, as `tests/application/test_tick.py` has it. Without it, the tick stops at the load with "agent home unavailable" before it reaches the restore.

    What I built (0edf9d3f, listed in entry 13):
    - `src/factory/application/sealed_runs.py` is deleted.
    - The five Git operations are removed from `src/factory/application/git.py` and `src/factory/adapters/git_cli.py`.
    - `RepositoryUnsealed` is removed from `src/factory/domain/errors.py`, and the dispatcher's re-raise is removed from `src/factory/application/dispatcher.py`.
    - `CheckoutPreparer.prepare` in `src/factory/application/scheduler.py` now only clones a missing checkout.
    - The restore in `src/factory/application/tick.py` no longer removes ignored paths.
    - `run_agent` in `src/factory/application/stage_environment.py` returns the run's result.
    - The `nested_repository` stall and the probe's nested-repository fault are removed from `src/factory/application/stage.py` and `src/factory/application/preflight.py`.
    - `StallReason` and its post text are removed from `src/factory/domain/journal.py` and `src/factory/domain/post_texts.py`.
    - `RECORDS_CONTRACT` is "3.0", and the schemas were regenerated with `uv run python -m factory.entry.contract`.

    Main choice: each environment calls the runtime in its own `run_agent`. I rejected a shared helper on the abstract base, because there `run_agent` is an abstract method and the interface carries no behaviour.

    What the journal changed: criterion 9 now means "the probe item passes with an empty detail". The Description is unchanged, and it is outside my write paths.

    Status: when 0edf9d3f was made, `make test` failed only in these two tests. I did not run `make check` in this run, because nothing changed.

    Noticed, not touched: `CheckoutPreparer` still stores `self._log` but never reads it. It stays, because the Interface keeps the parameter and the human agreed in entry 14. `make duplicates` (vulture) may list it.
17. factory: started tests as self.
18. tester: I made the two test changes that the human approved in entry 14 and the coder listed in entry 16. I changed nothing else.

    1. `tests/application/test_probe_nested_repository.py::test_a_probe_run_that_leaves_a_nested_repository_passes`: the line `assert item.detail is None` is now `assert item.detail == ""`. `PreflightItem.detail` is typed `str` and stays that way, and the probe returns an empty detail when the run has no login.
    2. `tests/application/test_tick_restore_ignored.py`: I added `import pytest` and `pytestmark = pytest.mark.usefixtures("installed_agents")`, the same line `tests/application/test_tick.py` has. Without the fixture the tick stopped at the load with "agent home unavailable" and never reached the restore.

    Both are test modules this story added, so no earlier story's test changed. Files changed: the two above. No files created.

    Run: `make lint`: lint: green (0.7 s). `make test`: test: green (70.4 s), total coverage 99.55 %. Every module imported.

    `lint`: lint: green (0.7 s)
    `test`: test: green (69.6 s)
19. factory: started doing as self.
20. coder: The tester made the two test changes from entry 14 in entry 18, so the code committed in 0edf9d3f now passes every test. In this run I changed no code and no test, and I ran `make check` in the foreground. It is green: `test: green (69.2 s)`, coverage 99.55 %, `check: green`.

    What I built (0edf9d3f; full list in entry 13):
    - Deleted `src/factory/application/sealed_runs.py`.
    - `src/factory/application/git.py` and `src/factory/adapters/git_cli.py` lose `seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored` and `discard`, along with GitCli's private helpers that only those used. Git now has twenty-one operations.
    - `src/factory/domain/errors.py` loses `RepositoryUnsealed`, and `src/factory/application/dispatcher.py` loses its re-raise.
    - `src/factory/application/scheduler.py`: `CheckoutPreparer.prepare` clones only when `.git` is missing and has the docstring the Interface gives. `_keep_or_clone_again` and `_write_log` are gone; the signature is unchanged.
    - `src/factory/application/tick.py`: the restore no longer removes ignored paths.
    - `src/factory/application/stage_environment.py`: `run_agent` returns `AgentRunResult` directly in both environments.
    - `src/factory/application/stage.py` and `src/factory/application/preflight.py`: the `nested_repository` stall and the probe's fault for a nested repository are gone.
    - `src/factory/domain/journal.py` and `src/factory/domain/post_texts.py`: the reason and its stall sentence are gone.
    - `src/factory/domain/contract.py`: `RECORDS_CONTRACT = "3.0"`. I regenerated the five schemas under `src/factory/contract/` with `uv run python -m factory.entry.contract`.

    Main choice: each environment calls the runtime in its own `run_agent` with `(run or boundaries.agent_runtime.run)(request)`. I rejected a shared concrete helper on `StageEnvironment`: there `run_agent` is an `@abstractmethod`, and project interfaces hold no behaviour.

    What the journal changed: criterion 9 now means the probe item passes with an empty detail (`PreflightItem.detail` stays `str`, entry 14). The Description is outside my write paths and unchanged.

    Refactor: I re-read the diff against `main` and found nothing to change. It is pure removal, plus the new return type and docstrings.

    Noticed, not touched:
    - `make duplicates` reports 7 new, 34 known and 4 gone, and exits non-zero. That target is a record, not a check. None of the 7 new findings are in files this story changed: they are similar code in claude_runtime/opencode_runtime, podman_runs, fake_containers and zfs_snapshots, and possible dead code in `FakeContainerRuns`, `FakeSnapshots` and `FakeContainerRuns.calls`.
    - vulture does not flag `CheckoutPreparer`'s unread `self._log`. It stays, as entry 14 decided.
    - The docs criterion is the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 34 known, 4 gone
21. factory: started review as self.
22. reviewer: Review, round 0. I read the work item, the `--stat`, the whole diff under `src/` (with the five regenerated schemas), every new test module and every changed earlier test.

    Groups 1 to 3 pass:
    - Every criterion from 1 to 9 has a test that checks what the criterion says. The failing sides the Interface states are covered: the removed names, a group-writable `.git` and a nested repository left alone, `GitError("seal", ...)` counted as an error, and no schema naming `nested_repository`.
    - The factory's `make check` after the coder was green (entry 20).
    - The layers hold, and the source code adds no marker that silences a check.
    - The `src/` diff is pure removal plus the new `run_agent` return type. Each environment returns `(run or boundaries.agent_runtime.run)(request)`, as the Interface says.
    - No name of the removed hygiene is left in `src/factory`. The comment at `src/factory/entry/wiring.py:156` is about the factory's git environment, which stays.
    - `CheckoutPreparer` still stores `_log` without reading it. That stays by the human's answer in entry 14.

    Group 4 (quality) fails:

    1. `tests/application/test_stage_environment.py:60` `RecordingRun`: this is a verbatim second copy of `RecordingRun` at `tests/application/test_container_environment.py:280` (same docstrings, same body, returns `COMPLETED`). Fix: under the standing leave to move a shared test helper, the tester moves `RecordingRun` into `tests/sealed_run_support.py` beside `COMPLETED` and `run_request`. Both modules then import it from there, and every test keeps its name and what it checks. The coder hands this on with `tests`.

    Earlier tests (a test file `main` held that the diff changed or deleted). The leave for each is the Interface's test list (decision 22 of `feature.md`) unless the line says otherwise:
    - `tests/adapters/test_git_cli_ignored.py` (deleted): the Interface's list.
    - `tests/adapters/test_git_cli_nested.py` (deleted): the Interface's list.
    - `tests/adapters/test_git_cli_seal.py`: the Interface's list. Only the broken-git-folder test stays, with `headless`, `repository_above` and `_head_or_none`.
    - `tests/application/test_checkout_preparer_seal.py`: the Interface's list (two tests renamed, two deleted, `group_umask` gone). The criterion-2 test it adds needs no leave.
    - `tests/application/test_container_environment.py`: the Interface's list (both tests read the result itself), plus the module docstring that followed.
    - `tests/application/test_dispatcher_unsealed.py` (deleted): the Interface's list.
    - `tests/application/test_git_interface.py`: the Interface's list (twenty-one operations, renamed test).
    - `tests/application/test_interfaces.py`: the Interface's list (renamed test, same assertion).
    - `tests/application/test_nested_repositories.py` (deleted): the Interface's list.
    - `tests/application/test_sealed_project_commands.py` (deleted): the Interface's list.
    - `tests/application/test_sealed_runs.py` (deleted): the Interface's list.
    - `tests/application/test_sealed_runs_ignored.py` (deleted): the Interface's list.
    - `tests/application/test_sealed_runs_no_home.py` (deleted): the Interface's list.
    - `tests/application/test_sealed_runs_runner.py`: the Interface's list (`Runner` and its test gone, the probe test stays).
    - `tests/application/test_stage_environment.py`: the Interface's list (the run test reads the result through a recording function of its own; the nested-repository test is deleted). The criterion-4 tests it adds need no leave.
    - `tests/application/test_stage_environment_calls.py`: the Interface's list (the stand-in returns the result; the preflight-import test is deleted).
    - `tests/application/test_stage_run_ignored.py` (deleted): the Interface's list.
    - `tests/application/test_stall_environment.py`: the Interface's list (the stand-in's return type).
    - `tests/application/test_tick.py`: the Interface's list (`ignored.log` stays with its text).
    - `tests/application/test_tick_docstrings.py`: the Interface's list (the `PREPARE` text).
    - `tests/application/test_tick_ignored.py` (deleted): the Interface's list.
    - `tests/conftest.py`: the Interface's list (`pytest_configure`'s umask, `TESTS_UMASK` and `group_umask` gone).
    - `tests/domain/test_contract.py`: the Interface's list (reads `3.0`).
    - `tests/domain/test_contract_provider_limit.py`: the Interface's list (reads `3.0`).
    - `tests/domain/test_contract_version_2.py`: the Interface's list (reads `3.0`, same name).
    - `tests/domain/test_stall_texts.py`: the Interface's list (the `nested_repository` row gone).
    - `tests/sealed_run_support.py`: the Interface's list (`leave` gone), plus the module docstring that followed.
    - `tests/test_home_reset_removed.py`: the Interface's list (the `sealed-project-commands-parameters` row and its import gone).
    - `tests/test_tests_umask.py` (deleted): the Interface's list.
23. factory: started doing as self.
24. coder: Round 1. The reviewer's only finding (entry 22, group 4, item 1) is a test helper that was copied. It needs a change to tests and no change to code, so I changed nothing in this run. The code is still what 0edf9d3f holds (the full list is in entry 13), and `make check` was green on it (entry 20).

    I confirmed the finding. `RecordingRun` at `tests/application/test_stage_environment.py:60` is a verbatim copy of `RecordingRun` at `tests/application/test_container_environment.py:280`: same docstrings, same body, and both return `COMPLETED` from `tests/sealed_run_support.py`.

    Tester, please make this one move, under the standing leave in `CLAUDE.md` (*Tests*) to move a shared test helper: move `RecordingRun` into `tests/sealed_run_support.py` beside `COMPLETED` and `run_request`, delete the class from `tests/application/test_stage_environment.py` and `tests/application/test_container_environment.py`, and have both import it from `tests.sealed_run_support`. Every test keeps its name and checks the same thing. Please name both changed test files in your entry.

    What I built (unchanged since 0edf9d3f):
    - `src/factory/application/sealed_runs.py` is deleted.
    - The five Git operations are gone from `src/factory/application/git.py` and `src/factory/adapters/git_cli.py`.
    - `RepositoryUnsealed` is gone from `src/factory/domain/errors.py`, and its re-raise from `src/factory/application/dispatcher.py`.
    - The preparer in `src/factory/application/scheduler.py` now only clones a missing checkout.
    - The restore in `src/factory/application/tick.py` no longer removes ignored paths.
    - `run_agent` in `src/factory/application/stage_environment.py` returns the result directly.
    - The `nested_repository` stall and the probe's fault for it are gone from `src/factory/application/stage.py` and `src/factory/application/preflight.py`.
    - `nested_repository` is gone from `src/factory/domain/journal.py` and `src/factory/domain/post_texts.py`.
    - `RECORDS_CONTRACT` is "3.0", and the schemas in `src/factory/contract/` were regenerated with `uv run python -m factory.entry.contract`.

    Main choice: each environment calls the runtime in its own `run_agent`. I rejected a shared concrete helper on the abstract `StageEnvironment`, because project interfaces carry no behaviour.

    What the journal changed: nothing new in this round. The Description is outside my write paths.

    Noticed, not touched: as before, `CheckoutPreparer` stores `self._log` but never reads it. It stays, as entry 14 decided.
25. factory: started tests as self.
26. tester: Mode: the approved test change from the coder's entry 24, which is the reviewer's finding in entry 22, group 4, item 1. I made the move under the standing leave in `CLAUDE.md` (*Tests*) to move a shared test helper. No test of a criterion changed.

    The change:
    - `tests/sealed_run_support.py` now holds `RecordingRun`, beside `COMPLETED` and `run_request`. Its docstrings and body are unchanged. The module docstring now names the recording run too.
    - `tests/application/test_stage_environment.py` no longer holds its copy of `RecordingRun` and imports it from `sealed_run_support`. The `AgentRunRequest` import, now unused, is gone.
    - `tests/application/test_container_environment.py` no longer holds its copy and imports it from `sealed_run_support`. It still uses `AgentRunRequest` and `AgentRunResult` in its own stand-in, so those imports stay.

    Every test keeps its name and checks the same thing.

    Earlier test files changed under the standing leave: `tests/application/test_stage_environment.py` and `tests/application/test_container_environment.py`. `tests/sealed_run_support.py` is the shared place that now holds the helper.

    `make lint` is green, and one run of `make test` is green (`test: green`). I created no files, and every module imported.

    `lint`: lint: green (0.7 s)
    `test`: test: green (67.8 s)
27. factory: started doing as self.
28. coder: Round 1. The reviewer's only finding (entry 22, group 4, item 1: the copied `RecordingRun`) was a change to tests, and the tester made it in entry 26: the class now lives in `tests/sealed_run_support.py`, and both `tests/application/test_stage_environment.py` and `tests/application/test_container_environment.py` import it from there. I changed no code and no test in this run. I ran `make check` in the foreground on the committed state and it is green: `test: green (65.7 s)`, coverage 99.55 %, `check: green`.

    What I built (unchanged since 0edf9d3f; entry 13 has the full list):
    - Deleted `src/factory/application/sealed_runs.py`.
    - Removed the five Git operations from `src/factory/application/git.py` and `src/factory/adapters/git_cli.py`, so Git has twenty-one.
    - Removed `RepositoryUnsealed` from `src/factory/domain/errors.py`, and the re-raise of it from `src/factory/application/dispatcher.py`.
    - `src/factory/application/scheduler.py`: `CheckoutPreparer.prepare` now only clones a missing checkout.
    - `src/factory/application/tick.py`: the restore no longer removes ignored paths.
    - `src/factory/application/stage_environment.py`: `run_agent` returns the `AgentRunResult` itself.
    - Removed the `nested_repository` stall and the probe's fault for it from `src/factory/application/stage.py` and `src/factory/application/preflight.py`.
    - Removed `nested_repository` from `src/factory/domain/journal.py` and `src/factory/domain/post_texts.py`.
    - `RECORDS_CONTRACT` is "3.0". I regenerated the schemas under `src/factory/contract/` with `uv run python -m factory.entry.contract`.

    Main choice: each environment calls the runtime in its own `run_agent`. I rejected a shared concrete helper on the abstract `StageEnvironment`, because the project's interfaces carry no behaviour.

    Refactor: there was no new diff in this round, so there was nothing to refactor.

    What the journal changed: nothing new in this round. The Description is outside my write paths.

    Noticed, not touched: `CheckoutPreparer` still stores `self._log` but never reads it. It stays, as the human decided in entry 14.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 34 known, 4 gone
29. factory: started review as self.
30. reviewer: Review, round 1. I read the work item, the diff's `--stat` and name-status, the whole diff under `src/` (the regenerated schemas aside), the round-1 move of `RecordingRun` and the two test modules it touched. I also searched `src` and `tests`, after the merge of `origin/main`, for names of the removed hygiene that might be left.

    no findings

    - Group 1: entry 22's reading still holds. Criteria 1 to 9 each have a test that checks what the criterion says, and the failing sides the Interface states are covered. The factory's `make check` after the coder was green (entry 28: `check: green`).
    - Group 2: the `src/` diff only removes code, apart from `run_agent`'s new return type. Each environment returns `(run or boundaries.agent_runtime.run)(request)`, as the Interface says. No layer gains an import.
    - Group 3: no marker that silences a check is added.
    - Group 4: last round's only finding is fixed. `RecordingRun` now lives once, in `tests/sealed_run_support.py`, and `tests/application/test_stage_environment.py` and `tests/application/test_container_environment.py` both import it from there. No copy is left.
    - Leftovers: none of `seal(`, `check_seal`, `remove_nested_repositories`, `remove_ignored`, `discard(`, `RepositoryUnsealed`, `nested_repository`, `sealed_runs`, `SealedRun`, `group_umask` or `TESTS_UMASK` is left in `src`. In `tests` the only hits are the new tests that check the names are gone, and `tests/entry/test_git_nested_repositories.py`, which belongs to the factory's git environment, which stays.
    - Group 5: the Description and the docs criterion match what was built.
    - `CheckoutPreparer._log` is stored and never read. It stays by the human's answer in entry 14.

    Earlier tests (files `main` held that the diff changes or deletes):
    - `tests/adapters/test_git_cli_ignored.py` (deleted): the Interface's test list (decision 22 of `feature.md`).
    - `tests/adapters/test_git_cli_nested.py` (deleted): the Interface's test list.
    - `tests/adapters/test_git_cli_seal.py`: the Interface's test list.
    - `tests/application/test_checkout_preparer_seal.py`: the Interface's test list.
    - `tests/application/test_container_environment.py`: the Interface's test list. Moving `RecordingRun` out of it falls under the standing leave to move a shared test helper.
    - `tests/application/test_dispatcher_unsealed.py` (deleted): the Interface's test list.
    - `tests/application/test_git_interface.py`: the Interface's test list.
    - `tests/application/test_interfaces.py`: the Interface's test list.
    - `tests/application/test_nested_repositories.py` (deleted): the Interface's test list.
    - `tests/application/test_sealed_project_commands.py` (deleted): the Interface's test list.
    - `tests/application/test_sealed_runs.py` (deleted): the Interface's test list.
    - `tests/application/test_sealed_runs_ignored.py` (deleted): the Interface's test list.
    - `tests/application/test_sealed_runs_no_home.py` (deleted): the Interface's test list.
    - `tests/application/test_sealed_runs_runner.py`: the Interface's test list.
    - `tests/application/test_stage_environment.py`: the Interface's test list. Moving `RecordingRun` out of it falls under the standing leave to move a shared test helper.
    - `tests/application/test_stage_environment_calls.py`: the Interface's test list.
    - `tests/application/test_stage_run_ignored.py` (deleted): the Interface's test list.
    - `tests/application/test_stall_environment.py`: the Interface's test list.
    - `tests/application/test_tick.py`: the Interface's test list.
    - `tests/application/test_tick_docstrings.py`: the Interface's test list.
    - `tests/application/test_tick_ignored.py` (deleted): the Interface's test list.
    - `tests/conftest.py`: the Interface's test list.
    - `tests/domain/test_contract.py`: the Interface's test list.
    - `tests/domain/test_contract_provider_limit.py`: the Interface's test list.
    - `tests/domain/test_contract_version_2.py`: the Interface's test list.
    - `tests/domain/test_stall_texts.py`: the Interface's test list.
    - `tests/sealed_run_support.py`: the Interface's test list (`leave` gone). It now holds `RecordingRun` as the shared place, under the standing leave to move a shared test helper.
    - `tests/test_home_reset_removed.py`: the Interface's test list.
    - `tests/test_tests_umask.py` (deleted): the Interface's test list.
31. factory: started docs as self.
32. documenter: Docs, round 1. The checkout's hygiene is removed, and the documentation now says so. I wrote the docs criterion's list, cross-read the rest and found no finding for the coder. The code matches the Interface: I read `git diff main...HEAD` over `src/` against it. I changed only documents, so I did not run `make check`. `make documents` printed `documents ok`.

    Files changed:
    - `docs/project-guide/git-and-hosting.md`: the five rows (`seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored`, `discard`) are gone. The count says twenty-one. *Restoring the checkout* says three and loses the `remove_ignored()` bullet. *Which part uses which operation* loses its row.
    - `docs/project-guide/stage-environment.md`:
      - *The stage environment* and *The container environment* now say `run_agent` returns the `AgentRunResult`.
      - The inline environment's `run_agent` is described as sealing and removing nothing.
      - The probe line and the tests line no longer name `run_sealed`.
      - `SealedRun` is gone.
      - The `project_commands` row of the wiring table already had no `SealedProjectCommands`, so I left it.
    - `docs/project-guide/stages.md`:
      - *The reasons* has ten, without `nested_repository`.
      - *After the agent run* loses the nested-repository rule, and the remaining steps are renumbered 1 to 5.
      - The launch step no longer says the inline environment seals.
    - `docs/project-guide/watching.md`:
      - The restore step no longer calls `remove_ignored()`.
      - The probe text no longer names `run_sealed`.
      - The dispatcher's `RepositoryUnsealed` re-raise is gone.
      - The module list loses `sealed_runs`.
      - `RepositoryUnsealed` is gone from the git-environment paragraph.
      - The "Every agent run is sealed" paragraph is replaced by a short *Agent runs* paragraph.
      - The preparer is described as: clone when `.git` is missing, otherwise do nothing, and `log` is unused.
    - `docs/project-guide/write-guard.md`: *Limits* no longer says `run_sealed` removes ignored paths. It now says the factory removes none and the take never brings one in.
    - `docs/project-guide/processes-and-checks.md`:
      - *Sealed project commands* is removed.
      - The paragraph on the tests' umask now says tests run under pytest's starting umask. It names the one exempt fixture, `umask_of`, from the human's answer (a) in entry 9, and the test `tests/test_tests_run_under_the_starting_umask.py`.
      - *Rules of `run`* and *Mutation testing* held no umask or seal text, so there was nothing to remove there.
    - `docs/project-guide/README.md`: the `watching.md` line loses `sealed_run_support`'s sibling module `sealed_runs`. The `conftest.py` line loses `group_umask`. The `sealed_run_support.py` line says the agent runs' completed result and request, and `RecordingRun` (the helper moved there in round 1).
    - `docs/operator-guide.md`:
      - The section is now *The checkout is cloned when it is missing*, and a kept checkout is not checked.
      - The sentences on the seal, the nested-repository removal and the project commands' ignored-state removal and umask are gone.
      - The stall note count says ten, and the nested-repository cause is gone.
      - The restore text says ignored paths stay. Its `checkout_restore_failed` text no longer mentions an ignored folder it cannot empty.
      - The cross-reference title is updated.
      - *The records contract* says `3.0` and why.
    - `docs/decisions.md`: the six entries you named each gain their closing line. The "disposable" one gets "The seal, the re-clone and the removal of ignored paths went with v1.2 F0044-S0006; the restore stays." The other five get "Replaced by the dataset's rollback, v1.2 F0044-S0006."
    - `README.md`: none, as the criterion says.

    Cross-read and found current: `docs/project-guide/agents.md` (the umask hits are opencode's run file, unrelated), `docs/project-guide/work-items.md` (the records contract text names no version) and the remaining `docs/decisions.md` entries.

    Stale text I saw and did not touch:
    1. `docs/operator-guide.md`, *Users and directories*, around line 695: the table row for `/work/checkout/.git` still says `2750`, `factory:factory-work`, "the factory alone writes it" and "the work tree around it stays group-writable". That is the second-user and group layout, which S0005 removed, and it is not on this story's docs criterion.
    2. `docs/operator-guide.md`, the `checkout_restore_failed` paragraph (around line 1211), still says "Repair with `chmod -R g+w <path>` as root". It belongs to the same second-user layout.
    3. `docs/operator-playbook.md` lines 55, 117, 118 and 194 mention a nested repository as an attempts-cap cause and the seal's umask rows. That file is the human's, and no stage keeps it.
    4. `docs/project-guide/processes-and-checks.md` line 15 keeps "the git folder sealed" as the title of a decision-log entry. That title is the entry's real name, so it is correct as it stands.

    `check`: check: green (not run again: passed on tree 121c8da73c66 at 2026-10-25T16:35:16Z)
    `secrets`: secrets: green (3.8 s)
    `documents`: documents ok
