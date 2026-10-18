# Pre-check F0020, round 1: the feature, its human's changes and its decisions

I played this against v1.1's shipped roles (`claude/agents/*.md`), `factory/feature-form.md`, `factory/story-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml` and the `Makefile`, and against factory-rf as it is on 2026-10-18.

During the pre-check the human sent a new fact, relayed by the coordinator. At the human's work:
- a company build of opencode logs in through the company's single sign-on, not with an API key;
- it knows its own endpoint.

It changes S0008, decisions 2, 10, 17 and 21, and the goal (F3 to F8).

The nine stories have their own files beside this one.

| Story | Verdict |
|---|---|
| S0001 | pass with two required edits (E1 re-exports by `__all__`, E2 the `recorder` fixture moved) and two recommended (E3, E4); change 1 before the merge |
| S0002 | pass with one required edit (E1 re-exports by `__all__`) and one recommended (E2) |
| S0003 | pass with one recommended edit (E1) |
| S0004 | refuse as drafted (`PLR0913` makes `make lint` red without the new change 7); pass with change 7 on `main` and the recommended E2 to E4 |
| S0005 | pass with one recommended edit (E1) |
| S0006 | pass with one recommended edit (E1); change 7 first |
| S0007 | pass with two recommended edits (E1, E2) |
| S0008 | refuse for the human's work as drafted (new fact: E1 key optional, E2 the build is the operator's, E3 the build's folders); pass with E1 to E4 |
| S0009 | pass; recommended: not built yet (decision 15) |

## How the facts were checked

- **Read.** The feature, the nine stories, the drafter's brief, the opencode probe of 2026-10-17, v1.1's roles and forms, and the code and tests each story file names. Also F0019's `feature.md` and its journals in `done/`:
  - The intake asked for missing criteria in S0001 and S0004.
  - A structural test contradicted a story in S0002 (the human's leave in entry 8).
  - Reviews sent S0002 and S0003 back over criteria shape and untested clauses.
  - `mutants/seed/.git` crashed A0001 twice. `81fd6131` fixed it on `main`.
  - The lessons the drafter took over are visible: leaves named, helpers imported, both sides of each rule as rows.
- **Run, in temporary folders outside the repository (all removed):**
  - `factory-check-story` on all nine stories, in a throwaway container of `factory-self-factory`. All gave `: ok`.
  - ruff 0.17 with the project's configuration on scratch files:
    - `import X as X` gives `PLC0414`;
    - an imported fixture gives `F811`;
    - a 6-argument `__init__` gives `PLR0913`.
  - detect-secrets 1.5 on a scratch file: `API_KEY = "..."` and `{"ANTHROPIC_API_KEY": "..."}` are flagged; the stories and `feature.md` scan clean.
- **Not run:** every smoke test. Each imports a name its own story makes, so none can run before its story. S0008's closing `grep` gives `0` today. I traced each against the Interface; see the story files.
- **Not read:** anything under `image/secrets/`, and any token or key.

## The opencode facts against the probe

The probe (opencode-ai 1.19.3, one machine, four runs) saw these, and the stories rely on them:
- `run --format json` with standard input closed;
- the events `step_start`, `text`, `tool_use` (with `state.status` and its error), `step_finish` (with `tokens` and `cost`);
- `sessionID` and a timestamp on each event;
- `--session`, `--agent` and `--auto`;
- `bash` permissions per pattern;
- the snapshot folder in the home.

The stories assume more than the probe saw. Only the hand probe or the real run shows these:
- `OPENCODE_CONFIG`;
- the `agent` map with `mode`, `prompt`, `tools` and `permission`;
- the keys `snapshot`, `share` and `autoupdate`;
- the long option `--model` (the probe used `-m`);
- the exact field names under `part` (`tool`, `state.input`, `state.time`, `tokens.cache.read`/`write`);
- the `error` event's shape (`error.data.statusCode`, `error.data.message`);
- that a deny after `"*": "allow"` wins;
- that nothing is written under `~/.config/opencode`;
- whether opencode prints anything at all on an HTTP 428, or retries or hangs silently.

Decision 20 names most of these. F6 adds the rest.

## The human's changes

1. **The empty key file before S0001's merge: correct and needed.**
   - `create_host_path: false` makes Compose refuse a missing source. Without it, Docker makes a folder in the file's place, and the login shell would then refuse every run with `factory-api-login: cannot be read`.
   - There is no tolerant form that is also safe:
     - a short-syntax bind creates that folder;
     - a folder bind needs its folder to exist just the same;
     - a Compose `secrets:` file must exist too.
   - The only way around it is a script that reads a Docker-made empty folder as "no key". That would also hide a wrong `FACTORY_API_KEY_FILE`. Not recommended.
   - **The order is safe for `self`.** The running container never re-reads the compose file. The file only has to exist before the next `docker compose up` that uses S0001's compose file, and creating it now changes nothing (today's compose file does not name it).
   - The tests read the compose file as YAML and start no Compose, and the smoke tester runs inside the running container, so neither needs the file.
   - The same holds under Podman, as it does for `claude-token`.
   - `tests/test_claude_token_mount.py` reads the token's bind as `_volumes()[3]`. The new bind is the fifth entry, so that test stays green. Decision 19's leave for `tests/test_compose.py` is the only one needed.
