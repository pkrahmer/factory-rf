---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 554
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T23:57:39.580609Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-05T00:03:00.804196Z'
  stage: acceptance
  run: 615004053aca43e29fba6f74877f2ea8
stories: [F0050-S0001, F0050-S0002, F0050-S0003, F0050-S0004, F0050-S0005, F0050-S0006, F0050-S0007, F0050-S0008, F0050-S0009, F0050-S0010, F0050-S0011, F0050-S0012, F0050-S0013, F0050-S0014]
outcome: null
---

# Acceptance of The factory shows what it runs and what it uses

## Recommendation

**accepted.** Every scope item is built, and so are the two stories from A0002. `make check` is green. The feature's walk-through is green end to end. A server that refuses a push with two `remote:` lines now keeps both of them in the retry reason (S0013), and the decision log no longer contradicts itself about tool times (S0014). The one new finding is minor. An example in the operator guide shows git's human-readable ref line, which the factory's `--porcelain` push never writes. One docs story is proposed for it (S0015). No promise is broken.

## 1 Scope

A0001 checked S0001 to S0008 against every scope item, and A0002 checked S0009 to S0012. I did not repeat those readings. This acceptance checks the two stories from A0002 and the whole against the Goal.

- **S0013, git's summary line.** `push_reason` (`src/factory/domain/git.py:157-181`) leaves out a stripped line that starts with `PUSH_SUMMARY_PREFIX` (`error: failed to push some refs to `). It does this in the same `startswith` tuple as `hint:` and `To `. Any other `error:` line is kept, and so is `remote: error: failed to push ...`. The three-line and 300-character limits are unchanged. The walk-through shows both server lines (see 2).
- **S0014, the decision log.** The F0012 entry now has the line `- Superseded by *The cost record sums up the run's tool calls, without their content*` (`docs/decisions.md:410`). The S0006 entry's Decision ends with `This supersedes *The time per tool command inside a run is not recorded*.` (`:1542`).
- **The Goal as a whole.** The image is built for one runtime. The pins are current. Every completed record carries `machine`, `tools` and, when the folder is set, `transcript`. A stop says why and is logged once. There is one fetch per iteration. Refused pushes and hosting calls are retried and logged with the server's words. A hosting failure after the claim charges no crash. Out of scope is respected: there is no retention code, no cloud resource, no transcript on GitHub, no limit on the new measures, and the cap of three stays.

Finding: none.

## 2 The feature's smoke test

This is the walk-through of A0002, run unchanged on today's code except for one line: the remote's `pre-receive` hook now writes two server lines, `Internal Server Error` and `request id 1234`, on the second and third push. That is the case S0013 fixed. Part (a) is one stage of a story with:
- a Claude Code 2.1.318-shaped transcript with `api-request-blob` replays;
- a real `CgroupMachineReadings` and a real `FileTranscriptStore`;
- two refused pushes;
- the contract schema check;
- one stop raised three times;
- the hosting retry.

Part (b) is three ticks with a hosting failure right after the claim, then one tick without it.

Command (run from the checkout's root). The module is taken from A0002's report, `done/F0050-A0002-acceptance.md`, section 2, and only the hook line is changed:

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
python3 - "$d" <<'PY'
import re, sys, pathlib
src = pathlib.Path("factory/features/F0050-the-factory-shows-what-it-runs-and-what-it-uses/done/F0050-A0002-acceptance.md").read_text()
code = re.search(r"The module:\n\n```python\n(.*?)```", src, re.S).group(1)
code = code.replace("""'if [ "$n" -eq 1 ] || [ "$n" -eq 2 ]; then echo "Internal Server Error" >&2; exit 1; fi\\n'""",
                    """'if [ "$n" -eq 1 ] || [ "$n" -eq 2 ]; then echo "Internal Server Error" >&2; echo "request id 1234" >&2; exit 1; fi\\n'""")
assert "request id 1234" in code
pathlib.Path(sys.argv[1], "test_feature_walk.py").write_text(code)
PY
PYTHONPATH=tests uv run pytest -p conftest -s -q "$d/test_feature_walk.py" --rootdir "$PWD" -c pyproject.toml -p no:cacheprovider 2>&1 | grep -v '^Bytecode'
```

What it printed:

```
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
2026-10-12T12:00:00Z push: retry 1 of 3 in 5 s: remote: Internal Server Error | remote: request id 1234 | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)
2026-10-12T12:00:05Z push: retry 2 of 3 in 15 s: remote: Internal Server Error | remote: request id 1234 | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)

