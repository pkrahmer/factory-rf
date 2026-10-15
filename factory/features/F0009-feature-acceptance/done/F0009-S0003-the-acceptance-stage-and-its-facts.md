---
stage: done
pr: 105
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# The acceptance stage and the acceptance reviewer's facts

## Assignment (as of log entry 1)

Open a due acceptance and give the acceptance reviewer what it needs. A due acceptance is opened by pushing a branch `work-item/F0001-A0001` that holds one new file, the report's head: the state (stage = the pipeline definition's `acceptance_stage`, `stories` = the archived stories, counters at their initial values), the title taken from the feature file (`# Acceptance of <feature title>`) and an empty `## Journal` section. That is all the opening does: the claim, the draft pull request and the agent run belong to the stage protocol, which meets the acceptance as an ordinary work item at its stage, read from its branch (S0008 makes the watcher see it, S0009 runs it). The reviewer's prompt gets three facts computed by code, not by the agent: the archived stories, the next free story number and the cost of the stories, read from the cost records of the archived stories; this story builds them and `acceptance_prompt`, and S0009 has the stage protocol append them. The reviewer may write only its report and new stories in the feature's backlog: that is the role's write paths in the pipeline definition, expanded by F0004's `WritePathService` as for any work item, and this story shows it for an acceptance. Each acceptance has its own report file and so its own cost line, which counts only its own records (GH4.4), shown with F0005's `BillService`. Covers GH4.4; keeps kept thing 19 (the acceptance judges the whole and proposes stories that only the human starts), kept thing 2 (proposed stories only as backlog files) and kept thing 20 (each acceptance costed). The factory opens the acceptance without a `created` entry of a human: its journal starts with the stage protocol's `started` entry. The units here are `acceptance_prompt` and the service that opens and reads. `AcceptanceDueHandler` is registered for `acceptance_due` in `factory.entry.wiring.build_handlers` by S0010, which also takes the kind out of `NOT_YET_HANDLED`. Criteria 16 to 18 pass at once against code that F0004 and F0005 built; they show that the reviewer's write paths and the own cost line work for an acceptance's file and fail the day either changes.

## Interface

`src/factory/domain/acceptance.py` (grown)

```python
class AcceptanceFacts(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    archived: list[WorkItemId]
    next_story: WorkItemId
    cost_line: str

    def lines(self) -> list[str]: ...

def acceptance_facts(files: FeatureFiles, cost_line: str) -> AcceptanceFacts: ...
def acceptance_prompt(base: str, facts: AcceptanceFacts) -> str: ...
def acceptance_head(feature_title: str, stage: str, stories: Sequence[WorkItemId]) -> WorkItemDocument: ...
```

`src/factory/application/acceptance.py` (new)

```python
class OpenedAcceptance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WorkItemId
    branch: str
    path: str
    commit: CommitId

class AcceptanceService:
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def open(self, feature: FeatureId) -> OpenedAcceptance: ...
    def facts(self, feature: FeatureId) -> AcceptanceFacts: ...

class AcceptanceDueHandler(Handler):      # Handler: factory.application.dispatcher (F0006-S0003)
    def __init__(self, boundaries: Boundaries, definition: PipelineDefinition) -> None: ...
    def handle(self, event: Event) -> None: ...
```

`CommitId` is in `factory.domain.git`, `CannotHandle`, `WorkItemFormatError` and `PushFailed` in `factory.domain.errors`, `JOURNAL` in `factory.domain.sections`.

Rules:

