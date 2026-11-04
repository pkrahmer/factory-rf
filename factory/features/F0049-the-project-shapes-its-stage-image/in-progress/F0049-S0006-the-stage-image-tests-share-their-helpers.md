# The stage image's tests share their helpers and pin the image without an environment

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

The reviewers of F0049-S0002 and F0049-S0003 left notes that were not findings, and the coders carried them as "noticed, not touched" to the end of each story: copies of shared test values and helpers, and one side of `PodmanImages.path` that the code handles but no row pins. This story is for the tester alone and changes no code. `tests/adapters/test_podman_images.py` and `tests/entry/test_wiring_image_path.py` define the base `PATH` again (`SYSTEM_PATH`, `BASE_PATH`) in place of importing `SYSTEM_PATH` from `factory.domain.containers`; `tests/entry/test_wiring_image_path.py` copies `PROBE` and `COMPLETED` from `tests/entry/test_wiring_run.py`, and both hold values that `tests/probe_support.py` (`COMPLETED`, the probe's result) and `tests/agent_definition_support.py` (`COMPLETED`) already share; `Machine.log_lines` in `tests/application/test_tick_preflight.py` copies the body of `state_log_lines` of `tests/log_support.py`; and `test_path_is_the_images_configured_path_or_the_base_default` has no row for `podman image inspect` printing `null`, which podman prints for an image that configures no environment (`src/factory/adapters/podman_images.py` returns the default `PATH` for it). The move is made under the standing leave of `CLAUDE.md` (*Tests*): every earlier test keeps its name and checks the same thing. `STAND_IN` in `tests/adapters/test_podman_images.py`, a variant of `PODMAN_SCRIPT` in `tests/podman_support.py` that also lists the build context, stays as it is; folding the two is left to a later story.

## Interface

- No module under `src/factory/` changes.
- `tests/adapters/test_podman_images.py`: `SYSTEM_PATH` imported from `factory.domain.containers`; its local definition removed; a row `null` in `test_path_is_the_images_configured_path_or_the_base_default` whose printed output is `null` and whose expected `PATH` is `SYSTEM_PATH`.
- `tests/entry/test_wiring_image_path.py`: `BASE_PATH` replaced by `SYSTEM_PATH` from `factory.domain.containers`; `PROBE` imported as `COMPLETED as PROBE` from `tests/probe_support.py` and `COMPLETED` from `tests/agent_definition_support.py`, which hold the same values; `tests/entry/test_wiring_run.py` does the same (standing leave). The other modules that define their own `PROBE` or `COMPLETED` stay as they are.
- `tests/application/test_tick_preflight.py`: `Machine.log_lines` returns `state_log_lines(self.directory / "state")` from `tests/log_support.py` (standing leave). `log_lines` of `tests/log_support.py` keeps its body, which `tests/test_shared_bodies.py` uses as its sample.
- `tests/vm_support.py` keeps its own `SYSTEM_PATH`: it describes the VM's shell, not the image's default.

## Acceptance criteria

1. `PodmanImages.path` given inspect output `null` returns `/usr/local/bin:/usr/bin:/bin`, as a row of `test_path_is_the_images_configured_path_or_the_base_default` beside `with-path` and `without-path`.
2. Under `tests/`, outside `tests/vm_support.py`, no module assigns the text `"/usr/local/bin:/usr/bin:/bin"` to a name; the two modules above import `SYSTEM_PATH` from `factory.domain.containers`.
3. Neither `tests/entry/test_wiring_run.py` nor `tests/entry/test_wiring_image_path.py` assigns `PROBE` or `COMPLETED`; both import them from `tests/probe_support.py` and `tests/agent_definition_support.py`, and every test in both modules keeps its name and passes.
4. `Machine.log_lines` in `tests/application/test_tick_preflight.py` calls `state_log_lines`; every test in that module keeps its name and passes, and `tests/test_shared_bodies.py` passes unchanged.
5. `make check` stays green.
6. docs: none: no behaviour, command or decision changes, and the test conventions of `CLAUDE.md` already cover the move.

## Smoke test

```bash
grep -rlF '= "/usr/local/bin:/usr/bin:/bin"' tests | grep -v '^tests/vm_support.py$' | wc -l
grep -hE '^(PROBE|COMPLETED) = ' tests/entry/test_wiring_run.py tests/entry/test_wiring_image_path.py | wc -l
uv run pytest tests/adapters/test_podman_images.py tests/entry/test_wiring_image_path.py tests/entry/test_wiring_run.py tests/application/test_tick_preflight.py tests/test_shared_bodies.py 2>&1 | tail -1
```

Expect: `0`, `0`, then a line that ends in `passed` with no `failed`.

## Journal
