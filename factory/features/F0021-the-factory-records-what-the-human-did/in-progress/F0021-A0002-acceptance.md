---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 245
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T01:41:39.113920Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T02:09:01.700025Z'
  stage: acceptance
  run: 43083d8ac1c84b93bfa86b581048bab4
stories: [F0021-S0001, F0021-S0002, F0021-S0003, F0021-S0004, F0021-S0005, F0021-S0006, F0021-S0007, F0021-S0008, F0021-S0009]
outcome: null
---

# Acceptance of The factory records what the human did

## Recommendation

Accepted with stories. Every scope item of `feature.md` has its story and its code, and the three follow-up stories of the first acceptance (S0007 to S0009) did what they promised. The feature smoke test is green end to end: it drives four real ticks built by `build_tick`, and `main_branch_failing` stays standing across the factory's own `stops recorded` commits and clears only for the human's fix. `make check` is green, and every mutant that survives in the feature's own lines is equivalent or an error text. What remains is one documentation repair: the README, which a newcomer reads first, says nothing of what the feature built and contradicts itself on its count of commands. That is proposed as S0010.

## 1 Scope

None. The first acceptance (`done/F0021-A0001-acceptance.md`, section 1) mapped every scope bullet to S0001 to S0006 and their code. This acceptance checked that mapping again against `main` and found it unchanged: a grep for `kind="question"` and `kind="stall"` under `src/factory` still finds only the writers that pass `blocked` or `reason`. The three later stories stay inside the feature:

