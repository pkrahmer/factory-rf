---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 338
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T05:08:55.187596Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T05:11:59.780037Z'
  stage: acceptance
  run: ab943626c888415aa0c0b498ac8c79b0
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-20T05:13:19.589714Z'
  stage: done
stories: [F0035-S0001]
outcome: accepted
---

# Acceptance of Smoke tests never pass -q to pytest

## Recommendation

accepted. The one story did exactly what `feature.md` promised: intake's *Stage* step 2 carries the general `-q` rule, the human's change 1 put the project-specific rule into `factory/story-form.md` on `main` (9333e74f), and `make check` is green. The feature smoke test below is green end to end, and nothing the stories noticed or the docs show is worth a story.

## 1 Scope

none. The Scope has three items and S0001 covers each one. `claude/agents/intake.md:53` (step 2) ends with the Interface's sentences. `tests/test_claude_agent_texts_smoke_pytest.py` is new and pins the sentence, where it sits and that only intake has it. `docs/project-guide/agents.md:248` and `docs/decisions.md:869` were written from the docs criterion. The Goal also asks for the human's change 1 on `main`: it is there, in commit 9333e74f, at `factory/story-form.md:19`. The merge 10fb130f touches nothing outside the scope: one line in `claude/agents/intake.md`, the new test, the two documents and the archived story. Nothing in Out of scope was touched. There is no code check, `template/` holds only `CLAUDE.md`, `Makefile` and `factory/pipeline.yml` (no `pyproject.toml` and no story form, as decision 3 says), and the smoke tester, the demo and the stories F0022-S0005 and F0023-S0004 are unchanged. No paid call was made.

## 2 Feature smoke test

The feature's purpose, end to end. First, pytest's behaviour that the rule exists for. Then intake as an agent home installs it and the factory reads it, through `FrontmatterAgentDefinitionReader`, the reader the wiring uses. Then the form the human drafts from. Last, the form check, which still passes a story after the form change.

Command (`bash smoke.sh` with `D` set to a self-removing `mktemp -d` folder):

```bash
set -u
cd /work/checkout
m=tests/test_claude_agent_texts_smoke_pytest.py
echo "== 1 the premise: pyproject's addopts ="; grep -n '^addopts' pyproject.toml
echo "-- pytest as configured, last line:"; uv run pytest -p no:cacheprovider "$m" 2>&1 | tail -1
echo "-- pytest with a second -q, last line:"; uv run pytest -q -p no:cacheprovider "$m" 2>&1 | tail -1
echo "-- summary lines at -qq:"; uv run pytest -q -p no:cacheprovider "$m" 2>&1 | grep -cE '^[0-9]+ passed in '
echo "== 2 intake as installed in an agent home"
mkdir -p "$D/home/agents"; cp claude/agents/*.md "$D/home/agents/"
uv run python - "$D/home" <<'EOF'
import sys
from pathlib import Path
from factory.adapters.agent_files import FrontmatterAgentDefinitionReader
from factory.domain.sections import section_text
r = FrontmatterAgentDefinitionReader(Path(sys.argv[1]))
mark = "passes no `-q` when the project's pytest configuration already sets one"
for name in r.names():
    print(name, r.read(name).instructions.count(mark))
stage = section_text(r.read("intake").instructions, "Stage") or ""
step = [l for l in stage.splitlines() if l.startswith("2. ")]
print("step 2 lines:", len(step), "| ends:", step[0][-60:])
EOF
echo "== 3 the story form the human drafts from"
grep -c -F 'A block that runs pytest never passes `-q`' factory/story-form.md
echo "== 4 the form check still passes the archived story"
uv run factory-check-story factory/features/F0035-smoke-tests-never-pass-q-to-pytest/done/F0035-S0001-intake-asks-about-a-smoke-test-that-passes-q-to-pytest-a-second-time.md; echo "exit $?"
```

Output:

```
== 1 the premise: pyproject's addopts =
99:addopts = "-q --strict-markers"
-- pytest as configured, last line:
9 passed in 0.02s
-- pytest with a second -q, last line:
.........                                                                [100%]
-- summary lines at -qq:
0
== 2 intake as installed in an agent home
acceptance-reviewer 0
coder 0
documenter 0
intake 1
reviewer 0
smoke-tester 0
tester 0
step 2 lines: 1 | ends: nts or names it cannot be met. Such a command is a question.
== 3 the story form the human drafts from
1
== 4 the form check still passes the archived story
factory/features/F0035-smoke-tests-never-pass-q-to-pytest/done/F0035-S0001-intake-asks-about-a-smoke-test-that-passes-q-to-pytest-a-second-time.md: ok
exit 0
```

