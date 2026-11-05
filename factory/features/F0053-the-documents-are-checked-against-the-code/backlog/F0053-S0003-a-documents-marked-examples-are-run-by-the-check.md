# A document's marked examples are run by the check

## Description

An example that shows a command and what it prints is the claim a reader trusts most, and the one easiest to check: run it. This story lets a document mark an example as runnable, like a notebook whose cells the test runner executes instead of the reader. A fenced block with the info string `console` holds lines that start with `$ ` (the commands) and the lines below each (the expected output). Its info string may name a fixture, `console fixture=<name>`; this story gives the one fixture `checkout` (a copy of the repository at the checked commit, and the default) and S0006 adds the others. The blocks of one document run in order and share their fixture, like the cells of a notebook: each document starts fresh, and a block sees what the blocks above it did (the human, 2026-11-05). The commands run in a fixed environment, and the expected output may hold `...` on a line of its own for any lines and `<placeholder>` for any text within a line, for what varies, such as times, ids and temporary paths. A block marked `console vm`, `console github` or `console model` is not run; the report names it, and the acceptance reviewer runs the `vm` ones (S0005). Until S0004, a failed example is only printed.

## Interface

- `factory.shared.domain.documents` (pure):
  - `examples(text) -> list[Example]`: the runnable blocks of one document in order, each with its line, fixture name, commands and expected output, and the marked blocks it skips, with their kind.
  - `matches(expected, actual) -> bool`, with the two placeholders.
- `factory.shared.application.document_examples`:
  - `Fixture`, an interface: `prepare(folder) -> dict[str, str]` builds the starting point in an empty folder and gives the extra environment the commands get.
  - `ExampleRunner`, an interface: `run_document(document, examples, fixtures) -> list[str]` gives the findings of one document.
  - The fixture `checkout`: a copy of the repository's tracked files at the checked commit, as a git checkout.
- An adapter runs a document's commands through the project commands' container environment (the container a check runs in), in a temporary folder that the fixture prepared, with `env -i` and `TZ=UTC`, `LANG=C.UTF-8`, `HOME` a temporary folder, `PATH` the container's; each command has a time limit of 60 seconds. The folder is removed afterwards.
- `make documents` runs the examples; `make check` does not. It ends with `documents: green (<seconds> s)` like the other targets, so that its time shows in every docs stage's output.
- A command that runs the test suite or `make check` (`make check`, `make test`, `pytest` over the suite) is never a runnable example: the document marks it `console vm`, and the acceptance reviewer runs it once per feature. `examples` reports such a command in a runnable block as a finding (the human, 2026-11-05: the examples must not make the docs stage grow with the suite).
- Tests: `tests/shared/domain/test_document_examples.py` (pure), and an adapter test with the fake containers.

## Acceptance criteria

1. `examples` finds a `console` block's fixture (`checkout` when none is named), commands and expected output, in the document's order; it lists a `console vm`, `console github` or `console model` block as skipped with its kind (rows per kind).
2. `matches` accepts equal lines, `...` for any number of lines and `<placeholder>` for any text in a line, and refuses a missing or an extra line (rows of one test).
3. The blocks of one document run in order in one folder: a file the first block writes is there for the second; the next document starts in a new folder.
4. A command whose output differs gives one finding, `<document>:<line>: the example printed <first differing line>`; one that matches gives none. A command that runs past 60 seconds gives `<document>:<line>: the example did not end in 60 s`, and the document's later blocks are not run.
5. A block that names an unknown fixture gives `<document>:<line>: no fixture <name>`.
6. The commands never run in the checkout itself; `env` inside a block shows only the fixed environment and the fixture's variables.
7. `make documents` ends with `documents: green (<seconds> s)` when it finds nothing. A runnable block whose command is `make check`, `make test` or `pytest` without a file gives `<document>:<line>: the suite is not a runnable example; mark it console vm` (rows per command).
8. `make check` stays green.
9. docs: `docs/project-guide/style.md` (from F0052) or, until it exists, `docs/project-guide/shared.md`: how to write a runnable example, name a fixture, use the placeholders, and mark one that needs the VM, GitHub or a model; that a command running the suite or `make check` is marked `console vm`.

## Smoke test

```bash
uv run python -c "from factory.shared.domain.documents import examples; print(len(examples('\`\`\`console\n\$ echo hi\nhi\n\`\`\`\n').runnable))"
```
Expect: `1`

## Journal
