---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 222
comments_read: [6251638379]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T15:12:15.852400Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T15:12:15.858536Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T15:12:38.591046Z'
  stage: intake
  run: 75a6e89899c444468bee01e3aa970eba
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T15:12:58.703444Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T15:16:42.293834Z'
  stage: tests
  run: 902b85af1b4c4c03bb5b3ae127bd298a
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T15:17:02.459866Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T15:20:37.599737Z'
  stage: doing
  run: b7940bb81d9d440b9701df380a2c776b
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T15:20:58.041187Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T15:22:14.550608Z'
  stage: review
  run: e9141c98e5d449cc8d426ad9b3971f3a
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T15:22:34.591908Z'
  stage: doing
- number: 11
  speaker: coder
  kind: question
  at: '2026-10-18T15:23:01.337331Z'
  stage: doing
  run: a5d43fa09d07473a9ac1363f4368f4d5
- number: 12
  speaker: human
  kind: comment
  at: '2026-10-18T15:24:17.469940Z'
  stage: doing
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-18T15:24:34.948620Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-18T15:24:57.750228Z'
  stage: doing
  run: 684785e4577549389e1dfa31e211987e
---

# The write paths and the tool paths become the kernel's targets

## Description

The kernel allows writes beneath folders and on existing files, while a stage's write paths are `fnmatch` patterns, and an agent run also writes the project's tool state (`.venv`, caches, reports), which no write path names. This story gives the pipeline definition an optional key `tool_paths`, folder patterns written by every role's agent run (`<folder>/*` in the checkout, `~/<folder>/*` in the agent's home; feature decision 8), carries them in the guard settings the write-path service returns, and adds two pure functions to the domain: `write_targets` turns a run's write paths and tool paths into folders and files of the kernel, and `confinement_of` turns those targets, with the files that exist and the runtime's own paths, into the `Confinement` of S0002. A path the kernel cannot name exactly is widened to the nearest folder it can, never to the checkout's root, and the undo narrows it after the run (feature decision 6). The hook and the undo keep judging the write paths as they do; the tool paths reach neither. Nothing uses the targets yet: the runtime does in S0004. factory-rf's own `factory/pipeline.yml` gets its `tool_paths` from the human once the image runs this code (the feature's change 5).

## Interface

`factory.domain.pipeline_definition` (`domain`):

```python
class PipelineDefinition(BaseModel):
    ...
    tool_paths: list[WritePath] = []
```

- A new load-time rule in `_RULES`: every tool path must match `<folder>/*` or `~/<folder>/*`, where `<folder>` is one or more `/`-separated segments, each non-empty, none `..`, none holding `*`, `?` or `[`, and `<folder>` does not start with `/`. A tool path that does not is the fault `f"tool path {path}: must be <folder>/* or ~/<folder>/*"`, one per such path, joined with the other rules' faults as today.
- An absent key is `[]`; the key is strict like the others (a string instead of a list is refused by the model).

`factory.domain.agent_runs` (`domain`):

```python
class GuardSettings(BaseModel):
    ...
    tool_paths: list[str] = []
```

`factory.application.write_paths` (`application`):

- `WritePathService.at` returns `GuardSettings` with `tool_paths` the definition's `tool_paths` at the stage-start commit, unchanged (no placeholder is expanded in them); `write_paths` and `protected_paths` are as before.

`factory.domain.confinement` (`domain`):

```python
TargetKind = Literal["folder", "file"]

class WriteTarget(BaseModel):
    """One path the kernel may allow: a folder and everything beneath it, or one file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: AbsolutePath
    kind: TargetKind

def write_targets(guard: GuardSettings, *, home: Path | None) -> list[WriteTarget]:
    """The kernel's targets of the write paths, then the tool paths, of `guard`."""

def confinement_of(
    targets: Sequence[WriteTarget],
    *,
    root: Path,
    existing_files: Collection[Path],
    extras: Sequence[WriteTarget],
    temporary_directory: Path,
) -> Confinement:
    """The rules of one run: the targets as the files that exist allow them, and the extras."""
```

- `write_targets`, for each write path `p` of `guard.write_paths`, in order, relative to `guard.root`:
  - `p` empty, starting with `/`, or holding a `..` segment: no target.
  - `p` ending in `/*` with no `*`, `?` or `[` before it: the folder `root / p[:-2]`.
  - `p` holding none of `*`, `?`, `[`: the file `root / p`.
  - any other `p`: the folder of the segments before the first segment that holds `*`, `?` or `[`; no target when there is none (a pattern at the root, such as `*.md`).
- then for each tool path `t` of `guard.tool_paths`, in order: `~/<folder>/*` is the folder `home / <folder>`, and no target when `home` is `None`; `<folder>/*` is the folder `root / <folder>`; any other `t` gives no target.
- A target equal to an earlier one is left out; the order is otherwise kept.
- `confinement_of`: a folder target goes to `folders`; a file target in `existing_files` goes to `files`; a file target not in `existing_files` puts its parent folder in `folders`, unless that parent is `root`, in which case it gives nothing. The `extras` are taken as they are, never widened and never checked against `existing_files`: their folders follow the targets' folders and their files the targets' files, each in the order given. A path equal to an earlier one of the same list is left out. `temporary_directory` is taken as given.

Tests (the tester writes them): `tests/domain/test_tool_paths.py` (the rule, through `PipelineDefinition` or the YAML reader), `tests/domain/test_write_targets.py`, `tests/domain/test_confinement_of.py`, `tests/application/test_write_paths_tool_paths.py`. A pipeline definition written in a test passes every other load-time rule (`CLAUDE.md`, *Tests*).

## Acceptance criteria

1. A pipeline definition with `tool_paths: [".venv/*", "a/b/*", "~/.cache/*"]` loads with those three in order, and one without the key loads with `tool_paths == []` (rows of one parametrized test).
2. Each of `"*.log"`, `".venv"`, `"/var/cache/*"`, `"../x/*"`, `"a/../b/*"`, `"a/*/b/*"`, `"a/b?/*"`, `"a/[b]/*"`, `"~/*"`, `"~/../x/*"` and `"a//b/*"` alone in `tool_paths` makes the definition invalid with the fault `tool path <path>: must be <folder>/* or ~/<folder>/*`; two of them give two faults; and `tool_paths: ".venv/*"`, a string instead of a list, makes it invalid with `invalid tool_paths: Input should be a valid list` (rows of one parametrized test).
3. `WritePathService.at` returns the definition's `tool_paths` at the stage-start commit, `[".venv/*", "~/.cache/*"]`, unchanged, and `[]` for a definition without the key; a `tool_paths` pushed after the stage-start commit is not in the result (rows of one parametrized test).
4. With `root` `/work/checkout` and `home` `/home/agent`, `write_targets` gives for each write path (rows of one parametrized test): `src/*` the folder `/work/checkout/src`; `a/b/*` the folder `/work/checkout/a/b`; `README.md` the file `/work/checkout/README.md`; `factory/features/F0001-x/in-progress/F0001-S0001-y.md` that file; `docs/*.md` the folder `/work/checkout/docs`; `a/b*/c` the folder `/work/checkout/a`; `a/b?/c` the folder `/work/checkout/a`; `a/[bc]/d` the folder `/work/checkout/a`; `*.md` nothing; `*` nothing; `""` nothing; `/etc/*` nothing; `../x/*` nothing; `src/../x` nothing.
5. With the same `root`, `write_targets` gives for each tool path (rows of one parametrized test): `.venv/*` the folder `/work/checkout/.venv`; `~/.cache/*` with `home` `/home/agent` the folder `/home/agent/.cache`; `~/.cache/*` with `home` `None` nothing; `*.log`, of neither form, nothing.
6. `write_targets` keeps the order write paths first, then tool paths, and leaves out a repeated target: write paths `["src/*", "docs/*", "src/*"]` and tool paths `[".venv/*", "src/*"]` give the folders `src`, `docs`, `.venv`, in that order.
7. `confinement_of` with `root` `/w` (rows of one parametrized test): a folder target `/w/src` is in `folders`; a file target `/w/README.md` that is in `existing_files` is in `files`; a file target `/w/docs/openapi.json` that is not gives the folder `/w/docs`; a file target `/w/NEW.md` that is not gives nothing; a file target `/w/a/b/c.md` that is not gives the folder `/w/a/b`.
8. `confinement_of` puts the folder extras after the targets' folders and the file extras after the targets' files, in their order, takes a file extra as given even when it is not in `existing_files`, leaves out a path already in the same list (a missing file whose folder is also a folder target gives that folder once; a folder extra equal to a target's folder is left out), and returns `temporary_directory` as given.
9. `GuardSettings` built without `tool_paths` has `tool_paths == []`, and the verdict `refusal`, which the hook and the undo share, ignores the tool paths: with write paths `["src/*"]` and tool paths `[".venv/*"]`, `.venv/x` is refused as outside the write paths and `src/x` is allowed (rows of one parametrized test).
10. `make check` stays green.
11. docs: `docs/project-guide.md`, section *The pipeline definition*, names `tool_paths`, its form and its fault; section *The write paths* gains a subsection *The kernel's targets*: the rules of `write_targets` and `confinement_of` with the widening of a missing file and of a wildcard pattern to a folder, never the root, and that the undo narrows the rest. `docs/operator-guide.md`, section *The pipeline definition*, names `tool_paths` with an example (`[".venv/*", ".reports/*", "~/.cache/*"]`) and says that a project's tools that write elsewhere are refused once the guard is live. `docs/decisions.md` gets an entry *The kernel's targets of the write paths and the tool paths*, dated 2026-10-18 (F0019-S0003), with the reasons of the feature's decisions 6, 8 and 15.

## Smoke test

```bash
uv run -q python -c '
from pathlib import Path
from factory.adapters.pipeline_yaml import RuamelPipelineDefinitionReader
from factory.domain.errors import PipelineDefinitionInvalid
text = Path("template/factory/pipeline.yml").read_text(encoding="utf-8").rstrip() + "\n"
reader = RuamelPipelineDefinitionReader()
print(reader.parse(text + "tool_paths: [\".venv/*\", \"~/.cache/*\"]\n").tool_paths)
try:
    reader.parse(text + "tool_paths: [\"*.log\"]\n")
except PipelineDefinitionInvalid as error:
    print(error)
'
```
Expect: two lines, `['.venv/*', '~/.cache/*']` and then `tool path *.log: must be <folder>/* or ~/<folder>/*`

```bash
uv run -q python -c '
from pathlib import Path
from factory.domain.agent_runs import GuardSettings
from factory.domain.confinement import write_targets
guard = GuardSettings(root=Path("/work/checkout"), write_paths=["src/*", "README.md", "docs/*.md", "*.md"], protected_paths=[], tool_paths=[".venv/*", "~/.cache/*"])
for target in write_targets(guard, home=Path("/home/agent")):
    print(target.kind, target.path)
'
```
Expect: five lines, `folder /work/checkout/src`, `file /work/checkout/README.md`, `folder /work/checkout/docs`, `folder /work/checkout/.venv` and `folder /home/agent/.cache`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`PipelineDefinition.tool_paths`, `GuardSettings.tool_paths`, `WritePathService.at`, `WriteTarget`, `write_targets`, `confinement_of`), with the exact fault text and the layer of each.
   Criteria: each is testable by one parametrized test. Every Interface clause has its own criterion on both sides. Tool paths: the accepted forms (1), the eleven refused forms and the string-instead-of-list case (2). Write paths: each branch of the `write_targets` rules (4). Tool path forms and `home=None` (5). Order and de-duplication (6). Each branch of `confinement_of` (7, 8). The hook and undo ignoring tool paths (9).
   Smoke test: both commands are runnable against existing modules and `template/factory/pipeline.yml`. Each `Expect:` line gives exact output that can be compared.
   Architecture: the pure functions and DTOs are in `domain`, the settings pass-through is in `application.write_paths`, and the key is read by the existing YAML reader. No layer rule is broken, and the story adds no adapter, dependency or wrapper.
   Scope: it matches the feature's S0003 scope. Nothing here belongs to its Out of scope list; the runtime use is left to S0004.
4. factory: started tests as self.
5. tester: I wrote red tests for criteria 1 to 9. One `make test` run showed them failing for the right reason: tests that read `tool_paths` fail, and the target and confinement modules fail to import. `make lint` is green.

   criterion 1: tests/domain/test_tool_paths.py::test_the_tool_paths_load_in_order_and_default_to_none
   criterion 2: tests/domain/test_tool_paths.py::test_a_tool_path_of_neither_folder_form_is_refused
   criterion 3: tests/application/test_write_paths_tool_paths.py::test_at_returns_the_tool_paths_of_the_definition_at_the_stage_start_commit
   criterion 4: tests/domain/test_write_targets.py::test_a_write_path_becomes_the_folder_or_file_the_kernel_can_name
   criterion 5: tests/domain/test_write_targets.py::test_a_tool_path_becomes_a_folder_in_the_checkout_or_the_home
   criterion 6: tests/domain/test_write_targets.py::test_the_write_paths_come_first_and_a_repeated_target_is_left_out
   criterion 7: tests/domain/test_confinement_of.py::test_a_target_is_a_folder_a_file_or_the_folder_of_a_missing_file
   criterion 8: tests/domain/test_confinement_of.py::test_the_extras_follow_the_targets_as_given_and_a_repeated_path_is_left_out
   criterion 9: tests/domain/test_tool_paths.py::test_the_verdict_ignores_the_tool_paths
   criteria 10 and 11 (`make check`, docs): no test of their own.

   Files created: tests/domain/test_tool_paths.py, tests/domain/test_write_targets.py, tests/domain/test_confinement_of.py, tests/application/test_write_paths_tool_paths.py, tests/write_path_support.py.

   Earlier test file changed: tests/application/test_write_paths.py. Under the standing leave in CLAUDE.md (*Tests*), I moved its `_stage_start` and `_push_definition` helpers and its `PIPELINE_FILE` constant to tests/write_path_support.py as `stage_start`, `push_definition` and `PIPELINE_FILE`. The new application test uses them too. Every earlier test keeps its name and checks the same thing.

   Modules the test runner could not import: `factory.domain.confinement` has no `WriteTarget`, `write_targets` or `confinement_of` yet, so test_write_targets.py and test_confinement_of.py fail at collection. The rest fail on the missing `tool_paths` of `PipelineDefinition` and `GuardSettings`.

   Notes for the coder:
   - The tool-path rule is tested through `RuamelPipelineDefinitionReader`, which the Interface allows. That is because the fault `invalid tool_paths: Input should be a valid list` is written by the reader.
   - The "two faults" row compares the faults split on `; ` as a set, so the order of the two faults is not fixed.
   - In criterion 9, the default `tool_paths == []` and the verdict share one parametrized test. Its rows are a guard with and without `tool_paths`, crossed with `.venv/x` (refused) and `src/x` (allowed).

   Nothing is open.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/domain/test_write_targets.py - ImportError while importing test m...
6. factory: started doing as self.
7. coder: I added `tool_paths` to the pipeline definition and the guard settings, and added `write_targets` and `confinement_of` to the domain. `make check` is green and I left every test untouched.

   Built:
   - `src/factory/domain/pipeline_definition.py`: adds `PipelineDefinition.tool_paths: list[WritePath] = []` and a new rule `_tool_path_faults` in `_RULES`. Its fault text is `tool path <path>: must be <folder>/* or ~/<folder>/*`. Two public helpers sit beside it: `tool_path_folder` returns the folder of either form with `~/` kept, or `None`; `has_wildcard` checks for `*`, `?` or `[`. The constants `HOME_PREFIX` and `PARENT_SEGMENT` are new here too.
   - `src/factory/domain/agent_runs.py`: adds `GuardSettings.tool_paths: list[str] = []`.
   - `src/factory/application/write_paths.py`: `WritePathService.at` passes the definition's `tool_paths` through unchanged.
   - `src/factory/domain/confinement.py`: adds `TargetKind`, `WriteTarget`, `write_targets` and `confinement_of`, with private helpers for one write path, one tool path, the widening of a missing file to its folder, and order-keeping de-duplication.
   - `src/factory/domain/write_paths.py`: the private `_is_safe` is now public as `is_inside_checkout`, so `write_targets` can reuse it. Its `..` constant now comes from `pipeline_definition` instead of being a second copy. `refusal` and `is_writable` behave exactly as before.

   Main design decision: `write_targets` handles every write path with one rule. It finds the first segment that holds a wildcard and uses the folder of the segments before it. With no wildcard the path is a file target; with the wildcard in the first segment there is no target, because the root would allow everything. This covers both the Interface's `<folder>/*` case and its "any other pattern" case, since `src/*` and `docs/*.md` both stop at their first wildcard segment.
   - Rejected: a separate branch for paths ending in `/*`. It gives the same results in every case and only adds code.
   - Rejected: a regex for the tool-path form. A `(~/)?` regex also accepts `~/*` as a checkout folder named `~`. Removing the `~/` prefix first and then requiring `/*` refuses `~/*` without a special case.

   Refactor: I read the diff once and found nothing to change.

   Smoke test: the second command printed exactly the five expected lines.

   Noticed but not touched:
   - `make duplicates` reports 3 new findings, all dead code. Two are `write_targets` and `confinement_of`, which nothing calls until the runtime uses them in S0004. The third, `CONFINE_COMMAND` in `src/factory/domain/agent_runs.py`, was there before this story.

   The journal did not change the task's meaning, so I left `## Description` as it is.

   `check`: check: green
   `duplicates`: duplicates: 3 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: Group 1 (acceptance criteria) fails. The tests cover criteria 1 to 9 as written. Each Interface rule has its refused side tested, and the coder's journal reports `make check` green. But the Description promises "never to the checkout's root", and that rule has a gap in both the story and the code. No criterion tests a `.` segment, and pathlib collapses `.` segments, so the root, its parent or the whole home can each become a kernel target. Both findings are against the story. They need the human's word on the Interface and criteria 2 and 4, so the coder should end with `question` and propose the fix below.

   1. `src/factory/domain/pipeline_definition.py:51` (`_is_plain_segment`) accepts the segment `.`. So `tool_paths: ["./*"]` passes the load-time rule, and `write_targets` turns it into the folder `root` (the whole checkout). `["~/./*"]` likewise becomes the whole `home`. The Interface's tool-path rule forbids `..` but not `.`, and criterion 2 has no such row. Fix: add "none `.`" to the tool-path rule in the Interface, and add rows `"./*"`, `"a/./b/*"` and `"~/./*"` to criterion 2. Then refuse a `.` segment in `_is_plain_segment`.
   2. `src/factory/domain/confinement.py:86` checks only `first_wildcard == 0`, so a leading `.` segment gets past the root check. The write path `./*` (or `./*.md`) gives the folder `root.joinpath(".")`, which is the checkout's root. The write path `.` gives the file target `root`. At `confinement_of` (`confinement.py:109`), `root` is not in `existing_files` and its parent is not `root`, so it widens to the folder above the checkout. That is wider than the root the Description rules out. The Interface's `write_targets` rules allow both results, and criterion 4 has no row for them. Fix: in the Interface, say that a write path holding a `.` segment, or whose target would be `root` or a folder above it, gives no target. Add rows `./*`, `./*.md` and `.` (each giving nothing) to criterion 4. Then make `_write_path_target` return `None` for these cases.

   Earlier tests:
   - `tests/application/test_write_paths.py` — standing leave to move a shared test helper. The tester moved `_stage_start`, `_push_definition` and `PIPELINE_FILE` to `tests/write_path_support.py` as `stage_start`, `push_definition` and `PIPELINE_FILE`. Every earlier test keeps its name and checks the same thing.
10. factory: started doing as self.
11. coder: I stopped before changing any code. I checked both review findings against the code and both are real. Fixing them means changing the Interface and adding test rows that criteria 2 and 4 don't have yet. That needs your decision first, then the tester's rows, before I implement. The working tree is unchanged from the coder's round 0, and `make check` was green there.

    What I checked:
    - `src/factory/domain/pipeline_definition.py:51` (`_is_plain_segment`) refuses only empty, `..` and wildcard segments. So the tool path `./*` passes the load-time rule and becomes the folder `root`, the whole checkout. `~/./*` becomes all of `home`.
    - `src/factory/domain/confinement.py:86` (`_write_path_target`) only skips a wildcard in the first segment. So the write path `./*` (or `./*.md`) gives the folder `root.joinpath(".")`, which is `root` itself.
    - The write path `.` gives the file target `root`. `confinement_of` then widens it to `root.parent` (`confinement.py:109`), which is the folder above the checkout.

    The Interface's rules as written allow all of these results. The Description says never the checkout's root. The two disagree, so I can't fix this without changing the Interface.

    Question: should the Interface be amended to close the gap, and how?

    - Option A (I'd choose this; it is the reviewer's proposal):
      - Tool-path rule: add "none `.`" to the segment conditions, so `.` gets the same fault as `..`. Add `"./*"`, `"a/./b/*"` and `"~/./*"` to criterion 2.
      - `write_targets`: a write path holding a `.` segment gives no target. Add `./*`, `./*.md` and `.`, each giving nothing, to criterion 4.
      - With `.` and `..` gone, no target can be `root` or above it. I would refuse `.` in `is_inside_checkout`'s check. The hook's `refusal` uses that same function, so a pattern like `./x` would also become unwritable there. If the hook should stay as it is, I would put the check in the targets code only.
    - Option B: keep the load-time rule as it is, and have `write_targets` and `confinement_of` drop any target that resolves to `root`, to a folder above it, or to `home` itself. Fewer rule changes, but `./*` still loads silently and then grants nothing.
    - Option C: accept the gap for this story and leave it to a later story. I would not choose this, because the Description promises the opposite.

    After your answer, I'll end with `tests` and name the rows to add. The tester adds them, and I implement on the next round.

    Noticed but not touched: `make duplicates` still lists `write_targets`, `confinement_of` and the older `CONFINE_COMMAND` as dead code, until the runtime uses them in S0004.

    The journal did not change the meaning of `## Description`.
12. 2026-10-18 human: A, with the check in the targets code only:
    - Tool paths: `.` refused at load time with the same fault as `..`; add `"./*"`, `"a/./b/*"` and `"~/./*"` to criterion 2.
    - `write_targets`: a write path with a `.` segment gives no target; add `./*`, `./*.md` and `.`, each giving nothing, to criterion 4.
    - Leave `is_inside_checkout` as it is, so the hook's refusal does not change in this story.
    Amend the Interface's rules accordingly (feature decision 20, on main). End with `tests` naming the rows.
13. factory: started doing as self.
14. coder: I rewrote `## Description` to follow the human's answer (entry 12, option A with the check in the targets code only). The heading is now "as of the human's answer in journal entry 12". Changes to the work item's text:
    - The Interface's tool-path rule now says "none `.` or `..`".
    - The Interface's `write_targets` rule now reads: "`p` empty, starting with `/`, or holding a `.` or `..` segment: no target".
    - The summary paragraph says a `.` segment is refused in a tool path and gives no target in a write path (feature decision 20).
    - Criteria 2 and 4 have the new rows listed below.

    `is_inside_checkout` and the hook's `refusal` stay as they are. I changed no code this round, and the working tree's code is still round 0's (`make check` was green there).

    Tests to add (the tester's change, two existing parametrized tests):
    - `tests/domain/test_tool_paths.py::test_a_tool_path_of_neither_folder_form_is_refused`: add the rows `"./*"`, `"a/./b/*"` and `"~/./*"`, each giving the fault `tool path <path>: must be <folder>/* or ~/<folder>/*`.
    - `tests/domain/test_write_targets.py::test_a_write_path_becomes_the_folder_or_file_the_kernel_can_name`: add the rows `./*`, `./*.md` and `.`, each giving no target.

    Plan for the next doing round:
    - Refuse a `.` segment in `_is_plain_segment` (`src/factory/domain/pipeline_definition.py`).
    - Have `_write_path_target` (`src/factory/domain/confinement.py`) give no target for a write path with a `.` segment.

    Rejected: putting the `.` check into `is_inside_checkout`. The human ruled it out because it would change what the hook refuses in this story.

    Noticed but not touched: `make duplicates` still lists `write_targets`, `confinement_of` and the older `CONFINE_COMMAND` as dead code, until S0004 uses them.

    The factory undid changes outside the write paths: factory/features/F0019-the-write-guard-by-the-kernel/in-progress/F0019-S0003-the-write-paths-and-the-tool-paths-become-the-kernel-s-targets.md.