2. **The `CLAUDE.md` sentences: correct, but needed earlier, and with one more login.**
   - Before S0004 starts, R5 says the agent runtime is "reached only through one wrapper class". S0004's intake (step 4, the architecture) and its reviewer read `CLAUDE.md`, and either could ask.
   - Recommended: make change 2 **before S0004 starts**, and name the single sign-on login (F11).
3. **The Vocabulary sentence: correct**, after S0005.
4. **The hook's cross-check: correct.** The build is Claude Code's on `self`.
5. **The template's and the demo's lines: correct.**
   - Both `Makefile`s have exactly the four lines quoted (lines 74 to 77), and the template's `test` recipe has the quoted `uv run pytest` line.
   - The demo's `pyproject.toml` has `branch = true` under `[tool.coverage.run]`.
   - The template has no `pyproject.toml` of its own.
   - `tool_paths` is a valid key since F0019.
   - It stays needed for the opencode demo run: the kernel refuses a `.coverage` at the root.
6. **The todo-demo run: correct for the run at home, on a key.** The run at the human's work is another, with the company build and single sign-on. It is the new change 8.
7. **Missing: `PLR0913` for the opencode runtime, before S0004 starts.**
   - `pyproject.toml` exempts only `claude_runtime.py`.
   - S0004's constructor has 10 parameters (11 with S0006, 12 with S0008's E3), against `max-args = 5`.
   - `make lint` is red as drafted, and `CLAUDE.md` allows no `noqa` outside the process module. Text in F2.
8. **New: the run at the human's work** (after change 6, or instead of it there). Text in F12.

## The decisions

