---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 234
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-18T20:48:41.941367Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-18T21:14:01.624045Z'
  stage: acceptance
  run: 05d3735f1f5743a585205783d3ea7f5c
stories: [F0019-S0001, F0019-S0002, F0019-S0003, F0019-S0004, F0019-S0005, F0019-S0006, F0019-S0007, F0019-S0008, F0019-S0009, F0019-S0010, F0019-S0011, F0019-S0012]
outcome: null
---

# Acceptance of The write guard by the kernel

## Recommendation

**Accepted.** All twelve stories are merged. The three that the second acceptance (F0019-A0002) proposed each reached their aim:
- S0010: the project guide's start wrapper section is true.
- S0011: on `main`, the hook allows the run's `$TMPDIR`.
- S0012: the refusals before the irreversible calls run in the test process. The `replace_process` survivors are gone, and `confine.py` is down from 15 survivors to 2 equivalent ones.

The feature smoke test is green from the real pipeline definition through `factory-confine` and the hook to the kernel. `make check` is green, and the mutation score rose to 91.5 %. One story is proposed, for the guard's remaining real survivors. It is not a broken promise.

One thing is for the human, not for a story. The image that `self` runs was built before S0011 was merged, so this run's hook still refused `$TMPDIR` (see 2). Rebuilding `self` puts S0011 live. Decision 16's cross-check should count only runs after that rebuild.

## 1 Scope

