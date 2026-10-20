---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 325
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T03:35:27.978831Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T03:39:32.049426Z'
  stage: acceptance
  run: f35f9348ca5e46a487015b3c11ba1ca4
stories: [F0036-S0001]
outcome: null
---

# Acceptance of No stage writes a .claude folder at any depth

## Recommendation

accepted. The one story did what `feature.md` promised. `PROTECTED_PATHS` holds `*/.claude/*` second. Both refusals now cover a nested `.claude/` in every role of the real `factory/pipeline.yml`: the `factory-guard` hook refuses it with the root's words, and the undo removes it after the run, even when a shell rename put it there. The three docs say the same as the code. `make check` is green and nothing of weight is left behind, so no story is proposed.

## 1 Scope

None. Every Scope item has its change in S0001 (merge `28bb97da`):

- `src/factory/domain/write_paths.py:23` holds `"*/.claude/*"` right after `.claude/*`.
- `tests/domain/test_write_paths.py` has only the rename to `..._twelve_patterns` and the new second item.
- `tests/domain/test_nested_claude_paths.py` and `tests/application/test_undo_nested_claude.py` are new.
- `docs/operator-guide.md`, `docs/project-guide/write-guard.md` and `docs/decisions.md` were changed.

One file is outside the Scope list: `tests/undo_support.py`. The story's Interface allowed it, and it is the standing-leave move of `tests/application/test_undo.py`'s helpers. Everything under Out of scope is untouched:

- `factory.domain.confinement` and `factory-confine`;
- `~/.claude`;
- R14 in `claude/agents/`;
- a bare `.claude` file or link;
- `claude/` without the dot.

The Goal is reached. `refusal` judges both the hook (`src/factory/adapters/claude_guard.py`, `judge`) and the undo, and both take their protected paths from `WritePathService.at` (`src/factory/application/write_paths.py:44`, `list(PROTECTED_PATHS)`). So the one constant reaches both, as the feature said.

## 2 Feature smoke test

The walk a human would do after this feature: take every role's real write paths from `factory/pipeline.yml`, and try to write a nested `.claude/` under each. Part 1 sends each write to the real `factory-guard` CLI as a Claude Code `Write` payload. Part 2 has the undo clean up after a coder run on a real bare remote and clone. Part 2 includes a write the hook never sees: a folder written elsewhere and renamed into `src/pkg/.claude` by a shell route. Both scripts ran from `$TMPDIR`, with `uv run python -I <script>`, from the repository root.

Part 1 (the hook), script:

```python
import json, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.agent_runs import GuardSettings
from factory.domain.write_paths import PROTECTED_PATHS, expand_write_paths
definition = RuamelPipelineDefinitionReader().parse(Path("factory/pipeline.yml").read_text())
item = "factory/features/F0099-x/in-progress/F0099-S0001-y.md"
cases = {"coder": [...], "tester": [...], "documenter": [...], "acceptance-reviewer": [...], "intake": [...]}  # the paths printed below
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "checkout"; root.mkdir()
    for role, paths in cases.items():
        wp = expand_write_paths(definition.roles[role].write_paths, work_item_path=item, feature_path="factory/features/F0099-x")
        settings = Path(tmp) / f"{role}.json"
        settings.write_text(GuardSettings(root=root, write_paths=wp, protected_paths=list(PROTECTED_PATHS)).model_dump_json())
        for p in paths:
            payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(root / p)}})
            r = subprocess.run(["uv", "run", "factory-guard", "--settings", str(settings)], input=payload, capture_output=True, text=True)
            print(f"{role:20} {p:55} exit {r.returncode} {r.stderr.strip() or 'allowed'}")
```

Output:

