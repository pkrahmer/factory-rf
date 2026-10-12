# The story check command

## Assignment (as of log entry 1)

Give the human the command that checks a story before it is started (kept thing 9: the form is checked by code, and v1's `factory-check-story` was the human's tool for a draft before promotion). The command takes story paths relative to the repository root, checks where each file sits (name, feature directory, the feature file beside it) and the story's form against the project's own `factory/story-form.md`, prints every finding and exits 1 when there is one. The placement rules are a second pure function in `factory.domain.story_form`; the command is the first thing in `factory.entry`, and it reaches the work item reader only through `factory.entry.wiring`, the one module that picks concrete adapters. The console script entry `factory-check-story` belongs in `pyproject.toml`, which is outside every write path, so the human adds it (`factory-check-story = "factory.entry.check_story:main"`); until then the command runs as `uv run python -m factory.entry.check_story`. `Boundaries` and `build_boundaries` do not exist yet (F0003-S0001 creates `Boundaries`), so the wiring here builds only what this command needs. The story covers no condition of its own; it keeps kept thing 9 and uses SI1.3 (through the section finder) and R13 (through the reader).

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
- For each path in the order given: a path whose place has the finding `not a work item location` is printed with that finding and is not read. Any other file is read as UTF-8 under `root`; when that fails, `cannot read <path>: <reason>` goes to standard error and `main` returns 2 at once, keeping what it printed before. A file in `backlog` is read with `parse_specification` and any other with `parse`; a `WorkItemFormatError` becomes one finding whose message is its fault, and the form check is then skipped for that file. Otherwise the findings are those of `check_story_place` (with `feature_file_exists` true when the file `factory/features/<directory>/feature.md` exists under `root`) followed by those of `check_story_form` for the folder of the path.
- A file with no finding prints `<path>: ok`. A finding prints `<path>:<line>: <message>`, or `<path>: <message>` when it has no line; the line is a line of the body. `main` returns 1 when any file had a finding and 0 when every file was ok.

Tests: `tests/domain/test_story_place.py`, `tests/entry/test_check_story.py`, `tests/entry/test_wiring.py`.

## Acceptance criteria

1. `check_story_place("factory/features/F0002-work-item-data/backlog/F0002-S0001-x.md", feature_file_exists=True)` gives no finding, and the same for the folders `in-progress` and `done` and for a story file name without a slug.
2. A path in v1's `ongoing` folder, a path one part too deep or too short, a path outside `factory/features` and a path in a folder that is not a lifecycle folder give the single finding `not a work item location: expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md`, whatever else is wrong with them.
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
13. `main` for a path that has a valid place but no file prints `cannot read <path>: ` followed by a reason to standard error and returns 2, and what it printed for earlier paths stays.
14. A path whose place is `not a work item location` is printed with that finding, is not read (the file need not exist) and gives the status 1.
15. A story in `in-progress` is read with `parse`: a front matter with the key `comments_seen` prints the finding `unknown key: comments_seen`, without form findings, and `main` returns 1.
16. A story in `backlog` that starts with front matter is read as a specification and gets the finding `a backlog story carries no front matter: stage`.
17. `build_work_item_reader()` returns a `FrontmatterWorkItemReader`, and no module of `factory.entry` other than `factory.entry.wiring` imports from `factory.adapters`, found by parsing the imports with `ast`.
18. Running `python -m factory.entry.check_story` with no argument in a subprocess exits with the status 2 and prints the usage line to standard error.
19. make check stays green.
20. docs: `docs/operator-guide.md` explains how to check a story before starting it with `uv run python -m factory.entry.check_story <path>`, the output, the three exit statuses and the findings with what to do about each; `docs/project-guide.md` lists the placement rules and says that the console script is added in `pyproject.toml` by the human.

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
uv run python -m factory.entry.check_story; echo "status $?"
```
Expect: the line `usage: factory-check-story <path>...` (on standard error) and then `status 2`.

## Log (append only)

1. 2026-10-12 human: created.
