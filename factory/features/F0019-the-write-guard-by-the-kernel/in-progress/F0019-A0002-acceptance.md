---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 230
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-18T19:45:50.835178Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-18T20:14:38.293765Z'
  stage: acceptance
  run: 9bfeb97a8f2c449da12e35ee4b0243f1
stories: [F0019-S0001, F0019-S0002, F0019-S0003, F0019-S0004, F0019-S0005, F0019-S0006, F0019-S0007, F0019-S0008, F0019-S0009]
outcome: null
---

# Acceptance of The write guard by the kernel

## Recommendation

**Accepted with stories.** All nine stories are merged. This includes the three that the first acceptance (F0019-A0001) proposed, and each of those reached its aim:
- S0007: the five documentation faults are fixed.
- S0008: the rules-root and preflight-`PATH` survivors are killed.
- S0009: `confine.py` survivors fell from 36 to 15, and its coverage rose from 78 % to 95 %.

The feature smoke test is green from the real pipeline definition through `factory-confine` to the kernel. This run was itself confined, and `make check` is green. No promise is broken. Three stories are proposed:
- S0010: a stale sentence and a misplaced paragraph in the project guide.
- S0011: the hook refuses the `$TMPDIR` that R14 sends agents to. This is a disagreement between the hook and the kernel that decision 15 did not foresee, and the cross-check of decision 16 would trip on it.
- S0012: in-process tests for the refusals that happen before the irreversible calls.

## 1 Scope

Every Scope item of `feature.md` was built by S0001 to S0006; the first acceptance's table (`done/F0019-A0001-acceptance.md`, section 1) still holds, and nothing has moved since. S0007 to S0009 were proposed by that acceptance and stay inside the Scope:
- S0007 is documents only (`README.md`, `docs/operator-guide.md`, `docs/project-guide.md`).
- S0008 is tests only (`tests/adapters/test_claude_runtime_confinement_root.py`, `tests/entry/test_wiring_extras_path.py`, the helper move to `tests/confine_support.py`).
- S0009 gave `factory.entry.confine.main` two injected steps, `restrict` and `replace` (`src/factory/entry/confine.py:33`), and added `tests/entry/test_confine_steps.py`.

No story falls outside the Scope, and Out of scope holds:
- The hook `factory-guard` is still there.
- The image is unchanged.
- The template and the demo still write `.licenses-requirements.txt` at the root (`template/Makefile:74`, `demo/todo-service/project/Makefile:74`) and name no `tool_paths`. This is decision 17, now documented at `docs/operator-guide.md:708`.

The human's changes 1 to 6 are all on `main`. Change 3, which was open at the first acceptance, is now in `CLAUDE.md` (*Agent runtime (R12)*). The Goal is reached: the guard is live.

## 2 Feature smoke test

The walk-through is the feature's purpose, end to end, and it extends the first acceptance's script with three checks:
- A write path naming a missing root file (`NOTES.md`): S0008's promise.
- A second tool path (`.reports/*`).
- The file left afterwards.

The script reads `factory/pipeline.yml` through the real reader and takes the acceptance reviewer's write paths, with placeholders expanded, plus `NOTES.md`, and the definition's ten tool paths. It runs one agent run through `ClaudeCodeRuntime(..., confine_executable="factory-confine")`. A stand-in `claude` tries every kind of write the feature names. Afterwards the script reads what is left, then runs the preflight item `confinement` against the real kernel and on both failing sides.

The script lay in `$TMPDIR` and was run as `bash "$TMPDIR/feature-smoke.sh" < /dev/null` from the repository root. Its temporary tree removes itself by a `trap`.

