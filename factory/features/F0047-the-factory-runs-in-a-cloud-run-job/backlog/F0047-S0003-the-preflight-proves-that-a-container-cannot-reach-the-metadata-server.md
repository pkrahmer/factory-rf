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
