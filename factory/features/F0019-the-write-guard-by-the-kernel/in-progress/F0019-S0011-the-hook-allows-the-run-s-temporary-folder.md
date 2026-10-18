---
stage: review
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
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-18T20:26:05.402243Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-18T20:26:19.826150Z'
  stage: intake
  run: 371965e7aa6640ac9de38a58038edba9
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-18T20:26:40.088547Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-18T20:29:51.896966Z'
  stage: tests
  run: 64ff27c3ae124cd0b90806c9d89e63d3
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-18T20:30:12.250594Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-18T20:32:18.568092Z'
  stage: doing
  run: b7ec67ca5d4c422fb8c3ada141c0218c
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
   - The checkout `<R>` placed beneath `<T>`, with write paths `["docs/*"]`: a `Write` to `<R>/src/a.py` is refused with the text `refusal` gives for `src/a.py`.
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
5. factory: started intake as self.
6. intake: accepted
   - Interface: `GuardSettings.temporary_directory`, `judge` and `ClaudeCodeRuntime.run` are named with modules and signatures. Every ordering and "beneath" clause is stated.
   - Criteria: each is testable by one parametrized test. Criterion 1 covers both sides of each rule: inside, missing folders, the folder itself, the `-x` sibling, the link into the checkout, `None`, and the checkout-first ordering. Criterion 2 covers a present, an absent and a relative value. Criterion 3 covers both runtime builds. Criterion 4 covers the console script's exit 0 and exit 2. I added the ordering row to criterion 1 (a checkout `<R>` beneath `<T>`, write paths `["docs/*"]`, a `Write` to `<R>/src/a.py` refused with the text `refusal` gives for `src/a.py`). It comes from journal entry 4, the human's answer (a) to my question in entry 3.
   - Smoke test: runnable with `uv run -q factory-guard --settings`. The `Expect:` line (`with: 0`, then `without: 2`) can be checked against the output.
   - Architecture: a domain model field, an adapter judge and the runtime adapter, each in its own layer. No new dependency, package or layer. The hook stays and the tool paths stay kernel-only (decision 8).
   - Scope: inside F0019 and not in its "Out of scope". Removing the hook is left out. The story makes the hook agree with the kernel for R14's temporary folder, which supports decision 16's cross-check.
7. factory: started tests as self.
8. tester: Wrote the red tests for the temporary-folder rule of the guard.

   Criterion → test:
   - criterion 1: tests/adapters/test_claude_guard_temporary.py::test_a_write_beneath_the_temporary_folder_is_allowed_after_the_checkout_rules. Seven rows: file in folder, missing folders, the folder itself, prefixed sibling `<T>-x`, link into the checkout, no temporary folder, checkout beneath the folder. The refused rows expect the text `refusal` gives for `src/a.py`.
   - criterion 2: tests/adapters/test_claude_guard_temporary.py::test_the_settings_file_reads_the_temporary_folder_back. Rows: absolute, absent (reads back as None), relative (raises GuardSettingsInvalid).
   - criterion 3: tests/adapters/test_claude_runtime_guard_temporary.py::test_the_guard_settings_file_names_the_run_s_temporary_folder_when_confined. Rows: confined, through the real factory-confine as the existing confinement tests do (the value must equal the recorded $TMPDIR), and unconfined (the value must be null). It reuses the stand-in claude from tests/adapters/claude_stand_in.py, which already records the environment and the guard settings file named in the hook settings.
   - criterion 4: tests/adapters/test_claude_guard_temporary.py::test_the_console_script_allows_a_write_in_the_temporary_folder_it_is_given. It runs the installed factory-guard beside sys.executable. Rows: with the folder (exit 0, empty stderr) and without it (exit 2, `<T>/notes.txt is outside the checkout.`). It sits in the new adapters module because the Interface names only these two new test modules.
   - criteria 5 and 6 (make check, docs): no tests.

   Files created: tests/guard_support.py (shared helpers hook_payload and outside), tests/adapters/test_claude_guard_temporary.py, tests/adapters/test_claude_runtime_guard_temporary.py.

   Earlier test files changed under the standing leave to move a shared test helper (CLAUDE.md, Tests):
   - tests/adapters/test_claude_guard.py: its _payload and _outside now come from guard_support (hook_payload, outside).
   - tests/entry/test_guard.py: its identical _payload copy now comes from guard_support.hook_payload, and its unused json import is gone.
   Every test in both files keeps its name and checks the same thing.

   Imports: no module failed to import. The modules under test exist; the new tests fail because GuardSettings has no field temporary_directory yet and the runtime does not write one into the guard settings file.

   Checks: make test was run once and is red on purpose; its last lines name the four new console-script and runtime tests. I read only those last lines, so they do not show the failure reason or the result of the two changed test files; the factory's own make test run shows both. make lint is green. The type check was skipped as this stage says.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/adapters/test_claude_runtime_guard_temporary.py::test_the_guard_settings_file_names_the_run_s_temporary_folder_when_confined[unconfined]
9. factory: started doing as self.
10. coder: Made the tester's red tests pass. `make check` is green, and no test was touched.

    What I built:
    - `src/factory/domain/agent_runs.py`: `GuardSettings` has a new field, `temporary_directory: AbsolutePath | None = None`. Because it is `AbsolutePath`, a relative value is refused just as `root` is. The docstring now names the new field.
    - `src/factory/adapters/claude_guard.py`: `judge` keeps its order.
      - A real path inside the real root still goes to `refusal`, even when the root lies beneath the temporary folder.
      - Only a path outside the checkout is then tested by `_beneath_temporary_directory`. That test compares real paths by their parts with `Path.is_relative_to`, and it does not count the folder itself as beneath itself.
      - The `realpath` call and its error handling are now in one helper, `_real_path`, which both checks share instead of each having a copy.
      - With `temporary_directory` set to `None`, the verdict is the same as before.
    - `src/factory/adapters/claude_runtime.py`: a new method, `ClaudeCodeRuntime._guard_settings`, copies the request's guard settings with `temporary_directory` set to `files.temporary` when the runtime has a `confine_executable`, and to `None` when it does not. This is the same path the confined command gets as `TMPDIR`.

    Main choice: the runtime fills in the temporary folder when it writes the settings file. The rejected alternative was having the caller who builds the `AgentRunRequest` set it. That caller does not know the folder's name, which is built from the session inside the runtime. Setting it in the runtime also means an unconfined runtime always writes `null`, whatever the request carries.

    Refactor pass: I read the diff and kept the shared `_real_path` helper. Nothing else needed changing.

    Noticed but not touched: nothing.

    The journal did not change the meaning of the task. The human's answer in entry 4 added only the checkout-first row, which intake had already written into criterion 1. The Description is unchanged.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 36 known, 3 gone
