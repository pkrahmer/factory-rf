---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The image mounts the agent's login token

## Assignment (as of log entry 1)

S0003 taught the factory to hand the token in `FACTORY_CLAUDE_LOGIN_FILE` to each agent run. This story puts the token there in the container, so that a new instance, a new `claude-home` volume and the Podman machine need no interactive login (the first start of 2026-10-17, `planning/overnight/first-start-checklist.md`, "Results", fault 3; the human's answer of the same day). The token is made once with `claude setup-token` and kept on the host as `image/secrets/claude-token`, beside the hosting token; git ignores the folder. `image/compose.yml` bind-mounts it read-only at `/home/agent/.claude-token`, in the agent's home, where the agent may read it, because it is the agent's own login, as its login file in the `claude-home` volume is today; it lies outside that volume, so no mount is nested in another, and outside `/home/factory/.secrets`, which the agent must not enter. The factory itself does not read it: S0003's login shell reads it at each call, as the agent under `sudo`, or as the factory's user on an instance without an agent user. The mount has `create_host_path: false`, like the hosting token's: a missing host file makes Compose refuse to start instead of creating a folder in its place, and an empty file is the operator's way to keep the manual login (FEATURE decision 10). The image sets `ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token`. The files are under `image/`, in the coder's write paths. One test of an earlier story changes by the human's leave (FEATURE decision 14).

## Interface

`image/Dockerfile`: a new line `ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token` directly after `ENV FACTORY_AGENT_USER=agent`, before `USER factory`, with a comment above it: the agent's login, a token from `claude setup-token` that Compose mounts; each agent run's shell reads it. Nothing else in the Dockerfile changes.

`image/compose.yml`: the service's `volumes` gain a bind mount as their fourth entry, directly after `claude-home:/home/agent/.claude` and before the comment that stands above the hosting token's bind mount, so that comment stays with its mount; the hosting token's mount stays the last entry. As ruamel.yaml's safe loader reads it, its keys are, in this order, `type`, `source`, `target`, `read_only` and `bind`: it is a bind mount; its source is the host file `./secrets/claude-token`, its target `/home/agent/.claude-token`; it is read-only; and its bind options set `create_host_path` to false. A comment above it says why: the agent's own login, readable by the agent, outside the token's folder; a missing host file makes Compose refuse to start. Nothing else in the compose file changes: the name, the build, the restart policy, the health check, the environment, the three named volumes and the hosting token's mount stay.

Tests: a new module `tests/test_claude_token_mount.py`, reading the Dockerfile with `dockerfile_instructions` of `tests/dockerfile_support.py` and the compose file with ruamel.yaml's safe loader as `tests/test_compose.py` does. By the human's leave (FEATURE decision 14), and no other change to an earlier story's test: in `tests/test_compose.py` (F0010-S0007, changed by F0013-S0001), `test_the_three_volumes_are_mounted_and_declared` gains the new bind mount as the fourth entry of the expected `volumes`, before the hosting token's (`{"type": "bind", "source": "./secrets/claude-token", "target": "/home/agent/.claude-token", "read_only": True, "bind": {"create_host_path": False}}`); its name and its assertion on the three top-level volumes stay.

## Acceptance criteria

1. The Dockerfile sets `ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token` exactly once, after `ENV FACTORY_AGENT_USER=agent` and before `USER factory`.
2. The variable's name is `factory.domain.settings.CLAUDE_LOGIN_FILE_VARIABLE`, so the setting S0003 reads is the one the image sets.
3. The fourth entry of the compose service's `volumes` has the keys `type`, `source`, `target`, `read_only` and `bind` in that order; it is a bind mount of the host file `./secrets/claude-token`, read-only, whose bind options set `create_host_path` to false, and its `target` is exactly the value of the Dockerfile's `ENV FACTORY_CLAUDE_LOGIN_FILE`.
4. The target's parent folder is `/home/agent`, the parent of the Dockerfile's `FACTORY_CLAUDE_HOME`, which the runtime gives the agent as `HOME`; the target lies neither inside `/home/factory/.secrets` nor inside the target of a named volume (`/work`, `/state`, `/home/agent/.claude`), compared by path parts (`PurePosixPath.is_relative_to`), not by string prefix, since `/home/agent/.claude-token` starts with the text `/home/agent/.claude`. (Test constants avoid the word `token` in their names, for ruff's `S105`.)
5. The service's `volumes` are the three named volumes, the agent's token and the hosting token, in that order (the changed test of `tests/test_compose.py`), and the hosting token's mount is still the last entry (`tests/test_token_folder.py` passes).
6. What must still hold: `FACTORY_TOKEN_FILE` is still the only `ENV` or `ARG` whose name holds `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL`, and the compose `environment` holds no such name (`tests/test_image_credentials.py` passes); the compose project's name is as before (`tests/test_compose_project.py`).
7. The comments say why; the reviewer checks them in the diff, and no test is written for a comment: the one above the new `ENV` and the one above the new bind mount, as the Interface says.
8. `make check` stays green.
9. docs: in the operator guide, *The agent runs as a second user* replaces "Log in once as `agent`" with the agent's login token: run `claude setup-token` once, on the host where Claude Code is installed or in a running container as `agent` (`docker exec -it -u agent <container> claude setup-token`), and save the token it prints, with nothing else in the file, as `image/secrets/claude-token`; on Windows write it as plain text without a byte-order mark (for example `Set-Content -NoNewline -Encoding ascii image/secrets/claude-token <token>`), since PowerShell 5's `>` writes UTF-16, which is not read as the token; Compose mounts it read-only at `/home/agent/.claude-token`, the image sets `FACTORY_CLAUDE_LOGIN_FILE` to that path, and every instance and the Podman machine use the same file with no login of their own. A missing host file makes Compose refuse to start; an empty file means no token, and the agent then needs the manual login (`docker exec -it -u agent <container> claude`), which is kept in the volume `claude-home` (`/home/agent/.claude/.credentials.json`) and survives `docker compose down` and `up`, while `/home/agent/.claude.json` lies outside the volume and is rebuilt by `claude` in a new container (both seen at the first start of 2026-10-17). The host file's permissions, by host: Linux with Docker, `chown 1001:1002` and `chmod 0440` (the agent reads it as its owner; the group `factory-work` lets a run on an instance without an agent user, which runs as `factory`, read it too); Linux with rootless Podman, `chmod 0440` first and then `podman unshare chown 1001:1002`; Windows and macOS, a folder of your own user account that other accounts cannot read. Two morning observations are added: `docker exec -u agent <container> test -r /home/agent/.claude-token && echo readable` prints `readable`, and the probe passes on a new instance with no login. The table in *Users and directories* gets a row for `/home/agent/.claude-token` (the host's owner and mode; the agent's login token, readable by the agent). *The container: compose, entrypoint and health check* names the new mount beside the three volumes, and its sentence on a renamed instance no longer says that it needs a new `claude` login when the token file is in place. *The preflight's items* says, for `agent-run-probe`, that a missing or expired token is the usual cause when the detail names the login file. The decision log's entry "The agent's login is a token from a file" gains the mount, its place and the empty-file rule. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from pathlib import Path
from ruamel.yaml import YAML
loaded = YAML(typ='safe').load(Path('image/compose.yml').read_text(encoding='utf-8'))
volumes = loaded['services']['factory']['volumes']
print(len(volumes))
print(volumes[3])
print(volumes[4]['target'])
"
```
Expect: three lines: `5`, then `{'type': 'bind', 'source': './secrets/claude-token', 'target': '/home/agent/.claude-token', 'read_only': True, 'bind': {'create_host_path': False}}`, then `/home/factory/.secrets/hosting-token`.

```bash
grep -x "ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token" image/Dockerfile
```
Expect: exactly one line: `ENV FACTORY_CLAUDE_LOGIN_FILE=/home/agent/.claude-token`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_claude_token_mount.py tests/test_compose.py tests/test_token_folder.py tests/test_image_credentials.py tests/test_compose_project.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
