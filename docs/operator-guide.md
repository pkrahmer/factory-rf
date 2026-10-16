# Operator guide

The guide for the person who runs the factory this repository implements: how to install it, how to configure it, which stops it can reach and what to do about each. Parts are built: the wrappers for git, the build commands and the `claude -p` runtime, the hosting-service client, the factory log and the health status file, the stops of the repository, the machine and a work item, the pipeline definition with its reader, rules and loader, the agent definition reader, the claim of a stage with its lease, the write paths with the guard and the undo, the stage protocol (one stage run from the pushed claim to the result commit, with stalls, checks and reports, and v1's decision rules with the factory's own questions), the cost records with the bill, and the reading of the remote: the evaluation that picks the next event, the tick with its stops, the dispatcher with its handlers, and `factory-watch`. The handlers start a stage and answer the human's acts on the pull request: comments are copied into the journal, questions are recorded and then posted, a merge archives the story, a close discards it or sends it back (for an acceptance, a close books it refused), an illegal stage change is moved back, and the pull request is handed over at the approval. After a crash, a restart reruns the dead stage, an expired lease of another instance is taken over, the crash cap asks the human, and the tick deletes a stale branch. `factory-run` (also `python -m factory.entry.run`) now runs one instance: it reads the settings, prepares the checkout and makes one tick per iteration until `SIGTERM` or `SIGINT`; the repository waiter, the container's health check and the entrypoint are built (see "The container: compose, entrypoint and health check"); the preflight and the other machine checks are added by later stories of F0010, and a real container is not yet observed. The commands are `factory-run`, `factory-check-story`, `factory-bill` and `factory-watch` (you run them) and `factory-guard` (the agent runtime runs it). `factory-health` (also `python -m factory.entry.health`) prints the stops in force. The sections below describe what the built parts expect of your machine and your project. The documenter stage extends this from each story's docs criterion.

## The instance's settings

One factory instance runs one project (R2) and is told what it needs through environment variables. `factory.domain.settings.read_settings` reads them and refuses a bad one with `SettingsInvalid`, whose message is `<variable>: <fault>`; it reports the first fault in the order of the table. `factory-run` calls it first; `factory-watch` reads the same environment.

| Variable | Required | Meaning |
|---|---|---|
| `FACTORY_REPOSITORY_URL` | yes | The one repository of the instance. No whitespace and no comma: a list of repositories is refused. |
| `FACTORY_INSTANCE` | yes | The instance's name, matching `^[a-z][a-z0-9-]*$` (`factory-1`; `Factory-1`, `1st`, `factory_1` and `-x` are refused). |
| `GIT_USER_NAME` | no | Name of the factory's commits. Default `factory`. |
| `GIT_USER_EMAIL` | no | Email of the factory's commits. Default `factory@noreply.invalid`. |
| `FACTORY_IMAGE_ID_FILE` | no | The file that holds the identity of the image the instance runs on. Default `/opt/factory/image-id`. |
| `FACTORY_CLAUDE_HOME` | no | The directory where the agents are installed (`<it>/agents/<role>.md`). Default `$HOME/.claude`, or `/home/agent/.claude` when `HOME` is unset or blank. |
| `FACTORY_CLAUDE` | no | The agent runtime's executable. Default `claude`. |
| `FACTORY_CLAUDE_VERSION` | no, but the preflight fails without it | The version of the agent runtime the image pins (`2.1.289`). The image sets it; a missing or blank value is read as not pinned. |
| `FACTORY_TOKEN_FILE` | no, but needed to build the boundaries | The file that holds the hosting-service token. No default. |

A required variable that is missing, empty or only spaces is refused. The two commit-identity variables are decided one by one: a half that is unset or only spaces falls back to its own default, so the commits are `factory <factory@noreply.invalid>` unless you set them. No preflight item checks the identity.

The image identity is read from the file, stripped, so that a rebuild of the image with the same build argument cannot keep an old preflight stamp valid. The image build generates the file (see "The machine's image"). A file that does not exist, cannot be read or holds only spaces is refused with `FACTORY_IMAGE_ID_FILE` as the variable. The variable `FACTORY_IMAGE` is only a label of the build and is never read as the identity.

A blank value of the three optional variables above counts as unset. The token is read once, when the boundaries are built, from the file `FACTORY_TOKEN_FILE` names, stripped of surrounding whitespace. An unset variable, a file that does not exist or cannot be read, and a file that holds only spaces are each refused with `FACTORY_TOKEN_FILE` as the variable; the message names the path and never the token. The token reaches the hosting service (PyGithub) from the factory process, and git only through its credential helper, `/usr/local/bin/git-credential-factory`, which the token story provides.

The repository's `owner/name`, which the hosting service needs, is taken from `FACTORY_REPOSITORY_URL`: `https://host/owner/name(.git)`, `ssh://git@host/owner/name(.git)` or `git@host:owner/name(.git)`. Any other URL is refused with `FACTORY_REPOSITORY_URL` as the variable. `factory-run` builds the boundaries from them when it starts.

The checkout and the state directory are not settings you can change: the checkout is always `/work/checkout` and the state directory `/state`. `FACTORY_CHECKOUT`, `FACTORY_STATE_DIRECTORY` and any other variable are ignored.

### A repository URL with a password is refused

A URL whose user information holds a colon, that is a user name followed by a password before the `@`, is refused, because git would keep the password in the shared checkout's `.git/config`, which the agent can read. Put the token in the token file instead. A user name alone is accepted: `ssh://git@github.com/owner/project.git`, `https://user@github.com/owner/project.git` and the form `git@github.com:owner/project.git`.

## When the process refuses to start

`factory-run` ends with status 2, never with a traceback, when the environment is invalid (any fault in the table above, including a missing or empty image identity file), when the token file cannot be read, and when the repository URL has no owner and no name. It writes one time-stamped line to the factory log and standard output, `settings invalid: <variable>: <fault>`, and a `preflight_failed` stop with scope `machine` to `health.json`, so the container's health check fails and the fault is visible without opening the log. The stop is added to the stops already in the file; an older `preflight_failed` stop is replaced and no other stop is dropped. Correct the variable or the file and start the instance again.

