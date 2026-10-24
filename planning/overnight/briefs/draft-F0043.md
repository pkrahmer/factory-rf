# Brief: draft feature F0043 (the machine and the stage image) and its stories

## Goal

Write `feature.md` and the stories of F0043 (the machine and the stage image), so that v1.1 can build each story in one run through intake, tests, coding, review, docs and smoke test. The feature is the second of v1.2; its design is decided by the human on 2026-10-24 and written in `planning/v1.2-plan.md` (read it whole first; the sections "The cycle of a stage", "The machine", "F0043" and "The human's decisions" are binding). F0042 (the stage environment behind one interface) is drafted under `planning/overnight/stories/F0042-the-stage-environment-behind-one-interface/`; read its `feature.md` and stories, because F0043 builds the machine that F0042's `container` environment runs on, and the settings names (`FACTORY_STAGE_ENVIRONMENT`, `FACTORY_DATASET`, `FACTORY_WORKSPACE`, `FACTORY_STAGE_IMAGE`, `FACTORY_PODMAN`, `FACTORY_ZFS`) are F0042's; use them as F0042 defines them.

Requirements, numbered:

1. **The stage image**, `vm/Dockerfile`: today's `image/Dockerfile` without the factory and without the layers: the pinned base image, git, make, curl, ca-certificates, procps, nodejs and npm, uv, Claude Code and opencode at the pinned versions, no second user, no `sudo`, no `sudoers`, no entrypoint, no `/etc/gitconfig`, no `USER`, no `/opt/factory`, no `COPY src`. The agent files (`claude/agents`, `claude/settings.json`) are copied to `/etc/factory/claude` read-only; the factory copies them into the dataset's `/work/home/.claude` before the base moves (F0042 does the copying; this image only carries them). The image carries the label `factory.image` as today (the preflight reads it) and the same environment for the agent runtimes that today's image sets for them (`DISABLE_AUTOUPDATER`, `UV_LINK_MODE=copy`, `PYTHONDONTWRITEBYTECODE`, the opencode model ids), minus everything that named the second user or the factory's own paths. `tests/test_image*.py` pin today's Dockerfile; this story adds tests of the same kind for `vm/Dockerfile` and changes none of the old ones (the old image stays until F0044). The image is built on the VM with `podman build -f vm/Dockerfile -t <FACTORY_STAGE_IMAGE> .` from a checkout; say so in the docs.
2. **`vm/setup.sh`**, idempotent, run as root once on a fresh Ubuntu 24.04 with a spare disk, with the facts the human brings back from the prototype (`planning/overnight/gcp-runbook-2026-10-24.md`, sections 4 and 5; its results file `planning/overnight/gcp-prototype-results-*.md` if present): installs `zfsutils-linux`, `podman`, `uidmap`, `slirp4netns`, `git`, `make`, `python3.12-venv`; makes the pool on the given device (an argument), the datasets `tank/factory` and `tank/factory/<instance>` with `compression=lz4`, `atime=off` and a `quota` (an argument, default 30G), the mount at `/srv/factory/<instance>/work`; the user `factory` with linger; `zfs allow -u factory snapshot,destroy,rollback,diff,mount` on the instance's dataset; the `sudoers` fallback only when asked by a flag; the factory's own virtual environment under `/srv/factory/<instance>/factory` from a given git ref of the repository (`uv sync --frozen --no-dev`); the secrets folder `/home/factory/.secrets` (mode 0700, empty: the operator places the token files by hand); the systemd unit from `vm/factory.service` with an environment file `/srv/factory/<instance>/factory.env` the script writes from its arguments. Every step prints one line of what it did or found done. The script is tested by a test that runs it under `sh -n` and checks its text for the steps and their order (no VM in the suite), as `tests/test_entrypoint*.py` check the entrypoint today.
3. **`vm/factory.service`**: a systemd unit for the user `factory` (`User=factory`, `WorkingDirectory=/srv/factory/<instance>`, `EnvironmentFile=/srv/factory/<instance>/factory.env`, `ExecStart=<venv>/bin/factory-run`, `Restart=always`, `RestartSec=15`), with the environment the compose file sets today translated into the environment file (the instance, the repository URL, the agent runtime, the opencode variables, `FACTORY_STAGE_ENVIRONMENT=container`, the dataset, the workspace, the image, `FACTORY_TOKEN_FILE`, the login files, `FACTORY_STATE=/srv/factory/<instance>/state`). The health file stays where `factory-health` reads it. Pinned by a text test like the compose tests.
4. **The operator guide's chapter "The machine"**: GCP in numbered steps (the project and the budget alert, NAT and IAP, the VM with no service account, the disk, the script, the secrets by hand, the image build, the first start, the board over SSH, the rebuild after a merge: pull, `uv sync`, `podman build`, `systemctl restart`), and the same for any Ubuntu 24.04 VM; what the container can and cannot see; the costs (the plan's numbers); the metadata server; where the logs are. Written from the runbook and the plan; the documenter writes it (docs is its write path), so it is a story of its own or the docs criterion of the others, your choice, said in `feature.md`.
5. **The first stage on the VM** is the human's story 4 in the plan: not a story of yours. Write it in `feature.md` under *The human's changes* as the acceptance's precondition: the human starts the instance `vm` on factory-rf and builds one documents-only story, and writes the timings into the night log.

