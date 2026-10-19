# Pre-check F0029, round 1: the feature, its human's changes and its decisions

I checked `F0029-opencode-starts-in-a-fresh-home-and-no-test-races-its-time-limit` and its two stories against these sources:

- v1.1's roles and forms, `factory/pipeline.yml` and `CLAUDE.md` (*Tests*, the bullet human's change 2 replaces);
- the image (`Dockerfile`, `entrypoint.sh`, `compose.yml`, `sudoers-factory-agent`);
- `src/factory/entry/confine.py` and `src/factory/adapters/opencode_runtime.py`;
- every image test, and every test under `tests/` with a time limit of five seconds or less.

The stories' results are in `F0029-S0001-1.md` and `F0029-S0002-1.md`.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 the folder | question: criterion 2 does not pin "right after the users' `RUN`" (edit 1) | none; every image test stays green, and both smoke blocks give their lines |
| S0002 the limits | question: criterion 6 is a command, not a test (edit 2) | none; one 5-second row with two calls is left out (edit 1, and edit A here) |

## What I ran

Throwaway containers of `factory-self-factory` (`--network none --cpus 1`, a copy with LF line endings, pytest and xdist on `PYTHONPATH`), one at a time.

**The Dockerfile change of S0001.** All ten modules that read the Dockerfile stay green with it, as do `test_agent_home_ownership.py` and `tests/adapters/test_opencode_runtime_folders.py`. With the root-level tests and `tests/domain` together, the only failures are the three environment ones, known from earlier pre-checks (the demo test with no `demo/` in the copy, and the two `test_tmp_path_reopening` rows).

**Decision 1's mechanism, in today's image.** It confirms what the drafting agent found:

- In a fresh home under `factory-confine`, `opencode debug config` ends 1 with `EACCES: permission denied, mkdir '<home>/.config'`.
- With a read-only `.config/opencode` it ends 0 and leaves the folder empty.

That holds as `agent` unconfined and inside an outer `factory-confine`, which is how the smoke tester runs.

**The time limits.** I ran today's nine modules with `-n 64` on one CPU. That reproduces the fault: two failures, the `[time-limit]` row and `test_resume_gets_what_is_left_of_the_time_limit_and_unknown_measures`. With a prototype of S0002 the same run was green twice (127 s and 131 s).

## The human's changes

1. **The check on a fresh home: right as written.**
   - `/home/agent/.config` is not a volume (only `claude-home:/home/agent/.claude` is), so a recreated container gets the image's folders.
   - The workaround `FACTORY_OPENCODE_FOLDERS=.config/opencode` should be removed first, as step 1 says.
   - Step 3's expected `stat` lines are the owners and modes S0001 sets.
   - `self` runs Claude Code and never reads the folder.
2. **`CLAUDE.md`, *Tests*.** The bullet `- A test that waits for a time limit gives the process it starts room to start` exists as quoted, and no test pins `CLAUDE.md`'s own text. The pinned texts are `claude/agents/tester.md` and `template/CLAUDE.md`, which decision 8 leaves alone. The new bullet is right. If edit A is made, its "fifteen" stays unmentioned there, so nothing in it changes.

## Decisions

- **1 to 5 (S0001):** confirmed.
  - The image runs the entrypoint as `factory`.
  - `/home/agent` is `agent:factory-work 755`.
  - The agent's only group is `factory-work`, so a `factory:factory-work 0755` folder is read-only to it, guard or no guard.
  - `factory-confine` makes a run's folders as the agent (`_make_folders`), so `.config` must stay the agent's (decision 3).
  - Decision 5's smoke design works in the image as it is.
- **6:** confirmed by the load run. Ten seconds and a bound of 25 hold, every stand-in that the limit must end waits 30 or 60 s, and a missed kill still fails.
- **7 and 9:** one test missing. `test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` has 5 s, and its assertion `len(_calls(tmp_path)) == 2` needs a first call to finish and a resume to start before the limit. By decision 7's own rule it belongs in decision 9 (edit A). The kept-short tests named in decision 7 are right. The two version rows of `test_opencode_runtime_launch.py` (3 s) would check nothing if their child were killed early; I recommend leaving them.
- **Decision 9, `test_claude_runtime_confinement.py`:** the comment it rewrites sits above three constants (edit B).
- **8, 10, 11:** confirmed.

## Where F0029 meets other features

- **F0020-S0010 (backlog)** adds opencode tests with "a time limit of 3 seconds", where the stand-in must print a `step_start` before the kill (`session` `ses_a`) or run under the stand-in confine. Those are new tests of exactly the kind S0002 fixes. Started after F0029-S0002 and human's change 2, its tester should take `ROOMY_LIMIT` (point 3).
- **F0020-S0012 (backlog)** moves `Recorder` out of `tests/adapters/test_process_streaming.py`, one of S0002's modules. That is harmless one after the other.
- **F0022-S0005 (backlog)** changes `tests/test_agent_home_ownership.py`'s `layout` fixture, not `_path_settings`, which S0001's test imports from `tests/test_image.py`.
- **F0028:** independent of F0029. Either order works.

## Points for the human, with recommended answers

1. **Edit A (decision 9 and the counts):** (a) add the missing row; (b) leave it. Recommended: (a). It is the same race, and the smoke test runs it.
2. **Edit B (the confinement module's comment):** (a) as given below; (b) as drafted. Recommended: (a).
3. **F0020-S0010's 3-second criteria:** (a) change them to `ROOMY_LIMIT` when that story is started, after F0029; (b) leave them to the tester's reading of `CLAUDE.md`. Recommended: (a). A criterion that says "3 seconds" outweighs a rule in `CLAUDE.md`.
4. **Order:** (a) S0001 then S0002, as drafted; (b) the other way round. Recommended: (a). S0001 unblocks every opencode instance, and the two are independent.

## Verdict

The feature is ready with edits A and B to `feature.md`. The stories need S0001 edit 1 and S0002 edit 2 (required) and S0002 edit 1 (recommended), given in their files.

Edit A (recommended, `feature.md`):

- In *Goal*, replace `Fourteen more tests in nine modules, that one's own among them,` with `Fifteen more tests in nine modules, that one's own among them,`.
- In decision 6, replace `fifteen tests wait about ten seconds instead of one to five, roughly 120 more worker seconds` with `sixteen tests wait about ten seconds instead of one to five, roughly 130 more worker seconds`.
- In decision 7, replace `That is the fifteen of decision 9;` with `That is the sixteen of decision 9;`.
- In decision 9, in the bullet `S0002, tests/adapters/test_claude_runtime_resume.py`, after `both rows of test_call_killed_by_the_time_limit_has_no_model_duration (2 s) get ROOMY_LIMIT.` insert `The row resume ended by the time limit of test_model_duration_of_a_resumed_run_adds_the_known_calls (5 s; the first call must finish and the resume write its record before the limit) gets ROOMY_LIMIT.` (with the names in backticks, as the bullet writes them).

Edit B (recommended, `feature.md`, decision 9, the bullet `S0002, tests/adapters/test_claude_runtime_confinement.py`): replace

```markdown
`SHORT_LIMIT` (3 s) stays for `test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result`, and its comment becomes `# Short: the hanging shell it limits need not start to be killed.`
```

with

```markdown
`SHORT_LIMIT` (3 s) stays for `test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result`, with its own comment `# Short: the hanging shell it limits need not start to be killed.`; `WAIT_SECONDS` and `ELAPSED_BOUND` follow under `# The stand-ins wait far longer than any limit here.`
```
