# Handling of audit F0010-1

How each finding of `audits/F0010-1.md` was handled in `planning/overnight/stories/F0010-machine/` (FEATURE.md and drafts/), and how the human's answers of 2026-10-14 were applied. 50 findings: 48 fixed (33 as a gap recorded for v2 and 44 done by the human, as the human answered), 1 fixed in part with the rest deferred (35, the kill under `sudo`), 1 deferred (45, the split of the token story). Nothing is deferred as "needs interfaces.md"; the sheet amendments that the changes imply are listed at the end.

## New ids

The audit's findings cite the drafts of 2026-10-13. Five stories were added (S0002 and S0003 by splitting old S0001, S0012 by splitting old S0009, and S0013 and S0014 as new stories), so the old ids moved. "Old" always means the old draft, "new" the story as it stands.

| Old | New | What happened |
|---|---|---|
| S0001 | S0001, S0002, S0003 | split: settings and loop (S0001), the boundaries from the settings (S0002), the process that runs them and `factory-watch` (S0003); old c17 and c18 (`main`) are now S0003 c12 to c16 |
| S0002 | S0004 | the pinned image |
| S0003 | S0005 | the health check and the entrypoint |
| S0004 | S0006 | the preflight's items |
| S0005 | S0007 | the probe and the stamp |
| S0006 | S0008 | agent files with no dead keys |
| S0007 | S0009 | the shipped agents and settings |
| S0008 | S0010 | no token in an agent run |
| S0009 | S0011, S0012 | split: the factory's side (runtime, request, environment) and the image's side (sudoers, umask, `agent-user`) |
| new | S0013 | the preflight probes one agent run (questionnaire 1, Q22) |
| new | S0014 | v1's role and stage texts in the shipped agents (questionnaire 1, Q29) |

