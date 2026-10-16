---
stage: done
pr: 125
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The health check and the entrypoint's stops

## Assignment (as of log entry 1)

Make the machine's own stops visible to Docker. A stop of the repository or the machine already lands in the health status file through the stop service; this story adds the command that turns that file into the container's health check, the compose file that runs the container with a restart policy and that health check, the entrypoint script, whose own lines carry time stamps, and the wait for a repository that is not ready yet, which becomes the stop `repository_unavailable` instead of a silent loop. This covers ST3.3 (as a static test of the compose file plus tests of the health command, and a morning observation of a running container with `docker compose ps`) and implements R27 for the container side, with the time stamps of ST3.4 on the entrypoint's lines. The console script `factory-health` is already declared in `pyproject.toml`; the compose file calls the same module with `python -m`. A watchdog for a container that is dead is not built; Docker's restart policy and this health check are what R27 names. The entrypoint starts the factory in `/opt/factory`, so that `claude --version` runs in a fixed directory (questionnaire 1, Q23), makes sure the directory for the files of agent runs exists with the mode the image story decided, and sets no git configuration: the factory's git gets the identity and the credential helper through `GitOptions` only (questionnaire 1, Q17, Q18; F0001 decision 7).

## Interface

`src/factory/entry/health.py`

```python
def main(argv: Sequence[str] | None = None, *, store: HealthStatusStore | None = None) -> int: ...
```

`src/factory/application/scheduler.py` (extends the module of the scheduler story, F0010-S0002)

```python
class RepositoryWaiter:
    def __init__(
        self, preparer: CheckoutPreparer, boundaries: Boundaries, stops: StopService
    ) -> None: ...
    def prepare(self) -> bool: ...
```

`image/compose.yml`

```yaml
name: factory
services:
  factory:
    build:
      context: ..
      dockerfile: image/Dockerfile
      args:
        FACTORY_IMAGE: ${FACTORY_IMAGE:-unlabelled}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-m", "factory.entry.health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    environment:
      FACTORY_REPOSITORY_URL: ${FACTORY_REPOSITORY_URL:?set FACTORY_REPOSITORY_URL to the project's repository}
      FACTORY_INSTANCE: ${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}
    volumes:
      - work:/work
      - state:/state
      - claude-home:/home/agent/.claude
volumes:
  work:
  state:
  claude-home:
```

`image/entrypoint.sh` (POSIX `sh`, its first line the shebang for `/bin/sh`) runs these steps in this order:

```sh
set -eu
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
opt="${FACTORY_OPT:-/opt/factory}"
home="${FACTORY_CLAUDE_HOME:-$HOME/.claude}"
state="${FACTORY_STATE:-/state}"
```

then: check that `$opt/claude/agents` is a directory and `$opt/claude/settings.json` is a file, else `log "missing <path>"` to standard error and `exit 1`; `rm -rf "$home/agents"`, `mkdir -p "$home"`, copy `$opt/claude/agents` to `$home/agents` and `$opt/claude/settings.json` to `$home/settings.json`, then `log "installed agents and settings into $home"`; `mkdir -p "$state/runs"` and `chmod 2750 "$state/runs"`, then `log "prepared $state/runs"`; `log "starting instance ${FACTORY_INSTANCE:-unset}"`; `cd "$opt"`; `exec python -m factory.entry.run`.

Rules:

