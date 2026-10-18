---
stage: done
pr: 35
blocked: null
comments_seen: 2
round: 0
attempts: 0
---
# The story check command

## Assignment (as of log entry 1)

Give the human the command that checks a story before it is started (kept thing 9: the form is checked by code, and v1's `factory-check-story` was the human's tool for a draft before promotion). The command takes story paths relative to the repository root, checks where each file sits (name, feature directory, the feature file beside it) and the story's form against the project's own `factory/story-form.md`, prints every finding and exits 1 when there is one. The placement rules are a second pure function in `factory.domain.story_form`; the command is the first thing in `factory.entry`, and it reaches the work item reader only through `factory.entry.wiring`, the one module that picks concrete adapters. The console script `factory-check-story` is already declared in `pyproject.toml` (`factory-check-story = "factory.entry.check_story:main"`), so this story writes no packaging; the module also runs as `python -m factory.entry.check_story`. The command is run by the human on a checkout of `main`, where a started story is the human's moved file with no front matter (the state lives on the work item's branch, ST6.1); the command therefore reads a story that has no front matter as a specification and applies the state rules only to a file that carries front matter. `Boundaries` and `build_boundaries` do not exist yet (F0003-S0001 creates `Boundaries`), so the wiring here builds only what this command needs: `build_work_item_reader` stays afterwards as a building block that `build_boundaries` calls, so that later stories add tests and change none of `tests/entry/test_wiring.py`. The story covers no condition of its own; it keeps kept thing 9 and uses SI1.3 (through the section finder) and R13 (through the reader).

## Interface

`src/factory/domain/story_form.py` (adds to the module of F0002-S0006)

```python
def check_story_place(path: str, *, feature_file_exists: bool) -> list[FormFinding]: ...
```

`src/factory/entry/wiring.py`

```python
def build_work_item_reader() -> WorkItemReader: ...
```

`src/factory/entry/check_story.py`

```python
def main(argv: Sequence[str] | None = None, *, root: Path | None = None) -> int: ...
```

The module is also runnable: `python -m factory.entry.check_story <path>...` exits with the status of `main`. `check_story_place` returns findings without a line. `path` is a repository-relative path with `/`. Its rules, with the message of each finding; every rule has a criterion below:

- The path must have exactly the five parts `factory`, `features`, `<feature directory>`, `<folder>`, `<file>`, where the folder is one of `LIFECYCLE_FOLDERS`; else the only finding is `not a work item location: expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md`.
- Otherwise, in this order and each on its own: when the file name is not a story file name (`F0000-S0000.md` or with a slug; an acceptance's name is not one): `the file name "<name>" is not F0000-S0000[-slug].md`; when the feature directory does not parse: `the feature directory "<directory>" is not F0000[-slug]`; when both parse and their feature ids differ: `the story <story id> is in the directory of feature <feature id of the directory>`; when `feature_file_exists` is false: `the feature file feature.md is missing in factory/features/<directory>`.

`main(argv, root=...)` takes the paths from `argv` (default `sys.argv[1:]`), and resolves them and the story form against `root` (default the current directory):

- With no path it prints `usage: factory-check-story <path>...` to standard error and returns 2. When `factory/story-form.md` under `root` cannot be read it prints `cannot read factory/story-form.md: <reason>` to standard error and returns 2. Nothing is printed to standard output in either case.
- For each path in the order given: a path whose place has the finding `not a work item location` is printed with that finding and is not read. Any other file is read as UTF-8 under `root`; when that fails (a file that is not UTF-8 included), `cannot read <path>: <reason>` goes to standard error and `main` returns 2 at once, keeping what it printed before.
- How a file is read. A file in `backlog` is read with `parse_specification`. A file in `in-progress` or `done` is read with `parse` and checked with the folder of its path. When `parse` raises `WorkItemFormatError` with the fault `no front matter`, the file is read again with `parse_specification` and checked with the folder `backlog`. Whether a file has front matter is the reader's rule (F0002-S0003), not a test of the first line. Such a file is a started story as the human moved it, with no state to check: rules 8 and 9 of F0002-S0006 are for the factory's own calls on a branch. Any other `WorkItemFormatError` becomes one finding whose message is its fault, without a line, and the form check is then skipped for that file.
- The findings of a file, in this order: those of `check_story_place` (with `feature_file_exists` true when the file `factory/features/<directory>/feature.md` exists under `root`), then either the fault of the reader or the findings of `check_story_form`.
- A file with no finding prints `<path>: ok`. A finding prints `<path>:<line>: <message>`, or `<path>: <message>` when it has no line; the line is a line of the body. `main` returns 1 when any file had a finding and 0 when every file was ok.

Tests: `tests/domain/test_story_place.py`, `tests/entry/__init__.py` (new), `tests/entry/test_check_story.py`, `tests/entry/test_wiring.py`.

## Acceptance criteria

1. `check_story_place("factory/features/F0002-work-item-data/backlog/F0002-S0001-x.md", feature_file_exists=True)` gives no finding, and the same for the folders `in-progress` and `done` and for a story file name without a slug.
2. A path in a folder named `ongoing`, a path one part too deep or too short, a path outside `factory/features` and a path in a folder that is not a lifecycle folder give the single finding `not a work item location: expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md`, whatever else is wrong with them.
3. A file name that is not a story file name (`F0002-S0001-x.txt`, `.gitkeep`, `F0002-A0001-x.md`, `s0001.md`) gives `the file name "<name>" is not F0000-S0000[-slug].md` with the name.
4. A feature directory such as `work-item-data` or `f0002-x` gives `the feature directory "<directory>" is not F0000[-slug]` with the directory.
5. A story `F0003-S0001-x.md` in the directory `F0002-work-item-data` gives `the story F0003-S0001 is in the directory of feature F0002`, and none when the ids agree.
6. `feature_file_exists=False` gives `the feature file feature.md is missing in factory/features/F0002-work-item-data`, and `True` gives none.
7. A story with a bad file name in a bad directory with no feature file gets the three findings of criteria 3, 4 and 6 in that order.
8. `main([path], root=root)` for a story in `backlog` that has no finding prints `<path>: ok` to standard output and returns 0.
9. `main` for a story with findings prints each as `<path>:<line>: <message>`, or `<path>: <message>` for one without a line, place findings before form findings, and returns 1.
10. `main` with several paths checks every one in the order given, prints the result of each, returns 1 when any has a finding and 0 only when all are ok.
11. `main([], root=root)` prints `usage: factory-check-story <path>...` to standard error, prints nothing to standard output and returns 2.
12. `main([path], root=root)` with no `factory/story-form.md` under `root` prints `cannot read factory/story-form.md: ` followed by a reason to standard error, prints nothing to standard output and returns 2.
13. `main` for a path that has a valid place but no file, and for one whose file is not UTF-8 (the bytes `\xff\xfe`), prints `cannot read <path>: ` followed by a reason to standard error and returns 2, and what it printed for earlier paths stays.
14. A path whose place is `not a work item location` is printed with that finding, is not read (the file need not exist) and gives the status 1.
15. A story in `in-progress` that has front matter is read with `parse`: a front matter with the key `colour` prints the finding `unknown key: colour`, without form findings, and `main` returns 1.
16. A story in `in-progress` and one in `done` that have a valid front matter are checked with the folder of their path: front matter whose `journal` lists two records above a `Journal` section that shows one entry prints `the journal data lists 2 entries but the text shows 1`, and `main` returns 1.
17. A started story as the human moved it, in `in-progress` and in `done`, with a complete form and no front matter, prints `<path>: ok` for each and `main` returns 0: neither `no front matter` nor `the story has no state` is a finding.
18. A story in `backlog` that starts with front matter is read as a specification and gets the finding `a backlog story carries no front matter: stage`.
19. A story in the wrong directory (`F0003-S0001-x.md` in `F0002-work-item-data`) in `in-progress` whose front matter has the key `colour` prints two lines in this order: the finding `the story F0003-S0001 is in the directory of feature F0002`, then `unknown key: colour`, and `main` returns 1.
20. `build_work_item_reader()` returns a `FrontmatterWorkItemReader`, and no module of `factory.entry` other than `factory.entry.wiring` imports from `factory.adapters`, found by parsing the imports with `ast`.
21. Running `python -m factory.entry.check_story` with no argument in a subprocess exits with the status 2 and prints the usage line to standard error.
22. `main()` without arguments takes the paths from `sys.argv[1:]` and resolves them and `factory/story-form.md` against the current directory: with `sys.argv` set to `["factory-check-story", <path>]` and the current directory changed to a `tmp_path` that holds a story form, a feature file and a clean backlog story, it prints `<path>: ok` and returns 0.
23. `main` for a backlog story whose feature directory has no `feature.md` prints `<path>: the feature file feature.md is missing in factory/features/<directory>` and returns 1; once the file exists the same story prints `<path>: ok`.
24. make check stays green.
25. docs: `docs/operator-guide.md` explains how to check a story before starting it with `uv run factory-check-story <path>...` (the form `uv run python -m factory.entry.check_story <path>...` works too), the output, the three exit statuses, which reader a story gets by its folder and by whether it has front matter, and the findings with what to do about each; `docs/project-guide.md` lists the placement rules.

## Demo

```bash
uv run python -c "
import pathlib, tempfile
from factory.entry.check_story import main
root = pathlib.Path(tempfile.mkdtemp())
folder = root / 'factory' / 'features' / 'F0009-demo' / 'backlog'
folder.mkdir(parents=True)
(root / 'factory' / 'story-form.md').write_text('# Form\n\n## Description\n\n## Acceptance criteria\n')
(root / 'factory' / 'features' / 'F0009-demo' / 'feature.md').write_text('# Feature\n')
good = '# Good\n\n## Description\n\nText.\n\n## Acceptance criteria\n\n1. It works.\n2. make check stays green.\n3. docs: none, nothing changes.\n'
(folder / 'F0009-S0001-good.md').write_text(good)
(folder / 'F0009-S0002-bad.md').write_text(good.replace('3. docs: none, nothing changes.', '3. done.'))
print(main(['factory/features/F0009-demo/backlog/F0009-S0001-good.md'], root=root))
print(main(['factory/features/F0009-demo/backlog/F0009-S0002-bad.md'], root=root))
"
```
Expect: four lines: `factory/features/F0009-demo/backlog/F0009-S0001-good.md: ok`, then `0`, then `factory/features/F0009-demo/backlog/F0009-S0002-bad.md:11: the last criterion must start with "docs:"`, then `1`.

```bash
uv run factory-check-story; echo "status $?"
```
Expect: the line `usage: factory-check-story <path>...` (on standard error) and then `status 2`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: 1. The Interface says `main` passes `feature_file_exists` as true when `factory/features/<directory>/feature.md` exists under `root`. No criterion tests `main` on the other side. Criterion 6 tests only `check_story_place` called directly. Criteria 8, 22 and the Demo always have the feature file, so a `main` that always passes `True`, or one that looks in the wrong folder, would pass every test. Proposed addition, before the two closing criteria: "`main` for a backlog story whose feature directory has no `feature.md` prints `<path>: the feature file feature.md is missing in factory/features/<directory>` and returns 1; once the file exists the same story prints `<path>: ok`." I would choose this one. Everything else checks out and I would accept the story once it is added: the Interface is concrete, the other rules have a criterion for the failing side, the Demo is runnable (the line 11 expectation counts correctly), the architecture matches (only wiring imports adapters), and the story is in scope for the feature.
3. human (pull request comment, 2026-10-13): Yes: add your criterion, as you worded it, before the two closing ones: "`main` for a backlog story whose feature directory has no `feature.md` prints `<path>: the feature file feature.md is missing in factory/features/<directory>` and returns 1; once the file exists the same story prints `<path>: ok`." It is the failing side of the Interface's own `feature_file_exists` rule.
4. intake: accepted. Carried in the human's answer (log entry 3): I added criterion 23, worded as the human approved it, before the two closing criteria. They are now 24 (`make check`) and 25 (`docs:`). The meaning of the task is unchanged, so I left the Assignment alone.
   - Interface: `check_story_place`, `build_work_item_reader` and `main` have concrete modules and signatures. Every behaviour stated in the Interface has a criterion.
   - Criteria: each is testable by one test function. Each rule has a criterion for its failing side. The `feature_file_exists` side in `main` is now covered by criterion 23, which was the gap in entry 2.
   - Demo: both blocks are runnable. Each `Expect:` line can be checked against the output.
   - Architecture: only `factory.entry.wiring` imports adapters, and criterion 20 checks that. The placement rules are a pure function in `factory.domain`.
   - Scope: the story is within the feature's scope ("The story form check ... and its command") and touches nothing in "Out of scope".
5. tester: wrote red tests for criteria 1–23, one per criterion. Criterion 20 has two tests, one for each of its parts.
   - criterion 1: tests/domain/test_story_place.py::test_a_story_in_its_place_has_no_finding (backlog, in-progress, done, no slug)
   - criterion 2: tests/domain/test_story_place.py::test_a_path_outside_the_work_item_locations_gives_only_that_finding (ongoing, one part too deep (six parts), one part too short (four), outside `factory`, outside `features`, `drafts`, and a path with everything else wrong too)
   - criterion 3: tests/domain/test_story_place.py::test_a_file_name_that_is_not_a_story_name_is_a_finding
   - criterion 4: tests/domain/test_story_place.py::test_a_feature_directory_that_does_not_parse_is_a_finding
   - criterion 5: tests/domain/test_story_place.py::test_a_story_in_the_directory_of_another_feature_is_a_finding and ::test_a_story_in_the_directory_of_its_own_feature_is_no_finding
   - criterion 6: tests/domain/test_story_place.py::test_a_missing_feature_file_is_a_finding (False and True)
   - criterion 7: tests/domain/test_story_place.py::test_a_bad_name_in_a_bad_directory_without_feature_file_gives_three_findings_in_order
   - criterion 8: tests/entry/test_check_story.py::test_a_clean_backlog_story_prints_ok_and_returns_0
   - criterion 9: tests/entry/test_check_story.py::test_findings_print_with_and_without_a_line_place_before_form
   - criterion 10: tests/entry/test_check_story.py::test_several_paths_are_checked_in_the_order_given (all ok gives 0, one finding gives 1)
   - criterion 11: tests/entry/test_check_story.py::test_no_path_prints_the_usage_and_returns_2
   - criterion 12: tests/entry/test_check_story.py::test_an_unreadable_story_form_prints_the_reason_and_returns_2
   - criterion 13: tests/entry/test_check_story.py::test_an_unreadable_story_prints_the_reason_and_returns_2_at_once (no file, and the bytes `\xff\xfe`). A path after the broken one is not printed, per the Interface's "returns 2 at once".
   - criterion 14: tests/entry/test_check_story.py::test_a_path_outside_the_work_item_locations_is_reported_and_not_read
   - criterion 15: tests/entry/test_check_story.py::test_a_started_story_with_a_bad_front_matter_prints_the_fault_alone. The body also breaks the form, which shows the form check is skipped.
   - criterion 16: tests/entry/test_check_story.py::test_a_started_story_with_front_matter_is_checked_with_its_folder (in-progress, done)
   - criterion 17: tests/entry/test_check_story.py::test_a_started_story_as_the_human_moved_it_is_ok
   - criterion 18: tests/entry/test_check_story.py::test_a_backlog_story_with_front_matter_is_read_as_a_specification
   - criterion 19: tests/entry/test_check_story.py::test_a_place_finding_comes_before_the_fault_of_the_reader
   - criterion 20: tests/entry/test_wiring.py::test_the_work_item_reader_is_the_frontmatter_reader and ::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer (uses `ast` through tests/source_search.py)
   - criterion 21: tests/entry/test_check_story.py::test_the_module_runs_as_a_script_and_prints_the_usage_without_a_path (subprocess with `sys.executable`, `# noqa: S603` as in tests/test_layers.py)
   - criterion 22: tests/entry/test_check_story.py::test_main_without_arguments_reads_argv_and_the_current_directory
   - criterion 23: tests/entry/test_check_story.py::test_the_feature_file_is_looked_for_beside_the_story

   Files created: tests/domain/test_story_place.py, tests/entry/__init__.py (empty, like tests/domain/__init__.py), tests/entry/test_check_story.py, tests/entry/test_wiring.py.

   `make test` fails at collection, on purpose: 3 errors, one per new test module, because `check_story_place` in `factory.domain.story_form`, `factory.entry.check_story` and `factory.entry.wiring` do not exist yet. `make lint` is green. I skipped the type check, as the stage says.

   The test stories use the form `# Story form / ## Description / ## Acceptance criteria / ## Journal`. On a correct story, the last criterion is on body line 11.

   I interpreted no criterion beyond the Interface's own wording, so I have no questions.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
6. coder: I built the story check command, and the tests for criteria 1–23 now pass. `make check` is green with 99.64 % coverage. Both Demo blocks give the expected output: `ok`/`0`, the `:11:` finding/`1`, and the usage line with status 2.
      - `src/factory/domain/story_form.py`:
        - `check_story_place(path, *, feature_file_exists)` applies the placement rules in the Interface's order.
        - A story file name is a work item file name from `parse_work_item_file_name` whose id is not an acceptance (`is_acceptance`). The feature-id comparison uses `feature_of`.
        - The location message is built from `FEATURES_DIRECTORY` and `LIFECYCLE_FOLDERS`, so the folder names are written in only one place.
        - New public helper: `lifecycle_folder_of_location(path) -> LifecycleFolder | None`. It returns the folder of a path that sits in a work item location, whatever the file and directory names are.
      - `src/factory/entry/wiring.py`: `build_work_item_reader()` returns a `FrontmatterWorkItemReader`. It is the only module in the entry layer that imports from adapters.
      - `src/factory/entry/check_story.py`:
        - `main(argv, *, root)`. A path outside a work item location gets only that finding and is not read.
        - Otherwise the place findings come first, then either the reader's fault or the form findings.
        - A backlog story is read with `parse_specification`.
        - A started story is read with `parse`. When that fails with the fault `no front matter`, the file is read again with `parse_specification` and checked as `backlog` (in `_read_started`).
        - A file that cannot be read (OS error or not UTF-8) raises a private `_UnreadableError`. `main` catches it and prints it to standard error with status 2; output already printed for earlier paths stays. The same path covers an unreadable `factory/story-form.md`, which is read before anything is printed.
        - The module runs with `python -m`.
      - Main design decision: `main` decides "not a work item location" with the domain helper `lifecycle_folder_of_location`, which also gives the folder used to pick the reader.
        - Rejected: comparing the message of `check_story_place`'s finding (fragile).
        - Rejected: reusing `paths.folder_of`. It returns None for bad file or directory names, which this command has to report as findings and then still read.
        - This adds one public function beyond the Interface. The reviewer may judge whether it should be private.
      - Commits:
        - feat: `ticket F0002-S0008: feat(entry): the story check command and its placement rules`
        - refactor: `ticket F0002-S0008: refactor(entry): read a started story in its own function` (moved the nested try into `_read_started`, with a small frozen `_Read` model for the document and its folder)
      - Noticed, not touched:
        - The fault text `no front matter` is a literal in the adapter (`work_item_markdown.py`) and is now matched as a literal in `check_story.py` too. A shared constant in `factory.domain.errors` would be cleaner, but that is beyond this ticket.
        - The `if __name__ == "__main__"` line is not covered, because criterion 21 runs it only in a subprocess.

   `make check`: check: green
7. reviewer: no findings.
      - Acceptance criteria: criteria 1–23 each have a test named after them, and each test checks what its criterion says. The coder's entry reports `make check` green.
        - The five-part rule is tested on both sides: four and six parts are refused, five are accepted.
        - Criterion 2 covers `ongoing`, `drafts`, outside `factory` and outside `features`, plus one path where everything else is wrong too.
        - Criterion 13 covers a missing file and the bytes `\xff\xfe`. It also checks that earlier output stays and that later paths are not printed ("at once").
        - Criterion 15 gives a broken body, so it shows the form check is skipped.
        - Criterion 23 covers the feature file in `main` on both sides.
        - Criterion 20 parses the imports with `ast` and also checks that `factory.entry.check_story` exists, so the test cannot pass with an empty set.
      - Architecture:
        - `check_story_place` and `lifecycle_folder_of_location` are pure functions in `factory.domain.story_form`.
        - `factory.entry.check_story` imports only from domain, from application (the `WorkItemReader` interface) and from `factory.entry.wiring`. `wiring` is the only entry module that imports from adapters.
        - No `dict[str, Any]` crosses a function boundary. The private `_Read` is a frozen Pydantic model.
      - Security:
        - No string-built shell or SQL. The test's subprocess uses `sys.executable` with fixed arguments.
        - The test's `# noqa: S603` has its reason beside it and follows the precedent in `tests/test_layers.py`. There is no `nosec`, `nosemgrep` or baseline entry.
        - Errors that reach the user are `cannot read <path>: <reason>`, as the Interface specifies.
      - Quality:
        - Names and docstrings are in place, and the one comment explains why (`_read_started`).
        - Messages are built from the `paths` constants and not repeated as literals.
      - Judged, not findings:
        1. `lifecycle_folder_of_location` (`src/factory/domain/story_form.py`) is a public function beyond the Interface. It is imported across modules, so it has to be public.
           - It overlaps in part with `paths.folder_of`. But `folder_of` also rejects bad names, which this command must report and still read, so `folder_of` does not already cover it. I accept the coder's choice.
        2. The fault text `"no front matter"` appears as a literal both in `src/factory/entry/check_story.py:27` and in `src/factory/adapters/work_item_markdown.py:111`. The Interface specifies this fault text, and the criterion 17 test and the adapter's own test would both catch a change on either side.
           - The shared constant in `factory.domain.errors` that the coder proposed can be a later story. It is not needed here.
      - Ticket hygiene:
        - The coder's entry states the main decision: the location helper, and why comparing the message and reusing `folder_of` were rejected.
        - The Assignment matches what was built.
        - The docs criterion (25) still describes what the operator and the agents need to know.
8. documenter: no findings; `make check` green.
   - Changed `docs/operator-guide.md`: new section "Checking a story before it starts". It gives the command (both forms), the output format, the three exit statuses, which reader a story gets by folder and by front matter, and a table of findings with what to do about each. The intro no longer says there is no command to run.
   - Changed `docs/project-guide.md`: new subsections "Where a story sits" (the five placement rules, `check_story_place`, `lifecycle_folder_of_location`) and "The check command" (wiring, the two readers, the `no front matter` fallback), placed after the form check.
   - Changed `README.md`: replaced "nothing to run yet" with the command and added it to the list of what is built.
   - I ran the command by hand: a story missing a section gives the finding and status 1, and no argument gives the usage line and status 2.
   - Cross-read and found current: the form-check section and the reader's fault table in `project-guide.md`, `decisions.md`, and the rest of the operator guide.
   - The code matches the Interface. I saw nothing stale that I left untouched.

   `make check`: check: green
9. demo: no findings. I ran both Demo commands from the repository root exactly as written, and both meet their `Expect:` lines.

   Command 1 (the `uv run python -c` script: a clean backlog story and one whose last criterion is `3. done.`):
   ```
   factory/features/F0009-demo/backlog/F0009-S0001-good.md: ok
   0
   factory/features/F0009-demo/backlog/F0009-S0002-bad.md:11: the last criterion must start with "docs:"
   1
   ```
   Met: the output is the four expected lines, in order.

   Command 2 (`uv run factory-check-story; echo "status $?"`):
   ```
   usage: factory-check-story <path>...
   status 2
   ```
   Met. I ran it a second time with standard error discarded (`2>/dev/null`). Only `status 2` was left, so the usage line goes to standard error and nothing goes to standard output (criterion 11).

   Criteria check:
   - Nothing in the demo contradicts any acceptance criterion.
   - Command 1 shows criterion 8 (`<path>: ok`, return 0) and criterion 9 (`<path>:<line>: <message>`, return 1, the line counted in the body).
   - Command 2 shows criteria 11 and 21 through the console script that `pyproject.toml` already declares.
   - I did not exercise the other criteria here. Tests cover them, as the tester's and the reviewer's entries record.
10. done (pull request merged); cost: 7 runs, 7.2 min, 58 turns, 173k tokens in (1246k more from cache), 32k out, $2.00
