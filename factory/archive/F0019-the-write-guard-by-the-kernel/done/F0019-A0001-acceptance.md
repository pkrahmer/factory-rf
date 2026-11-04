---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 226
comments_read: [6253637332]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-18T17:31:19.105372Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-10-18T18:04:46.816289Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-10-18T18:04:48.291413Z'
  stage: acceptance
- number: 4
  speaker: factory
  kind: crash
  at: '2026-10-18T18:34:42.629819Z'
  stage: acceptance
- number: 5
  speaker: factory
  kind: question
  at: '2026-10-18T18:34:42.629819Z'
  stage: acceptance
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-18T18:38:46.986090Z'
  stage: acceptance
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T18:39:04.610183Z'
  stage: acceptance
- number: 8
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-18T19:07:42.240521Z'
  stage: acceptance
  run: 9020bd0e3e124c348c5fbbdf582f38c2
- number: 9
  speaker: factory
  kind: done
  at: '2026-10-18T19:08:59.856005Z'
  stage: done
stories: [F0019-S0001, F0019-S0002, F0019-S0003, F0019-S0004, F0019-S0005, F0019-S0006]
outcome: accepted
---

# Acceptance of The write guard by the kernel

## Recommendation

**Accepted with stories.** All six stories are merged and every Scope item is built. The human's changes 1, 2 and 4 to 6 are on `main`. The guard is live: this acceptance ran under it, and its own writes to `/tmp`, the checkout's root and the home were refused. The feature's smoke test passes from the real pipeline definition through `factory-confine` to the kernel, and `make check` is green. No promise is broken. Three stories are proposed: a documentation repair (the documents still speak of the guard as future, the README miscounts the commands, and a project from the template or the demo has no warning), two missing criteria (the runtime's root and the preflight's `PATH`), and in-process steps for `factory-confine`, whose survivors decision 18 predicted.

## 1 Scope

| Scope item | Story | Where |
|---|---|---|
| `domain/confinement.py`: ABI, `Confinement`, `WriteTarget`, `write_targets`, `confinement_of`, devices | S0001, S0003, S0004 | `src/factory/domain/confinement.py` |
| `ConfinementError` | S0001 | `src/factory/domain/errors.py` |
| `CONFINE_COMMAND`, `GuardSettings.tool_paths` | S0002, S0003 | `src/factory/domain/agent_runs.py` |
| `tool_paths` and its load-time rule | S0003 | `src/factory/domain/pipeline_definition.py` |
| Landlock through `ctypes` | S0001 | `src/factory/adapters/landlock.py` |
| `replace_process` | S0002 | `src/factory/adapters/process.py` |
| `factory-confine` | S0002 | `src/factory/entry/confine.py`, `pyproject.toml:19` (change 1) |
| tool paths into the guard settings | S0003 | `src/factory/application/write_paths.py` |
| every call through the wrapper, rules file, temporary folder, `CLAUDE_CONFIG_DIR`, refusal | S0004 | `src/factory/adapters/claude_runtime.py:410`, `:561`, `:577`, `:630` |
| the runtime built with the wrapper; the preflight extra | S0004, S0005 | `src/factory/entry/wiring.py:386` |
| preflight item `confinement` | S0005 | `src/factory/application/preflight.py:184` |
| R14 in all seven agents | S0006 | `claude/agents/*.md` |

No story falls outside the Scope. Out of scope holds. The hook `factory-guard` is still there. The template and the demo are unchanged: `template/Makefile:74` and `demo/todo-service/project/Makefile:74` still write `.licenses-requirements.txt` at the root, and neither names `tool_paths` (decision 17). The image is unchanged. The Goal is reached: the guard is live once changes 4 to 6 are made, and changes 1, 2, 4 (`pyproject.toml:108`, `Makefile:66`), 5 and 6 (`37d27368`, `334f454d`, `factory/pipeline.yml:16`) are on `main`. Change 3 is not: `CLAUDE.md`, *Agent runtime (R12)*, still says only "It may install Claude Code hook scripts that refuse writes outside a write path". The feature marked change 3 as recommended, not needed, so it goes to the human under 6. Change 6 also added a tool path the feature did not list: `demo/todo-service/project/.ruff_cache/*`.

