---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 368
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T22:55:39.391547Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T23:02:34.268125Z'
  stage: acceptance
  run: 1aa79e8273a24204b82152a8c7f56cd0
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-20T23:03:53.914741Z'
  stage: done
stories: [F0029-S0001, F0029-S0002, F0029-S0003]
outcome: accepted
---

# Acceptance of opencode starts in a fresh home, and no test races its time limit

## Recommendation

accepted. The three stories together make what `feature.md` promised:
- The image makes `/home/agent/.config/opencode` read-only to the agent. opencode under the write guard dies in a fresh home and starts in the image's layout.
- The human's change 1 confirmed this on a recreated `opencode-demo` (night log, 08:52).
- Every test of decision 9 takes `ROOMY_LIMIT`. The whole suite passed on 64 workers on 20 cores.
- A broken relation of the shared limits now names its values (S0003).

No finding of weight and no story proposed. The one open item is the human's change 2: `CLAUDE.md:40` still gives testers "a limit of a few seconds".

## 1 Scope

none. Every Scope item has its story, and nothing outside the scope was built:
- `image/Dockerfile:32-38`, the one `RUN` right after the user `RUN` (S0001).
- `tests/test_opencode_config_folder.py` (S0001).
- `tests/time_limits.py` and `tests/test_time_limits.py` (S0002). The test's failure message (S0003): each row is `(left, relation, right)`, and a broken one fails with `<left> <relation name> <right>` (`tests/test_time_limits.py:66`). The new `test_a_relation_that_breaks_names_its_values` pins it.
- The eleven earlier modules of decision 9 (S0002), as the previous acceptance (F0029-A0001) checked.
- The documents: `docs/operator-guide.md`, `docs/project-guide/agents.md` and `processes-and-checks.md:125`, and `docs/decisions.md:836,888,896`.

Out of scope stayed out:
- `RUNTIME_FOLDERS` and `image/entrypoint.sh` are unchanged.
- The shipped lesson is unchanged: `claude/agents/tester.md:76` and `template/CLAUDE.md:17` still say "a few seconds".

The branch's diff against `main` is the report alone.

The goal "the first probe in a fresh home passes" was the human's change 1, and it is met. The night log row of 08:52 records it: the rebuilt and recreated `opencode-demo` showed `/home/agent/.config agent:factory-work 755` and `/home/agent/.config/opencode factory:factory-work 755`, and its first preflight's agent-run probe passed. `FACTORY_OPENCODE_FOLDERS` was already empty there. F0029-A0001 listed this change as open; it is closed.

I also read the short limits that later features added to `tests/`:
- `SHORT_LIMIT` of `tests/adapters/test_make_commands_user.py:18` (F0040). The stand-in `sudo` writes its record before it runs the inner `timeout` that the limit is handed to. That is decision 7's `sudo` case, so it is no race.
- `FRESH_HOME_TIME_LIMIT` patched to 3 s in `tests/adapters/test_sudo_agent_home.py:191`. Its program only has to hang, so it is also no race.
- `tests/adapters/test_process_session.py` (F0030) reuses `ROOMY_LIMIT` and `ROOMY_BOUND_SECONDS`, so the shared module serves beyond this feature.

## 2 Feature smoke test

The script was `feature-smoke.sh` in a `mktemp -d` folder, run as `bash <file>` from the checkout as the agent user. This run's container was built from the current image and has 20 cores. The script:
1. reads the real agent home;
2. runs opencode's own `opencode debug config` under the real `factory-confine` with the runtime's three folders, in a fresh home and in a home laid out as the image lays it out (offline, no paid call);
3. lowers a stand-in's wait to the bound, as someone raising the limit or lowering a wait would, and calls the shared relation test with it;
4. runs the whole suite on 64 workers;
5. reads the time-limit tests' times from that run's JUnit report.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
cd /work/checkout || exit 2
echo "== 1 the image's agent home"
stat -c '%n %U:%G %a' /home/agent/.config /home/agent/.config/opencode
if [ -w /home/agent/.config/opencode ]; then echo "config/opencode writable"; else echo "config/opencode read-only"; fi
echo "entries in config/opencode: $(ls -A /home/agent/.config/opencode | wc -l)"
echo "== 2 opencode under factory-confine, fresh home against the image's layout"
mkdir -p "$d/fresh" "$d/made/.config/opencode" "$d/w"
chmod 0555 "$d/made/.config/opencode"
for home in fresh made; do
  printf '{"folders":["%s/w","%s/%s/.local/share/opencode","%s/%s/.local/state/opencode","%s/%s/.cache/opencode"],"files":["/dev/null"],"temporary_directory":"%s/t-%s"}' "$d" "$d" "$home" "$d" "$home" "$d" "$home" "$d" "$home" > "$d/rules-$home.json"
  HOME="$d/$home" XDG_CONFIG_HOME= factory-confine --rules "$d/rules-$home.json" -- sh -c 'cd "$1" && exec opencode debug config' sh "$d/w" >/dev/null 2>"$d/err-$home"
  echo "$home $?"
