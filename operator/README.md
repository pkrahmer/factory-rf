# Kumpel's skill (staging)

Kumpel is the product; kumpel-factory, this repository, is one of its components. This folder stages another: `kumpel`, a skill that lets an agent (Claude Code, or opencode at work) run a factory instance with its human: watch the work items' pull requests, answer the factory's questions within the feature's decisions, check and (when allowed) merge finished stories, start the next story, and shape stories and features on request. The plan and its decisions are in `planning/operator-skill/DESIGN.md`.

**First version, 2026-10-31, written by hand and not yet tried.** It will be tried and finished with the human on the todo demo after F0047 (the factory runs in a Cloud Run job). Until then, nothing here is used. Once it holds, it moves to a repository of its own, `kumpel-skill`, and this folder goes (the human, 2026-10-31).

## What is here

| Path | What |
|---|---|
| `skill/kumpel/SKILL.md` | the skill: what to read first, the loop, the switches |
| `skill/kumpel/references/` | the standing orders, how to answer, how to approve, how to shape |
| `skill/kumpel/scripts/` | `settings.sh` (the switches), `status.sh` (the state from GitHub), `wait.sh` (wait for the next event), `approval.sh` (the six checks' facts), `start-story.sh` |
| `opencode/command/kumpel.md` | the command `/kumpel [<switch> on|off]` for opencode |
| `claude/commands/kumpel.md` | the same command for Claude Code |

## Installing (for the trial)

Both tools read Claude Code's skill folder, so one copy serves both:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/operator/skill/kumpel" ~/.claude/skills/kumpel
```

Then the command: for opencode `cp operator/opencode/command/kumpel.md ~/.config/opencode/command/`, for Claude Code `cp operator/claude/commands/kumpel.md ~/.claude/commands/`. Start the tool again, so that it reads the skill list. The first act of the skill asks for the repository and the checkout and writes `~/.config/kumpel/settings.json`, which never enters a repository.

## Needs

`gh` logged in for the project's GitHub, `git`, `python3`, and a POSIX shell. For an instance in a Cloud Run job, `gcloud` for the job's log when a stop needs its reason; status itself comes from GitHub alone.
