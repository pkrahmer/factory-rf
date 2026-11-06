# The VM and its stage image

A topic of the [operator guide](README.md). It is for the operator of an [instance](../project-guide/glossary.md) who knows Linux and does not read the code. The factory's own words are explained in the [glossary](../project-guide/glossary.md). They are [stage](../project-guide/glossary.md), [dataset](../project-guide/glossary.md), [base](../project-guide/glossary.md), [take](../project-guide/glossary.md), [tick](../project-guide/glossary.md), [stop](../project-guide/glossary.md), [work item](../project-guide/glossary.md), [claim](../project-guide/glossary.md), [cost record](../project-guide/glossary.md), [crash](../project-guide/glossary.md) and [role](../project-guide/glossary.md).

An `sh` block holds bare commands for a real machine or a cloud account. The text above it says where they run. `make documents` does not run them, and they show no output. It does run the `console` blocks.

## The machine

The machine runs every stage in containers on a dataset. This chapter takes a fresh Ubuntu 24.04 VM to a running instance, and says what the machine is, what it costs and where to look when it misbehaves.

### What it is

One host, one dataset, one throwaway container for each step of a stage.

- **The host** is a Linux VM. The factory runs on it as a systemd service, `factory@<instance>`, under the user `factory`. The hosting token is on the host and nowhere else: the host alone fetches and pushes.
- **The dataset** is the ZFS dataset `<pool>/factory/<instance>`, mounted at `/srv/factory/<instance>/work` on the host and at `/work` in every container. It holds the checkout and the agent's home. Its one snapshot is the base, `@base`, moved forward at every stage's start.
- **The container** is the stage image (see *The stage image*), started for one step, with `--rm`, `--userns=keep-id` and `--timeout` set to the step's time limit. It mounts the dataset and is thrown away.

There is one user, `factory`, and no second one. `factory` has no `sudo` right but three. These are the page-cache helper, the four `zfs` commands of the optional `--sudoers` fallback and, with the option `--idle-shutdown`, `/usr/bin/systemctl poweroff` (see *The script*). The steps that need root run from your own account with `sudo`. They are the script, `systemctl` and the install of the secrets.

By default one repository URL serves both the factory's own code and the project. `--repository-url` is then the clone of `/srv/factory/<instance>/factory` and the value of `FACTORY_REPOSITORY_URL`. An instance thus builds the repository it runs from. With `--code-url` the two are apart. The clone of `/srv/factory/<instance>/factory` comes from `--code-url`. `--repository-url` stays the project and the value of `FACTORY_REPOSITORY_URL` (see *The code and the project apart*).

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

A managed sandbox such as a Cloud Run job cannot start the factory's containers the way the VM does. Set `FACTORY_CONTAINER_PROFILE=job` there. The default, `rootless`, is what the VM uses.

What the sandbox lacks, as measured with Podman 5.4:

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

Podman's storage root must be on a filesystem the kernel's overlay accepts as its upper layer. In a job, whose root file system is itself an overlay, that is a tmpfs. The start script mounts one at Podman's storage root.

The factory names no mount program. A userspace overlay (`fuse-overlayfs`) passes every file read from an image through a daemon. On a job of eight CPUs `make test` took about ten minutes with it and about three with the native overlay on a tmpfs. The image build took about three minutes against about two. A tmpfs is memory: the image layers and the containers' writes then count against the job's memory, so size the job for them.

The container runs as the job's root with every capability dropped (`--cap-drop=all`). `--security-opt=no-new-privileges`, `--pids-limit`, `--memory`, `--timeout` and the mounts are those of `rootless`, and a container ended by `--timeout` exits with status 255, read as the time limit. Files a container writes to `/work` belong to root, which is the job's own user.

### The metadata server in a job

In a Cloud Run job a container shares the job's network with `--network=host`. The metadata server at `169.254.169.254` answers any process there with the job's service-account token. It is reachable from host-network and bridge containers, by address and by name. An agent that holds that token acts as the job's account, so no container may reach the server. The VM is different: it has no service account (see *The metadata server* below).

The block is a firewall rule on the job's side. The start script installs it before the factory starts. It rejects TCP port 80 to that address. DNS, the proxy and everything the factory needs keep working. As an `nft` file, loaded with `nft -f <file>`:

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

With the profile `job` the preflight proves that the rule is in force. Its item `metadata-block` runs one container, right after `stage-image`. The container has no mounts and an empty environment, and it has 30 seconds. It asks the server for the instance id. The command runs in a container of the stage image, not on the host:

```sh
curl -sS -m 5 -o /dev/null -w %{http_code} http://169.254.169.254/computeMetadata/v1/instance/id
```

The item reads the last non-blank line of the output:

| The probe | The item |
| --- | --- |
| prints `000` (curl could not connect, whatever its exit status) | passes, detail `refused` |
| ends past its limit, whatever it printed (checked first) | `the metadata probe did not end within its limit` |
| prints three other digits, such as `200` | `a container reached the metadata server (HTTP <code>); reject tcp port 80 to 169.254.169.254 in the job's firewall` |
| prints nothing, or a line that is not three digits (no `curl` in the image gives exit status 127) | `the metadata probe could not tell (exit <status>): <the last line or "no output">` |
| cannot be started | `cannot run the metadata probe: <error>` |

A failed item stops the machine like any failed preflight item. The stop is `preflight_failed`, with the scope `machine`. The item is not run with the profile `rootless`.

#### The stop `preflight_failed` from `metadata-block`

- **What you see:** `factory-health` shows `preflight_failed`, and the detail is one of the messages in the table above.
- **What it means:** a container could reach the metadata server, or the probe could not tell.
- **What you do:** if the container reached the server, load the rule in the job's network namespace and restart. If the probe could not tell, run the command by hand in the stage image and fix what it shows, for example a `curl` missing from the image.

### Without ZFS

A sandbox that has no ZFS, such as a Cloud Run job, keeps the base as a plain copy. Set `FACTORY_SNAPSHOTS=copy` and `FACTORY_SNAPSHOT_BASE` to an absolute directory outside the workspace, the checkout and the state directory. `FACTORY_DATASET` and `FACTORY_ZFS` are then not read.

Make the base directory once, empty. The first stage fills it. Run this on the sandbox:

```sh
mkdir -p /srv/factory/vm/base
```

Every stage start then does what ZFS does, with copies. `reset` empties the workspace and copies the base into it. `advance` replaces the base with a copy of the workspace. The list of changes compares the two trees file by file, by mode, bytes and link target. It reads bytes in chunks of at most 1 MiB, so a large file is never held whole.

