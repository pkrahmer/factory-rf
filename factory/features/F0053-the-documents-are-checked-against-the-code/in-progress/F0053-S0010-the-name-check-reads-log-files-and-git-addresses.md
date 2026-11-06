# The name check reads log files and git addresses
## Description

The name check's report on today's documents still holds texts that are no repository name, and the rewrite cannot put a page on the checked list while they remain. S0004 taught the check that `factory.env` is a file name. It did not cover the other file names the operator guide writes, `factory.log` (`docs/operator-guide/machine.md`) and the state's `.jsonl` records. A scp-style git address, `git@github.com:owner/project.git` (`docs/operator-guide/install.md`, `docs/operator-guide/cloud-run.md`), is read as a repository path. The feature acceptance listed `docs/operator-guide/install.md` in a copy, and the address blocked it. This story widens the file-name rule by two extensions and reads a text with a `:` before its first `/` as no path. Every other rule of S0001 and S0004 stays. Placeholders (`<state>/records/disk.jsonl`) stay the writer's way to name a path outside the repository.

## Interface

- `factory.shared.domain.documents`: `_FILE_NAME_EXTENSIONS` gains `.log` and `.jsonl`, so that `factory.log` and `factory.records.jsonl` are file names and no module.
- `named_references`: a backticked text whose first `:` comes before its first `/` (`git@github.com:owner/project.git`, `host:path/x.md`) is no path reference. A pytest node id (`tests/a/test_b.py::test_c`) keeps its first `/` before `::`, and is checked as S0004 says.
- Tests: rows in `tests/shared/domain/test_document_references.py`.

## Acceptance criteria

1. `factory.log` and `factory.x.jsonl` in backticks give no reference, and `factory.shared.domain.nothing_here` still gives a module reference (rows of the criterion 1 test of the name check).
2. `git@github.com:owner/project.git` and `git@host:owner/name.git` give no reference. `tests/x.py::test_y` still gives the path reference `tests/x.py`, and `docs/a:b.md` (a `:` after the first `/`) is still a path (rows of one test).
3. On today's documents, `make documents` prints no finding for `factory.log` (`docs/operator-guide/machine.md`) and none for the two git addresses (`docs/operator-guide/install.md`, `docs/operator-guide/cloud-run.md`).
4. `make check` stays green.
5. docs: `docs/project-guide/shared.md`, *The name check*: the reader learns which file names and addresses the check leaves out. `docs/project-guide/style.md`, rule 8: none.

## Smoke test

```bash
uv run python -m factory.entry.check_documents | grep -c "git@\|factory.log does not exist"
```
Expect: `0`

## Journal
