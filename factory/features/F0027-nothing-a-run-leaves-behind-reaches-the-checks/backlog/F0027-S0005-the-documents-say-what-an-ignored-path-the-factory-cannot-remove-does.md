# The documents say what an ignored path the factory cannot remove does

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0027 made the factory remove every git-ignored path of the checkout after each agent run and at every restore. Its acceptance (F0027-A0001) found what an ignored path the factory cannot remove does in practice, and the documents do not say it. On 2026-10-20 the acceptance reviewer's own `make check`, as `agent`, left `.venv/lib/python3.12/site-packages/__pycache__/` as `drwxr-sr-x` with a `-rw-r--r--` `_virtualenv.cpython-312.pyc`. The removal after the run raised `GitError` from `run_sealed`, so the stage ended without a result. Every tick then stopped with `checkout_restore_failed`. Once the human repaired the folder (`chmod g+w`, as root), the factory recorded the stage as a crash and ran it again, and the second run hit the same folder. That was two crashes and `crash_cap` (the report's journal, entries 2 to 6, and the night log of 2026-10-20). The operator guide names `checkout_restore_failed` for such a path, but not the crash before it, not the repair, and not bytecode as the usual cause. It also says that only "a stricter umask" makes the removal fail. The human's quick fix on `main` is in the `Makefile`: `export UV_COMPILE_BYTECODE := 1` (fd0fcd0b), so uv writes `.venv`'s bytecode at its sync, group-writable. It hides the cause and does not remove it: a test child without `-B` still writes bytecode under the tests' umask `022` for a module that has none yet. S0004 removes the cause in the test helpers. The quick fix's reason is in no decision entry. Two smaller stale lines: the operator guide's bullet on `sudo`'s `umask=0002` names the restore as `git reset --hard`, `git clean -fd`, without the removal of ignored paths. And `docs/project-guide/watching.md` gives `build_boundaries(settings, token, *, hosting=None, end_leftovers=True)` without its `which` and `confine_executable` keywords. This story writes these facts. No code, test or `Makefile` changes.

## Interface

None: documents only (`docs/operator-guide.md`, `docs/project-guide/watching.md`, `docs/decisions.md`). No module under `src/factory/` and no test changes.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`:
   - *The project's make targets*, the paragraph on ignored state: a Python that writes bytecode (`__pycache__`) under a umask stricter than `002`, such as factory-rf's tests under `022`, leaves a folder the factory cannot remove. This happens when the process does without the container's `PYTHONDONTWRITEBYTECODE=1`: an emptied environment drops it, and `-I` ignores it. Use the words `a bytecode folder`. factory-rf's `Makefile` exports `UV_COMPILE_BYTECODE=1`, so uv compiles `.venv`'s bytecode at its sync, under the caller's umask.
   - The `checkout_restore_failed` row, or the paragraph under the table: when the path was left by an agent run, the stage that ran ends without a result. Once the checkout is repaired, the factory records it as a crash and runs it again, with the words `records it as a crash`. The repair is `chmod -R g+w <path>` as root on the path git's message names (as the human did on 2026-10-20), or removing it as root. A second run that leaves the same path again reaches the crash cap.
   - The bullet on `umask=0002` under *The one `sudo` rule*: the restore's commands name the removal of ignored paths (`git clean -X`) beside `git reset --hard` and `git clean -fd`.
   
   `docs/project-guide/watching.md`: the `build_boundaries` signature in *Boundaries* is the code's, `build_boundaries(settings, token, *, hosting=None, which=shutil.which, confine_executable=CONFINE_COMMAND, end_leftovers=True)`, with one sentence each on `which` (it finds the `sudo` the runtime starts) and `confine_executable` (`None` starts no wrapper).
   
   `docs/decisions.md`: the entry *The factory removes the git-ignored paths after every agent run and at the restore* gains a bullet `Seen on 2026-10-20`. It names the two crashes of F0027's acceptance from an agent-made bytecode folder, and the human's `UV_COMPILE_BYTECODE=1` in the `Makefile` (fd0fcd0b) as the human's quick fix: uv writes `.venv`'s bytecode at its sync, group-writable, so the test children find it there and write none. It says that the quick fix hides the cause and does not remove it, since a child without `-B` still writes bytecode under the tests' umask `022` for a module that has none, and that the test helpers' `-B` (S0004) removes the cause. It also says why the answer lies in how the files are written and not in a later repair: a fix of modes after every agent call was rejected (F0033's entry, *The tests set their own umask, and uv syncs under the caller's*), so what an agent's commands write must be group-writable from the start. `README.md`: none, nothing a newcomer does changes.

## Smoke test

```bash
grep -q "a bytecode folder" docs/operator-guide.md && echo found
```
Expect: `found`

```bash
grep -q "records it as a crash" docs/operator-guide.md && echo found
```
Expect: `found`

```bash
grep -c "confine_executable=CONFINE_COMMAND, end_leftovers=True)" docs/project-guide/watching.md
```
Expect: `1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