The cost: a reset takes about 1.6 s per GiB, measured on a tree of 20000 files, and the comparison is much slower than `rsync` would be. In a memory-backed sandbox the workspace and the base are both in memory, so the tree is held twice.

The preflight has the item `snapshots` in place of `zfs` and `dataset` (see *The preflight's items* in [health.md](health.md)). The default, `zfs`, uses the items `zfs` and `dataset`.

### The stage image

Every container of a stage (the sync, the agent, the checks) starts from one image that holds the tools and nothing of the factory. [Dockerfile](../../operator/vm/Dockerfile) builds it.

It holds:

- the pinned base image, and Debian's `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils`, at the versions the base image's Debian release ships;
- `uv` and one agent runtime, Claude Code or opencode, at exact versions, with the runtimes' environment: `DISABLE_AUTOUPDATER`, `UV_LINK_MODE`, `PYTHONDONTWRITEBYTECODE`, the two version records `FACTORY_CLAUDE_VERSION` and `FACTORY_OPENCODE_VERSION`, and the opencode model ids `FACTORY_OPENCODE_MODELS`;
- the agent files (`agents/agents` and `agents/settings.json`) at `/etc/factory/agents`, read-only.

It holds no user of its own and no `sudo`, no copy of the factory's source or its `uv sync`, no image-id file and no login or token path: the container runs as the caller's user (`--userns=keep-id`) and mounts the dataset.

The image only carries the agent files. The sync container copies them into the dataset's `/work/home/.claude` before the base moves.

Build it on the VM as the user `factory`, from a checkout. [job-start.sh](../../operator/vm/job-start.sh) does the same in a job:

```sh
podman build -f operator/vm/Dockerfile --build-arg AGENT_RUNTIME=<claude|opencode> -t <FACTORY_STAGE_IMAGE> <the checkout>
```

`AGENT_RUNTIME` has no default. The image holds only that runtime, so it must be the instance's `FACTORY_AGENT_RUNTIME` (the preflight's `agent-runtime-version` fails on an image built for the other one). A build without it, with an empty value or with any other value, fails at once with a message that names `AGENT_RUNTIME`, `claude` and `opencode`. `job-start.sh` passes `FACTORY_AGENT_RUNTIME` itself. After a change of runtime, rebuild the image and renew the file `FACTORY_IMAGE_ID_FILE` names, so that the instance gets a new `image-id`.

`--build-arg FACTORY_IMAGE=<ref>` sets the image's label, `factory.image=<ref>`; the default is `unlabelled`. The label is not the identity of the image. The settings read the identity from the file `FACTORY_IMAGE_ID_FILE` names, and you renew that file after every build. [setup.sh](../../operator/vm/setup.sh) makes the file with a fresh uuid when it is missing or empty (see *The script*). Nothing in `make check` builds the image.

`operator/vm/Dockerfile` installs six Debian packages by name alone: `git`, `make`, `curl`, `ca-certificates`, `procps` and `xz-utils`. Debian's mirror keeps only a package's current version. An exact version would stop building at the next point release, and a job rebuilds the image at every start. The base image's digest fixes the Debian release instead. Within one stable release Debian ships only security and serious fixes.

Everything that shapes a result is still pinned. The base image is named with its digest, and `uv`, Node, Claude Code and opencode have exact versions. A pin is changed in `operator/vm/Dockerfile` alone. The test [test_stage_image.py](../../tests/vm/test_stage_image.py) checks that each pin has its form. It also reports any reference that floats: a `FROM` without a digest, `latest`, a download piped into a shell, or an `apt-get install` of anything but those six names. Run it with `uv run pytest tests/vm/test_stage_image.py`.

A VM's next rebuild takes the current packages of the same release.

The agent runtime is installed by a Node of its own, in a first build stage. That stage downloads Node 22 from nodejs.org, pinned by `NODE_VERSION` and `NODE_SHA256`. It checks the archive with `sha256sum -c` before it unpacks it into `/opt/factory/node`. Then it installs the one runtime `AGENT_RUNTIME` names with that Node's npm.

The final stage copies from it only that runtime's native executable, to `/opt/factory/bin/<runtime>`. `/usr/local/bin/<runtime>` execs it and passes its arguments on. The final stage therefore holds no Node, no npm, no npm cache, no other runtime and no opencode `baseline` executable. It clears apt's lists, debconf's cache, the install logs and `/tmp`. The image has no command for the other runtime, and no `node` or `npm` for projects. A project that needs one installs its own, and that cannot change the runtimes.

To change the Node pin, set both `ARG`s in `operator/vm/Dockerfile`. `NODE_VERSION` is a `22.<n>.<n>` release. `NODE_SHA256` is the SHA-256 that nodejs.org's `SHASUMS256.txt` lists for `node-v<NODE_VERSION>-linux-x64.tar.xz`, in 64 lowercase hex digits. A wrong checksum fails the build.

#### Update the pins

The Debian packages carry no version, so a security or point update needs no edit. Moving to a new Debian release is a deliberate change of the base image's digest. Every pin lives in [Dockerfile](../../operator/vm/Dockerfile).

1. Edit the pin you want to change:

   - Base image: read its digest as shown below, and put the digest after `@sha256:` in the `BASE_IMAGE` default. On the VM as `factory`:

     ```sh
     podman pull <image>
     podman inspect --format '{{index .RepoDigests 0}}' <image>
     ```
   - `uv`: the `UV_VERSION` default.
   - Node: `NODE_VERSION` and `NODE_SHA256` together (see above).
   - Claude Code: the `CLAUDE_CODE_VERSION` default, three numbers. It is installed from its npm package, `@anthropic-ai/claude-code`, with its auto-update off (`DISABLE_AUTOUPDATER=1`). The version is in the environment as `FACTORY_CLAUDE_VERSION`, so the preflight can read it.
   - opencode: the `OPENCODE_VERSION` default and the `FACTORY_OPENCODE_MODELS` value. Check the model ids with the command below, on a computer where opencode is installed:

     ```sh
     opencode models anthropic
     ```

2. Run the test. It reports any reference that floats:

   ```console
   $ uv run pytest tests/vm/test_stage_image.py
   ...
   <n> passed in <seconds>s
   ```

3. Rebuild the image and renew its id, as *The rebuild after a merge* describes. [setup.sh](../../operator/vm/setup.sh) carries the pins into the environment file.

### The project's stage file

A project can add tools to the stage image (a compiler, a JDK, a browser) without changing the image for every project. It commits the file `<project>/factory/stage.Containerfile` to `main`. Every container of the instance (the sync, the agent and the checks) then runs in the image that file builds on top of the stage image.

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

The sizes are in GB of 10^9 bytes with two decimals, so 1 580 000 000 bytes give `1.58`. A size that cannot be read is written `unknown`, as `base unknown` or `layer unknown`. A project image that is smaller than its base also has `layer unknown`.

