# The agent runtime and the agent files

A topic of the [operator guide](README.md).

## The agent runtime

The factory runs each agent as a `claude -p` call under Claude Code, or as an `opencode run` call under opencode (see "Running on opencode"). The rest of this passage is about Claude Code. It needs the `claude` program and the agent's login (an API key file, the token file, or a session logged in by hand when neither holds one). The factory itself holds no key or token: the call's own shell reads them. The call gets only the environment the run's request gives, with no variable inherited from the factory. The flags are those of v1; the preflight's item `agent-run-probe` makes one call with them once for each image build, so a flag the pinned `claude` rejects stops the machine before any claim. If a call fails at once, see "The probe of the agent run" in [health.md](health.md). The factory asks `claude --version` and takes the first word of its output (for example `2.1.289`). The pinned version is the one the flags were written for; the preflight compares it with `FACTORY_CLAUDE_VERSION` (see "The preflight's items" in [health.md](health.md)).

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

Every agent call runs in a throwaway container as the host's `factory` (`--userns=keep-id`). No second user and no `sudo` stand between the factory and the agent: the only fence on the host is the folder of the token file (see "The hosting-service token" in [health.md](health.md)). The agent's home is the dataset's `home/`, and the dataset's rollback clears it before every stage.

The take keeps the write paths. It copies out of the dataset only the changed paths the role may write, and the dataset's rollback discards the rest. A write elsewhere is lost, not refused: temporary files go through `mktemp` or `tempfile`, and they are lost with the stage. No kernel rule stands behind this.

**The agent's login token.** The login is a token, made once for all instances and the Podman machine:

1. Run `claude setup-token`, on the host where Claude Code is installed, or on the VM as `factory`.
2. Save the token it prints, with nothing else in the file, as `/home/factory/.secrets/claude-token` (see "The machine" in [machine.md](machine.md), step 8 of "On GCP, step by step" in [machine.md](machine.md)). If you write it on Windows, use plain text without a byte-order mark, for example `Set-Content -NoNewline -Encoding ascii claude-token <token>`: PowerShell 5's `>` writes UTF-16, which is not read as the token.
3. Install it with `install -m 0600 -o factory -g factory`, as the steps of "The machine" in [machine.md](machine.md) show, so that only the factory's user can read it.

The environment file sets `FACTORY_CLAUDE_LOGIN_FILE` to its path, and the agent's container mounts it read-only. The file must exist, even empty: podman refuses to mount a missing one.

An empty file means no token, and the agent then needs the manual login: run `claude` once as `factory` on the VM. Since F0044-S0001 the runtime no longer sets `CLAUDE_CONFIG_DIR`, so `claude` keeps its `.claude.json` in the home's root.

**The agent's API key.** An instance can run its agents on an Anthropic API key instead of the subscription, for example at a workplace that has a key and no subscription. This repository's own build stays on the subscription.

1. Save the key, with nothing else in the file, as `/home/factory/.secrets/anthropic-api-key`, as plain ASCII text. On Windows use `Set-Content -NoNewline -Encoding ascii`, as for the token: a file saved as UTF-16 stops the run with `agent runtime failed: cannot read the agent's API login file <path>: not ASCII text`. A file that is a folder or unreadable stops it with `...: cannot be read`. No call is made in either case.
2. Set the file's permissions as for the token file.
3. An instance has its own file: the VM holds one instance, and the file is in its `factory` user's folder.

The environment file sets `FACTORY_API_LOGIN_FILE` to its path, and the agent's container mounts it read-only.

- The file must exist, even empty, or podman refuses to mount it (as for `claude-token`). An empty file means no API key.
- A key in the file wins over the token, which is not read then. Anything else in the environment named `ANTHROPIC_API_KEY` is dropped; the file is the only source.
- The file is read at every call, so a new key applies from the next call, without a restart. The key stands in no argument, run file, result, journal entry, cost record or log, and not in the factory's own environment.
- Switching back to the subscription means emptying the file; the next call reads it as it is.

