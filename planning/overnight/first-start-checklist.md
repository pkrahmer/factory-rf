# The first start of v1.1 (plan step 2): what the human does, what the session does

v1 keeps running beside it in its own compose project (`factory`); v1.1's is `factory-<instance>` (F0012-S0022), so the two cannot collide. Commands run from `C:\Dev\Projects\factory-rf` in Git Bash.

## The human's three parts

### 1. The repository v1.1 serves

Create an empty private repository on GitHub, for example `pkrahmer/factory-todo-shakedown`, with no README, licence or `.gitignore` (an empty repository). It serves the first start now and the shakedown run of the todo demo (plan step 4) later. Tell the session its name: the session pushes the todo demo's empty project (`demo/todo-service/project/`) as its first commit, so v1.1 finds a `factory/pipeline.yml` and idles with an empty backlog.

### 2. The token

A fine-grained personal access token, limited to that one repository, with these repository permissions: Contents read and write, Pull requests read and write, Issues read and write (labels), Metadata read. No other repository, no account permissions. Then save it, with nothing else in the file:

```bash
mkdir -p image/secrets
```

```bash
notepad image/secrets/hosting-token
```

Paste the token, save, close. `image/secrets/` is ignored by git. On Windows the repository folder under your own account is the protection (operator guide, "The hosting-service token"). Do not paste the token into the chat.

### 3. The agent's login (after the session has started the container)

The session tells you the container's name. Then, in a terminal:

```bash
docker exec -it -u agent <container> claude
```

Complete the login in the browser (your subscription), then `/exit`. For the Podman run the same with `podman exec`; a second login is needed there, because the Podman machine has its own volumes.

## The session's part

1. Push the todo demo's empty project to the new repository as its first commit.
2. Docker Desktop: `FACTORY_REPOSITORY_URL=https://github.com/<you>/<repo>.git FACTORY_INSTANCE=shakedown docker compose -f image/compose.yml up -d --build`; wait for the entrypoint, give the human the container name for the login; then read the health status and the factory log until the preflight passes.
3. The observations of the operator guide, "Log in once as `agent`", each noted with its result in the night log: `sudo` as `agent`; the token's folder refused to the agent (`cat` and `ls`), owned by uid 1000 with `drwx------`; no token in the agent's environment; the modes of what an agent makes (775, 664); `settings.json` refused to the agent; the restore after an agent-made directory; `sudo` to root refused; no push and a `401` from the API as the agent; `/work/.git/hooks` (F0013 decision 15); whether the agent's login survives `docker compose down` and `up` (its `~/.claude.json` lies in `/home/agent`, outside the `claude-home` volume); the disk record at the start; a restart with `docker restart`.
4. The same under Podman (`podman compose`, provider docker-compose v2, instance `shakedown-podman`), plus the restart after `podman machine stop` and `start` (the guide's manual restart).
5. A short real run: one tiny story (not from the todo demo) with a short `time_limit`, to see an agent run end to end and a `time_limit` under `sudo` (F0010 decision 30); then remove it.
6. Each fault: a story for v1 with a test, before the shakedown run. Then both instances down; the volumes stay until the shakedown.

## Results (2026-10-17, the first start)

Instance `shakedown` under Docker Desktop and `shakedown-podman` under rootless Podman 5.8.3 (provider docker-compose v2), both on `pkrahmer/factory-demo-todo` (the todo demo's empty project, commit `0885fef`), image built from `4aaef36e` with the pins of `b642dd31`. Both healthy after one manual `claude` login as `agent`; the preflight's `agent-run-probe` stop clears on the next tick after the login.

Held on both runtimes: the agent runs as `agent`; it cannot list or read `/home/factory/.secrets` (`drwx------`, uid 1000; the mounted file itself shows `-rwxrwxrwx 0 0`); no token in its environment; an agent-made folder is `2775` and a file `664` (umask 0002; the factory's 0022); `settings.json` refused to the agent; `sudo` to root refused; no push credential (`could not read Username`) and `401` from the API; the restore removes an agent-made folder; under Docker the agent's login survives `docker compose down` and `up` (`.credentials.json` is in the `claude-home` volume; `~/.claude.json` is lost and rebuilt).

Faults, for F0014 (built by v1 before the shakedown run):
1. The agent cannot use git in the checkout: `git status` as `agent` fails with `detected dubious ownership in repository at '/work/checkout'` (the checkout is `factory`'s; no `safe.directory` for the agent). Every agent stage that reads a diff or a log is hit.
2. The agent can write `/work/checkout/.git/hooks` (`drwxrwsr-x factory factory-work`), and the factory's git runs hooks as `factory`, who can read the token: the indirect route F0013 decision 15 named, confirmed.
3. Every new instance (a new `claude-home` volume, the Podman machine) needs an interactive `claude` login. The human's word (2026-10-17): every credential is injected from outside, no interactive login: the Claude token from `claude setup-token` (`image/secrets/claude-token`), passed to agent runs only as `CLAUDE_CODE_OAUTH_TOKEN`; the hosting token as today; optionally an API key the same way.
4. The guide: an agent-made folder is `2775` (setgid), not `775`; the login's place (the volume keeps `.credentials.json`); under Podman on Windows the operator's PowerShell may not see the saved connection (`connection "podman-machine-default" not found`): `--url` and `--identity`, or `podman system connection list`.

Not yet observed: a real agent run end to end and a `time_limit` under `sudo` (the tiny story of step 5), after F0014.

5. (found while F0014 was drafted, tested on the running Docker instance) The agent can write the checkout's `.git/config` (`-rw-rw-r-- 1000:1002`, and `.git` itself `drwxrwsr-x`, from `core.sharedRepository=group`): a `core.fsmonitor` line written as `agent` made the factory's own `git status` run a command as `factory` (`PWNED-as-factory`), who can read the hosting token. The config was restored at once. The hooks fix does not cover this (filter drivers, `fsmonitor`, `diff.external` and more run from the config). Fix: the factory alone writes the checkout's `.git` (agents never commit; the factory does); the work tree stays group-writable for the agent.

6. (the human's word, 2026-10-17, for the status map; checked against v1.1's models) The viewer reads GitHub only. Already there: places and ids, `WorkItemState` (stage, blocked, round, attempts, crashes, pull request, hand-over), `claim` (instance, stage, started_at, lease), the cost records (run, stage, role, attempt, started_at, durations, cost), `JournalRecord` (number, speaker, kind), the story form's fixed sections. Missing, as one story of F0014: `JournalRecord` gains `at` (UTC, when written), `stage` (the stage it was written in) and `run` (the agent run it came from, if any); `CostRecord` gains `instance`. All optional for old records, set for every new one. No markers in the body, no change to the pull request.