stage: next doing | stall None
log: push: retry 1 of 3 in 5 s: remote: Internal Server Error | remote: request id 1234 | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)
log: push: retry 2 of 3 in 15 s: remote: Internal Server Error | remote: request id 1234 | ! refs/heads/work-item/F0001-S0001:refs/heads/work-item/F0001-S0001 [remote rejected] (pre-receive hook declined)
waits: [5.0, 15.0]
machine: {'base_image_bytes': 580000000, 'project_layer_bytes': 0, 'store_free_bytes': None, 'dataset_free_bytes': None, 'memory_peak_since_boot_bytes': 8100000000, 'memory_total_bytes': 16000000000, 'cpu_seconds': 12.0, 'cpu_wait_seconds': 2.0, 'memory_wait_seconds': 0.0}
tools: [{'tool': 'Bash', 'calls': 1, 'failed': 1, 'seconds': 2.0}, {'tool': 'Read', 'calls': 1, 'failed': 0, 'seconds': 0.5}]
transcript: {'path': 'F0001-S0001/49aa2c73c63146c483f2ccf966e8b328.jsonl.gz', 'sha256': '10562e3e5303c27004cf52fb6d7f93668de6c7469f776e6f2cbaca90bab064b3'}
file mode 0o600 | sha256 matches True | lines 7
SECRET in pushed records: False
records valid against contract 4.4
2026-10-12T12:00:20Z stop repository fetch_failed: fatal: unable to access
stop lines after three raises: 1
hosting retry: total 5 backoff 2 PATCH True
.2026-10-12T12:00:00Z handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injected failure

outage tick 1: claim None | crashes 0 | agent runs 0
2026-10-12T12:00:00Z handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injected failure

outage tick 2: claim None | crashes 0 | agent runs 0
2026-10-12T12:00:00Z handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injected failure

