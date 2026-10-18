# Brief: draft F0022, a project's own skills and agents (step 6 of the order after F0011)

## Goal

Write the feature `F0022-a-project-brings-its-own-skills-and-agents` and its stories (two to four) so that v1.1 can build them after F0020 (opencode as a second agent runtime). The content is the human's, in `planning/overnight/restructure-after-f0011.md`, sections "A project's own skills" and "A project's own agents" (both of 2026-10-17), and step 6 of "The order of the work after F0011": a project's own skills and agents; then a new image and a short smoke run on the todo demo.

## Inputs (read these first)

- The plan: `C:/Dev/Projects/factory-rf/planning/overnight/restructure-after-f0011.md` (the two sections and step 6).
- The agents and how they are read: `claude/agents/*.md`, `src/factory/adapters/` (`FrontmatterAgentDefinitionReader` and its port), the preflight and the tick's checks of agent definitions (`src/factory/application/machine.py`, `preflight` code, `checkout_restore`, the stop reason `agent_definition_invalid`), the pipeline definition reader (it reads `factory/pipeline.yml` from `origin/main`: the model for reading `factory/agents/<role>.md` the same way), the protected paths (`security/`, the write guard's refusals, `factory/pipeline.yml`'s write paths) and the runtime that passes the tools (`src/factory/adapters/claude_runtime.py`).
- Their tests: `tests/test_claude_files.py`, `tests/test_claude_agent_texts.py`, `tests/test_model_configuration.py`, the reader's and the preflight's tests.
- F0020, which is built before F0022 and changes the runtime: `planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/` (`feature.md` and `backlog/`). Say where F0022 touches what F0020 changes (the tools list per runtime: does opencode load skills at all? If not, say so as a decision: skills only under the Claude runtime, or the story's scope).
- F0021, in progress now: `factory/features/F0021-the-factory-records-what-the-human-did/` (its S0005 changes `claude/agents/reviewer.md`; build on the text as it will be).
- The forms and rules: `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `CLAUDE.md`, `docs/project-guide.md`, `docs/operator-guide.md`, `docs/decisions.md`.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002) under the kernel's write guard, with no paid call. The plan's "prove it once" runs (an agent run with a skill, a project agent for `coder`) are paid: put them under *The human's changes* as a check after the feature, not in a smoke test.
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`, `claude/` if it is outside) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Keep it small and generic (the human's rule: solid over clever): a project agent replaces the shipped one whole, never extends it; the engine learns no agent's text.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0022-a-project-brings-its-own-skills-and-agents/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0022-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run --project C:/Dev/Projects/factory-rf factory-check-story <path>`, run from the temporary folder `C:/Users/pasca/AppData/Local/Temp/f22draft` (and nowhere else), which holds a copy of the story laid out as `factory/features/F0022-.../backlog/` beside a copy of `factory/story-form.md`; every line must end in `: ok`. If the check needs the Landlock adapter, which does not import on Windows, stub it in that temporary folder only.

## Not

No git commands. No network calls. No file outside `planning/overnight/stories/F0022-a-project-brings-its-own-skills-and-agents/` and the temporary folder. Do not start sub-agents. No paid model call of your own. Remove the temporary folder when done (if a removal is refused, say so). You may look inside v1.1's container read-only with `docker exec factory-self-factory-1 <command>` (set `MSYS_NO_PATHCONV=1` first); change nothing there, and never read a token or key file.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (opencode and skills above all), and anything you could not place.
