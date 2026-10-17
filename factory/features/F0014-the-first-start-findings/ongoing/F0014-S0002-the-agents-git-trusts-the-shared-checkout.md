---
stage: ready
pr: null
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The agent's git trusts the shared checkout

## Assignment (as of log entry 1)

The agent cannot use git in the checkout. At the first start of 2026-10-17 (`planning/overnight/first-start-checklist.md`, "Results", fault 1), `git status` as `agent` in `/work/checkout` failed with `detected dubious ownership in repository at '/work/checkout'`: the checkout belongs to `factory`, and git refuses a repository of another user unless a `safe.directory` names it. Every agent stage that reads a diff or a log is hit. The human's answer (2026-10-17): a root-owned `/etc/gitconfig` in the image, readable and not writable by the agent, with `safe.directory` for the checkout. The factory's own git needs none: it owns the checkout, and its git wrapper reads no system configuration (`GIT_CONFIG_NOSYSTEM=1`), so this file never reaches the factory's git commands; a project command's git (`make` as `factory`) does read it, and a safe directory for the factory's own checkout changes nothing there. Git trusts only the exact work-tree path (not a trailing slash, not `.git`; checked with git 2.39.5, the image's version), so the entry is `/work/checkout`, tied to the settings' `CHECKOUT_PATH`. The agent's git needs only read access to `.git`, which S0006's `0640` keeps: `git status` skips its index refresh when it cannot write. The file lives in the repository as `image/gitconfig` and the Dockerfile copies it, so a test can read exactly what the image installs; the files are under `image/`, in the coder's write paths. A real agent's `git status` is observed at the shakedown run (plan step 4), since the test cannot be a second user.

## Interface

A new file `image/gitconfig`, git's configuration format, with at least one comment line (`#`) at the top that says why (the agent's git trusts the checkout the factory owns; the factory's git wrapper reads no system configuration), and exactly one entry: the section `[safe]` with `directory = /work/checkout`. Besides comment lines and blank lines it holds only the two lines `[safe]` and `directory = /work/checkout` (indented with a tab), in that order.

`image/Dockerfile`, after the two lines that install `git-credential-factory` and before `ENV FACTORY_TOKEN_FILE=...`:

```dockerfile
COPY image/gitconfig /etc/gitconfig
RUN sed -i 's/\r$//' /etc/gitconfig && chmod 0644 /etc/gitconfig
```

with a comment above them: the agent's git trusts the checkout the factory owns; the factory's git does not read this file. The `COPY` has no `--chown` and no `--chmod`, so the file belongs to `root:root`, and no `chown` names `/etc/gitconfig`. Nothing else in the Dockerfile changes.

Tests: a new module `tests/test_image_gitconfig.py`. It reads the file's entries with the real git through `run_git` of `tests/git_support.py` (`run_git(ROOT, "config", "--file", str(GITCONFIG), "--list")`, the path absolute), and no other route to a git process. It reads the Dockerfile with `dockerfile_instructions` and `DOCKERFILE` of `tests/dockerfile_support.py`, and with `_path_settings` of `tests/test_image.py`, as `tests/test_token_folder.py` does. No test of an earlier story changes.

## Acceptance criteria

1. `git config --file image/gitconfig --list` prints exactly one line, `safe.directory=/work/checkout`: no other entry, and no `safe.directory=*`.
2. The safe directory of `image/gitconfig` equals `str(factory.domain.settings.CHECKOUT_PATH)`, so a moved checkout cannot leave the agent's git behind.
3. `image/gitconfig` has at least one line that starts with `#`, and its other non-blank lines, stripped, are exactly `[safe]` and `directory = /work/checkout`, in that order.
4. Among the Dockerfile's instructions (`dockerfile_instructions()`), `COPY image/gitconfig /etc/gitconfig` appears exactly once, without `--chown` and without `--chmod`, and the instruction right after it is exactly `RUN sed -i 's/\r$//' /etc/gitconfig && chmod 0644 /etc/gitconfig`. The `COPY` comes after the `RUN` instruction that holds `chmod 0755 /usr/local/bin/git-credential-factory`, and that `RUN` comes before `ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token`.
5. In the Dockerfile's raw text, the line directly above `COPY image/gitconfig /etc/gitconfig` starts with `#`.
6. The last `chmod` of `/etc/gitconfig` in the Dockerfile is `0644` (`_path_settings(dockerfile, "chmod")`), and no `chown` of the Dockerfile names `/etc/gitconfig` (`_path_settings(dockerfile, "chown")` has no such key), so the file stays `root:root` and not writable by the agent.
7. What must still hold: the factory's git reads no system configuration (`test_system_configuration_is_ignored` in `tests/adapters/test_git_cli_reading.py` passes), the image is still pinned and the image id is still written after the last `COPY` (`tests/test_image.py`), and the image still installs no `credential.helper` and no `.git-credentials` (`tests/test_image_credentials.py`).
8. `make check` stays green.
9. docs: the operator guide's table in *Users and directories* gets a row for `/etc/gitconfig`, `0644`, `root:root`: git's system configuration, read by the agent's git and not by the factory's git wrapper, naming `/work/checkout` as a safe directory, so that the agent can run `git status`, `git diff` and `git log` in the checkout `factory` owns, and cannot change the file. The morning observations in *The agent runs as a second user* get a row: `docker exec -u agent <container> git -C /work/checkout status --short` prints no `dubious ownership` (expected: the status, or nothing on a clean checkout); the row of the push says that the failure is git's `could not read Username`, no credential. The decision log gets an entry "The agent's git trusts the shared checkout" (the first start's fault, the human's answer, why the factory's git needs none, that git trusts only the exact work-tree path, and what was rejected: `safe.directory=*`, which trusts every repository; a `.gitconfig` in the agent's home, which the agent can rewrite; a `GIT_CONFIG_*` name in the agent run's environment, which would widen its allow list). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
git config --file image/gitconfig --list
```
Expect: exactly one line: `safe.directory=/work/checkout`.

```bash
grep -n "/etc/gitconfig" image/Dockerfile
```
Expect: among the lines printed, `COPY image/gitconfig /etc/gitconfig` and the `RUN` line holding `chmod 0644 /etc/gitconfig`; a comment line naming the file may be printed as well.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_image_gitconfig.py tests/test_image.py tests/test_image_credentials.py tests/adapters/test_git_cli_reading.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
