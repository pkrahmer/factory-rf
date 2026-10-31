# The container profile job

## Description

`PodmanRuns` starts every container rootless with `--userns=keep-id`, on podman's default network and storage. In a Cloud Run job that cannot work: the job's root has `NoNewPrivs` (no `newuidmap`), the cgroup layout is hybrid (crun refuses it, runc accepts it), the root filesystem is an overlay (podman's overlay storage needs a mount program), no bridge network reaches the outside, and podman copies the job's proxy variables into every container. Measured on 2026-10-31 (`planning/cloud-sandbox/`, P2, P3, P10, P11): Podman 5.4 with `--runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay --storage-opt overlay.mount_program=/usr/bin/fuse-overlayfs`, `--network=host`, `--http-proxy=false`, as root with `--cap-drop=all`, ran the factory's other flags (`--timeout` ending a container with exit status 255, `--pids-limit`, `--memory`, `--security-opt=no-new-privileges`, bind mounts, `:ro`). This story adds the setting `FACTORY_CONTAINER_PROFILE` with the value `job` and gives `PodmanRuns` that profile. Unchanged: the default profile `rootless` and its words, the container call's DTOs, the grace and the exit-status reading (255 at or after the limit is the time limit, as today). Left to later stories: the metadata proof (S0003) and the start script (S0006).

## Interface

`factory.domain.settings` (domain): `CONTAINER_PROFILE_VARIABLE = "FACTORY_CONTAINER_PROFILE"` and the field `InstanceSettings.container_profile: Literal["rootless", "job"] = "rootless"`; unset or blank is `rootless`, `job` is accepted, anything else is `SettingsInvalid(FACTORY_CONTAINER_PROFILE, "is neither rootless nor job")`.

`factory.domain.containers` (domain): `JOB_PODMAN_OPTIONS: tuple[str, ...]` = `("--runtime=runc", "--cgroup-manager=cgroupfs", "--storage-driver=overlay", "--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs")`.

`factory.adapters.podman_runs` (adapters): `PodmanRuns(executable, image, workspace, *, time_limit=PODMAN_TIME_LIMIT, profile: Literal["rootless", "job"] = "rootless")`.

- `rootless`: every word as today.
- `job`: `launch` gives `<executable> <JOB_PODMAN_OPTIONS...> run --rm --http-proxy=false --network=host --timeout <seconds> --cap-drop=all --security-opt=no-new-privileges --pids-limit=<PIDS_LIMIT> --memory=<MEMORY_LIMIT> <--env words> <--volume words> --workdir <dir> <image> <command...>`: no `--userns=keep-id`, the global options before `run`, the other words in today's order. `version` runs `<executable> <JOB_PODMAN_OPTIONS...> --version` and `image_exists` runs `<executable> <JOB_PODMAN_OPTIONS...> image exists <image>`. Mounts, the grace, the mapping of results and the `ValueError` rules are those of `rootless`.
- The profile is fixed at construction and changes nothing else.

`factory.entry.wiring` (entry): `_container_adapters` gives `PodmanRuns` the setting's profile.

Tests (the tester writes them): `tests/domain/test_settings_container_profile.py`, `tests/adapters/test_podman_runs_job_profile.py` (the stand-in `podman` of `tests/podman_support.py`), `tests/entry/test_wiring_container_profile.py`. `tests/adapters/test_podman_runs*.py` pass unchanged.

## Acceptance criteria

1. With `FACTORY_CONTAINER_PROFILE` unset the words of `PodmanRuns.launch`, `version` and `image_exists` are exactly those of before this story (the existing tests pass unchanged; one new row compares a launch of the default with a launch of `profile="rootless"`).
2. `FACTORY_CONTAINER_PROFILE` is read, rows of one test: unset and blank give `rootless`; `job` gives `job`; `Job`, `root` and `job now` are refused as `is neither rootless nor job`.
3. A `job` launch of the command `["make", "check"]` with one environment entry `A=1`, one read-write mount and one `:ro` mount, the limit 90 s and the working directory `/work/checkout` has exactly these words in this order: the executable, the four `JOB_PODMAN_OPTIONS`, `run`, `--rm`, `--http-proxy=false`, `--network=host`, `--timeout`, `90`, `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g`, `--env`, `A=1`, the workspace volume, the two mount volumes (the second ending `:ro`), `--workdir`, `/work/checkout`, the image, `make`, `check`; its time limit is 90 s plus the grace, its environment `None`.
4. A `job` launch contains none of `--userns=keep-id` and `--user`.
5. `version` of a `job` runner runs the executable, the four options and `--version`, and `image_exists` runs the executable, the four options, `image`, `exists` and the image name; their results and faults are those of `rootless` (exit 0 and 1, any other outcome a `ContainerError`).
6. `run` of a `job` runner reads the end as `rootless` does: exit status 255 at or after the limit is `timed_out`, 255 before it is the command's own, 125 is podman's own fault.
7. `build_boundaries` with the setting `job` gives a `PodmanRuns` whose launch has the four global options; with the setting unset, none.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: the variable in the configuration table and a subsection *The job profile*: what each word is for, with the measured facts (crun and Podman 6 refuse the hybrid cgroups, rootless is impossible under `NoNewPrivs`, no bridge reaches outside), and that the container runs as the job's root with every capability dropped. `docs/project-guide/stage-environment.md`: *The podman adapter* gains the profile and its words. `docs/decisions.md`: an entry *A root container profile for a managed sandbox*, from the feature's decisions 3 to 5. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from datetime import timedelta
from pathlib import Path
from factory.adapters.podman_runs import PodmanRuns
runs = PodmanRuns('podman', 'img:1', Path('/work'), profile='job')
launch = runs.launch(['true'], mounts=[], environment={}, time_limit=timedelta(seconds=10), working_directory='/work/checkout')
print(launch.argv[:6])
print('--userns=keep-id' in launch.argv, '--network=host' in launch.argv)
"
```
Expect: two lines, `['podman', '--runtime=runc', '--cgroup-manager=cgroupfs', '--storage-driver=overlay', '--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs', 'run']` and `False True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
