# Pre-check F0022, round 2: the feature after its edits

The feature `F0022-a-project-brings-its-own-skills-and-agents` after the fix agents' edits and the human's answers of 2026-10-19 (decision 17), checked against today's `main` (F0020-S0001 to S0005 and F0025 merged) and `docs/project-guide/README.md`'s list of guide files. Both stories were prototyped together in a copy and the whole suite run in a throwaway container of `factory-self-factory`: only the five failures that the container also gives on unpatched `main`. Per story: `F0022-S0001-2.md`, `F0022-S0002-2.md`.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 | accepted (`tests`) | no stop expected; two optional edits (one Interface line without a criterion, the guide's index) |
| S0002 | accepted (`tests`) | the smoke tester stops on block 3 (no state directory); two docs criteria name the wrong section |

## Round 1's verdict, applied

All of it is in `feature.md`: decision 14's S0001 leave with "All four keep their names", change 1's fallback through the volume, change 2's instance, `drwxr-sr-x` and "the demo's instance (not `self`)", decisions 10, 11, 12 and 16 as worded. The stories agree with the decisions; no criterion is referred to by an old number.

## Findings

1. S0002's smoke block 3 builds `OpencodeRuntime(..., d / "state")` without making `state`. F0020-S0004's human answer 5 settled that the runtime does not create its state directory, and today's code fails with `cannot write the state directory`. The fix is in `F0022-S0002-2.md`, edit 1. This is required.
2. S0002's docs criterion names *The shipped agents and settings* for the agent-home paragraph, which is in *The agent runs as a second user*. It also names *The seven agents* for `LEFT_OUT_TOOLS`, whose refusal text is in *The opencode runtime*. Fixes: `F0022-S0002-2.md`, edits 2 and 3.
3. Decision 14, S0002 bullet: its conditional sentence on F0020-S0004's test is moot, because that test uses `NotebookEdit`. Optional rewording below.
4. Decision 16 still holds. F0020-S0006 to S0008 are not merged yet, and no merged F0020 test reads `agent_definitions` from `build_boundaries(...)`. If F0022 is built before F0020-S0008, the S0001 wiring change is the same one line.

Aside, outside F0022: F0020-S0006's smoke test (in its `backlog/`) also does `mkdir "$d/work"` and then builds `OpencodeRuntime(str(d / "opencode"), d / "state")`, so it probably fails the same way. Not run here.

## Verdict

Ready to build once S0002's smoke block 3 makes `$d/state` (required); the docs and wording edits are recommended. No change to `feature.md` is required.

Optional edit, decision 14, the S0002 bullet: replace "If F0020-S0004's test of a tool outside `TOOL_NAMES` uses `Skill` as its example, that one row's tool becomes `NotebookEdit` and its expected text with it." with:

```markdown
F0020-S0004's test of a tool outside `TOOL_NAMES` uses `NotebookEdit` and stays as it is.
```
