---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-04T12:23:35.918605Z'
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
---

# A refused push or hosting call is retried and logged

## Description

GitHub's partial outage of 2026-11-04 (about 09:36 to 10:05 UTC) was analysed in `planning/outage-2026-11-04.md`. The factory held up: no stop, nothing half-written on the remote, F0050-S0001 finished. But two things went wrong, and neither could be read from what the factory kept. First, the docs stage of S0001 finished its run and its checks at 09:36:46, and the push of its result most likely failed once; one failed push discards a finished run, charges a crash and runs the paid agent again, and the first run's cost record is lost with it (19 runs recorded, 20 ran). Second, the hand-over failed three times in about 90 s, reached the handler's error cap and was never tried again, and its first two errors were logged nowhere. This story makes a short outage cheap and visible. Every handler error the factory counts gets a log line; a refused or unreachable push of a stage's result or of a recorded change is tried again after 5, 15 and 45 s before it fails as today; the push error keeps git's own reason; and the GitHub client retries with a backoff, writes included. A test pins what happens when the hosting service fails after a stage's claim, which the analysis found untested. The cap of three tries stays (the human, 2026-11-04).

## Interface

- `Dispatcher._count` (or wherever a handler error is counted) writes one log line per counted error: `handler error <event key> <n> of <cap>: <exception type>: <text>`, the text on one line and at most 300 characters. Nothing else about the counting or the cap changes.
- The push of a stage's result (`StageFinisher._commit_and_push`) and of a recorded change (`WorkItemRecorder.publish`), on a push that is refused or cannot reach the remote, waits 5, 15 and 45 s and pushes again, then raises `PushFailed` as today. Each retry writes `push: retry <n> of 3 in <s> s: <reason>`. No force, no rebase, no new commit between the tries. The waits go through the factory's clock or sleeper interface, so the tests wait no real time.
- `PushFailed` carries git's reason: the last non-empty lines of git's output (at most three, at most 300 characters), in its message and so in every report and log line that names it.
- The PyGithub client is created with a retry that backs off and covers `PATCH` as well as the default methods: `GithubRetry(total=5, backoff_factor=2, allowed_methods=<the default methods plus PATCH>)` or its equivalent in the installed version, in the one place the client is built.
- A test of what happens when the hosting service fails after a stage's claim (in `ensure_pull_request`, called at the stage's start): it pins today's behaviour. If that behaviour charges a crash for a stage in which no agent ran, the test is marked with `pytest.mark.xfail(strict=True, reason=...)` naming that, and the story's entry names it for the human; the fix is not part of this story.

## Acceptance criteria

1. A handler error that is counted writes its line with the event key, the count, the cap, the type and the text; rows: the first, the second and the third (capped) error of one event; a text with a line break is written on one line; a text over 300 characters is cut.
2. A result push that fails twice and then passes is pushed on the third try, writes two retry lines, raises nothing and charges no crash; one that fails four times raises `PushFailed` after the three retries. The same two rows for `WorkItemRecorder.publish`. The test's clock shows waits of 5, 15 and 45 s, and the test takes no real time.
3. `PushFailed`'s message holds git's last lines: rows for a server error (`remote: Internal Server Error` with `! [remote rejected]`), a non-fast-forward rejection, and an unreachable remote.
4. The hosting client is built with a retry whose total is 5, whose backoff factor is 2, and whose allowed methods include `PATCH` and every default method.
5. The test of a hosting failure after the claim exists and pins the behaviour, as the Interface says.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`: in the section on stops and errors, the handler error line, that a refused push is retried after 5, 15 and 45 s, that the reason in a push error is git's own, and what the factory does during a hosting outage (today's evidence in short). `docs/decisions.md`: one entry with the reason (the outage of 2026-11-04 and `planning/outage-2026-11-04.md`), and that the cap of three tries stays. `README.md`: none. The project guide: the file on the hosting service names the client's retry.

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