What this feature does **not** do: it removes no file under `image/` (F0044 does), changes no agent text, builds no code of the environment (F0042), and creates nothing on GCP (the human does, by the runbook).

## Inputs (read these first)

- `planning/v1.2-plan.md` whole; `planning/overnight/gcp-runbook-2026-10-24.md`; `planning/overnight/stories/F0042-the-stage-environment-behind-one-interface/` (feature and stories).
- `image/Dockerfile`, `image/compose.yml`, `image/entrypoint.sh` and the tests that pin them (`tests/test_image*.py`, `tests/test_compose*.py`, `tests/test_entrypoint*.py`, `tests/dockerfile_support.py`, `tests/compose_support.py`, `tests/entrypoint_support.py`).
- `docs/operator-guide.md` (its chapters "Install", "Configuration", "The machine's image", "The container", "Container runtimes"), `docs/decisions.md` (the pinned image, the users and directories).
- `src/factory/domain/settings.py` (the settings and their faults), `src/factory/application/preflight.py` (the image label).
- `CLAUDE.md`, above all *Architecture*, *Tests* and "Not without asking".
- `factory/feature-form.md`, `factory/story-form.md` and `factory/pipeline.yml` (the roles, their write paths and time limits). Note: `vm/*` is not yet a write path; `feature.md` names the human's change that adds it to the coder's write paths in `factory/pipeline.yml`, before S0001.
- `claude/agents/intake.md`: the checks your stories must pass.
- `docs/operator-playbook.md`, section 2 (a feature, from plan step to acceptance).
- `docs/project-guide/README.md` and the guide files it names for the domains touched.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour the Description, the Interface or a decision states has its own criterion. Every rule has its failing side too. Every limit is stated with its number, and both sides are tested. The sides of one rule are rows of one parametrized test.
- Test data is valid under the built code. Every file a smoke test or a test names exists or is made by the story.
- A smoke test runs in v1.1's container (Linux, as the factory user, umask 002, nothing listening, no podman, no zfs, no systemd) under the kernel's write guard, with no paid call. So smoke tests check texts and `sh -n`, never a build or a VM. Its `Expect:` is met exactly by the built code.
- A smoke test never passes `-q` to pytest: `pyproject.toml` already sets it, and at `-qq` pytest prints no summary line.
- Mutation testing is never part of a story or of the acceptance.
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md` (*Tests*), names them in its Interface, and `feature.md` gives the leave as a numbered decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `uv.lock`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`, and `vm/` until the write path exists) goes under *The human's changes* in `feature.md`, with exact lines and the story it must come before or after.
- Use only the dependencies in `pyproject.toml` and the standard library. No new top-level package.
- No secret-like key with a value in a story's text, and no 32-character hex value.
- Every product decision you take goes into `feature.md` as a numbered decision, naming its story.
- Keep it small (the human's rule: solid over clever). No new mechanism unless the goal asks for it.

## How much a story fixes in advance (the human, 2026-10-20)

Write what must be true, not how to build it. Fix in the story: the behaviour and its rules with their edge cases and limits; every contract another story builds on; the earlier tests the story may change, by exact name; the documents to change; every decision that is the human's. Leave to the agents: private helpers and internal structure; the layout of the test files and the names of new tests; the exact wording of small outputs that nothing else reads. A criterion names an exact value only where the value is the rule.

## Write

Only the folder `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0043-the-machine-and-the-stage-image/`:

- `feature.md`, in the sections of `factory/feature-form.md`.
- `backlog/F0043-S000N-<slug>.md` for each story, in the sections of `factory/story-form.md`, with an empty Journal.

## Check each story

`factory-check-story` takes only a path `factory/features/<dir>/<backlog|in-progress|done>/<file>.md`, and the suite and the check do not run on Windows. So check in a throwaway container, on a copy:

1. Copy the repository into `C:/Users/pasca/AppData/Local/Temp/f43draft/repo`, leaving out `./.git`, `./image/secrets`, `./.venv` and `./mutants`. Convert the copy's text files to LF line endings.
2. Inside that copy, place your drafts under `factory/features/F0043-the-machine-and-the-stage-image/backlog/`.
3. Run the check in a throwaway container of the image:

   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --network none --entrypoint /bin/sh \
     -v C:/Users/pasca/AppData/Local/Temp/f43draft/repo:/src -w /src factory-self-factory -c 'factory-check-story factory/features/F0043-the-machine-and-the-stage-image/backlog/<file>.md'
   ```

   Every line must end in `: ok`. Fix the draft in `planning/` and check again.
4. Run each smoke test you can against today's code the same way.

Never run anything in the running instance `factory-self-factory-1`. You may look inside it read-only with `MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 <command>`; change nothing there.

## Not

- Never open, read, print or copy anything under `image/secrets/`, and never read a token or key file.
- Temporary files only in `C:/Users/pasca/AppData/Local/Temp/f43draft`, nowhere else. Delete it when done; if a removal is refused, say so.
- No git commands in the repository. No commit, no push. No network calls.
- No file outside `planning/overnight/stories/F0043-the-machine-and-the-stage-image/` and the temporary folder.
- No sub-agents. No paid model call of your own.
- Do not change `CLAUDE.md`, the forms, the agents, `planning/v1.2-plan.md`, the runbook, F0042's drafts or any other feature.

## Reply

At most 25 lines: the stories, one line each (id, short name, number of criteria); the human's changes; the decisions you took for the human; open questions; anything you could not place. Every id with its short name.
