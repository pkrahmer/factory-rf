---
stage: doing
blocked: null
round: 0
attempts: 1
crashes: 0
pull_request: 414
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T17:07:07.773734Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T17:07:07.779610Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T17:07:31.222622Z'
  stage: intake
  run: da4bca229a64443992ab7b91b91dc0f8
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T17:07:51.860763Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T17:11:16.227846Z'
  stage: tests
  run: 8ae6fd9f0cc4454cb4a6fb41a0a79a58
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T17:11:36.820753Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T17:13:27.776534Z'
  stage: doing
  run: fe44c1532a91496c8dad6882ce0df507
- number: 8
  speaker: factory
  kind: stall
  at: '2026-10-24T17:13:27.799635Z'
  stage: doing
  run: fe44c1532a91496c8dad6882ce0df507
  reason: check_red
---

# `sync` is the fourth target of the project contract

## Description

The contract between a project and the factory is three make targets today: `check`, `lint` and `test`. v1.2 needs a fourth, `sync`: the command that brings a checkout's tools up to date after a checkout (`uv sync --frozen` for Python; a Java or TypeScript project names its own command in the same target), which the stage environment runs in the sync container before every agent run and, with `make <command>`, before every check (`planning/v1.2-plan.md`, "What stays, what goes, what is new"). This story adds the target to the template's `Makefile` and the command `sync` with a time limit to the template's pipeline definition, `template/factory/pipeline.yml`, makes the template's header say four targets, and makes the template's rules file, `template/CLAUDE.md`, say that the pipeline definition names the four. This repository's own `Makefile` and `factory/pipeline.yml` are the human's change 1 in `feature.md`, not this story's; the Java/Gradle and TypeScript/npm template designs under `planning/overnight/templates/` are the human's too (change 3). No code changes: the pipeline definition already accepts any named project command with a time limit, and S0005 already reads `sync`'s limit when it is there. What stays: the three targets as they are, `check` running the same seven targets, no `sync` inside `check`.

## Interface

No module under `src/factory/` changes. The coder changes three files of the template:

`template/Makefile`:

- Line 1 becomes `# The contract between a project and the factory is four targets: `check`, `lint`, `test`, `sync`.`; lines 2 to 5 stay exactly as they are (`tests/test_template_makefile_header.py` pins lines 4 and 5 and is not changed). What `sync` does is said in the target's own comment below.
- The `.PHONY` line gains `sync` after `test`: `.PHONY: check lint types layers sast secrets licenses test sync duplicates mutants` (decision 18 f: `tests/test_template_makefile.py::test_phony_line_names_the_targets_and_there_is_no_documents_target` expects it).
- A new target after the `check:` rule and before `lint:`:

  ```make
  # The fourth target of the contract: the tools after a checkout. The stage environment runs it in its
  # sync container before every agent run, and before every check; a project of another stack names its
  # own command here.
  sync:
  	$(start)
  	uv sync --frozen
  	$(green)
  ```

- `check` keeps its seven targets and does not run `sync`.

`template/factory/pipeline.yml`: under `project_commands:` after `test: {time_limit: 10}` a line `  sync: {time_limit: 5}`, with the comment `# the tools after a checkout: the stage environment runs it, no stage lists it` at its end. No stage lists `sync` in `checks` or `reports`.

Tests (the tester writes them): `tests/test_template_sync.py`, built like `tests/test_template_makefile.py` with a stand-in `uv` on the `PATH` (its helpers `_stand_in` and `_make` may move to a shared module under the standing leave); the one change to `tests/test_template_makefile.py` and the one line of `TEMPLATE_RULES_LINES` in `tests/test_claude_files.py` named above under the leave of decision 18 f. `tests/test_template_makefile_header.py` is not changed.

## Acceptance criteria

