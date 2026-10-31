# The operator skill: an agent that runs the factory with the human (draft, 2026-10-31)

## The idea

On 2026-10-31 the human and Claude Code ran F0047 together: Claude Code watched the instance, answered the factory's questions within the feature's decisions, approved and merged, started the next story, and shaped stories and features with the human. The human wants the same at work, where the factory runs in a Cloud Run job and the agent at hand is opencode with a company model. This folder plans a skill that lets an agent (opencode at work, Claude Code at home) do most of that.

## What it does (the human, 2026-10-31)

Four of the five jobs; coordinating probes for another session is left out.

| Job | What | Mostly | Switch |
|---|---|---|---|
| Watch | health, the board, the stage, wait for the next event, the status bar | scripts | always on |
| Answer | answer a factory question within the feature's decisions; beyond them, the best answer marked **For the morning**, and go on | judgment | `answer` |
| Approve | the six checks, merge, wait for the archive, rebuild if needed, start the next story | scripts and one judgment | `merge`, `start_next`, `rebuild` |
| Shape | review and draft features and stories, the form check, small fixes on `main` | judgment | on demand |

## Decisions so far (the human, 2026-10-31)

1. **Switches, like opencode's own toggles.** A local settings file, never in the repository, holds one switch per job where a switch makes sense (`merge`, `answer`, `start_next`, `rebuild`); commands turn them on and off (for example `/operator merge off`). The skill reads the file before every act, so a switch takes effect at the next event. With `merge` off the skill runs the checks and writes its verdict on the pull request, and the human merges.
2. **Home: factory-rf, with subfolders where the tools differ.** One skill (a `SKILL.md` with its scripts) serves both tools, since the opencode at work reads Claude Code's skills; `operator/claude/` and `operator/opencode/` hold only what differs, the commands. Versioned with the factory, so what is improved at home reaches work with a pull. No company value in it; those live in the local settings file.
3. **Watching by a wait inside the turn.** After every act the agent calls a wait script as a plain shell command. It blocks until an event (a question as the newest comment, an approval, a health stop, a story archived) or a time limit below the shell tool's own timeout, and prints one line (`event: ...` or `continue: nothing new`). The agent acts or waits again; its turn never ends, so no cron is needed. Each return costs one model call on a cached context; the laptop stays awake and the session open; the human can interrupt at any time.

## What the skill must carry

- **The standing orders**, today in Claude Code's memory: be penurious (small findings fixed on `main` or recorded, not sent back); decide what is unavoidable, quiz only real alternatives with a recommendation first; never stall (beyond the decisions: the best answer, marked For the morning, and go on); plain full sentences for a reader who is not a native speaker; every feature or story id with its short name; a status bar of phone width only when something changed; a log of every act with times from `date -u`.
- **The safety rules**: never read, print or copy a key or a token (size checks with `test -s` only); no push to a work item's branch; stage named files only, pull before push, a failing secrets hook stops the commit; nothing paid in a cloud without the human; no company value in factory-rf.
- **The six approval checks**: the changed files inside their write paths; an earlier test changed only under a leave (the standing one or the human's); the journal's last entries (the smoke test met, no open finding); the `Expect:` lines; no new suppression marker without precedent; the cost.
- **How to answer a question**: read the whole question and the journal entries it refers to; answer within the feature's decisions and the story's Interface; a fault in the story's own text is fixed in the answer (as in F0047-S0004, the writer injected); a change outside the role's write paths (`pyproject.toml`, `security/`) is made on `main` by the skill and named in the answer; a round cap whose rounds each found something real goes on, with the next findings folded into the answer.

## At work, not at home

- **No VM.** A merge that changes the factory's code reaches the job at its next execution (or `gcloud run jobs execute`); "rebuild" becomes that.
- **The factory's state is in the job's memory.** Status comes from GitHub (labels, comments, the board through the API) and from Cloud Logging, where the factory log arrives line by line (it goes to standard output).
- **opencode, not Claude Code.** Its capabilities decide the thin layer: see `CAPABILITIES-REQUEST.md`.
- **A Sonnet-class model, not Opus.** The judgment jobs need their rules written out more explicitly.

## Facts from the opencode at work (`CAPABILITIES-REQUEST.md`, 2026-10-31)

- **One skill serves both tools.** The company's opencode (1.18.34, its own build of the upstream line) loads `SKILL.md` skills with Claude Code's front matter (`name`, `description`), from `.opencode/skills/`, `~/.config/opencode/skills/` and also **`~/.claude/skills/`**, and loads one on demand with its `skill` tool (tried). So the skill itself needs no per-tool copy; per-tool subfolders are needed only for commands, which differ (`.opencode/command/*.md` with `$ARGUMENTS`, `$1`, `$2`, tried with `merge off`).
- **The wait inside the turn works.** The shell tool's default limit is 120 s, but each call takes a `timeout` in milliseconds: 300 s and 600 s were tried, 40 minutes ran in a probe. Three two-minute waits in a row kept the turn open. Calls made in one message run in parallel, so the wait must be the only call of its message.
- **Context and compaction.** A context of 1,000,000 tokens, and opencode compacts by itself (the reporting session had been compacted once).
- **Switches.** A JSON file in `~/.config/factory-operator/`, rewritten by one script that a command calls and read by the skill before every act, works without a restart. Keep its reads and writes behind that one script, so that one permission rule covers them (`external_directory` may ask once).
- **Reach.** `gh` is logged in to the company's GitHub; `gcloud` reaches the cloud project by impersonation and may read Cloud Logging of jobs and run `gcloud run jobs execute` (tried on the sandbox's throwaway jobs, not yet on the factory's own job). Whether the laptop needs the proxy depends on its network.

## Open, for the next quiz

- The switches' defaults, and whether `merge` may depend on the story (no earlier test changed, no human change due).
- Where the local settings file and the log live on the operator's machine.
- Which of today's scratchpad scripts become `operator/common/` scripts, and which become factory commands instead (`factory-watch` already is one).
- Whether the skill itself is built by the factory as a feature (its scripts tested like `vm/`), or written by hand first and tried.
