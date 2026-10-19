---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 247
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-19T02:18:26.239732Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-19T03:27:04.603800Z'
  stage: acceptance
  run: 34fd8e56421a4ac787eefe2268e91aee
stories: [F0021-S0001, F0021-S0002, F0021-S0003, F0021-S0004, F0021-S0005, F0021-S0006, F0021-S0007, F0021-S0008, F0021-S0009, F0021-S0010]
outcome: null
---

# Acceptance of The factory records what the human did

## Recommendation

Accepted. Every scope item of `feature.md` has its story and its code. The four follow-up stories (S0007 to S0010) repaired what the two earlier acceptances found, and S0010, the only story since the second acceptance, changed `README.md` and `docs/operator-guide.md` and nothing else. The feature smoke test is green end to end. It now also checks what the README and the operator guide promise against the commands. `make check` is green. Mutation testing has now reached 89 % of the feature's mutants (5565 of 6233), and every survivor in the feature's own lines is equivalent or an error text. No finding is worth a story, so I propose none.

## 1 Scope

None. The first acceptance (`done/F0021-A0001-acceptance.md`, section 1) mapped every scope bullet to S0001 to S0006, and the second (`done/F0021-A0002-acceptance.md`, section 1) placed S0007 to S0009 inside the feature. Since then only S0010 was archived. `git diff --stat` from the second acceptance's merge to `HEAD`, outside `factory/`, shows `README.md` (4 lines), `docs/operator-guide.md` (2 lines) and the human's own `planning/` and `docs/runs/` files (`56a7680e`, F0024's pre-check). No file under `src/` or `tests/` changed, so the code mapping of the earlier acceptances still holds. S0010 is inside the feature: it repairs the documents of S0003 and S0006's work for the newcomer. The out-of-scope items stay out.

`factory/stops.jsonl` is still not on `origin/main`, and `origin/main` has no `stops recorded` commit. No stop of the repository or the machine has been raised in production since S0003's image rebuild. The publish is therefore still unobserved in production, but the smoke test below runs it through real ticks.

## 2 Feature smoke test

The walk-through of the feature's purpose: a reader outside the factory learns the human's part from the records alone, the stop records on `main` tell the truth about `main`, and the documents a newcomer reads match the commands. It is the second acceptance's script (its section 2), extended by the contract command's refused side in part 3 and by part 4. The script:

1. reads the ten archived stories, all three acceptance reports and the pipeline definition;
2. validates each record against the committed schemas (with `jsonschema`, which is in the virtual environment only as another tool's dependency, so nothing is declared);
3. computes the waits and the facts line;
4. builds a real instance with `build_boundaries` and `build_tick` on a temporary bare remote, and runs four ticks with `main` probed red and the machine's items failing, a human commit in between;
5. regenerates the contract into a folder whose parent is missing, and calls the command with two arguments;
6. checks the README and the operator guide against `pyproject.toml` and the command's real usage line.

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
    refused = subprocess.run(["uv", "run", "-q", "python", "-m", "factory.entry.contract", str(Path(d) / "c"), "extra"],
                             capture_output=True, text=True)
    print(f"   two arguments: status {refused.returncode}; stderr {refused.stderr.strip()!r}; "
          f"folder written {(Path(d) / 'c').exists()}")

print("4. what the documents promise a newcomer matches the commands")
readme, guide = (root / "README.md").read_text(), (root / "docs/operator-guide.md").read_text()
scripts = [l.split("=")[0].strip() for l in (root / "pyproject.toml").read_text().split("[project.scripts]")[1]
           .split("\n[")[0].splitlines() if "=" in l]
print(f"   console scripts in pyproject.toml: {len(scripts)}; README says 'Seven commands exist': "
      f"{'Seven commands exist' in readme}; 'seven console commands': {'seven console commands' in readme}")
print(f"   README names: {[t for t in ('factory.entry.contract', 'factory/stops.jsonl', 'Human:', 'src/factory/contract/') if t in readme]}")
print(f"   operator guide quotes the command's usage line: {refused.stderr.strip() in guide}")
```

Output (the factory log lines of part 2 shortened after their first item):

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
   F0021-S0010: front matter valid; 0 questions answered, 0.0 h waited; causes []; 6 cost lines valid, 6 with denials (sum 0)
   facts line over the feature: 7 questions answered (question 7), 0.2 h waited
   done/F0021-A0001: front matter valid against acceptance-state
   done/F0021-A0002: front matter valid against acceptance-state
   in-progress/F0021-A0003: front matter valid against acceptance-state
   factory/pipeline.yml valid against pipeline-definition
2. the stops reach main as records, and a red main stays red across them
2026-10-19T03:25:47Z stop repository main_branch_failing: lint failed on main
2026-10-19T03:25:47Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
   tick 1: stopped preflight_failed; standing ['main_branch_failing', 'preflight_failed']
           main holds ['raised main_branch_failing']
2026-10-19T03:25:48Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
   tick 2: stopped preflight_failed; standing ['main_branch_failing', 'preflight_failed']
           main holds ['raised main_branch_failing', 'raised preflight_failed']
   the human pushes a commit that changes README.md
2026-10-19T03:25:48Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
2026-10-19T03:25:48Z stop cleared main_branch_failing
   tick 3: stopped preflight_failed; standing ['preflight_failed']
           main holds ['raised main_branch_failing', 'raised preflight_failed']
2026-10-19T03:25:48Z stop machine preflight_failed: tool:git: git is not on the PATH; ...
   tick 4: stopped preflight_failed; standing ['preflight_failed']
           main holds ['raised main_branch_failing', 'raised preflight_failed', 'cleared main_branch_failing']
   detail published: False; instances ['smoke']
   subjects on main: ['stops recorded', 'the human fixes main', 'stops recorded', 'stops recorded', 'seed']
3. the contract regenerates to the committed files
   contract: 5 schemas written
   identical to src/factory/contract: True ['acceptance-state.schema.json', 'cost-record.schema.json', 'pipeline-definition.schema.json', 'stop-record.schema.json', 'work-item-state.schema.json']
   versions: ['1.0']
   two arguments: status 2; stderr 'usage: python -m factory.entry.contract [<folder>]'; folder written False
4. what the documents promise a newcomer matches the commands
   console scripts in pyproject.toml: 7; README says 'Seven commands exist': True; 'seven console commands': True
   README names: ['factory.entry.contract', 'factory/stops.jsonl', 'Human:', 'src/factory/contract/']
   operator guide quotes the command's usage line: True
```

Green. The output shows the following:

- Every record validates against the committed schemas, including S0010's and this report's front matter.
- The facts line computed from the records equals this run's prompt line: 7 questions answered (question 7), 0.2 h waited.
- `main_branch_failing` stays standing across the factory's own `stops recorded` commits (S0008), and only the human's commit clears it. The `cleared` record reaches `main` at the next tick, and no detail is published.
- The contract regenerates byte for byte into a new nested folder. With two arguments the command exits 2, prints its usage line on standard error and writes nothing (S0009).
- The documents now say what S0010 promised: "Seven commands exist" matches the seven `[project.scripts]`, the README names the contract command, `factory/stops.jsonl`, the `Human:` line and `src/factory/contract/`, and the operator guide quotes the usage line the command really prints.

## 3 Mutation score

`make check` was green as I found it (`check: green`, `test: green (37.4 s)`, coverage 99.06 %). `make mutants` covers the 30 modules the feature's story commits changed, the same set as at the second acceptance, since S0010 changed no module. It went on from the results kept in `mutants/`. The first run made no progress in its 540 s:

```
⠴ 3286/13237  🎉 3139 🫥 0  ⏰ 2  🤔 0  🙁 145  🔇 0  🧙 0mutants: stopped after 540 s; the results below are partial, run it again to go on
```

That is where the second acceptance's second run had stopped. The only line before the progress line was mutmut's warning that seven `.costs.jsonl` files had changed and that it kept the cached results. To learn what lay behind the stall, I ran `uv run mutmut run` with module patterns on the feature's modules that were not yet checked, in six foreground runs of at most 530 s each. Each run had its own `TMPDIR` and the Makefile's `.git` clean-up, and every pattern was a feature module except `factory.application.handlers.*`, which also took in 523 mutants of other handlers. The targeted runs went fast: `domain.journal`, which no earlier run had reached, finished in one. After them, a second `make mutants` printed:

```
⠇ 6088/13237  🎉 5843 🫥 0  ⏰ 2  🤔 0  🙁 243  🔇 0  🧙 0mutants: stopped after 540 s; the results below are partial, run it again to go on
```

That second run checked only 6 more mutants of the feature's modules, all in `recovery`, whose mutants each run a large share of the suite. Not counting the 523 other handlers, the score over the feature's 30 modules is **5347 killed, 2 timeouts, 216 survived, of 5565 checked**. Another 668 are `not checked`: `application.stage` 405, `entry.wiring` 116, `application.recovery` 103, `application.costs` 30, and 14 more in six modules. The score is still partial, but it covers 89 % of the feature's mutants, up from 53 % at the second acceptance.

The survivors, grouped. I matched each surviving line to the commit that last changed it (`git blame` on the line from `uv run mutmut show`), for all 216, and read the diff of every one that falls in F0021's lines and of each new group:

- **The feature's own lines: 18 survivors, all equivalent or error texts, so no criterion is missing.**
  - The second acceptance's 10 are unchanged: `entry.contract.write_contract` (3, the encoding of ASCII JSON), `domain.contract.contract_schema` (3, `indent` with the byte-for-byte test deselected), `human_waits._answered_at` (`>=`), `AcceptanceService._waits` (a guard for the type checker), `domain.stops._require_scope_of_reason` and `cost_records_jsonl._refuse_constant` (error texts).
  - New, `application.stops.StopPublisher.publish` (S0003), 8 survivors. Three change `mkdir(parents=True)` to `parents=False` or leave it out: the publish writes `factory/stops.jsonl`, and `factory/` always exists on `main`, since it holds the pipeline definition. Five change the `encoding="utf-8"` and `newline="\n"` of `write_text`: the line is `model_dump_json` of an ASCII reason, event, scope and time plus the instance name, written on Linux, where the default newline is `\n` and Python's locale coercion makes UTF-8 the default. All are equivalent for every repository the factory runs on.
  - `AcceptanceHandOver.handle` mutant 52 (`role` becomes `None` in the `_show` call) blames to S0002, but only because S0002 added `state` to that call. The role picks the reviewer's entry for the description's findings (`acceptance_description`, F0009-S0004), so the gap in the test is F0009's, not this feature's.
- **The lines S0004 relies on, in older code:** `claude_runtime._resumed_result`, 3 survivors in the `time_limit` branch, where the first call's `permission_denials` are joined to the resume's (F0001-S0010). They do not affect the record: a `time_limit` run's cost record has `denials` and `denied_paths` set to `None` (decision 8), and the completed resume's join is killed (`test_completed_resume_adds_up_the_measures_and_joins_the_denials`).
- **Older code in the touched modules (the other 195):** `application.acceptance` (30 besides the one above), `claude_runtime` (22 more, including `_write_files`'s encoding), `recovery` (24), `entry.wiring` (20), `domain.acceptance` (16), `stage` (14), `closed` (13), `acceptance_reading` (10), `questions` (8), `stalls` (7), `tick` (6), `hand_over` (6), `domain.journal` (5, Markdown parsing from F0002), `post_texts` (4), `cost_records_jsonl._line_of_record` (3, `model_dump(mode="json")` from F0002), `preflight` (3), and one each in `paths`, `decisions` and `agent_runs`. As in the earlier acceptances, these predate the feature and are not proposed here.

## 4 What the stories noticed

The first two acceptances collected S0001 to S0009 (their sections 4). From S0010:

- Tester (entry 5), coder (entry 7), reviewer (entry 9) and documenter (entry 11): nothing noticed. The coder's "Noticed, not touched: none", and the documenter "noticed no stale text outside this story".
- Smoke tester (entry 13), a note that was not a finding: the README's summary sentence now chains "and the cost records with the bill, and the records the human can read from outside: …". Also, "It is no console script, and `make check` does not run it" now follows two `python -m` commands. I read both as a newcomer. The first is clumsy but says the right things. The second still holds for both commands: neither is a console script, and `make check` runs neither, although it does run a test that compares the committed schemas. So neither misleads. A wording change is left to the next documenter who touches that paragraph, and I propose no story for it.

Still standing from the second acceptance, unchanged and left as it decided:

- `tests/application/test_stop_publisher.py:43` still holds an identical copy of the `records` fixture in `tests/conftest.py:204`. The standing leave lets the next tester who touches that module remove it.
- The uncovered `__main__` guard of `entry/contract.py:41`.
- `make duplicates`' "3 gone" (`security/duplicates-baseline.txt` is the human's file).

## 5 The documentation as a whole

I read `README.md` and `docs/` from the top as a newcomer. The four findings of the second acceptance are repaired:

- the README's summary names the four things the feature built and points to "The records contract";
- "seven console commands" agrees with "Seven commands exist" and with the seven `[project.scripts]`;
- `factory.entry.contract` appears once in the README;
- the operator guide's "The records contract" gives the refused side (`docs/operator-guide.md:814`).

The project guide's own passage on the contract command (`docs/project-guide.md:550`, "returns 2 with a usage line for more than one argument") agrees with the operator guide and with the command. No passage still says "six" commands. The operator guide's opening paragraph lists the six commands besides `factory-health`, as the README does. `python -m factory.entry.check_documents` prints `documents ok`, and part 4 of the smoke test checks the repaired passages against the code. Findings: none. The one remark on wording is under 4.

## 6 Decisions taken for the human

The feature's decisions 1 to 16 and the answers in S0001 to S0006's journals are listed in the first acceptance (section 6). The decisions of S0007 to S0009 are in the second (section 6), and the human merged both. S0010 took no decision: it needed the human not once, and its journal records no default. Still open for the human, from the second acceptance and unchanged:

1. A stops-only commit is still probed once (`make lint` on `main`) when the machine's items pass (`docs/decisions.md:626`, "left to a later story"). I would keep that, and I propose no story.
2. Decision 6 still counts 7 of the human's 8 answers: S0001's round-cap answer predates the `blocked` field.
3. Decision 10's round-0 send-backs for copied test helpers cost S0008 and S0009 four runs each. Changing that is a change to the reviewer's agent text.

New, for the human to weigh:

4. `make mutants` cannot finish this feature. Its 30 modules hold 6233 mutants, and the `stage`, `recovery` and `entry.wiring` mutants each run a large share of the 5177 tests. Its first run here made no progress in 540 s, and it moved on only after module-pattern runs of mutmut had cleared the faster modules (section 3). Whether an acceptance may run mutmut with module patterns, or whether `make mutants` should order or split its modules, is the human's to decide. The `Makefile` is outside this feature, so I propose no story here.

Earlier tests changed: S0010 changed no test file (its diff outside `factory/` is `README.md` and `docs/operator-guide.md`, and the reviewer's entry 9 says "Earlier tests: none"). No earlier test changed without a leave named.

## 7 The slow checks

The project offers nothing beyond `make check` and `make mutants`: no image scan and no SBOM target. The disk is unchanged. `Disk now` (acceptance) and the previous record (start) both read `/work 985.6 GB free, 0.5 GB used; /state 0.0 GB used; /tmp 0.0 GB used`, so there is no growth to explain. The `mutants/` folder lies under `/work` and is ignored by git.

`make test` took 37.4 s for 5177 tests. The slowest, from `.reports/junit.xml`:

- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s.
- `tests/test_fault_paths_7_to_13.py::test_acceptance_container_lost_in_review_reruns_once_and_books_result[refused]`: 3.2 s.
- `tests/adapters/test_claude_runtime_confinement.py`: three time-limit tests of 3.0 to 3.1 s.

None of these is the feature's. `make mutants` is the slow check that does not fit: two runs of 540 s plus six module-pattern runs reached 5565 of the feature's 6233 mutants (section 3 and 6.4).

## 8 Cost

98 runs, 98.3 min, $25.88 for ten stories. The first nine cost 92 runs, 95.9 min and $25.26 (second acceptance, section 8). S0010 cost 6 runs, 2.4 min and $0.62, one run per stage, the cheapest story of the feature. Its tester and coder each ended at once with "nothing changed", as its criterion 1 asked.

| Story | Runs | Cost |
|---|---|---|
| S0001 | 15 | $6.04 |
| S0002 to S0006 | 51 | $14.59 |
| S0007 | 6 | $0.77 |
| S0008 | 10 | $2.47 |
| S0009 | 10 | $1.39 |
| S0010 | 6 | $0.62 |

S0001 still stands out, for the reasons the first acceptance gave: three send-backs over its own tests, then the round cap. S0008 and S0009 each spent 4 of their 10 runs on a round-0 send-back for copied test helpers (6.3).

Human interventions of the stories: 7 questions answered (question 7), 0.2 h waited. All seven are in S0002 (1), S0003 (3) and S0004 (3), and S0005 to S0010 needed the human not once. The story that needed the human most is S0001. Its round-cap answer predates the field and counts 0 (decision 6). Among the counted questions, S0003's and S0004's were about behaviour the stories had to decide: a `raise_stop` without a readable status, the `notebook_path` fallback, and a smoke test's duplicate `run`.

## Proposed stories

None. Every finding of the earlier acceptances is repaired. The survivors in the feature's own lines are equivalent or error texts. The remaining remarks (the README's wording, the copied fixture, `make mutants`' reach) are either left to the standing rules or outside the feature, and are listed for the human under 4 and 6.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed; make mutants 5347/5565 (the feature's 30 modules: 216 survived, 2 timed out, 668 of 6233 not checked; two make mutants runs plus six module-pattern mutmut runs; make mutants' own progress line read 5843/6088, which includes 523 mutants of other handlers)
   1 Scope: no gap. Since the second acceptance only S0010 was archived, and it changed README.md and docs/operator-guide.md only. The code mapping of S0001 to S0009 still holds. factory/stops.jsonl is still not on origin/main, because no stop has been raised in production since S0003.
   2 Feature smoke test: green. All ten stories, the three acceptance reports, every cost line and pipeline.yml validate against the committed schemas, and the facts line equals the prompt's (7 questions answered, 0.2 h waited). Over four real ticks, main_branch_failing survives the factory's own "stops recorded" commits and clears only on the human's commit. No detail is published. The contract regenerates byte for byte; with two arguments it exits 2, prints its usage line and writes nothing. README and operator guide now match pyproject.toml and the command.
   3 Mutants: 89 % of the feature's mutants are now checked (53 % before). The first make mutants run made no progress in 540 s; it moved on only after module-pattern runs. All 18 survivors in F0021's own lines are equivalent or error texts. The 8 new ones are StopPublisher.publish's mkdir parents and write_text encoding/newline. The rest are older code.
   4 Noticed: S0010's stages noticed nothing. The smoke tester found two awkward README sentences; they mislead no one and are left to the next documenter. Still left as before: the copied records fixture in test_stop_publisher.py, the uncovered __main__ guard, and "3 gone" in duplicates.
   5 Docs: the second acceptance's four findings are repaired. The project guide, the operator guide and the README agree on the contract command and the count of seven commands. documents ok. No finding.
   6 Decisions: S0010 took none and changed no test. Still open from A0002: the probe of a stops-only commit, decision 6's uncounted round-cap answer, and decision 10's round-0 send-backs. New: make mutants cannot finish this feature within its limits; whether to allow module patterns or to order or split the target is the human's call (the Makefile is outside the feature).
   7 Slow checks: nothing beyond make check and make mutants. Disk unchanged (0.5 GB used at start and now). make test took 37.4 s for 5177 tests; the slowest is the 5.0 s time-limited resume test, not this feature's.
   8 Cost: 98 runs, 98.3 min, $25.88. S0010 was the cheapest story: 6 runs, $0.62. S0001 still stands out ($6.04, 15 runs; round cap). 7 questions answered, 0.2 h waited, all in S0002 to S0004; S0005 to S0010 needed the human not once. S0001 needed the human most, but its answer predates the field and counts 0.
