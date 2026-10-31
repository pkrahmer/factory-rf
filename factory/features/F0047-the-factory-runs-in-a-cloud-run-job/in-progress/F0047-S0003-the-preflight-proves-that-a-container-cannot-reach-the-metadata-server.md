---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 483
comments_read: [6546695740]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-10-31T18:01:07.511873Z'
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
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-31T17:23:57.194376Z'
  stage: intake
  run: 4382554ee5fe488ca2afae75663a2544
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-31T17:24:17.599492Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-31T17:31:19.063802Z'
  stage: tests
  run: d0414a3684fb40298df660e9b79fbfd8
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-31T17:31:39.714982Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-31T17:38:46.276058Z'
  stage: doing
  run: 1eea099a19e745f1a87be056e4e15889
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-31T17:39:08.390504Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-31T17:39:49.228456Z'
  stage: review
  run: 62346ef7291c44aca11a76bea9b03fa8
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-31T17:40:09.694246Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-31T17:43:41.938323Z'
  stage: doing
  run: c1d331cf1791456ab4445cb9334f8b40
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-31T17:44:04.568982Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-31T17:54:14.691292Z'
  stage: tests
  run: a07d9adb7337478aa59a2b3d7284674b
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-31T17:54:35.272780Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-31T18:00:45.107401Z'
  stage: doing
  run: 4e0051d1c8d241198c75dcdeb321eff7
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-31T18:01:07.511873Z'
  stage: review
---

# The preflight proves that a container cannot reach the metadata server

## Description

In a Cloud Run job the agent's container shares the job's network, and the metadata server at `169.254.169.254` answers any process there with the job's service-account token (measured on 2026-10-31, `planning/cloud-sandbox/`, P2b: reachable from host-network and bridge containers, by address and by name). A firewall rule that rejects TCP port 80 to that address stops it, without breaking DNS, the proxy or anything the factory needs. This story makes the factory prove that the rule is in force: with the container profile `job` the preflight gains the item `metadata-block`, which runs one container that asks the metadata server for the instance id and passes only when the connection is refused or times out. A machine that fails it stops, like any failed preflight item. Unchanged: the preflight's other items, every profile other than `job`, and the rule itself (the start script installs it, S0006). Left to later stories: the start script (S0006).

## Interface

`factory.domain.containers` (domain): `METADATA_PROBE_URL = "http://169.254.169.254/computeMetadata/v1/instance/id"` and `METADATA_PROBE_COMMAND: tuple[str, ...]` = `("curl", "-sS", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}", METADATA_PROBE_URL)`.

`factory.application.preflight` (application): `def metadata_block_item(probe: Callable[[], ContainerResult]) -> PreflightItem`, the item `metadata-block`. `probe` runs `METADATA_PROBE_COMMAND` in one container and returns its `ContainerResult`; the item reads the last non-blank line of `result.output`, stripped:

- `000` (curl could not connect, whatever its exit status): passes, detail `refused`.
- Any other three digits: fails with `a container reached the metadata server (HTTP <code>); reject tcp port 80 to 169.254.169.254 in the job's firewall`.
- A result with `timed_out` true, whatever its output (this rule is checked first): fails with `the metadata probe did not end within its limit`.
- No such line (the program is missing, the exit status 127, an empty output): fails with `the metadata probe could not tell (exit <status>): <the last line or "no output">`.
- `probe` raising `ContainerError`: fails with `cannot run the metadata probe: <error>`.

`factory.entry.wiring` (entry): for the profile `job`, `_container_items` adds `lambda: metadata_block_item(...)`, which runs the command through `containers.run(list(METADATA_PROBE_COMMAND), mounts=[], environment={}, time_limit=timedelta(seconds=30), working_directory=WORK)`, after the `stage-image` item and before the agent-run probe; for `rootless` no such item.

Tests (the tester writes them): `tests/application/test_preflight_metadata_block.py`, `tests/entry/test_wiring_metadata_block.py` (the container fakes of the suite).

