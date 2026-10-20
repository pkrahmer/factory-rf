# Pre-check F0040, round 1: the feature, agent code never runs with the factory's rights

I checked `feature.md` against its four stories, the human's answers of 2026-10-20 (F0041 "the old hook guard is removed" first; decision 1 answered A), F0041's `feature.md` and drafts, F0027's drafts and its round-2 pre-check (`F0027-feature-2.md`), F0030's draft, `CLAUDE.md`, and today's `main` (with F0020-S0016 and F0037-S0001). The stories' own findings are in `F0040-S0001-1.md` to `F0040-S0004-1.md`.

## What changes because F0041 comes first

- No F0040 story relies on anything F0041 removes or changes. I checked `claude_guard.py`, `entry/guard.py`, `GUARD_COMMAND`, the hook settings, the preflight's `factory-guard` search and `GuardSettings.temporary_directory`. No F0040 story names, calls or tests any of them. F0041's decision 11 asked F0040 to name the narrowed `agent_environment_item(environment, is_directory)`. No F0040 story calls that item, so nothing changes.
- The two features share files but no lines: `wiring.py` (F0041: imports, `machine_extras`, a comment; F0040: `build_boundaries` and new functions), `claude_runtime.py` (F0041: the run files and arguments; F0040: one constant), and the operator guide and `agents.md` (different passages).
- `CLAUDE.md`'s R12 bullet. After F0041's human's change 2, the clause after "its own temporary folder;" is "the undo after the run reverts whatever else changed outside the write paths, and no hook judges a tool call." F0040's change 2 still inserts after "its own temporary folder;", and the result reads well. Edit 2 gives the whole sentence and replaces the clash paragraph, now that the order is decided.
- F0041's operator check (no `hook error: [factory-guard` in the transcripts after a run) must be done before S0004 is merged. After S0004 the checks that follow a forward-moving run reset the home within seconds.

## Leaves

Decision 14 grants none, but two earlier structural tests pin exactly what S0003 and S0004 add (both seen red on a prototype):