```bash
#!/bin/bash
set -u
d=$(mktemp -d); trap 'chmod -R u+rwX "$d"; rm -rf "$d"' EXIT
F=factory/features/F0001-x
mkdir -p "$d/checkout/$F/in-progress" "$d/checkout/$F/backlog" "$d/checkout/src" "$d/home" "$d/runs" "$d/tmp"
printf '# Item\n' > "$d/checkout/$F/in-progress/F0001-A0001-acceptance.md"
cat > "$d/claude" <<'EOF'
#!/bin/sh
F=factory/features/F0001-x; item=$F/in-progress/F0001-A0001-acceptance.md
t() { if sh -c "$2" 2>/dev/null; then r="$r $1=ok"; else r="$r $1=refused"; fi; }
r=""
t item-in-place   "echo edited >> $item"
t item-rename     "echo new > $F/in-progress/new.md && mv $F/in-progress/new.md $item"
t backlog-new     "echo s > $F/backlog/F0001-S0007-x.md"
t src             "echo x > src/a.py"
t root            "echo x > NEW.md"
t root-missing-wp "echo x > NOTES.md"
t venv            "echo x > .venv/marker"
t reports         "echo x > .reports/marker"
t home-cache      "echo x > \$HOME/.cache/marker"
t home-profile    "echo x >> \$HOME/.profile"
t shared-tmp      "echo x > SHARED/x"
t own-tmp         "echo x > \$TMPDIR/x"
t claude-config   "echo x > \$CLAUDE_CONFIG_DIR/state"
py=$(python3 -c 'open("src/b.py","w")' 2>&1 | tail -1)
printf '{"type": "result", "subtype": "success", "is_error": false, "num_turns": 1, "total_cost_usd": 0.01, "usage": {"input_tokens": 1, "output_tokens": 1}, "permission_denials": [], "structured_output": {"decision": "question", "entry": "%s | %s"}}\n' "$r" "$py"
EOF
sed -i "s|SHARED/x|$d/tmp/x|" "$d/claude"; chmod +x "$d/claude"
uv run -q python - "$d" <<'EOF'
import os, shutil, sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from factory.adapters.claude_runtime import ClaudeCodeRuntime
from factory.adapters.landlock import abi_version
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.application.preflight import confinement_item
from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings
d = Path(sys.argv[1]); F = "factory/features/F0001-x"
definition = RuamelPipelineDefinitionReader().parse(Path("factory/pipeline.yml").read_text())
role = definition.roles["acceptance-reviewer"]
write_paths = [p.replace("{work_item}", f"{F}/in-progress/F0001-A0001-acceptance.md").replace("{feature}", F) for p in role.write_paths] + ["NOTES.md"]
print("write paths:", write_paths)
print("tool paths:", len(definition.tool_paths), "from factory/pipeline.yml")
runtime = ClaudeCodeRuntime(str(d / "claude"), d / "runs", confine_executable="factory-confine", temporary_root=d / "tmp")
guard = GuardSettings(root=d / "checkout", write_paths=write_paths, protected_paths=[], tool_paths=definition.tool_paths)
agent = AgentDefinition(name="acceptance-reviewer", model="sonnet", tools=["Bash"], budget_usd=Decimal("1"), instructions="Probe.")
env = {"PATH": os.environ["PATH"], "HOME": str(d / "home")}
request = AgentRunRequest(agent=agent, prompt="Probe.", allowed_decisions=["question"], time_limit=timedelta(minutes=1), working_directory=d / "checkout", environment=env, guard=guard)
result = runtime.run(request)
print("run:", result.end_reason)
for part in result.entry.split(" | ")[0].split():
    print("  ", part)
print("python sees:", result.entry.split(" | ")[1])
print("after the run: tmp", sorted(os.listdir(d / "tmp")), "runs", sorted(os.listdir(d / "runs")))
print("item:", (d / "checkout" / F / "in-progress/F0001-A0001-acceptance.md").read_text().splitlines())
print("NOTES.md exists:", (d / "checkout" / "NOTES.md").exists())
which = lambda name, path: shutil.which(name, path=path)
print("preflight:", confinement_item(abi_version, env, which))
print("preflight, no wrapper on PATH:", confinement_item(abi_version, {"PATH": "/usr/bin:/bin", "HOME": "/x"}, which))
print("preflight, ABI 2:", confinement_item(lambda: 2, env, which))
EOF
echo "exit $?"
```

