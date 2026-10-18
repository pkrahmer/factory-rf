# Brief: draft F0019, the write guard by the kernel (plan step 5a), for v1.1 to build

## Goal

Write the feature `F0019-the-write-guard-by-the-kernel` and its stories so that v1.1, which builds this repository itself since the handover of 2026-10-18 (commit `3bcee441`), can build plan step 5a: every agent run starts through a wrapper that restricts the run's writes, and those of every child process, to the stage's write paths plus what the run itself needs, by Landlock; the Claude Code hook `factory-guard` stays for one shakedown-sized run as a cross-check and is removed in a later story; the undo stays as the backstop.

This is the first feature drafted for v1.1's own pipeline: write it against v1.1's forms (`factory/feature-form.md`, `factory/story-form.md`) and v1.1's shipped agents (`claude/agents/*.md`), not v1's (`factory/v1/` is history; do not use its `TICKET.md`, `FEATURE.md` or v1's skills).

## Inputs (read these first)

- The design and the probe: `planning/overnight/write-guard-landlock-2026-10-17.md` (the human's discussion of 2026-10-17: what is allowed and refused, the per-run temporary folder, the agent's home, ABI 7 on this machine's WSL2 kernel, the open points) and any probe files it names.
- The plan: `planning/overnight/restructure-after-f0011.md`, step 5a and 5b (opencode comes after and relies on this guard), and the night log's rows of 2026-10-18 (the handover, the umask fault and its fix `27bdaa73`, F0018).
- v1.1's code that starts an agent run and guards it: `src/factory/adapters/claude_runtime.py` (the `sudo ... timeout --signal=KILL` command line and the login shell), `src/factory/adapters/process.py`, the guard (`src/factory/entry/guard.py`, `factory-guard`), the undo and write-path services (`src/factory/application/write_paths.py`, `undo.py`), the sealed runs (`run_sealed`), the preflight and its items, the stops, the image (`image/Dockerfile`, `image/entrypoint.sh`, `image/compose.yml`), and the tests that pin each (search `tests/`).
- The forms and rules v1.1 applies: `factory/pipeline.yml` (write paths per role: the coder `src/*`, `image/*`, `template/*`, `claude/*`; the tester `tests/*`; the documenter `README.md`, `docs/*`; time limits and leases), `factory/story-form.md`, `factory/feature-form.md`, `claude/agents/*.md` (above all intake, tester, coder, reviewer), `CLAUDE.md` (Architecture: wrappers R5, interfaces R6, the one process module; Tests; Not without asking), `docs/project-guide.md` and `docs/decisions.md` where they touch the guard, the runtime, the preflight and the image.
- How v1.1's own first feature went: `factory/features/F0018-the-documents-name-the-handover/` (`feature.md`, the stories in `done/`, the acceptance report): the intake asks when a story edits something its feature's Scope does not name, so name every touched document and module in the Scope.

## The content (the human's design of 2026-10-17)

1. A start wrapper for every agent run that applies Landlock rules: write allowed on the stage's write paths in the checkout (folders for folder patterns, single existing files for file patterns such as the work item), a temporary folder of the run's own (`TMPDIR` pointing to it, removed by the factory after the run), the parts of the agent's home that Claude Code, `uv` and pip write, and the project's `.venv` as the probe finds them; everything else refused (the rest of `/work`, `/state`, the shared `/tmp`). Then it executes the runtime. Say where the wrapper lives (a module and an entry point in the image, reached through the one process module), how it gets the rules (arguments, a file in `/state/runs`), and how it fails closed.
2. A preflight item: Landlock available with the ABI the rules need; without it the factory stops (a new stop) or falls back to the hook: recommend one and give it as a decision for the human.
3. What the agent sees on a refused write (`Permission denied`) and the line of its instructions that explains it.
4. The cross-check: the hook stays; a later story (not in this feature unless the split puts it last) removes it after one shakedown-sized run in which it refused nothing the kernel did not.
5. The open points of the design (a path that does not exist when the run starts; access rights per ABI; files the agent creates in an allowed folder), each answered or given as a decision.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes, see `factory/pipeline.yml`) and a budget of a few dollars; size them so.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002; tests run under the `Makefile`'s umask 022).
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before. A new dependency (a Landlock binding, if any) is the human's change; prefer the standard library (`ctypes` and the three Landlock system calls) and say why.
- Can the Landlock rules be tested in the test suite (in the container, as the test user)? Say how, and what can only be checked by the smoke test or a real agent run.
- No secret-like key with a value in a story's text, and no 32-character hex value.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0019-the-write-guard-by-the-kernel/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0019-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run --project C:/Dev/Projects/factory-rf factory-check-story <path>` from a temporary copy laid out as `factory/features/F0019-.../backlog/` beside a copy of `factory/story-form.md` (the check reads the form from `factory/` of the current folder); every line must end in `: ok`.

## Not

No git commands at all, not even read-only ones. No network calls. No file outside `planning/overnight/stories/F0019-the-write-guard-by-the-kernel/`. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and remove everything you create (if a removal is refused, say so; do not ask anyone to do it for you). You may look inside v1.1's container read-only with `docker exec factory-self-factory-1 <command>` (set `MSYS_NO_PATHCONV=1` first); change nothing there, and never read a token file.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (the fallback without Landlock above all), how the rules are tested, and anything you could not place.
