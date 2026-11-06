---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 587
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T07:24:24.847035Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T07:24:24.853652Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T07:24:42.001462Z'
  stage: intake
  run: 0e468b2cbdfc4a20b7506215dbc3eaa3
  blocked: question
---

# A document's marked examples are run by the check

## Description

An example that shows a command and what it prints is the claim a reader trusts most, and the one easiest to check: run it. This story lets a document mark an example as runnable, like a notebook whose cells the test runner executes instead of the reader. A fenced block with the info string `console` holds lines that start with `$ ` (the commands) and the lines below each (the expected output). Its info string may name a fixture, `console fixture=<name>`; this story gives the one fixture `checkout` (a copy of the repository at the checked commit, and the default) and S0006 adds `instance`. The blocks of one document run in order and share their fixture, like the cells of a notebook: each document starts fresh, and a block sees what the blocks above it did (the human, 2026-11-05). The commands run in a fixed environment, and the expected output may hold `...` on a line of its own for any lines and `<placeholder>` for any text within a line, for what varies, such as times, ids and temporary paths. A block marked `console vm`, `console github` or `console model` is not run, and neither is a block whose command runs the test suite (`make check`, `make test`, `pytest` without a file), which needs no mark; the report lists each with its kind, and nobody runs them routinely (the human, 2026-11-05: what they would add is small against what the name and settings checks and the scripts' own tests already catch, and the acceptance reviewer runs `make check` anyway). Until S0004, a failed example is only printed.

## Interface

- `factory.shared.domain.documents` (pure):
  - `examples(text) -> list[Example]`: the runnable blocks of one document in order, each with its line, fixture name, commands and expected output, and the marked blocks it skips, with their kind.
  - `matches(expected, actual) -> bool`, with the two placeholders.
- `factory.shared.application.document_examples`:
  - `Fixture`, an interface: `prepare(folder) -> dict[str, str]` builds the starting point in an empty folder and gives the extra environment the commands get.
  - `ExampleRunner`, an interface: `run_document(document, examples, fixtures) -> list[str]` gives the findings of one document.
  - The fixture `checkout`: a copy of the repository's tracked files at the checked commit, as a git checkout.
- An adapter runs a document's commands through the project commands' container environment (the container a check runs in), in a temporary folder that the fixture prepared, with `env -i` and `TZ=UTC`, `LANG=C.UTF-8`, `HOME` a temporary folder, `PATH` the container's; each command has a time limit of 60 seconds. The folder is removed afterwards.
- `make documents` runs the examples; `make check` does not. Its last line gives its time, `documents ok (<seconds> s)`, so that the time shows in every docs stage's output.
- A `console` block with a command that runs the suite (`make check`, `make test`, `pytest` without a file) is skipped as kind `suite`, so that the examples never make the docs stage grow with the suite (the human, 2026-11-05).
- Tests: `tests/shared/domain/test_document_examples.py` (pure), and an adapter test with the fake containers.

## Acceptance criteria

1. `examples` finds a `console` block's fixture (`checkout` when none is named), commands and expected output, in the document's order; it lists a `console vm`, `console github` or `console model` block, and an unmarked block that runs `make check`, `make test` or `pytest` without a file, as skipped with its kind (`vm`, `github`, `model`, `suite`; rows per kind); `pytest` with a file is run.
2. `matches` accepts equal lines, `...` for any number of lines and `<placeholder>` for any text in a line, and refuses a missing or an extra line (rows of one test).
3. The blocks of one document run in order in one folder: a file the first block writes is there for the second; the next document starts in a new folder.
4. A command whose output differs gives one finding, `<document>:<line>: the example printed <first differing line>`; one that matches gives none. A command that runs past 60 seconds gives `<document>:<line>: the example did not end in 60 s`, and the document's later blocks are not run.
5. A block that names an unknown fixture gives `<document>:<line>: no fixture <name>`.
6. The commands never run in the checkout itself; `env` inside a block shows only the fixed environment and the fixture's variables.
7. `make documents` ends with `documents ok (<seconds> s)` when nothing blocks, and the report lists every skipped block as `<document>:<line>: not run (<kind>)`.
8. `make check` stays green.
9. docs: `docs/project-guide/style.md` (from F0052) or, until it exists, `docs/project-guide/shared.md`: how to write a runnable example, name a fixture, use the placeholders, and mark one that needs the VM, GitHub or a model; that a block running the suite is skipped without a mark; that a `vm` example comes from a real run and says where it ran.

## Smoke test

```bash
uv run python -c "from factory.shared.domain.documents import examples; print(len(examples('\`\`\`console\n\$ echo hi\nhi\n\`\`\`\n').runnable))"
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: 1. The smoke test and the Interface disagree. The Interface gives `examples(text) -> list[Example]`, but the smoke test calls `examples(...).runnable`, which a list does not have, so the command fails and `Expect: 1` can't be met. It also says "the runnable blocks ... and the marked blocks it skips, with their kind" but not how they are returned. Options: (a) `examples` returns a frozen DTO `Examples` with `runnable: list[Example]` and `skipped: list[Skipped]` (each with line and kind). The smoke test stays as written. (b) It returns a list and the smoke test uses `len(examples(...))`. I would choose (a), since criterion 1 and `make documents` (criterion 7) need both lists. Please name the return type in the Interface either way.
   2. The Interface names no concrete module for the adapter that runs the commands in the container ("An adapter runs a document's commands ..."). It also doesn't say where the `checkout` fixture class lives, or what `ExampleRunner`'s and `Fixture`'s implementing classes are called. The architecture puts adapters in `factory.shared.adapters` or a named area's `adapters` layer, and the tests need the module path. Please give module and class names. I would choose `factory.shared.adapters.document_examples` with `ContainerExampleRunner(ExampleRunner)` and `CheckoutFixture(Fixture)`.
   3. The Interface says `make documents` ends with `documents ok (<seconds> s)`, and criterion 7 tests that. Nothing says which module prints the line, nor how the report is built from the findings and the skipped blocks. Please say whether the report and the time line come from an existing module (name it) or a new one. I would choose the existing document-check module behind `make documents`; please name it.
