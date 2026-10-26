---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 465
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-26T17:59:35.368810Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-26T18:12:29.028860Z'
  stage: acceptance
  run: 227e11558e604122b3366061f953dd98
stories: [F0046-S0001, F0046-S0002, F0046-S0003, F0046-S0004, F0046-S0005]
outcome: null
---

# Acceptance of The factory can be configured for a corporate environment

## Recommendation

**Accepted with stories.** All four Scope items and both of A0001's repair stories (S0004, S0005) are merged, and `make check` was green as I found it. The feature's smoke test, run through the real entry points, is green. It goes from the unit's two environment files through `read_settings` and `build_boundaries` to the preflight's `agent-run-probe` and a check, on stand-in `podman` and `zfs`, with the real login shell. A0001's contradiction is gone: the probe no longer advises a login in the agent's home. What is left is a set of documentation gaps that no story owned, none of them a broken promise of the Goal. They are proposed as one documents-only story (F0046-S0006):

- the project guide's constructor signatures and wiring table;
- an old decision entry that F0046's login rule supersedes, not marked as such;
- one inexact sentence of S0004's guide text.

## 1 Scope

None. Each Scope item has its story in `done/`, and so does each repair that A0001 proposed:

- `FACTORY_OPENCODE_PROVIDER_FILE` (S0001): `factory.domain.opencode_provider`, and `OpencodeRuntime(provider_file=)`, which reads the file at every run (`_provider_keys`, `src/factory/adapters/opencode_runtime.py:298`).
- `FACTORY_CONTAINER_ENV` and `FACTORY_CA_BUNDLE` (S0002): `factory.domain.containers.extra_environment` and `bundle_mounts`. `build_boundaries` computes the extras once (`src/factory/entry/wiring.py:254`) and hands them to both runtimes, `ContainerMakeCommands` and `Boundaries.container_extra_environment`.
- `factory.local.env` (S0003): `vm/factory.service:13` (`EnvironmentFile=-...`) and the `setup: local:` line of `vm/setup.sh:376`.
- The guide's passages on opencode's login: done now. S0004 changed the code's texts in `src/factory/application/preflight.py:259` (`_opencode_login_hint`) and `:266` (`_login_detail`), and the guide quotes them (`docs/operator-guide.md:758-760`). `grep -c "opencode build's own login"` gives 0 in both files.
- S0005: `docs/decisions.md` has no "Left to later stories of F0046" line, and it states feature decisions 1 and 9. The guide names `agent-run-probe` under *A company's provider*, and *The environment file* says that `factory.local.env` reaches the factory process itself.

No story went outside the Scope or into Out of scope. S0004 changed only opencode texts: the Claude Code texts are unchanged, and the Claude Code runtime, the pipeline definition and the records contract are untouched. S0005 changed two documents only. No company value is in either diff.

## 2 Feature smoke test

The walk-through of an operator at a company, as one script against the real entry points. It writes:

- a `factory.env` as `vm/setup.sh` writes it, with the opencode runtime, the Anthropic model map and an API login file;
- a `factory.local.env` with the guide's example provider file (`corp`, `https://llm.example.invalid/v1`, `api_key_env: ANTHROPIC_API_KEY`), the map `opus=corp/big,sonnet=corp/big,haiku=corp/small`, `HTTPS_PROXY`, `NO_PROXY`, `FACTORY_CONTAINER_ENV=HTTPS_PROXY, NO_PROXY, PATH` and `FACTORY_CA_BUNDLE`;
- a real clone of a bare remote, an agent home with `coder`, and stand-in `podman` and `zfs`. The stand-in `podman` records its words. For an agent call it runs the command after the image on the host with only the `--env` pairs, so the factory's real login shell runs. A stand-in `opencode` prints a completed `question` result.

It reads the files in the order of `vm/factory.service`'s `EnvironmentFile=` lines (a later one wins), over a host environment with `PATH=/host/bin:...` and a stray `SECRET_ON_HOST`. Then it runs `read_settings`, `build_boundaries` (with `FakeHostingService`), the preflight's `agent_run_probe_item` (a prepare, so the sync container, then the agent run) and one `check` through `boundaries.project_commands`. Then it repeats with:

- the provider's key coming through the operator's list (`CORP_KEY`, the login file named but not placed), first completed, then died (the S0004 texts);
- a broken provider file;
- a reserved name;
- no `factory.local.env`;
- no login file set at all.

The script was a temporary file outside the checkout.

```text
$ d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; uv run python <tmp>/smoke.py "$d" "$PWD"
unit reads: ['factory.env', 'factory.local.env']
models: {'opus': 'corp/big', 'sonnet': 'corp/big', 'haiku': 'corp/small'}
container_env: ('HTTPS_PROXY', 'NO_PROXY', 'PATH') ca_bundle: corp-ca.pem provider: corp-provider.json
probe: True | the agent runs log in with the API key from <tmp>/secrets/anthropic-api-key
sync : HTTPS_PROXY=http://proxy.example.invalid:3128 NO_PROXY=.example.invalid CA-names=['NODE_EXTRA_CA_CERTS', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE'] bundle-ro=True PATH-from-host=False host-secret=False token=False
agent: HTTPS_PROXY=http://proxy.example.invalid:3128 NO_PROXY=.example.invalid CA-names=['NODE_EXTRA_CA_CERTS', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE'] bundle-ro=True PATH-from-host=False host-secret=False token=False
--model: corp/big
config keys: ['agent', 'autoupdate', 'provider', 'share', 'small_model', 'snapshot'] | small_model: corp/small | apiKey: {env:ANTHROPIC_API_KEY} | baseURL: https://llm.example.invalid/v1
check: HTTPS_PROXY=http://proxy.example.invalid:3128 NO_PROXY=.example.invalid CA-names=['NODE_EXTRA_CA_CERTS', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE'] bundle-ro=True PATH-from-host=False host-secret=False token=False
no key in the login file, completed: True | the agent runs get no login from a file
  agent gets CORP_KEY: True
no key in the login file, died: False | the probe run ended died; run <tmp>/podman/opencode run by hand as the factory user to see why; the agent runs get no API key: put a key in the file FACTORY_API_LOGIN_FILE names
broken file: False | agent runtime failed: cannot use the opencode provider file <tmp>/srv/vm/corp-provider.json: base_url: Field required
  agent containers started: 0
reserved: FACTORY_CONTAINER_ENV: holds FACTORY_TOKEN_FILE, which the factory sets itself
defaults: None () None {}
default probe: True | config keys: ['agent', 'autoupdate', 'share', 'snapshot'] | HTTPS_PROXY in agent: False | --volume of a bundle: False
exit: 0
no login file set at all: True | ''
```

Green. What it shows:

- The local file wins over `factory.env`.
- The probe completes through the company's provider: `--model corp/big`, and a configuration with `provider` and `small_model` beside the existing keys, the key as `{env:ANTHROPIC_API_KEY}`.
- The sync, agent and check containers all get the listed names and the bundle, mounted `:ro` under its three names. None of them gets the host's `PATH` (although listed), the stray name or the hosting token.
- A key passed through the operator's list reaches the agent. The probe's opencode texts are S0004's, with no advice to log in in the agent's home.
- A broken provider file fails the probe before any agent container starts, and a reserved name is refused.
- Without `factory.local.env` all three options are off, and the configuration has its four earlier keys.

The last line is a finding for 5. With no login file set at all, the probe passes with an empty detail. The guide says that case gives `the agent runs get no login from a file`. That text comes when a login file is named but holds no login. On the machine `factory.env` always names both files, so an operator meets the named-but-missing case.

The real opencode against a real proxy is not run here: feature decision 9 leaves that to the probe on the machine.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

From the journals of S0004 and S0005, and A0001's list checked again on this tree:

1. S0004's coder (entries 14, 18, 22) noticed the stale guide quotes. Criterion 5 took them; they are done.
2. S0004's round-0 review (entry 16) had three test findings: a copied `_probe_result`, a duplicate row, and a line added to an earlier test beyond feature decision 10. All three were fixed in round 1 (entry 20). `probe_result` is now shared in `tests/probe_support.py`.
3. S0005's smoke tester (entry 13): *Behind a proxy* lacks a comma before `and list their names` (`docs/operator-guide.md:210`). Still true. It goes into F0046-S0006.
4. S0005's documenter left the CA-on-host question to the human, as the Description asked. It is still open (6, item 13).
5. Still open from A0001, with no story, each checked on this tree:
   - the copied test helpers of S0002: `_recording` and `_calls` in `tests/entry/test_wiring_container_extra.py:25,37` copy `tests/entry/test_wiring_stage_environment.py:28,41`; `CA_NAMES` in `tests/container_extra_support.py:26` repeats `CA_BUNDLE_NAMES`; and `REPLY` is imported from test modules;
   - `InstanceSettings` checks the names of `container_env` only in `read_settings`, not in its own validators (`src/factory/domain/settings.py:127-142`);
   - S0002's archived Interface and smoke test do not match what was built;
   - the coder's write paths drop a Description rewrite;
   - no shared helper sets up an opencode instance for the wiring tests;
   - `sudo`'s `env_reset` may drop the proxy for `vm/setup.sh` (not verified on the machine).
   None is new, and none is worth a story of this feature beyond what A0001 judged.
6. My own, from the smoke test: when the provider's key comes through `FACTORY_CONTAINER_ENV` and the probe dies, the hint still points to `FACTORY_API_LOGIN_FILE`. That is the guide's recommended path (*A company's provider*: "the name to give is `ANTHROPIC_API_KEY`"), so it is consistent, not a fault. I propose nothing.
7. My own: the decision entry *The agent runtime is chosen per instance* (`docs/decisions.md:807-816`) still gives single sign-on and `FACTORY_OPENCODE_FOLDERS`, "so a build can keep and refresh its login there", as reasons. `src/factory` no longer reads that setting, and F0046's entry says only the API login works. See 5.

## 5 The documentation as a whole

`README.md` needs nothing from this feature. The operator guide's passages of the three options and of S0004 and S0005 agree with each other and with the code. The provider example validates (it is my smoke test's file). Findings, all in F0046-S0006:

1. **The project guide's constructors.** `docs/project-guide/agents.md:22` and `:98` give `ClaudeCodeRuntime(...)` and `OpencodeRuntime(...)` without `extra_environment={}` and `ca_bundle=None`. Line 30 of the same file describes them, and the code has them (`src/factory/adapters/claude_runtime.py:312-325`, `src/factory/adapters/opencode_runtime.py:525-540`). An agent that copies the signature would miss the extras. A0001 said these files matched the code; the signatures do not.
2. **The project guide's wiring table.** `docs/project-guide/stage-environment.md:327` builds `ContainerMakeCommands(snapshots, containers, git, checkout=settings.checkout)` without the two keywords. No passage names `Boundaries.container_extra_environment`, through which `stage_environment_of` gives the sync its extras.
3. **An old decision against the feature's rule.** *The agent runtime is chosen per instance* (F0020) still says the preflight asks for no API key because a build may log in through single sign-on. It also still says that `FACTORY_OPENCODE_FOLDERS` lets a build keep its login in the home. *A company's provider for opencode* says the opposite ("Why only the API login works"). The log marks other superseded entries with a `Superseded in part by` bullet; this one has none.
4. **One inexact sentence of S0004.** `docs/operator-guide.md:760` gives the two `none` texts "when no login file is set". The smoke test shows that with no login file set the detail is empty. The `none` texts come when a named file is missing or blank.
5. The missing comma of 4, item 3.

None of these misleads an operator about what the factory does at a company. Items 1 to 3 mislead agents and the reader of the log, and item 4 is one sentence. So they are a story, not a refusal.

## 6 Decisions taken for the human

To accept or revisit:

1. The feature's decisions 1 to 10 in `feature.md`. All hold in the code; decision 10 is S0004's leave.
2. A0001's list, items 2 to 10 of its section 6 (S0001 to S0003's answers and defaults). Unchanged. Two of them are worth a second look:
   - the `.secrets.baseline` line filter that leaves every line naming `api_key_env` unscanned;
   - the `PLR0913` exemption for `src/factory/adapters/make_commands.py`.