done
grep -c "EACCES: permission denied, mkdir '$d/fresh/.config'" "$d/err-fresh"
echo "entries in made/.config/opencode: $(ls -A "$d/made/.config/opencode" | wc -l)"
echo "== 3 a broken relation of the shared limits names its values (stand-in wait lowered to the bound)"
uv run -q python - <<'PY'
import operator, sys
sys.path.insert(0, "tests")
from adapters import opencode_stand_in
from time_limits import ROOMY_BOUND_SECONDS
from test_time_limits import test_the_roomy_limit_leaves_room_and_stays_below_every_wait as check
opencode_stand_in.WAIT_SECONDS = ROOMY_BOUND_SECONDS  # as if someone lowered the wait
try:
    check(left=opencode_stand_in.WAIT_SECONDS, relation=operator.gt, right=ROOMY_BOUND_SECONDS)
    print("held")
except AssertionError as error:
    print(str(error).splitlines()[0])
PY
echo "== 4 the whole suite on 64 workers ($(nproc) cores)"
start=$(date +%s)
TMPDIR="$d" uv run pytest --no-header -q --tb=short -p no:cacheprovider -n 64 tests --junit-xml="$d/junit.xml" > "$d/out" 2>&1
echo "exit $? after $(( $(date +%s) - start )) s"
grep -c -E '^(FAILED|ERROR) ' "$d/out"
grep -E '^(FAILED|ERROR) ' "$d/out"
echo "== 5 the roomy tests' times under that load (s)"
# a short Python reader of $d/junit.xml: the six slowest tests of decision 9's eleven modules
# whose name holds limit, killed or timed-out, then the slowest of them and the number of tests
```

Output:

```
== 1 the image's agent home
/home/agent/.config agent:factory-work 755
/home/agent/.config/opencode factory:factory-work 755
config/opencode read-only
entries in config/opencode: 0
== 2 opencode under factory-confine, fresh home against the image's layout
fresh 1
made 0
1
entries in made/.config/opencode: 0
== 3 a broken relation of the shared limits names its values (stand-in wait lowered to the bound)
25 gt 25
== 4 the whole suite on 64 workers (20 cores)
exit 0 after 144 s
0
== 5 the roomy tests' times under that load (s)
   11.5 test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[sigkill-past-the-limit]
   11.5 test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[status-1-past-the-limit]
   10.1 test_opencode_budget::test_a_resume_past_what_is_left_of_the_time_limit_ends_the_run_by_time_limit
   10.1 test_claude_runtime_confinement::test_the_temporary_folder_is_empty_at_each_call_and_gone_after_the_run[time-limit]
   10.1 test_opencode_resume_session::test_a_run_resumes_the_named_session_and_reports_the_first_session_of_its_events[timed-out-with-events]
   10.1 test_claude_runtime_resume::test_first_call_ended_by_the_time_limit_is_not_resumed
