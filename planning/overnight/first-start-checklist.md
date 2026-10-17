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
