---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 285
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T20:41:08.711335Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T20:47:23.816379Z'
  stage: acceptance
  run: 013cf932f784407fa07e1bbf4b7d0669
stories: [F0022-S0001, F0022-S0002, F0022-S0003, F0022-S0004, F0022-S0005]
outcome: null
---

# Acceptance of A project brings its own skills and agents

## Recommendation

**Accepted with stories.** The feature now keeps its whole promise:
- The three stories A0001 proposed are merged and do what they said.
- `make check` is green as I found it.
- The feature's walk-through is green end to end. It covers a project coder with `Skill` first in its tools, under both runtimes.
- The human's proof run (change 2) passed both halves on 2026-10-19.

What remains is small and needs two stories. The documents do not yet record the proof run, and one sentence still names a nested-skills check that the run never made (S0006). The entrypoint tests still import their layout from a test module (S0007). Neither breaks a promise.

## 1 Scope

None. This acceptance follows A0001 (#266), which found every scope item of `feature.md` on `main` (S0001, S0002). The three stories since then are the ones A0001 proposed, and each stays inside the feature:
- **S0003** (#282) adds four rows to `test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused`. They pin `LEFT_OUT_TOOLS` wherever `Skill` stands (decision 11), and the leave is decision 14's S0003 bullet. `_tools` in `src/factory/adapters/opencode_runtime.py:271` is unchanged.
- **S0004** (#284) fills the four documentation gaps of A0001's check 5.
- **S0005** (#283) moves the copied probe, project-agent and entrypoint helpers to one place each, under the standing leave.

No story changed `src/`. The merge diffs under `src/`, `tests/`, `docs/`, `claude/` and `image/` hold exactly the files the stories name. Nothing from *Out of scope* was built.

The goal's last part, a skill and a project agent each seen in a real run, is done. The night log (rows 19:29 to 19:34) records change 2:
- the coder's entry began `project coder:`;
- the intake's, tester's and coder's entries ended with `skill: journal-marker`;
- no `agent_definition_invalid` appeared;
- the agent was refused when it tried to make a folder in `skills/`;
- the shipped coder came back once the project's was removed.

One gap in the feature's own record: `feature.md`, *Stories*, still lists only S0001 and S0002. The intake, coder and documenter of S0003 each noted it, and the file is the human's.

## 2 Feature smoke test

The walk-through of a human who runs the factory on a project of another kind:
- push a project coder and a skill to `main`. The coder is the shipped coder with `Skill` moved first in its tools and one sentence added: the order S0003 pins, which a project is free to choose.
- load it through the real `build_boundaries` and `PipelineLoader`.
- run it through `ClaudeCodeRuntime` and `OpencodeRuntime`, each with its test stand-in.
- ask the guard about the protected and the nested paths.
- make the project file faulty, then remove it.
- start the entrypoint on a home with a planted skill and command.

The script was `$TMPDIR/feature_smoke.py`. It used a `tempfile.TemporaryDirectory()` and was removed with the run's folder.

```
$ uv run -q python "$TMPDIR/feature_smoke.py"; echo "exit $?"
1 pushed: factory/agents/coder.md, .claude/skills/journal-marker/SKILL.md
2 load: ok, stops: []
3 coder: Begin your entry with the words `project coder:`. | tools: Skill,Read,Grep,Glob,Edit,Bash,Write
4 tester (shipped): You test what the criteria say and nothing else; a case they
5 claude: completed review | --tools Skill,Read,Grep,Glob,Edit,Bash,Write
6 skill in the run's directory: True | project sentence in the call: True
7 opencode: completed review | tools on: ['bash', 'edit', 'glob', 'grep', 'read', 'write']
8 guard factory/agents/coder.md -> factory/agents/coder.md is owned by the human; a change there is a question.
8 guard factory/agents/new-role.md -> factory/agents/new-role.md is owned by the human; a change there is a question.
8 guard .claude/skills/journal-marker/SKILL.md -> .claude/skills/journal-marker/SKILL.md is owned by the human; a change there is a question.
8 guard src/.claude/skills/x/SKILL.md -> allowed
8 guard src/x.py -> allowed
2026-10-19T20:43:44Z stop repository agent_definition_invalid: coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour
9 faulty: [('agent_definition_invalid', 'coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour')]
2026-10-19T20:43:44Z stop cleared agent_definition_invalid
10 removed: stops [] | coder: - A reviewer's finding of a copied test helper is a change to tests: w
exit 0
```

```
$ d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; mkdir -p "$d/opt" "$d/bin" "$d/home/skills/planted" "$d/home/commands"; cp -R claude "$d/opt/claude"; printf 'planted\n' > "$d/home/skills/planted/SKILL.md"; printf 'x\n' > "$d/home/commands/plant.md"; printf '#!/bin/sh\nexit 0\n' > "$d/bin/python"; chmod +x "$d/bin/python"; PATH="$d/bin:/usr/bin:/bin" FACTORY_OPT="$d/opt" FACTORY_CLAUDE_HOME="$d/home" FACTORY_STATE="$d/state" sh image/entrypoint.sh | sed 's/^[^ ]* //'; echo "exit $?"; (cd "$d/home" && stat -c '%a %n' skills commands && find skills commands -mindepth 1 | wc -l)
installed agents and settings into /tmp/factory-run-…/tmp.np3Vy2OCG9/home
prepared /tmp/factory-run-…/tmp.np3Vy2OCG9/state/runs
starting instance unset
exit 0
755 skills
755 commands
0
```

Green. What each line shows:
- **Line 3:** the project coder replaces the shipped one whole.
- **Line 5:** it reaches `claude -p` with `Skill` first in `--tools`.
- **Line 7:** under opencode, the same agent turns on every tool after `Skill`. This is the case S0003 pins: the `break` mutant would have left nothing on.
- **Line 4:** a role without a project file keeps the shipped agent.
- **Line 8:** `factory/agents/*` and the root `.claude/` are refused. `src/.claude/skills/` is allowed, which is the open point the operator guide now states.
- **Line 9:** a faulty project file stops the tick, names the file, and is not replaced by the shipped agent.
- **Line 10:** removing the file goes back to the shipped coder and clears the stop.
- **Entrypoint block:** it empties a planted `skills/` and `commands/`.

## 3 Mutation testing

By sweep, not run here. My agent text asks for `make mutants`, but `CLAUDE.md`, *Checks*, now says "No stage and no agent runs it: mutation testing runs only as sweeps outside the factory, which the human starts on a fresh copy, with `mutants/` made anew for every run" (the human, 2026-10-19, commit `23dc158a`; F0031). That is the human's latest explicit rule, so I followed it. The checkout's `mutants/` folder is not a fresh copy either.

The night log's 22:37 row kept `mutants/*` in `tool_paths` so that this acceptance could still run the target on the old agent text. I read that as leave to run it, not as an order to. If you want a score for F0022, a sweep with `make mutants FEATURE=F0022` on a fresh copy gives it.

The one survivor A0001 found in F0022's own code, `opencode_runtime._tools` mutmut_3 (`continue` → `break`), is now covered by S0003's rows `skill-first`, `skill-before-two`, `skill-in-the-middle` and `notebook-edit-after-skill-refused`. Each would fail under `break`. I confirmed this by reading the code, not by running mutmut. Line 7 of the smoke test shows the same case. A0001's other survivor groups are code from before F0022 (F0020's `opencode_runtime` and `agent_runs.resumed_result`, `wiring`), and the same holds for `agent_files._invalid`, whose survivors were equivalent. S0003 to S0005 changed no `src/`, so nothing about them is new.

## 4 What the stories noticed

- **`feature.md` lists only S0001 and S0002 under *Stories*.** S0003's intake (entry 3), coder (entry 7) and documenter (entry 11) each noted it. It is the human's file. No story; listed for the human.
- **`duplicates: 5 new, 33 known, 3 gone` in every coder entry of S0003 to S0005.** None of those branches changed `src/`. Each reviewer handed the record on to this acceptance. I ran `make duplicates`:
  - four similar-code findings between `claude_runtime` and `opencode_runtime`: `call_refusal`, `cleanup_launch`, `version_printed` and the `confine_executable` branch;
  - `ManualWaiter` in `src/factory/adapters/clock.py:45`, reported as dead code;
  - three findings gone (`ManualClock`, `advance`, `work_item_markdown.data`).

  All of them are F0020's or older, none F0022's. Accepting the findings or fixing them is a matter for F0020 or the human's `security/duplicates-baseline.txt`, outside this feature. No story here.
- **`tests/conftest.py` imports `Layout` from the test module `test_entrypoint`.** S0005's coder (entries 7 and 15) and reviewer (entries 9 and 17) each noted it. I found two more imports from that module: `AGENT_TEXT` in `test_agent_home_ownership.py`, and the private `_texts` in `test_entrypoint_skills.py`. S0005's own structural test pins the import line, so the move needs a leave of the human's. → **S0007**.
- **S0005's smoke command 3 added `-q` to `pyproject.toml`'s `-q`.** pytest then printed no summary line. The human accepted the evidence instead (entry 22). The night log's "for the morning" note asks for a rule against `-q` in story smoke tests. That rule belongs in `factory/story-form.md` or the intake, both the human's. No story.
- **S0005's first tester run renamed `layout` → `image_layout` by find-and-replace, which also hit the docstring of `tests/test_entrypoint.py`.** The review caught it, and round 1 put the text back. Nothing is left.
- **S0004's tester, coder, reviewer and documenter:** nothing noticed. S0004's documenter did not run the `docker run` recovery command, because it needs a Docker volume. The command names the real volume `factory-<instance>_claude-home`, as the pre-check fixed it.

## 5 The documentation as a whole

`README.md` names no agent or skill location and needs nothing from this feature. I read `docs/operator-guide.md` (*The agent runs as a second user*, *A project's own agents*, *A project's own skills*), `docs/project-guide/agents.md` (*The seven agents*, *The opencode runtime*) and the two F0022 entries of `docs/decisions.md`. S0004's four passages are in place. The F0012-S0025 entry is now marked as superseded for "skills". The guides and the log agree with each other and with the smoke test, including line 8's `src/.claude/skills/` → allowed. `make documents` passed on S0004's branch (entry 11).

Two remaining faults, both in `docs/operator-guide.md:1002` and the decision log:
- **"Whether Claude Code loads such a nested folder is not known (the feature's proof run looks)."** The proof run took place, and the night log's rows of change 2 record no look at a nested folder. The sentence promises a check that did not happen. Decision 17 had expected it.
- **"A run reads them from its checkout."** S0004 inserted the nested-folder sentences before it, so "them" now reads as the nested folder, not the root `.claude/skills/`.

There is also a gap. The decision log's entry *The agents load a project's skills…* still rests on decision 15's "only the proof run shows", and it does not record what the proof run showed.

→ **S0006** for all three. None contradicts behaviour in a way that misleads a user about what the factory does.

## 6 Decisions taken for the human

Decisions 1 to 13 of `feature.md` and the coder's placements were listed in A0001 and accepted with its merge. What these three stories added, or what is still yours:
1. **The nested `.claude/skills/` stays open** (decision 12). The proof run did not check it, by the night log. The guard allows `src/.claude/skills/…` (smoke line 8). Whether Claude Code loads such a folder could not be checked here without a paid call. Your options:
   - (a) leave it open, as the documents say (S0006 keeps it open);
   - (b) protect `*/.claude/*` in a later story, so that no stage writes a `.claude/` anywhere;
   - (c) a short real run that plants `src/.claude/skills/` and looks.

   I would choose (c) before (b), so that the protection is not built against a route that does not exist.
2. **S0003 left `_tools` as it is** and rejected a comprehension that would make the `break` mutant impossible. The coder chose this (entry 7), and the review agreed.
3. **S0005 named the shared fixtures `probe_settings` and `image_layout`.** It put `probe_settings` in the conftest rather than a support module, as the Interface asked. The `settings` fixture of `test_agent_run_probe_opencode.py` and the `PROJECT_CODER` of `test_project_agents.py` stay apart, because they are different texts.
4. **S0005's structural test `tests/test_shared_test_helpers.py` pins helper locations in test code.** A later move needs a leave (see S0007).
5. **The human's answer to S0005 (entry 22), option (b):** the smoke test passed on evidence rather than on the literal `Expect:`.
6. **This acceptance did not run `make mutants`** (check 3). It followed `CLAUDE.md` over its own agent text. If you meant this acceptance to run it, say so, and it runs again.

Earlier tests changed, each with its leave:
- **S0003:** `tests/adapters/test_opencode_left_out_tools.py`. Four rows were added to `test_skill_is_left_out_and_every_other_tool_without_an_opencode_name_is_refused`, under `feature.md` decision 14 (S0003). The reviewer named it (entry 9).
- **S0005:** these files changed under the standing leave to move a shared test helper (`CLAUDE.md`, *Tests*):
  - `tests/application/test_agent_run_probe.py`, `_api_login.py`, `_login.py`, `_opencode.py` and `_project_agent.py`;
  - `tests/conftest.py`;
  - `tests/git_support.py`;
  - `tests/entry/test_wiring_project_agents.py`;
  - `tests/test_agent_home_ownership.py`;
  - `tests/test_entrypoint.py`;
  - `tests/test_entrypoint_skills.py`.

  The reviewer named each one (entries 9 and 17). The one change beyond a move, the docstring of `tests/test_entrypoint.py`, was found and reverted in round 1.
- **S0004:** none.

The merge diffs of #282 and #283 under `tests/` hold exactly these files, plus the two new ones (`tests/probe_support.py`, `tests/test_shared_test_helpers.py`). No earlier test was changed without a leave.

## 7 The slow checks

**Other checks:** the project offers nothing beyond `make check`, `make duplicates`, `make documents` and the sweep-only `make mutants`: no image scan, no SBOM.

**`make check`:** green as I found it: `test: green (46.0 s)`, coverage 99.12 %, `check: green`.

**Test times** (`.reports/junit.xml`): 5983 test cases, 432 s of test time.
- **Slowest overall**, all F0020's:
  - `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.0 s);
  - `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s);
  - `test_opencode_sudo_time_limit::…[status-1-past-the-limit]` (4.5 s).
- **The modules these three stories touched** are quick:
  - `test_opencode_left_out_tools`: 14 cases, 0.3 s;
  - `test_shared_test_helpers`: 5 cases, 0.05 s;
  - `test_agent_run_probe`: 14 cases, 0.6 s;
  - `test_wiring_project_agents`, `test_entrypoint`, `test_agent_home_ownership`, `test_entrypoint_skills`: each under 0.2 s.

**Disk:** used space did not grow. /work is 0.5 GB used now, as at the previous record; /state and /tmp are at 0.0 GB.
- **Free space** fell from 977.0 GB to 970.4 GB on all three mounts alike, so it is the shared host disk. The feature's changes do not explain the 6.6 GB. They changed no `src/`, only tests and documents.
- **The likely cause** is the host's own work since that record: the proof run's new instance `skills-demo` with its volumes, and four rebuilds of `self` (night log 21:17 to 22:40). I cannot see the host from here to confirm it.

## 8 Cost

All five stories: **41 runs, 36.6 min, $10.19.** S0001 and S0002 together cost $5.86, as A0001 reported.

The three follow-ups cost $4.33:

| Story | Runs | Cost | Notes |
|---|---|---|---|
| S0003 | 6 | $0.86 | first pass, no source change |
| S0004 | 6 | $0.86 | first pass, documents only |
| S0005 | 11 | $2.61 | stands out |

Why S0005 stands out:
- **The tester's first run** (210 s, $0.72) is the costliest single run of the three. It made thirteen file changes and a new structural test.
- **The review round for the docstring** that the find-and-replace hit cost four runs (coder, tester, coder, review: about $0.73) to restore one line.
- **The smoke-test question** cost a second smoke run ($0.15). The command's text came from a pre-check's recommended edit, not from the story's work.

**Human interventions:** 1 question answered (S0005's smoke tester, the `-q` question; answer (b) in entry 22), 0.0 h waited. S0005 is the story that needed the human most, and the only one. The cause was the smoke command's text, not the work: the night log's 22:26 row says the session wrote the command from a pre-check's edit without noticing the `-qq` trap.

## Proposed stories

- `F0022-S0006-the-documents-record-the-proof-run-of-a-project-s-skill-and-coder`: records in the decision log what the proof run of 2026-10-19 showed. It also makes the operator guide no longer name a nested-skills check that the run did not make, and fixes the antecedent of "them" (documents only).
- `F0022-S0007-the-entrypoint-tests-take-their-layout-from-a-support-module`: moves `Layout`, its constants and `_texts` from the test module `test_entrypoint` to `tests/entrypoint_support.py`, so that no conftest or test imports from a test module. It needs a decision 14 leave of the human's for the one changed check of `test_shared_test_helpers.py` (tests only).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: Accepted with stories; 2 stories proposed. `make mutants` was not run: `CLAUDE.md` now says no stage and no agent runs it (the human, 2026-10-19).

   1. Scope: no finding. S0003 to S0005 are the three stories A0001 proposed, and each stays in scope; none changed `src/`. The proof run (change 2) passed both halves on 2026-10-19 (night log, 19:29–19:34). `feature.md`'s *Stories* still lists only S0001 and S0002; that file is the human's.
   2. Feature smoke test: green end to end. A project coder with `Skill` first in its tools goes through the real `build_boundaries` and `PipelineLoader`. It reaches `claude -p` with `--tools Skill,…`, and under opencode it turns on every tool after `Skill`. The guard refuses `factory/agents/*` and the root `.claude/` and allows `src/.claude/skills/`. A faulty project file stops the tick and clears when fixed; removing it brings back the shipped coder. The entrypoint empties a planted skill.
   3. Mutation testing: by sweep, not run here. I followed `CLAUDE.md` (commit 23dc158a) over my agent text. A0001's one survivor in F0022's own code (`_tools` `continue`→`break`) is covered by S0003's rows; I checked that by reading the code, not by running mutmut.
   4. Noticed: `tests/conftest.py` and two test modules import from the test module `test_entrypoint` (S0005's coder and reviewer noted it) → S0007. `duplicates: 5 new` comes from F0020 and older code, not F0022. The rule against `-q` in smoke tests belongs in the human's story form.
   5. Documentation: S0004's passages are in place and consistent. Two faults remain: the operator guide still says "(the feature's proof run looks)" for nested skills, and the run did not look; S0004's insertion left an unclear "them". The decision log also does not record what the proof run showed → S0006.
   6. Decisions for the human: the nested `.claude/skills/` stays open, with three options and my choice of a short real run before any protection. Also S0003's untouched `_tools`, S0005's fixture names and its structural test, and the skipped `make mutants`. Earlier tests changed: S0003 under decision 14, S0005's 11 files under the standing leave. All were named by their reviewers; none was changed without a leave.
   7. Slow checks: there is nothing beyond `make check` (green, 46.0 s, 99.12 %). The slowest tests are F0020's (5.0 s); the touched modules take under 1 s each. /work used space is unchanged at 0.5 GB. Free space fell 6.6 GB on all mounts alike: the shared host disk, not explained by the feature's changes, likely the `skills-demo` instance and the rebuilds of `self`.
   8. Cost: 41 runs, 36.6 min, $10.19 in total; the three follow-ups cost $4.33. S0005 stands out at $2.61: a $0.72 tester run, a four-run round ($0.73) to restore one docstring, and a second smoke run. Human interventions: 1 question (S0005's smoke command `-q`, caused by the command's text), 0.0 h waited.