1. `template/Makefile`'s `.PHONY` line names exactly `check lint types layers sast secrets licenses test sync duplicates mutants`, and `check:` still runs exactly `lint types layers sast secrets licenses test` with the recipe `echo "check: green"` (the two existing tests of `tests/test_template_makefile.py`, the first with `sync` added).
2. Line 1 of `template/Makefile` is `# The contract between a project and the factory is four targets: `check`, `lint`, `test`, `sync`.`, the file holds the phrase `three targets` zero times, lines 4 and 5 are as `tests/test_template_makefile_header.py` pins them, the line `sync:` lies after the `check:` line and before the `lint:` line, and `template/CLAUDE.md` holds the words `names `check`, `lint`, `test` and `sync`` once and `names `check`, `lint` and `test`` zero times (rows of one parametrized test in the new module; the header test is unchanged and green, and `tests/test_claude_files.py` is green with its one changed line).
3. `make sync` on a copy of the template's Makefile with the stand-in `uv` on the `PATH` calls `uv` exactly once with the arguments `["sync", "--frozen"]`, exits 0 and prints as its last line `sync: green (<seconds> s)` (the pattern of the other targets' green line); with the stand-in planned to exit 1, `make sync` exits 2 and prints no green line (rows of one parametrized test).
4. `template/factory/pipeline.yml` parses with `RuamelPipelineDefinitionReader().parse(text)` of `factory.adapters.pipeline_yaml` (as `tests/test_claude_files.py::test_template_pipeline_definition_is_valid_with_the_shipped_roles` does) to a definition whose `project_commands` has exactly the keys `check`, `lint`, `test`, `sync` in that order, `sync` with `time_limit` 5 and `not_read` `[]`, and no stage's `checks` or `reports` names `sync`.
5. `make check` stays green.
6. docs: `docs/project-guide/processes-and-checks.md`, *Project commands*: the contract is four targets, `sync` the fourth, what it does and who runs it (the stage environment's sync container and its check container, S0007 and S0009, never a stage's `checks`), and that this repository's `Makefile` has it (the human's change); `docs/project-guide/agents.md`, *The shipped agents, settings and template*: the template's `sync` target and the `sync` command of its pipeline definition; `docs/operator-guide.md`, *The project's make targets*: the sentence "The factory runs a project's build through make and calls three targets" becomes one that says four targets and names `sync` as the fourth (the tools after a checkout, run by the stage environment of a `container` instance and by no stage of an `inline` one), `uv sync --frozen` here, the project's own command for another stack, so that the phrase `three targets` is gone from the operator guide; and *The pipeline definition*: `sync` in `project_commands` with its time limit and that no stage lists it; `docs/project-guide/stage-environment.md` gains the section *The sync command* (one paragraph: what `make sync` must do for a project, and that the sync container's time limit is the command's). `docs/decisions.md`: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/bin" "$d/project"
printf '#!/bin/sh\necho "uv $*"\n' > "$d/bin/uv"; chmod +x "$d/bin/uv"
cp template/Makefile "$d/project/Makefile"
cd "$d/project" && env -u MAKEFLAGS -u MFLAGS -u MAKELEVEL PATH="$d/bin:$PATH" make sync SOURCE=src/x LAYERS=true | sed -E 's/\([0-9]+\.[0-9] s\)/(N s)/'
```
Expect: two lines, `uv sync --frozen` and `sync: green (N s)`

```bash
sed -n '1p' template/Makefile; grep -c 'three targets' template/Makefile || true; grep -E '^\.PHONY:' template/Makefile; grep -E '^  sync:' template/factory/pipeline.yml | cut -d'#' -f1 | sed 's/ *$//'
```
Expect: four lines: `# The contract between a project and the factory is four targets: `check`, `lint`, `test`, `sync`.`; `0`; `.PHONY: check lint types layers sast secrets licenses test sync duplicates mutants`; `  sync: {time_limit: 5}`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: concrete. It names the three template files, the exact line 1, the `.PHONY` line, the `sync:` recipe and its place, and the pipeline line with its comment. No `src/` module changes. One slip: it says "three files" but lists only `template/Makefile` and `template/factory/pipeline.yml`. The third, `template/CLAUDE.md`, is named by the Description and by criterion 2 (the words "names `check`, `lint`, `test` and `sync`" once, the old three-target wording zero times). I read the Interface as including it and did not ask, because criterion 2 fixes the wording.
   - Criteria: each one is testable by a parametrized test function.
     - 1: the `.PHONY` line, and `check:` unchanged with no `sync`.
     - 2: line 1, no "three targets", lines 4 and 5 pinned, the order of `sync:` between `check:` and `lint:`, and the `CLAUDE.md` wording.
     - 3: `uv` called once with `["sync", "--frozen"]`, exit 0 and the green last line; and the failing side, a stand-in `uv` that exits 1 gives `make` exit 2 and no green line.
     - 4: `project_commands` has the keys in order, `sync` has `time_limit` 5 and `not_read` `[]`, and no stage lists `sync` in `checks` or `reports`.
     - 5 and 6 are the usual `make check` and `docs:` criteria.
     - Every rule the Interface states has a criterion.
   - Smoke test: both blocks are runnable and run no pytest, so the `-q` rule does not apply. Each `Expect:` line is checkable. The first has two exact lines, with the seconds normalised by `sed`. The second has four exact lines; `grep -c ... || true` still prints `0`.
   - Architecture: this is template-only, with no layer change, which fits `CLAUDE.md`. The edit leaves to `tests/test_template_makefile.py` and `tests/test_claude_files.py` are named and rest on decision 18 f. `tests/test_template_makefile_header.py` stays unchanged.
   - Scope: it is within `feature.md`. This repository's own `Makefile` and `factory/pipeline.yml`, and the `planning/overnight/templates/` designs, are left to the human (changes 1 and 3). No stage lists `sync`, so no lease math changes.
