---
stage: tests
pr: 55
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The write-path guard hook

## Assignment (as of log entry 1)

Build the guard that refuses an agent's Edit or Write outside its write paths while the agent run is going on. It is the command `factory-guard --settings <file>` that the agent runtime registers as a Claude Code `PreToolUse` hook (R12: hook scripts that refuse writes outside a write path). The file holds the `GuardSettings` of the stage as JSON, taken from `WritePathService.at` (S0003) at the stage-start commit; the guard reads that file and nothing else, so a rewrite of the pipeline definition in the work tree changes no verdict (WE2.1, WE2.3). The verdict is S0003's `refusal`, applied to the real path of the file the tool call names; the same function drives the undo (S0005). `ClaudeCodeRuntime` (F0001-S0009, built) writes the settings file as `GuardSettings.model_dump_json()` and registers the hook on `Edit|Write`; this story reads the file. `pyproject.toml` registers `factory-guard = "factory.entry.guard:main"`; the tests and the demo run the guard as `python -m factory.entry.guard`. Covers WE2.1 and WE2.3 (the guard's side), R12 (the hook), R32; keeps kept things 5 (a hook refuses writes outside the write paths) and 17. Morning observation: a real agent run whose write outside its write paths is refused by the registered hook, and the console script on the `PATH` of the container.

## Interface

`src/factory/domain/errors.py` gains one type:

```python
class GuardSettingsInvalid(FactoryError):
    path: str
    fault: str
    def __init__(self, path: str, fault: str) -> None: ...
```

`src/factory/adapters/claude_guard.py`

```python
class GuardVerdict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    allowed: bool
    message: str = ""  # the refusal text

def read_guard_settings(path: Path) -> GuardSettings: ...
def judge(payload: str, settings: GuardSettings) -> GuardVerdict: ...
```

`src/factory/entry/guard.py`

```python
def main(argv: Sequence[str] | None = None, *, stdin: TextIO | None = None, stderr: TextIO | None = None) -> int: ...
```

`None` means `sys.argv[1:]`, `sys.stdin` and `sys.stderr`, read at the call. The module runs `raise SystemExit(main())` under `if __name__ == "__main__"`, so `python -m factory.entry.guard --settings <file>` works. `GuardSettings` is `factory.domain.agent_runs.GuardSettings`, `refusal` is S0003's.

`src/factory/entry/wiring.py` re-exports `read_guard_settings` and `judge` (it gains `__all__ = ["build_work_item_reader", "judge", "read_guard_settings"]`), and `guard.py` imports both from `factory.entry.wiring`, because `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` lets no other module of `factory.entry` import `factory.adapters`; that test stays unchanged.

Rules:

- The settings file holds `GuardSettings` as JSON, as `GuardSettings.model_dump_json()` writes it (`root` an absolute path). `read_guard_settings` raises `GuardSettingsInvalid(path, fault)` when the file is missing, unreadable, not JSON or not valid `GuardSettings`; the message names the file and the fault.
- `payload` is the JSON that Claude Code sends to a `PreToolUse` hook on its standard input. The guard looks at `tool_input.file_path` of any tool call it is given. It reads the payload with a private Pydantic model in the module (`extra="ignore"`, `tool_input: _ToolInput | None`, `file_path: StrictStr | None`), so no `Any` is inspected by hand. A payload that is not JSON, not an object, has no `tool_input` object, has no `file_path`, or has a `file_path` that is empty or not a string is allowed: any JSON error or `ValidationError` of that model means "allowed" (the guard fails open for what it cannot read, as v1; handover section 8 leaves this for v2).
- A relative `file_path` is taken relative to `settings.root`. The guard judges the real path: `os.path.realpath` of the joined path, so `..` segments and symbolic links are resolved. A real path that is not inside the real path of `settings.root` (by `Path.is_relative_to` or `os.path.commonpath`, never by a string prefix, so `<root>-x/a.py` is outside `<root>`) gives `allowed=False` with the message `<file_path as given> is outside the checkout.`. A real path inside it is judged with `refusal(<the real path relative to the root, POSIX>, settings)`, and a non-`None` result is the message.
- `judge` answers every payload it can read and never raises: a `file_path` whose real path cannot be computed (`os.path.realpath` raises `ValueError` for a NUL character, or any `OSError`) gives `allowed=False` with the message `<file_path as given> is outside the checkout.` `read_guard_settings` turns every failure to read or decode the file (`OSError`, `UnicodeDecodeError`, a JSON error, a `ValidationError`) into `GuardSettingsInvalid`, so `main` answers with 0 or 2 and never ends in an exception: Claude Code does not treat a crashed hook as a refusal.
- What `judge` returns has `allowed` true exactly when `message` is empty (a refusal always has its text); `GuardVerdict` itself is a plain data model and checks no such invariant.
- `main(argv, ...)` needs `--settings <file>` in `argv`. It reads the payload from `stdin`. It returns 0 for an allowed payload, writing nothing to `stderr`. It returns 2 for a refused one, writing the message and a newline to `stderr` (Claude Code blocks the tool call on status 2 and shows `stderr` to the agent). It returns 2 as well when `--settings` is missing or is the last argument with no value (the message is `usage: factory-guard --settings <file>`) and when `read_guard_settings` raises (the message is the error's). It never writes to a standard output. Called with no arguments, as the console script does, it reads `sys.argv[1:]`, `sys.stdin` and `sys.stderr`.
- The guard reads no file besides the settings file: it takes no write path from the pipeline definition, in the work tree or anywhere else.

Tests: `tests/adapters/test_claude_guard.py` and `tests/entry/test_guard.py`. Settings objects are built in `tmp_path` with a checkout directory; the end-to-end case runs `sys.executable -m factory.entry.guard` in a subprocess; the case of criterion 14 uses the shared fixtures and `WritePathService` (a `StageStart` built as in S0003's tests); the case of criterion 16 uses `monkeypatch` for `sys.argv`, `sys.stdin` and `sys.stderr`. Criterion 18 builds the model through a variable typed `type[BaseModel]` and assigns with `setattr(instance, field, value)`, the field's name in a variable, as `CLAUDE.md` asks under *Tests*.

## Acceptance criteria

1. `judge` allows an `Edit` payload and a `Write` payload whose absolute `file_path` is inside the write paths (`src/*`): `allowed` is true and `message` is empty.
2. `judge` refuses a path inside the checkout that no write path matches (`docs/a.md` under `src/*`) with the message `docs/a.md is outside the write paths of this stage.`
3. `judge` refuses a protected path although a write path matches it (write paths `["*"]`, `pyproject.toml`) with the message `pyproject.toml is owned by the human; a change there is a question.`
4. `judge` refuses a path outside the checkout (a sibling directory of the root, a sibling whose name begins with the root's name, `<root>-x/a.py`, and `/etc/passwd`) with the message `<file_path as given> is outside the checkout.`
5. `judge` resolves `..`: `<root>/src/../pyproject.toml` is refused as the protected `pyproject.toml`, and `<root>/src/../src/a.py` is allowed as `src/a.py`.
6. `judge` takes a relative `file_path` relative to the root: `src/a.py` is allowed and `docs/a.md` refused under `src/*`.
7. `judge` judges the real path: a symbolic link `src/out` pointing outside the checkout is refused as outside the checkout, a link `src/p` pointing at `pyproject.toml` is refused as protected, and a link `src/ok` pointing at `src/real.py` is allowed.
8. `judge` allows a payload that is not JSON, a JSON array, an object without `tool_input`, a `tool_input` that is a string, a `tool_input` without `file_path`, and a `file_path` that is a number or the empty string.
9. `read_guard_settings` returns the `GuardSettings` that `model_dump_json()` wrote, with `root` an absolute `Path`.
10. `read_guard_settings` raises `GuardSettingsInvalid` carrying the file's path and a fault, with a message naming both, for a missing file, a directory at the path, a file whose bytes are not UTF-8 (`b"\xff\xfe"`), a file that is not JSON and a JSON object that is not valid `GuardSettings`.
11. `main` returns 0 and writes nothing to `stderr` for an allowed payload on `stdin`.
12. `main` returns 2 and writes exactly the refusal message and a newline to `stderr` for a refused payload.
13. `main` returns 2 and writes `usage: factory-guard --settings <file>` when `--settings` is missing and when it is the last argument with no value, and returns 2 with a message naming the file when the settings file is missing or invalid.
14. The guard reads only the settings file: with the settings written from `WritePathService.at` at the stage-start commit, rewriting `factory/pipeline.yml` in the work tree to widen the role's write paths changes no verdict (`docs/a.md` stays refused, status 2).
15. Run as `python -m factory.entry.guard --settings <file>` in a subprocess, an allowed payload gives exit status 0 and a refused one gives exit status 2 with the message on `stderr` and nothing on `stdout`.
16. `main()` called with no arguments, as the console script `factory-guard = "factory.entry.guard:main"` calls it, reads `sys.argv`, `sys.stdin` and `sys.stderr`: with the three monkeypatched (`--settings <file>` in `sys.argv`, a refused payload on `sys.stdin`), it returns 2 and the patched `stderr` holds the refusal message and a newline; with an allowed payload it returns 0.
17. `judge` refuses a `file_path` that contains a NUL character (`<root>/src/a\x00.py`, the payload written with `json.dumps`, which escapes the NUL as `\u0000`) with `allowed=False` and the message `<file_path as given> is outside the checkout.`, instead of raising, and `main` returns 2 for that payload.
18. `GuardVerdict` is frozen and forbids unknown fields: assigning to `allowed` raises `ValidationError`, and building it with an unknown field `extra` raises `ValidationError`.
19. make check stays green.
20. docs: `docs/project-guide.md` explains the guard (the command, the settings file it reads, exit status 2 as the refusal, that it judges real paths and fails open for a payload it cannot read) and that `pyproject.toml` registers it as `factory.entry.guard:main`; `docs/operator-guide.md` names `factory-guard` among the commands on the `PATH` and says that the agent run's `PATH` must contain `factory-guard`, which F0010's preflight probes; `docs/decisions.md` records that the guard reads only the settings file taken at the stage-start commit and keeps v1's fail-open reading of the payload.

## Demo

```bash
uv run python - <<'EOF'
import json, subprocess, sys, tempfile
from pathlib import Path
from factory.domain.agent_runs import GuardSettings
from factory.domain.write_paths import PROTECTED_PATHS

root = Path(tempfile.mkdtemp())
settings = root / 'guard.json'
settings.write_text(GuardSettings(root=root, write_paths=['src/*'], protected_paths=list(PROTECTED_PATHS)).model_dump_json())

def ask(path):
    payload = json.dumps({'tool_name': 'Write', 'tool_input': {'file_path': str(root / path)}})
    done = subprocess.run([sys.executable, '-m', 'factory.entry.guard', '--settings', str(settings)], input=payload, capture_output=True, text=True)
    print(path, done.returncode, repr(done.stderr.strip()))

for path in ['src/app.py', 'docs/a.md', 'pyproject.toml', 'src/../pyproject.toml']:
    ask(path)
EOF
```
Expect: four lines. `src/app.py 0 ''`; `docs/a.md 2 'docs/a.md is outside the write paths of this stage.'`; `pyproject.toml 2 'pyproject.toml is owned by the human; a change there is a question.'`; `src/../pyproject.toml 2 'pyproject.toml is owned by the human; a change there is a question.'` (the traversal is resolved before the verdict).

```bash
echo '{}' | uv run python -m factory.entry.guard; echo "status $?"
```
Expect: one line on standard output, `status 2`, and the usage line `usage: factory-guard --settings <file>` on standard error (the option is missing, so the guard refuses).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: concrete modules and signatures (`GuardSettingsInvalid`, `GuardVerdict`, `read_guard_settings`, `judge`, `main`, the wiring re-export and `__all__`). The payload model, exit statuses, messages and the fail-open rule are fully specified.
   - Criteria: 20 criteria, each testable by one test function. Every Interface comment and rule has one. Each rule has both sides. Allowed and refused cover inside/outside the root, `..`, symlinks and a relative path. Readable and unreadable payloads are covered (8, 17). A valid settings file (9) and every kind of invalid one (10) are covered. Allowed `main` (11), refused `main` (12) and usage and settings errors (13) are covered. Frozen and `extra="forbid"` are covered (18). Criterion 20 is the docs item and `make check` stays last but one.
   - Demo: both blocks are runnable. Every `Expect:` line gives checkable output: exit codes, stderr text, and the resolved traversal.
   - Architecture: the guard sits in `factory.entry` and reaches the adapter only through `wiring`, which matches the existing import test. The verdict reuses the domain's `refusal` from S0003, as decisions 9, 11 and 12 describe.
   - Scope: inside F0004's scope (the guard hook). Writing the settings file and registering the hook stay with F0001-S0009 and are not touched here.
   - Minor gap, not blocking: a `file_path` that resolves to the root itself (for example `.`) has no criterion. It falls to S0003's `refusal` for an empty path.
