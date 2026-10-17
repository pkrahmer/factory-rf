# opencode probe (2026-10-17): a starting point for a second agent runtime

Asked by the human as a starting point for later planning: could v1.1 run its agents through opencode as a second implementation of the agent-runtime interface (R12)? Probed in v1's container (Debian 12, the human's API key in the environment, never read), with opencode-ai 1.19.3 from npm (the Linux x64 binary, copied to `/tmp/oc-probe/opencode`), model `anthropic/claude-haiku-5-5`, four tiny runs, about $0.01 in all. Kept for discussion: `/tmp/oc-probe` in v1's container (lost when the container is recreated) and the npm package in the session's scratch folder.

## What was seen

- **Headless call:** `opencode run --format json -m <provider>/<model> "<prompt>"`. It waits on stdin when stdin is open: with `< /dev/null` it returns in about a second; without it it hangs until killed (the first two tries timed out after 120 s). Exit 0.
- **Output:** JSON lines, one event per line: `step_start`, `text` (the reply's text with its time span), `tool_use` (tool name, input, `state.status` `completed` or `error`, the error text), `step_finish` (finish reason, `tokens` with input, output, reasoning, cache read and write, and `cost` in USD per step). A run's cost and tokens are the sum over its `step_finish` events. Every event carries `sessionID` and a millisecond timestamp.
- **Sessions:** `--continue` and `--session <id>` resume, `--fork` branches a session; `opencode export <id>` dumps a session as JSON; `opencode stats` sums usage.
- **Agents:** `--agent <name>`; `opencode agent create|list`. The default agent is `build` (mode `primary`). Its own agent file format (not checked in detail).
- **Permissions** in `opencode.json` in the working folder:
  - `"bash": {"*": "deny", "ls*": "allow"}` works per command pattern: a denied call comes back as a `tool_use` event with `status: "error"` and the rule named in the error, and the model goes on. So denials are visible in the output.
  - `"edit": "deny"` does not deny calls: it removes the edit and write tools from the session altogether (the model said it had only read, glob, grep, bash and a few others).
  - `"edit": {"src/*": "allow", "*": "deny"}` also left the session without edit or write tools: path patterns for edit did not work as a per-path allow in this version, or not in this form. A per-path write guard like v1.1's (`factory-guard` as a PreToolUse hook) is therefore not available as configuration; it would need a plugin (opencode has `opencode plugin`) or the factory's undo after the run alone.
- **Side effects:** it keeps a snapshot git repository of the working folder under `~/.local/share/opencode/snapshot/` and starts a file watcher; `HOME` held 165 MB after four runs. Under v1.1 this lands in the agent's home.
- **Other:** `--auto` approves permissions not explicitly denied; `opencode serve` and `--attach` run a server; `--variant` sets reasoning effort; no budget flag and no structured-output (JSON schema) flag was seen in `run --help`.

## What a runtime for v1.1 would need, against the Claude Code runtime

| v1.1 relies on | With opencode |
|---|---|
| One JSON reply with cost, tokens, model time, turns, denials, structured decision | Sum the `step_finish` events for cost and tokens; model time from the `text` spans or `step_start`/`step_finish` timestamps; denials from `tool_use` errors; the decision has to be parsed from the last text or asked for in a fixed form, since no schema flag was seen. |
| A per-run budget and one resume with a quarter of it | No budget flag: the factory would stop the run itself when the summed cost passes the budget, then resume with `--session`. |
| The write-path guard as a hook that refuses a write outside the stage's paths | Not as configuration (see above): a plugin, or rely on the undo. The hardest part. |
| `claude/agents/*.md` | opencode's own agent files, generated from the same source or kept beside it. |
| Login by subscription | An API key per provider (`opencode providers`): every opencode run is paid through the API, also with Anthropic models. |
| `--version`, the probe, the image pin | `opencode --version` works; the binary comes from npm (`opencode-ai`, platform packages) or its installer. |

## For later planning

A feature of about six to eight stories after the handover, built by v1.1 itself: the runtime adapter (call with stdin closed, event parsing, cost and time), the budget stop and resume, the write guard as a plugin (needs its own probe first), the agent files, the image and preflight, the guide. Testing it for real is a run of the todo demo through the API, about $15 to $25. Not before the shakedown run on Claude Code.