`FEATURE.md`: the Stories list has 14 lines; the decisions are renumbered 1 to 34 (new 7, 8, 18 to 20, 22 to 34; the human's of 2026-10-14 are 7, 8, 24, 25 and 26).

## The findings

| Finding | Severity | Handling |
|---|---|---|
| 1 | blocker | fixed, S0007 (old S0005) and decision 13. Rules: the preflight runs after the tick's fetch, load and restore and before the evaluation; `Tick(boundaries, instance, handlers, status=None, preflight=None)`; `Preflight.run()` returns the reason of the stop it raised, `None` when it passed (old: `bool`), and the tick returns `TickOutcome(stopped=<reason>)`. The probe keeps the constant `PROBE_TIME_LIMIT`, with the reason in the Assignment and decision 13. Criteria changed: old c1 "`Preflight.run()` returns `True`" → c1 "returns `None`"; old c2 "returns `False`" → c2 "returns `"main_branch_failing"`"; old c3 "returns `True`" → c3 "returns `None`"; old c4, c5 "returns `False`" → c4, c5 "returns `"preflight_failed"`"; old c6 and c7 "after its fetch and its reset... before it loads the pipeline definition" → c7 and c8 "the tick fetches before the preflight", c8 now `TickOutcome(stopped="main_branch_failing")`; old c8 "no event is dispatched" → c9 "`event is None`" |
| 2 | blocker | fixed, S0008 (old S0006). The loader raises `agent_definition_invalid` at `PIPELINE_REF` and clears it after a good load; other refs touch no stop; `Tick._load` turns the error into `stopped`; `run_watch` prints `factory-watch: <message>` and returns 1. Old c6 (`PipelineLoader.load` raises) → c8; old c7 "a tick ... leaves one stop" → c9 (the loader leaves the stop), c12 (the tick returns `stopped="agent_definition_invalid"`); old c9 "clears the stop" → c10; new c11 (other ref touches no stop) and c15 (`run_watch`) |
| 3 | blocker | fixed, S0008. The Assignment names `tests/adapters/test_agent_files.py::test_a_key_the_reader_does_not_interpret_is_left_aside` and its replacement (c4); the docs criterion c17 also rewrites the decision entry "Agent files: keys beyond the four are not interpreted until F0010" and the operator guide's "ignored for now". The human's word is asked in decision 28 (the audit said "recorded as the human's word"; no answer of the human covers it, so it is flagged, not claimed) |
| 4 | blocker | fixed, S0010 (old S0008). `TaskComposer` stays as built (F0005 decision 23); the allow list moved to `production_environment()` (F0006-S0007). Old c2 "keeps `PATH`, `LANG`, `LC_ALL`, `TERM`, `TZ`" → c1 "also `HOME`" (six names); old c3 "drops ... `HOME`" → c2 (list without `HOME`); old c4 "a request composed by `factory.application.task` ... has none of the other four names" → c3 (`production_environment()` with the four names set through `monkeypatch`) and c5 (a whole tick); new c4 (locale names kept). Old decision 18 and the Rules rewritten |
| 5 | blocker | fixed, S0010 c7 and S0011 c4 to c6. Old c6 (S0008) "exactly `request.environment`" → c7 "the entries of `request.environment` and of `SWITCHES` and nothing of the process's environment (apart from the stand-in's `LC_CTYPE`)"; old S0009 c3 "exactly `request.environment` as its environment" → S0011 c4; old S0009 c4 → S0011 c5 "one `NAME=value` for each entry of `request.environment` and of `SWITCHES`"; old S0009 c5 → S0011 c6 "the three switches included" |
| 6 | blocker | fixed, S0002 c8 and c9, S0010 c14 and c15. No `git config --system`; `git_environment(helper)` gives the five `GIT_CONFIG_*` entries and `git_options(settings)` hands them to `GitCli`. Old S0008 c15 "sets it as the system `credential.helper`" → S0010 c15 "no `credential.helper` in any git configuration"; new S0010 c14 runs `git credential fill` with the environment `GitCli` builds |
| 7 | blocker | fixed. S0005 (old S0003): the three `git config --global` lines and old c16 are gone; new c19 "the entrypoint sets no git configuration". S0012 (old S0009): the `core.sharedRepository` line is gone; old c14 "sets the global git configuration `core.sharedRepository` to `group`" → S0012 c6 (`umask 002` only) and S0002 c8 (`core.sharedRepository=group` in `git_environment`) |
| 8 | blocker | fixed, S0001. Field `git_identity`, `GIT_USER_NAME` and `GIT_USER_EMAIL`, each half on its own. Old rule "reads exactly two variables" → "requires exactly these two ... and reads two optional ones". New c7, c8; old c1 now also asserts the default identity |
| 9 | blocker | fixed, S0002 and S0003. `build_boundaries(settings, token, *, hosting=None)`, `repository_name`, `git_options`, `read_hosting_token`; `run_instance` keeps one `Tick`; `hosting` injected for tests. New S0002 c4, c5, c11 to c18; S0003 c5 (one `Tick`, shared status) and c6 |
| 10 | blocker | fixed, S0003 c19 and c20. F0006-S0006's test of its criterion 20 is named and replaced; flagged for the human in decision 28 |
| 11 | blocker | fixed, S0001 c6: old "no occurrence of the text `REPOS`" → "no match of the regular expression `\bREPOS\b`" |
| 12 | blocker | fixed, S0001 c12 (new): `InstanceSettings` built directly refuses an unknown key and an assignment, `instance="Factory-1"` refused and `"factory-1"` accepted. S0011 c3 (new): `agent_user="Agent"` refused built directly. The other new fields (`agent_home`, `claude_executable`, `token_file`, `image`, `pinned_agent_version`) have no limit of their own |
| 13 | blocker | fixed, S0007 c19 and c20 (old c16, c17 changed): `PreflightStamp` frozen and closed, `main_probed` and `main_failed` refuse `"a" * 39`, `"A" * 40`, `"g" * 40`, accept `"a" * 40` and `None`; a stamp file whose commit breaks the pattern reads as `None` |
| 14 | should fix | fixed, S0006 c2 (new) and the Interface: `PreflightItem` and `PreflightReport` frozen, `extra="forbid"` |
| 15 | should fix | fixed, S0003 c1 to c4 and `activity`: activity is a handled event that is not `idle`; a stopped tick, `capped`, `error` and `reported` are idle. Old rule "returns `True` unless the tick's event was `idle`" replaced |
| 16 | should fix | fixed, S0004 c17 and c18 (old c15, c16): `CostRecorder.begin(started, role)` named, tests in the new file `tests/application/test_cost_image.py`, the `StartedStage` made by a real stage start; c17 also asserts that the completed record keeps the image |
| 17 | should fix | fixed, S0004. Claude Code is installed by `npm install --global @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}` (`nodejs` and `npm` join the pinned packages: six → eight, `curl` stays); old c4 "passes `${CLAUDE_CODE_VERSION}` to the installer" → c4 "the install command is `npm install` of `...@${CLAUDE_CODE_VERSION}`"; old c6 "the six packages are exactly..." → c6 "the eight packages"; old c2 gains the npm, `npx`, `curl ... \| bash` and `wget ... \| sh` cases; the Interface lists them as floating |
| 18 | should fix | fixed by the human's answer: the identity is `/opt/factory/image-id`, generated by `cat /proc/sys/kernel/random/uuid`. S0004 c10, c11 (old c10 "`ARG FACTORY_IMAGE` has no default, `test -n` follows it, `ENV` copies it" → c10 "has a default and is used by one `LABEL` only", c11 the `RUN cat ...`); S0001 c9, c10, c11 (the file is read; missing or empty refused; `FACTORY_IMAGE` ignored); S0003 c13. Old S0002 c13 (`FACTORY_IMAGE=build-7` gives `image`) → S0001 c9 |
| 19 | should fix | fixed by the human's answer: `/state` stays `0755 factory:factory`; the run files go to `/state/runs`, `2750`, group `factory-work`. S0004 c14, c15, c16 (old c12 "makes `/work`, `/state` and `/home/agent/.claude` mode 2775" split into c13 users, c14 `/state`, c15 `/state/runs`, c16 the other two); S0002 c16 (the runtime's state directory is `<state directory>/runs`); S0005 c16 (the entrypoint makes the directory and sets `2750`). Gap found while doing it: files written with the factory's umask would be group-writable; S0011 c10 sets mode `0640` on the run files (decision 29, changes F0001's `ClaudeCodeRuntime`) |
| 20 | should fix | fixed, S0005 Demo 3: `FACTORY_CLAUDE_HOME="$d/home"` and `FACTORY_STATE="$d/state"` are set |
| 21 | should fix | fixed, S0005 c17 (new): `cd "$opt"`, the stub records its working directory (also Q23) |
| 22 | blocker | fixed, S0013 (new story), decision 22: items `agent-environment` and `agent-run-probe`, run once for each image build because they are machine extras; c1 to c11 |
| 23 | blocker | fixed, S0009 and S0014 (new), decision 16 and Out of scope. Old S0007 c9 "exactly two paragraphs" → S0009 c9 "starts with its boundary sentence, a blank line and its entry sentence"; S0014 c1 to c12 carry v1's texts renamed (no `stuck`, no v1 word, decisions named, the report sections `## Recommendation` and `## Proposed stories`) |
| 24 | should fix | fixed, S0009: the template is `template/factory/pipeline.yml`. Old c11 "`template/pipeline.yml` is read..." → c11 with the new path; old c12 "`template/` holds only `pipeline.yml`" → c12 "exactly one file, `template/factory/pipeline.yml`"; the Demo and the docs criterion (c14) say that the forms are the human's and that `StoryFormChecker` stops every stage until `factory/story-form.md` exists |
| 25 | should fix | fixed, S0007 c16, c17 (new), `PreflightStamp.main_failed`. A red `main` is probed once; its stop is kept (raised again, with the detail `... (probed earlier)`, only when the health status holds none) |
| 26 | should fix | fixed, S0007 c21, c22 (new) and `build_preflight`/`build_tick`; S0013 c12 to c14 assemble the extras. A `run_instance` test cannot stay valid as items are added, so S0007 tests `build_preflight` and the failing `build_tick`, and S0013 the full assembly |
| 27 | should fix | fixed, S0007 c18 (new): a run that ends as passed clears a standing `preflight_failed`, also when the stamp skipped the machine items |
| 28 | should fix | fixed, S0007 Interface: `class JsonPreflightStampFile(PreflightStampStore):`; also `FEATURE.md` (the other new classes inherit their interfaces) |
| 29 | should fix | fixed, S0008 c3, c6, c7: the fault is `key not applied by the agent runtime: <key>` and the check precedes the model's validation; the mixed cases are criteria. Old c3 "whose message contains it" → c3 "whose `fault` is `key not applied by the agent runtime: <key>`" |
| 30 | should fix | fixed, S0008 c14 (old c9): "carries on" → "the next tick returns `stopped=None`, dispatches the `run` event with the outcome `handled`", `handler_factory(boundaries, "factory-1", ...)` and a complete story named in the Tests line; old S0005 c8 → S0007 c9 ("no event is dispatched (`event is None`)") |
| 31 | should fix | fixed, S0010 c14 (see finding 6); c17 (old c17, WE3.5) stays "still works after an agent run" |
| 32 | should fix | fixed, S0003 c13, c16 and the `main` rule: `SettingsInvalid` from `read_settings` or from the runner (the token, the repository name) is a time-stamped line, a `preflight_failed` machine stop and status 2 |
| 33 | should fix | not built, by the human's answer; recorded as a gap left for v2: S0010 Assignment and docs criterion c19 (old c19 + "the project commands run as the factory's user, who can read the token file, which is left for v2" in the operator guide and `docs/decisions.md`), `FEATURE.md` decision 24 and Out of scope |
| 34 | should fix | fixed by the human's answer: S0012 `agent_user_item` (item `agent-user`), c7 fails with the token file and no agent user, c8 passes when the user is set, c9 passes when no token file exists; wired by S0013 c12, c13; decision 25 |
| 35 | should fix | fixed in part. Fixed in S0012: `Defaults:factory umask=0002`, `umask_override` and `!use_pty` in the sudoers file (c2 to c4; old c12 "exactly the line `factory ALL=(agent) NOPASSWD: ALL`" → c2 "exactly four lines" and c3 "the only line that is not a `Defaults` line is the rule"); the morning observations (agent-made file and directory, the factory's restore after an agent-made directory, a refused `sudo`, a time limit reached under `sudo`) are in the docs criteria of S0011 (c15) and S0012 (c11). Deferred: the kill of a timed-out agent under `sudo` (`run_process`' `killpg` cannot signal a root-owned `sudo`, so the limit is not enforced and the agent runs on). Both repairs (a `timeout --signal=KILL` wrapper whose exit status 137 the runtime reads as the limit, or a kill through `sudo -n -u agent -- kill`) need a hook in `process.py` or a rule for exit statuses that cannot be shown without `sudo`; it is `FEATURE.md` decision 30, open for the human |
| 36 | should fix | fixed, S0013 c8 and decision 20: the probe runs through `sudo` as the agent user, so a refusal is a machine stop before any claim; decision 20 now says what happens to a refusal that comes later (`AgentRuntimeError` after the claim: a counted error or a crash, not changed here). Old S0009 c7 (`AgentRuntimeError` from the runtime) stays as S0011 c8 |
| 37 | should fix | fixed, S0011 Interface: `*, version_time_limit: timedelta = VERSION_TIME_LIMIT, sudo_executable: str = "/usr/bin/sudo"` |
| 38 | should fix | fixed. New test files: `tests/adapters/test_agent_file_keys.py`, `tests/application/test_pipeline_loading_agents.py` (S0008), `tests/domain/test_agent_environment.py` (S0010), `tests/test_entrypoint_umask.py` with its own stub (S0012), `tests/application/test_cost_image.py` (S0004), `tests/application/test_boundaries_settings.py` (S0002); the one test that must change is named with the human's word asked (finding 3) |
| 39 | note | fixed, S0002 Interface: `@dataclass(frozen=True, kw_only=True)` |
| 40 | note | fixed, S0010: `token_file_item(path, *, uid, stat)`, `stat` passed by the wiring (`os.stat`); the demo and c8 to c10 pass `os.stat` |
| 41 | note | fixed: the Out of scope bullet is deleted; the sentences in old S0001 and S0003 are replaced by "already declared in `pyproject.toml`" (S0001, S0005) |
| 42 | note | fixed, S0006 c12: the test uses a `ClaudeCodeRuntime` whose executable path does not exist |
| 43 | note | fixed, S0010 docs criterion c19 (`chown 1000`, `chmod 0400` of the host file, and the ownership of the mounted file as a morning observation); decision 19 |
| 44 | note | done by the human (`.gitignore` has `image/secrets/`); S0010 Assignment and docs criterion c19 say that git ignores the token file; decision 26 |
| 45 | note | deferred. After the moves (the token setting and reader to S0002, the allow list into `production_environment()`, the user parts to S0011 and S0012) S0010 has 19 criteria and a smaller code part; if intake finds it too big for $4 and one lease, the split falls at c11 to c16 (the static files) |
| 46 | note | fixed in all 14 stories: the second-to-last criterion is `make check stays green.` (the form check ran over all drafts) |
| 47 | note | fixed, S0003 c14: `main` keeps the stops already in force and replaces only one of the same reason |
| 48 | note | fixed, S0009: `"Bash(factory-check-story *)"` replaces `"Bash(factory-*)"`; the count of allow entries stays 16 (Demo and c10 unchanged); a Rules bullet and the docs criterion say that no other `factory-` command is allowed |
| 49 | note | fixed by the audit's alternative, S0001: the operator guide tells the operator to delete a checkout whose clone was killed half-way (docs criterion c24); decision 33 |
| 50 | note | fixed, S0002 (the last Rules bullet) and S0006 (the last Rules bullet): the wiring passes one object to `Boundaries.settings` and to the preflight's arguments; decision 34. `Boundaries.settings` stays (cost records and the composer read it) |

