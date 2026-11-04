# The shared environment stays writable for every user of the instance

## Goal

On 2026-10-19 the instance `self` stopped with `main_branch_failing`. A commit on `main` changed only a comment in `pyproject.toml`, and the factory's own `make lint`, as the user `factory`, had `uv` reinstall the project. uv failed with "failed to remove file `.../factory-0.1.0.dist-info/INSTALLER`: Permission denied (os error 13)". That folder of the checkout's `.venv` belonged to the user `agent`, with mode `drwxr-sr-x` and files `-rw-r--r--`. It was made at 07:31, during F0020-S0005's tester run (07:27:58 to 07:34). Everything else in the venv is `factory:factory-work` and group-writable. The operator fixed it by hand with `chown factory:factory-work` and `chmod g+w`.

The cause is the `Makefile`, not `sudo` or the runtimes. The `test` recipe runs `umask 022` and then `uv run pytest`. That umask exists because the tests' own checkouts must not come out group-writable, or the seal refuses them. But `uv run` syncs the venv before it starts pytest, so a reinstall made inside `make test` is made under `022` too. An agent's `make check` or `make test`, as `agent`, then leaves agent-owned folders and files that the group cannot write. The next `uv run` as `factory` cannot remove them. The reverse fails too: the factory's own `make test` report leaves factory-owned `644` files that an agent's `uv run` cannot replace.

The rest of the chain keeps `002`, as checked on 2026-10-19 in a throwaway container of the image. `sudo -n -u agent -- timeout ... env -i ... sh -c umask` printed `0002`. A `uv sync --offline` as `agent` through that chain left the project's `dist-info` as `2775` with `664` files, and a later sync as `factory` succeeded. The instance's process has `Umask: 0002`. `factory-confine` and the runtimes set no umask, and Claude Code applies the process umask to the files it writes. The agent's roughly 600 `__pycache__` files in the venv are `664` and group-writable, so they are no fault.

The fix: the tests set their own umask, in `tests/conftest.py`, for every pytest run whatever umask it was started under. The `Makefile` then drops its `umask 022`, so `uv run` syncs under the caller's umask, which is `002` in the instance and under `sudo`. For the operator, who reads a red `main` as a fault of the code. Done when every story below is merged, the human's change 1 is on `main` and `make check` is green.

## Scope

- `tests/conftest.py`: a `pytest_configure` hook that sets the process umask to `0o022` (S0001, under decision 5).
- `tests/test_tests_umask.py` (new): the tests of that hook (S0001).
- `docs/project-guide/processes-and-checks.md`, `docs/decisions.md` and `docs/operator-playbook.md`, from the story's docs criterion (S0001).

## Out of scope

- `sudo`, the sudoers file, the entrypoint's `umask 002`, `factory-confine` and the runtimes: they already keep `002` (see *Goal*).
- Files a tool makes with a fixed mode whatever the umask, such as mypy's SQLite cache `.mypy_cache/3.12/cache.*.db` (`-rw-r--r--`, owned by `agent`). No fault seen; F0027 removes the git-ignored state after every run.
- What pytest itself writes into the checkout under the tests' umask (`.reports/.coverage`, `.reports/junit.xml`): unchanged from today.
- Repairing an instance's venv already broken this way: the operator's `chown`/`chmod g+w`, as done on 2026-10-19.
- An operator's shell opened with `docker exec -u agent` (umask `0022`): a hand action, not an agent run.
- The `mutants` recipe's own `umask 022`: F0032's change 1 rewrites that recipe (decision 3).
- Every paid call: no story and no smoke test makes one.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`. The human's change 1 comes after S0001 is merged.

- S0001: The tests set their own umask, so uv syncs the shared environment under the caller's

## The human's changes

Checked against `factory/pipeline.yml`: the tester writes `tests/*`, and the coder has nothing to write. The `Makefile` lies outside every write path.

1. After S0001 is merged, one commit on `main`. In the `Makefile`'s `test` recipe, these three lines go:

   ```make
   	# The tests' checkouts must not come out group-writable, or the seal refuses them; v1.1's
   	# container runs with umask 002 for its shared checkout, so the tests set their own.
   	umask 022
   ```

   In their place, one line:

   ```make
   	# The tests set their own umask (tests/conftest.py); uv syncs .venv under the caller's.
   ```

   Not before S0001 is merged: without the hook, `make test` in the container runs under `002`, the seal refuses the tests' checkouts, `main` turns red and the instance stops.

2. The real check, after change 1, in a throwaway container of the rebuilt image (`--network none`, as root to set up, then the two users as the factory starts them). Make a small uv project in a setgid `factory:factory-work` folder, with the image's uv cache copied into both homes, and sync it as `factory` under `umask 002`. Change a comment in its `pyproject.toml`, then run `make test` from a copy of the repository's `test` recipe as `agent`, through `sudo -n -u agent -- env -i ...`. Expected: the project's `*.dist-info` folder is `2775` and its files `664`, and a following `uv sync` as `factory` succeeds. Today the same run with the old recipe gives `755` and `644`.

## Decisions taken for the human

1. The cause is the `Makefile`'s `umask 022`, which comes before `uv run pytest`, so uv's reinstall runs under it (S0001's Description). Rejected: closing the agent's `uv` off from the venv with `UV_NO_SYNC` (an agent's `make check` after a dependency change would then test a stale venv); repairing modes after every agent call (it fixes the symptom, needs a new step as `agent`, and misses the factory's own `644` files).
2. The umask moves into `tests/conftest.py` (`pytest_configure`), not into a shell wrapper in the recipe (`uv run sh -c 'umask 022; exec pytest ...'`). This way a test module that an agent runs on its own with `uv run pytest <module>` under `002` gets the same umask as `make test`, and the `Makefile` gets simpler. The hook sets `0o022` for the whole run and restores nothing: the process ends with the run (S0001).
3. The `mutants` recipe's `umask 022` stays as F0032's change 1 writes it. Sweeps run on a fresh copy, outside the instance, so no shared venv is at stake, and F0032 owns that recipe. Since mutmut runs the copied `tests/conftest.py`, the line could go too; the human may drop it in F0032's change 1.
4. The story has no change under `src/` and the coder writes nothing. The tester's `tests/conftest.py` is the whole fix, so the doing stage only checks `make check` and hands on (S0001).
5. The leave to change `tests/conftest.py`, which earlier stories wrote, beyond the standing leave: the tester adds `TESTS_UMASK` and the `pytest_configure` hook to it, and changes nothing else in it. Every earlier test keeps its name and what it checks. Under `make test` they already ran under `0o022`, so only a module run on its own sees a different umask (S0001).
