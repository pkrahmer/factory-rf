---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-18T19:35:34.686997Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T19:35:34.681665Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T19:35:34.686997Z'
  stage: intake
---

# factory-confine's steps run in the test process

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's `make mutants` left 36 survivors in `src/factory/entry/confine.py`, and its coverage is 78 %. Every row that reaches the restriction or the `exec` runs `factory-confine` in a child process that imports the unmutated package, as decision 18 foresaw. So mutmut and coverage never see steps 3 to 6. Breaking any of the following would go unnoticed:
- dropping the run's folders and its own temporary folder from the rules (`restrict_writes(None, rules.files)`);
- dropping the temporary folder's `0700` mode;
- dropping `parents=True`;
- refusing a one-word command (`len(arguments) <= 4`);
- dropping `TMPDIR` from the command's environment.

This story lets the test process run those steps with the two irreversible calls injected, the same way `main` already takes `abi`. `main` gains `restrict` and `replace`, which default to `restrict_writes` and `replace_process`, and the new in-process tests pass recorders. The existing child-process tests stay as the check against the real kernel. `factory.adapters.landlock` and `replace_process` stay child-only: their own calls cannot be undone in the test process. The wrapper's behaviour, texts and exit status do not change.

## Interface

`factory.entry.confine` (`entry`):

```python
def main(
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    abi: Callable[[], int] | None = None,
    restrict: Callable[[Sequence[Path], Sequence[Path]], None] | None = None,
    replace: Callable[[Sequence[str], Mapping[str, str]], NoReturn] | None = None,
) -> int:
    """Confine this process's writes to the rules, then become the command; 1 when it cannot."""
```

- `restrict` `None` is `factory.adapters.landlock.restrict_writes`. `replace` `None` is `factory.adapters.process.replace_process`. The console script and `python -m factory.entry.confine` pass neither.
- The steps and their texts are unchanged (`docs/project-guide.md`, *The start wrapper*). `restrict` is called once, with `[*rules.folders, rules.temporary_directory]` and `rules.files` in their order, after every folder and the temporary folder exist and before `replace`. A `ConfinementError` from it is `factory-confine: <detail>`, and `replace` is never called.
- `replace` is called once, with the command and `{**os.environ, "TMPDIR": <temporary_directory>}`. An `OSError` from it is `factory-confine: cannot start <command>: <reason>`.

Test module (new): `tests/entry/test_confine_steps.py`. It calls `main` in-process with a recording `restrict` and a `replace` that records and raises a test-local exception. `tests/entry/test_confine.py` is unchanged.

## Acceptance criteria

1. With rules of a missing folder `<tmp>/a/b`, an existing file `<tmp>/f`, a missing temporary folder `<tmp>/t`, and the command `prog x`, `restrict` receives exactly `([<tmp>/a/b, <tmp>/t], [<tmp>/f])`. At that call `<tmp>/a/b` exists, and `<tmp>/t` exists with permission bits `0o700`.
2. In the same run, `replace` receives `["prog", "x"]` and an environment equal to the test process's environment plus `TMPDIR=<tmp>/t`. It is called after `restrict`, and `restrict` is called once.
3. Argument count (rows of one parametrized test): `--rules <file> -- prog`, the four-argument form, reaches `replace` with `["prog"]`. `--rules <file> --`, three arguments, writes the usage line, returns 1 and calls neither `restrict` nor `replace`.
4. Faults that stop the wrapper (rows of one parametrized test):
   - A `restrict` that raises `ConfinementError("<tmp>/l is a symbolic link")` gives exactly `factory-confine: <tmp>/l is a symbolic link\n` on the given `stderr`, returns 1 and never calls `replace`.
   - A `replace` that raises `OSError(errno.ENOENT, "No such file or directory")` gives `factory-confine: cannot start prog: No such file or directory\n` and returns 1.
5. An ABI below 3 calls neither `restrict` nor `replace`, and makes neither `<tmp>/a/b` nor `<tmp>/t`.
6. `restrict` and `replace` left `None` are the adapters' functions: a source check of `factory.entry.confine` finds them as the defaults, and the console script's existing child-process tests still pass unchanged.
7. `make check` stays green.
8. docs: `docs/project-guide.md`, section *The start wrapper*: the paragraph on its tests says that the rows up to step 6 also run in-process with `restrict` and `replace` injected, and that the child-process rows check the real kernel. No other document changes.

## Smoke test

```bash
uv run -q python -c '
import io, json, sys, tempfile
from pathlib import Path
from factory.entry.confine import main
class Replaced(Exception): pass
calls = []
def replace(argv, env):
    calls.append(("replace", list(argv), env["TMPDIR"]))
    raise Replaced
with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    rules = tmp / "rules.json"
    rules.write_text(json.dumps({"folders": [str(tmp / "a" / "b")], "files": [], "temporary_directory": str(tmp / "t")}))
    try:
        main(["--rules", str(rules), "--", "prog"], stderr=io.StringIO(), abi=lambda: 7, restrict=lambda folders, files: calls.append(("restrict", [p.name for p in folders])), replace=replace)
    except Replaced:
        pass
    print(calls[0], (calls[1][0], calls[1][1], Path(calls[1][2]).name), oct((tmp / "t").stat().st_mode & 0o777))
'
```
Expect: `('restrict', ['b', 't']) ('replace', ['prog'], 't') 0o700`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
