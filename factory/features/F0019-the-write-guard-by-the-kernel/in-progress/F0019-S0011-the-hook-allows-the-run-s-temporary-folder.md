---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 232
comments_read: [6254736316]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T20:24:50.431093Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T20:24:50.436693Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-18T20:25:04.553791Z'
  stage: intake
  run: cdaf3db1f67f4b3cb924f77e1a59786b
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-18T20:25:47.742152Z'
  stage: intake
---

# The hook allows an edit in the run's own temporary folder

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

R14 in every shipped agent says "Make temporary files only in `$TMPDIR` ... the run's own folder", and the kernel allows that folder. The hook `factory-guard` refuses it. In F0019's second acceptance, the acceptance reviewer's `Write` of `$TMPDIR/feature-smoke.sh` got `PreToolUse:Write hook error: [factory-guard --settings /state/runs/guard-<session>.json]: /tmp/factory-run-<session>/feature-smoke.sh is outside the checkout.`, and the agent then wrote the file through the shell. The agent's instructions thus send it to a folder that one of its own tools refuses, and it can then only work around the refusal, which R14 also forbids. The disagreement also falls outside decision 15, which names protected paths as the one expected disagreement between the hook and the kernel. So the cross-check of decision 16, which reads the hook's refusals in the transcripts, would count every such refusal as a disagreement. This story gives the guard settings the run's temporary folder, and the hook allows an `Edit` or `Write` beneath it. Without a temporary folder in the settings (an unconfined runtime, an older settings file), the hook judges as today. The tool paths stay kernel-only (decision 8). Removing the hook stays a later feature's work.

## Interface

`factory.domain.agent_runs` (`domain`):

```python
class GuardSettings(BaseModel):
    root: AbsolutePath
    write_paths: list[str]
    protected_paths: list[str]
    tool_paths: list[str] = []
    temporary_directory: AbsolutePath | None = None
```

- `temporary_directory` is the run's own temporary folder, or `None`. A relative path is refused like `root`.

`factory.adapters.claude_guard` (`adapters`):

```python
def judge(payload: str, settings: GuardSettings) -> GuardVerdict:
    """Judge the file a tool call names against the settings; never raises."""
```

- The real path (`os.path.realpath`) is judged, as today. A real path inside the real root goes to `refusal`, as today, even when the root lies beneath the temporary folder. Otherwise, a real path strictly beneath the real `temporary_directory` is allowed. Anything else is `<file_path> is outside the checkout.`, as today.
- "Beneath" is tested on path parts, not on a string prefix: `<temporary_directory>-x/a` is outside. The folder itself is not beneath itself.
- A link in the temporary folder that points into the checkout is judged by its real path, so the write paths decide.

`factory.adapters.claude_runtime` (`adapters`): `ClaudeCodeRuntime.run`, when built with `confine_executable` and given guard settings, writes the guard settings file with `temporary_directory` set to the run's temporary folder, the same path the command gets as `TMPDIR`. Built without `confine_executable`, it writes `temporary_directory` as `null`.

Test modules (new): `tests/adapters/test_claude_guard_temporary.py`, `tests/adapters/test_claude_runtime_guard_temporary.py`. Helpers of `tests/adapters/test_claude_guard.py` and `tests/confine_support.py` that the new tests need are reused or moved under the standing leave of `CLAUDE.md`.

## Acceptance criteria

1. `judge` with `temporary_directory` `<T>` (an existing folder outside the checkout `<R>`), rows of one parametrized test:
   - `<T>/notes.txt`: allowed.
   - `<T>/deep/new/x.txt` (missing folders): allowed.
   - `<T>` itself: refused, `<T> is outside the checkout.`.
   - `<T>-x/a.txt`: refused, `<T>-x/a.txt is outside the checkout.`.
   - `<T>/link.py`, a link to `<R>/src/a.py`, with write paths `["docs/*"]`: refused with the text `refusal` gives for `src/a.py`.
   - `<T>/notes.txt` with `temporary_directory` `None`: refused, `<T>/notes.txt is outside the checkout.`.
2. A guard settings file with `"temporary_directory": "<T>"` and one without the key both read back through `read_guard_settings`, the second as `None`. `"temporary_directory": "relative/t"` raises `GuardSettingsInvalid` (rows of one parametrized test).
3. Through a stand-in `claude` that records `$TMPDIR` and the guard settings file named in its hook settings, rows of one parametrized test:
   - A runtime built with `confine_executable`: the file's `temporary_directory` equals the recorded `$TMPDIR`.
   - A runtime built without it: the file's `temporary_directory` is `null`.
4. Through the console script `factory-guard --settings <file>` with a `Write` payload naming `<T>/notes.txt`: exit status 0 and nothing on standard error when the file names `<T>`, and exit status 2 with `<T>/notes.txt is outside the checkout.` when it does not (rows of one parametrized test).
5. `make check` stays green.
6. docs:
   - `docs/project-guide.md`, *Which path is judged*: the temporary-folder rule, its order after the checkout, and the unchanged verdict without it.
   - `docs/operator-guide.md`, *`factory-guard` on the agent run's `PATH`*: one sentence saying that the hook also allows an `Edit` or `Write` in the run's own temporary folder, as the kernel does.
   - `docs/decisions.md`: a new entry. It gives the reason (R14 sends the agent to `$TMPDIR`, and the cross-check of the hook against the kernel would otherwise count each such refusal as a disagreement) and the rejected alternatives: telling the agents to write temporary files through the shell only, and counting the refusals as expected in the cross-check.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/checkout" "$d/t"
printf '{"root": "%s/checkout", "write_paths": [], "protected_paths": [], "temporary_directory": "%s/t"}' "$d" "$d" > "$d/with.json"
printf '{"root": "%s/checkout", "write_paths": [], "protected_paths": []}' "$d" > "$d/without.json"
p=$(printf '{"tool_name": "Write", "tool_input": {"file_path": "%s/t/notes.txt"}}' "$d")
echo "$p" | uv run -q factory-guard --settings "$d/with.json"; echo "with: $?"
echo "$p" | uv run -q factory-guard --settings "$d/without.json" 2>/dev/null; echo "without: $?"
```
Expect: `with: 0`, then `without: 2`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: 1. The Interface for `judge` says "A real path inside the real root goes to `refusal`, as today, even when the root lies beneath the temporary folder". That is an ordering clause (checkout first, temporary folder second), and no criterion tests it. Criterion 1 has no row where `<R>` lies inside `<T>`. The link row only covers a link whose target is outside `<T>`. Two coders could read the ordering differently and both pass the tests. Options: (a) add a row to criterion 1: a checkout `<R>` placed beneath `<T>`, a write path `docs/*`, and a `Write` to `<R>/src/a.py`, which is refused with the text `refusal` gives for `src/a.py`. (b) Delete the clause from the Interface. I would choose (a).

   The other checks found nothing:
   - Format check: passed.
   - The Interface names concrete modules and signatures.
   - The other criteria each have a failing side.
   - The smoke test is runnable and its `Expect:` line is checkable.
   - The architecture fits: domain model, adapter and runtime, and no new layer or dependency.
   - The scope is inside F0019 and not in its "Out of scope". The hook stays.
4. 2026-10-18 human: (a): add the row to criterion 1 yourself. A checkout `<R>` beneath `<T>`, write paths `["docs/*"]`, and a `Write` to `<R>/src/a.py` is refused with the text `refusal` gives for `src/a.py`. The Interface clause stays.
