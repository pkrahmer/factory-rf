# One script turns a bare job into a running instance

## Description

On a Cloud Run job nothing is installed and nothing persists: the root filesystem is memory, there is no registry the factory can push an image to, every start is a first boot. `vm/job-start.sh` is the job's command: it turns a bare `debian:trixie-slim` into a running instance and ends in `exec factory-run`. In order it checks its inputs, routes `apt` through the proxy, installs podman, nftables, fuse-overlayfs, git, make, curl, rsync and python, installs the upstream runc release after checking its SHA-256, rejects TCP port 80 to the metadata address (S0003's rule), makes the directories, clones the factory's code without a credential (S0005), installs `uv` and the factory's environment, builds the stage image from the code checkout's `vm/Dockerfile` with the job's podman options, makes the empty base the copy snapshots need (S0001), starts the token refresher once synchronously and then in the background when a token endpoint is configured (S0004), and starts the instance with the profile `job` (S0002). The job's own environment is the instance's configuration; the script sets the derived variables only where the job gave none. Measured on 2026-10-31 (`planning/cloud-sandbox/`): the install, the clone and the image build fit a start of a few minutes, and a job of 8 vCPU and 16 to 32 GiB holds the checkout, the base copy and the image. The operator guide gains the chapter *On Cloud Run*. Unchanged: `vm/setup.sh` and the VM path, every setting. Left out: creating the job, its secrets and its schedule.

## Interface

No module under `src/factory/` changes. The coder adds `vm/job-start.sh` (POSIX `sh`) and changes `vm/Dockerfile` only if its test of floating references needs it (it should not).

