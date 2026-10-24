# Brief: draft feature F0042 (the stage environment behind one interface) and its stories

## Goal

Write `feature.md` and every story of F0042 (the stage environment behind one interface), so that v1.1 can build each story in one run through intake, tests, coding, review, docs and smoke test. The feature is the first of v1.2; its design is decided by the human on 2026-10-24 and written in `planning/v1.2-plan.md` (read it whole first; the section "The cycle of a stage" and the feature's own section "F0042" are the ground, the section "The human's decisions" is binding).

The idea in one paragraph: in v1.2 the factory runs on a Linux VM with ZFS. Every stage runs its steps in throwaway Podman containers on one ZFS dataset (mounted at `/work` in every container; on the host at a configured path). A stage rolls the dataset back to its base snapshot, runs a sync container (fetch from the host's own repository, checkout of the stage-start commit, `make sync`), moves the base snapshot forward, runs the agent's container, then **takes** from the dataset only what the role may write (the write-path refusal rule applied the other way round, instead of the undo) into the factory's own work tree on the host, rolls back again and runs the project's commands in a container on the taken result. v1.1's way (the agent in the factory's own container, the undo) stays as the second implementation of the same interface until F0044 removes it, so that `self` keeps building on Docker. The generic factory (claims, stage protocol, decisions, stalls, hosting, costs) does not change its behaviour.

Requirements, numbered:

1. **Two small interfaces with fakes.** `Snapshots` (abstract base class in `factory.application`): `reset()` puts the dataset back to the base; `advance()` moves the base to the dataset's current state; `changed_paths()` lists the paths that differ from the base (added, modified, deleted; a rename as a deletion and an addition). `ContainerRuns` (abstract base class in `factory.application`): `run(command, *, mounts, environment, time_limit, working_directory)` runs one command in a fresh container on the dataset and returns a result with the exit status, the merged output and whether the time limit ended it. Fakes in `factory.adapters`, inheriting the interfaces: `FakeSnapshots` works on a folder (a copy is the base; the diff is computed by walking); `FakeContainerRuns` runs the command as a child process on the host with the mounts mapped to folders (as `FakeAgentRuntime` stands in for the runtimes today). Fakes are what the suite and the smoke tests use; the real adapters are tested on recorders.
2. **`ZfsSnapshots(dataset, mount_point)`** in `factory.adapters`: `reset()` is `zfs rollback -r <dataset>@base`; `advance()` is `zfs destroy <dataset>@base` (skipped when it does not exist) then `zfs snapshot <dataset>@base`; `changed_paths()` is `zfs diff -H <dataset>@base`, parsed (`M`, `+`, `-`, `R`; the paths are made relative to the mount point; a path outside the mount point is a fault). A command that fails raises `SnapshotError` naming the command and the last line of its output. The snapshot's name is the constant `base`. The adapter runs the `zfs` executable it is given (the wiring gives `zfs`; a `sudoers` fallback is the operator's, outside the code: the wiring may take an executable like `sudo -n zfs` as a setting, keep it simple).
3. **`PodmanRuns(executable, image, workspace)`** in `factory.adapters`: `run` builds `podman run --rm --userns=keep-id --timeout <seconds> --env NAME=value ... --volume <host>:<container>[:ro] ... --workdir <dir> <image> <command...>`, with the dataset's host path mounted at `/work` always, runs it through `run_process` and reads the result: podman's exit status is the command's; a container ended by `--timeout` is read as ended by the time limit. The command line is pinned by a test (the read-only mounts above all, since a `:ro` bind mount is the whole protection of the host's repository). The podman executable comes from the wiring.
4. **The take.** `TakeService(boundaries).take(stage_start, settings, changed_paths) -> TakeReport` in `factory.application`: for every changed path under `checkout/` that is not ignored by the checkout's `.gitignore` (asked of the factory's own repository on the host with `git check-ignore`, never of the dataset's), has no `.git` component and is not refused by `refusal(path, settings)` of `factory.domain.write_paths` (the write paths, the protected paths) nor lies directly in another work item's `in-progress/` folder (the undo's second rule, unchanged), the file is copied from the dataset's checkout into the factory's work tree (a deletion is mirrored, the executable bit kept); a refused path is left in the dataset and listed. Then the work item's state and journal are put back from the stage-start commit with `restore_state_and_journal`, as the undo does today. Paths under `home/` or outside `checkout/` are neither taken nor listed. The report has `left` (the refused paths, sorted, no repeats) and `restored_work_item`; the undo's `UndoReport` is turned into the same report type with `left` = its reverted and deleted paths joined, so that `AfterAgent` and the entry's sentence read one type. The journal's sentence for `left` is a decision of yours (today: "The factory undid changes outside the write paths: ..."; it may become "The factory left out changes outside the write paths: ..."); name the pinned tests the change touches, for the leave.
5. **`StageEnvironment`** (abstract base class in `factory.application`) is what the stage protocol calls: `prepare(stage_start)` before the agent, `agent_runtime` (the `AgentRuntime` the stage runs its request through), `take(stage_start, settings)` after the agent, `project_commands` (the `ProjectCommands` the checks and reports use). Two implementations. `ContainerEnvironment(snapshots, containers, git, ...)`: `prepare` is reset, the sync container (`git init` when `/work/checkout` has no `.git`, `git fetch /upstream <branch>`, `git checkout -f <stage-start commit>`, `make sync`; `/upstream` is the host repository's `.git` folder mounted read-only), then advance; its `agent_runtime` is today's `ClaudeCodeRuntime` or `OpencodeRuntime` whose process is started inside a container instead of under `sudo` (the launch module gets the container wrapper at the place of the `sudo` wrapper; the runtimes are not duplicated; the instructions file and the login file are mounted read-only at their own paths; `HOME` is `/work/home`; the agent files are copied into `/work/home/.claude` before the base moves); its `take` is the `TakeService` with `snapshots.changed_paths()`; its `project_commands` resets the dataset, copies the taken files in (the `taken` paths of the last take, from the host's work tree; deletions mirrored), and runs `make sync && make <command>` in a container with the command's time limit. `InlineEnvironment`: `prepare` does nothing, `agent_runtime` and `project_commands` are today's (`run_sealed` and the sealed commands move inside it), `take` is the undo, reported as `TakeReport`. `StageLauncher`, `AfterAgent` and `StageFinisher` call the environment and know neither podman nor zfs nor `sudo`; `StageRunner` and `Preflight` get the environment from the boundaries.
6. **The sync command** is a fourth target of the project contract: `sync` in `project_commands` of the pipeline definition, with a time limit like the others; `make sync` in `template/Makefile` (`uv sync --frozen` for Python; the Java and TypeScript template designs under `planning/overnight/templates/` are not yours to change, name them under *The human's changes* with the target each would gain). This repository's `Makefile` and `factory/pipeline.yml` are the human's changes, with the exact lines; they must come before the story that runs `make sync` for real in a container, and may come before S0001.
7. **The settings.** `FACTORY_STAGE_ENVIRONMENT` (`inline`, the default, or `container`), `FACTORY_DATASET` (the ZFS dataset, for example `tank/factory/vm`), `FACTORY_WORKSPACE` (the dataset's mount point on the host, an absolute path), `FACTORY_STAGE_IMAGE` (the stage image's name), `FACTORY_PODMAN` and `FACTORY_ZFS` (the executables, defaults `podman` and `zfs`), in `InstanceSettings` with the faults the others have (a `container` environment without a dataset, a workspace or an image is `SettingsInvalid`). The wiring builds the environment from them.
8. **The preflight** for the `container` environment: the items `podman` (the executable answers `--version`), `zfs` (the same), `dataset` (`zfs list -H -o name <dataset>` names it), `stage-image` (`podman image exists <image>`); the agent-run probe and the `lint` probe of `main` go through the environment like a stage; the `inline` environment keeps today's items unchanged. The items `agent-user` and `confinement` are not run for the `container` environment.
9. **Timing lines in the factory log**, one per stage: `stage environment: reset <s> s, sync <s> s, advance <s> s, take <s> s` for the container environment, so the human can read the plan's measures (the start of a stage to the agent's first step under 20 s with a warm base) from `/state/factory.log`.
10. **The documents.** A new guide file `docs/project-guide/stage-environment.md` (the cycle, the two environments, the take, the settings, the preflight items), named in `docs/project-guide/README.md`; the operator guide gains the settings and the preflight items of the `container` environment in its existing sections (the chapter "The machine" is F0043's, not yours); `docs/decisions.md` gains the entry "One snapshot instead of many layers" (the design, the decision's date, what the take keeps from the undo). The write-guard guide's section "The undo" says that the undo is the inline environment's take.

What this feature does **not** do: it removes no layer (F0044), it builds no VM, image or `vm/` folder (F0043), it changes no agent text, it adds no second snapshot adapter, and it does not change the stage protocol's commits or pushes.

## Inputs (read these first)

- `planning/v1.2-plan.md` whole; `planning/v1.2-candidates.md`, first section, for the thinking behind it.
- The code the feature touches: `src/factory/application/stage.py` (`StageLauncher`, `AfterAgent`, `StageFinisher`, `StageRunner`), `sealed_runs.py`, `undo.py`, `project_commands.py`, `preflight.py`, `boundaries.py`, `agent_runtime.py`; `src/factory/adapters/agent_launch.py` (the `sudo` wrapper, `Starters`), `claude_runtime.py` and `opencode_runtime.py` (`_process_request`), `make_commands.py`, `process.py` (`run_process`), `fake_agent_runtime.py`; `src/factory/domain/write_paths.py` (`refusal`), `journal.py` (`restore_state_and_journal`), `settings.py`, `agent_runs.py`, `pipeline_definition.py` (`project_commands`); `src/factory/entry/wiring.py` (`build_boundaries`, `_agent_runtime`, `_project_commands`, `machine_extras`).
- The tests that pin them: `tests/application/test_undo.py`, `test_after_agent.py`, `test_stage_launch.py`, `test_stage_finish.py`, `test_stage_run.py`, `test_sealed_runs*.py`, `tests/application/test_interfaces.py`, `tests/domain/test_agent_entry.py`, `tests/entry/test_wiring_*.py`, `tests/adapters/test_make_commands*.py`, and the structural tests under `tests/` that pin names and places (`test_*_search.py`).
- `docs/project-guide/stages.md`, `write-guard.md` (the undo), `processes-and-checks.md`, `agents.md` (the launch module), `watching.md` (the preflight).
- `CLAUDE.md`, above all *Architecture*, *Tests* and "Not without asking".
- `factory/feature-form.md`, `factory/story-form.md` and `factory/pipeline.yml` (the roles, their write paths and time limits).
- `claude/agents/intake.md`: the checks your stories must pass.
- `docs/operator-playbook.md`, section 2 (a feature, from plan step to acceptance).
- `docs/project-guide/README.md` and the guide files it names for the domains touched; `docs/operator-guide.md`; `docs/decisions.md`.

## Rules for the split

- The plan's F0042 section sketches eight stories; follow that order unless a dependency forces another, and say so in `feature.md`. One story is one coder's work within its role's `time_limit` (40 minutes) and a budget of a few dollars. A documents-only part may be its own story.
- Every behaviour the Description, the Interface or a decision states has its own criterion. Every rule has its failing side too. Every limit is stated with its number, and both sides are tested. The sides of one rule are rows of one parametrized test.
- Test data is valid under the built code. Every file a smoke test or a test names exists or is made by the story.
- A smoke test runs in v1.1's container (Linux, as the factory user, umask 002, nothing listening, no podman, no zfs) under the kernel's write guard, with no paid call. So smoke tests use the fakes and the recorders, never the real adapters. Its `Expect:` is met exactly by the built code.
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

Only the folder `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0042-the-stage-environment-behind-one-interface/`:

- `feature.md`, in the sections of `factory/feature-form.md`.
- `backlog/F0042-S000N-<slug>.md` for each story, in the sections of `factory/story-form.md`, with an empty Journal.

## Check each story

`factory-check-story` takes only a path `factory/features/<dir>/<backlog|in-progress|done>/<file>.md`, and the suite and the check do not run on Windows. So check in a throwaway container, on a copy:

1. Copy the repository into `C:/Users/pasca/AppData/Local/Temp/f42draft/repo`, leaving out `./.git`, `./image/secrets`, `./.venv` and `./mutants`. Convert the copy's text files to LF line endings.
2. Inside that copy, place your drafts under `factory/features/F0042-the-stage-environment-behind-one-interface/backlog/`.
3. Run the check in a throwaway container of the image:

   ```bash
   MSYS_NO_PATHCONV=1 docker run --rm --network none --entrypoint /bin/sh \
     -v C:/Users/pasca/AppData/Local/Temp/f42draft/repo:/src -w /src factory-self-factory -c 'factory-check-story factory/features/F0042-the-stage-environment-behind-one-interface/backlog/<file>.md'
   ```

   Every line must end in `: ok`. Fix the draft in `planning/` and check again.
4. Run each smoke test you can against today's code the same way, to see that it runs and what it prints today.

Never run anything in the running instance `factory-self-factory-1`. You may look inside it read-only with `MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 <command>`; change nothing there.

## Not

- Never open, read, print or copy anything under `image/secrets/`, and never read a token or key file.
- Temporary files only in `C:/Users/pasca/AppData/Local/Temp/f42draft`, nowhere else: not a drive's root, not the repository. Delete it when done; if a removal is refused, say so.
- No git commands in the repository. No commit, no push. No network calls.
- No file outside `planning/overnight/stories/F0042-the-stage-environment-behind-one-interface/` and the temporary folder.
- No sub-agents. No paid model call of your own.
- Do not change `CLAUDE.md`, the forms, the agents, `planning/v1.2-plan.md` or any other feature.

## Reply

At most 25 lines: the stories, one line each (id, short name, number of criteria); the human's changes; the decisions you took for the human; open questions; anything you could not place. Every id with its short name.
