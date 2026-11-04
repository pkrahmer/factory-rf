# The project shapes its stage image

## Goal

Every stage of every project runs in one stage image, built from kumpel-factory's `vm/Dockerfile`. So a tool that one project needs goes into every project's image: on 2026-11-03 an ESP32 template in C needed `build-essential` and `cmake`, and the image grew by 288 MB for all of them (reverted as f755afe94). With C, Java, and TypeScript for user interfaces to come, each with its own runtime and libraries, a shared image would only grow, and in a Cloud Run job the image sits in memory. This feature splits the image in two. The factory's base image holds what every project needs and the factory itself: git, make, curl, uv, Python, and the agent runtimes with a Node of their own, apart under `/opt/factory`. A project that needs more ships `factory/stage.Containerfile`, an ordinary Containerfile that starts `FROM ${FACTORY_BASE}`. The factory reads it from the project's `main`, builds it on top of the base, and runs every stage of that project in the result. The image of a project without the file is the base. A changed file on `main` is rebuilt by the factory itself, with no step by the operator, and a new image identity makes the preflight and the reuse of passed checks start afresh. Done when every story below is merged and `make check` is green.

## Scope

- The base image: the factory's own tools under `/opt/factory`, with Node 22 of their own, apart from any tool a project installs; Debian's `nodejs` and `npm` leave the image (S0001).
- The project's layer: `factory/stage.Containerfile` read from `main`, its rule (`FROM ${FACTORY_BASE}` first, no build context), its build on the base, its image identity, and its `PATH` in every container of the project (S0002).
- The rebuild: a new `main` whose file differs from the built one rebuilds the layer between stages; a failed build is a stop with the build's last lines (S0003).

## Out of scope

- Any project's own stage file: the ESP32 template ships its own in its repository, outside this feature.
- An image per line or per role. One project image serves every stage now; the stories only keep the image in one place, so that a later feature can let a line or a role name its own (decision 3).
- Building firmware or any other output that is not part of `make check` (ESP-IDF, for instance).
- Files of the repository inside the build (`COPY` from the project): the build context is empty (decision 4). A later feature may open it.
- A registry or a cache of images between machines: each machine builds its own.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The factory's own tools live apart under /opt/factory, with a Node of their own
- S0002: A project's stage file builds the image its stages run in
- S0003: A changed stage file on main is rebuilt between stages

## The human's changes

None in the write paths. The coder writes `src/*` and `vm/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`; no story touches `Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md` or `.secrets.baseline`. kumpel-factory itself needs no stage file: its `make check` runs on the base.

A leave, for S0001: its tester may change, in `tests/test_stage_image.py`, the rows that pin the Debian packages, the Node and the npm installs and the places of `claude`, `opencode` and `uv`, to the image S0001 describes; nothing else in that module.

A leave, for S0002: its tester may change the rows that pin the containers' `PATH` (`/usr/local/bin:/usr/bin:/bin`, the sync environment and the agent environment) to the `PATH` S0002 describes, in `tests/adapters/test_make_commands_container.py`, `tests/adapters/test_podman_runs.py`, `tests/adapters/test_podman_runs_fence.py`, `tests/application/test_container_environment.py`, `tests/application/test_container_environment_extra.py`, `tests/domain/test_agent_environment.py`, `tests/entry/test_wiring_handlers.py` and `tests/vm_support.py`; nothing else in those modules.

## Decisions taken for the human

1. **A Containerfile, not a list of packages.** The project ships an ordinary Containerfile on the factory's base. Reason: Debian's own packages hold only Node 18 and Java 17, so a list of packages would need a recipe in the factory for every stack, and the shared image's growth would come back as a growing catalogue. A Containerfile covers every stack with no knowledge in the factory. The project's commands run at build time with the network, but `make check` already runs the project's code in every stage; reading the file from `main` alone, which the human merges, covers the rest. Rejected: a package list with a catalogue, `mise.toml` (language runtimes only, no system libraries), named stack images (the factory grows with every stack). The human, 2026-11-04.
2. **The factory's tools stay apart.** The agent runtimes and their Node live under `/opt/factory`; only the runtimes' own commands are on the containers' `PATH` from there, and the factory's Node is not. Reason: a project that installs its own Node or Python must not change the factory's, and Claude Code 2.1.296 already asks for Node 22 while Debian's is 18. The preflight's probe of the agent run, keyed to the image identity, confirms that a project's layer left the runtime working. The human, 2026-11-04.
3. **One image for every stage, room for more.** Every container of a project (sync, agent, checks) runs in the one project image, named in one place of the code. Reason: no second line exists yet, so its needs are unknown; the one place lets a later feature give a line or a role an image of its own without changing every caller. The human, 2026-11-04.
4. **The build sees no files.** The project's layer is built with an empty context, so `COPY` and `ADD` of local files have nothing to copy. Reason: what the image holds then comes only from the file's text and the network, so the file's hash and the base's identity name the image; the project pins its own versions and checksums. Taken for the human, 2026-11-04.
5. **The factory rebuilds, by hash.** The factory compares the hash of `main`'s file with the built one and rebuilds between stages, never during one. Reason: an operator step after a merge is easy to forget on the VM, and a Cloud Run job builds at every start anyway. The human, 2026-11-04.
6. **The runtimes run without Node.** Claude Code 2.1.296 and opencode 1.19.3 install native executables, so `/usr/local/bin/claude` and `/usr/local/bin/opencode` exec `/opt/factory/bin/<runtime>` directly with `"$@"`; the factory's Node 22 serves npm's install alone. Reason: a real build of S0001's first version on factory-vm showed both wrappers failing under Node (`ERR_UNKNOWN_FILE_EXTENSION` for `claude.exe`, a `SyntaxError` for opencode's ELF file). Taken for the human on PR #526, 2026-11-03.
7. **A leave for S0002 in `tests/entry/test_health.py`.** Its tester may add `stage_image_failed` to the tuple of machine-scoped reasons there, for the health row of the new stop, and nothing else in that module. Reason: the new stop has machine scope, as `preflight_failed` has, and the earlier test builds its scope from that tuple. Taken for the human on PR #527, 2026-11-04.
