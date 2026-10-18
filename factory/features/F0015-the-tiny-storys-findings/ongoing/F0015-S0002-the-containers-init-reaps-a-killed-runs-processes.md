---
stage: doing
pr: 207
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The container's init reaps a killed run's processes

## Assignment (as of log entry 1)

At the tiny story of 2026-10-18 (the night log's row of 06:09), the coder's 1-minute `time_limit` killed its run under `sudo`, as designed: `timeout --signal=KILL` inside the `sudo` call, then a stall and a retry that passed. Afterwards `ps` in the container showed `[claude] <defunct>`, owned by `agent`, with parent PID 1. PID 1 is the factory's own Python (`python -m factory.entry.run`, which the entrypoint `exec`s), because the image has no init process. A zombie is reaped only by its parent. As this session reads coreutils' `timeout`, its kill of its own process group kills `timeout` too, before it waits for `claude`, so `claude` and what it started are re-parented to PID 1. The factory waits only for its own child (`sudo`), so the zombies stay until the container restarts, one or more for every time limit. The same happens to the processes of a project command killed at its time limit (`run_process` kills the group and waits only for its child). The fix is the container runtime's own init: `init: true` on the service in `image/compose.yml`. Docker then runs `docker-init` (tini) as PID 1, and Podman, through its docker-compose provider, runs `catatonit`. Either one starts the entrypoint, forwards the stop signal to the factory and reaps every orphan (FEATURE decision 6). A test pins the setting, and a second pins the entrypoint's `exec`, which makes the factory the init's direct child. The real reaping cannot be shown in `make test`, which starts no container. It is a morning observation that the docs criterion writes into the operator guide, done at the shakedown (FEATURE decision 7). No earlier test changes (FEATURE decision 8).

## Interface

`image/compose.yml`: the service `factory` gains the key `init` with the YAML boolean `true`, right after `restart: unless-stopped` (a place for the reader: Compose gives the order of a service's keys no meaning, and no test pins it), with one comment line above it that says why. The comment says that the runtime's init is the first process and reaps what a killed run leaves, and that the factory reaps only its own children. Nothing else in the file changes.

`image/entrypoint.sh` and `image/Dockerfile`: unchanged. The entrypoint's last line stays `exec python -m factory.entry.run`.

Tests: new module `tests/test_compose_init.py`, which reads `image/compose.yml` with `YAML(typ="safe")` (`ruamel.yaml`) and `image/entrypoint.sh` as text, both from the repository root (`Path(__file__).parent.parent`), as `tests/test_compose_project.py` does:

- `test_the_container_runs_the_runtimes_init_as_its_first_process`: `services.factory.init` is `True`, the boolean, checked with `is True`, so a missing key and the string `"true"` both fail.
- `test_the_entrypoint_hands_over_to_the_factory_with_exec`: the last line of `image/entrypoint.sh` that is not blank is exactly `exec python -m factory.entry.run`.

No earlier test changes.

## Acceptance criteria

1. The service `factory` of `image/compose.yml` has `init` set to the YAML boolean `true`: `test_the_container_runs_the_runtimes_init_as_its_first_process`.
2. The entrypoint's last line that is not blank is `exec python -m factory.entry.run`, so the init's child is the factory itself and no shell stands between them: `test_the_entrypoint_hands_over_to_the_factory_with_exec`.
3. What must still hold: the restart policy, the health check, the required variables, the project name and the five mounts of the compose file are as before (the tests of `tests/test_compose.py`, `tests/test_compose_project.py`, `tests/test_claude_token_mount.py`, `tests/test_token_folder.py` and `tests/test_image_credentials.py` pass).
4. `make check` stays green.
5. docs: the operator guide's *The container: compose, entrypoint and health check* gets a paragraph. The service sets `init: true`, so the container's first process (PID 1) is the container runtime's own init: Docker's `docker-init` (tini, mounted at `/sbin/docker-init`) or Podman's `catatonit` (mounted at `/run/podman-init`). The init starts the entrypoint, forwards the stop signal to the factory and reaps every process whose parent has ended. Without it the factory's Python would be PID 1 and reap only its own children. Then every agent run killed at its `time_limit` under `sudo` leaves `claude` and what it started as zombies, `[claude] <defunct>` of `agent` with parent 1, until the container restarts (seen at the tiny story of 2026-10-18 under Docker Desktop). The same holds for the processes of a project command killed at its time limit. A container started without Compose needs `--init` (`docker run --init`, `podman run --init`). In *The entrypoint*, step 4 says that the factory runs as the init's child, not as PID 1. *A `time_limit` under `sudo`* and its row in the morning observations say what to check after the limit: `docker exec <container> ps -eo pid,ppid,user,stat,args` shows PID 1 as the runtime's init, and no line with `Z` in its `STAT` column and no `<defunct>`, besides no live `claude` process of `agent`. Under Podman this is first observed at the shakedown. If under Podman the container does not start because the runtime finds no init binary, or PID 1 is the factory's Python and not `catatonit`, the Compose provider or the Podman machine does not honour `init: true`: note it, and expect the zombies to pile up as before until the container restarts. The decision log gets an entry, "The container runtime's init reaps the processes a killed run leaves". It gives the cause (`timeout`'s kill of its own group ends `timeout` before it waits for `claude`, and the orphans go to PID 1) and the rejected alternatives with their reasons: the factory as the reaper, tini installed in the image, `timeout --foreground` (FEATURE decision 6). It also says why no test in `make test` shows the reaping (decision 7). No other document changes, the documents use no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "from pathlib import Path; from ruamel.yaml import YAML; print(YAML(typ='safe').load(Path('image/compose.yml').read_text(encoding='utf-8'))['services']['factory']['init'])"
```
Expect: `True`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_compose_init.py tests/test_compose.py tests/test_compose_project.py tests/test_claude_token_mount.py tests/test_token_folder.py tests/test_image_credentials.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-18 human: created.
2. intake: accepted
   - Interface: concrete. It names the file (`image/compose.yml`, key `init: true` after `restart: unless-stopped`, which I confirmed is at line 10), the unchanged entrypoint (its last line is already `exec python -m factory.entry.run`) and the new test module with both test names and what each asserts. Its one behaviour is the boolean `true`, and the criteria check it with `is True`.
   - Criteria: 1 and 2 are each one test function with no open decision. Criterion 3 is a list of existing tests that must still pass. The rules' failing sides are covered: criterion 1 fails on a missing key or the string "true", and criterion 2 fails on any other last line. Criteria 4 and 5 are the closing and docs criteria.
   - Demo: both commands are runnable. The first expects `True`, and the second expects a `<n> passed` line with no failed, error or skipped count. Both can be checked against the output.
   - Architecture: nothing under `src/` changes. This is a compose-file setting plus a test at the `tests/` root, next to `test_compose_project.py`. That fits the layout, since the module is outside the layers.
   - Scope: this is S0002 of F0015, finding 2, as the feature's Scope lists it. Out of scope are the factory acting as reaper, tini in the image, and v1's own compose file. Decisions 6 to 8 cover the choices, and no earlier test changes.
3. tester: wrote the tests from the Interface and the criteria.
   - criterion 1: tests/test_compose_init.py::test_the_container_runs_the_runtimes_init_as_its_first_process. It loads `image/compose.yml` with `YAML(typ="safe")` and checks `services.factory.get("init") is True`. A missing key or the string "true" fails it.
   - criterion 2: tests/test_compose_init.py::test_the_entrypoint_hands_over_to_the_factory_with_exec. The last line of `image/entrypoint.sh` that is not blank must equal `exec python -m factory.entry.run`. It already passes because the entrypoint stays unchanged; it guards against a later change.
   - criterion 3: no new test. The tests already in tests/test_compose.py, test_compose_project.py, test_claude_token_mount.py, test_token_folder.py and test_image_credentials.py cover it.
   - criteria 4 and 5: the closing and docs criteria, which need no test.
   Files created: tests/test_compose_init.py.
   Modules the runner could not import: none, because the module imports nothing under src/. Red for the right reason: the only failure in `make test` is test_the_container_runs_the_runtimes_init_as_its_first_process, since compose.yml has no `init` key yet. `make lint` is green. No criterion needed interpreting.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_compose_init.py::test_the_container_runs_the_runtimes_init_as_its_first_process
