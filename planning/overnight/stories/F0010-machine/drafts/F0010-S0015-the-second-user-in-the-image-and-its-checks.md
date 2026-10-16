# The second user in the image and its checks

## Assignment (as of log entry 1)

Give the factory's user the one right it needs over the second user, and make the machine fail loudly when the agent would run as the factory's user. The factory's user may become `agent` for one command and for nothing else, through one `sudo` rule in a file of its own. Three defaults for that user make `sudo` behave: the agent's files are created group-writable (`sudo` applies a umask of its own, by default `0022` joined with the caller's, so that the files and directories an agent makes would be `644` and `755` and the factory's restore, `git reset --hard` and `git clean -fd`, could not remove an agent-made directory: `checkout_restore_failed`), and the command gets no pseudo-terminal of its own (Debian's `sudo` defaults to `use_pty`, which puts the command in a new session). The entrypoint sets `umask 002` for the factory's own files. The image sets `FACTORY_AGENT_USER=agent`. The human decided on 2026-10-14 that a preflight item `agent-user` fails when `agent_user` is `None` and the token file exists, because every agent would then run as `factory`, who can read the token file, and no check would say so (WE3.1 and R33 silently off); it passes when the user is set, and when no token file exists (tests, local runs). This covers WE3.1 on the image's side and implements R33. The second user, the `sudo` rule and the group exist only in a real image: v1's container can test the files statically and the item; the real `sudo` call, the umask of agent-made files, the factory's restore after an agent-made directory and a refused `sudo` are morning observations (the last is also found by the probe of an agent run before any claim). The factory's side is the previous story.

## Interface

`image/sudoers-factory-agent`

```text
Defaults:factory umask=0002
Defaults:factory umask_override
Defaults:factory !use_pty
factory ALL=(agent) NOPASSWD: ALL
```

`image/Dockerfile` gains these instructions before the `RUN` that writes `/opt/factory/image-id` (which stays after the last `COPY`, F0010-S0006 criterion 12):

```dockerfile
COPY image/sudoers-factory-agent /etc/sudoers.d/factory-agent
RUN chmod 0440 /etc/sudoers.d/factory-agent && visudo -cf /etc/sudoers.d/factory-agent
ENV FACTORY_AGENT_USER=agent
```

`image/entrypoint.sh` gains, directly after `set -eu`, the line `umask 002`.

`src/factory/application/preflight.py` (extends the module)

```python
def agent_user_item(settings: InstanceSettings, exists: Callable[[Path], bool]) -> PreflightItem: ...
```

Rules:

- `agent_user_item(settings, exists)` is the item `agent-user`. It fails when `settings.agent_user` is `None` and `settings.token_file` is not `None` and `exists(settings.token_file)`; its detail is `FACTORY_AGENT_USER is not set: every agent would run as the factory's user, who can read the token file`. In every other case it passes: the agent user is set, or there is no token file to protect.
- The sudoers file holds, apart from blank and comment lines, exactly the four lines shown, in this order. Only the last is a rule, and no line gives `agent` anything.
- The values of the sudoers file's `umask` and the entrypoint's `umask` agree: both are `0002`.
- Wiring: the items `agent-user` and, when `settings.agent_user` is not `None`, `tool_item("sudo", which)` are added to the machine checks by the story that builds the probe of an agent run, which assembles every extra item in one place.

Tests: `tests/test_image_users.py` (the Dockerfile, the sudoers file and the compose file), `tests/test_entrypoint_umask.py` (a file of its own, with a stub `python` of its own that writes the output of `umask` to a file; `tests/test_entrypoint.py` is the entrypoint story's), `tests/application/test_agent_user_item.py`.

## Acceptance criteria

1. The Dockerfile copies `image/sudoers-factory-agent` to `/etc/sudoers.d/factory-agent`, sets mode `0440`, validates it with `visudo -cf`, and sets `ENV FACTORY_AGENT_USER=agent`, all before `USER factory`.
2. `image/sudoers-factory-agent` holds, apart from blank and comment lines, exactly the lines `Defaults:factory umask=0002`, `Defaults:factory umask_override`, `Defaults:factory !use_pty` and `factory ALL=(agent) NOPASSWD: ALL`, in this order.
3. The only line of `image/sudoers-factory-agent` that is not a `Defaults` line is `factory ALL=(agent) NOPASSWD: ALL`, and no line of the file names `root`, `ALL=(ALL`, or the user `agent` as the one who may use `sudo`.
4. The `umask` value of the sudoers file equals the value of the entrypoint's `umask` line (both `0002`): the agent's files and the factory's are group-writable alike.
5. The uid of the compose secret `hosting-token` equals the uid the Dockerfile gives the user `factory` and differs from the uid it gives `agent`, and `agent`'s uid is not 0 (WE3.1: the token file is readable only by the factory's user).
6. The entrypoint sets `umask 002` directly after `set -eu`, and before it starts the instance the stub sees the umask `0002`.
7. `agent_user_item` fails, with the detail `FACTORY_AGENT_USER is not set: every agent would run as the factory's user, who can read the token file`, when `settings.agent_user` is `None` and `exists` answers true for the token file.
8. `agent_user_item` passes, with the name `agent-user` and an empty detail, when `settings.agent_user` is `agent`, whether or not the token file exists.
9. `agent_user_item` passes when `settings.agent_user` is `None` and `settings.token_file` is `None`, and when it is a path for which `exists` answers false.
10. make check stays green.
11. docs: `docs/operator-guide.md` explains the one `sudo` rule and its three defaults and why, the preflight item `agent-user` and what the operator does when it fails (set `FACTORY_AGENT_USER` or remove the token file), and lists the morning observations that need a real image with commands that perform them: an agent run as `agent` (WE3.1), its failed reads and pushes (WE3.3, WE3.4), the mode of a file and a directory an agent made, the factory's restore after an agent-made directory, and a refused `sudo`; `docs/decisions.md` records why the factory's user may become `agent` for one command only, why the sudoers file sets the umask and no pseudo-terminal, and why a missing agent user with a token file is a stop (the human, 2026-10-14).

## Demo

```bash
grep -v '^#' image/sudoers-factory-agent | grep -v '^$'
```
Expect: exactly four lines: `Defaults:factory umask=0002`, `Defaults:factory umask_override`, `Defaults:factory !use_pty` and `factory ALL=(agent) NOPASSWD: ALL`.

```bash
uv run python -c "
from pathlib import Path
from factory.application.preflight import agent_user_item
from factory.domain.settings import read_settings
env = {'FACTORY_REPOSITORY_URL': '/srv/project.git', 'FACTORY_INSTANCE': 'factory-1', 'FACTORY_TOKEN_FILE': '/run/secrets/hosting-token'}
item = agent_user_item(read_settings(env), lambda path: True)
print(item.name, item.passed)
item = agent_user_item(read_settings({**env, 'FACTORY_AGENT_USER': 'agent'}), lambda path: True)
print(item.name, item.passed)
"
```
Expect: two lines, `agent-user False` and `agent-user True`.

```bash
d=$(mktemp -d) && mkdir -p "$d/opt/claude/agents" "$d/bin" && : > "$d/opt/claude/agents/x.md" && echo '{}' > "$d/opt/claude/settings.json" && printf '#!/bin/sh\numask\n' > "$d/bin/python" && chmod +x "$d/bin/python" && HOME="$d" FACTORY_OPT="$d/opt" FACTORY_CLAUDE_HOME="$d/home" FACTORY_STATE="$d/state" PATH="$d/bin:$PATH" sh image/entrypoint.sh | tail -1
```
Expect: one line, `0002`.

## Log (append only)

1. 2026-10-12 human: created.
