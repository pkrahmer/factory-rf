# Installing and running an instance

A topic of the [operator guide](README.md). It takes you from an empty machine to a running [instance](../project-guide/glossary.md): you install the factory, set the instance's environment variables, and learn what the process does when it starts, when it refuses to start and when it has nothing to do. The last parts say what the project must offer for the factory to build it.

An instance runs one project. It is told what it needs through environment variables. Words in this guide that the factory gave its own meaning, such as [stage](../project-guide/glossary.md), [stop](../project-guide/glossary.md) and [tick](../project-guide/glossary.md), are explained in the [glossary](../project-guide/glossary.md).

## Install

Install the factory on a repository that holds no work items from an older version of the factory, or whose old work items are archived or discarded. The factory starts fresh and does not detect old work items.

1. Install the factory's packages:

       uv sync

2. Check the installation. The last line must be `check: green`:

       make check

3. Prepare the machine. `operator/vm/setup.sh` is the way to run an instance: it makes the VM, installs the factory and its service, and builds the stage image, which carries the agent runtime and the pinned tools. See "The machine" in [machine.md](machine.md).

4. Set the instance's environment variables, as *Configuration* describes. On the VM, `operator/vm/setup.sh` writes most of them to the environment file `factory.env`.

5. Start the instance with `factory-run`. It reads the same environment as `factory-watch`. If it refuses, see "When the process refuses to start".

## Configuration

The tables below list every variable the factory reads. A variable that is unset or holds only spaces counts as unset, and takes its default. A variable that is required and unset is refused (see *The refusals*).

Every path is absolute. The examples below are from the VM that `operator/vm/setup.sh` makes, where `<instance>` is the instance's name.

The factory reports the first fault it finds, in this order: the repository, the instance, `FACTORY_CHECKOUT`, `FACTORY_STATE`, the image identity file, the faults of `FACTORY_WORKSPACE`, then the other variables.

### The instance