## 2 Feature smoke test

The walk-through follows the feature's purpose. It reads `factory/pipeline.yml` through the real reader and takes the acceptance reviewer's write paths (placeholders expanded) and the definition's ten tool paths. It runs one agent run through `ClaudeCodeRuntime(..., confine_executable="factory-confine")`, with a stand-in `claude` that tries every kind of write the feature names. It reads what is left after the run, then runs the preflight item `confinement` with the real kernel and the two failing sides. Last, it checks this acceptance run itself, the first real run under the guard. The script lay in a temporary folder that removed itself. It was run as `bash feature-smoke.sh < /dev/null` from the repository root. The two inner heredocs were delimited `EOF` in the run and are `EOF2` here, so that this report could be written by a heredoc:

```bash
#!/bin/bash
set -u
d=$(mktemp -d); trap 'chmod -R u+rwX "$d"; rm -rf "$d"' EXIT
F=factory/features/F0001-x
mkdir -p "$d/checkout/$F/in-progress" "$d/checkout/$F/backlog" "$d/checkout/src" "$d/home" "$d/runs" "$d/tmp"
printf '# Item\n' > "$d/checkout/$F/in-progress/F0001-A0001-acceptance.md"
cat > "$d/claude" <<'EOF2'
#!/bin/sh
F=factory/features/F0001-x; item=$F/in-progress/F0001-A0001-acceptance.md
t() { if eval "$2" 2>/dev/null; then r="$r $1=ok"; else r="$r $1=refused"; fi; }
r=""
t item-in-place  "echo edited >> $item"
t item-rename    "echo new > $F/in-progress/new.md && mv $F/in-progress/new.md $item"
t backlog-new    "echo s > $F/backlog/F0001-S0007-x.md"
t src            "echo x > src/a.py"
t root           "echo x > NEW.md"
t venv           "echo x > .venv/marker"
t home-cache     "echo x > \$HOME/.cache/marker"
t home-profile   "echo x >> \$HOME/.profile"
t shared-tmp     "echo x > $SHARED/x"
t own-tmp        "echo x > \$TMPDIR/x"
t claude-config  "echo x > \$CLAUDE_CONFIG_DIR/state"
py=$(python3 -c 'open("src/b.py","w")' 2>&1 | tail -1)
printf '{"type": "result", "subtype": "success", "is_error": false, "num_turns": 1, "total_cost_usd": 0.01, "usage": {"input_tokens": 1, "output_tokens": 1}, "permission_denials": [], "structured_output": {"decision": "question", "entry": "%s | %s"}}\n' "$r" "$py"
EOF2
sed -i "s|\$SHARED|$d/tmp|" "$d/claude"; chmod +x "$d/claude"
uv run -q python - "$d" <<'EOF2'
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
write_paths = [p.replace("{work_item}", f"{F}/in-progress/F0001-A0001-acceptance.md").replace("{feature}", F) for p in role.write_paths]
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
which = lambda name, path: shutil.which(name, path=path)
print("preflight:", confinement_item(abi_version, env, which))
print("preflight, no wrapper on PATH:", confinement_item(abi_version, {"PATH": "/usr/bin:/bin", "HOME": "/x"}, which))
print("preflight, ABI 2:", confinement_item(lambda: 2, env, which))
EOF2
```

followed by this acceptance run's own writes:

```bash
for p in /tmp/x /work/checkout/x ~/x /work/checkout/.reports/x "$TMPDIR/x"; do (echo > "$p") 2>/dev/null && { echo "$p written"; rm -f "$p"; } || echo "$p refused"; done
```

Output:

```
write paths: ['factory/features/F0001-x/in-progress/F0001-A0001-acceptance.md', 'factory/features/F0001-x/backlog/*']
tool paths: 10 from factory/pipeline.yml
run: completed
   item-in-place=ok
   item-rename=refused
   backlog-new=ok
   src=refused
   root=refused
   venv=ok
   home-cache=ok
   home-profile=refused
   shared-tmp=refused
   own-tmp=ok
   claude-config=ok
python sees: PermissionError: [Errno 13] Permission denied: 'src/b.py'
after the run: tmp [] runs []
item: ['# Item', 'edited']
preflight: name='confinement' passed=True detail=''
preflight, no wrapper on PATH: name='confinement' passed=False detail="factory-confine is not on the agent run's PATH /usr/bin:/bin"
preflight, ABI 2: name='confinement' passed=False detail="the kernel offers Landlock ABI 2, the write guard needs ABI 3 or higher: update the kernel (on WSL: wsl --update), or allow the Landlock system calls in the container runtime's seccomp profile"
exit 0
--- this acceptance run itself:
/tmp/x refused
/work/checkout/x refused
/home/agent/x refused
/work/checkout/.reports/x written
/tmp/factory-run-24befcda-500b-447d-a5d8-28ec51785f31/x written
```

