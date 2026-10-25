Heartbeat for v1.2's instance `vm` (the Multipass VM `factory-vm`) building factory-rf. `self` is retired (2026-10-25); never start or touch Docker instances, and never touch v1 in C:/Dev/Projects/factory. Read the memory note factory-rf-overnight-run first (its newest UPDATE line holds the build order and the rules).

Check, in this order:
1. `multipass list`: `factory-vm` is Running (if stopped and a story is due, `multipass start factory-vm`).
2. On the VM (`MSYS_NO_PATHCONV=1 multipass exec factory-vm -- sudo bash -c '...'`): `systemctl is-active factory@vm`; `/srv/factory/vm/state/health.json` (stops in force); the last lines of `/srv/factory/vm/state/factory.log`; `df -h /srv/factory/vm` (stop between stages below 5 GB).
3. The board, filtered to the current feature: `sudo -iu factory bash -c 'set -a; . /srv/factory/vm/factory.env; set +a; cd /srv/factory/vm/repo && /srv/factory/vm/factory/.venv/bin/factory-watch'`.
4. A watcher for the story in progress: `FOLLOW_VM=1 sh <scratchpad>/demo_follow.sh 180`, run in the background.
5. A pull request waiting for an answer or approval: answer within the decisions after the question comment is posted; run the six approval checks; merge with `gh pr merge <n> --merge`; wait for the archive commit; make the human's change due; start the next story (`sh <scratchpad>/start_story.sh <id>`), pre-checked one ahead.
6. After a merge that changes `src/`, `vm/`, `pyproject.toml` or `uv.lock`: rebuild `vm` between two stages by the operator guide's "The rebuild after a merge"; copy `vm/setup.sh` from `git show HEAD:vm/setup.sh` (LF line endings) and transfer it from a relative path.
7. On `main_branch_failing` with lint or syntax errors that `main` does not have: compare every tracked file of `/srv/factory/vm/work/checkout` with git (`git hash-object --no-filters` against `git ls-files -s`), the zero-byte fault of 2026-10-25; repair by `rm .git/index; git reset --hard`, then move `@base`.
8. Usage with get_usage: start a story only at or below 95 % of the 5-hour window and 90 % weekly.

Rules: never read, print or copy keys or tokens (size checks with `test -s` only); stage named files only, pull before push, and let a failing secrets hook stop the commit; nothing paid on GCP. Log every act in docs/runs/2026-10-12-overnight/night-log.md with times from `date -u`; choices beyond the decisions marked **For the morning**. Show the status bar only when something changed. If nothing needs doing, say so in one line.
