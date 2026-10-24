# The checkout and the state directory are settings

## Description

The factory's own checkout lies at `/work/checkout` and its state directory at `/state`: both are fixed in the code (`CHECKOUT_PATH` and `STATE_DIRECTORY` of `factory.domain.settings`), because in v1.1's container they are volumes and nothing else needs to move them. On the machine of v1.2 the factory runs as a systemd service on the host, under `/srv/factory/<instance>` (`planning/v1.2-plan.md`, "The cycle of a stage", step 1: the factory's own clone at `/srv/factory/<instance>/repo`; "Where the factory runs": `/state` as a folder of the service), and S0003's environment file names both places. This story makes them settings: `FACTORY_CHECKOUT` and `FACTORY_STATE`, each an absolute path, each with today's value as its default, read by `read_settings` with the faults the other path settings have, and makes `factory-run` write the stop of invalid settings into the directory `FACTORY_STATE` names, so that a fault on the VM lands where `factory-health --state-directory` reads it. The name `FACTORY_STATE` is the one the entrypoint already reads for `/state/runs`. What stays: a compose instance that sets neither variable runs exactly as today; `factory-health` keeps its `--state-directory` option and its default `/state`; the entrypoint is unchanged; every other setting and fault is unchanged (decision 1 of `feature.md`).

## Interface

`factory.domain.settings` (`domain`):

```python
CHECKOUT_VARIABLE = "FACTORY_CHECKOUT"
STATE_VARIABLE = "FACTORY_STATE"
```

- `read_settings(environ, ...)` reads the two variables, each stripped of surrounding whitespace; a blank or unset value gives the default (`CHECKOUT_PATH`, `/work/checkout`; `STATE_DIRECTORY`, `/state`). A relative value is `SettingsInvalid(<variable>, "is not an absolute path")`. The two are read after the instance's name and before the agent home, so a fault in them is reported before a fault in any later variable; `InstanceSettings.checkout` and `InstanceSettings.state_directory` take them. `InstanceSettings` built directly refuses a relative `checkout` or `state_directory` through a validator (`ValidationError`), and accepts any absolute path.
- Nothing else of the settings changes: `CHECKOUT_PATH` and `STATE_DIRECTORY` keep their names and values (`tests/test_image_gitconfig.py` reads `CHECKOUT_PATH`).

`factory.entry.run` (`entry`):

```python
def main(
    environ: Mapping[str, str] | None = None,
    *,
    runner: Callable[[InstanceSettings], None] | None = None,
    state_directory: Path | None = None,
    clock: Clock | None = None,
) -> int: ...
```

- When `state_directory` is `None`, the stop of invalid settings (`settings invalid: <variable>: <fault>` in the factory log, the `preflight_failed` stop in `health.json`) is written to the directory `FACTORY_STATE` names in the environment read (stripped) when it is set, non-blank and absolute, else to `STATE_DIRECTORY`. A `state_directory` given is used as today. A relative `FACTORY_STATE` is itself the fault reported, and the stop goes to `STATE_DIRECTORY`.

`factory.entry.health` (`entry`): unchanged; `--state-directory` stays, default `STATE_DIRECTORY`.

Tests (the tester writes them): `tests/domain/test_settings_paths.py` and `tests/entry/test_run_state_variable.py` (built like `tests/entry/test_run.py`, with a runner that raises or records and a manual clock). The existing settings and run tests are unchanged.

## Acceptance criteria

1. `read_settings` (rows of one parametrized test over `BASE` of `tests/settings_support.py`): neither variable gives `checkout` `Path("/work/checkout")` and `state_directory` `Path("/state")`; `FACTORY_CHECKOUT=/srv/factory/vm/repo` and `FACTORY_STATE=/srv/factory/vm/state` give those two paths; `FACTORY_CHECKOUT=  /srv/factory/vm/repo  ` (surrounding spaces) gives `Path("/srv/factory/vm/repo")`; an empty `FACTORY_STATE` gives `Path("/state")`.
2. The faults (rows of one parametrized test, each `SettingsInvalid` with the named variable and the text `is not an absolute path`): `FACTORY_CHECKOUT=srv/repo`; `FACTORY_STATE=state`; `FACTORY_STATE=./state`; and the order: `FACTORY_CHECKOUT=relative` together with `FACTORY_MIN_FREE_GB=0` reports `FACTORY_CHECKOUT`, while `FACTORY_INSTANCE=Bad` together with `FACTORY_CHECKOUT=relative` reports `FACTORY_INSTANCE`.
3. `InstanceSettings` built directly (rows of one parametrized test through a `type[BaseModel]`): `checkout=Path("/srv/factory/vm/repo")` is accepted; `checkout=Path("srv/repo")` is `ValidationError`; `state_directory=Path("/srv/factory/vm/state")` is accepted; `state_directory=Path("state")` is `ValidationError`.
4. `factory.entry.run.main` with an invalid environment (a `FACTORY_REPOSITORY_URL` that names two repositories, as `tests/entry/test_run.py` does) and `FACTORY_STATE=<tmp>/state`, without `state_directory`: returns 2, `<tmp>/state/factory.log` holds the line ending `settings invalid: FACTORY_REPOSITORY_URL: names more than one repository`, `<tmp>/state/health.json` holds the `preflight_failed` stop with that detail, and nothing is written under the default `/state` (the test passes a `clock` and reads the two files under `<tmp>`).
5. `main` with an invalid environment whose `FACTORY_STATE` is itself relative (`state`), without `state_directory`: returns 2, writes nothing under `<tmp>` and prints to standard error the line `factory-run: settings invalid: FACTORY_STATE: is not an absolute path` when `/state` cannot be written, or, when it can (the container's `/state` exists and is the factory's), writes the stop there (the test asserts the return code and the standard error line's presence or the stop's presence by whether `/state` is writable, in one row each); `main(..., state_directory=<tmp>/other)` with `FACTORY_STATE=<tmp>/state` writes the stop under `<tmp>/other` and nothing under `<tmp>/state` (a given directory wins).
6. `main` with a valid environment (the hosted environment of `tests/entry/test_run.py` with `FACTORY_CHECKOUT=<tmp>/repo` and `FACTORY_STATE=<tmp>/state`) and a recording runner: the runner receives settings whose `checkout` is `<tmp>/repo` and `state_directory` `<tmp>/state`, and `main` returns 0.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, *Configuration*: two table rows, `FACTORY_CHECKOUT` (no; the factory's own checkout, an absolute path; default `/work/checkout`; a relative path is refused with `FACTORY_CHECKOUT` as the variable) and `FACTORY_STATE` (no; the state directory, an absolute path; default `/state`; a relative path is refused with `FACTORY_STATE` as the variable; `factory-health --state-directory <it>` reads the same place), and the paragraph "The checkout and the state directory are not settings you can change ..." rewritten: they are, through these two variables, the image leaves both unset, and the VM of v1.2 sets both under `/srv/factory/<instance>` (pointing to `## The machine`); *When the process refuses to start*: the stop and the log line go to the directory `FACTORY_STATE` names, else `/state`, and a relative `FACTORY_STATE` is the fault itself; *The entrypoint*: the sentence "(the factory ignores `FACTORY_STATE`: the state directory is fixed)" becomes one that says the factory reads it too; *The health check and the restart policy*: the `--state-directory` option of `factory-health`. `docs/project-guide/git-and-hosting.md` (which names `factory.domain.settings`): one sentence on the two path settings and their validator; `docs/project-guide/watching.md` (which names `factory.entry.run` and `factory.entry.health`): where the stop of invalid settings goes. `docs/decisions.md`: a closing line under "The services read the instance's settings from `Boundaries.settings`" or a new short entry "The checkout and the state directory are settings" naming 2026-10-24, `planning/v1.2-plan.md` and F0043, the documenter's choice. `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
from pathlib import Path

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import CHECKOUT_PATH, STATE_DIRECTORY, read_settings

base = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "vm"}
s = read_settings({**base, "FACTORY_CHECKOUT": " /srv/factory/vm/repo ", "FACTORY_STATE": "/srv/factory/vm/state"})
print(s.checkout, s.state_directory)
d = read_settings(base)
print(d.checkout == CHECKOUT_PATH, d.state_directory == STATE_DIRECTORY, d.checkout, d.state_directory)
for extra in ({"FACTORY_CHECKOUT": "srv/repo"}, {"FACTORY_STATE": "./state"}, {"FACTORY_CHECKOUT": "x", "FACTORY_MIN_FREE_GB": "0"}):
    try:
        read_settings({**base, **extra})
    except SettingsInvalid as error:
        print(error.variable, "|", error.fault)
EOF
```
Expect: five lines: `/srv/factory/vm/repo /srv/factory/vm/state`; `True True /work/checkout /state`; `FACTORY_CHECKOUT | is not an absolute path`; `FACTORY_STATE | is not an absolute path`; `FACTORY_CHECKOUT | is not an absolute path`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
FACTORY_REPOSITORY_URL='https://example.invalid/a.git,https://example.invalid/b.git' FACTORY_INSTANCE=vm FACTORY_STATE="$d/state" uv run factory-run; echo "status $?"
grep -c 'settings invalid: FACTORY_REPOSITORY_URL: names more than one repository' "$d/state/factory.log"; grep -c preflight_failed "$d/state/health.json"
```
Expect: four lines: the time-stamped line ending `settings invalid: FACTORY_REPOSITORY_URL: names more than one repository`, `status 2`, `1`, `1`

```bash
uv run pytest tests/domain/test_settings_paths.py tests/entry/test_run_state_variable.py tests/domain/test_settings.py tests/entry/test_run.py tests/entry/test_health.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal
