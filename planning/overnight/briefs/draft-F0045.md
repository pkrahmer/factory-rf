# Brief: draft feature F0045 (smaller items of the candidates list) and its stories

## Goal

Write `feature.md` and the stories of F0045, so that the factory can build each story in one run through intake, tests, coding, review, docs and smoke test. F0045 is the fourth and last feature of v1.2 (`planning/v1.2-plan.md`, section "F0045"; read the plan whole). It is built by the instance `vm` on the VM with the `container` environment, after F0044 (the layers go), which is drafted under `planning/overnight/stories/F0044-the-layers-go/` (read its `feature.md`, above all decisions 1 to 29, and every story: many candidate items fall with F0044, and F0045 must build on the code as F0044 leaves it, not as it is today). F0042 (the stage environment behind one interface) is under `factory/features/F0042-the-stage-environment-behind-one-interface/`; F0043 (the machine and the stage image) under `planning/overnight/stories/F0043-the-machine-and-the-stage-image/`.

The items, numbered:

1. **The six items of `planning/v1.2-candidates.md`, section "Smaller items noted on 2026-10-21"**: for each, decide from F0044's stories whether it falls with F0044 (then no story; say which F0044 story removes it, in a numbered decision) or stays (then a story, or part of one). The plan's F0045 section lists them.
2. **The three items of the section "For F0045, beside the six items above"** of the same file: the idle shutdown, an option off by default (as written there: its setting, what idle means, the wrapper, the one right `vm/setup.sh` gives only when it is used, the operator guide's text; decide the open point "a story waiting for the human counts as idle" as proposed there, as a numbered decision); the removal of the stall reason `left_branch` with the records contract's next major (after F0044's 3.0, so 4.0; say so); the two settings defaults that name v1.1's image, `FACTORY_CLAUDE_HOME` and `FACTORY_IMAGE_ID_FILE` (make them required or give them the VM's paths: decide, with the reason, as a numbered decision).
3. **Not in F0045:** the v1.3 candidate "the agents' project commands run through the factory" and anything the plan's "Not in v1.2" names.

Every story names the earlier tests it changes, by exact name where they exist today and by module and row where F0044 writes them; `feature.md` gives each story's leave as a numbered decision marked "the human's leave, to be given before the story starts".

## Inputs (read these first)

- `planning/v1.2-plan.md` whole; `planning/v1.2-candidates.md` whole.
- `planning/overnight/stories/F0044-the-layers-go/` (feature and all stories); `factory/features/F0042-the-stage-environment-behind-one-interface/` (feature and stories); `planning/overnight/stories/F0043-the-machine-and-the-stage-image/`.
- The acceptance reports the six items cite (`factory/features/F0039-*/`, `F0040-*/`, `F0038-*/`), and the code and tests each item touches, under `src/factory/` and `tests/`.
- `docs/operator-guide.md`, `docs/decisions.md` (the records contract's version rule), `docs/project-guide/README.md` and the guide files it names.
- `CLAUDE.md`, above all *Architecture*, *Tests* and "Not without asking".
- `factory/feature-form.md`, `factory/story-form.md` and `factory/pipeline.yml`.
- `claude/agents/intake.md`: the checks your stories must pass.
- `docs/operator-playbook.md`, section 2.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour the Description, the Interface or a decision states has its own criterion. Every rule has its failing side too. Every limit is stated with its number, and both sides are tested. The sides of one rule are rows of one parametrized test.
- Test data is valid under the built code. Every file a smoke test or a test names exists or is made by the story.
- A smoke test runs in the stage container of F0043 (`vm/Dockerfile`: Linux, no second user, no `sudo`, no podman, no zfs, no systemd, nothing listening), with no paid call; write it so it also runs in v1.1's container. So smoke tests check imports, texts and `--help` outputs, never a build or a VM. Its `Expect:` is met exactly by the built code; a removal is best smoke-tested by an import that fails (`... || echo gone`).
- A smoke test never passes `-q` to pytest: `pyproject.toml` already sets it, and at `-qq` pytest prints no summary line.
- Mutation testing is never part of a story or of the acceptance.
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md` (*Tests*), names them in its Interface, and `feature.md` gives the leave as a numbered decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `uv.lock`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`; read `factory/pipeline.yml` for the rest) goes under *The human's changes* in `feature.md`, with exact lines and the story it must come before or after.
- Use only the dependencies in `pyproject.toml` and the standard library. No new top-level package.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Every product decision you take goes into `feature.md` as a numbered decision, naming its story.
- Keep it small (the human's rule: solid over clever). No new mechanism unless the goal asks for it.

## How much a story fixes in advance (the human, 2026-10-20)

Write what must be true, not how to build it. Fix in the story: the behaviour and its rules with their edge cases and limits; every contract another story builds on; the earlier tests the story may change, by exact name; the documents to change; every decision that is the human's. Leave to the agents: private helpers and internal structure; the layout of the test files and the names of new tests; the exact wording of small outputs that nothing else reads. A criterion names an exact value only where the value is the rule.

## Write

Only the folder `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0045-smaller-items-of-the-candidates-list/`:

- `feature.md`, in the sections of `factory/feature-form.md`.
- `backlog/F0045-S000N-<slug>.md` for each story, in the sections of `factory/story-form.md`, with an empty Journal.

## Check each story

`factory-check-story` takes only a path `factory/features/<dir>/<backlog|in-progress|done>/<file>.md`, and the suite and the check do not run on Windows. So check in a throwaway container, on a copy:

1. Copy the repository (with robocopy and absolute `/XD` paths: `C:\Dev\Projects\factory-rf\.git`, `...\image\secrets`, `...\.venv`, `...\mutants`; then check that `image/secrets` is absent in the copy) into `C:/Users/pasca/AppData/Local/Temp/f45draft/repo`, leaving out `./.git`, `./image/secrets`, `./.venv` and `./mutants`. Convert the copy's text files to LF line endings.
2. Inside that copy, place your drafts under `factory/features/F0045-smaller-items-of-the-candidates-list/backlog/`.
3. Run the check in a throwaway container of the image:

   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --network none --entrypoint /bin/sh \
     -v C:/Users/pasca/AppData/Local/Temp/f45draft/repo:/src -w /src factory-self-factory -c 'factory-check-story factory/features/F0045-smaller-items-of-the-candidates-list/backlog/<file>.md'
   ```

   Every line must end in `: ok`. Fix the draft in `planning/` and check again.
4. Run each smoke test against today's code the same way: before the story it must print what the code prints today (say so), and its `Expect:` must be what it prints after the removal.

Never run anything in the running instance `factory-self-factory-1`. You may look inside it read-only with `MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 <command>`; change nothing there.

## Not

- Never open, read, print or copy anything under `image/secrets/`, and never read a token or key file.
- Temporary files only in `C:/Users/pasca/AppData/Local/Temp/f45draft`, nowhere else. Delete it when done; if a removal is refused, say so.
- No git commands in the repository. No commit, no push. No network calls.
- No file outside `planning/overnight/stories/F0045-smaller-items-of-the-candidates-list/` and the temporary folder.
- No sub-agents. No paid model call of your own.
- Do not change `CLAUDE.md`, the forms, the agents, `planning/v1.2-plan.md`, the runbook, F0042's, F0043's or F0044's files or any other feature.

## Reply

At most 30 lines: the stories, one line each (id, short name, number of criteria); the human's changes; the leaves (story and test count); the decisions you took for the human; open questions; anything you could not place. Every id with its short name.
