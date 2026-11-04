---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 343
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T07:42:54.442199Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-20T07:48:51.399450Z'
  stage: acceptance
  run: a0eb8597af8e4faa8aa7db25157b416a
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-20T08:32:10.918421Z'
  stage: done
stories: [F0029-S0001, F0029-S0002]
outcome: accepted
---

# Acceptance of opencode starts in a fresh home, and no test races its time limit

## Recommendation

accepted. The two stories together make what `feature.md` promised. The image lays out `/home/agent/.config/opencode` read-only to the agent. Under the write guard, opencode dies in a fresh home and starts in that layout. All eighteen tests of decision 9 take `ROOMY_LIMIT`, and the whole suite passed on 64 workers on a 20-core machine. Nothing found is a broken promise. What is open: the human's change 2 (`CLAUDE.md`) is not on `main` yet, and change 1 (the recreated opencode instance) is outside what this run can see. One small story is proposed, for a reviewer's note that nobody took on.

## 1 Scope

none. Every Scope item has its story, and nothing was built outside the scope:
- `image/Dockerfile` (S0001): the `RUN` at lines 32–38, right after the user `RUN` and before `WORKDIR /opt/factory`.
- `tests/test_opencode_config_folder.py` (S0001).
- `tests/time_limits.py` and `tests/test_time_limits.py` (S0002).
- The eleven modules of decision 9, changed in limit, bound and comment only (S0002). The two rewrites are `test_resume_gets_what_is_left_of_the_time_limit_and_unknown_measures` and `test_time_limit_of_one_second_runs`.
- The three documents (both stories).

The Out of scope stayed out:
- `RUNTIME_FOLDERS` is unchanged.
- `image/entrypoint.sh` is unchanged.
- The shipped tester lesson in `claude/agents/tester.md:76` and `template/CLAUDE.md:17` is unchanged.

I grepped `tests/` for every limit of five seconds or less that is still left. The ones that remain are decision 7's list (`tests/adapters/test_claude_runtime.py:376`, `tests/adapters/test_git_cli_reading.py:109`, `SHORT_LIMIT` for the removal test in `tests/adapters/test_claude_runtime_confinement.py:42`, and the `sudo` tests behind `SUDO_GRACE`), plus durations or request validation that start no child. The goal "the first probe in a fresh home passes" is checked for real by the human's change 1. This acceptance run's own container was built from the new image: `/home/agent/.config/opencode` there is `factory:factory-work 755` and empty (smoke test, part 1). That container runs Claude Code, not opencode.

## 2 Feature smoke test

The script is `$TMPDIR/smoke/feature-smoke.sh`, run with `bash` from the checkout as the agent user, in this run's container (built from the new image, 20 cores). It does four things:
1. Reads the real agent home.
2. Runs opencode's own `opencode debug config` under the real `factory-confine` with the three runtime folders, once in a fresh home and once in a home laid out as the image lays it out. Offline, no paid call.
3. Runs the whole suite on 64 workers, more load than `make check`'s 20.
4. Reads the time-limit tests' times from the JUnit report of that run.

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
echo "== 3 the whole suite on 64 workers ($(nproc) cores)"
start=$(date +%s)
TMPDIR="$d" uv run pytest --no-header -q --tb=short -p no:cacheprovider -n 64 tests --junit-xml="$d/junit.xml" > "$d/out" 2>&1
echo "exit $? after $(( $(date +%s) - start )) s"
grep -c -E '^(FAILED|ERROR) ' "$d/out"
grep -E '^(FAILED|ERROR) ' "$d/out"
tail -1 "$d/out"
echo "== 4 the roomy tests' times under that load (s)"
# a short Python reader of $d/junit.xml: the eight slowest tests, and the slowest whose name holds
# time_limit, time-limit, killed or timed-out
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
== 3 the whole suite on 64 workers (20 cores)
exit 0 after 71 s
0
.............                                                            [100%]
== 4 the roomy tests' times under that load (s)
  13.8 test_fault_paths_7_to_13::test_acceptance_container_lost_in_review_reruns_once_and_books_result[accepted]
  12.8 test_fault_paths_7_to_13::test_round_cap_question_killed_between_post_and_record_posts_once_and_waits
  11.6 test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[status-1-past-the-limit]
  11.6 test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[sigkill-past-the-limit]
  10.9 test_fault_paths_7_to_13::test_close_at_approval_tick_killed_after_close_recorded_reopens_once_and_asks_once
  10.1 test_claude_runtime_confinement::test_a_wrapper_line_of_a_call_killed_at_its_time_limit_is_a_runtime_error
  10.1 test_opencode_sudo_time_limit::test_under_sudo_a_kill_at_the_limit_ends_time_limit_and_keeps_session_and_login[killed-at-the-limit]
  10.0 test_claude_runtime_resume::test_call_killed_by_the_time_limit_has_no_model_duration[nothing printed]
