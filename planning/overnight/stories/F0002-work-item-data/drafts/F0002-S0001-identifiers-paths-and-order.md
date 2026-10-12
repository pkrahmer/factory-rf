# Identifiers, paths and order

## Assignment (as of log entry 1)

Create the two pure domain modules that give every work item its identity, its order and its place: the id patterns for stories, acceptances and features, the parsing of work item file names and feature directory names, the branch name of a work item, the folder and file names of the project's `factory/` tree, the path of a work item and of its cost-record sidecar, and the one sort key for work item ids. Plain string order of the ids stays the human's only priority (kept thing 15); the sort key adds the one stated rule that an acceptance sorts after every story of its feature, whatever the slug of the feature or the stories (the rule that F0009's ST6.3 relies on). The names are the glossary's (R3): `backlog`, `in-progress`, `done`, `work-item/<id>`. It covers no acceptance condition of the handover by itself; it keeps kept things 4 (identity of a work item) and 15 (order) and is the base of R13 and R15 in the stories after it. Nothing here touches a file, the clock or a process.

## Interface

`src/factory/domain/identifiers.py`

```python
FEATURE_ID = r"F\d{4}"
STORY_ID = r"F\d{4}-S\d{4}"
ACCEPTANCE_ID = r"F\d{4}-A\d{4}"
WorkItemId = Annotated[str, StringConstraints(pattern=r"^F\d{4}-[SA]\d{4}$")]
FeatureId = Annotated[str, StringConstraints(pattern=r"^F\d{4}$")]
Name = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]  # stage, role and instance names

class WorkItemFileName(BaseModel):
    id: WorkItemId
    slug: str | None                      # "[a-z0-9][a-z0-9-]*"; may start with a digit

class FeatureDirectoryName(BaseModel):
    id: FeatureId
    slug: str | None

def parse_work_item_file_name(name: str) -> WorkItemFileName | None: ...
def parse_feature_directory_name(name: str) -> FeatureDirectoryName | None: ...
def is_acceptance(work_item: WorkItemId) -> bool: ...
def feature_of(work_item: WorkItemId) -> FeatureId: ...
def work_item_order(work_item: WorkItemId) -> tuple[str, int, str]: ...
def branch_name(work_item: WorkItemId) -> str: ...
def work_item_of_branch(branch: str) -> WorkItemId | None: ...
```

`src/factory/domain/paths.py`

```python
REMOTE = "origin"
MAIN_BRANCH = "main"
FACTORY_DIRECTORY = "factory"
PIPELINE_DEFINITION_FILE = "factory/pipeline.yml"
STORY_FORM_FILE = "factory/story-form.md"
FEATURE_FORM_FILE = "factory/feature-form.md"
FEATURES_DIRECTORY = "factory/features"
FEATURE_FILE_NAME = "feature.md"
LifecycleFolder = Literal["backlog", "in-progress", "done"]
LIFECYCLE_FOLDERS: tuple[LifecycleFolder, ...] = ("backlog", "in-progress", "done")
V1_LIFECYCLE_FOLDERS = ("drafts", "ongoing")
COST_RECORDS_SUFFIX = ".costs.jsonl"
BRANCH_PREFIX = "work-item/"
LABEL_PREFIX = "stage:"

def work_item_path(feature_directory: str, folder: LifecycleFolder, file_name: str) -> str: ...
def cost_records_path(work_item_path: str) -> str: ...
def folder_of(path: str) -> LifecycleFolder | None: ...
```

The rules; each has a criterion below:

- A work item file name is `<id>.md` or `<id>-<slug>.md`, where the id matches `WorkItemId` and the slug matches `[a-z0-9][a-z0-9-]*`. A feature directory name is `<id>` or `<id>-<slug>` with the same slug rule. Both parse functions return `None` for any other string and never raise.
- A function that takes a `WorkItemId` (`is_acceptance`, `feature_of`, `work_item_order`, `branch_name`) raises `ValueError` for a string that does not match the pattern. `feature_of("F0002-S0003")` is `"F0002"`.
- `work_item_order(id)` is `(feature id, 0 for a story or 1 for an acceptance, id)`. Sorting ids with it as the key puts every story of a feature, in plain string order of the ids, before the acceptances of that feature, and the features in plain string order. The slug is not part of the id, so it cannot change this order.
- `branch_name(id)` is `BRANCH_PREFIX + id` (`work-item/F0002-S0001`), never the file name. `work_item_of_branch` returns the id for exactly that form and `None` for any other string.
- `work_item_path(feature_directory, folder, file_name)` is `factory/features/<feature_directory>/<folder>/<file_name>`.
- `cost_records_path(path)` replaces the final `.md` of the path with `COST_RECORDS_SUFFIX`, so the sidecar sits beside the work item; a path that does not end in `.md` raises `ValueError`.
- `folder_of(path)` returns the lifecycle folder of a work item path and `None` for anything else. A work item path has exactly the shape `factory/features/<feature directory>/<folder>/<file>` where the directory parses as a feature directory name, the folder is one of `LIFECYCLE_FOLDERS` and the file parses as a work item file name (an acceptance file too).
- Both modules import no module that does I/O and read no clock (`os`, `pathlib`, `subprocess`, `socket`, `datetime`, `time`).

Tests: `tests/domain/test_identifiers.py`, `tests/domain/test_paths.py`.

## Acceptance criteria

1. `WorkItemId` accepts `F0001-S0001` and `F0012-A0003` and refuses `F001-S0001`, `F0001-X0001`, `f0001-s0001`, `F0001-S00001`, `F0001-S0001-slug` and the empty string; `FeatureId` accepts `F0001` and refuses `F001`, `F00001` and `F0001-x`; `Name` accepts `intake`, `smoke-test` and `a1` and refuses the empty string, `1a`, `Intake`, `-a` and `a_b` (checked through `pydantic.TypeAdapter`).
2. `WorkItemFileName` and `FeatureDirectoryName` are frozen and refuse an unknown field with `pydantic.ValidationError`.
3. `parse_work_item_file_name` returns the id and the slug for `F0001-S0001-domain-model.md`, a slug of `None` for `F0001-S0001.md`, a slug of `2fa` for `F0002-S0001-2fa.md` (a slug may start with a digit) and the id `F0001-A0001` for `F0001-A0001-acceptance.md`.
4. `parse_work_item_file_name` returns `None` for `F0001-S0001` (no `.md`), `F0001-S0001-Domain.md` (upper case), `F0001-S0001-.md` (empty slug), `F0001-S0001-a_b.md`, `F0001-S001-x.md`, `F0001-S0001-x.md.bak`, `F0001-S0001-x.costs.jsonl` and `.gitkeep`.
5. `parse_feature_directory_name` returns the id and the slug for `F0002-work-item-data`, a slug of `None` for `F0002`, and a slug of `2fa` for `F0002-2fa`; it returns `None` for `f0002-x`, `F002-x`, `F0002-Upper`, `F0002-` and `F0002-x/y`.
6. `is_acceptance("F0001-A0001")` is true and `is_acceptance("F0001-S0001")` is false; `feature_of("F0002-S0003")` and `feature_of("F0002-A0001")` are `"F0002"`.
7. `is_acceptance`, `feature_of`, `work_item_order` and `branch_name` raise `ValueError` for `F0001`, `F0001-X0001` and the empty string.
8. Sorting the ids parsed from the file names `F0002-A0001.md`, `F0002-S0002-2fa.md`, `F0002-S0001.md` and `F0001-S0010-x.md` with `work_item_order` as the key gives `F0001-S0010`, `F0002-S0001`, `F0002-S0002`, `F0002-A0001`, whereas plain string order puts `F0002-A0001` first of the feature: an acceptance sorts after the stories of its feature whatever the slug.
9. `work_item_order` keeps plain string order inside a kind and across features: `F0001-S0009` sorts before `F0001-S0010`, `F0001-S0010` before `F0002-S0001`, and `F0001-A0001` before `F0002-S0001`.
10. `branch_name("F0002-S0001")` is `work-item/F0002-S0001`; `work_item_of_branch` returns `F0002-S0001` for it and `None` for `main`, `work-item/`, `work-item/F0002`, `work-item/F0002-S0001-slug` and `ticket/F0002-S0001`.
11. The constants of `factory.domain.paths` have exactly the values in the Interface, and `LIFECYCLE_FOLDERS` is `("backlog", "in-progress", "done")` in that order.
12. `work_item_path("F0002-work-item-data", "in-progress", "F0002-S0001-x.md")` is `factory/features/F0002-work-item-data/in-progress/F0002-S0001-x.md`.
13. `cost_records_path` of `factory/features/F0002-a/done/F0002-S0001-x.md` is `factory/features/F0002-a/done/F0002-S0001-x.costs.jsonl`, and `cost_records_path("factory/features/F0002-a/done/F0002-S0001-x.txt")` raises `ValueError`.
14. `folder_of` returns `backlog`, `in-progress` and `done` for a path in each of the three folders, for a story file and for an acceptance file.
15. `folder_of` returns `None` for a path in v1's `drafts` or `ongoing` folder, one level too deep or too shallow, in a folder that is not a lifecycle folder, outside `factory/features`, in a feature directory that does not parse, and for a sidecar file, a `.gitkeep` and a `README.md` in a lifecycle folder.
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
Expect: three lines: `factory/features/F0002-work-item-data/in-progress/F0002-S0001-identifiers-paths-and-order.md`, then the same path ending in `F0002-S0001-identifiers-paths-and-order.costs.jsonl`, then `in-progress None None` (the sidecar and v1's `ongoing` folder are not work items).

## Log (append only)

1. 2026-10-12 human: created.
