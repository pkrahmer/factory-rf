---
stage: doing
pr: 182
blocked: asked
comments_seen: 3
round: 0
attempts: 0
---
# The token in a folder only the factory can enter

## Assignment (as of log entry 1)

The agent can read the hosting token, under Docker Desktop and under Podman alike. `image/compose.yml` mounts the token file as the compose secret `hosting_token` at `/run/secrets/hosting-token` and gives it `uid: "1000"`, `gid: "1002"` and `mode: 0400`. Compose ignores those three keys outside Swarm mode: the file is a plain bind mount with the host file's owner and mode, which on Windows is `-rwxrwxrwx`, owner 0. The probe of 2026-10-17 (`planning/overnight/podman-probe-2026-10-17.md`, fault 1) printed the token with `sudo -u agent cat /run/secrets/hosting-token`. The human's answer: the token file is mounted into a folder that only the factory's user can enter, `/home/factory/.secrets`, mode `0700`, made in the image. The agent (uid 1001) then cannot reach the file, whatever the file's own mode. This story makes that folder in the image, replaces the compose secret by a read-only bind mount of the same host file into the folder, and points `FACTORY_TOKEN_FILE` at the new path; the factory and git's credential helper read the token from there through the variable, as they do now. It is the first story of the feature, before any real run with a token. The preflight item `token-file` still checks the file's own owner and mode; S0002 moves that check to the folder. The files are under `image/`, in the coder's write paths. Four tests of earlier stories change by the human's leave (FEATURE decision 9).

## Interface

`image/Dockerfile`, in the `RUN` that creates the users and folders:

- `/home/factory/.secrets` is added to the `mkdir -p` of `/work /state/runs /home/agent/.claude`;
- `chown factory:factory /home/factory/.secrets` and `chmod 0700 /home/factory/.secrets` are added, as `/state` has its own `chown` and `chmod`.

The group `factory` (gid 1000) has no member: both users have the primary group `factory-work`, and no `useradd` gives a supplementary group.

`image/Dockerfile`: `ENV FACTORY_TOKEN_FILE=/run/secrets/hosting-token` becomes `ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token`, still before `USER factory`; its comment says that only the factory's user can enter the folder. Nothing else in the Dockerfile changes.

`image/compose.yml`: the top-level `secrets:` and the service's `secrets:` are removed, and so is the comment above the service's `secrets:`. The service's `volumes` gain a fourth entry after the three named volumes, in this key order:

```yaml
      - type: bind
        source: ./secrets/hosting-token
        target: /home/factory/.secrets/hosting-token
        read_only: true
        bind:
          create_host_path: false
```

A comment above it says why: Compose ignores a file secret's owner and mode outside Swarm, so the folder, not the file, keeps the agent out. The host file stays `image/secrets/hosting-token`. Nothing else in the compose file changes: the name, the build, the restart policy, the health check, the environment and the three named volumes stay.

`image/entrypoint.sh`: its header comment's last sentence ("so either can remove the other's") is made true again: the shared umask lets either user remove the other's files in `/work`. This is the stale comment F0012's acceptance found (section 4); no line of code changes.

Tests: a new module `tests/test_token_folder.py`, reading the Dockerfile with `_path_settings` of `tests/test_image.py` and `dockerfile_instructions` of `tests/dockerfile_support.py`, the uids with `_uid_of` of `tests/test_image_users.py`, and the compose file with ruamel.yaml's safe loader as `tests/test_compose.py` does. By the human's leave (FEATURE decision 9), and no other change to an earlier story's test:

- `tests/test_image_credentials.py` (F0010-S0013): `FILE_SETTING` becomes `"ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token"`; in `test_the_compose_file_mounts_the_token_as_a_secret_and_sets_nothing_secret`, the two assertions on `compose["secrets"]` and `service["secrets"]` are replaced by `"secrets" not in compose` and `"secrets" not in service`, and the test is renamed `test_the_compose_file_has_no_secret_and_sets_nothing_secret`; its assertions on the environment and `env_file` stay; the module's docstring says "a mounted file" for "a mounted secret".
- `tests/test_image_users.py` (F0010-S0015): `test_the_token_secret_belongs_to_the_factory_user_and_not_to_the_agent` is removed, with the `COMPOSE` constant and the imports only it used; `_uid_of` stays, used by the new module; the module's docstring drops "and the uids of both users". Its check (the factory's uid is not the agent's, and the agent's is not 0) moves to criterion 4 of the new module.
- `tests/test_compose.py` (F0010-S0007): in `test_the_three_volumes_are_mounted_and_declared`, the expected list of the service's `volumes` gains the bind mount above as its fourth entry, as the safe loader reads it (`{"type": "bind", "source": "./secrets/hosting-token", "target": "/home/factory/.secrets/hosting-token", "read_only": True, "bind": {"create_host_path": False}}`); the test's name and its assertion on the three top-level volumes stay.