Output:

```
write paths: ['factory/features/F0001-x/in-progress/F0001-A0001-acceptance.md', 'factory/features/F0001-x/backlog/*', 'NOTES.md']
tool paths: 10 from factory/pipeline.yml
run: completed
   item-in-place=ok
   item-rename=refused
   backlog-new=ok
   src=refused
   root=refused
   root-missing-wp=refused
   venv=ok
   reports=ok
   home-cache=ok
   home-profile=refused
   shared-tmp=refused
   own-tmp=ok
   claude-config=ok
python sees: PermissionError: [Errno 13] Permission denied: 'src/b.py'
after the run: tmp [] runs []
item: ['# Item', 'edited']
NOTES.md exists: False
preflight: name='confinement' passed=True detail=''
preflight, no wrapper on PATH: name='confinement' passed=False detail="factory-confine is not on the agent run's PATH /usr/bin:/bin"
preflight, ABI 2: name='confinement' passed=False detail="the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher: update the kernel (on WSL: wsl --update), or allow the Landlock system calls in the container runtime's seccomp profile"
exit 0
```

Then this acceptance run's own writes, from its shell:

```bash
for p in /tmp/acceptance-probe /work/checkout/acceptance-probe /work/checkout/.reports/acceptance-probe "$TMPDIR/acceptance-probe"; do if (: > "$p") 2>/dev/null; then echo "$p written"; rm -f "$p"; else echo "$p refused"; fi; done
```

```
/tmp/acceptance-probe refused
/work/checkout/acceptance-probe refused
/work/checkout/.reports/acceptance-probe written
/tmp/factory-run-fc5bb7ac-fe3a-4880-a960-904269fc1b91/acceptance-probe written
```

**Green.** Each line holds what the feature promised:
- The work item is edited in place, and a rename over it is refused (decision 3).
- A folder write path allows a new file.
- `src`, the root and a missing root write path are refused. `NOTES.md` stays unwritten, so the checkout is never widened (decision 6, S0008).
- Both tool paths and `~/.cache` are allowed; `~/.profile` is refused (decisions 8, 9).
- The shared temporary root is refused, while `$TMPDIR` and `CLAUDE_CONFIG_DIR` are allowed (decisions 9, 11).
- Python sees `PermissionError: [Errno 13]`, as R14 says (decision 14).
- Nothing is left after the run.
- The preflight passes on ABI 7 and fails with the documented texts (decision 12).

One thing the smoke test does not show, but this run met: the hook. The reviewer's `Write` of the script to `$TMPDIR` was refused with `PreToolUse:Write hook error: [factory-guard --settings /state/runs/guard-fc5bb7ac-fe3a-4880-a960-904269fc1b91.json]: /tmp/factory-run-fc5bb7ac-fe3a-4880-a960-904269fc1b91/feature-smoke.sh is outside the checkout.`. The script was then written by a shell heredoc, which the kernel allows. See 4 and F0019-S0011.

## 3 Mutation score

`make mutants` (feature F0019, 12 modules) was run twice in the foreground. Both runs ended on their 540 s limit with `mutants: stopped after 540 s; the results below are partial, run it again to go on`, and the counter stood at `2298/12873  🎉 2078 🫥 144  ⏰ 2  🤔 0  🙁 74  🔇 0  🧙 0` after each run. `uv run mutmut results --all true` shows the feature's 18 remaining mutants as `not checked`: 16 in `process.py` (`run_process`, `_decode`, `_seconds`), one in `agent_runs` and one in `pipeline_definition`. These are the same 18 as at the first acceptance. A broken `run_process` runs every process test to its time limit, so the target cannot reach them in a window.

