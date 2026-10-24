# Brief: draft feature F0044 (the layers go) and its stories

## Goal

Write `feature.md` and the stories of F0044 (the layers go), so that the factory can build each story in one run through intake, tests, coding, review, docs and smoke test. The feature is the third of v1.2; its design is decided by the human on 2026-10-24 and written in `planning/v1.2-plan.md` (read it whole first; the sections "What stays, what goes, what is new", "F0044", "The order and the cut-over", "The human's decisions" and "Inventory of what goes" are binding). F0044 is built by the instance `vm` on the VM with the `container` stage environment, after F0042 (the stage environment behind one interface) and F0043 (the machine and the stage image) are merged. F0042 is under `factory/features/F0042-the-stage-environment-behind-one-interface/` (10 of 15 stories merged; S0009 to S0012 and S0015 are still in `backlog/` or `in-progress/`: read them as the contracts that will be true); F0043 is drafted under `planning/overnight/stories/F0043-the-machine-and-the-stage-image/`. Read both features and all their stories: F0044 removes what they made unnecessary, and must not remove what they still use.

Requirements, numbered:

1. **One story per layer, in the plan's order:** the kernel's write guard (Landlock, `factory-confine`, `tool_paths`); the second user (`CommandUser`, the `sudo` chain, `env -i`, `agent-user`, `FACTORY_AGENT_USER`); the leftovers program and the process table reading; the fresh home; the undo; the checkout's hygiene; the inline environment and the Docker path; the documents. You may split a layer into two stories when one would not fit one coder's run, or merge two small ones; say why in `feature.md`. Read the code first (the plan's inventory is from 2026-10-24 and F0042's later stories may have moved things): every module, test, setting, stall reason, preflight item and document section a story removes is named by its exact path or name in that story.
2. **What stays** is stated in each story as a criterion with its test: what the `container` environment and the take still use from a removed layer's neighbourhood (for example the write paths keep their meaning through the take; the time limit stays through podman's `--timeout`, S0015's 255), so no removal breaks the VM instance.
3. **The leaves.** Every story names the earlier tests it deletes or changes, by exact module and test name, in its Interface; `feature.md` gives each story's leave as a numbered decision marked "the human's leave, to be given before the story starts" (the plan: "gets the human's leave in `feature.md` before it starts, as F0039's decision 14 did"). Read F0039's `feature.md` (decision 14) for the form.
4. **The human's changes** (outside every write path): `pyproject.toml` loses `factory-confine`; `factory/pipeline.yml` and the template lose `tool_paths`; `tests/test_make_search.py`'s allowed places and other structural tests; `CLAUDE.md` loses the rules about `sudo`, the umask and the second user; `image/` goes if no write path covers it. Each with its exact lines (as they stand today) and the story it must come before or after.
5. **The measures** of the plan go into the acceptance in `feature.md`: lines removed against lines added since the tag `v1.1`, the suite's running time, no stall reason and no stop reason that names a removed layer.

What this feature does **not** do: it builds no new mechanism, changes no agent text except where a removed layer is named in it (then it is the human's change), and touches nothing on GCP or the VM.

## Inputs (read these first)

- `planning/v1.2-plan.md` whole; `planning/v1.2-candidates.md`; `planning/overnight/gcp-prototype-results-local-2026-10-24.md`.
- `factory/features/F0042-the-stage-environment-behind-one-interface/` (feature and every story in `backlog/`, `in-progress/` and `done/`); `planning/overnight/stories/F0043-the-machine-and-the-stage-image/`.
- `factory/features/F0039-the-code-says-what-it-does-once/feature.md` (decision 14, the form of a leave); `factory/features/F0040-agent-code-never-runs-with-the-factory-s-rights/` and `F0041-the-old-hook-guard-is-removed/` (what the second user and the guard are, and how a removal feature was split before).
- The code the plan's inventory names, under `src/factory/` and `tests/`; `image/`; `pyproject.toml`; `factory/pipeline.yml`.
- `docs/operator-guide.md`, `docs/decisions.md`, `docs/project-guide/README.md` and the guide files it names.
- `CLAUDE.md`, above all *Architecture*, *Tests* and "Not without asking".
- `factory/feature-form.md`, `factory/story-form.md` and `factory/pipeline.yml` (the roles, their write paths and time limits).
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

Only the folder `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0044-the-layers-go/`:

- `feature.md`, in the sections of `factory/feature-form.md`.
- `backlog/F0044-S000N-<slug>.md` for each story, in the sections of `factory/story-form.md`, with an empty Journal.

## Check each story

`factory-check-story` takes only a path `factory/features/<dir>/<backlog|in-progress|done>/<file>.md`, and the suite and the check do not run on Windows. So check in a throwaway container, on a copy:

1. Copy the repository (with robocopy and absolute `/XD` paths: `C:\Dev\Projects\factory-rf\.git`, `...\image\secrets`, `...\.venv`, `...\mutants`; then check that `image/secrets` is absent in the copy) into `C:/Users/pasca/AppData/Local/Temp/f44draft/repo`, leaving out `./.git`, `./image/secrets`, `./.venv` and `./mutants`. Convert the copy's text files to LF line endings.
2. Inside that copy, place your drafts under `factory/features/F0044-the-layers-go/backlog/`.
3. Run the check in a throwaway container of the image:

   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --network none --entrypoint /bin/sh \
     -v C:/Users/pasca/AppData/Local/Temp/f44draft/repo:/src -w /src factory-self-factory -c 'factory-check-story factory/features/F0044-the-layers-go/backlog/<file>.md'
   ```

   Every line must end in `: ok`. Fix the draft in `planning/` and check again.
4. Run each smoke test against today's code the same way: before the story it must print what the code prints today (say so), and its `Expect:` must be what it prints after the removal.

Never run anything in the running instance `factory-self-factory-1`. You may look inside it read-only with `MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 <command>`; change nothing there.

## Not

- Never open, read, print or copy anything under `image/secrets/`, and never read a token or key file.
- Temporary files only in `C:/Users/pasca/AppData/Local/Temp/f44draft`, nowhere else. Delete it when done; if a removal is refused, say so.
- No git commands in the repository. No commit, no push. No network calls.
- No file outside `planning/overnight/stories/F0044-the-layers-go/` and the temporary folder.
- No sub-agents. No paid model call of your own.
- Do not change `CLAUDE.md`, the forms, the agents, `planning/v1.2-plan.md`, the runbook, F0042's or F0043's files or any other feature.

## Reply

At most 30 lines: the stories, one line each (id, short name, number of criteria); the human's changes; the leaves (story and test count); the decisions you took for the human; open questions; anything you could not place. Every id with its short name.