Install v1.1 only on a repository v1 has not worked in, or whose v1 work items are archived or discarded (decision 008 of factory-v2): v1.1 starts fresh, and nothing detects a v1 work item.

## The loop and its pauses

An instance repeats one iteration: it prepares the checkout, then makes one tick. The first iteration of a run happens at once, so a restart with the same instance name does not wait out a pause. Only a tick that handled an event other than `idle` counts as activity: a standing stop, a capped event and an error are idle, so the pause keeps growing while nothing changes. The first iteration is idle whatever the tick found, so the first pause is 30 seconds. One tick object serves the whole run, which keeps its error counts in memory from one iteration to the next; a restart starts them again.

After an iteration the instance pauses 15 seconds when the tick found activity. Each idle tick in a row doubles the pause (15, 30, 60 seconds) up to 120 seconds, and the next activity brings it back to 15 seconds. An iteration whose preparation or tick fails counts as idle. The failure is one line in the factory log, `iteration failed: <exception type>: <message>`, and the loop goes on.

### The checkout is recloned only when it is missing

The checkout lies at `/work/checkout`. When that directory has no `.git`, the instance clones the repository into it; an existing clone is left as it is, with no git call. After you delete the checkout the next iteration clones it again.

A clone that was killed half-way is not recognised: if its `.git` exists, the instance takes it for a clone, and if it does not, git refuses to clone into the non-empty directory and the iteration fails. In both cases delete the checkout directory and let the next iteration clone it again. The checkout is disposable (see "The stops of the tick"), so nothing is lost.

## The project's make targets

The factory runs a project's build through make and calls three targets: `check` (the full gate, which must be green before a stage hands forward), `lint` (run after the tester stage) and `test`. A project must define them in the Makefile at the root of its checkout. Each is judged by its exit status alone, and a target that does not exist counts as a failed command. A target that runs past its time limit is killed and counts as failed for that reason; the factory reads only the exit status, the last line and the last 30 lines of the output.

## The agent runtime

The factory runs each agent as a `claude -p` call under your own `claude` login: it needs the `claude` program and a session you have already logged in to, and it holds no API key of its own. The call gets only the environment the run's request gives, with no variable inherited from the factory. The flags are those of v1 and have not yet been checked against the pinned `claude` version. If a call fails at once, check them first. The factory asks `claude --version` and takes the first word of its output (for example `2.1.289`). The pinned version is the one the flags were written for; the preflight compares it with `FACTORY_CLAUDE_VERSION` (see "The preflight's items").

A run whose budget is spent is not lost: the factory resumes the same session once with a quarter of the budget (at least 0.50 USD) and asks the agent to finish with its decision, `question` if the work is not done. That costs up to that extra amount, and the cost and tokens of both calls are added up. If the resume is also over budget, the run stops as a stall; there is no third call. A run that dies, runs past its time limit or returns no usable decision stops the work item as a stall. One `time_limit` covers both calls: the resume gets what is left. A run the `time_limit` ends is killed, is not resumed, and shows its cost, tokens and turns as unknown.

### `factory-guard` on the agent run's `PATH`

