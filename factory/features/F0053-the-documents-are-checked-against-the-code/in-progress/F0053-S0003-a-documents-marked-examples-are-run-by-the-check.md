---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 587
comments_read: [6679620269, 6679692361, 6679759183, 6679929799]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-06T07:57:56.056666Z'
  lease_duration: 60
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
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T07:28:33.633757Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T07:28:36.023479Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T07:28:58.724938Z'
  stage: intake
  run: c850745622914b23b18a92712af5e125
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T07:29:03.790530Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-06T07:30:00.894290Z'
  stage: tests
  run: b81caa3c331d4e8aa9601f79214aa9c1
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-06T07:31:50.375443Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T07:31:52.891416Z'
  stage: tests
- number: 11
  speaker: tester
  kind: question
  at: '2026-11-06T07:34:28.691354Z'
  stage: tests
  run: 9f0fd318225f44beb7e04f523cce89d0
  blocked: question
- number: 12
  speaker: human
  kind: comment
  at: '2026-11-06T07:36:18.105953Z'
  stage: tests
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-06T07:36:20.672868Z'
  stage: tests
- number: 14
  speaker: tester
  kind: result
  at: '2026-11-06T07:37:07.178843Z'
  stage: tests
  run: 4d3c02f13e3046469f5ad9f15a25851e
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-06T07:37:12.577175Z'
  stage: doing
- number: 16
  speaker: coder
  kind: question
  at: '2026-11-06T07:45:19.194746Z'
  stage: doing
  run: bc040921dc834b7fbbe0c2778f3724bb
  blocked: question
- number: 17
  speaker: human
  kind: comment
  at: '2026-11-06T07:47:10.050237Z'
  stage: doing
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T07:47:12.725718Z'
  stage: doing
- number: 19
  speaker: coder
  kind: result
  at: '2026-11-06T07:47:31.946145Z'
  stage: doing
  run: 7ab4cbd256f145518ddb00805e3070a8
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T07:47:37.478176Z'
  stage: tests
- number: 21
  speaker: tester
  kind: result
  at: '2026-11-06T07:48:31.353350Z'
  stage: tests
  run: 7ae96c5023d64d12bcd71e3fddfef81e
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-06T07:48:36.591590Z'
  stage: doing
- number: 23
  speaker: coder
  kind: result
  at: '2026-11-06T07:52:56.033601Z'
  stage: doing
  run: e63de3332f8f4c6792ac11b1ce6bc68a
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-06T07:53:01.579577Z'
  stage: review
- number: 25
  speaker: reviewer
  kind: result
  at: '2026-11-06T07:54:57.289531Z'
  stage: review
  run: 9328e68e5dc445f3a2347a938b27b997
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-06T07:55:03.009670Z'
  stage: doing
- number: 27
  speaker: coder
  kind: result
  at: '2026-11-06T07:57:50.700464Z'
  stage: doing
  run: 9b822f0136004777a7fd72f5919d65a0
- number: 28
  speaker: factory
  kind: started
  at: '2026-11-06T07:57:56.056666Z'
  stage: tests
---

# A document's marked examples are run by the check

## Description

