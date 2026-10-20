# Pre-check F0027, round 2: the feature after the human's answers and the merges since round 1

Checked against:

- `feature.md` as it is now (edited 2026-10-19 23:33: decision 3 answered B, S0004 removed);
- the round-1 report `F0027-feature-1.md`;
- today's `main`, after F0023, F0028, F0029-S0001, F0031 to F0036;
- F0030 and F0039 as drafted, and the names of F0040 and F0041 (no draft of either is in the repository yet).

Findings only.

## What I ran

The runs are in the three story reports `F0027-S000N-2.md`:

- the form checks (`ok` for all three);
- the S0003 prototype: exactly decision 16's three tests fail in `tests/application`, and `tests/entry` passes;
- the smoke tests on today's code and on the prototype;
- a throwaway container in which the tests' umask makes a `python -I` child leave `755` agent folders that `git clean -X` as `factory` cannot remove, and `-I -B` leaves none.

## Findings

1. **`feature.md` still describes S0004.** Decision 3 is answered B and the S0004 file is gone. Yet these still name S0004 and its kept folders: the Goal, four lines of *Scope*, *Stories*, the intro of *The human's changes*, change 3, change 4 and decisions 13 to 17. An intake reads the feature's scope and finds a story that does not exist (edits 1 to 6).
2. **Round 1's blocker (the factory cannot remove what the agent made) is settled, but not in this feature.**
   - F0033 dropped the `Makefile`'s `umask 022`, so `uv` builds `.venv` under `sudo`'s `0002`.
   - F0033's decision log rejects "a repair of modes after every agent call", which was round 1's point 1(a), the proposed S0005. So S0005 is not drafted, and round 1's edit A is void.
   - What is left: the tests' own `umask 022` (`tests/conftest.py`) reaches every child a test starts. S0001's criterion 11 starts `python -I`, which ignores `PYTHONDONTWRITEBYTECODE`. That makes S0001's edit 4 (`-I -B`) required, and a decision 19 records it (edit 7).
3. **Round 1's edits B, C and F are still missing.**
   - B: the stages in the human's change 1.
   - C: change 4, step 2's command.
   - F: S0001's leave in decision 16.

   They are still required, with the texts of `F0027-feature-1.md`. Round 1's D and E are void with S0004.
4. **The operation count is settled.** F0023-S0001 is merged, and the Git tests are named `twenty_four` today. So S0003's operation is the twenty-fifth (edit 5).
5. **`mutants/` (F0031, F0032).**
   - `mutants/*` is no longer a tool path (`factory/pipeline.yml:18`).
   - `make mutants` removes `mutants/` first.
   - No stage runs it.

   Decision 1's list of what every role writes is stale (edit 4). The removal of `mutants/` by S0003 costs nothing.

## Clashes

- **F0030** ("a command stopped at its time limit leaves no process running"):
  - It adds `factory.domain.sessions.ProcessEntry` and a reader of `/proc/<pid>/stat` in `factory.adapters.process`. S0001 adds `factory.domain.leftovers.ProcessEntry` and a reader of `/proc/<pid>/status`. That is two models of one name and two table readers, which F0039 and the reviewer's rule on copied helpers count as a finding. See S0001's point 1.
  - The behaviour is complementary. F0030's rounds leave the agent's processes out under `sudo` (its decision 4), and S0002 ends exactly those after the call.