- S0007 changed only `docs/` (the five passages of A0001's section 5). `git log` shows no file under `src/` or `tests/` in its commits.
- S0008 is the follow-up that decision 1 left to "a later story": `changes_only_stop_records` in `src/factory/domain/preflight.py`, used by `Preflight._clear_stale_failing_stop` and `_changes_only_stop_records` in `src/factory/application/preflight.py:390-409`. Skipping the probe for such a commit stays out, as its Description says.
- S0009 added tests only (`tests/entry/test_contract_arguments.py`, `tests/contract_support.py`); `src/factory/entry/contract.py` is unchanged.

The out-of-scope items stay out. `factory/stops.jsonl` is still not on `origin/main`, because no stop of the repository or the machine has been raised since S0003's image rebuild. The publish has not been seen in production, but the smoke test below runs it through real ticks.

## 2 Feature smoke test

The walk-through of the feature's purpose: a reader outside the factory learns the human's part from the records alone, and the stop records on `main` tell the truth about `main`. The script has three parts:

1. It reads the nine archived stories, both acceptance reports and the pipeline definition, validates each record against the committed schemas (with `jsonschema`, which is in the virtual environment only as another tool's dependency, so nothing is declared), and computes the waits and the facts line.
2. It builds a real instance with `build_boundaries` and `build_tick`, on a temporary bare remote that holds this repository's `factory/pipeline.yml`, with the shipped agent files and a fake hosting service. The preflight stamp says `main` was probed red and `main_branch_failing` stands, and `which` finds no tool, so the machine's items fail. Then it runs two ticks, a human commit to `README.md` and two more ticks, and reads `factory/stops.jsonl` from the human's clone after each tick.
3. It regenerates the contract into a folder whose parent is missing and compares the result with `src/factory/contract/`.

Command, from the root of the checkout: `uv run python -I "$TMPDIR/smoke/feature_smoke.py"`. The script:

```python
"""F0021 end to end: a reader outside the factory computes the human's part from the records alone."""
import json, subprocess, tempfile
from pathlib import Path

import frontmatter, jsonschema
from ruamel.yaml import YAML

from factory.adapters.cost_records_jsonl import JsonLinesCostRecordReader
from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.adapters.work_item_markdown import FrontmatterWorkItemReader
from factory.application.stops import StopService
from factory.domain.stops import HealthStatus
from factory.domain.human_waits import human_line, human_waits
from factory.domain.paths import STOP_RECORDS_FILE
from factory.domain.preflight import PreflightStamp
from factory.domain.settings import InstanceSettings
from factory.domain.stops import RepositoryStop
from factory.entry.wiring import build_boundaries, build_tick

root = Path.cwd()
contract = root / "src/factory/contract"
schema = {p.name.removesuffix(".schema.json"): json.loads(p.read_text()) for p in sorted(contract.glob("*.schema.json"))}
feature = next((root / "factory/features").glob("F0021-*"))
reader, costs = FrontmatterWorkItemReader(), JsonLinesCostRecordReader()

def as_json(value):
    return json.loads(json.dumps(value, default=str))

def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

print("1. the archived stories: causes on the records, the human's waits, the contract")
everything = []
for path in sorted((feature / "done").glob("F0021-S*.md")):
    story = path.name[:11]
    jsonschema.validate(as_json(frontmatter.loads(path.read_text()).metadata), schema["work-item-state"])
    journal = reader.read(path).state.journal
    waits = human_waits(journal)
    everything += waits
    lines = costs.read(path.with_suffix(".costs.jsonl"))
    for line in path.with_suffix(".costs.jsonl").read_text().splitlines():
        jsonschema.validate(json.loads(line), schema["cost-record"])
    denied = [r.denials for r in lines if r.denials is not None]
    blocked = sorted({r.blocked for r in journal if r.blocked})
    print(f"   {story}: front matter valid; {human_line(waits)}; causes {blocked}; "
          f"{len(lines)} cost lines valid, {len(denied)} with denials (sum {sum(denied)})")
print(f"   facts line over the feature: {human_line(everything)}")
for path in sorted(feature.glob("*/F0021-A*-acceptance.md")):
    jsonschema.validate(as_json(frontmatter.loads(path.read_text()).metadata), schema["acceptance-state"])
    print(f"   {path.parent.name}/{path.name[:11]}: front matter valid against acceptance-state")
jsonschema.validate(as_json(YAML(typ="safe").load((root / "factory/pipeline.yml").read_text())), schema["pipeline-definition"])
print("   factory/pipeline.yml valid against pipeline-definition")

print("2. the stops reach main as records, and a red main stays red across them")
with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    seed = d / "seed"; seed.mkdir()
    git("init", "-q", "-b", "main", cwd=seed)
    (seed / "factory").mkdir()
    (seed / "factory/pipeline.yml").write_text((root / "factory/pipeline.yml").read_text())
    (seed / "README.md").write_text("seed\n")
    git("add", ".", cwd=seed); git("-c", "user.name=h", "-c", "user.email=h@x", "commit", "-qm", "seed", cwd=seed)
    git("clone", "-q", "--bare", str(seed), str(d / "origin.git"), cwd=d)
    git("clone", "-q", str(d / "origin.git"), str(d / "checkout"), cwd=d)
    git("clone", "-q", str(d / "origin.git"), str(d / "human"), cwd=d)
    state = d / "state"; state.mkdir()
    (d / "agents/agents").mkdir(parents=True)
    for agent in (root / "claude/agents").glob("*.md"):
        (d / "agents/agents" / agent.name).write_text(agent.read_text())
    settings = InstanceSettings(repository_url=str(d / "origin.git"), instance="smoke", checkout=d / "checkout",
                                state_directory=state, agent_home=d / "agents", min_free_gb=1)
    boundaries = build_boundaries(settings, "", hosting=FakeHostingService(), confine_executable=None)
    boundaries.health.write(HealthStatus())
    red = git("rev-parse", "HEAD", cwd=d / "checkout")
    # main was probed red: the stamp remembers the commit and the stop stands
    JsonPreflightStampFile(state / "preflight-stamp.json").write(PreflightStamp(image=None, main_failed=red))
    StopService(boundaries).raise_stop(RepositoryStop(scope="repository", reason="main_branch_failing",
                                                      detail="lint failed on main", at=boundaries.clock.now()))
    tick = build_tick(boundaries, settings, which=lambda name: None)  # the machine's items fail

    def standing():
        return [s.reason for s in boundaries.health.read().stops]

    def published():
        git("fetch", "-q", cwd=d / "human")
        try:
            text = git("show", f"origin/main:{STOP_RECORDS_FILE}", cwd=d / "human")
        except subprocess.CalledProcessError:
            return []
        rows = [json.loads(line) for line in text.splitlines()]
        for row in rows:
            jsonschema.validate(row, schema["stop-record"])
        return [f"{r['event']} {r['reason']}" for r in rows]

    for n in (1, 2):
        outcome = tick.run()
        print(f"   tick {n}: stopped {outcome.stopped}; standing {standing()}")
        print(f"           main holds {published()}")
    git("-c", "user.name=h", "-c", "user.email=h@x", "pull", "-q", cwd=d / "human")
    (d / "human/README.md").write_text("fixed\n")
    git("-c", "user.name=h", "-c", "user.email=h@x", "commit", "-qam", "the human fixes main", cwd=d / "human")
    git("push", "-q", "origin", "main", cwd=d / "human")
    print("   the human pushes a commit that changes README.md")
    for n in (3, 4):
        outcome = tick.run()
        print(f"   tick {n}: stopped {outcome.stopped}; standing {standing()}")
        print(f"           main holds {published()}")
    rows = [json.loads(l) for l in git("show", f"origin/main:{STOP_RECORDS_FILE}", cwd=d / "human").splitlines()]
    print(f"   detail published: {any('detail' in r for r in rows)}; instances {sorted({r.get('instance') for r in rows})}")
    print(f"   subjects on main: {git('log', '--format=%s', 'origin/main', cwd=d / 'human').splitlines()}")

print("3. the contract regenerates to the committed files")
with tempfile.TemporaryDirectory() as d:
    target = Path(d) / "a/b"
    out = subprocess.run(["uv", "run", "-q", "python", "-m", "factory.entry.contract", str(target)],
                         capture_output=True, text=True, check=True).stdout.strip()
    print(f"   {out}")
    same = all((target / p.name).read_bytes() == p.read_bytes() for p in contract.glob("*.schema.json"))
    print(f"   identical to src/factory/contract: {same} {sorted(p.name for p in target.iterdir())}")
    print(f"   versions: {sorted({s['x-records-contract'] for s in schema.values()})}")
```

Output (the factory log lines of part 2 shortened to their first words; each `preflight_failed` line lists the failed machine items in full):

```
1. the archived stories: causes on the records, the human's waits, the contract
   F0021-S0001: front matter valid; 0 questions answered, 0.0 h waited; causes []; 15 cost lines valid, 0 with denials (sum 0)
   F0021-S0002: front matter valid; 1 questions answered (question 1), 0.0 h waited; causes ['question']; 11 cost lines valid, 0 with denials (sum 0)
   F0021-S0003: front matter valid; 3 questions answered (question 3), 0.1 h waited; causes ['question']; 13 cost lines valid, 0 with denials (sum 0)
   F0021-S0004: front matter valid; 3 questions answered (question 3), 0.1 h waited; causes ['question']; 15 cost lines valid, 0 with denials (sum 0)
   F0021-S0005: front matter valid; 0 questions answered, 0.0 h waited; causes []; 6 cost lines valid, 6 with denials (sum 0)
   F0021-S0006: front matter valid; 0 questions answered, 0.0 h waited; causes []; 6 cost lines valid, 6 with denials (sum 0)
   F0021-S0007: front matter valid; 0 questions answered, 0.0 h waited; causes []; 6 cost lines valid, 6 with denials (sum 0)
   F0021-S0008: front matter valid; 0 questions answered, 0.0 h waited; causes []; 10 cost lines valid, 10 with denials (sum 0)
   F0021-S0009: front matter valid; 0 questions answered, 0.0 h waited; causes []; 10 cost lines valid, 10 with denials (sum 0)
   facts line over the feature: 7 questions answered (question 7), 0.2 h waited
   done/F0021-A0001: front matter valid against acceptance-state
   in-progress/F0021-A0002: front matter valid against acceptance-state
   factory/pipeline.yml valid against pipeline-definition
2. the stops reach main as records, and a red main stays red across them
2026-10-19T02:05:24Z stop repository main_branch_failing: lint failed on main
2026-10-19T02:05:25Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
   tick 1: stopped preflight_failed; standing ['main_branch_failing', 'preflight_failed']
           main holds ['raised main_branch_failing']
2026-10-19T02:05:25Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
   tick 2: stopped preflight_failed; standing ['main_branch_failing', 'preflight_failed']
           main holds ['raised main_branch_failing', 'raised preflight_failed']
   the human pushes a commit that changes README.md
2026-10-19T02:05:26Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
2026-10-19T02:05:26Z stop cleared main_branch_failing
   tick 3: stopped preflight_failed; standing ['preflight_failed']
           main holds ['raised main_branch_failing', 'raised preflight_failed']
2026-10-19T02:05:26Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
   tick 4: stopped preflight_failed; standing ['preflight_failed']
           main holds ['raised main_branch_failing', 'raised preflight_failed', 'cleared main_branch_failing']
   detail published: False; instances ['smoke']
   subjects on main: ['stops recorded', 'the human fixes main', 'stops recorded', 'stops recorded', 'seed']
3. the contract regenerates to the committed files
   contract: 5 schemas written
   identical to src/factory/contract: True ['acceptance-state.schema.json', 'cost-record.schema.json', 'pipeline-definition.schema.json', 'stop-record.schema.json', 'work-item-state.schema.json']
   versions: ['1.0']
```

Green, and the output shows the following:

- Every record validates against the committed schemas.
- The facts line computed from the records equals this run's prompt line.
- Ticks 1 and 2 each pushed a `stops recorded` commit, and `main_branch_failing` stayed through both (S0008, through the real tick: restore, publish, preflight).
- Only the human's commit to `README.md` cleared it (tick 3), and the `cleared` record reached `main` at the next tick (4).
- No detail is published, and the contract regenerates byte for byte into a new nested folder (S0009's behaviour).

A first attempt stopped at `pipeline_definition_invalid` (no agent files in the temporary agent home) and, as documented, published nothing because it stopped before the restore. The run above installs the shipped `claude/agents/*.md`.

## 3 Mutation score

`make check` was green before the runs (`check: green`, `test: green (40.6 s)`, coverage 99.06 %). `make mutants` (feature F0021, now 30 modules, S0008's two preflight modules included) ran twice in the foreground. It went on from the results the first acceptance left in `mutants/`. The second run ended:

```
⠧ 3286/13237  🎉 3139 🫥 0  ⏰ 2  🤔 0  🙁 145  🔇 0  🧙 0mutants: stopped after 540 s; the results below are partial, run it again to go on
```

Score over the checked mutants of the feature's modules: **3139 killed, 2 timeouts, 145 survived, of 3286 checked**. Another 2947 remain `not checked`, mostly in `claude_runtime` (480), `application.stage` (581), `acceptance_reading` (281), `domain.journal` (251, not reached at all) and `stalls` (174). As in F0019's acceptances and this feature's first one, the score is partial. S0008's modules were checked in full: `domain.preflight` 29 of 29 killed, and `application.preflight` 448 killed, 3 survived.

The survivors, grouped. I blamed each surviving line (`git blame` on the line the mutant changes) and read `uv run mutmut show` for every one in the feature's own lines:

- **The feature's own lines (10 survivors): all equivalent or error texts, so no criterion is missing.**
  - `entry.contract.write_contract`, 3 survivors: `encoding="utf-8"` becomes `None`, `"UTF-8"` or nothing. `json.dumps` writes ASCII only (`ensure_ascii` by default), and the committed schemas are ASCII, so all three are equivalent. S0009's two targets (`sys.argv[1:]`, `parents=True`) are now killed.
  - `domain.contract.contract_schema`, 3 survivors: `indent=2` becomes `None` or `3`. These are equivalent in mutmut's copy, where human change 1 deselects the byte-for-byte test.
  - `human_waits._answered_at`: `>` becomes `>=`. Equivalent, because the question record is never spoken by `human`.
  - `AcceptanceService._waits`: the `document.state is None` guard, which exists for the type checker only.
  - `stops._require_scope_of_reason`: an error text.
  - `cost_records_jsonl._refuse_constant`: an error text.
- **S0008's lines: none survive.** The 3 survivors in `application.preflight` are older (2026-10-16): `MachineChecks._hosting_service` passes `None` for `MAIN_BRANCH` to the fake's `find_open_pull_request`, and `_run_probe` checks out `main` without `start_point=origin/main`. The second is worth knowing: S0008's rule relies on the work tree being at `origin/main`, which the tick's restore guarantees (the reviewer checked it in S0008 entry 9), not `_run_probe`.
- **Older code in the touched modules (the other 135)**, unchanged since the first acceptance: `recovery` (24), `entry.wiring` (20), `application.acceptance` (19), `claude_runtime` (18), `closed` (13), `domain.acceptance` (12), `stage` (9), `questions` (8), `hand_over` (6), plus one or two each in `stalls`, `post_texts`, `tick` and `stops`. As in earlier acceptances, these are not proposed here.

## 4 What the stories noticed

The first acceptance collected S0001 to S0006 (its section 4) and took the document passages into S0007. That leaves the three later stories:

- S0007: every entry reports "nothing noticed".
- S0008 coder (entries 7, 11) and reviewer (entry 9): `Git.changed_paths(since)` compares with the work tree, not `origin/main`. The rule therefore relies on the tick's restore leaving the checkout at `origin/main`. The reviewer confirmed it, the project guide now says it (`docs/project-guide.md:791`), and the smoke test above exercises it. Nothing open.
- S0008 tester (entry 13) and coder (entry 15): `tests/application/test_stop_publisher.py:43` still holds an identical copy of the `records` fixture that moved to `tests/conftest.py`. It overrides the shared one with the same body. Five lines, harmless. The standing leave lets the next tester who touches that module remove it, so I propose no story of its own.
- S0009 reviewer's note (entry 17): `SCHEMA_NAMES` in `tests/entry/test_contract_arguments.py:13` and `SCHEMA_FILES` in `tests/entry/test_contract.py:16`. They are not one helper copied: one is derived from `CONTRACT` and the other is a literal list that pins the names. I leave it as it is.
- S0009 coder (entries 7, 11, 15): `src/factory/entry/contract.py:41`, the `__main__` guard, is the module's one uncovered line. Every `entry` module shows the same line, and the smoke test's `python -m` run reaches it. No story.
- S0009 documenter (entry 19): the operator guide does not say what the contract command does with two or more arguments (it prints the usage line to standard error and exits with 2), and offered a sentence. Taken into S0010.
- S0008 decision entry (`docs/decisions.md:626`): "The probe still runs once for such a commit when the machine's items pass; skipping it is left to a later story." This is listed for the human under 6, with no story proposed.
- Still standing from the first acceptance: `make duplicates` reports "3 gone" in every story (the unused `close` methods). `security/duplicates-baseline.txt` is the human's file.

## 5 The documentation as a whole

I read `README.md` and `docs/` from the top. The five findings of the first acceptance are repaired (S0007), the preflight passages written by S0008 agree across the three documents (`docs/operator-guide.md:347-348`, `docs/project-guide.md:791`, `docs/decisions.md:626`), and `make documents` prints `documents ok`. Findings:

1. **The README says nothing of the feature.** Its summary of what is built names the stops, the health status and the cost records with the bill. It does not name the journal's causes, the `Human:` line, the stop records on `main` or the records contract. A newcomer meets `factory/stops.jsonl` commits on `main` with no word about them in the first document they read.
2. **The README omits the contract command.** Its paragraph on the `python -m` commands names `factory.entry.check_documents`, and its *Where to look next* names `factory.entry.check_demos`. It does not name `factory.entry.contract`, which every story that changes a covered model runs (`CLAUDE.md`, *Checks*).
3. **The README contradicts itself.** *Getting started* says "Seven commands exist" (the seven `[project.scripts]` of `pyproject.toml`), and the next paragraph says "Beside the six console commands". The "six" predates this feature (`a7e1a4e6`, 2026-10-17, before F0019 added `factory-confine`), but it is a contradiction a newcomer reads, and S0010 touches the same paragraph.
4. **The operator guide's "The records contract" leaves out the command's refused side** (two or more arguments: the usage line on standard error, status 2), which S0009 pinned.

These go into one documents-only story, S0010. None of them misleads a user about behaviour in a way that loses data.

## 6 Decisions taken for the human

The feature's decisions 1 to 16 and the answers recorded in S0001 to S0006's journals are listed in the first acceptance (`done/F0021-A0001-acceptance.md`, section 6); the human merged that acceptance. New since then, to accept or revisit:

1. S0008: a git error while comparing (the remembered failing commit is not in the clone) clears `main_branch_failing`. The rule is "a stop never outlives a `main` the clone cannot check" (S0008's Interface and the comment in `_changes_only_stop_records`).
2. S0008: a `stops recorded` commit is still probed once (`make lint` on `main`) when the machine's items pass. Skipping that probe is left to "a later story" (`docs/decisions.md:626`). The cost is one `lint` run per stop event on a healthy machine, and the result is correct either way, since a red `main` only raises the standing stop again. I propose no story and would keep it as it is. Proposing one is the human's call.
3. Decision 10 ("from round 1 on") as it played out. S0008 and S0009 were each sent back once at round 0 for copied test helpers: four extra runs each, 40 % of their runs (section 8). The rule works as decided, since no story reached the round cap. If the human wants those runs saved too, the reviewer would pass helper copies on as notes from round 0. That is a change to the agent text, which only the human can decide.
4. Decision 6 still leaves S0001's round-cap answer uncounted: the human answered 8 times and the facts line says 7. Unchanged since the first acceptance.

Earlier tests changed by S0007 to S0009. I listed every test file with status `M` in the stories' commits and checked each against the reviewers' entries:

- S0007: none.
- S0008: all under the standing leave to move a shared test helper, as the reviewer's entry 17 names them:
  - `tests/application/test_disk_recorder.py`, `test_preflight_stale_main_stop.py`, `test_stale_branches.py`, `test_tick.py` and `test_tick_stop_records.py`;
  - `tests/conftest.py` (the shared `records` fixture) and `tests/human_clone.py` (`push_files`, with `push_file` delegating to it).
- S0009: `tests/entry/test_contract.py`, under the standing leave (`WRITTEN`, `USAGE` and `MainRow` moved to `tests/contract_support.py`), as the reviewer's entry 17 names it.

No earlier test changed without a leave named.

## 7 The slow checks

The project offers nothing beyond `make check` and `make mutants`: no image scan and no SBOM target. The disk is unchanged: `Disk now` (acceptance) and the previous record (start) both read `/work 985.7 GB free, 0.5 GB used; /state 0.0 GB used; /tmp 0.0 GB used`. There is no growth to explain.

`make test` took 40.6 s for 5177 tests. The slowest (`.reports/junit.xml`):

- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s.
- `tests/adapters/test_claude_runtime_confinement.py::test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result`: 3.1 s.
- Four more time-limit tests (`claude_runtime_confinement`, `make_commands`, `process`): 3.0 s each.

None of these is the feature's. `make mutants` still cannot finish the feature's 30 modules within its 540 s limit. Two runs reached 3286 of the 6233 mutants in the feature's modules, up from 2806 at the first acceptance.

## 8 Cost

92 runs, 95.9 min, $25.26 for nine stories. The first six cost 66 runs, 75.3 min and $20.63 (first acceptance, section 8). The three follow-ups:

| Story | Runs | Minutes | Cost | Runs per stage |
|---|---|---|---|---|
| S0007 | 6 | 3.3 | $0.77 | one each |
| S0008 | 10 | 10.2 | $2.47 | tests 2, doing 3, review 2 |
| S0009 | 10 | 7.1 | $1.39 | tests 2, doing 3, review 2 |

S0001 ($6.04, 15 runs) still stands out over the feature, for the reasons the first acceptance gave: three send-backs over its own tests and then the round cap. Among the follow-ups, S0008 and S0009 follow the same pattern. Each was sent back at round 0 only for copied test helpers (S0008 entry 9: four copies; S0009 entry 9: one). That cost a doing run that changed nothing, a tester run that made the move, a second doing run and a second review, which is 4 of their 10 runs. This is the rule as decided (decision 10, and 6.3 above), not a fault.

Human interventions: 7 questions answered (question 7), 0.2 h waited. All seven are in S0002 (1), S0003 (3) and S0004 (3). S0005 to S0009 needed the human not once. The story that needed the human most is still S0001, whose round-cap answer predates the field and counts 0 (decision 6). Among the counted ones, S0003's and S0004's questions were about behaviour the stories had to decide: a `raise_stop` without a readable status, and the `notebook_path` fallback and a smoke test's duplicate `run`.

## Proposed stories

- `F0021-S0010-the-readme-names-what-the-feature-built-and-counts-its-commands-right.md`: the four documentation findings of section 5, in one documents-only story. They are the README's missing clause on what F0021 built, the missing `python -m factory.entry.contract`, the README's "six" against "seven" console commands, and the contract command's refused side in the operator guide.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 stories proposed; make mutants 3139/3286 (145 survived and 2 timed out; 2947 of the feature's 6233 mutants were not reached in two 540 s runs, which went on from the first acceptance's results, so the score is partial)
   1 Scope: no gap. S0001 to S0006 still cover every scope bullet, and a grep finds no question or stall writer without its field. S0007 changed docs only. S0008 is the follow-up decision 1 left to a later story. S0009 added tests only. factory/stops.jsonl is not on origin/main yet because no stop has been raised in production since S0003.
   2 Feature smoke test: green. All nine archived stories, both acceptance reports, every cost line and pipeline.yml validate against the committed schemas, and the facts line computed from them equals the prompt's (7 questions answered, 0.2 h waited). Four real ticks from build_tick on a temporary bare remote, with the machine's items failing: main_branch_failing stays across two "stops recorded" commits and clears only after the human's commit to README.md. No detail is published. The contract regenerates byte for byte into a new nested folder.
   3 Mutants: none of the feature's own lines lacks a criterion. Its 10 survivors are equivalent (write_text encoding of ASCII JSON, indent with the byte test deselected, >= in _answered_at, a type-checker guard) or error texts. S0009's targets are killed, and S0008's lines have no survivor (domain.preflight 29/29 killed). The other 135 are in older code of the touched modules, not proposed.
   4 Noticed: test_stop_publisher.py keeps a copy of the shared records fixture (5 lines, left for the standing leave). SCHEMA_NAMES and SCHEMA_FILES are not a copy. The __main__ guard is uncovered, as in every entry module. The contract command's usage error is undocumented, taken into S0010. Skipping the probe of a stops-only commit was deferred, listed under 6.
   5 Docs: S0007 repaired A0001's five passages, and S0008's preflight text agrees across the three docs. Still open: the README names nothing the feature built and not the contract command, and it says "Seven commands exist" and then "the six console commands" (the six predates F0019). The operator guide does not give the contract command's refused side. All four go into S0010.
   6 Decisions: feature decisions 1 to 16 were listed in A0001, which the human merged. New since then: S0008 clears the stop on a git error while comparing. A stops-only commit is still probed once when the machine passes (I would keep that and propose no story). Decision 10's round-0 send-backs cost S0008 and S0009 four runs each. Decision 6 still counts 7 of the 8 answers. Every earlier test S0008 and S0009 changed falls under the standing helper-move leave the reviewers name, and none changed without a leave.
   7 Slow checks: nothing beyond make check and make mutants. Disk unchanged (0.5 GB used at start and now). make test took 40.6 s for 5177 tests; the slowest, the time-limited resume, took 5.0 s. make mutants still cannot finish the feature's 30 modules within its limit.
   8 Cost: 92 runs, 95.9 min, $25.26. S0001 still stands out ($6.04, 15 runs; round cap). The follow-ups: S0007 $0.77 (6 runs), S0008 $2.47 and S0009 $1.39 (10 runs each, 4 of them a round-0 send-back for copied test helpers). 7 questions answered, 0.2 h waited, all in S0002 to S0004, and S0005 to S0009 needed the human not once. The story that needed the human most is still S0001, whose uncounted round-cap answer predates the field.