Green. Each line holds what the feature promised:
- The single-file work item is edited in place but cannot be replaced by a rename (decision 3).
- A folder write path (`backlog/*`) allows new files.
- Everything else in the checkout is refused, the root included (decision 6).
- A tool path in the checkout (`.venv`, made by the wrapper) and one in the home (`~/.cache`) are allowed, and the home's root (`.profile`) is not (decisions 8, 9).
- The shared temporary root is refused and the run's own `TMPDIR` is allowed (decision 11).
- `CLAUDE_CONFIG_DIR` is writable (decision 9).
- Python sees `PermissionError: [Errno 13]`, as R14 now tells the agents (decision 14).
- After the run, neither the temporary folder nor the rules file is left.
- The preflight passes on this kernel (ABI 7) and fails with the documented texts on both sides (decision 12).
- `make check` ran inside this confined run and ended `check: green`, which is change 6's step 4. The tool paths cover everything the project's checks write.

## 3 Mutation score

`make mutants` (feature F0019, 12 modules) was run twice in the foreground. The first run ended on its time limit. The second went on from the kept results, spent its 540 s without finishing another mutant, and printed `mutants: stopped after 540 s; the results below are partial, run it again to go on` with the counter `2285/12860  🎉 2041 🫥 144  ⏰ 2  🤔 0  🙁 98  🔇 0  🧙 0` (the 12860 counts mutants of every module; only the feature's are run).

**Score: 2041 killed of 2303 mutants of the feature's modules (88.6 %).** Of the rest, 98 survived, 144 have no test, 2 timed out and 18 were not checked. The 18 unchecked mutants are 16 in `process.py` (`run_process`, `_decode`, `_seconds`), one in `agent_runs._must_be_absolute` and one in `pipeline_definition._lease_faults`. A mutant of `run_process` breaks every test that starts a process, so it runs to its time limit across the whole suite. These 18 are why the second run made no progress, and the same kind of mutant is behind the crashes this report's journal records. That is a limit of the target, not of this feature's tests.

The 98 survivors and 144 untested mutants, grouped:

- **A. Code that runs only in a child process (decision 18): 144 untested and 43 survivors.**
  - `landlock.py`: all 144 untested (coverage 35 %), plus 3 survivors in `abi_version` whose `ctypes` arguments are equivalent (`c_void_p(None)` vs `None`, `c_size_t(0)` vs `None`) or are reached only on a kernel without Landlock (`max(.., 0)` → `1`).
  - `entry/confine.py`: 36 survivors, for example `restrict_writes(None, rules.files)` (every folder and the run's own temporary folder dropped from the rules), `os.mkdir(path, )` (the `0700` mode dropped), `folder.mkdir(parents=None, ...)`, `len(arguments) <= 4` (a one-word command refused) and `sys.argv` never read.
  - `process.replace_process`: 4 survivors (`os.execvpe(argv[0], list(argv), None)`, the error text).
  
  The tests check these lines only in a child that imports the unmutated package. mutmut maps tests to mutants inside the test process, so a child never counts. `landlock.py` cannot run in the test process, because its `restrict_self` cannot be undone. `confine.py`'s steps can, with the irreversible calls injected: **F0019-S0009**.
- **B. The runtime's rules root: 1 survivor.** `_confinement`'s `root=guard.root` → `root=None` survives (`claude_runtime.py:425`). With it, a write path naming a missing file at the checkout's root widens to the whole checkout, the one thing decision 6 rules out. `confinement_of` has a domain test for this, but no runtime test passes such a path through: **F0019-S0008**.
- **C. The preflight's search path: 2 survivors.** `_which_on`'s `path=path` dropped (`wiring.py:392`). The item `confinement` (and the older `agent-environment`) would then search the factory's own `PATH` instead of the agent run's, and nothing would notice: **F0019-S0008**.
- **D. Older code in the touched modules: 52 survivors, none of them on this feature's lines.**
  - `claude_runtime.py`: 25 (resume and version texts, `format(.., "f")`, `_login_refusal`, `_start`'s `argv[0]`, the encoding of the run files, where `"UTF-8"` and `"utf-8"` are equivalent).
  - `wiring.py`: 21 (`repository_name`, `read_hosting_token`, `_read_utf8`, `machine_log`, `build_boundaries`' log and disk records).
  - `preflight.py`: 3 (the hosting check's branch name, the probe's start point).
  - 1 each in `write_paths.at` (an error text), `errors.AgentDefinitionError` and `process._kill_group`.
  
  These stem from F0001, F0010 and F0012. They are no promise of this feature, and no story is proposed for them.

## 4 What the stories noticed

- `confine.py` at 78 % and `landlock.py` at 35 % coverage, because their rows run in a child (S0001 coder entry 10, S0002 coder entries 14, 16, 22). This is group A above; S0009 brings `confine.py` into the test process.
- `make duplicates` listed `CONFINE_COMMAND`, `write_targets` and `confinement_of` as dead code until S0004 (S0002 and S0003 coders). Resolved: `make duplicates` now prints `duplicates: 0 new, 36 known, 3 gone`.
- The name `tests/test_process_search.py::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` no longer fits: it now checks six markers in `process.py` and two in `confinement.py`. S0004's coder and documenter noted it six times. The human (S0004 entry 47) logged it for later, because `[tool.mutmut]` in `pyproject.toml` deselects it by that name. Listed under 6.
- S0003's documenter noted that the operator guide's opening says `factory-confine` is used "once the runtime uses it". It still says so after S0004 (`docs/operator-guide.md:3`), and so does `README.md:12`: S0007.
- S0005's documenter found `docs/project-guide.md:1302` ("does not start the wrapper yet") and `:1223` stale. Both have since been corrected. They also found that the project guide does not describe `confinement_item`: S0007.
- S0001's coder noted that the "cannot open" text is built twice in `landlock.py` (in `_check_path` and in `_add_rule`'s guard for a path that vanishes). It is small, and the reason is in the coder's entry. No story.
- Reviewer remarks (S0002, S0005, S0006: a split parametrization and helper copies) were findings and were fixed in their stories through helper moves. None is left open.
- The human's entry 6 in this report: `make mutants` left `mutants/seed/.git` and crashed this stage twice. It was fixed on `main` by `81fd6131` (the target's `EXIT` trap). This run's two `make mutants` left no `.git` (`git status --short` shows only this report's cost sidecar).

## 5 The documentation as a whole

I read `README.md`, `docs/operator-guide.md` (*The agent runtime*, *The kernel refuses every other write*, the preflight's items, the stops, *The pipeline definition*), `docs/project-guide.md` (*The `claude -p` runtime*, the targets, *The kernel's write guard*, *The start wrapper*) and the four new entries in `docs/decisions.md` (`:555`, `:564`, `:584`, `:592`, with S0003's entry between them). What they say about the rules matches the smoke test above. Five faults:

1. `README.md:12` says "Six commands exist" and then names seven (`factory-run`, `factory-check-story`, `factory-bill`, `factory-watch`, `factory-health`, `factory-guard`, `factory-confine`). The count was not raised when S0002's documenter added `factory-confine` (`e0edc0a2`). `pyproject.toml` installs the seven.
2. `README.md:12` and `docs/operator-guide.md:3` say `factory-confine` starts every agent run "once the runtime uses it". The runtime has used it since S0004.
3. `docs/operator-guide.md:706` says "Once the kernel's write guard is live". It is live: `factory/pipeline.yml:16` holds the tool paths, and this run was confined.
4. A section the feature made necessary is missing. A project made from `template/`, or the todo demo, writes `.licenses-requirements.txt` (its `Makefile:74`) and `.coverage` at the checkout's root, and names no `tool_paths`. Under the guard, the kernel refuses both root files (a root path has no target), so every `make check` of such a project fails with `Permission denied`. Decision 17 leaves the template's fix to later, but no document tells the operator. They meet it at the first run of a new project.
5. `docs/project-guide.md` describes `token_file_item` (`:774`) but not `confinement_item(abi, environment, find)` (S0005's documenter noted it).

None of these contradicts behaviour in a way that leads a user into a wrong action except 4, which is a missing warning about out-of-scope code. All five go into **F0019-S0007**.

## 6 Decisions taken for the human

From `feature.md` (each accepted when the stories were built; listed here to accept or revisit):
1. Landlock through `ctypes`, no PyPI binding.
2. Only ABI 3's twelve write rights are handled; reads, execution, network, `ioctl` and scopes stay open; the minimum is ABI 3.
3. A folder rule allows everything beneath; a file rule only in-place writes (no rename over a single-file target; the smoke test above confirms).
4. A symbolic-link rule path is refused, and every path is checked before the first call (fail closed).
5. The wrapper is `factory-confine --rules <file> -- <command>`, with rules in `/state/runs/confine-<session>.json` (`0640`) and `os.execvpe`.
6. A missing folder is made; a missing file widens to its folder; a wildcard widens to its fixed leading folder; never the root.
7. The leave for S0002's three structural tests.
8. `tool_paths` in the pipeline definition; environment-variable cache moves rejected.
9. `CLAUDE_CONFIG_DIR=<HOME>/.claude`.
10. The device files and `/dev/shm`.
11. One `0700` temporary folder per run, removed after every call.
12. **No fallback without Landlock**: the preflight stops the machine. The alternative, an operator setting that falls back to the hook with a warning on every tick, is still open for the human to choose.
13. The runtime confines by default through `build_boundaries`; the leave for two wiring tests.
14. What a refused write looks like, in R14.
15. Protected paths inside an allowed folder: the hook refuses and the undo reverts them, and the kernel cannot exclude them. This is the one expected disagreement.
16. **The cross-check is still to do**: the hook stays through a shakedown-sized stretch of runs (recommended: plan step 5b on factory-rf), then the hook's refusals in the transcripts are compared with the rules, and a later feature removes the hook.
17. **The template and the todo demo are not ready for the guard**: they need `.coverage` and `.licenses-requirements.txt` moved off the root and `tool_paths` named. This is open before plan step 5b's demo run and the baseline run (step 10). S0007 only documents it.
18. Testing the rules in child processes, with no skip without Landlock.
19. `factory.entry.confine` imports the two adapters directly (the human's answer on #221, option A).
20. A `.` segment is refused like `..` in tool paths and write targets (the human's answer on #222, option A).
21. `# noqa: S108  # nosec B108` on the `/dev/shm` line, now in `CLAUDE.md`'s exception list.

From the journals:
- S0001 entry 4: the order of path checks became a criterion (folder before file, first of two).
- S0004 entry 4: three criteria added (wrapper line at the time limit; the removal's working folder and empty environment; `boundaries_from_environment` and `factory.entry.run` pass no other wrapper).
- S0004 entry 9: the removal's shell is `SHELL_EXECUTABLE`.
- S0004 entries 25 and 29: two criteria added (missing device targets; a removal that hangs).
- S0004 entry 47: one more review round only for two helper findings.

Left open for the human:
- Change 3 to `CLAUDE.md` (*Agent runtime (R12)*), recommended by the feature, is not made.
- Renaming `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` together with its `[tool.mutmut]` deselect line in `pyproject.toml`.
- Change 6 added `demo/todo-service/project/.ruff_cache/*` to `tool_paths`, which the feature's list did not have.

Earlier tests changed, each with its leave as the reviewers' entries name it:
- `tests/test_process_search.py`, `test_no_module_uses_another_route_to_a_process` and `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`: decision 7 (S0002). The second test again for the `/dev/shm` marker: the human's entry 14 of S0004 (decision 21), named by the coder in entry 16.
- `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: decision 7 (S0002).
- `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`: the human's entry 8 of S0002 (decision 19).
- `tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_keeps_its_run_files_under_runs` and `tests/entry/test_wiring_login.py::test_the_built_runtime_hands_the_login_file_s_token_to_claude`: decision 13 (S0004).
- `tests/entry/test_wiring_extras.py::test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user`: decision 12 (S0005).
- Helper moves under the standing leave:
  - S0003: `tests/application/test_write_paths.py` → `tests/write_path_support.py`.
  - S0004: `tests/conftest.py`, `test_wiring_command_records.py`, `test_wiring_run.py`, `test_wiring_boundaries.py`, `test_wiring_login.py` → `tests/wiring_support.py`.
  - S0005: `every_tool` in five modules → `tests/wiring_support.py`.
  - S0006: `_body` → `tests/shipped_agents.py`.

No earlier test was changed without a named leave.

## 7 The slow checks

The project offers nothing beyond `make check`, `make duplicates`, `make documents` and `make mutants`: no image scan, no SBOM. `make check` was green as found (`check: green`, total coverage 98.67 %, `test: green (38.1 s)`). The JUnit report (`.reports/junit.xml`) has 4912 tests summing to 389.8 s. The slowest is `tests.adapters.test_claude_runtime_resume::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]` at 5.0 s, then two fault-path tests at 3.2 s each. Three of this feature's tests follow at 3.0 s, each waiting on a time limit: `test_a_removal_that_outlasts_its_time_limit_is_ended_and_changes_no_result`, `test_a_wrapper_line_of_a_call_killed_at_its_time_limit_is_a_runtime_error` and `test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run[time-limit]`. The feature's 115 confinement tests take 17.3 s together. `make mutants` cannot finish the feature in two windows of 540 s (see 3). Disk: `/work` has 986.1 GB free and 0.5 GB used, against 986.2 GB free and 0.5 GB used at the previous record (the earlier start of this acceptance). Used space is unchanged and the 0.1 GB of free space belongs to the shared host disk, so there is no growth to explain.

## 8 Cost

77 runs, 92.2 min, $23.19:

| Story | Runs | Minutes | Dollars |
|---|---|---|---|
| S0001 | 7 | 6.4 | 1.94 |
| S0002 | 13 | 15.2 | 3.51 |
| S0003 | 12 | 14.1 | 3.66 |
| S0004 | 25 | 41.9 | 10.47 |
| S0005 | 10 | 8.5 | 2.13 |
| S0006 | 10 | 6.2 | 1.48 |

S0004 stands out, with 45 % of the dollars and 6 tests runs, 10 doing runs and 5 review runs. Its journal gives the reasons:
- Three questions to the human before and during the build (entries 4, 9, 14): the missing criteria, the removal's shell, and the `/dev/shm` marker that `make sast` refused and only the human could allow.
- A numbering conflict: the human's two new criteria on `main` collided with the intake's criteria 15 to 17 and needed a retry (entry 29).
- Review rounds up to the cap, for helper copies in its own test module, with a reset by the human (entry 47).

It was also the story with the most moving parts: the wrapper on the command line, the rules file, the temporary folder and its removal through `sudo`, and `CLAUDE_CONFIG_DIR`. S0002 and S0003 each paid for one question round (decision 19, decision 20).

## Proposed stories

- `backlog/F0019-S0007-the-documents-describe-the-live-write-guard.md`: the documentation repairs of 5 (the README's command count, the three sentences that speak of the guard as future, the template and demo warning, `confinement_item` in the project guide).
- `backlog/F0019-S0008-the-confinement-s-root-and-the-preflight-s-path-are-the-run-s.md`: the two missing criteria behind survivor groups B and C (the runtime builds the rules against the checkout's root; the preflight item searches the agent run's `PATH`).
- `backlog/F0019-S0009-factory-confine-s-steps-run-in-the-test-process.md`: `factory-confine`'s steps before the irreversible calls become testable in the test process (injected `restrict` and `replace`), so mutmut and coverage see the 36 survivors of `confine.py`.

## Journal

1. factory: started acceptance as self.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit 2f4512b15e7f5a3075b1b3656a6660a123a6d16b.
3. factory: started acceptance as self.
4. factory: crash 2: the run of stage acceptance ended without a result. Its work is discarded back to commit 5b401fe6a0620fd5a21b22b88e030251443a4f2a.
5. factory: Stage acceptance crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
6. 2026-10-18 human: Retry. Both crashes had one cause, not the write guard: `make mutants` left `mutants/seed/.git` in the checkout, owned by the agent and not group-writable, so the factory could not remove it after the run. Most likely a mutant of `process.py` made a test run `git init seed` in `mutants/`. The human removed it, and main now has `81fd6131`: the `make mutants` EXIT trap removes every `.git` under `mutants/`. This stage merges main when it starts, so it gets the fix. The second run had drafted F0019-S0007 (the documents describe the live write guard), and that work was lost: draft it again if the findings still call for it.
7. factory: started acceptance as self.
8. acceptance-reviewer: Accepted with stories; 3 stories proposed; make mutants 2041/2303

   The guard is live and does what the feature promised, end to end. Nothing in this run was left unfinished.

   1. Scope: every Scope item was built by S0001 to S0006, and nothing outside Out of scope was touched. The human's changes 1, 2 and 4 to 6 are on main. Change 3 (`CLAUDE.md`, *Agent runtime (R12)*) is not; it was only recommended, so it is listed under 6 for the human.
   2. Feature smoke test: green. It used the real `factory/pipeline.yml` and ran one run through `ClaudeCodeRuntime` and `factory-confine`. Allowed: editing the work item in place, a new backlog file, `.venv`, `~/.cache`, `$TMPDIR` and `CLAUDE_CONFIG_DIR`. Refused: renaming over the work item, `src`, the checkout's root, `~/.profile` and the shared temporary root. Python saw `PermissionError: [Errno 13]`, and nothing was left after the run. The preflight passed on ABI 7 and failed with the documented texts on both failing sides. This acceptance run was itself confined: `/tmp`, the checkout's root and the home were refused, and `make check` was green inside it.
   3. Mutants: 2041 of 2303 killed. `make mutants` stopped at its time limit twice; the second run finished none of the 18 mutants still left, 16 of them in `process.py`, whose broken `run_process` runs every process test to its time limit.
      - 187 untested or surviving mutants are in code that only runs in a child process, as decision 18 foresaw: `landlock.py` (144 with no test, 3 surviving), `confine.py` (36) and `replace_process` (4). F0019-S0009 covers `confine.py`.
      - 1 survivor: the runtime's rules root can be dropped (F0019-S0008).
      - 2 survivors: the preflight's `PATH` search can be dropped (F0019-S0008).
      - 52 survivors are in older code that F0001, F0010 and F0012 wrote. No story for them.
   4. Noticed: the coverage gaps of `confine.py` and `landlock.py` (S0009). The dead-code records from S0002 and S0003 are resolved (`duplicates: 0 new`). The out-of-date test name `..._the_four_in_the_process_wrapper` is the human's to fix, together with `pyproject.toml`. The stale "once the runtime uses it" passages go to S0007. The project guide's two stale lines are already corrected. The `mutants/seed/.git` that crashed this stage twice is fixed on main by `81fd6131`.
   5. Documents (S0007):
      - `README.md` says "Six commands exist" but names seven.
      - "once the runtime uses it" in `README.md:12` and `docs/operator-guide.md:3` is stale.
      - `docs/operator-guide.md:706` still says "Once the kernel's write guard is live", and it is live.
      - Nothing warns that a project from the template or the demo writes `.coverage` and `.licenses-requirements.txt` at the checkout's root, which the kernel refuses.
      - The project guide does not describe `confinement_item`.
   6. Decisions: the report lists the feature's 21 decisions and the journal answers. Still open for the human: the hook fallback offered as the alternative in decision 12, the cross-check of decision 16, the template and demo of decision 17, change 3, and the test rename. Every changed earlier test names its leave.
   7. Slow checks: none exist beyond the make targets. The slowest test takes 5.0 s; the feature's 115 tests take 17.3 s together. The disk shows no growth to explain (0.5 GB used, as at the previous record).
   8. Cost: $23.19 over 77 runs. S0004 stands out with $10.47 and 25 runs. Its journal names three questions to the human, a criterion-numbering conflict that needed a retry, and review rounds up to the cap for helper copies.
9. factory: done (pull request merged); cost: 1 runs, 28.6 min, 62 turns, 139697 tokens in (4680381 more from cache), 51199 out, $3.08