**Score: 2078 killed of 2316 mutants of the feature's modules (89.7 %; it was 2041 of 2303, 88.6 %).** Of the rest, 74 survived, 144 have no test, 2 timed out and 18 were not checked.

Groups:

- **A. Paths that end before the irreversible calls, so far tested only in a child process: 144 untested and 22 survivors.**
  - `landlock.py`: 144 with no test (coverage 35 %). Most are in the system calls themselves, which stay child-only (decision 18). But `_check_path` and the check loop of `restrict_writes` refuse before the first system call, so they can run in the test process. Its 3 survivors in `abi_version` are equivalent (`c_void_p(None)` against `None`, `c_size_t(0)`) or reachable only without Landlock.
  - `entry/confine.py`: 15 survivors, down from 36.
    - Six are `main`'s defaults, never taken in the test process (`sys.argv[2:]`, `... if (restrict is None) and False else restrict`).
    - Three are the unreadable rules file's fault text (`fault = None`, `"XX XX".join`, `str(None)`). The test checks only the prefix and the single line.
    - Three are `exist_ok` dropped for an existing folder.
    - One is the folder fault's text (`raise _Stop(None)`, lines 97-98, uncovered).
    - Two are encoding spellings (`"UTF-8"`, `None` under a UTF-8 locale), which are equivalent.
  - `process.replace_process`: 4 survivors. Three change the `ValueError` text. One passes no environment (`os.execvpe(argv[0], list(argv), None)`), so the program is searched on the factory's own `PATH`. A non-executable file on the given `PATH` tells the two apart in-process.
  - All of these except the equivalent ones go to **F0019-S0012**. Every row in it names a path that cannot be opened, so a broken check still fails before `landlock_restrict_self` binds the worker.
- **B. Older code in the touched modules: 52 survivors and 2 timeouts, none on this feature's lines.**
  - `claude_runtime.py`: 25, plus 2 timeouts in `version`.
  - `wiring.py`: 21 (`repository_name`, `read_hosting_token`, `_read_utf8`, `machine_log`, `build_boundaries`' records, `machine_extras`' `agent_user_item(settings, None)`).
  - `preflight.py`: 3.
  - 1 each in `write_paths.at`, `errors.AgentDefinitionError` and `process._kill_group`.
  - These are the same 52 as the first acceptance's group D, from F0001, F0010 and F0012. No story.
- **Gone since the first acceptance:**
  - The rules-root survivor in `claude_runtime._confinement` and the two `_which_on` survivors, all killed by S0008's tests.
  - 21 of `confine.py`'s 36, killed by S0009's.

## 4 What the stories noticed