- **F0039-S0001** (`read_call_end`): it rewrites the lines of both runtimes' `_call` that S0002 extends. S0002's edit 7 makes S0002 hold in either order.
- **F0040** ("agent code never runs with the factory's rights"):
  - *Out of scope*'s first bullet and the decision log's entry "The project commands run as the factory's user and are left for v2" describe exactly what F0040 changes, so that bullet goes stale with F0040.
  - "A fresh home per run" empties the agent's uv cache, which decision 4 and *Out of scope*'s `~/.cache/*` bullet assume is warm. With S0003, every run then downloads every package.
  - Project commands run as `agent` need the leftovers program after them too, and an environment that keeps `PYTHONDONTWRITEBYTECODE=1` (otherwise every test child leaves `755` bytecode that S0003's removal cannot remove).
  - The human's change 1's reason "(and under `make check`, the factory)" becomes false.

  None of this blocks F0027. Each is for F0040's drafter (points 2 and 3).
- **F0041** ("the old hook guard is removed"):
  - It will edit the same `CLAUDE.md` bullet (R12) as the human's change 2. Change 2 inserts after "its tool paths and its own temporary folder;", and the clause after that semicolon is the hook's, which F0041 removes.
  - It will rewrite `docs/project-guide/write-guard.md` (*The guard command*) and its line in `docs/project-guide/README.md`, which S0001's docs criterion also extends.

  Recommended: commit change 2 before F0041's `CLAUDE.md` change, so that F0041 edits the merged text.

## Points for the human

1. **S0005: none.** F0033's decision rejects the repair of modes, and S0001's `-B` closes the one remaining child. Options:
   - (a) no S0005, and S0001's edit 4;
   - (b) S0005 anyway, for any project's stricter umask.

   Recommended: (a). A project with a stricter umask meets the stop `checkout_restore_failed` with a clear detail (S0003's optional edit 4 says so in the operator guide).
2. **The order with F0030.** Recommended: F0030 first, since it is ready, small and touches only `process.py`. S0001's Interface is then edited to extend F0030's `ProcessEntry` and reader by `uid`, before S0001 starts. The alternative is to keep two models.
3. **F0040's uv cache.** Recommended: F0040 decides a uv cache for agent runs outside the fresh home. Otherwise F0027's cost (decision 4) grows from seconds to a full download per stage. Read it at the human's change 4, step 4, whichever comes first.

## Verdict

`F0027: the feature needs edits 1 to 7 before S0001 starts; with them and the stories' required edits, all three stories are buildable in the order S0001, S0002, S0003.`

Edit 1 (required, *Goal*). Replace

```markdown
One conditional story lets a project keep ignored folders it names, which F0024's mutation report needs. 
```

with

```markdown
No ignored folder is kept: mutation testing runs only as sweeps outside the factory (decision 3, answer B). 
```

Edit 2 (required, *Scope*). Delete ` It gains `kept` in S0004.` and ` It gains `kept_ignored` in S0004.`. Replace `(S0003, and the kept folders in S0004)` with `(S0003)`. Delete the three bullets that start with `` - `src/factory/domain/pipeline_definition.py` ``, `` - `src/factory/application/stage.py` `` and `` - `src/factory/domain/contract.py` ``.

Edit 3 (required, *Stories* and *The human's changes*).

- Delete the line `- S0004: A project keeps the ignored folders it names (only on the answer A of decision 3; otherwise move it out of `backlog/` unbuilt)`.
- In the intro of *The human's changes*, delete `, and S0004's regenerated schemas are the coder's`.
- Replace change 3, from `3. Only with the answer A of decision 3,` to `stops with `pipeline_definition_invalid`.`, with

  ```markdown
  3. None: withdrawn with S0004 (decision 3, answer B). `factory/pipeline.yml` gains no `kept_ignored` key.
  ```

- In change 4, replace `after S0003 (and change 3, if any) is merged` with `after S0003 is merged`.
- Round 1's edits B (change 1) and C (change 4, step 2) apply as written in `F0027-feature-1.md`.

Edit 4 (required, decision 1). Replace

```markdown
Who can write what: every role writes the tool paths (`.venv/*`, the caches, `.reports/*`, `mutants/*`).
```

with

```markdown
Who can write what: every role writes the tool paths (`.venv/*`, the caches, `.pytest_cache/*`, `.reports/*`); `mutants/*` is no tool path any more (`factory/pipeline.yml`), so the kernel refuses an agent's write there.
```

Edit 5 (required, decision 16). Replace `- S0001 and S0002: none. Every existing runtime test` with the text of round 1's edit F (`F0027-feature-1.md`). In the S0003 bullet, replace

```markdown
Its test `test_git_has_exactly_the_twenty_three_operations_and_git_cli_has_each` is renamed with the next number: `..._twenty_four_...`, or `..._twenty_five_...` when F0023-S0001 has already renamed it to `twenty_four`. `tests/application/test_interfaces.py`: the test `test_git_abstract_methods_are_exactly_its_twenty_three_operations` is renamed the same way (it reads `OPERATIONS`).
```

with

```markdown
Its test `test_git_has_exactly_the_twenty_four_operations_and_git_cli_has_each` (named so by F0023-S0001) becomes `test_git_has_exactly_the_twenty_five_operations_and_git_cli_has_each`. `tests/application/test_interfaces.py`: the test `test_git_abstract_methods_are_exactly_its_twenty_four_operations` becomes `test_git_abstract_methods_are_exactly_its_twenty_five_operations` (it reads `OPERATIONS`).
```

Replace the bullet that starts `    - S0004: in `tests/domain/test_contract.py`` with `    - S0004: withdrawn (decision 3).`

Edit 6 (required, decisions 13, 14, 15 and 17).

- Replace `13. **`kept_ignored` keeps only a folder that git lists whole** (S0004, only on the answer A of decision 3).` with `13. **`kept_ignored` keeps only a folder that git lists whole** (withdrawn with S0004, decision 3 answered B; kept as the record, and wrong for git 2.39.5 by the pre-check of round 1).`
- Replace `14. **The records contract (S0004 only).**` with `14. **The records contract (withdrawn with S0004; F0027 changes no contract).**`
- In decision 15, replace `Both add an operation to `Git`, so the operation counts in the tests depend on which is merged first (decision 16). Both raise the records contract's minor, each by one. ` with `F0023 added its `Git` operation first, so S0003's is the twenty-fifth (decision 16). `
- In decision 17, delete ` S0004 is a field with its load rule, a listing in the git wrapper and two arguments passed on.`

Edit 7 (required, a new decision after 18):

```markdown
19. **What the factory removes stays removable** (pre-check of round 2). The removal runs as the factory's user and reaches the agent's files through the group alone, so they must be group-writable. F0033 settled it for `uv`: the `Makefile` sets no umask, and `.venv` is built under `sudo`'s `0002`; its decision log rejects a repair of modes after every agent call. The tests set their own umask `022` (`tests/conftest.py`), and every child a test starts inherits it; a `python -I` child ignores `PYTHONDONTWRITEBYTECODE` and writes `755` bytecode folders of the agent's into `src/factory`, which `git clean -X` as the factory cannot remove (seen in the pre-check: 111 refusals, exit 1). So S0001's child runs with `-I -B`, and any later test that starts an isolated Python child does the same. (S0001, S0003)
```
