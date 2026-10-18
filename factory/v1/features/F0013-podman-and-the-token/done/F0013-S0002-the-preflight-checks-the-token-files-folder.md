---
stage: done
pr: 183
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The preflight checks the token file's folder

## Assignment (as of log entry 1)

The preflight item `token-file` passes only when the token file belongs to the factory's user and has no permission bit for group or others. Since S0001 that is not what keeps the agent out: the file is a bind mount whose owner and mode are the host's (on Windows `-rwxrwxrwx`, owner 0, under Docker Desktop and Podman), and the folder `/home/factory/.secrets`, the factory's alone with mode `0700`, keeps the agent from reaching it. So the item as it stands would stop every start on Windows with `the token file belongs to uid 0, not to 1000`, and it would pass a file of mode `0600` in a folder anyone can enter, which is no protection when the file is replaced. The human's answer (2026-10-17): the agent cannot read the token "whatever the file's own mode". This story makes the item check the folder that holds the token file: it exists, belongs to the factory's user and has no permission bit for group or others; the file must exist, and its own owner and mode are no longer checked (FEATURE decision 10). The tests of the item, written by F0010-S0013, are replaced by the human's leave (FEATURE decision 11).

## Interface

`factory.application.preflight.token_file_item(path: Path | None, *, uid: int, stat: Callable[[Path], os.stat_result]) -> PreflightItem`: the signature, the name `token-file` and the detail form `<path>: <fault>` stay. The rule, checked in this order, the first fault found being the detail:

| Case | Fault |
|---|---|
| `path` is `None` | `no token file is set` (as now) |
| `stat(path.parent)` raises `FileNotFoundError` | `the token file does not exist` |
| `stat(path.parent).st_uid != uid` | `the folder <folder> belongs to uid <n>, not to <uid>` |
| `S_IMODE(stat(path.parent).st_mode) & 0o077 != 0` | `the folder <folder> has mode <mode>; make it 0700` |
| `stat(path)` raises `FileNotFoundError` | `the token file does not exist` (as now) |
| otherwise | passes |

`<folder>` is `path.parent` as `str`, `<n>` its owner, `<mode>` its permission bits as four octal digits (`0750`). The folder comes first, so a folder that is not the factory's user's is reported even when that user cannot enter it (a `stat(path)` there would raise `PermissionError`). The item reads only through `stat`: once with `path.parent`, then, only when the folder passes, once with `path`, and with nothing else; the token file's own owner and mode do not count. `_GROUP_AND_OTHERS` keeps its value; the faults on the file's owner and mode are removed. The docstring says what the item checks now.

Tests: by the human's leave (FEATURE decision 11), the tester replaces the three tests of `tests/application/test_token_file_item.py` (F0010-S0013) by the tests of the criteria below and updates the module's docstring; each test builds a folder in `tmp_path` and the token file in it, so the data is real. Nothing else changes. `tests/entry/test_wiring_extras.py` keeps passing unchanged: its token file lies in `tmp_path`, which pytest makes with mode `0700` for the test's own user.

## Acceptance criteria

