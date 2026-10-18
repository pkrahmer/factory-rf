---
stage: done
pr: 209
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0015-S0001, F0015-S0002, F0015-S0003]
outcome: accepted
---
# Acceptance of The tiny story's findings

## Verdict

**Accepted with drafts.** Each of the three findings has its story, and the stories together reach the Goal's "Done when". The template's and the todo demo's `make secrets` leave out the cost records, and a test keeps the two recipes equal. The container's first process is the runtime's init. The guides explain all three findings. The feature demo shows this end to end with the real detect-secrets: on the template and on the demo, a run id written by the factory's own writer leaves `make secrets` green, while the old line is red on the same file. One documentation repair is proposed. Three passages still describe a commit by the agent, which the new S0003 text and the decision log now contradict. FEATURE named that fault as out of scope. Separately, the decision log's reason against the factory as the reaper leaves out the race that FEATURE decision 6 gives. Neither breaks a promise of F0015. The human's change 3 (factory-rf's own `Makefile`) is still open and is due before the handover (section 6).

## 1 Scope

None. Each scope bullet maps to one archived story, and the code matches each story's Interface:
- Finding 1, S0001: `template/Makefile:66` is the human's line from `83eaa11`, byte for byte the same as `demo/todo-service/project/Makefile:66` (the human's change 1 is in). `tests/test_template_makefile.py` gains four rows: `sidecar-on-main`, `sidecars-on-branch`, `sidecar-only` and `look-alikes`. `tests/test_demo_makefile_secrets.py` pins the two recipes as equal. The human's change 2 is in: `pyproject.toml:133` has `"demo/"` in `also_copy`.
- Finding 2, S0002: `image/compose.yml` has `init: true` after `restart: unless-stopped`, with its comment. The entrypoint's last line is `exec python -m factory.entry.run`. Both are pinned by `tests/test_compose_init.py`.
- Finding 3, S0003: documentation only. It started after S0001 was merged (intake checked the template line), as decision 11 (2) asks.

Nothing out of scope was built. The run id is unchanged (`RunId`, 32 lowercase hexadecimal characters). `template/CLAUDE.md` is untouched, nothing in the image installs an init, there is no reaper in `src/`, and the agents get no new rule. The one item of the Goal that no story could reach is the real reaping in a running container. By decision 7 that is a morning observation of the shakedown, and the operator guide's table row (`docs/operator-guide.md:146`) now says what to check.

## 2 The feature demo

Green. The script `/tmp/f0015-demo/demo.sh` walks through the feature as an operator of a template project would meet it. It sets up a project from `template/Makefile`, from the todo demo's `Makefile`, and from the template with the old filter line (`before`, made with `sed`). Each project gets a real bare remote, a `main`, and a work item branch with a start commit, as the factory makes one. The script then writes the running run's `started` record with the factory's own `JsonLinesCostRecordWriter` and a fresh `uuid4` run id. It runs the project's real `make secrets`: `uv` is a stand-in that runs factory-rf's own `detect-secrets-hook`, against a baseline made by `detect-secrets scan`. It does this twice: on the work item's first run (sidecar untracked) and on a later run (sidecar committed, then modified). It then checks that the same kind of id in a code file is still found, reads the compose service's `init`, and greps the guides. The script:

