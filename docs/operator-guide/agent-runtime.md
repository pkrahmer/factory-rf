# The agent runtime and the agent files

A topic of the [operator guide](README.md). It is for the operator of an [instance](../project-guide/glossary.md) who knows Linux and does not read the code. The factory's own words are explained in the [glossary](../project-guide/glossary.md).

An agent is one call of a model under a program: Claude Code (`claude -p`) or opencode (`opencode run`). This page says how that call is made, how it logs in, what it may reach, what the factory does when the provider refuses it, and how the agent files are chosen. Exact lists (settings, faults, log lines, flags) are in *Reference* at the end.

## How a call is made

Every agent call runs in a throwaway container of the [stage](../project-guide/glossary.md) image, on the stage's [dataset](../project-guide/glossary.md), as the host's `factory` user. No second user and no `sudo` stand between the factory and the agent. The only fence on the host is the folder of the token file (see "The hosting-service token" in [health.md](health.md)).

- The agent's home is `home/` on the dataset. The rollback to the [base](../project-guide/glossary.md) clears it before every stage, so nothing an agent or a login command leaves there reaches the next run.
- The call gets only the environment its request gives, with `HOME=/work/home`. No variable is inherited from the factory.
- The factory itself holds no key or token. A small shell inside the container reads the login files (see *The login*).
- The [take](../project-guide/glossary.md) copies out of the dataset only the changed paths the agent's [role](../project-guide/glossary.md) may write. A write elsewhere is lost, not refused, so an agent keeps temporary files in `mktemp` or `tempfile`. No kernel rule stands behind this.

The preflight's `agent-runtime-version` runs `claude --version` or `opencode --version` in the stage image and compares the first word of its output (for example `2.1.289`) with `FACTORY_CLAUDE_VERSION` or `FACTORY_OPENCODE_VERSION`, the pinned version the flags were written for (see "The preflight's items" in [health.md](health.md)). The preflight's `agent-run-probe` makes one call with the real flags once for each image build. A flag the pinned program rejects stops the machine before any [claim](../project-guide/glossary.md). If a call fails at once, see "The probe of the agent run" in [health.md](health.md).

### The container's fence

Every container (the sync, the agent and each check) has the same fence:

- no capabilities, and no set-uid program gives it rights;
- at most 4096 processes and 4 GB of memory;
- podman's default network, because the sync and the checks need the package index and the agent needs the model's API.

A container the kernel kills for its memory before the time limit is an ordinary failure, not a time-out. A check then fails, usually with make's exit status 2 when the kernel ended one of its children, or 137 when it ended the container's first process.

A call that podman's `--timeout` ends is a run that reached its time limit. The factory reads podman's exit status 255 as the time limit when the call lasted at least its limit. A run the time limit ends is killed, is not resumed, and shows its cost, tokens and turns as unknown.

### The environment of an agent run

The factory builds the environment from an allow list of six names (see "The hosting-service token" in [health.md](health.md)). Two matter here:

- `PATH` is the directory where the factory's console scripts are installed, followed by the `PATH` the stage image sets (`/usr/local/bin:/usr/bin:/bin` when it sets none; see "The project's stage file" in [machine.md](machine.md)). The tools an agent needs must be in the stage image, in a directory of that `PATH`.
- `HOME` is `/work/home`, whatever the instance's settings. No preflight item checks it: it is a path inside the container.

`LANG`, `LC_ALL`, `TERM` and `TZ` reach the agent when the factory process has them. The names in `FACTORY_CONTAINER_ENV` and the variables that `FACTORY_CA_BUNDLE` sets reach it too (see *Behind a proxy*). The login shell adds one name, `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`.

## The login

The call logs in with the first of these that holds something:

1. an API key, when `FACTORY_API_LOGIN_FILE` names a file that holds one;
2. a token, when `FACTORY_CLAUDE_LOGIN_FILE` names a file that holds one, made once with `claude setup-token`;
3. otherwise none: the call has no login and the shell reports `none` (see *Without a login file*).

A variable that is unset, or a file that is missing or blank, counts as holding nothing. Both files are read the same way:

- The shell reads the file at the start of every call, as the factory's user, and hands its content to the program. A new token or key applies from the next call, without a restart.
- The secret reaches only the agent calls. It is not in the factory's own environment, the [project commands](../project-guide/glossary.md)' or `--version`'s. The same variable in a request's environment is dropped: the file is the only source.
- The secret stands in no process's arguments, so `ps` inside the container does not show it. A host user's `ps` shows a container's processes with their arguments unless `/proc` is mounted with `hidepid=2`, and the secret is not among them.
- A file that cannot be read, or is not plain ASCII text, stops the run before any call (see *The faults*).
- The file must exist, even empty: podman refuses to mount a missing one. The container mounts it read-only.

### The agent's login token

The token is made once for all instances and the Podman machine.

1. Run `claude setup-token` on the host where Claude Code is installed, or on the VM as `factory`. It needs a subscription and prints the token.

   ```sh
   claude setup-token
   ```
2. Save the token it prints, with nothing else in the file, as `claude-token` in your own folder. On Windows, write it as plain text without a byte-order mark, in PowerShell:

   ```powershell
   Set-Content -NoNewline -Encoding ascii claude-token <token>
   ```

   PowerShell 5's `>` writes UTF-16, which is not read as the token.
3. Install it so that only the factory's user can read it, and remove the copy. On the VM, from your own account:

   ```sh
   sudo install -m 0600 -o factory -g factory claude-token /home/factory/.secrets/claude-token
   shred -u claude-token
   ```

   "The machine" in [machine.md](machine.md) shows the same steps, as step 8 of "On GCP, step by step".
4. Set `FACTORY_CLAUDE_LOGIN_FILE` to its path in the environment file.

### The agent's API key

An instance can run its agents on an Anthropic API key instead of the subscription, for example at a workplace that has a key and no subscription. An opencode instance always uses the key (see *Running on opencode*).

1. Save the key, with nothing else in the file, as `/home/factory/.secrets/anthropic-api-key`, as plain ASCII text. On Windows write it with `Set-Content -NoNewline -Encoding ascii`, as for the token.
2. Set the file's permissions as for the token file.
3. Set `FACTORY_API_LOGIN_FILE` to its path in the environment file.

Each instance has its own file. The VM holds one instance, and the file is in its `factory` user's folder.

- A key in the file wins over the token, which is then not read. An `ANTHROPIC_API_KEY` anywhere else in the environment is dropped.
- The key stands in no argument, run file, result, [journal](../project-guide/glossary.md) entry, cost record or log, and not in the factory's own environment.
- To go back to the subscription, empty the file. The next call reads it as it is.

To see which login is in force, read the [cost record](../project-guide/glossary.md) of a run: its field `login` is `subscription`, `api_key` or `none` (a record written before the field existed lacks it). The preflight also writes one factory-log line for the probe, once for each image build:

```text
preflight: agent-run-probe: the agent runs log in with the API key from <file>
```

### Without a login file

With neither file, the call has no login and the shell reports `none`. A login made by hand with `claude` as `factory` on the VM does not help: the agent's home is on the dataset, and the rollback clears it before every stage. Make the token file instead (see *The agent's login token*).

## Behind a proxy

A container's environment is closed: the factory's own environment reaches none of them. Two settings open it for what a company network needs.

1. Put the variables in `factory.local.env` (see "The environment file" in [machine.md](machine.md)), where they are also in the factory process's own environment.
2. List their names in `FACTORY_CONTAINER_ENV`, for example `HTTPS_PROXY,NO_PROXY,UV_INDEX_URL,NPM_CONFIG_REGISTRY`: the proxy, the hosts that bypass it, and a package mirror for `uv` and for `npm`. Each name the factory's environment holds is passed with its value into the agent, sync and check containers.
3. If the network has its own certificate authority, set `FACTORY_CA_BUNDLE` to the PEM file. It is mounted read-only into the same containers at its own path, and `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` name it. If a listed name is one of those three, the bundle's value wins.
4. Restart the service. The factory reads its environment when it starts.

The bundle must hold the public certificates beside the company's own. `SSL_CERT_FILE` replaces Python's list of authorities instead of adding to it, so a file with the company's certificate alone breaks every connection to a public host.

The names the factory gives a container itself win over the list: a listed `PATH` leaves each container's own `PATH`. `HOME`, the two login names, `OPENCODE_CONFIG`, `GIT_ASKPASS` and every `FACTORY_` name are refused when the settings are read, so the hosting token (`FACTORY_TOKEN_FILE`) reaches no container. With neither setting the containers get nothing more.

