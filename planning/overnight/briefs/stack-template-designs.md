# Brief: designs for two more stack templates (the human's word, 2026-10-19): Java/Gradle and TypeScript/npm

## Goal

Today v1.1 ships one project template, for Python with uv (`template/`), and the demo `demo/todo-service/` on it. Write one design document per stack, so that its stories can be drafted later without new research: `planning/overnight/templates/java-gradle.md` (the human's work projects: Java, Gradle, run rootless under Podman at work, a corporate network) and `planning/overnight/templates/typescript-npm.md` (the first use: the Factory Timeline, a static page with pure-function modules in `C:/Dev/Projects/factory-timeline`, see its `docs/plan.md`). These are designs, not stories.

Each document covers, for its stack, the equivalent of every part of the Python template and of what the factory expects from a project:

1. The project commands the pipeline definition calls and their exact output contract (`<target>: green (<seconds> s)`, `check: green`, a JUnit report, the duplicates, documents and mutants reports), and how they map onto the stack's tool (Gradle tasks or a Makefile over them; npm scripts or a Makefile): read the Python template's `Makefile` and `factory/pipeline.yml`.
2. The checks: lint and format, types, layers (the project declares its layers, R8: ArchUnit, dependency-cruiser or similar), static security analysis, the secret scan, licences, tests with coverage at a threshold, duplicates and dead code, mutation testing (PIT, Stryker) with a per-story run as F0024 designs it, and the equivalent of leaving structural tests out of mutation runs.
3. The factory's interfaces it touches: does the make-based project-commands class (R11) suffice, or does the stack need its own implementation? The write paths and protected paths of its pipeline definition; what F0023's `not_read` would be and whether reuse is safe (pinned dependencies: Gradle lockfiles and the dependency cache, `package-lock.json`); the tool paths the kernel's write guard must allow (`~/.gradle`, `~/.m2`, `~/.npm`, `node_modules`), and caches that must not let one run change the next.
4. The image: what it must add (a JDK and the Gradle wrapper, or Node and npm), sizes, pinned versions, and whether one image holds all stacks or one image per stack; offline and proxy needs at work (a corporate Maven or npm mirror, a proxy, certificates), from the Podman notes in `C:/Users/pasca/.claude/projects/C--Dev-Projects/memory/podman-at-work.md`.
5. The agents: what the shipped agents' texts assume of Python (`claude/agents/*.md`, `CLAUDE.md`'s *Tests* and *Checks* rules) and what must change or move into the project's own `CLAUDE.md`, skills or project agents (F0022's draft, `planning/overnight/stories/F0022-a-project-brings-its-own-skills-and-agents/`).
6. A demo for the stack (the todo service again?) and how its stories would read.
7. The order of the stories to build it, small and generic, and the open questions for the human with recommended answers.

Name every tool with the version you would pin, marked "to be checked" where you cannot confirm it offline.

## Inputs

`template/` (all of it), `demo/todo-service/`, `factory/pipeline.yml`, `Makefile`, `pyproject.toml`, `CLAUDE.md`, `docs/project-guide/README.md` and `docs/project-guide/processes-and-checks.md`, `docs/operator-guide.md`, `image/Dockerfile`; the drafts of F0022, F0023 and F0024 under `planning/overnight/stories/`; `C:/Dev/Projects/factory-timeline/docs/plan.md`; the Podman note named above.

## Not

No git commands; no network; no sub-agents; no paid model call; no file other than the two outputs and your temporary folder `C:/Users/pasca/AppData/Local/Temp/tmpldes` (removed at the end); never read a token or key file.

## Reply

Per stack: the shape in five lines, the biggest risk, and the open questions.
