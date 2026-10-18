# The unattended night of 2026-10-19

The human sleeps; the session plays the human for `self` (v1.1 building factory-rf) by the routine of `planning/operator-playbook.md` and the decisions of each feature. Every act is a row in `docs/runs/2026-10-12-overnight/night-log.md`; a choice the decisions do not cover is answered with the agent's recommendation when it stays inside the feature's scope, and marked **For the morning**.

## Where it starts (00:55 local, 22:55 UTC)

- F0021 (the factory records what the human did): S0001 merged (#235); S0002 in progress (#236, at the coder); S0003 to S0006 in `backlog/`; then the acceptance.
- F0020 (opencode as a second agent runtime): eight stories drafted, pre-checked and fixed in `planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/` (S0009 in `deferred/`); its notes from F0021's pre-check are at the end of its `feature.md`.
- Usage: weekly 4 % (resets Mon 2026-10-20 05:00 local); the 5-hour window about 35 %.

## The order

1. **F0021 to its end.** Per story: follow the board; answer a question within the decisions; at approval check the six points of the playbook (the diff's files, the reviewer's last entry, the smoke test's `Expect:`, every earlier test changed with its leave, nothing outside the write paths, the cost); merge; wait for `work item <id>: merged, archived`; **rebuild `self`** (F0021's change 2); start the next story.
   - **Before S0006 starts:** F0021's change 3, the `CLAUDE.md` bullet on the records contract (the exact text in `feature.md`), as its own commit.
   - From S0003's merge and rebuild on, the factory commits `stops recorded` on `main`: pull before every push.
   - The acceptance opens by itself after S0006. Proposed stories: start them in turn when they are of the feature's kind; drop or defer one that reopens a decided point, with a decision in `feature.md`.
2. **F0020's stories brought up to date with F0021**, before F0020 starts: one fix agent (sonnet, the subscription) applies the four notes at the end of F0020's `feature.md` to its stories (S0001's `login` key after `denied_paths`; S0004's `PermissionDenial.path` from opencode's `filePath` with a criterion; S0005's `provider_limit` in `StallReason` of `factory.domain.journal` and the `denials` row; the schema regeneration and the contract's minor version in every story that changes `CostRecord` or the stall reasons). Its temporary folder: `C:/Users/pasca/AppData/Local/Temp/f20fix`, nowhere else. Check every story with `factory-check-story` (the Landlock adapter stubbed on Windows). Commit by named files.
3. **F0020.** Move the feature to `factory/features/`, start S0001, and build S0001 to S0008 one after another as in step 1, rebuilding `self` after each merge. The human's changes at their points:
   - **change 1, before S0001's pull request is merged:** `: > image/secrets/anthropic-api-key` (an empty file, no key; it is git-ignored);
   - **changes 2 and 7, before S0004 starts:** the `CLAUDE.md` wording of R5 and R12, and the `PLR0913` per-file ignore for `src/factory/adapters/opencode_runtime.py` in `pyproject.toml`, each as `feature.md` gives it;
   - **change 3, after S0005's merge:** the `CLAUDE.md` vocabulary sentence;
   - **change 4, after S0008:** the hook's refusals in `/home/agent/.claude/projects/` listed against the kernel's, as F0019's decision 16 says; the result in the night log;
   - **change 5, after S0008:** the template's and the demo's `Makefile`, `pyproject.toml` and pipeline definitions as `feature.md` gives them; `make check` green before the push;
   - then F0020's acceptance.
4. **Stop at change 6.** The todo-demo run on opencode needs the human's key. Nothing is placed or read. Leave it **For the morning**.

## Standing order: planning in spare capacity (the human's word, 2026-10-19 01:07; until the weekly reset, Mon 2026-10-20 05:00 local)

At every heartbeat: when the 5-hour window likely has spare room (about 60 % or less with under 2.5 hours to its reset) and no planning agent runs, start one planning agent on the subscription for the remaining steps that needs no human. It writes only under `planning/overnight/` and its own temporary folder under `C:/Users/pasca/AppData/Local/Temp/`. In order: the draft of step 6 (F0022, a project's own skills and agents; started 01:07), its pre-check, then the draft and pre-check of step 7 (skip known checks), then of step 7a (mutation testing per story). Briefs in `planning/overnight/briefs/`; results **For the morning**. The build of the stories always comes first: a planning agent never delays an answer, an approval or a start.

## Stop and wait for the human (log it, start nothing new)

- Usage: the 5-hour window above 95 % (let the running story finish; start the next when it resets); the weekly window above 90 %.
- A machine stop in `/state/factory.log` that the playbook's incident table does not cover, or a stop that comes back after its fix.
- A story that reaches a cap a second time, or a run whose cost is far above the stories before it without a reason in the journal.
- A question that would change a decision of the feature, widen the scope, or silence a check without a reason.
- Anything that needs a key, a token, a Windows or Docker setting, or the deletion of the human's files.
- Docker not answering after one restart of Docker Desktop.

## Never

- Edit a running work item on `main` (amend on its branch: merge `main` in, edit, push).
- Push between a merge and its archive commit.
- Start v1 (`C:/Dev/Projects/factory`) or run `docker compose up` there.
- Read, print or copy a token or key file.
- Stage anything but named files.

## The heartbeat (every 30 minutes)

Docker answers (`timeout 15 docker info`); the disk has room (`df -h /c`, stop below 5 GB); the board (`factory-watch` in `factory-self-factory-1`) and the factory log's last lines; a watcher (`scratchpad/demo_follow.sh`) runs for the story in progress; a stage running far over its time limit; the usage windows. Nothing to do: one line.

## In the morning, for the human

- What the night built, its cost and every **For the morning** row.
- Change 6 (the todo demo on opencode, the key) and the hook's cross-check result.
- Still open: delete `C:/t20`, `C:/t21` and `%TEMP%/claude/ed.py`; review `planning/operator-playbook.md`; look at the Factory Timeline.
