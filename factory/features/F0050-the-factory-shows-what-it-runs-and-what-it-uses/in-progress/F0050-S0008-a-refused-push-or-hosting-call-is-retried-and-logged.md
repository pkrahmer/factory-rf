---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 540
comments_read: [6630647682, 6630816683, 6631188803]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-04T13:12:09.747104Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T12:23:35.911782Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T12:23:35.918605Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T12:24:06.454303Z'
  stage: intake
  run: 42c597e967034e93b8854e0a906e05a0
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T12:32:12.184425Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T12:32:16.006866Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T12:32:41.844409Z'
  stage: intake
  run: 395f0a8f3f324a4eb058f67869d6b6d5
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T12:32:48.233812Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-04T12:34:21.286427Z'
  stage: tests
  run: 62008eeeb5904f8989f2d6b8cf0589b2
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-04T12:40:22.806684Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T12:40:26.398912Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-04T12:45:40.725068Z'
  stage: tests
  run: 97005f8c0cc942d8851a90f9728c2805
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T12:45:47.161275Z'
  stage: doing
- number: 13
  speaker: coder
  kind: question
  at: '2026-11-04T12:50:52.987449Z'
  stage: doing
  run: f81195d101a642248e59316d59c21fa0
  blocked: question
- number: 14
  speaker: human
  kind: comment
  at: '2026-11-04T12:56:53.238129Z'
  stage: doing
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-04T12:56:56.615731Z'
  stage: doing
- number: 16
  speaker: coder
  kind: result
  at: '2026-11-04T12:59:11.769462Z'
  stage: doing
  run: f1f22b1681794484b9df37497af81d09
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-04T12:59:18.130950Z'
  stage: tests
- number: 18
  speaker: tester
  kind: result
  at: '2026-11-04T13:00:20.026854Z'
  stage: tests
  run: a7356a966a6a4b36b3fa5f95a2a2d16b
- number: 19
  speaker: factory
  kind: started
  at: '2026-11-04T13:00:26.653561Z'
  stage: doing
- number: 20
  speaker: coder
  kind: result
  at: '2026-11-04T13:04:31.316995Z'
  stage: doing
  run: d36ed4a3c03b4523ba3e4a166b20e292
- number: 21
  speaker: factory
  kind: started
  at: '2026-11-04T13:04:37.627853Z'
  stage: review
- number: 22
  speaker: reviewer
  kind: result
  at: '2026-11-04T13:06:48.126081Z'
  stage: review
  run: f89b02c6fc7e4ce79a7d6fdda8986749
- number: 23
  speaker: factory
  kind: started
  at: '2026-11-04T13:06:54.502220Z'
  stage: doing
- number: 24
  speaker: coder
  kind: result
  at: '2026-11-04T13:07:15.073673Z'
  stage: doing
  run: b11e7ebfb0f64c598a7d74dce1b0beb1
- number: 25
  speaker: factory
  kind: started
  at: '2026-11-04T13:07:21.552883Z'
  stage: tests
- number: 26
  speaker: tester
  kind: result
  at: '2026-11-04T13:08:13.789404Z'
  stage: tests
  run: 3edf4a6e31d44bd3a6fa3314b18ab66c
- number: 27
  speaker: factory
  kind: started
  at: '2026-11-04T13:08:20.561295Z'
  stage: doing
- number: 28
  speaker: coder
  kind: result
  at: '2026-11-04T13:12:02.978248Z'
  stage: doing
  run: 3b37a1ca572543528ca6a54dba4eb8a4
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-04T13:12:09.747104Z'
  stage: review
---

# A refused push or hosting call is retried and logged

## Description

GitHub's partial outage of 2026-11-04 (about 09:36 to 10:05 UTC) was analysed in `planning/outage-2026-11-04.md`. The factory held up: no stop, nothing half-written on the remote, F0050-S0001 finished. But two things went wrong, and neither could be read from what the factory kept. First, the docs stage of S0001 finished its run and its checks at 09:36:46, and the push of its result most likely failed once; one failed push discards a finished run, charges a crash and runs the paid agent again, and the first run's cost record is lost with it (19 runs recorded, 20 ran). Second, the hand-over failed three times in about 90 s, reached the handler's error cap and was never tried again, and its first two errors were logged nowhere. This story makes a short outage cheap and visible. Every handler error the factory counts gets a log line; a refused or unreachable push of a stage's result or of a recorded change is tried again after 5, 15 and 45 s before it fails as today; the push error keeps git's own reason; and the GitHub client retries with a backoff, writes included. A test pins what happens when the hosting service fails after a stage's claim, which the analysis found untested. The cap of three tries stays (the human, 2026-11-04).

## Interface

- `Dispatcher._count` (or wherever a handler error is counted) writes one log line per counted error: `handler error <event key> <n> of <cap>: <exception type>: <text>`, the text on one line and at most 300 characters. Nothing else about the counting or the cap changes.
- The push of a stage's result (`StageFinisher._commit_and_push`) and of a recorded change (`WorkItemRecorder.publish`), on a push that is refused or cannot reach the remote, waits 5, 15 and 45 s and pushes again, then raises `PushFailed` as today. Each retry writes `push: retry <n> of 3 in <s> s: <reason>`. No force, no rebase, no new commit between the tries. The waits go through the factory's clock or sleeper interface, so the tests wait no real time.
- `PushFailed` carries git's reason: the last non-empty lines of git's output (at most three, at most 300 characters), in its message and so in every report and log line that names it. The reason is built by the pure function `push_reason(output)` in `factory.domain.git`. Before it takes the last three lines, it leaves out git's advice lines: exactly `Please make sure you have the correct access rights` and `and the repository exists.` (after stripping), and any line that starts with `hint:`.
- The PyGithub client is created with a retry that backs off and covers `PATCH` as well as the default methods: `GithubRetry(total=5, backoff_factor=2, allowed_methods=<the default methods plus PATCH>)` or its equivalent in the installed version, in the one place the client is built.
- Only a server refusal (`! [remote rejected]`) and an unreachable remote are retried; `! [rejected]` with `non-fast-forward` or `fetch first` fails at once, no wait, no retry line. The reason's 300 characters are for the whole reason (the up to three lines joined), cut at the end. The stall push in `stalls.py` stays without a retry. The retry is built in `factory.adapters.pygithub_hosting`, used by `pygithub_service(repository, token)`.
- A test of what happens when the hosting service fails after a stage's claim (in `ensure_pull_request`, called at the stage's start): it pins today's behaviour. If that behaviour charges a crash for a stage in which no agent ran, the test is marked with `pytest.mark.xfail(strict=True, reason=...)` naming that, and the story's entry names it for the human; the fix is not part of this story.