- `health.main` reads the option `--state-directory PATH` (default `STATE_DIRECTORY`) and, when `store` is `None`, reads `health_store(<state directory>)` of `factory.entry.wiring` (a `JsonHealthStatusFile` at `<state directory>/health.json`; only the wiring imports adapters, `tests/entry/test_wiring.py`). Healthy: prints `healthy` and returns 0. Otherwise it prints one line per stop, `<reason> (<scope>): <detail> (since <at in the form YYYY-MM-DDTHH:MM:SSZ>)`, and returns 1. `python -m factory.entry.health` ends with `raise SystemExit(main())`.
- `RepositoryWaiter.prepare` first calls `preparer.prepare()`. A `GitError` from it is a stop: `RepositoryStop(scope="repository", reason="repository_unavailable", detail="cannot prepare the checkout: <message>")`, and `prepare` returns `False`.
- Then, when `git.resolve("origin/main")` is `None` or `git.show_file("origin/main", PIPELINE_DEFINITION_FILE)` is `None`, it calls `git.fetch()` once and looks again. A `GitError` from the fetch is the stop with detail `cannot fetch: <message>`. Still no `origin/main`: detail `the repository has no main branch yet`. A main branch without the file: detail `origin/main has no factory/pipeline.yml yet`. Each returns `False`.
- When `origin/main` carries `factory/pipeline.yml`, it calls `stops.clear_stop("repository_unavailable")` and returns `True`.
- A stop is raised only when the health status does not already hold a `repository_unavailable` stop with the same detail (v1 printed each reason once).
- The stop's `at` is `boundaries.clock.now()`; the stop service writes the time-stamped line (F0003).
- `factory.entry.run.run_instance` passes `RepositoryWaiter(preparer, boundaries, StopService(boundaries)).prepare` to the `Scheduler` as its `prepare`, in place of the bare preparer (wiring; criterion 12 shows it).
- In the entrypoint every line written to standard output or standard error goes through `log`; no `echo` or `printf` outside `log`. `FACTORY_OPT`, `FACTORY_CLAUDE_HOME` and `FACTORY_STATE` are hooks for tests and the image's own layout; the factory process ignores `FACTORY_STATE` (the state directory is fixed).
- The entrypoint runs no `git config`.

Tests: `tests/entry/test_health.py`, `tests/application/test_repository_waiter.py`, `tests/test_compose.py` (parses `image/compose.yml` with `ruamel.yaml`), `tests/test_entrypoint.py` (runs `image/entrypoint.sh` with `sh`, a stub `python` on the `PATH` that writes its arguments and its working directory to files, `HOME`, `FACTORY_OPT`, `FACTORY_CLAUDE_HOME` and `FACTORY_STATE` in `tmp_path`). The waiter tests use `GitCli` on real bare remotes in `tmp_path`, the real `StopService` and a `FactoryLog` that collects lines.

## Acceptance criteria