Every Scope item of `feature.md` was built by S0001 to S0006. The first acceptance's table (`done/F0019-A0001-acceptance.md`, section 1) still holds. S0010 to S0012 were proposed by the second acceptance and stay inside the Scope:
- S0010 is documents only (`docs/project-guide.md`, *The start wrapper* and *The kernel's write guard*).
- S0011 changes three modules:
  - `GuardSettings.temporary_directory` (`src/factory/domain/agent_runs.py`).
  - `judge`'s temporary-folder rule (`src/factory/adapters/claude_guard.py:51-54`, `_beneath_temporary_directory` at `:80`).
  - `ClaudeCodeRuntime._guard_settings` (`src/factory/adapters/claude_runtime.py:569`).
  It is inside the guard's cross-check purpose (decisions 15 and 16) and keeps the hook, as Out of scope demands.
- S0012 is tests only (`tests/adapters/test_landlock_checks.py`, `tests/adapters/test_process_replace_faults.py`, `tests/entry/test_confine_defaults.py`, and helpers moved to `tests/confine_support.py`).

Out of scope still holds:
- The hook `factory-guard` is still there.
- `image/` is unchanged.
- The template and the demo name no `tool_paths` (decision 17).

The human's changes 1 to 6 are all on `main`, so the Goal is reached. The guard is live on the kernel side.

## 2 Feature smoke test

The walk-through is the feature's purpose, end to end. It extends the second acceptance's script with what S0011 promised: a stand-in `claude` reads the hook command that the runtime wrote into its hook settings and pipes four `Write` payloads through it. The script does the following:
1. Reads `factory/pipeline.yml` through the real reader.
2. Takes the acceptance reviewer's write paths, with placeholders expanded, plus a missing root file `NOTES.md`, and the definition's ten tool paths.
3. Runs one agent run through `ClaudeCodeRuntime(..., confine_executable="factory-confine")`.
4. Has the stand-in try every kind of write the feature names, then ask the hook for its verdicts.
5. Reads what is left, then runs the preflight item `confinement` against the real kernel and on both failing sides.

Command, from the repository root (the script on standard input, see below for why; its tree removes itself by a `trap`):

```bash
bash -s <<'SCRIPT'
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
# The hook command the runtime wrote into the hook settings, judged on four Write payloads.
hooks=""; prev=""; for a in "$@"; do [ "$prev" = "--settings" ] && hooks=$a; prev=$a; done
hook=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["hooks"]["PreToolUse"][0]["hooks"][0]["command"])' "$hooks")
h() { printf '{"tool_name": "Write", "tool_input": {"file_path": "%s"}}' "$2" | sh -c "$hook" 2>/dev/null; r="$r hook-$1=$?"; }
h own-tmp    "$TMPDIR/notes.txt"
h backlog    "$PWD/$F/backlog/F0001-S0008-x.md"
h src        "$PWD/src/c.py"
h shared-tmp "SHARED/y"
printf '{"type": "result", "subtype": "success", "is_error": false, "num_turns": 1, "total_cost_usd": 0.01, "usage": {"input_tokens": 1, "output_tokens": 1}, "permission_denials": [], "structured_output": {"decision": "question", "entry": "%s | %s"}}\n' "$r" "$py"
EOF
sed -i "s|SHARED/|$d/tmp/|" "$d/claude"; chmod +x "$d/claude"
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
SCRIPT
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
   hook-own-tmp=0
   hook-backlog=0
   hook-src=2
   hook-shared-tmp=2
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
/tmp/factory-run-4c11f5b5-21bf-464c-8489-c54ef1d08655/acceptance-probe written
```

**Green.** Each line holds what the feature promised:
- The work item is edited in place, and a rename over it is refused (decision 3).
- A folder write path allows a new file.
- `src`, the root and a missing root write path are refused. `NOTES.md` stays unwritten (decision 6).
- Both tool paths and `~/.cache` are allowed, and `~/.profile` is refused (decisions 8, 9).
- The shared temporary root is refused, while `$TMPDIR` and `CLAUDE_CONFIG_DIR` are allowed (decisions 9, 11).
- Python sees `PermissionError: [Errno 13]` (decision 14).
- The hook that the runtime registered (found first on `PATH` from the checkout's `.venv`, so `main`'s code) allows the run's `$TMPDIR` and the backlog. It refuses `src` and the shared temporary root, so the hook and the kernel agree (S0011).
- Nothing is left after the run.
- The preflight passes on ABI 7 and fails with the documented texts (decision 12).

**What this run met itself.** My `Write` of the script to `$TMPDIR` was refused again with `PreToolUse:Write hook error: [factory-guard --settings /state/runs/guard-4c11f5b5-....json]: /tmp/factory-run-4c11f5b5-.../feature-smoke.sh is outside the checkout.`. The cause is not S0011's code:
- The guard settings file of this run (`/state/runs/guard-4c11f5b5-....json`) has no `temporary_directory` key.
- `/opt/factory/src/factory/domain/agent_runs.py` has no such field.
- `/opt/factory` dates from 17:24, while S0011 was archived at 20:36 UTC.

`self` runs an image built before S0011. I did not write the file another way: the script was passed to `bash -s` on standard input instead. See 6 for the human's rebuild.

## 3 Mutation score

`make mutants` (feature F0019, 13 modules: `claude_guard` joined through S0011) was run twice in the foreground. Both runs ended at the 540 s limit with `mutants: stopped after 540 s; the results below are partial, run it again to go on`. The counter after the second run:

```
⠴ 2381/12906  🎉 2195 🫥 106  ⏰ 2  🤔 0  🙁 78  🔇 0  🧙 0
```

`uv run mutmut results --all true` shows 18 of the feature's mutants as `not checked`:
- 16 in `process.py` (`run_process` 13, `_decode` 2, `_seconds` 1).
- 1 in `agent_runs._must_be_absolute`.
- 1 in `pipeline_definition._lease_faults`.

These are the same 18 as at both earlier acceptances.

**Score: 2195 killed of 2399 mutants of the feature's modules (91.5 %).** It was 2078 of 2316 (89.7 %) at the second acceptance and 88.6 % at the first. Of the rest, 78 survived, 106 have no test, 2 timed out and 18 were not checked.

Groups:

- **A. Code that runs only in a child process: 106 with no test and 16 survivors.** Decision 22 accepts these, so no story.
  - The 106 with no test are all in `landlock.py`: `_add_rule` 34, `_create_ruleset` 24, `_restrict_self` 44 and `_raise_on_failure` 4. The second acceptance counted 144.
  - The 16 survivors are in `restrict_writes`. Since S0012's in-process tests reach that function, mutmut maps its system-call half to them, and these mutants now show as survivors instead of "no tests":
    - `_add_rule(None, folder, ...)`, `ruleset_fd = None` and `os.close(None)`, among others.
    - `x_restrict_writes__mutmut_7` (`expect_folder=None` for `False`), which is equivalent.
  - The child-process tests in `tests/adapters/test_landlock.py` are their check.
- **B. The guard's own module, new to the count: 5 survivors.** This is **F0019-S0013**.
  - `claude_guard._beneath_temporary_directory` has 2 survivors, both in S0011's code. `mutmut_8` turns `real_folder is None or real_path is None` into `and`, and `mutmut_11` turns `return False` into `return True`. A `file_path` with a NUL character and a temporary folder set is refused today. Under `mutmut_11` it is allowed, and under `mutmut_8` `judge` raises `AttributeError`. The one NUL test builds its settings without a temporary folder.
  - `read_guard_settings` has 3 survivors, from older code (F0012). `mutmut_10` raises `GuardSettingsInvalid(str(path), str(None))`: the test checks only `assert caught.value.fault`, which `"None"` passes. `mutmut_2` and `mutmut_4` change the encoding's spelling and are equivalent.
- **C. Equivalent ones in this feature's code: 5.** No story.
  - `confine._read_rules` has 2 (`encoding=None` and `"UTF-8"`). S0012 took `confine.py` from 15 survivors to these 2.
  - `landlock.abi_version` has 3 (`c_void_p(None)` against `None`, `c_size_t(0)` against `None`, and `max(..., 1)`, which only a kernel without Landlock tells apart).
- **D. Older code in the touched modules: 52 survivors and 2 timeouts.** None is on this feature's lines, so no story. These are the same 52 as at both earlier acceptances:
  - `claude_runtime.py`: 25, plus 2 timeouts in `version`. Among them are the `_write_files` encoding spellings, `_start`, `_resume` and `_make_state_directory`'s error text.
  - `wiring.py`: 21.
  - `preflight.py`: 3.
  - 1 each in `write_paths.at`, `errors.AgentDefinitionError.__init__` and `process._kill_group`.
- **Gone since the second acceptance:** all 4 survivors of `replace_process`, 13 of `confine.py`'s 15, and 38 of `landlock.py`'s 144 untested mutants (now mapped, see A), all by S0012.

## 4 What the stories noticed

- S0010: every entry says "noticed: nothing".
- S0011: the coder, reviewer and documenter noticed nothing. The smoke tester's first try, wrapped in `bash -c '…'`, was refused by Claude Code's own safety check (an `rm -rf` in a trap). That is the runtime's behaviour, not the factory's, so no story.
- S0012: the coder noted `landlock.py` coverage at 61 % (lines 54-62 and 79-126, the system calls), as decision 18 foresaw. `make check` today shows the same. No story.
- Found by this acceptance:
  - The hook in `self`'s image predates S0011, so this run's `Write` to `$TMPDIR` was refused once more. This is the human's rebuild (see 6), not a story.
  - The project guide's `Tests:` line for the guard (`docs/project-guide.md:1271`) does not name S0011's `tests/adapters/test_claude_guard_temporary.py`. S0011's documenter cross-read the guard sections but did not add it. This is folded into **F0019-S0013**'s docs criterion.
- Carried from the earlier acceptances and still open, the human's: the name `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` (`tests/test_process_search.py:62`, deselected by that name at `pyproject.toml:132`) now checks eight markers.

## 5 The documentation as a whole

I read the parts the three new stories changed (`git diff af84eb79 HEAD -- docs README.md`), and then each whole section around them:
- `docs/project-guide.md`: *The guard command* (*Which path is judged*, *Failing open*), *The kernel's write guard* and *The start wrapper*.
- `docs/operator-guide.md`: *`factory-guard` on the agent run's `PATH`*, and *The agent runtime* with its temporary-folder paragraph.
- `docs/decisions.md`: the new entry *The hook allows the run's temporary folder*.
- `README.md`: unchanged since the second acceptance, which read it.

The second acceptance's two faults are repaired:
- "Nothing starts it yet" is gone. *The start wrapper* now says `ClaudeCodeRuntime` starts every run through it by default.
- The `confinement_item` paragraph sits at the end of *The kernel's write guard*.

S0011's texts agree with each other and with `judge`:
- The operator guide's one sentence.
- The project guide's paragraph, which names the checkout first, "beneath" on path parts, the link rule and `None` for an older file.
- The decision entry, with both rejected alternatives.

S0012's tests paragraphs match the test modules. The smoke test above confirms what the documents say about the rules and the hook.

One small gap is left: the guard's `Tests:` line (`docs/project-guide.md:1271`) omits `tests/adapters/test_claude_guard_temporary.py`. It goes to S0013. No contradiction between documents, and none between documents and behaviour.

## 6 Decisions taken for the human

From `feature.md` (to accept or revisit):
1. Landlock is reached through `ctypes`, with no PyPI binding.
2. Only ABI 3's twelve write rights are handled. Reads, execution, the network, `ioctl`s and scopes stay open. The minimum is ABI 3.
3. A folder rule allows everything beneath it. A file rule allows only in-place writes, so a rename over a single-file target is refused (the smoke test confirms it).
4. A link as a rule path is refused, and every path is checked first (fail closed).
5. `factory-confine --rules <file> -- <command>`, with its rules file `0640` in `/state/runs`, ending in `os.execvpe`.
6. A missing folder is made. A missing file widens to its folder, and a wildcard to its fixed leading folder. The root is never allowed.
7. The leave for S0002's three structural tests.
8. `tool_paths` in the pipeline definition.
9. `CLAUDE_CONFIG_DIR=<HOME>/.claude`.
10. The device files, and `/dev/shm`.
11. One `0700` temporary folder per run, removed after every call.
12. **No fallback without Landlock.** The alternative is still open: an operator setting that falls back to the hook, with a warning on every tick.
13. The runtime confines by default, with the leave for two wiring tests.
14. What a refused write looks like, in R14.
15. Protected paths inside an allowed folder are the one expected disagreement between the hook and the kernel. S0011 removed the second one, `$TMPDIR`, from `main`'s code.
16. **The cross-check is still to do.** Recommended: start counting the hook's refusals only after `self`'s image is rebuilt from a `main` that holds S0011. Until then the running hook refuses `$TMPDIR`, as this run's transcript shows, and those refusals would read as disagreements.
17. **The template and the todo demo are not ready for the guard.** This is still open before plan step 5b's demo run and the baseline run.
18. Testing in child processes, with no skip without Landlock. S0012 narrowed it to the system calls and the `exec`.
19. `factory.entry.confine` imports the two adapters directly (#221).
20. A `.` segment is refused like `..` (#222).
21. `# noqa: S108  # nosec B108` on the `/dev/shm` line.
22. The child-only mutants are accepted with no story (the human's word at the second acceptance). This report follows it: groups A and C propose nothing.

From the journals of S0010 to S0012:
- S0011, intake: the human's answer (a) on entry 4. Criterion 1 gained the row in which a checkout lies beneath the temporary folder, and the Interface's checkout-first clause stayed.
- S0011, coder (entry 10), a default: the runtime fills in `temporary_directory` when it writes the settings file, rather than the caller who builds the request, and an unconfined runtime always writes `null`.
- S0010 and S0012: no human answer and no default. Both coders chose to leave `src/` untouched, as their Interfaces said.

For the human to do or choose:
- **Rebuild `self`'s image** (`docker compose -f image/compose.yml up -d --build`, with `FACTORY_INSTANCE=self` and the repository URL). Change 5's warning no longer applies, because `tool_paths` is on `main`. Without the rebuild, S0011 is merged but not live.
- Still open from the earlier acceptances:
  - Renaming `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`, together with its deselect line in `pyproject.toml`.
  - The extra `demo/todo-service/project/.ruff_cache/*` tool path, which the feature's list did not have.

Earlier tests changed by S0010 to S0012, as their reviewers name them:
- S0011, under the standing leave to move a shared test helper (reviewer entry 12):
  - `tests/adapters/test_claude_guard.py`: `_payload` and `_outside` moved to `tests/guard_support.py`.
  - `tests/entry/test_guard.py`: its `_payload` copy now comes from there, and an unused import is gone.
- S0012, under the standing leave to move a shared test helper (reviewer entry 9):
  - `tests/entry/test_confine.py`: `USAGE` and `_rules` moved, `_rules` now named `write_rules`.
  - `tests/entry/test_confine_steps.py`: `USAGE`, `Replaced` and `Steps` moved.
  - `tests/confine_support.py`: only gains them.
- S0010: none.

Every test kept its name and what it checks. No earlier test was changed without a named leave.

## 7 The slow checks

The project offers nothing beyond `make check`, `make duplicates`, `make documents` and `make mutants`: no image scan, no SBOM. `make check` was green as found: `test: green (40.8 s)`, `check: green`, total coverage 99.05 %.

The JUnit report (`.reports/junit.xml`) has 4966 tests summing to 406.8 s. The slowest:
- `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s.
- This feature's three time-limit tests in `tests/adapters/test_claude_runtime_confinement.py`, at 3.0 to 3.1 s each.

The 35 tests that S0011 and S0012 added take 1.7 s together. The slowest of them is `test_claude_guard_temporary::test_the_console_script_allows_a_write_in_the_temporary_folder_it_is_given[without-folder]` at 0.74 s, because it starts the console script.

`make mutants` cannot finish the feature in two windows (see 3).

Disk: `/work` is 985.9 GB free and 0.5 GB used now, against 986.0 GB free and 0.5 GB used at the previous record, whose occasion is an acceptance. `/state` and `/tmp` are unchanged at 0.0 GB used. Used space is the same, and the 0.1 GB of free space belongs to the shared host disk. No growth to explain.

## 8 Cost

The stories cost 118 runs, 121.5 min and $31.60. The two earlier acceptances' own runs are not in this sum.

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
| S0010 | 6 | 2.4 | 0.62 |
| S0011 | 7 | 5.8 | 1.78 |
| S0012 | 6 | 5.4 | 1.51 |

S0004 still stands out, with a third of the dollars. Its journal names three questions to the human, a criterion-numbering retry and review rounds to the cap, as the first acceptance describes.

The three follow-ups of the second acceptance cost $3.91 together, with no rework round. S0011's one extra run is its intake question (the checkout-first row), which the human answered at once. S0010 and S0012 each took the six runs of a clean pass, though their coders had nothing to build.

## Proposed stories

- `backlog/F0019-S0013-the-hook-s-refusals-of-what-it-cannot-resolve-are-pinned.md`: tests in the test process for the guard module's real survivors. These are a NUL path with a temporary folder set (S0011's `_beneath_temporary_directory`), and the exact fault text of `read_guard_settings`. The guard's `Tests:` line in the project guide gains S0011's module and the new one.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: Accepted; 1 story proposed; make mutants 2195/2399

   The write guard does what `feature.md` promised:
   - The feature smoke test is green.
   - `make check` is green as found.
   - All twelve stories are merged, including the second acceptance's S0010 to S0012.

   One thing is for the human: `self`'s image was built at 17:24, before S0011 was merged at 20:36 UTC. So this run's hook still refused a `Write` to `$TMPDIR`. Rebuild `self` to put S0011 live, and only then start decision 16's cross-check.

   1. Scope: every Scope item was built by S0001 to S0006. S0010 (documents), S0011 (the hook allows `$TMPDIR`) and S0012 (tests only) stay inside the Scope, and Out of scope holds. The human's changes 1 to 6 are on `main`.
   2. Feature smoke test: green, through the real `factory/pipeline.yml`, `ClaudeCodeRuntime` and `factory-confine`, plus the hook the runtime registered.
      - The kernel allows the work item in place, the backlog, `.venv`, `.reports`, `~/.cache`, `$TMPDIR` and `CLAUDE_CONFIG_DIR`.
      - It refuses a rename over the work item, `src`, the root, a missing root write path, `~/.profile` and the shared `/tmp`.
      - The hook with `main`'s code allows `$TMPDIR` and the backlog, and refuses `src` and the shared `/tmp`.
      - Nothing is left after the run, and the preflight passes and fails as documented.
   3. Mutants: 2195 of 2399 killed (91.5 %, up from 89.7 %). Both runs stopped at 540 s, and the same 18 mutants stay unchecked.
      - 106 with no test and 16 survivors are child-only `landlock` code: decision 22, no story.
      - 5 survivors are in `claude_guard`: 2 real ones in S0011's `_beneath_temporary_directory` (a NUL path with a temporary folder set) and 1 in `read_guard_settings`' fault text, which go to S0013; 2 are equivalent encoding spellings.
      - 5 are equivalent ones in `confine` and `abi_version`, and the same older 52 plus 2 timeouts remain.
      - S0012 killed all of `replace_process`'s survivors and 13 of `confine`'s 15.
   4. Noticed:
      - The stories' entries name nothing new.
      - This run found the stale image and the guard's `Tests:` line missing S0011's module (in S0013).
      - The test name `..._the_four_in_the_process_wrapper` is still the human's.
   5. Documents: S0010's repairs are in place, and S0011's three texts agree with `judge`. The one gap is `docs/project-guide.md:1271` not naming `test_claude_guard_temporary.py` (S0013). There are no contradictions.
   6. Decisions: the 22 feature decisions are listed, plus S0011's intake answer (a) and its coder's default (the runtime fills in `temporary_directory`). Open for the human:
      - The fallback alternative of decision 12.
      - The cross-check of decision 16, after the rebuild.
      - The template and demo of decision 17.
      - The test rename and the demo `.ruff_cache` tool path.
      - Rebuilding `self`.
      No earlier test was changed without a named leave.
   7. Slow checks: none exist beyond the make targets. The slowest test takes 5.0 s, and the 35 new tests take 1.7 s together. Disk usage is unchanged at 0.5 GB used.
   8. Cost: $31.60 over 118 runs. S0004 stands out with $10.47, as before. S0010 to S0012 cost $3.91 together with no rework round; S0011's one extra run was its intake question.