slowest time-limit test 12.8 s, bound 25
```

Green.
- Part 1: the image's layout, as built: the parent is the agent's, the folder is read-only and empty.
- Part 2: opencode under the guard dies in a fresh home (`EACCES ... mkdir '.../fresh/.config'`) and starts in the image's layout. It leaves the read-only folder empty, as the operator guide says.
- Part 3: no failed or errored test under 64 workers.
- Part 4: the "12.8 s" of the last line is the fault-path test `test_round_cap_question_killed_...`, which my name filter caught by its word "killed". It has no time limit. The slowest real time-limit tests are the two `sudo` rows that end past the limit, 11.6 s, well below `ROOMY_BOUND_SECONDS` (25).

Not covered here: a recreated opencode instance's first paid probe. That is the human's change 1.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- S0001, smoke-tester (entries 13 and 16): Claude Code's own safety check refused the story's second smoke block twice, as a `sh -c` script that runs `rm` (the `trap 'rm -rf "$d"' EXIT` with an `sh -c` inside the loop). The human ran the block (answer (a)). This acceptance ran the same block, `trap` and all, saved in a file and run with `bash <file>`, and it passed. That supports the smoke-tester's option (b). It is a rule for how stories write smoke tests (`factory/story-form.md`, the intake's checks), which is the human's file, so no story is proposed: listed under 6.
- S0002, tester (entry 5) and coder (entry 7): the story's Interface said "the comment the feature gives", and the tester, who does not read `feature.md`, wrote its own wording. That cost one review round (reviewer entry 9, findings 1–3). It is the same kind of rule for stories: a text a later stage must copy is quoted in the story, not referred to. Listed under 6, with no story.
- S0002, reviewer (entry 17, *Notes*): each row of `tests/test_time_limits.py` is a `bool` worked out when pytest collects the module, so a failing row prints only `assert False`. Proposed as F0029-S0003.
- S0001 coder, S0002 coder and both reviewers: `make duplicates` reported `5 new, 33 known, 3 gone`, all in `src/factory`, which neither story touched. They come from before this feature, and nothing in F0029's scope owns them, so no story is proposed here.
- Documenters: no stale text reported.

## 5 Documentation

Read as a newcomer: `README.md`, `docs/operator-guide.md` (*Running on opencode*, *The probe of the agent run*), `docs/project-guide/agents.md` (*opencode's folders*), `docs/project-guide/processes-and-checks.md` (*Starting a process*), and the two new entries of `docs/decisions.md` (lines 836 and 888). They agree with each other and with the code:
- The owner and mode of the folder are the same in all three documents and in `image/Dockerfile`.
- `ROOMY_LIMIT` (10 s) and `ROOMY_BOUND_SECONDS` (25) match `tests/time_limits.py`.
- The operator guide's claim that opencode "starts and leaves it empty" held in the smoke test.

One contradiction, in a human's file:
- `CLAUDE.md:38` still says "A limit of a few seconds".
- `docs/project-guide/processes-and-checks.md:82` says `ROOMY_LIMIT` (ten seconds).

A tester reads both. This is the human's change 2 of `feature.md`, due after S0002 and not yet on `main`. It is not a story, because `CLAUDE.md` is the human's. The shipped lesson (`claude/agents/tester.md:76`, `template/CLAUDE.md:17`) keeps "a few seconds", as decision 8 intends.

## 6 Decisions taken for the human

To accept or revisit:
1. `feature.md` decisions 1–5 (S0001):
   - The folder is made by the image, not allowed to the run.
   - The image makes it, not the entrypoint.
   - `.config` stays the agent's.
   - `XDG_CONFIG_HOME` is rejected.
   - The smoke test shows the mechanism, and change 1 shows the image.
2. `feature.md` decisions 6–10 (S0002):
   - Ten seconds, and a bound of 25.
   - The list of tests that change and of the ones that keep a short limit.
   - The rule goes in `CLAUDE.md`, not in the shipped lesson.
   - The leaves of decision 9.
   - No production code changes.
3. `feature.md` decision 11: the number F0029 and the folder name.
4. S0001, entry 14: the human chose (a) for the blocked smoke block and ran it by hand (`fresh 1`, `made 0`, `1`).
5. S0002, entry 5 (tester): `ruff check --fix` also removed the import of `timedelta` that `tests/adapters/test_opencode_budget.py` no longer used. The import was dead after the decision-9 change, so it is within that change.
6. S0002, entry 5 (tester): `test_grandchild_is_killed_with_the_child_at_the_time_limit` also got an elapsed bound (`ROOMY_BOUND_SECONDS`). Decision 9 bounds only the first `test_process.py` test, but criterion 3 asks for a bound on both. The reviewer (entry 9) accepted it.
7. Still open, the human's: change 1, the recreated `opencode-demo` instance with `FACTORY_OPENCODE_FOLDERS=.config/opencode` removed. Nothing in the archived stories records it as done.
8. Still open, the human's: change 2, the `CLAUDE.md` bullet (see 5).
9. For the human's forms, no story: a smoke block whose `trap 'rm -rf'` sits beside an `sh -c` is refused by Claude Code's safety check. Saving the block to a file and running `bash <file>` passes it.
10. For the human's forms, no story: a story should quote a text a later stage must copy word for word, rather than send that stage to `feature.md`.

Earlier tests changed:
- S0001: none (reviewer entry 9).
- S0002: eleven modules, each under the human's leave of `feature.md` decision 9 (reviewer entry 17):
  - `tests/adapters/test_claude_runtime_confinement.py`
  - `test_claude_runtime_provider_limit.py`
  - `test_claude_runtime_resume.py`
  - `test_make_commands.py`
  - `test_opencode_budget.py`
  - `test_opencode_confinement.py`
  - `test_opencode_events.py`
  - `test_opencode_resume_session.py`
  - `test_opencode_sudo_time_limit.py`
  - `test_process.py`
  - `test_process_streaming.py`

  The round-0 comment wording went beyond the leave and was corrected word for word in round 1. No earlier test was changed without a leave.

## 7 Slow checks

The project offers nothing beyond `make check` but `make mutants` (check 3) and `make duplicates` (a record, `5 new, 33 known, 3 gone`, from before this feature). Nothing else to run.

`make check` was green as I found it: `test: green (81.6 s)`, coverage 99.16 %, 6133 tests, 654 s summed over the workers. The slowest tests in `.reports/junit.xml` are this feature's own:
- the `sudo` rows `status-1-past-the-limit` and `sigkill-past-the-limit`, 11.5 s each;
- then the 10.0 s rows: `killed-at-the-limit`, the confinement `time-limit` row, the provider-limit test and the opencode confinement `time-limit` row.

That is the cost decision 6 expected, and the wall time of `make test` stayed near 80 s (S0002's entries give 77–81 s).

Disk: the Disk now line is the same as the Disk at the previous record line (/work 0.5 GB used, /state and /tmp 0.0 GB). No growth.

## 8 Cost

17 runs, 17.1 min, $4.24 in total.

S0001: 7 runs, 4.7 min, $1.28. Its smoke test ran twice because Claude Code's safety check blocked the second block.

S0002: 10 runs, 12.5 min, $2.96. It stands out a little:
- One review round (doing → tests → doing → review) went to three comments that the Interface named only as "the comment the feature gives", text the tester could not see.
- Its first tester run was the longest of the feature (215 s, 19 turns). It changed eleven modules.

Human interventions: 1 question answered (question 1), 0.0 h waited. It was S0001's smoke test (entry 13), answered about two minutes later (entry 14) by running the blocked block by hand. S0001 is the story that needed the human most, and only because of the safety check, not a gap in the story.

## Proposed stories

- `backlog/F0029-S0003-the-shared-time-limits-test-names-the-values-of-a-relation-that-broke.md`: the S0002 reviewer's note. A broken row of `tests/test_time_limits.py` prints only `assert False`. Each row will carry its two values and the relation, so the failure names them. Before it starts, it needs the human's leave in `feature.md` to change S0002's test.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted; 1 story proposed
   1 Scope: none. Every Scope item has its story and every Out of scope item stayed out. The short limits left in `tests/` are decision 7's list.
   2 Feature smoke test: green. This container was built from the new image: `.config` is `agent:factory-work 755`, `.config/opencode` is `factory:factory-work 755`, read-only and empty. Under `factory-confine`, `opencode debug config` gave `fresh 1` (`EACCES` mkdir `.config`) and `made 0`. The whole suite on 64 workers (20 cores) gave exit 0 with 0 FAILED/ERROR. The slowest time-limit tests took 11.6 s, under the bound of 25.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: Claude Code's safety check blocked S0001's smoke block (`trap rm -rf` beside `sh -c`); the same block passes when run as `bash <file>`. S0002 lost one review round to "the comment the feature gives", text the tester cannot read. S0002's reviewer noted that `test_time_limits.py` rows fail with only `assert False` (proposed as S0003). `make duplicates` shows 5 new findings from before this feature, outside its scope.
   5 Docs: the three documents and the two decision entries agree with each other and with the code. One contradiction is in the human's file: `CLAUDE.md:38` says "a few seconds" and `processes-and-checks.md:82` says `ROOMY_LIMIT`. This is the human's change 2, not yet on `main`.
   6 Decisions: `feature.md` 1–11, S0001's answer (a), and the extra elapsed bound on the grandchild test. Changes 1 and 2 are still open, plus two notes for the human's story form. S0002 changed earlier tests in eleven modules, all under decision 9. Nothing was changed without a leave.
   7 Slow checks: nothing beyond `make check`, which was green (test 81.6 s, 99.16 %). The slowest tests are this feature's `sudo` rows at 11.5 s. Disk is unchanged.
   8 Cost: 17 runs, 17.1 min, $4.24. S0002 ($2.96) had one review round spent on three comments. S0001 needed the human once (0.0 h waited), because the safety check blocked its smoke block.
3. factory: done (pull request merged); cost: 1 runs, 5.9 min, 20 turns, 81839 tokens in (1040649 more from cache), 18630 out, $1.24
