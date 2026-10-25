---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 453
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T19:57:00.190824Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T19:57:00.196674Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T19:57:21.087779Z'
  stage: intake
  run: 94a37b3b8e254dd3bf75ad298c490e50
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T19:57:41.520956Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T20:03:55.540186Z'
  stage: tests
  run: fe5c504d0ff446c4a0ee38e98232d859
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T20:04:16.545242Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T20:07:29.117632Z'
  stage: doing
  run: 6c4472b3213446968173b706093081ec
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-25T20:07:50.327836Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-25T20:09:35.589260Z'
  stage: review
  run: 4b1791f8cd624dc0bea4c5d967e6ddd0
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-25T20:09:56.151653Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-25T20:13:00.196789Z'
  stage: docs
  run: 3b4d2d0c5c044bd6b84aae1e5b004216
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-25T20:13:21.185170Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-25T20:13:55.963901Z'
  stage: smoke-test
  run: ba45922f5c764ff89864d443dffdc677
---

# The Docker path and the host's process table are removed

## Description

v1.1 runs as one long-lived Docker container: `image/Dockerfile` builds the factory with its two users, `sudo`, `/etc/gitconfig` and the read-only installs; `image/compose.yml` starts it with `init: true`, the volumes and the login mounts; `image/entrypoint.sh` sets the umask and installs the agents; and the process module ends a timed-out command by reading the kernel's process table, because an agent's code on the host could leave processes in groups of their own. On the VM of F0043 (the machine and the stage image) the factory runs as a systemd service from `vm/setup.sh`, the stages run in the stage image of `vm/Dockerfile`, and no agent code runs on the host: what the factory starts there is git, `zfs` and `podman`, and a container ends whole with its call. After S0008 (the inline environment and its setting are removed) and the human's change 0 of `feature.md` (`self` is stopped), nothing uses the Docker path. This story removes it: every file under `image/` but the credential helper, which moves to `vm/git-credential-factory` because the factory's git on the VM reaches the token only through it (decision 12 of `feature.md`), and every test that pins those files; and it shrinks the kill of a timed-out command to the kill of its process group, removing the process table reading and `factory.domain.sessions` (decision 7). What stays: `vm/Dockerfile`, `vm/setup.sh`, `vm/factory.service` and their tests; the credential helper's behaviour and its installed path `/usr/local/bin/git-credential-factory`; a command that reaches its time limit is ended with every process of its process group and read as `timed_out`.

## Interface

Removed: `image/Dockerfile`, `image/compose.yml`, `image/entrypoint.sh`, `image/sudoers-factory-agent`, `image/gitconfig`. Moved unchanged: `image/git-credential-factory` to `vm/git-credential-factory`. `image/secrets/` is the human's and untracked; no stage touches it.

`vm/setup.sh`: the `tools` step installs `vm/git-credential-factory` of the checkout as `/usr/local/bin/git-credential-factory`, in place of `image/git-credential-factory`, under the rule it has today (mode `0755`, only in the run that made the clone or when the installed file is missing; an installed file that differs is reported and left); nothing else in the script changes. `vm/Dockerfile`: its second comment line becomes `# Every reference is pinned (docs/decisions.md).`; nothing else in it changes. `vm/Dockerfile` builds `FROM ${BASE_IMAGE}`, not from the factory's image, and `vm/setup.sh` installs the factory's code from its own clone, so nothing on the VM reads `image/` but the helper.

Removed whole: `src/factory/domain/sessions.py`.

`factory.adapters.process` (`adapters`): `read_process_table`, `_kill_one`, `_PROCESS_TABLE` and `_ROUND_PAUSE_SECONDS` go; `_kill_session(process)` sends `SIGKILL` to the child's process group (`os.killpg(process.pid, signal.SIGKILL)`, a group already gone being no error) and reads no table. It does not wait for the group's processes to end, so a grandchild may still be ending for a moment after the call returns. The docstrings of `run_process` and `run_streaming` and the comment in `_kill_session` say "process group" where they say "session".

Tests (the leave is decision 26 of `feature.md`):

