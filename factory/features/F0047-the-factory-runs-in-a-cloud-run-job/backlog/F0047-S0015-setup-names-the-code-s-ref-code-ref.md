# Setup names the code's ref --code-ref

## Description

F0047's decision 16 gave the repository split the names `--code-url` and `--code-ref`. S0005 built `--code-url`, but `vm/setup.sh` still takes the code's ref as `--ref`, while the job's start script calls it `FACTORY_CODE_REF`. One idea has two names. This story renames the option to `--code-ref` (the human, 2026-11-01). The old name is refused with a hint, so that an old command line says at once what changed: `setup.sh: --ref is now --code-ref`, exit status 2, before anything runs. Unchanged: the default (`main`), what the ref does (the clone of the factory's code at that ref, with `--code-url` or without it), every other option and step.

## Interface

`vm/setup.sh` (shell): the option `--code-ref <git ref>` (default `main`) takes the place of `--ref` in the parsing, the usage text and the option table of the operator guide; the variable it sets is the same. `--ref` with or without a value prints `setup.sh: --ref is now --code-ref` and the usage on standard error and exits 2, before any step runs (through the script's `fault`).

Tests (the tester writes them): `tests/test_vm_setup_code_ref.py`. The leave over earlier tests (the human, 2026-11-01): `tests/test_vm_setup.py` uses `--code-ref` where it used `--ref` (lines 16 and 80 today), every test keeping its name and what it checks; no other earlier test changes.

## Acceptance criteria

1. `setup.sh --code-ref v9` clones the factory's code with `--branch v9`, rows of one test: without `--code-url` (with the askpass, as today) and with a different `--code-url` (without a credential, as S0005 built).
2. Without `--code-ref` the clone uses `--branch main`.
3. `setup.sh ... --ref v9` prints `setup.sh: --ref is now --code-ref` on standard error, exits 2, and calls no stand-in.
4. `setup.sh --help` and the usage text name `--code-ref` and not `--ref`.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`: every `--ref` of the script becomes `--code-ref` (the option table, the steps, *The rebuild after a merge*, *The code and the project apart*, the GCP steps), with one sentence that the old name is refused. `docs/decisions.md`, *The code and the project apart*: one line that the option is `--code-ref`, from the feature's decision 16. `README.md`: only if it names `--ref`.

## Smoke test

```bash
sh vm/setup.sh --ref v9; echo "exit $?"
```
Expect: the first line is `setup.sh: --ref is now --code-ref`, and the last line is `exit 2`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
