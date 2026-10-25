# Operator guide

The guide for the person who runs the factory this repository implements: how to install and configure an instance, which stops it can reach and what to do about each. The machine of v1.2, a VM that runs the instance's stages in containers on a ZFS dataset, is described in "The machine"; v1.1's image is described in "The machine's image".

- "Install"
- "Configuration"
- "When the process refuses to start"
- "The loop and its pauses"
- "The project's make targets"
- "The agent runtime"
- "The machine"
- "The machine's image"
- "The container: compose, entrypoint and health check"
- "Container runtimes"
- "The factory log and the health status file"
- "The stops"
- "What a stage run shows"
- "A stall: the stall note"
- "A stall by a red check"
- "The factory's own questions"
- "The stop `pipeline_definition_invalid`"
- "The stop `agent_definition_invalid`"
- "The stops of the tick"
- "The pipeline definition"
- "The agent files"
- "The records contract"
- "Checking a story before it starts"
- "What a work item cost: `factory-bill`"
- "Looking at the remote: `factory-watch`"
- "When a feature acceptance is due"
- "The hand-over at the approval"
- "A stale branch is deleted by the tick"
- "A merge archives the story"
- "A close before the approval discards the story"
- "A close at the approval sends the story back"
- "Branch deletion on merge must be off"
- "An idle tick that is not empty"
- "A stage changed by hand"
- "An event that keeps failing"
- "Stops that cannot be done"
- "A restart during a stage"
- "An expired lease"
- "Claims, leases and the clock"
- "Replaced from v1"

## Install

Install v1.1 only on a repository v1 has not worked in, or whose v1 work items are archived or discarded: v1.1 starts fresh, and nothing detects a v1 work item.

Install the factory with `uv sync`, then check the installation with `make check`; it ends with the line `check: green`. The machine's image (see "The machine's image") is the usual way to run an instance: it carries the factory, the agent runtime and the pinned tools. Then set the instance's environment as described under "Configuration".

## Configuration

One factory instance runs one project and is told what it needs through environment variables. `factory.domain.settings.read_settings` reads them and refuses a bad one with `SettingsInvalid`, whose message is `<variable>: <fault>`; it reports the first fault in this order: the repository, the instance, `FACTORY_CHECKOUT`, `FACTORY_STATE`, the image identity file, the stage environment's faults (the inside-workspace fault of a `container` instance among them), then the variables below those in the table. `factory-run` calls it first; `factory-watch` reads the same environment.