## Acceptance criteria

1. The Dockerfile creates `/home/factory/.secrets` with `mkdir -p`, and that folder's last `chown` is `factory:factory` and its last `chmod` is `0700`.
2. The Dockerfile sets `ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token` before `USER factory`, and `FACTORY_TOKEN_FILE` is still the only `ENV` or `ARG` whose name holds `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL` (the changed test of `tests/test_image_credentials.py`).
3. The last entry of the compose service's `volumes`, as ruamel.yaml's safe loader reads it, has the keys `type`, `source`, `target`, `read_only` and `bind` in that order. It is a bind mount whose source is the host file `./secrets/hosting-token`; it is read-only; and its bind options set `create_host_path` to false. Its `target` is exactly the value of the Dockerfile's `ENV FACTORY_TOKEN_FILE`, and the target's folder (its parent) is the folder of criterion 1.
4. The owner of the token's folder is the user `factory`, whose `useradd --uid` (1000) differs from the agent's (1001), and the agent's uid is not 0; no `useradd` gives `agent` the group `factory`.
5. The compose file has no top-level `secrets` and the service has none (the changed test of `tests/test_image_credentials.py`), and the service's `volumes` are the three named volumes followed by the bind mount (the changed test of `tests/test_compose.py`).
6. What must still hold: the credential helper is still copied before `USER factory`, the compose project's name and the health check are as before (the tests of `tests/test_image_credentials.py`, `tests/test_compose_project.py` and `tests/test_compose.py` pass), and the agent home and `/work` keep their owners and modes (`tests/test_agent_home_ownership.py`).
7. The comments say why; the reviewer checks them in the diff, and no test is written for a comment: the header comment of `image/entrypoint.sh` no longer says that either user can remove the other's files without naming `/work`; the comment above `ENV FACTORY_TOKEN_FILE` says that only the factory's user can enter the folder; the comment above the bind mount in `image/compose.yml` says that Compose ignores a file secret's owner and mode outside Swarm, so the folder, not the file, keeps the agent out.
8. `make check` stays green.
9. docs: the operator guide's section *The hosting-service token* says that the host file is still `image/secrets/hosting-token`, that Compose mounts it read-only at `/home/factory/.secrets/hosting-token` (where `FACTORY_TOKEN_FILE` points), that the folder is made in the image as `factory:factory`, mode `0700`, so the agent cannot enter it whatever the file's mode, and why the compose secret was dropped (Compose ignores a file secret's `uid`, `gid` and `mode` outside Swarm; on Windows the file shows `-rwxrwxrwx`, owner 0, under Docker Desktop and Podman alike); that the host file's permissions still matter, because anyone on the host who can read it has the token: on a Linux host with Docker, `chown 1000` and `chmod 0400`; with rootless Podman on a Linux host, `chmod 0400 image/secrets/hosting-token` first and then `podman unshare chown 1000 image/secrets/hosting-token`, because the host user maps to root in the container and no longer owns the file after the `chown`; on Windows and macOS, keep the repository in a folder of your own user account that other accounts cannot read; that a missing host file makes Compose refuse to start rather than create a folder in its place. Its paragraph "Left for v2" also names git's hooks in the shared checkout's `.git`, which the agent can write and the factory's git runs as the factory's user, beside the project commands: the folder closes the agent's direct read, not code the factory's user runs for it. The morning observations there and in *The agent runs as a second user* use the new path (`docker exec -u agent <container> cat /home/factory/.secrets/hosting-token` and `ls /home/factory/.secrets` are refused with `Permission denied`; `ls -lnd /home/factory/.secrets` shows `drwx------` and uid 1000), and that section no longer says the token file is `0600` and owned by `factory`, but that the agent cannot enter its folder. The section *Users and directories* gets a row for `/home/factory/.secrets`. The configuration table's row of `FACTORY_TOKEN_FILE` says that the image sets it to the new path. The project guide's sentence on the credential helper says "the mounted file" for "the secret". The decision log records the folder, the bind mount, the probe that found the fault on both runtimes, the indirect route through git's hooks left for v2 with the project commands, and what was rejected (a compose secret with an absolute target, a `chown` or `chmod` in the entrypoint of a file whose owner and mode are the host's, Swarm mode); it marks the earlier claim that the factory's user alone reads the mounted secret, and the default path `/run/secrets/hosting-token`, as superseded. The preflight item `token-file` is S0002's and its text is not changed here. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from pathlib import Path
from ruamel.yaml import YAML
loaded = YAML(typ='safe').load(Path('image/compose.yml').read_text(encoding='utf-8'))
print(loaded['services']['factory']['volumes'][-1])
print('secrets' in loaded, 'secrets' in loaded['services']['factory'])
"
```
Expect: two lines: `{'type': 'bind', 'source': './secrets/hosting-token', 'target': '/home/factory/.secrets/hosting-token', 'read_only': True, 'bind': {'create_host_path': False}}` and `False False`.

```bash
grep -n "/home/factory/.secrets" image/Dockerfile
```
Expect: among the lines printed, the `mkdir -p` that holds `/home/factory/.secrets`, a `chown factory:factory` and a `chmod 0700` of `/home/factory/.secrets`, and `ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token`; a comment line naming the folder may be printed as well.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_token_folder.py tests/test_image_credentials.py tests/test_image_users.py tests/test_compose.py tests/test_compose_project.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted.
   - Interface: names concrete files and lines (`image/Dockerfile` mkdir/chown/chmod and the ENV line, `image/compose.yml` bind entry with key order, `image/entrypoint.sh` header comment), and the test modules and helpers to reuse (`_path_settings`, `dockerfile_instructions`, `_uid_of`). The changes to the three earlier test modules are named exactly and carry the human's leave (FEATURE decision 9).
   - Criteria: each is testable by one test function. Criterion 1 covers mkdir, last chown and last chmod. Criterion 2 covers the ENV before `USER factory` and the only-credential-name rule. Criterion 3 covers the bind entry, its key order and target, and `create_host_path: false`, which is the refusing side for a missing host file. Criterion 4 covers the owner uid, the uid difference, the agent not being 0, and no `useradd` giving agent the group `factory`. Criterion 5 covers the absence of `secrets` and the volume list. Criterion 6 covers what must still hold. Criteria 7 and 9 are comment and docs criteria for the reviewer and documenter. The Interface states no limit or validation whose failing side lacks a criterion.
   - Demo: all three commands are runnable (a Python one-liner on the compose file, a grep, a pytest run). Each `Expect:` line is checkable against the output.
   - Architecture: the files are all under `image/`, tests and docs. This touches no layer of `src/factory`, and the write paths are in order per FEATURE.
   - Scope: inside FEATURE's Scope (the token, and the stale entrypoint comment, decision 8). The preflight item is left to S0002, and the image pins and Podman restart are out of scope. No finding from the format check.
3. tester: red tests for the token folder, plus the changes to three earlier test modules allowed by FEATURE decision 9.
   - criterion 1: tests/test_token_folder.py::test_the_image_makes_the_token_folder_for_the_factory_user_alone (the `mkdir -p` includes `/home/factory/.secrets`; that folder's last chown is `factory:factory` and its last chmod is `0700`, both read with `_path_settings`)
   - criterion 2: tests/test_token_folder.py::test_the_token_setting_points_into_the_folder_before_the_user_changes, and tests/test_image_credentials.py::test_the_dockerfile_installs_the_helper_and_sets_nothing_secret (`FILE_SETTING` changed to the new path)
   - criterion 3: tests/test_token_folder.py::test_the_token_is_bind_mounted_read_only_at_the_setting_in_the_folder (the last volume entry's keys in order and its values; `target` equals the Dockerfile's ENV value and its parent is the folder)
   - criterion 4: tests/test_token_folder.py::test_the_folder_belongs_to_the_factory_user_whom_the_agent_is_not (the folder's owner is `factory`; the uids are 1000 and 1001, they differ, and the agent's is not 0; agent has exactly one useradd, and none of its `--gid/-g/--groups/-G` values is `factory`)
   - criterion 5: tests/test_image_credentials.py::test_the_compose_file_has_no_secret_and_sets_nothing_secret (renamed; asserts `"secrets" not in compose` and not in the service) and tests/test_compose.py::test_the_three_volumes_are_mounted_and_declared (the bind mount added as the fourth expected entry)
   - criterion 6: covered by the existing tests in tests/test_image_credentials.py, tests/test_compose_project.py, tests/test_compose.py and tests/test_agent_home_ownership.py. No new test.
   - criteria 7 and 9 are left to the reviewer and the documenter. Criterion 8 is the gate.

   Files: created tests/test_token_folder.py. Changed tests/test_image_credentials.py (FILE_SETTING, the renamed test, the module docstring now says "mounted file"). Changed tests/test_image_users.py (removed the token-secret test, the COMPOSE constant and the YAML import; `_uid_of` stays; docstring trimmed). Changed tests/test_compose.py (the fourth volume entry). These are the earlier-test edits the Interface names, and no others.

   The new module defines its own `COMPOSE` path, because the constant in test_image_users.py is removed. It reuses `_commands` and `_path_settings` from tests/test_image.py, `dockerfile_instructions` and `DOCKERFILE` from tests/dockerfile_support.py, and `_uid_of` from tests/test_image_users.py. I renamed one constant to `FILE_ENV` because ruff's S105 flagged the name `TOKEN_SETTING`.

   `make test` result: 7 tests fail, all with wrong-result assertions or a KeyError for the missing folder setting. Every module imports, and there are no collection errors. `make lint` is green.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_token_folder.py::test_the_token_setting_points_into_the_folder_before_the_user_changes
4. coder: the implementation is committed (0978b427), but `make check` is red. The cause is the story's own text, not the code.

   Built:
   - `image/Dockerfile`: `/home/factory/.secrets` is added to the `mkdir -p`, with `chown factory:factory` and `chmod 0700` next to those of `/state`. `ENV FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token` keeps its place before `USER factory`, and its comment now says only the factory's user can enter the folder.
   - `image/compose.yml`: both `secrets:` blocks and the old comment are gone. The read-only bind mount is the fourth volume entry, keys in the Interface's order, with a comment explaining that Compose ignores a file secret's owner and mode outside Swarm.
   - `image/entrypoint.sh`: the header comment now ends "remove the other's files in /work".

   Checks: lint, types, layers, sast, licenses and test are green, and the 7 red tests now pass. The failure is `make secrets`. detect-secrets flags a "Secret Keyword" at line 51 of this ticket file, which is acceptance criterion 3. I narrowed the match to the text from `secrets/hosting-token`, `read_only: true` and `bind: {create_host_path: false}`; its `target` is…; shorter pieces of that text pass. The image and test files pass the hook on their own. The tester ran only `make lint`, so this didn't show before. I did not touch the criterion: it is not `## Assignment`, and a `pragma: allowlist secret` or a baseline entry needs your leave under CLAUDE.md.

   Options:
   (a) Reword criterion 3 so it no longer matches, without changing what it means. For example, give the values as prose: "the source is `./secrets/hosting-token`, it is read-only, and `create_host_path` is false". I would rewrite only that sentence and check it with the hook.
   (b) Add `<!-- pragma: allowlist secret -->` at the end of line 51.
   (c) Add a `.secrets.baseline` entry for the ticket file.

   I would choose (a): it changes no meaning and leaves no marker or baseline entry once the ticket moves to `done/`. Say which, and I will apply it, run `make check` and send the story to review.

   Refactor: I read the diff; it is three small config changes and a comment, with nothing to tidy.
