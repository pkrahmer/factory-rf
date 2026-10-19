# Security review of the write guard, 2026-10-19 (from reading only)

Brief: `planning/overnight/briefs/security-review-write-guard.md`. The review agent read the code, the docs and the image, and inspected `factory-self-factory-1` read-only with `docker inspect`. A safety stop ended its run while it was writing the confined test script, so **no route was tested in a container**. Every row below comes from reading, and its severity is provisional. Goals: (a) writing outside the write paths, (b) persistence into later runs, (c) reading or leaking a secret, (d) GitHub beyond the factory, (e) a check passing that should fail.

| Route | Goals | Stopped by | Evidence | Severity |
|---|---|---|---|---|
| The project commands (`make check`, `lint`, `test`) run agent-written code as `factory`, unconfined, with the factory's environment and the hosting token readable | b c d e | nothing; known, `docs/decisions.md` "The project commands run as the factory's user and are left for v2" | code reading | high |
| Git-ignored state (`.venv/*`, `.mypy_cache`, `.ruff_cache`, `.import_linter_cache`, `mutants/`, `__pycache__`, `*.pyc`, or a nested `.gitignore` an agent adds) is never reverted, committed or cleaned (`git clean -f -d` without `-x`), so it persists across stages and stories, unseen in the pull request, and later `make check` runs execute or trust it | b e, then c d through the row above | nothing | code reading | high |
| Network egress from a run is open: Landlock restricts writes only, every agent has Bash and `Bash(uv run *)`, and its own login is readable by design | c (the agent's login) | nothing; Landlock ABI 7 network rules filter by port only | code reading | high |
| Files added to the agent's `~/.claude` (a user `CLAUDE.md`, `.claude.json`) persist into later runs | b | partly: `--strict-mcp-config` blocks MCP servers; F0022 closes `skills/` and `commands/` only; already noted open in the decision log | code reading | medium |
| A nested `CLAUDE.md` inside a write path (`src/CLAUDE.md`, `docs/CLAUDE.md`) is loaded by later runs | b | the diff shows it to the reviewer and the human; no protection | code reading | medium |
| A process outliving its run keeps its confinement and network, and can write the tool paths and `~/.claude` during later stages and checks | b | nothing; the `.git` swap variant is noted in the log | code reading | medium |
| opencode (F0020): `~/.cache/*` is a tool path and covers `~/.cache/opencode`, which may hold code opencode loads | b | not checked; the image has no opencode yet | code reading | medium |
| `.git` writes, hooks, `core.fsmonitor`, `core.hooksPath` | a b | the seal, mode `0640`, Landlock; both settings pinned in the factory's git environment | code reading | probably closed |
| The protected paths at the root | a e | Landlock rules and the hook | code reading | probably closed |
| Replacing the work item | a | a file rule allows writing in place only | code reading | probably closed |
| Symlinks and hard links out of a write path | a | Landlock checks the real target; the hook uses realpath | code reading | probably closed |
| The hosting token | c d | its folder is mode `0700`, owned by `factory` (but see the first row) | code reading | probably closed |
| Rewriting `claude/settings.json` or the agents | b | file modes and the sticky bit | code reading | probably closed |
| A symlink committed to `backlog/` that the factory reads later | a | only after the human merges it | code reading | low |
| `/dev/shm` as a channel between runs | b | not checked | — | low |
| `.reports/*` changed by an agent | e | the factory judges the checks by exit status only | code reading | low |

## Proposed stories (each needs the human's say)

1. **Run the project commands as the agent's user under `factory-confine`.** It fits F0019's line (or a new confinement feature). Criterion: a `make check` that tries to read the hosting-token folder or write outside the check's write paths fails with a Landlock denial, and the factory's own git and hosting calls still work.
2. **Remove or rebuild ignored state between stages.** Use `git clean -fdx` except a `.venv` verified against `uv.lock`, or rebuild `.venv` from `uv.lock` before each check, and don't trust tool caches across stages. Criterion: a file an agent drops in `.venv/lib/.../site-packages` or `__pycache__` during one stage is gone before the next stage's checks run.
3. **An egress allowlist for agent runs.** A proxy, or a container network that allows only the model API host (and, for the factory, the hosting host). Criterion: from inside a confined run, a request to any other host fails, and a stage run still completes.
4. **Make `~/.claude` read-only except the state folders Claude Code needs, and protect `CLAUDE.md` at any depth.** It fits F0022, which already closes `skills/` and `commands/`. Criterion: a run that writes `~/.claude/CLAUDE.md` or `src/CLAUDE.md` is denied (or the factory refuses the stage's result).
5. **Kill whatever the agent's user still runs after each run** (for example `pkill -KILL -u agent` before the undo). Criterion: a background process started by a run is gone before the factory's checks start.

## Not tested

Every route above, because no container test ran. The brief's method (throwaway containers of `factory-self-factory`, `--network none`, stand-in secrets, as the agent through `factory-confine`) still stands if the human wants the evidence. It is best done by hand or in a session the human starts for it, not by an unattended helper.