4. factory: started tests as self.
5. tester: I wrote the tests for criteria 1 to 4. They fail as they should: the template has no `sync` target or command yet, and its `CLAUDE.md` still names three targets. `make lint` is green.

   Criterion → test:
   - criterion 1: `tests/test_template_makefile.py::test_phony_line_names_the_targets_and_there_is_no_documents_target` now expects `sync` after `test`. `tests/test_template_makefile.py::test_check_runs_the_other_targets_and_says_green` is unchanged.
   - criterion 2: `tests/test_template_sync.py::test_template_says_the_contract_is_four_targets` has five rows:
     - `first-line`
     - `no-three-targets`
     - `lines-four-and-five`
     - `sync-after-check-before-lint`
     - `rules-file`: `template/CLAUDE.md` says "names `check`, `lint`, `test` and `sync`" once and the three-target wording zero times.

     `tests/test_template_makefile_header.py` is unchanged. The `TEMPLATE_RULES_LINES` line in `tests/test_claude_files.py` now reads "The pipeline definition names `check`, `lint`, `test` and `sync`; …".
   - criterion 3: `tests/test_template_sync.py::test_sync_runs_uv_sync_frozen_once_and_says_green` has two rows:
     - Stand-in exits 0: `make sync` exits 0, calls `uv` once with `["sync", "--frozen"]`, and the last line is `sync: green (<s> s)`.
     - Stand-in exits 1: `make sync` exits 2, calls `uv` once, and prints no green line.
   - criterion 4: `tests/test_template_sync.py::test_template_pipeline_definition_names_sync_and_no_stage_lists_it` parses with `RuamelPipelineDefinitionReader().parse`. It expects the `project_commands` keys in order `check, lint, test, sync`, `sync` with `time_limit == 5` and `not_read == []`, and no stage naming `sync` in `checks` or `reports`.
   - criteria 5 and 6: `make check` and docs, nothing to test.

   Files:
   - New: `tests/test_template_sync.py`.
   - New: `tests/template_make_support.py`, a shared helper module:
     - `MAKEFILE` and `DROPPED`
     - `green_line` (was `_green`)
     - `template_project` (the body of the `project` fixture)
     - `stand_in_uv` (was `_stand_in`)
     - `run_make` (was `_make`)
   - Changed: `tests/test_template_makefile.py`. I moved its helpers into the shared module under the standing leave in `CLAUDE.md`. Every test keeps its name and checks the same thing; the `project` fixture stays and calls `template_project`. The `sync` row in the `.PHONY` test falls under decision 18 f, as the Interface says.
   - Changed: `tests/test_claude_files.py`, the one `TEMPLATE_RULES_LINES` line, also under decision 18 f.

   Before implementation, `make test` fails on these:
   - the five-row test (the `rules-file` row fails)
   - both `make sync` rows (`No rule to make target 'sync'`)
   - the pipeline test (keys are `['check', 'lint', 'test']`)
   - the `.PHONY` test
   - `test_template_rules_file_is_the_python_project_text` in `tests/test_claude_files.py`

   The other modules are not shown in the five lines I read.

   Every module imported; none were missing.

   Open: the new list entry for `tests/template_make_support.py` in `docs/project-guide/README.md`, *Shared test helpers*, is for the docs stage.

   `lint`: lint: green (0.6 s)
   `test`: FAILED tests/test_template_sync.py::test_template_pipeline_definition_names_sync_and_no_stage_lists_it - AssertionError: assert ['check', 'lint', 'test'] == ['check', 'li...test', 'sync']