## Acceptance criteria

1. A handler error that is counted writes its line with the event key, the count, the cap, the type and the text; rows: the first, the second and the third (capped) error of one event; a text with a line break is written on one line; a text over 300 characters is cut.
2. A result push that fails twice and then passes is pushed on the third try, writes two retry lines, raises nothing and charges no crash; one that fails four times raises `PushFailed` after the three retries. The same two rows for `WorkItemRecorder.publish`. The test's clock shows waits of 5, 15 and 45 s, and the test takes no real time.
3. `PushFailed`'s message holds git's last lines: rows for a server error (`remote: Internal Server Error` with `! [remote rejected]`), a non-fast-forward rejection, and an unreachable remote.
4. The hosting client is built with a retry whose total is 5, whose backoff factor is 2, and whose allowed methods include `PATCH` and every default method.
5. The test of a hosting failure after the claim exists and pins the behaviour, as the Interface says: one tick in which the fake hosting service fails in `ensure_pull_request` after the claim was pushed; no agent run was started (the fake runtime has no call); at the next tick the journal and the crash count are asserted. It is marked `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")` exactly when that next tick records a `crash` entry or a crash count of 1 for that stage; otherwise it passes as written. The entry names which of the two it is.
6. `PushFailed`'s reason holds at most the last three non-empty lines of git's output: a row with five lines keeps the last three; a row whose joined reason is over 300 characters keeps the first 300 characters (the 300 are for the whole reason, cut at the end).
7. The retried push is the same command each time, without `--force`, and the branch's head commit id is the same before each try (result push and `WorkItemRecorder.publish`).
8. The retry lines read `push: retry 1 of 3 in 5 s: <reason>` and `push: retry 2 of 3 in 15 s: <reason>` (and `push: retry 3 of 3 in 45 s: <reason>` in the four-failure row), each ending with git's reason.
9. Only a refusal by the server (`! [remote rejected]`, for example with `Internal Server Error`) and an unreachable remote are retried. A rejection with `! [rejected]` and `non-fast-forward` or `fetch first` fails at once with `PushFailed`, with no wait and no retry line (rows for both the result push and `WorkItemRecorder.publish`).
10. The `GithubRetry` is built by a small module-level function or constant in `factory.adapters.pygithub_hosting`, which `pygithub_service(repository, token)` passes to `github.Github(auth=..., lazy=True)`; a test reads the `retry` the built client was given, without a network.
11. `make check` stays green.
12. docs: `docs/operator-guide.md`: in the section on stops and errors, the handler error line, that a refused push is retried after 5, 15 and 45 s, that the reason in a push error is git's own, and what the factory does during a hosting outage (today's evidence in short). `docs/decisions.md`: one entry with the reason (the outage of 2026-11-04 and `planning/outage-2026-11-04.md`), and that the cap of three tries stays. `README.md`: none. The project guide: the file on the hosting service names the client's retry.

## Smoke test

```bash
grep -rhoE 'handler error|push: retry' src/factory | sort -u
grep -rc 'PATCH' src/factory/adapters | awk -F: '{s+=$2} END {print (s>0)}'
uv run pytest tests/application tests/adapters -k "push or handler or hosting" 2>&1 | tail -1
```

Expect: the two lines `handler error` and `push: retry`, then `1`, then a line that ends in `passed` with no `failed` (an `xfailed` count may stand beside it).

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: The format check passed. The story is not buildable yet. Questions:

   1. Interface: `PushFailed` carries "at most three" last non-empty lines and "at most 300 characters". Criterion 3 has rows only for three kinds of failure. Neither limit has a criterion, so neither the case of more than three lines nor the case over 300 characters is tested. I would add two rows: one with five lines of output, which keeps the last three; one with a very long line, which is cut at 300. Which characters are cut, and is the 300 per line or for the whole reason? I would take the whole reason, cut at the end.

   2. Interface: "No force, no rebase, no new commit between the tries" has no criterion. I would add one: the retried push is the same command, with no `--force` and no new commit id. Add it?

   3. Interface: the retry line `push: retry <n> of 3 in <s> s: <reason>` is not pinned in criterion 2, which says only "two retry lines". The numbers and the reason are not tested. I would add: lines `retry 1 of 3 in 5 s` and `retry 2 of 3 in 15 s`, each ending with the reason. Add it?

   4. Interface: the retry covers a push that "is refused or cannot reach the remote". Criterion 2 does not say whether a refused push is retried too, for example a non-fast-forward rejection, which waiting does not cure. Criterion 3 has that row only for the message. Please state whether every `PushFailed` is retried, or only the server-error and unreachable kinds. If only those, the non-fast-forward kind needs a criterion that it fails at once without a wait.

   5. Scope: `stalls.py:143` has a third `_commit_and_push` (`StallContext`). The story names only `StageFinisher._commit_and_push` and `WorkItemRecorder.publish`. Is the stall push meant to stay without a retry? I would assume it does. Please confirm.

   6. Criterion 4 pins the retry's total, backoff factor and allowed methods. It does not say where the client is built or how a test reaches the retry. Please name the module and function (the "one place the client is built") in the Interface, so the test has a seam.

   7. Interface, last bullet: criterion 5 says the test "pins the behaviour" but gives no expected behaviour, and no seam beyond `ensure_pull_request`. Please say what the test asserts: the outcome of the tick, the crash count and the journal. Please also say what makes it `xfail`: a crash charged although no agent ran.

   Already fine: the pytest `addopts` has `-q`, and the smoke test passes none. The architecture fits: the log line and the retry sit in the application layer, and the sleeper (`machine.py`) is an existing interface. The scope fits the feature's list for S0008.
