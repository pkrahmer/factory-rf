# The VM and its stage image

A topic of the [operator guide](README.md).

## The machine

The machine of v1.2 runs every stage in containers on a dataset. This chapter takes a fresh Ubuntu 24.04 VM to a running instance, and says what the machine is, what it costs and where to look when it misbehaves.

### What it is

One host, one dataset, one throwaway container for each step of a stage.

- **The host** is a Linux VM. The factory runs on it as a systemd service, `factory@<instance>`, under the user `factory`. The hosting token is on the host and nowhere else: the host alone fetches and pushes.
- **The dataset** is the ZFS dataset `<pool>/factory/<instance>`, mounted at `/srv/factory/<instance>/work` on the host and at `/work` in every container. It holds the checkout and the agent's home. Its one snapshot is the base, `@base`, moved forward at every stage's start.
- **The container** is the stage image (see *The stage image*), started for one step, with `--rm`, `--userns=keep-id` and `--timeout` set to the step's time limit. It mounts the dataset and is thrown away.

There is one user, `factory`, and no second one. `factory` has no `sudo` right but the page-cache helper, the four `zfs` commands of the optional `--sudoers` fallback and, with the option `--idle-shutdown`, `/usr/bin/systemctl poweroff` (see *The script*). The steps that need root (the script, `systemctl`, the install of the secrets) run from your own account with `sudo`.

By default one repository URL serves both the factory's own code and the project. `--repository-url` is then the clone of `/srv/factory/<instance>/factory` and the value of `FACTORY_REPOSITORY_URL`, so an instance builds the repository it runs from. With `--code-url` the two are apart: the clone of `/srv/factory/<instance>/factory` comes from `--code-url`, and `--repository-url` stays the project and the value of `FACTORY_REPOSITORY_URL` (see *The code and the project apart*).

The layout of `/srv/factory/<instance>`:

| Path | Holds |
|---|---|
| `work` | the dataset's mount point |
| `repo` | the factory's own clone of the project, where it fetches, claims and pushes |
| `state` | the factory log, `health.json` and the records |
| `factory` | the factory's code, cloned at `--code-ref`, with its `.venv` |
| `tools` | a virtual environment holding `uv` |
| `factory.env` | the service's environment file, written by the script |
| `factory.local.env` | your own environment file, optional; the script never writes it |
| `image-id` | the identity of the stage image |
| `askpass` | the script git asks for the hosting token |

### The job profile

A managed sandbox such as a Cloud Run job cannot start the factory's containers the way the VM does. Set `FACTORY_CONTAINER_PROFILE=job` there; the default, `rootless`, is what the VM uses and is unchanged.

What the sandbox lacks, measured on 2026-10-31 with Podman 5.4:

- Rootless Podman is impossible: the job's root has `NoNewPrivs`, so `newuidmap` cannot map a user namespace.
- The cgroup layout is hybrid. `crun` and Podman 6 refuse it; `runc` accepts it.
- The root file system is an overlay, and Podman's overlay storage cannot sit on top of it.
- No bridge network reaches the outside.
- Podman copies the job's proxy variables into every container.

The profile therefore puts three global options in front of every `podman` command, `launch`, `version` and `image exists` alike, and swaps the isolation words of `run`:

| Word | Why |
| --- | --- |
| `--runtime=runc` | `crun` refuses the hybrid cgroups |
| `--cgroup-manager=cgroupfs` | the cgroup manager measured to work with `runc` in the job |
| `--storage-driver=overlay` | Podman uses the kernel's native overlay and refuses to start on an unsuitable storage root instead of falling back to a slower driver |
| `--network=host` | a bridge reaches nothing; the container shares the job's network |
| `--http-proxy=false` | the job's proxy variables are not copied into the container (name the ones you want in `FACTORY_CONTAINER_ENV`) |
| no `--userns=keep-id` | rootless is impossible here |

