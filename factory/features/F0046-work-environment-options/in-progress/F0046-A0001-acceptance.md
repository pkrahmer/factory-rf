---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 462
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-26T16:37:50.882432Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-26T16:49:54.268423Z'
  stage: acceptance
  run: 5438b5c51c25433e884e7bc7428011ac
stories: [F0046-S0001, F0046-S0002, F0046-S0003]
outcome: null
---

# Acceptance of The factory can be configured for a corporate environment

## Recommendation

**Accepted with stories.** All four Scope items have a merged story, and `make check` was green as I found it. The feature's smoke test, run through the real entry points, is green. It reads the unit's two environment files in order, then `read_settings`, then `build_boundaries`, and runs one stage's sync, agent run and check on stand-in `podman` and `zfs`. Every container gets the operator's names and the CA bundle, and nothing else from the host. The opencode run gets the provider and `--model corp/big`, and a broken provider file stops the run before podman starts. Two findings are worth a story, and neither breaks a promise of the Goal:

- The preflight's opencode hint still advises the login in the agent's home that S0001 corrected in the guide. The guide quotes that hint, so it now contradicts itself (F0046-S0004).
- The decision log and the guide have four gaps the stories could not see from inside one story (F0046-S0005).

## 1 Scope

None of weight. Each Scope item has its story in `done/`, and the code holds what the Descriptions promise:

- `FACTORY_OPENCODE_PROVIDER_FILE` (S0001): `factory.domain.opencode_provider` (`read_provider`, `provider_configuration`), `OpencodeRuntime(provider_file=)`, which reads the file at every run in `_provider_keys`, and the wiring in `factory.entry.wiring._agent_runtime`.
- `FACTORY_CONTAINER_ENV` and `FACTORY_CA_BUNDLE` (S0002): `factory.domain.settings._container_env`, `factory.domain.containers.extra_environment` and `bundle_mounts`. Both runtimes, `ContainerEnvironment` and `ContainerMakeCommands` take `extra_environment=`/`ca_bundle=`. `build_boundaries` computes the extras once and carries them on `Boundaries.container_extra_environment`.
- `factory.local.env` (S0003): `vm/factory.service` has `EnvironmentFile=-/srv/factory/%i/factory.local.env` after `factory.env`, and `vm/setup.sh` ends with the `setup: local:` line.
- The guide's passages on opencode's login (S0001's docs criterion): *Running on opencode* and step 8 were corrected. One passage the item covers is not: *The probe of the agent run* quotes the code's opencode hint, `log in once as the factory user with the opencode build's own login`. That is a text in `factory.application.preflight._opencode_login_hint`, so no documenter could change it. I count it under 5, with a story (F0046-S0004). The human may count it as a gap in this Scope item instead.

No story went outside the Scope or into Out of scope. I found no company value: the tests and documents use `example.invalid` and made-up ids. The Claude Code runtime, the pipeline definition and the records contract are unchanged. The Claude Code runtime only gained the shared keywords, which S0002's Interface names. The Goal's "with none of them set the factory behaves exactly as before" holds in the code: the configuration is byte-identical without the file, the extras are `{}`, the bundle mounts are `[]`, and the unit's `-` prefix makes the second file optional.

## 2 Feature smoke test

The walk-through of an operator at a company. It writes the guide's example provider file (`corp`, `https://llm.example.invalid/v1`, `api_key_env: ANTHROPIC_API_KEY`, models `big` with prices and `small`), a CA bundle, a `factory.env` as `vm/setup.sh` writes it (Anthropic model map, `FACTORY_AGENT_RUNTIME=opencode`), and a `factory.local.env`. The local file holds the provider file, the model map `opus=corp/big,sonnet=corp/big,haiku=corp/small`, `HTTPS_PROXY`, `NO_PROXY`, `FACTORY_CONTAINER_ENV=HTTPS_PROXY, NO_PROXY, PATH` and `FACTORY_CA_BUNDLE`. The script then:

- reads the files in the order of `vm/factory.service`'s `EnvironmentFile=` lines, later wins, over a host environment with `PATH=/host/bin:...` and a stray `SECRET_ON_HOST`;
- calls `read_settings` and `build_boundaries`, with `FakeHostingService` and stand-in `podman` and `zfs` executables (the stand-in `podman` records its words and keeps a copy of the mounted opencode configuration);
- runs `stage_environment_of(boundaries).prepare`, one `opus` agent run and one `check` through `boundaries.project_commands`;
- breaks the provider file and runs again;
- lists `FACTORY_TOKEN_FILE`;
- drops the three settings.

The script was a temporary file and is gone with the stage.

```text
$ d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; uv run python <tmp>/smoke.py "$d" "$PWD"
unit reads: ['factory.env', 'factory.local.env']
models: {'opus': 'corp/big', 'sonnet': 'corp/big', 'haiku': 'corp/small'}
container_env: ('HTTPS_PROXY', 'NO_PROXY', 'PATH') ca_bundle: corp-ca.pem
agent run ended: died (the stand-in podman replies nothing)
sync: HTTPS_PROXY=http://proxy.example.invalid:3128 NO_PROXY=.example.invalid SSL_CERT_FILE-is-bundle=True bundle-ro=True host-secret=False token=False PATH-from-host=False
agent: HTTPS_PROXY=http://proxy.example.invalid:3128 NO_PROXY=.example.invalid SSL_CERT_FILE-is-bundle=True bundle-ro=True host-secret=False token=False PATH-from-host=False
check: HTTPS_PROXY=http://proxy.example.invalid:3128 NO_PROXY=.example.invalid SSL_CERT_FILE-is-bundle=True bundle-ro=True host-secret=False token=False PATH-from-host=False
--model: ['corp/big']
config keys: ['agent', 'autoupdate', 'provider', 'share', 'small_model', 'snapshot']
small_model: corp/small apiKey: {env:ANTHROPIC_API_KEY}
broken file: agent runtime failed: cannot use the opencode provider file <tmp>/srv/vm/corp-provider.json: base_url: Field required
podman calls after the broken file: 0
reserved: FACTORY_CONTAINER_ENV: holds FACTORY_TOKEN_FILE, which the factory sets itself
defaults: None () None
exit: 0
```

Green. What it shows:

- The local file wins: the model map is the company's.
- All three containers get the listed names and the bundle, mounted `:ro` and named by `SSL_CERT_FILE`. They get neither the host's `PATH`, although `PATH` is listed, nor the stray name, nor the hosting token.
- The opencode configuration holds the provider and `small_model` beside the existing keys, with the key as `{env:ANTHROPIC_API_KEY}`.
- A broken file ends the run before any container starts, and a reserved name is refused.
- Without the settings everything is off.

The `died` is the stand-in's empty reply, not the feature. The real opencode against a real proxy is not run here: feature decision 9 leaves that to the probe on the machine. `grep -c 'factory.local.env' vm/setup.sh` gives `1`, the closing line.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

From the archived journals, still true on this tree unless I say otherwise:

1. S0001 documenter (entry 32): the opencode probe hint quoted in the guide advises a login that cannot work on the machine. Story F0046-S0004.
2. S0003 documenter (entry 25): the S0002 decision entry's "Left to later stories of F0046" line is stale. So is S0001's. Story F0046-S0005.
3. S0002 reviewer notes (entries 33, 41), all still in the tree. No stage owned them, and they are tester work under the standing leave; I propose no story for them:
   - `_recording` and `_calls` in `tests/entry/test_wiring_container_extra.py:25,37` copy `_recording_stand_in` and `_calls` of `tests/entry/test_wiring_stage_environment.py:28,41`;
   - `CA_NAMES` in `tests/container_extra_support.py:26` repeats `factory.domain.containers.CA_BUNDLE_NAMES`;
   - `REPLY` is imported from test modules (`tests/container_extra_support.py:12`, `tests/entry/test_wiring_container_extra.py:12`).
4. S0001 reviewer note (entry 30): in `tests/domain/test_settings_opencode_provider.py`, the refused side of the setting is a separate test function, not a row of the accepted side's test. It is open, small, and has no story.
5. S0002's archived text disagrees with what was built (entries 39, 41, 43, 45):
   - its Interface still puts the extras into `run_environment`'s "runtime part", but the code puts them beneath its result;
   - the Interface lacks the constructor keywords of entry 9;
   - it names `tests/adapters/test_make_commands_extra.py`, which was never made;
   - its smoke test 1, as written, fails with a `ValidationError`.
   `done/` is the human's; whether to correct it is theirs.
6. A pipeline observation from S0002. The coder's two rewrites of the Description were dropped ("changes outside the write paths"), because the coder's write paths in `factory/pipeline.yml` do not hold `{work_item}`. Only the reviewer could correct the Description, and it did (entry 41). The Interface and the smoke test stayed stale, which is how item 5 came about. That file is the human's.
7. Error 139 (a segmentation fault) twice in S0002: once in `make test` (entry 21) and once in `make types` (entry 39). Neither run kept a test name, and neither crash came back in the next run. Not seen in my run.
8. The same test-setup gap struck twice. A wiring test of an opencode instance needs `opencode_models`, `settings.json` in the agent home and a `runs/` folder. S0001 (entry 10) and S0002 (entries 13, 18) each found these one at a time and asked the human. No shared helper sets up an opencode instance for the wiring tests.
9. My own observation: `InstanceSettings` checks the names of `container_env` only in `read_settings`, not in its model validator. Unlike `ca_bundle` and `opencode_provider_file`, a model built in code accepts `container_env=("HOME",)`. S0002's Interface asked only for the read. No caller builds the model from anything other than `read_settings` but the tests.
10. S0002 documenter (entry 43): it did not check how `vm/setup.sh` and the image build take a proxy. The guide says only "give them the proxy in their own environment". The script runs under `sudo`, whose default `env_reset` drops `HTTPS_PROXY`, so an operator may need `sudo -E` or the like. I did not verify this on the machine. It is an observation, not a story.

## 5 The documentation as a whole

Findings, read from `README.md` down through `docs/`:

1. **A contradiction.** In `docs/operator-guide.md`, *Running on opencode* (S0001) says that a login kept in the agent's home does not work on the machine. *The probe of the agent run* still quotes the hint `log in once as the factory user with the opencode build's own login`, and the completed detail `the runtime uses the login kept in its home`. The code prints both (`factory.application.preflight`). An operator whose probe fails is sent to a login that cannot work. Story F0046-S0004 changes the code text, and its docs criterion changes the quotes.
2. **Stale lines in `docs/decisions.md`.** Lines 1161 and 1173 say the other options are "Left to later stories of F0046"; they are merged.
3. **A decision entry short of the feature's decisions.** *A company's provider for opencode* was to be written from the feature's decisions 1 to 5 and 9 (S0001, criterion 12). The documenter could not read `feature.md` and said so. Decision 1 (off by default, byte-identical) and decision 9 (no test runs the real opencode; the probe shows it on the machine) are missing. The guide's *A company's provider* also does not tell the operator where to see that the provider works.
4. **What reaches the factory process itself.** *Behind a proxy* tells the operator to put `HTTPS_PROXY` and the like in `factory.local.env`. Neither it nor *The environment file* says that the unit sets those names for the whole service, so they are in the factory's own environment too, not only in the containers' that `FACTORY_CONTAINER_ENV` lists.

Items 2 to 4 are story F0046-S0005. Otherwise the three stories' passages agree. The configuration table, *Behind a proxy*, *A company's provider*, *The environment file*, the layout table and *The service* tell one story. The guide's provider example validates: it is the file of my smoke test. The project guide's `agents.md` and `stage-environment.md` match the code. `README.md` needs nothing from this feature.

## 6 Decisions taken for the human

To accept or revisit:

1. The feature's decisions 1 to 9 as `feature.md` lists them. All nine hold in the code: the three options are off by default; the provider file is validated, needs a `small_model`, has optional prices and is read at every run; the key goes through `{env:NAME}`; the allow-list stays closed; the CA bundle is read-only under three names; the second file is read after the first and is optional; no test runs opencode.
2. S0001, entry 4: a trailing `/` of `base_url` is kept, not stripped.
3. S0001, entry 11: the tests write the key names through constants, with no pragma and no baseline entry.
4. S0001, entry 18: **`main` holds a line filter in `.secrets.baseline`, so lines that name `api_key_env` are not scanned at all.** It is broad. A real key on such a line in any file, a journal included, would pass `make secrets`. Worth a second look.
5. S0001, coder default (entry 10): the provider file is read and validated at every run, not once at start, so a fixed file applies without a restart. The probe only runs once per image build, so a file changed later is first tried by a stage's run.
6. S0002, entry 4: the bundle's three names win over a listed name of the same name. The factory's own names (`PATH`, `HOME`, the constants of the sync and check containers) win over every extra. Review round 0 carried the same rule into the agent's container (entries 25, 27).
7. S0002, entry 9: the keywords `extra_environment=` and `ca_bundle=` go on all four classes. The coder's default: the extras travel on `Boundaries.container_extra_environment`, so the application layer never reads `os.environ`.
8. S0002, entry 14: **`pyproject.toml` exempts `src/factory/adapters/make_commands.py` from `PLR0913`** (the human's change), so `ContainerMakeCommands` takes six arguments.
9. S0002, entry 19: a wider leave for the setup of one test's opencode row.
10. S0003, entry 6: the tests run only the closing text of `vm/setup.sh` (`sh` in `tmp_path`, which stands in for the instance folder). That a whole run leaves `factory.local.env` alone rests on the static rows of criterion 2, not on a run.
11. Open, not decided by anyone: does the factory's own process need the company's CA on the host? Its hosting client and git see the proxy names of `factory.local.env` (5, item 4). Out of scope names only "a proxy or an allow-list of the agent's network". F0046-S0005 states the fact and leaves this question to you.

Earlier tests changed (from the reviewers' entries), each under a named leave:

- `tests/test_vm_service.py`: the human's leave, S0003 entry 9 (the `service` row skips `EnvironmentFile`).
- `tests/test_vm_setup_text.py`, `tests/test_vm_setup_writes.py`, `tests/conftest.py`: the standing leave to move a shared helper, S0003 entries 19 and 23 (the `code` fixture).
- S0001 and S0002 changed no earlier test (their reviewers found every test file with status `A`).

No earlier test was changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` today (no image scan, no SBOM). `make duplicates` is a record, and it read `0 new, 43 known, 0 gone` after every coder run of the three stories. `make mutants` is check 3.

In my `make check` (`test: green (157.1 s)`, 99.56 % branch coverage), `.reports/junit.xml` holds 7339 tests. The slowest take about 10 s each, all `ROOMY_LIMIT` tests from earlier features:

- `test_claude_runtime_resume::test_call_killed_by_the_time_limit_has_no_model_duration[nothing printed]`: 10.2 s;
- `test_podman_timeout_status::...[255-at-the-limit]` and `[137-at-the-limit]`;
- `test_process_session::test_time_limit_ends_every_process_of_the_group[run_streaming-own-session]`;
- `test_process::test_grandchild_is_killed_with_the_child_at_the_time_limit`;
- `test_opencode_resume_session::...[timed-out-resumed-without-events]`.

This feature's test modules are not among them.

Disk: at the previous record (`disk start`), 40.4 GB were free on the filesystem, and `/srv/factory/vm` used 1.2 GB. Now 37.9 GB are free, and `/srv/factory/vm` still uses 1.2 GB (`state` and `/tmp` 0.0 GB both times). So 2.5 GB went to something outside the instance's folders. The feature's changes do not explain it: three small code changes, no new dependency, no change to `vm/Dockerfile`. The likely cause is the stage image rebuilt after the merges (the night log names "vm rebuilt" after S0002), with old images or the build cache kept, but I cannot see it from here. `podman system df` on the machine would tell.

## 8 Cost

The stories cost 47 runs, 119.8 min, 418 turns and $16.45:

| Story | Runs | Cost |
| --- | --- | --- |
| S0001 | 15 | $5.07 |
| S0002 | 20 | $8.85 |
| S0003 | 12 | $2.52 |

S0002 stands out, with 54 % of the cost. Its tests stage ran six times ($2.97) and its review three times ($2.26). The journal says why:

- the Interface named no constructor keywords (entry 8);
- the Interface put the agent's extras where a listed `PATH` would override the request's own, against the human's rule of entry 4. Review round 0 found this (entry 25);
- the reviewers added two criteria, 8 and 9, for untested sides of the name rule;
- an opencode wiring row needed setup step by step (entries 13, 18, 21).

Human interventions: 9 questions answered, all of the cause `question`, with 1.6 h waited. S0001 had 3 (entries 4, 11, 18), S0002 had 4 (entries 4, 9, 14, 19), and S0003 had 2 (entries 6, 9). S0002 needed the human most. Its questions were:

- two intake gaps;
- an Interface without the keyword names;
- a wrong test together with a lint rule only the human could relax;
- the setup of one test row.

Three of the nine questions across the feature were test fixes that a shared opencode wiring helper would have avoided (4, item 8). Two came from text the stage that saw the fault was not allowed to write:

- S0001's journal line, which `make secrets` flagged;
- S0002's Description (4, item 6).

## Proposed stories

- `F0046-S0004-the-opencode-probe-no-longer-advises-a-login-kept-in-the-agent-s-home.md`: the code's opencode probe hint and detail contradict S0001's corrected guide and send the operator to a login that cannot work on the machine. It needs the human's leave in `feature.md` to change the shared helper `opencode_sso_hint`.
- `F0046-S0005-the-feature-s-documents-agree-with-what-was-built-and-with-each-other.md`: a documents-only repair. It removes the stale "Left to later stories" lines, adds the missing feature decisions 1 and 9 to the decision entry, points the operator to `agent-run-probe` for the provider, and states that `factory.local.env` reaches the factory's own process.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 2 stories proposed

   1. Scope: none of weight. All four Scope items are merged and no story went outside the scope. The guide's opencode probe hint is the one passage of the scope's login item that is still wrong; it is code text, so it goes to F0046-S0004.
   2. Feature smoke test: green, `exit: 0`. One script runs the unit's two env files in order, then `read_settings` and `build_boundaries`, then the sync, an `opus` agent run and a check on stand-in podman and zfs.
      - All three containers get the listed proxy names and the read-only bundle. They get neither the host's `PATH` (although listed), nor a stray host name, nor the hosting token.
      - The opencode configuration gets `provider` and `small_model`, and the run gets `--model corp/big`.
      - A broken provider file stops the run with no podman call, and a reserved name is refused.
      - Without the settings, all three options are off.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: ten items. Two lead to the stories. Still open with no story:
      - three S0002 reviewer notes on copied test helpers;
      - S0002's archived Interface and smoke test, which no longer match what was built;
      - the coder's write paths, which drop R5's Description rewrite;
      - two one-off Error 139 crashes;
      - an opencode wiring-test setup gap that cost three human answers;
      - `InstanceSettings` checks `container_env` names only in `read_settings`, not in its model validator.
   5. Docs: one contradiction. *Running on opencode* says a login in the agent's home cannot work, while *The probe of the agent run* quotes the code's hint advising exactly that (S0004). Three gaps, all F0046-S0005:
      - two stale "Left to later stories of F0046" lines in `docs/decisions.md`;
      - the feature's decisions 1 and 9 are missing from the S0001 decision entry;
      - the guide never says that `factory.local.env` reaches the factory process itself.
   6. Decisions: the feature's nine decisions plus nine answers and defaults from the journals are listed for the human. Two are flagged:
      - the `.secrets.baseline` line filter excludes every line containing `api_key_env` from scanning (I confirmed it in the file);
      - the PLR0913 exemption for `make_commands.py`.
      One question is open: does the host process need the company's CA? Every earlier test was changed under a named leave.
   7. Slow checks: nothing beyond `make check`, which was `test: green (157.1 s)` at 99.56 % coverage. The slowest tests are the 10 s `ROOMY_LIMIT` tests of earlier features. Disk: free space fell from 40.4 GB to 37.9 GB, while `/srv/factory/vm` stayed at 1.2 GB used. The feature's changes do not explain the 2.5 GB; image rebuilds are the likely cause, and `podman system df` on the machine would tell.
   8. Cost: $16.45 over 47 runs. S0002 alone took $8.85 and 20 runs: its Interface named no constructor keywords and placed the agent's extras where a listed `PATH` overrides the request's. Its reviewers also added two criteria, and one opencode test row needed setup step by step. The human answered 9 questions (3, 4 and 2 per story) and the stories waited 1.6 h; S0002 needed the human most.

   Both proposed stories pass `factory-check-story`. `make check` was green as I found it, and `make secrets` is green over the report and the stories. I could not remove the temporary folder `/tmp/tmp.jj2uKqzc4n` (the call was denied); it goes with the stage.