Inputs (the job's environment): required `FACTORY_INSTANCE`, `FACTORY_REPOSITORY_URL`, `FACTORY_CODE_URL`, `FACTORY_TOKEN_FILE` (a readable file, the hosting token); optional `FACTORY_CODE_REF` (default `main`), `FACTORY_STAGE_IMAGE` (default `factory-stage:<instance>`), `FACTORY_JOB_ROOT` (default `/srv/factory/<instance>`), `FACTORY_JOB_PREFIX` (default empty: put in front of the system paths `/etc` and `/usr/local/bin`, for tests), `RUNC_VERSION` (default a pinned version in the script, with its SHA-256 in the script), `HTTPS_PROXY`/`https_proxy` (when set, `apt` and every download use it), `FACTORY_TOKEN_URL` with its companions (S0004; when `FACTORY_TOKEN_URL` is set the refresher runs). A missing required input is `job-start: <name> is not set` on standard error, exit 2, before anything else runs.

The script sets, only where the environment has no value: `FACTORY_SNAPSHOTS=copy`, `FACTORY_SNAPSHOT_BASE=<root>/base`, `FACTORY_WORKSPACE=<root>/work`, `FACTORY_CHECKOUT=<root>/repo`, `FACTORY_STATE=<root>/state`, `FACTORY_CLAUDE_HOME=<root>/factory/claude`, `FACTORY_IMAGE_ID_FILE=<root>/image-id`, `FACTORY_CONTAINER_PROFILE=job`, `FACTORY_AGENT_RUNTIME=opencode`, `FACTORY_CONTAINER_ENV` and `FACTORY_CA_BUNDLE` untouched.

Steps, in this order, each printing `job-start: <step>` on standard output: `inputs`, `proxy` (writes `<prefix>/etc/apt/apt.conf.d/99proxy` when a proxy is set), `packages` (`apt-get update`, then one `apt-get install -y --no-install-recommends` of `podman uidmap fuse-overlayfs nftables git make curl ca-certificates rsync python3 python3-venv`, no exact versions), `runc` (download `runc.amd64` and `runc.sha256sum` of `RUNC_VERSION` from the project's release, `sha256sum -c`, install as `<prefix>/usr/local/bin/runc`; a mismatch stops with `job-start: runc: checksum does not match` and exit 1), `metadata` (writes `<root>/metadata-block.nft` with the table `inet factory_block`, chains `blockout` (hook output) and `blockfwd` (hook forward), both `ip daddr 169.254.169.254 tcp dport 80 reject`, and loads it with `nft -f`), `directories` (the workspace, the empty base, the checkout, the state), `code` (`git clone --branch <ref> <code url> <root>/factory` with `GIT_TERMINAL_PROMPT=0` and no credential), `tools` (a virtual environment `<root>/tools` with `uv`, then `uv sync --frozen --no-dev` in the code checkout), `image` (`podman` with `JOB_PODMAN_OPTIONS`, `build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=<ref> -t <image> <root>/factory`, then a new uuid in the image-id file), `token` (when `FACTORY_TOKEN_URL` is set: `python -m factory.entry.refresh_token --once`, which must succeed, then the same command without `--once` in the background), `start` (`exec <root>/factory/.venv/bin/factory-run`).

A secret file's content is never printed, and the script passes no secret on a command line.

Tests (the tester writes them): `tests/test_vm_job_start.py`, through `tests/vm_support.py` and a folder of stand-in executables (`apt-get`, `curl`, `sha256sum`, `install`, `nft`, `git`, `python3`, `uv`, `podman`, `factory-run`) that record their arguments, with `FACTORY_JOB_ROOT` and `FACTORY_JOB_PREFIX` in `tmp_path`.

## Acceptance criteria

1. A missing required input stops the script before any stand-in is called: rows for `FACTORY_INSTANCE`, `FACTORY_REPOSITORY_URL`, `FACTORY_CODE_URL` and `FACTORY_TOKEN_FILE` (also a path that is no file), each exit 2 and `job-start: <name> is not set` (or `is not a file`).
2. With every input given, the steps print in the order of the Interface and the stand-ins are called in that order; the last call is `factory-run`, started with `exec` (the stand-in's parent is the script's own process).
3. With a proxy set, `99proxy` holds both `Acquire::http::Proxy` and `Acquire::https::Proxy` with its value; without one the file is not written.
4. The package install is one `apt-get install` naming exactly the packages of the Interface and no `=`.
5. The runc step downloads `runc.amd64` and `runc.sha256sum` of `RUNC_VERSION` from the release URL, runs `sha256sum -c`, and installs the binary only after it passed; a stand-in `sha256sum` that fails stops the script with `job-start: runc: checksum does not match`, exit 1, and `install`, `git` and `podman` are never called.
6. `<root>/metadata-block.nft` holds the table `inet factory_block`, two chains named `blockout` and `blockfwd` with the hooks `output` and `forward`, each with the rule `ip daddr 169.254.169.254 tcp dport 80 reject`, and `nft` is called with `-f` and that file; no chain is named `fwd`.
7. The directories exist with an empty base; the `git clone` call has `--branch <ref>` (default `main`, `FACTORY_CODE_REF` when set), the code url, `GIT_TERMINAL_PROMPT=0` and no `GIT_ASKPASS` and no `core.askPass`.
8. The `podman` call of the image step starts with the four `JOB_PODMAN_OPTIONS`, then `build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=<ref> -t <image> <root>/factory`; the image-id file holds a uuid afterwards.
9. With `FACTORY_TOKEN_URL` set the stand-in `python3 -m factory.entry.refresh_token --once` runs once and, when it exits 0, the same command without `--once` is started in the background; when `--once` exits 1 the script stops with exit 1 before `factory-run`; without the variable neither runs.
10. The environment of `factory-run` holds the derived variables of the Interface where the input had none and the input's values where it had.
11. No file or output of a run contains the content of the token file (a test with the text `s3cret-token-text`).
12. `make check` stays green.
13. docs: `docs/operator-guide.md`: a chapter *On Cloud Run* with: what the job needs (the size and the numbers measured: copy reset about 1.6 s per GiB, memory-backed root, 16 GiB or more, a task timeout of 24 hours and a nightly re-execution, the proxy and the shared connector, secrets mounted as files with `--set-secrets` paths, the environment variables of this script), the order of the script's steps, what a restart costs (the factory's recovery charges one crash for the stage in flight; the checkout, the base and the image are rebuilt, a few minutes), what does not work (rootless, a bridge network, a pushed image, a second job sharing the disk), the free-model note (a price of 0 makes `budget_usd` inert, the time limit is the only bound), and the generic `gcloud run jobs create` flags with placeholders. `docs/project-guide/README.md`: the files line names `vm/job-start.sh`. `docs/decisions.md`: an entry *A bare job becomes an instance at start*, from the feature's decisions 10 to 12. `README.md`: one sentence that the factory also runs in a job, with the pointer to the chapter.

## Smoke test

```bash
sh vm/job-start.sh; echo "exit $?"
```
Expect: two lines, `job-start: FACTORY_INSTANCE is not set` and `exit 2`

```bash
grep -c 'ip daddr 169.254.169.254 tcp dport 80 reject' vm/job-start.sh
```
Expect: `2`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
