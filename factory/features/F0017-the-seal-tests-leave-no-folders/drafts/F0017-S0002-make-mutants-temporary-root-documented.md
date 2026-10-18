# The documents explain why make mutants runs under a temporary root of its own

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0017's feature acceptance read `README.md` and `docs/` against the whole feature. S0001 documented its own part: the fixture `reopened_tmp_path`, which reopens a test's `tmp_path` so that pytest can remove the `garbage-*` folders a mutant of the seal leaves. The feature's second half is the human's change 1 to the `Makefile` (FEATURE decision 7). It reached `main` outside the pipeline, so no stage documented it. The `mutants:` recipe:
- makes a folder with `mktemp -d`,
- runs `mutmut run` with `TMPDIR` set to that folder,
- and, in an `EXIT` trap, opens the folder (`chmod -R u+rwX`) and removes it (`rm -rf`).

The trap runs whether mutmut finished, was stopped at `MUTANTS_SECONDS` or failed. The reason: mutmut stops a mutant's pytest at its time limit (a `timeout` result), and a stopped pytest never removes its numbered folder's `.lock` file. pytest leaves a locked folder alone for three days, so `/tmp/pytest-of-<user>` filled up (58 such folders, 2.4 GB, on 2026-10-18). Today only the `Makefile`'s comment says any of this. The decision-log entry *The tests reopen their tmp_path after every test* names only the `garbage-*` cause, so a reader can think the fixture covers both kinds of leftover folder.

This story is documentation only: the tester writes no tests and the coder has nothing to build; the documenter writes it from the docs criterion. The human may prefer to make the edit by hand.

## Interface

None: no code changes. Files: `docs/project-guide.md` (section *Mutation testing*) and `docs/decisions.md` (a new entry, and one sentence in *The tests reopen their tmp_path after every test*). `README.md` and `docs/operator-guide.md` are read for consistency and changed only where they contradict the new text.

## Acceptance criteria

1. `make check` stays green.
2. docs: this story is the documentation. Afterwards:
   - `docs/project-guide.md`'s *Mutation testing* section has a paragraph after the one that begins "`make mutants FEATURE=<id>`". It says that the recipe runs mutmut with `TMPDIR` set to a folder of its own made by `mktemp -d`, and that the recipe's `EXIT` trap opens that folder for its owner and removes it when the recipe ends. The trap runs also after `mutants: stopped after …` and after a failed run. So every pytest that mutmut starts keeps its base folders there, and a run leaves `/tmp/pytest-of-<user>` as it found it. It points to the decision log entry below by its title.
   - `docs/decisions.md` has a new entry at its end, *make mutants runs under a temporary root of its own*, dated 2026-10-18 (F0017, the human's change 1; F0017 decision 7). It holds:
     - the cause: mutmut stops a mutant's pytest at its time limit, a stopped process runs no teardown and leaves its numbered folder's `.lock`, and pytest removes a locked folder only when the lock is older than three days; on 2026-10-18 v1's container held 58 such folders, 2.4 GB;
     - the decision: the `TMPDIR` set by `mktemp -d` and the `EXIT` trap, as above;
     - the rejected ways, each with its reason as FEATURE decision 7 gives it: `-o tmp_path_retention_policy=none` in mutmut's pytest arguments (each run's cleanup removes the numbered folders of the other workers still running); `--basetemp` (each run removes the given folder at its start, so parallel workers remove each other's); a sweep of `/tmp/pytest-of-<user>` at the start of a session (it works outside `tmp_path` and cannot tell a stopped run's locked folder from a running session's); `PYTEST_DEBUG_TEMPROOT` (pytest's debug variable, not a documented setting; `TMPDIR` is what `tempfile.gettempdir()` reads).
   - The entry *The tests reopen their tmp_path after every test* gains one sentence. It says that the fixture cannot reach the `pytest-*` folders that a stopped run leaves locked, because a stopped process runs no teardown, and that those are handled by the entry above, named by its title.
   - No other text in `README.md` or `docs/` describes `make mutants` in a way that contradicts the new paragraph.

## Demo

```bash
grep -n "TMPDIR\|mktemp" docs/project-guide.md
```
Expect: at least one line, in the *Mutation testing* section, names both `TMPDIR` and `mktemp -d`, or the two names appear in adjacent lines of the same paragraph.

```bash
grep -n "^## make mutants runs under a temporary root of its own\|PYTEST_DEBUG_TEMPROOT\|--basetemp" docs/decisions.md
```
Expect: the heading line, and at least one line naming `PYTEST_DEBUG_TEMPROOT` and one naming `--basetemp` (they may be the same line).

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-18 human: created.
