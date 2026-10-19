---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 266
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T13:54:16.117863Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T14:22:40.042125Z'
  stage: acceptance
  run: 4d0e83045d184d81b61dcde48efca1ba
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-19T14:23:58.405481Z'
  stage: done
stories: [F0022-S0001, F0022-S0002]
outcome: accepted
---

# Acceptance of A project brings its own skills and agents

## Recommendation

accepted with stories. Both stories together keep the feature's promise. The feature's walk-through ran green end to end: a project's coder and skill on `main`, the real wiring, loader, Claude Code runtime (stand-in), guard and entrypoint. `make check` is green, and every scope item has its code. The findings are small. One mutant survives in the feature's own `LEFT_OUT_TOOLS` skip, because every test lists `Skill` last. The documents leave out two things the feature recorded: the open nested `.claude/skills/` and the reused-volume upgrade step. Three test helpers are still copied. None of these breaks a promise.

## 1 Scope

None. Every scope item of `feature.md` has its code on `main`:
- `is_name` is in `src/factory/domain/identifiers.py`.
- `PROJECT_AGENTS_DIRECTORY`, `project_agent_file` and `AGENT_SUFFIX` are in `src/factory/domain/paths.py`.
- `factory/agents/*` is the eleventh entry of `PROTECTED_PATHS` in `src/factory/domain/write_paths.py`.
- `AgentDefinitionReader.parse` is in `src/factory/application/agent_runtime.py`.
- `FrontmatterAgentDefinitionReader.parse` is in `src/factory/adapters/agent_files.py`, with `read` built on it.
- `src/factory/application/project_agents.py` is new.
- `src/factory/entry/wiring.py:271` wires `ProjectAgentDefinitions(git, FrontmatterAgentDefinitionReader(settings.agent_home))`.
- In `claude/agents/*.md`, `Skill` is last in every agent's tools and R15 follows R14.
- `claude/settings.json` has `Skill` after `Grep`.
- `image/entrypoint.sh` has the `skills`/`commands` loop.
- `src/factory/adapters/opencode_runtime.py` has `LEFT_OUT_TOOLS`.

One addition is outside the scope list: `check_agent_name` in `src/factory/domain/agent_runs.py`. It came from S0001's round-0 review, which asked for one place for the name refusal. It is a domain function in a domain module, inside the spirit of decision 3. No story goes outside the scope, and nothing from *Out of scope* was built: the demos, `template/`, project settings and opencode skills are unchanged. The goal's last part, a skill and a project agent each seen in a real run of the todo demo, is the human's change 2. It comes after the feature, as `feature.md` says. The night log on `main` (`607cd632`) records change 1 as checked.

## 2 Feature smoke test

The walk-through of a human who runs the factory on a project of another kind:
- put a project coder (the shipped coder plus one sentence) and a skill on `main`;
- let the factory's real `build_boundaries` and `PipelineLoader` load it;
- run the coder through `ClaudeCodeRuntime` with the stand-in `claude` of `tests/adapters/claude_stand_in.py`;
- check that the guard refuses an agent's write to both;
- make the project coder faulty, then remove it;
- start the entrypoint on an agent home with a planted skill and command.

The script was `$TMPDIR/feature_smoke.py`, a `tempfile.TemporaryDirectory()` for its repositories. It was removed with the run's folder.

```
$ uv run -q python "$TMPDIR/feature_smoke.py"
1 push: pushed
2 load: ok, stops: []
3 coder: Begin your entry with the words `project coder:`. | tools: Read,Grep,Glob,Edit,Bash,Write,Skill
4 tester: You test what the criteria say and nothing else; a case they
5 run: completed review | --tools Read,Grep,Glob,Edit,Bash,Write,Skill
6 skill in the run's directory: True | project sentence in the call: True
7 guard factory/agents/coder.md -> factory/agents/coder.md is owned by the human; a change there is a question.
7 guard .claude/skills/journal-marker/SKILL.md -> .claude/skills/journal-marker/SKILL.md is owned by the human; a change there is a question.
7 guard src/x.py -> allowed
2026-10-19T14:16:34Z stop repository agent_definition_invalid: coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour
8 faulty: [('agent_definition_invalid', 'coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour')]
2026-10-19T14:16:34Z stop cleared agent_definition_invalid
9 removed: stops [] | coder: Never edit tests; a wrong test is a question.
exit 0
```