```bash
#!/usr/bin/env bash
# Feature demo of F0015: a project set up from the template, a real run's cost record
# written by the factory's own writer, and the project's real `make secrets` (detect-secrets).
set -u
REPO=/work/factory-rf
WORK=$(mktemp -d)
mkdir -p "$WORK/bin"
# `uv run <tool> ...` runs the tool from factory-rf's environment (the real detect-secrets).
cat > "$WORK/bin/uv" <<SHIM
#!/usr/bin/env bash
[ "\$1" = run ] && shift
exec "$REPO/.venv/bin/\$1" "\${@:2}"
SHIM
chmod +x "$WORK/bin/uv"
export PATH="$WORK/bin:$PATH"
unset MAKEFLAGS MFLAGS MAKELEVEL

write_sidecar() {  # the factory's writer, a fresh uuid4 run id, a `started` record
  (cd "$REPO" && uv run python - "$1" <<'PY'
import sys, uuid
from datetime import datetime, UTC
from pathlib import Path
from factory.adapters.cost_records_jsonl import JsonLinesCostRecordWriter
from factory.domain.cost_records import CostRecord
record = CostRecord(run=uuid.uuid4().hex, work_item="F0001-S0001", stage="doing", role="coder",
                    attempt=0, status="started", started_at=datetime.now(UTC))
JsonLinesCostRecordWriter().write(Path(sys.argv[1]), [record])
print(Path(sys.argv[1]).read_text(), end="")
PY
  )
}

project() {  # $1 Makefile to use; prints the folder of a fresh clone on main
  local dir="$WORK/$2"
  git init -q --bare "$dir.git"
  git clone -q "$dir.git" "$dir" 2>/dev/null
  cp "$1" "$dir/Makefile"
  printf '# Todo\n' > "$dir/README.md"
  mkdir -p "$dir/src/todo"; printf 'x = 1\n' > "$dir/src/todo/a.py"
  (cd "$dir" && uv run detect-secrets scan > .secrets.baseline)
  (cd "$dir" && git add -A && git -c user.name=h -c user.email=h@x commit -qm main && git push -q origin HEAD:main 2>/dev/null && git fetch -q && git checkout -qb ticket \
    && mkdir -p factory/features/F0001-todo/in-progress && printf '# Add\n' > factory/features/F0001-todo/in-progress/F0001-S0001-add.md \
    && git add -A && git -c user.name=f -c user.email=f@x commit -qm 'ticket F0001-S0001: start')
  echo "$dir"
}

SIDE=factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl
for case in template demo before; do
  case $case in
    template) mk=$REPO/template/Makefile ;;
    demo) mk=$REPO/demo/todo-service/project/Makefile ;;
    before) mk=$WORK/Makefile.before; sed 's/|\.\*\\\.costs\\\.jsonl//' "$REPO/template/Makefile" > "$mk" ;;
  esac
  dir=$(project "$mk" "$case")
  echo "== $case: an agent's make secrets, the running run's record uncommitted"
  mkdir -p "$dir/$(dirname $SIDE)"; write_sidecar "$dir/$SIDE"
  printf 'x = 2\n' > "$dir/src/todo/a.py"
  (cd "$dir" && git status --short && make --no-print-directory secrets; echo "exit $?")
  echo "-- $case: a later run, the sidecar committed and then modified"
  (cd "$dir" && git add -A && git -c user.name=h -c user.email=h@x commit -qm stage)
  write_sidecar "$dir/$SIDE" >/dev/null
  (cd "$dir" && git status --short && make --no-print-directory secrets; echo "exit $?")
done
dir=$(project "$REPO/template/Makefile" leak)
echo "== template: the same kind of id in a code file is still found"
id=$(cd "$REPO" && uv run python -c 'import uuid; print(uuid.uuid4().hex)')
printf 'token = "%s"\n' "$id" > "$dir/src/todo/a.py"
(cd "$dir" && make --no-print-directory secrets 2>&1 | grep -E 'Secret Type|Location|secrets:'; echo "exit ${PIPESTATUS[0]}")
echo "== the container's first process"
cd "$REPO" && uv run python -c "from pathlib import Path; from ruamel.yaml import YAML; s=YAML(typ='safe').load(Path('image/compose.yml').read_text())['services']['factory']; print('init:', s['init'])"
tail -1 image/entrypoint.sh
echo "== the guides"
grep -c "costs.jsonl" docs/project-guide.md docs/operator-guide.md docs/decisions.md
grep -c "init: true" docs/operator-guide.md docs/decisions.md
grep -c "the running run's" docs/project-guide.md docs/operator-guide.md docs/decisions.md
uv run python -m factory.entry.check_documents
rm -rf "$WORK"
```

Its output follows. Two things are masked in this report: the run ids, shown as `<run id>`, because a real one in this file would turn factory-rf's own `make secrets` red, and the times, shown as `<now>`. detect-secrets' "Possible mitigations" paragraph is also left out.