Which login is in force: the cost record of each run has the field `login`, which is `subscription`, `none` or the value for the API key (a line written before the field existed lacks it), and the preflight writes one factory-log line for the probe, for example `preflight: agent-run-probe: the agent runs log in with the API key from <file>`. The line comes with each run of the machine's items, so once for each image build.

### The agent in a container

The call runs in a throwaway container. The words are `podman run --rm --userns=keep-id --timeout <seconds> --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=4g --env NAME=value ... --volume <dataset>:/work --volume <login file>:<login file>:ro --volume <instructions file>:<instructions file>:ro --workdir /work/checkout <image> /bin/sh -c <login shell> ... claude -p ...` (`opencode run ...` under opencode). The login files and the call's instructions (or configuration) file are mounted read-only at their own paths, so the login shell reads the token or key as on a host and the container cannot change them. The call gets only the environment the request gives, with `HOME=/work/home`. A call that podman's `--timeout` ends is a run that reached its time limit, not resumed; podman ends the container with exit status 255, which the factory reads as the time limit when the call lasted at least its limit. `claude --version` runs in the container too, so the preflight's `agent-runtime-version` compares the pin with the runtime in the stage image (the image is F0043's). The wiring gives the runtime this chain (see "The stage environment" under *Configuration* in [install.md](install.md)).

Every container (the sync, the agent and each check) has the same fence. It has no capabilities (`--cap-drop=all`), and no set-uid program gives it rights (`--security-opt=no-new-privileges`). It may start 4096 processes and use 4 GB of memory. It keeps podman's default network, because the sync and the check's `make sync` need the package index and the agent needs the model's API. A container the kernel kills for its memory before the time limit is an ordinary failure, not a time-out: a failed check, usually with make's exit status 2 when the kernel ended one of its children, or 137 when it ended the container's first process.

### Behind a proxy

A container's environment is closed: the factory's own environment reaches none of them. Two settings open it for what a company network needs.

- `FACTORY_CONTAINER_ENV` lists names, for example `HTTPS_PROXY,NO_PROXY,UV_INDEX_URL,NPM_CONFIG_REGISTRY` (the proxy, the hosts that bypass it, a package mirror for `uv` and for `npm`). Each name that the factory's environment holds is passed, with its value, into the agent, sync and check containers. Put the variables in `factory.local.env` (see "The environment file" in [machine.md](machine.md)), where they are also in the factory process's own environment (see the same section), and list their names in `FACTORY_CONTAINER_ENV`; the factory reads its environment when it starts, so restart the service after a change.
- `FACTORY_CA_BUNDLE` is the PEM file with the company's CA certificate. It is mounted read-only into the same containers at its own path, and `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` name it. If a listed name is one of those three, the bundle's value wins.

The bundle must hold the public certificates beside the company's own: `SSL_CERT_FILE` replaces Python's own list of authorities instead of adding to it, so a file with the company's certificate alone breaks every connection to a public host.

The names the factory gives a container itself win over the list: a listed `PATH` leaves each container's own `PATH`. `HOME`, the two login names, `OPENCODE_CONFIG`, `GIT_ASKPASS` and every `FACTORY_` name are refused when the settings are read, so the hosting token (`FACTORY_TOKEN_FILE`) reaches no container. The allow list stays closed for every other name, and the login names are still removed where they were before. With neither setting the containers are as before.

`vm/setup.sh` and the build of the stage image run outside the factory and read none of these settings: give them the proxy (and the mirror) in their own environment.

### The agent run's `PATH` and `HOME`