```
$ d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; mkdir -p "$d/opt" "$d/bin" "$d/home/skills/planted" "$d/home/commands"; cp -R claude "$d/opt/claude"
$ printf 'planted\n' > "$d/home/skills/planted/SKILL.md"; printf 'x\n' > "$d/home/commands/plant.md"; printf '#!/bin/sh\nexit 0\n' > "$d/bin/python"; chmod +x "$d/bin/python"
$ PATH="$d/bin:/usr/bin:/bin" FACTORY_OPT="$d/opt" FACTORY_CLAUDE_HOME="$d/home" FACTORY_STATE="$d/state" sh image/entrypoint.sh | sed 's/^[^ ]* //'; echo "exit $?"
installed agents and settings into /tmp/factory-run-…/tmp.xjd0q9uyvO/home
prepared /tmp/factory-run-…/tmp.xjd0q9uyvO/state/runs
starting instance unset
exit 0
$ cd "$d/home" && stat -c '%a %n' skills commands && find skills commands -mindepth 1 | wc -l
755 skills
755 commands
0
```

Green. Every half of the promise holds. The project's coder replaces the shipped one whole (line 3) and reaches `claude -p` with `Skill` in `--tools` (line 5). The role without a project file falls back to the shipped one (line 4). The skill lies in the run's working directory, where Claude Code finds it (line 6). `factory/agents/` and `.claude/` are refused to an agent (line 7). A faulty project file stops the tick with the named file and is never replaced by the shipped one (line 8). Removing it goes back to the shipped coder and clears the stop (line 9). The entrypoint removes a planted skill and command. Only the real run can show that Claude Code offers and loads the skill (decision 15, the human's change 2).

## 3 Mutation score

`make mutants` (plain, on `work-item/F0022-A0001`) ran twice. Each run was stopped at 540 s. The modules were `agent_files`, `opencode_runtime`, `agent_runtime`, `project_agents`, `agent_runs`, `identifiers`, `paths`, `write_paths` and `wiring`. The second run's lines:

```
Generating mutants
   done in 73ms (0 files mutated, 0 ignored, 129 unmodified)
Running clean tests
   done
Running forced fail test
   done
3772/14982  🎉 3588 🫥 0  ⏰ 3  🤔 0  🙁 181  🔇 0  🧙 0mutants: stopped after 540 s; the results below are partial, run it again to go on
```

The counter includes results that `mutants/` keeps from F0020's acceptance (`claude_runtime`, `process`, `cost_records_jsonl`). I counted the feature's nine modules from their `mutants/src/factory/**.py.meta`:
- **Killed:** 1453 of 1551 (93.7 %).
- **Survived:** 93.
- **Timed out:** 1 (`opencode_runtime`).
- **Not checked:** 4. They are `agent_runs._must_be_absolute` mutmut_2, `identifiers._checked` mutmut_6, `identifiers.work_item_order` mutmut_4 and `paths.cost_records_path` mutmut_3, the `ValueError(None)` mutants of code before F0022. mutmut stalls on them, as F0020's acceptance saw. Capping a mutant's wall time is the human's (`Makefile`, `[tool.mutmut]`).
- **No survivor:** `project_agents` (19/19), `write_paths` (47/47), `paths` and `identifiers`.

Survivors by group, from `uv run mutmut show`:
- **F0022's own code, one survivor:** `opencode_runtime._tools` mutmut_3. The `continue` after a tool in `LEFT_OUT_TOOLS` can become `break`. Every test lists `Skill` last: the rows `["Read","Skill"]` and `["Skill"]`, and the seven shipped agents. A project agent with `tools: [Skill, Read, Bash]` under opencode would then silently run with no tools. → **S0003**.
- **`agent_files._invalid`, 5 survivors (mutmut 5, 12, 33, 36, 37), equivalent.** They mutate the whole-model branch: the empty `loc`, the `"agent"` label of `first_fault`. `AgentDefinition` has no model validator, and a front matter that is not a mapping is refused earlier (`front matter is not a mapping`, which I checked by hand). The branch cannot be reached. This is code from before F0022.
- **`agent_runs.resumed_result`, 2 survivors:** F0020's code, in F0028-S0004's scope (`test_resumed_result_time_limit.py`, the human's draft).
- **`opencode_runtime`, 63 more survivors and 1 timeout:** F0020's code (`_call`, `_resume`, `_model_ms`, `parse_result_block`, `_Watch`). They are already proposed as F0020-S0009 and F0020-S0010 by F0020's acceptance.
- **`wiring`, 22 survivors** in `machine_log`, `read_hosting_token`, `repository_name`, `boundaries_from_environment` and the `log`/`disk_records` arguments of `build_boundaries`. All of them are in code before F0022: the mutants of F0022's own wiring line were killed. This is a later sweep of `factory.entry`, as F0028 says.

## 4 What the stories noticed

- **S0001 coder (entry 7): a literal `".md"` in `project_agents.py`.** Fixed in round 1 as `AGENT_SUFFIX`.
- **S0001 coder (entry 11): `_WORK_ITEM_SUFFIX` and `AGENT_SUFFIX` both hold `.md`.** They were kept apart on purpose, because they mean different things. I agree; no story.
- **S0001 tester (entry 5) and intake: no test of "writes nothing" or "the installed file is then not read" on its own.** Criterion 7 covers the second indirectly, and 19/19 killed mutants in `project_agents` agree. No story.
- **S0001 reviewer (entry 13): copied test helpers.** `ENVIRONMENT`, `COMPLETED` and `settings` in `tests/application/test_agent_run_probe_project_agent.py` are copied from `test_agent_run_probe.py`, and `PROJECT_CODER` is defined again across modules. All are still on `main`. I found `ENVIRONMENT` in two more probe modules (`_login`, `_opencode`). → **S0005**.
- **S0001 reviewer (entry 13): tests that branch on a parameter in their body.** `tests/application/test_pipeline_loading_project_agents.py:30` and `test_project_agents.py:69` do it. This is a style note, not worth a story.
- **S0001 documenter (entry 15): the probe paragraph's "the reader's message naming the agent".** It is still true. None.
- **S0002 reviewer (entry 17): the entrypoint `layout` fixture copied into `tests/test_entrypoint_skills.py`.** There is a third copy in `test_agent_home_ownership.py`, and the original is in `test_entrypoint.py`. → **S0005**.
- **S0002 documenter (entry 19): stale passages in the decision log.** The entries of 2026-10-16 (F0010; the entry wrote "2016") and 2026-10-17 (F0012-S0025) still say skills stay writable in the home. The new entry does not say it supersedes them. → **S0004**.
- **S0002 smoke tester (entry 21): its smoke test drops the log lines and does not check ownership.** The tests of criterion 4 cover both. None.
- **Mine:** a project agent with an empty body is accepted, with instructions `''`, the same as for a shipped file. Decision 1 accepts that a project agent may drop the shipped rules. This is listed under 6, not a story.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` (*The agent files*, *A project's own agents*, *A project's own skills*, *The shipped agents and settings*, *The agent runs as a second user*, the probe and the stops), `docs/project-guide/agents.md`, `work-items.md`, `write-guard.md` and the two new entries of `docs/decisions.md`. The two stories' texts agree with each other and with what the smoke test shows. `uv run python -m factory.entry.check_documents` prints `documents ok`. Four gaps, all left out rather than wrong:
- **`.claude/*` is protected at the root only.** `docs/operator-guide.md:913` says "`.claude/*` is a protected path that no stage writes". Neither the guide nor the decision log says what decision 12 left open: a `.claude/skills/` in a subfolder (`src/.claude/skills/`) is inside a stage's write paths and may be loaded. An operator would take every skill for the human's.
- **The upgrade step of a reused `claude-home` volume is only in `feature.md` (change 1).** On a reused volume, a `skills/` folder that an agent made without group write stops the new entrypoint, and the instance restarts. The operator guide, written for the operator, does not say so.
- **The decision log's new entry does not say it supersedes the open "skills"** of the F0012-S0025 entry.
- **`docs/project-guide/agents.md` says "there is no other copy"** of an agent's text. That is true for factory-rf's shipped agents, but it no longer holds for a project that carries `factory/agents/`.

→ **S0004** for all four. `README.md` names no agent location, and nothing there needs the feature.

## 6 Decisions taken for the human

To accept or revisit:
1. **A project agent replaces the shipped one whole, read from `origin/main` only.** It may drop the shipped rules, and an empty body runs with no instructions at all (decision 1).
2. **A project may add a role.** `names()` is the union of the installed names and the project's names (decision 2).
3. **A faulty project file stops with `agent_definition_invalid`** and is never replaced by the shipped one (decision 3).
4. **`parse` joins the reader's interface** (decision 4).
5. **`factory/agents/*` is the eleventh protected path.** R14 is unchanged (decision 5).
6. **The probe runs the project's coder once per image.** A project agent added later is checked by every tick's load only (decision 6).
7. **`Skill` is given to all seven shipped agents** (decision 7).
8. **`Skill` is in the settings' `allow` list,** whether or not Claude Code 2.1.296 needs it (decision 8).
9. **R15 sits right after R14 in every agent** (decision 9).
10. **The entrypoint remakes `skills/` and `commands/` empty at every start.** A folder of mode 0700 that an agent made stops the entrypoint (decision 10, change 1).
11. **Only Claude Code's runs get `Skill`.** opencode leaves it out, and whether opencode loads skills by itself is unknown (decision 11).
12. **A run reads the skills from its checkout.** Open: a nested `.claude/skills/` is not protected; the proof run looks (decision 12).
13. **The factory does not check what a skill says** (decision 13).
14. **The coder's choices.** `check_agent_name` went into `factory.domain.agent_runs`, not `identifiers` (S0001 entry 11). `AGENT_SUFFIX` is public in `paths`. `LEFT_OUT_TOOLS` is a set of its own, not a sentinel in `TOOL_NAMES` (S0002 entry 7). `FrontmatterAgentDefinitionReader.parse` checks the name again, though `read` already did.
15. **Still open:** the proof run (change 2) has not been done. It is the only evidence that Claude Code offers and loads the skill under `--tools …,Skill`.

Earlier tests changed, each with its leave. All are under the feature's decision 14, and each reviewer named them:
- S0001: `tests/domain/test_write_paths.py` (the rename to `..._eleven_patterns`, plus `"factory/agents/*"`); `tests/entry/test_wiring_boundaries.py` (expects `ProjectAgentDefinitions`, clones `remote`; one import that the change left unused was removed); `tests/application/test_agent_definition_reader.py` (`parse` in the abstract methods and the sorted names).
- S0002: `tests/shipped_agents.py` (`_ALL_TOOLS`, `_TOOLS_WITHOUT_WRITE` gain `"Skill"`); `tests/test_claude_files.py` (`SETTINGS` `allow` gains `"Skill"`).

No earlier test was changed without a leave. The diff of `00d1b12e^1..bd6d0edc` under `tests/` modifies exactly these five files and adds the rest.

## 7 The slow checks

The project offers nothing beyond `make check` and `make mutants`: no image scan and no SBOM. `make check` was green as I found it (`test: green (51.3 s)`, coverage 99.07 %, `check: green`).

From `.reports/junit.xml`: 5760 test cases and 489 s of test time.
- **The slowest overall** are F0020's: `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` and `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.0 s each), then `test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused]` (4.1 s).
- **The feature's 89 test cases** take 3.6 s together. The slowest is `test_tick_project_agent::test_the_stage_runs_the_project_agent_of_its_role` at 0.4 s per row.

Disk: at acceptance, /work has 978.6 GB free and 0.5 GB used, and /state and /tmp 0.0 GB used. That equals the previous record (at start). No growth.

## 8 Cost

- **Total:** 18 runs, 19.6 min, 145 turns, $5.86.
- **S0001:** 8 runs, $3.44. Its tester run (196 s, $1.08) is the most expensive single run of the feature. It wrote eight new test modules and changed three earlier ones. One review round sent it back, for the copied name refusal and the literal `.md`.
- **S0002:** 10 runs, $2.42. A review finding about the tests alone (two test functions of one rule) cost a coder → tester → coder detour of three runs (about $0.44) on top of the second review.
- **Neither story stands out** against its size.
- **Human interventions:** 0 questions answered, 0.0 h waited. No story needed the human. The pre-check answers of 2026-10-19 morning (decision 17) were given before the stories started.

## Proposed stories

- `F0022-S0003-the-opencode-runtime-leaves-out-skill-wherever-it-stands-in-an-agent-s-tools`: pins the one surviving mutant in the feature's own code, a left-out `Skill` that is not last (tests only).
- `F0022-S0004-the-documents-name-a-nested-skills-folder-and-the-upgrade-of-a-reused-agent-home`: the four documentation gaps of check 5 (documents only).
- `F0022-S0005-the-probe-project-agent-and-entrypoint-tests-share-their-helpers`: moves the copied test helpers that the reviewers noted to one place each, under the standing leave (tests only).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 3 stories proposed; make mutants 1453/1551

   1 Scope: none. Every scope item is on main, and the only addition, `check_agent_name` in `domain/agent_runs.py`, came from the review. The real run of a skill and a project agent is still the human's change 2.
   2 Feature smoke test: green. A project coder and skill on main go through the real `build_boundaries`, the `PipelineLoader`, `ClaudeCodeRuntime` with the stand-in `claude` (`--tools …,Skill`), the guard refusals, the faulty file's stop (raised, then cleared) and the fallback to the shipped coder. The entrypoint empties `skills/` and `commands/`.
   3 Mutation score: `make mutants` stopped at 540 s twice; mutmut stalls on 4 `ValueError(None)` mutants of code from before F0022. On the feature's nine modules, 1453 of 1551 mutants were killed (93.7 %), with 93 survivors and 1 timeout. Only one survivor is in F0022's own code: `opencode_runtime._tools` `continue`→`break`, because every test lists `Skill` last (S0003). The `agent_files._invalid` survivors are equivalent. The rest are F0020 and wiring code from before F0022, already proposed elsewhere or in F0028.
   4 What the stories noticed: the copied test helpers the reviewers named are still on main, and I found two more copies (S0005). The decision log entries saying skills stay writable are not marked as superseded (S0004). The other notes were fixed or are covered.
   5 Documentation: no contradictions, but four gaps (S0004): the open nested `.claude/skills/`, the upgrade step for a reused `claude-home` volume, the "supersedes" note in the decision log, and "there is no other copy" in the project guide.
   6 Decisions for the human: decisions 1–13 of `feature.md`, plus the coder's placements of `check_agent_name`, `AGENT_SUFFIX` and `LEFT_OUT_TOOLS`. Two points stay open: the proof run (change 2) and the nested-skills question. Five earlier tests were changed, all under decision 14's leave and named by the reviewers; none was changed without leave.
   7 Slow checks: the project has nothing beyond `make check` and `make mutants`. `make check` is green (51.3 s, 99.07 % coverage). The feature's 89 test cases take 3.6 s; the slowest is 0.4 s. Disk use is the same as at the start (0.5 GB).
   8 Cost: 18 runs, 19.6 min, $5.86. S0001 cost $3.44, with the costliest single run (the tester, 196 s, $1.08) and one review round. S0002 cost $2.42, including a three-run coder→tester→coder detour for a test-only finding. The human answered 0 questions and the stories waited 0.0 h for them.
3. factory: done (pull request merged); cost: 1 runs, 28.3 min, 84 turns, 177901 tokens in (8807712 more from cache), 50115 out, $4.19
