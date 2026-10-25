# The checkout's hygiene is removed

## Description

v1.1 keeps the factory's own checkout clean of what an agent could leave in it: the git folder is sealed (its group and others' write bits taken) before every run and every project command and checked after, a repository nested in the work tree is removed and stalls the stage as `nested_repository`, the git-ignored paths are removed after every run and at the tick's restore, a checkout whose `.git` fails the check is cloned again, and the tests set their own umask because the seal refuses a group-writable checkout. On a `container` instance no agent and no project command touches the host's checkout: the agent works on the dataset, the checks run on a rolled-back copy, and the take brings in only the role's paths, `.git` and the ignored ones never among them. After S0005 (the second user is removed) no other user can write the checkout either. This story removes the hygiene: the four git operations of the seal and the cleaning and `discard`, `RepositoryUnsealed` and the dispatcher's re-raise, the re-clone in `CheckoutPreparer`, the removal of ignored paths at the restore, `factory.application.sealed_runs` whole (`run_sealed`, `SealedRun`, `SealedProjectCommands`), the stall reason `nested_repository` and its note, the probe's nested-repository fault, and the tests' umask. `StageEnvironment.run_agent` returns the run's result itself, now that a sealed run carries nothing else (F0042's decision 2 named this move). Removing a value of the stall reasons narrows a contract model, so the records contract rises to 3.0 (decision 5 of `feature.md`). What stays: the tick's restore of the checkout (`reset_to("HEAD")`, the switch to `main`, the deletion of local work-item branches); the clone of a missing checkout; the factory's git environment (the credential helper, no hooks, no fsmonitor); the stall reason `left_branch` (decision 14); the take's ignore filter (`Git.ignored`).

## Interface

Removed whole: `src/factory/application/sealed_runs.py`.

`factory.application.git.Git` (`application`) loses the operations `seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored` and `discard`, which leaves twenty-one; `factory.adapters.git_cli.GitCli` loses them with `_check_git_folder`, `_raise_unsealed`, `_nested_repositories` and the helpers only they use.

`factory.domain.errors`: `RepositoryUnsealed` goes. `factory.application.dispatcher`: its `except RepositoryUnsealed: raise` goes (every handler error is counted).

`factory.application.scheduler.CheckoutPreparer.prepare()` (`application`): clones when `<checkout>/.git` does not exist; otherwise does nothing (no check, no log line, no clone again).

`factory.application.tick` (`application`): `_restore_checkout` removes no ignored paths.

`factory.application.stage_environment` (`application`):

```python
@abstractmethod
def run_agent(self, request: AgentRunRequest, *, run: Callable[[AgentRunRequest], AgentRunResult] | None = None) -> AgentRunResult: ...
```

- Both environments return `(run or boundaries.agent_runtime.run)(request)`; the inline one seals nothing.

`factory.application.stage` (`application`): `LaunchedStage.nested_repositories` and the branch of `_early_stall` that stalls `nested_repository` go. `factory.application.preflight.agent_run_probe_item`: the fault `the probe run left a git repository in the work tree, ...` goes.

`factory.domain.journal.StallReason` loses `nested_repository`; `factory.domain.post_texts` loses its stall sentence. `factory.domain.contract.RECORDS_CONTRACT = "3.0"`; the five schemas regenerated (`work-item-state` and `acceptance-state` lose the value).

`factory.entry.wiring`: `_project_commands` builds no `SealedProjectCommands` (S0005 left none).

Tests (the leave is decision 22 of `feature.md`):

- Deleted whole: `tests/adapters/test_git_cli_ignored.py`, `tests/adapters/test_git_cli_nested.py`, `tests/application/test_dispatcher_unsealed.py`, `tests/application/test_nested_repositories.py`, `tests/application/test_sealed_project_commands.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_sealed_runs_ignored.py`, `tests/application/test_stage_run_ignored.py`, `tests/test_tests_umask.py`, the helper module `tests/sealed_run_support.py`.
- `tests/adapters/test_git_cli_seal.py`: every test but `test_git_never_reaches_a_repository_above_a_working_copy_whose_git_folder_is_broken` is deleted (the two `discard` tests with the operation).
- `tests/application/test_checkout_preparer_seal.py`: `test_a_missing_checkout_is_cloned_and_sealed` becomes `test_a_missing_checkout_is_cloned` and `test_a_sealed_checkout_is_kept_and_sealed_again_without_a_log_line` becomes `test_an_existing_checkout_is_kept_without_a_log_line`; `test_a_checkout_whose_git_folder_fails_the_check_is_removed_and_cloned_again` and `test_a_checkout_that_cannot_be_discarded_is_the_repository_unavailable_stop` are deleted.
- `tests/application/test_sealed_runs_runner.py`: `test_a_sealed_run_calls_its_runner_instead_of_the_runtime` is deleted; `test_the_probe_does_not_wait_out_a_provider_limit` stays.
- `tests/application/test_git_interface.py`: `OPERATIONS` loses the five names and `test_git_has_exactly_the_twenty_six_operations_and_git_cli_has_each` becomes `..._twenty_one_...`; `tests/application/test_interfaces.py::test_git_abstract_methods_are_exactly_its_twenty_six_operations` becomes `..._twenty_one_...`, the same assertion.
- `tests/application/test_stage_environment.py::test_run_agent_is_the_sealed_run_through_the_runtime_or_the_given_run` (the result itself) and `::test_run_agent_removes_a_nested_repository_and_names_it` (deleted); `tests/application/test_container_environment.py::test_run_agent_runs_unsealed_through_the_runtime_or_the_given_run` and `::test_run_agent_leaves_nested_repositories_ignored_files_and_the_home` (they read the result itself); the stand-ins `RecordingEnvironment.run_agent` of `tests/application/test_stage_environment_calls.py` and `TakingEnvironment.run_agent` of `tests/application/test_stall_environment.py` return the result; `tests/application/test_stage_environment_calls.py::test_the_preflight_does_not_import_the_sealed_run` is deleted.
- `tests/domain/test_stall_texts.py::test_each_stall_cause_is_its_sentence_alone_or_with_the_detail`: the row `nested_repository` goes; `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` and `tests/domain/test_contract_provider_limit.py::test_the_committed_schemas_list_provider_limit_at_version_1_2` read `3.0`.
- `tests/conftest.py`: `pytest_configure`'s `os.umask`, `TESTS_UMASK` and the fixture `group_umask` go, with every use of `group_umask` (`tests/application/test_checkout_preparer_seal.py`).

