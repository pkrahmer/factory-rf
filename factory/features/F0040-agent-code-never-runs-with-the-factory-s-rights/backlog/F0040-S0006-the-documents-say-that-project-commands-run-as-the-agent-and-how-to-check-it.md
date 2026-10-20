# The documents say that project commands run as the agent, and how to check it

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0040 made every project command run as the agent's user, under that user's own `timeout`, and gave every agent run and every project command a fresh agent home. Each story's documenter wrote its own part of this, but four older sentences still describe how things were before, and the operator guide is missing the checks that the feature's `feature.md` asks the operator to run after the merge (*The human's changes*, 3). The four sentences are these. (1) `docs/project-guide/processes-and-checks.md`, *Rules of `run`*, says without condition that when a command is ended by `time_limit`, "every process of its session is killed". That holds for the factory's own kill, when there is no user. With a `CommandUser`, the user's own `timeout` kills `make`'s process group, and the leftovers program ends whatever left that group (*Running as another user* in the same file says so). (2) `docs/decisions.md`, *The agent's git trusts the shared checkout*, says "A project command's git (`make` as `factory`) does read it". Since F0040-S0002, `make` runs as `agent`. (3) The decision log's entry of 2026-10-17 on the agent files (F0012-S0025) says, under "Open:", that the files the agent may add to `~/.claude` stay writable and that `claude` reads them (a user `CLAUDE.md`). Since F0040-S0004 the fresh home removes them before every run. The entry of 2026-10-16 got a "closed by" note for the same reason; this one did not. (4) `docs/project-guide/watching.md` says that `build_boundaries` gives `leftovers_command()` to "every agent runtime it builds". It also gives it to the project commands' `CommandUser` when the instance has an agent user. The operator guide's *Morning observations* has rows for the fresh home and for the token's folder. It has no row for the operator's checks 3.1 (a stage's `make` runs as `agent`), 3.2 (the reset does not fail), 3.5 (the shared `.venv` stays group-writable after a check that synced it) and 3.7 (a check that reaches its time limit leaves no process of `agent`). This story corrects the four sentences and adds the four rows. No code, no test, no `README.md` change.

## Interface

None: documents only (`docs/project-guide/processes-and-checks.md`, `docs/project-guide/watching.md`, `docs/decisions.md`, `docs/operator-guide.md`). No module under `src/factory/` changes, and no test changes.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/processes-and-checks.md`, *Rules of `run`*, the bullet on the exit status: the clause "every process of its session is killed" becomes "without a user, every process of its session is killed; with a user, the user's own `timeout` kills `make`'s process group, and the leftovers program ends what left it (see *Running as another user*)". Nothing else in the bullet changes.
   - `docs/decisions.md`, *The agent's git trusts the shared checkout*: "(`make` as `factory`)" becomes "(`make`, as `agent` since F0040-S0002)".
   - `docs/decisions.md`, the entry of 2026-10-17 (F0012-S0025) on the agent files: after the clause on the files the agent may add to `~/.claude` that `claude` reads, the note "(closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*)". The rest of its "Open:" list stays as it is.
   - `docs/project-guide/watching.md`: the sentence on `leftovers=leftovers_command()` also says that, when the instance has an agent user, `build_boundaries` hands the same list to the project commands' `CommandUser` (see `processes-and-checks.md`, *Running as another user*).
   - `docs/operator-guide.md`, *Morning observations*: four new rows, after the row "The home is fresh". (a) "A project command runs as `agent`": `docker exec <container> ps -o user,args -C make` while a stage's check runs; expected: every line's user is `agent`, and there is no `make` of `factory`. (b) "The home is reset": `docker exec <container> tail -n 50 /state/factory.log` after the first stage run after a rebuild; expected: no `cannot reset the agent's home`, and the run passes. (c) "The shared `.venv` stays writable": `docker exec <container> find /work/checkout/.venv -maxdepth 3 ! -perm -g+w` after a check that synced it; expected: nothing printed. (d) "A check at its limit leaves no process": `docker exec <container> ps -o user,pid,args -U agent` after a check that reached its time limit; expected: only the header (the user's `timeout` ended its group, and the leftovers program ended the rest).
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`. `README.md`: none, because nothing a newcomer does changes.

## Smoke test

```bash
grep -c "(\`make\` as \`factory\`)" docs/decisions.md
```
Expect: `0`

```bash
grep -c "without a user, every process of its session is killed" docs/project-guide/processes-and-checks.md
```
Expect: `1`

```bash
grep -c "ps -o user,args -C make\|find /work/checkout/.venv -maxdepth 3" docs/operator-guide.md
```
Expect: `2`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
