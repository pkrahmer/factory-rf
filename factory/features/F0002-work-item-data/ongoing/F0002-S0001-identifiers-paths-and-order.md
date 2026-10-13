---
stage: review
pr: 28
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Identifiers, paths and order

## Assignment (as of log entry 1)

Add to the two pure domain modules that F0001 already created, and that give every work item its identity, its order and its place: the id patterns for stories, acceptances and features, the parsing of work item file names and feature directory names, the branch name of a work item, the folder and file names of the project's `factory/` tree, the path of a work item and of its cost-record sidecar, and the one sort key for work item ids. F0001 built `WorkItemId` and `Name` in `factory.domain.identifiers` and `REMOTE`, `MAIN_BRANCH` and `LABEL_PREFIX` in `factory.domain.paths` (F0001's decision 3); this story imports and keeps them and never defines them again. Plain string order of the ids stays the human's only priority (kept thing 15); the sort key adds the one stated rule that an acceptance sorts after every story of its feature, whatever the slug of the feature or the stories (the rule that F0009's ST6.3 relies on). The names are the glossary's (R3): `backlog`, `in-progress`, `done`, `work-item/<id>`. It covers no acceptance condition of the handover by itself; it keeps kept things 4 (identity of a work item) and 15 (order) and is the base of R13 and R15 in the stories after it. Nothing here touches a file, the clock or a process.

## Interface

`src/factory/domain/identifiers.py` (F0001 created the module with `WorkItemId` and `Name`; this story adds the rest)

```python
FEATURE_ID = r"F\d{4}"
STORY_ID = r"F\d{4}-S\d{4}"
ACCEPTANCE_ID = r"F\d{4}-A\d{4}"
WorkItemId = Annotated[str, StringConstraints(pattern=r"^F\d{4}-[SA]\d{4}$")]  # exists (F0001), unchanged
FeatureId = Annotated[str, StringConstraints(pattern=r"^F\d{4}$")]
Name = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]  # exists (F0001), unchanged

class WorkItemFileName(BaseModel):
    id: WorkItemId
    slug: Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")] | None
        # lower-case segments joined by single hyphens; a segment may start with a digit

class FeatureDirectoryName(BaseModel):
    id: FeatureId
    slug: Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")] | None

def parse_work_item_file_name(name: str) -> WorkItemFileName | None: ...
def parse_feature_directory_name(name: str) -> FeatureDirectoryName | None: ...
def is_acceptance(work_item: WorkItemId) -> bool: ...
def feature_of(work_item: WorkItemId) -> FeatureId: ...
def work_item_order(work_item: WorkItemId) -> tuple[str, int, str]: ...
def branch_name(work_item: WorkItemId) -> str: ...
def work_item_of_branch(branch: str) -> WorkItemId | None: ...
```

`src/factory/domain/paths.py` (F0001 created the module with `MAIN_BRANCH`, `LABEL_PREFIX` and `REMOTE`; this story adds the rest)

```python
REMOTE = "origin"                         # exists (F0001), unchanged
MAIN_BRANCH = "main"                      # exists (F0001), unchanged
FACTORY_DIRECTORY = "factory"
PIPELINE_DEFINITION_FILE = "factory/pipeline.yml"
STORY_FORM_FILE = "factory/story-form.md"
FEATURE_FORM_FILE = "factory/feature-form.md"
FEATURES_DIRECTORY = "factory/features"
FEATURE_FILE_NAME = "feature.md"
LifecycleFolder = Literal["backlog", "in-progress", "done"]
LIFECYCLE_FOLDERS: tuple[LifecycleFolder, ...] = ("backlog", "in-progress", "done")
COST_RECORDS_SUFFIX = ".costs.jsonl"
BRANCH_PREFIX = "work-item/"
LABEL_PREFIX = "stage:"                   # exists (F0001), unchanged

def work_item_path(feature_directory: str, folder: LifecycleFolder, file_name: str) -> str: ...
def cost_records_path(work_item_path: str) -> str: ...
def folder_of(path: str) -> LifecycleFolder | None: ...
```