1. With the folder of the test's own uid, the item passes for the folder modes `0700` and `0500`, and fails for `0740`, `0720`, `0710`, `0704`, `0702` and `0701` (one permission bit of group or others each), each failure with the detail `<path>: the folder <folder> has mode <mode>; make it 0700` (rows of one parametrized test; the token file has mode `0600`).
2. With the folder of mode `0700` and the test's own uid, the item passes for every token file mode of `0600`, `0644`, `0666` and `0777`: the file's own mode does not count (rows of one parametrized test).
3. With the folder of mode `0700`, the item fails for `uid=os.getuid() + 1`, with the detail `<path>: the folder <folder> belongs to uid <the folder's owner>, not to <that uid>`; a file of a different owner in a folder of the test's own uid is not testable without root and is covered by criterion 6.
4. The item fails for a `None` path with the detail `None: no token file is set`, and for a missing file in a folder of mode `0700` with `<path>: the token file does not exist`; the name is `token-file` in every case (rows of one parametrized test).
5. The first fault found is the detail: a missing token file in a folder of mode `0750` and the test's own uid gives `<path>: the folder <folder> has mode 0750; make it 0700`; a folder of mode `0750` checked with `uid=os.getuid() + 1` gives `<path>: the folder <folder> belongs to uid <the folder's owner>, not to <that uid>`; a token path whose folder does not exist gives `<path>: the token file does not exist` (rows of one parametrized test).
6. The item reads only through `stat`: with a stub that answers, for an absent path and its parent only, an `os.stat_result` of mode `0o100000` (a file with no permission bit) and owner `uid + 1` for the file, and of mode `0o040700` and owner `uid` for the folder, the item passes, and the stub was asked for `path.parent` and then for `path`, once each.
7. What must still hold: the preflight of a tick with a token file in `tmp_path` passes the item, and without the file stops with `preflight_failed` naming `token-file` (the existing test of `tests/entry/test_wiring_extras.py`); the item `agent-user` is unchanged (`tests/application/test_agent_user_item.py`).
8. `make check` stays green.
9. docs: the operator guide's paragraph on the preflight item `token-file` (section *The hosting-service token*) and its row in *The preflight's items* say what the item checks now (the file exists; its folder belongs to the factory's user and has no bit for group or others; the file's own mode does not count, because a bind mount shows the host's) with the four faults and the fix for each (`FACTORY_TOKEN_FILE`, the host file, or a folder that is not the image's); the project guide's sentence on `token_file_item` says the same; the decision log records that the check moved from the file to the folder and why. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
import os, tempfile
from pathlib import Path
from factory.application.preflight import token_file_item
with tempfile.TemporaryDirectory() as folder:
    secrets = Path(folder) / 'secrets'
    secrets.mkdir()
    secrets.chmod(0o700)
    token = secrets / 'hosting-token'
    token.write_text('example-value', encoding='utf-8')
    token.chmod(0o777)
    print(token_file_item(token, uid=os.getuid(), stat=os.stat).passed)
    secrets.chmod(0o750)
    print(token_file_item(token, uid=os.getuid(), stat=os.stat).detail.replace(folder, '<tmp>'))
"
```
Expect: two lines: `True` and `<tmp>/secrets/hosting-token: the folder <tmp>/secrets has mode 0750; make it 0700`.

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_token_file_item.py tests/application/test_agent_user_item.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: `token_file_item` in `factory.application.preflight` has its full signature. The fault table gives the order, the exact detail strings and the formats of `<folder>`, `<n>` and `<mode>`. It also pins the `stat` call sequence (parent first, then the path only when the folder passes).
   - Criteria: each is testable by one parametrized test function. Every rule has both sides. Folder mode: passing 0700/0500 and six failing single-bit modes (criterion 1). Owner: criterion 3 for the failing side, the passing side covered by the other criteria. Missing file and `None`: criterion 4. Order of faults: criterion 5. The file's own mode and owner not counting: criteria 2 and 6. The four-digit octal format of the mode is checked through the detail string in criterion 1.
   - Demo: both commands are runnable. Each `Expect:` line is checkable: the printed `True` and the exact detail with `<tmp>` substituted, and the pytest summary line.
   - Architecture: the change stays in the application layer and reads only through the injected `stat`, so no new I/O or layer crossing. The wiring test in the entry layer stays unchanged.
   - Scope: this is FEATURE decision 10 (S0002 in Scope), and the replacement of the old tests has the human's leave (decision 11). The docs criterion is limited to the operator guide, the project guide and the decision log.
3. tester: Replaced the three tests in `tests/application/test_token_file_item.py` with tests for the criteria, as FEATURE decision 11 allows, and updated the module docstring. Each test builds a `secrets` folder in `tmp_path` and the token file inside it. The `folder` fixture sets the folder back to 0700 at teardown so a 0500 folder can still be cleaned up.
   - criterion 1: tests/application/test_token_file_item.py::test_the_folder_passes_only_without_a_bit_for_group_or_others (0700 and 0500 pass; 0740, 0720, 0710, 0704, 0702 and 0701 fail with the exact detail)
   - criterion 2: tests/application/test_token_file_item.py::test_the_token_files_own_mode_does_not_count (0600, 0644, 0666, 0777)
   - criterion 3: tests/application/test_token_file_item.py::test_a_folder_of_another_owner_fails
   - criterion 4: tests/application/test_token_file_item.py::test_no_path_or_a_missing_token_file_fails (rows: no-path, missing)
   - criterion 5: tests/application/test_token_file_item.py::test_the_first_fault_found_is_the_detail (rows: mode-before-missing-file, owner-before-mode, missing-folder)
   - criterion 6: tests/application/test_token_file_item.py::test_the_item_reads_only_through_stat (the stub records the paths asked; the expected order is [path.parent, path])
   - criterion 7: no new test. The existing tests in tests/entry/test_wiring_extras.py and tests/application/test_agent_user_item.py cover it, and I did not change them.
   - criteria 8 and 9: the coder's `make check` and the docs stage.
   Files changed: tests/application/test_token_file_item.py only. Every module imports, so there are no import errors. The tests fail because the code still checks the file: the item passes a folder with group or others bits, still checks the file's own mode, and calls `stat` with the path, not its parent. The rows that the current code already gets right pass. `make lint` is green. I also ran pytest once on this one module, beyond the single `make test` run the stage asks for, to check why the tests fail after fixing the lint errors (long lines and confusing test ids).

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/application/test_token_file_item.py::test_the_item_reads_only_through_stat
4. coder: The `token-file` item now checks the folder that holds the token file instead of the file itself. The change is in `src/factory/application/preflight.py`, commit "feat(application): the token-file item checks the token's folder".
      - `_token_file_fault` deals with a `None` path first. It then calls the new `_token_folder_fault(path.parent, uid, stat)`: a missing folder → "the token file does not exist", wrong owner → "the folder <folder> belongs to uid <n>, not to <uid>", any 0o077 bit → "the folder <folder> has mode <mode:04o>; make it 0700". Only when the folder passes does it call `stat(path)`, where a `FileNotFoundError` gives "the token file does not exist". The file's own owner and mode are no longer read. `_GROUP_AND_OTHERS` keeps its value and its comment now names the folder. The docstring says what the item checks now.
      - The missing-file text is a shared constant `_MISSING_FILE_FAULT`. I first named it `_NO_TOKEN_FILE`, but ruff S105 flagged it as a possible hardcoded password, so I renamed it rather than add a `noqa`.
      - Design: I split the folder check into its own helper and kept `_token_file_fault` as the sequencer. I rejected one function with both `stat` calls inline: it would have mixed two try blocks and four faults in one body.
      - Refactor: I read the diff and found nothing to change, so there is no refactor commit.
      - Checks: `make check` green (test: green, check: green). `make duplicates`: 0 new, 39 known, 0 gone. The first demo prints `True` and `<tmp>/secrets/hosting-token: the folder <tmp>/secrets has mode 0750; make it 0700`. `tests/entry/test_wiring_extras.py` and `tests/application/test_agent_user_item.py` pass unchanged.
      - Open: criterion 9 (operator guide, project guide, decision log) is for the docs stage. `src/factory/entry/wiring.py` needed no change.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1–6 has a test in `tests/application/test_token_file_item.py`, and each test checks the full detail string, not a substring. Criterion 1 covers 0700 and 0500 against the six single-bit modes, and its detail string checks the four-digit octal form. Criterion 3 checks the owner fault. Criterion 4 covers `None` and a missing file. Criterion 5 has three rows: mode before missing file, owner before mode, and a missing folder. Criterion 6's stub records the paths it is asked for and checks the order `[path.parent, path]`. Each fault in the Interface table has a failing-side test, and the passing side of the owner rule is covered by the other rows. Criterion 7 needs no new test: `src/factory/entry/wiring.py` is unchanged, and no other code or test refers to the old fault texts. The coder's entry records `make check` green.
      - Architecture: the change stays in `factory.application.preflight` and reads only through the injected `stat`. No new import and no I/O.
      - Security: no suppression markers, and the fault texts expose only the configured path, its owner uid and its mode.
      - Quality: `_token_file_fault` runs the checks in order and `_token_folder_fault` checks the folder. The comments explain why. The renamed `_MISSING_FILE_FAULT` constant avoids a `noqa`. The public docstring says what the item checks now. `make duplicates` reported 0 new findings.
      - Ticket hygiene: the log gives the design split and the version that was rejected. `Assignment` matches the code. Criterion 9 still describes what the documenter has to write.
