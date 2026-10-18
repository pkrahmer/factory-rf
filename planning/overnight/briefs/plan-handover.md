# Brief: plan the handover of factory-rf from v1 to v1.1 (plan step 5)

## Goal

Write the exact plan for the handover: the one human commit, and the steps around it, after which v1.1 builds `pkrahmer/factory-rf` itself and v1 no longer does. The plan says it is "one human commit while no v1 story is in progress: v1.1's own pipeline definition and forms replace `factory/stages.yml`, `TICKET.md` and `FEATURE.md`, `CLAUDE.md`'s vocabulary rule turns to v1.1's words, and v1's features stay as history where v1.1 does not read them (decision 008: v1.1 reads no v1 work item, so none may be left in progress)". Turn that into something the session can carry out without a guess, checked against v1.1's code as built, so that v1.1's first tick on factory-rf finds a valid repository and no stop.

## Inputs (read these first)

- The plan: `C:/Dev/Projects/factory-rf/planning/overnight/restructure-after-f0011.md`, step 5 and the section "v1.1 builds itself".
- The night log's 2026-10-18 rows: `docs/runs/2026-10-12-overnight/night-log.md` (the shakedown, F0016, the human's open items).
- v1.1's code as built: how it reads the repository (`src/factory/` readers of `factory/pipeline.yml`, `factory/story-form.md`, `factory/features/<feature>/feature.md` and its `backlog/`, `in-progress/`, `done/`), what its health check and the stop `repository_unavailable` require, how it treats a folder under `factory/features/` that is not in its layout (v1's `FEATURE.md`, `drafts/`, `ongoing/`, `done/` with v1's tickets, `ACCEPTANCE.md`), branch names (`work-item/<id>`) against v1's (`ticket/...`, `acceptance/...`), labels, and anything on the hosting side (open pull requests, labels of v1) that v1.1 would read.
- The template v1.1 sets a project up from: `template/` (`CLAUDE.md`, `Makefile`, `factory/pipeline.yml`) and the demo's `demo/todo-service/project/factory/pipeline.yml` (an example with `docs/openapi.json`). factory-rf's own lanes today: `factory/stages.yml` (v1's write paths per stage, which v1.1's roles must keep: the coder `src/*`, `image/*`, `template/*`, `claude/*`; the tester `tests/*`; the documenter `README.md`, `docs/*`), its `Makefile` targets (`check`, `lint`, `test`, `duplicates`, `documents`, `mutants`), `pyproject.toml`, `CLAUDE.md` (its *Vocabulary* section and the F0016 change 2 lines in `factory/features/F0016-the-shakedown-findings/FEATURE.md`).
- The operator guide (`docs/operator-guide.md`) and `demo/todo-service/README.md` for how an instance is set up (`FACTORY_REPOSITORY_URL`, `FACTORY_INSTANCE`, the hosting token at `image/secrets/hosting-token`, the agent's login token, branch deletion on merge off, merge commits allowed).
- v1's side: `C:/Dev/Projects/factory/` (read only): how v1 is told which repositories it builds (its `.env`/`REPOS` setting or equivalent; do not print any secret value, read only the variable names), so that it stops taking factory-rf's stories; whether v1 must be stopped or only reconfigured.

## What the plan must hold

1. The preconditions, each with the command that checks it (no v1 story or acceptance in progress or open; the image to build from; disk; usage).
2. The commit, file by file: what is added (factory-rf's `factory/pipeline.yml`, roles with write paths, `time_limit`, `lease_duration`, the stages, the project commands; `factory/story-form.md`), what is removed or moved (`factory/stages.yml`, `TICKET.md`, `FEATURE.md`), where v1's features go so that v1.1 reads none of them as a work item (and whether moving them breaks a test in factory-rf that reads `factory/features/`; search `tests/`), the `CLAUDE.md` changes (vocabulary rule, F0016's change 2), and anything else a test or `make check` needs afterwards. Give the exact text of `factory/pipeline.yml`. Recommend one option where there is a choice, with the reason.
3. The instance: the commands to start a v1.1 instance on factory-rf (its name, the compose call, the hosting token: say exactly what scope a new fine-grained token needs; the human makes and places it, the session never reads it), the agent login, the health check, and what to watch on the first tick.
4. v1: how it stops taking factory-rf's stories (the change, the command), and how it stays the fallback.
5. The first story v1.1 builds on itself and how to start it (the plan's order puts 5a, the write guard, first; the session's earlier recommendation was step 7, skipping known checks, as a small first story: list both, recommend one, the human chooses).
6. What can go wrong on the first ticks and how the session sees it; how to roll back (the previous state as one revert commit and v1 restarted).
7. Everything the human must do by hand, in order, marked.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/handover-plan.md`.

## Not

No git commands at all, not even read-only ones. No network calls (no `gh`). No file other than the plan. Do not start sub-agents. Never read or print the contents of a token, key or `.env` value. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and leave nothing behind. You may look inside v1's container read-only with `docker compose exec -T factory <command>` from `C:/Dev/Projects/factory` (`MSYS_NO_PATHCONV=1` first); change nothing.

## Reply

The plan in short (the commit's files, the instance, v1's change, the first story), every choice with your recommendation, every step for the human, and the risks.