1. `health.main` with no health file in the state directory prints `healthy` and returns 0.
2. `health.main` with one stop (scope `machine`, reason `preflight_failed`, detail `tool:make: make is not on the PATH`, and a known `at`) prints exactly one line `preflight_failed (machine): tool:make: make is not on the PATH (since <at as YYYY-MM-DDTHH:MM:SSZ>)` and returns 1.
3. `health.main([], store=<a JsonHealthStatusFile in tmp_path holding two stops>)` reads that store, prints two lines, one per stop in the order of the health status, and returns 1.
4. For each of the seven reasons of `RepositoryStopReason` (`fetch_failed`, `checkout_restore_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `repository_unavailable`, `main_branch_failing` with scope `repository`, and `preflight_failed` with scope `machine`; ST3.3), a stop raised through `StopService.raise_stop` makes `health.main` return 1, and after `StopService.clear_stop` of that reason it returns 0 again.
5. `python -m factory.entry.health --state-directory <dir>` run as a process exits with status 0 for a directory without stops and with status 1 for one whose `health.json` holds a stop.
6. `RepositoryWaiter.prepare` returns `True`, leaves no `repository_unavailable` stop and fetches nothing when the checkout is cloned and `origin/main` carries `factory/pipeline.yml`: a commit the human pushed to `main` after the clone is not in the checkout's `origin/main` afterwards.
7. A clone that fails (a repository URL that does not exist) and a fetch that fails (the remote deleted after the clone, with no `origin/main` yet) each make `prepare` return `False` and leave one `repository_unavailable` stop whose detail is the prefix and the message of the `GitError` raised: it starts `cannot prepare the checkout: git clone --quiet ` for the clone and `cannot fetch: git fetch --prune origin failed` for the fetch.
8. A remote that is a bare repository without any commit makes `prepare` return `False` with the stop detail `the repository has no main branch yet`, and the stop's `at` is the time of the test's clock.
9. After the human pushes `factory/pipeline.yml` to that remote, the next `prepare` fetches, returns `True`, and the `repository_unavailable` stop is gone.
10. A remote whose `main` has no `factory/pipeline.yml` makes `prepare` return `False` with the stop detail `origin/main has no factory/pipeline.yml yet`.
11. Two calls of `prepare` that meet the same fault write the stop and its time-stamped line once, not twice; a different fault in between writes a new line.
12. `run_instance` over a remote that is a bare repository without any commit, with `hosting` given and `should_stop` true once the first sleep was recorded, leaves the stop `repository_unavailable` with the detail `the repository has no main branch yet` in the health status and calls `sleep` once, with 30.0 seconds (the waiter is the scheduler's `prepare`).
13. `image/compose.yml` runs the service `factory` with `restart: unless-stopped` and a `healthcheck` whose test is `["CMD", "python", "-m", "factory.entry.health"]`, `interval: 30s`, `timeout: 10s`, `retries: 3` and `start_period: 60s` (ST3.3: a restart policy and a health check), and builds from the context `..` with the dockerfile `image/Dockerfile`.
14. In `image/compose.yml`, `FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE` are each written `${NAME:?<message>}` (compose refuses to start when one is unset, and neither has a default with `:-`), the build argument `FACTORY_IMAGE` is written `${FACTORY_IMAGE:-unlabelled}` (it is only a label), and the volumes `work`, `state` and `claude-home` are mounted at `/work`, `/state` and `/home/agent/.claude` and declared at the top level.
15. Every line that `image/entrypoint.sh` writes while it runs to the end starts with a time stamp in the form `YYYY-MM-DDTHH:MM:SSZ`, and the script has no `echo` or `printf` outside the `log` function (ST3.4); after their time stamps, the lines of a run to the end read `installed agents and settings into <FACTORY_CLAUDE_HOME>`, `prepared <FACTORY_STATE>/runs` and `starting instance <FACTORY_INSTANCE, or unset>`.
16. The entrypoint replaces `$FACTORY_CLAUDE_HOME/agents` with a copy of `$FACTORY_OPT/claude/agents` (an agent file that is no longer in the image is gone from the home) and copies `settings.json` next to it.
17. The entrypoint with no `claude/agents` directory, and with no `claude/settings.json` file, under `$FACTORY_OPT` (two cases) exits with status 1 after one time-stamped line on standard error that names the missing path, and never starts the stub `python`.
18. Without `FACTORY_CLAUDE_HOME` the entrypoint installs the agents into `$HOME/.claude/agents` and the settings into `$HOME/.claude/settings.json`.
19. The entrypoint creates `$FACTORY_STATE/runs` when it is missing and sets its mode to `2750` (`stat -c %a` reads `2750`), also when the directory exists with another mode.
20. The entrypoint changes into `$FACTORY_OPT` before it starts the instance: the stub `python` records a working directory equal to `$FACTORY_OPT` (questionnaire 1, Q23).
21. The entrypoint's last act is to `exec` `python -m factory.entry.run`: the stub receives exactly the arguments `-m factory.entry.run`.
22. The entrypoint sets no git configuration: the script contains no `git config`, and with a `git` stub on the `PATH` that records its calls, the entrypoint makes none.
23. make check stays green.
24. docs: `docs/operator-guide.md` explains the health check (`docker compose ps` shows the container unhealthy while any machine or repository stop stands, and `python -m factory.entry.health` names the stops), the restart policy, the compose variables (`FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE` required, `FACTORY_IMAGE` an optional label), and for each of the four stops `preflight_failed`, `checkout_restore_failed`, `pipeline_definition_invalid` and `repository_unavailable` what it means and what the operator does; it states that a container whose process is dead is left to Docker's restart policy and that a real container is the morning observation; `docs/decisions.md` records why the entrypoint sets no git configuration and starts in `/opt/factory`.

## Demo

```bash
uv run python -c "
import tempfile, pathlib
from datetime import UTC, datetime
from factory.adapters.health_file import JsonHealthStatusFile
from factory.domain.stops import HealthStatus, RepositoryStop
from factory.entry.health import main
d = pathlib.Path(tempfile.mkdtemp())
print(main(['--state-directory', str(d)]))
stop = RepositoryStop(scope='machine', reason='preflight_failed', detail='tool:make: make is not on the PATH', at=datetime(2026, 10, 12, tzinfo=UTC))
JsonHealthStatusFile(d / 'health.json').write(HealthStatus(stops=[stop]))
print(main(['--state-directory', str(d)]))
"
```
Expect: four lines: `healthy`, `0`, a line that starts with `preflight_failed (machine): tool:make: make is not on the PATH (since 2026-10-12T` and ends with `Z)`, and `1`.

```bash
uv run python -c "
from ruamel.yaml import YAML
service = YAML(typ='safe').load(open('image/compose.yml'))['services']['factory']
print(service['restart'], service['healthcheck']['interval'], service['healthcheck']['test'][-1])
"
```
Expect: one line, `unless-stopped 30s factory.entry.health`.

```bash
d=$(mktemp -d) && mkdir -p "$d/opt/claude/agents" "$d/bin" && : > "$d/opt/claude/agents/x.md" && echo '{}' > "$d/opt/claude/settings.json" && printf '#!/bin/sh\necho stub "$@"\n' > "$d/bin/python" && chmod +x "$d/bin/python" && HOME="$d" FACTORY_OPT="$d/opt" FACTORY_CLAUDE_HOME="$d/home" FACTORY_STATE="$d/state" PATH="$d/bin:$PATH" sh image/entrypoint.sh; stat -c %a "$d/state/runs"
```
Expect: the output has the lines `installed agents and settings into`, `prepared`, `starting instance unset`, each starting with a time stamp in the form `YYYY-MM-DDTHH:MM:SSZ`, then `stub -m factory.entry.run`, and the last line is `2750`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.entry.health.main`, `RepositoryWaiter` in `factory.application.scheduler`, `image/compose.yml`, `image/entrypoint.sh` with its steps in order). Every comment-stated behaviour has a criterion: the health line format (2, 3), the stop details (7, 8, 10), once-only stops (11), and the entrypoint's order, log lines and exec arguments (15, 16, 20, 21).
   - Criteria: each can be tested by one test function. Each rule has its failing side. Health: stops give exit 1 (2, 3, 4), no stops give 0 (1, 4). Waiter: clone failure, fetch failure, no main, and no pipeline file each give False plus a stop (7, 8, 10), and the passing side is 6 and 9. Entrypoint: a missing agents directory or settings file (17, two cases), a missing or wrongly-moded `runs` directory (19), and no git configuration (22). Compose: required variables with no `:-` default (14).
   - Demo: all three blocks are runnable commands, and each `Expect:` line is checkable against the output.
   - Architecture: `health.py` is in `entry` and reads its store through `entry.wiring`. `RepositoryWaiter` is in `application` and uses only interfaces (preparer, git, stops). Adapters are touched only in wiring. This fits CLAUDE.md's layers.
   - Scope: inside F0010's "health check and entrypoint's stops" item. The story builds no watchdog, which FEATURE.md puts out of scope.
