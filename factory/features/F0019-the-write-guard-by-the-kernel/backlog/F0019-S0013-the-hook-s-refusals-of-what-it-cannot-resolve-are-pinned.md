# The hook's refusals of a path or settings file it cannot resolve are pinned

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's third `make mutants` counts `factory.adapters.claude_guard` among the feature's modules, because S0011 changed it. Five mutants survive there. Two are in S0011's new `_beneath_temporary_directory`. With a temporary folder in the settings, a `file_path` whose real path cannot be computed (a NUL character) is refused today with `<file_path> is outside the checkout.`. But a mutant that allows it (`return True`), or one that lets `judge` raise (`or` turned into `and`, then `None.is_relative_to`), goes unnoticed: the one NUL test (`tests/adapters/test_claude_guard.py`) builds its settings without a temporary folder. A raising `judge` makes `factory-guard` end with a traceback instead of status 2, which Claude Code does not treat as a refusal. The third is older code, `read_guard_settings`. Its test checks only that the fault is not empty, so a fault text replaced by `str(None)` passes, although the project guide promises `guard settings <file>: <fault>`. The last two change only the spelling of the encoding and are equivalent. This story pins the current behaviour with tests in the test process. No module under `src/factory/` is expected to change. The project guide's list of the guard's tests gains S0011's module and the new one.

## Interface

No module under `src/factory/` is expected to change. The pinned behaviour:

- `factory.adapters.claude_guard.judge(payload, settings)` (`adapters`) never raises. A `file_path` whose real path cannot be computed (`os.path.realpath` raises `ValueError` for a NUL character) is refused with `<file_path as given> is outside the checkout.`. This holds whether `settings.temporary_directory` is set or `None`, and whether the path lies beneath the temporary folder or the checkout.
- `factory.adapters.claude_guard.read_guard_settings(path)` (`adapters`): `GuardSettingsInvalid.fault` is exactly `str()` of the `OSError`, `UnicodeDecodeError` or `ValidationError` that reading or validating raised, and the message is `guard settings <path>: <fault>`.

Test module (new): `tests/adapters/test_claude_guard_faults.py`. It calls the functions in the test process. `tests/adapters/test_claude_guard.py` and `tests/adapters/test_claude_guard_temporary.py` stay unchanged, apart from helpers moved under the standing leave of `CLAUDE.md`.

## Acceptance criteria

1. `judge` with settings whose root is `<R>` (an existing folder, write paths `["src/*"]`) and whose `temporary_directory` is `<T>` (an existing folder beside `<R>`), with a `Write` payload. Rows of one parametrized test, each returning `GuardVerdict(allowed=False, message="<file_path> is outside the checkout.")` and raising nothing:
   - `<T>/a\x00.txt`.
   - `<R>/src/a\x00.py`.
   - `<T>/a\x00.txt` with `temporary_directory` `None`: the same refusal, which is the side that already passes.
   - `<T>/a.txt` (no NUL): `GuardVerdict(allowed=True, message="")`. This is the allowed side, so the refusal above is the NUL character's and not the folder's.
2. `read_guard_settings` on a file that cannot be read. Rows of one parametrized test, each raising `GuardSettingsInvalid` whose `fault` is exactly the given text and whose `str()` is `guard settings <path>: <fault>`:
   - `<path>` a folder: `[Errno 21] Is a directory: '<path>'`.
   - `<path>` missing: `[Errno 2] No such file or directory: '<path>'`.
   - `<path>` holding `root: /x\n`: `str()` of the `ValidationError` that `GuardSettings.model_validate_json("root: /x\n")` raises.
3. `make check` stays green.
4. docs: `docs/project-guide.md`, section *The guard command*, the `Tests:` line after *Failing open*: it names `tests/adapters/test_claude_guard_temporary.py` (S0011's module, missing there today) and `tests/adapters/test_claude_guard_faults.py`. No other document changes.

## Smoke test

```bash
uv run -q python -c '
import json, tempfile
from pathlib import Path
from factory.adapters.claude_guard import judge
from factory.domain.agent_runs import GuardSettings
with tempfile.TemporaryDirectory() as d:
    base = Path(d); (base / "checkout").mkdir(); (base / "t").mkdir()
    settings = GuardSettings(root=base / "checkout", write_paths=["src/*"], protected_paths=[], temporary_directory=base / "t")
    for name in ("t/a\x00.txt", "checkout/src/a\x00.py"):
        verdict = judge(json.dumps({"tool_name": "Write", "tool_input": {"file_path": f"{d}/{name}"}}), settings)
        print(verdict.allowed, verdict.message.replace(d, "<base>").replace("\x00", "<NUL>"))
'
```
Expect: `False <base>/t/a<NUL>.txt is outside the checkout.`, then `False <base>/checkout/src/a<NUL>.py is outside the checkout.`

```bash
uv run -q python -c '
import tempfile
from pathlib import Path
from factory.adapters.claude_guard import read_guard_settings
from factory.domain.errors import GuardSettingsInvalid
with tempfile.TemporaryDirectory() as d:
    try:
        read_guard_settings(Path(d))
    except GuardSettingsInvalid as error:
        print(str(error).replace(d, "<base>"))
'
```
Expect: `guard settings <base>: [Errno 21] Is a directory: '<base>'`

## Journal
