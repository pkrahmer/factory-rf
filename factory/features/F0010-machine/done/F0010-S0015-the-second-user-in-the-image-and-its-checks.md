---
stage: done
pr: 133
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
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
RUN sed -i 's/\r$//' /etc/sudoers.d/factory-agent && chmod 0440 /etc/sudoers.d/factory-agent && visudo -cf /etc/sudoers.d/factory-agent
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
2. intake: accepted.
   - Interface: names concrete files (`image/sudoers-factory-agent`, `image/Dockerfile` lines, `image/entrypoint.sh` umask line) and the signature `agent_user_item(settings, exists) -> PreflightItem` in `src/factory/application/preflight.py`. Checked against the repo: `InstanceSettings.agent_user` and `token_file` exist, `PreflightItem` and `tool_item` exist, the Dockerfile has `useradd` for uid 1000 and 1001 and `USER factory`, `image/compose.yml` has the secret with uid 1000, and the entrypoint has `set -eu`. The test files are named.
   - Criteria: 1 to 6 are static file checks, one test function each. 7 to 9 cover both sides of the `agent-user` rule: it fails with a token file and no agent user, and passes with an agent user (token file present or not), with no token file, or with a token file that `exists` denies. The sudoers rule is covered by 2 and 3, and its refused side by 3 (no `root`, no `ALL=(ALL`). The umask agreement is criterion 4 and the entrypoint's is criterion 6. 10 and 11 are the closing criteria.
   - Demo: all three commands are runnable. Each `Expect:` line is checkable: four lines, `agent-user False` then `agent-user True`, and `0002`.
   - Architecture: the item lives in the application layer and takes `exists` as an argument, so it has no I/O. Wiring is explicitly left to the probe story (S0016), so the item is not wired here.
   - Scope: within F0010's scope (agent user, WE3.1, R33). It does not touch the project commands or the `time_limit` under `sudo`, which are out of scope.