The write-path guard is the command `factory-guard`, installed with the factory like `factory-check-story`. The runtime registers it as a Claude Code hook that refuses an agent's `Edit` or `Write` outside the stage's write paths. The runtime adds no `PATH` to the call, so the `PATH` of the agent run's environment must contain `factory-guard`. If it does not, the hook cannot start, and what Claude Code does then is not the guard's refusal; F0010's preflight will probe for it, until then nothing does. The factory builds that environment itself and it has two variables only: a `PATH` of the directory where `factory-guard` is installed (the directory of the factory's Python) followed by `/usr/local/bin:/usr/bin:/bin`, and a `HOME` (the factory user's home). Nothing else from your shell reaches the agent. So `factory-guard` must be installed in the same environment as the factory, and the tools an agent needs must be in one of those four directories. The guard reads only the settings file the runtime wrote for the run and exits 2 (a refusal, shown to the agent) for a write outside the write paths, a missing option or an unreadable settings file. A payload it cannot read is allowed. The details are in the project guide, "The guard command".

## The machine's image

`image/Dockerfile` builds the machine the factory runs on. Nothing in it floats (R29): the base image is named with its digest, Claude Code, `uv` and the eight Debian tools have exact versions, and the factory's own dependencies are installed by `uv sync --frozen --no-dev` from `uv.lock` alone (the build backend, `hatchling`, is pinned in `pyproject.toml`). `tests/test_image.py` checks this statically; it reports any reference that floats, such as a `FROM` without a digest, an `apt-get install` package without `=version`, `latest`, or a download piped into a shell.

### Build it

Run it from the repository root, with Docker:

```bash
docker build -f image/Dockerfile -t factory:local .
```

The build argument `FACTORY_IMAGE` is optional and is only a label (`docker build --build-arg FACTORY_IMAGE=2026-10 ...`); it defaults to `unlabelled`. The identity of the image is not the label. The build generates a fresh id and writes it to `/opt/factory/image-id`, which the settings read. Every rebuild that changes an earlier layer gets a new id, so it invalidates the preflight stamp, even when you pass the same label.

A real build is not yet observed: v1's container has no Docker. The Dockerfile also copies `claude/` and `template/`, which later stories of F0010 create, so the build is meaningful only once they exist. Treat the first build as the morning observation.

### Replace the placeholders before the first build

The digest of `BASE_IMAGE` (64 zeros) and the eight Debian package versions (`0~unpinned`: `git`, `make`, `curl`, `ca-certificates`, `procps`, `sudo`, `nodejs`, `npm`) cannot be looked up without a network, so the file carries placeholders of the right form. The build fails on them until you replace them.

To update any pin, edit its line and run `uv run pytest tests/test_image.py`:

- Base image: `docker pull python:3.12-slim-bookworm`, then take the digest from `docker inspect --format '{{index .RepoDigests 0}}'` and put it after `@sha256:` in the `BASE_IMAGE` default.
- Debian package: in the base image, `apt-cache policy <package>` shows the version; write it as `name=version`.
- `uv`: the `UV_VERSION` default. Claude Code: the `CLAUDE_CODE_VERSION` default (three numbers).

### Claude Code

Claude Code is installed from its npm package, `@anthropic-ai/claude-code`, at the pinned version `2.1.289`, with its auto-update off (`DISABLE_AUTOUPDATER=1`). The version is also in the container's environment as `FACTORY_CLAUDE_VERSION`, so the preflight can read it. A maintenance feature after v1.1 updates the pin (questionnaire 1, Q21); until then it changes only when you edit the Dockerfile.

### Users and directories

The container runs as `factory` (uid 1000); the agent runs as `agent` (uid 1001). Both have the group `factory-work`.

| Path | Mode and owner | What it means |
|---|---|---|
| `/state` | `0755`, `factory:factory` | The agent can read the health file, the log and the stamp, and cannot write them. |
| `/state/runs` | `2750`, `factory:factory-work` | The files of an agent's run: the agent can read them and cannot write them. |
| `/work`, `/home/agent/.claude` | `2775`, group `factory-work` | Both users can write. |

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

The volumes `work` (`/work`), `state` (`/state`) and `claude-home` (`/home/agent/.claude`) outlive the container.

### The entrypoint

`image/entrypoint.sh` is the container's entrypoint. Every line it writes starts with a UTC time stamp. In order, it:

1. checks that the image holds `claude/agents` and `claude/settings.json` under `/opt/factory`; if one is missing it writes `missing <path>` to standard error and exits with status 1;
2. replaces `agents` in the Claude home with a copy of the image's (an agent file no longer in the image is gone) and copies `settings.json` next to it: `installed agents and settings into <home>`;
3. creates `/state/runs` if needed and sets its mode to `2750`: `prepared /state/runs`;
4. writes `starting instance <name>` and starts the factory (`python -m factory.entry.run`) from `/opt/factory`.

It sets no git configuration; the factory's git gets its identity and credential helper from the factory itself. For tests, `FACTORY_OPT`, `FACTORY_CLAUDE_HOME` and `FACTORY_STATE` move the three directories; leave them unset in a container (the factory ignores `FACTORY_STATE`: the state directory is fixed).

### The health check and the restart policy

Docker runs `python -m factory.entry.health` every 30 seconds (10 seconds to answer, three failures to be unhealthy, 60 seconds of grace at the start). It reads `health.json` in the state directory. With no stop it prints `healthy` and exits 0; with stops it prints one line per stop and exits 1:

```
preflight_failed (machine): tool:make: make is not on the PATH (since 2026-10-12T08:00:00Z)
```

So `docker compose -f image/compose.yml ps` shows the container as unhealthy while any repository or machine stop stands, and `docker compose -f image/compose.yml exec factory python -m factory.entry.health` names the stops. The container becomes healthy again by itself when the factory clears the stop. A stop of a work item is not in the health status.

`restart: unless-stopped` brings the container back after a crash or a reboot. A container whose process is dead is left to that policy: the factory builds no watchdog. A real running container has not been observed yet; the morning observation is `docker compose ps` over a container with a stop standing.

### The stops you will see here

| Stop | Meaning | What to do |
|---|---|---|
| `preflight_failed` (machine) | A tool the machine needs is missing or the agent runtime does not work; the detail names it, for example `tool:make: make is not on the PATH`. | Fix the image or the login, then rebuild or restart; the stop clears when the check passes. |
| `checkout_restore_failed` | See "The stops of the tick". | As there. |
| `pipeline_definition_invalid` | See "The stop `pipeline_definition_invalid`". | As there. |
| `repository_unavailable` | The checkout cannot be made, or `origin/main` is not ready. The detail says which: `cannot prepare the checkout: <git's message>` (the clone failed: check `FACTORY_REPOSITORY_URL` and the credentials), `cannot fetch: <git's message>`, `the repository has no main branch yet` (the repository has no commit on `main`), or `origin/main has no factory/pipeline.yml yet`. | Fix the address or credentials, or push `factory/pipeline.yml` to `main`. |

### The preflight's items

The preflight is a list of seven items, built in `factory.application.preflight`. Every item runs whatever the others found, so one report names everything that is wrong. A failed report becomes one `preflight_failed` stop with scope `machine`; its detail lists each failed item as `<name>: <detail>`, joined by `; `. The preflight installs nothing: a missing tool is reported and you fix the image. (Wiring the preflight into the tick, the stamp and the probe of `main` come in later stories of F0010; until then nothing runs these items at start.)

| Item | Passes when | If it fails |
|---|---|---|
| `tool:git`, `tool:uv`, `tool:make` | the tool is on the `PATH` | The detail is `<tool> is not on the PATH; add it to the image`. Add the tool to the image and rebuild. |
| `tool:<claude>` | the agent runtime's executable (`FACTORY_CLAUDE`, default `claude`) is on the `PATH`; the item is named after the value, for example `tool:/opt/claude/bin/claude` | As for the other tools. |
| `hosting-service` | a read-only call (the open pull request of `main`) is answered | The detail holds the operation and the service's message. Check the token (`FACTORY_TOKEN_FILE`) and the network. |
| `agents` | at least one agent file is in `FACTORY_CLAUDE_HOME` (`<it>/agents/<role>.md`) | The detail names the directory, whether it is empty, missing or unreadable. Install the agents into `FACTORY_CLAUDE_HOME`. |
| `agent-runtime-version` | the first word of `claude --version` equals `FACTORY_CLAUDE_VERSION` | The detail names both versions (`the agent runtime reports 2.1.290, the image pins 2.1.289`): rebuild the image or change the pinned version. Without `FACTORY_CLAUDE_VERSION` it says `the image does not pin a version: FACTORY_CLAUDE_VERSION is not set`; when `claude --version` cannot run, it holds the runtime's error. |

The items read the instance's settings, so the three variables `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE` and `FACTORY_CLAUDE_VERSION` are the ones to check first. The commit identity is not an item.

### The wait for a repository that is not ready

Before each tick the instance checks that `origin/main` exists and holds `factory/pipeline.yml`. When it does, nothing is fetched here (the tick fetches) and any `repository_unavailable` stop is cleared. When it does not, the instance fetches once, looks again, and if the fault stays it raises the stop and skips the tick; the loop pauses as for any idle iteration and tries again. The stop is written once per detail: the same fault on the next iteration adds no second line, a different fault adds a new one. Push the missing branch or file and the next iteration clears the stop.

## The factory log and the health status file

Both live in the factory's state directory. Nothing starts the factory yet, so this describes what the built parts write; the next section says when a stop is written and when it goes away.

### The factory log

`TimestampedFactoryLog` writes every line twice: to standard output and, appended, to a file (UTF-8, lines end in `\n`). A line is `<stamp> <text>`. The stamp is `YYYY-MM-DDTHH:MM:SSZ`: UTC, whole seconds (a fraction is cut off, not rounded). One call can hold several lines, and they all carry one stamp, because the clock is read once per call:

```text
2026-10-12T12:00:07Z first
2026-10-12T12:00:07Z second
2026-10-12T12:00:12Z third
```

Missing parent directories are created. If the file cannot be written, the line has still reached standard output, and the write fails with an `OSError`.

### The health status file

`health.json` in the state directory holds the stops in force for the repository or the machine, as one JSON object: `{"stops": [{"scope": ..., "reason": ..., "detail": ..., "at": ...}]}`. The container's health check reads it (see "The container: compose, entrypoint and health check"); an empty `stops` list is healthy.

- One stop per reason. `scope` is `machine` for `preflight_failed` and `repository` for every other reason; `detail` names the fault and is never blank; `at` is in UTC.
- The reasons are `fetch_failed`, `checkout_restore_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `repository_unavailable`, `main_branch_failing` and `preflight_failed`.
- A file that is missing, cannot be read, is not JSON or is not a valid status reads as healthy (no stops). Do not repair it by hand: the next stop that is raised replaces the whole file, and a fault that lasts is raised again.
- A write goes to a temporary file in the same directory and replaces `health.json` in one step, so a reader never sees half a file. If `health.json` is a directory, the write fails with an `OSError` and leaves nothing behind.

## Stops of the repository or the machine

When the factory finds a fault of the repository or the machine (a failed fetch, a checkout it cannot restore, an invalid pipeline definition, a failing preflight), it raises a stop in two places, and tries both: a line in the factory log and an entry in the health status file. A stop of this kind never goes to a pull request; look in the log and in `health.json`.

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

## Stops of one work item

A stop of one work item (a question, a cap reached) is meant to appear as one comment on that work item's pull request. A question is first recorded (a journal entry of kind `question`, with `blocked` set, committed and pushed) and then posted; see "The factory's own questions". The rules below are those of `StopService.post`, which the dispatcher's error report calls (see "An event that keeps failing"). A stall does not follow them: it has its own rule, given under "A stall: the stall note". A posted comment says what each possible answer will do, and it ends with the factory's marker and the stop's key:

```
<!-- factory -->
<!-- factory key=F0001-S0001:stall:3 -->
```

- If the work item has no pull request yet, `StopService.post` opens a draft pull request first, on the work item's branch (`work-item/<id>`), and posts the stop there. The description says: "The factory opened this draft pull request to report a stop on <work item>. The stop is the comment below."
- It opens one only when the branch is on the remote with a commit beyond `main`. Otherwise it opens nothing, posts nothing and reports a `create_pull_request` error: `branch <branch> is not on the remote with a commit beyond main`. The factory pushes the branch before it can report a stop, so you see this only if the remote branch was removed or reset.
- If the work item's branch already has an open pull request, the factory posts on that one. A pull request you closed or merged is not reused for a new one; but when the work item's state records a pull request number, the stop is posted there even if you have since closed it.
- A restart never repeats a stop. The key identifies the stop: if the factory died after posting and before recording it, the next attempt finds the key on the pull request and posts nothing. The same key with another text is still a repeat; a different kind or number is a new stop and a new comment.
- The posting writes no state. In particular the dispatcher does not record the number of a pull request it opened for an error report; a later stop finds that pull request by its branch.

## What a stage run shows

One stage run leaves these traces on the remote and the pull request, in this order:

1. **The draft pull request.** The first stage of a work item opens it, titled `<id>: <title>`, with the work item's text as the description. Only an open pull request is reused; a closed or merged one never is, and a new draft is opened instead.
2. **The stage-start commit.** It is pushed before any agent runs. It holds the claim and one journal entry, speaker `factory`, kind `started`, with the text `factory: started <stage> as <instance>.` (for example `factory: started doing as factory-1.`). If this push fails, no agent runs.
3. **The agent's entry.** The speaker is the agent's role and the kind is `result`, or `question` when the agent asked; code writes both, the agent writes the words. For each green check and each report the entry ends with one line `` `<command>`: <last line of its output> ``, for example `` `check`: 12 passed ``.
4. **One commit by the factory**, above the stage-start commit (or above the agent's last commit, when the agent committed): the result commit, or the stall commit after a stall. It holds the whole work tree.
5. **The label** `stage:<stage>` (written so, for example `stage:review`) on the pull request. It is written after the result commit is pushed, and after a stall's note is posted. It is a projection of the stage and is never read back.

If the push of the result commit fails, no label is written. If the hosting service fails at the label, the commit stays pushed.

## A stall: the stall note

A stall is a stage that ended without a result the factory can keep. The causes are the nine listed below; the first ones are an agent run that died, ran past its time limit, spent its budget (and the resume too), or gave no valid decision and entry. A stall costs one attempt of the work item and is never a crash. The factory keeps what the agent wrote inside the stage's write paths, undoes the rest, releases the claim and pushes one commit with a `stall` entry in the journal. Only then does it post the stall note on the pull request and write the pull request's `stage:` label for the stalled stage, so a work item whose first stage stalls has its label too. The note's key is `<work item>:stall:<n>`, where `n` is the number of the stall entry.

The note reads:

```text
Stalled (attempt 1 of 2): the agent run died without a result. Retrying on the next tick.
```

- `attempt n of m`: `n` is the work item's attempts after this stall; `m` is `attempts_cap` of the pipeline definition.
- The cause is one sentence. The reasons are: the agent run died without a result; it reached its time limit; it spent its budget, and the resume too; the agent gave no valid decision and entry; the agent's decision is not an allowed one; the agent left the work item's branch; the work item's form broke during the stage; a check is red after the stage; merging the main branch conflicts and the merge was aborted. A detail, such as the name of a red check, follows the sentence after a colon. A detail of several lines (the output of a red check) puts its first line in the sentence and the other lines in a code block below it; see "A stall by a red check".
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
- Reports (the stage's `reports`) run after all checks are green. They are recorded and never hold a move. Every report that ran adds one line `` `<command>`: <last line of its output> `` to the agent's entry, passed or failed; the line has the same form either way, so only its last line shows whether the report passed. A failing report holds nothing and stops nothing.

The result commit of every stage holds the whole work tree. Make sure the project's `.gitignore` covers whatever its checks create (build output, caches, coverage files); otherwise the factory commits it.

## The factory's own questions

Besides an agent's `question`, the factory asks you itself. Every question reaches you in two steps: it is recorded first, as a journal entry of kind `question` in the work item's file (committed and pushed, with `blocked` set), and only then posted as one comment on the pull request. If the factory dies or the post fails between the two, the question is already recorded and the next attempt posts it once: the comment's key is made from the recorded entry's number, and a post whose key the pull request already holds is a no-op. The handler of `ask` (`AskHandler`) does both steps.

The questions you can meet on a pull request, and how to answer each:

| Question | `blocked` | Comment reads | A comment | Closing the pull request |
| --- | --- | --- | --- | --- |
| An agent's | `question` | `<role>: <the agent's words>` | answers it; the stage runs again | discards the story |
| The form has findings | `question` | see below | answers it; the stage runs again | discards the story |
| The round cap | `round_cap` | see below | answers it | discards the story |
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

A comment answers a question when it was written after the factory posted that question. The handler of `comment` (`CommentHandler`) works like this for a work item that waits (`blocked` is set):

- Your comments are copied into the journal and, in the same commit, the wait ends. The answer is read from ids and keys, never from what you wrote; a blank comment is marked read but does not answer.
- A comment written before the question was posted is only recorded and the wait stays. The same holds when the question is recorded but not posted yet, and when the only post on the pull request belongs to an earlier question. Comment again once the question is on the pull request.
- Each answer clears the wait and resets only what belongs to that wait: `attempts` go back to 0 for the attempts cap, `crashes` go back to 0 for the crash cap, nothing else. The `round` is never reset, so the next send-back at the round cap asks again.
- A comment on a work item that does not wait for you, at an approval stage for instance, is only recorded; `stage`, `round`, `attempts`, `crashes` and the hand-over are untouched.
- A comment event that keeps failing is tried three times on the same remote state and then reported once on the pull request, like every other event (see "An event that keeps failing"). The factory's own comments (those with its marker) never answer.

- **The form has findings.** The agent decided to move forward, but the work item's form still has findings after the run. The comment reads: `The work item's form has findings, so the stage cannot move forward: 1. <message> 2. <message>. What should happen? Answer with a comment; the stage then runs again. Close the pull request to discard the work item.` The stage stays where it is and the round is not counted. Answer with a comment (say how to fix the form, or that the finding is wrong); the stage then runs again. Closing the pull request discards the work item.
- **The round cap is passed.** A stage with `round_cap` sent the work item back once more than the cap allows. The comment reads: `This work item has now been sent back <n> times, more than <cap>. What should happen? Answer with a comment; close the pull request to discard the work item.` The stage stays where it is and the round shows the count. Answer with a comment; closing the pull request discards the work item.

A stage without `round_cap` sends back without limit and never asks. Sending back counts rounds; a stall counts attempts (see "A stall"), and the two caps are separate.

## The stop `pipeline_definition_invalid`

The pipeline definition is `factory/pipeline.yml` as it stands on `origin/main`, never the file in the work tree. The factory loads it each cycle, and a load that refuses it raises the stop `pipeline_definition_invalid` (scope `repository`): a line in the factory log and an entry in the health status, nothing on a pull request.

```text
2026-10-12T12:00:07Z stop repository pipeline_definition_invalid: missing key: contract
```

The detail is the fault. The faults the load reports:

| Fault | Cause and what to do |
|---|---|
| `factory/pipeline.yml is missing at origin/main` | the file is not on `main`; merge it |
| a fault of the text, such as `missing key: contract`, `unknown key: <path>`, `invalid <path>: <message>`, `not valid YAML: <problem>` | fix `factory/pipeline.yml` on `main`; several faults are joined by `; ` |
| a fault of the rules across keys, such as `stage doing: next names unknown stage ship`, `contract major 2 is not supported (this factory reads major 1)`, `role coder: write_paths is empty`, `role coder at stage doing: 61 min exceed lease_duration 60 min` | fix `factory/pipeline.yml` on `main`; see "The pipeline definition" for the rules you meet most often and the project guide, "The rules of the definition", for the full list |
| `role <role>: agent is not installed` | the role has no file `<agent home>/agents/<role>.md`; install it. Every missing role is named, in the order of `roles`, joined by `; ` |
| `agent home unavailable: <fault>` | `<agent home>/agents` is missing or is not a directory (see "The agent files") |

The agents are checked only when the text itself is valid, so a broken file and a missing agent home show the file's fault alone until it is fixed. A key with a default may be left out and takes it; a key without one that is missing is a fault.

The stop clears itself at the next load of `origin/main` that succeeds, with the line `stop cleared pipeline_definition_invalid`; stops of other reasons are not touched. Only the load of `origin/main` raises or clears this stop: a look at the definition on another branch can be refused, but it changes neither the health status nor the log. A git failure while reading (an unreachable repository, an unknown ref) is not a fault of the definition and raises no stop. If the health status cannot be written, the load reports an `OSError` and not the fault; the log line has been written. What the cycle does while the stop stands is described with the tick.

## The stops of the tick

A tick works from the remote alone: the checkout is disposable. It fetches first, loads the pipeline definition from `origin/main`, puts the checkout back on `main` at `origin/main`, and only then looks at the work items. Three repository stops end a tick before it looks at any work item; each is a log line and a health status entry, never a comment on a pull request. The next tick tries again and clears the stop when the fault is gone.

| Stop | Meaning | What to do |
|---|---|---|
| `fetch_failed` | `git fetch` failed; the detail is git's message. | Fix the network, the remote's address or the credentials. An expired or revoked token shows as `fetch_failed` too: renew the token. Nothing is lost; the next tick after a successful fetch carries on. |
| `pipeline_definition_invalid` | `factory/pipeline.yml` on `origin/main` is refused. | See "The stop `pipeline_definition_invalid`". The tick does not touch the checkout while this stop holds. |
| `checkout_restore_failed` | The factory could not put the checkout on `origin/main` (for example, an untracked file or directory it cannot remove); the detail is git's message. | Fix the cause in the checkout, such as a path's permissions, or delete the checkout and clone again. |

The restore throws away every uncommitted change and every untracked file in the checkout (ignored paths stay) and deletes the local branches of the work items, so that a stage starts from the remote's branch. When it throws changes away it writes one line to the log, `discarded uncommitted changes: <path>, <path>`. Do not keep work in the factory's checkout.

A work item file that cannot be read is not a stop. The tick ends with the error, naming the file's path, and does so on every tick until a human repairs the file (on its branch, or on `main` for a started story without a branch) or moves the story out of `in-progress/` on `main`. Closing the pull request changes nothing: the tick reads every story in `in-progress/` before it looks at any pull request. A work item in a stage that the pipeline definition lacks fails the same way.

v1's leftover files in `.git/` (`factory-run.json`, `factory-tick.lock`, `factory-tick.json`) are neither read nor written; they change nothing and can be deleted.

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
| `project_commands` | name to `time_limit` in minutes | `check`, `lint` and `test`, each 10 |
| `attempts_cap` | attempts before the human is asked | 2 |
| `crash_cap` | crashes before the human is asked | 2 |
| `acceptance_stage` | the stage of the feature acceptance | none |

A stage has `role` (none: no agent runs), `next` (the first name is the forward move), `approval` (the human decides), `checks` (project commands that must pass after the agent), `reports` (project commands run after green and only recorded) and `round_cap` (none: no cap). A role has `write_paths` (required), `lease_duration` (60 minutes) and `time_limit` (40 minutes, one agent run). A write path may hold `{work_item}`, the work item's own file, and `{feature}`, its feature's path (`factory/features/F0004-x`). The engine's protected paths (`factory/pipeline.yml`, the forms, `feature.md`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `.claude/`) are outside every write path. Every limit is a positive whole number.

The rules you meet most often:

- The stage `done` must exist, with no role and no `next`. Write it `done: {}`; `done:` alone is refused.
- The contract major must be 1. Any minor is read.
- Every stage other than `done` needs a non-empty `next` and either a role or `approval: true`; every name in `next` must be a stage.
- The lease: for each stage with a role, the role's `time_limit` plus the `time_limit` of every command in the stage's `checks` and `reports` must be at most the role's `lease_duration`. With the defaults, 40 + 10 (one check) + 10 (one report) = 60 fits; a stage with two checks and a report adds up to 70 and is refused. Raise the `lease_duration` or lower a limit.
- Values are taken only in their YAML type: a limit is an integer (not `'30'`, `30.0` or `true`), `approval` is `true` or `false` (not `'yes'` or `1`), names and write paths are text. A write path must hold a character that is not whitespace.
- A key that is not listed is refused, so a misspelt key is never ignored. A given `project_commands` replaces the default set as a whole: list `check`, `lint` and `test` again if you still want them.
- Every role needs an agent file (see "The agent files").

A refused definition raises the stop `pipeline_definition_invalid`, described above. The project guide, "The rules of the definition", lists every fault.

## The agent files

An agent is a file `<agent home>/agents/<name>.md`. The name is lowercase letters, digits and hyphens, starting with a letter (`coder`); `README.md` and `Coder.md` are not agents, nor is a file with another suffix or one in a subdirectory. Every role of the pipeline definition needs an agent file of the same name.

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

The body, without the whitespace around it, is the instructions; a line of hyphens inside it belongs to it. Any other front matter key is ignored for now: which ones the agent runtime applies is decided with F0010.

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
| `missing key: <key>` | `model`, `tools` or `budget_usd` is left out |
| `budget_usd must be greater than 0` | zero, negative, text or a boolean |
| `invalid <key>: <reason>` | any other value of the wrong type |

When a file has several faults, the first is reported: a missing key before an invalid value.

## Checking a story before it starts

`factory-check-story` checks story files against where they sit and against your project's `factory/story-form.md`. Run it from the root of a checkout, with the paths relative to that root. The checkout must be laid out the v1.1 way: `factory/story-form.md`, a `feature.md` in each feature's directory, and the stories in `backlog`, `in-progress` or `done`.

This repository's own `factory/` tree is v1's (`drafts/`, `ongoing/`, `FEATURE.md`, `TICKET.md`), so the command does not apply to it: run here it prints `cannot read factory/story-form.md: ...` and exits 2. That holds until this repository moves to v1.1's layout.

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

Findings about the content follow the form check (`docs/project-guide.md`, "The form check of a story"):

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

Every agent run writes a cost record beside its work item. `factory-bill` adds the records up and prints the bill. Run it from a checkout of your project:

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
| stage | runs | min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: |
| tests | 1 | 1.0 | 7 | 62 | 1000 | 300 | 0.35 |
| doing | 2 | 2.5 | 5 | 10 | 500 | 100 | 1.20 + 1 unknown |
| **total** | 3 | 3.5 | 12 | 72 | 1500 | 400 | 1.55 + 1 unknown |
```

One row per stage, in the order the stage first ran; a stage that runs again (`doing`, `review`, `doing`) is one row. The last row is the total.

| Column | Meaning |
|---|---|
| runs | agent runs, every one counted whatever its end: a run that died, ran past its time limit or spent its budget is in the bill |
| min | the runs' duration in minutes, one decimal |
| turns | the turns the runtime reported |
| in | input tokens plus cache-creation tokens |
| cached | tokens read from the cache |
| out | output tokens |
| USD | the cost in dollars, two decimals |

Figures are rounded half up.

### The cost line

The line under the table sums the same figures: `3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55 + 1 unknown`.

### An unknown cost

A run whose cost the runtime did not report (a run that died, or one the time limit ended) has an unknown cost. It is not counted as $0.00: it is left out of the sum and shown as `+ <n> unknown` after the dollars, where `<n>` is the number of such runs. Unknown turns and tokens are left out of their sums in the same way, without a mark; so the figures are a lower bound when `unknown` is shown.

## Looking at the remote: `factory-watch`

`factory-watch` is the window on what the factory would do next. It evaluates once, as a tick would after its fetch, and prints two things: the event the next tick would handle, and the board. It has no options; `--help` shows its usage.

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
- Exit status: 0 after printing; 1 when the pipeline definition on `origin/main` is invalid (the fault goes to standard error as `factory-watch: <fault>`, standard output stays empty, no stop is raised); 2 for an unknown option, and when the environment is invalid or the token file cannot be read: then `factory-watch: settings invalid: <variable>: <fault>` goes to standard error (never a traceback) and standard output stays empty. `factory-watch` reads the same environment as `factory-run` (see the table above) and builds its boundaries the same way, so it looks at the instance the container runs. A repository whose `origin/main` does not resolve (a clone that never fetched) ends with a git error.
- v1's `--follow` mode and its `factory-last-line` file are gone: `--follow` is an unknown option, and nothing writes that file. A file of that name left by v1 is not read and can be deleted.

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

The next acceptance id of a feature is one above the highest acceptance id among its reports on `main` and on remote acceptance branches. The reader exists as `AcceptanceReader` in `factory.application.acceptance_reading`; the watcher's evaluation and the board command use it.

A running acceptance is a work item like a story and is picked by the same order, by id. A due acceptance is not started before the feature's own stories: the next event is `acceptance_due:<feature>` only when no story of that feature (or of an earlier feature) can run; it still comes before the stories of a later feature. A waiting work item and a held claim come first, as for stories. `factory-watch` shows the event as `event: acceptance_due:F0002  acceptance of F0002 is due`.

## The hand-over at the approval

When a work item reaches an approval stage, the factory shows you on its pull request what to decide. `HandOverHandler` (in `factory.application.handlers.hand_over`) does this for the `hand_over` event. It is registered.

It does these things, in this order:

1. **Replaces the pull request description.** What you or the factory wrote there before is gone. The new description has these sections, in this order, each headed `## <name>`: Description and Acceptance criteria (the story's own sections, verbatim), Tests, Review, Documentation and Smoke test (the text of the latest `result` entry of the tester, reviewer, documenter and smoke tester), and Commits (a code block with one line per commit beyond `main`: the first seven characters of the id and the subject). A story section that is missing or empty, and a report whose role never recorded a `result`, show `none`. The reports are found by the journal's data (speaker and kind), never by the text of an entry. The description ends with a paragraph saying that a merge accepts the story and that a close with a comment sends it back.
2. **Marks the pull request ready for review.** A draft says the factory works; ready says you decide.
3. **Posts the cost table**, headed `Cost of this work item so far`, read from the cost records committed on the work item's branch (see "What a work item cost"). The post is keyed by the number of the latest `result` entry, so a repeat does not post it twice.
4. **Records `handed_over = <stage>`** in the work item and pushes, in one commit with the subject `work item <id>: handed over at <stage>`. This comes last.

A work item whose `handed_over` already equals its stage is left alone: no description change, no post, no commit. A stage that is not an approval, or a work item without a pull request, is a `CannotHandle` for `hand_over` and changes nothing.

### The hand-over of an acceptance

When a feature's acceptance reaches its approval stage, you see the same steps on its pull request: the draft turns ready for review, the description is replaced, the cost table is posted once and `handed_over = <stage>` is recorded in the report with the commit subject `work item <id>: handed over at <stage>`. `AcceptanceHandOver` (in `factory.application.acceptance`) does it for the acceptance's `hand_over` event, which the wired `SplitByWorkItemKind` sends to it. No agent writes the description. The cost table is the one of the acceptance's own cost records, keyed by the number of the latest `result` entry as for a story.

The description has four parts, joined by an empty line:

1. `## Recommendation`: the report's own `## Recommendation` section.
2. `## Findings in short`: the text of the acceptance reviewer's latest `result` entry, without its `<speaker>: ` prefix. The reviewer is found by the journal's data (speaker and kind), not by the text.
3. `## Proposed stories`: the report's `## Proposed stories` section.
4. A closing text that says what you can do.

A part whose section is missing or empty, and findings with no `result` entry of the reviewer, show `none`. The closing text names no merge method; any method the hosting service offers works.

What your act does. The result is yours, whatever the acceptance reviewer recommended: a merge of an acceptance that recommended `not accepted` still books it accepted.

- **Merge** accepts. The report moves from the feature's `in-progress/` folder to its `done/` folder with its cost records file, its state says `done` and `accepted`, and its journal gets one `done` entry, `done (pull request merged); cost: <the acceptance's own cost>`. The proposed stories your merge brought into the feature's backlog stay there untouched; you refine them before starting any. While they wait, the feature is `incomplete` and not due; once you have started and archived them it is due again, and a new acceptance follows. A merge that brought no proposed stories leaves the feature `accepted`. The acceptance's branch is then deleted, on the remote and locally. The commit changes only the report and its cost records file (subject `work item <id>: merged, archived`). `AcceptanceMerged` (in `factory.application.acceptance`) does it, in one tick.
- **Close**, with a comment saying why, refuses, at any stage: while the reviewer works or asks, at the approval, or after a failed hand-over. The report is written to the main branch at `done` as refused, `blocked` is cleared, the proposed stories are discarded (they were only on the branch), and the feature counts as not accepted until another story is archived and a new acceptance runs. The report has `Refused by the human on <date>: <your comment>` as the first paragraph under its `## Recommendation`, and a `done` entry `done (pull request closed by the human); cost: <cost>`; its cost records file is copied beside it. The commit changes only these two files (subject `work item <id>: closed, refused`). Your reason is your comments written after the reviewer's last result, each stripped of surrounding whitespace, blank ones skipped, joined with one space and otherwise copied unchanged; the factory never interprets them. With no comment the reason is `no reason given`. `AcceptanceClosed` (in `factory.application.acceptance`) does it, in one tick.
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

A merge of a story's pull request, by any method (merge commit, squash or rebase), accepts the story as it is, at whatever stage it has reached: working, waiting for you, or at an approval stage. The merged handler (`MergedHandler`) then archives it on `main`, in one commit with the subject `work item <id>: merged, archived`:

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

When you close a story's pull request while the story is at any stage that is not an approval stage, you have said you do not want this version. The closed handler (`ClosedHandler`) then discards the story on `main`, in one commit with the subject `work item <id>: closed before the approval, back in the backlog`:

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

When you close the pull request of a story that waits at an approval stage, you have said "not like this". `ClosedHandler` then sends the story back to the second stage in the approval's `next` (`doing` in the usual pipeline). An approval with only one stage in `next` cannot be sent back: the handler raises `CannotHandle` for `closed` and records nothing. The same holds for a story without a pull request number.

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

## An event that keeps failing

The dispatcher hands each event to its handler and counts what goes wrong, per event and per remote state (the commit the work item's branch is at). Any error from the handler counts, an event kind without a handler included. The tick calls the dispatcher once per pass.

The handlers of the human's acts on the pull request (`comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate`, `pull_request_lookup`), of the stage run, of `crash` and `expired` (see "A restart during a stage" and "An expired lease") and of `acceptance_due` are registered: every kind of event has a handler, and `NOT_YET_HANDLED` in `factory.entry.wiring` is empty. Should a future kind have none, the event leads to this:

It ends in the one report of its work item and remote state, and then holds back all new work, until its handler is registered. A push to the branch makes the factory try again.

After three errors on one event and one remote state, the factory posts one report on the work item's pull request and stops retrying that event. The report reads: "The factory failed 3 times on `<event>` and has stopped retrying it. Last error: <error>. A new commit on the work item's branch (now at <12 characters of the commit>) makes the factory try again." It is posted once: a restart does not post it again, because the report carries a key that the pull request already holds. If the work item has no pull request, the factory opens a draft one for the report first, as under "Stops of one work item".

What to do about it:

- Read the last error in the report and fix its cause (a broken checkout, a missing tool, a bad file on the branch).
- Push a commit to the work item's branch. That is a new remote state: the count starts again at 1 and the event is tried again. Nothing else restarts it; comments do not.
- Two different events of one work item on one remote state share one report; the one that reached three errors first posts it, and the other is not tried again either.
- A success clears the event's count.

The counts are kept in memory only. After a restart they begin at zero, so the event is tried up to three more times; the report is not posted twice.

If the work item's branch is not on the remote, no pull request can be opened for the report and no later tick would change that. The report is then one line in the factory log, `error cap reached on <event>: <last error>`, written once; so is the report of an event that belongs to no work item. If the report cannot be posted for another reason (the hosting service is down, or git fails in the factory's checkout while the report resolves the branch), the factory tries to post it again on the next tick, without counting that as an error.

## Stops that cannot be done

Three situations have no work the factory can do. Each is a counted error, never a silent success: the handler raises `CannotHandle`, the dispatcher counts it per event and remote state, tries the event three times, and then posts one report on the work item's pull request (a draft is opened for it first when there is none), as under "An event that keeps failing". A restart posts no second report. The handlers (`DuplicateHandler`, `PullRequestLookupHandler` in `factory.application.handlers.lookups`, and `AskHandler`) are registered; the report's last error reads as below.

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

Your own claim is never an expiry, however old it is: that is the restart case. A claim whose lease has not run out is refused as before.

## Claims, leases and the clock

An instance claims a stage by pushing the stage-start commit; the claim records the instance's name, the start time and the role's `lease_duration` (60 minutes unless the pipeline definition says otherwise, per role). The claim keeps the value it was made with: changing `lease_duration` in the definition affects new claims only, never one that is running.

- Your own claim is recognised whatever its age. After a restart with the same instance name, the instance reruns its stage at once and does not wait for the lease.
- Another instance's claim is waited for until its lease has run out (the age reaches `lease_duration`); then it counts as expired and the factory handles it as above.
- Instances need a synchronised clock (NTP). Expiry compares the start time recorded by the claiming instance with the checking instance's own clock, so a clock that is off by minutes makes a lease end early or late.
