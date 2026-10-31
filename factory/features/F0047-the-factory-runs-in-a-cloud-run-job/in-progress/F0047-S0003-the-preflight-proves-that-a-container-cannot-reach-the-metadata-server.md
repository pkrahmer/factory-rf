---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 483
comments_read: [6546695740]
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-10-31T17:23:37.944619Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T17:21:44.392339Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T17:21:44.398244Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-31T17:22:02.819322Z'
  stage: intake
  run: 3cebf8e1450a496c8a9940f30504d019
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-31T17:23:20.247240Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-31T17:23:37.944619Z'
  stage: intake
---

# The preflight proves that a container cannot reach the metadata server

## Description

In a Cloud Run job the agent's container shares the job's network, and the metadata server at `169.254.169.254` answers any process there with the job's service-account token (measured on 2026-10-31, `planning/cloud-sandbox/`, P2b: reachable from host-network and bridge containers, by address and by name). A firewall rule that rejects TCP port 80 to that address stops it, without breaking DNS, the proxy or anything the factory needs. This story makes the factory prove that the rule is in force: with the container profile `job` the preflight gains the item `metadata-block`, which runs one container that asks the metadata server for the instance id and passes only when the connection is refused or times out. A machine that fails it stops, like any failed preflight item. Unchanged: the preflight's other items, every profile other than `job`, and the rule itself (the start script installs it, S0006). Left to later stories: the start script (S0006).

## Interface

`factory.domain.containers` (domain): `METADATA_PROBE_URL = "http://169.254.169.254/computeMetadata/v1/instance/id"` and `METADATA_PROBE_COMMAND: tuple[str, ...]` = `("curl", "-sS", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}", METADATA_PROBE_URL)`.

`factory.application.preflight` (application): `def metadata_block_item(probe: Callable[[], ContainerResult]) -> PreflightItem`, the item `metadata-block`. `probe` runs `METADATA_PROBE_COMMAND` in one container and returns its `ContainerResult`; the item reads the last non-blank line of `result.output`, stripped:

- `000` (curl could not connect, whatever its exit status): passes, detail `refused`.
- Any other three digits: fails with `a container reached the metadata server (HTTP <code>); reject tcp port 80 to 169.254.169.254 in the job's firewall`.
- A result with `timed_out` true: fails with `the metadata probe did not end within its limit`.
- No such line (the program is missing, the exit status 127, an empty output): fails with `the metadata probe could not tell (exit <status>): <the last line or "no output">`.
- `probe` raising `ContainerError`: fails with `cannot run the metadata probe: <error>`.

`factory.entry.wiring` (entry): for the profile `job`, `_container_items` adds `lambda: metadata_block_item(...)`, which runs the command through `containers.run(list(METADATA_PROBE_COMMAND), mounts=[], environment={}, time_limit=timedelta(seconds=30), working_directory=WORK)`, after the `stage-image` item and before the agent-run probe; for `rootless` no such item.

Tests (the tester writes them): `tests/application/test_preflight_metadata_block.py`, `tests/entry/test_wiring_metadata_block.py` (the container fakes of the suite).

## Acceptance criteria

1. With the profile `rootless` (the default) the preflight's items are those of before this story, none named `metadata-block`.
2. With the profile `job` the items hold `metadata-block` right after `stage-image` and before `agent-run-probe`, and the run's command words are exactly `METADATA_PROBE_COMMAND`, with no mounts and an empty environment.
3. `metadata_block_item`, rows of one parametrized test: the output `000` with exit status 7 passes with the detail `refused`; `000` with exit status 28 passes; the output `200` fails with the sentence naming HTTP 200; `404` fails with HTTP 404; `000` printed after an earlier line `x` passes (the last line counts); an empty output with exit status 127 fails with `could not tell (exit 127): no output`; the output `curl: not found` with exit status 127 fails with that line in the sentence; a result with `timed_out` fails with the sentence about the limit.
4. A probe that raises `ContainerError("curl", "no such image")` fails with `cannot run the metadata probe: container command curl failed: no such image`.
5. A failed `metadata-block` item makes the preflight's report fail and stops the machine through the existing path (a test through `Preflight.run` with the other items passing).
6. `make check` stays green.
7. docs: `docs/operator-guide.md`: a subsection *The metadata server* under the job profile: why a container must not reach it, the rule (`ip daddr 169.254.169.254 tcp dport 80 reject` in the output and forward hooks, as a file loaded with `nft -f`, with the warning that a chain called `fwd` is a reserved word), the preflight item with its sentences, and what to do when it fails. The preflight's item table gains the row. `docs/project-guide/stage-environment.md`: *The preflight* names the item. `docs/decisions.md`: an entry *A container must not reach the metadata server*, from the feature's decision 6. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from datetime import timedelta
from factory.application.preflight import metadata_block_item
from factory.domain.containers import ContainerResult
def result(output, status):
    return ContainerResult(exit_status=status, output=output, timed_out=False, duration=timedelta(seconds=1))
print(metadata_block_item(lambda: result('000', 7)).passed)
print(metadata_block_item(lambda: result('200', 0)).detail)
"
```
Expect: two lines, `True` and `a container reached the metadata server (HTTP 200); reject tcp port 80 to 169.254.169.254 in the job's firewall`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-31 human: created.
2. factory: started intake as vm.
3. intake: 1. The Interface says the wiring runs the probe with `time_limit=timedelta(seconds=30)` and `working_directory=WORK`. No criterion tests either value. Criterion 2 covers only the command words, the empty mounts and the empty environment. Two coders could read it two ways and both would pass. Should criterion 2 also say the run's time limit is 30 seconds and its working directory is `WORK`? I would add both to criterion 2.

   2. The Interface does not say which rule wins when the result has `timed_out` true and its output also ends in `000` or another line. The rows in criterion 3 test `timed_out` only with no usable line. A coder can check `timed_out` first or the output first, and both pass. Should a timed-out result always fail with the limit sentence, whatever its output? I would say yes, and add a criterion row for `timed_out` true with output `000`.

   3. The Interface says the item reads the last non-blank line, stripped. No row has trailing blank lines or surrounding whitespace, for example `"000\n\n"` or `" 000 "`. Both are clauses of the rule. Should a row cover them? I would add the row `"000\n\n"` passes.

   4. A last line of more than three digits, such as `0000` or `2000`, is neither "three digits" nor an absent line. By the Interface it goes to the "could not tell" case. No criterion pins that. Should one row cover it? I would add `2000` failing with `could not tell (exit 0): 2000`.

   The format check passed. The architecture and the feature's scope are fine.
4. 2026-10-31 human: Answers to question 3: all four as you propose.

   1. Yes: criterion 2 also says the run's time limit is 30 seconds and its working directory is `WORK`.
   2. Yes: a timed-out result always fails with the limit sentence, whatever its output; add the row `timed_out` true with output `000`.
   3. Yes: add the row `"000\n\n"` passes, and `" 000 "` passes (stripped).
   4. Yes: add the row `2000` failing with `could not tell (exit 0): 2000`.
5. factory: started intake as vm.