An example that shows a command and what it prints is the claim a reader trusts most, and the one easiest to check: run it. This story lets a document mark an example as runnable, like a notebook whose cells the test runner executes instead of the reader. A fenced block with the info string `console` holds lines that start with `$ ` (the commands) and the lines below each (the expected output). Its info string may name a fixture, `console fixture=<name>`; this story gives the one fixture `checkout` (a copy of the repository at the checked commit, and the default) and S0006 adds `instance`. The blocks of one document run in order and share their fixture, like the cells of a notebook: each document starts fresh, and a block sees what the blocks above it did (the human, 2026-11-05). The commands run in a fixed environment, and the expected output may hold `...` on a line of its own for any lines and `<placeholder>` for any text within a line, for what varies, such as times, ids and temporary paths. A block marked `console vm`, `console github` or `console model` is not run, and neither is a block whose command runs the test suite (`make check`, `make test`, `pytest` without a file), which needs no mark; the report lists each with its kind, and nobody runs them routinely (the human, 2026-11-05: what they would add is small against what the name and settings checks and the scripts' own tests already catch, and the acceptance reviewer runs `make check` anyway). Until S0004, a failed example is only printed.

## Interface

- `factory.shared.domain.documents` (pure):
  - `examples(text) -> Examples`: a frozen DTO with `runnable: list[Example]` (the runnable blocks of one document in order, each with its line, fixture name, commands and expected output) and `skipped: list[Skipped]` (`line` and `kind`).
  - `matches(expected, actual) -> bool`, with the two placeholders.
- `factory.shared.application.document_examples`:
  - `Fixture`, an interface: `prepare(folder) -> dict[str, str]` builds the starting point in an empty folder and gives the extra environment the commands get.
  - `ExampleRunner`, an interface: `run_document(document, examples, fixtures) -> list[str]` gives the findings of one document.
- `factory.shared.adapters.document_examples`: `ProcessExampleRunner(ExampleRunner)` runs each command through `factory.shared.adapters.process` (no container of its own: `make documents` already runs in the check container), in a temporary folder that the fixture prepared, with `env -i` and `TZ=UTC`, `LANG=C.UTF-8`, `HOME` a temporary folder, `PATH` the container's; each command has a time limit of 60 seconds (the test passes a shorter one in). The folder is removed afterwards.
- `factory.hosting.adapters.checkout_fixture`: `CheckoutFixture(Fixture)`, the fixture `checkout`: a copy of the repository's tracked files at the checked commit, built through `GitCli`. `factory.entry` wires the two classes.
- `make documents` runs the examples; `make check` does not. `factory.entry.check_documents` builds the report: today's findings, the name and settings findings, the example findings, one `<document>:<line>: not run (<kind>)` line per skipped block, and last `documents ok (<seconds> s)` when nothing blocks, so that the time shows in every docs stage's output.
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
8. A command that prints fewer lines than its expected output holds gives `<document>:<line>: the example printed nothing more`.
9. A command run through `uv run` is read like the one after it: `uv run make check`, `uv run make test`, `uv run pytest` and a `pytest` with options only (`pytest -q`) are skipped as `suite`, and `uv run pytest <file>` is run (rows of the criterion 1 tests).
10. `make check` stays green.
11. docs: `docs/project-guide/style.md` (from F0052) or, until it exists, `docs/project-guide/shared.md`: how to write a runnable example, name a fixture, use the placeholders, and mark one that needs the VM, GitHub or a model; that a block running the suite is skipped without a mark; that a `vm` example comes from a real run and says where it ran.

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
4. 2026-11-06 human: 1. (a): `examples(text) -> Examples`, a frozen DTO with `runnable: list[Example]` and `skipped: list[Skipped]`; `Skipped` holds `line` and `kind`. The smoke test stays as written.
   2. `make documents` already runs inside the factory's check container, so the runner starts no container of its own: it runs each command as a process in that container. Names:
      - `factory.shared.adapters.document_examples`: `ProcessExampleRunner(ExampleRunner)`. It runs each command through `factory.shared.adapters.process`, the one module that starts processes (R5), with `env -i`, the fixed environment, the 60-second limit and the folder the fixture prepared.
      - `factory.hosting.adapters.checkout_fixture`: `CheckoutFixture(Fixture)`, since git belongs to hosting. It builds the copy of the tracked files at the checked commit through the git wrapper `GitCli`, not by its own `git` call.
      - `Fixture` and `ExampleRunner` stay in `factory.shared.application.document_examples`, and `factory.entry` wires the two classes.
      The adapter tests run real short commands (`echo`, `printf`, a file written in one block and read in the next) in `tmp_path`, with no network; the time-limit row uses `sleep` past a limit the test passes in.
   3. The existing `factory.entry.check_documents` (behind `make documents`) builds the report: today's findings, the name and settings findings, the example findings, then one `<document>:<line>: not run (<kind>)` line per skipped block, and last `documents ok (<seconds> s)` when nothing blocks. It measures the seconds with the clock it already uses, or with `time.monotonic` passed in from `main`.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete after the human's answer (journal 4). I wrote it into `## Interface`: `examples(text) -> Examples` (frozen DTO with `runnable` and `skipped`, `Skipped` holds `line` and `kind`), `factory.shared.adapters.document_examples.ProcessExampleRunner`, `factory.hosting.adapters.checkout_fixture.CheckoutFixture` (through `GitCli`), and `factory.entry.check_documents` for the report and time line. The smoke test is unchanged and now matches the return type.
   - Criteria: each is testable by one test function. Both sides are covered: the match and no-match cases (2, 4), the timeout (4), the unknown fixture (5) and the skipped and run kinds (1, including `pytest` with a file). I found no Interface rule without a criterion.
   - Smoke test: the python one-liner is runnable and `Expect: 1` is checkable. It runs no pytest, so the `-q` rule does not apply.
   - Architecture: this fits. Pure code is in shared domain, interfaces in shared application, the process adapter in shared adapters, git in hosting adapters, wiring in entry. Processes start only through `factory.shared.adapters.process`.
   - Scope: this is within the feature's S0003. It leaves out the `instance` fixture (S0006) and blocking (S0004). The route is `tests` because the Interface changes `src` code.
7. factory: started tests as vm.
8. tester: I wrote no tests. The Interface leaves the following open, and the tests would otherwise decide each one. I read `factory.entry.check_documents`, `factory.shared.domain.documents`, `factory.shared.adapters.process` and `tests/entry/test_check_documents.py`.

   1. An existing test conflicts with criterion 7. `tests/entry/test_check_documents.py::test_clean_documents_print_documents_ok_and_return_zero` asserts the output is exactly `"documents ok\n"`. Today `documents ok` is printed first, before the name and settings findings. Criterion 7 wants `documents ok (<seconds> s)` as the last line. That test belongs to another story, so changing it needs your leave. Options: (a) I change its assertion to the output's last line matching `documents ok (<n> s)`; (b) the coder keeps the old line too. I would choose (a).

   2. Which documents have their examples run? (a) The documents `_named_documents` already reads: `README.md` and every `*.md` under `docs/operator-guide/` and `docs/project-guide/`. (b) Only `DOCUMENT_PATHS` and the guide files. I would choose (a). In both cases the document is named by its path relative to the root.

   3. Names and shapes the tests need:
      - (a) `Example` fields. I would choose `line: int` (the block's opening fence), `fixture: str`, `commands: list[Command]`, with `Command` holding `line: int` (the `$ ` line), `command: str` (without `$ `) and `expected: list[str]`.
      - (b) Which line a finding names. I would choose the `$ ` line for criterion 4, and the fence line for criteria 1 (skipped) and 5 (unknown fixture).
      - (c) The runner's signature. I would choose `run_document(document: str, examples: list[Example], fixtures: Mapping[str, Fixture]) -> list[str]`.
      - (d) How the shorter limit is passed in. I would choose `ProcessExampleRunner(time_limit: timedelta = timedelta(seconds=60))`. The finding then names the limit's seconds, so with the test's limit it reads `did not end in <n> s`.
      - (e) How a command is run. I would choose `sh -c <command>`, with the command's stdout and stderr merged, compared against the expected lines.

   4. Criterion 6, "`env` shows only the fixed environment". A shell adds `PWD` (and bash also adds `SHLVL` and `_`). Options:
      - (a) The test checks that the output of `env | sort` holds exactly `HOME`, `LANG`, `PATH`, `TZ`, the fixture's variables and `PWD`.
      - (b) The test checks that those variables are present and that a variable set in the test's own environment is absent.

      I would choose (b), since it doesn't pin the shell.

   5. Criterion 7 through `main(["--root", tmp])`. `factory.entry` wires `CheckoutFixture`, but a tmp root with only skipped blocks is no git repository. Options:
      - (a) The test's root holds only skipped blocks, and `main` builds or uses the fixture only when a block runs.
      - (b) `main` takes the runner and fixtures as parameters.

      I would choose (a). CheckoutFixture's own behaviour (the tracked files at the checked commit) has no criterion. Should it get a test with a real local repository: a tracked file is in the folder, an untracked one is not? I would say yes, as part of criterion 6.

   6. The Interface says "an adapter test with the fake containers", but your answer in journal entry 4 says real short commands in `tmp_path` and no container. I will follow your answer: real `echo`, `printf` and `sleep` through `ProcessExampleRunner`, in `tests/shared/adapters/test_document_examples.py`. The pure tests go in `tests/shared/domain/test_document_examples.py`, and the report tests in `tests/entry/test_check_documents_examples.py`.

   Files created: none. Modules not imported: none (no test run).
9. 2026-11-06 human: 1. (a), with the human's leave: the tester changes `tests/entry/test_check_documents.py::test_clean_documents_print_documents_ok_and_return_zero` so that the output's last line matches `documents ok (<n> s)` and the exit status stays 0, and nothing else in that module. Its entry names the change.
   2. (a): the documents `_named_documents` already reads, each named by its path relative to the root.
   3. Yes to all five as you propose: (a) `Example(line, fixture, commands)` and `Command(line, command, expected)`; (b) the `$ ` line for an output or time finding, the fence line for a skipped block and an unknown fixture; (c) `run_document(document: str, examples: list[Example], fixtures: Mapping[str, Fixture]) -> list[str]`; (d) `ProcessExampleRunner(time_limit: timedelta = timedelta(seconds=60))`, the finding naming the limit's seconds; (e) `sh -c <command>` with stdout and stderr merged.
   4. (b): the fixed variables and the fixture's are present, and a variable set in the test's own environment is absent.
   5. (a), and yes: `CheckoutFixture` gets a test on a real local repository, a tracked file is in the folder and an untracked one is not, under criterion 6.
   6. Yes, follow the answer in entry 4: real short commands, no containers, in the three test modules you name.
10. factory: started tests as vm.
11. tester: I wrote the tests for every criterion and made the one change you allowed, but I'm stopping with a question. Once the coder adds the time line, three more tests in the module you let me change will fail, and you gave no leave for them.

    Question 1: three other tests in `tests/entry/test_check_documents.py` check that the whole output is exactly `"documents ok\n"`:
    - `test_without_a_root_the_current_directory_is_read`
    - the `clean` row of `test_the_module_run_as_a_process_exits_with_the_status_of_main`
    - `test_documents_are_read_as_utf_8`

    Under criterion 7 the last line becomes `documents ok (<seconds> s)`, so all three fail after the coder's work. The coder can't fix them and `make check` stays red. Journal entry 9 lets me change only `test_clean_documents_print_documents_ok_and_return_zero`, "and nothing else in that module".
    - (a) I give these three the same change: the output's last line matches `documents ok \(\d+(\.\d+)? s\)`, and each keeps its exit-status check. For the process row, the stdout's last line. The `empty-directory` row is unchanged.
    - (b) Leave them, and the coder's `make check` stays red.

    I would choose (a).

    Question 2: the Interface doesn't give `CheckoutFixture`'s constructor. My test assumes `CheckoutFixture(git: GitCli)` on the `checkout` fixture's clone, with `prepare(folder)` copying the tracked files at `HEAD`. The other option is `CheckoutFixture(root: Path)`, which builds its own `GitCli`. I would keep `CheckoutFixture(git)`.

    Criterion → test:
    - criterion 1: `tests/shared/domain/test_document_examples.py::test_a_console_block_gives_its_fixture_commands_and_expected_output_in_order` (also covers `pytest` with a file being run), and `::test_a_marked_block_or_one_that_runs_the_suite_is_skipped_with_its_kind` (one row each for vm, github, model, make-check, make-test, pytest-without-a-file)
    - criterion 2: `tests/shared/domain/test_document_examples.py::test_matches_accepts_equal_lines_and_the_placeholders_and_refuses_missing_or_extra_lines`
    - criterion 3: `tests/shared/adapters/test_document_examples.py::test_the_blocks_of_one_document_share_a_folder_and_the_next_document_starts_fresh`
    - criterion 4: `tests/shared/adapters/test_document_examples.py::test_a_command_whose_output_differs_gives_one_finding_and_one_that_matches_none`, `::test_the_output_compared_holds_stderr_too` (stdout and stderr merged, journal 9 3e), and `::test_a_command_past_its_limit_gives_one_finding_and_the_later_blocks_do_not_run` (limit 1 s, `sleep 30`, elapsed under 15 s)
    - criterion 5: `tests/shared/adapters/test_document_examples.py::test_a_block_naming_an_unknown_fixture_gives_a_finding`
    - criterion 6: `tests/shared/adapters/test_document_examples.py::test_the_commands_never_run_in_the_current_directory`, `::test_env_in_a_block_shows_the_fixed_variables_and_the_fixtures_and_not_the_callers`, and `tests/hosting/adapters/test_checkout_fixture.py::test_the_checkout_fixture_copies_the_tracked_files_and_not_the_untracked_ones`
    - criterion 7: `tests/entry/test_check_documents_examples.py::test_the_report_lists_every_skipped_block_and_ends_with_the_time_line`
    - criteria 8 and 9: no test (`make check` and docs)

    Lines are 1-based. Following journal 9 3b, a finding names the `$ ` line for output or time and the fence line for a skipped block or an unknown fixture.

    Files created:
    - `tests/shared/domain/test_document_examples.py`
    - `tests/shared/adapters/test_document_examples.py`
    - `tests/hosting/adapters/test_checkout_fixture.py`
    - `tests/entry/test_check_documents_examples.py`

    Earlier test file changed, with your leave from journal 9 (1a): in `tests/entry/test_check_documents.py`, `test_clean_documents_print_documents_ok_and_return_zero` now checks that the last line matches `documents ok (<n> s)`, and the status stays 0. I also added `import re` to that module.

    Test run: the three new pure and adapter modules fail at collection, for the right reason:
    - `factory.shared.domain.documents` has no `Command`
    - no module named `factory.shared.adapters.document_examples`
    - no module named `factory.hosting.adapters.checkout_fixture`

    The two entry tests fail on their assertions, since there is no time line yet. `make lint` is green.
12. 2026-11-06 human: 1. (a), with the human's leave: the three tests `test_without_a_root_the_current_directory_is_read`, the `clean` row of `test_the_module_run_as_a_process_exits_with_the_status_of_main` (its stdout's last line) and `test_documents_are_read_as_utf_8` get the same change: the last line matches `documents ok \(\d+(\.\d+)? s\)`, and each keeps its exit-status check. The `empty-directory` row stays. Nothing else in that module changes, and your entry names all four.
    2. `CheckoutFixture(git: GitCli)`, as you propose.
13. factory: started tests as vm.
14. tester: I made the change you allowed in journal 12. I left the tests from journal 11 as they were, and they match answer 2: `CheckoutFixture(git: GitCli)`.

    Earlier test file changed, with your leave (journals 9 and 12): `tests/entry/test_check_documents.py`. I added a module constant `TIME_LINE = r"documents ok \(\d+(\.\d+)? s\)"`. Four tests now check that the output's last line matches it, and each keeps its exit-status check:
    - `test_clean_documents_print_documents_ok_and_return_zero` (from journal 11, now uses the constant)
    - `test_without_a_root_the_current_directory_is_read`
    - `test_documents_are_read_as_utf_8`
    - the `clean` row of `test_the_module_run_as_a_process_exits_with_the_status_of_main`. That row's expected output is now `None`, and the test checks the stdout's last line against `TIME_LINE`. The `empty-directory` row is unchanged.

    Nothing else in that module changed.

    Criterion → test:
    - criterion 1: `tests/shared/domain/test_document_examples.py::test_a_console_block_gives_its_fixture_commands_and_expected_output_in_order` (also covers `pytest` with a file being run), and `::test_a_marked_block_or_one_that_runs_the_suite_is_skipped_with_its_kind` (rows: vm, github, model, make-check, make-test, pytest-without-a-file)
    - criterion 2: `tests/shared/domain/test_document_examples.py::test_matches_accepts_equal_lines_and_the_placeholders_and_refuses_missing_or_extra_lines`
    - criterion 3: `tests/shared/adapters/test_document_examples.py::test_the_blocks_of_one_document_share_a_folder_and_the_next_document_starts_fresh`
    - criterion 4: `tests/shared/adapters/test_document_examples.py::test_a_command_whose_output_differs_gives_one_finding_and_one_that_matches_none`, `::test_the_output_compared_holds_stderr_too` and `::test_a_command_past_its_limit_gives_one_finding_and_the_later_blocks_do_not_run`
    - criterion 5: `tests/shared/adapters/test_document_examples.py::test_a_block_naming_an_unknown_fixture_gives_a_finding`
    - criterion 6: `tests/shared/adapters/test_document_examples.py::test_the_commands_never_run_in_the_current_directory`, `::test_env_in_a_block_shows_the_fixed_variables_and_the_fixtures_and_not_the_callers`, and `tests/hosting/adapters/test_checkout_fixture.py::test_the_checkout_fixture_copies_the_tracked_files_and_not_the_untracked_ones`
    - criterion 7: `tests/entry/test_check_documents_examples.py::test_the_report_lists_every_skipped_block_and_ends_with_the_time_line`, and the four tests above in `tests/entry/test_check_documents.py`
    - criteria 8 and 9: no test (`make check` and docs)

    Files created (journal 11): `tests/shared/domain/test_document_examples.py`, `tests/shared/adapters/test_document_examples.py`, `tests/hosting/adapters/test_checkout_fixture.py`, `tests/entry/test_check_documents_examples.py`.

    Modules the test run could not import:
    - `factory.shared.domain.documents` (no `Command`)
    - `factory.shared.adapters.document_examples`
    - `factory.hosting.adapters.checkout_fixture`

    These three test modules fail at collection. The entry tests fail on their assertions, since there is no time line yet. `make lint` is green.

    `lint`: lint: green (0.1 s)
15. factory: started doing as vm.
16. coder: I built all of it, but `make check` is red on four tests I'm not allowed to change. I stopped there and need your leave for two test changes.

    What I built (in the working tree):
    - `src/factory/shared/domain/documents.py`: `Command`, `Example`, `Skipped`, `Examples`, `examples(text)`, and `matches(expected, actual)` with `...` and `<placeholder>`. Next to `matches`, `first_difference(expected, actual)` finds the first printed line that departs, and `runs_the_suite(command)` also reads `uv run pytest`.
    - `src/factory/shared/application/document_examples.py`: the `Fixture` and `ExampleRunner` interfaces.
    - `src/factory/shared/adapters/document_examples.py`: `ProcessExampleRunner(time_limit=60 s)`.
      - Each command runs through `run_process` as `env -i <the fixture's variables> PATH= HOME= TZ=UTC LANG=C.UTF-8 sh -c <command>`, with stderr merged. The fixed variables come last, so no fixture can override them.
      - Each document gets one new temporary folder and home. A fixture is prepared once per document.
      - A command past its limit ends the document. When the output runs out before the expected lines do, the finding says `printed nothing more`.
    - `src/factory/hosting/adapters/checkout_fixture.py`: `CheckoutFixture(git: GitCli)`. It calls a new `GitCli.export(ref, folder)`, which runs `read-tree` into a temporary index and then `checkout-index --all --prefix=<folder>/`.
    - `src/factory/entry/check_documents.py`: the report prints today's findings, the name and settings findings, the example findings, then one `not run (<kind>)` line per skipped block. When nothing blocks, it ends with `documents ok (<n.n> s)`, timed with `time.monotonic`.

    Two choices I made to fit tests that already exist:
    - `export` is on `GitCli` only, not on the `Git` interface. I tried the interface first, but `tests/hosting/application/test_git_interface.py` and `test_checkout_hygiene_removed.py[git-twenty-two]` pin exactly 22 operations. `CheckoutFixture` takes a `GitCli`, as journal 12 says. I rejected building the copy from `show_file` calls: two processes per tracked file is far too slow for the whole repository.
    - The suite check compares whole strings like `"make check"`. `tests/guards/test_make_search.py` allows only the make class to contain `"make"` as a string literal.

    The new tests from journals 11 and 14 all pass, and so do lint, `mypy --strict` and the format check. `make check` fails on these four:

    Question 1: `tests/guards/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module` pins the set of modules that may import `factory.shared.adapters.process`. Your journal 4 answer has `ProcessExampleRunner` run commands through that module, so `factory.shared.adapters.document_examples` is a new importer.
    - (a) The tester adds `"factory.shared.adapters.document_examples"` to that set. I would choose (a).
    - (b) The runner goes through some other wrapper. There is no fitting one, and this contradicts journal 4.

    Question 2: three more tests still expect the whole output to be exactly `"documents ok\n"`. Journals 9 and 12 gave leave only for `tests/entry/test_check_documents.py`. They now print `documents ok (0.0 s)`:
    - `tests/entry/test_check_documents_guide_files.py::test_the_files_beside_the_index_are_read[others-ignored]`
    - `tests/entry/test_check_documents_guide_files.py::test_the_files_beside_the_index_are_read[utf-8]`
    - `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[as-it-is]`

    Options:
    - (a) Each row's last line matches `documents ok \(\d+(\.\d+)? s\)` and keeps its exit-status check, the same change as journal 12. I would choose (a).
    - (b) The code also prints a bare `documents ok` line, which goes against criterion 7.

    With your leave I end the next run with `tests` naming these changes, and the tester makes them.

    Still open:
    - The refactor step: it comes after `make check` is green, so it is not done yet.
    - Criterion 9, the docs in `docs/project-guide/shared.md`, is the documenter's.
    - I noticed `documents.py` is now about 590 lines. I did not split it.
17. 2026-11-06 human: 1. (a), with the human's leave: the tester adds `"factory.shared.adapters.document_examples"` to the set in `tests/guards/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`, and renames nothing else in that module. The runner is a new wrapper: it is the one place that runs a document's commands, as R5 asks of a wrapper. If the test's name counts the wrappers, it keeps its name.
    2. (a), and a wider leave so this does not come back: in any earlier test whose only failure is the exact `documents ok` line, the tester makes the last line match `documents ok \(\d+(\.\d+)? s\)` and keeps its exit-status check. That covers the three rows you name and any other of the same kind. Nothing else in those modules changes, and the entry names each test it changed.
    Noted: `documents.py` at about 590 lines is for a later split, not this story.
18. factory: started doing as vm.
19. coder: I changed no code this round. Your answer in journal 17 calls for test changes, and only the tester makes those. The implementation from journal 16 is committed on the branch, and `make check` fails only on the tests named below.

    What the tester changes, with your leave from journal 17:
    1. `tests/guards/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: add `"factory.shared.adapters.document_examples"` to the set of modules allowed to import `factory.shared.adapters.process`. Nothing else in that module changes, and the test keeps its name.
    2. The tests whose only failure is the exact `documents ok` line now check that their last line matches `documents ok \(\d+(\.\d+)? s\)`, and each keeps its exit-status check:
       - `tests/entry/test_check_documents_guide_files.py::test_the_files_beside_the_index_are_read`, rows `others-ignored` and `utf-8`
       - `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`, row `as-it-is`
       - any other earlier test that fails the same way. The entry names each one changed.

    Still open:
    - My refactor step comes after `make check` is green, so I do it when the work item comes back.
    - Criterion 9 (the docs) is the documenter's.
    - `documents.py` at about 590 lines is for a later split, as you noted.
20. factory: started tests as vm.
21. tester: I made the test changes the human allowed in journal 17, as the coder listed them in journal 19.

    1. `tests/guards/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: I added `"factory.shared.adapters.document_examples"` to the set of modules allowed to import `factory.shared.adapters.process`. Nothing else in that module changed, and the test keeps its name.

    2. Three earlier tests failed only on the exact `documents ok` line. Each now checks that its last line matches `documents ok \(\d+(\.\d+)? s\)`, and each keeps its exit-status check:
       - `tests/entry/test_check_documents_guide_files.py::test_the_files_beside_the_index_are_read`, rows `others-ignored` and `utf-8`. Their expected output is now `None`. The test checks the last line against the time line when the expected output is `None`, and the whole output otherwise. The `guide-file-read` row is unchanged.
       - `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`, row `as-it-is`. Its expected output is now `None`, handled the same way. The other rows are unchanged.

       I searched `tests/` for any other test expecting a bare `documents ok` and found none. The run over `tests/entry/test_check_documents*.py`, `tests/entry/test_entry_arguments.py` and `tests/guards/test_operator_guide_files.py` passes.

    3. I moved the shared time-line pattern under the standing leave in CLAUDE.md (*Tests*). Without the move, the two modules above would have been the third and fourth copies of it. `TIME_LINE` now lives in `tests/support/check_documents_support.py`, as the same regex string.
       - `tests/entry/test_check_documents.py` and `tests/entry/test_check_documents_examples.py` (written by this story, journal 11) now import it from there, instead of each holding its own copy.
       - The examples module now calls `re.fullmatch(TIME_LINE, …)` instead of a compiled pattern's `fullmatch`.
       - Every test in both modules keeps its name and checks the same thing.

    Earlier test files I changed: `tests/guards/test_wrapper_search.py`, `tests/entry/test_check_documents_guide_files.py`, `tests/entry/test_check_documents_operator_guide.py`, `tests/entry/test_check_documents.py` and `tests/support/check_documents_support.py`. I also changed this story's own `tests/entry/test_check_documents_examples.py`.

    Files created: none.

    Modules the test run could not import: none.

    Run: `uv run pytest -q` over those files: 49 passed.

    `make lint`: lint: green (0.1 s)

    The criterion-to-test mapping is unchanged from journal 14.

    `lint`: lint: green (0.1 s)
22. factory: started doing as vm.
23. coder: I changed no code this round. The tester's changes (journal 21) made `make check` green on the implementation already committed on the branch: `check: green`, coverage 99.17 %. I ran the smoke test and it prints `1`.

    What I built (from journal 16, committed on the branch):
    - `src/factory/shared/domain/documents.py`:
      - the models `Command`, `Example`, `Skipped` and `Examples`, and the functions `examples(text)` and `matches(expected, actual)`.
      - `matches` is built on `first_difference`, a small set-of-states matcher in which `...` stands for any number of lines and `<placeholder>` for any text in a line.
      - `runs_the_suite(command)` also reads `uv run make check`, `uv run make test` and `uv run pytest`.
    - `src/factory/shared/application/document_examples.py`: the `Fixture` and `ExampleRunner` interfaces.
    - `src/factory/shared/adapters/document_examples.py`: `ProcessExampleRunner(time_limit=60 s)`.
      - Each command runs through `run_process` as `env -i <fixture vars> PATH HOME TZ=UTC LANG=C.UTF-8 sh -c <command>`, with stderr merged.
      - Each document gets one temporary work folder and one home. A fixture is prepared at most once per document.
      - A command past its limit ends the document.
    - `src/factory/hosting/adapters/checkout_fixture.py`: `CheckoutFixture(git: GitCli)`. It calls a new `GitCli.export(ref, folder)` in `src/factory/hosting/adapters/git_cli.py`, which runs `read-tree` into a temporary index, then `checkout-index --all --prefix=`.
    - `src/factory/entry/check_documents.py`: wires the runner and the `checkout` fixture. It prints the example findings and the `not run (<kind>)` lines, and ends with `documents ok (<n.n> s)` (timed with `time.monotonic`) when nothing blocks.

    Main decision: `export` is a `GitCli` method only, not an operation of the `Git` interface, because two tests pin that interface at exactly 22 operations. I rejected building the copy from `show_file` calls, which would start two processes per tracked file.

    Refactor: I reread the diff against `main` and found nothing to rename, simplify or remove.

    Noticed, not touched:
    - `_commands` in `documents.py` fills `Command.expected` by appending to the list of a frozen model while it parses. This works, but a reviewer may prefer building the list first.
    - `check_documents.main` builds `CheckoutFixture(GitCli(root))` every time, even when no block runs. This is harmless because the fixture touches git only when it prepares a folder.
    - `documents.py` is about 690 lines. The human left the split for later (journal 17).
    - Criterion 9 (the docs) is the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 39 known, 4 gone
24. factory: started review as vm.
25. reviewer: Findings:
    1. criterion 8 added: it needs its test. When a command prints fewer lines than expected, `src/factory/shared/adapters/document_examples.py` (`_difference`, `_NOTHING_MORE`) reports `the example printed nothing more`. No criterion names this and no test covers it. Fix: the tester adds a row to `tests/shared/adapters/test_document_examples.py::test_a_command_whose_output_differs_gives_one_finding_and_one_that_matches_none` (for example `echo hi` expecting `hi`, `more`).
    2. criterion 9 added: it needs its test. `src/factory/shared/domain/documents.py` `runs_the_suite` strips a leading `uv run` and treats `pytest` followed only by options as the suite. No row covers `uv run make check`, `uv run make test`, `uv run pytest`, `pytest -q` or `uv run pytest <file>`. Fix: the tester adds these as rows of the two criterion 1 tests in `tests/shared/domain/test_document_examples.py`.
    3. `src/factory/shared/domain/documents.py` `runs_the_suite`: every word after `pytest` that does not start with `-` counts as a file. So `pytest -q 2>&1 | tail -5`, the form CLAUDE.md itself writes, and `pytest -k name` are run, although they run pytest without a file, which the Interface says is skipped as `suite`. Fix: stop reading at the first shell operator or redirection (`|`, `&&`, `;`, `2>&1`, `>`), skip an option's value, and count a word as a file only when it names a test path. Add those rows to the criterion 1 skip test.
    4. `src/factory/shared/domain/documents.py` `_commands`: it builds each `Command`, a frozen model, with `expected=[]` and then fills it with `commands[-1].expected.append(line)`, so a frozen DTO is changed after it is built. Fix: collect each command's lines first, then build the `Command` with its complete `expected`.
    5. `tests/shared/domain/test_document_examples.py:7`, `tests/shared/adapters/test_document_examples.py:15` and `tests/entry/test_check_documents_examples.py:13`: each holds its own `FENCE = "```"`, a third, fourth and fifth copy of the constant in `tests/pipeline/domain/test_documents.py:38`. Fix (tester, standing leave): move `FENCE` to a module in `tests/support/` and import it in all four.
    6. `## Interface`, the line "Tests: ... and an adapter test with the fake containers": this is out of date. The human's answers in journals 4 and 9 (6) settled on real short commands in `tmp_path` and no containers, and that is what was built. Fix: rewrite the line to name `tests/shared/adapters/test_document_examples.py` with real short commands and no containers, plus `tests/hosting/adapters/test_checkout_fixture.py` and `tests/entry/test_check_documents_examples.py`. A reviewer may correct only the Description, so this is left to the coder.

    Notes:
    - The 60-second default limit has no test. `ProcessExampleRunner()` defaults to `EXAMPLE_TIME_LIMIT = timedelta(seconds=60)` in `src/factory/shared/adapters/document_examples.py`, and `_no_end` formats it as `60 s`, so the code does what the Interface says. Missing row: `ProcessExampleRunner()._time_limit`, or a finding text built from the default, equals 60 s.

    Checked and in order: criteria 1 to 7 each have a test that checks what it is named after. Journal 23 shows `make check` green after the coder. The layers and wrappers hold: the new process importer has the human's leave (journal 17), `GitCli.export` goes through `_run` with `check_git_argument`, and a timeout kills the process group (`process.py`). Example findings do not change the exit status, as "until S0004" asks. No suppression markers were added.

    Earlier tests:
    - `tests/entry/test_check_documents.py`: the human's leave, journals 9 (1) and 12 (1).
    - `tests/entry/test_check_documents_guide_files.py`: the human's leave, journal 17 (2).
    - `tests/entry/test_check_documents_operator_guide.py`: the human's leave, journal 17 (2).
    - `tests/guards/test_wrapper_search.py`: the human's leave, journal 17 (1).
    - `tests/support/check_documents_support.py`: the standing leave to move a shared test helper (`TIME_LINE` moved there, the earlier tests unchanged in name and in what they check).
26. factory: started doing as vm.
27. coder: I fixed the two code findings from the review (journal 25) and the Interface line. The remaining findings are test changes, so this goes to the tester. `make check`: check: green (coverage 99.18 %).

    Code changes in `src/factory/shared/domain/documents.py`:
    - Finding 3, `runs_the_suite`:
      - It now reads only up to the first shell operator (`|`, `&`, `;`, `<`, `>`) in the command, through `_first_simple_command`.
      - A word counts as a file only when it names a test path, meaning it holds a `/` or `.py` (`_names_a_test_path`).
      - So `pytest -q 2>&1 | tail -5`, `pytest -k name` and `pytest -q` are now `suite`. `uv run pytest tests/a/test_b.py` and `pytest tests/a/test_b.py::t -q` are still run. I checked those cases by hand.
      - I rejected the reviewer's other suggestion of a table of pytest options that take a value. Once a bare word no longer counts as a file, an option's value (the name after `-k`) is never one, so the table is not needed.
      - The unused `_OPTION_MARK` constant is gone.
    - Finding 4, `_commands`: it finds the `$ ` lines first. It then builds each `Command` with its complete `expected` slice, so no frozen model is changed after it is built.

    Finding 6: in the work item's `## Interface`, I rewrote the "Tests:" line. It now names the four test modules, with the adapter test running real short commands in `tmp_path` with no containers. The Description itself is unchanged.

    For the tester:
    1. Criterion 8: add a row to `tests/shared/adapters/test_document_examples.py::test_a_command_whose_output_differs_gives_one_finding_and_one_that_matches_none`. Example: `echo hi` expecting `hi`, `more`, which gives `<document>:<line>: the example printed nothing more`.
    2. Criterion 9: add rows to the two criterion 1 tests in `tests/shared/domain/test_document_examples.py`.
       - Skipped as `suite`: `uv run make check`, `uv run make test`, `uv run pytest`, `pytest -q`.
       - Run: `uv run pytest <file>`.
    3. Finding 3: add `pytest -q 2>&1 | tail -5` and `pytest -k name` as `suite` rows of the criterion 1 skip test.
    4. Finding 5, under the standing leave: move `FENCE = "```"` into a module in `tests/support/`. Import it in `tests/pipeline/domain/test_documents.py`, `tests/shared/domain/test_document_examples.py`, `tests/shared/adapters/test_document_examples.py` and `tests/entry/test_check_documents_examples.py`.
    5. Optionally, the reviewer's note: a row showing that the default limit of `ProcessExampleRunner()` is 60 s.

    Refactor: I reread the diff and found nothing more to change.

    Noticed, not touched:
    - `runs_the_suite` looks only at the first simple command, so `cd x && pytest` is run, not skipped. Neither the Interface nor the finding covers this case.
    - `documents.py` is still large; the human left the split for later (journal 17).

    The factory left out changes outside the write paths: factory/features/F0053-the-documents-are-checked-against-the-code/in-progress/F0053-S0003-a-documents-marked-examples-are-run-by-the-check.md.
28. factory: started tests as vm.