`operator/vm/setup.sh` and the build of the stage image run outside the factory and read none of these settings. Give them the proxy and the mirror in their own environment.

## A run that ends without a result

A run that exits non-zero, gives no reply, runs past its time limit or returns no usable decision stops the [work item](../project-guide/glossary.md) as a [stall](../project-guide/glossary.md). Two cases have their own handling.

### A run whose budget is spent

The factory resumes the same session once with a quarter of the budget (at least 0.50 USD). It asks the agent to finish with its decision, `question` if the work is not done. That costs up to the extra amount, and the cost and tokens of both calls are added up.

- If the resume is also over budget, the run stops as a stall. There is no third call.
- One `time_limit` covers both calls: the resume gets what is left.

Under opencode the factory keeps the budget itself, because opencode has no budget flag. It adds up the cost of every step as the run prints it and stops the run when the sum is above the agent's budget. Then it resumes once, as above. A step is counted when it ends, so a run may pass its budget by the cost of one step.

### A run that ends `died`

A run ends `died` when it exits non-zero, gives no reply or an error reply, and neither a provider limit, the budget nor the time limit applies. The factory log names it with one line:

```text
run <run id> of <work item> (<stage>) died: <text>
```

The text is the first of these that exists: the error reply's text, the last three non-empty lines of standard error (without the login shell's `factory-login-used:` line), or `exit <status>` (negative for a signal). Lines are stripped and joined with ` / `, and the text is cut to 300 characters with `…` at the end. The agent's own answer is never quoted. The cost record carries no text.

If a provider's usage limit is the cause and the run ended `died` instead of `provider_limit`, copy a stable part of this text into `FACTORY_PROVIDER_LIMIT_MESSAGE`.

## A provider's spend limit

Some gateways limit the spend per model in a rolling window and answer a call past it with an HTTP error. One gateway answers with status 428 after about $3 in 10 minutes. Without a rule the run would end `died`. The factory gives it its own end reason, `provider_limit`, and keeps the run's session in the result so that a later run can continue it.

What counts as the limit:

- The status in `FACTORY_PROVIDER_LIMIT_STATUS` (default 428) as a whole number in the text. `HTTP 428:` and `(428)` match; `14280` does not.
- Or a text that the regular expression in `FACTORY_PROVIDER_LIMIT_MESSAGE` finds. Set it when the gateway's text is not known to carry the status.

Where the factory looks for it:

- In the error result the `claude` call printed, or, when no result could be read, in a line of its standard error.
- Under opencode, while the run streams: in an `error` event (its `statusCode`, or the limit in its message) or in a line of standard error. The run stops at once with the session kept.
- Never in the agent's own text, so an agent that writes "428" in a report cannot end its run.
- A run past its time limit, or stopped by its budget, keeps that end reason. The limit is looked for only when neither applies.

A message that names a wait (`in 7 minutes`, `after 30 s`, `retry-after: 420`) gives the run's wait. Otherwise none is known. The cost record's `end_reason` is `provider_limit`, and it carries the refused calls (`denials`, `denied_paths`) like any run that replied.

### The wait

