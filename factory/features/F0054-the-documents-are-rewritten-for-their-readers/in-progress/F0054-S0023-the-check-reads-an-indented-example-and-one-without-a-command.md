---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 609
comments_read: [6697578988]
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-06T22:47:58.338963Z'
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
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T22:41:27.370645Z'
  stage: tests
  run: 67d09e2143a04ecea3de9ea01ab76cba
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T22:41:32.403983Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-11-06T22:46:35.986904Z'
  stage: doing
  run: ddf3b1cfbea5456b9047a1d68cecdb34
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-06T22:46:41.158438Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-11-06T22:47:52.267061Z'
  stage: review
  run: a5a9cf4cbb484b2295348678e8d9c90c
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-06T22:47:58.338963Z'
  stage: docs
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
8. tester: I added the red tests for every criterion: new rows in the two earlier modules that the Interface names. No earlier row was changed.

   - criterion 1: tests/shared/domain/test_document_examples.py::test_a_block_indented_under_a_step_reads_as_at_column_0 (rows: three-spaces, four-spaces, tab, column-0, line-less-indented-than-fence; every row expects the same Example, fence line 5 and command line 6, and the less-indented row keeps its one space in the expected line ` hi`)
   - criterion 2: tests/entry/test_check_documents_examples.py::test_a_console_block_without_a_command_is_a_finding_at_its_fence (rows: column-0, indented; the finding `docs/project-guide/shared.md:<fence line>: the example has no command` is printed and `main` does not raise). A second test covers the domain side: tests/shared/domain/test_document_examples.py::test_a_console_block_without_a_command_gives_no_example (rows: column-0, indented; `examples` does not raise and gives no runnable Example). It does not pin whether such a block appears in `skipped`, because the Interface leaves that open.
   - criterion 3: tests/entry/test_check_documents_examples.py::test_an_example_finding_blocks_in_a_listed_file_and_is_reported_in_any_other (rows: no-command-listed blocks with exit 1; no-command-not-listed and mismatch-not-listed are reported under the report heading with exit 0)
   - criterion 4: tests/entry/test_check_documents_examples.py::test_an_indented_example_is_run_and_a_mismatch_in_a_listed_file_blocks (rows: match prints only the time line with exit 0; mismatch-listed prints one finding, `the example printed ...`, with exit 1)

   The entry tests run on the `minimal` fixture (tests/support/minimal_documents_support.py). They append a numbered step with a `console` block to `docs/project-guide/shared.md` and commit it through `add_and_commit`. `docs/checked-documents.txt` holds either that page or nothing.

   Files changed: tests/shared/domain/test_document_examples.py and tests/entry/test_check_documents_examples.py. I created no new files. No module failed to import, because `factory.shared.domain.documents` exists.

   Test run (`uv run pytest -q` on the two files): 13 new rows fail, all with `ValueError: zip() argument 2 is longer than argument 1` at src/factory/shared/domain/documents.py:681. The column-0 row of criterion 1 and every earlier row pass. I ran the tests twice: the first run showed that my own helper `_append_step` counted the fence line wrongly, so I changed it to use `line_of` and ran once more to see the real reasons. `make lint` is green.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I made the 13 red rows pass without changing a test. `make check` is green (`check: green`).

    What I built:
    - `src/factory/shared/domain/documents.py`:
      - The new `_block_lines` removes the opening fence's indentation from each line of a block, using `str.removeprefix`. A line indented less than its fence keeps what it has, and line numbers do not change.
      - `_commands` returns `[]` for a block with no `$ ` line. Before, it crashed with the strict `zip` error.
      - `examples` sends such a block to a new field, `Examples.without_command`, which holds the fence line of each block without a command. Such a block is neither runnable nor skipped.
      - The finding's text is the new public constant `NO_COMMAND`.
    - `src/factory/entry/check_documents.py`, `_example_results`: it turns each line in `without_command` into a `GatedFinding` `<document>:<line>: the example has no command`. These go to the same `split_findings` path as the runner's findings, so they block in a listed file and are reported in any other.

    The Interface says "no other module changes", but the entry tests for criteria 2 and 3 need `main` to print the finding. The Interface also says it goes "through the same path as the other example findings", and that path is in the entry module. So this four-line change there is unavoidable; please judge whether it is acceptable.

    Main design decision: the domain reports blocks without a command as a list of fence lines, and the entry formats the finding with the document name, the way it already formats the "not run" lines. I rejected two alternatives:
    - Reporting such a block as a `Skipped` kind: the entry would print it as "not run (...)" in the report and never block on it.
    - Building finding strings in `examples`: it does not know the document's path.

    Refactor: I read my diff once and found nothing to change.

    The smoke-test command was refused by the shell's permission check, so I did not run it. The tester's indented rows in `tests/shared/domain/test_document_examples.py` check the same thing (`echo hi` from a block indented three spaces) and pass.

    Noticed, not touched: an unclosed `console` block still reads to the end of the document, as before.

    The journal did not change the meaning of the task beyond what intake already carried into the Description.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
