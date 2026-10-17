# Brief: draft the todo demo, `demo/todo-service/`, in v1.1's form (plan step 3)

## Goal

The plan's step 3: run 4's to-do service (three features, eight stories, built by v1 in its run 4) rewritten by hand into v1.1's forms and words, as the first demo v1.1 ships. It is the input of the shakedown run (step 4) and of the baseline todo run (step 10), so a story here must be one v1.1's pipeline can build first-pass, and the whole demo must pass the demo check F0012-S0023 builds. The human decided its shape on 2026-10-17 (the plan's section "The demo, shipped with v1.1"). You write the files in a staging folder; the session commits them into `demo/` after F0012's acceptance, as the human's change.

## Inputs

- The plan: `C:\Dev\Projects\factory-rf\planning\overnight\restructure-after-f0011.md`, the order's steps 3, 4 and 10 and the sections "The demo, shipped with v1.1", "Telemetry in v1.1", "Disk space, fixed in v1.1".
- The source: v1's demo, `C:\Dev\Projects\factory\demo\` (its `README.md`, `project\` with `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock` and whatever else it holds, and `features\` with F0001-todo-service, F0002-operations, F0003-search). Keep what each story builds and its criteria's substance; change the form and the words.
- The target form, v1.1's: `C:\Dev\Projects\factory-rf\docs\project-guide.md` (the sections on work items: "Identity, order and places of work items", "The data of a work item", "The feature acceptance", "Reading and writing a work item file", "The form check of a story", "The story form check"), `docs\operator-guide.md` (how an operator starts a project and a run), the glossary words in `CLAUDE.md` (*Vocabulary*) and `docs\decisions.md`, `template\CLAUDE.md`, `template\factory\pipeline.yml`, and the code that reads these files (`src\factory\adapters\work_item_markdown.py`, `src\factory\entry\check_story.py`, `src\factory\adapters\pipeline_yaml.py`).
- What F0012 adds before the demo lands (treat as built): the drafts under `C:\Dev\Projects\factory-rf\factory\features\F0012-housekeeping\drafts\`, above all S0023 (the demo check: the exact files and findings it requires, including `project/factory/story-form.md`), S0029 (the template `Makefile`, the starting point of the project's `Makefile`), S0028 and S0011 (the lessons in `template/CLAUDE.md`), S0012 and S0013 (target times and the record of every project command: the `<target>: green (<seconds> s)` lines), and FEATURE.md's decisions.
- The lessons of the v1.1 build: `C:\Dev\Projects\factory-rf\planning\lessons-for-the-skills.md` (the Python and general rows belong in the demo's `project/CLAUDE.md` where the template does not already carry them).

## Write (all under `C:\Dev\Projects\factory-rf\planning\overnight\demo\`)

1. `README.md`: the index of `demo/`, one line per demo (kind, stack, what it builds, stories, the run it is the baseline of), naming `` `todo-service/` ``, and what every demo holds (`README.md`, `project/`, `features/`).
2. `todo-service/README.md`: what it builds, what it needs, how to run it with v1.1 (from the operator guide), the prompt for the session that plays the human (adapted from v1's demo README to v1.1's words and stops), what a run looks like and what run 4 cost, per story and in total, where v1's demo or its run records say so.
3. `todo-service/project/`: the empty project the factory builds into: `CLAUDE.md` (from the template and v1's demo project), `Makefile` (from S0029's template `Makefile` with the project's source folder and layers command filled in; `check`, `lint`, `test`, `duplicates`, `mutants`; each target's `<target>: green (<seconds> s)` line, pytest-xdist, the JUnit report), `pyproject.toml` with every development dependency the targets need, pinned, `uv.lock` generated with `uv lock` from that `pyproject.toml`, `factory/pipeline.yml` (from the template, loadable by `RuamelPipelineDefinitionReader().parse`), `factory/story-form.md` (as S0023 requires), and any skeleton v1's demo project holds that the first story needs (a package with an empty `__init__.py`, an empty `tests/` package) so that `make check` is green on the empty project.
4. `todo-service/features/<feature>/feature.md` and `todo-service/features/<feature>/backlog/<story>.md` for the three features and eight stories, in v1.1's work item form and identifiers, each story passing v1.1's story check (`backlog_story_findings` as S0023 states it, or today's `check_story` where S0023's function does not exist yet).
5. `todo-service/NOTES.md` (staging only, not committed into `demo/`): what you changed from v1's demo and why, each choice you took for the human marked "taken for the human, to confirm", and the commands you ran with their outputs.

## Rules

- A story must be buildable first-pass by v1.1's pipeline: every behaviour its own criterion, both sides of every rule as rows of one parametrized test, test data valid under the code the earlier stories build, a Demo whose `Expect:` the built code meets exactly, no doubled `-q`, each story within the coder's budget and a 60-minute lease as the template's `pipeline.yml` sets them.
- Check what you can run: `make check` on the empty `project/` (in a copy outside the staging folder, so that no `.venv`, `.reports` or caches land in it), the pipeline reader on `pipeline.yml`, the story check on every backlog story. Report each command's last lines in NOTES.md.
- v1.1's words only (the glossary); no word of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section.
- Leave no file behind outside the staging folder; use temporary directories that remove themselves.

## Not

- No git commands. No file outside `C:\Dev\Projects\factory-rf\planning\overnight\demo\`. Do not change v1's demo, the F0012 drafts or any code.

## Reply

The tree you wrote, one line per story, the checks you ran with their results, the choices taken for the human, and anything you could not place.

Model: opus.
