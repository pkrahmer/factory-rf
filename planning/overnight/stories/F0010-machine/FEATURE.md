# The machine

## Goal

One pinned container runs one project and keeps its own faults visible. The project's repository URL and the instance's name come from environment variables, the checkout is one fixed path on a volume and is recloned when it is missing, and the loop ticks with a pause of 15 seconds after activity that doubles to 120 seconds while idle. The image pins every tool, generates its own identity at build and records it in each cost record. After each fetch, load and restore a preflight checks the machine, only when the image build changed, and probes the main branch with the project's lint, only when the main branch moved; the machine's own stops make the container's health check fail. Agent files hold only keys the agent runtime applies, and an agent run holds no credential for the hosting service: it runs as a second unprivileged user with an allow-listed environment while the token stays in a file only the factory's user can read. Done when each of these is shown by a test, with the parts that need Docker, root or a second operating-system user shown by a static test of the files plus a morning observation.

## Scope

- One instance, one project (R2, R25): settings from the environment, the fixed checkout path, the reclone, the loop and its pauses (ST7.1, ST7.2, ST7.3).
- The boundaries of the instance (questionnaire 1, Q17, Q18, Q20): `build_boundaries(settings, token)`, the token read once from its file, the repository name for the hosting client, the git options (identity, credential helper and shared-group setting as `GitOptions.environment` entries), the run, and `factory-watch` reading the same settings.
- The pinned image (R29, R4): the base image by digest, Claude Code by exact version from its npm package, the tool packages by exact version, the factory installed from the lock file, a fresh identity generated at build and kept in `/opt/factory/image-id`, the identity in each cost record, no `tasks/.gitkeep` in the template (ST5.1, ST5.2, ST5.4, SI3.3).
- The health check and the entrypoint's stops (R27, container side): the health command, the compose file with a restart policy and a health check, the entrypoint with time-stamped lines, the wait for a repository that is not ready (ST3.3, ST3.4 for the entrypoint).
- The preflight's items: the tools, the hosting service, the agents where `FACTORY_CLAUDE_HOME` points, the agent runtime's version against the pinned one, the token file, the agent user, `sudo`, the agent run's `PATH` and `HOME`, and one `claude -p` probe with the factory's own arguments (ST4.4, ST5.3; questionnaire 1, Q22).
- The probe and the stamp: lint probed on the main branch after the fetch, the load and the restore, the stamp keyed to the image build, a failing main branch a reported stop and remembered (ST4.1, ST4.2, ST4.3, ST4.5).
- Agent files without dead keys, refused at load as a reported stop raised by the pipeline loader, and the shipped agents with v1's role and stage texts renamed, the settings and the pipeline definition template, each key with an effect (SI4.1, SI4.2, SI4.3, R30; questionnaire 1, Q29).
- No hosting-service token in an agent run, and agent runs as a second unprivileged user (WE3.1 to WE3.5, R33).

## Out of scope

- A watchdog for a container that is dead: Docker's restart policy and the health check are what R27 names.
- Preflight checks of the project's setup, of the hosting service's settings and of the token's expiry.
- A sandbox for agent runs, and writes by an agent to ignored paths or outside the checkout (left for v2).
- Running the project commands as the second user: they run agent-written code as the factory's user, who can read the token file (left for v2, the human, 2026-10-14).
- Enforcing a `time_limit` of an agent run under `sudo` (decision 30 is open).
- The table of all stops and its tests: feature F0011.
- The story and feature forms, and any skill file (the runner applies no `skills` key).

## Stories

- S0001 — One instance, one project, one checkout
- S0002 — The boundaries of one instance
- S0003 — The instance's run and the watcher's wiring
- S0004 — The pinned image
- S0005 — The health check and the entrypoint's stops
- S0006 — The preflight's items
- S0007 — The probe on the main branch and a stamp keyed to the image
- S0008 — Agent files with no dead keys
- S0009 — The shipped agents and settings
- S0010 — No hosting-service token in an agent run
- S0011 — Agent runs as a second unprivileged user
- S0012 — The second user in the image and its checks
- S0013 — The preflight probes one agent run
- S0014 — v1's role and stage texts in the shipped agents

## Decisions taken for the human