Podman's storage root must be on a filesystem the kernel's overlay accepts as its upper layer. In a job, whose root file system is itself an overlay, that is a tmpfs (the start script mounts one at Podman's storage root). The factory names no mount program: a userspace overlay (`fuse-overlayfs`) passes every file read from an image through a daemon, and measured on 2026-10-31 (`planning/cloud-sandbox/`, P15 and P16) `make test` took 601 s with it in a job of eight CPUs against 182 s with the native overlay on a tmpfs, and the image build 199 s against 107 s. A tmpfs is memory: the image layers and the containers' writes then count against the job's memory, so size the job for them.

The container runs as the job's root with every capability dropped (`--cap-drop=all`). `--security-opt=no-new-privileges`, `--pids-limit`, `--memory`, `--timeout` and the mounts are those of `rootless`, and a container ended by `--timeout` still exits with status 255, read as the time limit as before. Files a container writes to `/work` belong to root, which is the job's own user.

### The metadata server in a job

In a Cloud Run job a container shares the job's network (`--network=host`), and the metadata server at `169.254.169.254` answers any process there with the job's service-account token (measured on 2026-10-31, `planning/cloud-sandbox/`: reachable from host-network and bridge containers, by address and by name). An agent that holds that token acts as the job's account, so no container may reach the server. (The VM is different: it has no service account, see *The metadata server* below.)

The block is a firewall rule on the job's side, installed before the factory starts (the start script does it): reject TCP port 80 to that address. DNS, the proxy and everything the factory needs keep working. As an `nft` file, loaded with `nft -f <file>`:

```
table inet factory_block {
    chain blockout {
        type filter hook output priority 0; policy accept;
        ip daddr 169.254.169.254 tcp dport 80 reject
    }
    chain blockfwd {
        type filter hook forward priority 0; policy accept;
        ip daddr 169.254.169.254 tcp dport 80 reject
    }
}
```

Do not call a chain `fwd`: `nft` reads it as a reserved word and refuses the file. The names above are free of it.

With the profile `job` the preflight proves that the rule is in force. Its item `metadata-block` runs one container, right after `stage-image`, that asks the server for the instance id with `curl -sS -m 5 -o /dev/null -w %{http_code} http://169.254.169.254/computeMetadata/v1/instance/id`, with no mounts and an empty environment, within 30 seconds. It reads the last non-blank line of the output:

| The probe | The item |
| --- | --- |
| prints `000` (curl could not connect, whatever its exit status) | passes, detail `refused` |
| ends past its limit, whatever it printed (checked first) | `the metadata probe did not end within its limit` |
| prints three other digits, such as `200` | `a container reached the metadata server (HTTP <code>); reject tcp port 80 to 169.254.169.254 in the job's firewall` |
| prints nothing, or a line that is not three digits (no `curl` in the image gives exit status 127) | `the metadata probe could not tell (exit <status>): <the last line or "no output">` |
| cannot be started | `cannot run the metadata probe: <error>` |

A failed item stops the machine like any failed preflight item (`preflight_failed`, scope `machine`). If the container reached the server, load the rule in the job's network namespace and restart. If the probe could not tell, run the command by hand in the stage image and fix what it shows (`curl` missing from the image, for instance). The item is not run with the profile `rootless`.

### Without ZFS

A sandbox that has no ZFS, such as a Cloud Run job, keeps the base as a plain copy. Set `FACTORY_SNAPSHOTS=copy` and `FACTORY_SNAPSHOT_BASE` to an absolute directory outside the workspace, the checkout and the state directory. `FACTORY_DATASET` and `FACTORY_ZFS` are then not read.

Make the base directory once, empty; the first stage fills it:

```bash
mkdir -p /srv/factory/vm/base
```

Every stage start then does what ZFS does, with copies: `reset` empties the workspace and copies the base into it, `advance` replaces the base with a copy of the workspace, and the list of changes compares the two trees file by file (mode, bytes and link target; bytes in chunks of at most 1 MiB, so a large file is never held whole).

The cost: a reset takes about 1.6 s per GiB, measured on a tree of 20000 files, and the comparison is slower than the 0.2 s that `rsync` measured. In a memory-backed sandbox the workspace and the base are both in memory, so the tree is held twice. A later version may use `rsync`.

The preflight has the item `snapshots` in place of `zfs` and `dataset` (see *The preflight's items*). The default, `zfs`, is unchanged.

### The stage image

Every container of a v1.2 stage (the sync, the agent, the checks) starts from one image that holds the tools and nothing of the factory. `vm/Dockerfile` builds it.

It holds:

- the pinned base image, and Debian's `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils`, at the versions the base image's Debian release ships;
- `uv` and one agent runtime, Claude Code or opencode, at exact versions, with the runtimes' environment: `DISABLE_AUTOUPDATER`, `UV_LINK_MODE`, `PYTHONDONTWRITEBYTECODE`, the two version records `FACTORY_CLAUDE_VERSION` and `FACTORY_OPENCODE_VERSION`, and the opencode model ids `FACTORY_OPENCODE_MODELS`;
- the agent files (`claude/agents` and `claude/settings.json`) at `/etc/factory/claude`, read-only.

It holds no user of its own and no `sudo`, no copy of the factory's source or its `uv sync`, no image-id file and no login or token path: the container runs as the caller's user (`--userns=keep-id`) and mounts the dataset.

The image only carries the agent files. The sync container copies them into the dataset's `/work/home/.claude` before the base moves (F0042).

Build it on the VM as the user `factory`, from a checkout:

```bash
podman build -f vm/Dockerfile --build-arg AGENT_RUNTIME=<claude|opencode> -t <FACTORY_STAGE_IMAGE> <the checkout>
```

`AGENT_RUNTIME` has no default. The image holds only that runtime, so it must be the instance's `FACTORY_AGENT_RUNTIME` (the preflight's `agent-runtime-version` fails on an image built for the other one). A build without it, with an empty value or with any other value, fails at once with a message that names `AGENT_RUNTIME`, `claude` and `opencode`. `vm/job-start.sh` passes `FACTORY_AGENT_RUNTIME` itself. After a change of runtime, rebuild the image and renew the file `FACTORY_IMAGE_ID_FILE` names, so that the instance gets a new `image-id`.

`--build-arg FACTORY_IMAGE=<ref>` sets the label `factory.image`; it defaults to `unlabelled`. The label is not the identity of the image. The settings read the identity from the file `FACTORY_IMAGE_ID_FILE` names, and you renew that file after every build. `vm/setup.sh` makes the file with a fresh uuid when it is missing or empty (see *The script*). Nothing in `make check` builds the image.

`vm/Dockerfile` installs six Debian packages by name alone: `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils`. Debian's mirror keeps only a package's current version, so an exact version stops building at the next point release, and a job rebuilds the image at every start. The base image's digest fixes the Debian release instead, and within one stable release Debian ships only security and serious fixes. Everything that shapes a result is still pinned: the base image is named with its digest, and `uv`, Node, Claude Code and opencode have exact versions. A pin is changed in `vm/Dockerfile` alone and checked with `uv run pytest tests/vm/test_stage_image.py`, which reports any reference that floats (a `FROM` without a digest, `latest`, a download piped into a shell, an `apt-get install` of anything but those six names) and checks that each pin has its form.

A VM's next rebuild takes the current packages of the same release.

The agent runtime is installed by a Node of its own, in a first build stage. That stage downloads Node 22 from nodejs.org, pinned by `NODE_VERSION` and `NODE_SHA256`, checks the archive with `sha256sum -c` before it unpacks it into `/opt/factory/node`, and installs the one runtime `AGENT_RUNTIME` names with that Node's npm. The final stage copies from it only that runtime's native executable, to `/opt/factory/bin/<runtime>`; `/usr/local/bin/<runtime>` execs it and passes its arguments on. The final stage therefore holds no Node, no npm, no npm cache, no other runtime and no opencode `baseline` executable, and it clears apt's lists, debconf's cache, the install logs and `/tmp`. The image has no command for the other runtime, and no `node` or `npm` for projects: a project that needs one installs its own, and that cannot change the runtimes. To change the Node pin, set both `ARG`s in `vm/Dockerfile`: `NODE_VERSION` to a `22.<n>.<n>` release and `NODE_SHA256` to the SHA-256 that nodejs.org's `SHASUMS256.txt` lists for `node-v<NODE_VERSION>-linux-x64.tar.xz` (64 lowercase hex digits). A wrong checksum fails the build.

#### Update the pins

The Debian packages carry no version, so a security or point update needs no edit. Moving to a new Debian release is a deliberate change of the base image's digest. Edit the line in `vm/Dockerfile`, then run the test:

- Base image: `podman pull <image>`, then take the digest from `podman inspect --format '{{index .RepoDigests 0}}'` and put it after `@sha256:` in the `BASE_IMAGE` default.
- `uv`: the `UV_VERSION` default. Node: `NODE_VERSION` and `NODE_SHA256` together (see above). Claude Code: the `CLAUDE_CODE_VERSION` default (three numbers; now `2.1.318`). Claude Code is installed from its npm package, `@anthropic-ai/claude-code`, with its auto-update off (`DISABLE_AUTOUPDATER=1`); the version is in the environment as `FACTORY_CLAUDE_VERSION`, so the preflight can read it.
- opencode: the `OPENCODE_VERSION` default (now `1.19.5`) and the `FACTORY_OPENCODE_MODELS` value. Check the model ids with `opencode models anthropic`.

After a change, rebuild the image and renew its id (see "The rebuild after a merge"); `vm/setup.sh` carries the pins into the environment file.

### The project's stage file

A project can add tools to the stage image (a compiler, a JDK, a browser) without changing the image for every project. It commits the file `factory/stage.Containerfile` to `main`. Every container of the instance (the sync, the agent and the checks) then runs in the image that file builds on top of the stage image.

Only `main` counts. `factory-run` fetches when it starts, reads the file from `origin/main`, and builds it before the preflight. A file on a branch has no effect. Without the file, every container runs in the base image, `FACTORY_STAGE_IMAGE`, under the identity of `FACTORY_IMAGE_ID_FILE`, and takes the `PATH` that the base image configures (`/usr/local/bin:/usr/bin:/bin` only when it configures none).

#### A change on `main` takes effect before the next stage

No restart is needed. Before every tick, after the fetch, the factory compares the stage file on `origin/main` with the one it last handled. The same text, or no file again, builds nothing and logs nothing; a new commit that does not touch the file counts as the same.

- A file that was added or changed is built as at the start. The stages after it run in the new image, under its new identity and its `PATH`, so the preflight and the reuse of passed checks start afresh. The previous project image is removed once the new one is tagged, so the machine keeps one project image.
- A file that was removed returns the instance to the base image and the base's identity.
- A stage that is running is never interrupted. If `main` moves while it runs, its remaining containers keep the image it started with, and the change takes effect before the next stage.

Each change writes one line to the factory log, and an unchanged file writes none. `<commit>` is the first 12 hex digits of `origin/main`:

| Line | When |
|---|---|
| `stage image: built <identity> at <commit> in <s> s, base <GB> GB, layer <GB> GB, <n> warnings` | a build passed (also the one at the start) |
| `stage image: base <GB> GB` | once, at the factory's start, for an instance without a stage file |
| `stage image: back to the base at <commit>` | the file was removed while a project image was in use |
| `stage image: failed at <commit>` | the file broke the rule or did not build |

The sizes are in GB of 10^9 bytes with two decimals (1 580 000 000 bytes give `1.58`). A size that cannot be read is written `unknown` (`base unknown`, `layer unknown`); a project image that is smaller than its base also has `layer unknown`. The warnings are the lines of the build's output that hold `WARN` or `warning`, in any case, except apt's `update-alternatives: warning:` lines, which a slim base prints for every manual page it lacks. A count above zero is worth reading in the build output: npm's `EBADENGINE` is one. An image that is reused with no build (the factory adopts it) gives the same two sizes to the cost records, with no log line of a build.

#### The rule

The file must be a layer on the base and nothing else:

- Before its one `FROM`, it holds only blank lines, comments and the line `ARG FACTORY_BASE`.
- It holds exactly one `FROM` (in any case), and that is `FROM ${FACTORY_BASE}` or `FROM $FACTORY_BASE`, with nothing after the name: no `AS`, no `--platform`.
- It is at most 64 KiB, measured on the UTF-8 encoding of the text as the factory reads it.
- It holds no U+FFFD. The factory decodes the file with replacement, so a file with bytes that are not UTF-8 reads as one with U+FFFD; both are refused with one reason that names both.

A file that breaks a rule is refused with the rule's reason, and nothing is built. This file satisfies the rule and adds `build-essential` and `cmake`:

```dockerfile
ARG FACTORY_BASE
FROM ${FACTORY_BASE}
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake && rm -rf /var/lib/apt/lists/*
```

#### How it is built

The factory builds the file with `podman build --build-arg FACTORY_BASE=<the base image> --network=host` and an empty build context, tags the result `<FACTORY_STAGE_IMAGE>-project` (for `factory-stage:vm`, `factory-stage:vm-project`), and then removes the images the build left without a tag. A build may take 30 minutes; after that it fails.

Two things follow for the project. The build has the network, so it can download. It has no file of the repository, so a `COPY` finds nothing, and the layer is only as repeatable as its commands: pin the versions and check the checksums of what it downloads, as `vm/Dockerfile` does. Debian packages installed by name take the version the release ships at the time of the build.

The layer must not break the stage image's tools. The runtimes live under `/opt/factory` and the image has no `node` or `npm` on the `PATH` for projects, so a project that installs its own Node does not change the runtimes.

#### The `PATH` and the identity

Every container takes the `PATH` that the image in use sets, as `podman image inspect` reads it from the image's configuration, and `/usr/local/bin:/usr/bin:/bin` when the image sets none. The sync and the checks get that `PATH`; the agent gets the folder of the factory's console scripts first and then the same `PATH`. So an `ENV PATH=/opt/jdk/bin:$PATH` in the stage file puts the JDK on the `PATH` of `make check` and of the agent. If the factory cannot read the image's configuration, it uses the default `PATH`.

The instance's image identity becomes the base's identity, a `+`, and the first 12 hex digits of the SHA-256 of the file, for example `<base identity>+20733148ba61`. It is what the preflight's stamp and the reuse of a passed check key on, so a changed file makes the preflight run its machine items again, the agent-run probe included, and confirms that the layer left the agent runtime working. It is also the image on the cost records (see "The image on the cost records"). The project image itself shows in `podman images` under the tag above.

#### The stop `stage_image_failed`

A file that breaks the rule, or does not build, raises the machine stop `stage_image_failed` (see "The stops" in [stops.md](stops.md)). Its detail is the rule's reason, or `the stage file did not build in <s> s:` followed by the last 20 lines of the build's output; a build that reaches its time limit gives `the stage file did not build in <s> s:` followed by podman's message that the build did not end within its limit, and no build output. While the stop stands the factory starts no stage, and it does not fall back to the base image. `factory-health` shows the stop; `factory-watch` shows no stop of any reason.

The detail starts with `at <commit>: `, the first 12 hex digits of the `origin/main` that was tried. The image in use stays the one before the failed build.

What to do: read the detail and fix `factory/stage.Containerfile` on `main`. A failed build waits for a new `main`: the same file again is not built again, so a commit that leaves the file as it is does not end the stop. The next `main` with another file ends the stop and the file is built; a `main` without the file ends it and returns to the base. A restart of `factory-run` builds the same file again: it ends the stop when that build passes (after a network fault, for instance) and raises it again when it fails. In a job, a machine stop that has stood for ten minutes ends the execution (see "The idle shutdown"), so the fix is a new commit on `main` and a new execution.

### The image on the cost records

Every cost record names the image the agent run ran on (the identity from the file `FACTORY_IMAGE_ID_FILE` names, joined with the stage file's digest when the project has one; see "The project's stage file"). A record made when the instance has no image identity has none.

### The code and the project apart

Some projects live on a host of their own, such as a company's enterprise host, and run the factory's public code from a public repository. Give `--repository-url` the project and `--code-url` the code:

```bash
sudo sh vm/setup.sh --device /dev/sdb \
  --repository-url https://git.company.example/team/project.git \
  --code-url https://github.com/pkrahmer/kumpel-factory.git
```

- **The code is cloned without a credential.** The clone of `/srv/factory/<instance>/factory` runs with `GIT_TERMINAL_PROMPT=0` and without `GIT_ASKPASS` and `core.askPass`, after the wait for the secrets, in the same pass as the install of the helper and the unit. A code repository that asks for a credential fails the clone: `setup: checkout: cannot clone <url> without a credential; the code repository must be readable without a token`, exit status 1. `--code-url` equal to `--repository-url`, or absent, keeps the checkout as it was, with the token.
- **`factory.env` holds the project only.** `FACTORY_REPOSITORY_URL` is `--repository-url`; the code url is written nowhere.
- **The project brings its own files.** The factory reads `factory/pipeline.yml`, `factory/story-form.md` and `factory/feature-form.md` from the project, and optionally `factory/agents/`. Its `Makefile` has the targets `check`, `lint`, `test` and `sync`.
- **The stage image comes from the code.** `vm/Dockerfile` is the one in the code checkout, not the project's.
- **An update of the code is a new ref and a rebuild.** Run `vm/setup.sh` again with the new `--code-ref`, as *The rebuild after a merge* describes. A checkout that exists is not cloned again, so a changed `--code-url` alone changes nothing on a machine that has one.
- **The helper answers only the project's host.** With `FACTORY_REPOSITORY_URL` set, `git-credential-factory` gives the token only when git asks for the host of that URL, so the token is never offered to the code repository's host or to any other (see *The hosting-service token*).

### The script

`vm/setup.sh` makes the machine from a fresh Ubuntu 24.04 with a spare disk and installs the service. It is POSIX `sh`, runs as root and does only what is missing, so a second run changes nothing.

```bash
sudo sh vm/setup.sh --device /dev/sdb --repository-url https://github.com/<owner>/<repo>.git
```

| Option | Default | Meaning |
|---|---|---|
| `--device <path>` | required | The disk, or a file such as `/var/lib/factory-pool.img`, the pool is made on. The script does not test it: a pool that exists is found whatever `--device` names. |
| `--repository-url <url>` | required | The repository the factory works on, and runs from when `--code-url` is not given. |
| `--code-url <url>` | the `--repository-url` | The repository the factory's code and its stage image's `vm/Dockerfile` come from. When it differs from `--repository-url` it is cloned without any credential (see *The code and the project apart*). |
| `--instance <name>` | `vm` | The instance's name; its folder is `/srv/factory/<instance>`. |
| `--pool <name>` | `tank` | The ZFS pool. |
| `--quota <size>` | `30G` | The quota of the instance's dataset. |
| `--code-ref <git ref>` | `main` | The factory's git ref to check out. The old name `--ref` is refused: the script prints `setup.sh: --ref is now --code-ref` and the usage, and exits 2 before any step runs. |
| `--image <tag>` | `factory-stage:<instance>` | The stage image. |
| `--runtime claude\|opencode` | `claude` | The agent runtime. |
| `--sudoers` | off | Reach `zfs` through `sudo` (see below). |
| `--idle-shutdown <minutes>` | off | Let the factory power the machine off after that many idle minutes: a whole number of ASCII digits, at least 1 (`0`, `x`, `-5`, `1.5` and an empty value are refused). Gives `factory` the power-off right (step 9) and adds `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>` to the environment file (step 14). See *The idle shutdown*. |
| `--help` | | Print the usage to standard output and exit 0. |

A missing required option, an option without its value, an `--idle-shutdown` value that is not a whole number of at least 1, an unknown word or a runtime other than the two prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2. When the user is not root it prints `setup.sh: run as root` and exits 2. Nothing is made or changed before either exit.

#### The steps

Each step prints one line, `setup: <step>: `, followed by what it changed (joined with `; `) or, when nothing needed doing, what it found, which says `found`. The steps run in this order:

1. `packages`: `apt-get update`, then `apt-get install -y --no-install-recommends` of the missing ones among `zfsutils-linux podman uidmap slirp4netns git make python3.12-venv`.
2. `pool`: `zpool create -o ashift=12 -O compression=lz4 -O atime=off <pool> <device>`, unless `<pool>` exists.
3. `user`: the user `factory` with a home and `/bin/bash`, unless it exists. `/etc/subuid` and `/etc/subgid` must each hold a `factory:` line; the script does not make one. Without it, it prints `setup: user: no subuid and subgid range for factory; add one with usermod --add-subuids and --add-subgids` to standard error and exits 1. Add the ranges and run the script again.
4. `linger`: `loginctl enable-linger factory`, so rootless Podman and the user's runtime folder outlive a login.
5. `datasets`: `<pool>/factory` and `<pool>/factory/<instance>`, both with `compression=lz4` and `atime=off`, the second mounted at `/srv/factory/<instance>/work`, with the quota, and the mount point owned by `factory`, and then the first base `<pool>/factory/<instance>@base`, taken while the dataset is still empty and owned by `factory` and before the delegation of step 6. A dataset that already has a base keeps it; the script never touches it. A dataset that exists without a base gets one.
6. `delegation`: `zfs allow -u factory snapshot,destroy,rollback,diff,mount` on the instance's dataset, unless all five are already delegated.
7. `sudoers`: only with `--sudoers`, see below. Without it the line says `not asked` and neither file is touched.
8. `caches`: on every run, with or without `--sudoers`, the helper `/usr/local/bin/factory-drop-caches` (mode `0755`; it runs `sync`, then writes `1` to `/proc/sys/vm/drop_caches`) and `/etc/sudoers.d/factory-drop-caches` (mode `0440`), which holds the one rule `factory ALL=(root) NOPASSWD: /usr/local/bin/factory-drop-caches`. Each is written only when its text differs. The rule is checked with `visudo -cf`; if `visudo` refuses it, the script removes the file, prints `setup: caches: visudo -cf refused /etc/sudoers.d/factory-drop-caches; removed it` to standard error and exits 1. See *The page cache after a rollback*.
9. `poweroff`: with `--idle-shutdown`, `/etc/sudoers.d/factory-poweroff` (mode `0440`, owner root), which holds the one rule `factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff`, written only when its text differs and checked with `visudo -cf`; if `visudo` refuses it, the script removes the file, prints `setup: poweroff: visudo -cf refused /etc/sudoers.d/factory-poweroff; removed it` to standard error and exits 1. Without the option it runs `rm -f` on that file, so a right an earlier run gave is taken back, and the line says `setup: poweroff: not asked; the factory gets no power-off right`. See *The idle shutdown*.
10. `folders`: `/srv/factory/<instance>` with `state` and `repo`, owned by `factory` (mode `0755`), and `/home/factory/.secrets` (mode `0700`). If `state`, `repo` or `/home/factory/.secrets` is a link, the script prints `setup: folders: ...` to standard error and exits 1 before it makes anything in the step: remove the link and run it again. The script sets the secrets folder's owner and mode and never touches a file in it: the secrets you placed stay as they are on every run.
11. `image-id`: `/srv/factory/<instance>/image-id`, a fresh uuid (mode `0644`) when the file is missing or empty. A rebuilt image needs a new id; renew the file yourself (see *The stage image*).
12. `checkout`: the factory at `--code-ref`, cloned as `factory` into `/srv/factory/<instance>/factory`, unless it holds a `.git`.
13. `tools`: a virtual environment `/srv/factory/<instance>/tools` with `uv` installed from `pip` at the version of `ARG UV_VERSION` in the checkout's `vm/Dockerfile`; `uv sync --frozen --no-dev` in the checkout, which makes the factory's own `.venv`; and `/usr/local/bin/git-credential-factory`, copied from the checkout's `vm/git-credential-factory` (see *The two passes*). `uv sync` runs on every run and changes nothing when the environment matches the lockfile.
14. `environment`: `/srv/factory/<instance>/factory.env` (mode `0644`). With `--idle-shutdown` its last line is `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`; without the option the file holds no such line, so a run without it takes the setting back. It always holds `FACTORY_TRANSCRIPT_DIR=/srv/factory/<instance>/transcripts` before that line.
15. `service`: the unit `vm/factory.service` as `/etc/systemd/system/factory@.service` (mode `0644`; see *The two passes*), `systemctl daemon-reload`, and `systemctl enable factory@<instance>`. The service is enabled, not started.
16. `transcripts`: the folder `/srv/factory/<instance>/transcripts` (owner `factory`, mode `0700`), made only when it is not already so. If the folder is a link, the script prints `setup: transcripts: <path> is a link; remove it and run this script again` to standard error and exits 1, before it makes anything there. The script writes no `tmpfiles.d` rule and has no option for an age. See *Transcripts*.

The script writes the files under `/srv/factory/<instance>` (`image-id`, the askpass script and `factory.env`) as `factory`, with `cat` from its own standard input, because a process started by `runuser` may not reopen root's `/dev/stdin`.

The script ends with `setup: done: build the stage image and start factory@<instance>; see the operator guide, "The machine"`.

#### The two passes

The checkout of the private repository needs the hosting token. When `/home/factory/.secrets/hosting-token` is not there at step 12, the script prints `setup: checkout: waiting for /home/factory/.secrets/hosting-token; place the secrets and run this script again` and exits 0. Place all three files, `hosting-token`, `claude-token` and `anthropic-api-key`, in `/home/factory/.secrets`, readable by `factory`, and run the same command again: steps 1 to 11 report `found` and the rest completes. All three must exist whatever the runtime; with the `claude` runtime the key file stays empty.

The token is written into no file. Git asks the askpass script (`/srv/factory/<instance>/askpass`) for it, and only that script reads the token file; the clone sets `core.askPass` on its own command line, not in any git configuration.

The unit and the credential helper come from the checkout, and root installs them only in the run that made the clone (whose content is the remote's at `--code-ref`, before the service ever ran) or when the installed file is missing. So a first run that stopped after the clone is completed by the next. A later run that finds the installed file in place but different from the checkout installs nothing and prints one of these two lines to standard error:

```text
setup: tools: /usr/local/bin/git-credential-factory differs from the checkout; not installed; install it from your own copy of vm/git-credential-factory (operator guide, "The rebuild after a merge")
setup: service: /etc/systemd/system/factory@.service differs from the checkout; not installed; install it from your own copy of vm/factory.service (operator guide, "The rebuild after a merge")
```

Root installs nothing from the checkout, because `factory` can write it; your own copy of the ref is the trusted text. So install the new file yourself, from your copy, before you run the script again. On your own computer, in your checkout of the ref the instance runs, copy the script and both files to the VM:

```bash
gcloud compute scp --zone=europe-west3-a --tunnel-through-iap vm/setup.sh vm/factory.service vm/git-credential-factory factory-vm:
```

On the VM from your own account, install the file the script named:

```bash
sudo install -m 0644 factory.service /etc/systemd/system/factory@.service
sudo install -m 0755 git-credential-factory /usr/local/bin/git-credential-factory
```

Then run the script as in *The rebuild after a merge*: it runs `systemctl daemon-reload` and reports the file found.

#### The environment file

Every run rewrites `factory.env` from the arguments and from the pins in the checkout's `vm/Dockerfile` (the Claude Code and opencode versions and the opencode model ids), and writes it only when its text differs. A change therefore goes into the script's arguments (or the Dockerfile), never into the file: an edit by hand is lost at the next run.

For values the script does not know (a model map for a company's proxy, the path of a provider file, the names of the proxy variables), make a second file, `/srv/factory/<instance>/factory.local.env`, in the same `NAME=value` form. The unit reads it after `factory.env`, so a value in it wins over the same name there. It is optional: without it the unit starts as before. The script never creates, changes or removes it, and says so in its last line (`setup: local: ...`). Restart the instance after a change: the factory reads its environment when it starts.

Every name in `factory.local.env` is in the factory process's own environment, because the unit sets it for the whole service. `FACTORY_CONTAINER_ENV` then chooses which of these names the containers also get.

#### The page cache after a rollback

A page that a stage wrote through `mmap` survives `zfs rollback` in the kernel's page cache. After the rollback the file has the snapshot's size but may still read the newer page: a file the stage made shorter reads as zero bytes past its end, and git's stat cache calls it clean, so the sync does not repair it. The factory therefore drops the clean page cache after every reset, right after a rollback that succeeded, by running `sudo -n /usr/local/bin/factory-drop-caches`. This is not a setting and does not depend on `--sudoers` or `FACTORY_ZFS`: step 8 installs the helper and its `sudoers` rule on every run.

The drop is machine-wide. It also empties the cache of other files, so the next sync reads from the disk and is a little slower. A drop that fails (no helper, no rule so that `sudo` asks for a password, or the time limit of ten minutes) is a `SnapshotError` like a failed `zfs` command and the stage does not start. A machine set up by hand with the same two files, as `vm` was, is found unchanged by step 8.

#### The `sudoers` fallback

The delegation of step 6 is the way for the factory to reach `zfs`. When it does not suffice on your machine, run the script with `--sudoers`. Step 7 then writes `/etc/sudoers.d/factory-zfs` (mode `0440`), which lets `factory` run exactly `zfs snapshot`, `zfs destroy`, `zfs rollback -r` and `zfs diff -FH`, each on `<dataset>@base` alone, as root without a password, and checks it with `visudo -cf`. If `visudo` refuses it, the script removes the file, prints the refusal to standard error and exits 1. It also writes `/usr/local/bin/zfs-factory` (mode `0755`), a wrapper that runs those four commands through `sudo -n /usr/sbin/zfs` and every other command as itself, and the environment file then holds `FACTORY_ZFS=/usr/local/bin/zfs-factory`.

The rule names `diff -FH` because the factory runs `zfs diff` with those flags and `sudoers` matches the whole argument list; a rule for `diff -H` would not match.

### The service

The unit `vm/factory.service` is a systemd template, installed as `factory@.service`; the text after the `@` is the instance. For the default instance it is `factory@vm`. The unit runs as `factory`, with `/srv/factory/%i` as its working directory, reads `/srv/factory/%i/factory.env` and then, if it exists, `/srv/factory/%i/factory.local.env` (see *The environment file*), and starts `/srv/factory/%i/factory/.venv/bin/factory-run`. `Restart=always` with `RestartSec=15` restarts it fifteen seconds after any exit.

```bash
sudo systemctl start factory@vm      # also stop, restart, status
sudo journalctl -u factory@vm        # the process's output
sudo -u factory /srv/factory/vm/factory/.venv/bin/factory-health --state-directory /srv/factory/vm/state
```

Nothing runs a health check by itself: ask `factory-health` as `factory`. Build the stage image before the first start (see *The stage image*).

The environment file holds these variables, which *Configuration* explains:

| Variable | Value |
|---|---|
| `FACTORY_INSTANCE` | `--instance` |
| `FACTORY_REPOSITORY_URL` | `--repository-url` |
| `FACTORY_AGENT_RUNTIME` | `--runtime` |
| `FACTORY_DATASET` | `<pool>/factory/<instance>` |
| `FACTORY_WORKSPACE` | `/srv/factory/<instance>/work` |
| `FACTORY_STAGE_IMAGE` | `--image` |
| `FACTORY_ZFS` | `zfs`, or `/usr/local/bin/zfs-factory` with `--sudoers` |
| `FACTORY_CHECKOUT` | `/srv/factory/<instance>/repo` |
| `FACTORY_STATE` | `/srv/factory/<instance>/state` |
| `FACTORY_IMAGE_ID_FILE` | `/srv/factory/<instance>/image-id` |
| `FACTORY_CLAUDE_HOME` | `/srv/factory/<instance>/factory/claude` |
| `FACTORY_TOKEN_FILE` | `/home/factory/.secrets/hosting-token` |
| `FACTORY_CLAUDE_LOGIN_FILE` | `/home/factory/.secrets/claude-token` |
| `FACTORY_API_LOGIN_FILE` | `/home/factory/.secrets/anthropic-api-key` |
| `FACTORY_CLAUDE_VERSION`, `FACTORY_OPENCODE_VERSION`, `FACTORY_OPENCODE_MODELS` | the pins of `vm/Dockerfile` |
| `PATH` | `/srv/factory/<instance>/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin` (`/usr/sbin` holds `zfs`) |
| `XDG_RUNTIME_DIR` | `/run/user/<uid of factory>`, where rootless Podman finds its runtime folder |
| `FACTORY_TRANSCRIPT_DIR` | `/srv/factory/<instance>/transcripts` |
| `FACTORY_IDLE_SHUTDOWN_MINUTES` | `--idle-shutdown`, only when it is given |

### On GCP, step by step

This is the machine of the decisions of 2026-10-24: instance `vm`, an `e2-standard-2` in `europe-west3`, no inbound port, no service account, a budget alert of $120 a month. Steps 1 to 5 run on your own computer with `gcloud` signed in; replace `<project-id>` and `<account-id>`. Never paste a token or key into a chat or an agent's prompt; make each secret file by hand.

1. Create the project and the budget first, so that the alert exists before any cost does:

   ```bash
   gcloud auth login
   gcloud projects create <project-id> --name="factory"
   gcloud config set project <project-id>
   gcloud billing accounts list
   gcloud billing projects link <project-id> --billing-account=<account-id>
   gcloud services enable compute.googleapis.com iap.googleapis.com
   gcloud billing budgets create --billing-account=<account-id> --display-name="factory" \
     --budget-amount=120USD --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
   ```

2. Give the VM its way out: a router and Cloud NAT. The VM gets no external address, so apt, npm, GitHub and the Anthropic API are reached through NAT.

   ```bash
   gcloud compute routers create factory-router --network=default --region=europe-west3
   gcloud compute routers nats create factory-nat --router=factory-router --region=europe-west3 \
     --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
   ```

3. Open SSH for IAP's range only. Nothing else is open to the internet.

   ```bash
   gcloud compute firewall-rules create allow-iap-ssh --network=default --direction=INGRESS \
     --allow=tcp:22 --source-ranges=35.235.240.0/20
   ```

4. Create the data disk. It holds the ZFS pool and survives the VM (`auto-delete=no` in the next step).

   ```bash
   gcloud compute disks create factory-data --size=50GB --type=pd-balanced --zone=europe-west3-a
   ```

5. Create the VM from Ubuntu 24.04, with no service account and no external address, and the disk attached under the device name `factory-data`:

   ```bash
   gcloud compute instances create factory-vm --zone=europe-west3-a --machine-type=e2-standard-2 \
     --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud --boot-disk-size=20GB \
     --no-service-account --no-scopes --no-address \
     --disk=name=factory-data,device-name=factory-data,mode=rw,auto-delete=no
   ```

6. Copy the script to the VM through the tunnel, and open a shell there. Copy it from a checkout of the ref you will run.

   ```bash
   gcloud compute scp --zone=europe-west3-a --tunnel-through-iap vm/setup.sh factory-vm:
   gcloud compute ssh factory-vm --zone=europe-west3-a --tunnel-through-iap
   ```

   The script is `vm/setup.sh`.

7. On the VM, run the script as root, the first time. The disk is `/dev/disk/by-id/google-factory-data` (`ls -l /dev/disk/by-id/ | grep google` shows it). `--code-ref` is the tag or branch to run.

   ```bash
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/kumpel-factory.git --code-ref <the tag or branch to run>
   ```

   It installs the packages and makes the pool, the user `factory`, the datasets, the delegation and the folders. Then it stops with `setup: checkout: waiting for /home/factory/.secrets/hosting-token` and exit status 0: the private repository needs the token (see *The script*, "The two passes"). On a VM that the prototype of `planning/overnight/gcp-runbook-2026-10-24.md` already prepared, the script finds those steps done and reports `found`.

8. Place the three secrets by hand, from your own account on the VM, one file each: `hosting-token` (the GitHub token), `claude-token` (the output of `claude setup-token`) and `anthropic-api-key`. Make each file in your home folder with an editor, install it, and remove the copy:

   ```bash
   sudo install -m 0600 -o factory -g factory hosting-token /home/factory/.secrets/hosting-token
   sudo install -m 0600 -o factory -g factory claude-token /home/factory/.secrets/claude-token
   sudo install -m 0600 -o factory -g factory anthropic-api-key /home/factory/.secrets/anthropic-api-key
   shred -u hosting-token claude-token anthropic-api-key
   ```

   All three files must exist, because the factory mounts every login file the environment file names and podman refuses to mount a missing one; every agent run would stop with exit status 125 (decision 10 of the feature F0043). This holds whatever the runtime is. Under `claude` the file `anthropic-api-key` may be empty (an empty file means no key); under `opencode` the file `claude-token` may be empty, since opencode does not read it, and `anthropic-api-key` holds the key.

9. Run the script a second time with the same arguments. It clones the factory, installs the tools, writes the environment file and installs and enables the unit.

   ```bash
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/kumpel-factory.git --code-ref <the tag or branch to run>
   ```

10. Build the stage image as `factory`, from the checkout the script made. `<ref>` labels the image; any text will do.

    ```bash
    sudo -iu factory
    cd /srv/factory/vm/factory
    podman build -f vm/Dockerfile -t factory-stage:vm --build-arg FACTORY_IMAGE=<ref> /srv/factory/vm/factory
    exit
    ```

11. Start the instance and look at it:

    ```bash
    sudo systemctl start factory@vm
    sudo -iu factory
    set -a; . /srv/factory/vm/factory.env; set +a
    /srv/factory/vm/factory/.venv/bin/factory-watch
    /srv/factory/vm/factory/.venv/bin/factory-health --state-directory /srv/factory/vm/state
    ```

    `factory-watch` shows the board and what the next tick would do. `factory-health` prints `healthy` or one line per stop in force. The console scripts live in the factory's virtual environment, which the environment file's `PATH` does not name, so the full path is needed. The environment file is loaded so that `factory-watch` reads the instance's settings.

12. When the machine is not used, stop the instance first and then the VM. A VM stop during a stage ends the factory after systemd's stop timeout of 90 seconds, and the next start counts that stage as a crash (see *The rebuild after a merge*). So wait until no work item is held by `vm`: on the VM as `factory`, run `factory-watch` as in step 11 and look at the board. Then, on the VM from your own account (leave the `factory` shell with `exit`), stop the instance:

    ```bash
    sudo systemctl stop factory@vm
    ```

    Then, on your own computer, stop the VM:

    ```bash
    gcloud compute instances stop factory-vm --zone=europe-west3-a
    ```

    A stopped VM costs only its disks and NAT (see *The costs*). Start it again on your own computer with `gcloud compute instances start factory-vm --zone=europe-west3-a`; the service is enabled and comes up with it, because `systemctl stop` does not disable it.

### On any Ubuntu 24.04 VM

A Hyper-V VM at home or a VM on TrueNAS SCALE does as well as GCP. Take the steps of *On GCP, step by step* from step 6 on, without `gcloud`: copy `vm/setup.sh` to the VM, run it as root with `--device` naming a spare disk (or a file such as `/var/lib/factory-pool.img`), place the three secrets, run the script again, build the image, start the service.

The script needs:

- a Linux kernel with the ZFS module (Ubuntu 24.04's ships it signed; the script installs `zfsutils-linux`);
- a spare block device for the pool;
- rootless Podman, with a `factory:` range in `/etc/subuid` and `/etc/subgid` (Ubuntu's `useradd` adds one);
- outbound network for apt, npm, GitHub and the Anthropic API.

`podman machine`, WSL 2 and the workplace's Podman Desktop are not hosts for it: they give no kernel with ZFS and no rootless Podman on a real Linux host (question 7 of `planning/v1.2-plan.md`). Run the instance on a Linux VM instead.

### What the container can and cannot see

A stage container sees:

- the dataset at `/work`: the checkout and the agent's home (`HOME=/work/home`). It may write anywhere there; the take copies only what the role may write, and the next stage starts from the base again;
- read-only mounts: in the sync container the host repository's `.git` at `/upstream` (the sync fetches from it, because the container has no credentials), and in the agent's container the login file and the instructions file at their paths. A rootless container cannot write a read-only mount;
- the network: the Anthropic API, npm and GitHub through NAT.

It does not see the hosting token (only the host reads it, and the host alone pushes), the host's files outside its mounts, the next stage, or anything of the metadata server worth having (see *The metadata server*). Every container runs with `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g` and `--userns=keep-id` (the files it writes belong to `factory` on the host), and with `--timeout` set to the step's time limit.

### The costs

The numbers are the plan's (`planning/v1.2-plan.md`), in US dollars, for `europe-west3`:

| Item | Cost |
|---|---|
| VM `e2-standard-2` (2 vCPU, 8 GB) | about $50 to $55 a month; `e2-standard-4` about $100 |
| Data disk, 50 GB `pd-balanced` | about $5 a month |
| Cloud NAT | about $1 a month plus traffic |

The budget alert is $120 a month, with thresholds at 50 %, 90 % and 100 %; it warns and stops nothing. A stopped VM costs its disks (the boot disk and the data disk), not the machine.

### The metadata server

Every GCP VM reaches a metadata server at `169.254.169.254`, and so does every container on it, through the VM's network. A request needs the header `Metadata-Flavor: Google`. The VM is created with `--no-service-account --no-scopes`, so the server gives instance metadata (name, zone, network) and no access token. The factory needs no Google API, so a container that reads it gets nothing it can use. Outside GCP there is no such server.

### Where the logs are

- `sudo journalctl -u factory@vm`: what `factory-run` prints, and the unit's own starts and exits. The `systemctl` commands are in *The service*.
- `/srv/factory/vm/state/factory.log`: the factory log (see "The factory log and the health status file" in [health.md](health.md)). After every stage it holds a line `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`. The plan's measure "the start of a stage to the agent's first step" (target under 20 s with a warm base, the reset under 2 s) is `reset` plus `sync` plus `advance`; `take` is the copy back.
- `health.json` in the state directory, through `factory-health --state-directory /srv/factory/vm/state`.
- `sudo -iu factory podman ps`: a stage container that is running now. Containers run with `--rm`, so a finished one leaves nothing to look at.

### The idle shutdown

A VM costs money for every hour it runs, also while the factory has nothing to do. With `FACTORY_IDLE_SHUTDOWN_MINUTES` set to a whole number above 0, the factory powers the machine off after an idle stretch of that many minutes. Unset, blank or `0` leaves it off, and then none of this runs.

**What is idle.** A tick is idle when it ran, ended at no stop and handled the event `idle`. That holds when nothing can be started, when the first waiting work item waits for the human (an approval, a question the factory posted), and when another instance holds a claim. A story that waits overnight for your merge therefore counts as idle: that is the cost the option saves. A tick that ended at a stop, or that handled any other event (a run, a comment, a merge, a crash, an error), is not idle and starts the stretch again. A stop waits for a fix you may make on the machine, so on a VM the machine stays up while one stands (in a job, see *In a job* below). An iteration that ran no tick (the checkout could not be prepared) neither counts nor ends the stretch. The first stretch starts when the instance starts.

**The two log lines.** Both go to the factory log (`factory.log` in the state directory) and both begin `idle shutdown: `:

- `idle shutdown: idle for <n> minutes, powering the machine off` is written right after the idle tick that ends a stretch of at least the limit, just before the factory asks the machine to power off.
- `idle shutdown: power off failed: <detail>; the factory runs on` follows it when the machine refused or could not be asked.

**A refused power-off.** The factory runs `sudo -n /usr/bin/systemctl poweroff`, the one command it needs. When `factory` has no right to it, `sudo` is missing, the call reaches its time limit of one minute, or the instance does not run on the VM, the second line holds the last line `sudo` printed (for example `sudo: a password is required`) or `exit status <n>`. It is not a stop: the instance runs on, starts a new stretch, and asks again only after another full limit. Read the line with `grep 'idle shutdown' /srv/factory/vm/state/factory.log`. No preflight item checks the right.

**In a job.** A Cloud Run job has no `systemctl` and no `sudo`, so `poweroff` would only be refused and the job billed until its task timeout. With `FACTORY_IDLE_SHUTDOWN_ACTION=exit` the factory, after the idle tick that ends the stretch, stops its own loop the way a `SIGTERM` does: the tick in progress is the last, and `factory-run` ends with status 0, which ends the job's execution. The job's schedule starts it again, or you do (`gcloud run jobs execute <job>`), as you start a stopped VM. The log line says what happens, `idle shutdown: idle for <n> minutes, ending the factory's process`; with `poweroff` it is `idle shutdown: idle for <n> minutes, powering the machine off`. The idle rule and `FACTORY_IDLE_SHUTDOWN_MINUTES` are unchanged (`0` is still off). A VM keeps `poweroff`.

**A machine stop in a job.** On a VM a machine stop waits for a fix you make on the machine; in a job nobody can, because its file system is gone with the execution and the only fix is a new execution with other settings. So with the idle shutdown on and the action `exit`, a machine stop that has stood for ten minutes ends the process: `factory-run` ends with status 1, the execution ends as failed, and the last line of the job's log names the stop, `machine stop: standing for 10 minutes in a job, ending the factory's process: <reason>: <detail>`. The ten minutes are fixed and count from the first time of an unbroken stretch of the stop, though the preflight raises it again on every tick. A stop lifted before then ends nothing, and a new one counts from its own time. The rule is checked after every tick and after every iteration that ran no tick. It holds for no stop of scope `repository` (a push to `main` lifts those, and a job can see it), and not with `poweroff` or with the idle shutdown off.

**The right.** The setup script gives `factory` the right to that one command, and sets the variable in the environment file, with its option `--idle-shutdown <minutes>`: step `poweroff` writes `/etc/sudoers.d/factory-poweroff`, step `environment` the line `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`, both from the same run. Without the right, set the variable only if you accept the second log line above.

**Turning it on and off.** To turn it on, or to change the minutes, run the script again with the option, then restart the service so that it reads the new environment file:

```bash
sudo sh vm/setup.sh --device /dev/sdb --repository-url https://github.com/<owner>/<repo>.git --idle-shutdown 30
sudo systemctl restart factory@vm
```

To turn it off, run the script again without the option (and restart the same way): it removes `/etc/sudoers.d/factory-poweroff` and the line in the environment file. The script never starts or stops the service and never powers the machine off itself.

**Starting the machine again.** Starting is outside the factory. By hand, from your own computer:

```bash
gcloud compute instances start factory-vm --zone europe-west3-a
```

Or let a GCP instance schedule start it at the hours you work. Make the schedule by hand with `gcloud compute resource-policies create instance-schedule` and attach it with `gcloud compute instances add-resource-policies`; give it a start time only, so that the factory's own power-off is the only thing that stops the VM. The service is enabled and comes up with the machine. A merge, a close or an answer you gave while the VM was off is seen at the first tick after the start.

### The rebuild after a merge

The instance runs the factory's code from `/srv/factory/vm/factory` and the stage image built from it. After a merge to the ref it runs, stop the instance between two stages, bring both up to date, and start it again.

Stop it first. An agent run lasts up to its role's `time_limit`, so a running instance may be in the middle of a stage. A stop during a stage ends the factory after systemd's stop timeout of 90 seconds, and the restart counts that stage as a crash (see "If the factory dies while a stage runs"). So wait until no work item is held by `vm`: on the VM as `factory`, run `factory-watch` as in step 11 of *On GCP, step by step*, and look at the board. Then, on the VM from your own account, stop the instance:

```bash
sudo systemctl stop factory@vm
```

A stop of the service also ends the instance's running agent and check containers. The unit runs `podman stop --filter label=factory.instance=%i` as `factory` after every end of `factory-run`, a stop or a crash, and every container the factory starts carries that label, so containers of another instance, or without the label, are left alone. A stage cut off this way is a crash for the factory, and the next start takes it up again (see "A restart during a stage" in [work-items.md](work-items.md)). A machine set up before this change keeps the old unit until you install the new one by hand: copy `vm/factory.service` from your checkout to the VM, then run `sudo install -m 0644 factory.service /etc/systemd/system/factory@.service` and `sudo systemctl daemon-reload`. `vm/setup.sh` prints that the file differs and leaves it (see below).

Then bring the checkout and the image up to date. On the VM as `factory` (`sudo -iu factory`):

```bash
git -C /srv/factory/vm/factory pull --ff-only          # for a tagged ref: git fetch --tags, then git checkout <tag>
cd /srv/factory/vm/factory
/srv/factory/vm/tools/bin/uv sync --frozen --no-dev
podman build -f vm/Dockerfile -t factory-stage:vm --build-arg FACTORY_IMAGE=<ref> /srv/factory/vm/factory
podman image prune -f
cat /proc/sys/kernel/random/uuid > /srv/factory/vm/image-id
exit
```

`podman image prune -f` removes the previous stage image, which the build left untagged, and the build's leftovers. It removes only untagged images that no container uses, so another instance's tagged image and a running container are safe. Without it every rebuild leaves an image behind in the factory's storage. The prune also removes the intermediate images the build's layer cache would reuse, so the next build is slower without the cache.

The new uuid in `image-id` is what tells the settings the image is new; the label is not its identity. Then run the setup script from a copy of your own, as root: copy `vm/setup.sh` from your checkout of the ref the instance runs, as in step 6 of *On GCP, step by step*, and run it from your own account with the arguments of the first run. Root runs nothing from `/srv/factory/vm/factory`, because `factory` can write that checkout.

On your own computer, in your checkout, copy the script and the two files it may need to install to the VM, and open a shell there:

```bash
gcloud compute scp --zone=europe-west3-a --tunnel-through-iap vm/setup.sh vm/factory.service vm/git-credential-factory factory-vm:
gcloud compute ssh factory-vm --zone=europe-west3-a --tunnel-through-iap
```

On a VM outside GCP, copy `vm/setup.sh`, `vm/factory.service` and `vm/git-credential-factory` from your own checkout by your own means, such as `scp`, as *On any Ubuntu 24.04 VM* does.

On the VM from your own account, run the script and start the instance again:

```bash
sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
  --repository-url https://github.com/pkrahmer/kumpel-factory.git --code-ref <the same ref>
sudo systemctl start factory@vm
```

`vm/setup.sh` is idempotent, so run it after every merge: it carries a changed pin of `vm/Dockerfile` into the environment file, updates `uv` and the factory's virtual environment, and reports the rest found. It does not replace an installed `/etc/systemd/system/factory@.service` or `/usr/local/bin/git-credential-factory` that differs from the checkout: it prints that the file differs and leaves it. When a merge changed `vm/factory.service` or `vm/git-credential-factory`, install it from your own copy with the commands of *The two passes* before you run the script.