3. S0004, entry 8 (the human): `tests/entry/test_wiring_without_agent_user.py`, row `opencode-no-login`, now pins `put a key in the file FACTORY_API_LOGIN_FILE names` in place of `log in once as the factory user`. This was option (b), not the coder's (a).
4. S0004, coder default (entry 7): one runtime branch inside `_login_detail`, not a second helper.
5. S0004, coder default (entry 14): the two `_login_detail` texts share a prefix but stay as two literals.
6. S0004, tester (entry 20): `probe_result(reason, login)` made public in `tests/probe_support.py`, under the standing leave. `opencode_sso_hint()` lost its argument, under decision 10.
7. S0004, Description: Claude Code's third login (the login in the agent's home) stays as it is. Whether it still works on the machine is left outside F0046. It is the same question as for opencode, and it is still open.
8. S0005: the CA-on-host question is still open. Does the factory's own hosting client and git need the company's CA on the host, now that `factory.local.env` gives them the proxy names?
9. Open, from my smoke test: with no login file set at all, a passing probe logs an empty detail. F0046-S0006 documents it. Whether it should say more is yours.

Earlier tests changed, each with its leave:

- `tests/probe_support.py`: feature decision 10 (the hint), and the standing leave (`probe_result` moved in), S0004 entries 5 and 20.
- `tests/application/test_agent_run_probe_opencode.py`: feature decision 10. The `own login` line that went beyond it in round 0 was removed in round 1 (entries 16, 20).
- `tests/application/test_agent_run_probe_factory_user.py`: feature decision 10.
- `tests/entry/test_wiring_without_agent_user.py`: the human's answer, S0004 entry 8.
- `tests/application/test_agent_run_probe_api_login.py`: the standing leave (helper moved out); otherwise only added tests.
- S0005 changed no test (`git diff --name-status` of its merge: `docs/decisions.md`, `docs/operator-guide.md`).
- S0001 to S0003: as A0001 found, each under a named leave.

No earlier test was changed without a leave.

## 7 The slow checks

The project offers nothing beyond `make check` today (no image scan, no SBOM). `make duplicates` read `0 new, 43 known, 0 gone` after every coder run of S0004 and S0005. `make mutants` is check 3.

My `make check` was `check: green` with `test: green (157.7 s)` and 99.56 % branch coverage. `.reports/junit.xml` holds 7345 tests. The slowest take about 10 s each, all `ROOMY_LIMIT` tests of earlier features:

- `tests.adapters.test_podman_timeout_status::...[255-at-the-limit]` and `[137-at-the-limit]`: 10.0 s each;
- `tests.adapters.test_process::test_child_is_killed_at_the_time_limit`;
- `tests.adapters.test_process_session::test_time_limit_ends_every_process_of_the_group[run_streaming-own-session]` and `[run_process-own-session]`;
- `tests.adapters.test_claude_runtime_resume::test_call_killed_by_the_time_limit_has_no_model_duration[nothing printed]`.

None of this feature's test modules is among them.

Disk: at the previous record (`disk start`), 35.6 GB were free and `/srv/factory/vm` used 1.2 GB. Now 52.0 GB are free and `/srv/factory/vm` still uses 1.2 GB; `state` and `/tmp` are 0.0 GB both times. Free space grew by 16.4 GB, and nothing grew, so there is nothing to explain. Something outside the instance's folders was freed between the records, likely old images or the build cache. I cannot see which from here.

## 8 Cost

The stories cost 66 runs, 149.5 min, 522 turns and $19.71:

| Story | Runs | Cost |
| --- | --- | --- |
| S0001 | 15 | $5.07 |
| S0002 | 20 | $8.85 |
| S0003 | 12 | $2.52 |
| S0004 | 13 (25.2 min) | $2.52 |
| S0005 | 6 (4.4 min) | $0.74 |

The first three are A0001's figures; the five add up to the prompt's 66 runs and $19.71. S0002 still stands out, with 45 % of the cost; A0001 gave why. Of the two new stories, S0004 stands out for its size: 13 runs for two strings in one module. The journal shows why:

- The leave that A0001 proposed and the human gave (decision 10) named the helper and two modules. It missed a fourth module that pinned the old text, `tests/entry/test_wiring_without_agent_user.py`. The coder found it red and asked (entry 7), which cost a question, a doing round and a tests round.
- The round-0 review found three test findings (a copied helper, a duplicate row, and a line beyond the leave), which cost a second tests round and a doing round.

The lesson for this proposal: before naming a test leave, grep `tests/` for the text that will change. F0046-S0006 changes no test.

Human interventions: 10 questions answered, all of the cause `question`, with 1.7 h waited. S0001 had 3, S0002 had 4, S0003 had 2, S0004 had 1 (entry 8) and S0005 had none. S0002 needed the human most, with four questions:

- two intake gaps;
- an Interface without the keyword names;
- a wrong test together with a lint rule;
- the setup of one opencode test row (A0001, section 8).

## Proposed stories

- `F0046-S0006-the-project-guide-and-the-decision-log-agree-with-the-feature-s-constructors-and-its-login-rule.md`: one documents-only repair of what no story owned. It adds the `extra_environment` and `ca_bundle` keywords to the project guide's constructors and wiring table, and marks the F0020 decision entry as superseded in part by F0046's login rule. It also corrects S0004's "when no login file is set" sentence and adds the comma that S0005's smoke tester noted. `factory-check-story` reads it `ok`.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed

   1. Scope: none. All four Scope items are merged, and so are A0001's two repairs (S0004, S0005). No story went outside the scope. The probe's opencode hint no longer advises a login kept in the agent's home.
   2. Feature smoke test: green, `exit: 0`. One script runs the unit's two env files, then `read_settings`, `build_boundaries`, the preflight's `agent_run_probe_item` and a check, on stand-in podman and zfs with the real login shell.
      - The probe completes through `corp/big` with `provider` and `small_model` in the configuration.
      - The sync, agent and check containers get the listed names and the read-only bundle. None gets the host's `PATH`, the stray name or the token.
      - The S0004 texts show when the key comes through the operator's list.
      - A broken provider file starts no agent container, and a reserved name is refused.
      - Without `factory.local.env`, every option is off.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: S0004's review findings were fixed in round 1. S0005's smoke tester noted a missing comma, which goes into S0006. A0001's open items (copied S0002 test helpers, `container_env` checked only in `read_settings`, and others) still hold and get no new story. My own item: the F0020 decision entry still gives the login in the home and `FACTORY_OPENCODE_FOLDERS` as reasons.
   5. Docs: four gaps no story owned, none a broken promise, all in F0046-S0006:
      - the project guide's `ClaudeCodeRuntime`/`OpencodeRuntime` signatures lack `extra_environment` and `ca_bundle`;
      - its wiring table builds `ContainerMakeCommands` without them;
      - *The agent runtime is chosen per instance* is not marked superseded by F0046's login rule;
      - S0004's "when no login file is set" is inexact: with no file set, the detail is empty.
   6. Decisions: the feature's ten decisions, A0001's list, and S0004's answer (b) plus three defaults are listed. Still open: the CA on the host, Claude Code's login in the home, and the empty probe detail. Every earlier test was changed under a named leave.
   7. Slow checks: nothing beyond `make check`, which was green, `test: green (157.7 s)`, 99.56 % coverage, 7345 tests. The slowest tests are the 10 s `ROOMY_LIMIT` tests of earlier features. Disk: free space grew from 35.6 to 52.0 GB, and `/srv/factory/vm` stayed at 1.2 GB used, so there is no growth to explain.
   8. Cost: $19.71 over 66 runs. S0002 is still the largest ($8.85). S0004 took 13 runs ($2.52) for two strings: the leave A0001 proposed missed `tests/entry/test_wiring_without_agent_user.py`, and round-0 review found three test findings. The human answered 10 questions and the stories waited 1.7 h; S0002 needed the human most (4 questions).

   The proposed story passes `factory-check-story`. `make secrets` is green. I ran `make check` twice: the second run only to read its summary lines. I could not remove the temporary script folder `/tmp/tmp.Rr5DDuuuqp` because the call was denied; it goes with the stage.