## The human's answers of 2026-10-14

| Finding | Applied |
|---|---|
| 19 | S0004 c14, c15; S0005 c16; S0002 c16; S0011 c10 and the 0640 gap; decision 8 |
| 33 | recorded as left for v2: S0010 c19, decision 24, Out of scope |
| 34 | S0012 c7, c8, c9; decision 25 |
| 18 | S0001 c9, c10, c11; S0004 c10, c11; S0003 c13; decision 7 |
| 44 | S0010 Assignment and c19; decision 26 |

## Questionnaire answers applied

| Answer | Applied |
|---|---|
| Q3, Q4, Q11, Q13, Q14 | no edit (as the audit said) |
| Q15 and decision 008 | S0003 docs criterion c22: "install v1.1 only on a repository v1 has not worked in, or whose v1 work items are archived or discarded (decision 008), because nothing detects them" |
| Q17 | decision 18; S0002 (`git_environment`, `git_options`); S0005 (no `git config`, c19); S0010 c15, c14; S0011 and S0012 (the `core.sharedRepository` line removed) |
| Q18 | decision 11; S0001 |
| Q20 | S0002, S0003 (`build_boundaries`, one `Tick`, `activity`), S0007 and S0013 (the preflight and the extras in `build_tick`) |
| Q21 | S0004 docs criterion c21 (names 2.1.289 and the maintenance feature) |
| Q22 | S0013 and decision 22 |
| Q23 | S0005 c17 and decision 23 |
| Q29 | S0009 c9, S0014, decision 16, Out of scope, Stories |
| Names built differently | S0009 (`F0001-S0009 and S0010`, the stand-in `tests/adapters/claude_stand_in.py`), S0011 (`version_time_limit`, c4 to c6), S0002 (`kw_only`), S0004 (`CostRecorder.begin`), S0007 (the order, the `Tick` signature), S0008 (the loader raises the stop, `AgentDefinitionInvalid(name, fault, key)` is used as built, no error type is created), S0010 (the scrub in `production_environment`), S0002 (`GitCli(directory, GitOptions(...))`) |

