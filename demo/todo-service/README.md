# Demo: v1.1 builds a to-do service

v1.1 builds a working FastAPI to-do service into an empty GitHub repository: eight stories in three features, each through intake, tests, code, review, documentation and a smoke test, each accepted by a merged pull request, and each feature closed by its acceptance. A Claude Code session plays the human: it sets the repository up, puts the stories in, starts one at a time, answers the pipeline's questions on the pull requests, and merges. It writes no product code; the factory's agents do that, in the container.

It is the input of two runs of the plan (`planning/overnight/restructure-after-f0011.md`): the shakedown run, which finds v1.1's faults, and the baseline todo run, which v2 is measured against. Both are measured against v1's run 4 of the same stories (see *What a run looks like*).

## What is in this folder

- `project/`: the empty project the factory builds into. Its `CLAUDE.md` (architecture, tests, docs, checks), `Makefile` (`check`, `lint` and `test` for the pipeline, the other targets of `check`, `duplicates` and `mutants` as reports, `openapi`), `pyproject.toml` with every dependency pinned and its `uv.lock`, `.gitignore`, `.secrets.baseline`, the vendored semgrep rules under `security/semgrep/`, the package `src/app/` and the test package `tests/`, both empty, a README for the service's readers, and under `factory/` the pipeline definition (`pipeline.yml`) and the story form (`story-form.md`).
- `features/`: the three features with their stories, ready to copy in. Each `feature.md` already lists the product decisions behind its stories; each story waits in its feature's `backlog/`.
  - `F0001-todo-service`: domain model, service layer, HTTP API, SQLite storage (S0001 to S0004).
  - `F0002-operations`: health endpoint, version command, statistics (S0001 to S0003).
  - `F0003-search`: title search (S0001).

The pipeline definition is the template's (`template/factory/pipeline.yml`) with two changes: the coder may also write `docs/openapi.json`, which `make openapi` generates from the routes, and `make duplicates` runs as a report after the coder's stage.

## What you need

- Docker with Compose, `git`, `uv`, and Claude Code on your machine, and a checkout of v1.1 (this repository); the commands below run from its root.
- An empty GitHub repository for the demo, cloned beside the checkout (`../<repo>`). In its settings, allow merge commits, and turn off "Automatically delete head branches": v1.1 reads a story's state from its branch, and a branch deleted on merge restarts a story whose file is still in `in-progress/` (operator guide, "Branch deletion on merge must be off").
- The GitHub CLI `gh`, logged in with `repo` scope, for the session: it comments, merges and closes with it.
- A token for the container: fine-grained, limited to the demo's repository, with Contents and Pull requests read and write. It lives in `image/secrets/hosting-token`, owned by uid 1000 and readable by it alone (operator guide, "The hosting-service token").
- A Claude login for the container's user `agent`; the agents run there as Claude Code.

## How to run it with v1.1

These steps run v1.1's container, which is kept at the tag `v1.1`; since F0044 an instance runs on the machine of `docs/operator-guide.md`, *The machine*.

1. Put the token in place:

   ```bash
   mkdir -p image/secrets && printf '%s\n' '<token>' > image/secrets/hosting-token
   sudo chown 1000 image/secrets/hosting-token && sudo chmod 0400 image/secrets/hosting-token
   ```

2. Set the instance's two variables in the shell you run Compose from, and keep them for every Compose command below:

   ```bash
   export FACTORY_REPOSITORY_URL=https://github.com/<owner>/<repo>.git FACTORY_INSTANCE=todo
   ```

3. Set the repository up (see *Set up* below) and push `main`: the instance waits with the stop `repository_unavailable` until `main` holds `factory/pipeline.yml`.
4. Build the image and start the instance: `docker compose -f image/compose.yml up -d --build`. Every instance is its own Compose project, `factory-<instance>`, with its own container and volumes.
5. Log the agent user in to Claude once: `docker compose -f image/compose.yml exec -u agent factory claude`, complete the login, `/exit`.
6. Check the instance: `docker compose -f image/compose.yml exec factory python -m factory.entry.health` must print `healthy`. Any other line names a stop of the repository or the machine; the operator guide's section *The stops* says what to do about each.

Then give the session the prompt below.

## The prompt

Start Claude Code in your v1.1 checkout and give it this, with your repository's name:

> Read `demo/todo-service/README.md` and run the demo against `<owner>/<repo>`; its checkout is `../<repo>`. You are the human in the loop: set the repository up, put the features in, start one story at a time, answer the pipeline on the pull requests, merge or close. Never write product code. Stop and report when the demo says to.

