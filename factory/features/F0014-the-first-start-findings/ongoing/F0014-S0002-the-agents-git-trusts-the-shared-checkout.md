---
stage: demo
pr: 195
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
2. intake: accepted
   - Interface: concrete. `image/gitconfig` content is pinned line by line, and the two Dockerfile lines are given verbatim with their position. Helpers named exist (`run_git` in tests/git_support.py, `dockerfile_instructions` and `DOCKERFILE` in tests/dockerfile_support.py, `_path_settings` in tests/test_image.py). `CHECKOUT_PATH` is `/work/checkout` in settings, and the Dockerfile's anchor lines (git-credential-factory chmod RUN at line 39, `ENV FACTORY_TOKEN_FILE` at line 41) are there.
   - Criteria: each is testable by one test function. Every Interface rule has a criterion for the failing side too: criterion 1 rejects any extra entry and `safe.directory=*`, criterion 3 rejects any other line, criterion 4 rejects `--chown`/`--chmod` and a duplicate `COPY`, criterion 6 rejects a `chown` of the file. The sed CRLF strip is pinned as the exact instruction text in criterion 4.
   - Demo: all three commands are runnable. Each Expect line is checkable against the output (one exact line, the named lines, `<n> passed` with no failed/error/skipped).
   - Architecture: the change is image files only, with a test module at the `tests/` root, which suits a module outside the layers. No layer is touched.
   - Scope: within the feature's S0002 scope (`image/gitconfig`, `image/Dockerfile`). Nothing is in "Out of scope". The real `git status` as agent is left to step 4, as the feature says. No test of an earlier story changes, so no leave is needed.
3. tester: Wrote the red tests for the image's git system configuration.
   - criterion 1: tests/test_image_gitconfig.py::test_the_configuration_holds_only_the_checkout_as_safe_directory (real git through `run_git(ROOT, "config", "--file", <absolute path>, "--list")`)
   - criterion 2: tests/test_image_gitconfig.py::test_the_safe_directory_is_the_settings_checkout_path (against `factory.domain.settings.CHECKOUT_PATH`)
   - criterion 3: tests/test_image_gitconfig.py::test_the_file_says_why_and_holds_only_the_safe_section
   - criterion 4: tests/test_image_gitconfig.py::test_the_image_copies_the_configuration_as_root_after_the_credential_helper (exactly one COPY naming gitconfig, with no --chown and no --chmod; the next instruction is the exact sed/chmod RUN; the RUN holding the git-credential-factory chmod comes before the COPY and before `ENV FACTORY_TOKEN_FILE=...`)
   - criterion 5: tests/test_image_gitconfig.py::test_a_comment_stands_directly_above_the_copy (raw Dockerfile text)
   - criterion 6: tests/test_image_gitconfig.py::test_the_configuration_is_readable_by_all_and_owned_by_root (`_path_settings` chmod is 0644; no chown key for /etc/gitconfig)
   - criterion 7: no new test. The criterion names the existing tests that must keep passing: tests/adapters/test_git_cli_reading.py::test_system_configuration_is_ignored, tests/test_image.py and tests/test_image_credentials.py. They are unchanged.
   - criteria 8 and 9: `make check` and docs, nothing to test here.
   Files created: tests/test_image_gitconfig.py. There was no import failure, because the module imports only existing test helpers and `factory.domain.settings`. The tests are red because `image/gitconfig` does not exist yet (git config --file fails, read_text fails) and the Dockerfile does not have the COPY/RUN lines yet. `make lint` is green. I named the token-file ENV constant `FILE_SETTING`, because ruff's S105 flagged a name containing TOKEN. No interpretation was needed.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_image_gitconfig.py::test_the_configuration_is_readable_by_all_and_owned_by_root
4. coder: Added the image's git system configuration (commit f0f1ff8b).
   - `image/gitconfig`: three comment lines saying why (the agent's git trusts the checkout the factory owns; the factory's git wrapper reads no system configuration), then `[safe]` and a tab-indented `directory = /work/checkout`. Running `git config --file image/gitconfig --list` prints exactly `safe.directory=/work/checkout`.
   - `image/Dockerfile`: a comment followed by `COPY image/gitconfig /etc/gitconfig` and `RUN sed -i 's/\r$//' /etc/gitconfig && chmod 0644 /etc/gitconfig`. They sit right after the git-credential-factory install and before `ENV FACTORY_TOKEN_FILE=...`. There is no `--chown`/`--chmod` and no chown of the file, so it stays root:root. Nothing else in the Dockerfile changed.
   - Design: I followed the interface as written. It already rejects the alternatives (`safe.directory=*`, a `.gitconfig` in the agent's home, a `GIT_CONFIG_*` env name). The sed strip matches the other copied files, so a CRLF checkout cannot break the config.
   - Refactor: I read the diff and found nothing to change. It is two data files and adds no code.
   - Not touched: the docs from criterion 9 (operator guide rows, decision log entry). Those belong to the documenter.
   - `make check`: green.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Diff read: `image/gitconfig` (3 comment lines, `[safe]`, tab-indented `directory = /work/checkout`); `image/Dockerfile` (a comment, `COPY image/gitconfig /etc/gitconfig` with no `--chown`/`--chmod`, then the exact sed/`chmod 0644` RUN, placed between the git-credential-factory RUN and `ENV FACTORY_TOKEN_FILE=...`; nothing else changed); `tests/test_image_gitconfig.py`.
      - Criteria 1–6: each has a test in `tests/test_image_gitconfig.py` that checks what the criterion says. It uses the routes the Interface names: `run_git` for the real `git config --file <absolute> --list`, `dockerfile_instructions`/`DOCKERFILE`, and `_path_settings` of `tests/test_image.py`. The failing sides are covered: any extra entry or `*` (equality on the full list), any other line (equality on the non-comment lines), a duplicate or flagged COPY (the filter catches any COPY naming gitconfig), a missing comment above, and any chown of the file. Criterion 7 is covered by the unchanged existing tests. The coder's entry records `make check` green.
      - Considered, not counted: the Interface puts the COPY before `ENV FACTORY_TOKEN_FILE` and the directory line under a tab, and criteria 3 and 4 do not test either (criterion 4 orders only the helper RUN against the ENV). Neither changes what the image installs or how git reads the file, and the code matches the Interface on both.
      - Architecture: no `src/` change. Security: no secrets, no markers, and the file stays root-owned with mode 0644. Quality: the test helpers are reused, not copied. Hygiene: Assignment matches what was built, and criterion 9 states what the documenter must write.
6. documenter: wrote the docs criterion (criterion 9).
   - `docs/operator-guide.md`: a row for `/etc/gitconfig` (`0644`, `root:root`) in *Users and directories*; a new morning observation row (`git -C /work/checkout status --short` as `agent` prints no `dubious ownership`); the push row now says git fails with `could not read Username`, no credential.
   - `docs/decisions.md`: new entry "The agent's git trusts the shared checkout" (fault, the human's answer, why the factory's git needs none, exact work-tree path, and the rejected `safe.directory=*`, `.gitconfig` in the agent's home and `GIT_CONFIG_*` in the agent's environment).
   - `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because I changed only docs.
   - Cross-read the diff (`image/gitconfig`, `image/Dockerfile`) against the guide's `.git` seal text and the sudo section: current. The README is unchanged.
   - The code matches the Interface; no findings. Nothing stale seen that I left alone.

   `make check`: check: green
   `make documents`: documents ok