4. 2026-11-04 human: Answers of the human:

   1. Yes, both rows. The 300 characters are for the whole reason (the up to three lines joined), cut at the end: the first 300 characters are kept.
   2. Yes: a criterion that the retried push is the same command, with no `--force`, and that the branch's head commit id is the same before each try.
   3. Yes: the lines `push: retry 1 of 3 in 5 s: <reason>` and `push: retry 2 of 3 in 15 s: <reason>` (and `retry 3 of 3 in 45 s` in the four-failure row), each ending with git's reason.
   4. Only the kinds a wait can cure are retried: a refusal by the server (git's `! [remote rejected]`, for example with `Internal Server Error`) and a remote that cannot be reached. A rejection that waiting does not cure (git's `! [rejected]` with `non-fast-forward` or `fetch first`) fails at once with `PushFailed`, with no wait and no retry line. Add a criterion with that row.
   5. Confirmed: the stall push in `stalls.py` stays without a retry in this story.
   6. The one place is `pygithub_service(repository, token)` in `factory.adapters.pygithub_hosting` (line 156, where `github.Github(auth=..., lazy=True)` is built). The test reads the retry from the built client (the `retry` the client was given); the coder may add a small module-level function or constant that builds the `GithubRetry`, so the test can check it without a network, and says so in its entry.
   7. The test drives one tick in which the hosting service fails in `ensure_pull_request` (`factory.application.opening`) after the claim was pushed, using the fake hosting service. It asserts: no agent run was started (the fake runtime has no call), and then, at the next tick, what the journal and the crash count hold. It is marked `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")` exactly when the next tick records a `crash` entry or a crash count of 1 for that stage; otherwise it passes as written. The entry names which of the two it is.
5. factory: started intake as vm.
6. intake: accepted. I carried the human's answers (journal entry 4) into the story; that is their edit, not mine. Criteria 5 to 10 and one Interface bullet are new or reworded, and `make check` and `docs:` are now criteria 11 and 12.
   - Interface: the push retry, the `PushFailed` reason, the client's retry and the log line are concrete. The seam is now named: `pygithub_service(repository, token)` in `factory.adapters.pygithub_hosting`, plus a small function or constant that builds the `GithubRetry`. The coder says so in its entry. The retried kinds and the 300-character limit for the whole reason (answers 1 and 4) are written into the Interface.
   - Criteria: each is testable by one test function, and the two limits and the failing side now have criteria. Criterion 6 covers three lines versus five and the 300-character cut. Criterion 7 covers the same command with no `--force` and the same head id. Criterion 8 covers the retry lines. Criterion 9 covers the failing side: `! [rejected]` with non-fast-forward or fetch first fails at once with no wait. Criterion 5 now says what the hosting-failure test asserts, and that it is xfail(strict) exactly when a crash is charged although no agent ran. The tester's entry names which of the two it is. The fix is not part of this story.
   - Smoke test: the three commands can be run, and each Expect line can be checked against the output. The pytest `addopts` already sets `-q` and the command passes none.
   - Architecture: the log line and the retry sit in the application layer, and the sleeper is an existing interface. The GitHub client change stays in the adapters, behind the hosting-service interface.
   - Scope: this is the feature's S0008 item. The stall push in `stalls.py` stays without a retry (answer 5). The cap of three tries stays.
7. factory: started tests as vm.
8. tester: I stopped before writing any tests. I read the work item, `dispatcher.py`, `stage.py` (`StageFinisher`), `handlers/recording.py` (`WorkItemRecorder`), `errors.py` (`PushFailed`), `git_cli.py` (`push`, `_failed_push`, `UNREACHABLE_MARKERS`), `machine.py`/`clock.py` (`Waiter`, `ManualWaiter`, already in the `boundaries` fixture) and `pygithub_hosting.py`. Criteria 1, 2, 4, 5, 7, 8, 9 and 10 can be tested. For 2, 7, 8 and 9 the plan is a real bare remote whose `pre-receive` hook fails a counted number of times, with `ManualWaiter.waits` checked for 5/15/45 s. Criteria 3 and 6 can't be tested as written without me choosing an interpretation, so I am asking.

   Question: where does "git's reason" come from, and how does a test give git an output it controls?

   `CLAUDE.md` says "do not fake git", so tests push to a real local remote. But when a real push is refused, git prints its own lines after the hook's `remote:` lines. With `--porcelain` and stderr merged, as `GitCli._execute` runs it, the output ends with the `To <url>` line, the `!\t<ref>\t[remote rejected] (pre-receive hook declined)` line and `error: failed to push some refs to ...`. So:
   - (criterion 3) "the last three non-empty lines" of a real server refusal would hold `[remote rejected]`, but not `remote: Internal Server Error`. Is the row met when only the `[remote rejected]` line is in the message?
   - (criterion 6) a hook that prints five lines doesn't produce output that ends in those five lines. A test can't build "five lines, keep the last three" or "a joined reason over 300 characters, cut at the end" through a real push without guessing git's own trailing lines.

   The options I see:
   - (a) The Interface names a pure function in `factory.domain`, e.g. `push_reason(output: str) -> str`: the last non-empty lines (at most three), joined, cut to 300 characters. Criteria 3 and 6 are text rows on that function. One further test per kind, on a real remote (hook refusal, non-fast-forward, removed remote), checks that `str(PushFailed)` from `StageFinisher`/`WorkItemRecorder.publish` holds the line that names the kind (`[remote rejected]`, `[rejected]` with `non-fast-forward`/`fetch first`, `does not appear to be a git repository`).
   - (b) A stand-in `git` executable, given through `GitOptions.executable`, that prints a fixed output for `push` and hands everything else to the real git. That is a partial fake of git, which `CLAUDE.md` rules out.
   - (c) Only real pushes, with criteria 3 and 6 reworded to what a real refusal prints (for example "the reason holds at most three lines and at most 300 characters, and its last line is git's last non-empty line").

   I would choose (a), with the function's name and module put in the Interface.

   A smaller point, to confirm with the same answer: for criterion 7, I would check "the same command, without `--force`" with a recording subclass of `GitCli`. It records each `push(branch)` call and the branch head before calling the real `push`, and the hook records the new commit id it got. Nothing is faked: the push runs. Real git can't be observed in any other way, because a server-side hook can't see `--force`.

   Files created: none. No test run, so no import failures recorded yet.
