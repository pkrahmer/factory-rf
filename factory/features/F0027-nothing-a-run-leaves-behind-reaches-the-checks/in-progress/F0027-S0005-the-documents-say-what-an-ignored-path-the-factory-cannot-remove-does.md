---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 359
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-20T19:28:05.653811Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T19:22:12.819821Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T19:22:12.826808Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T19:22:45.277299Z'
  stage: intake
  run: f668b26a4b434b01a304b0dcb5019f2d
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T19:23:07.138994Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T19:25:45.153723Z'
  stage: tests
  run: 0446e2f5433f418b8e017213cc9a4b04
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T19:26:07.043117Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T19:27:44.959372Z'
  stage: doing
  run: 143d6c883881486fb2bb669f99e2bb41
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T19:28:05.653811Z'
  stage: review
---

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
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None: documents only" names the three files (`docs/operator-guide.md`, `docs/project-guide/watching.md`, `docs/decisions.md`). That fits a documents-only story. No signature is stated apart from the `build_boundaries` one in the docs criterion, which I compared with `src/factory/entry/wiring.py:236`. The code has `(settings, token, *, hosting=None, which=shutil.which, confine_executable=CONFINE_COMMAND, end_leftovers=True)`, so the criterion's text is the code's.
   - Criteria: criterion 1 (nothing under `src/` or `tests/` changes) and criterion 2 (`make check` green) are checkable. Criterion 3 lists the exact texts to add, and each bullet names a phrase or a signature that can be searched for. The phrases are `a bytecode folder`, `records it as a crash`, `chmod -R g+w`, `git clean -X` and the `Seen on 2026-10-20` bullet. The Interface states no behaviour and no rule, so there is no failing side to cover.
   - Smoke test: three `grep` commands, each runnable from the repository root with a checkable `Expect:` line (`found`, `found`, `1`). None runs pytest.
   - Architecture: nothing in `src/` changes. The documents are in the documenter's write paths (`docs/*`), and `README.md` is correctly left out. The sections the docs criterion names exist: *The project's make targets* (`docs/operator-guide.md:74`), *Boundaries* (`docs/project-guide/watching.md:260`) and the decision entry *The factory removes the git-ignored paths after every agent run and at the restore* (`docs/decisions.md:934`). The `umask=0002` bullet and the `checkout_restore_failed` row (line 858) are also in the operator guide.
   - Scope: the story is within F0027's scope, since the feature lists `docs/operator-guide.md`, `docs/project-guide/` and `docs/decisions.md` as documentation. The story is proposed by F0027-A0001 (the feature's acceptance), and none of it is in the feature's "Out of scope". The S0004 and S0005 references to the Makefile quick fix match the feature's change 5.
4. factory: started tests as self.
5. tester: This story only changes documents, and its Interface says "None: documents only". So I wrote no tests and changed nothing under `src/` or `tests/`.

   - criterion 1 (nothing under `src/` or `tests/` changes): no test function. It is kept by this stage and the coder's adding nothing there. I changed nothing under `src/` or `tests/` and created no files.
   - criterion 2 (`make check` stays green): no test function. The factory runs `make check` after the coder.
   - criterion 3 (the docs): no test function. It is the documenter's work, and the story's smoke test checks it with three `grep` commands (`a bytecode folder`, `records it as a crash`, the `build_boundaries` signature in `docs/project-guide/watching.md`). I did not repeat those checks in pytest, because the criteria say no test changes.

   Files created: none. Modules the test run could not import: none. `make test` ran once and is green (`test: green`, coverage 99.17 %). There are no red tests, because nothing is left for the coder to implement in code. `make lint` is green.

   I did not have to interpret any criterion, so nothing is left open.

   `lint`: lint: green (0.8 s)
   `test`: test: green (70.4 s)
6. factory: started doing as self.
7. coder: This story changes only documents, so I built nothing. Nothing under `src/` or `tests/` changes, and I created no files; the working tree holds only the factory's `.costs.jsonl` sidecar.

   - **What I built:** nothing. The tester wrote no tests, the Interface is "None: documents only", and nothing in the work item needs code.
   - **Main choice:** I left all three documents to the documenter: `docs/operator-guide.md`, `docs/project-guide/watching.md` and `docs/decisions.md`. `CLAUDE.md` says the documenter keeps these true from each story's docs criterion and the coder does not write them.
   - **Rejected:** writing the docs criterion's texts myself in this stage. That would be the documenter's work and outside the coder's part.
   - **Refactor:** there is no diff to read, so nothing needed changing.
   - **Description:** no journal entry changed the meaning of the task, so I did not rewrite it.
   - **Noticed but not touched:** the docs criterion's `build_boundaries` signature matches `src/factory/entry/wiring.py`, as the intake entry checked. The documenter can copy it as it stands.

   `make check`: check: green (test: green (70.9 s), coverage 99.17 %).

   `check`: check: green (not run again: passed on tree 416ad76bbc59 at 2026-10-20T19:16:27Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
