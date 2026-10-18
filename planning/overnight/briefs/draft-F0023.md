# Brief: draft F0023, the engine skips a project command whose result for that commit is known (step 7 of the order after F0011)

## Goal

Write the feature `F0023-a-known-result-is-not-checked-again` and its stories (one to three) so that v1.1 can build them after F0022 (a project brings its own skills and agents). The content is the human's, in `planning/overnight/restructure-after-f0011.md`: step 7 of "The order of the work after F0011" (the engine skips a project command whose result for that commit is already known, the docs stage's `make check` on code the documenter cannot change; then a new image and a short smoke run), the lever in "The time `make check` takes" (skip a `make check` on a commit whose result is already known: the coder's, the documenter's and the factory's runs on the same commit), and the telemetry line "the count of `make check` runs on one commit". Measure first: from the journals and cost records of F0019 and F0021 under `factory/features/*/done/`, count how often the factory's own check after a stage ran on a commit (tree) that an earlier check had already passed, and give the expected saving in the feature's description. Key the known result on what the command reads (the commit's tree, or the tree of the files the command depends on), never on the stage; a failed result is never reused; say what invalidates a known result (a merge of main, a changed pipeline definition, a new image).

## Inputs (read these first)

- The plan: `C:/Dev/Projects/factory-rf/planning/overnight/restructure-after-f0011.md` (step 7, "The time `make check` takes", "Telemetry in v1.1").
- How the factory runs project commands today: the project-commands interface and its make-based implementation (`src/factory/application/` and `src/factory/adapters/`), the stage protocol that runs `checks` and `reports` after a role (`src/factory/application/stage.py` and the handlers), the pipeline definition (`factory/pipeline.yml`: `checks`, `reports`, `time_limit`), where results are recorded (journal records, `.costs.jsonl`), and the git wrapper (tree ids).
- Their tests, above all the stage-run and pipeline-definition tests.
- F0020 and F0022, built before F0023: `planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/`, `planning/overnight/stories/F0022-a-project-brings-its-own-skills-and-agents/`. F0021 (in progress): `factory/features/F0021-the-factory-records-what-the-human-did/`. Say where F0023 touches what they change.
- The forms and rules: `factory/pipeline.yml`, `factory/story-form.md`, `factory/feature-form.md`, `CLAUDE.md`, `docs/project-guide.md`, `docs/operator-guide.md`, `docs/decisions.md`.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002) under the kernel's write guard, with no paid call. The plan's short smoke run after the feature is paid: put it under *The human's changes* as a check after the feature, not in a smoke test.
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`, `claude/` if it is outside) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Keep it small and generic (the human's rule: solid over clever): the engine learns no target names and no stage names; a skipped command is recorded as skipped, with the result it reused, so no check is silenced.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0023-a-known-result-is-not-checked-again/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0023-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run --project C:/Dev/Projects/factory-rf factory-check-story <path>`, run from the temporary folder `C:/Users/pasca/AppData/Local/Temp/f23draft` (and nowhere else), which holds a copy of the story laid out as `factory/features/F0023-.../backlog/` beside a copy of `factory/story-form.md`; every line must end in `: ok`. If the check needs the Landlock adapter, which does not import on Windows, stub it in that temporary folder only.

## Not

No git commands. No network calls. No file outside `planning/overnight/stories/F0023-a-known-result-is-not-checked-again/` and the temporary folder. Do not start sub-agents. No paid model call of your own. Remove the temporary folder when done (if a removal is refused, say so). You may look inside v1.1's container read-only with `docker exec factory-self-factory-1 <command>` (set `MSYS_NO_PATHCONV=1` first); change nothing there, and never read a token or key file.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (the key of a known result and what invalidates it above all), the measured count and saving, and anything you could not place.
