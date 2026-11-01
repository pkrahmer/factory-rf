# The start script installs the credential helper and makes the runtime's runs folder
<!-- proposed by feature acceptance of 2026-11-01; refine before starting -->

## Description

`vm/job-start.sh` (S0006) ends in `exec factory-run`, but two things that `factory-run` needs are missing from the job, so the instance it starts cannot work (the feature acceptance F0047-A0001, its smoke test):

- **The credential helper.** The factory's git always takes its credential from `/usr/local/bin/git-credential-factory` (`git_environment` in `factory.entry.wiring`). `vm/setup.sh` installs that helper on a VM; the job script does not. In a job, git then answers `not found` and `could not read Username`, so no fetch of a private project and no push can authenticate.
- **The runs folder.** The agent runtimes keep a run's files in `<state>/runs`. `OpencodeRuntime` writes its configuration file there without making the folder, and an earlier test (F0020-S0004) pins that as an error. A job starts with an empty state at every start and runs opencode by default, so the preflight's `agent-run-probe` fails with `cannot write the state directory <state>/runs` at every start, and the machine stops.

This story adds both to the script within its existing steps:

- The step `code` installs the code checkout's `vm/git-credential-factory` as `<prefix>/usr/local/bin/git-credential-factory`, mode 0755, right after the checkout of `FACTORY_CODE_REF`. It is the helper of the same ref as the factory's code, and it answers only the host of `FACTORY_REPOSITORY_URL` (S0005).
- The step `directories` also makes `<FACTORY_STATE>/runs`.

Unchanged: the twelve steps, their names and their order, every message and exit status, the inputs and the derived variables, `vm/setup.sh`, and every module under `src/factory/`. Left to the human: whether the opencode runtime should make its own folder as the Claude Code runtime does; that needs a leave over F0020-S0004's test.

## Interface

No module under `src/factory/` changes. The coder changes `vm/job-start.sh`:

```sh
# step directories, beside the folders it makes today
mkdir -p "$FACTORY_WORKSPACE" "$FACTORY_SNAPSHOT_BASE" "$FACTORY_CHECKOUT" "$FACTORY_STATE" "$FACTORY_STATE/runs" || failed directories
# step code, after `git -C "$code" checkout --detach "$FACTORY_CODE_REF"`
install -m 0755 "$code/vm/git-credential-factory" "$prefix/usr/local/bin/git-credential-factory" || failed code
```

- `<FACTORY_STATE>/runs` is made in the step `directories`, whether the job gave `FACTORY_STATE` or the script derived it.
- The helper is installed only after `git checkout --detach` succeeded, and before the step `tools`. A failing `install` of the helper stops the script with `job-start: code: failed` on standard error and exit status 1, and neither `podman` nor `factory-run` is called.
- The source is `<root>/factory/vm/git-credential-factory`, the code checkout's own; no other file is installed under `<prefix>/usr/local/bin` besides `runc` and the helper.

Tests (the tester writes them): `tests/test_vm_job_start_instance.py`, through `tests/vm_support.py::run_job_start` and its stand-ins. A stand-in `install` that fails only for the helper's target may be added to `tests/vm_support.py` as a new option of `run_job_start`, every earlier caller keeping its behaviour. `tests/test_vm_job_start.py` passes unchanged.

## Acceptance criteria

1. With every input given, the steps print exactly the twelve lines of S0006 in their order, and the first call of each stand-in keeps S0006's order (`tests/test_vm_job_start.py` passes unchanged).
2. The step `code` makes one `install` call with `-m 0755`, the source `<root>/factory/vm/git-credential-factory` and the target `<prefix>/usr/local/bin/git-credential-factory`. It comes after the `git` call holding `checkout --detach` and before the first `uv` call.
3. A `FACTORY_CODE_REF` that does not exist stops the script with `job-start: code: no ref <ref> in <url>` and exit 1, with no `install` call naming the helper's target. An `install` that fails for the helper's target stops it with `job-start: code: failed` and exit 1, with no `podman` and no `factory-run` call (rows of one test).
4. After a run, `<FACTORY_STATE>/runs` is a directory, in two rows: the state the script derives (`<root>/state/runs`) and a `FACTORY_STATE` the job gives (`<given>/runs`).
5. The recorded `install` calls name exactly two targets under `<prefix>/usr/local/bin`: `runc` and `git-credential-factory`.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, *On Cloud Run*, *The steps*: step 6 names the runs folder, and step 8 names the helper's install with what it is for (the factory's git, the project's host only; see *The hosting-service token*). `docs/decisions.md`, *A bare job becomes an instance at start*: one line that the job installs the helper of its own code ref and makes the runtimes' runs folder, and why (the factory's git has no other credential; the state is new at every start). `README.md`: none, no newcomer-facing change.

## Smoke test

```bash
grep -c 'usr/local/bin/git-credential-factory' vm/job-start.sh
```
Expect: `1`

```bash
grep -c 'FACTORY_STATE/runs' vm/job-start.sh
```
Expect: `1`

```bash
uv run pytest tests/test_vm_job_start_instance.py tests/test_vm_job_start.py 2>&1 | tail -1
```
Expect: one line that holds `passed` and neither `failed` nor `error`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