```
$ /tmp/f0015-demo/demo.sh
== template: an agent's make secrets, the running run's record uncommitted
{"run":"<run id>","work_item":"F0001-S0001","stage":"doing","role":"coder","attempt":0,"status":"started","started_at":"<now>","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null}
 M src/todo/a.py
?? factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl
secrets: green (0.3 s)
exit 0
-- template: a later run, the sidecar committed and then modified
 M factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl
secrets: green (0.3 s)
exit 0
== demo: an agent's make secrets, the running run's record uncommitted
{"run":"<run id>","work_item":"F0001-S0001","stage":"doing","role":"coder","attempt":0,"status":"started","started_at":"<now>","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null}
 M src/todo/a.py
?? factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl
secrets: green (0.3 s)
exit 0
-- demo: a later run, the sidecar committed and then modified
 M factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl
secrets: green (0.3 s)
exit 0
== before: an agent's make secrets, the running run's record uncommitted
{"run":"<run id>","work_item":"F0001-S0001","stage":"doing","role":"coder","attempt":0,"status":"started","started_at":"<now>","duration_seconds":null,"model_seconds":null,"end_reason":null,"turns":null,"tokens":null,"cost_usd":null,"image":null}
 M src/todo/a.py
?? factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl
ERROR: Potential secrets about to be committed to git repo!

Secret Type: Hex High Entropy String
Location:    factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl:1

make: *** [Makefile:60: secrets] Error 1
exit 2
-- before: a later run, the sidecar committed and then modified
 M factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl
ERROR: Potential secrets about to be committed to git repo!

Secret Type: Hex High Entropy String
Location:    factory/features/F0001-todo/in-progress/F0001-S0001-add.costs.jsonl:1

make: *** [Makefile:60: secrets] Error 1
exit 2
== template: the same kind of id in a code file is still found
Secret Type: Hex High Entropy String
Location:    src/todo/a.py:1
exit 2
== the container's first process
init: True
exec python -m factory.entry.run
== the guides
docs/project-guide.md:7
docs/operator-guide.md:3
docs/decisions.md:3
docs/operator-guide.md:1
docs/decisions.md:1
docs/project-guide.md:1
docs/operator-guide.md:1
docs/decisions.md:1
documents ok
```

The `before` case reproduces finding 1 with the tiny story's own conditions, and the template and demo cases show the fix. The `leak` case shows that the filter leaves the scan as strict as before on every other path. With no Docker or Podman on this machine, the demo cannot start a container. The reaping itself is the shakedown's morning observation (decision 7).

The demo also showed something it did not set out to show. A first version of the script had no start commit on its branch. Its `before` case was then green on the untracked sidecar and red only once the file was committed. The reason is that the template's `secrets` takes a branch whose `HEAD` equals `origin/main` for `main` and scans `git ls-files`, the tracked files only, so an untracked file goes unscanned there. The factory's branches always carry the stage-start commit, so this never happens to a work item, and the behaviour predates F0015 (F0012-S0029). No draft.

## 3 Mutation score

`make mutants FEATURE=F0015` printed

```
mutants: no module under src/factory changed by F0015
```

So the score is 0/0, as FEATURE's "The human's changes" (2) foresaw: no story changed a module under `src/factory`. There are no survivors to group. The human's change 2 also puts `demo/` into mutmut's copy, so `tests/test_demo_makefile_secrets.py` and `tests/test_demos.py` will run there at the next feature that changes a module. That cannot be shown here.

## 4 What the stories noticed