9. 2026-11-04 human: Answers of the human:

   1. **(a)** "The Interface names a pure function in `factory.domain`, e.g. `push_reason(output: str) -> str`: the last non-empty lines (at most three), joined, cut to 300 characters." Put it in `factory.domain.git` (beside the other git rules), named `push_reason`. Criteria 3 and 6 are text rows on that function. A server refusal's row is met when the `! ... [remote rejected] ... (<reason>)` line is in the message: git repeats the server's reason in that line's parentheses (on 2026-11-04: `! [remote rejected] main -> main (Internal Server Error)`). Plus one test per kind on a real remote (hook refusal, non-fast-forward, removed remote), as you describe, checking that `str(PushFailed)` holds the line that names the kind.

   2. Confirmed: a recording subclass of `GitCli` that records each `push` call and the branch head before calling the real `push`, with the hook recording the commit id it got. That is no fake: the push runs.
10. factory: started tests as vm.
11. tester: I wrote the tests for criteria 1 to 10, following the human's answers in journal entry 9. The reason text is tested on a pure function, `push_reason` in `factory.domain.git`. Each kind of failure also has a test on a real remote. Criterion 7 uses `RecordingGit`, a subclass of `GitCli`: it records each `push` call and the head before calling the real push. The remote's `pre-receive` hook refuses a counted number of pushes with `Internal Server Error` and records the commit id it was offered. Waits are read from the `boundaries` fixture's `ManualWaiter`, so no real time passes. Retry lines are read from a `RecordingLog` (`tests/recording_log.py`) that replaces `boundaries.log`.

    Mapping (every push test in `test_push_retry.py` runs twice through the `case` fixture: `result` is `StageFinisher.finish`, which reaches `_commit_and_push`; `record` is `WorkItemRecorder.publish`):
    - criterion 1: tests/application/test_dispatcher_error_lines.py::test_each_counted_error_writes_its_key_count_cap_type_and_text, ::test_an_error_text_with_a_line_break_is_written_on_one_line, ::test_an_error_text_is_written_with_at_most_300_characters (300 kept, 301 cut)
    - criterion 2: tests/application/test_push_retry.py::test_a_push_refused_twice_is_pushed_on_the_third_try_without_a_crash, ::test_a_push_refused_four_times_raises_push_failed_after_three_retries
    - criterion 3: tests/domain/test_push_reason.py::test_the_reason_holds_gits_last_lines (server, non-fast-forward, unreachable). On a real remote: the four-failure test above (`[remote rejected]`), ::test_a_push_behind_the_remote_fails_at_once_without_a_retry (`[rejected]`), ::test_a_push_to_an_unreachable_remote_is_retried_and_names_gits_reason (`does not appear to be a git repository`)
    - criterion 4: tests/adapters/test_pygithub_retry.py::test_the_hosting_client_retries_five_times_with_a_backoff_and_covers_patch
    - criterion 5: tests/application/test_hosting_failure_after_claim.py::test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick
    - criterion 6: tests/domain/test_push_reason.py::test_the_reason_keeps_the_last_three_non_empty_lines (3, 4 and 5 lines), ::test_a_one_line_reason_is_cut_at_300_characters (300 kept, 301 cut), ::test_a_joined_reason_over_300_characters_keeps_its_first_300
    - criterion 7: tests/application/test_push_retry.py::test_the_retried_push_is_the_same_push_of_the_same_head
    - criterion 8: tests/application/test_push_retry.py::test_each_retry_line_names_its_try_its_wait_and_gits_reason
    - criterion 9: tests/application/test_push_retry.py::test_a_push_behind_the_remote_fails_at_once_without_a_retry (fetch first, non-fast-forward)
    - criterion 10: tests/adapters/test_pygithub_retry.py::test_the_hosting_client_retries_five_times_with_a_backoff_and_covers_patch. It reads the retry from the built client, `vars(service)["_repository"].requester`, with no network call. It does not depend on the name of the builder function.

    Criterion 5 is the xfail case. Before writing the test I ran a probe once. After `create_pull_request` fails at the claim, the claim is pushed and no agent runs. The next tick records `factory crash`, then `started`, and the crash count is 1. So the test is marked `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")`. Today a crash is charged for a stage in which no agent ran; the human should know this. The fix is not part of this story.

    Interpretations, all inside the Interface's wording:
    - The 300-character limit in the dispatcher line applies to `<text>` after `<exception type>: `.
    - How a line break is replaced is not pinned. The test checks only that the line has no break and keeps both parts.
    - The retry reason is not compared with a fixed text, because git's trailing lines vary. The test checks that each reason holds `[remote rejected]`; in the four-failure row it also checks that the reason appears in `str(PushFailed)`.

    The Interface does not yet name `push_reason`; the human's answer 9 does.

    Files created: tests/application/test_push_retry.py, tests/application/test_dispatcher_error_lines.py, tests/application/test_hosting_failure_after_claim.py, tests/domain/test_push_reason.py, tests/adapters/test_pygithub_retry.py. No earlier test file was changed.

    Test run: I ran the test files once. Collection stopped on `ImportError: cannot import name 'push_reason' from 'factory.domain.git'`, which is the expected missing name. Because collection stopped there, that run did not show the other files' failures. I did not run them again (stage rule). `make lint` is green. The type check was skipped, as this stage allows.

    `lint`: lint: green (0.1 s)
