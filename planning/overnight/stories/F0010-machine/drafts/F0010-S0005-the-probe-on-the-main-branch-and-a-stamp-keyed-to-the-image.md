# The probe on the main branch and a stamp keyed to the image

## Assignment (as of log entry 1)

Put the preflight into the tick, in the right place and with the right memory. The preflight runs after the tick has fetched and reset its checkout to the remote, and before the pipeline definition is loaded. It runs the machine's items of the previous story only when the image build changed since the last pass, and it probes the code by running the project's `lint` command on the main branch, never on a work item's branch, only when the main branch has moved since the last pass. A machine that fails is a machine stop, a main branch that fails the lint is a repository stop, and in both cases the tick does nothing else. No timer expires the stamp. This covers ST4.1, ST4.2, ST4.3 and ST4.5, and keeps kept thing 16 (an idle tick does not run the project's commands) and kept thing 18. The probe uses a constant `time_limit` of 10 minutes, the default of every project command, because the pipeline definition is loaded after the preflight; the stop for a main branch that fails is reported through the stop service of F0003, whose health status the container's health check reads.

## Interface

`src/factory/domain/preflight.py` (extends the module)

```python
class PreflightStamp(BaseModel):
    image: str | None                         # the image identity the machine items passed on
    main_probed: CommitId | None = None       # the commit of origin/main whose lint passed
```

`src/factory/application/preflight.py` (extends the module)

```python
PROBE_COMMAND = "lint"
PROBE_TIME_LIMIT = timedelta(minutes=10)

class PreflightStampStore(ABC):
    @abstractmethod
    def read(self) -> PreflightStamp | None: ...          # missing or unreadable: None (a cache)
    @abstractmethod
    def write(self, stamp: PreflightStamp) -> None: ...

class Preflight:
    def __init__(
        self,
        boundaries: Boundaries,
        checks: MachineChecks,
        stamps: PreflightStampStore,
        stops: StopService,
        image: str | None,
    ) -> None: ...
    def run(self) -> bool: ...
```

`src/factory/adapters/preflight_stamp_file.py`

```python
class JsonPreflightStampFile:                 # implements PreflightStampStore
    def __init__(self, path: Path) -> None: ...
```

`src/factory/application/tick.py`: the tick (built by F0006-S0004) takes one more keyword argument, `preflight: Preflight | None = None`. When it is given, the tick calls `preflight.run()` after its fetch and its reset of the checkout to the remote, and before it loads the pipeline definition. When `run()` returns `False` the tick ends there.

Rules for `Preflight.run`:

- Machine items. When `image` is not `None` and the stored stamp's `image` equals it, the machine items are skipped. Otherwise `checks.run()` runs. A failed report is raised as `machine_stop(report, at=boundaries.clock.now())` through `stops.raise_stop`, the stamp is not written, and `run` returns `False` without probing. A passed report clears the stop `preflight_failed` and writes `PreflightStamp(image=image, main_probed=<the stored main_probed if the stored image equals image, else None>)`.
- Probe. `main = git.resolve("origin/main")`; when it is `None` there is nothing to probe and `run` returns `True`. When the stored `main_probed` equals `main` the probe is skipped and the stop `main_branch_failing` is cleared. Otherwise the probe runs `git.checkout("main", start_point="origin/main")`, `git.reset_to("origin/main")` and `project_commands.run("lint", time_limit=PROBE_TIME_LIMIT)`.
- A probe whose result is `passed` clears `main_branch_failing`, writes the stamp with `main_probed=main` and returns `True`.
- A probe whose result is not `passed` (red, or the `time_limit` reached) raises `RepositoryStop(scope="repository", reason="main_branch_failing", detail="lint is red on main at <first 12 characters of main>: <the result's last_line>")` (for the `time_limit` case the detail says `lint reached its time_limit on main at <first 12 characters of main>`) and returns `False`; the stamp's `main_probed` is not changed.
- A `ProjectCommandError` or a `GitError` while probing raises `RepositoryStop(scope="machine", reason="preflight_failed", detail="the probe on main could not run: <message>")` and returns `False`.
- No timer is involved: `Preflight` compares no times (the clock is read only for the `at` of a stop) and the stamp holds no time.

Wiring puts the file at `<state directory>/preflight-stamp.json`. `JsonPreflightStampFile.read` returns `None` for a missing file and for a file that is not a valid stamp; `write` replaces the file with one JSON object holding the two fields.