This story adds to both modules. F0001's five definitions (`WorkItemId`, `Name`, `REMOTE`, `MAIN_BRANCH`, `LABEL_PREFIX`) and their tests in `tests/domain/test_name.py` stay as they are; this story writes its tests in new files.

The rules; each has a criterion below:

- A work item file name is `<id>.md` or `<id>-<slug>.md`, where the id matches `WorkItemId` and the slug is lower-case segments of letters and digits joined by single hyphens (`[a-z0-9]+(-[a-z0-9]+)*`, v1's rule: no leading, trailing or doubled hyphen). A feature directory name is `<id>` or `<id>-<slug>` with the same slug rule. Both parse functions return `None` for any other string and never raise. `WorkItemFileName` and `FeatureDirectoryName` enforce the same slug rule themselves: a slug that breaks it is a `ValidationError`.
- A function that takes a `WorkItemId` (`is_acceptance`, `feature_of`, `work_item_order`, `branch_name`) raises `ValueError` for a string that does not match the pattern. `feature_of("F0002-S0003")` is `"F0002"`.
- `work_item_order(id)` is `(feature id, 0 for a story or 1 for an acceptance, id)`. Sorting ids with it as the key puts every story of a feature, in plain string order of the ids, before the acceptances of that feature, and the features in plain string order. The slug is not part of the id, so it cannot change this order.
- `branch_name(id)` is `BRANCH_PREFIX + id` (`work-item/F0002-S0001`), never the file name. `work_item_of_branch` returns the id for exactly that form and `None` for any other string.
- `work_item_path(feature_directory, folder, file_name)` is `factory/features/<feature_directory>/<folder>/<file_name>`.
- `cost_records_path(path)` replaces the final `.md` of the path with `COST_RECORDS_SUFFIX`, so the sidecar sits beside the work item; a path that does not end in `.md` raises `ValueError`.
- `folder_of(path)` returns the lifecycle folder of a work item path and `None` for anything else. A work item path has exactly the shape `factory/features/<feature directory>/<folder>/<file>` where the directory parses as a feature directory name, the folder is one of `LIFECYCLE_FOLDERS` and the file parses as a work item file name (an acceptance file too).
- Both modules import no module that does I/O and read no clock (`os`, `pathlib`, `subprocess`, `socket`, `datetime`, `time`).

Tests: `tests/domain/test_identifiers.py`, `tests/domain/test_paths.py` (both new). A test that constructs a model with an unknown field does so through a variable typed `type[BaseModel]`, and one that assigns to a frozen field does so with `setattr` (`CLAUDE.md`, Tests).

## Acceptance criteria

1. `WorkItemId` accepts `F0001-S0001` and `F0012-A0003` and refuses `F001-S0001`, `F0001-X0001`, `f0001-s0001`, `F0001-S00001`, `F0001-S0001-slug` and the empty string; `FeatureId` accepts `F0001` and refuses `F001`, `F00001` and `F0001-x`; `Name` accepts `intake`, `smoke-test` and `a1` and refuses the empty string, `1a`, `Intake`, `-a` and `a_b` (checked through `pydantic.TypeAdapter`).
2. `WorkItemFileName` and `FeatureDirectoryName` are frozen and refuse an unknown field with `pydantic.ValidationError`; each accepts the slugs `None`, `x`, `2fa` and `a-b` and refuses the slugs `Bad`, `""`, `a-`, `-a` and `a--b` with `ValidationError`.
3. `parse_work_item_file_name` returns the id and the slug for `F0001-S0001-domain-model.md`, a slug of `None` for `F0001-S0001.md`, a slug of `2fa` for `F0002-S0001-2fa.md` (a slug may start with a digit) and the id `F0001-A0001` for `F0001-A0001-acceptance.md`.
4. `parse_work_item_file_name` returns `None` for `F0001-S0001` (no `.md`), `F0001-S0001-Domain.md` (upper case), `F0001-S0001-.md` (empty slug), `F0001-S0001-a-.md` (trailing hyphen), `F0001-S0001-a--b.md` (doubled hyphen), `F0001-S0001-a_b.md`, `F0001-S001-x.md`, `F0001-S0001-x.md.bak`, `F0001-S0001-x.costs.jsonl` and `.gitkeep`.
5. `parse_feature_directory_name` returns the id and the slug for `F0002-work-item-data`, a slug of `None` for `F0002`, and a slug of `2fa` for `F0002-2fa`; it returns `None` for `f0002-x`, `F002-x`, `F0002-Upper`, `F0002-`, `F0002-a-`, `F0002-a--b` and `F0002-x/y`.
6. `is_acceptance("F0001-A0001")` is true and `is_acceptance("F0001-S0001")` is false; `feature_of("F0002-S0003")` and `feature_of("F0002-A0001")` are `"F0002"`.
7. `is_acceptance`, `feature_of`, `work_item_order` and `branch_name` raise `ValueError` for `F0001`, `F0001-X0001` and the empty string.
8. Sorting the ids parsed from the file names `F0002-A0001.md`, `F0002-S0002-2fa.md`, `F0002-S0001.md` and `F0001-S0010-x.md` with `work_item_order` as the key gives `F0001-S0010`, `F0002-S0001`, `F0002-S0002`, `F0002-A0001`, whereas plain string order puts `F0002-A0001` first of the feature: an acceptance sorts after the stories of its feature whatever the slug.
9. `work_item_order` keeps plain string order inside a kind and across features: `F0001-S0009` sorts before `F0001-S0010`, `F0001-S0010` before `F0002-S0001`, and `F0001-A0001` before `F0002-S0001`.
10. `branch_name("F0002-S0001")` is `work-item/F0002-S0001`; `work_item_of_branch` returns `F0002-S0001` for it and `None` for `main`, `work-item/`, `work-item/F0002`, `work-item/F0002-S0001-slug` and `ticket/F0002-S0001`.
11. The constants of `factory.domain.paths` have exactly the values in the Interface, and `LIFECYCLE_FOLDERS` is `("backlog", "in-progress", "done")` in that order; `FEATURE_ID`, `STORY_ID` and `ACCEPTANCE_ID` of `factory.domain.identifiers` are exactly the patterns in the Interface; the five definitions of F0001 keep their values (`REMOTE` is `"origin"`, `MAIN_BRANCH` is `"main"`, `LABEL_PREFIX` is `"stage:"`, and `WorkItemId` and `Name` accept and refuse what criterion 1 says).
12. `work_item_path("F0002-work-item-data", "in-progress", "F0002-S0001-x.md")` is `factory/features/F0002-work-item-data/in-progress/F0002-S0001-x.md`.
13. `cost_records_path` of `factory/features/F0002-a/done/F0002-S0001-x.md` is `factory/features/F0002-a/done/F0002-S0001-x.costs.jsonl`, and `cost_records_path("factory/features/F0002-a/done/F0002-S0001-x.txt")` raises `ValueError`.
14. `folder_of` returns `backlog`, `in-progress` and `done` for a path in each of the three folders, for a story file and for an acceptance file.
15. `folder_of` returns `None` for a path in a folder named `drafts` or `ongoing` (not a lifecycle folder), one level too deep or too shallow, in a folder that is not a lifecycle folder, outside `factory/features`, in a feature directory that does not parse, and for a sidecar file, a `.gitkeep` and a `README.md` in a lifecycle folder.
16. `factory.domain.identifiers` and `factory.domain.paths` import none of `os`, `pathlib`, `subprocess`, `socket`, `datetime` and `time`, found by parsing the two modules' imports with `ast`.
17. make check stays green.
18. docs: `docs/project-guide.md` lists the spellings of the lifecycle folders, the branch prefix, the feature file and the sidecar suffix, and states the sort rule for acceptances; `docs/decisions.md` records why the acceptance rule is a sort key and not a property of the alphabet.

## Demo

```bash
uv run python -c "
from factory.domain.identifiers import branch_name, parse_work_item_file_name, work_item_order
names = ['F0002-A0001.md', 'F0002-S0002-2fa.md', 'F0002-S0001.md', 'F0001-S0010-x.md']
ids = [parse_work_item_file_name(n).id for n in names]
print(sorted(ids))
print(sorted(ids, key=work_item_order))
print(branch_name('F0002-S0001'))
"
```
Expect: three lines: `['F0001-S0010', 'F0002-A0001', 'F0002-S0001', 'F0002-S0002']`, then `['F0001-S0010', 'F0002-S0001', 'F0002-S0002', 'F0002-A0001']` (the acceptance moved behind its stories), then `work-item/F0002-S0001`.

```bash
uv run python -c "
from factory.domain.paths import cost_records_path, folder_of, work_item_path
path = work_item_path('F0002-work-item-data', 'in-progress', 'F0002-S0001-identifiers-paths-and-order.md')
print(path)
print(cost_records_path(path))
print(folder_of(path), folder_of(cost_records_path(path)), folder_of('factory/features/F0002-x/ongoing/F0002-S0001.md'))
"
```
Expect: three lines: `factory/features/F0002-work-item-data/in-progress/F0002-S0001-identifiers-paths-and-order.md`, then the same path ending in `F0002-S0001-identifiers-paths-and-order.costs.jsonl`, then `in-progress None None` (the sidecar and a folder `ongoing` are not work items).

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: both modules are named with concrete signatures. The constants, patterns, models and functions are listed, and F0001's five definitions are marked as existing and unchanged. The test files are named.
   - Criteria: 18 criteria, each testable by one test function. Every rule has its failing side. Slugs: 2 and 4 to 5. `ValueError` on malformed ids: 7. `None` from `work_item_of_branch`: 10. `cost_records_path` on a non-`.md` path: 13. `folder_of` returning `None`: 15. Criterion 11 pins the constants. Criteria 8 and 9 test the order through sorting, not the tuple value; that is enough, because the order is the behaviour.
   - Demo: both commands are runnable with `uv run python -c`, and each Expect line gives exact output to compare against.
   - Architecture: pure domain modules in `factory.domain`, with no I/O imports, and criterion 16 checks that with `ast`. This matches the layering in CLAUDE.md.
   - Scope: it matches FEATURE.md ("Identifier patterns... plain string order, with an acceptance sorting after the stories") and touches nothing under Out of scope. The acceptance's due order stays with F0009.
3. tester: Wrote red tests for criteria 1–16 in two new files: tests/domain/test_identifiers.py and tests/domain/test_paths.py. tests/domain/test_name.py is unchanged.
   - criterion 1: tests/domain/test_identifiers.py::test_id_and_name_types_accept_only_their_pattern (WorkItemId, FeatureId and Name through TypeAdapter, every listed case)
   - criterion 2: tests/domain/test_identifiers.py::test_name_models_are_frozen_and_refuse_an_unknown_field (assignment through setattr, unknown field through a type[BaseModel] variable) and ::test_name_models_accept_only_hyphen_joined_lower_case_slugs (both models × the nine slugs)
   - criterion 3: tests/domain/test_identifiers.py::test_work_item_file_name_parses_into_id_and_slug
   - criterion 4: tests/domain/test_identifiers.py::test_malformed_work_item_file_name_parses_to_none
   - criterion 5: tests/domain/test_identifiers.py::test_feature_directory_name_parses_into_id_and_slug and ::test_malformed_feature_directory_name_parses_to_none
   - criterion 6: tests/domain/test_identifiers.py::test_kind_and_feature_of_a_work_item_come_from_its_id
   - criterion 7: tests/domain/test_identifiers.py::test_functions_on_a_work_item_id_refuse_a_malformed_id (4 functions × 3 strings)
   - criterion 8: tests/domain/test_identifiers.py::test_acceptance_sorts_after_the_stories_of_its_feature_whatever_the_slug
   - criterion 9: tests/domain/test_identifiers.py::test_work_item_order_keeps_string_order_within_a_kind_and_across_features
   - criterion 10: tests/domain/test_identifiers.py::test_branch_name_is_the_prefix_and_the_id and ::test_branch_that_is_not_a_work_item_branch_has_no_work_item
   - criterion 11: tests/domain/test_paths.py::test_path_constants_have_their_stated_values (including REMOTE, MAIN_BRANCH and LABEL_PREFIX) and tests/domain/test_identifiers.py::test_id_patterns_are_the_stated_regular_expressions. WorkItemId and Name are covered by criterion 1's test.
   - criterion 12: tests/domain/test_paths.py::test_work_item_path_lies_in_the_folder_of_its_feature_directory
   - criterion 13: tests/domain/test_paths.py::test_cost_records_path_sits_beside_the_work_item and ::test_cost_records_path_refuses_a_path_that_is_not_markdown
   - criterion 14: tests/domain/test_paths.py::test_folder_of_a_work_item_path_is_its_lifecycle_folder (3 folders × a story file and an acceptance file)
   - criterion 15: tests/domain/test_paths.py::test_folder_of_a_path_that_is_no_work_item_is_none (drafts, ongoing, one level too deep, one too shallow, an `archive` folder, `docs/features/...`, the feature directory `f0002-x`, a sidecar, `.gitkeep`, README.md)
   - criterion 16: tests/domain/test_paths.py::test_identity_modules_import_no_io_or_clock (uses the existing tests/source_search.py imported_modules/modules, which parse with ast)
   Criteria 17 and 18 are the coder's and the documenter's.
   make test result: 2 collection errors, as intended. The test runner could not import ACCEPTANCE_ID (and the rest of the new names) from factory.domain.identifiers, or BRANCH_PREFIX (and the rest) from factory.domain.paths. make lint is green. Nothing needed interpreting.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: Implemented criteria 1–16. `make check` is green: all tests pass and total coverage is 99.5 %. Commit 917668d.
      - `src/factory/domain/identifiers.py`:
        - adds `FEATURE_ID`, `STORY_ID`, `ACCEPTANCE_ID`, `FeatureId`, a `Slug` type (`[a-z0-9]+(-[a-z0-9]+)*`), and the frozen, extra-forbidding models `WorkItemFileName` and `FeatureDirectoryName`;
        - adds `parse_work_item_file_name` and `parse_feature_directory_name`. They use `re.fullmatch`, so a trailing newline cannot slip through the way it can with `$`. They return None and never raise;
        - adds `is_acceptance`, `feature_of`, `work_item_order` (feature, 0 or 1, id), `branch_name` and `work_item_of_branch`. Each function that takes an id checks it in the private `_checked` and raises `ValueError` if it is malformed;
        - F0001's `WorkItemId` and `Name` are unchanged.
      - `src/factory/domain/paths.py`: adds the constants from the Interface and `work_item_path`, `cost_records_path` (`ValueError` if the path does not end in `.md`) and `folder_of`. `folder_of` checks the exact shape `factory/features/<dir>/<folder>/<file>`, parses the directory and the file, and then accepts only a lifecycle folder. F0001's `REMOTE`, `MAIN_BRANCH` and `LABEL_PREFIX` are unchanged.
      - Main decision: the Interface creates an import cycle. `branch_name` in identifiers needs `BRANCH_PREFIX` from paths, and `folder_of` in paths needs the parsers in identifiers. I made paths depend on identifiers only:
        - `BRANCH_PREFIX = "work-item/"` is now defined in identifiers, with a comment saying why;
        - paths exposes it as `BRANCH_PREFIX = identifiers.BRANCH_PREFIX`, so `from factory.domain.paths import BRANCH_PREFIX` works and has the stated value.
      - Rejected alternatives:
        - a deferred import inside `folder_of` (ruff PLC0415 refuses it);
        - `import X as X` re-export (ruff PLC0414 refuses it);
        - copying the id and slug regexes into paths (duplication).
      - For the reviewer: the spec puts the definition of `BRANCH_PREFIX` in paths; it is in identifiers instead. If the human wants the definition in paths, the cycle has to be broken another way, for example by moving `folder_of`'s parsing into a third domain module.
      - Refactor pass: I read the diff and found nothing to change. One duplication is deliberate: the private `_WORK_ITEM_ID` fragment repeats the body of `WorkItemId`'s pattern. I kept F0001's definition spelled exactly as it was rather than building it from the fragment.
      - Both demo commands print the expected output.
      - Noticed but not touched: nothing.

   `make check`: check: green