- `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`: `{"factory.entry.wiring", "factory.entry.confine"}`. `factory.entry.fresh_home` imports `factory.adapters.home_files`.
- `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: five modules. `factory.adapters.agent_home` imports `factory.adapters.process`.

S0001 and S0002 need no leave (checked: no earlier test builds the boundaries with an agent user and then runs a project command or an agent run through them).

## Points for the human

1. **The two leaves** (edit 1). Options:
   - A: grant both, one line each.
   - B: no leaves; the program imports its adapter through the wiring (about 0.6 s more per reset), and the reset is copied into both runtime modules.

   Recommended: A.
2. **Decision 8** (a fresh home by clearing, the reset in `run_sealed`). It is still open; only decision 1 was answered. Recommended: A, as drafted. The prototype cleared a real home of the image in 0.1 s, kept the factory's files and the kept paths, and `python -I` as `agent` imports the installed `factory`.
3. **Decision 9 and F0027's uv cache** (F0027 round 2, point 3). The drafter chose to drop the caches, `~/.cache/uv` included. A cache outside the fresh home that runs share must be writable by `agent`: uv refuses one it cannot write (`failed to open file .../CACHEDIR.TAG: Permission denied`, tried as `agent`). So a shared cache is a channel from one run to the next check. With F0027-S0003 (`.venv` removed after every run), each stage then downloads every package two or three times (the run's first `uv run`, then each check). Options:
   - A: as drafted; measure after F0027.
   - B: keep `.cache/uv` as a kept folder, accepting that channel.

   Recommended: A, and record in F0027 that its decision 4 (a warm cache) no longer holds.
4. **F0027 and F0030 drafts** (the human's change 4, unchanged by this pre-check). With F0040 first, F0027-S0002's leftovers program after every project command must be built against F0040's `SealedProjectCommands`. F0027's out-of-scope line on `~/.cache/*` and its change 1's reason ("under `make check`, the factory") are stale. The re-check of F0027 should take these in.

## Verdict

`F0040: the feature needs edit 1 (the leaves, with the human's word), edit 2 (the R12 sentence after F0041) and edit 3 (where the transcript stays) before S0003 starts; edit 4 is optional.`

Edit 1 (required, *Decisions taken for the human*). Replace

```
14. **No leave to change a test another story wrote.** Every story adds new test modules; `tests/adapters/test_make_commands.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_interfaces.py`, `tests/test_compose.py` and the settings tests stay unchanged and green.
```

with

```
14. **Two leaves, one line each, and no other change to a test another story wrote** (the human, 2026-10-20). S0003: `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` expects `{"factory.entry.wiring", "factory.entry.confine", "factory.entry.fresh_home"}`: the program runs as the agent's user and imports its adapter directly, as `factory.entry.confine` does, instead of loading the whole wiring before every reset. S0004: `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module` expects `factory.adapters.agent_home` too: `SudoAgentHome` starts the program through the process module, as the runtimes start theirs. Every other test module is new; `tests/adapters/test_make_commands.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_interfaces.py`, `tests/test_compose.py` and the settings tests stay unchanged and green.
```

Edit 2 (required, *The human's changes*). Replace

```
2. After S0004 is merged, one commit on `main`. In `CLAUDE.md`, *Architecture*, the bullet on the agent runtime (R12): after the sentence that ends "its tool paths and its own temporary folder;", insert:
```

with

```
2. After S0004 is merged, one commit on `main`, on the bullet as F0041's human's change 2 left it. In `CLAUDE.md`, *Architecture*, the bullet on the agent runtime (R12): after "its tool paths and its own temporary folder;" and before "the undo after the run reverts whatever else changed outside the write paths, and no hook judges a tool call.", insert:
```

and replace

```
   - **F0041** (*The old hook guard is removed*, being drafted). Both touch `src/factory/entry/wiring.py`, the runtime modules (S0004 adds one constant to each) and the operator guide's *The agent runs as a second user*; `CLAUDE.md`'s R12 bullet is changed by both (the human's change 2 here). No story depends on the other. Build them one after the other, not interleaved; if F0041 lands first, the human's change 2 inserts its sentence into F0041's version of the bullet.
```

with

```
   - **F0041** (*The old hook guard is removed*), built first (the human, 2026-10-20). No F0040 story relies on what it removes. Both touch `src/factory/entry/wiring.py`, `claude_runtime.py` (S0004 adds one constant) and the operator guide, in other lines and passages. `CLAUDE.md`'s R12 bullet then reads, after both human's changes: "Every agent run starts through `factory-confine`, which restricts the run's writes with Landlock to its write paths, its tool paths and its own temporary folder; every project command runs as the agent's user too (`sudo`, the agent's own `timeout`, `env -i`), with the checkout's git folder sealed, and every agent run and every project command starts from a fresh agent home (`factory.entry.fresh_home`, as that user), so no code an agent wrote runs as the factory's user and no run reads or inherits what an earlier one left in the home; the undo after the run reverts whatever else changed outside the write paths, and no hook judges a tool call." F0041's operator check on the transcripts is done before S0004 is merged.
```

Edit 3 (required, *Out of scope*, decision 10 and the operator's check 3.3). Replace

```
- Keeping the transcripts somewhere else for the operator: the last run's transcript stays until the next run starts (decision 10).
```

with

```
- Keeping the transcripts somewhere else for the operator: the last run's transcript stays until the next agent run or project command starts (decision 10).
```

and replace

```
10. **The reset comes before a run, not after** (S0004). It suffices for the rule (no run starts with what an earlier one left), and the last run's transcript stays for the operator to read after a failure until the next run starts. The first reset after the upgrade removes what the volume gathered (222 MB on `self`).
```

with

```
10. **The reset comes before a run and before each project command, not after** (S0004). It suffices for the rule (no run or check starts with what an earlier run left). The transcript of a run that asks, stalls or fails stays for the operator to read until the next run starts. The transcript of a run that moves the work item forward goes with the stage's first check right after it, unless that check's result is reused. The first reset after the upgrade removes what the volume gathered (222 MB on `self`).
```

and replace

```
   3. After a run: `docker exec -u agent factory-self-factory-1 ls -A /home/agent/.claude` lists the factory's `agents`, `commands`, `skills`, `settings.json` and only what that one run made; no `CLAUDE.md`; `du -sh /home/agent/.claude` is a few megabytes, not 222 MB.
```

with

```
   3. After a run that ended with a question (no check follows it): `docker exec -u agent factory-self-factory-1 ls -A /home/agent/.claude` lists the factory's `agents`, `commands`, `skills`, `settings.json` and only what that one run made; after a forward move and its checks, only the factory's files and a kept login; no `CLAUDE.md` either way; `du -sh /home/agent/.claude` is a few megabytes, not 222 MB.
```

Edit 4 (optional, decision 9). Replace

```
Options: A, this (recommended); B, keep `~/.cache/uv` too, as a kept folder, if the operator's measurement after F0027 shows checks too slow.
```

with

```
F0027's round-2 pre-check (point 3) asked for a uv cache outside the fresh home. uv refuses a cache it cannot write (`failed to open file .../CACHEDIR.TAG: Permission denied`, as `agent`), so any cache the runs share is writable by every run and reaches the next check. Options: A, this (recommended); B, keep `~/.cache/uv` too, as a kept folder, if the operator's measurement after F0027 shows checks too slow, accepting that channel.
```
