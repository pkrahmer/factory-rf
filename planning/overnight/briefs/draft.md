# Brief: draft feature {{FID}} ({{NAME}}) and its stories

## How to fill in

Copy this file into the helper's prompt and replace every placeholder:

- `{{FID}}`: the feature id, for example `F0033`.
- `{{NAME}}`: its short plain name, for example "the reviewer may rewrite a stale Description".
- `{{SLUG}}`: the folder name, `{{FID}}-<the name in lowercase words joined by hyphens>`.
- `{{GOAL}}`: the human's design, each requirement numbered. Requirements the human adds later go here before the drafter starts, not into the stories afterwards.
- `{{SOURCES}}`: what to read beyond the standing inputs: the plan step, earlier features' journals, the code and tests the feature touches.
- `{{TEMP}}`: the helper's exact temporary folder, a short name, for example `C:/Users/pasca/AppData/Local/Temp/f33draft`.

Delete this section before you hand the brief over.

## Goal

Write `feature.md` and every story of {{FID}} ({{NAME}}), so that v1.1 can build each story in one run through intake, tests, coding, review, docs and smoke test. Where the feature fixes a fault, find its cause first, in the code and the records, and say it in `feature.md`; then the fix.

{{GOAL}}

## Inputs (read these first)

- {{SOURCES}}
- `CLAUDE.md`, above all *Architecture*, *Tests* and "Not without asking".
- `factory/feature-form.md`, `factory/story-form.md` and `factory/pipeline.yml` (the roles, their write paths and time limits).
- `claude/agents/intake.md`: the checks your stories must pass.
- `docs/operator-playbook.md`, section 2 (a feature, from plan step to acceptance).
- `docs/project-guide/README.md` and the guide files it names for the domains touched; `docs/operator-guide.md`; `docs/decisions.md`.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour the Description, the Interface or a decision states has its own criterion. Every rule has its failing side too. Every limit is stated with its number, and both sides are tested. The sides of one rule are rows of one parametrized test.
- Test data is valid under the built code. Every file a smoke test or a test names exists or is made by the story.
- A smoke test runs in v1.1's container (Linux, as the factory user, umask 002, nothing listening) under the kernel's write guard, with no paid call. Its `Expect:` is met exactly by the built code.
- A smoke test never passes `-q` to pytest: `pyproject.toml` already sets it, and at `-qq` pytest prints no summary line.
- Mutation testing is never part of a story or of the acceptance. No criterion, smoke test or docs line runs `make mutants`; sweeps are the human's.
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md` (*Tests*), names them in its Interface, and `feature.md` gives the leave as a numbered decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `uv.lock`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`) goes under *The human's changes* in `feature.md`, with exact lines and the story it must come before or after.
- Interfaces are abstract base classes, and every implementation inherits its interface, fakes included. No `typing.Protocol` for the factory's own interfaces.
- Use only the dependencies in `pyproject.toml` and the standard library. No new top-level package.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Every product decision you take goes into `feature.md` as a numbered decision, naming its story.
- Keep it small (the human's rule: solid over clever). Fix the cause, not the symptom. No new mechanism unless the goal asks for it.

## How much a story fixes in advance (the human, 2026-10-20)

Write what must be true, not how to build it. Fixed details that turn out wrong (a test's user, an output format, a call path) stopped stories with questions; the tester, the coder and the reviewer decide them better on the spot.

- **Fix in the story:** the behaviour and its rules with their edge cases and limits; every contract another story builds on (a public name, a signature, a file another story reads); the earlier tests the story may change, by exact name, for the leave; the documents to change; every decision that is the human's (security trade-offs, architecture, scope).
- **Leave to the agents:** private helpers and internal structure; the layout of the test files and the names of new tests; test-row tables where a rule already states what must hold; the exact wording of small outputs that nothing else reads.
- A criterion names an exact value only where the value is the rule (a limit, a message another program or the human reads).

## Write

Only the folder `C:/Dev/Projects/factory-rf/planning/overnight/stories/{{SLUG}}/`:

- `feature.md`, in the sections of `factory/feature-form.md`.
- `backlog/{{FID}}-S000N-<slug>.md` for each story, in the sections of `factory/story-form.md`, with an empty Journal.

## Check each story

`factory-check-story` takes only a path `factory/features/<dir>/<backlog|in-progress|done>/<file>.md`, and the suite and the check do not run on Windows. So check in a throwaway container, on a copy:

1. Copy the repository into `{{TEMP}}/repo`, leaving out `./.git`, `./image/secrets`, `./.venv` and `./mutants`. Convert the copy's text files to LF line endings.
2. Inside that copy, place your drafts under `factory/features/{{SLUG}}/backlog/`.
3. Run the check in a throwaway container of the image:

   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --network none --entrypoint /bin/sh \
     -v {{TEMP}}/repo:/src -w /src factory-self-factory -c 'factory-check-story factory/features/{{SLUG}}/backlog/<file>.md'
   ```

   Every line must end in `: ok`. Fix the draft in `planning/` and check again.
4. Run each smoke test you can against today's code the same way, to see that it runs and what it prints today.

Never run anything in the running instance `factory-self-factory-1`. You may look inside it read-only with `MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 <command>`; change nothing there.

## Not

- Never open, read, print or copy anything under `image/secrets/`, and never read a token or key file.
- Temporary files only in `{{TEMP}}`, nowhere else: not a drive's root, not the repository. Delete `{{TEMP}}` when done; if a removal is refused, say so.
- No git commands in the repository. No commit, no push. No network calls.
- No file outside `planning/overnight/stories/{{SLUG}}/` and `{{TEMP}}`.
- No sub-agents. No paid model call of your own.
- Do not change `CLAUDE.md`, the forms, the agents or any other feature.

## Reply

At most 25 lines: the stories, one line each (id, short name, number of criteria); the human's changes; the decisions you took for the human (a fault's cause above all); open questions; anything you could not place. Every id with its short name.