Then watch: `docker compose -f image/compose.yml logs -f` for the ticks, the pull requests on GitHub for the work, and the board with `docker compose -f image/compose.yml exec factory factory-watch`.

## For the session: how to run the demo

You are the human in the loop, not a stage. Work in the target's checkout (`../<repo>`), commit with your machine's git identity, push after every step. Run v1.1's commands from the target's checkout with `uv run --project <the v1.1 checkout> <command>`.

### Set up

1. Copy everything in `demo/todo-service/project/` into the target's root, `.gitignore`, `.secrets.baseline` and `security/` included.
2. Run `uv sync` and `make check` in the target. It must end with `check: green` before the first story.
3. Commit `Set up the repository for the factory` and push.

### Put the stories in, one at a time

1. Copy a feature from `demo/todo-service/features/` into the target's `factory/features/`: its `feature.md` and its `backlog/`. Check its stories with `factory-check-story <path>...`: every line must end in `: ok`. Commit `F0001: add the feature and its stories` and push.
2. Start the lowest story: `mkdir -p factory/features/<feature>/in-progress && git mv factory/features/<feature>/backlog/<story>.md factory/features/<feature>/in-progress/`. Commit `F0001-S0001: start` and push. The factory opens the branch `work-item/F0001-S0001` and a draft pull request.
3. Wait until the story's pull request is merged and the factory has archived the story (it is in `done/` on `main`, with its cost records beside it). Pull, then start the next one.
4. When a feature's last story is archived, the feature's acceptance is due, and the factory opens it as a work item of its own (`F0001-A0001`, its report in the feature's `in-progress/`). Its pull request reaches you at the approval with the recommendation, the findings and the proposed stories.
   - Merge it if the recommendation is fair. Its proposed stories stay in the feature's `backlog/`; they are yours to refine, and this demo does not start them.
   - Otherwise close it with a comment saying why: the acceptance is booked as refused.
5. Then copy in the next feature. A story takes about ten minutes when nothing asks.

### Answer and decide

- **The pipeline asks** on a pull request (an agent's question, the form's findings, a cap): answer with a comment, as a sensible single-user to-do service would. The factory copies your answer into the story's journal, and the stage runs again. Add every product decision you take to the feature's `feature.md` under *Decisions taken for the human*, in a commit on `main`.
- **A pull request is ready** (stage `approval`): read its description (the story, the reports of the tester, the reviewer, the documenter and the smoke tester, the commits) and the cost table.
  - Merge with a merge commit (`gh pr merge <n> --merge`) when the story does what it says.
  - Otherwise comment what should change, then close it: the story goes back to `doing` with your comment as the finding.
- **Never** edit the target's `src/`, `tests/`, `README.md` or `docs/`: they belong to the stages. Never touch `.claude/` in the target, never put the token into a commit, never rewrite pushed history, never push to a `work-item/` branch, never run a stage's commands by hand to help a stuck story.

### Stop and report

Stop when one of these happens:

- the pipeline has spent more than 40 USD on the target (`factory-bill` with no argument for the work items in flight, plus the cost lines of the archived ones);
- you have been running for four hours;
- a stop stands in the health status that a fix of the target cannot clear, or a stage stalls in a way that looks like a fault of the factory, not of a story: the same stall twice, a stage that cannot finish, the log repeating a line;
- a pull request would merge something you believe is wrong although every stage passed it.

Stopping means: leave the pull request as it is, and write a summary as your last message. Cover what was built, what the pipeline asked and what you answered, every product decision, what went wrong with the log lines that show it, the cost and time per story, and what is open.

### Watch and act

```bash
docker compose -f image/compose.yml logs -f --since 5m                    # the ticks, the stops
docker compose -f image/compose.yml exec factory factory-watch            # the next event and the board
docker compose -f image/compose.yml exec factory python -m factory.entry.health   # the stops in force
gh pr list --repo <owner>/<repo>                                          # what is open, and whether it is ready
gh pr view <n> --repo <owner>/<repo> --comments                           # a question, the cost table
gh pr comment <n> --repo <owner>/<repo> --body "…"                        # an answer; the factory copies it into the journal
gh pr merge <n> --repo <owner>/<repo> --merge                             # accept; the factory archives the story
gh pr close <n> --repo <owner>/<repo>                                     # at the approval: send back (comment first); before it: discard
v11=$PWD; (cd ../<repo> && git fetch -q && uv run --project "$v11" factory-bill)    # what the work items in flight cost
```

The container keeps its own checkout in the `work` volume, and its records in the `state` volume (`/state/records/project-commands.jsonl` holds every project command with the time of each target); do not edit there.

## What a run looks like

v1's run 4 built these eight stories and three acceptances on 2026-10-05, 16:49 to 19:36 UTC (2 h 47 min of wall clock, the simulated human's waits included): 59 agent runs, 40 agent minutes, 15.89 USD. Its cost records are in v1's reference (`docs/reference/data/demo-dispatches.jsonl`, the first 59 lines; chapter 16, "Run 4, item by item"). v1 called the smoke test the demo stage; the stories built the same things, in v1's form and with v1's criteria.