slowest roomy test 11.5 s, bound 25; tests 6405
```

Green:
- Part 1: the image's layout is as built. The parent is the agent's; the folder is read-only and empty.
- Part 2: opencode dies in a fresh home (`EACCES ... mkdir '.../fresh/.config'`, exit 1) and starts in the image's layout (exit 0). It leaves the read-only folder empty.
- Part 3: the relation broken on purpose fails with `25 gt 25`, so the values and the relation are named.
- Part 4: no test failed or errored under 64 workers.
- Part 5: the slowest roomy tests take 11.5 s, well below `ROOMY_BOUND_SECONDS` (25).

The run took 144 s, against 71 s in F0029-A0001. In between, 272 tests joined: 6405 now against 6133, among them F0030's `test_process_session.py` rows, which also wait `ROOMY_LIMIT`. That growth explains it.

A recreated opencode instance's paid probe is not covered here; the human's change 1 did that (see 1).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0001, smoke tester (entries 13 and 16): Claude Code's safety check refused a smoke block that holds a `trap 'rm -rf'` beside an `sh -c`. F0029-A0001 found that the same block passes as `bash <file>`, and so does this run's. It is a rule for the human's story form, so no story: listed under 6.
- S0002, tester (entry 5) and reviewer (entry 9): the Interface named "the comment the feature gives", text the tester cannot read, and that cost a review round. Same kind of rule, for the human's form: listed under 6.
- S0002, reviewer (entry 17, *Notes*): the rows of `tests/test_time_limits.py` failed with only `assert False`. F0029-A0001 proposed this, and F0029-S0003 built it; the smoke test above shows the message. Closed.
- S0003: the coder noticed nothing, the documenter found nothing stale, and the reviewer had no remarks.
- `make duplicates` (S0003's coder, and this run): `6 new, 33 known, 3 gone`. F0029-A0001 counted 5 new. All six are in `src/factory`, which no story of this feature changed: S0001 changed `image/` and S0002 and S0003 changed `tests/`. They are:
  - four similar blocks in `claude_runtime.py` and `opencode_runtime.py`;
  - `ManualWaiter` in `adapters/clock.py`;
  - `output_abandoned` in `adapters/process.py`, from the later F0030 or F0040.

  They are not this feature's to own, and the night log already carries them as F0039-S0007's draft. No story.

## 5 Documentation

I read `README.md`, `docs/operator-guide.md` (*Running on opencode*), `docs/project-guide/agents.md` (*opencode's folders*), `docs/project-guide/processes-and-checks.md:125` and `docs/decisions.md:836,888,896` as a newcomer. They agree with each other and with the code:
- The folder's owner and mode match `image/Dockerfile:35-38`.
- `ROOMY_LIMIT` (10 s) and `ROOMY_BOUND_SECONDS` (25) match `tests/time_limits.py:8,11`.
- The operator guide's "starts and leaves it empty" held in the smoke test.
- S0003 changed no document, rightly: nothing documents the test's message.

One contradiction remains, in the human's file, as in F0029-A0001: `CLAUDE.md:40` says "A limit of a few seconds", while `docs/project-guide/processes-and-checks.md:125` and `docs/decisions.md:896` say `ROOMY_LIMIT` (ten seconds). That is the human's change 2 of `feature.md`. It was due after S0002 and is still not on `main`, now that every story is merged. A tester reads `CLAUDE.md` first: F0040's later tests took 3-second limits, which by decision 7 happen to be no race (see 1). The next one may not be so lucky. It is not a story, because `CLAUDE.md` is the human's. `docs/project-guide/agents.md:298` also states the shipped lesson ("a limit of a few seconds"). That describes the shipped `tester.md` correctly, and decision 8 keeps it.

## 6 Decisions taken for the human

To accept or revisit:
1. `feature.md` decisions 1–5 (S0001):
   - the folder is made by the image, not allowed to the run;
   - the image makes it, not the entrypoint;
   - `.config` stays the agent's;
   - `XDG_CONFIG_HOME` is rejected;
   - the smoke test shows the mechanism, and change 1 shows the image.
2. `feature.md` decisions 6–10 (S0002):
   - ten seconds and a bound of 25;
   - which tests change;
   - the rule goes in `CLAUDE.md`, not in the shipped lesson;
   - the leaves of decision 9;
   - no production code.
3. `feature.md` decision 9, S0003: the human's leave of 2026-10-20 to change S0002's `tests/test_time_limits.py`.
4. `feature.md` decision 11: the number and the name.
5. S0001, entry 14: the human chose (a) for the blocked smoke block and ran it by hand.
6. S0002, entry 5: `ruff check --fix` also removed the dead `timedelta` import of `test_opencode_budget.py`. The grandchild test of `test_process.py` got an elapsed bound beyond decision 9's letter, as its criterion 3 asked; the reviewer accepted both.
7. S0003, entries 5 and 9: the `limit` row now reads `ROOMY_LIMIT.total_seconds() eq 10.0` instead of `timedelta(seconds=10) == ROOMY_LIMIT`. It is the same relation, in the Interface's form.
8. Done: the human's change 1, met on 2026-10-20 (night log 08:52, about $0.06).
9. Still open: the human's change 2, the `CLAUDE.md` *Tests* bullet (see 5).
10. For the human's story form, no story: a smoke block with `trap 'rm -rf'` beside `sh -c` is refused by Claude Code's safety check, and `bash <file>` passes it.
11. For the human's story form, no story: a story should quote a text that a later stage must copy word for word, not send that stage to `feature.md`.

Earlier tests changed:
- S0001: none.
- S0002: the eleven modules of decision 9, each under that leave (reviewer entry 17). The round-0 comment wording went beyond the leave and was corrected word for word in round 1.
- S0003: `tests/test_time_limits.py` (F0029-S0002's test), under decision 9, S0003 (reviewer entry 9). It keeps its name, nine ids and relations.

No earlier test was changed without a leave.

## 7 Slow checks

The project offers nothing beyond `make check` but `make mutants` (check 3) and the `make duplicates` record (`6 new, 33 known, 3 gone`, none of them this feature's; see 4).

`make check` was green as I found it: `test: green (61.6 s)` and coverage 99.14 %. `.reports/junit.xml` holds 6405 tests and 729 s summed over the workers. The slowest tests:
- the two `sudo` rows `status-1-past-the-limit` and `sigkill-past-the-limit`, 11.5 s each (this feature's, as decision 6 expected);
- then F0030's `test_process_session.py` rows at 10.1 s, which reuse `ROOMY_LIMIT`;
- then the `killed-at-the-limit` `sudo` row, at 10.0 s.

The wall time of `make test` stayed near 60 s.

Disk: now `/work` 0.0 GB used, against 0.5 GB at the previous record (`disk start`). `/state` and `/tmp` are 0.0 GB at both. The disk shrank, so there is no growth to explain.

## 8 Cost

23 runs, 21.4 min, 138 turns, $5.14 in total:
- S0001: 7 runs, 4.7 min, $1.28. Its smoke test ran twice, because the safety check blocked the second block.
- S0002: 10 runs, 12.5 min, $2.96. It stands out. One review round went to three comments that its Interface only referred to, and its first tester run changed eleven modules (215 s, 19 turns).
- S0003: 6 runs, 4.3 min, $0.91, first pass. The tester's run was the longest (108 s, mostly `make test`), and the coder had nothing to build.

Human interventions: 1 question answered (question 1), 0.0 h waited. It was S0001's smoke test (entry 13), answered at entry 14 by running the blocked block by hand. S0001 needed the human most, because of the safety check, not because of a gap in the story.

## Proposed stories

none. Every noticed item is closed (F0029-S0003), is the human's own (change 2, the two story-form notes), or belongs outside this feature (the `make duplicates` findings).

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 0 stories proposed
   1 Scope: none. Every Scope item has its story. S0003 adds the failure message `<left> <relation name> <right>` to `tests/test_time_limits.py`, and everything listed as out of scope stayed out. The human's change 1 is met: a recreated `opencode-demo` passed its first probe (night log, 08:52). The later short limits in F0040's tests are decision 7's `sudo` case, not a race.
   2 Feature smoke test: green. The image's `.config/opencode` is `factory:factory-work 755`, read-only and empty. Under `factory-confine`, `opencode debug config` gave `fresh 1` (`EACCES` on mkdir `.config`) and `made 0`. A relation broken on purpose printed `25 gt 25`. The whole suite on 64 workers (20 cores) exited 0 with no FAILED or ERROR in 144 s. The slowest time-limit tests took 11.5 s, under the bound of 25.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the reviewer's `assert False` note was fixed by S0003. The two story-form notes (the safety check refusing `trap rm -rf` beside `sh -c`; Interfaces that point to `feature.md` text instead of quoting it) are the human's. `make duplicates` shows 6 new findings, all in `src/`, which this feature did not touch. S0003 noticed nothing.
   5 Docs: they agree with each other and with the code. `CLAUDE.md:40` still says "a few seconds", while `processes-and-checks.md:125` says `ROOMY_LIMIT`. That is the human's change 2, still not on `main`.
   6 Decisions: `feature.md` decisions 1–11, the S0003 leave of 2026-10-20, S0001's answer (a), S0002's extra bound, and S0003's form of the `limit` row. Change 1 is done and change 2 is open. Earlier tests were changed only under decision 9.
   7 Slow checks: there is nothing beyond `make check`, which was green (test 61.6 s, coverage 99.14 %, 6405 tests). The slowest tests are the two `sudo` rows at 11.5 s. Disk used went down (/work 0.5 to 0.0 GB), so there is no growth.
   8 Cost: 23 runs, 21.4 min, $5.14. S0002 ($2.96) stands out, with one review round spent on comments its Interface only referred to. S0003 cost $0.91 and passed first time. The one question (0.0 h waited) was S0001's smoke block, blocked by the safety check.
3. factory: done (pull request merged); cost: 1 runs, 6.8 min, 20 turns, 68036 tokens in (1012131 more from cache), 15405 out, $1.05
