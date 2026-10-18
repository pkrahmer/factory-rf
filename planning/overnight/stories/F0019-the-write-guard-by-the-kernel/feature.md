# The write guard by the kernel

## Goal

Today an agent may write outside its stage's write paths by any route but Claude Code's `Edit` and `Write`: the hook `factory-guard` sees only those two tools, and every other write (a shell command, a test, a child process, a tool's cache) is caught only afterwards, by the undo, for the paths git tracks. This feature makes the kernel refuse such writes as they happen. Every agent run starts through a wrapper, `factory-confine`, that restricts the run's writes, and those of every process it starts, with Landlock (Linux 5.13 and later, ABI 3 from Linux 6.2) to the stage's write paths in the checkout, a temporary folder of the run's own, the runtime's own folder in the agent's home, the project's tool state and a few device files; everything else is refused with `Permission denied`: the rest of `/work`, `/state`, the shared `/tmp`, the rest of the agent's home. The rule set covers every tool and every runtime, so opencode (plan step 5b) needs no guard of its own. The preflight checks that the kernel offers Landlock with the ABI the rules need, the agents' instructions say what a refused write looks like, the hook stays as a cross-check, and the undo stays as the backstop and the record. It is for the human, who can then let an agent run any command without trusting it to stay in its lane, and for the operator, who sees a kernel without Landlock as a stop before any agent runs. Done when every story below is merged and `make check` is green; the guard is live once the human's changes 4 to 6 below are made.

## Scope

- `src/factory/domain/confinement.py` (new): the minimum Landlock ABI and its fault text, the rules of one agent run (`Confinement`), the kernel's targets of the write paths and tool paths (`WriteTarget`, `write_targets`, `confinement_of`), the device files (S0001 to S0004).
- `src/factory/domain/errors.py`: `ConfinementError` (S0001).
- `src/factory/domain/agent_runs.py`: `CONFINE_COMMAND` (S0002); `GuardSettings.tool_paths` (S0003).
- `src/factory/domain/pipeline_definition.py`: the key `tool_paths` and its load-time rule (S0003).
- `src/factory/adapters/landlock.py` (new): the three Landlock system calls through `ctypes` (S0001).
- `src/factory/adapters/process.py`: `replace_process`, the one `exec` (S0002).
- `src/factory/entry/confine.py` (new): the wrapper `factory-confine` (S0002).
- `src/factory/application/write_paths.py`: the tool paths into the guard settings (S0003).
- `src/factory/adapters/claude_runtime.py`: every call through the wrapper, the rules file, the run's temporary folder and its removal, `CLAUDE_CONFIG_DIR`, the wrapper's refusal (S0004).
- `src/factory/entry/wiring.py`: the runtime built with the wrapper (S0004); the preflight item among the machine's extras (S0005).
- `src/factory/application/preflight.py`: the item `confinement` (S0005).
- `claude/agents/*.md`, all seven: the rule R14 says what a refused write looks like (S0006).
- The tests each story names, under `tests/`, and the earlier test modules named in decisions 7 and 12.
- `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md`, from each story's docs criterion.

## Out of scope

- Removing the hook `factory-guard` (its entry module, its adapter, its hook settings, its console script and its tests): a later feature, after the cross-check run of decision 16.
- Any Landlock rule on reading, executing, the network (ABI 4), device `ioctl`s (ABI 5) or scopes (ABI 6): reads stay open (decision 2).
- A fallback to the hook when the kernel offers no Landlock (decision 12).
- The template (`template/Makefile`, `template/factory/pipeline.yml`) and the todo demo (`demo/todo-service/`, and the live `pkrahmer/factory-demo-todo`): they write `.coverage` and `.licenses-requirements.txt` at the checkout's root and name no `tool_paths`; a later story or the human's change, before a project from the template or the demo runs under the guard (decision 17).
- Leftover temporary folders after a crash of the factory process itself (the folder of a run whose factory died is not removed; the next run never reads it, and recreating the container clears `/tmp`).
- opencode (plan step 5b), and any other runtime.
- The image (`image/*`): `uv sync` installs the new console script from `pyproject.toml`; nothing in the Dockerfile, the entrypoint or Compose changes.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The kernel restricts a process's writes (Landlock)
- S0002: `factory-confine` starts a command with its writes confined
- S0003: The write paths and the tool paths become the kernel's targets
- S0004: Every agent run starts through `factory-confine`
- S0005: The preflight checks the kernel's write guard
- S0006: The agents' instructions explain a refused write

## The human's changes

Checked against `factory/pipeline.yml`: the coder writes `src/*`, `image/*`, `template/*` and `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. The changes below lie outside every write path. No new dependency: the Landlock calls go through the standard library's `ctypes` (decision 1). No `.secrets.baseline` entry, no `security/` change.

1. Before S0002 starts: `pyproject.toml`, `[project.scripts]`, a new line after `factory-guard = "factory.entry.guard:main"`:

   ```toml
   factory-confine = "factory.entry.confine:main"
   ```

   S0002's tests and smoke test start the installed console script. The line is harmless before the module exists (the script fails to import until S0002 is merged).

2. Before S0002 starts: `CLAUDE.md`, *Not without asking*, the bullet "The one exception, decided with the seed" becomes:

   ```markdown
   - The one exception, decided with the seed: `src/factory/adapters/process.py`, the one module that starts processes (R5), may carry `# noqa: S404` and `# nosec B404` on its `subprocess` import, `# noqa: S603` and `# nosec B603` on its one `Popen` call, and `# noqa: S606` and `# nosec B606` on its one `os.execvpe` call (F0019: the write guard's wrapper replaces itself with the runtime), and nothing else.
   ```

3. Recommended with change 2, not needed by a story: `CLAUDE.md`, *Architecture*, the bullet *Agent runtime (R12)*, its third sentence "It may install Claude Code hook scripts that refuse writes outside a write path." becomes "Every agent run starts through `factory-confine`, which restricts the run's writes with Landlock to its write paths, its tool paths and its own temporary folder; the Claude Code hook that refuses an edit outside a write path stays until the cross-check of F0019 is done."

4. Any time before the guard goes live (harmless now; recommended together with change 1): the two files the project's tools write at the checkout's root move into `.reports/`, which is a tool path, because a missing file at the root cannot be allowed (decision 6).
   - `pyproject.toml`, `[tool.coverage.run]`, a new line after `branch = true`:

     ```toml
     data_file = ".reports/.coverage"
     ```

   - `Makefile`, the recipe of `licenses`, its four lines between `$(start)` and `$(green)` become:

     ```make
     	mkdir -p .reports
     	uv export -q --frozen --no-dev --no-emit-project --format requirements-txt -o .reports/licenses-requirements.txt
     	uv run pip-licenses --from=mixed --allow-only="$(ALLOWED_LICENSES)" \
     	  --packages $$(sed -n 's/^\([A-Za-z0-9_.-]*\)==.*/\1/p' .reports/licenses-requirements.txt) > /dev/null
     	rm -f .reports/licenses-requirements.txt
     ```

     (The recipe lines start with a tab, as the `Makefile`'s other recipes. `.reports/` is already git-ignored.)

5. When S0006's pull request is ready: stop the instance `self`, then merge it, so that F0019's acceptance, due at the next tick, becomes the first run under the guard; then, with `self` still stopped, `factory/pipeline.yml` gets a new top-level key after `project_commands` and before the comment above `roles`. It must not come earlier: the running image refuses an unknown key with `pipeline_definition_invalid`, and S0003's reader accepts it only once the image is rebuilt.

   ```yaml
   # What every agent run may write for the project's tools, besides its write paths: git-ignored
   # state in the checkout, and caches in the agent's home (~/). The kernel refuses every other write.
   tool_paths: [".venv/*", ".mypy_cache/*", ".ruff_cache/*", ".pytest_cache/*", ".import_linter_cache/*", ".reports/*", "mutants/*", "~/.cache/*", "~/.semgrep/*"]
   ```

   The list is what the agent user wrote in v1.1's container on 2026-10-18 (looked at read-only: `/work/checkout` holds `.venv`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.import_linter_cache`, `.reports` and `.coverage` written by the agent; `/home/agent` holds `.cache/uv`, `.cache/python-entrypoints` and `.semgrep`), plus `mutants/` for the acceptance's `make mutants`.

6. Then, before starting `self` again: a hand probe in a throwaway container of the new image (as the handover's check was made), as the agent user under `sudo`, on a copy of the checkout: `factory-confine` around a real `claude -p` call with a prompt that makes it use `Bash`, `Edit` on a file whose rule is a single file (a work item), and `make check`. Look for `Permission denied` in the transcript and the output; it confirms decisions 3, 9 and 10, which this drafting could only infer. A path the probe finds missing is a line for change 5 (a tool's state) or a story (the runtime's own needs). Then rebuild and start `self` (`docker compose -f image/compose.yml up -d --build`, with `FACTORY_INSTANCE=self` and the repository URL as for every compose call from factory-rf).

## Decisions taken for the human

1. Landlock is reached through the standard library's `ctypes` and the three system calls (`landlock_create_ruleset`, `landlock_add_rule`, `landlock_restrict_self`, numbers 444 to 446 on x86-64 and arm64) plus `prctl(PR_SET_NO_NEW_PRIVS)`, not through a binding from PyPI: about forty lines, as the probe of 2026-10-17 showed (`planning/overnight/landlock_probe.py.txt`), against a new pinned dependency, a licence to check and a young package's supply chain. Python 3.12 has no `os.landlock`. (Feature, S0001)
2. The ruleset handles exactly the twelve write rights of ABI 3 (write a file, truncate, make and remove files, folders, links, sockets, pipes and device nodes, and refer, which governs renames and links between folders), on every kernel with ABI 3 or higher; the minimum ABI is 3 (Linux 6.2), because without the truncate right a `truncate` call outside the rules would stay open. Reading, executing, the network (ABI 4), device `ioctl`s (ABI 5) and scopes (ABI 6) are not handled: the agent must read what it reads today and reach the API, and the rules behave the same on every kernel from 6.2. The ruleset attribute holds only `handled_access_fs`, so it does not depend on later ABIs. This machine's WSL2 kernel 6.18 offers ABI 7. (S0001)
3. A folder rule allows all twelve rights beneath the folder, also for files and folders the agent makes there later; a file rule allows only writing and truncating that one existing file in place. So an agent cannot rename, replace or delete a single-file target, such as its work item; a tool that saves by writing a new file beside it and renaming it over the old one is refused. Claude Code's `Edit` must therefore write the work item in place: the hand probe (change 6) confirms it; if it does not, the fix is to allow the work item's folder instead (the undo already reverts every other path in an `in-progress/` folder). (S0001, S0003)
4. A rule path that is a symbolic link is refused, and every path is checked before the first system call, so a refused rule leaves the process unrestricted and the wrapper starts nothing (fail closed). Landlock judges the real path of every write, so a link inside an allowed folder that points elsewhere is refused at the write. (S0001)
5. The wrapper is the console script `factory-confine` (`factory.entry.confine`), found on the agent run's `PATH` like `factory-guard`. It reads its rules from a file the runtime writes beside the guard's, `/state/runs/confine-<session>.json` (mode `0640`, readable by the agent's group, removed after the run), makes the missing folders of its rules and the run's own temporary folder, restricts itself, sets `TMPDIR` and replaces itself with the runtime through `replace_process` in the one process module (`os.execvpe`), so that `timeout`'s kill and the factory's kill of the process group still reach the runtime. Every fault before the replacement is one line starting `factory-confine:` on standard error and exit status 1, and the runtime is never started; the runtime turns that line into `AgentRuntimeError`, as it does for a refused `sudo`. Arguments (`--rules <file> -- <command>`) rather than environment variables keep the rules out of the agent's environment. (S0002, S0004)
6. Paths that do not exist when the run starts, and patterns the kernel cannot name exactly (the design's first open point): a folder pattern's missing folder is made, with its parents, by the wrapper before it restricts (an empty folder leaves no mark git sees); a file pattern whose file does not exist allows its folder instead, wider than the write path, and the undo narrows it after the run, as it does today for every route the hook does not see; a pattern with a wildcard anywhere but a trailing `/*` allows the folder of its fixed leading segments. None of them ever allows the checkout's root: such a pattern gets no rule, and the agent sees `Permission denied` and asks. This is why change 4 moves `.coverage` and `.licenses-requirements.txt` off the root. (S0003)
7. The leave to change tests other stories wrote, beyond the standing leave of `CLAUDE.md`, for S0002: `tests/test_process_search.py`, the test `test_no_module_uses_another_route_to_a_process` (its expected users become exactly `{"factory.adapters.process": {"os.execvpe"}}`) and the test `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` (it also expects `noqa: S606` and `nosec B606` on the one `os.execvpe` line and may be renamed to `test_the_only_suppression_markers_are_the_six_in_the_process_wrapper`); `tests/test_wrapper_search.py`, the test `test_only_the_three_wrappers_import_the_process_module` (its expected importers gain `factory.entry.confine`; its name may keep "three wrappers", since the entry module is no wrapper but the wrapper's start). The tester makes these changes, nothing else in those modules. (S0002)
8. The project's tool state is named by the project, in a new optional key of the pipeline definition, `tool_paths`: folder patterns `<folder>/*` in the checkout or `~/<folder>/*` in the agent's home, written by every role's agent run. The factory knows no tool's folder (R8), the hook and the undo ignore them (the folders are git-ignored), and a tool path that git tracks is still reverted by the undo. Moving caches into the run's folder by environment variables was rejected: each tool has its own variable, and some (semgrep's home folder) have none that `make` passes on. (S0003)
9. The runtime's own folder in the agent's home is `<HOME>/.claude`, and the runtime sets `CLAUDE_CONFIG_DIR` to it, so that Claude Code keeps its `.claude.json` there instead of in the home's root. Looked at read-only on 2026-10-18: Claude Code saves `/home/agent/.claude.json` by replacing it (the home folder's own time moved 24 ms after the file's, and `.claude/backups/` holds a copy per save), which a single-file rule refuses and only the whole home would allow. With the variable, the home's root, `.bashrc` and `.profile` stay refused, so an agent cannot change the environment of later runs; inside `.claude`, the agents and `settings.json` stay read-only by their file permissions (F0012-S0025), since Landlock cannot exclude beneath an allowed folder. The old `~/.claude.json` is left unused. The hand probe (change 6) confirms where Claude Code then writes. (S0004)
10. The device files every tool may write: `/dev/null`, `/dev/zero`, `/dev/full`, `/dev/random`, `/dev/urandom` and `/dev/tty` as files and `/dev/shm` as a folder, each only when it exists. (S0004)
11. One temporary folder per run, `<temporary root>/factory-run-<session>` (`/tmp` in the container), made by the wrapper as the run's user with mode `0700` and refused when it already exists, `TMPDIR` pointing to it; the runtime removes it after every call, also after a kill or an error, as the run's user (`chmod -R u+rwX`, then `rm -rf`, so a folder an agent closed is removed too); a resumed call gets it fresh. A removal that fails changes no result. It also ends the growth of `/tmp/pytest-of-agent` that F0018's acceptance found, since pytest follows `TMPDIR`. (S0004)
12. **The fallback without Landlock: none; the factory stops.** The preflight gains the item `confinement` (Landlock with ABI 3 or higher, and `factory-confine` on the agent run's `PATH`); its failure is the existing machine stop `preflight_failed` naming the item, so no new stop reason is needed and no agent runs. Recommended over falling back to the hook because the hook covers only `Edit` and `Write`, so a fallback would silently drop the guard for every other route on exactly the machine that lacks it; because the hook is to be removed after the cross-check, and a fallback would keep it alive as a second code path for good; and because the kernels the factory runs on offer ABI 3 or higher (this machine's 6.18 offers 7; current WSL2 kernels are 6.6 or later, `wsl --update`). The alternative, for the human to choose instead: an operator setting that falls back to the hook alone, with a warning on every tick. Also a leave for S0005: `tests/entry/test_wiring_extras.py`, the test `test_the_extras_come_in_the_operator_guides_order_sudo_only_with_an_agent_user`, whose two rows of names gain `"confinement"` between `"agent-environment"` and `"agent-run-probe"`. (S0005)
13. The runtime confines its calls when it is built with the wrapper's command (`confine_executable`), and the wiring always builds it so (a test pins it); the tests of earlier stories build it without the argument and keep their command lines unchanged, so no runtime test of an earlier story changes. A request without guard settings is still confined, with no path of the checkout. (S0004)
14. What the agent sees on a refused write is the system's `Permission denied` (`EACCES`): `cannot create ...: Permission denied` in a shell, `PermissionError: [Errno 13]` in Python, an `EACCES` error from Claude Code's tools. R14 in every shipped agent says so and tells the agent not to work around it but to ask when the work needs the path, and to make temporary files only in `$TMPDIR` (the design's third open point). (S0006)
15. The protected paths inside an allowed folder (`*/feature.md` matches `docs/x/feature.md`, which the documenter's folder rule allows) are refused by the hook while it stays and reverted by the undo after the run; the kernel cannot exclude them. This is the one expected disagreement between the hook and the kernel. (S0003)
16. The cross-check: the hook stays through this feature and through the first shakedown-sized stretch of runs after the guard goes live (recommended: the build of plan step 5b on factory-rf, about ten stories; the alternative is a rerun of the todo demo on the instance `shakedown`, which first needs the demo's own changes of decision 17). The session then lists every refusal of the hook in the agent's transcripts (`/home/agent/.claude/projects/`, the refusal texts of the guard: "is outside the write paths of this stage", "is owned by the human", "is not a path inside the checkout", "is outside the checkout") and checks each path against the stage's write paths and tool paths: a refused path that a folder or file rule would allow, other than decision 15's, is a disagreement. With none, a later feature removes the hook (the entry module, the adapter, the hook settings, the console script, `GUARD_COMMAND`, the preflight's check of it, their tests and the documents). (Feature)
17. The template and the todo demo stay as they are here (Out of scope): before a project made from them runs under the guard, its `Makefile` must move `.coverage` and `.licenses-requirements.txt` off the root and its pipeline definition must name its `tool_paths`, as changes 4 and 5 do for factory-rf. This matters for 5b's todo-demo run and for the baseline run (plan step 10). (Feature)
18. Testing the rules (the brief's question): Landlock restricts one process and its children and needs no privilege, so the tests restrict child processes they start in `tmp_path` and check each write's result, in v1.1's container as the test user. Every call that applies a ruleset runs in a child process, never in the pytest worker; the checks before a restriction (arguments, the rules file, the ABI, existing folders) run in-process with the ABI injected. No test is skipped without Landlock: every `make check` runs on a kernel the factory itself requires. Under a stage that is itself confined the tests still work, because rulesets stack and `tmp_path` lies under the run's `TMPDIR`. Only the hand probe and the first real runs can show what Claude Code, `uv`, pip and semgrep write, `sudo` with `timeout` and `env -i` around the wrapper as the real agent user, and Podman's seccomp profile. Code that runs only in a child process is not counted by pytest-cov 7, and `make mutants` may report survivors in `landlock.py` and `confine.py` for the same reason: the acceptance reads them as such. (Feature)
