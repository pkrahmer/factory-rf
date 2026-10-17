---
stage: tests
pr: 175
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The agent cannot rewrite its agents and settings

## Assignment (as of log entry 1)

The agent home `/home/agent/.claude` belongs to `agent` today, so one agent run can rewrite the agent files and `settings.json` that the factory and `claude` read on every later run, and widen its own tools, budget or permissions until the container restarts (F0010 decision 21, open point 4 of F0010's acceptance). The human's answer of 2026-10-17 (item 1.10): those files are owned by the factory and read-only to the agent. This story makes the image give the home to `factory`, group `factory-work`, mode `3775`: the agent, in the group, can still create its own files there (its `claude` login among them), and the sticky bit keeps it from renaming or deleting the factory's files; the entrypoint, which runs as `factory`, installs `agents/` as `0755` with each file `0644`, and `settings.json` as `0644`. The home is the mount point of the volume `claude-home`, so the agent cannot rename the folder itself either (FEATURE decision 28). The files are under `image/`, in the coder's write paths. One row of an F0010 image test moves to a new test by the human's leave (FEATURE decision 42).

## Interface

`image/Dockerfile`: in the `RUN` that creates the users and folders, `/home/agent/.claude` is `chown factory:factory-work` and `chmod 3775` (in place of `agent:factory-work` and `2775`); `/work` keeps `factory:factory-work` and `2775`. Nothing else changes.

`image/entrypoint.sh`: after it copies the agents and the settings into the home, it sets `agents/` to `0755`, every file in it to `0644`, and `settings.json` to `0644`; it changes the mode of nothing else in the home. Nothing else changes: the umask, the replaced copy of `agents/`, the runs folder, the log lines (`installed agents and settings into <home>` among them) and the start of the instance stay.

Tests: `tests/test_agent_home_ownership.py`, reading the Dockerfile with `_path_settings` of `tests/test_image.py` (or `dockerfile_instructions` of `tests/dockerfile_support.py`) and running the entrypoint as `tests/test_entrypoint.py` does (its `Layout` may be imported). By the human's leave (FEATURE decision 42), and no other change to an earlier story's test: the row `/home/agent/.claude` is removed from `test_the_shared_directories_are_writable_by_the_work_group` in `tests/test_image.py`, whose row `/work` stays.

## Acceptance criteria

1. The Dockerfile's last `chown` of `/home/agent/.claude` is `factory:factory-work` and its last `chmod` is `3775`; `/work` keeps `2775` and the group `factory-work`.
2. After the entrypoint runs, `<home>/agents` has mode `0755`, each agent file in it `0644`, and `<home>/settings.json` `0644`; none of them is writable by the group or by others.
3. The files' contents are still the image's (the existing tests of `tests/test_entrypoint.py` still pass), and the entrypoint still sets its umask `002` before anything else (the existing test of `tests/test_entrypoint_umask.py`).
4. A file the agent made in the home before (a stand-in `.credentials.json` with mode `0600`) is neither removed nor changed by the entrypoint.
5. `make check` stays green.
6. docs: the operator guide's section *Users and directories* gives `/home/agent/.claude` its own row (`3775`, owner `factory`, group `factory-work`: the agent adds its own files, it cannot change or remove the agents and the settings), and the sentence that the agent could change the files in its home (*The agent runs as a second user*) says what is protected now, that the login stays the agent's, and what stays writable (files of its own in `~/.claude` that `claude` reads, such as a user `CLAUDE.md` or skills, and `/home/agent/.claude.json`); it says that a `claude-home` volume made by an earlier image keeps its old owner and mode, so the protection holds on a new volume; the morning observations get one line to check it (`docker exec -u agent <container> sh -c 'echo x >> /home/agent/.claude/settings.json'` is refused); the decision log records that F0010 decision 21 is superseded for the agent files and the settings, and what stays open. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -n "/home/agent/.claude" image/Dockerfile
grep -n "chmod" image/entrypoint.sh
```
Expect: the Dockerfile lines name `chown factory:factory-work` and `chmod 3775` for `/home/agent/.claude`; the entrypoint lines set `0755` for the agents folder and `0644` for the agent files and `settings.json`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_agent_home_ownership.py tests/test_image.py tests/test_entrypoint.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete files and values. `image/Dockerfile` has the `chown factory:factory-work` and `chmod 3775` for `/home/agent/.claude`, and `/work` stays `2775`. `image/entrypoint.sh` has the modes `0755` for `agents/` and `0644` for each agent file and `settings.json`. The new test module `tests/test_agent_home_ownership.py` names the helpers it reuses (`_path_settings`, `dockerfile_instructions`, `Layout`). The removed row of `tests/test_image.py` is named and covered by FEATURE decision 42.
   - Criteria: each can be tested by one test function. 1 is the Dockerfile's last chown and chmod. 2 is the modes after the entrypoint runs, including not writable by group or others. 3 is the existing entrypoint and umask tests. 4 is a stand-in `.credentials.json` at `0600` that is unchanged. Every Interface rule has a criterion. The "changes the mode of nothing else in the home" rule is covered by 4, and the failing side of the modes by 2's "none writable by group or others". The sticky bit's effect on rename and delete is not a criterion. It is the Dockerfile's `3775` read by 1 and cannot be run without a container.
   - Demo: the `grep` commands and the pytest command are runnable. Each `Expect:` line is checkable against the output: the named `chown`, `chmod 3775` and `0755`/`0644` lines, and a final `<n> passed` line with no failed, error or skipped count.
   - Architecture: the change stays in `image/`, inside the coder's write paths, and adds no new dependency. The docs criterion touches only the operator guide and the decision log.
   - Scope: this is item 1.10 of FEATURE.md, listed as S0025 and decided in decisions 13, 28, 42 and 47. It is not in "Out of scope". The other writable files in the home stay open, as decision 47 says.
