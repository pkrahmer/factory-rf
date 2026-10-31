---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 488
comments_read: [6550566644]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T23:25:12.826835Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T23:25:12.833035Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-31T23:25:40.549890Z'
  stage: intake
  run: 4ef04e44d3674c7fb9591d8a13156115
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-31T23:26:56.150102Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-31T23:27:13.865521Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-31T23:27:45.804491Z'
  stage: intake
  run: 5a724fd32469478ca5e5bfa5336a2e2a
---

# One script turns a bare job into a running instance

## Description

On a Cloud Run job nothing is installed and nothing persists: the root filesystem is memory, there is no registry the factory can push an image to, every start is a first boot. `vm/job-start.sh` is the job's command: it turns a bare `debian:trixie-slim` into a running instance and ends in `exec factory-run`. In order it checks its inputs, routes `apt` through the proxy, installs podman, nftables, git, make, curl, rsync and python, mounts a tmpfs at podman's storage root so that images use the kernel's native overlay (S0009; P16), installs the upstream runc release after checking its SHA-256, rejects TCP port 80 to the metadata address (S0003's rule), makes the directories, clones the factory's code without a credential (S0005), installs `uv` and the factory's environment, builds the stage image from the code checkout's `vm/Dockerfile` with the job's podman options, makes the empty base the copy snapshots need (S0001), starts the token refresher once synchronously and then in the background when a token endpoint is configured (S0004), and starts the instance with the profile `job` (S0002). The job's own environment is the instance's configuration; the script sets the derived variables only where the job gave none. Measured on 2026-10-31 (`planning/cloud-sandbox/`): the install, the clone and the image build fit a start of a few minutes, and a job of 8 vCPU and 16 to 32 GiB holds the checkout, the base copy and the image. The operator guide gains the chapter *On Cloud Run*. Because the job rebuilds the stage image at every start, `vm/Dockerfile`'s seven Debian packages lose their exact versions (the human, 2026-10-31): Debian's mirror keeps only a package's current version, so a pin breaks the build at the next point release, and within one stable release Debian ships only security and serious fixes. The base image stays pinned by its digest, which also fixes the Debian release, and `uv`, Claude Code and opencode keep their exact versions, because they shape a stage's result and their registries keep every version. This changes the VM's image too: its next rebuild takes the current packages of the same release. Unchanged: `vm/setup.sh` and the VM path otherwise, every setting. Left out: creating the job, its secrets and its schedule.

## Interface