The warnings are the lines of the build's output that hold `WARN` or `warning`, in any case. The exception is apt's `update-alternatives: warning:` lines, which a slim base prints for every manual page it lacks. A count above zero is worth reading in the build output: npm's `EBADENGINE` is one. An image that is reused with no build gives the same two sizes to the cost records. The factory adopts such an image, and it writes no log line of a build.

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

The factory builds the file with `podman build --build-arg FACTORY_BASE=<the base image> --network=host` and an empty build context. It tags the result `<FACTORY_STAGE_IMAGE>-project`, for example `factory-stage:vm-project` for `factory-stage:vm`. Then it removes the images the build left without a tag. A build that takes more than 30 minutes fails.

Two things follow for the project. The build has the network, so it can download. It has no file of the repository, so a `COPY` finds nothing, and the layer is only as repeatable as its commands: pin the versions and check the checksums of what it downloads, as `operator/vm/Dockerfile` does. Debian packages installed by name take the version the release ships at the time of the build.

The layer must not break the stage image's tools. The runtimes live under `/opt/factory` and the image has no `node` or `npm` on the `PATH` for projects, so a project that installs its own Node does not change the runtimes.

#### The `PATH` and the identity

Every container takes the `PATH` that the image in use sets, as `podman image inspect` reads it from the image's configuration, and `/usr/local/bin:/usr/bin:/bin` when the image sets none. The sync and the checks get that `PATH`; the agent gets the folder of the factory's console scripts first and then the same `PATH`. So an `ENV PATH=/opt/jdk/bin:$PATH` in the stage file puts the JDK on the `PATH` of `make check` and of the agent. If the factory cannot read the image's configuration, it uses the default `PATH`.

The instance's image identity becomes the base's identity, a `+`, and the first 12 hex digits of the SHA-256 of the file, for example `<base identity>+20733148ba61`. The preflight's stamp and the reuse of a passed check key on it. So a changed file makes the preflight run its machine items again, the agent-run probe included, and confirms that the layer left the agent runtime working. It is also the image on the cost records (see *The image on the cost records*). The project image itself shows in `podman images` under the tag above.

#### The stop `stage_image_failed`

- **What you see:** `factory-health` shows the machine stop `stage_image_failed` (see *The stops* in [stops.md](stops.md)). The factory starts no stage and does not fall back to the base image. `factory-watch` shows no stop of any reason.
- **What it means:** the file broke the rule, or it did not build. The detail starts with `at <commit>: `, the first 12 hex digits of the `origin/main` that was tried. Then comes the rule's reason, or `the stage file did not build in <s> s:` and the last 20 lines of the build's output. A build that reached its time limit gives the same first words and podman's message that the build did not end within its limit, with no build output. The image in use stays the one before the failed build.
- **What you do:** read the detail and fix `<project>/factory/stage.Containerfile` on `main`.

A failed build waits for a new `main`. The same file again is not built again, so a commit that leaves the file as it is does not end the stop. The next `main` with another file ends the stop and the file is built. A `main` without the file ends it and returns to the base. A restart of `factory-run` builds the same file again. It ends the stop when that build passes, after a network fault for instance, and raises it again when it fails. In a job, a machine stop that has stood for ten minutes ends the execution (see *The idle shutdown*). The fix is then a new commit on `main` and a new execution.

### The image on the cost records

Every cost record names the image the agent run ran on. That is the identity from the file `FACTORY_IMAGE_ID_FILE` names, joined with the stage file's digest when the project has one (see *The project's stage file*). A record made when the instance has no image identity has none.

### The code and the project apart

Some projects live on a host of their own, such as a company's enterprise host, and run the factory's public code from a public repository. Give `--repository-url` the project and `--code-url` the code. Run this on the VM from your own account:

```sh
sudo sh operator/vm/setup.sh --device /dev/sdb \
  --repository-url https://git.company.example/team/project.git \
  --code-url https://github.com/pkrahmer/kumpel-factory.git
```

- **The code is cloned without a credential.** The clone of `/srv/factory/<instance>/factory` runs with `GIT_TERMINAL_PROMPT=0` and without `GIT_ASKPASS` and `core.askPass`. It runs after the wait for the secrets, in the same pass as the install of the helper and the unit. A code repository that asks for a credential fails the clone with exit status 1: `setup: checkout: cannot clone <url> without a credential; the code repository must be readable without a token`. A `--code-url` that equals `--repository-url`, or is absent, clones with the token.
- **`factory.env` holds the project only.** `FACTORY_REPOSITORY_URL` is `--repository-url`; the code url is written nowhere.
- **The project brings its own files.** The factory reads `<project>/factory/pipeline.yml`, `<project>/factory/story-form.md` and `<project>/factory/feature-form.md`, and optionally `<project>/factory/agents/`. Its `Makefile` has the targets `check`, `lint`, `test` and `sync`.
- **The stage image comes from the code.** `operator/vm/Dockerfile` is the one in the code checkout, not the project's.
- **An update of the code is a new ref and a rebuild.** Run `operator/vm/setup.sh` again with the new `--code-ref`, as *The rebuild after a merge* describes. A checkout that exists is not cloned again, so a changed `--code-url` alone changes nothing on a machine that has one.
- **The helper answers only the project's host.** With `FACTORY_REPOSITORY_URL` set, `git-credential-factory` gives the token only when git asks for the host of that URL. The token is never offered to the code repository's host or to any other. See *The hosting-service token* in [health.md](health.md).

### The script

[setup.sh](../../operator/vm/setup.sh) makes the machine from a fresh Ubuntu 24.04 with a spare disk and installs the service. It is POSIX `sh`, runs as root and does only what is missing, so a second run changes nothing. Run it on the VM from your own account, in the folder that holds your copy of the script:

```sh
sudo sh operator/vm/setup.sh --device /dev/sdb --repository-url https://github.com/<owner>/<repo>.git
```

