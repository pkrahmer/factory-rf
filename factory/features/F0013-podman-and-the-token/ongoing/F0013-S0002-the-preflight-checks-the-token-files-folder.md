---
stage: ready
pr: null
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
