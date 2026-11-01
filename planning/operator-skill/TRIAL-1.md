# The Kumpel skill's first trial (2026-11-01)

The first version of `operator/skill/kumpel` run by Claude Code at home on the todo demo, after F0047 was accepted: `pkrahmer/kumpel-demo-todo` (factory-rf's `demo/todo-service/project` with feature F0001), a second instance `demo` on the VM `factory-vm` beside `vm`, its code from factory-rf by `--code-url`. The human's leave (2026-10-31): two or three stories, `merge` off for the first and on afterwards. The skill's own log is `.kumpel/log/2026-11-01.md` in the demo repository.

## What ran

| Story | Path through the skill | Cost |
|---|---|---|
| F0001-S0001 (domain model and in-memory repository) | started by `start-story.sh`; `wait.sh` to the approval; `approval.sh`; verdict posted with `merge` off; merged by the human; archive seen by `wait.sh` | $3.14 |
| F0001-S0002 (service layer with filtering) | started with `start_next` on; approval with an earlier test changed under the standing leave (read as `approving.md` asks); merged by the skill with `merge` on | $1.66 |
| F0001-S0003 (HTTP API) | the intake's question answered by `answering.md`'s rule ("as you propose" when the option follows from the Interface); approval; merged by the skill | $2.37 |

Three stories in about 70 minutes, $7.17, one question, no round back. The factory itself ran the demo without a fault once its instance was up.

## What the skill got wrong, and what changed

1. **`wait.sh` reported "no work-item pull request is open" one minute after a story started**, in the gap before the factory opens the pull request. Fixed (`86f2536a3`): it reports an empty list only when a pull request was open and has gone.
2. **The wait beside another call.** `SKILL.md` says the wait must be the only call of its message, because calls in one message run in parallel. The operator broke that once and the wait failed at once (it ran in a fresh shell before the other call's `cd` mattered). The rule is right; keep it prominent.
3. **`approval.sh`'s journal tail is hard to read when filtered.** The useful lines (the smoke tester's `Met` and `Findings`, the tester's naming of each earlier test's leave) are indented and long. The second version should print those lines explicitly, and take the cost from the pull request's cost table (`<!-- factory key=...:cost_table:... -->`), which also works where long file names break a local `git show` on Windows.
4. **The next story is the agent's guess.** `start_next` needs the feature's build order; the agent read it from `feature.md`. The second version should have `next-story.sh`: the first story of the feature's *Stories* list that is still in `backlog/`, when nothing is in progress.

## What the factory got wrong (not the skill)

1. **`vm/setup.sh` makes no first `@base`.** A new instance stopped at its preflight: `zfs rollback -r tank/factory/demo@base failed: dataset does not exist`. The guide names the step only in the `dataset` item's error text. Made by hand (`zfs snapshot tank/factory/demo@base`). A candidate: `setup.sh` makes the first base when the dataset has none.
2. **A first start without a base leaves a wrongly owned folder in the dataset.** After the base was made, the sync failed with `/work/checkout/.git: Permission denied`: `checkout` belonged to uid 165536 (mapped from a container), made during the failed first start and kept by the snapshot. Removed by hand and the base retaken; it did not come back. A candidate together with 1: with a first base made by `setup.sh`, the failed first start cannot happen.

## What held

- `settings.sh`: init, show, get, a refused value; the switch changed between stories without a restart.
- `status.sh` from GitHub alone: the stage label, `waits: approval`, `waits: question`, `verdict posted` after the skill's verdict, the last archive.
- A verdict comment at the approval changes nothing in the factory (the operator guide: a comment on a work item that does not wait for you is only recorded).
- `start-story.sh` pulled first and pushed; the factory's own pushes to `main` (stop records, archives) did not collide.
- The project log in `.kumpel/log/` stayed out of every role's write paths.

## For the second version

Done on 2026-11-01 (the human's choice: by hand now): 1 was fixed during the trial; 2 is now a bold rule at the top of the loop in `SKILL.md`; 3 `approval.sh` prints the smoke test's lines, the findings, the leaves, the journal's last entry and the cost from the pull request (tried on the demo's PR 3); 4 `next-story.sh` names the next story of the build order (tried: `next: F0001-S0004` on the demo, `busy: F0047-S0013` on factory-rf). Still to come: then the trial at work with opencode against the job (the plan's step 3), where status comes from GitHub and a stop's reason from Cloud Logging.
