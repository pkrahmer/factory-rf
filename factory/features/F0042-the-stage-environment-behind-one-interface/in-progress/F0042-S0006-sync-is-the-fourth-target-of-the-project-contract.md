---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-24T17:07:07.779610Z'
  lease_duration: 60
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