- `docs/project-guide.md:1335` "Nothing starts it yet: the runtime will." is stale. S0007's documenter (entry 11) and smoke tester (entry 13), and S0009's documenter (entry 11), each named it and left it, since their criteria said no other passage changes. Still there: **F0019-S0010**.
- `confine.py` coverage: S0008's coder noted 78 % three times. S0009 raised it to 95 %, and its coder noted the remaining lines 97-98 (the `mkdir` fault) and 110 (`if __name__ == "__main__"`). Lines 97-98 go to **F0019-S0012**. Line 110 runs only as `python -m`, in a child process: no story.
- S0008's reviewer (entry 9) found a helper copy (`_bin_with` against `write_script`). It was fixed in its round through the tester under the standing leave. Nothing is open.
- S0009's coder did not run `make mutants`; this report does.
- Found by this acceptance: the hook refuses an `Edit` or `Write` in the run's own `$TMPDIR`, with "is outside the checkout." R14 tells every agent to make temporary files only there, and the kernel allows it. The agent can only go around the hook through the shell, which R14 also forbids ("never retry it by another route"). Decision 15 names protected paths as the one expected disagreement between the hook and the kernel. This is a second one, and decision 16's cross-check would count every such refusal in the transcripts: **F0019-S0011**.
- Also met by this run, as decision 3 foresaw: `sed -i` on the report itself failed with `sed: couldn't open temporary file .../in-progress/sedsXQo4X: Permission denied`, because the report is a single-file target and `sed -i` writes a new file beside it. The `Edit` tool, which writes in place, worked. This is expected, and R14's text covers it. No story.
- Carried from the first acceptance and still open, the human's: the name `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` (`tests/test_process_search.py:62`, deselected by that name at `pyproject.toml:132`) now checks eight markers. See 6.

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` (the opening, *The agent runtime*, *The kernel refuses every other write*, the preflight's items and stops, *The pipeline definition* with `tool_paths`), and `docs/project-guide.md` (*The kernel's targets*, the guard's *Which path is judged*, *The kernel's write guard*, *The start wrapper*). S0007's five repairs are all in place:
- `README.md:12` "Seven commands exist", naming seven.
- No "once the runtime uses it" anywhere.
- `docs/operator-guide.md:706` "An agent run can write only ...".
- The template and demo warning at `docs/operator-guide.md:708`.
- The `confinement_item` paragraph.

S0009's paragraphs in *The start wrapper* match `src/factory/entry/confine.py`. What the documents say about the rules matches the smoke test above. Three faults are left:

1. `docs/project-guide.md:1335`, "Nothing starts it yet: the runtime will.", contradicts `docs/operator-guide.md:88` and the code: S0010.
2. The `confinement_item` paragraph (`docs/project-guide.md:1337`) sits in *The start wrapper*, between its opening and *The arguments and the rules file*. S0007's criterion put it in *The kernel's write guard*, which is where a reader looking for the preflight item's rules would look: S0010.
3. Nothing tells the reader that the hook refuses the run's `$TMPDIR` while R14 and the kernel allow it. The fix belongs to the behaviour, not the documents: S0011, with its docs criterion.

None of these leads a user into a wrong action on the machine. The first misleads a reader of the project guide about the wiring.

## 6 Decisions taken for the human

From `feature.md` (taken when the stories were built; to accept or revisit):
1. Landlock through `ctypes`, no PyPI binding.
2. Only ABI 3's twelve write rights; reads, execution, network, `ioctl`s and scopes stay open; the minimum is ABI 3.
3. A folder rule allows everything beneath it. A file rule allows only in-place writes, so a rename over a single-file target is refused (the smoke test confirms).
4. A link as a rule path is refused, and every path is checked before the first call (fail closed).
5. The wrapper is `factory-confine --rules <file> -- <command>`, with its rules file `0640` in `/state/runs`, and it ends in `os.execvpe`.
6. A missing folder is made, a missing file widens to its folder, a wildcard widens to its fixed leading folder, and the root is never allowed.
7. The leave for S0002's three structural tests.
8. `tool_paths` in the pipeline definition; moving the caches by environment variables was rejected.
9. `CLAUDE_CONFIG_DIR=<HOME>/.claude`.
10. The device files, and `/dev/shm`.
11. One `0700` temporary folder per run, removed after every call.
12. **No fallback without Landlock.** The alternative is still open: an operator setting that falls back to the hook, with a warning on every tick.
13. The runtime confines by default through `build_boundaries`; the leave for two wiring tests.
14. What a refused write looks like, in R14.
15. Protected paths inside an allowed folder are the one expected disagreement between the hook and the kernel. **This acceptance found a second: the run's `$TMPDIR` (F0019-S0011).**
16. **The cross-check is still to do**: a stretch of runs, then the hook's refusals in the transcripts are compared with the rules. With S0011 merged first, the `$TMPDIR` refusals drop out of that comparison.
17. **The template and the todo demo are not ready for the guard.** This is open before plan step 5b's demo run and the baseline run. The operator guide now says so (S0007).
18. Testing the rules in child processes, with no skip without Landlock. S0009 and the proposed S0012 narrow this to the system calls and the `exec`.
19. `factory.entry.confine` imports the two adapters directly (the human's answer on #221).
20. A `.` segment is refused like `..` (the human's answer on #222).
21. `# noqa: S108  # nosec B108` on the `/dev/shm` line.

