# Brief: pre-check {{STORY}} ({{NAME}}), round {{ROUND}}, with v1.1's own roles

## How to fill in

Copy this file into the helper's prompt and replace every placeholder:

- `{{FID}}`: the feature id; `{{SLUG}}`: its folder under `planning/overnight/stories/` (or `factory/features/` for a story the acceptance proposed).
- `{{STORY}}`: the story id, for example `F0031-S0002`; `{{NAME}}`: its short plain name.
- `{{ROUND}}`: 1 for a fresh draft; 2 and on after edits. From round 2, the helper also reads the earlier rounds' reports and reports findings only.
- `{{SOURCES}}`: what to read beyond the standing inputs: the code and tests the story touches, the drafter's brief, other stories it must fit with.
- `{{CHECK}}`: the points to check in particular (a cause the feature names, a decision, an order with other stories), or "none".
- `{{TEMP}}`: the helper's exact temporary folder, a short name, for example `C:/Users/pasca/AppData/Local/Temp/f31pre`.

Delete this section before you hand the brief over.

## Goal

Play v1.1's intake exactly on {{STORY}} ({{NAME}}): the shipped `claude/agents/intake.md` with `factory/story-form.md`, both as they are on `main` now. Then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer would stop it. End with one verdict line and the exact replacement text for every edit. A refusal at the intake costs cents; one at the third review round costs dollars and the human's attention.

Check in particular: {{CHECK}}

## Inputs (read these; nothing else unless a step needs a named source file)

- The story: `planning/overnight/stories/{{SLUG}}/backlog/{{STORY}}-*.md`, and the feature's `feature.md` (scope, the human's changes, decisions).
- {{SOURCES}}
- `claude/agents/*.md` (the roles), `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml` (write paths, time limits), `CLAUDE.md`.
- `docs/project-guide/README.md` and the guide files it names, to check the docs criterion.
- From round 2: the earlier reports `planning/overnight/precheck/{{STORY}}-*.md` and the closing decision of `feature.md` that names the human's answers.

## What to check

- **Intake, step by step** (steps 2 to 4 of `intake.md`): the Interface names concrete modules and signatures; every criterion is testable by one test function without further decisions; every smoke test command is runnable and every `Expect:` is checkable.
- **Every clause of every rule** in the Description, the Interface and the feature's decisions has its own criterion, on both sides: an ordering, the second branch of an "or", a "when longer than", the value for every kind an enum names, a limit with its number.
- **Code facts against today's `main`**: every module, class, function, fixture, test and line number the story names exists and says what the story claims. Check each named test against the structural tests that pin it (`tests/application/test_interfaces.py`, the layer contracts, `mypy --strict`, ruff with the project's rules, coverage at 90 %).
- **Write paths**: each file a stage must write is inside that role's write paths in `factory/pipeline.yml`. What is not is a human's change in `feature.md`, with its order.
- **Leaves**: every earlier test the story changes is named in its Interface with a decision of the feature, or falls under the standing leave in `CLAUDE.md`.
- **Size**: the story fits one coder's run and one documenter's run within their 40-minute time limits and a few dollars.
- **The smoke test**: run it against today's code where it can run before the story, and against a small prototype of the story where that is cheap. It never passes `-q` to pytest (`pyproject.toml` already sets it; at `-qq` the summary line goes). Every file it names exists or is made by the story.
- **Mutation testing** is never part of a story or its acceptance: a criterion, smoke test or docs line that runs `make mutants` is a finding.
- **Round 2 and on**: what the edits may have broken (a criterion renumbered but still cited by its old number, a leave that no longer matches, an `Expect:` that no longer follows, a docs file or section that does not exist), and anything an earlier verdict asked for that is missing.

## How to run things

The suite and `factory-check-story` do not run on Windows. Run them in throwaway containers, on a copy:

1. Copy the repository into `{{TEMP}}/repo`, leaving out `./.git`, `./image/secrets`, `./.venv` and `./mutants`. Convert the copy's text files to LF line endings.
2. `factory-check-story` only accepts paths under `factory/features/`: place a copy of the story at `factory/features/{{SLUG}}/backlog/` inside that copy.
3. Run each command as:

   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --network none --entrypoint /bin/sh \
     -v {{TEMP}}/repo:/src -w /src factory-self-factory -c '<command>'
   ```

   If the image lacks a tool you need, say so in the report; never install it from the network. The image has no pytest: mount the host's pure-Python test packages read-only from their place (`-v C:/Dev/Projects/factory-rf/.venv/Lib/site-packages:/hostsite:ro`) and link into a folder on `PYTHONPATH` only the pure-Python packages the image lacks (pytest and its plugins), never the whole host folder: the host's Windows `pydantic_core` would otherwise win over the image's. Never point `uv` or `UV_PROJECT_ENVIRONMENT` at `factory-self-factory-1`'s `.venv`: it is the instance's own, and a sync there by another user can leave files the factory cannot replace (`self` stopped on 2026-10-19 on such a file).

Never run anything in the running instance `factory-self-factory-1`, and mount no instance volume and no secret.

## Output

One file: `C:/Dev/Projects/factory-rf/planning/overnight/precheck/{{STORY}}-{{ROUND}}.md`, in the shape of the earlier reports there:

- `# Pre-check {{STORY}}, round {{ROUND}}: {{NAME}}`, then one line on what you checked against.
- `## What I ran`: the form check's result, the code facts with paths and line numbers, the prototype and smoke test runs with their real output.
- `## Intake outcome (as v1.1's intake would end)`: `question` with numbered questions, or the `accepted` entry with one line each for the Interface, the criteria, the smoke test, the architecture and the scope.
- `## Predicted later stops, by role`: tester, coder, reviewer, documenter, smoke tester, acceptance reviewer, each with its reason or "none".
- `## Points for the human`: each with options and a recommended answer, or "none".
- `## Verdict`: one line, `` `{{STORY}}: accepted at intake as drafted.` `` or `` `{{STORY}}: <question at intake | accepted at intake>; edit 1 required (<reason>); edit 2 optional.` ``. Then each edit by number, marked required or optional, naming its section, as "replace" with the exact old text and "with" the exact new text in fenced blocks.

From round 2: findings only, no restatement of earlier rounds.

## Not

- Never open, read, print or copy anything under `image/secrets/`, and never read a token or key file.
- Temporary files only in `{{TEMP}}`, nowhere else. Delete `{{TEMP}}` when done; if a removal is refused, say so.
- No git commands in the repository. No commit, no push. No network calls.
- Do not change the story, `feature.md` or any other file. Write only the output file.
- No sub-agents. No paid model call of your own.

## Reply

The verdict line; each required or optional edit in one line; the points for the human with recommended answers. Every id with its short name.