11. factory: started review as vm.
12. reviewer: no findings

    What I checked (the diff `git diff main...HEAD -- . ':!factory'` and the work item):
    - Criterion 1: `tests/shared/domain/test_document_examples.py::test_a_block_indented_under_a_step_reads_as_at_column_0` has rows for three spaces, four spaces, a tab, column 0 and a line indented less than its fence (it keeps ` hi`). Every row expects fence line 5 and command line 6. In the code, `_block_lines` (`src/factory/shared/domain/documents.py:682`) applies `removeprefix` of the fence's own indentation, and the line numbers stay those of the raw lines.
    - Criterion 2: `tests/entry/test_check_documents_examples.py::test_a_console_block_without_a_command_is_a_finding_at_its_fence` has a column-0 row and an indented row. It checks the finding at the fence line from `line_of`, and `main` does not raise. The domain side is `test_a_console_block_without_a_command_gives_no_example`. In the code, `_commands` returns `[]` when there is no prompt (documents.py:692), and `examples` records `block.start + 1`, which is the 1-based fence line.
    - Criterion 3: one parametrized test covers three cases. The no-command finding blocks in a listed file (exit 1, no report heading, no time line). It is reported after the heading in an unlisted file (exit 0). An indented mismatch is reported in an unlisted file.
    - Criterion 4: one parametrized test. An indented match prints only the time line with exit 0. An indented mismatch in a listed file prints one `the example printed` finding with exit 1.
    - Interface limits: both sides are tested (indented and column 0, a tab, a less-indented line, a block with and without a command, a listed and an unlisted file). The tester's red run named the `zip` crash. The coder's `make check` was green (journal entry 10).
    - Architecture: the domain change is pure, with no I/O. `Examples` is not in the records contract, so the contract needs no regeneration. Nothing else in `src` or `tests` builds `Examples(...)`. The entry change is wiring only.
    - The coder asked whether changing `src/factory/entry/check_documents.py` is acceptable when the Interface says "No other module changes". I judge it acceptable, not a finding. The same Interface sends the finding "through the same path as the other example findings", and that path is `_example_results` in the entry module. Criteria 2 and 3 can only pass if `main` prints the finding. The change is four lines in `_example_results` and reuses the existing `GatedFinding` and `split_findings` path. The Description makes no claim about which modules change, so it is not stale.
    - Security: there are no markers, secrets, strings that reach a shell, or new dependencies.
    - Quality: I found no existing helper that `_fence_indentation` or `_block_lines` copies; `sections.py` only strips the indentation inside `_closes`. The docstrings of `Examples` and `examples` describe the new behaviour. I ran `make duplicates`: its 6 new findings are all outside this diff (`claude_runtime` and `opencode_runtime`, `hand_over` and `acceptance`, the fields of `cost_records`, and `matches`, which was already unused and only moved lines).
    - Work item hygiene: the coder's journal entry 10 names the main decision (a `without_command` field rather than a new `Skipped` kind or finding strings built in the domain) and what it rejected. The Description matches what was built. The docs criterion still names what the reader must know.
    - Smoke test: the coder did not run it, because the shell refused it. The domain rows cover the same case.

    Earlier tests:
    - tests/shared/domain/test_document_examples.py: none needed (rows added only; the Interface also allows them).
    - tests/entry/test_check_documents_examples.py: none needed (tests and imports added only, every earlier test unchanged; the Interface also allows them).
13. factory: started docs as vm.