- `acceptance_facts(files, cost_line)`: `archived` is `story_file_ids(files.done)`; `next_story` is `"<feature>-S<n>"` with `n` the highest story number among the story files of `backlog`, `in_progress` and `done`, plus one, written with four digits; with no story file it is number 1; when the highest number is 9999 it raises `ValueError`. `.gitkeep`, notes and an acceptance's report file do not count.
- `AcceptanceFacts.next_story` holds a story id only: a validator refuses an acceptance id with a `ValidationError`.
- `AcceptanceFacts.lines()` is exactly three lines: `Archived stories: ` followed by the ids joined by `, `; `Next free story number: ` and the id; `Cost of the stories: ` and `cost_line`.
- `acceptance_prompt(base, facts)` is `base`, an empty line, then the three lines, joined with `\n`.
- `acceptance_head(feature_title, stage, stories)` returns a `WorkItemDocument` whose state is an `AcceptanceState` with `initial_state(stage)`'s values (every counter 0, no claim, no pull request, empty journal), `stories` as given and `outcome` `None`, and whose body is exactly `# Acceptance of <feature_title>`, an empty line, `## Journal` and a final newline. The heading is built from `JOURNAL` (`f"## {JOURNAL}"`), never written as a literal: F0005-S0009's search test (`tests/test_no_journal_reading.py`) allows the literal `Journal` only in `factory.domain.sections` and `JOURNAL` only in a short list of modules. This story adds `"factory.domain.acceptance"` to the set `ALLOWED["JOURNAL"]` of F0005-S0009's `tests/test_no_journal_reading.py`, with the human's leave (the feature's decision 22), and changes nothing else of that file (S0004 adds it to `ALLOWED["entry_text"]`).
- `AcceptanceService.__init__` raises `ValueError` when `definition.acceptance_stage` is `None`; the handler below builds the service inside `handle`, after its own check.
- `open(feature)`: reads `AcceptanceReader.read()` (S0002); when the feature's status is not `due` it raises `CannotHandle(kind="acceptance_due", reason="feature <feature> is <status>, not due")` and changes nothing. The title is the first `# ` title of `f"{FEATURES_DIRECTORY}/{directory}/{FEATURE_FILE_NAME}"` at `origin/main`, with `directory` the directory's name that `read()` gives; a missing file or one without a title raises `WorkItemFormatError` with `path` set to that file, before anything is written. The id is the feature's `next_acceptance`; the path is `work_item_path(directory, "in-progress", acceptance_file_name(id))` (the directory's name, as F0002-S0001's function takes it). It runs `Git.checkout(branch, start_point="origin/main")`, creates the report's folder when missing, writes `acceptance_head(...)` with the work item writer, commits and pushes `branch`; a push whose outcome is not `pushed` raises `PushFailed`. It opens no pull request, writes no claim and runs no agent.
- `facts(feature)`: reads the feature at `origin/main` only. The feature's files and directory are those of `AcceptanceReader.feature_files` and `read()`; the cost line is `cost_line(bill(records))` over the cost records of the archived stories only, each read from `cost_records_path(work_item_path(directory, "done", <file name>))` at `origin/main` with `Git.show_file` and the cost record reader; a story without a sidecar file adds no record. A feature with no directory on `origin/main` raises `ValueError` naming the feature.
- The reviewer's write paths need no method of this story: `WritePathService(boundaries).at(stage_start, <report path>)` (F0004-S0003) gives the `write_paths` of the role of `definition.acceptance_stage`, with `{work_item}` the report and `{feature}` the feature directory two levels above it.
- An acceptance's own cost line is `BillService(boundaries.git, boundaries.cost_reader).for_work_item(<acceptance id>).line` (F0005-S0009): the report's sidecar is `cost_records_path(<report path>)`, so only its own records count.
- `AcceptanceDueHandler.__init__` stores its arguments and never raises. `handle(event)` raises, in this order, `CannotHandle(kind=<the event's kind>, reason="not an acceptance_due event")` for another kind; `CannotHandle(kind="acceptance_due", reason="no feature")` for an `acceptance_due` event without a feature; `CannotHandle(kind="acceptance_due", reason="no acceptance stage")` when `definition.acceptance_stage` is `None`. Otherwise it opens `event.feature` with `AcceptanceService(boundaries, definition).open`.

Tests: `tests/domain/test_acceptance_facts.py`, `tests/application/test_acceptance_service.py`, `tests/application/test_acceptance_due_handler.py`; the `remote`, `checkout`, `human`, `kill_points` and `boundaries` fixtures, with the pipeline definition of the fixture (`RuamelPipelineDefinitionReader().parse(PIPELINE_YAML)`). The fixture's feature `F0001` has a backlog story, so it is `incomplete`; a test that opens an acceptance pushes a feature `F0002-todo` of its own with `human.push_file("main", ...)`: its `feature.md` (`# Todo service`), story files under `done/`, and nothing under `backlog/` or `in-progress/`. Criteria 16 and 17 claim the opened acceptance with `ClaimService(boundaries, "factory-1", definition).claim(branch, path, document, "acceptance")`, which returns the `StageStart`. The closed-model test builds the models through a variable typed `type[BaseModel]` and assigns with `setattr`, the field's name in a variable. `Event.model_construct` builds the `acceptance_due` event without a feature in criterion 20, since `Event` itself refuses it.

## Acceptance criteria

1. `acceptance_facts` for `done = [F0002-S0001-a.md, F0002-S0002-b.md, F0002-S0004-d.md]`, `backlog = [F0002-S0006-x.md, .gitkeep]` gives `archived == ["F0002-S0001", "F0002-S0002", "F0002-S0004"]` and `next_story == "F0002-S0007"`.
2. `next_story` is written with four digits, also across a power of ten: the highest story number 9 gives `F0002-S0010`; a story file in `in_progress` counts; an acceptance's report file in `in_progress` does not.
3. `next_story` for the highest number 9998 is `F0002-S9999`, and for the highest number 9999 `acceptance_facts` raises `ValueError`.
4. `AcceptanceFacts.lines()` is exactly the three lines `Archived stories: F0002-S0001, F0002-S0002, F0002-S0004`, `Next free story number: F0002-S0007` and `Cost of the stories: <cost_line>` for the facts of criterion 1.
5. `acceptance_prompt("Judge the feature.", facts)` is `"Judge the feature."`, an empty line and the three lines, joined with newlines.
6. `acceptance_head("Todo service", "acceptance", ["F0001-S0001"])` has an `AcceptanceState` with stage `acceptance`, `stories == ["F0001-S0001"]`, `outcome is None`, every counter 0, no claim, no pull request and an empty journal, and the body `"# Acceptance of Todo service\n\n## Journal\n"`.
7. `AcceptanceService(boundaries, definition)` raises `ValueError` when `definition.acceptance_stage` is `None`.
8. `open("F0002")` for a due feature pushes the branch `work-item/F0002-A0001` and returns an `OpenedAcceptance` with that id and branch, the path `factory/features/F0002-todo/in-progress/F0002-A0001-acceptance.md` and the pushed commit; the report at that path on `origin/work-item/F0002-A0001` is `acceptance_head("Todo service", "acceptance", <the archived stories>)` as the writer renders it.
9. `open` adds exactly one commit on top of `origin/main` on the new branch, and that commit adds exactly the report path, also when the feature has no `in-progress/` folder on `origin/main` beforehand; no pull request exists afterwards (`hosting.pull_requests()` is empty).
10. `open` takes the title from the first `# ` line of `feature.md` at `origin/main`, and raises `WorkItemFormatError` with that file's path when the feature has no `feature.md` or no title in it, with no branch pushed.
11. `open("F0001")` for the fixture's feature, whose status is `incomplete`, raises `CannotHandle` with kind `acceptance_due` and the reason `feature F0001 is incomplete, not due`, and pushes nothing.
12. After `kill_points.arm(KillPoint.BEFORE_PUSH)` the first `open` raises `InjectedKill`; a second `open` for the same feature then ends with exactly one branch `work-item/F0002-A0001` on the remote, holding exactly one commit on top of `origin/main`.
13. `facts("F0002")` returns the archived stories and the next free story number of the feature as `origin/main` holds them, not of the work tree: a story file that exists only in the checkout's work tree is not counted.
14. `facts` takes its cost line from the cost records of the archived stories only: records of a story in `backlog`, of a story of another feature and of an acceptance are not counted, and a story without a sidecar file adds none; the line equals `cost_line(bill(<the archived stories' records>))`.
15. `facts` raises `ValueError` naming the feature for a feature that has no directory on `origin/main`.
16. At the stage-start commit of the claimed acceptance, `WritePathService(boundaries).at(stage_start, <report path>).write_paths` allows (`is_writable`) the report itself and `<feature directory>/backlog/F0002-S0005-new.md` with the fixture's pipeline definition.
17. The same write paths refuse `<feature directory>/done/F0002-S0001-a.md`, `<feature directory>/feature.md`, a file in another feature's `backlog`, `README.md` and `src/factory/x.py`.
18. GH4.4: with two acceptances `F0002-A0001` and `F0002-A0002` of one feature, each with its own cost records, and a story with its own, `BillService(...).for_work_item(<id>).line` of each acceptance counts only that report's records, and for a report without a cost records file it is `cost_line(bill([]))`.
19. `AcceptanceDueHandler.handle` opens the feature of an `acceptance_due` event: the branch for that feature exists on the remote afterwards.
20. `AcceptanceDueHandler.handle` raises `CannotHandle` with the reasons the Interface gives for an event of another kind and for an `acceptance_due` event without a feature, and pushes nothing.
21. `AcceptanceDueHandler(boundaries, definition)` with `definition.acceptance_stage` `None` is built without an error, and its `handle` of an `acceptance_due` event raises `CannotHandle` with kind `acceptance_due` and the reason `no acceptance stage`, and pushes nothing, and a `run` event with that definition raises with the reason `not an acceptance_due event`.
22. The models are closed and typed: `AcceptanceFacts` and `OpenedAcceptance` refuse an unknown key and an assignment to a field; `AcceptanceFacts.next_story` accepts `F0002-S0007` and refuses `F0002-A0007`; `AcceptanceFacts.archived` accepts `["F0002-S0001"]` and refuses `["F002-S0001"]`; `OpenedAcceptance.id` accepts `F0002-A0001` and refuses `F002-A0001`; `OpenedAcceptance.commit` accepts 40 lower-case hex characters and refuses 39; all with `ValidationError`.
23. F0005-S0009's search test passes on the real tree with `factory.domain.acceptance` in its allow-list of `JOURNAL`, and `acceptance_head` builds the heading from `JOURNAL`: the literal `## Journal` stands in no module of `src/factory` outside `factory.domain.sections`.
24. When the remote already holds a branch `work-item/F0002-A0001` that the checkout has not fetched (the human pushed it, without a report), `open("F0002")` raises `PushFailed` with the outcome `rejected`, and that remote branch is as the human left it.
25. make check stays green.
26. docs: `docs/project-guide.md` states what the opening of an acceptance writes (one report head on a branch `work-item/<acceptance id>`, no pull request, no claim), the three facts the reviewer gets, that the acceptance reviewer writes only its report and new backlog stories of its feature, and that `factory.domain.acceptance` is on the allow-list of `JOURNAL` in the journal search test.

## Demo

```bash
uv run python -c "
from factory.domain.acceptance import FeatureFiles, acceptance_facts, acceptance_prompt
files = FeatureFiles(feature='F0002', backlog=['F0002-S0006-x.md', '.gitkeep'], done=['F0002-S0001-a.md', 'F0002-S0002-b.md', 'F0002-S0004-d.md'])
facts = acceptance_facts(files, cost_line='19 runs, 7.1 min, 3.33 USD')
print(acceptance_prompt('Judge the feature.', facts))
"
```
Expect: five lines: `Judge the feature.`, an empty line, `Archived stories: F0002-S0001, F0002-S0002, F0002-S0004`, `Next free story number: F0002-S0007` and `Cost of the stories: 19 runs, 7.1 min, 3.33 USD`.

```bash
uv run python -c "
from factory.domain.acceptance import acceptance_head
head = acceptance_head('Todo service', 'acceptance', ['F0001-S0001', 'F0001-S0002'])
print(type(head.state).__name__, head.state.stage, head.state.stories, head.state.journal, head.state.claim)
print(repr(head.body))
"
```
Expect: two lines: `AcceptanceState acceptance ['F0001-S0001', 'F0001-S0002'] [] None`, then `'# Acceptance of Todo service\n\n## Journal\n'`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules (`factory.domain.acceptance`, `factory.application.acceptance`), signatures, the imports they need and the rules for each unit. The `tests/test_no_journal_reading.py` allow-list change is stated, with the feature's decision 22 as the leave.
   - Criteria: each is testable by one test function. Every rule has its failing side: `next_story` at 9999 (3), an acceptance id as `next_story` and malformed ids (22), `acceptance_stage` of `None` (7, 21), a feature that is not due (11), a missing or untitled `feature.md` (10), a push that is rejected (24), a feature with no directory (15), and a wrong event kind or no feature (20). Behaviours the Interface states, such as the four-digit number, the three lines, the exact head and body, and the cost line over archived stories only, are covered by 1 to 6, 13 and 14. Recovery is covered by 12.
   - Demo: both commands are runnable with the Interface's names, and each `Expect:` line is checkable against the output.
   - Architecture: pure facts and head sit in the domain, the service and handler in the application layer reached through `Boundaries`, and git and the writers are used only through their wrappers. Wiring is left to S0010 and the stage protocol to S0009, as the Assignment says.
   - Scope: the story stays within the feature's scope item "The acceptance stage" and decisions 5 to 8 and 22, and touches nothing in "Out of scope".
3. tester: red tests for the acceptance facts, the prompt, the head, AcceptanceService and AcceptanceDueHandler. `make lint` is green. `make test` stops at collection because the modules under test don't exist yet, which is the expected failure.

   Mapping:
   - criterion 1: tests/domain/test_acceptance_facts.py::test_the_facts_hold_the_archived_stories_and_the_number_after_the_highest
   - criterion 2: tests/domain/test_acceptance_facts.py::test_the_next_story_number_has_four_digits_and_counts_only_story_files (rows: highest 9 gives S0010, a story in in_progress, an acceptance report and notes in in_progress, no story file gives S0001)
   - criterion 3: tests/domain/test_acceptance_facts.py::test_the_next_story_number_ends_at_9999 (9998 and 9999)
   - criterion 4: tests/domain/test_acceptance_facts.py::test_the_facts_are_three_lines
   - criterion 5: tests/domain/test_acceptance_facts.py::test_the_prompt_is_the_base_an_empty_line_and_the_facts
   - criterion 6: tests/domain/test_acceptance_facts.py::test_the_head_is_an_initial_acceptance_state_a_title_and_an_empty_journal
   - criterion 7: tests/application/test_acceptance_service.py::test_the_service_needs_an_acceptance_stage
   - criterion 8: tests/application/test_acceptance_service.py::test_opening_pushes_the_report_head_on_the_acceptance_branch
   - criterion 9: tests/application/test_acceptance_service.py::test_opening_adds_one_commit_with_only_the_report_and_no_pull_request (with and without `in-progress/.gitkeep` on main)
   - criterion 10: tests/application/test_acceptance_service.py::test_opening_without_a_feature_title_is_a_format_error_and_pushes_nothing (missing file, untitled file) and ::test_opening_takes_the_first_title_of_the_feature_file
   - criterion 11: tests/application/test_acceptance_service.py::test_opening_a_feature_that_is_not_due_cannot_be_handled_and_pushes_nothing
   - criterion 12: tests/application/test_acceptance_service.py::test_opening_again_after_a_kill_before_the_push_leaves_one_branch_with_one_commit
   - criterion 13: tests/application/test_acceptance_service.py::test_the_facts_are_read_from_main_on_the_remote_only (story only in the work tree, or committed only locally)
   - criterion 14: tests/application/test_acceptance_service.py::test_the_cost_line_counts_the_records_of_the_archived_stories_only
   - criterion 15: tests/application/test_acceptance_service.py::test_the_facts_of_a_feature_without_a_directory_on_main_are_refused
   - criterion 16: tests/application/test_acceptance_service.py::test_the_reviewer_may_write_its_report_and_new_backlog_stories
   - criterion 17: tests/application/test_acceptance_service.py::test_the_reviewer_may_write_nothing_else
   - criterion 18: tests/application/test_acceptance_service.py::test_each_acceptance_has_its_own_cost_line (A0001 merged to done/, A0002 on its branch, A0003 on its branch without a sidecar, plus an archived story with its own records)
   - criterion 19: tests/application/test_acceptance_due_handler.py::test_an_acceptance_due_event_opens_its_feature
   - criterion 20: tests/application/test_acceptance_due_handler.py::test_an_event_the_handler_cannot_open_is_refused_and_pushes_nothing
   - criterion 21: tests/application/test_acceptance_due_handler.py::test_without_an_acceptance_stage_the_handler_is_built_and_refuses_every_event
   - criterion 22: tests/domain/test_acceptance_facts.py::test_the_facts_are_closed_and_typed and ::test_the_facts_refuse_an_assignment; tests/application/test_acceptance_service.py::test_the_opened_acceptance_is_closed_and_typed and ::test_the_opened_acceptance_refuses_an_assignment
   - criterion 23: tests/test_no_journal_reading.py::test_no_module_reads_data_from_the_journal_text, with `factory.domain.acceptance` added to `ALLOWED["JOURNAL"]` (the only change to that file, as the Interface allows). Also tests/domain/test_acceptance_facts.py::test_the_head_builds_its_journal_heading_from_the_section_name, which checks that `factory.domain.acceptance` imports `JOURNAL` from `factory.domain.sections`.
   - criterion 24: tests/application/test_acceptance_service.py::test_opening_onto_a_branch_the_checkout_has_not_fetched_is_a_rejected_push
   - criteria 25 and 26: no test (`make check` and docs).

   Files created: tests/domain/test_acceptance_facts.py, tests/application/test_acceptance_service.py, tests/application/test_acceptance_due_handler.py. Edited: tests/test_no_journal_reading.py (one line in the allow-list).

   Modules the test runner could not import: `factory.application.acceptance` (does not exist), and `AcceptanceFacts` from `factory.domain.acceptance` (the module exists but does not have it yet).

   Notes for the coder:
   - The tests call `boundaries.git.fetch()` before building the service. They assume `open` and `facts` read the last fetch and do not fetch themselves; criterion 24 depends on that.
   - A "run" event with no work item is built with `Event.model_construct`, just like the `acceptance_due` event without a feature.
   - The type check was skipped in this stage, as the stage allows.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented the acceptance opening and the reviewer's facts. All the tester's tests pass unchanged, and `make check` is green (coverage 99.5 %).

   Built:
   - `src/factory/domain/acceptance.py` (grown): `AcceptanceFacts`, `acceptance_facts`, `acceptance_prompt` and `acceptance_head`.
     - `AcceptanceFacts` has a validator that refuses an acceptance id as `next_story`, and its `lines()` gives the three fact lines.
     - `acceptance_facts` takes the highest story number from `story_file_ids` over backlog, in-progress and done, then adds one. A result above 9999 raises `ValueError`.
     - `acceptance_head` builds the `AcceptanceState` from `initial_state(stage).model_dump()` plus `stories`. It writes the heading as `f"## {JOURNAL}"`, with `JOURNAL` imported from `factory.domain.sections`.
   - `src/factory/application/acceptance.py` (new): `OpenedAcceptance`, `AcceptanceService` and `AcceptanceDueHandler(Handler)`.
     - `open` and `facts` both read through `AcceptanceReader` from S0002 (`read()` for the status, directory, archived stories and next acceptance; `feature_files` for the files), using the last fetch only. They never fetch.
     - `open` checks the status, then the title of `feature.md` at origin/main. Only then does it write: `checkout(branch, start_point="origin/main")`, mkdir of the report's folder, `work_item_writer.write`, `commit("<id> opens")`, then push. Any outcome other than `pushed` raises `PushFailed`.
     - Because of `--force-create`, a second `open` after a kill before the push resets the local branch, so the remote gets exactly one commit.
     - `facts` sums the sidecars of the story files in `done/` only. Acceptance reports are skipped, and a story without a sidecar adds no records.
     - A feature with no directory raises `ValueError` naming the feature. `open` uses the same lookup.

   Main decision: the service reuses `AcceptanceReader` for status, directory and files rather than reading the tree again. I rejected a separate listing in the service because it would duplicate S0002's rules for what is due.

   Refactor: I read the diff and found nothing to change, so there is no refactor commit.

   Noticed, not touched:
   - `AcceptanceService._feature_title` looks like the private `BoardService._feature_title` in `factory/application/board.py`, but it differs: it raises `WorkItemFormatError` with the path instead of returning `None`.
   - `AcceptanceService._records` does what `BillService._records` does (read a sidecar at a ref, or no records), but that one is private. A shared helper would mean changing `costs.py`, which is beyond this story.
   - Wiring the handler into `build_handlers` is left to S0010, and appending the facts to the prompt to S0009, as the Assignment says.
   - Criterion 26 (docs) is the documenter's.

   `make check`: check: green
5. reviewer: group 1 (acceptance criteria) passes. Criteria 1 to 24 each have a test that checks what the criterion says. The failing sides are tested: 9998 and 9999, a story id and an acceptance id as `next_story`, malformed ids, a 39-character commit, no acceptance stage, not due, a missing or untitled `feature.md`, a rejected push, no directory, the wrong kind and no feature. The coder's entry reports `make check` green. Group 2 (architecture) fails on the CLAUDE.md rule "Before writing a helper, search `src/factory` for one that does the same, and reuse or extend it; the reviewer counts a second copy of an existing helper as a finding". I stopped there, as the role says.

   1. `src/factory/application/acceptance.py` `AcceptanceService._records` copies `BillService._records` in `src/factory/application/costs.py:152` line for line: `show_file` at a ref, then `[]` on `None`, otherwise `cost_reader.parse`. The coder noted it and left it, saying that changing `costs.py` was out of scope. CLAUDE.md says to extend the existing helper instead. Fix: move the sidecar read into one shared function in the application layer, for example a module-level `read_cost_records(git, cost_reader, ref, sidecar)` in `factory.application.costs`. Have `BillService` and `AcceptanceService.facts` both call it, and delete the copy.
   2. `src/factory/application/acceptance.py` `AcceptanceService._feature_title` repeats the read in `BoardService._feature_title` in `src/factory/application/board.py:56`: the same path built from `FEATURES_DIRECTORY` and `FEATURE_FILE_NAME`, then `show_file` at `origin/main`, then `title`. Fix: extract one shared `feature_title(git, directory) -> str | None` that both use. `AcceptanceService` keeps only its own `WorkItemFormatError` handling for `None`. The missing file and the untitled file need to stay apart, so each gets its own message and both carry the path.

   No other groups were reviewed in this round.
6. coder: coder (round 1): fixed both of the reviewer's findings, and nothing else. No test was changed. `make check` is green (coverage 99.5 %). Commit ef1d36d.

   1. The copied sidecar read is now one function, `read_cost_records(git, cost_reader, ref, sidecar)`, at module level in `src/factory/application/costs.py`.
      - `BillService.for_work_item` calls it; its private `_records` is gone.
      - `AcceptanceService._records` now only builds the sidecar path and calls the same function at `origin/main`.
   2. The copied feature-file read is shared in two parts:
      - `feature_file_path(directory)` in `src/factory/domain/paths.py` builds the path.
      - `read_feature_file(git, directory) -> str | None` in `src/factory/application/work_items.py` returns the file's text at `origin/main`, or `None` when the file is missing.
      - `BoardReader._feature_title` (`src/factory/application/board.py`) uses both. Its now-unused `_MAIN_REF` and path imports are gone.
      - `AcceptanceService._feature_title` uses both too. It keeps its two separate `WorkItemFormatError`s, one for a missing file and one for a file without a title, and both carry the path.

   Main decision: I share the read of the text, not the title. I rejected the reviewer's example `feature_title(git, directory) -> str | None`: its `None` would mean both "missing" and "untitled", so `AcceptanceService` would have to read the file a second time to tell the two apart.

   `read_feature_file` sits beside `RemoteWorkItems` because that module already reads from main's refs. Putting it in `board.py` would have made the acceptance service import from the board use case.

   Noticed, not touched: `factory/entry/check_story.py` builds the same feature-file path on the local filesystem. It could use `feature_file_path`, but that is outside this ticket.

   `make check`: check: green
7. reviewer: reviewer (round 1): no findings.

   - Group 1 (acceptance criteria) passes. No test changed since the last review. Criteria 1 to 24 each have a test that checks what the criterion says. The failing sides are covered:
     - next story numbers 9998 and 9999, and an acceptance id as `next_story`
     - malformed `archived` and `id`, and a 39-character commit
     - no acceptance stage, at both the service and the handler
     - a feature that is not due, and a missing or untitled `feature.md` (both carry the path)
     - a rejected push, and a feature with no directory
     - an event of another kind, and one without a feature

     The coder's round-1 entry reports `make check` green.
   - Group 2 (architecture) passes. Both of last round's findings are fixed:
     1. `read_cost_records` is now a module-level function in `src/factory/application/costs.py`. `BillService.for_work_item` and `AcceptanceService._records` both use it, and the copy is gone.
     2. `feature_file_path` is in `src/factory/domain/paths.py` and `read_feature_file` in `src/factory/application/work_items.py`. `BoardReader._feature_title` and `AcceptanceService._feature_title` both use them.

     I accept the coder's choice to share the text read rather than the title: a single `str | None` could not tell a missing file from an untitled one. The layers hold: domain imports only domain, and the application reaches git only through `Boundaries`/`Git`. No new `dict[str, Any]` crosses a function boundary: the `model_dump()` spread in `acceptance_head` stays inside one constructor call.
   - Group 3 (security) passes. There are no secrets, no strings built into shell or SQL, and no markers that silence a check.
   - Group 4 (quality) passes.
     - Names and docstrings fit what they describe, and there is no dead code.
     - `_story_number` sits beside the existing `_acceptance_number`; I checked `factory.domain.identifiers` and it has no story-number helper.
     - In `facts`, the loop filters with parse plus `is_acceptance` instead of calling `story_file_ids`. That is not a copy: it needs file names to build sidecar paths, and `story_file_ids` returns ids.
     - The `JOURNAL` heading is built from `factory.domain.sections`.
   - Group 5 (ticket hygiene) passes. The log gives the main decisions (reuse `AcceptanceReader`; share the text, not the title) and what was rejected. `Assignment` matches what was built, and criterion 26 still says what the documenter must write.

   Open, not for this story:
   - `factory/entry/check_story.py` could use `feature_file_path`, as the coder noted.
   - Wiring the handler is S0010's job, and appending the facts to the prompt is S0009's.
8. documenter: documenter (round 1): wrote the docs criterion (26) and found no code finding. `make check` is green.

   Changed, in `docs/project-guide.md`:
   - Section "The feature acceptance", four new bullets before "The document and its error". "Opening" says what `open` writes: one report head on `work-item/<acceptance id>`, no pull request, no claim, no agent. It also gives the title source and the errors (`CannotHandle`, `WorkItemFormatError`, `PushFailed`) and what `AcceptanceDueHandler` does. "The reviewer's facts" gives the three facts and `acceptance_prompt`. "What the reviewer may write" says its report and new backlog stories only. "Its cost" says each report has its own sidecar and names the shared helpers `read_cost_records`, `feature_file_path` and `read_feature_file`.
   - Section "No code reads data from the journal's text": `factory.domain.acceptance` is added to the `JOURNAL` allow-list, matching `tests/test_no_journal_reading.py`.

   Cross-read and current: the `build_handlers` and `NOT_YET_HANDLED` text (the handler is not wired yet; the new bullet says so), the Reader bullet, and the board paragraph. README and the operator guide need nothing from this story.

   I did not run the examples, because I wrote none.

   Stale but not touched (unrelated): `factory/entry/check_story.py` builds the feature-file path itself instead of using `feature_file_path`. That is the coder's note, not documentation.

   `make check`: check: green
9. demo: Demo, round 1. I ran both `## Demo` commands from the repository root, in order. Both exited 0.

   Command 1 (`acceptance_facts` + `acceptance_prompt`):
   ```
   Judge the feature.

   Archived stories: F0002-S0001, F0002-S0002, F0002-S0004
   Next free story number: F0002-S0007
   Cost of the stories: 19 runs, 7.1 min, 3.33 USD
   ```
   Met its Expect line: the five lines appear exactly as specified, in order, with the empty line second.

   Command 2 (`acceptance_head`):
   ```
   AcceptanceState acceptance ['F0001-S0001', 'F0001-S0002'] [] None
   '# Acceptance of Todo service\n\n## Journal\n'
   ```
   Met its Expect line: both lines match exactly.

   I read the acceptance criteria again against this output. It agrees with criteria 1, 4, 5 and 6: archived stories, next free story number 4-digit and above the backlog's S0006, the three fact lines, the prompt joined with an empty line, the state type, stage, stories, empty journal, no claim, and the body. The demo contradicts no criterion. The criteria it does not exercise (opening on the remote, write paths, bill per acceptance, the handler) are left to the tests and the `make check` gate.

   No findings.
10. done (pull request merged); cost: 8 runs, 19.0 min, 88 turns, 277k tokens in (2502k more from cache), 44k out, $3.37
