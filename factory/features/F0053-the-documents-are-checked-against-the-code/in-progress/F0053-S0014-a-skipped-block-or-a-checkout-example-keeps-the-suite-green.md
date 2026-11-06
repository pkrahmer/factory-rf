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
  instance: vm
  stage: intake
  started_at: '2026-11-06T14:05:00.020466Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T14:05:00.013062Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T14:05:00.020466Z'
  stage: intake
---

# A skipped block or a checkout example keeps the suite green
## Description

The suite runs the examples of every document on a copy of the documents (the `documents` fixture of `tests/conftest.py`), so that a wrong example fails `make check` in any file. Two right documents fail it today as well. First, the copy holds only `README.md` and `docs/`, while the `checkout` fixture that `make documents` uses holds every tracked file. An example that reads a file of the repository, such as `$ ls operator/vm/setup.sh`, passes `make documents` but prints `ls: cannot access ...` in the suite. Second, `test_the_operator_guide_folder_is_checked_per_file` compares the whole output except the `does not exist` lines and the report heading. A block marked `vm`, `github`, `model` or `suite`, which `make documents` lists as `not run (<reason>)` and never blocks on, adds a line to that output. One `console vm` block anywhere in the documents fails five of the test's six rows. Feature decision 3 asks for exactly such blocks, and the rewrite (F0054) marks every command it cannot run, so its first story would turn `make check` red. This story makes the copy hold the repository's tracked files and makes that test leave out the `not run` lines too. A wrong runnable example still fails the suite in any document. The check itself, its output and `docs/checked-documents.txt` stay as they are.

## Interface

- `tests/conftest.py`, fixture `documents(tmp_path) -> Path`: a git repository under `tmp_path` with one commit. It holds every file that `git ls-files` lists in the repository, copied from the working tree, instead of only `README.md` and `docs/`. Files that git does not track (`.venv/`, `.reports/`, `mutants/`) are not in it. The fixture keeps its name and its docstring says what it holds.
- `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`: before it compares, the test leaves out every line that ends in `: not run (<reason>)`, as it already leaves out the `does not exist` lines and the report heading. Every row keeps its id and its expected output.
- Both are earlier tests. Feature decision 7 gives the human's leave for them: the fixture, that one test, and any other earlier test, whichever story wrote it, whose only failure is the effect this Interface describes. Every changed test keeps its name and what it checks, and the entry names each one.
- The suite stays fast: the full copy is built and committed once per test session (a session-scoped fixture), and `documents` gives each test its own cheap copy of it (`git clone --local` or a copy of that one repository), so no test copies the whole working tree again. `make test` must not grow by more than about ten seconds; the entry gives the time before and after.
- New rows go in `tests/entry/test_check_documents_operator_guide.py` (or a new module `tests/entry/test_check_documents_suite_copy.py`), and each new row changes the copy through `documents` and commits the change.
- No module under `src/factory/` changes.

## Acceptance criteria

1. In the `documents` copy, after a block is appended to `docs/project-guide/machine.md` and committed, `factory.entry.check_documents.main(["--root", <copy>])` with the `no-index` change of the earlier test prints, once the `does not exist` lines, the report heading and the `not run` lines are left out, exactly `docs/operator-guide/README.md: missing\n`, with exit status 1. This holds for the block marked `console vm`, `console github`, `console model` and for a block that runs `make test`. A `console` block with the command `$ echo one` and the expected line `two` adds the line `docs/project-guide/machine.md:<line>: the example printed one` (rows of one test).
2. In the `documents` copy, a committed `console` block in `docs/project-guide/machine.md` with `$ ls operator/vm/setup.sh` and the expected line `operator/vm/setup.sh` gives no line about `machine.md` in the output of `main`. The same block with `operator/vm/nothing.sh` gives the line `docs/project-guide/machine.md:<line>: the example printed ls: cannot access 'operator/vm/nothing.sh': No such file or directory` (rows of one test).
3. The `documents` copy holds `pyproject.toml` and `src/factory/shared/domain/documents.py`, holds no `.venv`, and `git status --porcelain` in it prints nothing.
4. Every row of `test_the_operator_guide_folder_is_checked_per_file` passes with today's documents, as before.
5. `make check` stays green.
6. docs: `docs/project-guide/style.md`, *Runnable examples*: the reader learns that the suite runs the examples on a copy of the repository's tracked files. So an example that passes `make documents` also passes the suite, and a block that is not run never fails either of them.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git clone -q . "$d/c" && cd "$d/c" && git config user.name smoke && git config user.email smoke@example.invalid && git config gc.auto 0
printf '\n```console vm\n$ systemctl is-active factory-vm\nactive\n```\n\n```console\n$ ls operator/vm/setup.sh\noperator/vm/setup.sh\n```\n' >> docs/project-guide/machine.md
git commit -qam smoke
PATH="$OLDPWD/.venv/bin:$PATH" python -m pytest -p no:cacheprovider -o addopts= tests/entry/test_check_documents_operator_guide.py 2>&1 | tail -1
```
Expect: a last line `<n> passed in <seconds>s`, with no `failed` in it.

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
