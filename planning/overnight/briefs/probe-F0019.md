# Brief: probe three facts for F0019 before it is built

## Goal

F0019 (the write guard by the kernel, `planning/overnight/stories/F0019-the-write-guard-by-the-kernel/`) rests on three facts its pre-check (`planning/overnight/precheck/F0019-feature-1.md`, H1 and H3) could not settle from the code. Find each out with one real Claude Code run as the user `agent` under a Landlock rule set, in a throwaway container of v1.1's current image, and write down what was seen:

1. **Does Claude Code's `Edit` tool write a file in place?** Under a rule that allows writing only the file `README.md` (a file rule: `LANDLOCK_ACCESS_FS_WRITE_FILE`, plus `TRUNCATE` on ABI 3+), not its folder, does an `Edit` of `README.md` succeed? If it fails, with what error (a rename or a new temporary file beside it)?
2. **Where does Claude Code write `.claude.json` and its other state?** With `CLAUDE_CONFIG_DIR=$HOME/.claude` and a folder rule on `$HOME/.claude` only (the home's root not allowed), does the run start and finish, and does anything fail to be written? Without `CLAUDE_CONFIG_DIR`, the same rules: what fails?
3. **Which fixed paths outside `TMPDIR` does Claude Code (and its `Bash` tool) write?** With `TMPDIR` pointing to a run folder of its own (allowed), and `/tmp` itself not allowed: do `Bash` commands run (Claude Code's shell snapshot, `/tmp/claude-<uid>`, `/tmp/cc-socks` or anything else)? What does each refusal say?

Also: the ABI the kernel reports in this container, and, if cheap, the same `Bash`-tool check for `uv run ruff --version` (the uv cache under `~/.cache`, allowed or not).

## How

- The image: `factory-self-factory` (v1.1, `3bcee441`). A throwaway container: `docker run --rm --init ...` with an entrypoint of your own (`--entrypoint bash`), as the user `agent` where the run needs it (`--user agent` or `su`/`sudo` as the image allows; say which you used). Never reuse the running instance `factory-self-factory-1` or its volumes; never mount `/work` or `/state` of an instance.
- The agent's login: mount the host file `C:/Dev/Projects/factory-rf/image/secrets/claude-token` read-only at `/home/agent/.claude-token`, as `image/compose.yml` does, and set `CLAUDE_CODE_OAUTH_TOKEN` from it inside the container (for example `export CLAUDE_CODE_OAUTH_TOKEN="$(tr -d ' \t\r\n' < /home/agent/.claude-token)"`). Never print, copy, log or read the token yourself, and never put it on a command line.
- The rules: a small Python script of your own that uses `ctypes` and the three Landlock system calls (444 `landlock_create_ruleset`, 445 `landlock_add_rule`, 446 `landlock_restrict_self`; `prctl(PR_SET_NO_NEW_PRIVS=38, 1, 0, 0, 0)` first), handling the write rights of ABI 3, then `os.execvpe` into the command. Keep it in a folder under `C:/Users/pasca/AppData/Local/Temp/` outside the repository (not under the repository; no `.py` file under `C:/Dev/Projects/`), mount it read-only, and remove it afterwards. The checkout: a folder under `/tmp/probe/checkout` inside the container with a `README.md`, made before the rules apply.
- The run: `claude -p "<a short task: edit README.md replacing one word; then use Bash to run: echo ok > \"$TMPDIR/x\" && cat \"$TMPDIR/x\" && pwd; then answer done>" --tools Read,Edit,Bash --permission-mode bypassPermissions --max-budget-usd 0.30 --output-format json`, with the environment the runtime sets (`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1`, `PYTHONDONTWRITEBYTECODE=1`). If `bypassPermissions` is refused, use what `src/factory/adapters/claude_runtime.py` passes. Run each variant once; at most four runs; a few cents each.
- Observe through the run's JSON result, its stderr, the file's content afterwards, and `ls -la` of the home and `/tmp` before and after. `strace` only if the image has it (do not install anything).

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/probe-F0019-2026-10-18.md`: for each of the three facts (and the extras) what was run, what was seen (the exact error lines, without any token), and what it means for F0019's stories (S0003's targets, S0004's rules and `CLAUDE_CONFIG_DIR`, decision 3 on file rules, the `tool_paths` of change 5), with the exact text change you recommend where a story must change.

## Not

No git commands. No change to any file under `C:/Dev/Projects/` except the one output file. No sub-agents. Never read or print the token. Nothing installed into an image; nothing done to the running instance or any volume. Remove the throwaway container (`--rm`) and your script folder afterwards; if a removal is refused, say so.

## Reply

The three answers in one line each, the ABI, the recommended changes to F0019's stories, and the cost of the runs.
