---
stage: ready
pr: 35
blocked: asked
comments_seen: 1
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
23. make check stays green.
24. docs: `docs/operator-guide.md` explains how to check a story before starting it with `uv run factory-check-story <path>...` (the form `uv run python -m factory.entry.check_story <path>...` works too), the output, the three exit statuses, which reader a story gets by its folder and by whether it has front matter, and the findings with what to do about each; `docs/project-guide.md` lists the placement rules.

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
