---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 609
comments_read: [6697578988]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-06T22:39:05.960744Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T22:36:50.244182Z'
  stage: intake
  run: 648c633bb9a54c50ba81a79e1b303124
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T22:38:39.900698Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T22:38:42.530110Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T22:39:00.812571Z'
  stage: intake
  run: 6b09def657a4483891f0cd8612b3835a
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T22:39:05.960744Z'
  stage: tests
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

1. A `console` block indented by three spaces under a numbered step, with `$ echo hi` and `hi`, gives one `Example` with the command `echo hi`, the expected line `hi` and the same line numbers as at column 0. Rows: three spaces, four spaces, a tab, and column 0; and a block whose fence is indented by three spaces and which holds a line indented by one space, which keeps that space.
2. A `console` block with no `$ ` line gives the finding `<document>:<line>: the example has no command` at its fence line, and no exception. Rows: at column 0 and indented.
3. On minimal documents, through `main(["--root", ...])`, the finding `the example has no command` blocks in a listed file and is reported without blocking in an unlisted one; an indented example that does not match is reported without blocking in an unlisted file. Rows of one test.
4. On minimal documents, `make documents` (through `main(["--root", ...])`) runs an indented example that matches and gives no finding. It gives one blocking finding for an indented example that does not match in a listed file. Rows of one test.
5. `make check` stays green.
6. docs: `docs/project-guide/style.md`, *Runnable examples*: the reader learns that an example may stand indented under its numbered step, and that a `console` block must hold at least one `$ ` command. `docs/project-guide/shared.md`, the example check: the reader learns that the block's indentation is removed before it is read, and the new finding. `docs/decisions.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; printf '# T\n\n1. Run it:\n\n   ```console\n   $ echo hi\n   hi\n   ```\n' > "$d/t.md"; uv run python -c "import sys; from factory.shared.domain.documents import examples; e = examples(open(sys.argv[1]).read()); print(len(e.runnable), e.runnable[0].commands[0].command)" "$d/t.md"
```
Expect: `1 echo hi`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface rule "A line of the block with less indentation than its fence keeps what it has" has no criterion. Add one, e.g. a row in criterion 1 where a block line is indented less than the fence and keeps its indentation. I would add it.
   2. Interface rule "That path blocks in a listed file and is reported in any other" is not tested for the new finding. Criterion 2 only covers `examples`, and criterion 3 covers only a mismatch in a listed file. Add a criterion with rows for the no-command finding in a listed file (blocking) and in an unlisted file (reported, not blocking), and the same for the unlisted side of an indented mismatch. I would add both.
   3. Criterion 1 names the line numbers as unchanged, but the finding line for a tab-indented fence and the "less indentation" case are not stated. Covered by 1 once added; confirm.
   Everything else checks out. Interface names the module and signatures. The smoke test is runnable and its Expect is checkable (no pytest). The docs criterion names what the reader must know and dictates no sentences. The architecture is a domain-only change. The scope fits F0054 (this is the follow-up story for the code fault the feature's Out of scope says becomes its own story).
4. 2026-11-06 human: 1. Yes: a row in criterion 1 where a block line is indented less than its fence and keeps the indentation it has.
   2. Yes, one more criterion with rows: the no-command finding blocks in a listed file and is only reported in an unlisted one; an indented example that does not match is only reported in an unlisted file.
   3. Confirmed: with those rows, criterion 1 states the line numbers for a tab-indented fence and for the less-indented line, unchanged from column 0.
5. factory: started intake as vm.
6. intake: accepted, with the human's answer (journal entry 4) carried into the story.
   Edits from entry 4: criterion 1 gets the row for a block line indented less than its fence, which keeps its indentation; a new criterion 3 tests the no-command finding as blocking in a listed file and only reported in an unlisted one, and an indented mismatch as only reported in an unlisted file. The later criteria are renumbered, and `make check` and `docs:` stay last.
   - Interface: `factory.shared.domain.documents.examples` is a concrete module with unchanged signatures. The indentation removal, the less-indented line and the `the example has no command` finding at the fence line are stated, and the finding's blocking path is stated.
   - Criteria: each is testable by one parametrized test. Every Interface rule has a criterion for both sides: indented and column 0, a tab, less-indented lines, no command against a command present, a listed file against an unlisted one.
   - Smoke test: the command is runnable and does not run pytest. `Expect: 1 echo hi` can be checked against the output.
   - Docs criterion: it names what the reader must know (an indented example under a step, at least one `$ ` command, the indentation removal, the new finding) and dictates no sentences.
   - Architecture: the change is domain-only in the shared area, with no new dependency.
   - Scope: it fits F0054. It is the code-fault follow-up story that the feature's Out of scope calls for.
7. factory: started tests as vm.