Green. The premise holds: a second `-q` removes the summary line. The installed intake carries the rule once, at the end of step 2, and no other agent carries it. The form holds the human's sentence, and the form check still accepts a story. The one step this smoke test cannot show is intake actually asking about a story that breaks the rule, because that is a paid run (Out of scope: "Every paid call").

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- Coder (entry 7): "the template/ copies of the agent files, if any, are out of scope". `template/` holds no agent files, so nothing is left behind.
- Documenter (entry 11): no stale text. Reviewer (entry 9): no remarks beyond its findings, and it had none.
- The coder's record `duplicates: 5 new, 33 known, 3 gone` (entry 7) still shows in my run today. The 5 new findings are four similar-code blocks between `claude_runtime` and `opencode_runtime` and an unused `ManualWaiter` in `src/factory/adapters/clock.py`. The 3 gone ones are `ManualClock`, `advance` and `data`. They come from code that F0035 did not touch, since the feature changed nothing under `src/`. So the baseline in `security/duplicates-baseline.txt` has drifted from `main` somewhere else. Nobody owns this. It is the human's to give to the feature that brought these findings, and not a story for F0035.
- My own observation: the rule names only `-q`, not its long form `--quiet`, which has the same effect. No smoke test on record has used `--quiet`. I propose no story for it.

## 5 Documentation

none. A newcomer reading it hears the rule in three places, and all three agree. `docs/project-guide/agents.md:248` describes intake's general rule, with the four configuration files. `docs/decisions.md:869` gives the decision, its reason and what it rejected. `factory/story-form.md:19` gives the project's own wording, which names `pyproject.toml`. `README.md` and `docs/operator-guide.md` need nothing, since nothing the operator does changed. Outside the human's files (`docs/runs/` repeats the history), no document holds a smoke test example that passes `-q` to pytest.

## 6 Decisions taken for the human

The four decisions in `feature.md`, to accept or revisit:

1. The rule goes into intake's *Stage* step 2, not into its *Lessons*, because `tests/test_claude_agent_texts.py` pins the Lessons lines and a Lessons line would change another story's test.
2. In intake the rule is general. It applies when the project's own pytest configuration sets `-q` (`addopts` in `pyproject.toml`, `pytest.ini`, `setup.cfg` or `tox.ini`).
3. `template/` is not changed. It has no pytest configuration and no story form.
4. This repository's story form names `pyproject.toml` directly (the human's change 1).

Story journals: no question was asked, and no default was taken beyond the Interface. Earlier tests: the reviewer (entry 9) names none changed, because the diff only adds `tests/test_claude_agent_texts_smoke_pytest.py`, and I confirmed this in the merge 10fb130f. No finding.

## 7 Slow checks

none. The project offers nothing beyond `make check` (`make mutants` is check 3's and not run). `make check` is green: 6103 tests, branch coverage 99.14 %, `test: green (40.7 s)`. The slowest tests in `.reports/junit.xml` predate the feature and wait for time limits:

- `tests.adapters.test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit` (5.0 s)
- `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` (5.0 s)
- two rows of `tests.adapters.test_opencode_sudo_time_limit` (4.5 s each)

The feature's nine tests take 0.001 to 0.002 s each. Disk: at `acceptance`, /work had 970.1 GB free and 0.5 GB used, /state 0.0 GB used and /tmp 0.0 GB used. That is the same as at the `start` record, so there is no growth.

## 8 Cost

One story: 6 runs, 3.6 min, 32 turns, 102816 tokens in (479294 more from cache), 9417 out, $0.90. No run stands out. Each stage ran once, with no rework round. The tester was the most expensive run ($0.20, 73 s wall time, most of it in `make test`), the coder took 66 s, and intake was the cheapest ($0.07, 13 s). Human interventions: 0 questions answered and 0.0 h waited. Before the story, the human's change 1 was made on `main`, as the feature planned it.

## Proposed stories

none. No finding is worth a story inside this feature's scope. The duplicates-baseline drift under 4 belongs to another feature's code.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1. Scope: none. S0001 covers all three scope items. The human's change 1 is on `main` (9333e74f, `factory/story-form.md:19`). Nothing in Out of scope was touched, and `template/` has no pytest configuration and no story form.
   2. Feature smoke test: green. With this repository's `addopts`, a second `-q` drops pytest's summary line (0 summary lines). The installed intake, read through `FrontmatterAgentDefinitionReader`, carries the rule once, at the end of step 2, and no other agent carries it. The story form holds the human's sentence, and `factory-check-story` still passes the archived story (exit 0). The script and its output are in the report.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the coder's note about `template/` copies of the agent files needs nothing, because there are none. The documenter and the reviewer noticed nothing. Unowned and outside F0035: `make duplicates` shows 5 new and 3 gone findings against the baseline (`claude_runtime`/`opencode_runtime` similar code, `ManualWaiter`) in code this feature did not touch. Minor: the rule names `-q` but not `--quiet`.
   5. Documentation: none. `docs/project-guide/agents.md:248`, `docs/decisions.md:869` and `factory/story-form.md:19` agree.
   6. Decisions for the human: the feature's decisions 1 to 4 are listed. No story question was asked and no default was taken. No earlier test was changed; the merge only adds a test file.
   7. Slow checks: there are none beyond `make check`, which is green (6103 tests, 99.14 % coverage, 40.7 s). The slowest tests are the existing time-limit tests at about 5 s. Disk did not change since the start record.
   8. Cost: 6 runs, 3.6 min, $0.90, no rework. No run stands out; the tester was the largest at $0.20. 0 questions and 0.0 h waited.
3. factory: done (pull request merged); cost: 1 runs, 3.0 min, 18 turns, 41684 tokens in (609838 more from cache), 9286 out, $0.64