12. factory: started doing as vm.
13. coder: I wrote the code and ran `make check`. The tests disagree with the Interface in four places, and these need the human's answer before the tester changes anything. My code is in the working tree. Every new test except two passes, and `xfail` (criterion 5) still holds. `make check` stops at `make types`. In `make test`, 11 tests fail, all listed below.

    What I built:
    - `src/factory/domain/git.py`: `push_reason(output)` keeps the last non-empty lines, at most three, joined with ` | ` and cut at the end to 300 characters. `push_is_retried(outcome, output)` is true for `unreachable`, and for `rejected` when the output holds `[remote rejected]`.
    - `src/factory/domain/errors.py`: `PushFailed(branch, outcome, reason="")` puts the reason in its message.
    - `src/factory/application/pushes.py` (new): `push_with_retries(boundaries, branch)` waits 5, 15 and 45 s through `boundaries.waiter` and writes `push: retry n of 3 in s s: <reason>` to `boundaries.log`. `push_failure(git, branch, outcome)` builds a `PushFailed` with git's reason. `StageFinisher._commit_and_push` and `WorkItemRecorder.publish` use the retry. Claims, stalls, acceptance and `delete_branch` use only `push_failure`, without a retry.
    - `src/factory/domain/tick_status.py`: `handler_error_line`. `Dispatcher._count` writes it once per counted error.
    - `src/factory/adapters/pygithub_hosting.py`: `hosting_retry()` is `GithubRetry(total=5, backoff_factor=2, allowed_methods=DEFAULT | {"PATCH"})`, passed by `pygithub_service`.
    - `GitCli` keeps the output of the last failed push in `last_push_output()`. The `Git` interface gained that method.

    Questions:

    1. `tests/application/test_push_retry.py::test_a_push_to_an_unreachable_remote_is_retried_and_names_gits_reason[result|record]` fails because of the rule "the last three non-empty lines". Against a moved local remote, git prints `fatal: '<path>' does not appear to be a git repository`, then `fatal: Could not read from remote repository.`, then the two advice lines `Please make sure you have the correct access rights` and `and the repository exists.` So the reason is `fatal: Could not read from remote repository. | Please make sure you have the correct access rights | and the repository exists.`, and the test's line is the fourth from last. Options:
       - (a) `push_reason` drops git's advice lines (these two, and lines starting with `hint:`) before it takes the last three. The Interface gets one more sentence; the domain tests pass as they are.
       - (b) The tester changes the expected text to `Could not read from remote repository`; the Interface is unchanged.

       I would choose (a). Over ssh, the line that names the cause comes before the same advice lines and would be lost too.

    2. `make types` fails in that same test file:
       - line 14 imports `GitOptions` from `factory.adapters.git_cli`, which does not export it. The import should come from `factory.domain.git`.
       - line 200 sets `message = None` on a variable that mypy typed as `str`. It needs `message: str | None`.

       These are the tester's changes, and I propose exactly these.

    3. Three tests pin the `Git` interface at exactly 21 operations:
       - `tests/application/test_git_interface.py::test_git_has_exactly_the_twenty_one_operations_and_git_cli_has_each`
       - `tests/application/test_interfaces.py::test_git_abstract_methods_are_exactly_its_twenty_one_operations`
       - `tests/test_checkout_hygiene_removed.py::test_the_names_of_the_checkouts_hygiene_are_gone[git-twenty-one]`

       To carry git's reason across the interface, `Git` needs a 22nd operation. The other way, `push` returning a DTO, breaks `RecordingGit.push(...) -> PushOutcome` and every test that compares an outcome with `"rejected"`. Options:
       - (a) keep `Git.last_push_output() -> str`, and the tester changes these three tests to 22 operations, `last_push_output` included.
       - (b) `push` and `delete_remote_branch` return a `PushResult(outcome, output)` DTO, which changes many tests.

       I would choose (a).

    4. Four tests in `tests/application/test_dispatcher.py` compare the whole log with only the cap line, or with nothing:
       - `test_a_report_for_a_branch_not_on_the_remote_becomes_one_log_line`
       - `test_an_event_without_a_work_item_is_reported_as_one_log_line`
       - `test_a_report_that_fails_with_a_git_error_leaves_the_entry_unreported`
       - `test_a_git_error_in_the_report_of_a_branch_not_on_the_remote_writes_no_log_line`

       They now also see the new lines, for example `assert ['handler err...eError: boom'] == ['error cap r...eError: boom']` and `assert ['handler err...eError: boom'] == []`. The Interface puts one line per counted error into the same log, and the dispatcher has no other. Options:
       - (a) the tester changes these four tests to leave out lines starting with `handler error ` (or to keep only `error cap reached` lines), each checking the same thing as now.
       - (b) the handler error lines go elsewhere, but no other log exists.

       I would choose (a).

    Not touched: the stall push in `stalls.py` still has no retry, as decided. It does carry git's reason now, through `push_failure`. The refactor step and `make duplicates` are left until the tests are settled.
14. 2026-11-04 human: Answers of the human:

    1. **(a)** "`push_reason` drops git's advice lines (these two, and lines starting with `hint:`) before it takes the last three." The advice lines are exactly `Please make sure you have the correct access rights` and `and the repository exists.` (after stripping), and any line that starts with `hint:`. The Interface gets that sentence; the reviewer has leave to add it to the Interface's `PushFailed` bullet. Leave for the tester: a domain row with those advice lines after a cause line.

    2. Yes, exactly those two: in `tests/application/test_push_retry.py`, `GitOptions` imported from `factory.domain.git`, and `message: str | None` at line 200. The tester's own file.

    3. **(a)** "keep `Git.last_push_output() -> str`, and the tester changes these three tests to 22 operations, `last_push_output` included." Leave for the tester: in the three tests you name, the count and the name list become 22 with `last_push_output`; the names of the tests may say twenty-two; nothing else in those modules.

    4. **(a)** "the tester changes these four tests to leave out lines starting with `handler error `, each checking the same thing as now." Leave for the tester: only those four tests in `tests/application/test_dispatcher.py`; nothing else in that module.

    End with `tests` as you need.
