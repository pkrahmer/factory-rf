# Pre-check F0041 feature.md, round 1: the old hook guard is removed

The edits that `feature.md` needs after the pre-check of its three stories (`F0041-S0001-1.md`, `F0041-S0002-1.md`, `F0041-S0003-1.md`). I checked the human's changes 1 to 3 against today's `pyproject.toml` (lines 17 and 128 hold exactly the two lines change 1 deletes) and `CLAUDE.md` (the R12 bullet holds exactly the clause change 2 replaces). Change 1's reason and order also hold: after S0002 the preflight no longer searches for `factory-guard`, and nothing in `make check` reads either line. Both were confirmed on a prototype of S0001 and S0002, whose whole suite was green apart from the 17 failures that come from the container.

## Edits

Edit 1 (required, decision 9; it needs the human's word, since the leave was granted "as listed"). The prototype of S0001 fails two earlier tests that decision 9 does not name. Both count the stand-in's files as three:

```
tests/adapters/test_claude_runtime_login.py:234: in test_the_login_stands_in_no_argument_no_run_file_and_no_result
E   AssertionError: assert 1 == 3
tests/adapters/test_claude_runtime_resume.py:178: in test_resumed_call_sees_the_same_run_files_and_none_is_left
E   AssertionError: assert 1 == 3
```

Replace

```markdown
   - `tests/adapters/test_claude_runtime_resume.py`: `RUN_FILES` keeps only `"instructions-*.md"`.
```

with

```markdown
   - `tests/adapters/test_claude_runtime_resume.py`: `RUN_FILES` keeps only `"instructions-*.md"`; `test_resumed_call_sees_the_same_run_files_and_none_is_left` expects `len(first.files) == 1`.
   - `tests/adapters/test_claude_runtime_login.py`: `test_the_login_stands_in_no_argument_no_run_file_and_no_result` expects `len(claude_call.files) == 1`.
```

Edit 2 (optional, decision 10): `Path` is the third import that only `_payload` uses. Replace

```markdown
   - `tests/application/test_undo.py`: `test_the_guard_refuses_exactly_what_the_undo_puts_back` as decision 8; its helper `_payload` and the imports only it used (`judge`, `json` if unused) go.
```

with

```markdown
   - `tests/application/test_undo.py`: `test_the_guard_refuses_exactly_what_the_undo_puts_back` as decision 8; its helper `_payload` and the imports only it used (`judge`, `json` and `Path`) go.
```

Edit 3 (optional, decision 11, the F0040 bullet): F0040's drafts as they stand name neither `agent_environment_item` nor `production_environment`, and the human's answer settles the order. Replace

```markdown
   - F0040 "agent code never runs with the factory's rights" (drafted at the same time): it changes the agent's home and the agent run's environment, so it is likely to touch `agent_environment_item`'s `HOME` check, `production_environment` and `agent_run_environment` in `factory.entry.wiring`. Recommended: F0041-S0002 first, and F0040's stories name the narrowed `agent_environment_item(environment, is_directory)`.
```

with

```markdown
   - F0040 "agent code never runs with the factory's rights" (drafted at the same time): its drafts change `factory.entry.wiring` (the project commands and the agent's home), add `LOGIN_STATE_FILE` to both runtime modules and rewrite other paragraphs of the operator guide's *The agent runs as a second user*; none names `agent_environment_item` or `production_environment`. F0041 goes first (the human's answer); a later F0040 story that touches the item names the narrowed `agent_environment_item(environment, is_directory)`.
```