outage tick 3: claim None | crashes 0 | agent runs 0
log: handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injecte
log: handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injecte
log: handler error run:F0001-S0001 1 of 3: HostingServiceError: hosting service create_pull_request failed: injecte
2026-10-12T12:00:00Z stage environment: reset 0.0 s, sync 0.0 s, advance 0.0 s, take 0.0 s
after the outage: crashes 0 | crash entries 0 | agent runs 1 | stage tests
.
```

**Green.**
- **Part (a).** The stage finished after two retries, with waits of 5 s and 15 s. Each retry reason now holds both of the server's lines and the ref line, and git's `error: failed to push some refs to '<url>'` line is gone. In A0002 that line pushed the first server line out (S0013).
- **The record.** It has all nine machine measures. The tool times survive the replayed lines. The transcript is a `0600` gzip file whose SHA-256 matches the record, and no content reached the pushed records. The records are valid against contract 4.4.
- **The stop.** It was raised three times and logged once.
- **Part (b).** Three failing ticks leave no claim and charge no crash, and each logs `1 of 3`. The fourth tick runs the agent.
- **Not shown here.** The two free-space values are `None` only because the fixture's `FakeDiskSpace` does not know the path. The image build and `vm/setup.sh` were not run, because podman is not in this container (as in A0001 and A0002).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

New from S0013 and S0014:

- **S0013.** The coders and the documenter noticed nothing outside the story. The reviewer's one finding was a copied `result_case` fixture. The tester moved it to `tests/conftest.py:571-592` under the standing leave. The documenter checked the operator-guide example at about line 2487 and found it "still true", because it holds no summary line. However, that example shows git's human-readable ref line (`! [remote rejected] <from> -> <to> (...)`), which the factory never gets from `git push --porcelain` (see 5, proposed story S0015).
- **S0014.** The coder and the documenter both noticed that the log marks supersession in two forms: a plain `Superseded by *...*` sentence (`docs/decisions.md:17`, `:397`, `:874`) and a `- Superseded ...` bullet. The story followed the bullet form. This is a matter of style with no contradiction, so no story is proposed.

Still open from A0001 and A0002, as far as this repository shows:
- the three vulture false positives on `MachineMeasures` (see 7);
- the test-helper copies that a later story can move under the standing leave;
- the `.job-start-probe` name shared by two jobs on one bucket;
- the `0700` mode of the store's subfolders, which no Interface states;
- the release commit that stays unpushed in the local checkout when the release push fails (harmless).

## 5 The documentation as a whole

- **An example that does not match the factory's output.** The handler-error example at `docs/operator-guide.md:2487` reads `... failed: rejected: remote: Internal Server Error | ! [remote rejected] work-item/F0001-S0001 -> work-item/F0001-S0001 (Internal Server Error)`. S0008 wrote that line. The factory pushes with `--porcelain` (`src/factory/adapters/git_cli.py:294`), so its reason holds `! refs/heads/<b>:refs/heads/<b> [remote rejected] (<reason>)`, as the walk-through prints. I ran `push_reason` by hand on a porcelain refusal, and it gives that form. An operator who searches the log for the example's `-> work-item/` finds nothing. Likewise, `:2498` names the refusal as "git's `! [remote rejected]`", a string that never occurs in the factory's reasons. The project guide (`docs/project-guide/git-and-hosting.md:142`) and the code (`SERVER_REFUSAL = "[remote rejected]"`) are right. This is a small repair, and the guide's rule itself is true (proposed story S0015).
- **S0013's text** (`docs/operator-guide.md:2502`, `docs/project-guide/git-and-hosting.md:142`) matches the code and the walk-through. The sentence "so the server's own `remote:` lines stay in", which A0002 found untrue with two lines, is now true.
- **S0014's lines** are in place (`docs/decisions.md:410`, `:1542`). The log no longer contradicts itself about tool times.
- `README.md` needs nothing for this feature. `make documents` says `documents ok`. Every other text I read agrees with the code.

## 6 Decisions taken for the human

From `feature.md`, to accept or revisit: decisions 1 to 12. A0001 and A0002 already list them and the journal defaults of S0001 to S0012.

From the journals of S0013 and S0014:

1. S0013: the summary line is matched by a prefix on the full phrase, on the stripped line (the coder's choice). Two alternatives were rejected: dropping every `error:` line, which would lose causes such as `error: src refspec main does not match any`, and a regular expression that also matches the URL.
2. S0014: the `This supersedes ...` sentence sits inside the S0006 entry's Decision bullet, because the entry has no other place "after the Decision" (the documenter's choice). The story ran through the coder and the reviewer with an empty diff, as the docs-only S0012 did.

Still open for the human from A0002, as far as this repository shows:
- the coder's and the tester's write paths, which do not include their own work item's Description (`factory/pipeline.yml`, the human's);
- the two branch commits per tick that a long hosting outage after the claim adds (S0010 journal 9, noted for later planning);
- a second run of `vm/setup.sh` on factory-vm for `FACTORY_TRANSCRIPT_DIR`;
- a refresh of `security/duplicates-baseline.txt`.

Earlier tests changed in S0013 and S0014, each with the leave the reviewers name:

- S0013: `tests/application/test_push_retry_reason.py`. Its copy of the `result_case` fixture and the imports only that copy used were removed, and the fixture moved to `tests/conftest.py`. This was under the standing leave to move a shared test helper (tester journal 13, reviewer journal 17). Its one test keeps its name and checks the same thing. `tests/conftest.py` only gained the fixture.
- S0014: none.

No earlier test was changed without a named leave.

## 7 The slow checks

The project offers nothing beyond `make check` but the records `make duplicates` and `make documents`. Both ran today.
- `make documents`: `documents ok`.
- `make duplicates`: `4 new, 41 known, 2 gone`, and it exits 1. These are the same four findings as in every story since S0002: three vulture false positives on `MachineMeasures` fields (`src/factory/domain/cost_records.py:45-47`) and the `version_launch` similarity between the two runtimes. The baseline is the human's.

`make test`: 9162 tests (nine more than A0002 counted), 957.9 s of test time on every core, `test: green (118.1 s)` wall, coverage 99.26 %. The slowest tests take about 10 s each. They are the tests that wait out `ROOMY_LIMIT`:
- `tests/adapters/test_podman_timeout_status.py` (both rows);
- `test_opencode_budget`;
- `test_claude_runtime_resume` (three tests);
- `test_opencode_events`;
- `test_opencode_resume_session`.

S0013's new tests take 0.45 s at most (the end-to-end retry test), the rest 0.0 s.

Disk: at acceptance `/srv/factory/vm` has 1.3 GB used, and 0.0 GB under state and `/tmp`, the same as at `disk start`. Free space fell from 27.7 GB to 27.6 GB on all three paths, which appear to share one filesystem. That 0.1 GB is not under any measured path. It may be rounding or something else on that filesystem, and nothing in the feature's last two stories, which changed one function, tests and two documents, explains it. It is too small to act on.

## 8 Cost

The stories cost 204 runs, 337.2 min, 1890 turns and $72.54, which is about $5.18 a story. The two stories since A0002 added 16 runs, 12.3 min and $2.63:
- S0013: 10 runs, 8.5 min, $1.83. It had one review round for the copied fixture.
- S0014: 6 runs, 3.8 min, $0.80.

The heavy stories are still the early ones, as in A0002:
- S0002: $11.83, 52.4 min, five answers and the crash cap.
- S0005: $9.77, four answers.
- S0004: 45.4 min for a small change, four answers.

Human interventions: 28 questions answered (25 questions, 2 at the round cap, 1 at the crash cap), and 3.4 h of waiting. These are the same totals as at A0002: S0013 and S0014 needed no answer. S0002 needed the human most: five answers and the crash cap, for its seams and its contract pins (feature decisions 7 and 8).

## Proposed stories

- `backlog/F0050-S0015-the-operator-guides-push-error-example-shows-the-porcelain-ref-line.md`. The operator guide's handler-error example and its "git's `! [remote rejected]`" show git's human-readable ref line. The factory's `--porcelain` push gives `! refs/heads/<b>:refs/heads/<b> [remote rejected] (...)` (sections 4 and 5).

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 1 story proposed (F0050-S0015). `make check` is green, the feature's walk-through is green end to end, and no promise is broken. A0002's two findings are closed (S0013, S0014). The one new finding is a small docs repair.
   1 Scope: every scope item is built, and so are the two stories from A0002. S0013 drops git's `error: failed to push some refs to` line from the push reason. S0014 marks the F0012 tool-time entry superseded. Nothing is outside the scope or against Out of scope.
   2 Smoke test: green. I reran A0002's walk-through with a hook that writes two server lines. Both now stay in every retry reason, and the summary line is gone. The nine machine measures, the timed tools, the 0600 transcript with a matching SHA-256, contract 4.4, the stop logged once and the hosting retry all hold. Three hosting failures after the claim charge no crash, and the next tick runs the agent.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: S0013 moved a copied `result_case` fixture to `tests/conftest.py` under the standing leave. S0014's coder and documenter saw two supersession forms in the log (style only, no story). The items open since A0001 and A0002 carry on (vulture false positives, helper copies, `.job-start-probe`, subfolder mode 0700, a local unpushed release commit).
   5 Documentation: the handler-error example at `docs/operator-guide.md:2487` shows git's human-readable ref line, `! [remote rejected] <b> -> <b> (...)`, and `:2498` names "git's `! [remote rejected]`". The factory's `--porcelain` push gives `! refs/heads/<b>:refs/heads/<b> [remote rejected] (...)` (S0015). S0013's and S0014's texts match the code.
   6 Decisions: feature decisions 1 to 12 and the journal defaults are listed in the report. In S0013 the coder chose a prefix match on the stripped line. In S0014 the documenter put the sentence inside the Decision bullet. Still open for the human: the write paths in `factory/pipeline.yml`, two branch commits per outage tick, a second run of `vm/setup.sh`, the duplicates baseline. The one earlier test changed (`tests/application/test_push_retry_reason.py`) was changed under the standing leave.
   7 Slow checks: `make documents` is ok. `make duplicates` gives `4 new, 41 known, 2 gone` (the same four since S0002). The slowest tests are about 10 s each, the `ROOMY_LIMIT` waits. Used disk is unchanged at 1.3 GB, but free space fell by 0.1 GB on the shared filesystem outside the measured paths. That may be rounding, the feature's changes do not explain it, and it is too small to act on.
   8 Cost: 204 runs, 337.2 min, $72.54 in total. S0013 and S0014 cost $2.63 together and needed no answer. The total is 28 questions answered (25 questions, 2 at the round cap, 1 at the crash cap) and 3.4 h waited. S0002 is still the most expensive story and the one that needed the human most.
