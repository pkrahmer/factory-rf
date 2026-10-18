# Brief: pre-check F0022 round 1 with v1.1's own roles (two stories)

## Goal

For each story of `F0022-a-project-brings-its-own-skills-and-agents`, play v1.1's intake exactly (the shipped agent `claude/agents/intake.md` with the story form `factory/story-form.md`), then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer (`claude/agents/*.md`) would stop it, and give it one verdict line. The stories were written by the session's drafting agent and have not been checked against v1.1's roles. Also judge the feature's "human's changes" and its decisions, above all: a project agent at `origin/main` replaces the shipped one whole and a faulty one never falls back (decisions 1 to 3); `Skill` for all seven agents and in `claude/settings.json`'s `allow` (decisions 7, 8); R15 in the Rules (decision 9); the agent's home closed by the entrypoint (decision 10, and whether its `rm -rf` under `set -e` is safe on reused volumes); opencode leaving `Skill` out (decision 11) against F0020's stories as drafted.

For every test a story names or describes, check it against the built code and the tests that pin it (structural tests such as `tests/test_claude_files.py`, `tests/test_claude_agent_texts.py`, `tests/shipped_agents.py`, `tests/test_model_configuration.py`, `tests/test_compose.py`, the protected-path tests, the wiring tests, the layer contracts, fixture order, `mypy --strict`, ruff with the project's rules, coverage at 90 %); run every smoke-test command against today's code where it can run before the story, and check that every file it names exists or is made by the story.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0022-a-project-brings-its-own-skills-and-agents/feature.md` and the two stories under `backlog/`.
- The brief the drafter worked from: `planning/overnight/briefs/draft-F0022.md`; the plan's sections in `planning/overnight/restructure-after-f0011.md` ("A project's own skills", "A project's own agents").
- v1.1's roles and forms: `claude/agents/*.md`, `claude/settings.json`, `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml`, `Makefile`, `image/` (the entrypoint).
- The code and tests each story touches: the agent definition reader and its port, the loader, the task composer, the preflight, `boundaries.py`, `wiring.py`, `src/factory/domain/paths.py` (the protected paths), `src/factory/adapters/claude_runtime.py`, and the test modules each story extends or changes.
- F0020 (built before F0022) and F0021 (in progress; S0005 changes `claude/agents/reviewer.md`): `planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/`, `factory/features/F0021-the-factory-records-what-the-human-did/`. Say where F0022 touches what they change and whether a story needs a note.

## Check in particular

- The order and sizing: each story fits a coder's 40-minute `time_limit` within a 60-minute lease and a few dollars.
- Every behaviour the Interface or a decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes another story's tests beyond the standing leave names them, and `feature.md` gives the leave.
- Each file a stage must write is inside that role's write paths in `factory/pipeline.yml` (`claude/*`, `image/*` included?); what is not is a human's change, with its order.
- The protected paths: does adding `factory/agents/*` collide with the work item's own files or the pipeline's writes under `factory/`?

## Output

One file per story, `F0022-S000N-1.md` (N 1 and 2), and `F0022-feature-1.md` for the feature, its human's changes and decisions, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1.1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands at all. No network calls. No file other than your outputs. Do not change the stories or `feature.md`. Do not start sub-agents. No paid model call of your own. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in the temporary folder `C:/Users/pasca/AppData/Local/Temp/f22pre` and nowhere else, and remove it when done (if a removal is refused, say so). `factory-check-story` imports the Landlock adapter, which fails on Windows: stub it in that temporary folder, or run smoke tests and checks that need Linux in a throwaway container of v1.1's image (`docker run --rm --entrypoint /bin/sh -v <a copy of the repository in the temporary folder>:/src factory-self-factory -c '...'`, `MSYS_NO_PATHCONV=1` first), never in the running instance `factory-self-factory-1`, which is building; mount no instance volume and no secret, and never read a token or key file.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes or the decisions.
