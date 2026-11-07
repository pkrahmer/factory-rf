# The operator folder

This folder holds what an operator runs next to a factory [instance](../docs/project-guide/glossary.md): the skill `kumpel`, the scripts for the site file and the Cloud Run job, and the files that set up a VM. Kumpel is the product; kumpel-factory, this repository, is one of its components.

The skill lets an agent (Claude Code, or opencode at work) run an instance together with you. It watches the pull requests of the [work items](../docs/project-guide/glossary.md), answers the factory's questions within the feature's decisions, checks and (when you allow it) merges finished stories, starts the next story, and shapes stories and features on request. Its plan is in `planning/operator-skill/DESIGN.md`.

The skill is a trial. Nothing here is used until a trial at work with opencode against the Cloud Run job has shown that it holds. After that it moves to a repository of its own, `kumpel-skill`, and this folder goes.

Where to read next:

- [Setting up an operator's machine](../docs/operator-guide/site.md): the whole setup, from a machine with nothing on it to a running job and a skill that drives it.
- [The operator guide](../docs/operator-guide/README.md): install, configure and run an instance.

## Installing

1. Write the site file and fill in its values, at least `SITE_REPOSITORY` and `SITE_CHECKOUT`. The file never enters a repository. Run this from the root of this repository:

   ```console
   $ sh operator/bin/site init
   site: wrote <path>; edit it, then run: site check
   ```

2. Check the machine. The command is read-only and ends with `site: ready` when every check passes:

   ```sh
   sh operator/bin/site check
   ```

3. Link the skill into Claude Code's skill folder. Both tools read that folder, so one copy serves both. Run this on the operator's machine, from the root of this repository:

   ```sh
   mkdir -p ~/.claude/skills
   ln -s "$(pwd)/operator/skill/kumpel" ~/.claude/skills/kumpel
   ```

4. Copy the command `/kumpel [<switch> on|off]` for your tool, and start the tool again so that it reads the skill list. For opencode:

   ```sh
   cp operator/opencode/command/kumpel.md ~/.config/opencode/command/
   ```

   For Claude Code:

   ```sh
   cp operator/claude/commands/kumpel.md ~/.claude/commands/
   ```

5. Write the settings file. The skill takes the repository and the checkout from the site file. When the site file gives both, the settings file holds only the switches, and `init` takes no argument. Otherwise the skill asks for both, and you pass them to `init`:

   ```sh
   sh operator/skill/kumpel/scripts/settings.sh init
   sh operator/skill/kumpel/scripts/settings.sh init <owner/name> <checkout>
   ```

   The file is `~/.config/kumpel/settings.json`, or the path in `KUMPEL_SETTINGS`. A new file has `merge` off, and `answer` and `start_next` on.

## What you need

- `git`, `curl`, `python3` and a POSIX shell.
- A hosting-service token, from `SITE_TOKEN_CMD` in the site file or, without it, from a `gh` login.
- `gcloud`, for an instance in a Cloud Run job: it creates the job and reads its log when a [stop](../docs/project-guide/glossary.md) needs its reason. The status of the work items comes from the hosting service alone.

## How Kumpel's acts are told from yours

Kumpel works with your token, so it signs everything it does. A reader of the pull request, the journal or the history can then tell its acts from yours.

- A comment ends with the line `— Kumpel, for the human who owns this project` and the marker `<!-- kumpel -->`.
- A start commit has the author `Kumpel <kumpel@noreply.invalid>`.
- A merge commit says `Merged by Kumpel after the six approval checks.`

## Reference

### Files

| Path | Use |
|---|---|
| `site.env.example` | every key of the site file, each with a comment and a made-up value |
| `lib/site.sh` | the loader every operator script sources: `site_path`, `site_load`, `site_require`, `site_value` |
| `lib/hosting.sh` | the hosting client: `hosting_token`, `hosting_api`, `hosting_repo_api`, `hosting_git`, with the token from `SITE_TOKEN_CMD` or `gh` |
| `bin/site` | the command for the site file: `path`, `init`, `show`, `get`, and `check`, the read-only checks that say whether a machine is ready |
| `bin/sanitise` | strips the site's names and the tokens from text that leaves the machine; `sanitise check FILE...` proves a file clean |
| `job/job.sh` | the factory's Cloud Run job: `create`, `update`, `execute`, `delete`, `log`, `status` |
| `skill/kumpel/SKILL.md` | the skill: what to read first, the loop, the switches |
| `skill/kumpel/references/` | the standing orders, how to answer, how to approve, how to shape |
| `skill/kumpel/scripts/settings.sh` | the switches, and the repository and checkout when the site file does not give them |
| `skill/kumpel/scripts/status.sh` | the state of the work items' pull requests, from the hosting service |
| `skill/kumpel/scripts/wait.sh` | waits for the next event |
| `skill/kumpel/scripts/approval.sh` | the six approval checks' facts |
| `skill/kumpel/scripts/next-story.sh` | the next story of the build order |
| `skill/kumpel/scripts/start-story.sh` | starts a story |
| `skill/kumpel/scripts/comment.sh` | posts a signed comment |
| `skill/kumpel/scripts/merge.sh` | merges an approved story and waits for its archive |
| `skill/kumpel/scripts/reset-to-tag.sh` | resets a trial repository to a tag |
| `opencode/command/kumpel.md` | the command `/kumpel [<switch> on\|off]` for opencode |
| `claude/commands/kumpel.md` | the same command for Claude Code |
| `vm/setup.sh` | prepares a fresh Ubuntu machine and installs the factory's service |
| `vm/factory.service` | the factory as a system service, one instance per name |
| `vm/Dockerfile` | the stage image of every stage's containers |
| `vm/git-credential-factory` | git's credential helper, which hands out the hosting token |
| `vm/job-start.sh` | the command of a Cloud Run job: it builds an instance and ends in `factory-run` |
| `template/` | the start of a new project: a pipeline definition, a `CLAUDE.md` and a `Makefile` |

### Settings file

| Name | What it does | Default | Example |
|---|---|---|---|
| `merge` | Kumpel merges an approved story itself | off | `merge on` |
| `answer` | Kumpel answers the factory's questions | on | `answer off` |
| `start_next` | Kumpel starts the next story when one is archived | on | `start_next off` |
| `KUMPEL_SETTINGS` | the path of the settings file | `~/.config/kumpel/settings.json` | `/tmp/kumpel.json` |