Tests: `tests/application/test_preflight_run.py`, `tests/application/test_tick_preflight.py` (the tick on the `remote`, `checkout`, `human`, `hosting` and `agent_runtime` fixtures with a real `MakeProjectCommands`; the remote's `main` gets a `Makefile` whose target `lint` is `test ! -f BROKEN`, and a file named `BROKEN` makes it red), `tests/adapters/test_preflight_stamp_file.py`. The machine items are counted through a `which` stub that records its calls.

## Acceptance criteria

1. With the checkout on a work item's branch whose `lint` fails (a file `BROKEN` on that branch only) and an `origin/main` whose `lint` passes, `Preflight.run()` returns `True`, and afterwards the checkout is on `main` at `origin/main` (ST4.1: a lint failure on the work item's branch does not fail the preflight).
2. With an `origin/main` whose `lint` fails, `run()` returns `False` and the health status holds exactly one stop: scope `repository`, reason `main_branch_failing`, a detail that starts `lint is red on main at <first 12 characters of origin/main>` (ST4.1 and ST4.5: a main branch that fails the lint is a reported stop).
3. After the human fixes `main` and pushes, the next `run()` returns `True` and the stop `main_branch_failing` is gone from the health status.
4. When a machine item fails (`which` answers `None` for `make`), `run()` returns `False`, the health status holds one stop with scope `machine` and reason `preflight_failed` whose detail contains `tool:make`, and `lint` was not run.
5. A `ProjectCommandError` raised by the probe leaves one stop with scope `machine`, reason `preflight_failed` and a detail that starts `the probe on main could not run`, and `run()` returns `False`.
6. The tick fetches before the preflight: with an `origin/main` that failed the lint when the checkout was cloned, and a fix the human pushed afterwards, one tick given the preflight passes it (ST4.2).
7. The same order in the other direction: with a clean `origin/main` at clone time and a breaking commit the human pushed afterwards, one tick given the preflight fails it with the stop `main_branch_failing`.
8. A tick whose preflight returns `False` does nothing else: no agent run is requested, no pull request exists in the fake hosting service, and no event is dispatched, although a started story is waiting on the remote.
9. While the image is unchanged the machine items run once: two `run()` calls with the same non-`None` image call `which` for each tool once, not twice (ST4.3).
10. No timer expires the stamp: after the test's clock is advanced by 90 days between two `run()` calls with the same image, the machine items still ran once.
11. A different image identity runs the machine items again and the stamp then holds the new identity.
12. A different image identity also probes the main branch again, although `origin/main` did not move.
13. With `image=None` the machine items run on every `run()`.
14. A failed machine report writes no stamp, so the next `run()` runs the machine items again; when they pass, the stop `preflight_failed` is gone.
15. The probe does not repeat for an `origin/main` that already passed: two `run()` calls run `lint` once, and after the human pushes a new commit to `main` the third call runs it again.
16. `JsonPreflightStampFile` reads back a stamp it wrote: `PreflightStamp(image="build-7", main_probed=<40 hexadecimal digits>)`.
17. `JsonPreflightStampFile.read` returns `None` for a missing file and for a file that holds text which is not a stamp.
18. `make check` stays green.
19. docs: `docs/operator-guide.md` explains the preflight as the tick runs it (after the fetch, before the pipeline definition is loaded), that the machine items are skipped while the image build is unchanged and the probe repeats only when `main` moves, the file `preflight-stamp.json` in the state directory and that deleting it only costs one more run, and for the stops `main_branch_failing` and `preflight_failed` what the operator does; `docs/decisions.md` records why the stamp is keyed to the image build and not to a timer, and why the probe runs `lint` on the main branch only.

## Demo

```bash
uv run python -c "
import tempfile, pathlib
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.domain.preflight import PreflightStamp
d = pathlib.Path(tempfile.mkdtemp())
store = JsonPreflightStampFile(d / 'preflight-stamp.json')
print(store.read())
store.write(PreflightStamp(image='build-7', main_probed='a' * 40))
stamp = store.read()
print(stamp.image, stamp.main_probed[:7])
(d / 'preflight-stamp.json').write_text('not a stamp')
print(store.read())
"
```
Expect: three lines, `None`, `build-7 aaaaaaa` and `None`.

```bash
uv run python -c "
from factory.application.preflight import PROBE_COMMAND, PROBE_TIME_LIMIT
print(PROBE_COMMAND, PROBE_TIME_LIMIT.total_seconds())
"
```
Expect: one line, `lint 600.0`.

## Log (append only)

1. 2026-10-12 human: created.
