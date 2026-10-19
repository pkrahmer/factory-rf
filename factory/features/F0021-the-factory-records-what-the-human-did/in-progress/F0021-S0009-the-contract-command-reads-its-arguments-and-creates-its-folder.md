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
  instance: self
  stage: intake
  started_at: '2026-10-19T01:24:43.429631Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T01:24:43.423550Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T01:24:43.429631Z'
  stage: intake
---

# The contract command reads its arguments and creates its folder

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0021's acceptance ran `make mutants` over the feature's modules. Two behaviours of `factory.entry.contract`, the command that regenerates the records contract, survived their mutants, because no test reaches them. First, the command as `python -m factory.entry.contract` runs it: `main()` without `argv` reads the arguments from `sys.argv[1:]`, and the tests always pass `argv`, so reading `sys.argv[2:]`, or ignoring `sys.argv` altogether, goes unnoticed. Second, `write_contract` creates a folder whose parent is missing (`mkdir(parents=True)`), and no test writes into such a folder. This story pins both, for the coder of a later story who regenerates the schemas and for a reader who writes them into a folder of their own. The code is expected to pass as it is. No behaviour changes, and the schemas, their version and the other criteria of the contract stay as they are.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of `factory.entry.contract` (`entry`):

```python
def write_contract(folder: Path) -> list[Path]: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

- `main()` called without `argv` takes its arguments from `sys.argv[1:]`. One argument is the folder, none means `CONTRACT_FOLDER`, and two or more print the usage line to standard error and return 2.
- `write_contract(folder)` creates `folder` together with every missing parent folder.

Test module (new): `tests/entry/test_contract_arguments.py`. Its tests set `sys.argv` with `monkeypatch.setattr` and patch `CONTRACT_FOLDER` into `tmp_path` in every row, as `tests/entry/test_contract.py` does, so no row writes into the real folder. No earlier test changes.

## Acceptance criteria

1. `main()` without `argv`, with `sys.argv` set as follows (rows of one parametrized test):
   - `["contract", "<tmp_path>/given"]`: returns 0, prints `contract: 5 schemas written`, and writes the five schemas into `<tmp_path>/given`; the patched `CONTRACT_FOLDER` stays empty;
   - `["contract"]`: returns 0 and writes the five schemas into the patched `CONTRACT_FOLDER`;
   - `["contract", "a", "b"]`: returns 2, prints `usage: python -m factory.entry.contract [<folder>]` to standard error, and writes nothing.
2. `write_contract(<tmp_path>/a/b)`, where neither `a` nor `b` exists, returns the five paths under `<tmp_path>/a/b` in `CONTRACT` order, and each file exists. With `a` existing and `b` missing, the result is the same (rows of one parametrized test).
3. `make check` stays green.
4. docs: none. The operator guide's "The records contract" already says `uv run python -m factory.entry.contract [<folder>]` and what it prints, and this story changes no behaviour.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python -m factory.entry.contract "$d/a/b" && ls "$d/a/b" | wc -l
```

Expect: two lines, `contract: 5 schemas written` and `5`.

```bash
uv run -q python -m factory.entry.contract one two; echo "status $?"
```

Expect: `usage: python -m factory.entry.contract [<folder>]` on standard error, then `status 2`.

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