```
coder                src/.claude/skills/x/SKILL.md                           exit 2 src/.claude/skills/x/SKILL.md is owned by the human; a change there is a question.
coder                template/.claude/settings.json                          exit 2 template/.claude/settings.json is owned by the human; a change there is a question.
coder                claude/.claude/agents/a.md                              exit 2 claude/.claude/agents/a.md is owned by the human; a change there is a question.
coder                claude/agents/coder.md                                  exit 0 allowed
coder                src/.claudex/n.md                                       exit 0 allowed
coder                src/x.claude/n.md                                       exit 0 allowed
coder                src/a.py                                                exit 0 allowed
tester               tests/.claude/commands/c.md                             exit 2 tests/.claude/commands/c.md is owned by the human; a change there is a question.
tester               tests/test_a.py                                         exit 0 allowed
documenter           docs/.claude/settings.json                              exit 2 docs/.claude/settings.json is owned by the human; a change there is a question.
documenter           docs/guide.md                                           exit 0 allowed
acceptance-reviewer  factory/features/F0099-x/backlog/.claude/skills/s.md    exit 2 factory/features/F0099-x/backlog/.claude/skills/s.md is owned by the human; a change there is a question.
acceptance-reviewer  factory/features/F0099-x/backlog/F0099-S0002-z.md       exit 0 allowed
intake               .claude/skills/x/SKILL.md                               exit 2 .claude/skills/x/SKILL.md is owned by the human; a change there is a question.
```

Part 2 (the undo). The script builds `Boundaries` on a real `GitCli` clone of a `make_remote` bare remote, with the same adapters as `tests/conftest.py`'s `boundaries` fixture. It claims a stage through `tests/undo_support.py`'s `start_stage`, with the coder's write paths read from `factory/pipeline.yml`. It writes the files below, then renames `src/staging` to `src/pkg/.claude` as a shell would, and runs `UndoService` through `undo_stage`. Output:

```
coder write paths (factory/pipeline.yml): ['src/*', 'image/*', 'template/*', 'claude/*']
deleted: ['src/.claude/skills/x/SKILL.md', 'src/pkg/.claude/skills/y/SKILL.md', 'template/.claude/settings.json']
src/.claude/skills/x/SKILL.md            gone
template/.claude/settings.json           gone
src/pkg/.claude/skills/y/SKILL.md        gone
src/.claudex/notes.md                    kept
claude/agents/extra.md                   kept
src/a.py                                 kept
```

Green. Every nested `.claude/` is refused in every role, with the root's text, and every look-alike is allowed. The undo also catches the write that came by rename, which the hook cannot see.

`make check` as found: `test: green (41.1 s)`, `check: green` (6083 tests, coverage 99.14 %).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- The coder ("Noticed, not touched: nothing"), the reviewer (no remarks beyond its checks) and the documenter ("Stale text I saw and did not touch: none") left nothing open.
- The coder's record `duplicates: 5 new, 33 known, 3 gone` was owned by nobody. I ran `make duplicates` again, and the 5 are not this feature's:
  - four similar-code pairs between `factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime`;
  - the dead-code `ManualWaiter` in `src/factory/adapters/clock.py`.

  All of them come from F0020's modules, and its acceptances already name them. The one line this feature changed adds no finding. They are left to the human's baseline or to an F0020 follow-up, not to a story in this feature.
- The documenter said it did not read `feature.md` and took decisions 1, 2 and 4 from the docs criterion. The decisions entry still matches the feature's decisions.

## 5 Documentation

None of weight. I read *A project's own skills* (`docs/operator-guide.md:995-1001`), the protected-paths list at `docs/operator-guide.md:896`, *Protected paths and the refusal* and *The undo* (`docs/project-guide/write-guard.md`) and both decision entries (`docs/decisions.md:770` and `docs/decisions.md:852-859`). They agree with each other and with the code:

- "twelve patterns" and the order match `PROTECTED_PATHS`;
- the operator guide's list names `.claude/` without a place;
- the F0022 open point now names the new entry.

`README.md` needs nothing. One small redundancy in `docs/operator-guide.md:999`: it first says "`.claude/*` is a protected path that no stage writes" and then, in the next sentence, "`.claude/` is protected at any depth (`.claude/*` and `*/.claude/*`)". Read on their own, the first words still suggest the root only. The next sentence corrects them, so a reader is not misled, and a story is not worth it. The documenter may merge the two sentences the next time it touches that section.

## 6 Decisions taken for the human

From `feature.md`, for the human to accept or revisit:

1. The pattern is `*/.claude/*`. A path that is only `.claude`, with nothing below it, is not protected, at the root or nested. So a file or a symbolic link named `src/.claude` may still be written, and the undo keeps it (`src/.claude -> False` in criterion 2). Whether Claude Code would load a nested `.claude/` at all was never checked; the feature made that question moot for folders, but not for such a link.
2. The kernel's targets are unchanged. Inside a folder a write path opens, a nested `.claude/` is refused only by the hook (Claude Code runs) and removed by the undo (every run, opencode included). Part 2 above shows that the undo alone catches a shell-route write.
3. The leave to change `tests/domain/test_write_paths.py` beyond the standing leave: the test was renamed to `test_the_protected_paths_are_the_engines_twelve_patterns`, and its tuple gained `"*/.claude/*"`.
4. R14 in the seven shipped agents keeps its words.

No journal records a question or a default.

Earlier tests changed, each with its leave:

- `tests/domain/test_write_paths.py`: under the feature's decision 3 (reviewer entry 9). The diff of merge `28bb97da` has only the rename and the one tuple item.
- `tests/application/test_undo.py`: under the standing leave to move a shared test helper (`CLAUDE.md`, *Tests*; tester entry 5, reviewer entry 9). `_pipeline`, `_start`, `_undo` and their constants moved to `tests/undo_support.py`. Every test keeps its name. The diff removes one assertion line, `assert git.push(BRANCH) == "pushed"`, which moved into `start_stage`.

No earlier test was changed without a named leave.

## 7 Slow checks

Beyond `make check`, the project offers `make duplicates` (a record) and `make documents` (the docs stage's check). `make duplicates` gives `duplicates: 5 new, 33 known, 3 gone`, none of them this feature's (see 4). No image scan and no SBOM. Disk: `/work` 0.5 GB used at start and now, `/state` and `/tmp` 0.0 GB at both, so there is no growth.

From `.reports/junit.xml`: the slowest tests are not this feature's.

- `test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`, 5.0 s;
- `test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit`, 5.0 s;
- the two `test_opencode_sudo_time_limit` rows, 4.5 s each.

This feature's tests take 0.17 s together, the undo test included.

## 8 Cost

6 runs, 5.2 min, 41 turns, 134562 tokens in (820600 more from cache), 15773 out, $1.34, all of it S0001. The tester stands out within the story: $0.44 of the $1.34, 120 s and 12 turns. Its entry 5 says why: besides the three tests, it moved `tests/application/test_undo.py`'s helpers and 13 constants to `tests/undo_support.py`, and it ran `make test` to see the 8 intended failures. The coder took 70 s but only 17 model seconds; the rest was `make check`.

Human interventions: 0 questions answered, 0.0 h waited. No story needed the human.

## Proposed stories

None. No finding needs a change. The leftover duplicates (4) belong to F0020's modules, and the redundant sentence (5) does not mislead.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed

   1. Scope: no gaps. `*/.claude/*` is second in `PROTECTED_PATHS` (`src/factory/domain/write_paths.py:23`). The tests and the three docs match Scope. `tests/undo_support.py` is the one file outside the Scope list, and the standing leave allowed it. Out of scope is untouched.
   2. Feature smoke test: green. I ran the real `factory-guard` CLI against every role's write paths from `factory/pipeline.yml`. It refused a nested `.claude/` with exit 2 and the root's text, and allowed `.claudex`, `x.claude` and `claude/`. `UndoService` on a real bare remote, with the coder's write paths, deleted all three nested `.claude/` files, the one renamed in by a shell route included, and kept the rest. `make check` green.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the stories left nothing open. The coder's `duplicates: 5 new` record are F0020's runtime pairs and `ManualWaiter`, not this feature's.
   5. Docs: consistent with each other and with the code. One redundant, non-misleading sentence in `docs/operator-guide.md:999`.
   6. Decisions: the feature's 1 to 4 are listed for the human, including that a bare `src/.claude` file or link stays writable. Two earlier tests were changed: `tests/domain/test_write_paths.py` under decision 3, and `tests/application/test_undo.py` under the standing leave. Neither was changed without a leave.
   7. Slow checks: there is no scan or SBOM. `make duplicates` has nothing new from this feature. Disk shows no growth (0.5 GB used on /work at start and now). The slowest tests are 5.0 s and come from other features.
   8. Cost: $1.34 over 6 runs. The tester was the largest share ($0.44), because it moved the shared undo helpers. 0 questions answered, 0.0 h waited.
