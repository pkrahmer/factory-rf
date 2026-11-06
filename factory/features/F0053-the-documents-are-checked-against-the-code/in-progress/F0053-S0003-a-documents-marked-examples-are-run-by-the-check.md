---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 587
comments_read: [6679620269, 6679692361, 6679759183]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-06T07:36:20.672868Z'
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