| Name | What it does | Default | Example |
|---|---|---|---|
| `--device <path>` | The disk, or a file, the pool is made on. The script does not test it: a pool that exists is found whatever `--device` names. | required | `/dev/sdb` or `/var/lib/factory-pool.img` |
| `--repository-url <url>` | The repository the factory works on, and runs from when `--code-url` is not given. | required | `https://github.com/<owner>/<repo>.git` |
| `--code-url <url>` | The repository the factory's code and its stage image's [Dockerfile](../../operator/vm/Dockerfile) come from. When it differs from `--repository-url` it is cloned without any credential (see *The code and the project apart*). | the `--repository-url` | `https://github.com/pkrahmer/kumpel-factory.git` |
| `--instance <name>` | The instance's name. Its folder is `/srv/factory/<instance>`. | `vm` | `vm` |
| `--pool <name>` | The ZFS pool. | `tank` | `tank` |
| `--quota <size>` | The quota of the instance's dataset. | `30G` | `50G` |
| `--code-ref <git ref>` | The factory's git ref to check out. The name `--ref` is refused: the script prints `setup.sh: --ref is now --code-ref` and the usage, and exits 2 before any step runs. | `main` | `main` |
| `--image <tag>` | The stage image. | `factory-stage:<instance>` | `factory-stage:vm` |
| `--runtime claude\|opencode` | The agent runtime. | `claude` | `opencode` |
| `--sudoers` | Reach `zfs` through `sudo` (see *The `sudoers` fallback*). | off | `--sudoers` |
| `--idle-shutdown <minutes>` | Let the factory power the machine off after that many idle minutes: a whole number of ASCII digits, at least 1 (`0`, `x`, `-5`, `1.5` and an empty value are refused). Gives `factory` the power-off right (step 9) and adds `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>` to the environment file (step 14). See *The idle shutdown*. | off | `--idle-shutdown 30` |
| `--help` | Print the usage to standard output and exit 0. | none | `--help` |

The usage runs without root:

```console
$ sh operator/vm/setup.sh --help | head -n 1
usage: setup.sh --device <path> --repository-url <url> [--code-url <url>] [--instance <name>] [--pool <name>] [--quota <size>] [--code-ref <git ref>] [--image <tag>] [--runtime claude|opencode] [--sudoers] [--idle-shutdown <minutes>] [--help]
```

The refusal of the old name `--ref` prints the usage after its message and exits 2:

```console
$ sh operator/vm/setup.sh --ref main 2>&1 | head -n 1
setup.sh: --ref is now --code-ref
```

A missing required option, an option without its value, an `--idle-shutdown` value that is not a whole number of at least 1, an unknown word or a runtime other than the two prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2. When the user is not root it prints `setup.sh: run as root` and exits 2. Nothing is made or changed before either exit.

#### The steps

Each step prints one line, `setup: <step>: `, followed by what it changed (joined with `; `) or, when nothing needed doing, what it found, which says `found`. The steps run in this order:

1. `packages`: `apt-get update`, then `apt-get install -y --no-install-recommends` of the missing ones among `zfsutils-linux podman uidmap slirp4netns git make python3.12-venv`.
2. `pool`: `zpool create -o ashift=12 -O compression=lz4 -O atime=off <pool> <device>`, unless `<pool>` exists.
3. `user`: the user `factory` with a home and `/bin/bash`, unless it exists. `/etc/subuid` and `/etc/subgid` must each hold a `factory:` line; the script does not make one. Without it, it prints `setup: user: no subuid and subgid range for factory; add one with usermod --add-subuids and --add-subgids` to standard error and exits 1. Add the ranges and run the script again.
4. `linger`: `loginctl enable-linger factory`, so rootless Podman and the user's runtime folder outlive a login.
5. `datasets`: `<pool>/factory` and `<pool>/factory/<instance>`, both with `compression=lz4` and `atime=off`, the second mounted at `/srv/factory/<instance>/work` with the quota and owned by `factory`. Then the first base `<pool>/factory/<instance>@base` is taken, while the dataset is still empty and before the delegation of step 6. A dataset that already has a base keeps it, and the script never touches it. A dataset that exists without a base gets one.
6. `delegation`: `zfs allow -u factory snapshot,destroy,rollback,diff,mount` on the instance's dataset, unless all five are already delegated.
7. `sudoers`: only with `--sudoers`, see below. Without it the line says `not asked` and neither file is touched.
8. `caches`: on every run, with or without `--sudoers`, the helper `/usr/local/bin/factory-drop-caches` (it runs `sync`, then writes `1` to `/proc/sys/vm/drop_caches`) and `/etc/sudoers.d/factory-drop-caches`, which holds the one rule `factory ALL=(root) NOPASSWD: /usr/local/bin/factory-drop-caches`. The helper has mode `0755` and the rule file `0440`. Each is written only when its text differs. The rule is checked with `visudo -cf`. If `visudo` refuses it, the script removes the file, prints `setup: caches: visudo -cf refused /etc/sudoers.d/factory-drop-caches; removed it` to standard error and exits 1. See *The page cache after a rollback*.
9. `poweroff`: with `--idle-shutdown`, `/etc/sudoers.d/factory-poweroff`, which holds the one rule `factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff`. The file has mode `0440` and owner root. It is written only when its text differs, and checked with `visudo -cf`. If `visudo` refuses it, the script removes the file, prints `setup: poweroff: visudo -cf refused /etc/sudoers.d/factory-poweroff; removed it` to standard error and exits 1. Without the option it runs `rm -f` on that file, so a right an earlier run gave is taken back, and the line says `setup: poweroff: not asked; the factory gets no power-off right`. See *The idle shutdown*.
10. `folders`: `/srv/factory/<instance>` with `state` and `repo`, owned by `factory` with mode `0755`, and `/home/factory/.secrets` with mode `0700`. If `state`, `repo` or `/home/factory/.secrets` is a link, the script prints `setup: folders: ...` to standard error and exits 1 before it makes anything in the step: remove the link and run it again. The script sets the secrets folder's owner and mode and never touches a file in it: the secrets you placed stay as they are on every run.
11. `image-id`: `/srv/factory/<instance>/image-id`, a fresh uuid (mode `0644`) when the file is missing or empty. A rebuilt image needs a new id; renew the file yourself (see *The stage image*).
12. `checkout`: the factory at `--code-ref`, cloned as `factory` into `/srv/factory/<instance>/factory`, unless it holds a `.git`.
13. `tools`: a virtual environment `/srv/factory/<instance>/tools` with `uv` installed from `pip` at the version of `ARG UV_VERSION` in the checkout's `operator/vm/Dockerfile`. Then `uv sync --frozen --no-dev` in the checkout makes the factory's own `.venv`. Last, `/usr/local/bin/git-credential-factory` is copied from the checkout's [git-credential-factory](../../operator/vm/git-credential-factory) (see *The two passes*). `uv sync` runs on every run and changes nothing when the environment matches the lockfile.
14. `environment`: `/srv/factory/<instance>/factory.env` (mode `0644`). With `--idle-shutdown` its last line is `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`; without the option the file holds no such line, so a run without it takes the setting back. It always holds `FACTORY_TRANSCRIPT_DIR=/srv/factory/<instance>/transcripts` before that line.
15. `service`: the unit `operator/vm/factory.service` as `/etc/systemd/system/factory@.service` (mode `0644`; see *The two passes*), `systemctl daemon-reload`, and `systemctl enable factory@<instance>`. The service is enabled, not started.
16. `transcripts`: the folder `/srv/factory/<instance>/transcripts` (owner `factory`, mode `0700`), made only when it is not already so. If the folder is a link, the script prints `setup: transcripts: <path> is a link; remove it and run this script again` to standard error and exits 1, before it makes anything there. The script writes no `tmpfiles.d` rule and has no option for an age. See *Transcripts* in [health.md](health.md).