The factory builds the environment of an agent run itself, from an allow list of six names (see "The hosting-service token" in [health.md](health.md)). The agent runs in the stage image, so the two names that matter here are a `PATH` of the directory where the factory's console scripts are installed (the directory of the factory's Python) followed by the `PATH` the stage image sets (`/usr/local/bin:/usr/bin:/bin` when it sets none; see "The project's stage file" in [machine.md](machine.md)), and a `HOME` of `/work/home`, the dataset's. The `HOME` is the same whatever the instance's settings, and no preflight item checks it: it is a path inside the container, not a directory on the factory's machine. Nothing else reaches the agent but the locale and time-zone names `LANG`, `LC_ALL`, `TERM` and `TZ`, when the factory process has them, and the names of `FACTORY_CONTAINER_ENV` and `FACTORY_CA_BUNDLE` (see "Behind a proxy"). So the tools an agent needs must be in the stage image, in a directory of that `PATH`.

### A provider's spend limit

Some gateways limit the spend per model in a rolling window and answer a call past it with an HTTP error (the human's gateway: status 428, about $3 per 10 minutes). Without a rule the run would end `died`. The factory gives it its own end reason, `provider_limit`, and keeps the run's session in the result so that a later run can continue it.

- What matches: the status in `FACTORY_PROVIDER_LIMIT_STATUS` (default 428) as a whole number in the text (`HTTP 428:` and `(428)` match; `14280` does not), or a text the regular expression in `FACTORY_PROVIDER_LIMIT_MESSAGE` finds. Set the message when the gateway's text is not known to carry the status.
- Where it is looked for: in the error result the `claude` call printed, or, when no result could be read, in a line of its standard error. The opencode runtime looks for it while the run streams: in an `error` event (its `statusCode`, or the limit in its message) or in a line of standard error, and stops the run at once with the session kept. Never in the agent's own text, so an agent that writes "428" in a report cannot end its run.
- A run past its time limit, or stopped by its budget, keeps that end reason; the limit is looked for only when neither applies.
- A message that names a wait (`in 7 minutes`, `after 30 s`, `retry-after: 420`) gives the run's wait; otherwise none is known.
- The cost record's `end_reason` is `provider_limit`, and the record carries the refused calls (`denials`, `denied_paths`) like any run that replied.
- The factory waits the limit out and continues the run; see below.

**A run that ends `died`.** A run whose text matches neither rule, or that exits non-zero or gives no reply, ends `died`, and the factory log names it with one line, time-stamped like the others: `run <run id> of <work item> (<stage>) died: <text>`. The text is what the agent runtime gave as the reason: the error reply's text, else the last 3 non-empty lines of standard error (without the login shell's `factory-login-used:` line), else `exit <status>` (negative for a signal). Lines are stripped and joined with ` / `, and the text is cut to 300 characters with `…` at the end. The agent's own answer is never quoted. When a provider's usage limit is the cause and the run ended `died` instead of `provider_limit`, this text is what `FACTORY_PROVIDER_LIMIT_MESSAGE` must match: copy a stable part of it into that expression. The cost record is the same as before and carries no text.

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

**What to do at the ceiling.** The stage stalls with the cause `the provider's spend limit lasted past the waiting ceiling`: one attempt is counted and the note is on the pull request (see "A stall: the stall note" in [stops.md](stops.md)). The next tick runs the stage again from what the stall kept, and at the attempts cap the factory asks you. A limit that lasts two hours is not a rolling window passing: look at the gateway (its quota, its window), or raise `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES`, before you answer.

