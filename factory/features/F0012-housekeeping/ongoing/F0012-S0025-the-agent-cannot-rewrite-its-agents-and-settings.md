---
stage: accept
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
3. tester: wrote the red tests for the agent home's ownership and modes.
   - criterion 1: tests/test_agent_home_ownership.py::test_the_agent_home_is_the_factorys_with_the_sticky_bit_and_work_stays_shared. It has two rows. In `agent-home`, `/home/agent/.claude` has `3775` and `factory:factory-work`. In `work`, `/work` has `2775` and group `factory-work`. Both read the last values through `_path_settings` of tests/test_image.py.
   - criterion 2: tests/test_agent_home_ownership.py::test_the_installed_agents_and_settings_are_not_writable_by_group_or_others. The rows are `agents` 0755, `agents/coder.md` 0644, `agents/reviewer.md` 0644 and `settings.json` 0644. Each row also checks that the group and others have no write bit. The test runs the entrypoint with `Layout` from tests/test_entrypoint.py. It makes the image's copies group-writable first (dir 0775, files 0664), as a checkout under umask 002 gives them. Without that the test passed by accident: `cp` keeps the source's 0644 under umask 002, so it was not testing the entrypoint. It adds a second agent file so that "each agent file" covers more than one.
   - criterion 3: covered by the existing tests of tests/test_entrypoint.py (contents, replaced agents) and tests/test_entrypoint_umask.py::test_the_entrypoint_sets_umask_002_after_set_eu_and_starts_the_instance_with_it. No new test was needed.
   - criterion 4: tests/test_agent_home_ownership.py::test_a_file_the_agent_made_in_the_home_is_left_as_it_was. A stand-in `.credentials.json` at 0600 keeps its text and mode. It passes already and guards against a later chmod reaching too far.
   - criteria 5 and 6 (make check, docs): not tests.
   - Approved change to an earlier test (FEATURE decision 42): removed the row `/home/agent/.claude` from `test_the_shared_directories_are_writable_by_the_work_group` in tests/test_image.py. Its row `/work` stays.
   - Files: created tests/test_agent_home_ownership.py and edited tests/test_image.py (that one row).
   - Red as intended: the `agent-home` row of criterion 1 fails because the Dockerfile still has `agent:factory-work` and `2775`. All four rows of criterion 2 fail on the mode the entrypoint leaves. Every module imported. No collection errors.
   - `make lint` is green. I ran `make test` twice because the first run showed the mode test passing for the wrong reason (above). The second run gave the five expected failures.
   - Not tested: the sticky bit's effect on renaming and deleting, which needs a container (intake noted this).

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_agent_home_ownership.py::test_the_installed_agents_and_settings_are_not_writable_by_group_or_others[settings]
4. coder: the factory now owns the agent home. Commit e0ce79e.
   - `image/Dockerfile`: `/home/agent/.claude` is now `chown factory:factory-work` and gets its own `chmod 3775`. `/work` keeps `factory:factory-work` and `chmod 2775`. Nothing else in that `RUN` changed.
   - `image/entrypoint.sh`: after the two `cp` commands it runs `chmod 0755 "$home/agents"`, `find "$home/agents" -type f -exec chmod 0644 {} +` and `chmod 0644 "$home/settings.json"`, with one comment saying why. The umask, the replaced copy, the log lines and the start of the instance are unchanged. Nothing else in the home is touched, so the agent's `.credentials.json` keeps its mode (criterion 4).
   - Design decision: I used `find -type f` rather than `chmod 0644 "$home/agents"/*`. A glob fails on an empty folder and skips dotfiles. I rejected `chmod -R u=rwX,go=rX` because it keeps an exec bit and does not give the exact `0644` the Interface asks for. One limit: a subfolder inside `agents/` would keep its copied mode. The image's agents folder has no subfolders today.
   - Refactor: I read the diff and found nothing to change. No separate refactor commit.
   - Noticed, not touched: the entrypoint's header comment says the umask lets "either remove the other's" files. That is still true in `/work`, but no longer for the factory's files in the home. The docs criterion (6) covers the operator guide and decision log for this story. The documenter may want to check whether that comment's wording matters.
   - `make check`: check: green.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
   - Criteria: criterion 1 is covered by `tests/test_agent_home_ownership.py::test_the_agent_home_is_the_factorys_with_the_sticky_bit_and_work_stays_shared`. Its rows check `/home/agent/.claude` (`3775`, `factory:factory-work`) and `/work` (`2775`, group `factory-work`), both read as the last value through `_path_settings`. Criterion 2 is covered by `test_the_installed_agents_and_settings_are_not_writable_by_group_or_others`. Before the entrypoint runs, the test makes the source copies group-writable (0775/0664). So a 0755/0644 result comes from the entrypoint, not from `cp` keeping the source mode, and the group/other write bit is asserted on all four rows. Criterion 3 is covered by the existing entrypoint and umask tests, which this diff leaves unchanged. Criterion 4 (the "changes the mode of nothing else" rule) is covered by `test_a_file_the_agent_made_in_the_home_is_left_as_it_was`. The coder's entry records `make check` green.
   - Approved test change: in `tests/test_image.py`, only the `/home/agent/.claude` row was removed, as FEATURE decision 42 allows. The `/work` row stays.
   - Image: `image/Dockerfile:24,27-28` matches the Interface. The agent's primary group is `factory-work` (line 20), so with the setgid bit it can still create its login files in the home.
   - Entrypoint: `image/entrypoint.sh:26-29` applies the three modes after the copies and before the log line. Nothing else changed. `find -type f` was chosen over a glob, and the log gives the reason.
   - Architecture, security: only `image/` and tests change. No silencing markers, no secrets, no new dependency.
   - Judged and not raised: the `layout` fixture in the new module repeats the one in `tests/test_entrypoint.py`. Moving it to `tests/conftest.py` would mean editing an earlier story's test, which the Interface forbids. The entrypoint's header comment ("so either can remove the other's") is still true for `/work`. The coder flagged it for the documenter, and the Interface keeps everything else in the entrypoint unchanged.
   - Open: the sticky bit's effect on renaming and deleting is not tested, because that needs a container (noted at intake). Docs criterion 6 is for the documenter.