6. documenter: wrote criterion 9; no findings. `python -m factory.entry.check_documents` prints `documents ok`. I did not run `make check`, because I changed only documents.
   - `docs/operator-guide.md`: the `token-file` paragraph in *The hosting-service token* now says what the item checks (the file exists; its folder belongs to the factory's user and has no bit for group or others; the file's own mode does not count). It lists the four faults, each with its fix. Its row in *The preflight's items* says the same.
   - `docs/project-guide.md`: the `token_file_item` sentence now describes the folder check and the `stat` order (`path.parent`, then `path` only when the folder passes).
   - `docs/decisions.md`: added the entry "The preflight checks the token's folder, not the file", with why and what was rejected. I removed the sentence in the F0013-S0001 entry that said the next story would move the check, since it is now done.
   - Cross-read and found current: README; the other parts of the operator guide on the token folder, `agent-user` and the morning observation; the project guide's wiring sections. The code matches the Interface.
   - Stale and unrelated, left alone: nothing seen.

   `make check`: check: green
   `make documents`: documents ok
7. demo: I ran both commands from the repository root exactly as written. Both met their `Expect:` lines, and nothing in the demo contradicts any acceptance criterion. No findings.

   Command 1 (the item on a real folder: mode 0700 with a token file of mode 0777, then the folder at mode 0750):
   ```
   True
   <tmp>/secrets/hosting-token: the folder <tmp>/secrets has mode 0750; make it 0700
   ```
   Met: the two lines match the expectation exactly, and the exit status was 0. This agrees with criterion 1 (a 0750 folder fails with the exact four-digit mode detail) and criterion 2 (a file of mode 0777 does not count when its folder is 0700).

   Command 2 (`uv run pytest --no-header -p no:cacheprovider tests/application/test_token_file_item.py tests/application/test_agent_user_item.py`):
   ```
   ..........................                                               [100%]
   26 passed in 0.05s
   ```
   Met: the last line is `26 passed in 0.05s`, with no failed, error or skipped count. That covers criteria 1–6 and the `agent-user` part of criterion 7.

   Not covered by the demo: the commands do not run `tests/entry/test_wiring_extras.py` (the wiring part of criterion 7), `make check` (criterion 8) or the docs (criterion 9). Earlier entries cover them: the coder and documenter recorded `make check` green, and the documenter recorded `documents ok`. The demo shows nothing against them.
8. done (pull request merged); cost: 6 runs, 3.8 min, 36 turns, 142k tokens in (421k more from cache), 14k out, $0.90