**The claim stays held while waiting.** The factory renews no lease, so a stage that waits may hold its claim past its `lease_duration` (the coder's time limit, the ceiling and the checks come to about 180 minutes, against a lease of 60). Only another instance on the same repository would act on the age; run one instance per repository.

**A stop or a restart during a wait** is a crash of the factory's own claim: the stage runs again at once and counts toward the crash cap, not toward the attempts (see "A restart during a stage" in [work-items.md](work-items.md)). The wait starts over.

### An opencode run's budget

opencode has no budget flag, so the factory keeps the budget of an opencode run itself: it adds up the cost of every step as the run prints it and stops the run when the sum is above the agent's budget. It then resumes the session once with a quarter of the budget (at least 0.50 USD), as for a `claude` run. A step is counted when it ends, so a run may pass its budget by the cost of one step.

### Running on opencode

An instance runs its agents on Claude Code unless the operator sets `FACTORY_AGENT_RUNTIME=opencode` (`--runtime opencode` of `vm/setup.sh`). The stage image holds only the runtime it was built for, so an opencode instance needs an image built with `AGENT_RUNTIME=opencode` (see "The stage image" in [machine.md](machine.md)). `opencode-ai` is installed from npm at the version `OPENCODE_VERSION` of `vm/Dockerfile`, and the environment file sets `FACTORY_OPENCODE_VERSION` to it.

**The login.** An opencode run logs in with the API key in the file `FACTORY_API_LOGIN_FILE` names (see "The agent's API key"). Every run is then paid through the API. The subscription token is not used.

A login that an operator's own build keeps in the agent's home does not work on the machine: the home is `home/` on the dataset, and the rollback to the base clears it before every stage, so nothing made by a login command survives to the next run. Put the key in the API login file, whatever the build.

The preflight does not read the key: the probe of the agent run shows whether a run can log in.

**Your own build.** Choose an opencode build with `FACTORY_OPENCODE` (its path), `FACTORY_OPENCODE_VERSION` (what `--version` prints) and `FACTORY_OPENCODE_MODELS`: add them to `factory.local.env` (see "The environment file" in [machine.md](machine.md)), install the build on the VM and restart the instance. The values `factory.env` carries are the stage image's `opencode-ai`, its pin in `vm/Dockerfile` and the three Anthropic ids.

**The models.** The agent files name `opus`, `sonnet` and `haiku`. `FACTORY_OPENCODE_MODELS` maps each to a `<provider>/<model>` id of opencode; `vm/Dockerfile` pins `opus=anthropic/claude-opus-5-5,sonnet=anthropic/claude-sonnet-5-5,haiku=anthropic/claude-haiku-5-5`. Check that an id exists with `opencode models anthropic`. A model written with a `/` in an agent file is used as it is.

**The version.** The stage image pins opencode (`OPENCODE_VERSION` in `vm/Dockerfile`); the item `agent-runtime-version` compares `opencode --version` with `FACTORY_OPENCODE_VERSION`. The pins are changed in `vm/Dockerfile` alone (see "The stage image" in [machine.md](machine.md)).

**The item `opencode`.** See "The preflight's items" in [health.md](health.md) for its two faults and what to do about each.

**What opencode keeps in the agent's home.** Sessions, logs and caches in `.local/share/opencode`, `.local/state/opencode` and `.cache/opencode`, for the length of one stage (the dataset's rollback clears them). The configuration in `.config/opencode` is what the next run reads, and an agent that could write it could loosen its own permissions.

**What differs from Claude Code.**

- The denied commands of `settings.json` become `deny` permissions in the run's own configuration file.
- No structured reply. The agent ends its message with a `<factory-result>` block; a reply without a valid block ends the run `no_result`.
- The budget is the factory's own (see "An opencode run's budget").

### A company's provider

An operator behind a company proxy that speaks the OpenAI protocol points opencode at it with a provider file. Set `FACTORY_OPENCODE_PROVIDER_FILE` to the file's absolute path in `factory.local.env` (see "The environment file" in [machine.md](machine.md)) and restart the instance. The file holds one provider and the small model; the runtime merges them into the configuration of every run, beside `autoupdate`, `share`, `snapshot` and the agent, and changes none of those keys. With the setting unset the configuration is as it was.

The preflight's `agent-run-probe` is where you see whether the pinned opencode accepts the provider file and reaches the proxy; see "The probe of the agent run" in [health.md](health.md) for when it runs.

An example, with made-up names:

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

