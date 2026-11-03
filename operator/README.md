# Kumpel's skill (staging)

Kumpel is the product; kumpel-factory, this repository, is one of its components. This folder stages another: `kumpel`, a skill that lets an agent (Claude Code, or opencode at work) run a factory instance with its human: watch the work items' pull requests, answer the factory's questions within the feature's decisions, check and (when allowed) merge finished stories, start the next story, and shape stories and features on request. The plan and its decisions are in `planning/operator-skill/DESIGN.md`.

**Second version, 2026-11-01.** The first version was tried on the todo demo (three stories, `planning/operator-skill/TRIAL-1.md`); this one carries its fixes. Next: a trial at work with opencode against the Cloud Run job. Until then, nothing here is used. Once it holds, it moves to a repository of its own, `kumpel-skill`, and this folder goes (the human, 2026-10-31).

## What is here

The map of the folder: each file, the story that made or last reshaped it (the skill's own scripts came before the factory built this folder), and its use.

| Path | Story | Use |
|---|---|---|
| `site.env.example` | F0048-S0001 | every key of the site file, each with a comment and a made-up value |
| `lib/site.sh` | F0048-S0001 | the loader every operator script sources: `site_path`, `site_load`, `site_require`, `site_value` |
| `lib/hosting.sh` | F0048-S0003 | the hosting client: `hosting_token`, `hosting_api`, `hosting_repo_api`, `hosting_git`, with the token from `SITE_TOKEN_CMD` or `gh` |
| `bin/site` | F0048-S0001, F0048-S0009 | the command for the site file: `path`, `init`, `show`, `get`, and `check`, the read-only checks that say whether a machine is ready |
| `bin/sanitise` | F0048-S0006 | strips the site's names and the tokens from text that leaves the machine; `sanitise check FILE...` proves a file clean |
| `job/job.sh` | F0048-S0005 | the factory's Cloud Run job: `create`, `update`, `execute`, `delete`, `log`, `status` |
| `skill/kumpel/SKILL.md` | | the skill: what to read first, the loop, the switches |
| `skill/kumpel/references/` | | the standing orders, how to answer, how to approve, how to shape |
| `skill/kumpel/scripts/settings.sh` | | the switches, and the repository and checkout when the site file does not give them |
| `skill/kumpel/scripts/status.sh` | | the state of the work items' pull requests, from the hosting service |
| `skill/kumpel/scripts/wait.sh` | | waits for the next event |
| `skill/kumpel/scripts/approval.sh` | | the six approval checks' facts |
| `skill/kumpel/scripts/next-story.sh` | | the next story of the build order |
| `skill/kumpel/scripts/start-story.sh` | | starts a story |
| `skill/kumpel/scripts/comment.sh` | F0048-S0012 | posts a signed comment |
| `skill/kumpel/scripts/merge.sh` | F0048-S0008 | merges an approved story and waits for its archive |
| `skill/kumpel/scripts/reset-to-tag.sh` | F0048-S0008 | resets a trial repository to a tag |
| `opencode/command/kumpel.md` | | the command `/kumpel [<switch> on\|off]` for opencode |
| `claude/commands/kumpel.md` | | the same command for Claude Code |

Kumpel signs everything it does. A comment ends with the line `— Kumpel, for the human who owns this project` and the marker `<!-- kumpel -->`, a start commit has the author `Kumpel <kumpel@noreply.invalid>`, and a merge commit says `Merged by Kumpel after the six approval checks.` So a reader of the pull request, the journal or the history can tell Kumpel's acts from the human's, although both use the human's token.

## Installing (for the trial)

Both tools read Claude Code's skill folder, so one copy serves both:

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/operator/skill/kumpel" ~/.claude/skills/kumpel
```

Then the command: for opencode `cp operator/opencode/command/kumpel.md ~/.config/opencode/command/`, for Claude Code `cp operator/claude/commands/kumpel.md ~/.claude/commands/`. Start the tool again, so that it reads the skill list. The first act of the skill asks for the repository and the checkout and writes `~/.config/kumpel/settings.json`, which never enters a repository.

## Needs

`gh` logged in for the project's GitHub, `git`, `python3`, and a POSIX shell. For an instance in a Cloud Run job, `gcloud` for the job's log when a stop needs its reason; status itself comes from GitHub alone.