No module under `src/factory/` changes. The coder adds `vm/job-start.sh` (POSIX `sh`) and changes `vm/Dockerfile`: the `apt-get install` line names `git make curl ca-certificates procps nodejs npm` without `=<version>`, everything else in the file as it is (the base image's digest, `UV_VERSION`, `CLAUDE_CODE_VERSION`, `OPENCODE_VERSION`, the order of the instructions, the comment on line 2 now says that every tool that shapes a result is pinned and Debian's packages follow the base image's release).

`tests/test_stage_image.py` (the tester, under this story's leave to change an earlier test): `test_the_stage_image_has_no_floating_reference` keeps the rule for everything but the stage image's Debian packages; the findings of `floating_references` for an `apt-get install` of exactly the seven package names without versions are allowed, and any other finding still fails it. `tests/dockerfile_support.py` and `tests/test_pins.py` stay as they are: the rule itself, as other images use it, is unchanged.

Inputs (the job's environment): required `FACTORY_INSTANCE`, `FACTORY_REPOSITORY_URL`, `FACTORY_CODE_URL`, `FACTORY_CODE_REF` (a tag or a commit the operator moves deliberately; no default, so that nothing pushed to the code repository's `main` reaches a job unseen: the human, 2026-10-31), `FACTORY_TOKEN_FILE` (a readable file, the hosting token); optional `FACTORY_STAGE_IMAGE` (default `factory-stage:<instance>`), `FACTORY_JOB_ROOT` (default `/srv/factory/<instance>`), `FACTORY_JOB_PREFIX` (default empty: put in front of the system paths `/etc` and `/usr/local/bin`, for tests), `RUNC_VERSION` and `RUNC_SHA256` (default `1.5.2` and `599f6f94ff8c5057241eff0d54c3c74f95c34935b6457b33fe545defc61e9488`, the SHA-256 of that release's `runc.amd64` as published in its `runc.sha256sum`, read on 2026-10-31; the version measured in P3; both in the script as constants; a `RUNC_VERSION` set without `RUNC_SHA256` is `job-start: RUNC_SHA256 is not set`, exit 2, because a version without its checksum is not checked), `HTTPS_PROXY`/`https_proxy` (when set, `apt` and every download use it), `FACTORY_TOKEN_URL` with its companions (S0004; when `FACTORY_TOKEN_URL` is set the refresher runs). A missing required input is `job-start: <name> is not set` on standard error, exit 2, before anything else runs.

The script sets, only where the environment has no value: `FACTORY_SNAPSHOTS=copy`, `FACTORY_SNAPSHOT_BASE=<root>/base`, `FACTORY_WORKSPACE=<root>/work`, `FACTORY_CHECKOUT=<root>/repo`, `FACTORY_STATE=<root>/state`, `FACTORY_CLAUDE_HOME=<root>/factory/claude`, `FACTORY_IMAGE_ID_FILE=<root>/image-id`, `FACTORY_CONTAINER_PROFILE=job`, `FACTORY_AGENT_RUNTIME=opencode`, `FACTORY_IDLE_SHUTDOWN_ACTION=exit` (S0008; `FACTORY_IDLE_SHUTDOWN_MINUTES` stays the operator's, off when unset), `FACTORY_CONTAINER_ENV` and `FACTORY_CA_BUNDLE` untouched.

Steps, in this order, each printing `job-start: <step>` on standard output: `inputs`, `proxy` (writes `<prefix>/etc/apt/apt.conf.d/99proxy` when a proxy is set), `packages` (`apt-get update`, then one `apt-get install -y --no-install-recommends` of `podman uidmap nftables git make curl ca-certificates rsync python3 python3-venv`, no exact versions), `runc` (download `runc.amd64` of `RUNC_VERSION` from `https://github.com/opencontainers/runc/releases/download/v<version>/runc.amd64`, check it with `sha256sum -c` against `RUNC_SHA256`, the checksum in the script and not one downloaded beside the binary, install as `<prefix>/usr/local/bin/runc`; a mismatch stops with `job-start: runc: checksum does not match` and exit 1), `metadata` (writes `<root>/metadata-block.nft` with the table `inet factory_block`, chains `blockout` (hook output) and `blockfwd` (hook forward), both `ip daddr 169.254.169.254 tcp dport 80 reject`, and loads it with `nft -f`), `directories` (the workspace, the empty base, the checkout, the state), `storage` (`mount -t tmpfs tmpfs <prefix>/var/lib/containers`, podman's storage root for root, on every start, since a job starts bare; a failed mount stops with `job-start: storage: cannot mount a tmpfs at <path>` and exit 1, because an overlay on the job's root filesystem cannot work), `code` (`git clone --no-checkout <code url> <root>/factory` and `git -C <root>/factory checkout --detach <FACTORY_CODE_REF>`, both with `GIT_TERMINAL_PROMPT=0` and no credential), `tools` (a virtual environment `<root>/tools` with `uv`, then `uv sync --frozen --no-dev` in the code checkout), `image` (`podman` with `JOB_PODMAN_OPTIONS`, `build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=<FACTORY_CODE_REF> -t <image> <root>/factory`, then a new uuid in the image-id file), `token` (when `FACTORY_TOKEN_URL` is set: `<root>/factory/.venv/bin/python -m factory.entry.refresh_token --once`, the factory's own environment and never the system's `python3`, which must succeed, then the same command without `--once` in the background), `start` (`exec <root>/factory/.venv/bin/factory-run`).

`JOB_PODMAN_OPTIONS` is one shell constant in `vm/job-start.sh` holding the three words of S0009's `JOB_PODMAN_OPTIONS` in `factory.domain.containers`: `--runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay`.

The proxy is the value of `HTTPS_PROXY` when it is set, else of `https_proxy`; the script exports it under both spellings for every later step, so the `curl` and `git` stand-ins see both with that value, and with neither set they see neither.

The script stops at the first failing step with exit 1 and `job-start: <step>: failed` on standard error (the steps with their own message keep it), and `factory-run` is never called.

A secret file's content is never printed, and the script passes no secret on a command line.

Tests (the tester writes them): `tests/test_vm_job_start.py`, through `tests/vm_support.py` and a folder of stand-in executables (`apt-get`, `curl`, `sha256sum`, `install`, `nft`, `mount`, `git`, `python3`, `uv`, `podman`) that record their arguments, with `FACTORY_JOB_ROOT` and `FACTORY_JOB_PREFIX` in `tmp_path` (the default root `/srv/factory/<instance>` is tested from the script's text only, since a run cannot use `/srv`); the stand-in `uv`'s `sync` writes the two stand-ins the script runs from the factory's environment, `<root>/factory/.venv/bin/python` and `<root>/factory/.venv/bin/factory-run`.

## Acceptance criteria

1. A missing required input stops the script before any stand-in is called: rows for `FACTORY_INSTANCE`, `FACTORY_REPOSITORY_URL`, `FACTORY_CODE_URL`, `FACTORY_CODE_REF` and `FACTORY_TOKEN_FILE` (also a path that is no file), each exit 2 and `job-start: <name> is not set` (or `is not a file`).
2. With every input given, the steps print in the order of the Interface and the stand-ins are called in that order; the last call is `factory-run`, started with `exec` (the stand-in's parent is the script's own process).
3. With a proxy set, `99proxy` holds both `Acquire::http::Proxy` and `Acquire::https::Proxy` with its value; without one the file is not written.
4. The package install is one `apt-get install` naming exactly the packages of the Interface and no `=`.
5. The runc step downloads only `runc.amd64` of `RUNC_VERSION` from the release URL (default `v1.5.2`), feeds `sha256sum -c` the line `<RUNC_SHA256>  <the downloaded file>` (default the checksum of the Interface; no checksum file is downloaded), and installs the binary only after it passed; `RUNC_VERSION` without `RUNC_SHA256` exits 2 before any stand-in is called; a stand-in `sha256sum` that fails stops the script with `job-start: runc: checksum does not match`, exit 1, and `install`, `git` and `podman` are never called; a row with both `RUNC_VERSION` and `RUNC_SHA256` given replaces the version in the URL and the checksum fed to `sha256sum -c`.
6. `<root>/metadata-block.nft` holds the table `inet factory_block`, two chains named `blockout` and `blockfwd` with the hooks `output` and `forward`, each with the rule `ip daddr 169.254.169.254 tcp dport 80 reject`, and `nft` is called with `-f` and that file; no chain is named `fwd`.
7. The directories exist with an empty base; the code is fetched at exactly `FACTORY_CODE_REF` (a tag or a full commit id: a `git clone` without a checkout, then `git checkout --detach <ref>`; a ref that does not exist stops with `job-start: code: no ref <ref> in <code url>`, exit 1), from the code url, `GIT_TERMINAL_PROMPT=0` and no `GIT_ASKPASS` and no `core.askPass`.
8. The `mount` call of the step `storage` comes before any `podman` call and names `-t tmpfs` and `<prefix>/var/lib/containers`; a stand-in `mount` that fails stops the script with the sentence of the Interface, exit 1, and `podman` is never called. The `podman` call of the image step starts with the three `JOB_PODMAN_OPTIONS`, then `build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=<FACTORY_CODE_REF> -t <image> <root>/factory`, where `<image>` is `FACTORY_STAGE_IMAGE` when given and `factory-stage:<instance>` otherwise (two rows); the image-id file holds a uuid afterwards.
9. With `FACTORY_TOKEN_URL` set the environment's stand-in `<root>/factory/.venv/bin/python -m factory.entry.refresh_token --once` runs once (the system's `python3` stand-in is not called for it) and, when it exits 0, the same command without `--once` is started in the background; when `--once` exits 1 the script stops with exit 1 before `factory-run`; without the variable neither runs.
10. The environment of `factory-run` holds the derived variables of the Interface where the input had none and the input's values where it had; `FACTORY_CONTAINER_ENV`, `FACTORY_CA_BUNDLE` and `FACTORY_IDLE_SHUTDOWN_MINUTES` are absent from it when the input had none and hold the input's value when it had one.
11. No file or output of a run contains the content of the token file (a test with the text `s3cret-token-text`), and no recorded stand-in argument contains it.
12. `vm/Dockerfile` installs the seven Debian packages by name alone; `floating_references` of it lists only those seven, and `test_the_stage_image_has_no_floating_reference` passes; a stage image with a floating base image (a tag without a digest), a Claude Code, opencode or `uv` without an exact version, or an eighth Debian package without a version still fails it (rows over a changed copy of the file's text, as `tests/test_pins.py` does).
13. The proxy reaches every later step: rows with `HTTPS_PROXY` set, with only `https_proxy` set, and with neither; the `curl` and `git` stand-ins see `https_proxy` and `HTTPS_PROXY` with that value (`HTTPS_PROXY` wins when both are set), or see neither when none is set.
14. The words of the shell constant `JOB_PODMAN_OPTIONS` in `vm/job-start.sh` equal `factory.domain.containers.JOB_PODMAN_OPTIONS`.
15. The default `FACTORY_JOB_ROOT` is `/srv/factory/<instance>`, checked from the script's text, where it is written once.
16. A failing step stops the script with exit 1, `job-start: <step>: failed` on standard error and no call of `factory-run`: rows for a failing `curl` at `runc`, a failing `nft -f` at `metadata` and a failing `apt-get` at `packages`.
17. `make check` stays green.
18. docs: `docs/operator-guide.md`: a chapter *On Cloud Run* with: what the job needs (the size and the numbers measured: copy reset about 1.6 s per GiB, memory-backed root, 16 GiB or more, a task timeout of 24 hours and a nightly re-execution, the proxy and the shared connector (measured in P20: the job cannot resolve `github.com` itself and reaches both git over HTTPS and the REST API only through the proxy; the factory's own git and PyGithub read the job's `https_proxy`, so the job's environment carries it and `NO_PROXY` must not name a GitHub host), secrets mounted as files with `--set-secrets` paths, the environment variables of this script), the order of the script's steps, what a restart costs (the factory's recovery charges one crash for the stage in flight, and after `crash_cap` crashes, two by default, the work item waits for the human's answer, so a story in flight on two nights waits once; the state directory goes with the memory, so the log, `health.json` and the preflight stamp start empty and the preflight runs at every start; the checkout, the base and the image are rebuilt, a few minutes; accepted by the human on 2026-10-31, a stop between stages before the restart is a candidate for later), what does not work (rootless, a bridge network, a pushed image, a second job sharing the disk, `fuse-overlayfs` for podman's storage: three times slower, P15 and P16), that the image layers live in the tmpfs and count against the job's memory, that two executions of one job must never overlap (two would both act as the one instance), so the task timeout is shorter than the schedule's interval (23 hours for a daily schedule), what the timeout does (measured in P18: `SIGTERM` reaches `factory-run` exactly at the timeout with no warning before, the factory ends after the tick in progress, and the platform marks the execution failed with `The configured timeout was reached` even when the exit status is 0, so a nightly timeout is planned and not a fault; the job is created with `--max-retries=0`, or a timeout would start a second execution at once), that an execution whose `factory-run` exits 0 (the idle exit of S0008) ends as succeeded at once, background processes such as the refresher included (P18), that with `FACTORY_IDLE_SHUTDOWN_MINUTES` set the execution ends when idle and the next one starts at the schedule or by `gcloud run jobs execute`, the free-model note (a price of 0 makes `budget_usd` inert, the time limit is the only bound), and the generic `gcloud run jobs create` flags with placeholders. `docs/project-guide/README.md`: the files line names `vm/job-start.sh`. `docs/decisions.md`: an entry *A bare job becomes an instance at start*, from the feature's decisions 10 to 12, and an entry *Debian's packages follow the base image's release*, from decision 17, whose text says that it changes the rule of 2026-10-16 (*Every tool of the machine's image is pinned*) for the operating system's packages. `docs/operator-guide.md`, *The stage image* and *Update the pins*: the seven packages without versions, the base image's digest as what fixes the Debian release, and moving to a new Debian release as a deliberate change of the digest. `README.md`: one sentence that the factory also runs in a job, with the pointer to the chapter.

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
1. 2026-10-31 human: created.
2. factory: started intake as vm.
3. intake: Questions (the format check passed, so there are no findings from it):

   1. Interface, `image` step: `--build-arg FACTORY_IMAGE=<ref>` never says what `<ref>` is. Criterion 8 tests the argument without a value, so two coders will read it two ways. Please name the value, for example the base image reference taken from `vm/Dockerfile`, or the same value as `<image>`. I would choose to state it exactly and add it to criterion 8.

   2. Interface, `image` step: "the three `JOB_PODMAN_OPTIONS`" are not named here. Criterion 8 requires the podman call to start with them. Please say where they come from (a shell constant in `vm/job-start.sh`, or S0002's definition, with the file and name) and spell out their three words in the story. I would choose to list the three words in the Interface.

   3. Interface, proxy: "when set, `apt` and every download use it" states a behaviour, but criterion 3 covers only `99proxy`. No criterion says that the `runc` download (`curl`) and the `git clone` and checkout use the proxy, and none covers the precedence or the lowercase `https_proxy` spelling versus `HTTPS_PROXY`. I would add one criterion with rows: `HTTPS_PROXY` set, only `https_proxy` set, and neither. Each row checks that the `curl` and `git` stand-ins see the proxy, or do not see it when none is set.

   4. Interface, defaults: `FACTORY_STAGE_IMAGE` (default `factory-stage:<instance>`) and `FACTORY_JOB_ROOT` (default `/srv/factory/<instance>`) have no criterion. Criterion 10 covers only the derived `FACTORY_*` variables. A given `FACTORY_STAGE_IMAGE` and the default `-t <image>` of criterion 8 are untested, and so is the default root. Please add rows, for example the image name in the `podman build -t` call with and without `FACTORY_STAGE_IMAGE`. A test cannot use the `/srv` default root under `tmp_path`, so say whether that default is meant to be tested at all.

   5. Interface, "untouched" and "stays the operator's": `FACTORY_CONTAINER_ENV`, `FACTORY_CA_BUNDLE` and `FACTORY_IDLE_SHUTDOWN_MINUTES` are stated as left alone, with no criterion. Criterion 10 checks only the variables the script sets. I would add to criterion 10 that these three are absent from `factory-run`'s environment when the input had none, and present with the input's value when it had one.

   6. Interface, `RUNC_VERSION`/`RUNC_SHA256` set together: criterion 5 tests the defaults and the failure. It does not test that a given pair replaces both the URL's version and the checksum fed to `sha256sum -c`. Please add that row.

   7. Interface, "A secret file's content is never printed, and the script passes no secret on a command line": criterion 11 checks files and output only. Is "no secret on a command line" to be tested, with the recorded stand-in arguments not containing `s3cret-token-text`? I would add that to criterion 11.

   8. Failing sides not covered: (a) a `curl` download that fails (stand-in exits non-zero) at the `runc` step; (b) a failing `nft -f` at `metadata`; (c) a failing `apt-get`. The Interface says nothing about what the script does in these cases (stop with which message and exit code, or fall through). Please state the rule, I would choose "stop on the first failing step with exit 1 and `factory-run` never called", and add a row for each.
4. 2026-10-31 human: Answers to question 3:

   1. `<ref>` is `FACTORY_CODE_REF`, the tag or commit the code was checked out at (decision 20): `--build-arg FACTORY_IMAGE=<FACTORY_CODE_REF>`. Criterion 8 names it.
   2. The three words are S0009's `JOB_PODMAN_OPTIONS` of `factory.domain.containers`: `--runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay`. The script holds them as one shell constant, `JOB_PODMAN_OPTIONS`, and a test compares that constant's words with the Python tuple, so the two cannot drift apart. List the three words in the Interface.
   3. Yes, one criterion with your three rows. The rule: the proxy is the value of `HTTPS_PROXY` when it is set, else of `https_proxy`; the script exports it under both spellings for every later step, so the `curl` and `git` stand-ins see `https_proxy` and `HTTPS_PROXY` with that value; with neither set they see neither.
   4. Yes: rows for the image name in the `podman build -t` call with and without `FACTORY_STAGE_IMAGE`. The `/srv/factory/<instance>` default of `FACTORY_JOB_ROOT` is tested from the script's text only (the default is written there once), since a run cannot use `/srv`.
   5. Yes, as you propose: the three are absent from `factory-run`'s environment when the input had none, and present with the input's value when it had one.
   6. Yes: a row where `RUNC_VERSION` and `RUNC_SHA256` are both given and replace the URL's version and the checksum fed to `sha256sum -c`.
   7. Yes: criterion 11 also checks that no recorded stand-in argument contains `s3cret-token-text`.
   8. The rule: the script stops at the first failing step with exit 1 and `job-start: <step>: failed` on standard error (the steps with their own message keep it), and `factory-run` is never called. Rows for a failing `curl` at `runc`, a failing `nft -f` at `metadata`, and a failing `apt-get` at `packages`.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete. It names `vm/job-start.sh` (POSIX sh), the `vm/Dockerfile` change, the inputs with defaults and exit codes, the derived variables and the ordered steps. No `src/` module changes. The human's answer (journal 4) is written in: `<ref>` is `FACTORY_CODE_REF`; `JOB_PODMAN_OPTIONS` is one shell constant with the three words `--runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay` (equal to `factory.domain.containers.JOB_PODMAN_OPTIONS`, which exists); the proxy rule (`HTTPS_PROXY` else `https_proxy`, exported under both spellings); the failing-step rule (exit 1, `job-start: <step>: failed`, no `factory-run`); the default root is tested from the script's text only.
   - Criteria: 18 now, each testable by one test function. Added from journal 4: criterion 13 (proxy rows), 14 (the constant equals the Python tuple), 15 (default root from the text), 16 (failing `curl`, `nft -f`, `apt-get` rows). Extended criterion 5 (given `RUNC_VERSION` and `RUNC_SHA256` pair row), 8 (`<FACTORY_CODE_REF>`, `FACTORY_STAGE_IMAGE` with and without), 10 (`FACTORY_CONTAINER_ENV`, `FACTORY_CA_BUNDLE`, `FACTORY_IDLE_SHUTDOWN_MINUTES` untouched) and 11 (no recorded stand-in argument holds the secret). Each rule has its failing side: missing inputs, checksum mismatch, `RUNC_VERSION` without `RUNC_SHA256`, mount failure, missing ref, `--once` failing. The closing two (`make check`, `docs:`) stay last as 17 and 18.
   - Smoke test: both commands run from the repository root. `sh vm/job-start.sh` stops at `inputs` with the message and exit 2, and `grep -c` gives 2 for the two chains. Both `Expect:` lines can be checked against the output. No pytest command, so there is no `-q` problem.
   - Architecture: shell and Dockerfile under `vm/`, which is in the coder's write paths. No layer is touched. Tests go through `tests/vm_support.py` with stand-ins. The change to `tests/test_stage_image.py` carries the human's leave in the Interface.
   - Scope: within F0047's scope (S0006 line, decisions 10 to 12, 17, 18 and 20). Creating the job is out of scope and the story leaves it out. The Dockerfile pin change is feature decision 17.
