---
stage: review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 432
comments_read: [6391472234]
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-25T01:05:33.636179Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T00:32:56.414525Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T00:32:56.420497Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-25T00:33:20.767433Z'
  stage: intake
  run: 1bb6eb3e18c14e67bb69aab148994b78
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-25T00:34:37.836563Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-25T00:34:55.901903Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-25T00:35:14.685866Z'
  stage: intake
  run: 50c85af711aa4e429e3b2aa6caaf025c
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-25T00:35:35.257037Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-25T00:41:48.223076Z'
  stage: tests
  run: 6a2115083e014220b8316dcc63048cdb
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-25T00:42:08.808766Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-25T00:49:20.506850Z'
  stage: doing
  run: 16eb50c357eb423fa3c326a3c8c5bbb5
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-25T00:49:41.586225Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-25T00:52:03.955794Z'
  stage: review
  run: df9cd6c06431424fb5cc6200515c840f
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-25T00:52:24.673769Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-25T00:56:38.638334Z'
  stage: doing
  run: cfa8c5bf2f3846c595e2c08f12aaa88c
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-25T00:56:59.426326Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-25T00:58:29.319076Z'
  stage: review
  run: 413ced19b3fb4d9d92d9908cd059ccea
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-25T00:58:50.042610Z'
  stage: docs
- number: 18
  speaker: documenter
  kind: result
  at: '2026-10-25T01:00:17.496809Z'
  stage: docs
  run: d910efe72a544229a725163be24d7d86
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-25T01:00:38.170705Z'
  stage: smoke-test
- number: 20
  speaker: smoke-tester
  kind: result
  at: '2026-10-25T01:01:37.032642Z'
  stage: smoke-test
  run: c160f8f18a6b415c9dc55b95ef417f84
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-25T01:01:57.332139Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-25T01:05:13.090983Z'
  stage: doing
  run: 806457236a8440ff8b892f35831577d9
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-25T01:05:33.636179Z'
  stage: review
---

# The setup script prepares the machine and installs the service

## Description