3. tester: Wrote the red tests for criteria 1–22 from the Interface and criteria. `make lint` is green. One `make test` run stopped at collection on purpose: `ModuleNotFoundError` for `factory.entry.health`, and `ImportError` for `RepositoryWaiter` from `factory.application.scheduler`. `tests/entry/test_run_waiter.py`, `tests/test_compose.py` and `tests/test_entrypoint.py` were not reached in that run. When they run they fail on the missing `image/compose.yml` and `image/entrypoint.sh`, and on `run_instance` still using the bare preparer.

   Mapping:
   - criterion 1: tests/entry/test_health.py::test_a_state_directory_without_a_health_file_is_healthy
   - criterion 2: tests/entry/test_health.py::test_one_stop_prints_its_line_and_returns_one
   - criterion 3: tests/entry/test_health.py::test_a_given_store_is_read_and_each_stop_prints_one_line_in_order
   - criterion 4: tests/entry/test_health.py::test_every_stop_reason_makes_the_check_fail_until_it_is_cleared (seven rows; real StopService on the conftest `boundaries`, `--state-directory tmp_path/state`)
   - criterion 5: tests/entry/test_health.py::test_the_module_run_as_a_process_exits_with_the_health_status (rows: no stop → 0, one stop → 1; started through `run_process`)
   - criterion 6: tests/application/test_repository_waiter.py::test_a_ready_checkout_is_not_fetched_and_leaves_no_stop
   - criterion 7: tests/application/test_repository_waiter.py::test_a_failing_clone_or_fetch_is_one_stop_naming_the_git_error (rows: missing URL, remote deleted after cloning an empty bare)
   - criterion 8: tests/application/test_repository_waiter.py::test_a_remote_without_any_commit_is_a_stop_at_the_clocks_time
   - criterion 9: tests/application/test_repository_waiter.py::test_the_pushed_pipeline_definition_is_fetched_and_clears_the_stop
   - criterion 10: tests/application/test_repository_waiter.py::test_a_main_branch_without_the_pipeline_definition_is_a_stop
   - criterion 11: tests/application/test_repository_waiter.py::test_a_repeated_fault_is_reported_once_and_a_changed_fault_again (sequence: no main, no main, no pipeline file, main deleted again; expects 3 `stop repository repository_unavailable: …` lines)
   - criterion 12: tests/entry/test_run_waiter.py::test_run_instance_over_a_remote_without_commits_stops_and_pauses_thirty_seconds
   - criterion 13: tests/test_compose.py::test_the_service_restarts_unless_stopped_and_runs_the_health_check
   - criterion 14: tests/test_compose.py::test_each_required_variable_refuses_to_start_unset_and_has_no_default, ::test_the_image_label_defaults_to_unlabelled, ::test_the_three_volumes_are_mounted_and_declared
   - criterion 15: tests/test_entrypoint.py::test_every_line_of_a_full_run_is_time_stamped (rows: FACTORY_INSTANCE unset and set), ::test_the_script_writes_output_only_through_its_log_function
   - criterion 16: tests/test_entrypoint.py::test_the_agents_are_replaced_by_the_images_and_the_settings_copied
   - criterion 17: tests/test_entrypoint.py::test_a_missing_image_file_ends_the_run_with_one_line_before_the_instance (rows: claude/agents, claude/settings.json)
   - criterion 18: tests/test_entrypoint.py::test_without_a_claude_home_the_agents_go_into_the_users_home
   - criterion 19: tests/test_entrypoint.py::test_the_runs_directory_gets_the_mode_2750 (rows: missing, existing with 755)
   - criterion 20: tests/test_entrypoint.py::test_the_instance_starts_in_the_opt_directory
   - criterion 21: tests/test_entrypoint.py::test_the_entrypoint_hands_over_to_the_run_module
   - criterion 22: tests/test_entrypoint.py::test_the_entrypoint_sets_no_git_configuration

   Files created: tests/entry/test_health.py, tests/entry/test_run_waiter.py, tests/application/test_repository_waiter.py, tests/test_compose.py, tests/test_entrypoint.py.

   Choices for the coder:
   - Criterion 12 lives in a new file, `tests/entry/test_run_waiter.py`. I did not add it to `tests/entry/test_run.py`, a test I did not write.
   - The waiter tests use a local `RecordingLog`. They build their boundaries with `dataclasses.replace` on the conftest `boundaries`: their own `GitCli`, the log, and the checkout at `tmp_path/instance`.
   - The entrypoint tests run `sh image/entrypoint.sh` with PATH set to `<stubs>:/usr/local/bin:/usr/bin:/bin`. The stubs are `python` and `git` written in `sh`. They record their calls to files.
   - Criterion 15 counts the lines of both stdout and stderr; every line must have a time stamp.
   - Criterion 17 also expects stdout to be empty, because the check is the script's first step.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Built the health check, the repository waiter, the compose file and the entrypoint. The tester's tests did not change, and `make check` is green (total coverage 99.51 %). Commits: 8430aa3 (feat) and e87bb75 (refactor).

   What I built:
   - `src/factory/entry/health.py`: `main(argv, *, store)`. It parses `--state-directory` with argparse (default `STATE_DIRECTORY`). With no `store` given, it reads `health_store(<dir>)` from the wiring. Healthy prints `healthy` and returns 0. Otherwise it prints one line per stop, `<reason> (<scope>): <detail> (since %Y-%m-%dT%H:%M:%SZ)`, and returns 1. It ends with `raise SystemExit(main())`.
   - `src/factory/application/scheduler.py`: `RepositoryWaiter(preparer, boundaries, stops).prepare()`.
     - It runs the preparer and turns a `GitError` into the detail `cannot prepare the checkout: <error>`.
     - Then it checks that `origin/main` exists and holds `factory/pipeline.yml`. Only if that check fails does it fetch once (a fetch `GitError` gives the detail `cannot fetch: <error>`) and check again.
     - A remaining fault raises `repository_unavailable` with `at = boundaries.clock.now()`. The stop is skipped when the health status already holds a stop with that reason and the same detail. Success clears the stop.
     - The `origin/main` name and the file path are built from `REMOTE`, `MAIN_BRANCH` and `PIPELINE_DEFINITION_FILE` in `factory.domain.paths`.
   - `src/factory/entry/run.py`: `run_instance` gives the `Scheduler` the waiter's `prepare` in place of the bare preparer.
   - `image/compose.yml`: written exactly as in the Interface.
   - `image/entrypoint.sh`: POSIX sh. It runs the Interface's steps in order: the `log` function, the checks for the agents directory and the settings file (a missing one is logged to stderr and exits 1), the agents and settings replaced and copied, `runs` set to 2750, `cd "$opt"`, `exec python -m factory.entry.run`. It runs no `git config`.

   Main decision: the waiter fetches only when the checkout is not ready. It does not fetch on every iteration, because criterion 6 requires a ready checkout to fetch nothing. The tick does its own fetch. Rejected: a fetch on every `prepare`. It would duplicate the tick's fetch and fail criterion 6.

   Refactor (e87bb75): moved the fetch-and-check-again step into `_fault_after_fetch`, so `prepare` reads as a straight sequence. I tried replacing the `if` with an `a and b` chain and dropped it as too clever. I also removed a `(docs/decisions.md)` reference from the entrypoint's comment, because that decision entry does not exist yet.

   Open:
   - The documenter still has criterion 24: the operator guide and the decision log entry on why the entrypoint sets no git configuration and starts in `/opt/factory`.
   - Not touched: the Dockerfile's `WORKDIR` is `/work` and its `ENV` sets `FACTORY_CLAUDE_HOME`, but not `FACTORY_OPT` or `FACTORY_STATE`. The script's defaults cover those two.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: criteria 1–22 each have a test that checks what the criterion says, and the coder's entry reports `make check` green. Every rule has its failing side tested. Health: no stops gives 0, stops give 1, for all seven reasons, also when the module runs as a process. Waiter: a failed clone, a failed fetch, no main branch and no `factory/pipeline.yml` each give `False` plus a stop; a ready checkout gives `True` with no fetch; a pushed pipeline file clears the stop. The same fault is reported once and a different fault again (criterion 11). Entrypoint: both missing image paths, a `runs` directory that is missing or has mode 755, and both the static check and the stub check for git configuration.
      - Architecture: `RepositoryWaiter` in `src/factory/application/scheduler.py` imports only application and domain modules. `src/factory/entry/health.py` reaches the adapter only through `entry.wiring.health_store`. The waiter is wired into `run_instance` in `src/factory/entry/run.py`.
      - Security: no secrets and no silencing markers. The entrypoint quotes every path it builds from environment variables, and `health.main` validates its arguments with argparse.
      - Quality: the waiter fetches only when the checkout is not ready, and the stop is written only when no stop with that reason and detail is already in force. Nothing in `StopService` or the tick already did this, so it is not a second copy. `parse_args(sys.argv[1:] if argv is None else argv)` matches `src/factory/entry/watch.py`. The time format string already appears twice, both as private constants (`domain/board.py`, `adapters/factory_log.py`), with no public helper to reuse, so the third private copy in `health.py` is not counted as a finding. Docstrings and comments meet *Docs*.
      - Ticket hygiene: the coder's entry states the main decision (fetch only when not ready) and the rejected option (fetch on every `prepare`). The Assignment matches what was built. Criterion 24 still describes what the documenter has to write.
      - Open, outside this story: the Dockerfile's `WORKDIR`/`ENV`, which the coder noted.
