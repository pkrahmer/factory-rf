---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 306
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T00:11:41.176891Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T00:15:20.950473Z'
  stage: acceptance
  run: 26c6170c18a348c8a21b21ee2b55e726
stories: [F0022-S0001, F0022-S0002, F0022-S0003, F0022-S0004, F0022-S0005, F0022-S0006, F0022-S0007]
outcome: null
---

# Acceptance of A project brings its own skills and agents

## Recommendation

**Accepted.** The two stories that A0002 proposed are merged and do what they said:
- S0006 records the proof run in the documents.
- S0007 moved the entrypoint tests' layout to a support module.

`make check` is green as I found it. The feature's walk-through is green end to end: a project coder and skill on `main`, through the real wiring and loader, then the guard, a faulty file, its removal, the opencode tool mapping and the entrypoint. What is left is either the human's (the *Stories* list of `feature.md`, the open nested `.claude/skills/`) or test debt from other features. Neither is worth a story here, so this report proposes none.

## 1 Scope

None. A0001 (#266) found every scope item of `feature.md` on `main`. A0002 found the same after S0003 to S0005. The two stories since then are the ones A0002 proposed, and each stays inside the feature:
- **S0006** (#302) changed only `docs/decisions.md` (3 lines) and `docs/operator-guide.md` (1 line), as its criterion 3 names.
- **S0007** (#304) changed only test files:
  - new: `tests/entrypoint_support.py`, `tests/search_support.py`, `tests/test_entrypoint_support.py`;
  - changed: `tests/conftest.py`, `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py`, `tests/test_entrypoint_skills.py`, `tests/test_shared_test_helpers.py`.

  Its leave is decision 14's S0007 bullet.

Neither story changed `src/`, `claude/`, `image/`, `template/` or `demo/`, and nothing from *Out of scope* was built. The goal's real test, the human's change 2, passed on 2026-10-19, and `docs/decisions.md` now records it in its `Proven:` bullet. `feature.md`, *Stories*, still lists only S0001 and S0002. It is the human's file (see 6).

## 2 Feature smoke test

The walk-through of a human who runs the factory on a project of another kind:
- push a project coder and a skill to `main`, with a `README.md` beside the coder that is not an agent. The coder is the shipped coder with `Skill` moved first in its tools and one sentence added.
- clone and build the real boundaries (`build_boundaries`), then load the pipeline definition (`PipelineLoader`).
- read the project coder and a shipped tester.
- ask the guard about the protected and the nested paths.
- make the project file faulty, then remove it on `main`.

The script was `$TMPDIR/feature_smoke.py`. It used a `tempfile.TemporaryDirectory()` and the test helpers `make_remote` and `HumanClone`.

```
$ uv run -q python "$TMPDIR/feature_smoke.py"; echo "exit $?"
1 pushed: factory/agents/coder.md, factory/agents/README.md, .claude/skills/journal-marker/SKILL.md
2 names: acceptance-reviewer,coder,documenter,intake,reviewer,smoke-tester,tester
3 load: ok, stops: []
4 coder (project): Begin your entry with the words `project coder:`. | tools: Skill,Read,Grep,Glob,Edit,Bash,Write
5 tester (shipped): tools: Read,Grep,Glob,Edit,Bash,Write,Skill | R15: True
6 skill in checkout: True
7 guard factory/agents/coder.md -> factory/agents/coder.md is owned by the human; a change there is a question.
7 guard .claude/skills/journal-marker/SKILL.md -> .claude/skills/journal-marker/SKILL.md is owned by the human; a change there is a question.
7 guard src/.claude/skills/x/SKILL.md -> allowed
7 guard src/x.py -> allowed
2026-10-20T00:13:33Z stop repository agent_definition_invalid: coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour
8 faulty: [('agent_definition_invalid', 'coder: factory/agents/coder.md at origin/main: key not applied by the agent runtime: colour')]
2026-10-20T00:13:34Z stop cleared agent_definition_invalid
9 removed: stops [] | coder tools: Read,Grep,Glob,Edit,Bash,Write,Skill | project sentence: False
exit 0
```

The opencode half. This calls the runtime's private `_tools` directly, without a stand-in run:

```
$ uv run -q python "$TMPDIR/opencode_smoke.py"; echo "exit $?"
opencode shipped tools on: ['bash', 'edit', 'glob', 'grep', 'read', 'write']
opencode project, Skill first tools on: ['bash', 'edit', 'glob', 'grep', 'read', 'write']
exit 0
```

The entrypoint, on a home with a planted skill and command:

```
$ d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; mkdir -p "$d/opt" "$d/bin" "$d/home/skills/planted" "$d/home/commands"; cp -R claude "$d/opt/claude"; printf 'planted\n' > "$d/home/skills/planted/SKILL.md"; printf 'x\n' > "$d/home/commands/plant.md"; printf '#!/bin/sh\nexit 0\n' > "$d/bin/python"; chmod +x "$d/bin/python"; PATH="$d/bin:/usr/bin:/bin" FACTORY_OPT="$d/opt" FACTORY_CLAUDE_HOME="$d/home" FACTORY_STATE="$d/state" sh image/entrypoint.sh | sed 's/^[^ ]* //'; echo "exit $?"; (cd "$d/home" && stat -c '%a %n' skills commands && find skills commands -mindepth 1 | wc -l)
installed agents and settings into /tmp/factory-run-…/tmp.ST8dVtXkhJ/home
prepared /tmp/factory-run-…/tmp.ST8dVtXkhJ/state/runs
starting instance unset
exit 0
755 skills
755 commands
0
```

Green. What each line shows:
- **Line 2:** the project's `README.md` is not taken for an agent (decision 2).
- **Lines 3 and 4:** the project coder replaces the shipped one whole and loads without a stop.
- **Line 5:** a role without a project file keeps the shipped agent, with `Skill` and R15.
- **Line 6:** the skill is in the run's working directory, from the checkout (decision 12).
- **Line 7:** `factory/agents/*` and the root `.claude/` are refused. `src/.claude/skills/` is allowed, which is the open point the documents state.
- **Line 8:** a faulty project file stops the load and names the file. The shipped agent does not replace it.
- **Line 9:** removing the file clears the stop and brings back the shipped coder.
- **opencode:** under opencode, `Skill` is left out wherever it stands.
- **Entrypoint block:** it empties a planted `skills/` and `commands/`.

The proof in a real run is the human's change 2, which is recorded in the documents now.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0006:** each of its five stage entries reported nothing noticed. The intake (entry 3), reviewer (entry 9) and documenter (entry 11) each said the proof run's evidence is the human's account and that they did not check it. The smoke tester (entry 13) counted the `Proven:` bullet's three sentences against the criterion's "one or two" as wording, not a finding. I agree: the bullet says exactly what the criterion lists.
- **S0007's reviewer (entry 17): `tests/test_shared_fixtures.py:9` (`_defining`) is a similar search outside the diff.** It is F0026's test, not F0022's. It searches every module without leaving itself out, so it does not quite match `modules_matching(pattern, leave_out)` in `tests/search_support.py`. Other older searches under `tests/` follow the same pattern, such as `test_test_names.py`, `test_single_project.py` and `test_process_search.py`. Folding them into one helper is a sweep across features, under the standing leave. It belongs to no F0022 story and is not proposed here. Listed for the human.
- **S0007's intake (entry 3):** decision 14's S0007 bullet has a real line break where the story writes `\n`. The intake read it as the story meant it, and the tests follow the story. It is the human's `feature.md`, and nothing is wrong in the code.
- **S0007's tester (entry 13):** it chose `modules_matching` over `test_modules_matching` because pytest would collect the second name as a test. That is a sound choice and needs nothing further.
- **`duplicates: 5 new, 33 known, 3 gone`** in both coder entries. It is unchanged since A0002, which traced every finding to F0020 or older code. Neither story changed `src/`.
- **`feature.md`, *Stories*, still lists only S0001 and S0002.** This is noted since S0003 and is the human's.

## 5 The documentation as a whole

None. I read `docs/operator-guide.md`, *A project's own skills* and *The shipped agents and settings*. I read `docs/decisions.md`, the entry *The agents load a project's skills, and the agent's home gets none*. In `docs/project-guide/` I read `agents.md` (the project agents, the opencode tools and the table of the seven agents), `work-items.md` and `write-guard.md`. `README.md` names no agent or skill location, and it needs none.

S0006's three repairs are in place:
- "(the feature's proof run looks)" is gone;
- "A run reads the root `.claude/skills/`" names its subject;
- the `Proven:` bullet records the proof run. The `Open:` bullet keeps the nested folder and says the run did not check it.

The guides and the log agree with each other and with the smoke test:
- line 7's `src/.claude/skills/` → allowed;
- `Skill` last in the shipped tools, with the settings allowing it after `Grep`;
- eleven protected paths;
- an opencode run leaves `Skill` out.

No example names the test helpers S0007 moved.

## 6 Decisions taken for the human

Decisions 1 to 17 of `feature.md` and the placements of S0001 to S0005 were listed in A0001 and A0002 and accepted with their merges. What S0006 and S0007 added, or what is still yours:
1. **The nested `.claude/skills/` stays open** (decision 12). The documents now say it was not checked. Your options:
   - (a) leave it open;
   - (b) protect `*/.claude/*` in a later story;
   - (c) a short real run that plants `src/.claude/skills/` and looks.

   As in A0002, I would choose (c) before (b).
2. **`feature.md`, *Stories*,** lists S0001 and S0002 and not S0003 to S0007. Update it or leave it as the original plan. It is your file.
3. **S0006's `Proven:` bullet** states the human's account of the proof run as fact. No stage checked it against the night log, and every stage said so.
4. **S0007's names:** `tests/entrypoint_support.py` holds `Layout`, its constants, `STAMP`, `STAMPED` and `texts` (the old `_texts`, now public). `tests/search_support.py` holds `modules_matching(pattern, leave_out)`, which the round-1 review asked for. The local `texts` in `test_a_missing_image_file_ends_the_run_with_one_line_before_the_instance` became `lines`, as the Interface said.
5. **The older test searches** (check 4) are left to a sweep across features rather than an F0022 story.

Earlier tests changed, each with its leave:
- **S0006:** none.
- **S0007, under the standing leave to move a shared test helper** (`CLAUDE.md`, *Tests*):
  - `tests/conftest.py`: the import line;
  - `tests/test_entrypoint.py`: its copies removed, and the local rename;
  - `tests/test_agent_home_ownership.py`: the import;
  - `tests/test_entrypoint_skills.py`: the import, and `_texts` → `texts`;
  - `tests/test_shared_test_helpers.py`: `_writing` replaced by `modules_matching`, with its names, ids and patterns unchanged.
- **S0007, under the human's leave** (decision 14, S0007, 2026-10-20): `tests/test_shared_test_helpers.py`, the one expected import line of `test_the_image_layout_fixture_returns_the_entrypoints_layout`.

The reviewer named each one (entries 9 and 17). The merge diff of #304 holds exactly these files plus the three new ones. No earlier test was changed without a leave.

## 7 The slow checks

**Other checks:** the project offers nothing beyond `make check`, `make duplicates`, `make documents` and the sweep-only `make mutants`: no image scan, no SBOM.

**`make check`:** green as I found it: `test: green (39.0 s)`, coverage 99.13 %, `check: green`.

**Test times** (`.reports/junit.xml`): 6017 test cases, 442.9 s of test time.
- **Slowest overall**, all F0020's:
  - `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s);
  - `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.0 s);
  - `test_opencode_sudo_time_limit::…[status-1-past-the-limit]` (4.5 s).
- **The modules S0007 touched** are quick:

  | Module | Cases | Time |
  |---|---|---|
  | `test_entrypoint` | 12 | 0.18 s |
  | `test_agent_home_ownership` | 7 | 0.11 s |
  | `test_entrypoint_skills` | 3 | 0.06 s |
  | `test_shared_test_helpers` | 5 | 0.06 s |
  | `test_entrypoint_support` | 1 | 0.03 s |

**Disk:** no growth. The Disk now line equals the previous record line (acceptance):
- /work: 970.3 GB free, 0.5 GB used;
- /state: 970.3 GB free, 0.0 GB used;
- /tmp: 970.3 GB free, 0.0 GB used.

## 8 Cost

All seven stories: **57 runs, 47.0 min, 355 turns, $12.87.** S0001 to S0005 cost 41 runs and $10.19, as A0002 reported. The two follow-ups cost $2.68:

| Story | Runs | Time | Cost | Notes |
|---|---|---|---|---|
| S0006 | 6 | 3.2 min | $0.75 | first pass, documents only |
| S0007 | 10 | 7.3 min | $1.93 | stands out, mildly |

S0007 stands out because of one review round. The round-0 reviewer (entry 9) found that the new test's `_containing` copied `_writing` of `tests/test_shared_test_helpers.py`. The round that fixed it cost four more runs: coder hand-back, tester move, coder check, review. That round was the price of the reviewer's rule against a second copy of a helper. It left `tests/search_support.py` as one shared search.

Over the whole feature, S0002 and S0005 remain the costly stories (A0001, A0002).

**Human interventions:** 1 question answered (question 1), 0.0 h waited. It is the one A0002 named: S0005's smoke tester asked about the `-q` in its smoke command, and the human answered (b) in entry 22. S0005 is still the story that needed the human most, and the only one. S0006 and S0007 asked nothing. S0007's leave in decision 14 was given before it started, not through a question.

## Proposed stories

None. No finding of weight is left in F0022. The remaining items are the human's (the *Stories* list in `feature.md`, the open nested `.claude/skills/`, listed under 6) or belong to other features' tests (the older test searches, check 4).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: Accepted; 0 stories proposed. `make check` was green as I found it: test 39.0 s, coverage 99.13 %.

   1. Scope: no finding. S0006 changed only the two documents and S0007 only test files, which are the two stories A0002 proposed. No story touched `src/`, `claude/`, `image/`, `template/` or `demo/`. The proof run (change 2) is now recorded in the decision log's `Proven:` bullet. `feature.md`, *Stories*, still lists only S0001 and S0002; that file is the human's.
   2. Feature smoke test: green end to end.
      - A project coder (with `Skill` first) and a skill on `main` go through the real `build_boundaries` and `PipelineLoader`. The coder replaces the shipped one, a `README.md` there is not taken for an agent, and the tester stays shipped with `Skill` and R15.
      - The guard refuses `factory/agents/*` and the root `.claude/`, and allows `src/.claude/skills/`.
      - A faulty project file stops the load and names the file. Removing it clears the stop and brings back the shipped coder.
      - Under opencode, `Skill` is left out wherever it stands.
      - The entrypoint empties a planted `skills/` and `commands/`.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: S0007's reviewer found that `tests/test_shared_fixtures.py` (`_defining`, from F0026) has a search similar to the new `modules_matching`. Other older searches under `tests/` are similar too. That is a sweep across features, not an F0022 story, so I listed it for the human. S0006 noticed nothing. `duplicates: 5 new` is unchanged and comes from F0020 or older code.
   5. Documentation: no finding. S0006's three repairs are in place. The operator guide, the project guide and the decision log agree with each other and with the smoke test.
   6. Decisions for the human:
      - the nested `.claude/skills/` stays open, with options (a) leave it, (b) protect `*/.claude/*`, (c) a real run first; I would choose (c);
      - `feature.md`'s *Stories* list;
      - the `Proven:` bullet rests on the human's account, which no stage checked;
      - S0007's helper names.

      Earlier tests: S0007 changed five under the standing leave, plus one expected line under decision 14's S0007 leave. The reviewer named all of them, and none was changed without a leave.
   7. Slow checks: there is nothing beyond `make check`. The slowest tests are F0020's (5.0 s); S0007's modules each take under 0.2 s. Disk is unchanged from the previous record.
   8. Cost: 57 runs, 47.0 min, $12.87 in total. S0006 cost $0.75. S0007 cost $1.93, because one review round (four more runs) removed a copied search helper. Human interventions: 1 question (S0005's smoke `-q`, as before), 0.0 h waited. S0005 is still the story that needed the human most.