3. tester: wrote red tests for criteria 1–9, one test per criterion. Criteria 7–9 share one parametrized test with a row for each side of the rule.
   - criterion 1: tests/test_image_users.py::test_the_dockerfile_installs_the_validated_sudoers_file_and_the_agent_user (COPY to /etc/sudoers.d/factory-agent, then one RUN with `chmod 0440` and `visudo -cf` on that path, and `ENV FACTORY_AGENT_USER=agent`; all of them before `USER factory`)
   - criterion 2: tests/test_image_users.py::test_the_sudoers_file_holds_exactly_the_three_defaults_and_the_rule_in_order
   - criterion 3: tests/test_image_users.py::test_the_only_sudoers_rule_lets_the_factory_become_agent_and_nobody_else_more (no line names `root` or contains `ALL=(ALL`, and no line starts with `agent` or `Defaults:agent`)
   - criterion 4: tests/test_image_users.py::test_the_sudoers_umask_equals_the_entrypoints_umask (the two values are compared as octal numbers, both equal 0o002)
   - criterion 5: tests/test_image_users.py::test_the_token_secret_belongs_to_the_factory_user_and_not_to_the_agent (reads the uids from the Dockerfile's `useradd --uid` and compares them with the uid of the compose secret `hosting-token`)
   - criterion 6: tests/test_entrypoint_umask.py::test_the_entrypoint_sets_umask_002_after_set_eu_and_starts_the_instance_with_it (the line after `set -eu` is `umask 002`; a stub `python` writes the output of `umask` to a file in tmp_path, and the test expects `0002`)
   - criteria 7, 8, 9: tests/application/test_agent_user_item.py::test_the_item_fails_only_without_an_agent_user_beside_an_existing_token_file. One row fails with the exact detail (agent_user None, token file exists). Three rows have agent_user `agent`: token file exists, token file missing, no token file. Three rows have agent_user None: no token file (with `exists` answering false and answering true), and a token file `exists` denies. Every row checks the name `agent-user` and an empty detail when the item passes.

   Files created: tests/test_image_users.py, tests/test_entrypoint_umask.py, tests/application/test_agent_user_item.py.

   `make test` stopped at collection with one error: `ImportError: cannot import name 'agent_user_item' from 'factory.application.preflight'`. Because of that, the image and entrypoint tests did not run in that run. They read `image/sudoers-factory-agent`, which does not exist yet, and the current Dockerfile and entrypoint, which lack the new lines, so they will fail on a missing file or a wrong result. `make lint` is green. I skipped the type check, as the stage says.

   I built `InstanceSettings` directly in the item test, not through `read_settings`, so the test covers only the item. I did not test the wiring into the machine checks: the Interface leaves that to the probe story.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
4. coder: made the tester's tests pass without changing them. `make check` is green (coverage 99.54 %). Commits: 3a5ad69 (feat) and f053f1d (refactor).
      - `image/sudoers-factory-agent` (new): a short comment explaining why, then exactly the four lines from the Interface, in order.
      - `image/Dockerfile`: added the `COPY` to `/etc/sudoers.d/factory-agent`, the `RUN` (strip CR, `chmod 0440`, `visudo -cf`) and `ENV FACTORY_AGENT_USER=agent`. They sit after `ENV FACTORY_TOKEN_FILE` and before the `RUN` that writes `/opt/factory/image-id`, so that `RUN` still comes after the last `COPY`, and all of it is before `USER factory`.
      - `image/entrypoint.sh`: `umask 002` is directly after `set -eu`. The test needs the next line to be exactly that, so I put the reason in the header comment instead of on a line of its own.
      - `src/factory/application/preflight.py`: `agent_user_item(settings, exists)` fails with the stated detail only when `agent_user` is None and `token_file` is set and `exists(token_file)` is true. It passes otherwise. `exists` is not called when `agent_user` is set or there is no token file. The name and the detail are module constants, next to the other item names.
      - Design: I added one small function next to `tool_item` and `token_file_item`, the same shape as those. I rejected folding the check into `token_file_item`: the two items answer different questions, and the Interface names this item `agent-user` on its own.
      - Refactor: moved `agent_user_item` below `_token_file_fault`, so `token_file_item` stays next to its helper. Nothing else needed changing.
      - Not done, as the Interface says: the item and `tool_item("sudo", which)` are not wired into the machine checks. That is left to the probe story.
      - Open: the docs criterion is for the documenter.

   `make check`: check: green
5. reviewer: one finding. Everything else checks out:
   - Criteria 1–9 each have a test that tests what it is named after.
   - The `agent-user` rule's failing side and every passing side are rows of one parametrized test, including `exists` answering true with no token file.
   - `agent_user_item` follows the Interface and does no I/O.
   - The sudoers file, the Dockerfile lines (before the image-id `RUN` and before `USER factory`) and `umask 002` directly after `set -eu` match the Interface.
   - No markers that silence a check, and no secrets.
   - The coder's entry reports `make check` green.

   1. `tests/test_image_users.py:17` `_instructions()` is a verbatim copy of `_instructions()` in `tests/test_image_credentials.py:17`: same docstring, same body. Copying an existing helper is a finding under CLAUDE.md. Fix: move it into a shared support module under `tests/` (like `tests/git_support.py`), for example `tests/dockerfile_support.py`, and import it in both test files. The coder may not edit tests, so this goes to the tester: the coder should end with `tests` and name exactly this change.
6. coder: coder (round 1): the review's one finding is about test code, so it goes to the tester. I changed nothing in `src/` or `image/`.
      - Confirmed: `_instructions()` at `tests/test_image_users.py:17` is a verbatim copy of `_instructions()` at `tests/test_image_credentials.py:17`. The docstring and body are the same, and each reads its own `DOCKERFILE` constant (`ROOT / "image" / "Dockerfile"`).
      - Change for the tester: move `_instructions()` into a new shared module `tests/dockerfile_support.py`, named like `tests/git_support.py`. Make it a public function, for example `dockerfile_instructions()`, that reads `image/Dockerfile` from the repository root. Import it in both `tests/test_image_users.py` and `tests/test_image_credentials.py`, and delete both local copies. The assertions stay as they are.
      - Open: nothing else. The implementation from round 0 (3a5ad69, f053f1d) is unchanged, and the reviewer had no findings against it.
7. tester: tester (round 1, approved test change): fixed the review's finding as entry 6 describes. The duplicated Dockerfile helper now lives in one shared test module.
      - New `tests/dockerfile_support.py` (named like `tests/git_support.py`). It holds `DOCKERFILE` (`image/Dockerfile` from the repository root) and the public `dockerfile_instructions()`, which has the same body and docstring as the old `_instructions()`.
      - `tests/test_image_users.py` and `tests/test_image_credentials.py`: deleted both local `_instructions()` copies and their local `DOCKERFILE` constants. Both files now import from `dockerfile_support`: users imports `dockerfile_instructions`; credentials imports that and `DOCKERFILE`, which it still reads once directly. Imports no longer used were dropped (`re` in credentials). No assertion changed.
      - `make test`: green (coverage 99.54 %). `make lint`: green.

   `make lint`: lint: green
   `make test`: test: green
8. coder: coder (round 1, after the tester's change): no code change was needed in this round. The review had one finding, the duplicated `_instructions()` test helper. The tester resolved it in entry 7 by moving the helper to `tests/dockerfile_support.py::dockerfile_instructions()`, which both `tests/test_image_users.py` and `tests/test_image_credentials.py` now import.
      - I re-ran `make check` on the committed state and it is green (coverage 99.54 %). My first call ran past the tool's 120 s default timeout and was moved to the background, so the next run should give `make check` a longer foreground timeout.
      - The implementation from round 0 is unchanged: 3a5ad69 (feat) and f053f1d (refactor), covering `image/sudoers-factory-agent`, `image/Dockerfile`, `image/entrypoint.sh` and `agent_user_item` in `src/factory/application/preflight.py`.
      - Refactor: nothing to change, because this round has no diff outside the tests.
      - Still open, as the Interface says: wiring `agent-user` and `tool_item("sudo", which)` into the machine checks belongs to the probe story. The docs criterion is for the documenter.

   `make check`: check: green
9. reviewer: reviewer (round 1): no findings.
      - Last round's finding is fixed. `tests/dockerfile_support.py::dockerfile_instructions()` is now the one copy of the Dockerfile helper. `tests/test_image_users.py` and `tests/test_image_credentials.py` both import it. No assertion changed.
      - Criteria 1–6: each has a static test or a run test that checks what it is named after.
        - Criterion 1: the COPY and a single RUN with `chmod 0440` and `visudo -cf` come before `USER factory`, and so does the ENV.
        - Criteria 2 and 3: the four sudoers lines are in order. There is no `root`, no `ALL=(ALL`, and no line where `agent` is the user who may use sudo.
        - Criterion 4: the two umasks are compared as octal numbers.
        - Criterion 5: the uids come from `useradd --uid` and are checked against the compose secret.
        - Criterion 6: `umask 002` is the line after `set -eu`, and the stub `python` records `0002`.
      - Criteria 7–9: the `agent-user` rule's failing side and every passing side are rows of one parametrized test. The test also checks that `exists` is asked only about the token file.
      - Code:
        - `agent_user_item` in `src/factory/application/preflight.py` follows the Interface. It does no I/O, has a docstring, and its name and detail are module constants beside the other item names.
        - In `image/Dockerfile` the new lines sit before the image-id RUN, which stays after the last COPY, and before `USER factory`. `sudo` is already in the apt line.
        - `image/sudoers-factory-agent` and `image/entrypoint.sh` match the Interface, and their comments explain why.
      - Wiring is left to the probe story, as the Interface says.
      - No markers that silence a check, no secrets, and no new dependencies.
      - The coder's entry 8 reports `make check` green.
      - Ticket hygiene: the log records the main decision (a separate item, not folded into `token_file_item`). Assignment matches what was built. The docs criterion still describes what the operator and the decision log need.
10. documenter: documenter (round 1): wrote the docs criterion; `make check` is green. I ran no `docker` commands, because there is no image here.
    - `docs/operator-guide.md`, "The agent runs as a second user":
      - Removed the "comes with the next story" wording.
      - Added the one `sudo` rule, quoted with its four lines.
      - Added why each of the three defaults is there: umask `0002` for the restore after an agent-made directory, no pseudo-terminal for the session.
      - Added the preflight item `agent-user`, with the fix: set `FACTORY_AGENT_USER` or remove the token file.
      - Added three morning observations to the table: the mode of an agent-made file and directory (`775`/`664`), the factory's restore after an agent-made directory, and a refused `sudo`.
      - The existing rows already cover the agent run as `agent` (WE3.1) and its failed reads and pushes (WE3.3, WE3.4).
    - `docs/operator-guide.md`, settings table and "The preflight's items": the `FACTORY_AGENT_USER` row says the image sets it. The items table has a new `agent-user` row, built but not yet wired (F0010-S0016). I changed "seven items" to "eight".
    - `docs/decisions.md`: new entry on why the factory's user may become `agent` for one command only, why the sudoers file sets the umask and no pseudo-terminal, and why a missing agent user beside a token file is a stop (the human, 2026-10-14). It also records that I rejected folding the check into `token-file`.
    - Cross-read the README and `docs/project-guide.md` against the diff and found nothing stale.
    - Stale but unrelated, not touched: the opening paragraph of the operator guide still says the preflight and the other machine checks are added by later stories, and the "seven items" count was already wrong before this story (the table had more rows).
    - Findings: none. The code matches the Interface.

    `make check`: check: green
11. demo: demo (round 1): ran the three demo commands from the repository root, in order. All three met their `Expect:` lines, and nothing in the demo contradicts an acceptance criterion. No findings.

    1. Sudoers file without comment and blank lines:
    ```text
    Defaults:factory umask=0002
    Defaults:factory umask_override
    Defaults:factory !use_pty
    factory ALL=(agent) NOPASSWD: ALL
    ```
    Met: exactly the four lines, in order (criteria 2 and 3).

    2. `agent_user_item` with the token file and without, then with, `FACTORY_AGENT_USER=agent`:
    ```text
    agent-user False
    agent-user True
    ```
    Met: two lines, `agent-user False` and `agent-user True`.

    3. Entrypoint with a stub `python` that prints `umask`:
    ```text
    0002
    ```
    Met: one line, `0002` (criterion 6).

    Cross-check against the criteria, beyond what the commands targeted:
    - Criterion 7: the failing item's detail is exactly `FACTORY_AGENT_USER is not set: every agent would run as the factory's user, who can read the token file`.
    - Criterion 8: with `agent_user=agent` and `exists` false, the item is `PreflightItem(name='agent-user', passed=True, detail='')`.
    - Criterion 9: with `agent_user` None and `exists` false, the item passes.
    - Criterion 1: `image/Dockerfile` has the COPY at line 41, the RUN with `chmod 0440` and `visudo -cf` at line 42 and the ENV at line 43. All three come before the image-id RUN (line 45) and before `USER factory` (line 52).
    - Criterion 5: `useradd` gives `factory` uid 1000 and `agent` uid 1001.
    - `umask 002` sits directly after `set -eu` in `image/entrypoint.sh` (criteria 4 and 6).

    Open: as the Interface says, the real `sudo` call, the umask of agent-made files, the factory's restore after an agent-made directory and a refused `sudo` need a real image. They are morning observations listed in `docs/operator-guide.md`. Wiring the item into the machine checks is left to the probe story.
12. done (pull request merged); cost: 10 runs, 37.8 min, 63 turns, 178k tokens in (1017k more from cache), 24k out, $2.15
