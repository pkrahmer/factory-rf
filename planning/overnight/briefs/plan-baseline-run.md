# Brief: prepare step 10, the baseline todo run (a plan, no build)

## Goal

Write `C:/Dev/Projects/factory-rf/planning/overnight/baseline-run-plan.md`: the plan for step 10 of "The order of the work after F0011" in `planning/overnight/restructure-after-f0011.md` (the baseline todo run, at the very end, under the strict rules: v1.1 builds `demo/todo-service` into a new empty repository, a session plays the human, disk records at start and end; it passes when everything is accepted with no fix to `factory-rf` during the run, every stop reached the human, and the cost and the agent minutes of each story first-pass in both runs are within 25 % of run 4's; start-to-archive minutes are recorded, not compared; it is the baseline v2 is measured against). The plan must let a later session run it without asking:

1. **The numbers to compare against.** Find run 4's per-story first-pass cost and agent minutes (v1's demo run of 2026-10-05 on `pkrahmer/factory-demo-todo`, now `factory-v1-demo-todo`: its cost tables and records, wherever this repository and the session logs keep them: search `docs/runs/`, `session-logs/`, `planning/`), and the shakedown run's (step 4, v1.1 on `pkrahmer/factory-demo-todo`, 2026-10-17/18). Define "first-pass" exactly (the runs of a story up to its first approval hand-over, without the runs a human's answer caused? say which and why), and give a table: story id, title, run 4 cost and agent minutes, shakedown cost and minutes, the 25 % band. Name every gap where a number cannot be found, and how the run would measure it instead.
2. **The setup**, step by step: the new repository (the human creates it; the token's access), seeding it from `demo/todo-service/` as for the shakedown (find how that was done: `planning/overnight/first-start-checklist.md`, `planning/overnight/demo-fixes-F0016.md`, the night log `docs/runs/2026-10-12-overnight/night-log.md`), the instance name, the compose command with its variables, the disk records at start and end, which runtime (Claude on the subscription, as for run 4; opencode is a separate comparison and not the baseline).
3. **The session's rules as the human**: what it may answer and how (within the demo's features' decisions only, never a fix to `factory-rf`), what counts as a fix that fails the run, what to do at a stop, the watcher and heartbeat it uses, what it logs and where.
4. **What must be true before it starts**: the steps before it (F0020, F0022 to F0025, the rename of step 9) and which of them change the numbers (for example F0023's skipped checks and F0024's per-story mutants change agent minutes), so that the comparison stays fair; recommend whether the 25 % band applies to cost, agent minutes, or both, given those changes.
5. **The report** the run ends with: its sections and its tables.

## Not

No git commands except read-only ones (`git log`, `git show`) in this repository and in local clones you find; read GitHub only with `gh` read-only commands (`gh pr list`, `gh pr view`, `gh api` GETs) on `pkrahmer/factory-demo-todo` and `pkrahmer/factory-v1-demo-todo`; no other network. No file other than the plan. Do not start sub-agents. No paid model call. Never read a token or key file. You may look inside `factory-self-factory-1` read-only (`MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 <command>`); change nothing there. Temporary files only in `C:/Users/pasca/AppData/Local/Temp/baseplan`, removed when done.

## Reply

The comparison table (or its gaps), the setup in short, the open points for the human with recommended answers.