15. factory: started doing as vm.
16. coder: I made the code change from the human's answer 1 (journal entry 14). The tests changes from answers 2 to 4 belong to the tester, so I am handing over with `tests`.

    What I built:
    - `src/factory/domain/git.py`: before `push_reason` takes the last three lines, it now leaves out git's advice lines.
      - The two exact lines `Please make sure you have the correct access rights` and `and the repository exists.` (after stripping) are dropped.
      - Any line starting with `hint:` is dropped.
      - New names: `PUSH_ADVICE_LINES`, `PUSH_HINT_PREFIX` and the private `_is_reason_line`.
    - Main choice: I filter these lines in the domain function, rejecting a filter in `GitCli`. That keeps the whole reason rule in one place.
    - The rest of the code is unchanged from the previous round (journal entry 13).
    - `tests/domain/test_push_reason.py` and `tests/application/test_push_retry.py` now pass, including `test_a_push_to_an_unreachable_remote_is_retried_and_names_gits_reason[result|record]`.

    Test changes for the tester, exactly as answered in journal entry 14:
    1. Answer 1: add a domain row in `tests/domain/test_push_reason.py`: a cause line followed by the two advice lines (and a `hint:` line), and the reason keeps the cause line.
    2. Answer 2: in `tests/application/test_push_retry.py`, import `GitOptions` from `factory.domain.git` (line 14), and type the variable at line 200 as `message: str | None`. Today these are the only `make types` errors.
    3. Answer 3: in `tests/application/test_git_interface.py::test_git_has_exactly_the_twenty_one_operations_and_git_cli_has_each`, `tests/application/test_interfaces.py::test_git_abstract_methods_are_exactly_its_twenty_one_operations` and `tests/test_checkout_hygiene_removed.py::test_the_names_of_the_checkouts_hygiene_are_gone[git-twenty-one]`, the count and the name list become 22 with `last_push_output`.
    4. Answer 4: in `tests/application/test_dispatcher.py`, four tests leave out lines starting with `handler error `:
       - `test_a_report_for_a_branch_not_on_the_remote_becomes_one_log_line`
       - `test_an_event_without_a_work_item_is_reported_as_one_log_line`
       - `test_a_report_that_fails_with_a_git_error_leaves_the_entry_unreported`
       - `test_a_git_error_in_the_report_of_a_branch_not_on_the_remote_writes_no_log_line`

    State:
    - `make test`: these 7 tests fail, and nothing else does.
    - `make types`: only the two errors from item 2.
    - `make lint`: green.
    - `make check`: not green until the tester's changes are in.
    - The refactor step and `make duplicates` wait for the next doing round.

    For the reviewer: answer 1 gives leave to add the advice-line sentence to the Interface's `PushFailed` bullet. I did not rewrite the Description.
17. factory: started tests as vm.
18. tester: I made the test changes from the human's answers 1 to 4 in entry 14, as the coder listed them in entry 16. Nothing else changed.

    - Answer 1, the advice lines. `tests/domain/test_push_reason.py::test_the_reason_holds_gits_last_lines` gets a new row, `advice-left-out`, with the new constant `ADVICE_AFTER_CAUSE`. That output holds `fatal: '<path>' does not appear to be a git repository` and `fatal: Could not read from remote repository.`, then an empty line, then the two advice lines and a `hint:` line. The row checks that the reason still holds `does not appear to be a git repository`.
    - Answer 2, `make types`. In `tests/application/test_push_retry.py` (my own file), `GitOptions` is now imported from `factory.domain.git` instead of `factory.adapters.git_cli`. In `test_each_retry_line_names_its_try_its_wait_and_gits_reason`, `message: str | None` is declared before the `try`.
    - Answer 3, 22 operations. `last_push_output` is added to `OPERATIONS` in `tests/git_interface_support.py`. That shared name list is what the two interface tests compare with, so they get the new name from there. The renames:
      - `tests/application/test_git_interface.py::test_git_has_exactly_the_twenty_one_operations_and_git_cli_has_each` is now `test_git_has_exactly_the_twenty_two_operations_and_git_cli_has_each`.
      - `tests/application/test_interfaces.py::test_git_abstract_methods_are_exactly_its_twenty_one_operations` is now `test_git_abstract_methods_are_exactly_its_twenty_two_operations`.
      - `tests/test_checkout_hygiene_removed.py::test_the_names_of_the_checkouts_hygiene_are_gone[git-twenty-one]` now counts 22 and its row id is `git-twenty-two`.
    - Answer 4, the dispatcher log. In `tests/application/test_dispatcher.py`, the asserts on `log.lines` now compare the lines that do not start with `handler error `. This covers the seven asserts in these four tests and nothing else in the module:
      - `test_a_report_for_a_branch_not_on_the_remote_becomes_one_log_line`
      - `test_an_event_without_a_work_item_is_reported_as_one_log_line`
      - `test_a_report_that_fails_with_a_git_error_leaves_the_entry_unreported`
      - `test_a_git_error_in_the_report_of_a_branch_not_on_the_remote_writes_no_log_line`

      Each test checks the same thing as before. I wrote the filter inline in each assert rather than adding a helper, so the module gains no new name.

    Earlier test files I changed, each under the human's leave in entry 14: `tests/git_interface_support.py`, `tests/application/test_git_interface.py`, `tests/application/test_interfaces.py`, `tests/test_checkout_hygiene_removed.py` and `tests/application/test_dispatcher.py`. No files were created.

    Results:
    - One run of the six test modules: all tests passed.
    - `make lint`: green.
    - Every module was imported.
    - I did not run `make types`. Running mypy on the files by hand, outside the Makefile's settings, printed nothing I could use. The coder's `make check` covers it.

    `lint`: lint: green (0.1 s)
