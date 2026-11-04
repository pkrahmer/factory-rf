---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 540
comments_read: [6630647682]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-04T12:32:48.233812Z'
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
---

# A refused push or hosting call is retried and logged

## Description

GitHub's partial outage of 2026-11-04 (about 09:36 to 10:05 UTC) was analysed in `planning/outage-2026-11-04.md`. The factory held up: no stop, nothing half-written on the remote, F0050-S0001 finished. But two things went wrong, and neither could be read from what the factory kept. First, the docs stage of S0001 finished its run and its checks at 09:36:46, and the push of its result most likely failed once; one failed push discards a finished run, charges a crash and runs the paid agent again, and the first run's cost record is lost with it (19 runs recorded, 20 ran). Second, the hand-over failed three times in about 90 s, reached the handler's error cap and was never tried again, and its first two errors were logged nowhere. This story makes a short outage cheap and visible. Every handler error the factory counts gets a log line; a refused or unreachable push of a stage's result or of a recorded change is tried again after 5, 15 and 45 s before it fails as today; the push error keeps git's own reason; and the GitHub client retries with a backoff, writes included. A test pins what happens when the hosting service fails after a stage's claim, which the analysis found untested. The cap of three tries stays (the human, 2026-11-04).

## Interface

- `Dispatcher._count` (or wherever a handler error is counted) writes one log line per counted error: `handler error <event key> <n> of <cap>: <exception type>: <text>`, the text on one line and at most 300 characters. Nothing else about the counting or the cap changes.
- The push of a stage's result (`StageFinisher._commit_and_push`) and of a recorded change (`WorkItemRecorder.publish`), on a push that is refused or cannot reach the remote, waits 5, 15 and 45 s and pushes again, then raises `PushFailed` as today. Each retry writes `push: retry <n> of 3 in <s> s: <reason>`. No force, no rebase, no new commit between the tries. The waits go through the factory's clock or sleeper interface, so the tests wait no real time.
- `PushFailed` carries git's reason: the last non-empty lines of git's output (at most three, at most 300 characters), in its message and so in every report and log line that names it.
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