The script writes the files under `/srv/factory/<instance>` (`image-id`, the askpass script and `factory.env`) as `factory`, with `cat` from its own standard input, because a process started by `runuser` may not reopen root's `/dev/stdin`.

The script ends with `setup: done: build the stage image and start factory@<instance>; see "The machine" in docs/operator-guide/machine.md`.

#### The two passes

The checkout of the private repository needs the hosting token. When `/home/factory/.secrets/hosting-token` is not there at step 12, the script prints `setup: checkout: waiting for /home/factory/.secrets/hosting-token; place the secrets and run this script again` and exits 0. Place all three files, `hosting-token`, `claude-token` and `anthropic-api-key`, in `/home/factory/.secrets`, readable by `factory`, and run the same command again: steps 1 to 11 report `found` and the rest completes. All three must exist whatever the runtime; with the `claude` runtime the key file stays empty.

The token is written into no file. Git asks the askpass script (`/srv/factory/<instance>/askpass`) for it, and only that script reads the token file; the clone sets `core.askPass` on its own command line, not in any git configuration.

The unit and the credential helper come from the checkout. Root installs them only in the run that made the clone, whose content is the remote's at `--code-ref`, or when the installed file is missing. So a first run that stopped after the clone is completed by the next. A later run finds the installed file in place but different from the checkout. It installs nothing and prints one of these two lines to standard error:

```text
setup: tools: /usr/local/bin/git-credential-factory differs from the checkout; not installed; install it from your own copy of operator/vm/git-credential-factory (docs/operator-guide/machine.md, "The rebuild after a merge")
setup: service: /etc/systemd/system/factory@.service differs from the checkout; not installed; install it from your own copy of operator/vm/factory.service (docs/operator-guide/machine.md, "The rebuild after a merge")
```

Root installs nothing from the checkout, because `factory` can write it. Your own copy of the ref is the trusted text. So install the new file yourself, from your copy, before you run the script again.

1. On your own computer, in your checkout of the ref the instance runs, copy the script and both files to the VM:

   ```sh
   gcloud compute scp --zone=europe-west3-a --tunnel-through-iap operator/vm/setup.sh operator/vm/factory.service operator/vm/git-credential-factory factory-vm:
   ```

2. On the VM from your own account, install the file the script named:

   ```sh
   sudo install -m 0644 factory.service /etc/systemd/system/factory@.service
   sudo install -m 0755 git-credential-factory /usr/local/bin/git-credential-factory
   ```

3. Run the script as *The rebuild after a merge* describes. It runs `systemctl daemon-reload` and reports the file found.

#### The environment file

Every run rewrites `factory.env` from the arguments and from the pins in the checkout's `operator/vm/Dockerfile` (the Claude Code and opencode versions and the opencode model ids), and writes it only when its text differs. A change therefore goes into the script's arguments (or the Dockerfile), never into the file: an edit by hand is lost at the next run.