6. documenter: wrote criterion 24 and fixed stale text. `make check` is green (coverage 99.51 %). No findings: the code matches the Interface and the criteria.

   Files changed:
   - docs/operator-guide.md: new section "The container: compose, entrypoint and health check".
     - It covers the compose variables (`FACTORY_REPOSITORY_URL` and `FACTORY_INSTANCE` required, `FACTORY_IMAGE` an optional label) and the volumes.
     - It lists the entrypoint steps and their time-stamped lines.
     - It explains the health check (`docker compose ps` shows unhealthy while a stop stands; `python -m factory.entry.health` names the stops, with the line format), and the restart policy.
     - It states that a dead container is left to Docker's restart policy and that a real container is the morning observation.
     - It has a table for `preflight_failed`, `checkout_restore_failed`, `pipeline_definition_invalid` and `repository_unavailable` (meaning and action), and a section on the wait for a repository that is not ready (fetch once, stop written once per detail, cleared on success).
   - docs/operator-guide.md, stale text corrected:
     - the intro no longer says `factory-health` is unbuilt or that the repository waiter is still to come;
     - the health-file section says the check reads the file now;
     - the Build section no longer lists `image/entrypoint.sh` among the files that later stories create.
   - docs/decisions.md: new entry on why the entrypoint sets no git configuration and starts in `/opt/factory`. It also records why the waiter fetches only when `origin/main` is not ready.

   Cross-read and found current: README.md. docs/project-guide.md was not read.

   Stale but not touched (outside this story): the Dockerfile has `WORKDIR /work` and its `ENV` lacks `FACTORY_OPT` and `FACTORY_STATE`. The entrypoint's defaults cover both, and the coder already noted it.

   I did not run the examples. The three demo blocks and the `docker compose` commands are untried, and the health line in the guide is illustrative.

   `make check`: check: green