- **1, 3, 5, 6, 7, 8, 9, 11, 12, 13, 18, 19, 22: correct as checked.**
  - Decision 5: one `Popen` line keeps `tests/test_process_search.py` green.
  - Decision 6: `claude/settings.json`'s `deny` entries are all `Bash(<pattern>*)`, opencode's wildcard form.
  - Decision 19: the three leaves are the only earlier tests that change. The `recorder` fixture moves under the standing leave (S0001's E2).
- **2: wrong for the human's work** (new fact). The item `opencode` must not need a key (F3; S0008's E1).
- **4: right in substance, wrong in form.** `X as X` is ruff's `PLC0414`; use `__all__`, as `settings` and `wiring` already do (F1).
- **10: incomplete for the human's work.** A build that logs in through single sign-on keeps that login somewhere in the home and may refresh it during a run. Name the folders by a setting, and make the one-time login the operator's step (F4; S0008's E3).
- **14: right.** I checked it against the lease code:
  - v1.1 renews no lease, and `lease_age` counts from the claim's start.
  - The coder's lease is exactly its time limit plus its check and report (40 + 15 + 5 = 60). Any wait therefore outlives the lease when the run uses its whole limit, and a 10-minute wait does once the run and checks pass 50 minutes. At the ceiling a stage holds its claim for about 180 minutes.
  - Only another instance would act on that (`claim_status` is `own` "whatever its age"), and one repository has one instance.
  - A restart during a wait is a crash of the instance's own claim. It counts toward `crash_cap`, not the attempts.
  - The stall past the ceiling counts one attempt, and the waits count toward nothing.
  - Say the lease part in the decision and the operator guide (F9; S0007's E2).
  - **Recommended: yes**, over the machine-stop alternative.
- **15: recommended not yet** (S0009's H1).
  - The coder's $4 and the reviewer's $3 budgets are each above the gateway's $3 per 10 minutes, so limits inside runs come whatever the throttle does. S0007 survives them.
  - Build S0009 when the work run's log shows that the waits cost enough.
- **16: recommended yes** (per instance). It is all the work needs, and it keeps tools out of the pipeline definition (R8).
- **17: incomplete** (new fact). The image's `opencode-ai@1.19.3` must be only the default. The operator chooses the build, its version and its models per compose call (F5; S0008's E2).
- **20: add** the facts listed above (F6).
- **21: narrower** (new fact). The company build knows its endpoint, so only a Claude Code instance on an API key needs a base URL.
  - Recommended: **not in F0020**, because the human's work does not need it.
  - It becomes a later story when such an instance is wanted: `FACTORY_API_BASE_URL` handed to Claude Code as `ANTHROPIC_BASE_URL` (F7).

## Points for the human, with the recommended answers

- **H1. opencode silent on a 428.**
  - If opencode prints no `error` event and no standard-error line while it waits on the limit, S0006 cannot see it. The run ends `time_limit` after 40 minutes and stalls.
  - Recommended: **wait for the run at work.** If it happens, add a later story with an idle stop: no event for N minutes counts as a provider limit, and the session is resumed.
- **H2. Proxy and CA variables.**
  - The agent run's environment carries six names only, so `HTTPS_PROXY`, `NO_PROXY` and `NODE_EXTRA_CA_CERTS` do not reach a run.
  - Recommended: **check in change 8's hand probe.** If they are needed, add a later story with a setting that names extra environment names for agent runs.
- **H3. Split S0004.** Recommended: **only if a pass ends at its budget** (S0004's H1).
- **H4. The SSO login's persistence.**
  - Recommended: **the operator's step**: a login after each container recreation, or a compose override that mounts the folder.
  - Not a shipped volume, because nobody here has seen the folder (S0008's H2).
- **H5. Decisions 14, 15 and 16:** yes, not yet, and yes (above).

## Verdict

`F0020: the order and the sizing hold (S0004 the largest); required: change 7 (PLR0913) before S0004, decision 4 by __all__ (F1), and for the human's work S0008's E1 to E3 with F3 to F5, F7, F8, F10 and F12; recommended: change 2 before S0004 (F11), F6, F9`

## Replacement texts

### F1 (required): decision 4, the re-exports

Replace

```text
stays a name of that module that it reads at the call, defined there or re-exported with `as`, so no earlier test changes.
```

with

```text
stays a name of that module that it reads at the call, defined there or imported and listed in its `__all__` (never `import X as X`: ruff's `PLC0414`), so no earlier test changes.
```

### F2 (required): the human's change 7

In *The human's changes*, replace

```text
No new structural test that reads the source, so `[tool.mutmut]` in `pyproject.toml` stays as it is.
```

with

```text
No new structural test that reads the source, so `[tool.mutmut]` in `pyproject.toml` stays as it is; `[tool.ruff.lint.per-file-ignores]` gains one line (change 7).
```

and add after change 6

````text
7. Before S0004 starts: `pyproject.toml`, `[tool.ruff.lint.per-file-ignores]`, a new line right after the one of `src/factory/adapters/claude_runtime.py`, because the opencode runtime's constructor takes ten parameters (eleven with S0006, twelve with S0008), beside the Claude Code runtime's, and ruff's `PLR0913` (`max-args = 5`) would turn `make lint` red:

   ```toml
   "src/factory/adapters/opencode_runtime.py" = ["PLR0913"]  # F0020-S0004 pins the second runtime's constructor beside the first's; no noqa in the source
   ```
````

### F3 (required, new fact): decision 2

Replace

```text
The preflight's item `opencode` checks only that the file is there and not empty, by its size. (S0001, S0008)
```

with

```text
The preflight's item `opencode` does not look at the key file: an API key is optional for opencode, whose operator's build may log in through single sign-on with a login it keeps in the agent's home (the human's fact of 2026-10-18), and whether a run can log in is the agent-run probe's to show, whose detail names the login in force. (S0001, S0008)
```

### F4 (required, new fact): decision 10

Before `(S0004, S0008)` at the end of decision 10, add

```text
An operator's own build may keep its state, its single sign-on login above all, in other folders of the home and refresh the login during a run: the operator names them in `FACTORY_OPENCODE_FOLDERS` (relative to the home), which the confinement allows after the three. The one-time login as the agent user is the operator's step, as `claude setup-token` is for Claude Code, and so is its repetition after the container is recreated, since no volume holds these folders (or the operator mounts the folder with a compose override file).
```

### F5 (required, new fact): decision 17

Before `(S0008)` at the end of decision 17, add

```text
The image's `opencode-ai` is only the default build: the operator chooses an instance's build per compose call with `FACTORY_OPENCODE` (its path in the container, which the operator mounts or installs, such as the company build at the human's work), `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS`, whose compose defaults equal the image's values.
```

### F6 (recommended): decision 20, the facts beyond the probe

Replace

```text
(`step_finish` with `part.cost` and `part.tokens`, `tool_use` with `part.state`, `text`, `error`), that it honours `OPENCODE_CONFIG`
```

with

```text
(`step_finish` with `part.cost` and `part.tokens`, `tool_use` with `part.state` and its `time`, `text`, and `error` with `error.data.statusCode` and `error.data.message`), that `--model` is the long form of the probe's `-m`, that a deny after `"*": "allow"` wins, that it honours `OPENCODE_CONFIG`
```

### F7 (required, new fact): decision 21 and its *Out of scope* bullet

Replace decision 21 with

```text
21. **The gateway's address is out of scope** (Out of scope), and with the human's fact of 2026-10-18 it concerns only the Claude Code runtime on an API key: the company build of opencode at the human's work knows its own endpoint and logs in through single sign-on, so the work run needs no base URL. A Claude Code instance on a key behind the gateway cannot reach it yet, because the agent run's environment is built from the allowed names alone. Recommended as a later story, when such an instance is wanted: an operator setting `FACTORY_API_BASE_URL`, handed to Claude Code as `ANTHROPIC_BASE_URL`, with its preflight detail. (Feature)
```

and in *Out of scope* replace

```text
- Reaching a provider through a gateway's own address (a base URL, `ANTHROPIC_BASE_URL` for Claude Code, `provider.anthropic.options.baseURL` for opencode): the agent run's environment holds only the allowed names, so neither runtime can be pointed at the gateway at the human's work yet. A later story (decision 21).
```

with

```text
- Reaching a provider through a gateway's own address (a base URL, `ANTHROPIC_BASE_URL` for Claude Code): the agent run's environment holds only the allowed names, so a Claude Code instance on an API key cannot be pointed at a gateway yet; the company build of opencode at the human's work knows its own endpoint and needs none. A later story (decision 21).
```

### F8 (required, new fact): the goal

In *Goal*, replace

```text
so that a project can run on another provider's models or on an API key alone, as at the human's work.
```

with

```text
so that a project can run on another provider's models, on an API key alone, or on an operator's own opencode build with its own login (single sign-on at the human's work).
```

### F9 (recommended): decision 14, the lease

In decision 14, replace

```text
The claim stays held while waiting: the lease's age passes `lease_duration`, which only another instance on the same repository could act on, and one repository has one instance;
```

with

```text
The claim stays held while waiting: v1.1 renews no lease, so a stage that waits may hold its claim for its time limit, the ceiling and its checks (about 180 minutes for the coder, against a lease of 60); the lease's age then passes `lease_duration`, which only another instance on the same repository could act on, and one repository has one instance;
```

### F10 (required, new fact): the Scope's settings, opencode runtime and image bullets

In *Scope*, replace

```text
`FACTORY_AGENT_RUNTIME`, `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION`, `FACTORY_OPENCODE_MODELS` (S0008)
```

with

```text
`FACTORY_AGENT_RUNTIME`, `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION`, `FACTORY_OPENCODE_MODELS`, `FACTORY_OPENCODE_FOLDERS` (S0008)
```

replace

```text
the budget stop and resume, the provider limit while the run streams (S0006).
```

with

```text
the budget stop and resume, the provider limit while the run streams (S0006); the folders of an operator's build (S0008).
```

and replace

```text
opencode installed at a pinned version, its version and models set, the runtime chosen per compose call (S0008).
```

with

```text
opencode installed at a pinned version as the default build, its version and models set, the runtime and the opencode build chosen per compose call (S0008).
```

### F11 (recommended): change 2 earlier, with the third login

Replace

```text
2. Recommended after S0004 is merged, not needed by a story: `CLAUDE.md`, *Architecture*:
```

with

```text
2. Before S0004 starts (its intake and its reviewer read R5's "one wrapper class" for the agent runtime): `CLAUDE.md`, *Architecture*:
```

and in it replace

```text
each under the login its files hold (a subscription token or an API key)."
```

with

```text
each under the login its files hold (a subscription token or an API key) or, for an operator's opencode build, the login it keeps in the agent's home."
```

### F12 (required, new fact): the human's change 8, the run at work

After change 7 (F2), add

```text
8. The run at the human's work, on the company build of opencode, after S0008 is merged (S0007's waits and S0005 and S0006's recognition are what it tests): the operator makes the company build reachable in the container (a compose override file that mounts it, or an image built on top), keeps the instance's key file empty, and starts with `FACTORY_AGENT_RUNTIME=opencode FACTORY_OPENCODE=<its path> FACTORY_OPENCODE_VERSION=<its version> FACTORY_OPENCODE_MODELS=<its alias=provider/model ids>`. A hand probe first, as in change 6.2, plus: the one-time login as the agent user (`docker exec -it -u agent <container> <its path> <its login command>`); which folders of `/home/agent` the login writes (each outside opencode's three goes into `FACTORY_OPENCODE_FOLDERS`); whether it needs proxy or CA variables, which the agent run does not pass yet (a later story); and what it prints on the gateway's 428 (an `error` event, a line of standard error, or nothing). Then watch the factory log's `provider limit:` lines.
```