For values the script does not know (a model map for a company's proxy, the path of a provider file, the names of the proxy variables), make a second file, `/srv/factory/<instance>/factory.local.env`, in the same `NAME=value` form. The unit reads it after `factory.env`, so a value in it wins over the same name there. It is optional: without it the unit reads `factory.env` alone. The script never creates, changes or removes it, and says so in its last line (`setup: local: ...`). Restart the instance after a change: the factory reads its environment when it starts.

Every name in `factory.local.env` is in the factory process's own environment, because the unit sets it for the whole service. `FACTORY_CONTAINER_ENV` then chooses which of these names the containers also get.

#### The page cache after a rollback

A page that a stage wrote through `mmap` survives `zfs rollback` in the kernel's page cache. After the rollback the file has the snapshot's size but may still read the newer page: a file the stage made shorter reads as zero bytes past its end, and git's stat cache calls it clean, so the sync does not repair it. The factory therefore drops the clean page cache after every reset, right after a rollback that succeeded, by running `sudo -n /usr/local/bin/factory-drop-caches`. This is not a setting and does not depend on `--sudoers` or `FACTORY_ZFS`: step 8 installs the helper and its `sudoers` rule on every run.

The drop is machine-wide. It also empties the cache of other files, so the next sync reads from the disk and is a little slower. A drop can fail for three reasons: there is no helper, there is no rule so that `sudo` asks for a password, or the time limit of ten minutes passes. The stage then does not start, as with a failed `zfs` command. The factory log names the command that failed. A machine set up by hand with the same two files is found unchanged by step 8.

#### The `sudoers` fallback

The delegation of step 6 is the way for the factory to reach `zfs`. When it does not suffice on your machine, run the script with `--sudoers`. Step 7 then writes `/etc/sudoers.d/factory-zfs` (mode `0440`). The file lets `factory` run exactly `zfs snapshot`, `zfs destroy`, `zfs rollback -r` and `zfs diff -FH`, each on `<dataset>@base` alone, as root without a password. The script checks it with `visudo -cf`. If `visudo` refuses it, the script removes the file, prints the refusal to standard error and exits 1.

Step 7 also writes `/usr/local/bin/zfs-factory` (mode `0755`). This wrapper runs those four commands through `sudo -n /usr/sbin/zfs` and every other command as itself. The environment file then holds `FACTORY_ZFS=/usr/local/bin/zfs-factory`.

The rule names `diff -FH` because the factory runs `zfs diff` with those flags and `sudoers` matches the whole argument list; a rule for `diff -H` would not match.

### The service

The unit [factory.service](../../operator/vm/factory.service) is a systemd template, installed as `factory@.service`. The text after the `@` is the instance, so the default instance is `factory@vm`. The unit runs as `factory`, with `/srv/factory/%i` as its working directory. It reads `/srv/factory/%i/factory.env` and then, if it exists, `/srv/factory/%i/factory.local.env` (see *The environment file*). It starts `/srv/factory/%i/factory/.venv/bin/factory-run`. `Restart=always` with `RestartSec=15` restarts it fifteen seconds after any exit.

On the VM from your own account, the first command starts the instance, and `stop`, `restart` and `status` work the same way. The second shows the process's output. The third asks `factory-health` as `factory`:

```sh
sudo systemctl start factory@vm
sudo journalctl -u factory@vm        # the process's output
sudo -u factory /srv/factory/vm/factory/.venv/bin/factory-health --state-directory /srv/factory/vm/state
```

Nothing runs a health check by itself: ask `factory-health` as `factory`. Build the stage image before the first start (see *The stage image*).

The environment file holds these variables. *Configuration* in [install.md](install.md) explains the settings in full. The default is the value the script writes:

| Name | What it does | Default | Example |
|---|---|---|---|
| `FACTORY_INSTANCE` | The instance's name. | `--instance` | `vm` |
| `FACTORY_REPOSITORY_URL` | The repository the factory works on. | `--repository-url` | `https://github.com/<owner>/<repo>.git` |
| `FACTORY_AGENT_RUNTIME` | The agent runtime. | `--runtime` | `claude` |
| `FACTORY_DATASET` | The ZFS dataset of the instance. | `<pool>/factory/<instance>` | `tank/factory/vm` |
| `FACTORY_WORKSPACE` | Where the dataset is mounted on the host. | `/srv/factory/<instance>/work` | `/srv/factory/vm/work` |
| `FACTORY_STAGE_IMAGE` | The stage image. | `--image` | `factory-stage:vm` |
| `FACTORY_ZFS` | The command that reaches `zfs`. | `zfs`, or `/usr/local/bin/zfs-factory` with `--sudoers` | `zfs` |
| `FACTORY_CHECKOUT` | The factory's own clone of the project. | `/srv/factory/<instance>/repo` | `/srv/factory/vm/repo` |
| `FACTORY_STATE` | The state directory. | `/srv/factory/<instance>/state` | `/srv/factory/vm/state` |
| `FACTORY_IMAGE_ID_FILE` | The file that holds the identity of the stage image. | `/srv/factory/<instance>/image-id` | `/srv/factory/vm/image-id` |
| `FACTORY_CLAUDE_HOME` | The folder of the agent files. | `/srv/factory/<instance>/factory/agents` | `/srv/factory/vm/factory/agents` |
| `FACTORY_TOKEN_FILE` | The hosting token's file. | `/home/factory/.secrets/hosting-token` | `/home/factory/.secrets/hosting-token` |
| `FACTORY_CLAUDE_LOGIN_FILE` | The login file of the `claude` runtime. | `/home/factory/.secrets/claude-token` | `/home/factory/.secrets/claude-token` |
| `FACTORY_API_LOGIN_FILE` | The API key file. | `/home/factory/.secrets/anthropic-api-key` | `/home/factory/.secrets/anthropic-api-key` |
| `FACTORY_CLAUDE_VERSION`, `FACTORY_OPENCODE_VERSION`, `FACTORY_OPENCODE_MODELS` | The versions and model ids the preflight compares with the image. | the pins of `operator/vm/Dockerfile` | the pins of `operator/vm/Dockerfile` |
| `PATH` | The service's `PATH`. `/usr/sbin` holds `zfs`. | `/srv/factory/<instance>/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin` | the default |
| `XDG_RUNTIME_DIR` | Where rootless Podman finds its runtime folder. | `/run/user/<uid of factory>` | `/run/user/1001` |
| `FACTORY_TRANSCRIPT_DIR` | Where the transcripts are kept. | `/srv/factory/<instance>/transcripts` | `/srv/factory/vm/transcripts` |
| `FACTORY_IDLE_SHUTDOWN_MINUTES` | The idle stretch after which the machine powers off. | `--idle-shutdown`, only when it is given | `30` |

### On GCP, step by step

This is the machine of the recommended setup: instance `vm`, an `e2-standard-2` in `europe-west3`, no inbound port, no service account, a budget alert of $120 a month. Steps 1 to 5 run on your own computer with `gcloud` signed in; replace `<project-id>` and `<account-id>`. Never paste a token or key into a chat or an agent's prompt; make each secret file by hand.

1. Create the project and the budget first, so that the alert exists before any cost does:

   ```sh
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

   ```sh
   gcloud compute routers create factory-router --network=default --region=europe-west3
   gcloud compute routers nats create factory-nat --router=factory-router --region=europe-west3 \
     --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
   ```

3. Open SSH for IAP's range only. Nothing else is open to the internet.

   ```sh
   gcloud compute firewall-rules create allow-iap-ssh --network=default --direction=INGRESS \
     --allow=tcp:22 --source-ranges=35.235.240.0/20
   ```

4. Create the data disk. It holds the ZFS pool and survives the VM (`auto-delete=no` in the next step).

   ```sh
   gcloud compute disks create factory-data --size=50GB --type=pd-balanced --zone=europe-west3-a
   ```

5. Create the VM from Ubuntu 24.04, with no service account and no external address, and the disk attached under the device name `factory-data`:

   ```sh
   gcloud compute instances create factory-vm --zone=europe-west3-a --machine-type=e2-standard-2 \
     --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud --boot-disk-size=20GB \
     --no-service-account --no-scopes --no-address \
     --disk=name=factory-data,device-name=factory-data,mode=rw,auto-delete=no
   ```

6. On your own computer, copy the script to the VM through the tunnel, and open a shell there. Copy it from a checkout of the ref you will run.

   ```sh
   gcloud compute scp --zone=europe-west3-a --tunnel-through-iap operator/vm/setup.sh factory-vm:
   gcloud compute ssh factory-vm --zone=europe-west3-a --tunnel-through-iap
   ```

   The script is `operator/vm/setup.sh`.

7. On the VM, run the script as root, the first time. The disk is `/dev/disk/by-id/google-factory-data` (`ls -l /dev/disk/by-id/ | grep google` shows it). `--code-ref` is the tag or branch to run.

   ```sh
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/kumpel-factory.git --code-ref <the tag or branch to run>
   ```

   It installs the packages and makes the pool, the user `factory`, the datasets, the delegation and the folders. Then it stops with `setup: checkout: waiting for /home/factory/.secrets/hosting-token` and exit status 0: the private repository needs the token (see *The two passes*).

8. Place the three secrets by hand, from your own account on the VM, one file each: `hosting-token` (the GitHub token), `claude-token` (the output of `claude setup-token`) and `anthropic-api-key`. Make each file in your home folder with an editor, install it, and remove the copy:

   ```sh
   sudo install -m 0600 -o factory -g factory hosting-token /home/factory/.secrets/hosting-token
   sudo install -m 0600 -o factory -g factory claude-token /home/factory/.secrets/claude-token
   sudo install -m 0600 -o factory -g factory anthropic-api-key /home/factory/.secrets/anthropic-api-key
   shred -u hosting-token claude-token anthropic-api-key
   ```

   All three files must exist, whatever the runtime is. The factory mounts every login file the environment file names, and podman refuses to mount a missing one. Every agent run would then stop with exit status 125. Under `claude` the file `anthropic-api-key` may be empty, which means no key. Under `opencode` the file `claude-token` may be empty, since opencode does not read it, and `anthropic-api-key` holds the key.

9. On the VM from your own account, run the script a second time with the same arguments. It clones the factory, installs the tools, writes the environment file and installs and enables the unit.

   ```sh
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/kumpel-factory.git --code-ref <the tag or branch to run>
   ```

10. On the VM as `factory`, build the stage image from the checkout the script made. `<ref>` labels the image; any text will do.

    ```sh
    sudo -iu factory
    cd /srv/factory/vm/factory
    podman build -f operator/vm/Dockerfile -t factory-stage:vm --build-arg FACTORY_IMAGE=<ref> /srv/factory/vm/factory
    exit
    ```

11. On the VM from your own account, start the instance. Then, as `factory`, look at it:

    ```sh
    sudo systemctl start factory@vm
    sudo -iu factory
    set -a; . /srv/factory/vm/factory.env; set +a
    /srv/factory/vm/factory/.venv/bin/factory-watch
    /srv/factory/vm/factory/.venv/bin/factory-health --state-directory /srv/factory/vm/state
    ```

    `factory-watch` shows the board and what the next tick would do. `factory-health` prints `healthy` or one line per stop in force. The console scripts live in the factory's virtual environment, which the environment file's `PATH` does not name, so the full path is needed. The environment file is loaded so that `factory-watch` reads the instance's settings.

12. When the machine is not used, stop the instance first and then the VM. A VM stop during a stage ends the factory after systemd's stop timeout of 90 seconds, and the next start counts that stage as a crash (see *The rebuild after a merge*). So wait until no work item is held by `vm`: on the VM as `factory`, run `factory-watch` as in step 11 and look at the board. Then, on the VM from your own account (leave the `factory` shell with `exit`), stop the instance:

    ```sh
    sudo systemctl stop factory@vm
    ```

    Then, on your own computer, stop the VM:

    ```sh
    gcloud compute instances stop factory-vm --zone=europe-west3-a
    ```

    A stopped VM costs only its disks and NAT (see *The costs*). The service is enabled and comes up with the VM, because `systemctl stop` does not disable it. Start the VM again as *Starting the machine again* describes.

### On any Ubuntu 24.04 VM

A Hyper-V VM at home or a VM on TrueNAS SCALE does as well as GCP. Take the steps of *On GCP, step by step* from step 6 on, without `gcloud`: copy `operator/vm/setup.sh` to the VM, run it as root with `--device` naming a spare disk (or a file such as `/var/lib/factory-pool.img`), place the three secrets, run the script again, build the image, start the service.

The script needs:

- a Linux kernel with the ZFS module (Ubuntu 24.04's ships it signed; the script installs `zfsutils-linux`);
- a spare block device for the pool;
- rootless Podman, with a `factory:` range in `/etc/subuid` and `/etc/subgid` (Ubuntu's `useradd` adds one);
- outbound network for apt, npm, GitHub and the Anthropic API.

`podman machine`, WSL 2 and the workplace's Podman Desktop are not hosts for it: they give no kernel with ZFS and no rootless Podman on a real Linux host. Run the instance on a Linux VM instead.

### What the container can and cannot see

A stage container sees:

- the dataset at `/work`: the checkout and the agent's home (`HOME=/work/home`). It may write anywhere there; the take copies only what the role may write, and the next stage starts from the base again;
- read-only mounts: in the sync container the host repository's `.git` at `/upstream` (the sync fetches from it, because the container has no credentials), and in the agent's container the login file and the instructions file at their paths. A rootless container cannot write a read-only mount;
- the network: the Anthropic API, npm and GitHub through NAT.

It does not see the hosting token, because only the host reads it and the host alone pushes. It does not see the host's files outside its mounts, the next stage, or anything of the metadata server worth having (see *The metadata server*). Every container runs with `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g`. It runs with `--userns=keep-id`, so the files it writes belong to `factory` on the host. `--timeout` is set to the step's time limit.

### The costs

The numbers are estimates in US dollars for `europe-west3`:

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
- `/srv/factory/vm/state/factory.log`: the factory log (see *The factory log* in [health.md](health.md)). After every stage it holds a line `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`. The time from the start of a stage to the agent's first step (the target is under 20 s with a warm base, the reset under 2 s) is `reset` plus `sync` plus `advance`; `take` is the copy back.
- `health.json` in the state directory, through `factory-health --state-directory /srv/factory/vm/state`.
- `sudo -iu factory podman ps`: a stage container that is running now. Containers run with `--rm`, so a finished one leaves nothing to look at.

### The idle shutdown

A VM costs money for every hour it runs, also while the factory has nothing to do. With `FACTORY_IDLE_SHUTDOWN_MINUTES` set to a whole number above 0, the factory powers the machine off after an idle stretch of that many minutes. Unset, blank or `0` leaves it off, and then none of this runs.

**What is idle.** A tick is idle when it ran, ended at no stop and handled the event `idle`. That holds when nothing can be started. It holds when the first waiting work item waits for the human, for an approval or a question the factory posted. It holds when another instance holds a claim. A story that waits overnight for your merge therefore counts as idle, which is the cost the option saves. A tick that ended at a stop is not idle. A tick that handled any other event is not idle either, whether a run, a comment, a merge, a crash or an error. Both start the stretch again. A stop waits for a fix you may make on the machine, so on a VM the machine stays up while one stands. In a job, see *In a job* below. An iteration that ran no tick neither counts nor ends the stretch. That happens when the checkout could not be prepared. The first stretch starts when the instance starts.

**The two log lines.** Both go to the factory log (`factory.log` in the state directory) and both begin `idle shutdown: `:

- `idle shutdown: idle for <n> minutes, powering the machine off` is written right after the idle tick that ends a stretch of at least the limit, just before the factory asks the machine to power off.
- `idle shutdown: power off failed: <detail>; the factory runs on` follows it when the machine refused or could not be asked.

**A refused power-off.** The factory runs `sudo -n /usr/bin/systemctl poweroff`, the one command it needs. Four things refuse it: `factory` has no right to the command, `sudo` is missing, the call reaches its time limit of one minute, or the instance does not run on the VM. The second line then holds the last line `sudo` printed, for example `sudo: a password is required`, or `exit status <n>`. It is not a stop. The instance runs on, starts a new stretch, and asks again only after another full limit. Read the line as the next step shows. No preflight item checks the right.

**In a job.** A Cloud Run job has no `systemctl` and no `sudo`, so `poweroff` would only be refused and the job billed until its task timeout. With `FACTORY_IDLE_SHUTDOWN_ACTION=exit` the factory, after the idle tick that ends the stretch, stops its own loop the way a `SIGTERM` does: the tick in progress is the last, and `factory-run` ends with status 0, which ends the job's execution. The job's schedule starts it again, or you do (`gcloud run jobs execute <job>`), as you start a stopped VM. The log line says what happens, `idle shutdown: idle for <n> minutes, ending the factory's process`; with `poweroff` it is `idle shutdown: idle for <n> minutes, powering the machine off`. The idle rule and `FACTORY_IDLE_SHUTDOWN_MINUTES` work as on a VM (`0` is off). A VM keeps `poweroff`.

**A machine stop in a job.** On a VM a machine stop waits for a fix you make on the machine; in a job nobody can, because its file system is gone with the execution and the only fix is a new execution with other settings. So with the idle shutdown on and the action `exit`, a machine stop that has stood for ten minutes ends the process. `factory-run` ends with status 1 and the execution ends as failed. The last line of the job's log names the stop, `machine stop: standing for 10 minutes in a job, ending the factory's process: <reason>: <detail>`. The ten minutes are fixed. They count from the first time of an unbroken stretch of the stop, though the preflight raises it again on every tick. A stop lifted before then ends nothing, and a new one counts from its own time. The rule is checked after every tick and after every iteration that ran no tick. It holds for no stop of scope `repository`, because a push to `main` lifts those and a job can see it. It does not hold with `poweroff` or with the idle shutdown off.

**The right.** The setup script gives `factory` the right to that one command, and sets the variable in the environment file, with its option `--idle-shutdown <minutes>`: step `poweroff` writes `/etc/sudoers.d/factory-poweroff`, step `environment` the line `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`, both from the same run. Without the right, set the variable only if you accept the second log line above.

**Turning it on and off.**

1. To turn it on, or to change the minutes, run your copy of `setup.sh` on the VM from your own account. Give it the arguments of the first run and add the option, as step 5 of *The rebuild after a merge* does:

   ```sh
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/kumpel-factory.git --code-ref <the same ref> --idle-shutdown 30
   ```

2. Restart the service so that it reads the new environment file:

   ```sh
   sudo systemctl restart factory@vm
   ```

3. To see whether the right works, read the log lines of the idle shutdown on the VM from your own account:

   ```sh
   grep 'idle shutdown' /srv/factory/vm/state/factory.log
   ```

To turn it off, run the script again with the arguments of the first run and without the option, and restart the same way. It removes `/etc/sudoers.d/factory-poweroff` and the line in the environment file. The script never starts or stops the service and never powers the machine off itself.

**Starting the machine again.** Starting is outside the factory. By hand, on your own computer with `gcloud`:

```sh
gcloud compute instances start factory-vm --zone europe-west3-a
```

Or let a GCP instance schedule start it at the hours you work. Make the schedule by hand with `gcloud compute resource-policies create instance-schedule` and attach it with `gcloud compute instances add-resource-policies`; give it a start time only, so that the factory's own power-off is the only thing that stops the VM. The service is enabled and comes up with the machine. A merge, a close or an answer you gave while the VM was off is seen at the first tick after the start.

### The rebuild after a merge

The instance runs the factory's code from `/srv/factory/vm/factory` and the stage image built from it. After a merge to the ref it runs, stop the instance between two stages, bring both up to date, and start it again.

An agent run lasts up to its role's `time_limit`, so a running instance may be in the middle of a stage. A stop during a stage ends the factory after systemd's stop timeout of 90 seconds, and the restart counts that stage as a crash (see *A restart during a stage* in [work-items.md](work-items.md)).

1. Wait until no work item is held by `vm`. On the VM as `factory`, run `factory-watch` as in step 11 of *On GCP, step by step* and look at the board.

2. On the VM from your own account, stop the instance:

   ```sh
   sudo systemctl stop factory@vm
   ```

   The stop also ends the instance's running agent and check containers. The unit runs `podman stop --filter label=factory.instance=%i` as `factory` after every end of `factory-run`, a stop or a crash. Every container the factory starts carries that label, so containers of another instance, or without the label, are left alone. The next start takes a cut-off stage up again.

   If your machine has a unit that does not stop containers, install the current one by hand: copy [factory.service](../../operator/vm/factory.service) from your checkout to the VM, then install it as steps 1 and 2 of *The two passes* describe. The script prints that the file differs and leaves it.

3. Bring the checkout and the image up to date. On the VM as `factory` (`sudo -iu factory`):

   ```sh
   git -C /srv/factory/vm/factory pull --ff-only          # for a tagged ref: git fetch --tags, then git checkout <tag>
   cd /srv/factory/vm/factory
   /srv/factory/vm/tools/bin/uv sync --frozen --no-dev
   podman build -f operator/vm/Dockerfile -t factory-stage:vm --build-arg FACTORY_IMAGE=<ref> /srv/factory/vm/factory
   podman image prune -f
   cat /proc/sys/kernel/random/uuid > /srv/factory/vm/image-id
   exit
   ```

   `podman image prune -f` removes the previous stage image, which the build left untagged, and the build's leftovers. It removes only untagged images that no container uses, so another instance's tagged image and a running container are safe. Without it every rebuild leaves an image behind in the factory's storage. The prune also removes the intermediate images that the build's layer cache would reuse, so the next build is slower without the cache.

   The new uuid in `image-id` tells the settings that the image is new. The label is not its identity.

4. Copy the setup script from your own checkout of the ref the instance runs, and open a shell on the VM. Root runs nothing from `/srv/factory/vm/factory`, because `factory` can write that checkout. On your own computer:

   ```sh
   gcloud compute scp --zone=europe-west3-a --tunnel-through-iap operator/vm/setup.sh operator/vm/factory.service operator/vm/git-credential-factory factory-vm:
   gcloud compute ssh factory-vm --zone=europe-west3-a --tunnel-through-iap
   ```

   The two other files are for the case that the script reports a difference. On a VM outside GCP, copy the three files by your own means, such as `scp`, as *On any Ubuntu 24.04 VM* does.

5. On the VM from your own account, run the script with the arguments of the first run, and start the instance:

   ```sh
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/kumpel-factory.git --code-ref <the same ref>
   sudo systemctl start factory@vm
   ```

The script is idempotent, so run it after every merge. It carries a changed pin of the Dockerfile into the environment file, updates `uv` and the factory's virtual environment, and reports the rest found. It does not replace an installed `/etc/systemd/system/factory@.service` or `/usr/local/bin/git-credential-factory` that differs from the checkout. It prints that the file differs and leaves it. When a merge changed `factory.service` or `git-credential-factory`, install it from your own copy with the commands of *The two passes* before you run the script.