6. documenter: Docs written for criterion 6. I changed only documents, so I did not run `make check`.
   - `docs/operator-guide.md`:
     - "The agent runs as a second user": replaced the sentence that the agent could change its home files. It now says what is protected, that the login stays the agent's, what stays writable (user `CLAUDE.md`, skills, `/home/agent/.claude.json`), and that an old `claude-home` volume keeps its old owner and mode.
     - "Users and directories": `/home/agent/.claude` has its own row (`3775`, `factory:factory-work`), and `/work` keeps `2775`.
     - Morning observations: one row for `docker exec -u agent <container> sh -c 'echo x >> /home/agent/.claude/settings.json'`, expected to be refused.
   - `docs/decisions.md`: a new section recording that F0010 decision 21 is superseded for the agent files and settings. It lists what stays open: old volumes, the other writable files, a subfolder in `agents/`, and the sticky bit not being tested.
   - Checks: `uv run python -m factory.entry.check_documents` prints `documents ok`. The new Dockerfile and entrypoint values match the diff. I could not run the new morning-observation command, because it needs a container.
   - Cross-read and found current: README.md and the rest of the operator guide.
   - Not touched: the `entrypoint.sh` header comment ("so either can remove the other's") is still true for `/work` and is code, not mine to edit. The guide's "Log in once as `agent`" paragraph says the login is in a volume only if you mount one there, but compose mounts `claude-home`. That is unrelated to this story.
   - Findings: none.

   `make check`: check: green
   `make documents`: documents ok
7. demo: ran both Demo commands from the repository root. Both met their `Expect:` lines, and nothing contradicts a criterion.

   Command 1:
   ```
   $ grep -n "/home/agent/.claude" image/Dockerfile
   21: && mkdir -p /work /state/runs /home/agent/.claude \
   24: && chown factory:factory-work /home/agent/.claude \
   28: && chmod 3775 /home/agent/.claude
   52:    FACTORY_CLAUDE_HOME=/home/agent/.claude
   $ grep -n "chmod" image/entrypoint.sh
   27:chmod 0755 "$home/agents"
   28:find "$home/agents" -type f -exec chmod 0644 {} +
   29:chmod 0644 "$home/settings.json"
   33:chmod 2750 "$state/runs"
   ```
   Met. The Dockerfile has `chown factory:factory-work` and `chmod 3775` for `/home/agent/.claude`. The entrypoint sets `0755` on `agents/` and `0644` on the agent files and on `settings.json`. Line 33 (`/state/runs`) was already there before this story.

   Command 2:
   ```
   $ uv run pytest --no-header -p no:cacheprovider tests/test_agent_home_ownership.py tests/test_image.py tests/test_entrypoint.py
   ........................................................................ [ 93%]
   .....                                                                    [100%]
   77 passed in 0.20s
   ```
   Met. The last line is `77 passed`, with no failed, error or skipped count.

   Criteria cross-check:
   - 1: `image/Dockerfile:23,27` keeps `/work` at `factory:factory-work` and `2775`, as required.
   - 2: the entrypoint changes only the agents folder and `settings.json`, so nothing else in the home is touched (criteria 2 and 4).
   - 3: covered by the existing entrypoint tests, which pass in the run above.
   - 6: `uv run python -m factory.entry.check_documents` prints `documents ok`. The diff against `origin/main` changes only `docs/operator-guide.md` and `docs/decisions.md`, with the row, the rewritten sentence, the note about old volumes, the morning-observation line and the decision entry.
   - 5: I did not run `make check` myself. The factory runs it as the gate.

   Findings: none.
   Open: the sticky bit's effect and the morning-observation command need a container. Neither was run here (already noted at intake and by the documenter).
