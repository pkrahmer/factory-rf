# Handling of the audit and the pre-check, F0001-boundaries, round 1

Reports: the audit `audits/F0001-1.md` (rows A1 to A34) and the pre-check `precheck/F0001-1.md` (rows P-S0002-1 and so on, named by the old story id and the question's number). The binding answers are in `skeleton-answers.md`, "Answers for F0001's round 1".

## Story numbers after this round

The feature now has fourteen stories (the answers ask for the splits of S0004 and S0008, and the added criteria pushed old S0010 over 26). Old to new:

| Old | New |
|---|---|
| S0001, S0002, S0003 | unchanged |
| S0004 | S0004 (the process wrapper, criteria 1 to 14 of the old story, widened) and S0005 (git errors, fetch and refs) |
| S0005 | S0006 |
| S0006 | S0007 |
| S0007 | S0008 |
| S0008 | S0009 (the call and its result) and S0010 (the budget resume and the version) |
| S0009 | S0011 |
| S0010 | S0012 (branches and merge) and S0013 (reset, revert and move) |
| S0011 | S0014 |

Criterion numbers below are the new numbers. FEATURE.md's Stories list and decisions are updated. Criterion counts now: S0001 17, S0002 18, S0003 23, S0004 16, S0005 24, S0006 25, S0007 25, S0008 26, S0009 21, S0010 18, S0011 23, S0012 18, S0013 13, S0014 20.

## Audit findings

| Finding | Severity | Handling |
|---|---|---|
| A1 | blocker | fixed. S0007 Demo, first block: `lint failed 3 'lint: red'` → `lint failed 2 'lint: red'`, and the Expect line says that make, not the recipe's `exit 3`, sets the status. S0007 rules say that GNU make exits 2 whenever a recipe fails. S0007 c7 gains "a target whose recipe exits with status 3 also gives `exit_status == 2`". FEATURE decision 11 says so. |
| A2 | should fix | fixed. S0014 c17: "Among the classes of `src/factory`, exactly `FakeHostingService` and `PyGithubHostingService` define `post_comment`" → "Among the concrete classes of `src/factory` (those that are not `Protocol` classes, so the `HostingService` protocol of S0002 is left out), exactly `FakeHostingService` and `PyGithubHostingService` define a method named `post_comment`, and no class under `tests/` does." |
| A3 | should fix | fixed. S0009 c5: "The stand-in's whole environment is `request.environment` plus the three switches, and a variable set in the test process is not in it" → for a request whose `environment` is `{"LC_ALL": "C.UTF-8", "TOKEN_PROBE": "x"}`, every variable is one of those two, the three switches, or `LC_CTYPE` (added by CPython under the C locale); the given variables and the switches are present with their values; a test-process variable is absent; with an empty `environment` the stand-in has no `PATH`. |
| A4 | should fix | fixed. Old S0008 c18 split. S0009 c15: armed, `run` raises `InjectedKill` after the writes, for a completed and a died reply. S0009 c16: not armed, `run` returns and `reached` is 1; a runtime built without kill points returns normally. S0010 c11 adds the two-call case. |
| A5 | should fix | fixed in the story, observation deferred. `--permission-prompts none` is dropped from S0009's argument list (binding answer); S0009 c1 now also says the arguments hold no `--permission-prompts`. Checking the flags against the pinned `claude --help` is recorded as a morning observation tied to F0010's preflight probe (S0009 Assignment, FEATURE decision 18). `--permission-mode auto` stays: v1's book, chapter 8, gives it; FEATURE decision 13 lists it as the change from v1's agent-file key that had no effect in print mode. Note for the human: chapter 8 of `v1-04-08.md` also lists `--permission-prompts none` ("chose `--permission-mode auto` with `--permission-prompts none`"), so the answer's premise (a flag not in that chapter) does not hold for this one; the answer was followed, and decision 13 says how to put it back. |
| A6 | should fix | fixed. Binding answer: the budget case is decided from `subtype` before the exit status. S0009 end-reason rule: a reply with `subtype` `error_max_budget_usd` is S0010's whatever the exit status. S0010 rules and new c6: a first reply with that subtype and exit status 1 is resumed in the same way and the run completes when the resumed call does. Whether the pinned `claude` exits non-zero on a budget stop is a morning observation (S0010 Assignment, decision 18). |
| A7 | should fix | fixed. S0004 old criteria 1 to 8 (`run_process`, the searches, the markers) are the new S0004 (16 criteria); the git error types, fetch and refs are S0005; later stories are renumbered. |
| A8 | should fix | fixed. The resume, `resume_budget`, the shared limit, the summed measures and `version()` are the new S0010; S0009 is the call and its result. Because `version` completes the `AgentRuntime` protocol, the structural-fit criterion moved to S0010 (c16) and S0009 says so. |
| A9 | should fix | fixed. S0006 c8 (new): with an uncommitted edit to a file that differs on branch `other`, `checkout("other")` raises `GitError`, the branch is unchanged and the edit is still in the work tree. "tracking it" is dropped from the `checkout` rule (the pre-check's option b), so S0006 c6 stays "creates a local branch at the remote's commit". |
| A10 | should fix | fixed. S0011 rule for `status`: "a tracked file that is changed, staged and changed again is `modified`; a path that HEAD does not have (untracked, or newly staged, also when edited after staging) is `added`". Old c16 "A file that is staged and then edited again is listed once in `status()`, as `modified`" → c16 "A tracked file that is changed, staged and then changed again is listed once in `status()`, as `modified`" plus new c17 "A new file that is staged and then edited again is listed once in `status()`, as `added`". FEATURE decision 14 updated. |
| A11 | should fix | fixed. S0012 c2: "`delete_remote_branch` of a branch that is already gone from the remote returns `pushed` and changes nothing" → "returns `pushed`, the remote is unchanged, and a stale `origin/<branch>` that the checkout still held is gone afterwards"; the rule says the same. FEATURE decision 15 updated. |
| A12 | should fix | fixed by the binding answer. `GitCli` takes `identity: GitIdentity \| None` (S0005 Interface; `GitIdentity` DTO, S0005 c21), filled from `GIT_USER_NAME` and `GIT_USER_EMAIL` by wiring. S0006 drops `FACTORY_AUTHOR_NAME` and `FACTORY_AUTHOR_EMAIL`; c11 "A commit has the author and the committer `factory <factory@noreply.invalid>` even when ..." → "the author and the committer given as `identity` at construction, also when the test process sets `GIT_AUTHOR_NAME`, and when `GIT_CONFIG_GLOBAL` points to a file with another `user.name` and `commit.gpgsign = true`"; new c12: a `GitCli` without an identity raises `GitError` (`exit_status` `None`, `no commit identity`) and `HEAD` is unchanged. FEATURE decision 10 rewritten. needs interfaces.md: `GitCli`'s constructor gains the keyword-only `identity: GitIdentity \| None = None` and `environment: Mapping[str, str] \| None = None`, and `factory.domain.git` gains `GitIdentity(name, email)` (F0010's wiring builds it from `GIT_USER_NAME` and `GIT_USER_EMAIL`). |
| A13 | should fix | fixed. S0005 Assignment, rules and decision 7: credentials reach git only through the environment of the factory process and the `environment` argument, never through global or system configuration. New criteria: S0005 c10 (an `environment` with `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0` and `GIT_CONFIG_VALUE_0` as `url.<remote>.insteadOf` makes a fetch of a missing origin succeed), c11 (the same entries in the test process's environment), and c8 gains "the same when the file is named by `GIT_CONFIG_GLOBAL` in the `environment` argument" so that `environment` cannot lift the isolation. S0005 c23 (docs) names the operator guide. |
| A14 | should fix | fixed. S0009 c18 (new): a `state_directory` below a regular file raises `AgentRuntimeError` naming the path, the stand-in is never called, `reached` is 0. The files are removed however the run ends, also after `AgentRuntimeError` (S0009 rule; c7 gains "and after `run` raises `AgentRuntimeError` for a missing executable"). The version limit is a constructor argument `version_time_limit` (S0010; `VERSION_TIME_LIMIT` is 30 s; c14 tests a 1-second limit against a stand-in that waits 60 seconds). "No resume when nothing is left": reworded to "a first call ended by the time limit is never resumed" with S0010 c7 (see P-S0008-3). |
| A15 | note | fixed. S0007 Tests paragraph allows the target of c16 that runs about 0.3 seconds. |
| A16 | note | fixed. S0004 Tests names the method (the grandchild writes its pid to a file; afterwards `os.kill(pid, 0)` raises `ProcessLookupError` or `/proc/<pid>/stat` shows `Z`, which also covers an orphan that no init has reaped, the pre-check's container risk); S0004 c6 uses it. S0007 c9 names the same method with the recipe writing `$!` to a file. |
| A17 | note | fixed. S0009 Tests: the stand-in also records the content of the file named after `--settings` inside the hook command of the hooks file; S0009 c6 reads the guard file's content from it. |
| A18 | note | fixed. S0004 c9 adds `timedelta(seconds=-1)` (rejected); S0007 c10 adds `timedelta(seconds=-1)` (`ValueError`). |
| A19 | note | fixed. The 1 ms limit is gone. S0005 c4 uses a stand-in `executable` script that sleeps 60 seconds with `time_limit=timedelta(seconds=1)` and expects `time limit reached` and a return within 6 seconds; `write_executable` is a helper of `tests/git_support.py`. |
| A20 | note | fixed. FEATURE decision 9 and S0004's Assignment now say that `CLAUDE.md` already allows the four markers in `process.py` and that `docs/decisions.md` records it; nothing is asked of the human. |
| A21 | note | deferred. needs interfaces.md: the sheet's rows for `factory.domain.identifiers`, `factory.domain.git` and `factory.domain.paths` must say that F0002-S0001 "adds to" the modules that F0001-S0002, S0005 and S0008 started (`WorkItemId`; `CommitId`, `RemoteBranch`, `GitIdentity`; `MAIN_BRANCH`, `LABEL_PREFIX`, `REMOTE`; `Name`); the cross-check should confirm that F0002-S0001's Interface says so. FEATURE decision 3 is updated with the new story ids. |
| A22 | note | fixed. S0002's Assignment says "the operations R10 lists plus those that R22 and kept thing 11 need", and names the four. |
| A23 | note | fixed. S0002 c15 (old 14) now matches a subscript of `dict`, `Mapping` or `MutableMapping` (also as `typing.Mapping` or `collections.abc.Mapping`) with `Any` as its second argument at any depth, and is run against a snippet; type aliases are named as not followed. S0004 c13 widens the R5 search to `os.exec*`, `os.spawn*`, `os.posix_spawn*`, `asyncio.create_subprocess_exec` and `asyncio.create_subprocess_shell` and names what it cannot see (`getattr`, `importlib`; ruff `S` covers them). S0003 c19 adds `aiohttp`, `urllib3` and `socket` to the imports that the SI2.1 search forbids and names what it leaves out. |
| A24 | note | kept for the human. FEATURE decisions 7, 11, 13 and 19 list the defaults without a source (git `time_limit` 5 minutes, `last_line` skipping `make:` lines, the resume budget minimum 0.50, the `question` resume message that reaches the human on a budget stop, the 30-second `version()` limit). Decision 19 is new. |
| A25 | note | fixed in the story, the open point deferred. S0009 rule: the runtime adds no `PATH`; the hook command `factory-guard` is found through the `PATH` of the request's environment, which F0005 and F0010 must provide; S0009 c5 checks that no `PATH` is added. FEATURE decision 17 records that a guard that cannot start fails open and that F0010's preflight should probe it. |
| A26 | note | fixed. S0003's Assignment: "wiring that builds the PyGithub `Repository` from the token is F0002 onward (`factory.entry.wiring`), with F0010 for the token". |
| A27 | note | fixed. S0003 rules: the constructor reads nothing from the repository (`owner.login` only inside `find_open_pull_request`); new c18: a stand-in that raises on every access is accepted by the constructor. |
| A28 | note | kept for the human. FEATURE decision 5 now says that the `set_labels` read sits beside R10's "labels are never read back" and names the alternative (add and remove calls that need no read). S0003 is unchanged. |
| A29 | note | fixed. S0011's Assignment: S0006 and S0012 do not depend on it, S0013's closing criterion does, and S0013 follows in id order. |
| A30 | note | fixed. The Tests paragraphs of S0002, S0005, S0006, S0007, S0008 and S0014 say that `tests/conftest.py` and `tests/domain/test_errors.py` are extended with new tests and fixtures only and that no existing test is changed. |
| A31 | note | fixed. S0005 (which creates `tests/git_support.py`), S0006, S0011, S0012 and S0013 say that test helpers start git through `factory.adapters.process.run_process`, never through `subprocess`. |
| A32 | note | fixed. S0013 c11 (the old "exactly these nineteen operations"): "`GitCli` implements exactly these nineteen operations of `Git`; the protocol has no other" → "`Git` has exactly the nineteen operations named in the rules, and `GitCli` has each of them (a test compares the public names of the protocol with that list and checks `hasattr` on `GitCli`)". |
| A33 | note | fixed. `GitError.output_tail` is the last 30 lines of the output, merged in the order written (S0005 rule; FEATURE decision 7); new S0005 c2 tests 40 lines against 3 lines with a stand-in `executable`. |
| A34 | note | fixed. S0007 c25 (docs): "the exit status as the only verdict" → "the exit status as the only judgment". |

## Pre-check items

The pre-check's intake questions each name an option; the recommended one was taken unless the table says otherwise. Pre-check S0001, S0003 and S0009 (old numbering) were accepted.

| Item | Severity | Handling |
|---|---|---|
| P-S0001 remark (rejected `after` below 0 on an armed point) | note | fixed. S0001 c10: "`arm(point, after=-1)` raises `ValueError` and leaves the point inert" → "... and leaves the point inert, and on a point that is already armed it leaves the earlier arming as it was". |
| P-S0002-1 (`parse_post_key` with trailing blank lines and spaces) | question | fixed, option a. S0002 rule: trailing whitespace including `\r` ignored, blank lines after the key do not matter. New c9: the key is returned for a key line followed by two blank lines, one ending in spaces, one ending in `\r`, and for `\r\n` line ends throughout. |
| P-S0002-2 (rule "merged whatever the merge method") | question | fixed, option a. The clause is dropped from S0002's rules; `merge_commit` is set exactly when `state` is `merged`. |
| P-S0002 risk (40-character literal and `make secrets`) | note | fixed. Tests paragraphs of S0002, S0003, S0005 and S0014 require low-entropy literals such as `"a" * 40`. |
| P-S0003 reviewer remark ("tests use the fake" before the fake exists) | note | fixed. S0003's docs criterion (c23) now says that the one fake (S0014) is what other tests use. |
| P-S0004-1 (UTF-8 decoding with replacement) | question | fixed, option a. S0004 c10: a child that writes the bytes `\xff ok\n` gives `stdout == "� ok\n"`. |
| P-S0004-2 (`GIT_CONFIG_NOSYSTEM`) | question | fixed, option a. S0005 c9: with `GIT_CONFIG_SYSTEM` in the test process pointing to a file that rewrites the remote's URL to a missing path, `fetch()` still succeeds. |
| P-S0004-3 (`resolve("HEAD")` without commits) | question | fixed, option a. S0005 c14: `resolve` returns `None` for `origin/nope` and for `HEAD` in a repository without commits (old c16 split into c13 and c14). |
| P-S0004-4 (what "merged" means for `output_tail`) | question | fixed, option a. S0005 rule: merged in the order written, the last 30 lines; c7 adds that the tail of the first case contains git's `not a git repository`. |
| P-S0004 flakiness (1 ms limit) and zombie risk | note | fixed, see A19 and A16. |
| P-S0005-1 (`checkout` blocked by uncommitted changes) | question | fixed, option a. See A9. |
| P-S0005-2 ("tracking it") | question | fixed, option b. See A9. |
| P-S0006-1 (the make class reaches no kill point) | question | fixed, option a. S0007 c18 (new): with all four kill points armed, `run` returns normally and `reached` is 0 for each. |
| P-S0006-2 ("with the current environment") | question | fixed, option a. S0007 c17 (new): a target that prints `$$PROBE` shows a variable set in the test process. |
| P-S0006 demo refusal | refusal | fixed, see A1. |
| P-S0007-1 (`deletes` escaping the working directory) | question | fixed, option a. S0008 c17: "A scripted run that writes `../escape.txt`, or an absolute path, makes `run` raise `AgentRuntimeError`, and nothing is written or deleted ..." → "A scripted run that writes `../escape.txt` or an absolute path, and a scripted run that deletes `../x` or an absolute path, each make `run` raise `AgentRuntimeError`, and nothing is written or deleted, not even by the valid entries of the same run (a file that exists under the working directory is still there)". |
| P-S0007-2 (`kill` true without kill points) | question | fixed, option a. S0008 c21 (new): a `FakeAgentRuntime()` without kill points returns the scripted result for a run with `kill` true, and the writes are on disk. |
| P-S0007-3 (`TokenCounts` negatives) | question | fixed, option a. S0008 c10: "rejects `input=-1`, accepts `input=0`, ..." → "rejects `-1` for each of `input`, `output`, `cache_read` and `cache_creation`, accepts `0` for each, and has `cache_read == 0` and `cache_creation == 0` by default". |
| P-S0008-1 (half-cent rounding) | question | fixed, option a. S0010 c1 adds `Decimal("2.02")` → `0.51` and `Decimal("2.10")` → `0.53` (half-even would give `0.50` and `0.52`); Demo 2 adds `2.02`. |
| P-S0008-2 (unwritable state directory) | question | fixed, option a. See A14 (S0009 c18). |
| P-S0008-3 ("no resume when nothing is left") | question | fixed, option a. The clause is reworded to "a first call that ended by the time limit is never resumed"; S0010 c7: a stand-in that waits 60 seconds with a limit of 1 second gives `time_limit` and exactly one call. The corner of a leftover below zero cannot be set up without a race and is not stated as a rule. |
| P-S0008-4 (one-sided measure sums) | question | fixed, option a. S0010 c9: a first reply without measures and a resumed one with them give the resumed call's values; neither gives `None`. |
| P-S0008-5 (required JSON fields) | question | fixed, option a. S0009 rule names `subtype` and `is_error` as required; c13: a JSON object without `subtype`, and one without `is_error`, give `died`. |
| P-S0008-6 (`usage` with one count) | question | fixed, option a. S0009 c10 adds: a `usage` with `input_tokens` only gives `tokens` `None`. |
| P-S0009 remark (S0010 depends on S0009) | note | fixed, see A29. |
| P-S0010-1 (`delete_remote_branch` other failure) | question | fixed, option a. S0012 c5: an invalid ref name such as `a..b` raises `GitError`. |
| P-S0010-2 (`delete_remote_branch` reaches no kill point) | question | fixed, option a. S0012 c6: with `BEFORE_PUSH` and `AFTER_PUSH` armed it returns `pushed` and both counts stay 0. |
| P-S0010-3 (merge default message) | question | fixed, option a. S0012 c12 adds that the merge commit's subject is git's default `Merge branch 'other'`. |
| P-S0010-4 (stale `origin/<branch>`) | question | fixed, option a. See A11. |
| P-S0010-5 (`fast_forward_only` with a fast-forward) | question | fixed, option a. S0012 c11 adds the same result with `fast_forward_only=True`, and the rule says it. |
| P-S0011 (criterion 17 against the protocol class) | question | fixed. See A2. |
| P-S0011 reviewer gap (no criterion for the side without kill points) | note | fixed. S0014 c12 adds "a `FakeHostingService` built without kill points posts normally". |
| P-cross-story: detect-secrets | note | fixed, see "P-S0002 risk". |

## Open for the human or later rounds

- needs interfaces.md: `GitCli(directory, kill_points=None, *, executable, time_limit, environment, identity)`, and `GitIdentity` in `factory.domain.git` (A12, A13).
- needs interfaces.md: "adds to" wording for the modules that F0001 starts (A21), the sheet's story tags for S0004 to S0008 (FEATURE decision 16), and the `last_line` refinement and the `output_tail` of `CheckResult` ("interleaved" there means the order written).
- The answer dropped `--permission-prompts none`, which v1's book lists (A5, FEATURE decision 13).
