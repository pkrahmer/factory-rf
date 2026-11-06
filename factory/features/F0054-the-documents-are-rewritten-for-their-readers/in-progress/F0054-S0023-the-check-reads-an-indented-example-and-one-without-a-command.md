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
  started_at: '2026-11-06T22:36:34.880607Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T22:36:34.873663Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T22:36:34.880607Z'
  stage: intake
---

# The check reads an indented example and one without a command

## Description

The style page asks for tasks as numbered steps, and a step's example belongs under its step, indented like the step's text. The document check cannot read such a block today: `examples` in `factory.shared.domain.documents` keeps each line's indentation, so it finds no line that starts with `$ `, and `_commands` then raises `ValueError: zip() argument 2 is longer than argument 1`. `make documents` ends in a traceback instead of a report. The same crash comes from any `console` block that holds no `$ ` line at all, indented or not. The rewrite of `docs/operator-guide/install.md` (F0054-S0001) found the first and works around it with every block at column 0. This story makes the check read a block indented under a step as if it stood at column 0, and makes a `console` block without a command one finding instead of a crash. Everything else the check reads, runs and prints stays as it is.

## Interface

- `factory.shared.domain.documents` (domain), signatures unchanged:
  - `examples(text) -> Examples`: the lines of a fenced block lose the indentation of its opening fence (the spaces or tabs before the fence) before they are read, so a `console` block indented under a numbered step gives the same `Example` as the same block at column 0, with the same line numbers. A line of the block with less indentation than its fence keeps what it has.
  - A `console` block that holds no line starting with `$ ` gives no `Example` and no crash. It gives the finding `<document>:<line>: the example has no command`, at the line of its opening fence, through the same path as the other example findings. That path blocks in a listed file and is reported in any other.
- Tests: new rows in `tests/shared/domain/test_document_examples.py` and in the entry tests of the example check, on documents the tests write (`tests/support/minimal_documents_support.py`), never on the real documents. Adding rows to these earlier modules needs no further leave. No earlier row changes its expected result; if one would, that is a question.
- No other module changes.

## Acceptance criteria

1. A `console` block indented by three spaces under a numbered step, with `$ echo hi` and `hi`, gives one `Example` with the command `echo hi`, the expected line `hi` and the same line numbers as at column 0. Rows: three spaces, four spaces, a tab, and column 0.
2. A `console` block with no `$ ` line gives the finding `<document>:<line>: the example has no command` at its fence line, and no exception. Rows: at column 0 and indented.
3. On minimal documents, `make documents` (through `main(["--root", ...])`) runs an indented example that matches and gives no finding. It gives one blocking finding for an indented example that does not match in a listed file. Rows of one test.
4. `make check` stays green.
5. docs: `docs/project-guide/style.md`, *Runnable examples*: the reader learns that an example may stand indented under its numbered step, and that a `console` block must hold at least one `$ ` command. `docs/project-guide/shared.md`, the example check: the reader learns that the block's indentation is removed before it is read, and the new finding. `docs/decisions.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; printf '# T\n\n1. Run it:\n\n   ```console\n   $ echo hi\n   hi\n   ```\n' > "$d/t.md"; uv run python -c "import sys; from factory.shared.domain.documents import examples; e = examples(open(sys.argv[1]).read()); print(len(e.runnable), e.runnable[0].commands[0].command)" "$d/t.md"
```
Expect: `1 echo hi`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