## Acceptance criteria

1. With the profile `rootless` (the default) the preflight's items are those of before this story, none named `metadata-block`.
2. With the profile `job` the items hold `metadata-block` right after `stage-image` and before `agent-run-probe`, and the run's command words are exactly `METADATA_PROBE_COMMAND`, with no mounts and an empty environment, a time limit of 30 seconds and the working directory `WORK`.
3. `metadata_block_item`, rows of one parametrized test: the output `000` with exit status 7 passes with the detail `refused`; `000` with exit status 28 passes; the output `200` fails with the sentence naming HTTP 200; `404` fails with HTTP 404; `000` printed after an earlier line `x` passes (the last line counts); an empty output with exit status 127 fails with `could not tell (exit 127): no output`; the output `curl: not found` with exit status 127 fails with that line in the sentence; a result with `timed_out` fails with the sentence about the limit; a result with `timed_out` and the output `000` fails with the same sentence; the output `"000\n\n"` passes; the output `" 000 "` passes (stripped); the output `2000` with exit status 0 fails with `could not tell (exit 0): 2000`.
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
6. intake: accepted
   - Interface: concrete. `factory.domain.containers` constants, `factory.application.preflight.metadata_block_item(probe)` with five outcomes, and the `factory.entry.wiring` change are all named with their exact sentences. I carried in journal entry 4 (the human's answer to question 3): the timed-out rule is now stated to win whatever the output (checked first).
   - Criteria: each is testable by one test function. Every Interface rule has both sides: `000` passes; HTTP codes fail; `timed_out` fails; no line fails; `ContainerError` fails. From entry 4, criterion 2 now also pins the 30-second limit and the working directory `WORK`. Criterion 3 gained rows for `timed_out` with `000`, `"000\n\n"`, `" 000 "` and `2000` (exit 0, "could not tell"). The `rootless` default has criterion 1, the stop through `Preflight.run` has criterion 5, and the docs criterion is last.
   - Smoke test: the command is runnable. Its `Expect:` line gives two exact lines, `True` and the HTTP 200 sentence, which the output can be checked against. It runs no pytest, so the `-q` rule does not apply.
   - Architecture: the constants are in domain, the item is in application, and only entry wiring picks the container run. That matches the layering, and the probe goes through `containers.run`, so no new tool is called.
   - Scope: it is inside F0047's scope ("preflight item `metadata-block` for the job profile"). The start script and the rule's installation are left to S0006, as `feature.md` says. It does not touch anything under "Out of scope".
7. factory: started tests as vm.
8. tester: Wrote the tests from the Interface and the acceptance criteria. There is one test per criterion. Criterion 3 is a single parametrized test whose rows are the ones the criterion lists.

   - criterion 1: tests/entry/test_wiring_metadata_block.py::test_the_metadata_block_item_runs_after_the_stage_image_with_the_job_profile_alone, rows `default` and `rootless`. The items must be `CONTAINER_ITEMS` plus `agent-run-probe`, with no `metadata-block`.
   - criterion 2, item order: the same test, row `job`. `metadata-block` must come right after `stage-image` and before `agent-run-probe`.
   - criterion 2, run arguments: tests/entry/test_wiring_metadata_block.py::test_the_metadata_probe_runs_its_command_alone_for_30_seconds_in_work. It reads the one `podman run` call that the suite's stand-in podman records. The words after the image must be exactly `METADATA_PROBE_COMMAND`. There must be no `--env`. There must be one `--volume` only, the workspace volume that every run gets; this is what "no mounts" means here. `--timeout` must be `30` and `--workdir` must be `WORK`.
   - criterion 3: tests/application/test_preflight_metadata_block.py::test_the_metadata_block_item_passes_only_when_the_probe_could_not_connect, with the 12 rows of the criterion in its order. Each row asserts the item's name, whether it passed and its detail. The two `000` rows with exit 7 and exit 28 also assert the detail `refused`, which the Interface gives for `000`.
   - criterion 4: tests/application/test_preflight_metadata_block.py::test_a_probe_that_cannot_run_fails_the_metadata_block_item
   - criterion 5: tests/application/test_preflight_metadata_block.py::test_a_failed_metadata_block_item_stops_the_machine. It runs the preflight rig's `Preflight.run`, where every other item passes, plus a `metadata-block` item whose probe answers `200`. The run must return `preflight_failed`, there must be exactly one machine stop, with the detail `metadata-block: <the HTTP 200 sentence>`, and no project command may run.
   - criteria 6 and 7 (`make check` and docs): no tests.

   Files created: tests/application/test_preflight_metadata_block.py and tests/entry/test_wiring_metadata_block.py. No earlier test file changed.

   `make test`: both new modules fail to collect with an ImportError. `metadata_block_item` does not exist yet in `factory.application.preflight`, nor `METADATA_PROBE_COMMAND` in `factory.domain.containers`. `make lint` is green.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/entry/test_wiring_metadata_block.py - ImportError while importing test module '/work/checkout/tests/entry/test_wiring_metadata_block.py'.
9. factory: started doing as vm.
10. coder: Added the `metadata-block` preflight item for the container profile `job`. `make check` is green; the tester's two modules pass, and the smoke test prints `True` and then the HTTP 200 sentence.

    - `src/factory/domain/containers.py`: adds `METADATA_PROBE_URL` and `METADATA_PROBE_COMMAND`, as the Interface gives them.
    - `src/factory/application/preflight.py`: adds `metadata_block_item(probe)`. A `ContainerError` from the probe gives `cannot run the metadata probe: <error>`. The remaining rules live in `_metadata_fault`, in this order:
      - `timed_out` comes first, whatever the output.
      - Then the last non-blank line, stripped (`_last_line`): `000` passes with the detail `refused`.
      - Any other three digits (`[0-9]{3}`, full match) fail with the HTTP sentence.
      - Anything else, or no line at all, fails with `could not tell (exit <status>): <line or "no output">`.
    - `src/factory/entry/wiring.py`: `_container_items` adds the item after `stage-image` only when `settings.container_profile == "job"`. The run goes through `_metadata_probe(containers)`: `containers.run(list(METADATA_PROBE_COMMAND), mounts=[], environment={}, time_limit=_METADATA_PROBE_TIME_LIMIT (30 s), working_directory=WORK)`. `machine_extras` still appends `agent-run-probe` after it, so that order is unchanged.

    Main choice: the item takes a bare `Callable[[], ContainerResult]`, as the Interface says, and the wiring holds the run's arguments. The rejected alternative was passing the `Containers` interface into the application function and letting it build the call. That would have put the time limit and working directory in the application layer and broken the `stage_image_item(image, exists)` pattern the other container items follow. I also kept the three-digit test as a regex full match rather than `str.isdigit`, which accepts non-ASCII digits.

    Refactor pass: I read the diff and found nothing to change.

    Noticed but did not touch:
    - `_metadata_probe` is typed with the concrete `PodmanRuns`, because `_ContainerAdapters.containers` is typed that way already.
    - The journal changed nothing in the Description's meaning beyond what intake already carried in.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 41 known, 0 gone
11. factory: started review as vm.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` against the work item. Checks 1 to 3 pass. Acceptance criteria: criteria 1 to 5 each have a test that checks what it is named after, and criterion 3's twelve rows are rows of one parametrized test. Every rule in the Interface has its failing side tested: the HTTP codes, `timed_out`, a missing line, `2000` and `ContainerError`. The coder's entry 10 reports `make check` green. Architecture: the constants are in domain, the item is in application and the run's arguments are in entry wiring. Security: nothing to report. Check 4, Quality, fails: four second copies of existing helpers.

    1. src/factory/application/preflight.py:234 `_last_line`: its comprehension `[line.strip() for line in output.splitlines() if line.strip()]` is a second copy of `printed_lines` in src/factory/adapters/printed_output.py:7. The application layer cannot import adapters. Fix: move `printed_lines` down to a domain module, have `factory.adapters.printed_output` and `metadata_block_item` both use it, and drop the copy.
    2. tests/entry/test_wiring_metadata_block.py:16-40: the `environment` fixture and `_settings` are copies of the ones in tests/entry/test_wiring_container_extras.py:15-41; the fixture is also in tests/entry/test_wiring_copy_snapshots.py:26-29. Fix: the tester moves them to `tests/wiring_support.py` (or the fixture to a conftest) under the standing leave and uses them from there.
    3. tests/entry/test_wiring_metadata_block.py:96-97: `[words] = [... if "run" in call.arguments]` and `words[words.index(IMAGE) + 1 :]` redo `run_words` and `after_image` of tests/wiring_support.py:85-93. Fix: use those two helpers.
    4. tests/entry/test_wiring_metadata_block.py:77 `_value_of` is a copy of `_after` in tests/adapters/test_claude_runtime_container.py:79. Fix: the tester moves it to a shared support module under the standing leave and both tests use it.

    Group 5 (work item hygiene) was not reached.

    Earlier tests: none. Both test files the diff touches are new (`A`), and no test file `main` already holds was changed.
13. factory: started doing as vm.
14. coder: Round 1. I fixed review finding 1, the only one in the code. Findings 2 to 4 are changes to tests, so they go to the tester. `make check` is green.

    Finding 1, the second copy of `printed_lines`:
    - New file `src/factory/domain/printed_lines.py` holds `printed_lines(output)`. It moved there unchanged from `factory.adapters.printed_output`.
    - `src/factory/adapters/printed_output.py` now imports it from the domain module. Its `first_printed_line` and `failure_detail` are unchanged. No other module or test imported `printed_lines` from the adapter.
    - In `src/factory/application/preflight.py`, `_last_line` now calls `printed_lines` and the copied comprehension is gone.

    Main choice: a new small domain module named after the helper. The alternative I rejected was putting `printed_lines` in `factory.domain.containers`. The adapters also use it on output from plain processes and zfs, not only on container results, so it would have been in the wrong module there.

    Tests for the tester, from the reviewer's entry 12. I touched none of them.
    - Finding 2: move the `environment` fixture and `_settings` from `tests/entry/test_wiring_metadata_block.py` and `tests/entry/test_wiring_container_extras.py` to one shared place: `tests/wiring_support.py` for `_settings`, and the fixture there or in a conftest. This falls under the standing leave. `tests/entry/test_wiring_copy_snapshots.py` also holds a copy of the `environment` fixture and should use the shared one.
    - Finding 3: `tests/entry/test_wiring_metadata_block.py` should use `run_words` and `after_image` from `tests/wiring_support.py` instead of redoing them on lines 96-97.
    - Finding 4: move `_value_of` (`tests/entry/test_wiring_metadata_block.py:77`) and its copy `_after` (`tests/adapters/test_claude_runtime_container.py:79`) to one shared support module, and have both tests use it. This falls under the standing leave.

    Refactor pass: I read the diff and found nothing more to change. The journal changed nothing in the Description.

    Noticed but did not touch: `_metadata_probe` in the wiring is still typed with the concrete `PodmanRuns`, as in round 0.

    `check`: check: green
15. factory: started tests as vm.
16. tester: Round 1. I made the test changes the coder's entry 14 handed on from review findings 2 to 4, under the standing leave to move a shared test helper (CLAUDE.md, *Tests*). Every earlier test keeps its name and checks the same thing. No criterion changed, so the mapping is the one in entry 8.

    - criterion 1: tests/entry/test_wiring_metadata_block.py::test_the_metadata_block_item_runs_after_the_stage_image_with_the_job_profile_alone, rows `default` and `rootless`.
    - criterion 2: the same test, row `job`, and tests/entry/test_wiring_metadata_block.py::test_the_metadata_probe_runs_its_command_alone_for_30_seconds_in_work.
    - criterion 3: tests/application/test_preflight_metadata_block.py::test_the_metadata_block_item_passes_only_when_the_probe_could_not_connect
    - criterion 4: tests/application/test_preflight_metadata_block.py::test_a_probe_that_cannot_run_fails_the_metadata_block_item
    - criterion 5: tests/application/test_preflight_metadata_block.py::test_a_failed_metadata_block_item_stops_the_machine

    Finding 2, the `environment` fixture and `_settings`:
    - The three copies of the fixture are now one fixture in `tests/conftest.py`. It is named `run_environment` because `tests/conftest.py` already has a different fixture called `environment`.
    - `_settings` is now `profile_settings` in `tests/wiring_support.py`.
    - The three modules now use the shared fixture, and the metadata-block and container-extras modules use `profile_settings`. Their local copies are gone.

    Finding 3, `run_words` and `after_image`:
    - The probe test now uses `after_image`.
    - It does not use `run_words`. That helper only finds a call whose first word is `run`, and under the `job` profile podman puts its global options before `run`. With `run_words` the test failed with `ValueError: not enough values to unpack (expected 1, got 0)`.
    - So the test still picks the call that holds `run`, with a comment saying why. I did not change `run_words`: four earlier tests use it, and widening it goes beyond moving a helper.

    Finding 4, `_value_of` and `_after`: both are gone. They are replaced by `value_after` in the new `tests/command_words_support.py`, which both the probe test and `tests/adapters/test_claude_runtime_container.py` now use.

    Files:
    - Created: `tests/command_words_support.py`.
    - Earlier test files changed under the standing leave: `tests/conftest.py`, `tests/wiring_support.py`, `tests/entry/test_wiring_container_extras.py`, `tests/entry/test_wiring_copy_snapshots.py`, `tests/adapters/test_claude_runtime_container.py`.
    - Also changed: this story's own `tests/entry/test_wiring_metadata_block.py`.

    Every module imported; none failed to import. `make test` is green, and so are `make lint` and `make types`.

    `lint`: lint: green (0.2 s)
    `test`: test: green (163.6 s)
17. factory: started doing as vm.
18. coder: Round 1, after the tester's entry 16. The tester made the test changes for review findings 2 to 4. My only fix, for finding 1, was already in the tree from entry 14. This round I changed no code. I ran `make check` on the tree as it now stands, with the moved shared helpers, and it is green.

    What the story built:
    - `src/factory/domain/containers.py`: `METADATA_PROBE_URL` and `METADATA_PROBE_COMMAND`.
    - `src/factory/domain/printed_lines.py`: `printed_lines`, moved down from `factory.adapters.printed_output`, which now imports it. This answers finding 1.
    - `src/factory/application/preflight.py`: `metadata_block_item`, `_metadata_fault` and `_last_line`. `timed_out` is checked first, then `000` passes, then three digits fail, then "could not tell".
    - `src/factory/entry/wiring.py`: the item runs with the `job` profile only, after `stage-image`, through `containers.run(list(METADATA_PROBE_COMMAND), mounts=[], environment={}, time_limit=30 s, working_directory=WORK)`.

    Main choice: the item takes a bare `Callable[[], ContainerResult]` and the wiring holds the run's arguments. This is the same pattern as `stage_image_item`. The rejected alternative was handing the `Containers` interface to the application function. That would have put the time limit and the working directory in the application layer.

    Refactor pass: I read the source diff again and found nothing to change.

    The journal changed nothing in the Description.

    Noticed but did not touch:
    - `_metadata_probe` in the wiring is typed with the concrete `PodmanRuns`, because `_ContainerAdapters.containers` is typed that way already.
    - In entry 16 the tester reported that `run_words` in `tests/wiring_support.py` finds only a call whose first word is `run`. It therefore misses the `job` profile's calls, where podman's global options come before `run`. Widening it would be a test change for another story.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 41 known, 0 gone
19. factory: started review as vm.