6. factory: started doing as self.
7. coder: I added `sync` to the template's project contract. No module under `src/factory/` changed, and `make check` is green (`test: green (62.5 s)`, then `check: green`).

   What I built:
   - `template/Makefile`:
     - Line 1 now says four targets: `check`, `lint`, `test`, `sync`. Lines 2 to 5 are unchanged.
     - The `.PHONY` line names `sync` after `test`.
     - A new `sync:` target sits between `check:` and `lint:`. It has the comment the Interface gives and the recipe `$(start)` / `uv sync --frozen` / `$(green)`.
     - `check:` is unchanged and does not run `sync`.
   - `template/factory/pipeline.yml`: added `  sync: {time_limit: 5}  # the tools after a checkout: the stage environment runs it, no stage lists it` after `test`. No stage lists `sync` in its checks or reports.
   - `template/CLAUDE.md`: "The pipeline definition names `check`, `lint` and `test`;" now reads "names `check`, `lint`, `test` and `sync`;". It matches the changed line of `TEMPLATE_RULES_LINES` word for word.

   Main decision: `sync` uses the same `$(start)`/`$(green)` macros as the other targets, so its last line is `sync: green (<seconds> s)` like theirs. I rejected a plain one-line `uv sync --frozen` recipe: it prints no green line, which the factory's records of project commands read and criterion 3 requires. I put the trailing comment on the pipeline line rather than on a line of its own above it, because the Interface puts it "at its end".

   Refactor: I read the diff and found nothing to change.

   Noticed, not touched:
   - The new shared test helper module `tests/template_make_support.py` still needs its entry in `docs/project-guide/README.md`, *Shared test helpers*. That is for the docs stage, as the tester noted.
   - This repository's own `Makefile` and `factory/pipeline.yml` still have no `sync`. They are the human's change 1.
   - The journal did not change the task's meaning, so I left `## Description` as it is.
8. factory: Stage doing stalled (attempt 1 of 2): a check is red after the stage: `check`
   Using CPython 3.12.15 interpreter at: /usr/local/bin/python3.12
   Creating virtual environment at: .venv
   Installed 106 packages in 83ms
   Bytecode compiled 4164 files in 352ms
   All checks passed!
   Bytecode compiled 4164 files in 97ms
   lint: green (0.5 s)
   Bytecode compiled 4164 files in 89ms
   make: *** [Makefile:39: types] Error 139
