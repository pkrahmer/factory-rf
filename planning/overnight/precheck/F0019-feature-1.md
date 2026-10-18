# Pre-check F0019, round 1: the feature, its human's changes and its decisions

I played this against v1.1's shipped roles (`claude/agents/*.md`), `factory/feature-form.md`, `factory/story-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml` and the `Makefile`, and against factory-rf as it is on 2026-10-18. The six stories have their own files beside this one. Their verdicts are:

| Story | Verdict |
|---|---|
| S0001 | pass with one recommended edit (E1) |
| S0002 | pass with one required edit (E1, smoke test 1) and two recommended (E2, E3); changes 1 and 2 first |
| S0003 | refuse as drafted (E1: `PLR0913`); pass with E1 and the recommended E2 |
| S0004 | refuse as drafted (E1: two earlier tests turn red without a leave; E2: follows S0003's E1); pass with E1, E2 and the recommended E3, E4 |
| S0005 | pass |
| S0006 | pass |

## How the facts were checked

- **Read.**
  - The feature, the six stories, the design (`write-guard-landlock-2026-10-17.md`), the drafter's brief and the probe (`planning/overnight/landlock_probe.py.txt`).
  - F0018's feature and its archived stories and acceptances. Its intake asked when a story touched something the Scope did not name. F0019's Scope names every module the stories touch; only S0004's two earlier tests are missing (F1).
  - The code and tests named in each story's file.
- **Run, in temporary folders outside the repository, all removed.**
  - `factory-check-story` on the six stories: all `: ok`.
  - The pipeline reader on the template and on factory-rf's own `factory/pipeline.yml` (both valid). An appended `tool_paths` is refused today with `unknown key: tool_paths`.
  - ruff and bandit with the project's configuration on scratch files: `os.execvpe` is `S606`/`B606`, and a six-parameter function is `PLR0913`.
  - The three smoke greps of S0006 on today's tree.
- **Read-only, in `factory-self-factory-1`:** the kernel, `/dev`, `/tmp`, the agent's home and the checkout's root.
  - One `grep` in Claude Code's binary for the `/tmp` paths below was refused by the session's permission classifier. I did not work around it, so that point is left to the probe (H3).
  - Not read: any token file.
- **Not run:** any Landlock call. This host is Windows, and the container may not be changed.

## The kernel's interface, checked

From Landlock's documented user-space interface (`include/uapi/linux/landlock.h`, the kernel's Landlock documentation), as I know it; nothing was fetched.

| | |
|---|---|
| System calls | `landlock_create_ruleset` 444, `landlock_add_rule` 445, `landlock_restrict_self` 446, the same on x86_64 and aarch64 (the unified table) |
| Version query | `landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION = 1)` returns the ABI. It fails with `EOPNOTSUPP` when Landlock is built but not enabled at boot, and `ENOSYS` when it is absent or refused by seccomp; S0001 reads either as 0 |
| Rule | `LANDLOCK_RULE_PATH_BENEATH = 1`, `struct landlock_path_beneath_attr { __u64 allowed_access; __s32 parent_fd; }` packed (12 bytes), `parent_fd` opened `O_PATH` |
| Restriction | needs `prctl(PR_SET_NO_NEW_PRIVS = 38, 1, 0, 0, 0)` (or `CAP_SYS_ADMIN`); layers stack, at most 16 |
| ABI 1 (Linux 5.13) | `EXECUTE` 0, `WRITE_FILE` 1, `READ_FILE` 2, `READ_DIR` 3, `REMOVE_DIR` 4, `REMOVE_FILE` 5, `MAKE_CHAR` 6, `MAKE_DIR` 7, `MAKE_REG` 8, `MAKE_SOCK` 9, `MAKE_FIFO` 10, `MAKE_BLOCK` 11, `MAKE_SYM` 12 |
| ABI 2 (5.19) | `REFER` 13 (renames and links between folders; before it, reparenting was always refused) |
| ABI 3 (6.2) | `TRUNCATE` 14 |
| ABI 4 (6.7) | `handled_access_net`: `BIND_TCP`, `CONNECT_TCP` |
| ABI 5 (6.10) | `IOCTL_DEV` 15 |
| ABI 6 (6.12) | `scoped`: abstract UNIX sockets, signals |
| ABI 7 (6.15) | audit-logging flags of `landlock_restrict_self` |

