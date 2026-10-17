# Brief: draft F0013, Podman and the token, for v1 to build

## Goal

Write the feature `F0013-podman-and-the-token` and its stories so that v1 can build plan step 1b right after F0012: v1.1 runs under rootless Podman as well as Docker Desktop, and the agent cannot read the hosting token on either. The human decided its content on 2026-10-17 from a probe of v1.1's image under Podman; F0012's acceptance added two small stories to it (F0012 decision 56).

## Inputs (read these first)

- The probe and the human's answers: `C:\Dev\Projects\factory-rf\planning\overnight\podman-probe-2026-10-17.md` (what works, faults 1 to 5, the answers).
- The plan: `C:\Dev\Projects\factory-rf\planning\overnight\restructure-after-f0011.md`, the order's step 1b and step 2.
- F0012's two proposed stories, to take in as they are or improved: `C:\Dev\Projects\factory-rf\factory\features\F0012-housekeeping\drafts\F0012-S0031-*.md` and `F0012-S0032-*.md`, and F0012's FEATURE.md decisions 55 and 56 and its ACCEPTANCE.md.
- The image and its tests: `image\Dockerfile`, `image\compose.yml`, `image\entrypoint.sh`, `tests\test_image.py`, `tests\test_agent_home_ownership.py`, `tests\test_compose_project.py`, and the operator guide's parts on the image, the token, the start and the runtime (`docs\operator-guide.md`).
- The code that reads the token: search `src\factory` for `hosting-token` and the token file setting.
- The forms and rules v1 applies: `factory\TICKET.md`, `factory\FEATURE.md`, `factory\stages.yml` (write paths: the coder writes `src/*`, `image/*`, `template/*`, `claude/*`; the tester `tests/*`; the documenter `README.md` and `docs/*`); v1's role files under `C:\Dev\Projects\factory\claude\skills\`; `CLAUDE.md` (Tests, Checks, Not without asking); `planning\lessons-for-the-skills.md`.
- How a feature and its stories look when they pass: `factory\features\F0012-housekeeping\FEATURE.md` and two of its stories in `done\` (S0022 and S0025, both image stories).

## The content (the human's answers)

1. The token: the token file is mounted into a folder only the factory user can enter (for example `/home/factory/.secrets`, mode 0700, made in the image), so the agent (uid 1001) cannot traverse it whatever the file's own mode; the compose file's `secrets:` with `uid`, `gid` and `mode`, which Compose ignores outside Swarm, is replaced; the factory reads the token from the new path; the operator guide says where the file lives on the host and that its host permissions still matter. First story, before any real run with a token.
2. F0012-S0031 and S0032 as they were proposed, renumbered for F0013, with their test leaves as FEATURE decisions.
3. Podman's restart: `unless-stopped` needs Podman's restart service in the machine; the operator guide's Podman section says how to enable it (and Quadlet as the alternative), and what the factory does after a machine restart until then. Testable only by hand: say so in the story and leave the test to the first start (step 2).
4. The Compose provider: the operator guide names the docker-compose v2 binary (standalone, Apache 2.0) as the provider for `podman compose`, and says that `podman-compose` 1.5.0 cannot build this compose file on Windows.
5. The operator guide's runtime section: the runtimes that passed (Docker Desktop; Podman with docker-compose v2; Rancher Desktop with the moby engine as untested), and a shared Linux host as the team setup.

## Rules for the split

- One story is one coder's work within $4 and a 60-minute lease. Documentation-only items may be one story whose coder changes nothing and whose docs criterion carries the text.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a Demo's `Expect:` met exactly by the built code, no doubled `-q`.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/stages.yml`, `security/*`) is "The human's change before S000N" in FEATURE.md, with exact lines.
- A story that changes tests another story wrote names them, and FEATURE.md gives the leave as a decision.
- No word of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section in the documents.

## Write

`C:\Dev\Projects\factory-rf\planning\overnight\stories\F0013-podman-and-the-token\FEATURE.md` (Goal, Scope, Out of scope, Stories in build order, the human's changes, Decisions taken for the human with their source) and the stories under `...\drafts\` as `F0013-S000N-<slug>.md`.

## Not

No git commands. No file outside `planning\overnight\stories\F0013-podman-and-the-token\`.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human, and anything you could not place.

Model: opus.