When a call ends `provider_limit`, no agent process is left running. The factory waits, then resumes the same session with a short continue prompt. It gives the budget that is left (the agent's budget less what the run has cost so far) and the time limit that is left. It asks no one and counts no attempt.

- The wait is the one the message names, or `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` (default 10) when it names none. A run with no session starts again from the stage's own prompt.
- The waits count toward neither the stage's `time_limit` nor its attempts. A run resumed after a limit is one run and one cost record, with the costs of all its calls added up.
- A limit that comes again is waited out again. When the waits add up to `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` (default 120), the last wait is cut to what is left of it and the run ends `provider_limit`.
- If nothing of the budget is left after a limit, the run ends `budget`. If none of the time is left, it ends `time_limit`. Neither waits.
- The preflight's probe never waits. A limit there is a failed probe (`the probe run ended provider_limit; ...`).

The factory log shows each wait and the end. The first line is written before each wait, with `a new run` in place of the session when the run has none. The second ends the run. Seconds are whole.

```text
2026-10-19T12:00:07Z provider limit: coder waits 600 s before it resumes ses_a
2026-10-19T12:10:07Z provider limit: coder waited 7200 s, the ceiling of 7200 s; the run ends provider_limit
```

### What to do at the ceiling

**You see** a stall with the cause `the provider's spend limit lasted past the waiting ceiling`, and the stall note on the pull request (see "A stall: the stall note" in [stops.md](stops.md)).

**It means** the factory waited out the whole ceiling and the limit was still there. One attempt is counted. The next [tick](../project-guide/glossary.md) runs the stage again from what the stall kept, and at the [attempts cap](../project-guide/glossary.md) the factory asks you.

**You do** one of these before you answer. A limit that lasts two hours is not a rolling window passing.

- Look at the gateway: its quota and its window.
- Raise `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES`.

### While the factory waits

- **The claim stays held.** The factory renews no [lease](../project-guide/glossary.md), so a stage that waits may hold its claim past its `lease_duration`. The coder's time limit, the ceiling and the checks come to about 180 minutes, against a lease of 60. Only another instance on the same repository would act on the age, so run one instance per repository.
- **A stop or a restart during a wait** is a [crash](../project-guide/glossary.md) of the factory's own claim. The stage runs again at once and counts toward the crash cap, not toward the attempts (see "A restart during a stage" in [work-items.md](work-items.md)). The wait starts over.

## Running on opencode

An instance runs its agents on Claude Code unless you switch it to opencode.

1. Set `FACTORY_AGENT_RUNTIME=opencode` in `factory.local.env` (see "The environment file" in [machine.md](machine.md)), or give `operator/vm/setup.sh` the option `--runtime opencode`.
2. Build the stage image with `AGENT_RUNTIME=opencode`. The image holds only the runtime it was built for (see "The stage image" in [machine.md](machine.md)). `opencode-ai` is installed from npm at the version `OPENCODE_VERSION` of `operator/vm/Dockerfile`, and the environment file sets `FACTORY_OPENCODE_VERSION` to it.
3. Put the API key in the file `FACTORY_API_LOGIN_FILE` names (see *The agent's API key*). Every run is then paid through the API. The subscription token is not used.
4. Check that the models exist, as *The models* below says.
5. Restart the instance. The factory reads its environment when it starts.

A login that a build keeps in the agent's home does not work on the machine. The rollback clears the home before every stage, so nothing made by a login command survives. Put the key in the API login file, whatever the build.

The preflight does not read the key: the probe of the agent run shows whether a run can log in. The item `opencode` has two faults; see "The preflight's items" in [health.md](health.md) for each.

**Your own build.** Choose an opencode build with `FACTORY_OPENCODE` (its path), `FACTORY_OPENCODE_VERSION` (what `--version` prints) and `FACTORY_OPENCODE_MODELS`. Add them to `factory.local.env` (see "The environment file" in [machine.md](machine.md)), install the build on the VM and restart the instance. The values `factory.env` carries are the stage image's `opencode-ai`, its pin in `operator/vm/Dockerfile` and the three Anthropic ids.

**The models.** The agent files name `opus`, `sonnet` and `haiku`. `FACTORY_OPENCODE_MODELS` maps each to a `<provider>/<model>` id of opencode. `operator/vm/Dockerfile` pins `opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5`. Check that an id exists by running this where opencode is installed, for example in the stage image:

```sh
opencode models anthropic
```

A model written with a `/` in an agent file is used as it is.

**The version.** The pins change in `operator/vm/Dockerfile` alone (see "The stage image" in [machine.md](machine.md)).

**What opencode keeps in the agent's home.** Sessions, logs and caches in the agent's home: `/work/home/.local/share/opencode`, `/work/home/.local/state/opencode` and `/work/home/.cache/opencode`, for the length of one stage. The configuration in `.config/opencode` is what the next run reads, and an agent that could write it could loosen its own permissions.

**What differs from Claude Code:**

- The denied commands of `settings.json` become `deny` permissions in the run's own configuration file.
- There is no structured reply. The agent ends its message with a `<factory-result>` block, and a reply without a valid block ends the run `no_result`.
- The budget is the factory's own (see *A run whose budget is spent*).

### A company's provider

Behind a company proxy that speaks the OpenAI protocol, point opencode at it with a provider file.

1. Write the provider file (the example below).
2. Set `FACTORY_OPENCODE_PROVIDER_FILE` to its absolute path in `factory.local.env` (see "The environment file" in [machine.md](machine.md)).
3. Map the aliases to the provider in `FACTORY_OPENCODE_MODELS`, for example `opus=corp/big,sonnet=corp/big,haiku=corp/small`.
4. Restart the instance.

The file holds one provider and the small model. The runtime merges them into the configuration of every run, beside `autoupdate`, `share`, `snapshot` and the agent, and changes none of those keys. With the setting unset the configuration is unchanged. The file is read at the start of every run.

The preflight's `agent-run-probe` shows whether the pinned opencode accepts the file and reaches the proxy (see "The probe of the agent run" in [health.md](health.md)). The example uses made-up names:

```json
{
  "id": "corp",
  "base_url": "https://llm.example.invalid/v1",
  "api_key_env": "ANTHROPIC_API_KEY",
  "models": {
    "big": {"name": "Corp Big", "context": 200000, "output": 8192, "input_cost": 3.0, "output_cost": 15.0},
    "small": {}
  },
  "small_model": "corp/small"
}
```

| Key | Meaning |
| --- | --- |
| `id` | The provider's id in model names: lower-case letters, digits and `-`, starting with a letter. |
| `base_url` | `http://` or `https://` and a host. A trailing `/` is kept as written. |
| `api_key_env` | The name of the environment variable that holds the key: capitals, digits and `_`, not starting with a digit. Give `ANTHROPIC_API_KEY`, which the login shell fills from `FACTORY_API_LOGIN_FILE`. The key itself is never in the file: the runtime writes `{env:<name>}` into the configuration. |
| `models` | At least one model, by the name the proxy knows. Each may have `name`, `context` and `output` (token limits, whole numbers of at least 1, given together) and `input_cost` and `output_cost` (dollars per million tokens, at least 0, given together). A model with none is `{}`. |
| `small_model` | `<id>/<model>`, one of `models`. opencode otherwise takes its small model from a service of its own, which a proxy does not offer. |

Any other key is refused. A fault ends the run with `cannot use the opencode provider file <path>: <reason>`, the reason naming the first field at fault. No run file is written and nothing starts. A missing file ends the run the same way.

A model without prices is costed at 0, so the factory's budget stop never fires for it. Give `input_cost` and `output_cost` when the budget is to count.

**What opencode may load and contact.** With a provider file the runtime also limits what opencode loads:

- The configuration gains `enabled_providers`, holding only the file's provider id (`["corp"]` for the example), and no `disabled_providers`.
- The call's environment gains `OPENCODE_DISABLE_MODELS_FETCH=1`, `OPENCODE_DISABLE_AUTOUPDATE=1` and `OPENCODE_DISABLE_DEFAULT_PLUGINS=1`. The runtime's values win over the same names in a request's environment.

Of the three, `OPENCODE_DISABLE_MODELS_FETCH` is the one that changes traffic: without it every run contacts opencode's public model catalogue, `models.opencode.ai`, once. The other two are upstream's own guards. They depend on the provider file because the file already defines the models. Without it opencode needs its public model list, so a run without the file is unchanged, byte for byte.

One contact stays: opencode 1.19.3 asks `registry.npmjs.org` at the start of every run, most likely for the provider's npm package, and no switch removes it. A deployment that must prove that a run sends nothing to the vendor reads the proxy's log.

### A bearer token for the model API

A model API behind an OAuth2 client-credentials grant gives out a bearer token that lives about an hour. The opencode runtime reads the file `FACTORY_API_LOGIN_FILE` names at every call and hands its content to the agent as `ANTHROPIC_API_KEY`. The token therefore only has to be kept fresh in that file.

The command `python -m factory.entry.refresh_token` does that, as a process of its own beside the factory. Run it like this, with the five variables below in its environment:

```sh
python -m factory.entry.refresh_token
```

Starting it with the instance is the start script's business (see "The machine" in [machine.md](machine.md)). It reads five variables. A missing or blank one prints `refresh_token: <variable> is not set` to standard error and exits 2.

| Name | What it does | Default | Example |
| --- | --- | --- | --- |
| `FACTORY_TOKEN_URL` | The grant's token endpoint. | none | `https://auth.example.invalid/token` |
| `FACTORY_TOKEN_SCOPE` | The scope to request. | none | `llm.invoke` |
| `FACTORY_TOKEN_CLIENT_ID` | The client id. | none | `factory` |
| `FACTORY_TOKEN_CLIENT_SECRET_FILE` | The file that holds the client secret, as UTF-8 text with surrounding whitespace dropped. Secret Manager mounts it, and the secret is never in the environment. A missing, blank or non-UTF-8 file exits 2 with `refresh_token: cannot read <path>`. | none | `/secrets/client-secret` |
| `FACTORY_API_LOGIN_FILE` | The file to write: the same one the runtime reads. | none | `/home/factory/.secrets/anthropic-api-key` |

What it does:

- It requests a token, writes it into the login file with nothing else (no newline) and replaces the file atomically, so a reader sees the old token or the new one. It prints `token refreshed: valid <n> s, next in <m> s`.
- It repeats every ten minutes, or after half the token's life when that is shorter, and never sooner than thirty seconds. A token that lives under twenty minutes would otherwise expire between two refreshes.
- A failed request, or any other fault of one refresh, prints `refresh_token: <the error>`, keeps the old file and tries again after a minute. The client secret and the token are replaced by `***` in every message.
- `--once` refreshes once and exits 0, or 1 after printing the error. Without it the command runs until `SIGTERM` or `SIGINT` and exits 0.

A container mounts the login file when it starts, and its login shell reads it once. A run therefore holds the token that was in the file at its start. The file is rewritten at least every ten minutes, so a run starts with a token at most ten minutes old. That token stays valid for at least its life less ten minutes, which for a one-hour token is fifty minutes, more than the longest stage. Use a grant whose token lives longer than ten minutes plus your longest stage.

**The proxy.** The request goes through Python's standard library, which honours `https_proxy` and `no_proxy`. Set `https_proxy` in the refresher's environment when the token endpoint is reached through a proxy, and `NO_PROXY` for an internal API host the agents reach directly.

## The agent files

An agent is a file `<name>.md`. The factory looks for it in two places: the project's own, `<project>/factory/agents/<name>.md` on `origin/main`, or the installed one, `<agent home>/agents/<name>.md`. Every role of the [pipeline definition](../project-guide/glossary.md) needs an agent file of the same name, from either place.

The name is lowercase letters, digits and hyphens, starting with a letter (`coder`). `README.md` and `Coder.md` are not agents, nor is a file with another suffix or one in a subdirectory.

The file is YAML front matter between two lines of three hyphens, then the agent's instructions:

```markdown
---
model: sonnet
tools: [Read, Write]
effort: low
budget_usd: 0.1
---
The agent's instructions.
```

The body, without the whitespace around it, is the instructions. A line of hyphens inside it belongs to it. The four keys are the only ones the agent runtime applies, because Claude Code ignores an agent file in print mode and the runner builds its flags and prompt from them itself. Any other key would read as if it did something and do nothing, so the file is refused when the pipeline definition is loaded. See "The stop `agent_definition_invalid`" in [stops.md](stops.md).

### A project's own agents

For each role the factory reads `<project>/factory/agents/<name>.md` from `origin/main` first, at every tick, the same ref as the pipeline definition. When the project has none, it uses the installed agent.

A project's agent replaces the installed one whole and never extends it. Nothing is merged, so a key or a line of instructions you leave out is not taken from the shipped file. To change a shipped agent, copy it from `agents/agents/` in the image's source to `<project>/factory/agents/<name>.md` and change the copy.

The file follows the same rules and has the same faults as any agent file. A fault of a project file is named with its place, for example `factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour`. The load of every tick and the preflight's probe check it. A faulty project file is never replaced by the installed one: the [stop](../project-guide/glossary.md) `agent_definition_invalid` stands until a commit on `main` fixes it.

- **A new role.** Add the role to `<project>/factory/pipeline.yml` and its file under `<project>/factory/agents/`, in one commit on `main`. A role whose only agent is the project's own needs no installed file.
- **Back to the shipped agent.** Remove `<project>/factory/agents/<name>.md` from `main`.
- **A branch's copy is never read.** A work item's branch, or an uncommitted edit in the checkout, changes nothing. Only `origin/main` counts, so a work item cannot change its own agent. A file under `<project>/factory/agents/` is a protected path (the human's), and an agent that writes there is refused.
- **The probe.** The preflight's `agent-run-probe` runs the project's `coder` when there is one, once for each image build. A faulty file fails the item with `agent coder: factory/agents/coder.md at origin/main: <fault>`.

### A project's own skills

A project may bring skills under `<project>/.claude/skills/`. Every shipped agent has the `Skill` tool and loads a skill whose description fits its work. Where a skill contradicts the agent's own instructions, the instructions win: the agent follows them and names in its journal entry the skill and the step it set aside.

The skills are the human's files, like `CLAUDE.md`. `.claude/` is a protected path at any depth, so no stage writes a `.claude/` folder anywhere in the repository, `<project>/src/.claude/skills/` included. The take leaves a nested `.claude/` write out after every run, also where a write path opens it, and the entry names the path. A run reads the root `.claude/skills/` from its checkout, the work item's branch.

Only Claude Code's runs are given the `Skill` tool. An opencode run leaves it out, and the factory does not check whether opencode loads skills of its own.

### The shipped agents and settings

The checkout ships them in its `agents/` folder: `agents/agents/<role>.md` and `agents/settings.json`. The stage image copies the folder to `/etc/factory/agents`. The files are in Claude Code's format and the opencode runtime translates them per run, so the folder carries no runtime's name. The setting `FACTORY_CLAUDE_HOME` names this folder for both runtimes.

The folder holds seven agents (`intake`, `tester`, `coder`, `reviewer`, `documenter`, `smoke-tester`, `acceptance-reviewer`) and `settings.json`. Each agent's `tools` ends with `Skill`, and the settings allow it in `permissions.allow`, right after `Grep`.

The instance reads them from `FACTORY_CLAUDE_HOME` (`/srv/factory/<instance>/factory/agents`, the `agents/` folder of the factory's own clone). Change the files in the repository: a change reaches the instance by a merge and the steps of "The rebuild after a merge" in [machine.md](machine.md).

What the settings allow and deny:

- An agent may run `factory-check-story` and no other `factory-` command. It cannot run `factory-run`, `factory-watch` or `factory-bill`.
- `git add` and `git commit` are denied, because an agent leaves its changes in the working tree and the factory makes the result commit. An agent has no git identity of its own.
- `git push`, `gh` and the commands that move or rewrite branches are denied, because the factory alone pushes.

A new project starts from `operator/template/` in the factory's checkout: a pipeline definition, a `CLAUDE.md` and a `Makefile` whose `SOURCE` and `LAYERS` placeholders you fill in. The [story](../project-guide/glossary.md) and [feature](../project-guide/glossary.md) forms are yours to add, and every stage stops until `factory/story-form.md` exists.

The smoke tester has two ways out when it finds something:

- When every finding is a slip in a document the documenter writes, and the code does what the work item says, it ends with `docs`. The documenter fixes exactly those findings and ends with `smoke-test`. A slip in a document is a sentence the code contradicts, or a contradicted criterion that is the `docs:` one.
- With any other finding, or a mix, it ends with `doing`.

Both count as [rounds](../project-guide/glossary.md).

## Reference

### The settings of this page

The full list of settings is in "Configuration" in [install.md](install.md).

| Name | What it does | Default | Example |
| --- | --- | --- | --- |
| `FACTORY_AGENT_RUNTIME` | `claude` or `opencode`. | `claude` | `opencode` |
| `FACTORY_CLAUDE_LOGIN_FILE` | The token file. | none | `/home/factory/.secrets/claude-token` |
| `FACTORY_API_LOGIN_FILE` | The API key file; wins over the token. | none | `/home/factory/.secrets/anthropic-api-key` |
| `FACTORY_CLAUDE_VERSION` | The pinned `claude` version the preflight compares. | none | `2.1.318` |
| `FACTORY_CLAUDE_HOME` | The folder of the shipped agents and `settings.json`. | none | `/srv/factory/<instance>/factory/agents` |
| `FACTORY_CONTAINER_ENV` | Names of variables passed into every container. | none | `HTTPS_PROXY,NO_PROXY` |
| `FACTORY_CA_BUNDLE` | The PEM file with the company's certificates. | none | `/etc/ssl/corp-ca.pem` |
| `FACTORY_PROVIDER_LIMIT_STATUS` | The HTTP status that means the provider's limit. | `428` | `429` |
| `FACTORY_PROVIDER_LIMIT_MESSAGE` | A regular expression that matches the limit's text. | none | `usage limit` |
| `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` | The wait when the message names none. | `10` | `5` |
| `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` | The total of the waits after which the run ends `provider_limit`. | `120` | `60` |
| `FACTORY_OPENCODE` | The path of an own opencode build. | `opencode` | `/usr/local/bin/opencode` |
| `FACTORY_OPENCODE_VERSION` | What the build's `--version` prints. | none | `1.19.5` |
| `FACTORY_OPENCODE_MODELS` | Maps `opus`, `sonnet` and `haiku` to `<provider>/<model>`. | none | `opus=corp/big,sonnet=corp/big,haiku=corp/small` |
| `FACTORY_OPENCODE_PROVIDER_FILE` | The provider file. | none | `/srv/factory/<instance>/provider.json` |
| `FACTORY_TOKEN_URL`, `FACTORY_TOKEN_SCOPE`, `FACTORY_TOKEN_CLIENT_ID`, `FACTORY_TOKEN_CLIENT_SECRET_FILE` | The token refresher's inputs. | none | see *A bearer token for the model API* |

### The login shell

The shell is started as `/bin/sh -c <script> factory-login --api-login <api file> <token file> claude ...` when `FACTORY_API_LOGIN_FILE` is set, with an empty word in place of the token file when `FACTORY_CLAUDE_LOGIN_FILE` is unset. Without the API setting it is `/bin/sh -c <script> factory-login <token file> claude ...`. The shell tells the runtime on standard error which login it handed over: `factory-login-used: api_key`, `subscription` or `none`. The runtime turns that into the run's `login`.

### The container's words

```text
podman run --rm --userns=keep-id --timeout <seconds> --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=4g --env NAME=value ... --volume <dataset>:/work --volume <login file>:<login file>:ro --volume <instructions file>:<instructions file>:ro --workdir /work/checkout <image> /bin/sh -c <login shell> ... claude -p ...
```

Under opencode the last words are `opencode run ...`. The login files and the call's instructions (or configuration) file are mounted read-only at their own paths, so the login shell reads the token or key as on a host and the container cannot change them. The container environment the runs use is described in "The stage environment" under *Configuration* in [install.md](install.md).

### The faults of a login file

The run stops with `agent runtime failed: ` and one of these, and no call is made.

| Message | Cause |
| --- | --- |
| `cannot read the agent's login file <path>: cannot be read` | The token file is a folder or unreadable. |
| `cannot read the agent's login file <path>: not ASCII text` | The token file is not plain ASCII, for example UTF-16 from PowerShell 5. |
| `cannot read the agent's API login file <path>: cannot be read` | The same for the API key file. |
| `cannot read the agent's API login file <path>: not ASCII text` | The same for the API key file. |

### The faults of an agent file

The reader reports these. `read` names the agent, and a fault with a key names that key.

| Fault | When |
| --- | --- |
| `no agents directory at <path>` | `<agent home>/agents` is absent or not a directory |
| `not an agent name: <name>` | the name is not a valid name, so no file is looked up |
| `no agent file <path>` | the file is absent or is a directory |
| `cannot read: <reason>` | the file cannot be read or is not UTF-8 |
| `no front matter` | the file does not start with front matter that is closed |
| `front matter is not valid YAML` | the YAML does not load |
| `front matter is not a mapping` | it loads as a list or a scalar |
| `key not applied by the agent runtime: <key>` | the front matter holds a key outside the four below; the first such key in the file's order is named |
| `missing key: <key>` | `model`, `tools` or `budget_usd` is left out |
| `budget_usd must be greater than 0` | zero, negative, text or a boolean |
| `invalid <key>: <reason>` | any other value of the wrong type |

When a file has several faults, the first is reported: a key that is not applied before a missing key, and a missing key before an invalid value.

Keys that would read as if they did something are refused, for example `name`, `description`, `permissionMode`, `hooks`, `background`, `disallowedTools`, `skills`, a misspelt key, or a known key in another case such as `Model`.

### The keys of an agent file

| Key | Meaning |
| --- | --- |
| `model` | required, text |
| `tools` | required, a list of texts; `[]` is allowed |
| `effort` | optional, text |
| `budget_usd` | required, a number greater than 0 |