- **The design matches.** `WRITE_RIGHTS = 0x7FF2` (bits 1 and 4 to 14, twelve rights) and `FILE_RIGHTS = 0x4002` are right, and so is the minimum ABI 3 (decision 2).
- **Renames.** With `REFER` handled and every folder rule granting all twelve rights, a rename between two allowed folders is allowed. A rename into a folder without a rule is refused with `EACCES`. `EXDEV` appears only where the destination would grant more than the source, which this rule set never makes.
- **The machine.** v1.1's container runs `6.18.54.1-microsoft-standard-WSL2`, x86_64, under Docker's default seccomp profile, which the probe of 2026-10-17 passed. `/sys/kernel/security` is not mounted there, so the LSM list cannot be read inside.

### Can a confined process run `sudo`?

No.

- `no_new_privs` survives every `execve` and makes the kernel ignore set-uid bits.
- sudo 1.9.13 (the image's `1.9.13p3`) detects it and refuses with `sudo: The "no new privileges" flag is set, which prevents sudo from running as root.`.
- So the wrapper must come after `sudo`. S0004's command line puts it after `sudo`, `timeout` and `env -i` (whose `-i` would otherwise drop `TMPDIR`) and before the login shell and `claude`: **S0004's order is right.** The reasons are in `F0019-S0004-1.md`.
- The removal of the temporary folder is a separate `sudo` started by the unconfined factory, so it is unaffected.

## The human's changes

1. **`factory-confine` in `[project.scripts]`: correct.**
   - The line goes after `factory-guard = "factory.entry.guard:main"`, line 18.
   - It is needed **before S0002** (criterion 13, the smoke tests, and S0004's tests, which start the installed script).
   - `uv run` reinstalls the editable project when `pyproject.toml` changes, so the checkout's `.venv` gets the script on the tester's first `make test`.
   - `uv.lock` does not change, because scripts are not locked.
2. **The widened exception in `CLAUDE.md`: correct, needed before S0002.**
   - The markers are exactly ruff's `S606` and bandit's `B606` for `os.execvpe`.
   - The intake and the reviewer read `CLAUDE.md`, so without it S0002 is a question at intake.
3. **R12's sentence: correct, recommended with 2.**
4. **`.coverage` and `.licenses-requirements.txt` into `.reports/`: correct.**
   - pytest-cov honours `data_file`, and its xdist parts are written as `.reports/.coverage.*`.
   - `make test` already makes `.reports`, and the new `licenses` recipe makes it too.
   - `.reports/` is git-ignored.
   - `[tool.mutmut]` runs with `-p no:cov`, so nothing else reads `.coverage`.
   - No test pins either recipe (`tests/test_make_search.py`, `test_template_makefile.py` read other things).
   - Harmless now. Recommended **with change 1, before S0002**.
5. **`tool_paths`: the list is right and every entry passes S0003's rule. The order is right, but one warning is missing (F3).**
   - The order: the old image refuses the key, so `self` is stopped, then the key is added, then the image is rebuilt.
   - The warning: if `self`'s image is rebuilt for any other reason after S0004 is merged and before this change, the guard goes live with no tool paths. Every `make check` is then refused `.venv`, the caches and `.reports`, and every work item stalls on a red check.
6. **The hand probe: needed, but too loose to be repeatable (F4).**
   - It does not say how to write a rules file or how to get the real command line. Running the runtime itself does both: `sudo`, `timeout`, `env -i`, the wrapper, the login shell, `CLAUDE_CONFIG_DIR` and `TMPDIR`, exactly as a stage has them.
   - It comes after all six stories are built. Decisions 3 and 9 and the `/tmp` findings (H3) could each change a story, so H1 recommends a cheaper early probe as well.

**Missing changes.** None beyond F3's warning.

- No dependency is added and no `security/` or `.secrets.baseline` entry is needed.
- The image needs no change: `uv sync --frozen --no-dev` installs the console script, the sudoers rule allows `/bin/sh`, and `/state/runs` is `2750 factory:factory-work`, so the agent reads `confine-<session>.json`.
- `[tool.mutmut]` needs no change, as long as the marker test keeps its name (F2).

## The decisions

- **1** (ctypes, no binding): right. The probe proves about forty lines. **2** (twelve write rights, minimum ABI 3, 8-byte attribute): right (table above).
- **3** (a file rule writes in place only): right as Landlock behaves. Its risk is wider than the work item, which the intake, the reviewer and the smoke tester rarely `Edit`: the documenter's `README.md` is a single-file target too, and it is edited in most stories.
  - If Claude Code's `Edit` saves by writing a new file and renaming it over the old one, both are refused. I could not check this: the classifier refused the `grep` of Claude Code's binary.
  - Decision 3's own fallback (allow the folder, and let the undo narrow) works for the work item. For `README.md` the folder is the checkout's root, which decision 6 forbids. There is no fallback in the feature for that case, so it would need a decision of its own.
  - So decision 3 should be confirmed before S0003 fixes the targets: H1, and F5 names the README.
- **4** (fail closed, links refused): right.
- **5** (the wrapper's arguments, rules file, `exec`): right, including the mode `0640` in `/state/runs` (`2750`, group `factory-work`).
- **6** (missing folders made, a missing file widened to its folder, never the root): right. It is why change 4 is needed.
- **7** (leave for the structural tests): right, except **the optional rename**. `[tool.mutmut]` deselects the marker test by name. A renamed test would run under mutmut, fail on the rewritten source, and stop `make mutants` at F0019's acceptance (F2).
- **8** (`tool_paths` in the pipeline definition): right.
- **9, the `CLAUDE_CONFIG_DIR` assumption.** Sound in its aim, unconfirmed in its effect.
  - The variable names the folder Claude Code uses anyway (`/home/agent/.claude`), so `settings.json`, the agents and the transcripts stay where they are. Only `.claude.json` should move into the folder, which a folder rule allows, and the home's root stays closed.
  - The container shows the state it changes: `/home/agent/.claude.json` (52 KB, `0600`), and `.claude/backups/`, `policy-limits.json`, `remote-settings.json`, `session-env/`, `shell-snapshots/` inside `.claude`.
  - What I could not confirm: that this Claude Code version (2.1.296) writes no lock or backup at the home's root when the variable is set, and reads nothing it needs from the old `~/.claude.json`. Both are cheap to see without Landlock (H1).
  - A residue that Landlock cannot close: inside `~/.claude` an agent may still create a user `CLAUDE.md`, skills or commands that later runs read. That is F0012-S0025's open point, unchanged by this feature.
- **10** (device files): right. All seven exist in the container.
- **11** (the run's temporary folder): right. It also ends the growth of `/tmp/pytest-of-agent`.
- **12, the factory stops without Landlock.** Recommended as written; confirm it.
  - A fallback to the hook would silently keep only the `Edit`/`Write` guard on exactly the machine that lacks the kernel's.
  - The item checks the ABI and the wrapper's `PATH`. A seccomp profile that allows the version query but refuses `landlock_restrict_self` would pass it, but the next item, `agent-run-probe`, runs through the wrapper (S0004) and fails. The stop is still `preflight_failed`, before any stage.
  - At work (Podman on WSL2), the kernel is the WSL kernel. 6.6 gives ABI 3 exactly, which is enough. Whether Landlock is enabled in that kernel's LSM list is not known from here (H2).
- **13: wrong** as it stands. Two earlier tests run a real call through `build_boundaries` and turn red once it always confines (F1, with S0004's E1).
- **14** (what the agent sees): right. A refused rename gives `EACCES` too (see above).
- **15** (protected paths inside an allowed folder), **16** (the cross-check) and **17** (template and demo): right.
- **18** (how the rules are tested): right. Rulesets stack under a confined stage, `tmp_path` lies under the run's `TMPDIR`, and child-only code is invisible to pytest-cov 7 and to mutmut's in-process trampolines.
  - One more consequence: from S0005 on, two earlier tick tests need the real kernel too (see `F0019-S0005-1.md`).

## Points for the human, with the recommended answers

- **H1. Probe before you build?** The decisions only a real run can confirm are 3 (in-place `Edit`), 9 (`CLAUDE_CONFIG_DIR`) and H3 (`/tmp`). Each could change S0003's or S0004's text.
  - (a) Probe now, in a throwaway container of today's image.
    1. Run `claude -p` once under `sudo -u agent` with `CLAUDE_CONFIG_DIR=/home/agent/.claude`, and see whether `/home/agent/.claude.json` and anything else at the home's root is touched.
    2. Then wrap the same call in the 2026-10-17 probe script, changed to restrict to the planned rules and then `os.execvp` `claude`: the write paths of a copy of the checkout, change 5's tool paths, `~/.claude`, the device files and a `TMPDIR`.
    3. Ask it to `Edit` a work-item file and `README.md` and to run `make check`.

    Recommended: about half an hour, and it moves the cheapest fixes before about $20 of stories.
  - (b) Rely on change 6 after all six stories.
- **H2. Decision 12 and the machine at work.** Recommended: **confirm decision 12.** Then, once, in a container under Podman at work, run `python3 -c 'import ctypes; print(ctypes.CDLL(None, use_errno=True).syscall(444, None, 0, 1))'`. It must print 3 or more; `-1` means no Landlock there.
- **H3. Three folders in v1.1's container's `/tmp`** were made by the agent user: `/tmp/claude-1001` and `/tmp/cc-socks` (Claude Code, last at 13:11) and `/tmp/semgrep-mcp` (at 12:36, with the first `make check`'s `.semgrep` and caches).
  - If any of them is a fixed path that ignores `TMPDIR`, it is refused under the guard. In a fresh container (the rebuilt one) that path does not exist yet, so the refused `mkdir` may end Claude Code's `Bash` tool or `make sast`.
  - Recommended: **check them in H1's probe or in change 6** (F4 lists them). A fixed path that is needed becomes a story, because a tool path cannot name `/tmp`.
- **H4. Rebuilding `self` mid-feature.** Recommended: **do not rebuild `self` between S0004's merge and change 5** (F3).
  - If a rebuild is needed after S0003, you may instead add `tool_paths` right after that rebuild, since the hook and the undo ignore them. Then no later rebuild can go live without them.
- **H5. S0004's size.** Recommended: **keep it whole**, with its edits (`F0019-S0004-1.md`, H2).

## Verdict

`F0019 feature.md: one required edit (F1, decision 13 and the Scope, with S0004's E1) and four recommended (F2 decision 7, F3 change 5, F4 change 6, F5 decision 3); changes 1 to 4 correct; decisions 12 and 3 and the CLAUDE_CONFIG_DIR assumption sound, 3 and 9 to be confirmed by a probe, recommended before S0001 (H1)`

## Replacement texts

### F1 (required, with S0004's E1): decision 13 and the Scope

In `## Scope`, replace

```text
- The tests each story names, under `tests/`, and the earlier test modules named in decisions 7 and 12.
```

with

```text
- The tests each story names, under `tests/`, and the earlier test modules named in decisions 7, 12 and 13.
```

In `## Decisions taken for the human`, replace decision 13 with

```text
13. The runtime confines its calls when it is built with the wrapper's command (`confine_executable`). `build_boundaries` builds it so by default, and its callers in the package (`factory.entry.run`, `boundaries_from_environment`) never pass another value (a test pins the default). The tests of earlier stories that build the runtime directly build it without the argument and keep their command lines unchanged. The two earlier tests that run a call through `build_boundaries` get a leave, for S0004: `tests/entry/test_wiring_boundaries.py`, the test `test_the_built_agent_runtime_keeps_its_run_files_under_runs`, and `tests/entry/test_wiring_login.py`, the test `test_the_built_runtime_hands_the_login_file_s_token_to_claude`, whose `build_boundaries` calls gain `confine_executable=None` (their requests have no `PATH`, and their stand-in records its calls in a folder no rule allows); the tester makes these changes, nothing else in those modules. A request without guard settings is still confined, with no path of the checkout. (S0004)
```

### F2 (recommended): the marker test keeps its name

In decision 7, replace

```text
(it also expects `noqa: S606` and `nosec B606` on the one `os.execvpe` line and may be renamed to `test_the_only_suppression_markers_are_the_six_in_the_process_wrapper`)
```

with

```text
(it also expects `noqa: S606` and `nosec B606` on the one `os.execvpe` line, and keeps its name: `[tool.mutmut]` in `pyproject.toml` deselects it by that name)
```

### F3 (recommended): no rebuild before change 5

In change 5, after the sentence `It must not come earlier: the running image refuses an unknown key with \`pipeline_definition_invalid\`, and S0003's reader accepts it only once the image is rebuilt.`, insert

```text
Until then, do not rebuild `self`'s image from a `main` that holds S0004: the rebuilt image would confine every run with no tool paths, and every `make check` would be refused `.venv`, the caches and `.reports`. If `self` must be rebuilt after S0003 is merged, add this key right after that rebuild instead (the hook and the undo ignore it).
```

### F4 (recommended): the hand probe through the runtime itself

Replace change 6 with

````text
6. Then, before starting `self` again: a hand probe through the runtime itself, so that `sudo`, `timeout`, `env -i`, the wrapper, the login shell, `CLAUDE_CONFIG_DIR` and `TMPDIR` stand as a stage has them. Build the image as for every compose call from factory-rf (`docker compose -f image/compose.yml build`, with `FACTORY_INSTANCE=self` and the repository URL), then, from the repository root, start a throwaway container of it:

   ```sh
   docker run --rm -it --entrypoint /bin/sh \
     -v factory-self_work:/mnt/work:ro \
     -v "$PWD/image/secrets/claude-token:/home/agent/.claude-token:ro" \
     factory-self-factory
   ```

   and in it, as the factory user:

   ```sh
   umask 002
   cp /opt/factory/claude/settings.json /home/agent/.claude/settings.json
   cp -a /mnt/work/checkout /work/probe
   printf '# Probe\n' > /work/probe/probe-item.md
   ls -a /tmp /home/agent > /work/before.txt
   python - <<'EOF'
   from datetime import timedelta
   from decimal import Decimal
   from pathlib import Path
   from factory.adapters.claude_runtime import ClaudeCodeRuntime
   from factory.domain.agent_runs import AgentDefinition, AgentRunRequest, GuardSettings

   checkout = Path("/work/probe")
   tool_paths = [".venv/*", ".mypy_cache/*", ".ruff_cache/*", ".pytest_cache/*", ".import_linter_cache/*", ".reports/*", "mutants/*", "~/.cache/*", "~/.semgrep/*"]
   runtime = ClaudeCodeRuntime("claude", Path("/state/runs"), login_file=Path("/home/agent/.claude-token"), confine_executable="factory-confine")
   guard = GuardSettings(root=checkout, write_paths=["probe-item.md", "README.md", "src/*"], protected_paths=[], tool_paths=tool_paths)
   agent = AgentDefinition(name="coder", model="sonnet", tools=["Read", "Edit", "Bash"], budget_usd=Decimal("2"), instructions="You probe the write guard: do exactly the steps of the prompt and report each result.")
   prompt = (
       "1. With Edit, add the line 'edited' to probe-item.md. "
       "2. With Edit, add the line 'probe' at the end of README.md. "
       "3. With Bash: touch /tmp/outside; touch /work/probe/outside.txt; touch \"$TMPDIR/inside\"; ls -a \"$TMPDIR\". "
       "4. With Bash: make check. "
       "End with the decision question; the entry gives each step's result and every error text verbatim."
   )
   request = AgentRunRequest(agent=agent, prompt=prompt, allowed_decisions=["question"], time_limit=timedelta(minutes=30), working_directory=checkout, environment={"PATH": "/opt/factory/.venv/bin:/usr/local/bin:/usr/bin:/bin", "HOME": "/home/agent"}, guard=guard, os_user="agent")
   result = runtime.run(request)
   print(result.end_reason, result.cost_usd)
   print(result.entry)
   EOF
   ls -a /tmp /home/agent | diff /work/before.txt - ; ls -la /home/agent/.claude
   git -C /work/probe status --short
   ```

   Expected: steps 1 and 2 succeed (Claude Code's `Edit` writes in place; if they fail with `EACCES`, decision 3's fallback applies, and for `README.md` it needs a decision); step 3 gives `Permission denied` for the first two `touch`es and lists `inside`; step 4 ends `check: green`; afterwards `/tmp` holds no `factory-run-*` and no new `claude-1001`, `cc-socks` or `semgrep-mcp`, `/home/agent` no new entry at its root, and `/home/agent/.claude` a `.claude.json`. A path the probe finds refused that a tool needs is a line for change 5 (a tool's state in the checkout or the home) or a story (a fixed path in `/tmp`, the runtime's own needs). Then rebuild and start `self` (`docker compose -f image/compose.yml up -d --build`, with `FACTORY_INSTANCE=self` and the repository URL as for every compose call from factory-rf).
````

### F5 (recommended): decision 3 names the README

In decision 3, after the sentence `Claude Code's \`Edit\` must therefore write the work item in place: the hand probe (change 6) confirms it; if it does not, the fix is to allow the work item's folder instead (the undo already reverts every other path in an \`in-progress/\` folder).`, insert

```text
The same holds for the documenter's `README.md`, a single-file target edited in most stories, whose folder is the checkout's root and so can never be allowed (decision 6): if `Edit` does not write in place, the documenter's README edits are refused, and that needs a decision before the guard goes live.
```