19. factory: started doing as vm.
20. coder: The tester's changes from entry 18 are in. `make check` was green on the first run of this round (`check: green`, total coverage 99.41 %). I made no further code changes.

    What I built (unchanged since entries 13 and 16):
    - `src/factory/domain/git.py`:
      - `push_reason(output)`: drops empty lines, git's two advice lines and `hint:` lines; keeps the last three lines left; joins them with ` | `; cuts the whole reason at the end to 300 characters.
      - `push_is_retried(outcome, output)`: true for `unreachable`, and for `rejected` only when the output holds `[remote rejected]`.
    - `src/factory/domain/errors.py`: `PushFailed(branch, outcome, reason="")` gains `reason`, which is added to its message.
    - `src/factory/application/pushes.py` (new):
      - `push_with_retries(boundaries, branch)`: waits 5, 15 and 45 s through `boundaries.waiter`, and before each wait writes `push: retry n of 3 in s s: <reason>` to `boundaries.log`. A refusal that is not retried raises `PushFailed` at once.
      - `push_failure(git, branch, outcome)`: builds a `PushFailed` with git's reason.
    - Where they are used: `StageFinisher._commit_and_push` (`stage.py`) and `WorkItemRecorder.publish` (`handlers/recording.py`) push with retries. The claim, stall, acceptance-opening and remote-branch-deletion pushes only use `push_failure`, without a retry.
    - `src/factory/application/git.py` and `src/factory/adapters/git_cli.py`: a new `Git.last_push_output()` operation (the 22nd), which returns git's whole output of the latest failed push or remote deletion.
    - `src/factory/domain/tick_status.py`: `handler_error_line`. `Dispatcher._count` (`dispatcher.py`) now takes the exception and writes one line per counted error. Counting and the cap are unchanged.
    - `src/factory/adapters/pygithub_hosting.py`: `hosting_retry()` builds `GithubRetry(total=5, backoff_factor=2, allowed_methods=DEFAULT_ALLOWED_METHODS | {"PATCH"})`, and `pygithub_service` passes it to `github.Github(...)`. This is the module-level function the human's answer 6 allowed.

    Main choice: git's reason crosses the `Git` interface through a separate `last_push_output()` operation. I rejected having `push` return a `PushResult` DTO, because it would have changed many tests (human's answer 3a). I also kept the whole reason rule, the advice-line filter included, in the pure domain function rather than in `GitCli`.

    Refactor step: I read the whole diff and found nothing to rename, simplify or remove.

    Criterion 5: the test is the `xfail(strict=True)` case. The tester found that a crash is charged at the next tick for a stage in which no agent ran. That is open for the human; the fix is not part of this story.

    Noticed, not touched:
    - `make duplicates` reports `3 new, 43 known, 0 gone` and exits with an error. The three new findings are vulture's unused-variable warnings (60 % confidence) for `store_free_bytes`, `dataset_free_bytes` and `memory_peak_since_boot_bytes` in `src/factory/domain/cost_records.py:41-43`, a file this story does not change. It is a record, not a check.
    - The stall push in `stalls.py` has no retry, as decided, but now carries git's reason.
    - The reviewer has the human's leave (entry 14, answer 1) to add the advice-line sentence to the Interface's `PushFailed` bullet; I did not rewrite the Description.

    `check`: check: green
    `duplicates`: duplicates: 3 new, 43 known, 0 gone
21. factory: started review as vm.
22. reviewer: Review of round 0. I read the work item and the diff (`src/`, `tests/`). The factory's `make check` after the coder was green (entry 20). I checked the code paths behind the tests: `GitCli._failed_push` and `_is_rejected`, `opening.ensure_pull_request`, and the dispatcher's wiring in `tick.py`. Production passes the log there, so the handler error line is written.

    Criteria 1, 3, 4, 6, 7, 8, 9 and 10 each have a test that tests what it is named after. Every limit has both sides tested: 300/301 for the error text and the reason, and 3/4/5 lines. Architecture holds:
    - `push_reason`, `push_is_retried` and `handler_error_line` are pure functions in the domain.
    - `pushes.py` sits in application and waits through `boundaries.waiter`.
    - The new `Git.last_push_output` is abstract, and `GitCli` implements it.
    - The retry is built only in `pygithub_hosting`.

    Security is clean: no marker, no new baseline entry, and the test token is a low-entropy value. The stall push stays without a retry, as the Interface says.

    Findings:
    1. `tests/application/test_hosting_failure_after_claim.py:9-21`. **What is wrong:** the `xfail(strict=True)` mark also covers the asserts after the first tick (claim pushed, `agent_runtime.requests() == []`). If no claim were pushed, or an agent ran, the test would still xfail. So criterion 5's "no agent run was started" is not pinned. **Fix:** assert the state after the first tick in a test that passes, or in a fixture it shares with the xfail test. Keep only the next-tick asserts (journal `crash`, `crashes == 0`) under the strict xfail mark.
    2. `tests/application/test_push_retry.py:150-170`. **What is wrong:** the two sides of the three-retry cap are separate test functions: `test_a_push_refused_twice_is_pushed_on_the_third_try_without_a_crash` and `test_a_push_refused_four_times_raises_push_failed_after_three_retries`. The boundary row is missing: refused three times, pushed on the fourth try after three retries and waits of 5, 15 and 45 s. The code handles that row as the Interface says (`src/factory/application/pushes.py:27-34`). **Fix:** one parametrized test over 2, 3 and 4 failures, each row giving the number of tries, the waits and whether `PushFailed` is raised.

    Interface corrected, under the human's leave in entry 14 (answer 1), with the module from entry 9 (answer 1). I added to the `PushFailed` bullet that `push_reason(output)` in `factory.domain.git` builds the reason. It first leaves out git's advice lines (the two exact lines, and lines starting with `hint:`), then takes the last three.

    Open for the human (criterion 5, as entry 11 reports): a crash is charged at the next tick for a stage in which no agent ran. The test pins this as xfail, and the fix is not part of this story.

    Earlier tests:
    - `tests/application/test_dispatcher.py`: the human's leave, entry 14 answer 4. Only the four named tests are changed, and only by the `handler error ` filter.
    - `tests/application/test_git_interface.py`: the human's leave, entry 14 answer 3 (renamed to twenty-two).
    - `tests/application/test_interfaces.py`: the human's leave, entry 14 answer 3 (renamed to twenty-two).
    - `tests/git_interface_support.py`: the human's leave, entry 14 answer 3. `OPERATIONS` is the name list that only those two tests read.
    - `tests/test_checkout_hygiene_removed.py`: the human's leave, entry 14 answer 3 (the count is 22, the row id `git-twenty-two`).