- S0001: the coder, the reviewer and the documenter noticed nothing. The demo noticed 15 pytest warnings, `(rm_rf) error removing /tmp/pytest-of-factory/garbage-…/test_seal_takes_the_group_and_0/checkout`. I checked: `/tmp/pytest-of-factory` holds 10 `garbage-*` folders, each with an unreadable `checkout/.git` from `tests/adapters/test_git_cli_seal.py` (F0014-S0006). It also holds 198 `pytest-*` base folders, 5.4 GB in all, on a disk 5 % used. Every later pytest run prints the warnings again. The data stays inside pytest's own base folder, but no cleanup removes it, and in the factory's container it grows with every run of `make test`. I did not pin which row leaves the folder closed, and the fix would change an earlier story's test, which needs the human's leave. So this is listed for the human, with no draft.
- S0002: the documenter noted that the opening paragraph of the operator guide still says a `time_limit` under `sudo` is "first observed at the shakedown". That is still true. The documenter also wrote that FEATURE decision 6 gives no reason for rejecting `timeout --foreground`, and wrote one of its own. FEATURE does give one ("it would no longer kill `claude`'s own children"), and the two agree. What the decision log lost is decision 6's reason against the factory as the reaper (section 5).
- S0003: no one noticed anything. In its cross-read, the documenter did not take up FEATURE's invitation to correct the operator guide's stale parenthesis on the agent's commit (section 5).

## 5 The documentation as a whole

I read README.md, the operator guide's container, make-target and stage-run sections, the project guide's cost-record, template and stage sections, and the decision log's three new entries. The three findings are explained consistently, and each entry is cross-referenced from the guides. `check_documents` prints `documents ok`. There are two findings, both repaired by the proposed draft:
- The guides contradict each other on whether an agent commits. `docs/project-guide.md:869`, from S0003, says the agent cannot commit, because the checkout's `.git` is the factory's alone. The decision log says agents never commit ("The factory alone writes the checkout's `.git`", F0014-S0006). But three older passages still say otherwise:
  - `docs/operator-guide.md:502` says "(or above the agent's last commit, when the agent committed)".
  - `docs/project-guide.md:1495` says "above the agent's last commit when it did (those commits stay in the history)".
  - `docs/project-guide.md:1564` says the same.

  No code in `src/` handles an agent's commit. FEATURE named the first passage as out of scope, so this is not a broken promise. A newcomer reading the guides still meets both statements.
- `docs/decisions.md:503` rejects the factory as the reaper because "it would own PID 1's duties". FEATURE decision 6's reason is missing. A reaping PID 1 would also reap the children `run_process` waits for, and those would find no exit status, a race with every process the factory starts. The decision log is where a later story looks before it adds a reaper, so the lasting reason belongs there.

No example in the new passages fails to run: the operator guide's `ps -eo pid,ppid,user,stat,args` is the command S0002 names, and the grep examples of the stories' demos still match. No section the feature needs is missing.

## 6 Decisions taken for the human

From FEATURE.md's "Decisions taken for the human" and the story logs. Accept them by merging, or revisit:
1. The run ids stay 32 lowercase hexadecimal characters. The projects' scans leave out the cost records instead, rather than a `run-` prefix, a baseline entry per finding, or a pragma per line (decision 1).
2. The pattern is `.*\.costs\.jsonl` in any folder, rather than the narrower `factory/features/.*\.costs\.jsonl` (decision 2).
3. Only the `secrets` recipe of the todo demo is pinned to the template's (decision 3).
4. The human's leave for S0001's tester to add four rows to an F0012-S0029 test. It was taken by the session for the human, to confirm (decision 4). The tester used it as written, with no other change to an earlier test.
5. factory-rf's own `Makefile` gets the cost-record exclusion before the handover, not before S0001 (decision 5). **Still open:** `Makefile`'s `secrets` filter is still `^(uv\.lock|\.secrets\.baseline|planning/.*|docs/runs/.*)$$`. The human's change 3 is due before plan step 5. Without it, v1.1's first agent run on factory-rf turns `make check` red, as the `before` case of the demo shows. The optional `CLAUDE.md` wording ("but the factory's cost records") is not made either.
6. The runtime's init reaps the orphans (`init: true`), rather than the factory reaping, tini in the image, or `timeout --foreground` (decision 6).
7. No test in `make test` of the reaping itself. It is a morning observation under Docker Desktop and Podman (decisions 7 and 11 (3)).
8. Finding 3 is documentation only, with no rule in the shipped agents (decision 9).
9. Three stories, one per finding, and S0003 on its own (decision 10).
10. v1's own compose file gets no `init: true` from this feature. That is the human's own choice (decision 11 (5)).
11. The S0002 documenter's own wording of the reason against `timeout --foreground` (`docs/decisions.md:503`). It agrees with decision 6 in substance.