7. demo: ran the three `## Demo` commands from the repository root in order. All three met their `Expect:` lines, and nothing in the output contradicts an acceptance criterion. No findings.

   1. Health check over a temporary state directory, first with no health file, then with one `preflight_failed` stop:
   ```
   healthy
   0
   preflight_failed (machine): tool:make: make is not on the PATH (since 2026-10-12T00:00:00Z)
   1
   ```
   Met: four lines, `healthy`, `0`, the stop line with the `(since 2026-10-12T…Z)` format, and `1`. Criteria 1 and 2.

   2. Parsing `image/compose.yml` with ruamel.yaml:
   ```
   unless-stopped 30s factory.entry.health
   ```
   Met: exactly the expected line. Criterion 13.

   3. Entrypoint run with a stub `python`, followed by `stat -c %a` on the runs directory:
   ```
   2026-10-16T08:21:21Z installed agents and settings into /tmp/tmp.9m8q4NF7hu/home
   2026-10-16T08:21:21Z prepared /tmp/tmp.9m8q4NF7hu/state/runs
   2026-10-16T08:21:21Z starting instance unset
   stub -m factory.entry.run
   2750
   ```
   Met: the three log lines each start with a `YYYY-MM-DDTHH:MM:SSZ` time stamp and read as criterion 15 says. Then comes `stub -m factory.entry.run` (criterion 21) and the last line is `2750` (criterion 19).

   Not shown by the demo (the tests cover these): the waiter criteria 6–12, the entrypoint's error paths (17) and the working directory (20). As the documenter noted, a real container under `docker compose ps` is still the morning observation.
8. done (pull request merged); cost: 6 runs, 20.1 min, 64 turns, 225k tokens in (2093k more from cache), 39k out, $2.68