23. factory: started doing as vm.
24. coder: Round 1: both of the reviewer's findings in entry 22 are changes to tests the tester wrote for this story, and no code needs to change for either. I changed no code and no test, and I am handing over to the tester.

    Test changes for the tester, as entry 22 states them:
    1. `tests/application/test_hosting_failure_after_claim.py`: the asserts after the first tick (the claim was pushed, and `agent_runtime.requests() == []`) must not sit under the `xfail(strict=True)` mark. They belong in a test that passes, or in a fixture that test shares with the xfail test. Keep only the next-tick asserts (a journal `crash` entry, and `crashes == 0`) under `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")`.
    2. `tests/application/test_push_retry.py`: merge `test_a_push_refused_twice_is_pushed_on_the_third_try_without_a_crash` and `test_a_push_refused_four_times_raises_push_failed_after_three_retries` into one test, parametrized over 2, 3 and 4 refusals. Each row gives the number of tries, the waits (5/15, 5/15/45, 5/15/45) and whether `PushFailed` is raised. The new boundary row is: refused three times, pushed on the fourth try, with no crash. Both `case` variants (`result` and `record`) stay.

    The code already handles the three-refusal row as the Interface says (`src/factory/application/pushes.py`), so neither change should need new code.

    What the code is: unchanged since entry 20, when `make check` was green.

    What the journal changed: the reviewer added the advice-line sentence to the Interface's `PushFailed` bullet, under the human's leave. I left the Description as it is.

    Open for the human: criterion 5 is still the xfail case. A crash is charged at the next tick for a stage in which no agent ran. The fix is not part of this story.
25. factory: started tests as vm.
26. tester: Mode: a test change the human approved. I made the two test changes the coder's entry 24 names, which come from the reviewer's findings in entry 22. Both are changes to tests this story wrote. I changed no code and no earlier story's test.

    1. `tests/application/test_hosting_failure_after_claim.py`: the setup is now the fixture `failed_after_claim`. It makes `create_pull_request` fail next and runs the first tick. The asserts after that first tick now sit in a passing test, `test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run`. They check that the claim was pushed and that `agent_runtime.requests() == []`. Only the next-tick asserts (no journal `crash` entry, `crashes == 0`) stay under `xfail(strict=True, reason="a crash is charged for a stage in which no agent ran")` in `test_a_hosting_failure_after_the_claim_charges_no_crash_at_the_next_tick`. The fixture requests `work_item` only so that the story exists before the tick, and drops it with `del` so that ruff's ARG001 passes.
    2. `tests/application/test_push_retry.py`: I merged `test_a_push_refused_twice_is_pushed_on_the_third_try_without_a_crash` and `test_a_push_refused_four_times_raises_push_failed_after_three_retries` into one test, `test_a_refused_push_is_retried_at_most_three_times`. It is parametrized over three rows:
       - `refused-twice`: 3 tries, waits of 5 and 15 s, pushed, `crashes == 0`.
       - `refused-three-times` (the new boundary row): 4 tries, waits of 5, 15 and 45 s, pushed, `crashes == 0`.
       - `refused-four-times`: 4 tries, waits of 5, 15 and 45 s, `PushFailed` naming `[remote rejected]`.

       Each row also checks the number of retry lines. Both `case` variants (`result` and `record`) stay, through the existing fixture.

    Mapping changes:
    - Criterion 5: `test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run` (passes), plus the strict xfail test above.
    - The retry-cap criterion: `tests/application/test_push_retry.py::test_a_refused_push_is_retried_at_most_three_times`.

    Results:
    - The one run of both files (`uv run pytest -q`) gave all passed and one xfailed.
    - After that run I added the one-line `del work_item` for lint. I did not run the tests again.
    - `make lint`: green.
    - No files were created, and every module was imported.

    `lint`: lint: green (0.2 s)
27. factory: started doing as vm.
28. coder: Round 1, after the tester's changes in entry 26. I changed no code and no test this round. On this round's run, `make check` was green (`check: green`, total coverage 99.41 %). The tester's changes from entry 26 are both in and pass: the passing `test_a_hosting_failure_after_the_claim_leaves_the_claim_pushed_and_no_agent_run` with its strict xfail partner, and the parametrized `test_a_refused_push_is_retried_at_most_three_times` with the `refused-three-times` boundary row. The code already handled that row (`src/factory/application/pushes.py`).

    What I built (unchanged since entry 20):
    - `src/factory/domain/git.py`: `push_reason` and `push_is_retried`.
    - `src/factory/domain/errors.py`: `PushFailed` now carries a `reason`.
    - `src/factory/application/pushes.py`: `push_with_retries` and `push_failure`.
    - The retried pushes, in `StageFinisher._commit_and_push` (`stage.py`) and `WorkItemRecorder.publish` (`handlers/recording.py`).
    - `Git.last_push_output` in `src/factory/application/git.py` and `src/factory/adapters/git_cli.py`.
    - `handler_error_line` in `src/factory/domain/tick_status.py`, used by `Dispatcher._count`.
    - `hosting_retry()` in `src/factory/adapters/pygithub_hosting.py`.

    Main choice (as in entry 20): git's reason crosses the `Git` interface through a separate `last_push_output()` operation. I rejected a `PushResult` return DTO from `push`, because it would have changed many tests.

    Refactor step: nothing new to refactor; the diff is the same as at entry 20.

    What the journal changed: entry 22 added the advice-line sentence to the Interface's `PushFailed` bullet. The meaning is the same, so I did not rewrite the Description.

    Open for the human: criterion 5 is the xfail case. At the next tick a crash is charged for a stage in which no agent ran. The fix is not part of this story.

    Noticed, not touched: `make duplicates` reported 3 new findings in round 0 (entry 20). They are vulture's warnings on unused variables in `src/factory/domain/cost_records.py:41-43`, a file outside this story.

    `check`: check: green
    `duplicates`: duplicates: 3 new, 43 known, 0 gone
29. factory: started review as vm.