| Name | What it does | Default | Example |
|---|---|---|---|
| `FACTORY_REPOSITORY_URL` | Required. The one repository of the instance. It holds no whitespace and no comma, so a list of repositories is refused. The forms `https://host/owner/name`, `ssh://git@host/owner/name` and `git@host:owner/name` work, each with an optional `.git`. | none | `https://github.com/owner/project.git` |
| `FACTORY_INSTANCE` | Required. The instance's name. It starts with a lower-case letter and holds only lower-case letters, digits and hyphens. `Factory-1`, `1st`, `factory_1` and `-x` are refused. | none | `factory-1` |
| `FACTORY_CHECKOUT` | The factory's own checkout of the repository. | `/work/checkout` | `/srv/factory/<instance>/repo` |
| `FACTORY_STATE` | The state directory: `health.json`, the factory log and the runs. `factory-health --state-directory <it>` reads the same place. | `/state` | `/srv/factory/<instance>/state` |
| `GIT_USER_NAME` | The name of the factory's commits. | `factory` | `factory` |
| `GIT_USER_EMAIL` | The email of the factory's commits. | `factory@noreply.invalid` | `factory@noreply.invalid` |
| `FACTORY_MIN_FREE_GB` | The least free space, in whole gigabytes of 10^9 bytes, at least 1. When the work directory (the checkout's parent) or the state directory has less, the tick stops with `disk_low` (see "The stops of the tick" in [stops.md](stops.md)). | `5` | `10` |
| `FACTORY_TRANSCRIPT_DIR` | The folder that keeps each agent run's transcript (see "Transcripts" in [health.md](health.md)). It lies outside the workspace, the checkout, the state directory and the agent home. Unset keeps no transcript, and is no fault. | none | `/srv/factory/<instance>/transcripts` |

The two commit-identity variables are decided one by one: a half that is unset falls back to its own default. No preflight item checks the identity.

### The logins and the token

| Name | What it does | Default | Example |
|---|---|---|---|
| `FACTORY_TOKEN_FILE` | The file that holds the hosting-service token. It is needed for `factory-run` to build its boundaries. See "The hosting-service token" in [health.md](health.md). | none | `/home/factory/.secrets/hosting-token` |
| `FACTORY_CLAUDE_LOGIN_FILE` | The file that holds the agent's login token, made with `claude setup-token`, as plain ASCII text. See "The agent runtime" in [agent-runtime.md](agent-runtime.md). | none | `/home/factory/.secrets/claude-token` |
| `FACTORY_API_LOGIN_FILE` | The file that holds the agent's Anthropic API key, as plain ASCII text. A key in it wins over the token. | none | `/home/factory/.secrets/anthropic-api-key` |
| `FACTORY_IMAGE_ID_FILE` | Required for `factory-run` and `factory-watch`. The file that holds the identity of the stage image the instance runs on. Renew it after every build of the image (see "The stage image" and "The rebuild after a merge" in [machine.md](machine.md)). | none | `/srv/factory/<instance>/image-id` |

### The agent runtime

| Name | What it does | Default | Example |
|---|---|---|---|
| `FACTORY_AGENT_RUNTIME` | The agent runtime of the instance: `claude` (Claude Code) or `opencode`. Surrounding spaces are stripped. See "Running on opencode" in [agent-runtime.md](agent-runtime.md). | `claude` | `opencode` |
| `FACTORY_CLAUDE_HOME` | Required. The directory where the agents are installed, as `<it>/agents/<role>.md`. `HOME` is not read. | none | `/srv/factory/<instance>/factory/agents` |
| `FACTORY_CLAUDE` | Claude Code's executable, used when the runtime is `claude`. | `claude` | `claude` |
| `FACTORY_CLAUDE_VERSION` | The version of Claude Code that the stage image pins. The preflight fails without it under Claude Code. `factory.env` sets it from the pins of `operator/vm/Dockerfile`. | none | `2.1.318` |
| `FACTORY_OPENCODE` | The opencode executable, used when the runtime is `opencode`. | `opencode` | `opencode` |
| `FACTORY_OPENCODE_VERSION` | The version of opencode that the stage image pins. The preflight fails without it under opencode. `factory.env` sets it from the pins of `operator/vm/Dockerfile`. | none | `1.19.5` |
| `FACTORY_OPENCODE_MODELS` | Comma-separated entries `<alias>=<provider>/<model>` that map the agent files' aliases (`opus`, `sonnet`, `haiku`) to opencode's model ids. Spaces around each part are stripped. The provider is the part before the first `/`, so `openrouter/anthropic/claude-opus-5-5` is one model. `factory.env` sets the three Anthropic ids from `operator/vm/Dockerfile`. | none | `opus=anthropic/claude-opus-5-5` |
| `FACTORY_OPENCODE_PROVIDER_FILE` | The path of a JSON file that describes a company's own OpenAI-compatible provider and the small model. The opencode runtime merges it into the configuration of every run. The file is read at the start of every run, so a new file applies from the next run, without a restart. A fault in it, or a missing file, ends that run with `cannot use the opencode provider file <path>: <reason>`. See "A company's provider" in [agent-runtime.md](agent-runtime.md). | none | `/srv/factory/<instance>/provider.json` |

### A provider's spend limit

See "A provider's spend limit" in [agent-runtime.md](agent-runtime.md) for what the factory does with these.

| Name | What it does | Default | Example |
|---|---|---|---|
| `FACTORY_PROVIDER_LIMIT_STATUS` | The HTTP status a provider answers with when its spend limit is reached: ASCII digits from 100 to 599. | `428` | `429` |
| `FACTORY_PROVIDER_LIMIT_MESSAGE` | A regular expression for the text that the gateway returns with the limit. It is Python `re.search`, applied as written and case-sensitive unless it says otherwise. | none | `spend limit` |
| `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` | How long the factory waits after a spend limit when the limit names no wait, in whole minutes, at least 1. | `10` | `15` |
| `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` | How long the waits of one run may add up to before the run ends `provider_limit`, in whole minutes, at least 1. It must not be shorter than the cool-down. | `120` | `240` |

### The machine and the containers

Every stage runs its commands in throwaway Podman containers on a folder whose base is kept and reset before every stage. By default that folder is a ZFS dataset. With `FACTORY_SNAPSHOTS=copy` it is a plain directory whose base is a copy of it (see *Without ZFS* in [machine.md](machine.md)).

An instance needs `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE`, and with `zfs` also `FACTORY_DATASET`, with `copy` also `FACTORY_SNAPSHOT_BASE`.

| Name | What it does | Default | Example |
|---|---|---|---|
| `FACTORY_SNAPSHOTS` | How the dataset's base is kept: `zfs` or `copy`. | `zfs` | `copy` |
| `FACTORY_DATASET` | Required with `zfs`. The ZFS dataset the stages run on. It is not read with `copy`. | none | `tank/factory/vm` |
| `FACTORY_SNAPSHOT_BASE` | Required with `copy`. The directory that holds the base. With `zfs` it is refused. It must not be, hold or lie inside the workspace, the checkout or the state directory. | none | `/srv/factory/<instance>/base` |
| `FACTORY_WORKSPACE` | Required. The folder the stage containers mount at `/work`: the dataset's mount point with `zfs`, a plain directory with `copy`. The checkout and the state directory must lie outside it, so the default checkout rules out `/work`. | none | `/srv/factory/vm/work` |
| `FACTORY_STAGE_IMAGE` | Required. The image the stage containers run. | none | `factory-stage:1` |
| `FACTORY_PODMAN` | The `podman` executable, one word. | `podman` | `podman` |
| `FACTORY_ZFS` | The `zfs` executable, one word. | `zfs` | `zfs` |
| `FACTORY_CONTAINER_PROFILE` | How the factory starts its containers: `rootless` or `job` (see *The job profile* in [machine.md](machine.md)). | `rootless` | `job` |
| `FACTORY_CONTAINER_ENV` | Comma-separated names of variables of the factory's own environment that every agent, sync and check container also gets, with their values. A name that the factory's environment lacks is skipped. See "Behind a proxy" in [agent-runtime.md](agent-runtime.md). | none | `HTTPS_PROXY,NO_PROXY` |
| `FACTORY_CA_BUNDLE` | The path of a PEM file on the machine, the company's CA certificates. Every agent, sync and check container gets it mounted read-only at the same path, and `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` name it. The settings do not check that the file exists: podman refuses to mount a missing file, and the container then fails. | none | `/etc/ssl/company-ca.pem` |

### The idle shutdown

See *The idle shutdown* under "The machine" in [machine.md](machine.md).

| Name | What it does | Default | Example |
|---|---|---|---|
| `FACTORY_IDLE_SHUTDOWN_MINUTES` | The idle stretch, in whole minutes, after which the factory powers the machine off. `0` is off. | `0` | `30` |
| `FACTORY_IDLE_SHUTDOWN_ACTION` | What the shutdown does at the limit: `poweroff` powers the machine off, `exit` ends `factory-run` with status 0 (for a job). It has no effect while the shutdown is off. See *In a job* in [machine.md](machine.md). | `poweroff` | `exit` |

### The refusals

`factory-run` and `factory-watch` refuse an invalid environment with one line, `<variable>: <fault>`. This table lists the faults. `<variable>` is the variable that is at fault, and the other `<placeholders>` stand for the value or path that varies.

| Refusal | When it happens |
|---|---|
| `<variable>: missing` | A required variable is unset or blank. For `FACTORY_DATASET`, `FACTORY_SNAPSHOT_BASE`, `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE` it is raised when `factory-run` builds its boundaries, in this order: with `zfs` the dataset, the workspace, the image; with `copy` the base, the workspace, the image. |
| `<variable>: is not an absolute path` | A path variable holds a relative path. |
| `<variable>: names more than one repository` | `FACTORY_REPOSITORY_URL` holds whitespace or a comma. |
| `<variable>: holds a password; use the token file` | `FACTORY_REPOSITORY_URL` holds a user name and a password before the `@`. |
| `<variable>: is not a name` | `FACTORY_INSTANCE` does not match the rule of its row. |
| `<variable>: cannot read <path>: <reason>` | The file that `FACTORY_IMAGE_ID_FILE` or `FACTORY_TOKEN_FILE` names does not exist or cannot be read. |
| `<variable>: <path> is empty` | The file that `FACTORY_IMAGE_ID_FILE` or `FACTORY_TOKEN_FILE` names holds only spaces. |
| `<variable>: <path> lies inside FACTORY_WORKSPACE` | `FACTORY_CHECKOUT` (checked first) or `FACTORY_STATE` is the workspace or lies inside it. |
| `<variable>: <path> lies inside <place>` | `FACTORY_TRANSCRIPT_DIR` lies inside the workspace, the checkout, the state directory or the agent home. |
| `<variable>: is only used with FACTORY_SNAPSHOTS=copy` | `FACTORY_SNAPSHOT_BASE` is set with `zfs`. |
| `<variable>: <path> overlaps <name>` | With `copy`, `FACTORY_SNAPSHOT_BASE` is, holds or lies inside the workspace, the checkout or the state directory. |
| `<variable>: is neither zfs nor copy` | `FACTORY_SNAPSHOTS` holds another value. |
| `<variable>: is neither rootless nor job` | `FACTORY_CONTAINER_PROFILE` holds another value. |
| `<variable>: holds <value>, which is neither claude nor opencode` | `FACTORY_AGENT_RUNTIME` holds another value. |
| `<variable>: is neither poweroff nor exit` | `FACTORY_IDLE_SHUTDOWN_ACTION` holds another value. |
| `<variable>: is not a whole number of <unit> of at least <minimum>` | `FACTORY_MIN_FREE_GB` or a provider-limit minutes variable holds anything but ASCII digits (`0`, `-1`, `2.5` and `five` are refused) or a number below the minimum. |
| `<variable>: is not a whole number of <unit>` | `FACTORY_IDLE_SHUTDOWN_MINUTES` holds anything but ASCII digits (`-1`, `x` and `1.5` are refused). There is no upper bound. |
| `<variable>: is not an HTTP status from <lowest> to <highest>` | `FACTORY_PROVIDER_LIMIT_STATUS` holds anything but ASCII digits from 100 to 599. |
| `<variable>: is not a regular expression: <error>` | `FACTORY_PROVIDER_LIMIT_MESSAGE` does not compile. |
| `<variable>: is shorter than the cool-down` | `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` is below `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES`. |
| `<variable>: holds <entry>, which is not <alias>=<provider>/<model>` | An entry of `FACTORY_OPENCODE_MODELS` lacks `=`, has an empty alias, or has a model without a `/` or with an empty side. |
| `<variable>: names <name> twice` | `FACTORY_OPENCODE_MODELS` names an alias twice, or `FACTORY_CONTAINER_ENV` names a variable twice. |
| `<variable>: holds <name>, which is not a variable name` | A name in `FACTORY_CONTAINER_ENV` does not match `[A-Za-z_][A-Za-z0-9_]*`. `http_proxy` is fine. |
| `<variable>: holds <name>, which the factory sets itself` | `FACTORY_CONTAINER_ENV` names `HOME`, `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `OPENCODE_CONFIG`, `GIT_ASKPASS` or a name that starts with `FACTORY_`. |

A repository URL with a password is refused because git would keep the password in the shared checkout's `.git/config`, which the agent can read. Put the token in the token file instead. A user name alone is accepted: `ssh://git@github.com/owner/project.git`, `https://user@github.com/owner/project.git` and `git@github.com:owner/project.git`.

A repository URL of another form is refused with `FACTORY_REPOSITORY_URL: names no owner/name on a host`, when `factory-run` takes the repository's `owner/name` from it to build the hosting-service client.

Try a refusal with an instance name that breaks the rule. The example runs on a valid instance, so only this one variable is at fault:

```console fixture=instance
$ FACTORY_INSTANCE=Factory-1 factory-run
<time> settings invalid: FACTORY_INSTANCE: is not a name
```

## When the process refuses to start

What you see: `factory-run` ends with status 2 and no traceback. The factory log and standard output hold one time-stamped line, `settings invalid: <variable>: <fault>`. The container's health check fails, and `health.json` holds a `preflight_failed` stop with scope `machine`.

What it means: the environment is invalid (any fault in *The refusals*, including a missing or empty image identity file), the token file cannot be read, or the repository URL has no owner and no name.

What you do:

1. Read the line and correct the variable or the file it names.
2. Start the instance again.

The stop goes to the directory `FACTORY_STATE` names, else to `/state`. A relative `FACTORY_STATE` is itself the fault reported, and its stop goes to `/state`. The stop is added to the stops already in the file: an older `preflight_failed` stop is replaced, and no other stop is dropped.

If the state directory cannot be written, `factory-run` still ends with status 2, but writes no stop. The time-stamped line reaches standard output. Two lines go to standard error, `factory-run: settings invalid: <variable>: <fault>` and `factory-run: cannot write the machine stop: <error type>: <message>`. Check the owner and mode of the `state` volume: it may be mounted read-only or with the wrong owner.

## The loop and its pauses

An instance repeats one iteration: it prepares the checkout, then makes one [tick](../project-guide/glossary.md). The first iteration of a run happens at once, so a restart with the same instance name does not wait out a pause.

- After an iteration whose tick found activity, the instance does not pause. The next tick has work.
- After an idle iteration it pauses 30 seconds. Each further idle iteration in a row doubles the pause (30, 60, 120 seconds) up to 120 seconds. The next activity ends the pauses.
- An iteration whose preparation or tick fails counts as idle. The failure is one line in the factory log, `iteration failed: <exception type>: <message>`, and the loop goes on.

A tick counts as activity only when it handled an event other than `idle`. A standing stop, a capped event and an error are idle, so the pause keeps growing while nothing changes.

One tick object serves the whole run and keeps its error counts in memory from one iteration to the next. A restart starts them again.

With `FACTORY_IDLE_SHUTDOWN_MINUTES` set, the loop also counts its idle ticks in a row. These are ticks that ran, ended at no stop and handled the event `idle`. After them it may power the machine off. The pauses above are unchanged. An iteration whose preparation failed ran no tick: it neither counts nor ends the stretch. See *The idle shutdown* under "The machine" in [machine.md](machine.md).

### The checkout is cloned when it is missing

The checkout lies where `FACTORY_CHECKOUT` names. When that directory has no `.git`, the instance clones the repository into it. A checkout that has a `.git` is kept as it is: the factory does not check it, does not clone it again and removes no repository nested in the work tree. What an agent can reach is bounded by the container it runs in (see "What the container can and cannot see" in [machine.md](machine.md)), not by checks on the checkout.

A folder with files and no `.git` is refused: git will not clone into a non-empty directory, and the iteration fails. Delete the checkout directory and let the next iteration clone it again. The checkout is disposable (see "The stops of the tick" in [stops.md](stops.md)), so nothing is lost.

## The project's make targets

The factory runs a project's build through make. It calls four targets, which the project defines in the Makefile at the root of its checkout:

| Target | What it is for |
|---|---|
| `check` | The full gate. It must be green before a stage hands forward. |
| `lint` | Run after the tester stage. |
| `test` | The tests. |
| `sync` | Brings a checkout's tools up to date: `uv sync --frozen` in a Python project, the project's own command in another stack. The stage environment runs it before every agent run and before every check. No stage lists it in `checks` or `reports`. |

Each target is judged by its exit status alone. A target that does not exist counts as a failed command. A target that runs past its time limit is killed and counts as failed for that reason. The factory reads only the exit status, the last line and the last 30 lines of the output.

The factory does not remove ignored paths such as `.venv` and the caches. The checks run on a rolled-back copy of the dataset, and only the paths the role may write reach the checkout. So each target should build what it needs. The `uv run` of kumpel-factory and of the template creates `.venv` from `uv.lock`, and the first check after a rebuild of the image downloads the packages once. A target that relies on an ignored file another stage left fails.

A project whose `check` scans for secrets, with the template's `make secrets` or a scanner of its own, must leave out the factory's cost records (`*.costs.jsonl`, beside each work item). Otherwise the first agent run of every work item makes `check` red.

### Mutation testing by sweep

No stage and no agent runs `make mutants`. Mutation testing runs only as sweeps outside the factory, which the human starts on a fresh copy in a throwaway container. Every run makes `mutants/` anew. The template's `CLAUDE.md` and `Makefile` say the same: `make mutants` is for a sweep by hand. A coder's entry has no `mutants` line, and the acceptance's check 3, *Mutation testing*, says `By sweep, not run here.`

A sweep's command is:

```sh
make mutants MODULES=factory.pipeline.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2
```

| Name | What it does | Default | Example |
|---|---|---|---|
| `MODULES` | The modules or packages to mutate. | none | `factory.pipeline.application` |
| `MUTANTS_SECONDS` | Stops mutmut after that many seconds. | none | `7200` |
| `MUTANTS_CHILDREN` | Caps mutmut's workers. It matters in a container limited to fewer cores than the host reports. | none | `2` |

Every run starts with mutmut's stats over the whole suite in one process. That is the cost to plan for: about three minutes on 20 cores, and 4.5 to 19 minutes on two cores. On top of that each mutant costs about a fifth of a second on 20 cores. The recipe sets no stop unless `MUTANTS_SECONDS` is given.

A `MUTANTS_SECONDS` below the stats checks no mutant, and the run then fails with `mutants: stopped after <n> s, so the mutants it did not reach are not checked`. So `MUTANTS_SECONDS` must cover the stats plus the mutants' time:

```sh
make mutants MODULES=<module> MUTANTS_SECONDS=1500
```

## Reference

The exact detail behind the sections above.

**The order of faults.** `read_settings` reads the repository, the instance, `FACTORY_CHECKOUT`, `FACTORY_STATE`, the image identity file, `FACTORY_SNAPSHOTS`, then the faults of `FACTORY_WORKSPACE` (a relative path, a checkout or state directory inside it), of `FACTORY_SNAPSHOT_BASE` and of `FACTORY_TRANSCRIPT_DIR`, and last the other variables. `factory-run` reads the settings first. `factory-watch` reads the same environment and, on a fault, writes `factory-watch: settings invalid: <variable>: <fault>` to standard error.

**The stage environment.** The container is the boundary. The agent's `HOME` is `/work/home` on the dataset. A checkout or a state directory inside the workspace is refused, because every rollback of the dataset would reset the factory's own checkout, and the agent's container would reach the health file and the runs.

**Exit statuses of `factory-run`.** 0 when the run ends without a fault, also at an idle shutdown with the action `exit`; 1 when a machine stop that stood too long in a job ended the instance; 2 when the settings are invalid.

**The image identity.** The identity is read from the file `FACTORY_IMAGE_ID_FILE` names and stripped, so that a rebuild of the image with the same build argument cannot keep an old preflight stamp valid. The variable `FACTORY_IMAGE` is only a label of the build and is never read as the identity. `operator/vm/setup.sh` makes the file.

**The hosting-service token.** The token is read once, when the boundaries are built, from the file `FACTORY_TOKEN_FILE` names, stripped of surrounding whitespace. An unset variable, a missing or unreadable file, and a file that holds only spaces are each refused with `FACTORY_TOKEN_FILE` as the variable. The message names the path and never the token. The token reaches the hosting service from the factory process. Git gets it only through its credential helper, `/usr/local/bin/git-credential-factory`, which reads the same file.

**The repository's name.** The hosting service needs `owner/name`. It is taken from `FACTORY_REPOSITORY_URL` in one of the three forms `https://host/owner/name(.git)`, `ssh://git@host/owner/name(.git)` and `git@host:owner/name(.git)`.

**Variables that are ignored.** `FACTORY_STATE_DIRECTORY` and any other variable that the tables do not name are ignored.

**Where the VM sets the variables.** `operator/vm/setup.sh` sets `FACTORY_CHECKOUT` to `/srv/factory/<instance>/repo`, `FACTORY_STATE` to `/srv/factory/<instance>/state`, `FACTORY_IMAGE_ID_FILE` to `/srv/factory/<instance>/image-id` and `FACTORY_CLAUDE_HOME` to `/srv/factory/<instance>/factory/agents`. The environment file it writes sets `FACTORY_TOKEN_FILE` to `/home/factory/.secrets/hosting-token`, `FACTORY_CLAUDE_LOGIN_FILE` to `/home/factory/.secrets/claude-token` and `FACTORY_API_LOGIN_FILE` to `/home/factory/.secrets/anthropic-api-key`. See "The machine" in [machine.md](machine.md).

**The mutation sweep's cost, exactly.** The stats took 165 s on 20 cores: 28 s listing the tests, 131 s of mutmut's clean test run and 5 s generating. They took 4.5 to 19 minutes on two cores in the sweeps of 2026-10-19. Each mutant cost 0.13 to 0.25 s on 20 cores.