1. The repository URL may not contain a comma or whitespace, and v1's `REPOS` list is not read at all: one instance, one project. (S0001, story text)
2. An instance name is a lowercase letter followed by lowercase letters, digits and hyphens, the same pattern as every other name. (S0001, story text)
3. The checkout is `/work/checkout` and the state directory is `/state`; no variable changes either. The files of agent runs go to `/state/runs`, under the state directory. (S0001, S0002, story text)
4. The pause is 15 seconds after activity and doubles for each further idle tick up to 120 seconds; the first tick of a start runs at once; a repository that is not ready and a tick that raises an exception both count as idle, and the exception is logged in one line. Only a handled event that is not `idle` is activity: a tick that ended at a stop, a capped event and an error are idle. (S0001, S0003, story text)
5. A start with an invalid environment, an unreadable token file or a repository URL without an owner and a name writes a machine stop and a time-stamped line, keeps the stops already in force, then ends with status 2. (S0003, story text)
6. The base image digest and the eight Debian package versions in the Dockerfile are placeholders (a digest of 64 zeros, the version `0~unpinned`), because they cannot be looked up without a network; the human replaces them before the first build. Claude Code 2.1.289 and `uv` 0.9.2 are the versions of v1's last build. Claude Code is installed from its npm package at the pinned version, with `nodejs` and `npm` among the pinned packages; the installer script is not used, because it floats. (S0004, story text)
7. The image identity is a fresh id that the build generates (`/proc/sys/kernel/random/uuid`) and writes to `/opt/factory/image-id`; the settings read it from that file, a missing or empty file is refused, and the build argument `FACTORY_IMAGE` is only a label. An unknown identity (settings built without the file reader, as in tests) never validates a stamp. (S0004, the human, 2026-10-14)
8. The image creates two users, `factory` (uid 1000) and `agent` (uid 1001), in the shared group `factory-work`; the container runs as `factory`. `/state` stays `0755` owned by `factory:factory`, so the agent can read but not write the health file, the log and the stamp; the files of an agent run go to `/state/runs`, mode `2750`, group `factory-work`, which the agent can read but not write; `/work` and `/home/agent/.claude` are `2775` and group-writable. The group `factory` is created with gid 1000 and has no member. (S0004, the human, 2026-10-14)
9. The health check runs every 30 seconds, times out after 10 seconds, fails after 3 retries and waits 60 seconds at start. (S0005, story text)
10. A repository that is not ready (not cloneable, no main branch yet, no pipeline definition on main) is the repository stop `repository_unavailable`, written once for each distinct detail. (S0005, story text)
11. v1's preflight item for the git identity is not rebuilt: `GitIdentity`'s default `factory <factory@noreply.invalid>` stands, and the settings `GIT_USER_NAME` and `GIT_USER_EMAIL` override it, each half on its own (questionnaire 1, Q18). (S0001, story text)
12. The agent runtime's version matches when the first word of what it reports equals the pinned version. (S0006, story text)
13. The preflight runs after the tick's fetch, load and restore, before the evaluation, because the built tick loads the definition before it restores the checkout (F0006 decision 10). The probe's `time_limit` stays the constant 10 minutes, not the pipeline definition's, so that `Preflight` needs no definition and its memory does not depend on one; a tick that the preflight stops ends with `TickOutcome(stopped=<the reason>)`. (S0007, story text)
14. The machine items are skipped while the image build is unchanged, with no timer; the lint probe repeats only when the main branch moved, and a main branch whose lint failed is remembered, so that an idle tick runs no project command even while the human has not pushed a fix. A valid stamp also clears a standing `preflight_failed` stop. (S0007, story text)
15. An agent file may hold only `model`, `tools`, `effort` and `budget_usd`; v1's six dead keys and `skills` are refused, and keys are case-sensitive. An unapplied key is reported before the model's own validation, with the fault `key not applied by the agent runtime: <key>`. The pipeline loader raises and clears the stop `agent_definition_invalid`, like the stop of the definition itself, and only for a load of `origin/main`; `factory-watch` prints the refusal and touches no stop. (S0008, story text)
16. No skills are shipped. The shipped agent bodies carry v1's role and stage texts, renamed into the glossary's words, with v1's decision `stuck` replaced by `question` (F0005 decision 24; questionnaire 1, Q29); the bodies start with each role's boundary sentence and entry sentence. The models, efforts, budgets and tools are v1's. (S0009, S0014, story text)
17. `template/` holds only `factory/pipeline.yml`, at the path a project reads it from; the story and feature forms stay the human's, and a project made from the template has no `factory/story-form.md` until the human adds it. (S0009, story text)
18. An agent run's environment is an allow list of six names (`PATH`, `HOME`, `LANG`, `LC_ALL`, `TERM`, `TZ`) applied at its source, `production_environment()`; `TaskComposer` passes it unchanged (F0005 decision 23). The token is read from a file named by `FACTORY_TOKEN_FILE`, default `/run/secrets/hosting-token`, and the factory's git gets it through the credential helper `/usr/local/bin/git-credential-factory`, handed to `GitCli` as `GitOptions.environment` entries (`GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0`, `GIT_CONFIG_VALUE_0`), never through system or global configuration (F0001 decision 7; questionnaire 1, Q17). The same entries carry `core.sharedRepository=group`. (S0002, S0010, story text)
19. The token file must belong to the factory's user and have no permission bit for group or others, else the preflight stops the machine. The operator makes the host file `chown 1000` and `chmod 0400`, because Docker Compose without swarm may ignore the secret's `uid`, `gid` and `mode`. (S0010, story text)
20. The agent is started by `sudo -n -u agent -- env -i NAME=value ... claude ...`. A refusal by `sudo` is an `AgentRuntimeError` raised by the runtime; the preflight's probe of an agent run runs through the same call as the agent user, so a refusal is found as a machine stop before any claim is pushed. A refusal that appears later raises from `StageLauncher.launch` after the claim and is a counted error or a crash (F0005, F0008), which this feature does not change. (S0011, S0013, story text)
21. The agent can write the agent home and the shared checkout, and the model login is kept for the user `agent`; hardening those paths is left for v2. (S0011, story text)
22. The preflight runs one `claude -p` call with the factory's own arguments once for each image build, as the agent user, with a budget of 0.10 dollar and the shipped agent `coder`, and checks the agent run's `PATH` and `HOME` (questionnaire 1, Q22; F0001 decisions 17 and 18). (S0013, story text)
23. The entrypoint starts the factory in `/opt/factory`, so `claude --version` runs in a fixed directory (questionnaire 1, Q23). (S0005, story text)
24. The project commands (`make check`, `lint`, `test`, and the preflight's `lint`) run agent-written code as the factory's user, who can read the token file; a test can print the token into the output tail that the factory writes into the journal. This is not built now. It is left for v2 and recorded in `docs/decisions.md` and the operator guide. (S0010, the human, 2026-10-14)
25. The preflight fails with an item `agent-user` when `agent_user` is `None` and the token file exists; it passes when the agent user is set, and when no token file exists (tests, local runs). (S0012, the human, 2026-10-14)
26. `image/secrets/` is in `.gitignore`, so the token file there is ignored by git; the human added the line, and the operator guide says so. (S0010, the human, 2026-10-14)
27. The sudoers file for the factory's user sets `umask=0002` with `umask_override` and `!use_pty` beside the one rule, because `sudo`'s own umask would make an agent's directories `755` and the factory's restore could not remove them, and a pseudo-terminal would put the agent in a new session. (S0012, story text)
28. Two tests that other stages wrote change, and the human's word is asked for both, as `CLAUDE.md` requires: F0003-S0005's `tests/adapters/test_agent_files.py::test_a_key_the_reader_does_not_interpret_is_left_aside` is deleted by S0008, because it asserts the opposite of SI4.1 and F0003's decision 14 left the other keys ignored only "until F0010"; F0006-S0006's test of its criterion 20 (the exit-2 line `no instance settings are wired yet`) is deleted by S0003, because F0006-S0006's own Assignment says F0010 replaces that line. (S0003, S0008, story text)
29. The factory writes the files of an agent run with the mode `0640` (instructions, guard settings, hook settings), so that the agent, who reads them as a member of the group `factory-work`, cannot rewrite its own guard settings and widen its write paths; this changes F0001's `ClaudeCodeRuntime`. (S0011, story text)
30. Open for the human: `run_process` kills the process group of an agent call at its `time_limit`, and under `sudo` the group's leader is a root-owned process that the factory's user may not signal (`PermissionError`, which becomes `AgentRuntimeError` while the agent runs on). Two repairs are possible: a `timeout --signal=KILL` wrapper inside the `sudo` call, with the runtime reading its exit status 137 as the limit and a grace time on the outer call; or a kill through `sudo -n -u agent -- kill`. Neither is built, because each needs a hook in `process.py` or a rule for exit statuses that cannot be shown without `sudo`; the morning observation lists it. (S0011, story text)
31. The probe of an agent run reads the shipped agent `coder` and lowers its budget to 0.10 dollar, so that it uses the model, tools and effort of a real run; an installation without an agent named `coder` fails the probe. (S0013, story text)
32. v1's role and stage texts are carried from a copy of v1's `claude/` tree that the human adds as `docs/v1-texts/` before S0014 starts; without it the coder asks. (S0014, story text)
33. A checkout whose clone was killed half-way is not recognised: only a missing checkout is recloned, and the operator deletes the directory. (S0001, story text)
34. The settings reach the services through one object: `Boundaries.settings`, and, where a story names it, as an argument that the wiring fills with the same object. (S0002, S0006, story text)
