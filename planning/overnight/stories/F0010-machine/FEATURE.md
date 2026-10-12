# The machine

## Goal

One pinned container runs one project and keeps its own faults visible. The project's repository URL and the instance's name come from environment variables, the checkout is one fixed path on a volume and is recloned when it is missing, and the loop ticks with a pause of 15 seconds after activity that doubles to 120 seconds while idle. The image pins every tool and records its identity in each cost record. After each fetch a preflight checks the machine, only when the image build changed, and probes the main branch with the project's lint, only when the main branch moved; the machine's own stops make the container's health check fail. Agent files hold only keys the agent runtime applies, and an agent run holds no credential for the hosting service: it runs as a second unprivileged user with an allow-listed environment while the token stays in a file only the factory's user can read. Done when each of these is shown by a test, with the parts that need Docker, root or a second operating-system user shown by a static test of the files plus a morning observation.

## Scope

- One instance, one project (R2, R25): settings from the environment, the fixed checkout path, the reclone, the loop and its pauses (ST7.1, ST7.2, ST7.3).
- The pinned image (R29, R4): the base image by digest, Claude Code and the tool packages by exact version, the factory installed from the lock file, the image identity in each cost record, no `tasks/.gitkeep` in the template (ST5.1, ST5.2, ST5.4, SI3.3).
- The health check and the entrypoint's stops (R27, container side): the health command, the compose file with a restart policy and a health check, the entrypoint with time-stamped lines, the wait for a repository that is not ready (ST3.3, ST3.4 for the entrypoint).
- The preflight's items: the tools, the hosting service, the agents where `FACTORY_CLAUDE_HOME` points, the agent runtime's version against the pinned one (ST4.4, ST5.3).
- The probe and the stamp: lint probed on the main branch after the fetch, the stamp keyed to the image build, a failing main branch a reported stop (ST4.1, ST4.2, ST4.3, ST4.5).
- Agent files without dead keys, refused at load as a reported stop, and the shipped agents, settings and pipeline definition template, each key with an effect (SI4.1, SI4.2, SI4.3, R30).
- No hosting-service token in an agent run, and agent runs as a second unprivileged user (WE3.1 to WE3.5, R33).

## Out of scope

- A watchdog for a container that is dead: Docker's restart policy and the health check are what R27 names.
- Preflight checks of the project's setup, of the hosting service's settings and of the token's expiry.
- A sandbox for agent runs, and writes by an agent to ignored paths or outside the checkout (left for v2).
- The table of all stops and its tests: feature F0011.
- The long stage and role texts of v1's skills, the story and feature forms, and any skill the runner does not apply.
- The console script entries in `pyproject.toml`, which lie outside every write path: the human adds them.

## Stories

- S0001 — One instance, one project, one checkout
- S0002 — The pinned image
- S0003 — The health check and the entrypoint's stops
- S0004 — The preflight's items
- S0005 — The probe on the main branch and a stamp keyed to the image
- S0006 — Agent files with no dead keys
- S0007 — The shipped agents and settings
- S0008 — No hosting-service token in an agent run
- S0009 — Agent runs as a second unprivileged user

## Decisions taken for the human

1. The repository URL may not contain a comma or whitespace, and v1's `REPOS` list is not read at all: one instance, one project. (S0001, story text)
2. An instance name is a lowercase letter followed by lowercase letters, digits and hyphens, the same pattern as every other name. (S0001, story text)
3. The checkout is `/work/checkout` and the state directory is `/state`; no variable changes either. (S0001, story text)
4. The pause is 15 seconds after activity and doubles for each further idle tick up to 120 seconds; the first tick of a start runs at once; a repository that is not ready and a tick that raises an exception both count as idle, and the exception is logged in one line. (S0001, story text)
5. A start with an invalid environment writes a machine stop and a time-stamped line, then ends with status 2. (S0001, story text)
6. The base image digest and the six Debian package versions in the Dockerfile are placeholders (a digest of 64 zeros, the version `0~unpinned`), because they cannot be looked up without a network; the human replaces them before the first build. Claude Code 2.1.289 and `uv` 0.9.2 are the versions of v1's last build. (S0002, story text)
7. The image identity is a build argument without a default, so a build without one fails; an unknown identity (a run outside the image) never validates a stamp. (S0002, story text)
8. The image creates two users, `factory` (uid 1000) and `agent` (uid 1001), in the shared group `factory-work`; the container runs as `factory`, and the directories `/work`, `/state` and `/home/agent/.claude` are group-writable. (S0002, story text)
9. The health check runs every 30 seconds, times out after 10 seconds, fails after 3 retries and waits 60 seconds at start. (S0003, story text)
10. A repository that is not ready (not cloneable, no main branch yet, no pipeline definition on main) is the repository stop `repository_unavailable`, written once for each distinct detail. (S0003, story text)
11. v1's preflight item for the git identity is not rebuilt: the entrypoint sets the identity from its defaults, so it cannot be missing. (S0004, story text)
12. The agent runtime's version matches when the first word of what it reports equals the pinned version. (S0004, story text)
13. The preflight runs after the fetch and the reset of the checkout, before the pipeline definition is loaded; so the probe's `time_limit` is the constant 10 minutes, not the pipeline definition's. (S0005, story text)
14. The machine items are skipped while the image build is unchanged, with no timer; the lint probe repeats only when the main branch moved, so an idle tick runs no project command. (S0005, story text)
15. An agent file may hold only `model`, `tools`, `effort` and `budget_usd`; v1's six dead keys and `skills` are refused, and keys are case-sensitive. (S0006, story text)
16. No skills are shipped. The shipped agent bodies hold the boundary sentence and the entry contents of each role; the long stage texts of v1's skills are for the human to add. The models, efforts, budgets and tools are v1's. (S0007, story text)
17. `template/` holds only `pipeline.yml`; the story and feature forms stay the human's. (S0007, story text)
18. An agent run's environment is an allow list of five names (`PATH`, `LANG`, `LC_ALL`, `TERM`, `TZ`) plus what the composer adds; the token is read from a file named by `FACTORY_TOKEN_FILE`, default `/run/secrets/hosting-token`, and git gets it through a credential helper that reads the same file. (S0008, story text)
19. The token file must belong to the factory's user and have no permission bit for group or others, else the preflight stops the machine. (S0008, story text)
20. The agent is started by `sudo -n -u agent -- env -i NAME=value ... claude ...`, and a refusal by `sudo` is a counted error, not a stall. (S0009, story text)
21. The agent can write the agent home and the shared checkout, and the model login is kept for the user `agent`; hardening those paths is left for v2. (S0009, story text)