The machine of v1.2 is a Linux VM with ZFS and rootless Podman, on which the factory runs as a systemd service under the user `factory` (`planning/v1.2-plan.md`, "The machine", "Where the factory runs"; the human's decisions 1, 3, 6 and 8). This story adds the two files that make such a machine from a fresh Ubuntu 24.04 with a spare disk, with the facts of the runbook's sections 4 and 5 (`planning/overnight/gcp-runbook-2026-10-24.md`): `vm/setup.sh`, an idempotent script run as root, which installs the packages, makes the pool on the given device and the datasets `<pool>/factory` and `<pool>/factory/<instance>` (`compression=lz4`, `atime=off`, a quota) mounted at `/srv/factory/<instance>/work`, the user `factory` with linger and the ZFS delegation `snapshot,destroy,rollback,diff,mount`, the `sudoers` fallback with its wrapper only when asked by `--sudoers`, the folders of the service (the state, the factory's own checkout, the secrets folder `0700`, the image-id file), the checkout of the factory at a given git ref with its own virtual environment (`uv sync --frozen --no-dev`, `uv` from `pip` in a tools venv), the environment file `/srv/factory/<instance>/factory.env` written from its arguments and the pins of `vm/Dockerfile`, and the systemd template unit `vm/factory.service` installed as `factory@.service` and enabled, not started; and `vm/factory.service` itself. Every step prints one line of what it did or found done. The checkout of the private repository needs the hosting token, so when the token file is not there yet the script ends at that step with a line that names the file, and the second run completes the rest (decision 4 of `feature.md`). No VM is in the suite: the script's argument faults and its root check run for real (every such run ends before the first step), everything else is pinned by its text and `sh -n`, as the entrypoint's tests do today. What stays: `image/`, the entrypoint and `compose.yml`, unchanged; F0042's settings as F0042 defines them; the GCP steps and the operator's hand steps are the guide chapter's, S0004.

## Interface

No module under `src/factory/` changes. The coder adds `vm/setup.sh` and `vm/factory.service`.

`vm/setup.sh` (POSIX `sh`; `#!/bin/sh` first, then comments, then `set -eu` as the first command):

- Options: `--device <path>` and `--repository-url <url>` are required; `--instance <name>` (default `vm`), `--pool <name>` (default `tank`), `--quota <size>` (default `30G`), `--ref <git ref>` (default `main`), `--image <tag>` (default `factory-stage:<instance>`), `--runtime claude|opencode` (default `claude`), `--sudoers` (a flag), `--help`. `--help` prints the usage to standard output and exits 0. A missing required option, an option without its value, an unknown word, or a `--runtime` other than the two prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2. The usage starts with `usage: setup.sh` and names every option. After the options, when `id -u` (the `id` found on `PATH`) is not `0`, the script prints `setup.sh: run as root` to standard error and exits 2. Nothing is made or changed before either exit.
- The steps, in this order, each one line on standard output beginning `setup: <step>: ` and saying what it did or found done; each command is run only when its result is missing, so a second run changes nothing and reports "found" (the wording of the lines is the coder's, the step names are these): `packages` (`apt-get install -y --no-install-recommends` of exactly the missing ones among `zfsutils-linux podman uidmap slirp4netns git make python3.12-venv`, after `apt-get update`); `pool` (`zpool create -o ashift=12 -O compression=lz4 -O atime=off <pool> <device>` unless `zpool list -H -o name <pool>` finds it; the device is passed as given, a disk or a file such as the local VM's `/var/lib/factory-pool.img`, and the script does not test it, so a pool that exists is found whatever `--device` names); `user` (`useradd --create-home --shell /bin/bash factory` unless `id factory`; then `/etc/subuid` and `/etc/subgid` must each hold a `factory:` line, else the script prints `setup: user: no subuid and subgid range for factory; add one with usermod --add-subuids and --add-subgids` to standard error and exits 1); `linger` (`loginctl enable-linger factory`); `datasets` (`zfs create <pool>/factory` unless it exists, `zfs set compression=lz4 atime=off <pool>/factory`, `zfs create -o mountpoint=/srv/factory/<instance>/work <pool>/factory/<instance>` unless it exists, `zfs set quota=<quota> <pool>/factory/<instance>`, the mount point owned by `factory:factory` (`chown factory:factory` or `install -d -o factory -g factory`)); `delegation` (`zfs allow -u factory snapshot,destroy,rollback,diff,mount <pool>/factory/<instance>`); `sudoers` (with `--sudoers`: `/etc/sudoers.d/factory-zfs`, mode `0440`, holding one rule, `factory ALL=(root) NOPASSWD: /usr/sbin/zfs snapshot <pool>/factory/<instance>@base, /usr/sbin/zfs destroy <pool>/factory/<instance>@base, /usr/sbin/zfs rollback -r <pool>/factory/<instance>@base, /usr/sbin/zfs diff -FH <pool>/factory/<instance>@base`, checked with `visudo -cf` (a failed check removes the file and exits 1), and the wrapper `/usr/local/bin/zfs-factory`, mode `0755`, a `sh` script whose `case` on its first word runs `rollback`, `destroy`, `snapshot` and `diff` as `exec sudo -n /usr/sbin/zfs "$@"` and every other word as `exec /usr/sbin/zfs "$@"`; without the flag the line says the fallback was not asked and neither file is touched); `folders` (`/srv/factory/<instance>` itself, which ZFS made as root when it mounted the dataset below it, then `/srv/factory/<instance>/state` and `/srv/factory/<instance>/repo`, owner `factory:factory` (`chown factory:factory` or `install -d -o factory -g factory`), mode `0755`; the script names the instance's folder through one variable, set once as `base=/srv/factory/$instance`; `/home/factory/.secrets`, owner `factory:factory`, mode `0700`); `image-id` (`/srv/factory/<instance>/image-id` written from `/proc/sys/kernel/random/uuid`, owner `factory`, mode `0644`, unless it exists non-empty); `checkout` (when `/home/factory/.secrets/hosting-token` is missing: the line `setup: checkout: waiting for /home/factory/.secrets/hosting-token; place the secrets and run this script again`, then exit 0 with no further step; else the askpass script `/srv/factory/<instance>/askpass`, owner `factory`, mode `0755`, a `sh` script that answers a first argument beginning `Username` with `x-access-token` and any other with the content of `/home/factory/.secrets/hosting-token`, and, unless `/srv/factory/<instance>/factory/.git` exists, `git clone -q --branch <ref> --config core.askPass=<askpass> <url> /srv/factory/<instance>/factory` as `factory` through `runuser -u factory --` with `GIT_ASKPASS=<askpass>` and `GIT_TERMINAL_PROMPT=0`, so that the clone itself writes `core.askPass` into the checkout as `factory` and no `git` runs as root in it (root's `git` refuses a repository another user owns: "detected dubious ownership")); `tools` (`UV_VERSION` read from the line `ARG UV_VERSION=` of the checkout's `vm/Dockerfile`; `python3 -m venv /srv/factory/<instance>/tools` unless it exists, `/srv/factory/<instance>/tools/bin/pip install uv==<that version>` unless `tools/bin/uv --version` already says it, then `/srv/factory/<instance>/tools/bin/uv sync --frozen --no-dev` in the checkout, all as `factory`; and, as root, the checkout's `image/git-credential-factory` installed as `/usr/local/bin/git-credential-factory`, mode `0755`, unless identical, because the factory's own git reaches the token only through that helper (`CREDENTIAL_HELPER` of `factory.entry.wiring`) and today only v1.1's image installs it); `environment` (the file below, written when its content differs, else found unchanged); `service` (`vm/factory.service` of the checkout installed as `/etc/systemd/system/factory@.service`, mode `0644`, unless identical; `systemctl daemon-reload`; `systemctl enable factory@<instance>` unless enabled; never `--now`, never `systemctl start`). After the last step one line `setup: done: build the stage image and start factory@<instance>; see the operator guide, "The machine"`.
- The environment file `/srv/factory/<instance>/factory.env`, mode `0644`, holds exactly these lines in this order, each `NAME=value` with no quotes and no spaces around `=`, and nothing else but one leading comment line: `FACTORY_INSTANCE=<instance>`, `FACTORY_REPOSITORY_URL=<url>`, `FACTORY_AGENT_RUNTIME=<runtime>`, `FACTORY_STAGE_ENVIRONMENT=container`, `FACTORY_DATASET=<pool>/factory/<instance>`, `FACTORY_WORKSPACE=/srv/factory/<instance>/work`, `FACTORY_STAGE_IMAGE=<image>`, `FACTORY_ZFS=zfs` (with `--sudoers`: `FACTORY_ZFS=/usr/local/bin/zfs-factory`), `FACTORY_CHECKOUT=/srv/factory/<instance>/repo`, `FACTORY_STATE=/srv/factory/<instance>/state`, `FACTORY_IMAGE_ID_FILE=/srv/factory/<instance>/image-id`, `FACTORY_CLAUDE_HOME=/srv/factory/<instance>/factory/claude`, `FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token`, `FACTORY_CLAUDE_LOGIN_FILE=/home/factory/.secrets/claude-token`, `FACTORY_API_LOGIN_FILE=/home/factory/.secrets/anthropic-api-key`, `FACTORY_CLAUDE_VERSION=<the ARG CLAUDE_CODE_VERSION default of the checkout's vm/Dockerfile>`, `FACTORY_OPENCODE_VERSION=<its ARG OPENCODE_VERSION default>`, `FACTORY_OPENCODE_MODELS=<its ENV FACTORY_OPENCODE_MODELS value>`, `PATH=/srv/factory/<instance>/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin` (`/usr/sbin` holds `zfs`, which `FACTORY_ZFS=zfs` names and the preflight runs), `XDG_RUNTIME_DIR=/run/user/<the uid of factory, from id -u factory>` (rootless Podman under a system unit finds the user's runtime folder that linger makes). No `FACTORY_AGENT_USER`, no `FACTORY_PODMAN` (its default `podman` holds), no token and no key in it.
- The script holds no download piped into a shell (`curl` or `wget` followed by `sh` or `bash` in one pipeline), writes, copies, moves or removes no file under `/home/factory/.secrets` (the secrets the operator placed stay as they are on every run; the folder's owner and mode are set on the folder alone, never with `-R`), writes the token into no file but reads it only through the askpass script, and names no `latest`.

`vm/factory.service` (a systemd template unit; `#` comment lines allowed):

- Section `[Unit]` with exactly `Description=` (naming the factory and `%i`), `After=network-online.target zfs.target`, `Wants=network-online.target`; section `[Service]` with exactly, in this order, `User=factory`, `Group=factory`, `WorkingDirectory=/srv/factory/%i`, `EnvironmentFile=/srv/factory/%i/factory.env`, `ExecStart=/srv/factory/%i/factory/.venv/bin/factory-run`, `Restart=always`, `RestartSec=15`; section `[Install]` with exactly `WantedBy=multi-user.target`. No `Environment=`, no `ExecStartPre=`, no `Type=`, no other key.

Tests (the tester writes them): `tests/test_vm_setup.py` (the runs: `sh -n`, the argument faults, the root refusal) and `tests/test_vm_setup_text.py` (the steps, their order, the sudoers and wrapper texts, the environment file's names, the absent patterns), both reading `vm/setup.sh` from the repository root as `tests/entrypoint_support.py` reads the entrypoint, and running it through `run_process` with `argv` `["sh", <path>, ...]` in `tmp_path`; `tests/test_vm_service.py` (the unit, parsed with `configparser.ConfigParser(strict=False, interpolation=None)` or read line by line). A support module `tests/vm_support.py` for the paths and the step list is the tester's choice.

## Acceptance criteria

1. `sh -n vm/setup.sh` exits 0; the file's first line is `#!/bin/sh`, and its first line that is neither blank nor a comment is `set -eu`.
2. The argument faults (rows of one parametrized test, each run with `sh vm/setup.sh <words>` in `tmp_path` as the test's own user): no words; `--device /dev/null` alone; `--repository-url https://example.invalid/r.git` alone; `--device` without a value; `--device /dev/null --repository-url https://example.invalid/r.git --bogus`; `--device /dev/null --repository-url https://example.invalid/r.git --runtime vim`: each exits 2, prints nothing to standard output, prints to standard error a first line beginning `setup.sh: ` and then a line beginning `usage: setup.sh` that holds `--device`, `--repository-url`, `--instance`, `--pool`, `--quota`, `--ref`, `--image`, `--runtime` and `--sudoers`; and `tmp_path` holds no new entry afterwards. `sh vm/setup.sh --help` exits 0 and prints the usage to standard output.
3. The root check: `sh vm/setup.sh --device /dev/null --repository-url https://example.invalid/r.git` and the same with `--instance x --pool p --quota 1G --ref v1 --image i:1 --runtime opencode --sudoers` (rows of one parametrized test) exit 2 with a stand-in `id` first on `PATH` that prints `1000` (so no run reaches the steps, whatever user the suite runs as), print exactly `setup.sh: run as root` to standard error and nothing to standard output, and `tmp_path` holds no new entry.
4. The steps and their order (read from the script's text with its comment lines dropped, here and in criteria 5 to 9; a step's text runs from the end of the line of the previous step's last `setup: <previous step>: ` text to the end of the line of its own last `setup: <step>: ` text, the first step's from the start of the file): the text holds, each at least once and the first occurrences in this order, `apt-get install -y --no-install-recommends`, `zpool create -o ashift=12 -O compression=lz4 -O atime=off`, `useradd --create-home --shell /bin/bash factory`, `loginctl enable-linger factory`, `zfs create`, `zfs set compression=lz4 atime=off`, `zfs set quota=`, `zfs allow -u factory snapshot,destroy,rollback,diff,mount`, `/etc/sudoers.d/factory-zfs`, `/home/factory/.secrets` (the folder), `image-id`, `/proc/sys/kernel/random/uuid`, `hosting-token`, `git clone -q --branch`, `ARG UV_VERSION=`, `python3 -m venv`, `uv sync --frozen --no-dev`, `/usr/local/bin/git-credential-factory`, `factory.env`, `factory@.service`, `systemctl daemon-reload`, `systemctl enable factory@`; and the thirteen step names `packages`, `pool`, `user`, `linger`, `datasets`, `delegation`, `sudoers`, `folders`, `image-id`, `checkout`, `tools`, `environment`, `service` each appear in a `setup: <step>: ` text, first occurrences in that order.
5. The package list is exactly `zfsutils-linux podman uidmap slirp4netns git make python3.12-venv` (seven words, read from the script's text); `apt-get update` comes before `apt-get install`; the text holds no `curl` or `wget` piped into `sh` or `bash`, no `[ -b ` or `test -b ` (the device is not tested), no `latest`, no `systemctl start`, no `enable --now` and no `FACTORY_AGENT_USER`; and no line that names `.secrets` holds `rm `, `mv `, `cp `, `tee `, `truncate`, ` -R `, or a `>` or `>>` followed (after spaces and quotes) by a path that holds `.secrets` (rows of one parametrized test over the forbidden forms).
6. The `sudoers` fallback (rows of one parametrized test): the text holds each of `/usr/sbin/zfs snapshot `, `/usr/sbin/zfs destroy `, `/usr/sbin/zfs rollback -r `, `/usr/sbin/zfs diff -FH ` exactly once, each followed by a word ending `@base` or, for the first three, `@base,` (the rule's separator), and holds `diff -H ` nowhere; it holds `factory ALL=(root) NOPASSWD:`, `chmod 0440`, `visudo -cf`, `/usr/local/bin/zfs-factory`, `rollback|destroy|snapshot|diff)`, `exec sudo -n /usr/sbin/zfs "$@"` and `exec /usr/sbin/zfs "$@"`; and in the `sudoers` step's text a line beginning `if ` (after its indentation) stands before the first line holding `/usr/sbin/zfs`, and one `setup: sudoers: ` text names `zfs allow` (the line for the flag not set).
7. The environment file's text (rows of one parametrized test over the names): the script's text holds each of the twenty lines' names of the Interface as `NAME=`, not preceded by a letter or `_`, exactly once, not counting the `ENV FACTORY_OPENCODE_MODELS=` the pin is read by, in the Interface's order, between the words `factory.env` and `factory@.service`; `FACTORY_STAGE_ENVIRONMENT=container` and `PATH=/srv/factory/` with `/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin` are literal; `FACTORY_ZFS=` is followed by `$` (a variable), and the `sudoers` step's text holds `=zfs` and `=/usr/local/bin/zfs-factory` (the variable's two values); the text holds `ARG CLAUDE_CODE_VERSION=`, `ARG OPENCODE_VERSION=` and `ENV FACTORY_OPENCODE_MODELS=` (the pins are read from the Dockerfile, not written into the script); and `FACTORY_PODMAN` appears nowhere. Each name's line holds its value in the text's own variable form, one row each, matched exactly and in no other form: `FACTORY_INSTANCE=$instance`, `FACTORY_REPOSITORY_URL=$repository_url`, `FACTORY_AGENT_RUNTIME=$runtime`, `FACTORY_STAGE_IMAGE=$image`, `FACTORY_DATASET=$pool/factory/$instance`; `FACTORY_WORKSPACE`, `FACTORY_CHECKOUT`, `FACTORY_STATE`, `FACTORY_IMAGE_ID_FILE` and `FACTORY_CLAUDE_HOME` each starting with `$base/` and ending in the path the Interface gives; the three secret paths `/home/factory/.secrets/hosting-token`, `/home/factory/.secrets/claude-token` and `/home/factory/.secrets/anthropic-api-key`; `XDG_RUNTIME_DIR=/run/user/$(id -u factory)`; and the three pins as the values read from the Dockerfile's `ARG` lines (the variable the script reads them into is the coder's to name).
8. The checkout step's text: `waiting for /home/factory/.secrets/hosting-token` with `run this script again` on the same line, `exit 0` after it before `git clone`; `Username` and `x-access-token` in the askpass text; `GIT_ASKPASS=` and `GIT_TERMINAL_PROMPT=0` on the clone's line or the lines before it; `--config core.askPass=` on the line of `git clone -q --branch`, and `git config` nowhere in the text; `runuser -u factory --` before `git clone` and before `uv sync`; `0700` on the line that makes `/home/factory/.secrets`; `0755` and `0644` in the `folders` and `image-id` steps.
9. The refusals, the modes and the rerun (rows of one parametrized test): the `user` step's text holds `/etc/subuid`, `/etc/subgid`, the line `setup: user: no subuid and subgid range for factory; add one with usermod --add-subuids and --add-subgids` and `exit 1`; in the `sudoers` step's text, after `visudo -cf`, `rm -f /etc/sudoers.d/factory-zfs` comes before `exit 1`, and a line naming `/usr/local/bin/zfs-factory` holds `0755`; the `tools` step's text holds `pip`, `install`, `uv==` and `uv --version`; the `checkout` step's text holds `0755` (the askpass script), and the `environment` and `service` steps' texts each hold `0644`; the text holds the guards `zpool list -H -o name`, `id factory`, `/.git` and `-s ` (the image-id file); the text holds `base=/srv/factory/$instance` exactly once, the `datasets` step's text holds `chown factory:factory` or `-o factory -g factory` (the mount point), and the `folders` step's text holds a line with `chown factory:factory` or `-o factory -g factory` on which `$base` or `"$base"` stands as a word of its own (the instance's folder, which ZFS makes as root); each of the thirteen steps' texts holds `found` (the line of a step that finds its work done); and after the last `setup: service: ` the text holds `setup: done: build the stage image and start factory@` with `see the operator guide, "The machine"` on the same line.
10. `vm/factory.service` (rows of one parametrized test over the sections): `[Unit]` has exactly the keys `Description`, `After`, `Wants` with `After=network-online.target zfs.target`, `Wants=network-online.target` and a `Description` holding `%i`; `[Service]` has exactly, in this order, `User=factory`, `Group=factory`, `WorkingDirectory=/srv/factory/%i`, `EnvironmentFile=/srv/factory/%i/factory.env`, `ExecStart=/srv/factory/%i/factory/.venv/bin/factory-run`, `Restart=always`, `RestartSec=15`; `[Install]` has exactly `WantedBy=multi-user.target`; there are exactly these three sections, and the file holds no `Environment=`, `ExecStartPre=` or `Type=`.
11. The option defaults (rows of one parametrized test, read from the script's text with its comment lines dropped): the text holds each of the assignments `instance=vm`, `pool=tank`, `quota=30G`, `ref=main` and `runtime=claude` exactly once, before the option parsing, and holds `image=factory-stage:$instance` (the default built from the instance when no `--image` is given). The variables are named exactly `instance`, `pool`, `quota`, `ref`, `runtime`, `image`, `device` and `repository_url`, beside `base=/srv/factory/$instance`.
12. `make check` stays green.
13. docs: `docs/operator-guide.md`, `## The machine` (made by S0001; this story adds two sections after `### The stage image`): `### The script`: the options with their defaults, the thirteen steps as a numbered list with what each does and what it prints, the two passes (the waiting line and the second run), that a rerun changes nothing and that the environment file is rewritten from the arguments and the Dockerfile's pins on every run (so a change goes into the arguments, not into the file), the `sudoers` fallback with the wrapper and why `diff -FH` (decision 7 of `feature.md`), that the token is read by the askpass script alone, and what the script refuses (`run as root`, the usage, the missing sub-id range); `### The service`: the template unit and its instance (`factory@vm`), `systemctl start|stop|restart|status factory@vm`, `journalctl -u factory@vm`, `factory-health --state-directory /srv/factory/vm/state` as `factory`, the environment file's variables as a table with one line each (pointing to *Configuration* for their meaning), `Restart=always` with `RestartSec=15` in place of Compose's policy, and that no health check runs by itself (the operator asks `factory-health`). `docs/project-guide/README.md`, *Shared test helpers*: the new support module, if the tester made one. `docs/decisions.md`: none (S0004 writes the entry).

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
sh -n vm/setup.sh && echo syntax-ok
(cd "$d" && sh "$OLDPWD/vm/setup.sh" >out 2>err; echo "status $?"; head -1 err | grep -c '^setup.sh: '; sed -n 2p err | grep -c '^usage: setup.sh'; wc -c < out)
(cd "$d" && sh "$OLDPWD/vm/setup.sh" --device /dev/null --repository-url https://example.invalid/r.git >out 2>err; echo "status $?"; cat err; ls | grep -vcE '^(out|err)$' || true)
```
Expect: eight lines: `syntax-ok`, `status 2`, `1`, `1`, `0`, `status 2`, `setup.sh: run as root`, `0`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
grep -v '^[[:space:]]*#' vm/setup.sh > "$d/code"
for w in 'apt-get install' 'zpool create' 'useradd' 'enable-linger' 'zfs create' 'zfs allow' 'sudoers.d/factory-zfs' '/home/factory/.secrets' 'image-id' 'git clone' 'uv sync --frozen --no-dev' 'factory.env' 'factory@.service' 'systemctl enable'; do grep -n -m1 -F -- "$w" "$d/code" | cut -d: -f1; done | awk 'NR>1 && $1<p {bad=1} {p=$1; n++} END{print (bad ? "out-of-order" : "in-order"), n}'
grep -c 'diff -FH' "$d/code"; grep -c 'diff -H ' "$d/code" || true; grep -c 'FACTORY_STAGE_ENVIRONMENT=container' "$d/code"; grep -c 'FACTORY_AGENT_USER' "$d/code" || true
```
Expect: five lines: `in-order 14`, `1`, `0`, `1`, `0`

```bash
grep -cE '^(User|Group)=factory$' vm/factory.service; grep -E '^(WorkingDirectory|EnvironmentFile|ExecStart|Restart|RestartSec|WantedBy)=' vm/factory.service
```
Expect: seven lines: `2`, `WorkingDirectory=/srv/factory/%i`, `EnvironmentFile=/srv/factory/%i/factory.env`, `ExecStart=/srv/factory/%i/factory/.venv/bin/factory-run`, `Restart=always`, `RestartSec=15`, `WantedBy=multi-user.target`

```bash
uv run pytest tests/test_vm_setup.py tests/test_vm_setup_text.py tests/test_vm_service.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: Format check passed. Two Interface rules have no criterion, so two coders could read them differently and both pass the tests:

   1. **Option defaults.** The Interface states `--instance` = `vm`, `--pool` = `tank`, `--quota` = `30G`, `--ref` = `main`, `--image` = `factory-stage:<instance>` and `--runtime` = `claude`. No criterion tests any of them. Criterion 7 pins only the names in the environment file, and criteria 2 and 3 pass explicit values. I would add a criterion, rows of one parametrized test, that reads the default assignments from the script text. For example, the text holds `instance=vm`, `pool=tank`, `quota=30G`, `ref=main` and `runtime=claude` once each, and the `--image` default is built from `$instance` as `factory-stage:`. Do you want that, or a different form such as the script's usage text naming the defaults?

   2. **Values of the environment file's lines.** Criterion 7 tests that each of the twenty names appears once, in order. It tests only two values: `FACTORY_STAGE_ENVIRONMENT=container` and the literal `PATH`. Nothing pins these values:
      - `FACTORY_DATASET=$pool/factory/$instance`
      - `FACTORY_WORKSPACE`, `FACTORY_CHECKOUT`, `FACTORY_STATE`, `FACTORY_IMAGE_ID_FILE` and `FACTORY_CLAUDE_HOME` under `/srv/factory/<instance>`
      - the three secret file paths
      - `XDG_RUNTIME_DIR=/run/user/` followed by the uid from `id -u factory`
      - `FACTORY_INSTANCE`, `FACTORY_REPOSITORY_URL`, `FACTORY_AGENT_RUNTIME` and `FACTORY_STAGE_IMAGE` taking the arguments
      - the three pins read from the Dockerfile

      A wrong path or a swapped variable would pass. I would extend criterion 7 so each name's line holds its stated value, in the text's own variable form: `$instance`, `$base`, `$(id -u factory)` and so on. Do you want that? If so, which variable names does the script have to use, or should the test accept any form that holds the stated literal parts?

   Checked and fine:
   - The Interface names concrete files.
   - The smoke test commands are runnable. The pytest line passes no `-q`, and `pyproject.toml` already sets it.
   - The scope and architecture are within `feature.md`.
4. 2026-10-25 human: Yes to both; add them to the criteria yourself, then continue.

   1. **The option defaults**: a new criterion, rows of one parametrized test reading the script's text (comment lines dropped): it holds the assignments `instance=vm`, `pool=tank`, `quota=30G`, `ref=main` and `runtime=claude` once each, before the option parsing, and the image default is built from the instance as `image=factory-stage:$instance` when no `--image` is given. The variable names are exactly `instance`, `pool`, `quota`, `ref`, `runtime`, `image`, `device` and `repository_url`, beside the Interface's `base=/srv/factory/$instance`.
   2. **The environment file's values**: criterion 7 is extended so each name's line holds its value in the text's own variable form, one row each: `FACTORY_INSTANCE=$instance`, `FACTORY_REPOSITORY_URL=$repository_url`, `FACTORY_AGENT_RUNTIME=$runtime`, `FACTORY_STAGE_IMAGE=$image`, `FACTORY_DATASET=$pool/factory/$instance`; `FACTORY_WORKSPACE`, `FACTORY_CHECKOUT`, `FACTORY_STATE`, `FACTORY_IMAGE_ID_FILE` and `FACTORY_CLAUDE_HOME` each starting with `$base/` and ending in the path the Interface gives; the three secret paths as `/home/factory/.secrets/hosting-token`, `/home/factory/.secrets/claude-token` and `/home/factory/.secrets/anthropic-api-key`; `XDG_RUNTIME_DIR=/run/user/$(id -u factory)`; the three pins as the values read from the Dockerfile's `ARG` lines (the variable the script reads them into may be named by the coder). The test matches these forms exactly; no other form.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete. It names `vm/setup.sh` and `vm/factory.service`, the options with their defaults, the thirteen steps, the environment file's twenty lines and the unit's keys. No module under `src/factory/` changes.
   - Criteria: each is testable by one test function. Every rule has a criterion for the side that passes and the side that fails: the argument faults, the root refusal, the missing sub-id range, the failed `visudo -cf` that removes the file, the missing token that ends at the checkout step, and the sudoers fallback that is not asked. The human's answer in journal entry 4 is written in. New criterion 11 pins the option defaults and the variable names. Criterion 7 now pins each environment line's value in the script's own variable form. `make check` and `docs:` stay last, as criteria 12 and 13.
   - Smoke test: the commands are runnable. The pytest line passes no `-q`, and `pyproject.toml` already sets it. Each `Expect:` line is checkable against the output. The new criterion 11 has no smoke test line, and none is needed.
   - Architecture: nothing in `src/` changes. The files sit in `vm/`, which the human's change 1 in `feature.md` adds to the coder's write paths. The tests go under `tests/`.
   - Scope: the story is within `feature.md`'s S0003 scope and touches nothing in its "Out of scope". `image/` stays unchanged. No suite test or smoke test runs `zfs`, `systemctl` or `apt-get`.

   I added criterion 11 and the extension to criterion 7 from journal entry 4, which is the human's edit carried in. The Description is unchanged because the meaning of the task did not change.
7. factory: started tests as self.
8. tester: I wrote the tests for criteria 1 to 11. They are red for the right reason: `vm/setup.sh` and `vm/factory.service` do not exist yet, so every test fails with `FileNotFoundError` on those paths. `make lint` is green. I skipped the type check, as the stage says.

   Criterion → test:
   - criterion 1: tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu
   - criterion 2: tests/test_vm_setup.py::test_an_argument_fault_prints_the_usage_and_exits_2 (the six rows) and tests/test_vm_setup.py::test_help_prints_the_usage_to_standard_output_and_exits_0
   - criterion 3: tests/test_vm_setup.py::test_a_user_other_than_root_is_refused_before_the_steps (two rows; a stand-in `id` in `tmp_path/bin` prints `1000`)
   - criterion 4: tests/test_vm_setup_text.py::test_the_commands_and_the_steps_come_in_their_order
   - criterion 5: tests/test_vm_setup_text.py::test_the_packages_are_the_seven_and_updated_before_install and tests/test_vm_setup_text.py::test_the_script_holds_no_forbidden_form (one row per forbidden form)
   - criterion 6: tests/test_vm_setup_text.py::test_the_sudoers_rule_names_each_zfs_command_once_on_base (the four `/usr/sbin/zfs …` rules) and tests/test_vm_setup_text.py::test_the_sudoers_fallback_is_written_only_when_asked (the other literals, the `if` before the files, the line for the flag not set)
   - criterion 7: tests/test_vm_setup_text.py::test_the_environment_file_holds_each_name_once_with_its_value (twenty rows: once, between `factory.env` and `factory@.service`, after the name before it, the exact value form) and tests/test_vm_setup_text.py::test_the_environment_file_reads_its_pins_and_picks_the_zfs_command (the three Dockerfile keys, no `FACTORY_PODMAN`, `=zfs` and `=/usr/local/bin/zfs-factory` in the sudoers step)
   - criterion 8: tests/test_vm_setup_text.py::test_the_checkout_waits_for_the_token_and_clones_as_factory
   - criterion 9: tests/test_vm_setup_text.py::test_the_refusals_modes_and_rerun_guards_are_in_their_steps
   - criterion 10: tests/test_vm_service.py::test_each_section_holds_exactly_its_keys (one row per section) and tests/test_vm_service.py::test_the_unit_has_three_sections_and_no_environment_pre_start_or_type
   - criterion 11: tests/test_vm_setup_text.py::test_each_default_is_assigned_once_before_the_option_parsing (five rows) and tests/test_vm_setup_text.py::test_the_options_land_in_their_named_variables (eight rows, plus `image=factory-stage:$instance`)
   - criteria 12 and 13 have no test: 12 is the checks, 13 is the docs stage's.

   Files created:
   - tests/vm_support.py: `SETUP`, `SERVICE`, `STEPS`, `REQUIRED`, `setup_code`, `step_texts`, `run_setup`, `entries`. It reuses `ROOT` and `SYSTEM_PATH` from `entrypoint_support` and `_uncommented` from `dockerfile_support`. The docs criterion names this module for *Shared test helpers*.
   - tests/test_vm_setup.py
   - tests/test_vm_setup_text.py
   - tests/test_vm_service.py

   Modules the test run could not import: none. The failures are the missing files `vm/setup.sh` and `vm/factory.service`. I changed no earlier test file.

   Choices in reading the text, which the coder should know:
   - **Package list:** read as the run of words that starts at `zfsutils-linux`, after joining `\`-continued lines. It must occur exactly once.
   - **Start of the option parsing (criterion 11):** the first `case "$1"`, `case $1` or `case ${1…`.
   - **Value forms (criterion 7):** each must be followed by a quote, a space or the end of the line. `${instance}` or a printf `%s` form fails.
   - **The three pins:** each must be `$<variable>`, and some line that assigns that variable must also hold its Dockerfile key (`ARG CLAUDE_CODE_VERSION=`, `ARG OPENCODE_VERSION=` or `ENV FACTORY_OPENCODE_MODELS=`).
   - **Step texts:** cut as the criteria say: each step ends at the end of the line of its own last `setup: <step>: ` text.

   `lint`: lint: green (0.6 s)
   `test`: ERROR tests/test_vm_setup_text.py::test_the_options_land_in_their_named_variables[repository_url] - FileNotFoundError: [Errno 2] No such file or directory: '/work/checkout/vm/setup.sh'
9. factory: started doing as self.
10. coder: I added `vm/setup.sh` and `vm/factory.service` and wrote neither elsewhere; no module under `src/factory/` changed. The 128 tests in `tests/test_vm_setup.py`, `tests/test_vm_setup_text.py` and `tests/test_vm_service.py` pass, and `make check` is green: it ends `check: green`, coverage is 99.20 %. The first `make check` run ended at `make types` with `Error 139` (mypy segfaulted, no other output). The second run was green with nothing changed, so I take it as a one-off crash of the machine's mypy rather than of this work.

    **What I built**
    - `vm/setup.sh` (POSIX `sh`, `set -eu`) has five parts in order:
      - the usage, with every option on its first line and one line per option with its default;
      - the option parsing: `need_value` refuses a missing value or one beginning with `--`, and `fault` prints `setup.sh: …` and the usage to standard error and exits 2;
      - the checks of the required options and of `--runtime`;
      - the root check;
      - the thirteen steps, each printing literal `setup: <step>: ` lines and a `found` line when its work is already done.
    - Nothing is made before the root check. The staging file (`mktemp`, removed by `trap`) is made only after it.
    - `vm/factory.service`: the template unit with exactly the keys the Interface lists.

    **Main choice: a staging file instead of text held in a variable.** Every file the script writes goes through one staging file (`stage` writes it from a here-document, `unchanged` compares it with `cmp -s`). This covers the sudoers rule, the wrapper, the askpass script and the environment file, and each is written only when it differs. I rejected holding the text in `$(cat <<EOF …)` and comparing strings, for two reasons:
    - The askpass and wrapper texts contain `case` patterns with `)` inside a command substitution, which is fragile to parse.
    - A helper that writes and reports "changed" through its exit status would run inside an `if`, where `set -e` is off, so a failed `install` would be reported as "found".

    **Other choices**
    - `as_factory` (`runuser -u factory -- env HOME=/home/factory`): runuser keeps root's `HOME`, so git and uv would otherwise read and write `/root`.
    - The user step ends with an extra line, `setup: user: found the subuid and subgid ranges of factory`. Without it the step's text would end on the refusal line, before its `exit 1`, and the test of criterion 9 could not see the `exit 1`.
    - The tools step calls `$tools/bin/uv --version` unquoted, because criterion 9 wants the literal `uv --version`. That is safe only while an instance name holds no spaces.

    **Refactor:** I read the diff once and found nothing to change.

    **Noticed, not touched**
    - The delegation step treats the delegation as found when `zfs allow <dataset>` prints `user factory diff,destroy,mount,rollback,snapshot`. I assumed OpenZFS lists the permissions sorted and comma-separated. If the real output differs, the step runs `zfs allow` again on every run, which does no harm.
    - The steps `datasets` (`zfs set`, the `chown` of the mount point), `tools` (`uv sync`) and `service` (`systemctl daemon-reload`) run some commands on every run. They are idempotent and the Interface lists them without a guard.
    - The permission check refused my one command that ran the smoke test's first two blocks, so I did not run the smoke test by hand. The suite runs the same argument and root checks for real.
    - No skill applied.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
11. factory: started review as self.
12. reviewer: Review, round 0. I read the work item, `vm/setup.sh`, `vm/factory.service`, `tests/vm_support.py`, `tests/test_vm_setup.py`, `tests/test_vm_setup_text.py` and `tests/test_vm_service.py`. I did not run `make check`.

    Groups 1 to 3 pass:
    - **Group 1:** every criterion from 1 to 11 has a test that checks what the criterion says. The Interface's refusals are tested on their failing side: the argument faults, `--runtime vim`, the root check, the missing sub-id range, the failed `visudo -cf` and the missing token. The coder's entry 10 reports `make check` green.
    - **Group 2:** nothing under `src/` changed, and `vm/` sits outside the layers.
    - **Group 3:** the script holds no secrets, and the token is read only by the askpass script.

    The review stops at group 4, on the script's rerun reports:

    1. `vm/setup.sh:170`: the delegation guard never matches, so every rerun runs `zfs allow` again and reports "delegated" instead of "found". The Interface says a second run changes nothing and reports "found". The guard greps for `user factory diff,destroy,mount,rollback,snapshot`, which is the order of neither the Interface nor the alphabet. OpenZFS lists permissions sorted by name, which is `destroy,diff,mount,rollback,snapshot`, and that also matches the coder's own stated assumption ("sorted") in entry 10. Fix: match the sorted list, or check each of the five permissions on the `user factory` line on its own.
    2. `vm/setup.sh:144,159-168,276-277,326-332`: steps print several lines each, and some lines say neither "found" nor what changed. The Interface asks for "each one line on standard output", and the Description says "every step prints one line of what it did or found done".
       - `user` prints two lines, `datasets` up to three, `tools` four, and `folders`, `checkout` and `service` two each.
       - `setup: datasets: … has the quota …` (line 168) and `setup: tools: synced …` (line 277) print on every run, so a clean rerun still reports something other than "found" for those steps.
       - Fix: gather each step's outcome and print one `setup: <step>: ` line at the step's end, which says "found" when nothing was done. For `user`, run the sub-id check before that line so the step's text still ends after its `exit 1` (criterion 9).

    Earlier tests: none. Every test file in the diff is new (status `A`).
13. factory: started doing as self.
14. coder: Round 1. I fixed the reviewer's two findings in `vm/setup.sh` and did nothing beyond them. `vm/factory.service` and the tests are unchanged. `make check` is green: it ends `check: green`, coverage 99.20 %. The 128 tests in `tests/test_vm_setup.py`, `tests/test_vm_setup_text.py` and `tests/test_vm_service.py` pass. `sh -n` passes.

    **Finding 1, the delegation guard.** A new helper, `delegated`, collects the permissions on every `user factory` line of `zfs allow <dataset>`. It then checks each of the five permissions on its own. The guard now works whatever order OpenZFS lists them in. I ran the helper against a sample `zfs allow` output in `$TMPDIR`: it finds the full set and refuses a partial one.

    **Finding 2, one line per step.** Each step now starts with `changes=`. Every action it takes calls `changed "<what it did>"`. The step ends with exactly one `echo "setup: <step>: $(said "found …")"`, which prints what changed (joined with `; `) or, if nothing changed, the found text.
    - **`user`:** the sub-id check runs before that line, so the step's text still ends after its `exit 1`.
    - **`datasets`:** these commands now run only when needed:
      - `zfs set compression=lz4 atime=off`, when `zfs get -H -o value compression,atime` does not print `lz4 off`;
      - `zfs set quota=`, when `zfs get -H -o value quota` differs from `--quota`;
      - `chown` of the mount point, when `stat` does not show `factory:factory`.
    - **`sudoers`:** the `if` on the flag stays first. With the flag, the step prints one line. Without it, it prints the line "not asked; … zfs allow …".
    - **`tools`:** `uv sync --frozen --no-dev` still runs on every run, but it no longer counts as a change. A comment says why: it changes nothing when the environment already matches the lockfile.
    - **`service`:** the same holds for `systemctl daemon-reload`. It still runs on every run, so a reload that failed after the unit was installed is redone on the next run.

    **Main choice and the alternative I rejected.** I gather each step's changes and print them once at the end. I rejected keeping one guard per line and moving the "found" lines to standard error, because the Interface says the step's line goes to standard output.

    **Refactor.** I read the diff once and found nothing to change.

    **Noticed, not touched**
    - `zfs get quota` may print a size in a different form from the one given (for example `30720M` for `30G`). If so, the quota is set again and reported as changed on every run, which does no harm.
    - `uv sync` and `daemon-reload` run on every rerun, as above. Whether a rerun that runs them still counts as "changes nothing" is the reviewer's call.
    - No skill applied.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
15. factory: started review as self.
16. reviewer: Review, round 1. I read the work item, the diff (`vm/setup.sh`, `vm/factory.service`, `tests/vm_support.py`, `tests/test_vm_setup.py`, `tests/test_vm_setup_text.py`, `tests/test_vm_service.py`) and the pins in `vm/Dockerfile`. I did not run `make check`. Entry 14 reports it green.

    no findings

    What I checked:
    - **Group 1, criteria 1 to 11:** each has a test that checks what the criterion says. Every rule the Interface states is tested on its failing side:
      - the six argument faults, including `--device` given without a value and `--runtime vim`;
      - the root refusal, through a stand-in `id`;
      - the missing sub-id range;
      - the failed `visudo -cf`, which removes the file;
      - the missing token, which ends at the checkout step;
      - the line printed when `--sudoers` is not set.
      `opencode` is accepted on the root-check row, which covers the accepted side of `--runtime`. The root side of the root check cannot run without a VM, as the Description says.
    - **Group 2:** nothing under `src/` changed, and `vm/` is outside the layers.
    - **Group 3:** the script holds no secret. Only the askpass script reads the token. No suppression marker was added, no download is piped into a shell, and nothing is written under `.secrets` except the folder's own mode.
    - **Round-0 finding 1 (`vm/setup.sh:125-133`):** fixed. `delegated` now checks each of the five permissions on the `user factory` lines, whatever order they are listed in.
    - **Round-0 finding 2:** fixed. Each step now prints exactly one `setup: <step>: ` line on standard output: what it changed, joined with `; `, or what it found. The user step's sub-id check comes before its line (`vm/setup.sh:163-167`), so criterion 9 still sees the `exit 1`. The datasets step's `zfs set` calls and its `chown` now run only when needed (`vm/setup.sh:181-196`). `uv sync` and `systemctl daemon-reload` still run on every run, but neither counts as a change. The Interface lists both without a guard, so that is acceptable.
    - **Group 5:** the journal states the main choice (one staging file plus `cmp -s`) and the alternative it rejected. The Description's "every step prints one line" now matches the code. The docs criterion still covers what the reader must know.

    Earlier tests: none. Every test file in the diff is new (status `A`).

    Notes:
    - `tests/test_vm_setup_text.py:413-415`: `test_the_options_land_in_their_named_variables` repeats the `image=factory-stage:$instance` assertion in all eight rows; it would fit better as a row or a test of its own. Each row also checks only that `$<variable>` is read somewhere, not that its option assigns it.
17. factory: started docs as self.
18. documenter: Docs round 1. I wrote the two sections the docs criterion asks for and found no findings: the code matches the Interface and the criteria. I changed only documents, so I did not run `make check`; the factory's checks decide. I did not run `vm/setup.sh` (no VM here), and the examples in the new sections are commands for the VM, so none of them was run.

    Files changed:
    - `docs/operator-guide.md`, `## The machine`: two new sections after `### The stage image`.
      - `### The script` holds the options with their defaults, the thirteen steps as a numbered list, and the one line each step prints. Under it are `#### The two passes`, `#### The environment file` and `#### The sudoers fallback`.
        - Two passes: the waiting line, then the second run.
        - Environment file: rewritten from the arguments and the Dockerfile's pins on every run, so a change goes into the arguments.
        - `sudoers` fallback: the rule, the wrapper, and why `diff -FH`. The unit and `diff -FH` come from the story and the script, since I may not read `feature.md`, so decision 7's own wording was not read. Please check that "the factory runs `zfs diff` with those flags and sudoers matches the whole argument list" is its reason.
        - The text also covers the token read only through the askpass script, and the refusals (usage, `run as root`, missing sub-id range, `visudo` refusal).
      - `### The service` covers the template unit and `factory@vm`, `systemctl` and `journalctl`, `factory-health` as `factory`, the environment file's variables as a table, `Restart=always` with `RestartSec=15` in place of Compose's policy, and that no health check runs by itself.
      - Also in this file, one sentence in `### The stage image`: "How `vm/setup.sh` makes the file is not described here yet" now says the script writes a fresh uuid when the image-id file is missing or empty.
    - `docs/project-guide/README.md`, *Shared test helpers*: one line for `tests/vm_support.py`, placed before `watch_support.py`.

    Cross-read and found current: `docs/operator-guide.md` *Configuration* (the variables the table points to; the defaults there are Compose's, and the new table states the VM's values), the hosting-service token section, and `vm/Dockerfile`'s pins as the stage image section describes them. `docs/decisions.md`: none, as the criterion says (S0004 writes the entry).

    Stale text I noticed and did not touch:
    - *Configuration* rows for `FACTORY_CLAUDE_LOGIN_FILE`, `FACTORY_API_LOGIN_FILE`, `FACTORY_TOKEN_FILE` and `FACTORY_IMAGE_ID_FILE` say "the image sets it to ..." with Compose paths. They are true of the long-lived container and are not wrong yet, but on the VM the environment file sets them. They are for the story that removes `image/` (F0044).
    - Reviewer note, not mine to fix: `tests/test_vm_setup_text.py:413-415` repeats the `image=factory-stage:$instance` assertion in every row.

    `check`: check: green (not run again: passed on tree 833d2a57ba51 at 2026-10-25T00:55:18Z)
    `secrets`: secrets: green (2.4 s)
    `documents`: documents ok
19. factory: started smoke-test as self.
20. smoke-tester: Smoke test, round 1. I ran the four blocks of `## Smoke test` from the repository root, in order, as the agent's user (uid 1001, not root, so the root check ends the script before its first step). Three met their `Expect:` line and one did not. I fixed nothing.

    One process note: on the first try I wrapped block 2 in `bash -c '…'`, and the tool's safety check refused it because of the `rm -rf` in the trap. I then ran the block's text directly, exactly as written. Block 1 had run the same way through `bash -c` without trouble.

    Command 1 (syntax, argument fault, root check): met.
    ```
    syntax-ok
    status 2
    1
    1
    0
    status 2
    setup.sh: run as root
    0
    ```

    Command 2 (step order and texts): **not met**. Expected `in-order 14`, `1`, `0`, `1`, `0`.
    ```
    out-of-order 14
    1
    0
    1
    0
    ```
    I looked up the first line of each word in the script with comment lines dropped: `apt-get install` 135, `zpool create` 142, `useradd` 149, `enable-linger` 160, `zfs create` 167, **`zfs allow` 116**, `sudoers.d/factory-zfs` 202, `/home/factory/.secrets` 234, `image-id` 241, `git clone` 265, `uv sync --frozen --no-dev` 281, `factory.env` 289, `factory@.service` 322, `systemctl enable` 328. Line 116 is inside the helper `delegated()`, which is defined before the steps: `permissions=$(zfs allow "$dataset" | sed -n 's/^[[:space:]]*user factory //p' | tr '\n' ',')`. The delegation command itself, `zfs allow -u factory snapshot,destroy,rollback,diff,mount "$dataset"`, is at line 190. That is between the `datasets` line (186) and the `sudoers` step (202), where it belongs.

    Command 3 (unit file): met.
    ```
    2
    WorkingDirectory=/srv/factory/%i
    EnvironmentFile=/srv/factory/%i/factory.env
    ExecStart=/srv/factory/%i/factory/.venv/bin/factory-run
    Restart=always
    RestartSec=15
    WantedBy=multi-user.target
    ```

    Command 4 (the three test modules): met.
    ```
    1
    ```

    Acceptance criteria: the smoke test contradicts none of them. Criterion 4 asks for the full text `zfs allow -u factory snapshot,destroy,rollback,diff,mount`, and its first occurrence (line 190) is in order. The three test modules pass.

    Findings:
    1. Smoke test command 2 (the order loop over the fourteen words). Expected `in-order 14`; observed `out-of-order 14`. The read-only `zfs allow "$dataset"` in the helper `delegated()` (code line 116) comes before `zfs create` (line 167), so the first `zfs allow` is out of order. No criterion is contradicted: the delegation command itself is in order, and criterion 4 names the full `zfs allow -u factory …` text. There are two fixes, and the coder chooses:
       - Change the script so that no `zfs allow` comes before the `datasets` step. For example, define or inline the check of the current permissions inside the `delegation` step.
       - Ask the human (R8) to change the smoke test's word to `zfs allow -u`. `## Smoke test` is the human's, so no stage may edit it without that answer.
21. factory: started doing as self.
22. coder: Round 2. This round fixes the smoke tester's one finding in entry 20, and nothing else. The only file changed is `vm/setup.sh`. `vm/factory.service` and the tests are unchanged.

    **What I changed.** I moved the `delegated()` helper in `vm/setup.sh`. It used to sit with the other helpers, before the steps. It now sits right after the `datasets` step's line and right before the `delegation` step that calls it. A second line on its comment says why it sits there: so the script's text keeps the order of its steps. Its body is the same as before. With comment lines dropped, the first `zfs allow` in the script now falls between `zfs create` and `sudoers.d/factory-zfs`.

    **Main choice and the alternative I rejected.** I moved the helper. I rejected asking the human to change the smoke test's word to `zfs allow -u`. The script can meet the smoke test as written, so there is nothing to ask. I also rejected inlining the permission check into the `delegation` step: that would need a flag variable in place of the helper's `return 1`, and it reads worse.

    **Verified**
    - I ran smoke test command 2 exactly as written. It printed `in-order 14`, `1`, `0`, `1`, `0`, which meets its `Expect:` line.
    - `sh -n vm/setup.sh` passes.
    - `make check` ends `check: green`, with coverage at 99.20 %.

    **Refactor.** I read the diff once. It only moves the helper, and I found nothing else to change.

    **Noticed, not touched.** The other helpers still sit before the first step, so `delegated` is now the only helper defined between steps. That is on purpose, as above. I did not add the same rule for the other helpers, because none of them contains one of the smoke test's step words. No skill applied.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
23. factory: started review as self.
