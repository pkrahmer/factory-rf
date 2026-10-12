# The health check and the entrypoint's stops

## Assignment (as of log entry 1)

Make the machine's own stops visible to Docker. A stop of the repository or the machine already lands in the health status file through the stop service; this story adds the command that turns that file into the container's health check, the compose file that runs the container with a restart policy and that health check, the entrypoint script, whose own lines carry time stamps, and the wait for a repository that is not ready yet, which becomes the stop `repository_unavailable` instead of a silent loop. This covers ST3.3 (as a static test of the compose file plus tests of the health command, and a morning observation of a running container with `docker compose ps`) and implements R27 for the container side, with the time stamps of ST3.4 on the entrypoint's lines. The console script entry `factory-health` belongs in `pyproject.toml`, outside the coder's write paths; the compose file calls the module with `python -m`, and the human adds the entry. A watchdog for a container that is dead is not built; Docker's restart policy and this health check are what R27 names.

## Interface

`src/factory/entry/health.py`

```python
def main(argv: Sequence[str] | None = None, *, store: HealthStatusStore | None = None) -> int: ...
```

`src/factory/application/scheduler.py` (extends the module of the first story of this feature)

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
        FACTORY_IMAGE: ${FACTORY_IMAGE:?set FACTORY_IMAGE to this build's identity}
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
```

then: check that `$opt/claude/agents` is a directory and `$opt/claude/settings.json` is a file, else `log "missing <path>"` to standard error and `exit 1`; `rm -rf "$home/agents"`, `mkdir -p "$home"`, copy `$opt/claude/agents` to `$home/agents` and `$opt/claude/settings.json` to `$home/settings.json`, then `log "installed agents and settings into $home"`; `git config --global user.name "${GIT_USER_NAME:-factory}"`, `git config --global user.email "${GIT_USER_EMAIL:-factory@noreply.invalid}"`, `git config --global pull.ff only`; `log "starting instance ${FACTORY_INSTANCE:-unset}"`; `exec python -m factory.entry.run`.

Rules:

- `health.main` reads the option `--state-directory PATH` (default `STATE_DIRECTORY`) and, when `store` is `None`, reads `JsonHealthStatusFile(<state directory>/health.json)`. Healthy: prints `healthy` and returns 0. Otherwise it prints one line per stop, `<reason> (<scope>): <detail> (since <at in the form YYYY-MM-DDTHH:MM:SSZ>)`, and returns 1. `python -m factory.entry.health` ends with `raise SystemExit(main())`.
- `RepositoryWaiter.prepare` first calls `preparer.prepare()`. A `GitError` from it is a stop: `RepositoryStop(scope="repository", reason="repository_unavailable", detail="cannot prepare the checkout: <message>")`, and `prepare` returns `False`.
- Then, when `git.resolve("origin/main")` is `None` or `git.show_file("origin/main", PIPELINE_DEFINITION_FILE)` is `None`, it calls `git.fetch()` once and looks again. A `GitError` from the fetch is the stop with detail `cannot fetch: <message>`. Still no `origin/main`: detail `the repository has no main branch yet`. A main branch without the file: detail `origin/main has no factory/pipeline.yml yet`. Each returns `False`.
- When `origin/main` carries `factory/pipeline.yml`, it calls `stops.clear_stop("repository_unavailable")` and returns `True`.
- A stop is raised only when the health status does not already hold a `repository_unavailable` stop with the same detail (v1 printed each reason once).
- The stop's `at` is `boundaries.clock.now()`; the stop service writes the time-stamped line (F0003).
- `factory.entry.run.run_instance` passes `RepositoryWaiter(preparer, boundaries, StopService(boundaries)).prepare` to the `Scheduler` as its `prepare`, in place of the bare preparer (wiring only; the waiter's tests above are its proof).
- In the entrypoint every line written to standard output or standard error goes through `log`; no `echo` or `printf` outside `log`.

Tests: `tests/entry/test_health.py`, `tests/application/test_repository_waiter.py`, `tests/test_compose.py` (parses `image/compose.yml` with `ruamel.yaml`), `tests/test_entrypoint.py` (runs `image/entrypoint.sh` with `sh`, a stub `python` on the `PATH` that writes its arguments to a file, `HOME`, `FACTORY_OPT` and `FACTORY_CLAUDE_HOME` in `tmp_path`). The waiter tests use `GitCli` on real bare remotes in `tmp_path`, the real `StopService` and a `FactoryLog` that collects lines.

## Acceptance criteria

1. `health.main` with no health file in the state directory prints `healthy` and returns 0.
2. `health.main` with one stop (scope `machine`, reason `preflight_failed`, detail `tool:make: make is not on the PATH`, and a known `at`) prints exactly one line `preflight_failed (machine): tool:make: make is not on the PATH (since <at as YYYY-MM-DDTHH:MM:SSZ>)` and returns 1.
3. For each of the four reasons `preflight_failed`, `checkout_restore_failed`, `pipeline_definition_invalid` and `repository_unavailable` (ST3.3), a stop raised through `StopService.raise_stop` makes `health.main` return 1, and after `StopService.clear_stop` of that reason it returns 0 again.
4. `python -m factory.entry.health --state-directory <dir>` run as a process exits with status 0 for a directory without stops and with status 1 for one whose `health.json` holds a stop.
5. `RepositoryWaiter.prepare` returns `True` and leaves no `repository_unavailable` stop when the checkout is cloned and `origin/main` carries `factory/pipeline.yml`.
6. A clone that fails (a repository URL that does not exist) and a fetch that fails (the remote deleted after the clone, with no `origin/main` yet) each make `prepare` return `False` and leave one `repository_unavailable` stop whose detail starts with `cannot prepare the checkout` or `cannot fetch`.
7. A remote that is a bare repository without any commit makes `prepare` return `False` with the stop detail `the repository has no main branch yet`.
8. After the human pushes `factory/pipeline.yml` to that remote, the next `prepare` fetches, returns `True`, and the `repository_unavailable` stop is gone.
9. A remote whose `main` has no `factory/pipeline.yml` makes `prepare` return `False` with the stop detail `origin/main has no factory/pipeline.yml yet`.
10. Two calls of `prepare` that meet the same fault write the stop and its time-stamped line once, not twice; a different fault in between writes a new line.
11. `image/compose.yml` runs the service `factory` with `restart: unless-stopped` and a `healthcheck` whose test is `["CMD", "python", "-m", "factory.entry.health"]`, `interval: 30s`, `timeout: 10s`, `retries: 3` and `start_period: 60s` (ST3.3: a restart policy and a health check).
12. In `image/compose.yml`, `FACTORY_REPOSITORY_URL`, `FACTORY_INSTANCE` and the build argument `FACTORY_IMAGE` are each written `${NAME:?<message>}` (compose refuses to start when one is unset, and none has a default with `:-`), and the volumes `work`, `state` and `claude-home` are mounted at `/work`, `/state` and `/home/agent/.claude` and declared at the top level.
13. Every line that `image/entrypoint.sh` writes while it runs to the end starts with a time stamp in the form `YYYY-MM-DDTHH:MM:SSZ`, and the script has no `echo` or `printf` outside the `log` function (ST3.4).
14. The entrypoint replaces `$FACTORY_CLAUDE_HOME/agents` with a copy of `$FACTORY_OPT/claude/agents` (an agent file that is no longer in the image is gone from the home) and copies `settings.json` next to it.
15. The entrypoint with no `claude/agents` directory under `$FACTORY_OPT` exits with status 1 after one time-stamped line on standard error that names the missing path, and never starts the stub `python`.
16. The entrypoint sets the global git configuration from `GIT_USER_NAME` and `GIT_USER_EMAIL`, defaulting to `factory` and `factory@noreply.invalid`, and sets `pull.ff` to `only`.
17. The entrypoint's last act is to `exec` `python -m factory.entry.run`: the stub receives exactly the arguments `-m factory.entry.run`.
18. `make check` stays green.
19. docs: `docs/operator-guide.md` explains the health check (`docker compose ps` shows the container unhealthy while any machine or repository stop stands, and `python -m factory.entry.health` names the stops), the restart policy, the three compose variables, and for each of the four stops `preflight_failed`, `checkout_restore_failed`, `pipeline_definition_invalid` and `repository_unavailable` what it means and what the operator does; it states that a container whose process is dead is left to Docker's restart policy and that a real container is the morning observation.

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
d=$(mktemp -d) && mkdir -p "$d/opt/claude/agents" "$d/bin" && : > "$d/opt/claude/agents/x.md" && echo '{}' > "$d/opt/claude/settings.json" && printf '#!/bin/sh\necho stub "$@"\n' > "$d/bin/python" && chmod +x "$d/bin/python" && HOME="$d" FACTORY_OPT="$d/opt" PATH="$d/bin:$PATH" sh image/entrypoint.sh
```
Expect: the last line is `stub -m factory.entry.run`, and every line before it starts with a time stamp in the form `YYYY-MM-DDTHH:MM:SSZ` (the lines `installed agents and settings into` and `starting instance unset`).

## Log (append only)

1. 2026-10-12 human: created.