## 7 The slow checks

None beyond `make check` and `make mutants`. The project has no image scan and no SBOM target. `make check` was green as I found it (`check: green`, coverage 99.47 %). Whether the container's init really reaps can only be checked at the shakedown, under Docker Desktop and under Podman, with the operator guide's `ps -eo pid,ppid,user,stat,args` right after `up -d` and after a `time_limit`.

## 8 Cost

18 runs, 8.6 min, $2.50 for three stories, each 6 runs with no rework round and no stall:
- S0001: 6 runs, 3.6 min, $1.24.
- S0002: 6 runs, 3.0 min, $0.71.
- S0003: 6 runs, 2.0 min, $0.55.

S0001 cost the most, about half the total. Its log shows why: its tester wrote nine-row table tests that run the real template `make`, and its demo ran the whole template test module. It also read the most (150k tokens in, against 83k and 66k). Nothing in the log points to waste. S0003, which was documentation only, still paid one short run per stage, as decision 10 accepted.

## Proposed stories

- `drafts/F0015-S0004-the-guides-say-agents-never-commit.md`: a documentation repair. It removes the three stale passages about an agent's commit, which contradict the decision log and S0003's new text, and gives the decision log FEATURE decision 6's lasting reason against the factory as the reaper (the race with `run_process`'s waits).

## Log (append only)

1. acceptor: accepted with drafts; 1 draft proposed; make mutants 0/0 (no module under src/factory changed by F0015)
   1. Scope: none. Each of the three findings has its story, and the code matches each Interface (`template/Makefile:66` is the same as the demo's line; `init: true` and the `exec` handover are pinned). The human's changes 1 and 2 are in, and nothing out of scope was built.
   2. Feature demo: green. In `/tmp/f0015-demo/demo.sh`, the template and demo projects stay green with the real detect-secrets when the running run's record comes from the factory's own writer, untracked or modified. The old line is red on the same file, and an id in a code file is still found. The compose file has `init: True`. The guides cover all three findings and `documents ok` prints. A side observation: on a branch whose `HEAD` equals `origin/main`, the template's `secrets` scans only the tracked files. This predates F0015 and never happens to a work item. No draft.
   3. Mutants: `mutants: no module under src/factory changed by F0015`, 0/0, as FEATURE foresaw.
   4. Noticed: the seal tests (`tests/adapters/test_git_cli_seal.py`) leave unremovable `.git` folders in pytest's base folder. That gives 15 rm_rf warnings per run, with 5.4 GB under `/tmp/pytest-of-factory`. Fixing it would change an earlier story's test, so it is listed for the human with no draft. S0002's documenter note on `timeout --foreground` is consistent with FEATURE.
   5. Documentation: two findings. First, three passages still describe an agent's commit (`docs/operator-guide.md:502`, `docs/project-guide.md:1495`, `docs/project-guide.md:1564`), which contradicts S0003's new text and the decision log; FEATURE had put this out of scope. Second, `docs/decisions.md:503` leaves out decision 6's reason against the factory as the reaper (the race with `run_process`'s waits). Draft S0004 fixes both.
   6. Decisions: 11 listed. Still open: the human's change 3 (factory-rf's own `Makefile` `secrets` filter) is not made and is due before the handover.
   7. Slow checks: none beyond make check and make mutants. `make check` was green as I found it (coverage 99.47 %). The real reaping can only be seen at the shakedown.
   8. Cost: 18 runs, 8.6 min, $2.50, with no rework and no stall. S0001 is about half ($1.24) because of its table tests that run the real template make. There is no sign of waste.
2. done (pull request merged); cost: 1 runs, 7.6 min, 35 turns, 98k tokens in (1979k more from cache), 27k out, $1.71
