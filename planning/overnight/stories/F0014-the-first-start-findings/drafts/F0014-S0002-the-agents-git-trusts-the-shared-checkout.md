# The agent's git trusts the shared checkout

## Assignment (as of log entry 1)

The agent cannot use git in the checkout. At the first start of 2026-10-17 (`planning/overnight/first-start-checklist.md`, "Results", fault 1), `git status` as `agent` in `/work/checkout` failed with `detected dubious ownership in repository at '/work/checkout'`: the checkout belongs to `factory`, and git refuses a repository of another user unless a `safe.directory` names it. Every agent stage that reads a diff or a log is hit. The human's answer (2026-10-17): a root-owned `/etc/gitconfig` in the image, readable and not writable by the agent, with `safe.directory` for the checkout. The factory's own git needs none: it owns the checkout, and it reads no system configuration (`GIT_CONFIG_NOSYSTEM=1`), so this file never reaches it. The file lives in the repository as `image/gitconfig` and the Dockerfile copies it, so a test can read exactly what the image installs; the files are under `image/`, in the coder's write paths. A real agent's `git status` is observed at the shakedown run (plan step 4), since the test cannot be a second user.

## Interface

A new file `image/gitconfig`, git's configuration format, with comment lines (`#`) that say why and exactly one entry: the section `[safe]` with `directory = /work/checkout`.

`image/Dockerfile`, after the two lines that install `git-credential-factory` and before `ENV FACTORY_TOKEN_FILE=...`:

```dockerfile
COPY image/gitconfig /etc/gitconfig
RUN sed -i 's/\r$//' /etc/gitconfig && chmod 0644 /etc/gitconfig
```

with a comment above them: the agent's git trusts the checkout the factory owns; the factory's git does not read this file. The `COPY` has no `--chown` and no `--chmod`, so the file belongs to `root:root`, and no `chown` names `/etc/gitconfig`. Nothing else in the Dockerfile changes.

Tests: a new module `tests/test_image_gitconfig.py`. It reads the file's entries with the real git, `git config --file image/gitconfig --list`, through `run_git` of `tests/git_support.py` or `subprocess` as the other tests that call git directly do, and the Dockerfile with `dockerfile_instructions` of `tests/dockerfile_support.py` and `_path_settings` and `_commands` of `tests/test_image.py`. No test of an earlier story changes.

## Acceptance criteria

1. `git config --file image/gitconfig --list` prints exactly one line, `safe.directory=/work/checkout`: no other entry, and no `safe.directory=*`.
2. The safe directory of `image/gitconfig` equals `str(factory.domain.settings.CHECKOUT_PATH)`, so a moved checkout cannot leave the agent's git behind.
3. The Dockerfile holds the instruction `COPY image/gitconfig /etc/gitconfig`, without `--chown` and without `--chmod`, before `USER factory`.
4. A `RUN` instruction after that `COPY` and before `USER factory` strips the carriage returns of `/etc/gitconfig` and sets its mode: the last `chmod` of `/etc/gitconfig` is `0644`, and no `chown` of the Dockerfile names `/etc/gitconfig`.
5. What must still hold: the factory's git reads no system configuration (the test of `GIT_CONFIG_SYSTEM` in `tests/adapters/test_git_cli_reading.py` passes), the image is still pinned (`tests/test_image.py`), and the image still installs no `credential.helper` and no `.git-credentials` (`tests/test_image_credentials.py`).
6. `make check` stays green.
7. docs: the operator guide's table in *Users and directories* gets a row for `/etc/gitconfig`, `0644`, `root:root`: git's system configuration, read by the agent's git and not by the factory's, naming `/work/checkout` as a safe directory, so that the agent can run `git status`, `git diff` and `git log` in the checkout `factory` owns, and cannot change the file. The morning observations in *The agent runs as a second user* get a row: `docker exec -u agent <container> git -C /work/checkout status --short` prints no `dubious ownership` (expected: the status, or nothing on a clean checkout); the row of the push says that the failure is git's `could not read Username`, no credential. The decision log gets an entry "The agent's git trusts the shared checkout" (the first start's fault, the human's answer, why the factory's git needs none, and what was rejected: `safe.directory=*`, which trusts every repository; a `.gitconfig` in the agent's home, which the agent can rewrite; a `GIT_CONFIG_*` name in the agent run's environment, which would widen its allow list). No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

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