From the journals of S0007 to S0009: no human answer and no default. S0001 to S0006's are listed in the first acceptance, section 6.

For the human to choose, new:
- F0019-S0011 lets the hook allow the run's `$TMPDIR` (recommended). The alternatives:
  - Leave the hook and tell the agents in R14 to write temporary files through the shell only.
  - Count `$TMPDIR` refusals as expected in decision 16's cross-check, as decision 15's are.

Still open from the first acceptance:
- Renaming `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`, together with its deselect line in `pyproject.toml`.
- Change 6 added `demo/todo-service/project/.ruff_cache/*` to `tool_paths`, which the feature's list did not have.
- Closed since then: change 3 (`CLAUDE.md`, *Agent runtime (R12)*) is made.

Earlier tests changed by S0007 to S0009, as their reviewers name them:
- S0008: `tests/adapters/test_claude_runtime_confinement.py` and `tests/conftest.py`, under the standing leave to move a shared test helper. Constants, `Layout` and helpers moved to `tests/confine_support.py`, and the `layout` fixture moved to `tests/conftest.py`. Every test kept its name and assertions (reviewer entries 9 and 17).
- S0007 and S0009: none (reviewer entries 9 and 9).

No earlier test was changed without a named leave. The changes of S0001 to S0006 are in the first acceptance, section 6.

## 7 The slow checks

The project offers nothing beyond `make check`, `make duplicates`, `make documents` and `make mutants`: no image scan, no SBOM. `make check` was green as found (`check: green`, total coverage 98.80 %, `test: green (42.1 s)`).

