# A document's marked examples are run by the check

## Description

An example that shows a command and what it prints is the claim a reader trusts most, and the one easiest to check: run it. This story lets a document mark an example as runnable, like a cell of a notebook that the test runner executes instead of the reader. A fenced block with the info string `console` holds lines that start with `$ ` (the commands) and the lines below each (the expected output). The check runs the commands of each block in order, in a temporary copy of the checkout, in a stage container, and compares the output line by line. In the expected output, `...` on a line of its own stands for any lines, and a `<placeholder>` in angle brackets for any text. A block whose info string is `console vm`, `console github` or `console model` is not run; the report names it. Until S0004 a failed example is only printed.

## Interface

- `factory.shared.domain.documents`: `examples(text) -> list[Example]` (pure): each runnable block with its document, line, commands and expected output; `matches(expected, actual) -> bool` (pure), with the two placeholders.
- `factory.shared.application.document_examples`: `ExampleRunner`, an interface; `run(example, checkout) -> list[str]` gives the findings of one example.
- An adapter runs the commands through the project commands' container environment (the same container as a check), in a temporary copy of the checkout, with a time limit of 60 seconds per block.
- `make documents` runs the examples; `make check` does not.
- Tests: `tests/shared/domain/test_document_examples.py` (pure), and an adapter test with the fake containers.

## Acceptance criteria

1. `examples` finds a `console` block's commands and expected output; it leaves out other blocks and the three marked kinds, which it lists as skipped (rows per kind).
2. `matches` accepts equal lines, `...` for any number of lines and `<placeholder>` for any text in a line, and refuses a missing or an extra line (rows of one test).
3. A runnable example whose output differs gives one finding, `<document>:<line>: the example printed <first differing line>`; one that matches gives none.
4. A block that runs past 60 seconds gives the finding `<document>:<line>: the example did not end in 60 s`.
5. The commands run in a temporary copy of the checkout, never in the checkout itself, and the copy is removed afterwards.
6. `make check` stays green.
7. docs: `docs/project-guide/style.md` (from F0052) or, until it exists, `docs/project-guide/shared.md`: how to write a runnable example and how to mark one that needs the VM, GitHub or a model.

## Smoke test

```bash
uv run python -c "from factory.shared.domain.documents import examples; print(len(examples('\`\`\`console\n\$ echo hi\nhi\n\`\`\`\n')))"
```
Expect: `1`

## Journal