## Decisions the reader should look at

- Decision 28: two tests of other stages change (F0003's left-aside key; F0006-S0006's exit-2 line). The human's word is asked, as `CLAUDE.md` requires.
- Decision 29: `ClaudeCodeRuntime` (F0001) writes the run files with mode `0640`; the human's decision for `/state/runs` is not enough without it.
- Decision 30: the kill of a timed-out agent under `sudo` is open.
- Decision 32: S0014 needs the human to copy v1's `claude/` tree to `docs/v1-texts/` first.
- Decision 7 and the Dockerfile: `/state` is owned by `factory:factory` as the human wrote it, which needs a group `factory` of its own (gid 1000, no member).

## Sheet amendments the changes imply (no finding was deferred for them)

`interfaces.md` should record: `build_boundaries(settings, token, *, hosting=None)` and `Boundaries.settings` (the sheet has `build_boundaries(settings)`); `Tick(boundaries, instance, handlers, status=None, preflight=None)` and `Preflight.run() -> RepositoryStopReason | None`; `PipelineLoader` raising and clearing `agent_definition_invalid`; `read_settings(environ, read_file=None)` and the new `InstanceSettings` fields; `PreflightStamp.main_failed`; `production_environment()` with the allow list; `ClaudeCodeRuntime`'s `0640` run files. These are names inside F0010 or F0010's changes to built F0001 to F0006 code, and each is spelled in the stories.