## Acceptance criteria

1. The removed names (rows of one parametrized test): `importlib.util.find_spec("factory.application.sealed_runs")` is `None`; `Git.__abstractmethods__` holds none of `seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored`, `discard` and has exactly twenty-one names; `GitCli` has none of them; `RepositoryUnsealed` is no attribute of `factory.domain.errors`; `"nested_repository"` is not in `typing.get_args(StallReason)`; `LaunchedStage.model_fields` holds no `nested_repositories`.
2. The preparer (rows of one parametrized test on a real bare remote): with no checkout, `prepare()` clones it and writes no log line; with a cloned checkout whose `.git` is group-writable, `prepare()` changes nothing (the mode stays, no clone, no log line); with a cloned checkout that holds a nested repository `sub/.git`, `prepare()` leaves it.
3. The restore keeps the ignored files: a tick's restore on a checkout that holds an ignored file `.venv/x` and an untracked changed file `src/a.py` discards `src/a.py` and logs `discarded uncommitted changes: src/a.py`, leaves `.venv/x`, and ends on `main` at `origin/main`.
4. `run_agent` returns the result (rows of one parametrized test over both environments with `FakeAgentRuntime`): the value is the queued run's `AgentRunResult`; with `run` given, `run` is called once and its result returned.
5. A stage whose agent leaves a nested repository no longer stalls for it (one test through `StageRunner` on the `boundaries` fixture, an intake stage, whose scripted run writes `sub/.git/HEAD` and decides `tests`): the work item moves to `tests`, and its journal's last entry is the intake's result, not a stall.
6. The dispatcher counts every error (one test): a handler that raises `GitError("seal", None, "x")` gives `handled` false and an error counted for the event, as for any other `GitError`.
7. The contract (rows of one parametrized test): `RECORDS_CONTRACT == "3.0"`; each committed schema holds `"x-records-contract": "3.0"` and equals the generated one; no schema names `nested_repository`.
8. A test runs under the umask pytest was started with: no module under `tests/` calls `os.umask` (one test reading the files).
9. `make check` stays green.
10. docs: `docs/project-guide/git-and-hosting.md`: the rows of `seal`, `check_seal`, `remove_nested_repositories`, `remove_ignored` and `discard` go and the count says twenty-one; `docs/project-guide/stage-environment.md`, *The stage environment*: `run_agent` returns the result; `docs/project-guide/stages.md` and `docs/project-guide/watching.md` (the dispatcher, the preparer, the restore): no seal, no re-clone, no removal of ignored paths, no `RepositoryUnsealed`; `docs/project-guide/processes-and-checks.md`, *Sealed project commands*: removed; `docs/project-guide/README.md`, *The files*: the lines follow; `docs/operator-guide.md`: *The checkout is cloned again when it is missing or its `.git` is not the factory's alone* becomes *The checkout is cloned when it is missing* (a kept checkout is not checked), the stall `nested_repository` goes from the stall table and every sentence on the seal, the removal of ignored paths or the tests' umask goes; *The records contract*: `3.0` and why. `docs/decisions.md`: the entries "No nested repository in the work tree", "The factory removes the git-ignored paths after every agent run and at the restore", "The tests set their own umask, and uv syncs under the caller's" and "The checkout is disposable and restored to `origin/main` at the start of every tick" each gain one closing line ("Replaced by the dataset's rollback, v1.2 F0044-S0006"; the last: "The seal, the re-clone and the removal of ignored paths went with v1.2 F0044-S0006; the restore stays"). `README.md`: none.

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