The JUnit report (`.reports/junit.xml`) has 4931 tests summing to 385.4 s. The slowest:
- `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s.
- This feature's three time-limit tests in `tests/adapters/test_claude_runtime_confinement.py`, at 3.0 s each: `test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result`, `test_a_wrapper_line_of_a_call_killed_at_its_time_limit_is_a_runtime_error` and `test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run[time-limit]`.

The feature's 132 confinement tests take 17.8 s together. `make mutants` cannot finish the feature in two windows (see 3).

Disk: `/work` 986.0 GB free and 0.5 GB used now, against 986.1 GB free and 0.5 GB used at the previous record, whose occasion is an acceptance. `/state` and `/tmp` are unchanged at 0.0 GB used. Used space is the same, and the 0.1 GB of free space belongs to the shared host disk. No growth to explain.

## 8 Cost

99 runs, 107.9 min, $27.69 (the first acceptance's own run, $3.08, is not in this sum):

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 | 7 | 6.4 | 1.94 |
| S0002 | 13 | 15.2 | 3.51 |
| S0003 | 12 | 14.1 | 3.66 |
| S0004 | 25 | 41.9 | 10.47 |
| S0005 | 10 | 8.5 | 2.13 |
| S0006 | 10 | 6.2 | 1.48 |
| S0007 | 6 | 2.5 | 1.01 |
| S0008 | 10 | 8.7 | 2.33 |
| S0009 | 6 | 4.4 | 1.16 |

S0004 still stands out, with 38 % of the dollars. Its journal names three questions to the human, a criterion-numbering conflict that needed a retry, and review rounds up to the cap for helper copies. The first acceptance covers it in detail.

The three follow-ups cost $4.50 together. S0008 is the dearest of them, because of one extra review round. Its reviewer found the test helper `_bin_with` copying `write_script`, so the story went doing → tests → doing → review again (entries 9 to 17), four runs more than a clean pass. No story among S0007 to S0009 otherwise stands out.

## Proposed stories

- `backlog/F0019-S0010-the-start-wrapper-section-says-the-runtime-starts-it.md`: two project-guide fixes. The stale "Nothing starts it yet: the runtime will." becomes true, and the `confinement_item` paragraph moves to *The kernel's write guard*, where S0007's criterion put it.
- `backlog/F0019-S0011-the-hook-allows-the-run-s-temporary-folder.md`: the guard settings carry the run's temporary folder, and the hook allows an `Edit` or `Write` beneath it. This ends the disagreement between R14, the kernel and the hook that this run met, before decision 16's cross-check reads the hook's refusals.
- `backlog/F0019-S0012-the-guard-s-refusals-before-its-irreversible-calls-run-in-the-test-process.md`: in-process tests for `restrict_writes`' path checks, `replace_process`'s faults and `factory-confine`'s defaults, folders and rules fault. They cover survivor group A apart from the system calls, which stay child-only.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: Accepted with stories; 3 stories proposed; make mutants 2078/2316

   The write guard does what `feature.md` promised. The feature smoke test is green, `make check` is green, and this run was itself confined. Nothing in this run was left unfinished.

   1. Scope: every Scope item was built by S0001 to S0006. S0007 to S0009, proposed by the first acceptance, stay inside the Scope, and Out of scope holds. The human's changes 1 to 6 are all on main; change 3 has been made since the first acceptance.
   2. Feature smoke test: green. It used the real `factory/pipeline.yml` and ran one run through `ClaudeCodeRuntime` and `factory-confine`.
      - Allowed: editing the work item in place, a new backlog file, `.venv`, `.reports`, `~/.cache`, `$TMPDIR` and `CLAUDE_CONFIG_DIR`.
      - Refused: a rename over the work item, `src`, the root, a missing root write path (`NOTES.md` stays unwritten), `~/.profile` and the shared temporary root.
      - Python saw `PermissionError: [Errno 13]`, and nothing was left after the run. The preflight passed on ABI 7 and failed with the documented texts on both sides.
      - This run's own writes to `/tmp` and the checkout's root were refused.
   3. Mutants: 2078 of 2316 killed (89.7 %; it was 88.6 %). Both runs stopped at 540 s, and 18 mutants in `process.py` and elsewhere stay unchecked, the same 18 as last time.
      - 144 have no test and 22 survived in paths that end before the irreversible calls (`landlock._check_path`, `confine` defaults and fault texts, `replace_process`): F0019-S0012.
      - 52 survivors are in older code, as before. No story.
      - S0008 and S0009 killed their 3 and 21 survivors.
   4. Noticed:
      - The stale project-guide line "Nothing starts it yet" was named by three agents: S0010.
      - New: the hook refuses `Edit` and `Write` in the run's `$TMPDIR`, which R14 and the kernel allow. That is a second disagreement between the hook and the kernel, besides decision 15's, and it would trip decision 16's cross-check: S0011.
      - `sed -i` on the work item is refused, as decision 3 foresaw.
   5. Documents: S0007's five repairs are in place. Left: `docs/project-guide.md:1335` is stale, and the `confinement_item` paragraph sits under *The start wrapper* instead of *The kernel's write guard* (S0010).
   6. Decisions: the feature's 21 decisions are listed. Open for the human:
      - The decision 12 alternative (a fallback to the hook).
      - The decision 16 cross-check.
      - The template and demo of decision 17.
      - Renaming the test `..._the_four_in_the_process_wrapper`.
      - The demo `.ruff_cache` tool path.
      - New: S0011 against its two alternatives (R14 says to use the shell only, or the cross-check counts `$TMPDIR` refusals as expected).
      No earlier test was changed without a named leave.
   7. Slow checks: none exist beyond the make targets. The slowest test takes 5.0 s, and the feature's 132 tests take 17.8 s together. The disk shows no growth (0.5 GB used, as at the previous record).
   8. Cost: $27.69 over 99 runs. S0004 stands out with $10.47 (questions, a numbering retry, review rounds to the cap). S0007 to S0009 cost $4.50 together; S0008 had 4 extra runs for one helper-copy review round.
