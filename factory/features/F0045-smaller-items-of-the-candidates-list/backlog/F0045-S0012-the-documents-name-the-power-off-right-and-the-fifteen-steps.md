# The documents name the power-off right and the fifteen steps

<!-- proposed by feature acceptance of 2026-10-27; refine before starting -->

## Description

F0045's acceptance read the documents as a whole after S0009 (the setup script gives the power-off right only with the idle shutdown) and found three passages that the feature's stories left behind, each a sentence that is now incomplete or wrong. `docs/operator-guide.md`, `## The machine`, says that `factory` "has no `sudo` right but the page-cache helper and the four `zfs` commands of the optional `--sudoers` fallback": since S0009, a run with `--idle-shutdown` also gives it `/usr/bin/systemctl poweroff` (S0008's documenter named the sentence as S0009's to fix; S0009's did not). The table of the environment file's variables under *The script* lists every line `vm/setup.sh` writes but `FACTORY_IDLE_SHUTDOWN_MINUTES`, which step `environment` writes with the option. And `docs/project-guide/README.md`, *Shared test helpers*, says `tests/vm_support.py` holds "the thirteen step names (`STEPS`)", which are fifteen since S0002 (`caches`) and S0009 (`poweroff`). This story repairs the three passages and nothing else; the documenter writes it.

## Interface

None: no module under `src/factory/`, no test, no file under `vm/`, `template/` or `claude/` changes. The documenter changes `docs/operator-guide.md` and `docs/project-guide/README.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/operator-guide.md`, `## The machine`, the paragraph that begins "There is one user, `factory`": its second sentence becomes "`factory` has no `sudo` right but the page-cache helper, the four `zfs` commands of the optional `--sudoers` fallback and, with the option `--idle-shutdown`, `/usr/bin/systemctl poweroff` (see *The script*)."
   - `docs/operator-guide.md`, the table after "The environment file holds these variables": one row after `XDG_RUNTIME_DIR`, `` | `FACTORY_IDLE_SHUTDOWN_MINUTES` | `--idle-shutdown`, only when it is given | ``.
   - `docs/project-guide/README.md`, *Shared test helpers*, the line of `vm_support.py`: "the fifteen step names (`STEPS`)" instead of "the thirteen step names (`STEPS`)".
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'with the option `--idle-shutdown`, `/usr/bin/systemctl poweroff` (see \*The script\*)' docs/operator-guide.md
grep -c '^| `FACTORY_IDLE_SHUTDOWN_MINUTES` | `--idle-shutdown`, only when it is given |$' docs/operator-guide.md
```
Expect: two lines: `1`; `1`

```bash
grep -c 'the thirteen step names' docs/project-guide/README.md; grep -c 'the fifteen step names (`STEPS`)' docs/project-guide/README.md
```
Expect: two lines: `0`; `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