5. human (pull request comment, 2026-10-17): (a). Reword only criterion 3's sentence as prose, with the same meaning (source `./secrets/hosting-token`, read-only, `create_host_path` false, the target, the key order), check it with the hook, then run `make check` and go on to review.
6. coder: I reworded criterion 3 as you asked in entry 5, but `make secrets` is still red because my own log entry 4 quotes the old text.

   - **The reword:** criterion 3 now gives the values as prose: the bind mount's source is the host file `./secrets/hosting-token`, it is read-only, its bind options set `create_host_path` to false, and the target and key order are unchanged. Running `detect-secrets scan` on the ticket no longer flags line 51. The change is in the working tree for the factory's commit.
   - **What is still red:** `make secrets` now fails on line 115 with a "Secret Keyword". That line is my log entry 4, which quotes the fragment that matched (`secrets/hosting-token`, `read_only: true` and `bind: {create_host_path: false}`; …). The log is append-only and belongs to the factory, so I can't change it.
   - **The implementation:** it is committed in 0978b427. `make secrets` is the only failing target; lint, types, layers, sast, licenses and test were green in my last run.

   Options:
   (a) You edit log entry 4 in a commit of your own and replace the quoted fragment with "the criterion's values", so nothing in it matches. Nothing goes into the baseline and no marker is added.
   (b) You give leave for a `.secrets.baseline` entry for this file. detect-secrets matches baseline entries by file path, so the entry stops covering the file once the ticket moves to `done/`. Then `make secrets` on `main` would fail again.
   (c) You add `pragma: allowlist secret` to line 115 yourself.

   I would choose (a). Once that commit is in, I will run `make check` and send the story to review.