| Variable | Required | Meaning |
|---|---|---|
| `FACTORY_REPOSITORY_URL` | yes | The one repository of the instance. No whitespace and no comma: a list of repositories is refused. |
| `FACTORY_INSTANCE` | yes | The instance's name, matching `^[a-z][a-z0-9-]*$` (`factory-1`; `Factory-1`, `1st`, `factory_1` and `-x` are refused). |
| `FACTORY_CHECKOUT` | no | The factory's own checkout, an absolute path. Default `/work/checkout`; unset or blank gives the default. A relative path is refused with `FACTORY_CHECKOUT` as the variable and `is not an absolute path`. |
| `FACTORY_STATE` | no | The state directory (`health.json`, the factory log, the runs), an absolute path. Default `/state`; unset or blank gives the default. A relative path is refused with `FACTORY_STATE` as the variable and `is not an absolute path`. `factory-health --state-directory <it>` reads the same place. |
| `GIT_USER_NAME` | no | Name of the factory's commits. Default `factory`. |
| `GIT_USER_EMAIL` | no | Email of the factory's commits. Default `factory@noreply.invalid`. |
| `FACTORY_IMAGE_ID_FILE` | no | The file that holds the identity of the image the instance runs on. Default `/opt/factory/image-id`. |
| `FACTORY_CLAUDE_HOME` | no | The directory where the agents are installed (`<it>/agents/<role>.md`). Default `$HOME/.claude`, or `/home/agent/.claude` when `HOME` is unset or blank. |
| `FACTORY_CLAUDE` | no | Claude Code's executable, used when the runtime is `claude`. Default `claude`. |
| `FACTORY_CLAUDE_VERSION` | no, but the preflight fails without it under Claude Code | The version of Claude Code the image pins (`2.1.296`). The image sets it; a missing or blank value is read as not pinned. |
| `FACTORY_TOKEN_FILE` | no, but needed to build the boundaries | The file that holds the hosting-service token. No default; the image sets it to `/home/factory/.secrets/hosting-token`. |
| `FACTORY_CLAUDE_LOGIN_FILE` | no | The file that holds the agent's login token, made with `claude setup-token`, as plain ASCII text. A blank value counts as unset. No default; the image sets it to `/home/agent/.claude-token`. See "The agent runtime" and "The agent's login token". |
| `FACTORY_API_LOGIN_FILE` | no | The file that holds the agent's Anthropic API key, as plain ASCII text. A blank value counts as unset. No default; the image sets it to `/home/agent/.anthropic-api-key`. A key in it wins over the token. See "The agent's API key". |
| `FACTORY_MIN_FREE_GB` | no | The least free space, in whole gigabytes of 10^9 bytes, at least 1. Default 5; unset or blank gives the default. Anything else (`0`, `-1`, `2.5`, `five`) is refused with `FACTORY_MIN_FREE_GB` as the variable. It guards the disk: when the work directory (the checkout's parent) or the state directory has less free space, the tick stops with `disk_low` (see "The stops of the tick"). |
| `FACTORY_PROVIDER_LIMIT_STATUS` | no | The HTTP status a provider answers with when its spend limit is reached. Default 428; unset or blank gives the default. A value of ASCII digits from 100 to 599 sets it; anything else is refused with `FACTORY_PROVIDER_LIMIT_STATUS` as the variable. See "A provider's spend limit". |
| `FACTORY_PROVIDER_LIMIT_MESSAGE` | no | A regular expression (Python `re.search`, as written, case-sensitive unless it says otherwise) for the text the gateway returns with the limit. Unset or blank means none. A value that is not a regular expression is refused with `FACTORY_PROVIDER_LIMIT_MESSAGE` as the variable. See "A provider's spend limit". |
| `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` | no | How long the factory waits after a provider's spend limit when the limit names no wait, in whole minutes of ASCII digits, at least 1. Default 10; unset or blank gives the default. Anything else (`0`, `-1`, `1.5`, `abc`) is refused with `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` as the variable. See "A provider's spend limit". |
| `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` | no | How long the waits of one run may add up to before the run ends `provider_limit`, in whole minutes of ASCII digits, at least 1. Default 120; unset or blank gives the default. Anything else is refused with `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` as the variable; a ceiling below the cool-down is refused with `is shorter than the cool-down`. See "A provider's spend limit". |
| `FACTORY_AGENT_RUNTIME` | no | The agent runtime of the instance: `claude` (Claude Code, the default) or `opencode`. Unset or blank gives `claude`; surrounding spaces are stripped; anything else (`Opencode`, `both`) is refused with `FACTORY_AGENT_RUNTIME` as the variable and `is neither claude nor opencode`. See "Running on opencode". |
| `FACTORY_OPENCODE` | no | The opencode executable, used when the runtime is `opencode`. Default `opencode`. |
| `FACTORY_OPENCODE_VERSION` | no, but the preflight fails without it under opencode | The version of opencode the image pins (`1.19.3`). The image sets it; a blank value is read as not pinned. |
| `FACTORY_OPENCODE_MODELS` | no | Comma-separated `<alias>=<provider>/<model>` entries that map the agent files' aliases (`opus`, `sonnet`, `haiku`) to opencode's model ids; spaces around each part are stripped. The provider is the part before the first `/`, so `openrouter/anthropic/claude-opus-5-5` is one model. Unset or blank gives none (the image sets the three Anthropic ids). An entry without `=`, with an empty alias or with a model that has no `/` or an empty side, and an alias named twice, are refused with `FACTORY_OPENCODE_MODELS` as the variable. |
| `FACTORY_STAGE_ENVIRONMENT` | no | Where a stage runs: `inline` (the default, the factory's own container) or `container` (the ZFS dataset and Podman containers). Unset or blank gives `inline`; surrounding spaces are stripped; anything else (`Container`, `podman`) is refused with `FACTORY_STAGE_ENVIRONMENT` as the variable and `holds <value>, which is neither inline nor container`. See "The stage environment". |
| `FACTORY_DATASET` | for `container` | The ZFS dataset the stages run on (`tank/factory/vm`). Missing or blank under `container` is refused with `FACTORY_DATASET` as the variable and `missing for the container environment`. Read and kept, but unused, under `inline`. |
| `FACTORY_WORKSPACE` | for `container` | The dataset's mount point on the host, an absolute path (`/srv/factory/vm/work`). Missing or blank under `container` is refused with `missing for the container environment`; a relative path with `is not an absolute path`. Not checked under `inline`. |
| `FACTORY_STAGE_IMAGE` | for `container` | The image the stage containers run (`factory-stage:1`). Missing or blank under `container` is refused with `FACTORY_STAGE_IMAGE` as the variable and `missing for the container environment`. |
| `FACTORY_PODMAN` | no | The `podman` executable, one word. Default `podman`; unset or blank gives the default. |
| `FACTORY_ZFS` | no | The `zfs` executable, one word. Default `zfs`; unset or blank gives the default. |

**The stage environment.** `FACTORY_STAGE_ENVIRONMENT` says where a stage runs. `inline` is v1.1's way and what every instance runs today: the agent runs in the factory's container as the factory's own user, and nothing needs to be set.

`container` runs each stage on a ZFS dataset and its commands in Podman containers. It needs `FACTORY_DATASET`, `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE`, and is refused when one is missing. It has no kernel write guard: the container is the boundary. The agent's `HOME` is `/work/home` on the dataset. The faults are reported in this order: dataset, workspace, image. After those, a checkout or a state directory that is the workspace or lies inside it is refused with `FACTORY_CHECKOUT` (checked first) or `FACTORY_STATE` as the variable and `<path> lies inside FACTORY_WORKSPACE`: every rollback of the dataset would reset the factory's own checkout, and the agent's container would reach the health file and the runs. With the default checkout, `FACTORY_WORKSPACE=/work` is refused for that reason.

This only lets an instance choose the environment. The VM it runs on, with the dataset and the stage image, is F0043's, and the preflight checks them: see "The preflight's items".

A required variable that is missing, empty or only spaces is refused. The two commit-identity variables are decided one by one: a half that is unset or only spaces falls back to its own default, so the commits are `factory <factory@noreply.invalid>` unless you set them. No preflight item checks the identity.

The image identity is read from the file, stripped, so that a rebuild of the image with the same build argument cannot keep an old preflight stamp valid. The image build generates the file (see "The machine's image"). A file that does not exist, cannot be read or holds only spaces is refused with `FACTORY_IMAGE_ID_FILE` as the variable. The variable `FACTORY_IMAGE` is only a label of the build and is never read as the identity.

A blank value of the three optional variables above counts as unset. The token is read once, when the boundaries are built, from the file `FACTORY_TOKEN_FILE` names, stripped of surrounding whitespace. An unset variable, a file that does not exist or cannot be read, and a file that holds only spaces are each refused with `FACTORY_TOKEN_FILE` as the variable; the message names the path and never the token. The token reaches the hosting service (PyGithub) from the factory process, and git only through its credential helper, `/usr/local/bin/git-credential-factory`, which reads the same file (see "The hosting-service token").

The repository's `owner/name`, which the hosting service needs, is taken from `FACTORY_REPOSITORY_URL`: `https://host/owner/name(.git)`, `ssh://git@host/owner/name(.git)` or `git@host:owner/name(.git)`. Any other URL is refused with `FACTORY_REPOSITORY_URL` as the variable. `factory-run` builds the boundaries from them when it starts.

The checkout and the state directory are settings: `FACTORY_CHECKOUT` and `FACTORY_STATE`. The image leaves both unset, so a compose instance keeps `/work/checkout` and `/state`; the VM of v1.2 sets both under `/srv/factory/<instance>` (see "The machine"). `FACTORY_STATE_DIRECTORY` and any other variable the table does not name are ignored.

### A repository URL with a password is refused

A URL whose user information holds a colon, that is a user name followed by a password before the `@`, is refused, because git would keep the password in the shared checkout's `.git/config`, which the agent can read. Put the token in the token file instead. A user name alone is accepted: `ssh://git@github.com/owner/project.git`, `https://user@github.com/owner/project.git` and the form `git@github.com:owner/project.git`.

## When the process refuses to start

`factory-run` ends with status 2, never with a traceback, when the environment is invalid (any fault in the table above, including a missing or empty image identity file), when the token file cannot be read, and when the repository URL has no owner and no name. It writes one time-stamped line to the factory log and standard output, `settings invalid: <variable>: <fault>`, and a `preflight_failed` stop with scope `machine` to `health.json`, both in the directory `FACTORY_STATE` names, else in `/state`; a relative `FACTORY_STATE` is itself the fault reported, and its stop goes to `/state`, so the container's health check fails and the fault is visible without opening the log. The stop is added to the stops already in the file; an older `preflight_failed` stop is replaced and no other stop is dropped. When the state directory cannot be written (a `state` volume mounted read-only or with the wrong owner), `factory-run` still ends with status 2: the time-stamped line reaches standard output, two lines go to standard error, `factory-run: settings invalid: <variable>: <fault>` and `factory-run: cannot write the machine stop: <error type>: <message>`, and no stop is written. Check the `state` volume's owner and mode. Correct the variable or the file and start the instance again.

## The loop and its pauses

An instance repeats one iteration: it prepares the checkout, then makes one tick. The first iteration of a run happens at once, so a restart with the same instance name does not wait out a pause. Only a tick that handled an event other than `idle` counts as activity: a standing stop, a capped event and an error are idle, so the pause keeps growing while nothing changes. The first iteration follows the same rule: the pause after it is 15 seconds when its tick handled an event other than `idle`, and 30 seconds when it was idle. One tick object serves the whole run, which keeps its error counts in memory from one iteration to the next; a restart starts them again.

After an iteration the instance pauses 15 seconds when the tick found activity. Each idle tick in a row doubles the pause (15, 30, 60 seconds) up to 120 seconds, and the next activity brings it back to 15 seconds. An iteration whose preparation or tick fails counts as idle. The failure is one line in the factory log, `iteration failed: <exception type>: <message>`, and the loop goes on.

### The checkout is cloned again when it is missing or its `.git` is not the factory's alone

The checkout lies at `/work/checkout`. When that directory has no `.git`, the instance clones the repository into it. At the start of every iteration it then seals the checkout's `.git`: the group's and others' write permission is taken from the folder and from every entry in it, so that only the factory writes the repository (see "Users and directories").

An existing `.git` is checked first. It must be a directory (not a symbolic link) of the factory's own user, closed to the group's and others' writes, and hold a `HEAD` file. A checkout whose `.git` fails the check is removed and cloned again on the next iteration, with the line `cloning the checkout again: <reason>` in `/state/factory.log`. That covers a clone made before this check existed (its `.git` is group-writable), a `.git` an agent replaced, and one without `HEAD`. A `.git` that is not closed is never repaired, because the factory cannot tell what an agent put in it. The instance's local state in the checkout is lost, which the restore discards anyway. A checkout the factory cannot remove is the stop `repository_unavailable`.

After every agent run the factory also looks for any entry named `.git` (a folder, a file or a symbolic link) below the work tree's root, other than the root's own, and removes each one before any git command runs. Git would otherwise record such a repository as a gitlink and start a child git in it, which reads that repository's own configuration, for example a `core.fsmonitor` command, as the factory's user. The stage stalls with the reason `nested_repository`, and the note names the paths: `Stalled (attempt 1 of 3): the agent left a git repository in the work tree, which the factory removed: notes/sub/.git. Retrying on the next tick.` The files next to a removed `.git` stay as ordinary files of the work tree, which the undo and the write paths judge like any other. At the start of every iteration the same search removes one an older checkout holds, with the line `removed nested repositories: <paths>` in `/state/factory.log`. One it cannot remove makes it clone the checkout again, and when that fails, the stop `repository_unavailable` follows. A probe run that leaves one fails the preflight item `agent-run-probe` with the paths. A project whose tools keep a git repository inside the work tree, even in an ignored folder, therefore stalls every stage: keep such clones outside `/work/checkout`.

A folder with files and no `.git` is still refused: git will not clone into a non-empty directory and the iteration fails. Delete the checkout directory and let the next iteration clone it again. The checkout is disposable (see "The stops of the tick"), so nothing is lost.

## The project's make targets

The factory runs a project's build through make and calls four targets: `check` (the full gate, which must be green before a stage hands forward), `lint` (run after the tester stage), `test` and `sync`. `sync` is the fourth: it brings a checkout's tools up to date after a checkout, `uv sync --frozen` in a Python project and the project's own command in another stack. The stage environment of a `container` instance runs it before every agent run and before every check; no stage of an `inline` instance runs it, and no stage lists it in `checks` or `reports`. A project must define them in the Makefile at the root of its checkout. Each is judged by its exit status alone, and a target that does not exist counts as a failed command. A target that runs past its time limit is killed and counts as failed for that reason; the factory reads only the exit status, the last line and the last 30 lines of the output.

The project's commands run on a checkout without any ignored state: the factory removes it after every agent run and at every restore. So each target builds what it needs (factory-rf's and the template's `uv run` create `.venv` from `uv.lock`; the first check after a rebuild of the image downloads the packages once), and a target that relies on an ignored file another stage left fails. The factory removes what an agent's run made there as its own user, through the group, so a project command an agent runs must leave its ignored files group-writable (the container's umask `002`); a stricter umask makes the removal fail with `checkout_restore_failed`. The usual cause is a bytecode folder: a Python that writes bytecode (`__pycache__`) under a umask stricter than `002`, such as factory-rf's tests under `022`, leaves a folder the factory cannot remove. It happens when the process does without the container's `PYTHONDONTWRITEBYTECODE=1`: an emptied environment drops it, and `-I` ignores it. factory-rf's `Makefile` exports `UV_COMPILE_BYTECODE=1`, so uv compiles `.venv`'s bytecode at its sync, under the caller's umask.

A project whose `check` scans for secrets, with the template's `make secrets` or a scanner of its own, must leave out the factory's cost records (`*.costs.jsonl`, beside each work item), or the first agent run of every work item makes `check` red.

### Mutation testing by sweep

No stage and no agent runs `make mutants`. Mutation testing runs only as sweeps outside the factory, which the human starts on a fresh copy in a throwaway container, with `mutants/` made anew for every run (the human's decision of 2026-10-19). The `mutants` target stays for those sweeps. A sweep's command is

```
make mutants MODULES=factory.application MUTANTS_SECONDS=7200 MUTANTS_CHILDREN=2
```

`MODULES` names the modules or packages, `MUTANTS_SECONDS` stops mutmut (no stop when unset) and `MUTANTS_CHILDREN` caps its workers, which matters in a container limited to fewer cores than the host reports. A coder's entry has no `mutants` line, and the acceptance's check 3, *Mutation testing*, says `By sweep, not run here.` The template's `CLAUDE.md` and `Makefile` say the same: `make mutants` is for a sweep by hand.

**How long it takes.** Every run starts with mutmut's stats, and they are the cost to plan for: 165 s on 20 cores (28 s listing the tests, 131 s of mutmut's clean test run, 5 s generating), and 4.5 to 19 minutes on two cores in the sweeps of 2026-10-19. On top of that each mutant costs 0.13 to 0.25 s on 20 cores. The recipe sets no stop unless `MUTANTS_SECONDS` is given. Every run removes `mutants/` first, so no run keeps the stats of an earlier one.

**A run that never gets past mutmut's stats.** Every run starts with mutmut's stats over the whole suite in one process. A `MUTANTS_SECONDS` below the stats checks no mutant, and the run then fails with `mutants: stopped after <n> s, so the mutants it did not reach are not checked`. A `MUTANTS_SECONDS` must cover the stats plus the mutants' time, for example:

```
make mutants MODULES=<module> MUTANTS_SECONDS=1500
```

## The agent runtime

The factory runs each agent as a `claude -p` call under Claude Code, or as an `opencode run` call under opencode (see "Running on opencode"). The rest of this passage is about Claude Code. It needs the `claude` program and the agent's login (an API key file, the token file, or a session logged in by hand when neither holds one). The factory itself holds no key or token: the call's own shell reads them. The call gets only the environment the run's request gives, with no variable inherited from the factory. The flags are those of v1; the preflight's item `agent-run-probe` makes one call with them once for each image build, so a flag the pinned `claude` rejects stops the machine before any claim. If a call fails at once, see "The probe of the agent run". The factory asks `claude --version` and takes the first word of its output (for example `2.1.289`). The pinned version is the one the flags were written for; the preflight compares it with `FACTORY_CLAUDE_VERSION` (see "The preflight's items").

The login of the call is, in this order:

1. an API key, when `FACTORY_API_LOGIN_FILE` names a file that holds one (see "The agent's API key");
2. a token, when `FACTORY_CLAUDE_LOGIN_FILE` names a file that holds one, made once with `claude setup-token`;
3. otherwise the login in the agent's home.

A variable that is unset, or a file that is missing or blank, counts as holding nothing. The text below is about the token; the API key is read the same way.

- A small shell reads the file at the start of every `claude -p` call, as the factory's own user, and hands the token to `claude` as `CLAUDE_CODE_OAUTH_TOKEN` before it replaces itself with `claude`. A new token is used from the next call, without a restart. The factory itself never reads the file.
- A file that cannot be read, or that is not plain ASCII text (a file saved as UTF-16 by Windows PowerShell 5, for example), stops the run with `agent runtime failed: cannot read the agent's login file <path>: cannot be read` or `...: not ASCII text`. No call is made.
- The token reaches only the `claude -p` calls. It is not in the factory's own environment, the project commands' or `claude --version`'s. A `CLAUDE_CODE_OAUTH_TOKEN` in a request's environment is dropped: the file is the only source.
- The token stands in no process's arguments, so neither `ps` inside the container nor a host user's `ps` on a Linux host shows it (a host shows a container's processes with their arguments unless `/proc` is mounted with `hidepid=2`).
- The allow list of the agent run's environment keeps its six names (`PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM`, `TZ`); the runtime's shell adds this one name, or `ANTHROPIC_API_KEY` when an API key is in force.
- With `FACTORY_API_LOGIN_FILE` set, the shell is started as `/bin/sh -c <script> factory-login --api-login <api file> <token file> claude ...`, with an empty word in place of the token file when `FACTORY_CLAUDE_LOGIN_FILE` is unset. Without it the shell is started as `/bin/sh -c <script> factory-login <token file> claude ...`. The shell tells the runtime on standard error which login it handed over (`factory-login-used: api_key`, `subscription` or `none`); the runtime turns that into the run's `login`.

A run whose budget is spent is not lost: the factory resumes the same session once with a quarter of the budget (at least 0.50 USD) and asks the agent to finish with its decision, `question` if the work is not done. That costs up to that extra amount, and the cost and tokens of both calls are added up. If the resume is also over budget, the run stops as a stall; there is no third call. A run that dies, runs past its time limit or returns no usable decision stops the work item as a stall. One `time_limit` covers both calls: the resume gets what is left. A run the `time_limit` ends is killed, is not resumed, and shows its cost, tokens and turns as unknown.

A `container` instance runs every agent call in a throwaway container as the host's `factory` (`--userns=keep-id`); an `inline` instance runs it as the factory's own user. No second user and no `sudo` stand between the factory and the agent: the only fence on the host is the folder of the token file (see "The hosting-service token"). On a `container` instance the agent's home is the dataset's `home/`, and the dataset's rollback clears it before every stage.

The take keeps the write paths. On a `container` instance it copies out of the dataset only the changed paths the role may write, and the dataset's rollback undoes the rest; on an `inline` instance the undo after the run reverts every change outside the write paths, whatever tool or command made it. A write elsewhere is lost, not refused: temporary files go through `mktemp` or `tempfile`, and they are lost with the stage. No kernel rule stands behind this.

**The agent's login token.** The login is a token, made once for all instances and the Podman machine:

1. Run `claude setup-token`, on the host where Claude Code is installed, or in a running container: `docker exec -it <container> claude setup-token`.
2. Save the token it prints, with nothing else in the file, as `image/secrets/claude-token` (git ignores the folder). On Windows write it as plain text without a byte-order mark, for example `Set-Content -NoNewline -Encoding ascii image/secrets/claude-token <token>`: PowerShell 5's `>` writes UTF-16, which is not read as the token.
3. Set the file's permissions for your host so that the factory's user can read it. Linux: `chmod 0440 image/secrets/claude-token`, with the file owned by that user or its group. Windows and macOS: keep the folder in your own user account, where other accounts cannot read it.

Compose mounts the file read-only and the image sets `FACTORY_CLAUDE_LOGIN_FILE` to its path. Every instance and the Podman machine use the same file and need no login of their own. A missing host file makes Compose refuse to start, instead of creating a folder in its place.

An empty file means no token, and the agent then needs the manual login:

```
docker exec -it <container> claude
```

That login is kept in the volume `claude-home`, and survives `docker compose down` and `up`. Since F0044-S0001 the runtime no longer sets `CLAUDE_CONFIG_DIR`, so `claude` keeps its `.claude.json` in the home's root.

**The agent's API key.** An instance can run its agents on an Anthropic API key instead of the subscription, for example at a workplace that has a key and no subscription. This repository's own build stays on the subscription.

1. Save the key, with nothing else in the file, as `image/secrets/anthropic-api-key` (git ignores the folder), as plain ASCII text. On Windows use `Set-Content -NoNewline -Encoding ascii`, as for the token: a file saved as UTF-16 stops the run with `agent runtime failed: cannot read the agent's API login file <path>: not ASCII text`. A file that is a folder or unreadable stops it with `...: cannot be read`. No call is made in either case.
2. Set the file's permissions as for the token file.
3. To give one instance its own key, point that instance's compose calls at another host file with `FACTORY_API_KEY_FILE=/path/to/file docker compose ...`. The default is `image/secrets/anthropic-api-key` beside `compose.yml`.

Compose mounts the file read-only and the image sets `FACTORY_API_LOGIN_FILE` to its path.

- The host file must exist, even empty, or Compose refuses to start (as for `claude-token`). An empty file means no API key.
- Several instances on one machine may differ: the instance that stays on the subscription keeps an empty file while another has a key in its own file.
- A key in the file wins over the token, which is not read then. Anything else in the environment named `ANTHROPIC_API_KEY` is dropped; the file is the only source.
- The file is read at every call, so a new key applies from the next call, without a restart. The key stands in no argument, run file, result, journal entry, cost record or log, and not in the factory's own environment.
- Switching back to the subscription means emptying the file and recreating the container (`docker compose up -d --force-recreate`), so that the container sees the file as it is now.

Which login is in force: the cost record of each run has the field `login`, which is `subscription`, `none` or the value for the API key (a line written before the field existed lacks it), and the preflight writes one factory-log line for the probe, for example `preflight: agent-run-probe: the agent runs log in with the API key from <file>`. The line comes with each run of the machine's items, so once for each image build.

### The agent in a container

On an instance whose stage environment is `container`, the call runs in a throwaway container. The words are `podman run --rm --userns=keep-id --timeout <seconds> --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=4g --env NAME=value ... --volume <dataset>:/work --volume <login file>:<login file>:ro --volume <instructions file>:<instructions file>:ro --workdir /work/checkout <image> /bin/sh -c <login shell> ... claude -p ...` (`opencode run ...` under opencode). The login files and the call's instructions (or configuration) file are mounted read-only at their own paths, so the login shell reads the token or key as on a host and the container cannot change them. The call gets only the environment the request gives, with `HOME=/work/home`. A call that podman's `--timeout` ends is a run that reached its time limit, not resumed; podman ends the container with exit status 255, which the factory reads as the time limit when the call lasted at least its limit. `claude --version` runs in the container too, so the preflight's `agent-runtime-version` compares the pin with the runtime in the stage image (the image is F0043's). The wiring gives a `container` instance's runtime this chain (see "The stage environment" under *Configuration*).

Every container of a `container` instance (the sync, the agent and each check) has the same fence. It has no capabilities (`--cap-drop=all`), and no set-uid program gives it rights (`--security-opt=no-new-privileges`). It may start 4096 processes and use 4 GB of memory. It keeps podman's default network, because the sync and the check's `make sync` need the package index and the agent needs the model's API. A container the kernel kills for its memory before the time limit is an ordinary failure, not a time-out: a failed check, usually with make's exit status 2 when the kernel ended one of its children, or 137 when it ended the container's first process.

### The agent run's `PATH` and `HOME`

The factory builds the environment of an agent run itself, from an allow list of six names (see "The hosting-service token"). The runtime adds no `PATH` to the call, so the two names that matter here are a `PATH` of the directory where the factory's console scripts are installed (the directory of the factory's Python) followed by `/usr/local/bin:/usr/bin:/bin`, and a `HOME` (the factory user's home). Nothing else reaches the agent but the locale and time-zone names `LANG`, `LC_ALL`, `TERM` and `TZ`, when the factory process has them. So the factory's commands must be installed in the same environment as the factory, and the tools an agent needs must be in one of those four directories. The preflight's item `agent-environment` checks the `HOME` (see "The preflight's items").

### A provider's spend limit

Some gateways limit the spend per model in a rolling window and answer a call past it with an HTTP error (the human's gateway: status 428, about $3 per 10 minutes). Without a rule the run would end `died`. The factory gives it its own end reason, `provider_limit`, and keeps the run's session in the result so that a later run can continue it.

- What matches: the status in `FACTORY_PROVIDER_LIMIT_STATUS` (default 428) as a whole number in the text (`HTTP 428:` and `(428)` match; `14280` does not), or a text the regular expression in `FACTORY_PROVIDER_LIMIT_MESSAGE` finds. Set the message when the gateway's text is not known to carry the status.
- Where it is looked for: in the error result the `claude` call printed, or, when no result could be read, in a line of its standard error. The opencode runtime looks for it while the run streams: in an `error` event (its `statusCode`, or the limit in its message) or in a line of standard error, and stops the run at once with the session kept. Never in the agent's own text, so an agent that writes "428" in a report cannot end its run.
- A run past its time limit, or stopped by its budget, keeps that end reason; the limit is looked for only when neither applies.
- A message that names a wait (`in 7 minutes`, `after 30 s`, `retry-after: 420`) gives the run's wait; otherwise none is known.
- The cost record's `end_reason` is `provider_limit`, and the record carries the refused calls (`denials`, `denied_paths`) like any run that replied.
- The factory waits the limit out and continues the run; see below.

#### The wait

When a call ends `provider_limit`, no agent process is left running. The factory waits, then resumes the same session with a short continue prompt, the budget that is left (the agent's budget less what the run has cost so far) and the time limit that is left (less the time the calls have used). It asks no one and counts no attempt.

- The wait is the one the message names (`limit_wait`), or `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` (default 10) when it names none. A run with no session starts again from the stage's own prompt.
- The waits count toward neither the stage's `time_limit` nor its attempts. A run resumed after a limit is one run and one cost record, with the costs of all its calls added up.
- A limit that comes again is waited out again. When the waits add up to `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` (default 120), the last wait cut to what is left of it, the run ends `provider_limit`.
- If nothing of the budget is left after a limit, the run ends `budget`; if none of the time is left, it ends `time_limit`. Neither waits.
- The preflight's probe never waits: a limit there is a failed probe (`the probe run ended provider_limit; ...`).

The factory log shows each wait and the end:

```text
2026-10-19T12:00:07Z provider limit: coder waits 600 s before it resumes ses_a
2026-10-19T12:10:07Z provider limit: coder waited 7200 s, the ceiling of 7200 s; the run ends provider_limit
```

The first line is written before each wait (`a new run` stands in for the session when the run has none). The second ends the run. Seconds are whole.

**What to do at the ceiling.** The stage stalls with the cause `the provider's spend limit lasted past the waiting ceiling`: one attempt is counted and the note is on the pull request (see "A stall: the stall note"). The next tick runs the stage again from what the stall kept, and at the attempts cap the factory asks you. A limit that lasts two hours is not a rolling window passing: look at the gateway (its quota, its window), or raise `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES`, before you answer.

**The claim stays held while waiting.** The factory renews no lease, so a stage that waits may hold its claim past its `lease_duration` (the coder's time limit, the ceiling and the checks come to about 180 minutes, against a lease of 60). Only another instance on the same repository would act on the age; run one instance per repository.

**A stop or a restart during a wait** is a crash of the factory's own claim: the stage runs again at once and counts toward the crash cap, not toward the attempts (see "A restart during a stage"). The wait starts over.

### An opencode run's budget

opencode has no budget flag, so the factory keeps the budget of an opencode run itself: it adds up the cost of every step as the run prints it and stops the run when the sum is above the agent's budget. It then resumes the session once with a quarter of the budget (at least 0.50 USD), as for a `claude` run. A step is counted when it ends, so a run may pass its budget by the cost of one step.

### Running on opencode

An instance runs its agents on Claude Code unless the operator sets `FACTORY_AGENT_RUNTIME=opencode` for that instance's compose calls, as `FACTORY_INSTANCE` is set. The image holds both runtimes: `opencode-ai` is installed from npm at the version `OPENCODE_VERSION` of the Dockerfile, and the image sets `FACTORY_OPENCODE_VERSION` to it.

**The login.** An opencode run logs in in one of two ways:

- An API key in the file `FACTORY_API_LOGIN_FILE` names (see "The agent's API key"). Every run is then paid through the API. The subscription token is not used.
- The login an operator's own build of opencode keeps in the agent's home (single sign-on). Make it once, as the factory user: `docker exec -it <container> <executable> <the build's login command>`, as `claude setup-token` is for Claude Code. The container loses it when it is recreated, unless you mount its folder with a compose override file.

The preflight asks for neither: the probe of the agent run shows whether a run can log in.

**Your own build.** Choose an opencode build per compose call with `FACTORY_OPENCODE` (its path in the container, which you mount or install), `FACTORY_OPENCODE_VERSION` (what `--version` prints) and `FACTORY_OPENCODE_MODELS`. The defaults are the image's `opencode-ai`, its pinned version and the three Anthropic ids.

**The models.** The agent files name `opus`, `sonnet` and `haiku`. `FACTORY_OPENCODE_MODELS` maps each to a `<provider>/<model>` id of opencode; the image sets `opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5`. Check that an id exists with `docker exec -u agent <container> opencode models anthropic`. A model written with a `/` in an agent file is used as it is.

**The version.** The image pins opencode (`OPENCODE_VERSION` in `image/Dockerfile`, default in `image/compose.yml` too); the item `agent-runtime-version` compares `opencode --version` with `FACTORY_OPENCODE_VERSION`. Change both together, as for Claude Code (see "Update the pins").

**The item `opencode`.** See "The preflight's items" for its two faults and what to do about each.

**What opencode keeps in the agent's home.** Sessions, logs and caches in `.local/share/opencode`, `.local/state/opencode` and `.cache/opencode`, for the length of one stage on a `container` instance (the dataset's rollback clears them). The configuration in `.config/opencode` is what the next run reads, and an agent that could write it could loosen its own permissions.

The image makes `/home/agent/.config/opencode`, owned by `factory` and read-only to the agent. opencode 1.19.3 makes that folder on its first run and dies (`EACCES ... mkdir`, the probe ends `died`) when it cannot; every recreated container has a fresh home, so without the folder each new container would stop. With the folder in place opencode starts and leaves it empty (its write of a default `opencode.jsonc` fails, and opencode ignores that). The folder's owner refuses the agent's write.

**What differs from Claude Code.**

- The denied commands of `settings.json` become `deny` permissions in the run's own configuration file.
- No structured reply. The agent ends its message with a `<factory-result>` block; a reply without a valid block ends the run `no_result`.
- The budget is the factory's own (see "An opencode run's budget").

## The machine

The machine of v1.2 runs every stage in containers on a dataset. This chapter takes a fresh Ubuntu 24.04 VM to a running `container` instance, and says what the machine is, what it costs and where to look when it misbehaves.

### What it is

One host, one dataset, one throwaway container for each step of a stage.

- **The host** is a Linux VM. The factory runs on it as a systemd service, `factory@<instance>`, under the user `factory`. The hosting token is on the host and nowhere else: the host alone fetches and pushes.
- **The dataset** is the ZFS dataset `<pool>/factory/<instance>`, mounted at `/srv/factory/<instance>/work` on the host and at `/work` in every container. It holds the checkout and the agent's home. Its one snapshot is the base, `@base`, moved forward at every stage's start.
- **The container** is the stage image (see *The stage image*), started for one step, with `--rm`, `--userns=keep-id` and `--timeout` set to the step's time limit. It mounts the dataset and is thrown away.

There is one user, `factory`, and no second one. `factory` has no `sudo` right but the four `zfs` commands of the optional `--sudoers` fallback (see *The script*). The steps that need root (the script, `systemctl`, the install of the secrets) run from your own account with `sudo`.

In v1.2 one repository URL serves both the factory's own code and the project. `--repository-url` is the clone of `/srv/factory/<instance>/factory` and the value of `FACTORY_REPOSITORY_URL`, so an instance builds the repository it runs from.

The layout of `/srv/factory/<instance>`:

| Path | Holds |
|---|---|
| `work` | the dataset's mount point |
| `repo` | the factory's own clone of the project, where it fetches, claims and pushes |
| `state` | the factory log, `health.json` and the records |
| `factory` | the factory's code, cloned at `--ref`, with its `.venv` |
| `tools` | a virtual environment holding `uv` |
| `factory.env` | the service's environment file |
| `image-id` | the identity of the stage image |
| `askpass` | the script git asks for the hosting token |

### The stage image

Every container of a v1.2 stage (the sync, the agent, the checks) starts from one image that holds the tools and nothing of the factory. `vm/Dockerfile` builds it.

It holds:

- the pinned base image, and Debian's `git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs` and `npm`, each at an exact version;
- `uv`, Claude Code and opencode at exact versions, with the runtimes' environment: `DISABLE_AUTOUPDATER`, `UV_LINK_MODE`, `PYTHONDONTWRITEBYTECODE`, the two version records `FACTORY_CLAUDE_VERSION` and `FACTORY_OPENCODE_VERSION`, and the opencode model ids `FACTORY_OPENCODE_MODELS`;
- the agent files (`claude/agents` and `claude/settings.json`) at `/etc/factory/claude`, read-only.

It does not hold what served the long-lived container of `image/Dockerfile`: no second user and no group, no `sudo`, no entrypoint, no `/etc/gitconfig`, no `USER`, `WORKDIR`, `ENTRYPOINT` or `CMD`, no copy of the factory's source or its `uv sync`, no image-id file and no login or token path.

The image only carries the agent files. The sync container copies them into the dataset's `/work/home/.claude` before the base moves (F0042).

Build it on the VM as the user `factory`, from a checkout:

```bash
podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> <the checkout>
```

`--build-arg FACTORY_IMAGE=<ref>` sets the label `factory.image`; it defaults to `unlabelled`. The label is not the identity of the image. The settings read the identity from the file `FACTORY_IMAGE_ID_FILE` names, and you renew that file after every build. `vm/setup.sh` makes the file with a fresh uuid when it is missing or empty (see *The script*). Nothing in `make check` builds the image.

`vm/Dockerfile` pins seven Debian packages: `git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs` and `npm`. `sudo` is pinned in `image/Dockerfile` alone. To update a pin, change the same lines in both Dockerfiles, following *Update the pins* under "The machine's image" for the shared ones. Check a changed pin with `uv run pytest tests/test_stage_image.py tests/test_image.py`. Until F0044 removes `image/`, `tests/test_stage_image.py` holds the two Dockerfiles to the same pins (the base image, the three versions, the seven Debian packages and the opencode model ids), so a pin changed in one file alone fails it.

### The script

`vm/setup.sh` makes the machine from a fresh Ubuntu 24.04 with a spare disk and installs the service. It is POSIX `sh`, runs as root and does only what is missing, so a second run changes nothing.

```bash
sudo sh vm/setup.sh --device /dev/sdb --repository-url https://github.com/<owner>/<repo>.git
```

| Option | Default | Meaning |
|---|---|---|
| `--device <path>` | required | The disk, or a file such as `/var/lib/factory-pool.img`, the pool is made on. The script does not test it: a pool that exists is found whatever `--device` names. |
| `--repository-url <url>` | required | The repository the factory works on and runs from. |
| `--instance <name>` | `vm` | The instance's name; its folder is `/srv/factory/<instance>`. |
| `--pool <name>` | `tank` | The ZFS pool. |
| `--quota <size>` | `30G` | The quota of the instance's dataset. |
| `--ref <git ref>` | `main` | The factory's git ref to check out. |
| `--image <tag>` | `factory-stage:<instance>` | The stage image. |
| `--runtime claude\|opencode` | `claude` | The agent runtime. |
| `--sudoers` | off | Reach `zfs` through `sudo` (see below). |
| `--help` | | Print the usage to standard output and exit 0. |

A missing required option, an option without its value, an unknown word or a runtime other than the two prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2. When the user is not root it prints `setup.sh: run as root` and exits 2. Nothing is made or changed before either exit.

#### The steps

Each step prints one line, `setup: <step>: `, followed by what it changed (joined with `; `) or, when nothing needed doing, what it found, which says `found`. The steps run in this order:

1. `packages`: `apt-get update`, then `apt-get install -y --no-install-recommends` of the missing ones among `zfsutils-linux podman uidmap slirp4netns git make python3.12-venv`.
2. `pool`: `zpool create -o ashift=12 -O compression=lz4 -O atime=off <pool> <device>`, unless `<pool>` exists.
3. `user`: the user `factory` with a home and `/bin/bash`, unless it exists. `/etc/subuid` and `/etc/subgid` must each hold a `factory:` line; the script does not make one. Without it, it prints `setup: user: no subuid and subgid range for factory; add one with usermod --add-subuids and --add-subgids` to standard error and exits 1. Add the ranges and run the script again.
4. `linger`: `loginctl enable-linger factory`, so rootless Podman and the user's runtime folder outlive a login.
5. `datasets`: `<pool>/factory` and `<pool>/factory/<instance>`, both with `compression=lz4` and `atime=off`, the second mounted at `/srv/factory/<instance>/work`, with the quota, and the mount point owned by `factory`.
6. `delegation`: `zfs allow -u factory snapshot,destroy,rollback,diff,mount` on the instance's dataset, unless all five are already delegated.
7. `sudoers`: only with `--sudoers`, see below. Without it the line says `not asked` and neither file is touched.
8. `folders`: `/srv/factory/<instance>` with `state` and `repo`, owned by `factory` (mode `0755`), and `/home/factory/.secrets` (mode `0700`). If `state`, `repo` or `/home/factory/.secrets` is a link, the script prints `setup: folders: ...` to standard error and exits 1 before it makes anything in the step: remove the link and run it again. The script sets the secrets folder's owner and mode and never touches a file in it: the secrets you placed stay as they are on every run.
9. `image-id`: `/srv/factory/<instance>/image-id`, a fresh uuid (mode `0644`) when the file is missing or empty. A rebuilt image needs a new id; renew the file yourself (see *The stage image*).
10. `checkout`: the factory at `--ref`, cloned as `factory` into `/srv/factory/<instance>/factory`, unless it holds a `.git`.
11. `tools`: a virtual environment `/srv/factory/<instance>/tools` with `uv` installed from `pip` at the version of `ARG UV_VERSION` in the checkout's `vm/Dockerfile`; `uv sync --frozen --no-dev` in the checkout, which makes the factory's own `.venv`; and `/usr/local/bin/git-credential-factory`, copied from the checkout's `image/` (see *The two passes*). `uv sync` runs on every run and changes nothing when the environment matches the lockfile.
12. `environment`: `/srv/factory/<instance>/factory.env` (mode `0644`).
13. `service`: the unit `vm/factory.service` as `/etc/systemd/system/factory@.service` (mode `0644`; see *The two passes*), `systemctl daemon-reload`, and `systemctl enable factory@<instance>`. The service is enabled, not started.

The script writes the files under `/srv/factory/<instance>` (`image-id`, the askpass script and `factory.env`) as `factory`, with `cat` from its own standard input, because a process started by `runuser` may not reopen root's `/dev/stdin`.

The script ends with `setup: done: build the stage image and start factory@<instance>; see the operator guide, "The machine"`.

#### The two passes

The checkout of the private repository needs the hosting token. When `/home/factory/.secrets/hosting-token` is not there at step 10, the script prints `setup: checkout: waiting for /home/factory/.secrets/hosting-token; place the secrets and run this script again` and exits 0. Place all three files, `hosting-token`, `claude-token` and `anthropic-api-key`, in `/home/factory/.secrets`, readable by `factory`, and run the same command again: steps 1 to 9 report `found` and the rest completes. All three must exist whatever the runtime; with the `claude` runtime the key file stays empty.

The token is written into no file. Git asks the askpass script (`/srv/factory/<instance>/askpass`) for it, and only that script reads the token file; the clone sets `core.askPass` on its own command line, not in any git configuration.

The unit and the credential helper come from the checkout, and root installs them only in the run that made the clone (whose content is the remote's at `--ref`, before the service ever ran) or when the installed file is missing. So a first run that stopped after the clone is completed by the next. A later run that finds the installed file in place but different from the checkout installs nothing and prints `setup: tools: /usr/local/bin/git-credential-factory differs from the checkout; not installed` or `setup: service: /etc/systemd/system/factory@.service differs from the checkout; not installed` to standard error. To take the checkout's version, remove the installed file and run the script again.

#### The environment file

Every run rewrites `factory.env` from the arguments and from the pins in the checkout's `vm/Dockerfile` (the Claude Code and opencode versions and the opencode model ids), and writes it only when its text differs. A change therefore goes into the script's arguments (or the Dockerfile), never into the file: an edit by hand is lost at the next run.

#### The `sudoers` fallback

The delegation of step 6 is the way for the factory to reach `zfs`. When it does not suffice on your machine, run the script with `--sudoers`. Step 7 then writes `/etc/sudoers.d/factory-zfs` (mode `0440`), which lets `factory` run exactly `zfs snapshot`, `zfs destroy`, `zfs rollback -r` and `zfs diff -FH`, each on `<dataset>@base` alone, as root without a password, and checks it with `visudo -cf`. If `visudo` refuses it, the script removes the file, prints the refusal to standard error and exits 1. It also writes `/usr/local/bin/zfs-factory` (mode `0755`), a wrapper that runs those four commands through `sudo -n /usr/sbin/zfs` and every other command as itself, and the environment file then holds `FACTORY_ZFS=/usr/local/bin/zfs-factory`.

The rule names `diff -FH` because the factory runs `zfs diff` with those flags and `sudoers` matches the whole argument list; a rule for `diff -H` would not match.

### The service

The unit `vm/factory.service` is a systemd template, installed as `factory@.service`; the text after the `@` is the instance. For the default instance it is `factory@vm`. The unit runs as `factory`, with `/srv/factory/%i` as its working directory, reads `/srv/factory/%i/factory.env` and starts `/srv/factory/%i/factory/.venv/bin/factory-run`. `Restart=always` with `RestartSec=15` restarts it fifteen seconds after any exit, in place of Compose's restart policy.

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
| `FACTORY_STAGE_ENVIRONMENT` | `container` |
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

7. On the VM, run the script as root, the first time. The disk is `/dev/disk/by-id/google-factory-data` (`ls -l /dev/disk/by-id/ | grep google` shows it). `--ref` is the tag or branch to run.

   ```bash
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/factory-rf.git --ref <the tag or branch to run>
   ```

   It installs the packages and makes the pool, the user `factory`, the datasets, the delegation and the folders. Then it stops with `setup: checkout: waiting for /home/factory/.secrets/hosting-token` and exit status 0: the private repository needs the token (see *The script*, "The two passes"). On a VM that the prototype of `planning/overnight/gcp-runbook-2026-10-24.md` already prepared, the script finds those steps done and reports `found`.

8. Place the three secrets by hand, from your own account on the VM, one file each: `hosting-token` (the GitHub token), `claude-token` (the output of `claude setup-token`) and `anthropic-api-key`. Make each file in your home folder with an editor, install it, and remove the copy:

   ```bash
   sudo install -m 0600 -o factory -g factory hosting-token /home/factory/.secrets/hosting-token
   sudo install -m 0600 -o factory -g factory claude-token /home/factory/.secrets/claude-token
   sudo install -m 0600 -o factory -g factory anthropic-api-key /home/factory/.secrets/anthropic-api-key
   shred -u hosting-token claude-token anthropic-api-key
   ```

   All three files must exist, because the factory mounts every login file the environment file names and podman refuses to mount a missing one; every agent run would stop with exit status 125 (decision 10 of the feature F0043). An empty `anthropic-api-key` means no key. With the `claude` runtime the key file stays empty.

9. Run the script a second time with the same arguments. It clones the factory, installs the tools, writes the environment file and installs and enables the unit.

   ```bash
   sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
     --repository-url https://github.com/pkrahmer/factory-rf.git --ref <the tag or branch to run>
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
- `/srv/factory/vm/state/factory.log`: the factory log (see "The factory log and the health status file"). After every stage it holds a line `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`. The plan's measure "the start of a stage to the agent's first step" (target under 20 s with a warm base, the reset under 2 s) is `reset` plus `sync` plus `advance`; `take` is the copy back.
- `health.json` in the state directory, through `factory-health --state-directory /srv/factory/vm/state`.
- `sudo -iu factory podman ps`: a stage container that is running now. Containers run with `--rm`, so a finished one leaves nothing to look at.

### The rebuild after a merge

The instance runs the factory's code from `/srv/factory/vm/factory` and the stage image built from it. After a merge to the ref it runs, stop the instance between two stages, bring both up to date, and start it again.

Stop it first. An agent run lasts up to its role's `time_limit`, so a running instance may be in the middle of a stage. A stop during a stage ends the factory after systemd's stop timeout of 90 seconds, and the restart counts that stage as a crash (see "If the factory dies while a stage runs"). So wait until no work item is held by `vm`: on the VM as `factory`, run `factory-watch` as in step 11 of *On GCP, step by step*, and look at the board. Then, on the VM from your own account, stop the instance:

```bash
sudo systemctl stop factory@vm
```

Then bring the checkout and the image up to date. On the VM as `factory` (`sudo -iu factory`):

```bash
git -C /srv/factory/vm/factory pull --ff-only          # for a tagged ref: git fetch --tags, then git checkout <tag>
cd /srv/factory/vm/factory
/srv/factory/vm/tools/bin/uv sync --frozen --no-dev
podman build -f vm/Dockerfile -t factory-stage:vm --build-arg FACTORY_IMAGE=<ref> /srv/factory/vm/factory
cat /proc/sys/kernel/random/uuid > /srv/factory/vm/image-id
exit
```

The new uuid in `image-id` is what tells the settings the image is new; the label is not its identity. Then run the setup script from a copy of your own, as root: copy `vm/setup.sh` from your checkout of the ref the instance runs, as in step 6 of *On GCP, step by step*, and run it from your own account with the arguments of the first run. Root runs nothing from `/srv/factory/vm/factory`, because `factory` can write that checkout.

On your own computer, in your checkout, copy the script to the VM and open a shell there:

```bash
gcloud compute scp --zone=europe-west3-a --tunnel-through-iap vm/setup.sh factory-vm:
gcloud compute ssh factory-vm --zone=europe-west3-a --tunnel-through-iap
```

On a VM outside GCP, copy `vm/setup.sh` from your own checkout by your own means, such as `scp`, as *On any Ubuntu 24.04 VM* does.

On the VM from your own account, run the script and start the instance again:

```bash
sudo sh setup.sh --device /dev/disk/by-id/google-factory-data \
  --repository-url https://github.com/pkrahmer/factory-rf.git --ref <the same ref>
sudo systemctl start factory@vm
```

`vm/setup.sh` is idempotent, so run it after every merge: it carries a changed pin of `vm/Dockerfile` into the environment file, updates `uv` and the factory's virtual environment, and reports the rest found. It does not replace an installed `/etc/systemd/system/factory@.service` or `/usr/local/bin/git-credential-factory` that differs from the checkout: it prints that the file differs and leaves it. When a merge changed `vm/factory.service` or `image/git-credential-factory`, remove the installed file and run the script again (see *The two passes*).

## The machine's image

`vm/Dockerfile` is the stage image of v1.2 (see "The stage image"); `image/Dockerfile` is the machine of v1.1 until F0044. Everything below describes `image/Dockerfile`.

`image/Dockerfile` builds the machine the factory runs on. Nothing in it floats: the base image is named with its digest, Claude Code, opencode, `uv` and the eight Debian tools have exact versions, and the factory's own dependencies are installed by `uv sync --frozen --no-dev` from `uv.lock` alone (the build backend, `hatchling`, is pinned in `pyproject.toml`). `tests/test_image.py` checks this statically; it reports any reference that floats, such as a `FROM` without a digest, an `apt-get install` package without `=version`, `latest`, or a download piped into a shell.

### What the container cannot see

Under Docker Desktop's WSL 2 backend and under Podman's machine on Windows the container has no disk limit, so `df` inside it shows the machine's virtual disk (about 1 TB), not the host drive. A check of free space inside the container therefore fires only on a Linux host or when the container has a real limit. Under either runtime the host drive is watched from outside, and Docker's disk image belongs on a drive with room.

When the disk image has grown and the host drive is full, the space comes back in two steps. Run `fstrim -v /mnt/docker-desktop-disk` in the `docker-desktop` distribution. Then stop Docker and run `compact vdisk` in `diskpart`.

### Build it

Run it from the repository root, with Docker:

```bash
docker build -f image/Dockerfile -t factory:local .
```

The build argument `FACTORY_IMAGE` is optional and is only a label (`docker build --build-arg FACTORY_IMAGE=2026-10 ...`); it defaults to `unlabelled`. The identity of the image is not the label. The build generates a fresh id and writes it to `/opt/factory/image-id`, which the settings read. Every rebuild that changes an earlier layer gets a new id, so it invalidates the preflight stamp, even when you pass the same label.

A build of the image with the pins of `image/Dockerfile` is not observed yet: check it once on a running instance. The Dockerfile also copies `claude/` and `template/`.

### Update the pins

The digest of `BASE_IMAGE` and the eight Debian package versions (`git`, `make`, `curl`, `ca-certificates`, `procps`, `sudo`, `nodejs`, `npm`) were read from the official `python:3.12-slim-bookworm` image on 2026-10-17 (Debian 12.15). Debian's mirrors keep only a package's current version, so a pinned version that a security or point update replaces stops building: then read the new versions with `apt-cache policy <package>` in the new base image and update the digest and the pins together.

To update any pin, edit its line and run `uv run pytest tests/test_image.py`:

- Base image: `docker pull python:3.12-slim-bookworm`, then take the digest from `docker inspect --format '{{index .RepoDigests 0}}'` and put it after `@sha256:` in the `BASE_IMAGE` default.
- Debian package: in the base image, `apt-cache policy <package>` shows the version; write it as `name=version`.
- `uv`: the `UV_VERSION` default. Claude Code: the `CLAUDE_CODE_VERSION` default (three numbers).
- opencode: the `OPENCODE_VERSION` default and the `FACTORY_OPENCODE_MODELS` value in `image/Dockerfile`, and the defaults of `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` in `image/compose.yml`; they change with it. Check the model ids with `opencode models anthropic`. `tests/test_opencode_image.py` pins the version and the model ids as well, so it changes with them; run it with `tests/test_image.py`.

### Claude Code

Claude Code is installed from its npm package, `@anthropic-ai/claude-code`, at the pinned version `2.1.296`, with its auto-update off (`DISABLE_AUTOUPDATER=1`). The version is also in the container's environment as `FACTORY_CLAUDE_VERSION`, so the preflight can read it. The pin changes only when you edit the Dockerfile.

### Users and directories

The container runs as `factory` (uid 1000); the agent runs as `agent` (uid 1001). Both have the group `factory-work`.

| Path | Mode and owner | What it means |
|---|---|---|
| `/state` | `0755`, `factory:factory` | The agent can read the health file, the log and the stamp, and cannot write them. |
| `/state/runs` | `2750`, `factory:factory-work` | The files of an agent's run: the agent can read them and cannot write them. |
| `/home/factory/.secrets` | `0700`, `factory:factory` | The folder where Compose mounts the token file. Only `factory` can enter it, so the agent cannot read the file whatever the file's own mode. |
| `/work` | `2775`, `factory:factory-work` | Both users can write. |
| `/work/checkout/.git` | `2750`, `factory:factory-work`; its files `0640` | Git's repository of the checkout. The factory alone writes it. The agent's git reads it (`git status`, `git diff`, `git log`) and cannot create, change, rename or remove anything in it. The work tree around it stays group-writable. |
| `/etc/gitconfig` | `0644`, `root:root` | Git's system configuration, installed from `image/gitconfig`. The agent's git reads it; the factory's git wrapper does not (it sets `GIT_CONFIG_NOSYSTEM=1`). It names `/work/checkout` as a safe directory, so that the agent can run `git status`, `git diff` and `git log` in the checkout `factory` owns. The agent cannot change the file. |
| `/home/agent/.claude-token` | the host file's owner and mode (`1001:1002`, `0440` on Linux), mounted read-only | The agent's login token. The agent can read it; it lies outside `/home/factory/.secrets` and outside the volume `claude-home`. |
| `/home/agent/.anthropic-api-key` | the host file's owner and mode (`1001:1002`, `0440` on Linux), mounted read-only | The agent's API key, or an empty file for none. Like the token file it lies outside `/home/factory/.secrets` and outside the volume `claude-home`. |
| `/home/agent/.claude` | `3775`, `factory:factory-work` | The agent adds its own files (its `claude` login among them) and cannot change or remove the agents and the settings. |

### The image on the cost records

Every cost record names the image the agent run ran on (the identity from `/opt/factory/image-id`). A record made when the instance has no image identity has none.

## The container: compose, entrypoint and health check

`image/compose.yml` runs the image as the service `factory`, built from the repository root with `image/Dockerfile`. Start it from the repository root:

```bash
FACTORY_REPOSITORY_URL=https://github.com/you/project.git FACTORY_INSTANCE=main docker compose -f image/compose.yml up -d
```

| Variable | Meaning |
|---|---|
| `FACTORY_REPOSITORY_URL` | Required. The project's repository. Compose refuses to start when it is unset. |
| `FACTORY_INSTANCE` | Required. This instance's name. Compose refuses to start when it is unset. |
| `FACTORY_IMAGE` | Optional. Only a label for the build (default `unlabelled`); it is not the image's identity. |

The compose project is named `factory-<instance>`, after `FACTORY_INSTANCE`. The volumes `work` (`/work`), `state` (`/state`) and `claude-home` (`/home/agent/.claude`) outlive the container, and are named `factory-<instance>_work`, `factory-<instance>_state` and `factory-<instance>_claude-home`. Beside them Compose bind-mounts two host files read-only: the agent's login token at `/home/agent/.claude-token` (from `image/secrets/claude-token`; see "The agent's login token") and the hosting token (next section). Two instances on one machine, and v1 beside v1.1, therefore get their own container and volumes and never replace or mount each other's. Renaming an instance changes the project name, so the renamed instance starts with new, empty volumes (a new checkout, a new state directory, and a new `claude` login only when the token file is empty); the old volumes stay until you remove them.

### The hosting-service token

The token lives in one file on the host, `secrets/hosting-token`, beside `image/compose.yml` (`image/secrets/hosting-token`; git ignores the directory). Compose mounts it read-only at `/home/factory/.secrets/hosting-token`, and the image sets `FACTORY_TOKEN_FILE` to that path. The folder `/home/factory/.secrets` is made in the image, `factory:factory`, mode `0700`: only the factory's user can enter it, so the agent (uid 1001) cannot read the file whatever the file's own mode.

The folder does the work because the file cannot. A compose secret cannot do it, because Compose ignores its `uid`, `gid` and `mode` outside Swarm mode: the file is a plain bind mount with the host file's owner and mode, which on Windows shows as `-rwxrwxrwx`, owner 0, under Docker Desktop and under Podman alike. A missing host file makes Compose refuse to start; it does not create a folder in its place (`create_host_path: false`).

The host file's permissions still matter: anyone on the host who can read it has the token. Set them by host:

- Linux with Docker: `chown 1000 image/secrets/hosting-token` and `chmod 0400 image/secrets/hosting-token`.
- Linux with rootless Podman: `chmod 0400 image/secrets/hosting-token` first, then `podman unshare chown 1000 image/secrets/hosting-token`. The host user maps to root in the container, so it no longer owns the file after the `chown`.
- Windows and macOS: keep the repository in a folder of your own user account that other accounts cannot read.

Only two things read the file: the factory process, once, to hand the token to PyGithub, and git's credential helper, `/usr/local/bin/git-credential-factory`. The helper answers git's `get` with the user name `x-access-token` and the file's content as the password. If `FACTORY_TOKEN_FILE` is unset or the file cannot be read, it prints nothing and exits 1, so a process that cannot read the file gets no credential. For `store`, `erase` and any other operation it prints nothing and exits 0. The factory's git reaches the helper only through the environment the factory gives it; the image sets no `credential.helper`, stores no `.git-credentials` and has no token, secret or password in an `ENV`, an `ARG` or the compose `environment`, so the agent's git has no credential.

An agent run's environment is an allow list of six names: `PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM` and `TZ`. The factory builds `PATH` and `HOME` itself and takes the other four from its own environment when it has them. Everything else the factory process holds (`FACTORY_TOKEN_FILE`, `GH_TOKEN`, `GITHUB_TOKEN`, `GIT_ASKPASS`, `SSH_AUTH_SOCK`, any variable of yours) is dropped at the source and never reaches an agent. The factory's own pushes and posts are not affected.

The preflight item `token-file` (see "The preflight's items") checks that the token file exists and that its folder belongs to the factory's user and has no permission bit for group or others. The file's own owner and mode do not count, because a bind mount shows the host's. Its detail is `<path>: <fault>`, with the fault:

- `no token file is set`: `FACTORY_TOKEN_FILE` is unset. Set it (the image does) and start the instance again.
- `the token file does not exist`: the folder or the file is missing. Put the token in the host file `secrets/hosting-token` that Compose mounts, or correct the path `FACTORY_TOKEN_FILE` names.
- `the folder <folder> belongs to uid <n>, not to <m>`: the folder is not the factory's user's. Use the image's `/home/factory/.secrets`, or `chown` your folder to that user.
- `the folder <folder> has mode <mode>; make it 0700`: `chmod 0700` the folder, or use the image's.

The folder is checked first, so a folder the factory's user does not own is reported even when it cannot enter it.

**Checks on a running instance.** Tests cover the files and the helper, but not a real agent run, which needs a container runtime (Docker or Podman) and the image's second operating-system user. Check by hand once after a build, inside the container:

- `docker exec -u agent <container> cat /home/factory/.secrets/hosting-token` and `docker exec -u agent <container> ls /home/factory/.secrets` are refused with `Permission denied`, and `ls -lnd /home/factory/.secrets` shows `drwx------` and uid 1000.
- As an agent (a run that tries it, or `su` to another user), `printenv` must show no token, `git -C . push origin main` must fail, and a call to the hosting service's API must fail.

**The project commands.** An `inline` instance runs every project command (`make check`, `lint`, `test`, `secrets`, `duplicates`, `documents`, and the preflight's `lint` on `main`) as the factory's own user; a `container` instance runs each in a check container.

### The init

The service sets `init: true`, so the container's first process (PID 1) is the container runtime's own init: Docker's `docker-init` (tini, mounted at `/sbin/docker-init`) or Podman's `catatonit` (mounted at `/run/podman-init`). The init starts the entrypoint, forwards the stop signal to the factory and reaps every process whose parent has ended. Without it the factory's Python would be PID 1 and reap only its own children. Then every agent run killed at its `time_limit` under `sudo` leaves `claude` and what it started as zombies, `[claude] <defunct>` of `agent` with parent 1, until the container restarts. The same holds for the processes of a project command killed at its time limit. A container started without Compose needs `--init` (`docker run --init`, `podman run --init`). Under Podman this is first observed at the shakedown. If under Podman the container does not start because the runtime finds no init binary, or PID 1 is the factory's Python and not `catatonit`, the Compose provider or the Podman machine does not honour `init: true`: note it, and expect the zombies to pile up until the container restarts.

### The entrypoint

`image/entrypoint.sh` is the container's entrypoint. Every line it writes starts with a UTC time stamp. In order, it:

1. checks that the image holds `claude/agents` and `claude/settings.json` under `/opt/factory`; if one is missing it writes `missing <path>` to standard error and exits with status 1;
2. replaces `agents` in the Claude home with a copy of the image's (an agent file no longer in the image is gone) and copies `settings.json` next to it: `installed agents and settings into <home>`;
3. creates `/state/runs` if needed and sets its mode to `2750`: `prepared /state/runs`;
4. writes `starting instance <name>` and starts the factory (`python -m factory.entry.run`) from `/opt/factory` with `exec`, so the factory runs as the init's child, not as PID 1, and no shell stands between them.

It sets no git configuration; the factory's git gets its identity and credential helper from the factory itself. For tests, `FACTORY_OPT`, `FACTORY_CLAUDE_HOME` and `FACTORY_STATE` move the three directories; leave them unset in a container (the factory reads `FACTORY_STATE` too, as the state directory; the image leaves it unset).

### The health check and the restart policy

Docker runs `python -m factory.entry.health` every 30 seconds (10 seconds to answer, three failures to be unhealthy, 60 seconds of grace at the start). It reads `health.json` in the state directory, `/state` unless `--state-directory <path>` names another (on the VM, the directory `FACTORY_STATE` names). With no stop it prints `healthy` and exits 0; when the file is missing it prints `no health status: <path> is missing` and exits 1 (`factory-run` writes an empty status when it starts, so a missing file means the instance has not started or the check reads another state directory; Docker counts the failure only after the 60 seconds of grace); with stops it prints one line per stop and exits 1:

```
preflight_failed (machine): tool:make: make is not on the PATH (since 2026-10-12T08:00:00Z)
```

So `docker compose -f image/compose.yml ps` shows the container as unhealthy while any repository or machine stop stands, and `docker compose -f image/compose.yml exec factory python -m factory.entry.health` names the stops. The container becomes healthy again by itself when the factory clears the stop. A stop of a work item is not in the health status. The stops this container can show in its health status are in "The stops", with what to do about each.

`restart: unless-stopped` brings the container back after a crash or a reboot. A container whose process is dead is left to that policy: the factory builds no watchdog. Under Podman the health check reports `starting`, then the text of a stop in force, with exit 1. Not yet checked on a running instance: `docker compose ps` over a container with a stop in force. Under Podman a machine or host restart does not bring the container back: see "Podman: the restart" under "Container runtimes".

### The preflight's items

The preflight is a list of seven items for an `inline` instance (five for a `container` one), and of up to twelve with the machine's extras (`inline`: `token-file`, `agent-environment`, `opencode` under opencode only, and `agent-run-probe`; `container`: `token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `opencode` under opencode only, and `agent-run-probe`, twelve in all; an `inline` one has eleven at most), in the order of the table. Every item runs whatever the others found, so one report names everything that is wrong. A failed report becomes one `preflight_failed` stop with scope `machine`; its detail lists each failed item as `<name>: <detail>`, joined by `; `. The preflight installs nothing: a missing tool is reported and you fix the image. The items run only when the image build has changed (see "The stamp and the probe of the main branch").

| Item | Passes when | If it fails |
|---|---|---|
| `tool:git`, `tool:uv`, `tool:make` | the tool is on the `PATH`; a `container` instance has no `tool:make` (see below) | The detail is `<tool> is not on the PATH; add it to the image`. Add the tool to the image and rebuild. |
| `tool:<claude>` | `inline` only: the executable of the runtime in force (`FACTORY_CLAUDE`, default `claude`; under opencode `FACTORY_OPENCODE`, default `opencode`) is on the `PATH`; the item is named after the value, for example `tool:/opt/claude/bin/claude` | As for the other tools. |
| `hosting-service` | a read-only call (the open pull request of `main`) is answered | The detail holds the operation and the service's message. Check the token (`FACTORY_TOKEN_FILE`) and the network. |
| `agents` | at least one agent file is in `FACTORY_CLAUDE_HOME` (`<it>/agents/<role>.md`) | The detail names the directory, whether it is empty, missing or unreadable. Install the agents into `FACTORY_CLAUDE_HOME`. |
| `agent-runtime-version` | the first word of the runtime's `--version` equals the pin of the runtime in force (`FACTORY_CLAUDE_VERSION`; under opencode `FACTORY_OPENCODE_VERSION`) | The detail names both versions (`the agent runtime reports 2.1.290, the image pins 2.1.289`): rebuild the image or change the pinned version. Without the pin it says `the image does not pin a version: FACTORY_CLAUDE_VERSION is not set` (`FACTORY_OPENCODE_VERSION` under opencode); when `claude --version` cannot run, it holds the runtime's error. |
| `token-file` | `FACTORY_TOKEN_FILE` names a file that exists, in a folder that belongs to the factory's user and has no permission bit for group or others (the file's own mode does not count) | The detail is `<path>: <fault>`; see "The hosting-service token" for the four faults and the fix. |
| `agent-environment` | the agent run's `HOME` is an existing directory | The detail names each fault: `the agent run has no HOME` or `the agent run's HOME <dir> is no directory`. Create the factory user's home. |
| `opencode` | under opencode only: for `inline`, the opencode executable is on the `PATH` of the agent run's environment; for `container`, no executable is looked for, since it is the stage image's and `agent-runtime-version` runs it there. Both: `FACTORY_OPENCODE_MODELS` maps every alias the installed agents use | The detail joins its faults with `; `, the executable's first (`inline` only). `<executable> is not on the agent run's PATH <path>` (or `the agent run has no PATH`): install opencode where the agent user finds it, or correct `FACTORY_OPENCODE`. `no model is set for <alias> in FACTORY_OPENCODE_MODELS`: add `<alias>=<provider>/<model>`. The item asks for no API key: see "Running on opencode". |
| `podman` | `container` only: `podman --version` answers; the detail is its first line (`podman version 4.9.3`), which the factory log names once per image build | The detail is `podman does not answer --version: <the error>`. Install `podman` where the factory runs, or correct `FACTORY_PODMAN`. |
| `zfs` | `container` only: `zfs --version` answers; the detail is its first line | The detail is `zfs does not answer --version: <the error>`. Install ZFS, or correct `FACTORY_ZFS`. |
| `dataset` | `container` only: `zfs list -H -o name <dataset>` names `FACTORY_DATASET` | `the dataset <dataset> does not exist; make it with zfs create, and its base with zfs snapshot <dataset>@base`: do that, once. When `zfs list` itself fails, the detail is `cannot list the dataset <dataset>: <the error>` (for example a permission the factory's user lacks). |
| `stage-image` | `container` only: `podman image exists <FACTORY_STAGE_IMAGE>` answers yes | `the stage image <image> is not built; build it with podman build`. When podman cannot answer, the detail is `cannot look for the stage image <image>: <the error>`. |
| `agent-run-probe` | one `claude -p` call, or one `opencode run` call under opencode, made as a stage makes it, ends `completed` | See "The probe of the agent run" below. |

A `container` instance does not run the items of the layers the container replaces, and each is named here with its reason:

- `agent-environment`: the agent's `HOME` is `/work/home`, a path inside the container, not a directory on the factory's machine.
- `tool:claude` (`tool:opencode` under opencode): the runtime's executable is the stage image's and not on the factory's `PATH`; `agent-runtime-version` runs it in the stage image, and fails if it is missing.
- `tool:make`: a `container` instance runs `make` only inside its sync and check containers.

#### The probe of the agent run

`agent-run-probe` runs the agent runtime once, with the factory's own arguments: the project's agent `coder` (`factory/agents/coder.md` on `origin/main`) or the installed one, a budget of 0.10 dollar, a fixed one-line prompt, the decision `question` only, a time limit of 2 minutes, as the factory user, with the agent run's environment and a guard that gives no write path. For a `container` instance the dataset is prepared for `main` first, as a stage's is (the sync container runs on `origin/main` and the base moves), so the run starts on a clean copy; two faults are added: `no origin/main to prepare the stage environment from` (the clone has no `main`: nothing is run), and the message of the snapshot or container command that failed, such as `snapshot command reset failed: no base at <path>` (the dataset has no `@base`: make it with `zfs snapshot <dataset>@base`) or `container command sync failed: <last output line>` (`make sync` failed in the sync container). It costs a few cents. Like the other machine items it runs once for each image build and is skipped while the image is unchanged.

It fails with `the probe run ended <reason>; run claude -p by hand as the factory user to see why` (under opencode `run <executable> run by hand as the factory user to see why`, with no token hint) when the run does not end `completed`. When `FACTORY_CLAUDE_LOGIN_FILE` is set, the detail ends with `; the agent's login token is read from <file>: make it with claude setup-token if it is missing, empty or expired`. When the probe ran with the API key, the detail ends instead with `; the agent's API key is read from <file>: check that it is valid and that its account has credit`. A login file that cannot be read or is not ASCII text fails the item with the runtime's message, `cannot read the agent's login file <file>: ...`, or `cannot read the agent's API login file <file>: ...` for the API key. The usual causes are a flag the pinned `claude` rejects (every real run would end `died` with no text that says why), a login missing for the factory user (a missing or expired token when the detail names the login file; otherwise log in as that user and keep the login in its `HOME`), and a run that ran out of its budget or time. A state directory that cannot be written fail it with the runtime's own message, and a missing agent `coder` fails it with the reader's message naming the agent. All of these stop the machine before any work item is claimed.

Under opencode, an image built before the folder `/home/agent/.config/opencode` was added (see "Running on opencode") ends this probe `died` in each new container, and the instance stops: rebuild the image.

Under opencode a failed probe whose login was `none` ends with `; the agent runs get no API key: log in once as the factory user with the opencode build's own login, or put a key in the file FACTORY_API_LOGIN_FILE names`.

When the probe completes, the item passes and the factory log gets one line with its detail, which names the login in force: `the agent runs log in with the API key from <file>`, `the agent runs log in with the subscription token from <file>`, or `the agent runs get no login from a file; the runtime uses the login kept in its home`.

The items read the instance's settings, so the three variables `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE` and `FACTORY_CLAUDE_VERSION` are the ones to check first; under opencode, `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`. The commit identity is not an item.

The detail of `preflight_failed` also takes a form that is no item: `the probe on main could not run: <message>` means the probe of the main branch (see "The stamp and the probe of the main branch") itself failed, because git or `make` could not run or the checkout is gone: fix the machine, not `main`. For a `container` instance the message may also be a snapshot or container command that failed while the dataset was prepared for `main`, for example `the probe on main could not run: container command sync failed: boom` or `the probe on main could not run: snapshot command reset failed: no base at <path>`.

### The stamp and the probe of the main branch

`Preflight.run` remembers what it has passed in `preflight-stamp.json` in the state directory: the image identity the machine's items passed on, and the commit of `origin/main` whose `lint` passed or failed. The stamp holds no time and no timer expires it.

- **The machine's items** run when the stamp's image differs from the instance's image identity, when there is no stamp, and on every call when the instance has no image identity. While the image build is unchanged they are skipped, however much time passes. A failed report writes no stamp, so the items run again at the next call.
- **The probe** runs the project's `lint` command with a `time_limit` of 10 minutes, on the main branch only: it puts the checkout on `main` at `origin/main` first, and for a `container` instance prepares the dataset for that commit before `lint` runs in a check container. A red `lint` on a work item's branch never fails the preflight. The probe runs only when `origin/main` is a commit the stamp has not seen, and after a new image build (a new build forgets what was probed). The preflight does not fetch; the tick that calls it does.
- **A red `lint` is a stop.** The probe raises `main_branch_failing` with the detail `lint is red on main at <12 characters of the commit>: <last line of the output>`, or `lint reached its time_limit on main at <commit>` when `lint` ran out of its time.
- **A red `main` is probed once.** The failing commit is remembered, so an idle tick runs no project command while the stop stands. If `health.json` loses the stop meanwhile, the next call raises it again with the detail `lint is red on main at <commit> (probed earlier)`, without running `lint`.
- **A fix clears it.** When you push a new commit to `main`, the next call probes it, and when `lint` passes the stop `main_branch_failing` is cleared. A call that ends without a probe error also clears a standing `preflight_failed` stop.
- **A failed machine clears a stale stop.** While the machine's items fail the probe cannot run, so a `main_branch_failing` is cleared when the stamp's failing commit is no longer `origin/main` (a fix was pushed, or `main` is gone) and the call still returns `preflight_failed`. The new `main` is probed when the machine's items pass again, and a red one raises the stop anew. A stop whose commit is still `main` stays, and so does a stop when git cannot resolve `origin/main`. The exception is a `main` that differs from the failing commit only in `factory/stops.jsonl`: see the next bullet. If git cannot compare the two (the failing commit is not in the clone), the stop is cleared. The stamp is not rewritten.
- **A `stops recorded` commit is a new `main`.** The probe runs again for it once the machine's items pass. While they fail (`preflight_failed` stands), the stale-stop rule above keeps `main_branch_failing` when every path that differs between the stamp's failing commit and the checkout is `factory/stops.jsonl`, so no `cleared` record is written for a `main` nobody fixed. A commit that also changes another file clears the stop.
- A repository with no commit on `main` has nothing to probe, and the preflight passes once the machine's items have.

Deleting `preflight-stamp.json` is safe: a missing or damaged stamp reads as no stamp, and the only cost is one more run of the machine's items and of the probe. The agent can read the file and cannot write it.

### The wait for a repository that is not ready

Before each tick the instance checks that `origin/main` exists and holds `factory/pipeline.yml`. When it does, nothing is fetched here (the tick fetches) and any `repository_unavailable` stop is cleared. When it does not, the instance fetches once, looks again, and if the fault stays it raises the stop and skips the tick; the loop pauses as for any idle iteration and tries again. The stop is written once per detail: the same fault on the next iteration adds no second line, a different fault adds a new one. Push the missing branch or file and the next iteration clears the stop. The detail says which fault it is:

- `cannot prepare the checkout: <git's message>`: the clone failed. Check `FACTORY_REPOSITORY_URL` and the credentials.
- `cannot fetch: <git's message>`: the fetch failed.
- `the repository has no main branch yet`: the repository has no commit on `main`.
- `origin/main has no factory/pipeline.yml yet`: push `factory/pipeline.yml` to `main`.

## Container runtimes

### The runtimes

The image and the compose file run under Docker Desktop and under rootless Podman with the docker-compose v2 binary as its Compose provider (seen with Podman 5.8.3 on Windows). Rancher Desktop with its moby engine is expected to work like Docker but is untested, because the probe did not run it. A Mac is not probed.

For a team, the setup is one shared Linux host (Docker Engine, or rootless Podman with the restart service below) that runs every instance, each its own compose project, rather than a runtime on every laptop.

### Podman: the commands

Every `docker` command of this guide works with `podman` in its place: `podman build`, `podman exec`, `podman compose -f image/compose.yml up -d`. Inside the container the users, groups, modes and the token's folder are the image's. On the machine the named volumes belong to sub-ids that are invisible inside.

On Windows a shell may not see the Podman machine's saved connection, and a command then fails with `connection "podman-machine-default" not found`. Run `podman system connection list` where the connection is seen: it shows its URI and identity file. Give them on each command with `podman --url <URI> --identity <identity file> ...`, for example `podman --url <URI> --identity <identity file> ps`. Whether `podman compose` hands them on to its Compose provider is not observed, so run `compose` from a shell that sees the connection.

### Podman: the Compose provider

`podman compose` hands the compose file to an external provider. Use the docker-compose v2 binary (standalone, Apache 2.0), named with `PODMAN_COMPOSE_PROVIDER` or with `compose_providers` in `containers.conf`. `podman-compose` 1.5.0 cannot build this compose file on Windows: it fails with `no Containerfile or Dockerfile specified or found in context directory`, from `context: ..` with `dockerfile: image/Dockerfile`.

### Podman: the restart

`restart: unless-stopped` stays in the compose file. It brings the container back after a crash and after `podman restart`, but not after the Podman machine or the host restarts. Docker Desktop restarts it by itself once it runs (its "start when you sign in" setting).

On Windows, under Podman, nothing restarts the factory after a machine or host restart. `systemctl --user enable podman-restart.service` in the WSL machine fails with `Failed to enable unit: Access denied`, and an `unless-stopped` container stayed `Exited` after `podman machine stop` and `podman machine start`. The operator runs `podman machine start` and then `podman compose -f image/compose.yml up -d`, by hand or as a scheduled task at logon.

Until then the container stays `Exited (0)`: no tick runs, nothing is claimed or pushed, and the health check does not run, so nothing shows unhealthy. A lease the instance held expires. Once started, the factory goes on as after any restart (see "A restart during a stage").

On a Linux host, `podman-restart.service` (it starts the containers matching `should-start-on-boot=true`) with `loginctl enable-linger` is the documented way. This was not tested here. The observation left to the first start on such a host: with the service enabled and linger on, a restart of the host brings the container back `Up` in `podman ps -a`. It is not observed yet.

### Podman: the disk

The disk record and the stop `disk_low` see the Podman machine's virtual disk, not the host drive, as under Docker Desktop. "What the container cannot see" names both runtimes.

## The factory log and the health status file

Both live in the factory's state directory. `factory-run` starts the factory; this describes what it writes; the next section says when a stop is written and when it goes away.

### The factory log

The factory log writes every line twice: to standard output and, appended, to a file (UTF-8, lines end in `\n`). A line is `<stamp> <text>`. The stamp is `YYYY-MM-DDTHH:MM:SSZ`: UTC, whole seconds (a fraction is cut off, not rounded). One call can hold several lines, and they all carry one stamp, because the clock is read once per call:

```text
2026-10-12T12:00:07Z first
2026-10-12T12:00:07Z second
2026-10-12T12:00:12Z third
```

**The stage environment's timing line.** An instance with the `container` stage environment writes one line per stage, after the take: `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s`, each in seconds with one decimal, for example `stage environment: reset 0.4 s, sync 12.3 s, advance 0.1 s, take 0.2 s`. `reset` and `advance` are the dataset's roll-back and the move of its base, `sync` the sync container (`make sync` included), `take` the copy of the agent's result into the checkout; read the cost of a stage's setup from these lines in `/state/factory.log`. An `inline` instance writes none.

Missing parent directories are created. If the file cannot be written, the line has still reached standard output, and the write fails with an `OSError`.

### The health status file

`health.json` in the state directory holds the stops in force for the repository or the machine, as one JSON object: `{"stops": [{"scope": ..., "reason": ..., "detail": ..., "at": ...}]}`. The container's health check reads it (see "The container: compose, entrypoint and health check"); an empty `stops` list is healthy.

- One stop per reason. `scope` is `machine` for `preflight_failed` and `disk_low`, and `repository` for every other reason; `detail` names the fault and is never blank; `at` is in UTC.
- The reasons are `fetch_failed`, `checkout_restore_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `repository_unavailable`, `main_branch_failing`, `preflight_failed` and `disk_low`.
- `factory-run` writes an empty status (`{"stops": []}`) when it starts and finds no file, before it reads the token file; an existing file is left as it is, its stops in force. If that write fails, `factory-run` fails with the `OSError` and clones nothing.
- A file that is missing reads as not healthy for the health check (`no health status: <path> is missing`, exit 1). A file that cannot be read, is not JSON or is not a valid status reads as healthy (no stops). Do not repair it by hand: the next stop that is raised replaces the whole file, and a fault that lasts is raised again.
- A write goes to a temporary file in the same directory and replaces `health.json` in one step, so a reader never sees half a file. If `health.json` is a directory, the write fails with an `OSError` and leaves nothing behind.

### The records

The state directory's `records/` folder holds four JSON Lines files. None is committed; the tick publishes the stop records to `factory/stops.jsonl` on `main` (see "The stop records on main"). `project-commands.jsonl` holds every project command run (below), `known-results.jsonl` is described in "The known results", `stops.jsonl` in "The stop records" and `disk.jsonl` in "The disk record". A line of any of them that a kill cut, or that is not UTF-8, is skipped when the factory reads the file, so a damaged record file needs no repair. A record appended right after a line a kill cut shares that line and is skipped with it; a whole line that is not UTF-8 costs only itself.

`records/project-commands.jsonl` in the state directory (`/state/records/project-commands.jsonl`) holds one JSON line for every project command the factory runs (`check`, `lint`, `test` and the rest), whoever asked for it: the stage checks after an agent, the preflight's probe and the check of `main`. The folder is created on the first run. A line has these fields:

| Field | Meaning |
|---|---|
| `command` | The make target, for example `check`. |
| `commit` | The 40-character commit of the checkout's `HEAD` when the command started; `null` when it cannot be read. |
| `started_at` | When the command started, UTC with an offset. |
| `duration_seconds` | How long it ran, in seconds. |
| `status` | `passed`, `failed` or `time_limit`. |
| `exit_status` | The exit status; `null` for `time_limit`. |
| `targets` | For each target that ended green, `{"target": ..., "seconds": ...}`, in the order printed (for `check`, the time of each of its targets). |

`project-commands.jsonl` is telemetry beside the factory log, not a work item's state: nothing reads it to decide anything. You may delete the file at any time; the next run starts a new one. A command that raises an error (a missing `make`, a time limit of 0) leaves no record. When a line cannot be written, the factory log gets `cannot write the record of <command>: <error>` and the run goes on.

To count the `check` runs of each commit, with the most-run commits first:

```bash
python3 -c "import json,collections as c; print(c.Counter(r['commit'] for r in map(json.loads, open('/state/records/project-commands.jsonl')) if r['command']=='check').most_common())"
```

A commit that appears more than once was checked more than once.

#### The known results

`records/known-results.jsonl` in the state directory holds one JSON line for each run of a stage's check or report and for each time the factory took an earlier result instead of running it. After an agent the factory runs every check and report of the stage; when the last run under the same key passed, it does not run the command again. The preflight's probe and `project-commands.jsonl` are not part of this: the probe still runs, and `project-commands.jsonl` still holds every real run and no reuse. A line has these fields:

| Field | Meaning |
|---|---|
| `key` | What the result depends on: `command`, `tree`, `definition` and `image`. |
| `at` | When the factory started the run or took the result, UTC. |
| `status` | `passed`, `failed` or `time_limit`. |
| `last_line` | The last line of the command's output. |
| `duration_seconds` | How long the command ran; 0 for a reuse. |
| `reused` | `null` for a real run; for a reuse, the `at` of the run it took. |

The key has four parts:

- `command`: the make target.
- `tree`: the tree the command reads, as `Git.work_tree_id` names it for the command's `not_read` (see "The pipeline definition").
- `definition`: the SHA-256, in hex, of the whole pipeline definition.
- `image`: the machine's image (see "The image on the cost records"), `null` without one.

A known result is invalidated by a change in any part: a changed file the command reads, a merge of `main` that brings one, any change of the pipeline definition (a time limit, a stage, any value), or a new image. A change only in left-out files keeps the key.

- A failed or timed-out result is never reused. The last real run of a key decides: a pass, then a failure of the same key, ends the reuse of the pass until a new run passes.
- A reuse is a record too, with the time of the run it took, so no check is silenced and the runs of a tree can be counted.
- Only the factory's own runs are known. What an agent ran itself is not.
- Deleting the file forgets every known result: the next run of each command runs it.

When something goes wrong the command runs as it did before, and the factory log says why, in one line:

| Line | Meaning |
|---|---|
| `known results: no key for <command>: <error>` | The tree could not be named; the command ran and nothing was recorded. |
| `known results: cannot read the records: <error>` | The file could not be read; the command ran. |
| `known results: cannot write the record of <command>: <error>` | The line could not be written; the result is still used. |

To count the `check` runs of each tree, the most-run first (a reuse is not counted):

```bash
python3 -c "import json,collections as c; print(c.Counter(r['key']['tree'] for r in map(json.loads, open('/state/records/known-results.jsonl')) if r['key']['command']=='check' and r['reused'] is None).most_common())"
```

#### The stop records

`records/stops.jsonl` in the state directory holds one JSON line for each event of a stop of the repository or the machine. A line has these fields, in this order: `event` (`raised` or `cleared`), `scope` (`machine` for `preflight_failed` and `disk_low`, `repository` for the rest), `reason`, `at` (UTC, ending in `Z`) and `instance` (the instance's name). It never holds the stop's detail:

```text
{"event":"raised","scope":"machine","reason":"disk_low","at":"2026-10-18T10:00:00Z","instance":"self"}
```

- `raised` is written when a stop of its reason is raised and the health status held none of that reason. A stop raised again every cycle while it lasts writes nothing more. `cleared` is written, after the status and the `stop cleared` line, when a stop of that reason stood and is removed; clearing a reason that does not stand writes nothing.
- A raise whose health status cannot be read writes no `raised` record. The next raise that can read the status finds no stop standing and writes it. A stop that clears before the status is readable again therefore never reaches the records; its line is still in the factory log.
- When the record cannot be written, the other destinations were still tried and the factory reports the `OSError` as for the log and the status.
- The factory never clears this file. The tick publishes its records to `main` (see "The stops"), and a record is pushed once. Delete the file only when `main`'s `factory/stops.jsonl` holds every line of it; a record deleted before it was pushed is lost.

#### The disk record

`records/disk.jsonl` in the state directory holds one JSON line each time the factory measures its folders: `at` (UTC with an offset), `occasion` (`start` or `acceptance`) and `folders`, a list of `{"path", "free_bytes", "used_bytes"}` for the work directory (the checkout's parent), the state directory and the process's temporary directory (`/tmp` in the container), in that order. `free_bytes` is the free space of the file system the folder is on; `used_bytes` is the size of what is under it. A value the factory could not read is `null`.

The same record is one line in the factory log, for example `disk start: /work 812.3 GB free, 0.7 GB used; /state 812.3 GB free, 0.0 GB used; /tmp 812.3 GB free, 4.3 GB used`, each value in GB or `unknown`.

It is written at each start of the instance, before the first tick, and at each feature acceptance. No record is written at the end of a run. Compare the new line with the last one to see whether disk use grows. When the line cannot be written, the factory log gets `cannot write the disk record: <error>` and the run goes on. It is not committed; the factory uses only its last record that reads whole, to name the previous measure beside the new one at a feature acceptance.

The size of a folder counts only what the factory user can read. The agent's own folders under `/tmp`, made by pytest or Claude Code with mode `0700`, are left out, while the free space of the file system still shows them.

The record cannot see the host. Read the host's own numbers by hand at the same moments and at the end of a run: the free space of the drive, and the size of Docker's disk image (`docker system df`).

## The stops

Every stop the factory raises has one destination. A stop of the repository or the machine goes to the health status and to a line of the factory log. A stop of one work item goes once on that work item's pull request. One case, a backlog story that names a later stage in its own file, has no stop. Every line about a stop in the factory log is time-stamped (see "The factory log").

| Stop | Destination | What you do |
|---|---|---|
| `fetch-failed` | health status and factory log | `git fetch` failed, an expired or revoked token included. Fix the network, the address or the credentials; see "The stops of the tick". |
| `checkout-restore-failed` | health status and factory log | The checkout cannot be put on `origin/main` (the dirty main branch). Fix the cause or delete the checkout and clone again; see "The stops of the tick". |
| `pipeline-definition-invalid` | health status and factory log | `factory/pipeline.yml` on `origin/main` fails its validation, an agent that is not installed included. See "The stop `pipeline_definition_invalid`". |
| `agent-definition-invalid` | health status and factory log | An agent file holds a key the runner does not apply. See "The stop `agent_definition_invalid`". |
| `repository-unavailable` | health status and factory log | The entrypoint or the tick waits for a repository that is empty or has no pipeline definition. Push `main` with `factory/pipeline.yml`; see "The wait for a repository that is not ready". |
| `main-branch-failing` | health status and factory log | `lint` fails on the main branch. Push a fix to `main`; see "The stamp and the probe of the main branch". |
| `preflight-failed` | health status and factory log | A preflight item fails, or the settings are invalid. Fix what the detail names; see "The preflight's items" and "When the process refuses to start". When the state directory cannot be written, `factory-run` still ends with status 2 but writes no stop: the settings fault reaches standard error as two lines without a stamp. Check the `state` volume. |
| `disk-low` | health status and factory log | The work or the state directory has less free space than `FACTORY_MIN_FREE_GB` asks for, or its free space cannot be read. Make room on the file system the detail names, and nothing more: the next tick clears the stop. |
| `duplicate` | pull request | Two work items have one id. Keep one file and rename or delete the other; see "Stops that cannot be done". |
| `pull-request-lookup` | pull request | The one pull request lookup fails. Fix the cause named after the colon; see "Stops that cannot be done". |
| `ask-without-pull-request` | pull request | A question is recorded for a work item that has no pull request. Open one for the branch or push a commit to it; see "Stops that cannot be done". |
| `handler-error` | pull request | A handler fails on the same event and state three times. See "An event that keeps failing". |
| `hand-over-error` | pull request | A hand-over fails every time, three ticks in a row. See "When the hand-over fails or is killed" and "An event that keeps failing". |
| `push-rejected` | pull request | A push is rejected, for example by a hook of the remote. No agent is run while it lasts. See "An event that keeps failing"; fix the remote's rule or push to the branch to start the count again. |
| `later-stage-in-backlog-file` | no stop | A backlog story whose own file names a later stage in its front matter. The start rule removes it: the work item starts at the first stage with `round`, `attempts` and `crashes` at 0, and nothing is reported. |

The ids are those of `STOP_TABLE` in `factory.domain.stop_table`, and the reasons in the health status are the same words with underscores.

### The stops of the repository or the machine

When the factory finds a fault of the repository or the machine, it raises a stop in two places, and tries both: a line in the factory log and an entry in the health status file. A stop of this kind never goes to a pull request; look in the log and in `health.json`.

The line when a stop is raised:

```text
2026-10-12T12:00:07Z stop repository fetch_failed: origin unreachable
```

That is `stop <scope> <reason>: <detail>`, after the stamp. `scope` is `repository` or `machine`; `reason` is one of the reasons listed under the health status file.

The line when the fault is gone:

```text
2026-10-12T12:00:12Z stop cleared fetch_failed
```

That is `stop cleared <reason>`. It is written only when the stop was in the health status; clearing a reason that is not stopped writes nothing.

- The health status holds one stop per reason. A stop raised again for a reason already there replaces the earlier one where it stood (with the new detail and time); it is not added twice. A new reason is added at the end. A fault that lasts is raised every cycle, so the log repeats the line and the status does not grow.
- A stop is removed from the health status, then the cleared line is written, when the factory finds the fault gone. You never clear one by hand; deleting `health.json` only hides it until the next cycle raises it again.
- One failing destination never loses the stop. If the log file cannot be written, the stop is still put into the health status; if the health status cannot be written, the line still reaches standard output and the log file. In both cases the factory then reports the write error (an `OSError`); when both fail, it is the log's error. If the health status cannot be written while a stop is cleared, the stop stays in force and no cleared line is written. If the log cannot be written while a stop is cleared, the stop is already removed.

### The stop records on main

Every raise and every clear of a stop of the repository or the machine is also a record (see "The stop records"). Each tick, right after it restored the checkout and before the preflight, pushes the records that `origin/main` does not hold to `factory/stops.jsonl` on `main`, as a commit with the subject `stops recorded`. The records carry the event, scope, reason, time and instance, without the detail, which stays in the factory log.

- A tick that ends before the restore succeeded (`disk_low`, `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `checkout_restore_failed`) publishes nothing. The records wait in the state directory for the next tick that gets past the restore, so a `fetch_failed` is published after the fetch works again.
- A failed push (for example a rule of the remote that refuses `main`), any other git error or a file that cannot be written leaves the records where they are and writes one line, `cannot publish the stop records: <error>`; the tick goes on and tries again next tick. Nothing is lost and nothing is pushed twice.
- **Pull `main` before you push to it.** The factory pushes `main` after a stop event as well as after an archive. If you push first the factory's push is refused and succeeds on the next tick; if the factory pushes first, yours is refused until you pull.

### The stops of one work item

A stop of one work item (a question, a cap reached) is meant to appear as one comment on that work item's pull request. A question is first recorded (a journal entry of kind `question`, with `blocked` set, committed and pushed) and then posted; see "The factory's own questions". The rules below are those of the factory's stop comment, which the dispatcher's error report posts (see "An event that keeps failing"). A stall does not follow them: it has its own rule, given under "A stall: the stall note". A posted comment says what each possible answer will do, and it ends with the factory's marker and the stop's key:

```
<!-- factory -->
<!-- factory key=F0001-S0001:stall:3 -->
```

- If the work item has no pull request yet, the factory opens a draft pull request first, on the work item's branch (`work-item/<id>`), and posts the stop there. The description says: "The factory opened this draft pull request to report a stop on <work item>. The stop is the comment below."
- It opens one only when the branch is on the remote with a commit beyond `main`. Otherwise it opens nothing, posts nothing and reports a `create_pull_request` error: `branch <branch> is not on the remote with a commit beyond main`. The factory pushes the branch before it can report a stop, so you see this only if the remote branch was removed or reset.
- If the work item's branch already has an open pull request, the factory posts on that one. A pull request you closed or merged is not reused for a new one; but when the work item's state records a pull request number, the stop is posted there even if you have since closed it.
- A restart never repeats a stop. The key identifies the stop: if the factory died after posting and before recording it, the next attempt finds the key on the pull request and posts nothing. The same key with another text is still a repeat; a different kind or number is a new stop and a new comment.
- The posting writes no state. In particular the dispatcher does not record the number of a pull request it opened for an error report; a later stop finds that pull request by its branch.
- Two files with one id are both read: the second is read from `origin/main` as a started story, because the id's branch holds only the first file. So the duplicate is reported on the first work item's pull request and does not end the tick.

## What a stage run shows

One stage run leaves these traces on the remote and the pull request, in this order:

1. **The draft pull request.** The first stage of a work item opens it, titled `<id>: <title>`, with the work item's text as the description. Only an open pull request is reused; a closed or merged one never is, and a new draft is opened instead.
2. **The stage-start commit.** It is pushed before any agent runs. It holds the claim and one journal entry, speaker `factory`, kind `started`, with the text `factory: started <stage> as <instance>.` (for example `factory: started doing as factory-1.`). If this push fails, no agent runs.
3. **The agent's entry.** The speaker is the agent's role and the kind is `result`, or `question` when the agent asked; code writes both, the agent writes the words. For each green check and each report the entry ends with one line `` `<command>`: <last line of its output> ``, for example `` `check`: 12 passed ``. A result the factory took instead of running the command names the run it took and says that the command did not run: `` `check`: check: green (not run again: passed on tree 0123456789ab at 2026-10-18T15:20:01Z) `` (the first 12 characters of the tree, and the start of that run in UTC). See "The known results". A report stopped at its time limit gets ` (stopped at its time limit after <seconds> s)` at the end of its line, for example `` `test`: ........ [ 87%] (stopped at its time limit after 600 s) `` (the tests stage's `make test`, stopped at its 10 minutes). Its last line is then only what it printed last, and the records hold `time_limit`.
4. **One commit by the factory**, directly above the stage-start commit: the result commit, or the stall commit after a stall. The agent cannot commit, because the checkout's `.git` is the factory's alone (see the decision log's "The factory alone writes the checkout's `.git`"). It holds the whole work tree.
   A stage that moves the work item to an approval also writes the pull request's description after the result commit and before its push, so the description is complete when the board first shows the approval. If that push fails, the description may already show the reports while the work item stays at its stage.
5. **The label** `stage:<stage>` (written so, for example `stage:review`) on the pull request. It is written after the result commit is pushed, and after a stall's note is posted. It is a projection of the stage and is never read back.

While an agent runs, the work item's `.costs.jsonl` is modified in the work tree and not committed: it holds the running run's record, which the result commit or the stall commit carries. An agent that mentions it in its entry has seen the factory's file, not made a change of its own.

If the push of the result commit fails, no label is written. If the hosting service fails at the label, the commit stays pushed.

## A stall: the stall note

A stall is a stage that ended without a result the factory can keep. The causes are the eleven listed below; the first ones are an agent run that died, ran past its time limit, spent its budget (and the resume too), or gave no valid decision and entry. A stall costs one attempt of the work item and is never a crash. The factory keeps what the agent wrote inside the stage's write paths and leaves out the rest (an `inline` instance undoes it; a `container` instance does not take it from the dataset), releases the claim and pushes one commit with a `stall` entry in the journal. Only then does it post the stall note on the pull request and write the pull request's `stage:` label for the stalled stage, so a work item whose first stage stalls has its label too. The note's key is `<work item>:stall:<n>`, where `n` is the number of the stall entry.

The note reads:

```text
Stalled (attempt 1 of 2): the agent run died without a result. Retrying on the next tick.
```

- `attempt n of m`: `n` is the work item's attempts after this stall; `m` is `attempts_cap` of the pipeline definition.
- The cause is one sentence. The reasons are: the agent run died without a result; it reached its time limit; it spent its budget, and the resume too; the provider's spend limit lasted past the waiting ceiling; the agent gave no valid decision and entry; the agent's decision is not an allowed one; the agent left the work item's branch; the work item's form broke during the stage; a check is red after the stage; merging the main branch conflicts and the merge was aborted; the agent left a git repository in the work tree, which the factory removed (the detail lists the paths). A detail, such as the name of a red check, follows the sentence after a colon. A detail of several lines (the output of a red check) puts its first line in the sentence and the other lines in a code block below it; see "A stall by a red check".
- The cause `the provider's spend limit lasted past the waiting ceiling` (`provider_limit`) means the factory waited out the provider's limit for the whole ceiling and the limit was still there. Nothing for you to do for one such stall: the next tick tries again. If it repeats, see "A provider's spend limit", "What to do at the ceiling".
- The note says "Retrying on the next tick." only while `n` is below `m`. Nothing for you to do then; the next tick runs the stage again from what the stall kept.
- At the cap the note ends `The attempts cap is reached; the factory asks you next.` and says nothing about retrying. At the cap the evaluation makes the event `ask` with the detail `attempts cap`. The `ask` handler records the attempts-cap question and posts it (see "The factory's own questions"). You read the cause and the stall entries in the work item's journal, fix what stops the stage (the agent, the stage's time limit or budget, the pipeline definition, the project's checks, a conflict with `main`), and answer on the pull request; the factory does not run the stage again until you have.
- The stall's pull request: an open pull request of the work item is reused; otherwise the stall opens a new draft titled `<id>: <title>` with the work item's text as description. It does not use the stop description, and it does not post on a closed pull request.

If the hosting service fails while the note is posted, the stall commit is already on the remote, no note is posted and no label is written. If it fails while the label is written, the note is posted and the label is missing. The error is reported, and the work item shows the stall in its file and journal.

## A stall by a red check

When the agent decides to move forward and the stage has checks, the factory runs them itself, in the order of the pipeline definition, and stops at the first that is red. A check is green only when its make target exits 0. A red check is a stall that costs one attempt; the stage, the round and the crash count stay. On the pull request you see the stall note with the cause `a check is red after the stage` and, after a colon, the check's name; below the sentence, in a code block, come the last 15 lines of its output (all of them when it printed fewer). The block keeps GitHub from rendering the output as Markdown. A note looks like this:

````text
Stalled (attempt 1 of 2): a check is red after the stage: `check`. Retrying on the next tick.

```text
  File "x.py", line 1, in <module>
make: *** [Makefile:6: check] Error 1
```
````

In the work item's journal the agent's entry comes first, ending with one line per check that was green, and the `factory` stall entry follows.

What to do:

- Below the attempts cap nothing: the next tick runs the stage again, and the agent sees the journal.
- At the cap, read the 15 lines and run the target yourself (`make check`) on the work item's branch. Fix what is wrong (the code, the target, or a tool missing on the machine), then answer on the pull request. At the cap the evaluation makes `ask` (`attempts cap`), the attempts-cap question described under "The factory's own questions" then appears on the pull request, and your comment answers it.
- Reports (the stage's `reports`) run after all checks are green. They are recorded and never hold a move. Every report that ran adds one line `` `<command>`: <last line of its output> `` to the agent's entry, passed or failed; the line has the same form either way, so only its last line shows whether the report passed. A report stopped at its time limit is the exception: its line ends with the stop note (see "What a stage run shows"). A failing report holds nothing and stops nothing.

The result commit of every stage holds the whole work tree. Make sure the project's `.gitignore` covers whatever its checks create (build output, caches, coverage files); otherwise the factory commits it.

## The factory's own questions

Besides an agent's `question`, the factory asks you itself. Every question reaches you in two steps: it is recorded first, as a journal entry of kind `question` in the work item's file (committed and pushed, with `blocked` set), and only then posted as one comment on the pull request. If the factory dies or the post fails between the two, the question is already recorded and the next attempt posts it once: the comment's key is made from the recorded entry's number, and a post whose key the pull request already holds is a no-op. The factory does both steps when it handles `ask`.

The questions you can meet on a pull request, and how to answer each:

| Question | `blocked` | Comment reads | A comment | Closing the pull request |
| --- | --- | --- | --- | --- |
| An agent's | `question` | `<role>: <the agent's words>` | answers it; the stage runs again | discards the story |
| The form has findings | `question` | `factory: ` and the findings question (`The work item's form has findings, so the stage cannot move forward: ...`) | answers it; the stage runs again | discards the story |
| The round cap | `round_cap` | `factory: ` and the round-cap question (`This work item has now been sent back <n> times, more than <cap>. ...`) | answers it; the count of rounds starts over at 0 | discards the story |
| The attempts cap | `attempts_cap` | `factory: ` and the text below | the attempts go back to 0 and the stage runs again | discards the story: it goes back to the backlog as you wrote it, and its branch and bill are deleted |
| The send-back | `send_back` | see "A close at the approval sends the story back" | answers it | discards the story: it goes back to the backlog as you wrote it, and its branch and bill are deleted (option 2 of the question). The send-back has already moved the story out of the approval, so a close cannot send it back again |
| The crash cap | `crash_cap` | `factory: ` and the text below | the crash counter goes back to 0 and the stage runs again | discards the story: it goes back to the backlog as you wrote it, and its branch and bill are deleted |

The attempts-cap question is recorded by the `ask` handler itself, when a work item has used all its attempts: an entry by `factory` of kind `question`, and `blocked` set to `attempts_cap`. It reads:

```text
Stage doing stalled 2 times. The last time: the agent gave no result

Comment anything to retry: the attempts go back to 0 and the stage runs again. Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
```

The last time is the text of the work item's latest `stall` entry. A work item at the cap with no stall entry cannot be asked about, and is a counted error. Comments you write while a question waits to be posted are recorded after it; the post stays keyed to the question's own entry.

### Which comment answers a question

A comment answers a question when it was written after the factory posted that question. The factory handles a `comment` like this for a work item that waits (`blocked` is set):

- Your comments are copied into the journal and, in the same commit, the wait ends. The answer is read from ids and keys, never from what you wrote; a blank comment is marked read but does not answer.
- A comment written before the question was posted is only recorded and the wait stays. The same holds when the question is recorded but not posted yet, and when the only post on the pull request belongs to an earlier question. Comment again once the question is on the pull request.
- Each answer clears the wait and resets only what belongs to that wait: `attempts` go back to 0 for the attempts cap, `crashes` go back to 0 for the crash cap, `round` goes back to 0 for the round cap, nothing else. The round cap's answer starts the count of rounds over, and that count also holds the send-backs of the approval; the factory does not read your words, so an answer cannot grant exactly one more round. An answer to any other wait keeps `round`: after the approval's send-back question (`send_back`) the count stays, so the next send-back past the cap asks the round cap question once more.
- A comment on a work item that does not wait for you, at an approval stage for instance, is only recorded; `stage`, `round`, `attempts`, `crashes` and the hand-over are untouched.
- A comment event that keeps failing is tried three times on the same remote state and then reported once on the pull request, like every other event (see "An event that keeps failing"). The factory's own comments (those with its marker) never answer.

- **The form has findings.** The agent decided to move forward, but the work item's form still has findings after the run. The comment reads: `The work item's form has findings, so the stage cannot move forward: 1. <message> 2. <message>. What should happen? Answer with a comment; the stage then runs again. Close the pull request to discard the work item.` The stage stays where it is and the round is not counted. Answer with a comment (say how to fix the form, or that the finding is wrong); the stage then runs again. Closing the pull request discards the work item.
- **The round cap is passed.** A stage with `round_cap` sent the work item back once more than the cap allows. The comment reads: `This work item has now been sent back <n> times, more than <cap>. What should happen? Answer with a comment, which starts the count of rounds over; close the pull request to discard the work item.` The stage stays where it is and the round shows the count. Answer with a comment: `round` goes back to 0 and the stage gets its rounds again. Closing the pull request discards the work item.

A stage without `round_cap` sends back without limit and never asks. Sending back counts rounds; a stall counts attempts (see "A stall"), and the two caps are separate.

### The reviewer's notes and added criteria

Three things in a reviewer's entry are not findings in the usual sense. From round 1 on, a point that is only about the quality of a test file the story adds (a copied helper, a name, a duplicate test) goes under `Notes:` after the findings, one line each with its location; the notes do not send the story back, so read them at the approval. The first review, at round 0, still sends such a point back. A point on a criterion, the architecture, security or `src/` is a finding at every round. When the diff builds a behaviour that no criterion names and pinning it needs no code, the reviewer writes the criterion into the story itself and names it in its entry as `criterion <n> added: it needs its test`; the coder changes no code and the tester writes the test. That is a send-back like any other and counts a round, so the round cap may still ask you afterwards.

When a story's Description has gone stale against what it built, and the human's answers, the Interface or the criteria settle what it should say, the reviewer rewrites the stale sentences itself. Its entry names each correction as `description corrected: <what it said> -> <what it says now>`, one line each. That is not a send-back and counts no round; read those lines at the approval. A Description the code contradicts with nothing to settle it still comes back as a finding or a question.

## The stop `pipeline_definition_invalid`

The pipeline definition is `factory/pipeline.yml` as it stands on `origin/main`, never the file in the work tree. The factory loads it each cycle, and a load that refuses it raises the stop `pipeline_definition_invalid` (scope `repository`): a line in the factory log and an entry in the health status, nothing on a pull request.

```text
2026-10-12T12:00:07Z stop repository pipeline_definition_invalid: missing key: contract
```

The detail is the fault. The faults the load reports:

| Fault | Cause and what to do |
|---|---|
| `factory/pipeline.yml is missing at origin/main` | the file is not on `main`; merge it |
| a fault of the text, such as `missing key: contract`, `unknown key: <path>`, `invalid <path>: <message>`, `not valid YAML: <problem> (line <l>, column <c>)` | fix `factory/pipeline.yml` on `main`; several faults are joined by `; `. A YAML fault is one line with a 1-based position, for example `not valid YAML: found duplicate key "done" with value "{}" (original value: "{}") (line 27, column 3)` (a stage key written twice; the factory refuses a repeated key on purpose) |
| a fault of the rules across keys, such as `stage doing: next names unknown stage ship`, `contract major 2 is not supported (this factory reads major 1)`, `role coder: write_paths is empty`, `role coder at stage doing: 61 min exceed lease_duration 60 min` | fix `factory/pipeline.yml` on `main`; see "The pipeline definition" for the rules you meet most often and `docs/project-guide/stages.md`, "The rules of the definition", for the full list |
| `role <role>: agent is not installed` | the role has neither a file `factory/agents/<role>.md` on `origin/main` nor a file `<agent home>/agents/<role>.md`; add one of them. Every missing role is named, in the order of `roles`, joined by `; ` |
| `agent home unavailable: <fault>` | `<agent home>/agents` is missing or is not a directory (see "The agent files") |

The agents are checked only when the text itself is valid, so a broken file and a missing agent home show the file's fault alone until it is fixed. A key with a default may be left out and takes it; a key without one that is missing is a fault.

The stop clears itself at the next load of `origin/main` that succeeds, with the line `stop cleared pipeline_definition_invalid`; stops of other reasons are not touched. Only the load of `origin/main` raises or clears this stop: a look at the definition on another branch can be refused, but it changes neither the health status nor the log. A git failure while reading (an unreachable repository, an unknown ref) is not a fault of the definition and raises no stop. If the health status cannot be written, the load reports an `OSError` and not the fault; the log line has been written. What the cycle does while the stop stands is described with the tick.

## The stop `agent_definition_invalid`

Once the pipeline definition on `origin/main` is valid, the load reads the agent file of every role, in the order of `roles`. A file the reader refuses (most often a key the agent runtime does not apply, see "The agent files") raises the stop `agent_definition_invalid` (scope `repository`). The detail is `<agent name>: <fault>`, and the first refused role is named:

```text
2026-10-16T12:00:07Z stop repository agent_definition_invalid: coder: key not applied by the agent runtime: permissionMode
```

The tick ends there and nothing else happens: no stage is started and no event is handled. To fix it, edit the named file and remove or correct the key the detail names. For a shipped agent that is `<agent home>/agents/<agent name>.md`. For a project's own agent the detail names the file and the ref, `<agent name>: factory/agents/<agent name>.md at origin/main: <fault>`, and the fix is a commit on `main`: a branch's copy is never read, and the installed agent does not stand in for a faulty project file. The next tick loads again and clears the stop with the line `stop cleared agent_definition_invalid`. A role whose agent is not installed is a fault of the definition and shows as `pipeline_definition_invalid`, because the other checks come first. As for that stop, only the load of `origin/main` raises or clears this one.

## The stops of the tick

A tick works from the remote alone: the checkout is disposable. It reads the free space first, before the fetch (see "The low disk" below), then fetches, loads the pipeline definition from `origin/main`, puts the checkout back on `main` at `origin/main`, publishes the stop records (see "The stop records on main"), and only then looks at the work items. Four repository stops, and the machine stop `disk_low`, end a tick before it looks at any work item; each is a log line and a health status entry, never a comment on a pull request. The next tick tries again and clears the stop when the fault is gone.

The four stops are `fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid` and `checkout_restore_failed`; "The stops" says what to do about each. An expired or revoked token shows as `fetch_failed`, and nothing is lost: the next tick after a successful fetch carries on. The tick does not touch the checkout while `pipeline_definition_invalid` or `agent_definition_invalid` stands.

`checkout_restore_failed` comes, for example, from an untracked file or directory the factory cannot remove, or from an ignored folder it cannot empty; its detail is git's message. When an agent run left the path, the stage that ran ends without a result; once the checkout is repaired, the factory records it as a crash and runs it again. Repair with `chmod -R g+w <path>` as root on the path git's message names, or remove it as root. A second run that leaves the same path again reaches the crash cap (`crash_cap`).

The restore throws away every uncommitted change and every untracked file in the checkout, ignored paths too (`.venv`, the caches, `mutants/`, `.reports/`), and deletes the local branches of the work items, so that a stage starts from the remote's branch. When it throws changes away it writes one line to the log, `discarded uncommitted changes: <path>, <path>`. The factory also removes the ignored paths after every agent run that returned. Do not keep anything in the factory's checkout.

A work item file that cannot be read is not a stop. The tick ends with the error, naming the file's path, and does so on every tick until a human repairs the file (on its branch, or on `main` for a started story without a branch) or moves the story out of `in-progress/` on `main`. Closing the pull request changes nothing: the tick reads every story in `in-progress/` before it looks at any pull request. A work item in a stage that the pipeline definition lacks fails the same way.

### The low disk

At the start of every tick, before the fetch, the factory reads the free space of the work directory (the checkout's parent) and of the state directory. When either has less than `FACTORY_MIN_FREE_GB` (exactly the minimum is enough), it raises the machine stop `disk_low` and ends the tick; nothing is fetched or written after it. The detail names each short directory with its free space, the work directory first. A free space that cannot be read is the same stop, with the detail `cannot read the free space of <path>: <error>`, and no later path is read. The first tick that finds enough room clears the stop. The preflight runs inside the tick, so this one check covers it.

What you do: make room on the file system the detail names. A checkout that is missing is cloned before the first check, by the iteration's preparation (see "The checkout is cloned again when it is missing or its `.git` is not the factory's alone"), so a clone onto a full disk fails as `repository_unavailable` first. On a full disk the stop's own writes (`health.json`, the factory log) can fail with an `OSError`; the iteration then ends with the `iteration failed` line (see "The loop and its pauses") and the next one tries again.

### The preflight in the tick

The tick runs the preflight (see "The preflight's items" and "The stamp and the probe of the main branch") after the fetch, the load and the restore, and before the cleanup of stale branches and before anything is evaluated. So the probe sees the `origin/main` the tick has just fetched: a fix you pushed is probed on the next tick, and a commit that broke `lint` stops that same tick. A tick the preflight stops (`main_branch_failing` or `preflight_failed`) does nothing else: no stale branch is deleted, no work item is read, no agent is started and no pull request is touched. The tick returns the reason as its outcome, and the stop is in the log and in `health.json`. An invalid pipeline definition ends the tick earlier, before the restore and the preflight, so it does not raise `preflight_failed`.

## The pipeline definition

`factory/pipeline.yml` is the project's configuration: its stages, the roles that work in them and the limits. The factory reads it only as it stands on `origin/main`, so a change takes effect when it is merged. This definition loads:

```yaml
contract: '1.0'
roles:
  tester:
    write_paths: ['tests/*', '{work_item}']
  coder:
    write_paths: ['src/*', '{work_item}']
stages:
  testing: {role: tester, next: [doing], checks: [lint]}
  doing: {role: coder, next: [review], checks: [check]}
  review: {approval: true, next: [done, doing], round_cap: 3}
  done: {}
```

The keys, with what a left-out key takes:

| Key | Meaning | Default |
|---|---|---|
| `contract` | the contract version, quoted: `'1.0'` | required |
| `stages` | name to stage; the order in the file is the pipeline's order | required |
| `roles` | name to role; the name is also the agent file's name | required |
| `project_commands` | name to `time_limit` in minutes and, optionally, `not_read` (see below) | `check`, `lint` and `test`, each 10 and `not_read: []` (the template's definition also names `sync`, 5 minutes) |
| `attempts_cap` | attempts before the human is asked | 2 |
| `crash_cap` | crashes before the human is asked | 2 |
| `acceptance_stage` | the stage of the feature acceptance | none |

A stage has `role` (none: no agent runs), `next` (the first name is the forward move), `approval` (the human decides), `checks` (project commands that must pass after the agent), `reports` (project commands run after green and only recorded) and `round_cap` (none: no cap). A role has `write_paths` (required), `lease_duration` (60 minutes) and `time_limit` (40 minutes, one agent run). A write path may hold `{work_item}`, the work item's own file, and `{feature}`, its feature's path (`factory/features/F0004-x`). The engine's protected paths (`factory/pipeline.yml`, the forms, `feature.md`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `.claude/`, `factory/agents/`) are outside every write path. Every limit is a positive whole number.

An unknown key is refused with `pipeline_definition_invalid`. That includes `tool_paths`, which earlier versions read: a definition that still holds it stops the factory until you remove the key. The write paths are all that an agent run may write; there are no further folders for tool state.

`not_read` of a project command lists the paths the command does not read, in the form of `write_paths` patterns: relative to the checkout, `*` also crosses `/`, case-sensitive. The default `[]` leaves nothing out. For example:

```yaml
project_commands:
  check: {time_limit: 10, not_read: ["README.md", "docs/*.md"]}
```

A pattern that cannot name a path inside the checkout (empty, starting with `/` or `~`, holding a `..` segment, or holding `{` or `}`) stops the definition from loading: `project command lint: not_read /etc/* must be a path pattern inside the checkout`. `not_read` is what lets a known result survive a change: the paths it names are left out of the tree that the key holds (see "The known results"), so a change only there is no reason to run the command again. List only what the command does not read at all. A linter, formatter or type checker that walks the whole tree reads every source file in every folder, so leave out file types it does not read, never a whole folder. A forgotten path costs one run; a path listed by mistake can let a reused `check` pass a fault.

factory-rf's own definition, `factory/pipeline.yml`, takes this, and only Markdown and JSON Lines files, because `make lint` reads every Python file of the tree, wherever it lies:

```yaml
project_commands:
  check: {time_limit: 8, not_read: ["README.md", "docs/*.md", "factory/features/*.md", "factory/features/*.jsonl", "factory/stops.jsonl", "planning/*", "session-logs/*"]}
```

Two warnings:

- A project whose `check` scans changed files for secrets keeps a scan of the left-out files only if something else runs it. factory-rf's docs stage runs `secrets` as a check of its own, with nothing left out.
- A command whose result depends on anything outside the tree and the image, such as dependencies fetched at run time with unpinned versions, is reused safely only when those versions are pinned in the tree (for example by a lockfile). Otherwise leave `not_read` empty and do not rely on reuse for it.

The rules you meet most often:

- The stage `done` must exist, with no role and no `next`. Write it `done: {}`; `done:` alone is refused.
- The contract major must be 1. Any minor is read.
- Every stage other than `done` needs a non-empty `next` and either a role or `approval: true`; every name in `next` must be a stage.
- The lease: for each stage with a role, the role's `time_limit` plus the `time_limit` of every command in the stage's `checks` and `reports` must be at most the role's `lease_duration`. With the defaults, 40 + 10 (one check) + 10 (one report) = 60 fits; a stage with two checks and a report adds up to 70 and is refused. Raise the `lease_duration` or lower a limit.
- Values are taken only in their YAML type: a limit is an integer (not `'30'`, `30.0` or `true`), `approval` is `true` or `false` (not `'yes'` or `1`), names and write paths are text. A write path must hold a character that is not whitespace.
- A key that is not listed is refused, so a misspelt key is never ignored. A given `project_commands` replaces the default set as a whole: list `check`, `lint` and `test` again if you still want them. `sync` is a project command with a `time_limit` like the others (`sync: {time_limit: 5}` in the template), and the stage environment reads that limit for its sync container; no stage lists it in `checks` or `reports`, so it never enters a lease. A definition without `sync` gives the sync the default limit of 10 minutes.
- Every role needs an agent file, a project's own or the installed one (see "The agent files").

A refused definition raises the stop `pipeline_definition_invalid`, described above. `docs/project-guide/stages.md`, "The rules of the definition", lists every fault.

## The agent files

An agent is a file `<name>.md`: the project's own, `factory/agents/<name>.md` on `origin/main`, or the installed one, `<agent home>/agents/<name>.md`. The name is lowercase letters, digits and hyphens, starting with a letter (`coder`); `README.md` and `Coder.md` are not agents, nor is a file with another suffix or one in a subdirectory. Every role of the pipeline definition needs an agent file of the same name, from either place.

The file is YAML front matter between two lines of three hyphens, then the agent's instructions:

```
---
model: sonnet
tools: [Read, Write]
effort: low
budget_usd: 0.1
---
The agent's instructions.
```

| Key | Meaning |
|---|---|
| `model` | required, text |
| `tools` | required, a list of texts; `[]` is allowed |
| `effort` | optional, text |
| `budget_usd` | required, a number greater than 0 |

The body, without the whitespace around it, is the instructions; a line of hyphens inside it belongs to it. These four are the only keys the agent runtime applies: Claude Code ignores an agent file in print mode, so the runner builds its flags and its prompt from them itself. Any other key (`name`, `description`, `permissionMode`, `hooks`, `background`, `disallowedTools`, `skills`, a misspelt one, or a known key in another case such as `Model`) would read as if it did something and do nothing, so the file is refused when the pipeline definition is loaded. See "The stop `agent_definition_invalid`".

The reader reports these faults. `read` names the agent; a fault with a key names that key.

| Fault | When |
|---|---|
| `no agents directory at <path>` | `<agent home>/agents` is absent or not a directory |
| `not an agent name: <name>` | the name is not a valid name, so no file is looked up |
| `no agent file <path>` | the file is absent or is a directory |
| `cannot read: <reason>` | the file cannot be read or is not UTF-8 |
| `no front matter` | the file does not start with front matter that is closed |
| `front matter is not valid YAML` | the YAML does not load |
| `front matter is not a mapping` | it loads as a list or a scalar |
| `key not applied by the agent runtime: <key>` | the front matter holds a key outside the four above; the first such key in the file's order is named |
| `missing key: <key>` | `model`, `tools` or `budget_usd` is left out |
| `budget_usd must be greater than 0` | zero, negative, text or a boolean |
| `invalid <key>: <reason>` | any other value of the wrong type |

When a file has several faults, the first is reported: a key that is not applied before a missing key, and a missing key before an invalid value.

### A project's own agents

For each role the factory reads `factory/agents/<name>.md` from `origin/main` first, at every tick, the same ref as the pipeline definition. When the project has no such file it uses the installed agent. A project's agent replaces the installed one whole and never extends it: nothing is merged, so a key or a line of instructions you leave out is not taken from the shipped file. To change a shipped agent, copy it from `claude/agents/` in the image's source, put the copy at `factory/agents/<name>.md` and change the copy.

The file follows the same rules as any agent file: the same four keys, the same faults. A fault of a project file is named with its place, `factory/agents/<name>.md at origin/main: <fault>`, for example `factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour`. The load of every tick and the preflight's probe check it, and a faulty project file is never replaced by the installed one: the stop `agent_definition_invalid` stands until a commit on `main` fixes it.

- **A new role.** Add the role to `factory/pipeline.yml` and its file under `factory/agents/`, in one commit on `main`. A role whose only agent is the project's own needs no installed file.
- **Back to the shipped agent.** Remove `factory/agents/<name>.md` from `main`.
- **A branch's copy is never read.** A work item's branch, or an uncommitted edit in the checkout, changes nothing; only `origin/main` counts, so a work item cannot change its own agent. A file under `factory/agents/` is a protected path (the human's), and an agent that writes there is refused.
- **The probe.** The preflight's `agent-run-probe` runs the project's `coder` when there is one, once for each image build; a faulty file fails the item with `agent coder: factory/agents/coder.md at origin/main: <fault>`.

### A project's own skills

A project may bring skills under `.claude/skills/` in its repository. Every shipped agent has the `Skill` tool and loads a skill whose description fits its work. The agents' own instructions win where a skill contradicts them (rule R15): the agent follows its instructions and names in its entry the skill and the step it set aside.

The skills are the human's files, like `CLAUDE.md`: `.claude/*` is a protected path that no stage writes, and the factory does not check what a skill says. `.claude/` is protected at any depth (`.claude/*` and `*/.claude/*`), so no stage writes a `.claude/` folder anywhere in the repository, `src/.claude/skills/` included (the human, 2026-10-19). The undo removes a nested `.claude/` write after every run, under either runtime. The kernel cannot refuse it inside a folder a write path opens, so the undo is what catches a write there. A run reads the root `.claude/skills/` from its checkout, the work item's branch.

Only Claude Code's runs are given the `Skill` tool. An opencode run leaves it out (the runtime turns on no opencode tool for it and does not refuse the agent), and the factory does not check whether opencode loads skills of its own.

### The shipped agents and settings

The image ships seven agents (`intake`, `tester`, `coder`, `reviewer`, `documenter`, `smoke-tester`, `acceptance-reviewer`) and `settings.json`. Each agent's `tools` ends with `Skill`, and the settings allow it in `permissions.allow`, right after `Grep`. The entrypoint installs them into `FACTORY_CLAUDE_HOME` at every start, so an edit made there by hand is gone at the next start; change the files in the image instead. The settings let an agent run `factory-check-story` and no other `factory-` command: it cannot run `factory-run`, `factory-watch` or `factory-bill`. They also deny `git add` and `git commit`, because an agent leaves its changes in the working tree and the factory makes the result commit (an agent user has no git identity of its own), and `git push`, `gh` and the commands that move or rewrite branches, because the factory alone pushes. A new project starts from `template/` in the image (a pipeline definition, a `CLAUDE.md` and a `Makefile` whose `SOURCE` and `LAYERS` placeholders you fill in); the story and feature forms are yours to add, and every stage stops until `factory/story-form.md` exists.

## The records contract

A reader outside the factory, such as a page that shows a factory's records from GitHub, may rely on these records and on nothing else:

| Record | Where | Schema |
|---|---|---|
| the front matter of a work item | the story file; for an acceptance report, its file | `work-item-state`; `acceptance-state` for an acceptance report |
| one line of a work item's cost records | `<work item>.costs.jsonl` | `cost-record` |
| one line of the stop records | `factory/stops.jsonl` | `stop-record` |
| the pipeline definition | `factory/pipeline.yml` | `pipeline-definition` |

The Markdown body of a work item, the text of the journal entries included, is for people. Never parse it.

The schemas are JSON Schema files (draft 2020-12) in `src/factory/contract/`, named `<schema>.schema.json`. They are generated from the models that validate each record and are never written by hand. A story that changes one of those models regenerates them in the same change; `make check` fails when a committed file differs from what the models give. To regenerate them, or to write them into another folder:

```bash
uv run python -m factory.entry.contract [<folder>]
```

The command prints `contract: 5 schemas written`. With two or more arguments it prints `usage: python -m factory.entry.contract [<folder>]` to standard error, writes nothing and exits with status 2. The files are package data, so they ship in the wheel, and a reader in another repository can fetch them from `main`.

**Where a work item's records are.** While the work item is in progress they are on its branch `work-item/<id>`: the factory writes the front matter and the sidecar there at every stage. From the merge on they are on `main`, moved to `done/` by the archive commit. A work item in `in-progress/` on `main` without a merge shows only the state it had at its start.

**The approval.** A work item enters the approval with its last `result` record in the journal. No record marks the entry, so a reader takes the approval's start from that record's `at` and its end from the `done` record's `at`.

**The version.** Each schema carries the records contract's version in `x-records-contract`, now `2.0` (`1.1` added the cost record's optional `login`; `1.2` added the end reason `provider_limit` to the cost record's `end_reason` and the stall reason `provider_limit` to the `reason` of the journal records in `work-item-state` and `acceptance-state`; `1.3` added the optional `not_read` of a project command to `pipeline-definition`; `2.0` removed `tool_paths` from `pipeline-definition`, a change that can break a reader, since the schema no longer allows the key). The major version rises for a change that can break a reader: a field removed or renamed, a type narrowed, a meaning changed. The minor version rises for an added optional field or value. This version is not the `contract` of the pipeline definition, which is the version of the definition's own format (see "The pipeline definition").

**Unknown properties.** The schemas say `additionalProperties: false` for what this version of the factory writes. A reader still ignores a property it does not know, since a later minor version may add one.

## Checking a story before it starts

`factory-check-story` checks story files against where they sit and against your project's `factory/story-form.md`. Run it from the root of a checkout, with the paths relative to that root. The checkout must be laid out the v1.1 way: `factory/story-form.md`, a `feature.md` in each feature's directory, and the stories in `backlog`, `in-progress` or `done`.

In a project laid out the v1.1 way (the paths are placeholders):

```bash
uv run factory-check-story factory/features/F0001-example/backlog/F0001-S0001-example-story.md
```

prints `factory/features/F0001-example/backlog/F0001-S0001-example-story.md: ok` and exits 0 when the story fits the form.

`uv run python -m factory.entry.check_story <path>...` does the same. For each path, in the order given, it prints `<path>: ok`, or one line per finding: `<path>:<line>: <message>` where the finding has a line (a line of the story's text after the front matter, counted from 1), and `<path>: <message>` where it has none. Findings about where the file sits come first, then those about its content.

| Status | Meaning |
|---|---|
| 0 | every file is ok |
| 1 | at least one file has a finding |
| 2 | the command could not do its job: no path (it prints `usage: factory-check-story <path>...`), `factory/story-form.md` unreadable, or a file that does not exist or is not UTF-8 (`cannot read <path>: <reason>`). Nothing more is checked after such a file; what was printed before stays. |

A path must be `factory/features/<feature directory>/<backlog|in-progress|done>/<file>.md`. Otherwise the only line is `not a work item location: ...` and the file is not read (it need not exist). `drafts` and `ongoing` are v1's folders and not work item locations, so they are not accepted.

How a file is read depends on its folder and on whether it has front matter. A story in `backlog` is read as a specification: front matter there is a finding. A story in `in-progress` or `done` with front matter is read as a work item and its state is checked too. A story there with no front matter is a started story as you moved it on `main`, where the state lives on the work item's branch; it is checked like a backlog story, with no complaint about missing state.

Findings about the place, and what to do:

| Finding | What to do |
|---|---|
| `the file name "<name>" is not F0000-S0000[-slug].md` | rename the file; an acceptance's name is not a story's |
| `the feature directory "<directory>" is not F0000[-slug]` | rename the directory |
| `the story <id> is in the directory of feature <id>` | move the story to its own feature's directory, or fix its id |
| `the feature file feature.md is missing in factory/features/<directory>` | add the feature's `feature.md` |

Findings about the content follow the form check (`docs/project-guide/work-items.md`, "The form check of a story"):

| Finding | What to do |
|---|---|
| `the story has no title line` | start the story with a `# Title` line |
| `missing section: ## <heading>` | add the section your story form lists |
| `criterion numbered <n> where <m> is expected` | renumber the criteria 1, 2, 3 |
| `the second-to-last criterion must contain "make check" and "green"`; `the last criterion must start with "docs:"` | make those the two closing criteria |
| `the Smoke test has no code block`; `the code block opened at line <n> is not followed by an "Expect:" line` | give each block of the smoke test an `Expect:` line after it |
| `journal entry numbered <n> where <m> is expected` | renumber the journal entries |
| `a backlog story carries no front matter: <keys>`; `a backlog story carries no journal entries` | remove the front matter or the entries; the factory writes them when the story starts |
| `the story has no state`; `the journal data lists <n> entries but the text shows <m>` | for a file with front matter in `in-progress` or `done`: the state is damaged, so restore the file from its work item's branch |
| a reader fault such as `unknown key: <key>` or `front matter is not valid YAML` | fix the front matter; no form findings are given until it reads |

## What a work item cost: `factory-bill`

Every agent run writes a cost record beside its work item; it holds the run's duration, the time the model took, the turns, the tokens and the cost. `factory-bill` adds the records up and prints the bill. Run it from a checkout of your project:

```bash
uv run factory-bill F0001-S0001
uv run factory-bill
```

With an id it prints the cost table, an empty line and `Cost: <line>`. With no argument it does that for every work item in flight, each block headed by its id and separated from the next by an empty line. A work item in flight is one that has a branch `work-item/<id>` on the remote.

The command reads the remote-tracking refs only (`origin/<the work item's branch>`, or `origin/main` for an archived work item), never your working tree and never the journal. It does not fetch: run `git fetch` first to see the latest records. Two checkouts that have fetched the same remote show the same bill.

| Exit status | Meaning |
|---|---|
| 0 | the bill was printed (with no argument, also when nothing is in flight) |
| 1 | `no work item <id>`: no file of that id on the remote |
| 2 | `not a work item id: <argument>`, or more than one argument (`usage: factory-bill [<work item id>]`) |

A work item with a file but no cost records has a bill of 0 runs and $0.00.

### The cost table

```
| stage | runs | min | model min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: |
| tests | 1 | 1.0 | 0.7 | 7 | 62 | 1000 | 300 | 0.35 |
| doing | 2 | 2.5 | 1.8 | 5 | 10 | 500 | 100 | 1.20 + 1 unknown |
| **total** | 3 | 3.5 | 2.5 | 12 | 72 | 1500 | 400 | 1.55 + 1 unknown |
```

One row per stage, in the order the stage first ran; a stage that runs again (`doing`, `review`, `doing`) is one row. The last row is the total.

| Column | Meaning |
|---|---|
| runs | agent runs, every one counted whatever its end: a run that died, ran past its time limit or spent its budget is in the bill |
| min | the runs' duration in minutes, one decimal |
| model min | the minutes the model took, from each run's `model_seconds`, one decimal; `min` less `model min` is the time of the tools and the factory; a run without `model_seconds` adds nothing |
| turns | the turns the runtime reported |
| in | input tokens plus cache-creation tokens |
| cached | tokens read from the cache |
| out | output tokens |
| USD | the cost in dollars, two decimals |

Figures are rounded half up.

When the factory posts the table on the pull request (see "The hand-over at the approval"), a line follows it after an empty line:

```
Human: 2 questions answered (question 1, crash_cap 1), 1.5 h waited
```

It counts the questions that stopped the work item for you: the agent's question and the stops `round_cap`, `send_back` and `crash_cap`. A question counts once you have answered it, by a comment or by closing the pull request; the close counts as an answer too. The parenthesis names each cause and how many were answered, and is left out when none was. The hours are the time from each question to your next record in the journal, summed. A question you have not answered yet counts in neither figure. The wait can be up to one tick too long, because a comment is dated when the factory copied it from the pull request, not when you wrote it. `1 questions answered` is the wording for one as well. `factory-bill` prints the table only, without this line.

### Refused tool calls in the sidecar

A completed record in the sidecar (`<work item>.costs.jsonl`) can carry two more keys: `denials`, the number of tool calls the agent runtime reported as refused in that run, and `denied_paths`, the files those calls named, each once, in the order reported. A third key, `login`, says which login the run's calls were handed: `subscription`, `none` or the value that names the API key; a runtime with no login file leaves it out. A run that got no reply (it died or ran past its time limit) has neither of those two keys; an older line has none of the three. Only the tool calls the runtime reports as refused are counted. A refusal that is only text in a tool's output, such as a write the kernel refuses, is not in them. `factory-bill` does not print these keys.

### The cost line

The line under the table sums the same figures: `3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55 + 1 unknown`.

### An unknown cost

A run whose cost the runtime did not report (a run that died, or one the time limit ended) has an unknown cost. It is not counted as $0.00: it is left out of the sum and shown as `+ <n> unknown` after the dollars, where `<n>` is the number of such runs. Unknown turns and tokens are left out of their sums in the same way, without a mark; so the figures are a lower bound when `unknown` is shown.

## Looking at the remote: `factory-watch`

`factory-watch` is the window on what the factory would do next. It evaluates once, as a tick would after its fetch, except that it judges its own instance's claim by the lease, since a tick never looks while its own stage runs. It prints two things: the event of that evaluation, and the board. It has no options; `--help` shows its usage.

It reads the remote-tracking refs as the last tick left them. It fetches nothing, so after a push to the remote the output stays the same until a tick has fetched. It writes nothing: no file in the checkout, nothing to the remote or the hosting service, no health status entry, no log line. It loads the pipeline definition at the head commit of `origin/main` and raises or clears no stop. The one hosting-service read it makes is the one an idle tick makes: the pull request (and its comments) of a waiting work item.

```
event: <key>  <detail, when there is one>

features
F0001  Todo service  backlog=1  in-progress=2  done=3  acceptance=-
work items
F0001-S0001  Domain model  in-progress  stage=tests  blocked=-  claim=factory-1  running_since=2026-10-14T09:30:00Z  pull_request=7
```

- The first line is `event: <key>`, followed by two spaces and the detail when the event has one.
- A feature row counts the story files in `backlog`, `in-progress` and `done`; `.gitkeep`, `feature.md` and files that are not work item names do not count, and a feature with no story file has no row. The title is the first `# ` title of the feature's `feature.md` on `origin/main`, else the directory's name. `acceptance` is the feature's acceptance status (`incomplete`, `due`, `in_flight`, `merged_unrecorded`, `accepted` or `refused`; see "When a feature acceptance is due"), or `-` when the pipeline definition has no `acceptance_stage`.
- A work item row exists for each story in `in-progress/` and for each running acceptance (one that is opened, waiting with a question or at its approval, or merged and not yet booked), with its title (the first `# ` title of the body, else the id), its stage, what it waits for (`blocked`), the instance holding its claim, since when (`running_since`, the claim's start in UTC) and its pull request. An absent value is `-`. The rows are in id order, so an acceptance's row comes after its feature's stories and before the stories of a later feature. An acceptance's title is `Acceptance of <feature title>`, its folder `in-progress`, and its state is the one on its branch.
- A claim of the instance `factory-watch` runs as shows as `event: idle:-  <work item> is held by <instance>` while its lease runs, because the instance may be running that stage, and as `event: crash:<work item>` once the lease has run out. The tick itself still reruns its own claim at its first look after a restart, whatever the claim's age. A stage that waits out a provider limit holds its claim past its lease, so it shows as a crash here while it waits; the factory log's line of the wait tells the two apart. A live stage that uses every limit can show as a crash for up to about a minute past its lease. The board's rows are the same either way.
- Exit status: 0 after printing; 1 when the pipeline definition on `origin/main` is invalid or an agent file is refused (the fault goes to standard error as `factory-watch: <fault>`, or `factory-watch: agent <name>: <fault>` for an agent file; standard output stays empty, no stop is raised); 2 for an unknown option, and when the environment is invalid or the token file cannot be read: then `factory-watch: settings invalid: <variable>: <fault>` goes to standard error (never a traceback) and standard output stays empty. `factory-watch` reads the same environment as `factory-run` (see the table above) and builds its boundaries the same way, so it looks at the instance the container runs. A repository whose `origin/main` does not resolve (a clone that never fetched) ends with a git error.

## When a feature acceptance is due

A feature's acceptance is due when the feature is complete and no recorded report covers exactly its archived stories. This is worked out from the files on `origin/main` (and the remote acceptance branches) alone, never from the checkout's work tree or a local branch. It applies only when the pipeline definition has an `acceptance_stage`; without one nothing is ever due.

A feature is complete when:

- it has at least one story file in `done`, and
- no story file waits in `backlog` or `in-progress`.

Only story files count (`F0001-S0001-name.md`), and only directly in `backlog/`, `in-progress/` or `done/`: a story file in a subdirectory (`done/old/F0001-S0001-name.md`) neither archives a story nor keeps the feature incomplete. A `.gitkeep`, a `README.md`, a note and an acceptance's report beside the stories never keep a feature incomplete, and never make it complete.

A report covers the archived stories when it is at `done` on `main` and its `stories` list equals the set of archived stories. A report that lists fewer or more stories does not cover them, so a story archived after an acceptance makes the feature due again.

The status of a feature is the first of these that applies:

| Status | Meaning |
| --- | --- |
| `in_flight` | A report is on its own remote branch `work-item/<F0001-A0001>` and not yet on `main`. |
| `merged_unrecorded` | A report is on `main` but not at `done`: the acceptance was merged and its result is not recorded yet. |
| `incomplete` | The feature has no archived story, or a story file waits in `backlog` or `in-progress`. A recorded result does not stand while a story file waits. |
| `accepted` or `refused` | A report at `done` covers exactly the archived stories; this is its outcome. With several covering reports the highest id decides. |
| `due` | None of the above: the acceptance is waiting to be started. |

A remote branch `work-item/F0001-A0001` without a report file in `in-progress/`, and the branch of a story, are ignored. A report on `main` whose front matter cannot be read as an acceptance's is a format error naming the report's path. If two directories share a feature id (`F0002-a`, `F0002-b`), the first in name order counts.

The acceptance reviewer cannot read the factory's state directory, so the factory tells it the disk in its prompt. When an acceptance's prompt is composed, the factory records the disk with occasion `acceptance` and adds two lines after the cost line: `Disk now: ...` and `Disk at the previous record: ...`. The second is the latest earlier record of any occasion (the instance's start or an earlier acceptance; a rerun of the acceptance compares with its own earlier record), or `none`. The report compares them and names growth that the feature's changes do not explain. Without the disk, the record log or the settings the lines are left out.

The prompt also carries the line `Human interventions of the stories: ...` right after `Cost of the stories: ...`: the human's line (see "The cost table") summed over the archived stories, not over earlier acceptances or stories still in `backlog`. A damaged archived story file adds nothing.

The next acceptance id of a feature is one above the highest acceptance id among its reports on `main` and on remote acceptance branches. The watcher's evaluation and the board command use the same rule.

A running acceptance is a work item like a story and is picked by the same order, by id. A due acceptance is not started before the feature's own stories: the next event is `acceptance_due:<feature>` only when no story of that feature (or of an earlier feature) can run; it still comes before the stories of a later feature. A waiting work item and a held claim come first, as for stories. `factory-watch` shows the event as `event: acceptance_due:F0002  acceptance of F0002 is due`.

## The hand-over at the approval

When a work item reaches an approval stage, the factory shows you on its pull request what to decide. The factory does this when it handles the `hand_over` event.

The description is written first by the stage that reaches the approval, before its push, and again, unchanged, by the hand-over on the next tick, which then marks the pull request ready and posts the cost table. The same holds for an acceptance. If the stage's write failed, the factory logs `pull request #<number>: description not written before the push` and the hand-over writes it.

It does these things, in this order:

1. **Replaces the pull request description.** What you or the factory wrote there before is gone. The new description has these sections, in this order, each headed `## <name>`: Description and Acceptance criteria (the story's own sections, verbatim), Tests, Review, Documentation and Smoke test (the text of the latest `result` entry of the tester, reviewer, documenter and smoke tester), and Commits (a code block with one line per commit beyond `main`: the first seven characters of the id and the subject). A story section that is missing or empty, and a report whose role never recorded a `result`, show `none`. The reviewer's entry under Review ends with the earlier tests the story changed and the leave for each. The reports are found by the journal's data (speaker and kind), never by the text of an entry. The description ends with a paragraph saying that a merge accepts the story and that a close with a comment sends it back.
2. **Marks the pull request ready for review.** A draft says the factory works; ready says you decide.
3. **Posts the cost table**, headed `Cost of this work item so far`, read from the cost records committed on the work item's branch (see "What a work item cost"), followed by the `Human:` line (see "The cost table"). The post is keyed by the number of the latest `result` entry, so a repeat does not post it twice.
4. **Records `handed_over = <stage>`** in the work item and pushes, in one commit with the subject `work item <id>: handed over at <stage>`. This comes last.

A work item whose `handed_over` already equals its stage is left alone: no description change, no post, no commit. A stage that is not an approval, or a work item without a pull request, is a `CannotHandle` for `hand_over` and changes nothing.

### The hand-over of an acceptance

When a feature's acceptance reaches its approval stage, you see the same steps on its pull request: the draft turns ready for review, the description is replaced, the cost table is posted once and `handed_over = <stage>` is recorded in the report with the commit subject `work item <id>: handed over at <stage>`. The factory does it when it handles the acceptance's `hand_over` event. No agent writes the description. The cost table is the one of the acceptance's own cost records, keyed by the number of the latest `result` entry as for a story.

The description has four parts, joined by an empty line:

1. `## Recommendation`: the report's own `## Recommendation` section.
2. `## Findings in short`: the text of the acceptance reviewer's latest `result` entry, without its `<speaker>: ` prefix. The reviewer is found by the journal's data (speaker and kind), not by the text.
3. `## Proposed stories`: the report's `## Proposed stories` section.
4. A closing text that says what you can do.

A part whose section is missing or empty, and findings with no `result` entry of the reviewer, show `none`. The closing text names no merge method; any method the hosting service offers works.

What your act does. The result is yours, whatever the acceptance reviewer recommended: a merge of an acceptance that recommended `not accepted` still books it accepted.

- **Merge** accepts. The report moves from the feature's `in-progress/` folder to its `done/` folder with its cost records file, its state says `done` and `accepted`, and its journal gets one `done` entry, `done (pull request merged); cost: <the acceptance's own cost>`. The proposed stories your merge brought into the feature's backlog stay there untouched; you refine them before starting any. While they wait, the feature is `incomplete` and not due; once you have started and archived them it is due again, and a new acceptance follows. A merge that brought no proposed stories leaves the feature `accepted`. The acceptance's branch is then deleted, on the remote and locally. The commit changes only the report and its cost records file (subject `work item <id>: merged, archived`). The factory does it in one tick.
- **Close**, with a comment saying why, refuses, at any stage: while the reviewer works or asks, at the approval, or after a failed hand-over. The report is written to the main branch at `done` as refused, `blocked` is cleared, the proposed stories are discarded (they were only on the branch), and the feature counts as not accepted until another story is archived and a new acceptance runs. The report has `Refused by the human on <date>: <your comment>` as the first paragraph under its `## Recommendation`, and a `done` entry `done (pull request closed by the human); cost: <cost>`; its cost records file is copied beside it. The commit changes only these two files (subject `work item <id>: closed, refused`). Your reason is your comments written after the reviewer's last result, each stripped of surrounding whitespace, blank ones skipped, joined with one space and otherwise copied unchanged; the factory never interprets them. With no comment the reason is `no reason given`. The factory does it in one tick.
- **A comment** is not answered while the acceptance waits; it goes into the report's journal.

Each acceptance has its own report and its own cost records, so the cost on its `done` entry counts only that acceptance's runs, never an earlier one's.

**Merged before its approval.** You may merge an acceptance's pull request while the reviewer still works or the acceptance waits with a question, before it reached its approval stage. The merge is still your decision: the acceptance is booked `accepted` exactly as above (a waiting question is cleared), and its `done` entry says so: `done (pull request merged before approval); cost: <the acceptance's own cost>`. A merge at the approval stage, before the hand-over, gets the ordinary entry. The merge brought the proposed stories into the feature's backlog, so the feature is `incomplete`, not due, until you have refined and archived them. Nothing loops: the report moves to `done/` as a new file, and the next tick finds it recorded.

**Accepted again.** When another story is archived after an acceptance, the stories no report covers any more and the feature is due again. The next acceptance is a new work item (`F0001-A0002`) with its own branch, report and cost records; the earlier report and its cost records stay as they were. Once the new acceptance's merge is recorded, the feature is `accepted` and not due if the merge brought no proposed stories, and `incomplete` if it brought some; until then it is `merged_unrecorded`. After a refusal the same happens once another story is archived.

**No loop.** Whatever stage an acceptance has reached, your merge or close of its pull request is booked in one tick, without an agent run: the stage run sees the merged or closed pull request and hands it to the acceptance's own handler, never to a story's. Once the booking is on `main` (accepted or refused), further ticks find nothing to do and yield `idle`: no commit, no post. A refused feature stays not due until another story is archived; an accepted one stays not due unless the set of archived stories changes.

**What a close records first.** Before the booking, your unread comments are copied into the report's journal on the acceptance's branch, followed by one `close` entry (speaker `human`, text `closed the pull request.`, dated today in UTC), and that is pushed with the subject `work item <id>: close recorded`. An acceptance ends at its first close: a report that already holds a `close` entry of yours gets no second one. The branch is deleted last, on the remote and locally.

**A close handled again.** A kill at any point is harmless: the recorded close is not recorded twice, a report already in `done/` is not booked twice, and a rerun after the branch is gone only finds the report in `done/`. If the branch is gone and the report is in neither place, the handler raises `CannotHandle` (`no report on the branch or the main branch`) and changes nothing. If the main branch moved since the last fetch, the push is rejected (`PushFailed`) after the close is recorded, and the branch stays; if the remote refuses to delete the branch, the refusal is already pushed and the branch stays. Both are counted and retried as in "An event that keeps failing".

A merge can be handled again after a kill: a report already in `done/` is not booked a second time, and only the branch deletion is repeated. If the main branch moved since the factory last fetched, the push is rejected and the event is retried (see "An event that keeps failing"); the branch stays on the remote until the booking is pushed. If the remote refuses to delete the branch, the booking is already pushed and the error is counted and reported the same way.

A hand-edited report with neither a `## Recommendation` nor a `## Journal` section gets a `## Recommendation` section at the end of the body, followed by an empty `## Journal` that holds the `done` entry. Reports the factory writes always have a journal.

### When the hand-over fails or is killed

Every step before the record can be repeated safely (for a story and for an acceptance alike), and nothing is recorded until they have all happened. A failure or a kill anywhere (the hosting service is down, the factory dies after the post) leaves `handed_over` unset, so the factory raises the event again on the next tick and completes the hand-over. You do nothing; there is never a second cost table post.

A hand-over that fails every time is a counted error like any other: it is tried on three ticks, and then one report is posted on the pull request and the event is capped (see "An event that keeps failing").

## A stale branch is deleted by the tick

After the restore of the checkout and before it looks at any work item, every tick deletes the remote branch `work-item/<id>` of each story whose file is in `backlog/` on `origin/main`. That is the leftover of a discard (see "A close before the approval discards the story") that was killed after it pushed the move, or whose deletion the remote refused. The branch of a story whose file is in `done/` is deleted the same way: it is the leftover of a merge (see "A merge archives the story") that was killed or refused between the archive and the deletion. Nothing for you to do after a kill.

- **A pull request still open on the branch** is closed by the hosting service when the branch goes (GitHub does so). The factory itself makes no call to the hosting service and posts nothing; a pull request that is already closed stays as it is.
- **A refused or unreachable deletion** is no stop. The factory log gets `could not delete stale branch <name>: rejected` (or `unreachable`), and the next tick tries again. A deletion is logged as `deleted stale branch <name>: its story is back in the backlog` (`its story is done` for a merged story).
- **Start the story again only after the tick has deleted the branch.** A story you start before that still finds the old branch with its old state and bill, and is discarded again. If the remote refuses deletions, lift the refusal and wait for a tick (the log line confirms it) before you start.
- **A branch is kept** when the same id also has a story file in `in-progress/` (two work items with one id are reported as a duplicate), and when no story file of its id is in `backlog/` or `done/` on `origin/main`. A move to `backlog/` that is not pushed to `main` deletes nothing. Branches that are not `work-item/<id>` (`main`, your own) are never touched.

## A merge archives the story

A merge of a story's pull request, by any method (merge commit, squash or rebase), accepts the story as it is, at whatever stage it has reached: working, waiting for you, or at an approval stage. The factory then archives it on `main`, in one commit with the subject `work item <id>: merged, archived`:

- the story file moves from `in-progress/` to `done/` of its feature, and its cost records (`<story>.costs.jsonl`) move beside it when it has them;
- its stage becomes `done`, with no wait and no claim, whoever held the claim; its counters and journal stay as they were;
- one journal entry is added, from `factory`, kind `done`: `done (pull request merged); cost: <the bill>`. The bill counts every cost record of the story, a died run and an unknown cost included; a story with no cost records gets the bill of none.

The handler posts nothing on the pull request. After the archive is pushed it deletes the work item's branch, on the remote and in the factory's checkout. A branch that is already gone (the hosting service deleted it) is no error. The handler trusts the merge: it asks nothing and checks nothing.

A merge found when the story's stage is due to run is handled first: the factory reads the pull request before every agent run, so a story you merged while its stage waited to run is archived as above, without that run.

When it goes wrong:

- **The push of the archive is rejected** (`PushFailed`, outcome `rejected`): `main` moved since the checkout. Nothing is archived and the branch is kept. The next tick fetches, and the story is archived then; do nothing.
- **The factory dies before the push**: `main` and the branch are as they were, and the story is archived once on the next tick.
- **The factory dies after the push, or the remote refuses to delete the branch** (`PushFailed` naming the branch, outcome `rejected`, for example when the remote forbids deletions): the archive stays on `main` and the story is under `done/`, so no event is raised for it again. The branch `work-item/<id>` is left on the remote. The next tick deletes it (see "A stale branch is deleted by the tick"); nothing in the factory reads it meanwhile. An unreachable remote during the deletion leaves the branch in the same way.

## A close before the approval discards the story

When you close a story's pull request while the story is at any stage that is not an approval stage, you have said you do not want this version. The factory then discards the story on `main`, in one commit with the subject `work item <id>: closed before the approval, back in the backlog`:

- the story file moves from `in-progress/` back to `backlog/` of its feature. It is moved, not rewritten: it is the text you wrote on `main`, whatever the work item's branch held;
- the commit changes nothing else.

After that push the handler deletes the work item's branch, on the remote and in the factory's checkout, and with it the branch's journal and cost records. So a story you start again begins with an empty bill. A branch that is already gone is no error. The handler posts nothing, and the pull request stays closed.

A close at an approval stage is a send-back, not a discard; see the next section.

A close found when the story's stage is due to run is handled first: the factory reads the pull request before every agent run, so a story you closed while its stage waited to run is discarded as above, without that run.

When it goes wrong:

- **The push of the move is rejected** (`PushFailed`, outcome `rejected`): `main` moved since the checkout. Nothing is discarded and the branch is kept. The next tick fetches and discards then; do nothing.
- **The factory dies before the push**: `main` and the branch are as they were, and the story is discarded once on the next tick.
- **The factory dies after the push, or the remote refuses or cannot be reached for the deletion** (`PushFailed` naming the branch, for example when the remote forbids deletions): the story is under `backlog/` on `main`, so no event is raised for it again, and the branch `work-item/<id>` is left on the remote. You do nothing: the next tick deletes it (see "A stale branch is deleted by the tick"). If the remote keeps refusing, lift the refusal; the tick tries again every tick.

## A close at the approval sends the story back

When you close the pull request of a story that waits at an approval stage, you have said "not like this". The factory then sends the story back to the second stage in the approval's `next` (`doing` in the usual pipeline). An approval with only one stage in `next` cannot be sent back: the factory raises `CannotHandle` for `closed` and records nothing. The same holds for a story without a pull request number.

The handler works in this order, and each step that changes the work item is pushed on its own:

1. **The close is recorded.** Your unread comments are copied into the journal, a `close` entry (speaker `human`, text `closed the pull request.`, dated today in UTC) is added, and `handed_over` is cleared. The subject is `work item <id>: close recorded`. A story that already holds a `close` entry since its latest `result` gets no second one, so a retry does not close twice; after an earlier send-back and a new stage result, a new close is recorded again.
2. **The pull request is reopened, as a draft.**
3. **The decision is recorded**, subject `work item <id>: sent back`: a `send_back` entry (`sent back to doing, round 3.`), `stage` set to the target, `round` raised by one, the claim released and, when a question is needed, a `question` entry with `blocked` set to `send_back`.
4. **The labels** of the pull request are rewritten to the new stage, so it does not keep `stage:approval`.

The handler itself posts nothing. A question is posted by the `ask` handler, like the others in "The factory's own questions".

### The reason and the round cap

A comment of yours counts as the reason when it was written after the latest `result` of the story: either copied earlier or copied at the close. The factory reads only the journal's records, never what you wrote, so the text of the comment does not matter. With a reason, and with the new round within the `round_cap` of the stage that hands over to the approval (the first one in the pipeline definition that has a cap), the story simply goes back to work with your comments as the findings.

Otherwise the factory asks, and `blocked` is `send_back`:

- You closed without a comment: `The pull request was closed without a comment. ` and the question below.
- The new round is past the cap: `This story has now been sent back <n> times, more than <cap>. ` and the question below. Past the cap the cap text wins, with or without a reason.

The question has three options, all of them things you can already do:

1. Comment what should change; the story is reworked with exactly that.
2. Close the pull request again to discard the story: it goes back to the backlog as you wrote it, and its branch is deleted.
3. If closing was a mistake: mark the pull request ready for review and merge it, which accepts the story as it is.

### When something fails or is killed

- **The reopen fails.** The close stays recorded (`HostingServiceError` is the counted error). The next attempt reopens and records the decision without a second `close` entry. A comment you write in between is copied then, and counts as the reason.
- **The push of the decision is rejected** (you pushed to the branch after the reopen). The close and your commit stay on the branch; the next attempt sends the story back once.
- **The labels cannot be set.** The decision stays recorded; the label is stale until the next stage's result commit rewrites it.
- **The factory is killed between the reopen and the recording of the decision.** The pull request is open again as a draft, but the story is still at the approval, so it is handed over again there and you have to repeat the close. Because the close is already recorded, the repeat adds no second `close` entry.

## Branch deletion on merge must be off

The factory reads a work item's state from its branch `origin/work-item/<id>`. A story in `in-progress/` on `main` with no such branch is read as a new start: it is at the first stage with fresh counters, whatever its file says. So turn off the hosting setting that deletes head branches when a pull request is merged ("Automatically delete head branches" on GitHub). With it on, a merged story whose file is still in `in-progress/` loses its branch and starts again.

## An idle tick that is not empty

When the factory does nothing, the evaluation may still have a reason. An `idle` result names it in its detail:

- A work item waits for the human (blocked, or at an approval stage) and its pull request is open with nothing new. While one waits, no new work starts, even if other work items could run. Answer, comment or merge on its pull request.
- Another instance holds a claim whose lease has not run out. Only one agent runs at a time, so the factory waits for that instance or for the lease to expire.

Neither is a fault. With neither, an idle tick means no work item has anything to do.

## A stage changed by hand

The factory changes a work item's stage only along the `next` lists of the pipeline definition (and archives to `done` from an approval stage). If someone edits `stage` in a work item's file on its branch to another one, the factory notices on its next tick and reports the change as a `reject` event: "stage changed from `<from>` to `<to>`, which the pipeline definition does not allow". What it looks at is the last commit on the branch, beyond `origin/main`, that touched the story's file. The factory puts the stage back as described below. A push to the work item's branch makes the factory try again, and the `reject` returns for as long as the newest commit beyond `origin/main` that touched the story's file is the illegal change.

### What the factory does when it moves a stage back

The factory corrects the change on the work item's branch, and only there; `main` is never written. It makes one new commit on top of the branch's head (also when later commits touched only other files) that:

- sets `stage` back to the one before the illegal change (`from`);
- clears the claim, since a claim belongs to the stage at the head and `to` is no longer it;
- appends a journal entry from `factory` of kind `move_back`: `illegal stage change <from> -> <to>, moved back.`

The commit's subject is `work item <id>: stage <to> -> <from>, moved back`; search the branch's history for `moved back` to find the corrections. When the work item has a pull request, the factory also posts one note there, `The stage was changed from <from> to <to>, which factory/pipeline.yml does not allow; it is back at <from>.`, and sets the `stage:<from>` label again, so the label does not keep the illegal stage.

If the factory is killed in the middle, do nothing: the note is posted first and keyed by the number of the entry to come, so the next tick makes the correction again from the same event and posts no second note. A failing label call after the push is an error of the event; the correction stays on the branch. A `reject` that cannot be corrected (the newest commit is a merge commit, changed no stage, has a parent without the story's file or with an unreadable one, or is itself a correction) is refused with `CannotHandle` and writes and posts nothing.

Not counted as such a change:

- the opening commit, whose parent is the story as you started it (a story started at `review` is not rejected). So the stage a work item branch you created by hand starts with is never judged, whatever it is: the first commit that gives the file its front matter is the opening commit, or has a previous version that cannot be read. Later stage changes on such a branch are judged like any other;
- a merge commit on the branch;
- the factory's own correction, which moves the stage back and appends a journal entry of kind `move_back`;
- a merge of the pull request by any method: merge commit, squash or rebase. The factory reads the pull request first, and a merged pull request is `merged`, never an illegal change.

A hand-made change that a later commit on the branch buried is not seen: only the newest commit that touched the file is judged.

### Never edit a running work item on main

Do not edit the file of a work item in `in-progress/` on `main`. Answer in its pull request instead: the agents amend the story on its branch (the description, the criteria), and your edit on `main` changes the same file. At the next stage start the factory merges `main` into the branch, the merge conflicts, and the stage stalls with the reason `merge_conflict`. When it has happened, revert the edit on `main`; the stage then starts again from the branch's story.

## An event that keeps failing

The dispatcher hands each event to its handler and counts what goes wrong, per event and per remote state (the commit the work item's branch is at). Any error from the handler counts, an event kind without a handler included. The tick calls the dispatcher once per pass.

The handlers of the human's acts on the pull request (`comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate`, `pull_request_lookup`), of the stage run, of `crash` and `expired` (see "A restart during a stage" and "An expired lease") and of `acceptance_due` are registered: every kind of event has a handler.

After three errors on one event and one remote state, the factory posts one report on the work item's pull request and stops retrying that event. The report reads: "The factory failed 3 times on `<event>` and has stopped retrying it. Last error: <error>. A new commit on the work item's branch (now at <12 characters of the commit>) makes the factory try again." It is posted once: a restart does not post it again, because the report carries a key that the pull request already holds. If the work item has no pull request, the factory opens a draft one for the report first, as under "The stops of one work item".

What to do about it:

- Read the last error in the report and fix its cause (a broken checkout, a missing tool, a bad file on the branch).
- Push a commit to the work item's branch. That is a new remote state: the count starts again at 1 and the event is tried again. Nothing else restarts it; comments do not.
- Two different events of one work item on one remote state share one report; the one that reached three errors first posts it, and the other is not tried again either.
- A success clears the event's count.

The counts are kept in memory only. After a restart they begin at zero, so the event is tried up to three more times; the report is not posted twice.

If the work item's branch is not on the remote, no pull request can be opened for the report and no later tick would change that. The report is then one line in the factory log, `error cap reached on <event>: <last error>`, written once; so is the report of an event that belongs to no work item. If the report cannot be posted for another reason (the hosting service is down, or git fails in the factory's checkout while the report resolves the branch), the factory tries to post it again on the next tick, without counting that as an error.

## Stops that cannot be done

Three situations have no work the factory can do. Each is a counted error, never a silent success: the factory raises `CannotHandle`, the dispatcher counts it per event and remote state, tries the event three times, and then posts one report on the work item's pull request (a draft is opened for it first when there is none), as under "An event that keeps failing". A restart posts no second report. The report's last error reads as below.

| Stop | Last error in the report | What to do |
|---|---|---|
| A work item that exists twice | `cannot handle duplicate: two work items share the id <id>`, followed by `: <the files>` when they are named | Two files carry the same id. Keep one, and rename or delete the other on `main` (or on its branch); the factory does not choose for you. |
| A failed pull request lookup | `cannot handle pull_request_lookup: the pull request lookup for <branch> failed`, followed by `: <cause>` when there is one | The hosting service could not say whether the branch has a pull request (rate limit, outage, token). Fix the cause named after the colon. A push to the branch starts the count again; nothing else does. |
| A question with no pull request to post it on | `cannot handle ask: work item <id> has no pull request` | The question is recorded in the journal but has nowhere to go. Open a pull request for the work item's branch, or push a commit to the branch so the factory tries again; the report itself opened a draft if the branch was on the remote. |

For all three the handler writes, posts and changes nothing itself; only the report is posted.

## A restart during a stage

If the factory dies while a stage runs and is started again with the same instance name, it finds its own claim on the work item's branch at its first look and treats it as a crash. It does not wait for the lease.

What it does, in one call:

- It throws away everything the dead stage did that is not on the remote: uncommitted and untracked files, commits that were never pushed, and the cost records of the discarded agent runs. Records of earlier stages stay.
- It records the crash in one commit on top of the remote's head: the claim is cleared, `crashes` goes up by one, and the journal gets an entry of kind `crash`: "crash 1: the run of stage doing ended without a result. Its work is discarded back to commit <commit>."
- It reruns the stage at once, unless the crash cap is reached (see "The crash cap"). `attempts` is not raised: a crash is not charged as a failed attempt.
- Below the cap it posts nothing on the pull request.

A commit that you pushed to the branch while the stage ran is on the remote, so it stays; the journal entry names the commit the discard went back to. The stage-start commit and its `started` entry stay in the history too.

Recovery is proved by injection tests: each of the six kill points is killed against a real local bare remote and the factory restarted, and v1's thirteen fault-injection paths are each walked with one kill or stall (`uv run pytest tests/test_kill_points.py tests/test_fault_paths.py tests/test_fault_paths_7_to_13.py`). The cases and paths are listed in the sections *Kill points* and *Fault-injection paths* of `docs/project-guide/README.md`.

If the push of the crash commit is rejected (someone pushed in between), the event is a counted error as under "An event that keeps failing"; a push to the branch makes the factory look again. A claim of another instance name is handled only once its lease has expired (see "An expired lease").

### The crash cap

`crash_cap` in the pipeline definition (default 2) is the number of crashes after which the factory asks you instead of rerunning. The count is `crashes` in the work item's state; it is reset by a forward move of the stage and by your answer, and kept by a rework move and by a stall, so it counts the crashes since the last forward move.

When a crash brings `crashes` up to the cap, the stage is not rerun. The same commit that records the crash records a question by `factory` and sets `blocked` to `crash_cap`; the commit is pushed, and only then is the question posted on the pull request, once. If the work item has no pull request yet, a draft is opened for it first. The question reads:

```text
Stage doing crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
```

- A comment you write after the question was posted ends the wait: `crashes` goes back to 0, `attempts` stay, and the stage runs again.
- Closing the pull request discards the story.
- A boundary error after the factory pushed its claim (hosting service, agent runtime, project command, git, a rejected result push) leaves the claim on the remote. The next look treats it as a crash and reruns the stage. If that fails again, it is the second crash and ends here with this question, not in the error report of "An event that keeps failing", because each rerun is a new event on a new remote state.
- If posting fails, the question stays recorded and pushed; the failure is a counted error of the event. A question lost between its record and its post is posted again by the `ask` handler when the work item has a pull request; for a work item without one it is not posted again.

## An expired lease

When an instance finds a claim of another name whose lease has run out (the claim's age is at least its `lease_duration`, 60 minutes by default), it treats the holder as gone and takes the stage over. Before that, the claim is waited for and nothing is touched.

What it does, in one call, is what a restart does (see "A restart during a stage"):

- It throws away what is not on the remote and records the expiry in one commit: the claim is cleared, `crashes` goes up by one, and the journal gets an entry of kind `expiry`: "expiry 1: the lease of stage doing ran out. Its work is discarded back to commit <commit>."
- `attempts` is not raised. An expiry is a crash, not a failed attempt, and it counts toward the crash cap.
- After the push it posts a note on the pull request (a draft is opened for it if there is none): "The run that held this stage ended without finishing: its lease expired (crash 1 of 2). Retrying."
- Then it reruns the stage itself. At the crash cap it does not: the note reads "... (crash 2 of 2). The factory does not rerun it and asks you instead." and is followed by the question of "The crash cap", on the same pull request.

The notes of the factory say "retrying" only where a rerun follows. A note without it means the factory has stopped and waits for you.

If the post of the note fails, the expiry stays recorded and pushed, the failure is a counted error of the event, and the note is not posted again. The stage is not rerun in that call; the next look finds no claim.

Your own claim is never an expiry, however old it is: that is the restart case. A claim whose lease has not run out is refused.

## Claims, leases and the clock

An instance claims a stage by pushing the stage-start commit; the claim records the instance's name, the start time and the role's `lease_duration` (60 minutes unless the pipeline definition says otherwise, per role). The claim keeps the value it was made with: changing `lease_duration` in the definition affects new claims only, never one that is running.

- Your own claim is recognised whatever its age. After a restart with the same instance name, the instance reruns its stage at once and does not wait for the lease. Only `factory-watch` judges it by the lease, as a look from outside: within the lease it shows the claim as held, since the tick may be running that stage.
- Another instance's claim is waited for until its lease has run out (the age reaches `lease_duration`); then it counts as expired and the factory handles it as above.
- Instances need a synchronised clock (NTP). Expiry compares the start time recorded by the claiming instance with the checking instance's own clock, so a clock that is off by minutes makes a lease end early or late.

## Replaced from v1

What v1 did and v1.1 does not, so that a file or an option you remember is not mistaken for a live one.

- `factory-watch` has no `--follow` mode and nothing writes the file `factory-last-line`: `--follow` is an unknown option. A file of that name left by v1 is not read and can be deleted.
- v1's leftover files in `.git/` (`factory-run.json`, `factory-tick.lock`, `factory-tick.json`) are neither read nor written; they change nothing and can be deleted.
- This repository's v1 history (v1's `stages.yml`, `TICKET.md`, `FEATURE.md` and its features F0001 to F0017) was `factory/v1/` and is kept at the tag `planning-history-2026-10-19`. Since the handover of 2026-10-18 v1.1 builds this repository from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`.