- Deleted whole: `tests/test_image.py`, `tests/test_image_credentials.py`, `tests/test_image_gitconfig.py`, `tests/test_image_users.py`, `tests/test_opencode_image.py`, `tests/test_opencode_config_folder.py`, `tests/test_compose.py`, `tests/test_compose_init.py`, `tests/test_compose_project.py`, `tests/test_entrypoint.py`, `tests/test_entrypoint_skills.py`, `tests/test_entrypoint_umask.py`, `tests/test_entrypoint_support.py`, `tests/test_agent_home_ownership.py`, `tests/test_api_login_mount.py`, `tests/test_claude_token_mount.py`, `tests/test_token_folder.py`, `tests/adapters/test_process_table.py`, `tests/domain/test_sessions.py`, and the helper modules `tests/compose_support.py`, `tests/entrypoint_support.py`, `tests/leftovers_support.py`. Before `tests/test_image.py` goes, the tester moves into `tests/dockerfile_support.py` the readers `tests/test_stage_image.py` imports from it (`DIGEST`, `THREE_NUMBERS`, `Command`, `Instruction`, `_arg_defaults`, `_commands`, `_env`, `_from_references`, `_instructions`, `_pipelines`, `floating_references`) with every constant and private helper they use (`DOCKER_KEYWORDS`, `NPM_PINNED`, `APT_PINNED`, `PIP_PINNED`, `SHELL_OPERATOR`, `VARIABLE`, `LATEST`, `_substitute`, `_shell_lines` and the `_*_findings` functions); `tests/dockerfile_support.py` loses `DOCKERFILE` and `dockerfile_instructions`, which only deleted modules use. Five tests of `tests/test_image.py` read no file under `image/` and move, names and assertions unchanged, into a new `tests/test_pins.py`: `test_a_floating_item_is_reported`, `test_a_pinned_item_is_not_reported`, `test_installed_versions_equal_the_locked_and_pinned_ones`, `test_the_template_has_no_placeholder_files_and_no_tasks_directory` and `test_the_build_backend_is_pinned`; every other test of the module goes with it.
- `tests/conftest.py`: the fixtures `compose_service` and `image_layout` go with their imports; `tests/test_shared_test_helpers.py::test_the_image_layout_fixture_returns_the_entrypoints_layout` is deleted, and so is the row `image-layout` of `tests/test_shared_test_helpers.py::test_each_shared_helper_is_written_in_one_module` (the `Layout(tmp_path)` it looks for leaves `conftest.py` with the fixture).
- F0043's `tests/vm_support.py`, `tests/test_vm_setup.py` and `tests/test_vm_setup_writes.py` import `ROOT` and `SYSTEM_PATH` from `tests/entrypoint_support.py`: both move into `tests/vm_support.py`, and the two test modules import `SYSTEM_PATH` from there; nothing else in them changes.
- `tests/test_git_credential_helper.py`: `HELPER` is `ROOT / "vm" / "git-credential-factory"`; every test keeps its name and assertions.
- F0043-S0001's `tests/test_stage_image.py`: its imports come from `tests/dockerfile_support.py`; the fixture `machine_instructions` goes; `test_the_stage_image_carries_the_machine_images_pins` becomes `test_each_pin_of_the_stage_image_has_its_form`, its five rows without the comparison with `image/Dockerfile`: `BASE_IMAGE` ends with a digest (`DIGEST`), `CLAUDE_CODE_VERSION`, `OPENCODE_VERSION` and `UV_VERSION` are three numbers (`THREE_NUMBERS`), and `FACTORY_OPENCODE_MODELS` maps `opus`, `sonnet` and `haiku` each to a `<provider>/<model>`; `test_each_debian_package_is_pinned_as_the_machine_image_pins_it` becomes `test_each_debian_package_is_pinned`, its seven rows keeping one install of the package at a version that is neither empty nor `*`; the module's docstring drops "as the machine's image pins them".
- F0043-S0003's `tests/test_vm_setup_text.py` names no `image/` path (its rows name the installed `/usr/local/bin/git-credential-factory`) and stays as it is.
- The pre-check ran the suite on a copy with this story's code: every test that failed is named above.
- `tests/adapters/test_process_session.py`: `test_time_limit_of_a_make_target_ends_what_timeout_started` and `test_process_the_kill_cannot_reach_does_not_hold_the_call` are deleted, with the import of `MakeProjectCommands`; `test_time_limit_ends_every_process_of_the_session` becomes `test_time_limit_ends_every_process_of_the_group`: its rows `run_process-group` and `run_streaming-group` (the grandchild stays in the child's process group) expect it ended through `is_gone(pid)` with its default wait, and its rows `run_process-own-group`, `run_streaming-own-group`, `run_process-own-session` and `run_streaming-own-session` (the grandchild takes a group or a session of its own) expect it still running (`is_gone(pid, within=0)` is `False`), the fixture `pid_file` killing it after; `test_stop_and_error_of_the_callback_end_every_process_of_the_session` becomes `test_stop_and_error_of_the_callback_end_every_process_of_the_group`, its child leaving the grandchild in the child's group (`"{}"` in place of `OWN_GROUP`) and the end checked through `is_gone(pid)` with its default wait.

## Acceptance criteria

1. The files (rows of one parametrized test over the repository root): `image/Dockerfile`, `image/compose.yml`, `image/entrypoint.sh`, `image/sudoers-factory-agent`, `image/gitconfig` and `image/git-credential-factory` do not exist; `vm/git-credential-factory` exists, is executable and holds the text `image/git-credential-factory` held on `main` before this story (the reviewer checks the move in the diff).
2. The credential helper (the tests of `tests/test_git_credential_helper.py` on `vm/git-credential-factory`): `get` with a readable token file prints `username=x-access-token` and `password=<the token>`; `get` without a readable token file prints nothing and exits 1; any other operation prints nothing and exits 0; `git credential fill` through the factory's git environment gets the token.
3. The script installs the moved helper (one test reading `vm/setup.sh` with its comment lines dropped): the `tools` step's text holds `vm/git-credential-factory` and `/usr/local/bin/git-credential-factory`, and the script holds `image/` nowhere; `sh -n vm/setup.sh` exits 0.
4. The removed names (rows of one parametrized test): `importlib.util.find_spec("factory.domain.sessions")` is `None`; `read_process_table` is no attribute of `factory.adapters.process`; no module under `src/factory` reads `/proc`.
5. The kill at the limit (rows of one parametrized test; every row whose child must start first gets `ROOMY_LIMIT` and bounds the call by `ROOMY_BOUND_SECONDS` of `tests/time_limits.py`): a child that starts a grandchild in the child's own process group (the grandchild takes no group and no session of its own) and both sleep 60 seconds ends `timed_out` with `exit_status` `None` within the bound, through `run_process` and through `run_streaming`, and the grandchild has ended within `GONE_WITHIN_SECONDS` of `tests/process_support.py` after the call returns (`is_gone(pid)` with its default wait); a grandchild that takes a process group of its own (`process_group=0`) or a session of its own is not ended (`is_gone(pid, within=0)` is `False`; the test kills it after); a kill that finds the group already gone (`os.killpg` patched to kill the group and then raise `ProcessLookupError`) is no error, and the call still ends `timed_out`; a child that ends by itself before its limit is not `timed_out` and keeps its exit status; a callback of `run_streaming` that asks to stop, and one that raises, end the child and the grandchild in the child's group the same way (the stop gives `stopped`, the raise propagates its exception).
6. No test reads a file under `image/` (one test over the text of every `.py` file under `tests/`): no module but those of the tests of criteria 1 and 6 holds the text `"image/` or `'image/` (a string literal, an f-string included, that begins `image/`), or a `/` followed by optional spaces and `"image"` or `'image'` (a path built with the part `image`); a string `"image"` that is no path part, such as a record's key, is allowed.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`: the chapter `## The machine's image` goes, but its subsection *The image on the cost records* moves under `## The machine` and names the file `FACTORY_IMAGE_ID_FILE` names in place of `/opt/factory/image-id`; the chapter `## The container: compose, entrypoint and health check` becomes `## The preflight and the health check`: its opening with the compose table, *The init* and *The entrypoint* go; *The hosting-service token* keeps the token file `FACTORY_TOKEN_FILE` names in a folder only the factory's user can enter, the credential helper, the allow list of an agent run's environment and the four faults of the item `token-file`, without Compose, `image/secrets/` and the checks with `docker exec`; *The health check and the restart policy* keeps what `factory-health` reads and prints, without Docker's interval and `restart:`; *The preflight's items*, *The probe of the agent run*, *The stamp and the probe of the main branch* and *The wait for a repository that is not ready* stay as they are, so every reference to them still finds them; the chapter `## Container runtimes` goes whole (on the VM Podman runs on the host, see `## The machine`); every sentence that names `image/compose.yml`, `image/entrypoint.sh`, `init: true`, the `claude-home` volume or `docker compose` goes; *The stage image*: a pin is changed in `vm/Dockerfile` alone, with the steps of *Update the pins* (without `image/compose.yml`, `sudo` and `tests/test_image.py`), and checked with `uv run pytest tests/test_stage_image.py`; what an operator of v1.1's container needs is one line that points to the tag `v1.1`; the list at the guide's top follows, and `## The machine`'s step 11 (`tools`) in *The steps* and *The rebuild after a merge* name `vm/git-credential-factory`; `docs/project-guide/processes-and-checks.md`, *Starting a process*: the kill of a timed-out command is the kill of its process group; `docs/project-guide/README.md`, *Shared test helpers*: the lines of the deleted helper modules go; `README.md`: no `docker compose` and no `image/`, and the run instructions point to `vm/setup.sh` and the chapter `## The machine`. `docs/decisions.md`: the entries "The container runtime's init reaps the processes a killed run leaves", "A command stopped at its time limit loses every process of its session", "The entrypoint sets no git configuration and starts in `/opt/factory`", "Every tool of the machine's image is pinned, and its identity is generated at build", "The compose project is named after the instance", "The agent home belongs to the factory; the agent adds files and cannot change the installed ones" and "opencode's configuration folder is made by the image, read-only to the agent" each gain one closing line: "Replaced by the machine of v1.2 (`vm/`), F0044-S0010" (the session entry: "The process group is killed; no agent code runs on the host since v1.2, F0044-S0010"), and so do the entries "Three top-level paths for the product beyond `src/` and `tests/`", "The token is a bind mount into a folder only the factory can enter", "The agent's git trusts the shared checkout", "The agent's login is a token from a file", "An agent run logs in with an API key when its file holds one" and "The agents load a project's skills, and the agent's home gets none". `docs/operator-guide.md`, *The agent runtime*: the login token and the API key are the files `## The machine` places in `/home/factory/.secrets/`, with no `image/secrets/`, no Compose and no `docker exec`; *The stage image* names no `image/Dockerfile`.

## Smoke test

```bash
ls image/Dockerfile image/compose.yml image/entrypoint.sh 2>/dev/null | wc -l; test -x vm/git-credential-factory && echo helper-moved; uv run python -c 'import factory.domain.sessions' 2>/dev/null && echo present || echo gone
```
Expect: three lines: `0`; `helper-moved`; `gone`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete paths and signatures: the five removed `image/` files, the helper's move to `vm/git-credential-factory`, `vm/setup.sh`'s `tools` step, `factory.domain.sessions` removed whole, and `factory.adapters.process._kill_session(process)` with `os.killpg(process.pid, signal.SIGKILL)`. The tests to delete, move and change are listed by name, and decision 26 of `feature.md` gives the leave. Two things have no test: the one-line comment change in `vm/Dockerfile` and the docstring wording "process group". Neither is behaviour, so I left them for the reviewer to check in the diff.
   Criteria: each is testable by a parametrized test. Criterion 1 covers the files, 2 the helper's three behaviours plus `git credential fill`, 3 the script's text and `sh -n`, and 4 the removed names. Criterion 5 covers both sides of the kill: the grandchild in the child's group is ended, one with its own group or session is not, an already-gone group is no error, and a child that ends by itself keeps its exit status. It also covers the stop and the raise of the `run_streaming` callback and both `run_process` and `run_streaming`. Criterion 6 is a text scan of `tests/`, 7 is `make check`, and 8 is the docs.
   Smoke test: one runnable command line, and its `Expect:` line gives three checkable lines (`0`, `helper-moved`, `gone`). It runs no pytest, so the `-q` rule does not apply.
   Architecture: the removal fits the layers. The process kill stays in the one process wrapper in `adapters`, `domain.sessions` goes, and nothing new is added. `vm/` is within the coder's write paths.
   Scope: it matches S0010 in `feature.md` and decisions 7, 12 and 40, and nothing is in "Out of scope". `image/secrets/` and `.gitignore` are untouched, and `pipeline.yml`, `pyproject.toml` and the demo README are left to the human's changes 10 and 11.
4. factory: started tests as self.
5. tester: Wrote the tests for the criteria and made the test changes the Interface lists (the leave is decision 26 of `feature.md`).

   Criterion → test:
   - criterion 1: tests/test_docker_path_removed.py::test_the_docker_files_are_gone_and_the_helper_is_moved (7 rows: the six `image/` files absent; `vm/git-credential-factory` is a file and executable. The criterion leaves the text comparison with `main` to the reviewer, so the test does not compare it.)
   - criterion 2: tests/test_git_credential_helper.py (existing tests, unchanged except `HELPER = ROOT / "vm" / "git-credential-factory"`): test_get_prints_the_user_name_and_the_token_from_the_file, test_get_without_a_readable_token_file_prints_nothing_and_fails, test_any_other_operation_prints_nothing_and_succeeds, test_git_credential_fill_gets_the_token_through_the_factorys_git_environment
   - criterion 3: tests/test_docker_path_removed.py::test_the_setup_script_installs_the_moved_helper
   - criterion 4: tests/test_docker_path_removed.py::test_the_process_table_names_are_removed (rows sessions-module, read_process_table, proc)
   - criterion 5: tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group (6 rows: the grandchild in the child's group is ended, checked with `is_gone(pid)`; one in its own group or own session is not, checked with `is_gone(pid, within=0) is False`); ::test_stop_and_error_of_the_callback_end_every_process_of_the_group (the child placed with `"{}"`, checked with `is_gone(pid)`); ::test_a_call_without_a_group_to_kill_ends_as_its_child_does (rows group-already-gone, with `os.killpg` patched to kill and then raise `ProcessLookupError`, giving `timed_out` and no exit status; run_process-ends-by-itself and run_streaming-ends-by-itself, giving not `timed_out` and exit status 3). The criterion says "one parametrized test", but the Interface names the two renamed tests and their rows. I kept those as the Interface says and put the remaining rows into one new test.
   - criterion 6: tests/test_docker_path_removed.py::test_no_test_reads_a_file_under_image (uses `search_support.modules_matching` and leaves out its own module; criteria 1 and 3 live in the same module, so it can name `image/`)
   - criteria 7 and 8: no tests (`make check`, docs).

   Files created: tests/test_docker_path_removed.py, tests/test_pins.py (the five tests moved from test_image.py, names and assertions unchanged).
   Files changed, as the Interface says:
   - tests/dockerfile_support.py: now holds the readers, constants and `_*_findings` helpers moved from test_image.py, plus `_env`; `DOCKERFILE` and `dockerfile_instructions` are gone.
   - tests/test_stage_image.py: imports from dockerfile_support; `machine_instructions` is gone; the two tests are renamed to test_each_pin_of_the_stage_image_has_its_form and test_each_debian_package_is_pinned; the docstring is updated.
   - tests/vm_support.py: now holds `ROOT` and `SYSTEM_PATH`.
   - tests/test_vm_setup.py and tests/test_vm_setup_writes.py: import `SYSTEM_PATH` from vm_support.
   - tests/conftest.py: `compose_service`, `image_layout`, their imports and the unused `YAML` import are gone.
   - tests/test_shared_test_helpers.py: the `image-layout` row and the layout fixture test are deleted.
   - tests/adapters/test_process_session.py: the make-target test, the unreachable-kill test and the `MakeProjectCommands` import are deleted.
   Deleted: the 19 test modules and the 3 helper modules the Interface lists.

   Test run: `make test` fails as intended, and no module failed to import. The failures are the files still present or missing (criterion 1, criterion 3 and the credential helper tests: FileNotFoundError on `vm/git-credential-factory`), `factory.domain.sessions` / `read_process_table` / `/proc` still present, and the `own-group` rows, because today's table-reading kill still ends the grandchild in a group of its own. I ran `make test` twice by mistake (the second run only to read its last lines); both gave the same result. `make lint` is green. I skipped the type check, as this stage says.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/adapters/test_process_session.py::test_time_limit_ends_every_process_of_the_group[run_streaming-own-group] - AssertionError: assert True is False
6. factory: started doing as self.
7. coder: Removed the Docker path and the process-table kill. `make check` is green: lint, types, layers, sast, secrets, licenses and test (61.4 s), ending `check: green`.

   Built:
   - Removed `image/Dockerfile`, `image/compose.yml`, `image/entrypoint.sh`, `image/sudoers-factory-agent` and `image/gitconfig`. Moved `image/git-credential-factory` unchanged to `vm/git-credential-factory` with `git mv`; it keeps its mode, and git records it as a rename with the content the same.
   - `vm/setup.sh`: in the `tools` step, the `cmp` and the `install` now read `$checkout/vm/git-credential-factory`. The rest of the step is unchanged.
   - `vm/Dockerfile`: the second comment line is now `# Every reference is pinned (docs/decisions.md).`
   - Removed `src/factory/domain/sessions.py`.
   - `src/factory/adapters/process.py`: `read_process_table`, `_kill_one`, `_PROCESS_TABLE`, `_ROUND_PAUSE_SECONDS` and the `factory.domain.sessions` import are gone. `_kill_session` only calls `os.killpg(process.pid, signal.SIGKILL)` and suppresses `ProcessLookupError`. Its comment now says why the group is enough: no agent code runs on the host. "session" became "process group" in the docstrings of `run_process` and `run_streaming`, and in the comments of `_has_ended` and `_read_bounded`, because both of those comments mean the same id or group. `run_process`'s first docstring line is shorter ("kill its process group at the time limit"), because "every process of its process group" went past the 100-column limit.

   Main choice: I kept the name `_kill_session`, as the Interface names it, and did not rename it to `_kill_group`. A rename would have gone beyond the Interface and changed the name the tests and the reviewer look for.

   Refactor: I read the diff and found nothing more to change.

   Noticed but not touched:
   - `pyproject.toml` line 142: mutmut's `also_copy` still lists `"image/"`, which no longer exists. It may break `make mutants`. Intake left `pyproject.toml` to the human's changes 10 and 11.
   - `security/duplicates-baseline.txt` may hold entries for the removed code. I did not run `make duplicates` and did not check.
   - The docs criterion (8) is left for the docs stage.

   The journal did not change the meaning of the task, so I left `## Description` as it is.

   `check`: check: green
   `duplicates`: duplicates: 8 new, 35 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I checked (round 0):
   - Criterion 1: `tests/test_docker_path_removed.py::test_the_docker_files_are_gone_and_the_helper_is_moved` has seven rows: the six `image/` files are absent, and `vm/git-credential-factory` exists and is executable. In the diff the helper's move shows as `R100 image/git-credential-factory -> vm/git-credential-factory` with mode 100755, so its text is the same as on `main`.
   - Criterion 2: the four tests of `tests/test_git_credential_helper.py` are unchanged except `HELPER`.
   - Criterion 3: `test_the_setup_script_installs_the_moved_helper` reads `setup_code()` (comment lines dropped) and the `tools` step text, and checks that `sh -n` exits 0. The diff of `vm/setup.sh` changes only the two paths, in the `cmp` and the `install`.
   - Criterion 4: three rows of one parametrized test.
   - Criterion 5: the group rows check `is_gone(pid)` with its default wait. The own-group and own-session rows check `is_gone(pid, within=0) is False`, and the `pid_file` fixture kills the grandchild after. The rows for a group already gone (`os.killpg` patched to kill and then raise) and for a child that ends by itself (both runners, exit status 3) form a third parametrized test. The criterion asks for one test, but the Interface names the two renamed tests, so three is acceptable. Every row whose child must start gets `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS`.
   - Criterion 6: `IMAGE_PATH` through `search_support.modules_matching`, with its own module left out. That module holds the tests of criteria 1, 3 and 6.
   - The factory's `make check` after the coder was green (entry 7).
   - Architecture and security: `_kill_session` in `src/factory/adapters/process.py` is now one `os.killpg` with `ProcessLookupError` suppressed. The `factory.domain.sessions` import and the module are gone, and no new marker, dependency or layer import was added. The docstrings and comments say "process group" where the Interface asks. The `vm/Dockerfile` comment line is as the Interface states.
   - Quality: I compared the moved code by AST. The readers, constants and `_*_findings` helpers in `tests/dockerfile_support.py` are identical to those of `tests/test_image.py` on `main`. The five tests and their helpers in `tests/test_pins.py` are identical too: names and assertions unchanged.
   - `make duplicates`: 8 new. All are in files this diff does not touch (`claude_runtime`, `opencode_runtime`, `fake_containers`, `podman_runs`, `zfs_snapshots`, `fake_snapshots`, `make_commands`), so none is this story's.
   - Hygiene: the Description matches what was built. Criterion 8 still describes the docs work.
   - Open, outside this diff's scope: `image/` is still named in `pyproject.toml:142` (mutmut `also_copy`), `.gitignore:15-16` and `demo/todo-service/README.md`. Intake left these to the human's changes 10 and 11.

   Earlier tests (each changed or deleted under the human's leave, decision 26 of `feature.md`, which the story's Interface names; no change goes beyond what the Interface lists):
   - tests/adapters/test_process_session.py: human's leave, decision 26
   - tests/adapters/test_process_table.py (deleted): human's leave, decision 26
   - tests/compose_support.py (deleted): human's leave, decision 26
   - tests/conftest.py: human's leave, decision 26
   - tests/dockerfile_support.py: human's leave, decision 26
   - tests/domain/test_sessions.py (deleted): human's leave, decision 26
   - tests/entrypoint_support.py (deleted): human's leave, decision 26
   - tests/leftovers_support.py (deleted): human's leave, decision 26
   - tests/test_agent_home_ownership.py (deleted): human's leave, decision 26
   - tests/test_api_login_mount.py (deleted): human's leave, decision 26
   - tests/test_claude_token_mount.py (deleted): human's leave, decision 26
   - tests/test_compose.py (deleted): human's leave, decision 26
   - tests/test_compose_init.py (deleted): human's leave, decision 26
   - tests/test_compose_project.py (deleted): human's leave, decision 26
   - tests/test_entrypoint.py (deleted): human's leave, decision 26
   - tests/test_entrypoint_skills.py (deleted): human's leave, decision 26
   - tests/test_entrypoint_support.py (deleted): human's leave, decision 26
   - tests/test_entrypoint_umask.py (deleted): human's leave, decision 26
   - tests/test_git_credential_helper.py: human's leave, decision 26
   - tests/test_image.py (deleted; five tests moved to tests/test_pins.py unchanged): human's leave, decision 26
   - tests/test_image_credentials.py (deleted): human's leave, decision 26
   - tests/test_image_gitconfig.py (deleted): human's leave, decision 26
   - tests/test_image_users.py (deleted): human's leave, decision 26
   - tests/test_opencode_config_folder.py (deleted): human's leave, decision 26
   - tests/test_opencode_image.py (deleted): human's leave, decision 26
   - tests/test_shared_test_helpers.py: human's leave, decision 26
   - tests/test_stage_image.py: human's leave, decision 26
   - tests/test_token_folder.py (deleted): human's leave, decision 26
   - tests/test_vm_setup.py: human's leave, decision 26
   - tests/test_vm_setup_writes.py: human's leave, decision 26
   - tests/vm_support.py: human's leave, decision 26
10. factory: started docs as self.
11. documenter: Docs round 0: no findings. The diff and the Interface agree on everything the docs state. I ran no `make check`, because I changed documents only; `make documents` printed `documents ok`.

    Files I changed:
    - `docs/operator-guide.md`:
      - Deleted the chapters `## The machine's image` and `## Container runtimes`, and the sections *The init* and *The entrypoint*.
      - *The image on the cost records* now sits under `## The machine` and names the file `FACTORY_IMAGE_ID_FILE` names.
      - `## The container: compose, entrypoint and health check` is now `## The preflight and the health check`. *The hosting-service token* is rewritten for `/home/factory/.secrets` and `vm/git-credential-factory`, keeping the allow list and the four `token-file` faults, with no Compose, `image/secrets/` or `docker exec`. *The health check* keeps what `factory-health` reads and prints, with no Docker interval and no `restart:`. The preflight sections are unchanged, so their references still find them.
      - *The stage image* now says a pin is changed in `vm/Dockerfile` alone and checked with `uv run pytest tests/test_stage_image.py`. I added *Update the pins* as a subsection there, without `image/compose.yml`, `sudo` or `tests/test_image.py`.
      - The intro has one line pointing to the tag `v1.1`, and the list at the top follows the chapters.
      - Step 11 (`tools`) and *The rebuild after a merge* name `vm/git-credential-factory`.
      - *The agent runtime* and *Running on opencode*: the login token and the API key are the files in `/home/factory/.secrets/`.
      - Removed the paragraphs about the opencode config folder made by the image, and the probe sentence about an image built before it.
      - Smaller fixes to `docker system df`, "the entrypoint", "the image ships the agents" and the `FACTORY_IMAGE_ID_FILE` row. The `FACTORY_CHECKOUT` and `FACTORY_STATE` paragraph, the *Install* paragraph and the references to the removed headings are corrected.
    - `docs/project-guide/processes-and-checks.md`, *Starting a process*: the kill is now `os.killpg` on the child's process group, with no process table and no wait for the group. The section is renamed *Killing a process group*. A grandchild that takes a group or session of its own is not killed. The `factory.domain.sessions` paragraph is removed.
    - `docs/project-guide/README.md`: removed the `factory.domain.sessions` mention and the lines for `compose_support.py`, `entrypoint_support.py` and `leftovers_support.py`. Removed the fixtures `compose_service` and `image_layout` from the `conftest.py` line. Rewrote the `dockerfile_support.py` line for what it now holds.
    - `docs/project-guide/agents.md`: removed the sentence saying the image makes `.config/opencode`. This was beyond the criterion, but it was stale because of this story.
    - `docs/decisions.md`: added the closing line to the 13 entries the criterion lists, 12 with "Replaced by the machine of v1.2 (`vm/`), F0044-S0010." and the session entry with "The process group is killed; no agent code runs on the host since v1.2, F0044-S0010."
    - `README.md`: the run pointer now goes to `vm/setup.sh` and *The machine*; no `docker compose` or `image/` is left.

    Cross-read and found current: `docs/project-guide/stage-environment.md`, `stages.md`, `watching.md`, `costs.md`, `work-items.md` and the rest of `docs/project-guide/README.md`. The remaining operator-guide chapters are also current.

    Stale text I did not touch:
    - `docs/operator-playbook.md` is the human's and still names `docker compose -f image/compose.yml`, `image/secrets/`, Docker Desktop and the entrypoint umask, in the run steps, the secrets bullet, the "Where it went wrong" tables and the plan list.
    - The last bullet of the decision *"The machine of v1.2 …"* near the end of `docs/decisions.md` still says "Open: F0044 removes the Docker path". It is now partly done. Whoever closes the feature should decide on it, since the criterion did not list it.
    - Left to the human's changes 10 and 11, as the reviewer noted: `pyproject.toml:142` (mutmut `also_copy` lists `image/`), `.gitignore:15-16` and `demo/todo-service/README.md`.
    - The operator guide's wording about `FACTORY_IMAGE_ID_FILE` keeps the code default `/opt/factory/image-id`, which `src/factory/domain/settings.py` still has; the VM overrides it. If that default should go, it is a code change for the coder.

    `check`: check: green (not run again: passed on tree 3b7c47a1e17a at 2026-10-25T20:06:21Z)
    `secrets`: secrets: green (2.4 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Ran the one smoke-test command from the repository root, exactly as written.

    Command 1:
    ```bash
    ls image/Dockerfile image/compose.yml image/entrypoint.sh 2>/dev/null | wc -l; test -x vm/git-credential-factory && echo helper-moved; uv run python -c 'import factory.domain.sessions' 2>/dev/null && echo present || echo gone
    ```
    Output:
    ```
    0
    helper-moved
    gone
    ```
    Expect: three lines: `0`; `helper-moved`; `gone`. Met.

    Checked against the acceptance criteria once more. Nothing in the run contradicts any criterion. Beyond the command, I checked these things myself, read-only: `git ls-files image/` lists nothing, and the `image/` directory is gone from the working tree. `git diff origin/main -M` shows `image/git-credential-factory` → `vm/git-credential-factory` as a rename at 100 % similarity, which fits criterion 1 (moved unchanged). The helper's mode is executable. The smoke test does not exercise criteria 2, 3, 5, 6 and 8 (helper behaviour, setup.sh text, kill at the limit, test-text scan, docs). I did not judge them here; they belong to the tests, the review and the docs stage. I did not run `make check` (criterion 7); the factory runs it as the stage's check.

    Findings: none. I fixed nothing and left no changes in the working tree.