| Work item | Agent runs | Agent minutes | Cost | Start to archive | What happened |
| :- | -: | -: | -: | -: | :- |
| F0001-S0001 | 11 | 6.1 | 2.85 USD | 62 min | the reviewer found a gap in a test; the coder asked; the human chose the test change (`doing → tests → doing`); about 52 of the 62 minutes were the human's two waits |
| F0001-S0002 | 6 | 2.5 | 1.31 USD | 7.0 min | clean |
| F0001-S0003 | 6 | 4.0 | 1.54 USD | 8.9 min | clean |
| F0001-S0004 | 8 | 5.0 | 1.94 USD | 10.2 min | one review rework |
| F0001 acceptance | 1 | 5.0 | 1.59 USD | | accepted with proposed stories |
| F0002-S0001 | 7 | 2.8 | 1.36 USD | 10.2 min | an intake question: an empty `TODO_DB` had no criterion (now criterion 3) |
| F0002-S0002 | 6 | 2.1 | 0.85 USD | 7.1 min | clean |
| F0002-S0003 | 6 | 2.2 | 1.12 USD | 7.0 min | clean |
| F0002 acceptance | 1 | 5.0 | 1.47 USD | | accepted with proposed stories |
| F0003-S0001 | 6 | 2.3 | 1.00 USD | 7.3 min | clean |
| F0003 acceptance | 1 | 3.1 | 0.87 USD | | accepted |
| **Total** | **59** | **40.1** | **15.89 USD** | | eight stories 11.97 USD, three acceptances 3.93 USD |

A clean story cost 0.85 to 1.54 USD (1.16 USD on average) in six agent runs and seven to nine minutes from its start to its archive; all eight averaged 1.50 USD. v1's own demo README reports two other runs of the same stories: a clean run of 87 minutes and 14.09 USD for the eight stories (48 agent runs, every stage passing first time), and 4.66 USD for the three acceptances.

In v1.1 a clean story is six agent runs too (intake, tests, doing, review, docs, smoke test) and the approval, which is yours. The cost table on each pull request shows the running total, and `factory-bill` the bill of any work item.

## The shakedown run and the baseline run

- **The shakedown run** (plan step 4) builds the whole demo to find v1.1's faults, not to set the baseline. Every fault is recorded by where it sat (the agent, the pipeline definition, the engine, the template, this demo) and fixed by v1 as a story of v1.1's repository, with a test there, so it cannot come back unnoticed. A fix in this demo's files is the human's change to `demo/`.
- **The baseline run** (plan step 10) builds the demo into a new empty repository with no fix to v1.1 during the run. Record the disk at its start and its end: the host drive's free space, the size of Docker's disk image, `docker system df`, and the container's `df` and the size of its `/tmp` and `/work`. It passes when every story and acceptance is accepted, every stop reached the human, and the cost and the agent minutes of each story that is first-pass in both runs are within 25 % of run 4's above; run 4's first-pass stories are F0001-S0002, F0001-S0003, F0002-S0002, F0002-S0003 and F0003-S0001. The minutes from start to archive are recorded beside them but not compared: they hold the human's waits and the tick's pause, which differ between v1 and v1.1. The stories' criteria were rewritten for v1.1 (both sides of every rule as rows of one test, three new criteria in F0001-S0003), so the comparison is of the same stories, not of the same texts.

## Another run on the same target

A run's history and pull requests stay; the next run starts from a commit that removes everything:

```bash
git -C ../<repo> tag run-<n> && git -C ../<repo> push origin run-<n>                  # where the run ended
git -C ../<repo> rm -r -q . && git -C ../<repo> commit -m "Clean the repository for run <n+1>" && git -C ../<repo> push
docker compose -f image/compose.yml down
docker volume rm factory-todo_work factory-todo_state                                  # the checkout, the health status and the records
```

The volume `factory-todo_claude-home` holds the installed agents; the agent's login lives in `/home/agent` and may need repeating after `down` (step 5 above). Then set the repository up again.