- `id`: the provider's id in model names: lower-case letters, digits and `-`, starting with a letter.
- `base_url`: `http://` or `https://` and a host. A trailing `/` is kept as written.
- `api_key_env`: the name of the environment variable that holds the key (capitals, digits and `_`, not starting with a digit). The key itself is never in the file: the runtime writes `{env:<name>}` into the configuration. The key stays in the file `FACTORY_API_LOGIN_FILE` names (see "The agent's API key"), which the run's login shell exports as `ANTHROPIC_API_KEY`, so the name to give is `ANTHROPIC_API_KEY`.
- `models`: at least one model, by the name the proxy knows. Each may have `name`, `context` and `output` (token limits, whole numbers of at least 1, given together) and `input_cost` and `output_cost` (dollars per million tokens, at least 0, given together). A model with none is `{}`.
- `small_model`: `<id>/<model>`, one of `models`. opencode otherwise takes its small model from a service of its own, which a proxy does not offer.

Any other key is refused. A fault ends the run with `cannot use the opencode provider file <path>: <reason>`, the reason naming the first field at fault, and no run file is written and nothing starts.

To use the provider, map the aliases to it in `FACTORY_OPENCODE_MODELS`, for example `opus=corp/big,sonnet=corp/big,haiku=corp/small`.

A model without prices is costed at 0, so the factory's own budget stop (see "An opencode run's budget") never fires for it. Give `input_cost` and `output_cost` when the budget is to count.

**What opencode may load and contact.** With a provider file the runtime also limits what opencode loads. The configuration gains `enabled_providers`, holding only the file's provider id (`["corp"]` for the example), and no `disabled_providers`. The call's environment gains `OPENCODE_DISABLE_MODELS_FETCH=1`, `OPENCODE_DISABLE_AUTOUPDATE=1` and `OPENCODE_DISABLE_DEFAULT_PLUGINS=1`; the runtime's values win over the same names in a request's environment. Of the three, `OPENCODE_DISABLE_MODELS_FETCH` is the one that changes traffic: without it every run contacts opencode's public model catalogue, `models.opencode.ai`, once. The other two stay as upstream's own guards. They depend on the provider file because the file already defines the models; without it opencode needs its public model list, so a run without the file is unchanged, byte for byte.

One contact stays: opencode 1.19.3 asks `registry.npmjs.org` at the start of every run, most likely for the provider's npm package, and no switch removes it. A deployment that must prove that a run sends nothing to the vendor reads the proxy's log, or runs the startup probe in `planning/cloud-sandbox/`.

### A bearer token for the model API

A model API behind an OAuth2 client-credentials grant gives out a bearer token that lives about an hour. The opencode runtime reads the file `FACTORY_API_LOGIN_FILE` names at every call and hands its content to the agent as `ANTHROPIC_API_KEY`, so the token only has to be kept fresh in that file. `python -m factory.entry.refresh_token` does that, as a process of its own beside the factory; the runtimes change nothing. Starting it with the instance is the start script's business (see "The machine" in [machine.md](machine.md)).

It reads five variables. A missing or blank one prints `refresh_token: <variable> is not set` to standard error and exits 2.

| Variable | Meaning |
|---|---|
| `FACTORY_TOKEN_URL` | The grant's token endpoint. |
| `FACTORY_TOKEN_SCOPE` | The scope to request. |
| `FACTORY_TOKEN_CLIENT_ID` | The client id. |
| `FACTORY_TOKEN_CLIENT_SECRET_FILE` | The file that holds the client secret, as UTF-8 text (surrounding whitespace is dropped). Secret Manager mounts it; the secret is never in the environment. A missing, blank or non-UTF-8 file exits 2 with `refresh_token: cannot read <path>`. |
| `FACTORY_API_LOGIN_FILE` | The file to write: the same one the runtime reads. |

What it does:

- It requests a token, writes it into the login file with nothing else (no newline) and replaces the file atomically, so a reader sees the old token or the new one. It prints `token refreshed: valid <n> s, next in <m> s`.
- It repeats every ten minutes, or after half the token's life when that is shorter (a token that lives under twenty minutes would expire between two refreshes), and never sooner than thirty seconds.
- A failed request, or any other fault of one refresh, prints `refresh_token: <the error>`, keeps the old file and tries again after a minute. The client secret and the token are replaced by `***` in every message.
- `--once` refreshes once and exits 0, or 1 after printing the error. Without it the command runs until `SIGTERM` or `SIGINT` and exits 0.

A container mounts the login file when it starts, and its login shell reads it once. A run therefore holds the token that was in the file at its start, which is at least the token's life less ten minutes old: with a one-hour token, fifty minutes, more than the longest stage. Use a grant whose token lives longer than ten minutes plus your longest stage.

The provider file's `api_key_env` is `ANTHROPIC_API_KEY` (see "A company's provider"), which is the variable the login shell fills from this file.

**The proxy.** The request goes through Python's standard library, which honours `https_proxy` and `no_proxy`. Set `https_proxy` in the refresher's environment when the token endpoint is reached through a proxy, and `NO_PROXY` for an internal API host the agents reach directly.

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

The body, without the whitespace around it, is the instructions; a line of hyphens inside it belongs to it. These four are the only keys the agent runtime applies: Claude Code ignores an agent file in print mode, so the runner builds its flags and its prompt from them itself. Any other key (`name`, `description`, `permissionMode`, `hooks`, `background`, `disallowedTools`, `skills`, a misspelt one, or a known key in another case such as `Model`) would read as if it did something and do nothing, so the file is refused when the pipeline definition is loaded. See "The stop `agent_definition_invalid`" in [stops.md](stops.md).

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

The skills are the human's files, like `CLAUDE.md`: `.claude/*` is a protected path that no stage writes, and the factory does not check what a skill says. `.claude/` is protected at any depth (`.claude/*` and `*/.claude/*`), so no stage writes a `.claude/` folder anywhere in the repository, `src/.claude/skills/` included (the human, 2026-10-19). The take leaves a nested `.claude/` write out after every run: it copies nothing from such a folder, also where a write path opens it, and the entry names the path. A run reads the root `.claude/skills/` from its checkout, the work item's branch.

Only Claude Code's runs are given the `Skill` tool. An opencode run leaves it out (the runtime turns on no opencode tool for it and does not refuse the agent), and the factory does not check whether opencode loads skills of its own.

### The shipped agents and settings

The checkout ships seven agents (`intake`, `tester`, `coder`, `reviewer`, `documenter`, `smoke-tester`, `acceptance-reviewer`) and `settings.json`. Each agent's `tools` ends with `Skill`, and the settings allow it in `permissions.allow`, right after `Grep`. The instance reads them from `FACTORY_CLAUDE_HOME` (`/srv/factory/<instance>/factory/claude`, the `claude/` folder of the factory's own clone), so change the files in the repository: a change reaches the instance by a merge and the steps of "The rebuild after a merge" in [machine.md](machine.md). The settings let an agent run `factory-check-story` and no other `factory-` command: it cannot run `factory-run`, `factory-watch` or `factory-bill`. They also deny `git add` and `git commit`, because an agent leaves its changes in the working tree and the factory makes the result commit (an agent has no git identity of its own), and `git push`, `gh` and the commands that move or rewrite branches, because the factory alone pushes. A new project starts from `template/` in the factory's checkout (a pipeline definition, a `CLAUDE.md` and a `Makefile` whose `SOURCE` and `LAYERS` placeholders you fill in); the story and feature forms are yours to add, and every stage stops until `factory/story-form.md` exists.

The smoke tester has two ways out when it finds something. When every finding is a slip in a document the documenter writes (the command read the document and found a sentence the code contradicts, or the contradicted criterion is the `docs:` one) and the code does what the work item says, it ends with `docs`, and the documenter fixes exactly those findings and ends with `smoke-test`. With any other finding, or a mix, it ends with `doing`. Both count as rework rounds.
