---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 527
comments_read: [6618558222, 6618632675, 6618725845, 6619198883, 6619524143]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-04T01:02:35.267881Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T23:52:12.848233Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T23:52:12.855066Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T23:52:33.832065Z'
  stage: intake
  run: 76f3189141154e57a61fe7479ee00c1e
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T23:56:27.530203Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T23:56:30.646180Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T23:56:58.507346Z'
  stage: intake
  run: d207184f90bf4141ab234c6c193c1052
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T23:57:04.224086Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-03T23:58:17.694225Z'
  stage: tests
  run: 01045af6e9324417bb58f82f1c5b86d6
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-04T00:00:06.668718Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T00:00:11.897268Z'
  stage: tests
- number: 11
  speaker: tester
  kind: question
  at: '2026-11-04T00:04:24.865472Z'
  stage: tests
  run: d1038cfc2d8b4df0bf0d1699c2787433
  blocked: question
- number: 12
  speaker: human
  kind: comment
  at: '2026-11-04T00:06:15.669914Z'
  stage: tests
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-04T00:06:18.816139Z'
  stage: tests
- number: 14
  speaker: tester
  kind: result
  at: '2026-11-04T00:07:18.538182Z'
  stage: tests
  run: ba77bab12fc14b3faddf7b9ab2bd503c
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-04T00:07:24.560888Z'
  stage: doing
- number: 16
  speaker: coder
  kind: question
  at: '2026-11-04T00:33:13.741272Z'
  stage: doing
  run: fe3fd47351a1473493e56e92e5eec49c
  blocked: question
- number: 17
  speaker: human
  kind: comment
  at: '2026-11-04T00:35:04.705357Z'
  stage: doing
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-04T00:35:07.993162Z'
  stage: doing
- number: 19
  speaker: coder
  kind: result
  at: '2026-11-04T00:35:40.035603Z'
  stage: doing
  run: 6fb5fc86e4a44e4f85082c1d3bff8b53
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-04T00:35:45.703890Z'
  stage: tests
- number: 21
  speaker: tester
  kind: result
  at: '2026-11-04T00:37:15.629667Z'
  stage: tests
  run: 251a94c64a0945659ae4ba1191f09a32
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-04T00:37:21.109075Z'
  stage: doing
- number: 23
  speaker: coder
  kind: result
  at: '2026-11-04T00:43:23.439863Z'
  stage: doing
  run: 0acb3a2c2ae14aa99160b3213f03dfff
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-04T00:43:29.541919Z'
  stage: review
- number: 25
  speaker: reviewer
  kind: result
  at: '2026-11-04T00:47:16.032608Z'
  stage: review
  run: 2cd6dc3f306c44d4bb24fafa38b4cc34
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-04T00:47:21.859637Z'
  stage: doing
- number: 27
  speaker: coder
  kind: question
  at: '2026-11-04T00:54:37.649204Z'
  stage: doing
  run: 8467255f2391468d8614b8dd87ceff7b
  blocked: question
- number: 28
  speaker: human
  kind: comment
  at: '2026-11-04T00:55:24.223122Z'
  stage: doing
- number: 29
  speaker: factory
  kind: started
  at: '2026-11-04T00:55:29.263113Z'
  stage: doing
- number: 30
  speaker: coder
  kind: result
  at: '2026-11-04T00:57:38.718384Z'
  stage: doing
  run: 064b9405a6a34dd3b54fd7bf5334eb19
- number: 31
  speaker: factory
  kind: started
  at: '2026-11-04T00:57:44.296000Z'
  stage: tests
- number: 32
  speaker: tester
  kind: result
  at: '2026-11-04T01:02:29.584940Z'
  stage: tests
  run: c7c6ecf863734796b2372c728549a1f1
- number: 33
  speaker: factory
  kind: started
  at: '2026-11-04T01:02:35.267881Z'
  stage: doing
---

# A project's stage file builds the image its stages run in

## Description

Every container of an instance (the sync, the agent, the checks) runs in the stage image the operator built from `vm/Dockerfile`, named by `FACTORY_STAGE_IMAGE` and identified by the file `FACTORY_IMAGE_ID_FILE`. A project that needs a compiler, a JDK or a browser has no way to add it but to change that image for every project. This story lets a project add its own layer. When `factory-run` starts, before the preflight, it reads `factory/stage.Containerfile` from the project's `origin/main`. Without the file, nothing changes: every container runs in the base image under the base's identity. With it, the factory checks the file's rule, builds it on top of the base with an empty build context, and tags the result as the project image. From then on every container of the instance runs in the project image, with the image's own `PATH`, and the instance's image identity, which keys the preflight's stamps and the reuse of a passed check, becomes the base's identity joined with the file's hash. So the preflight, its agent-run probe included, runs again on a new layer and confirms that the layer left the agent runtime working. A file that breaks the rule or does not build is a stop with its reason, and the factory starts no stage while it stands. A change of the file on `main` after the start is S0003's.

## Interface

- The rule (`factory.domain`, a module of its own or `factory.domain.containers`): `stage_layer(text: str, base_identity: str) -> StageLayer`, raising a refusal with the reason for a file that breaks it. `StageLayer` (a frozen Pydantic model) holds the file's text, its `digest` (the first 12 hex digits of its SHA-256) and `identity`, `f"{base_identity}+{digest}"`.
  - Before its one `FROM`, the file may hold only blank lines, comments and the line `ARG FACTORY_BASE`.
  - It holds exactly one `FROM` instruction (case-insensitive), and that is `FROM ${FACTORY_BASE}` or `FROM $FACTORY_BASE`, with nothing after the image name (no `AS`, no `--platform`).
  - It is at most 64 KiB of UTF-8.
  - The template, which the first criterion accepts, is these three lines: `ARG FACTORY_BASE`, `FROM ${FACTORY_BASE}`, and `RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake && rm -rf /var/lib/apt/lists/*`.
- The constant `STAGE_FILE = "factory/stage.Containerfile"` and the project image's tag, `f"{FACTORY_STAGE_IMAGE}-project"` (for example `factory-stage:vm-project`), each defined once.
- An interface in `factory.application` for the images, with one podman implementation in `factory.adapters` (podman is reached only through its wrapper, R5) and one fake:
  - `build(layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild`: builds `layer.text` with `--build-arg FACTORY_BASE=<base>`, `--network=host` and with an empty context directory, tags it `tag`, and removes images left without a tag after it. `ImageBuild` holds `passed`, `duration` and `output_tail` (the build's last 20 lines).
  - `path(image: str) -> str`: the `PATH` the image's configuration sets (podman's `image inspect`), or the base's default `/usr/local/bin:/usr/bin:/bin` when it sets none.
  - The build's time limit is 30 minutes, one constant.
- The project image is named in one place of the wiring: the image every container run takes, and the identity the preflight and the check reuse take. The sync environment's, the check environment's and the agent environment's `PATH` are built from `path(<the image in use>)` (the agent's with its scripts folder first), in place of the fixed `/usr/local/bin:/usr/bin:/bin`. Rows of earlier tests that pin that `PATH` change under the feature's leave.
- A new `RepositoryStopReason`, `stage_image_failed`, whose detail is the rule's reason or `the stage file did not build in <s> s:` followed by `output_tail`. While it stands no stage starts; `factory-health` shows it as it shows the other stops (`factory-watch` shows no stop of any reason, and that stays so). It ends with the next start of `factory-run` (and, after S0003, with a new `main`).

## Acceptance criteria

1. `stage_layer` accepts and refuses by its rule; rows: the template of the Interface (accepted, with its digest and identity); `FROM ${FACTORY_BASE}` alone; `from $FACTORY_BASE` in lower case; a comment and a blank line before `ARG FACTORY_BASE`; refused, each with its own reason: `FROM debian:bookworm`, `FROM ${FACTORY_BASE} AS build`, `FROM --platform=linux/amd64 ${FACTORY_BASE}`, a second `FROM`, no `FROM`, a `RUN` before the `FROM`, `ARG OTHER` before the `FROM`, a file of 64 KiB (accepted) and of 64 KiB and one byte (refused), and bytes that are not UTF-8.
2. Two files that differ in one byte have different digests, and the same file has the same digest and identity at every call; the identity is `<base identity>+<12 hex digits>`.
3. A start whose `origin/main` holds no stage file builds nothing, and every container run takes the base image with the base's identity, exactly as before this story.
4. A start whose `origin/main` holds a valid stage file builds it once, with the base image as `FACTORY_BASE` and the tag `<FACTORY_STAGE_IMAGE>-project`, before the preflight runs; every following container run (sync, agent, check) takes the project image, and the preflight's stamps and the check reuse take the layer's identity.
5. The containers' `PATH` is the image's: a fake image whose `PATH` is `/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin` gives the sync environment and the check environment that `PATH` and the agent environment its scripts folder followed by it; an image that sets none gives `/usr/local/bin:/usr/bin:/bin`.
6. A stage file that breaks the rule, and one whose build fails or reaches its time limit, each stand as the stop `stage_image_failed` with its detail as the Interface states, and no stage starts while it stands; the base image is not used in its place.
7. The podman adapter's build passes `--build-arg FACTORY_BASE=<base>`, `--network=host`, `-t <tag>` and an empty context directory, and after a build runs the removal of untagged images; its `path` reads the image's configured `PATH`. Tested through the argument lists and a stand-in for `podman`, without a real container.
8. The podman adapter's `output_tail`: a build that prints 25 lines gives the last 20 lines in order; one that prints 5 lines gives all 5.
9. The podman adapter's build that reaches its time limit gives `passed=False` (a short limit through a stand-in `podman`, with `ROOMY_LIMIT` as `CLAUDE.md` states), and the wiring passes the one 30-minute constant to `build`.
10. The podman adapter's `path`: inspect output with a `PATH` gives that `PATH`; inspect output without one gives `/usr/local/bin:/usr/bin:/bin`.
11. After a `stage_image_failed` stop, the next start of `factory-run` with a valid stage file, and one with no stage file, each holds no such stop.
12. `factory-health` shows `stage_image_failed` as a stop: a row `stage_image_failed` in `test_every_stop_reason_makes_the_check_fail_until_it_is_cleared` (`tests/entry/test_health.py`).
13. The podman adapter's `path` raises `ContainerError` when `image inspect` exits non-zero and when it prints no JSON; `build_boundaries` given images whose `path` raises gives the sync, the check and the agent `/usr/local/bin:/usr/bin:/bin`.
14. The podman adapter in the `job` container profile puts the job's global podman options before `build`, `image prune -f` and `image inspect`; in the `rootless` profile it puts none.
15. `make check` stays green.
16. docs: `docs/operator-guide.md`: a section *The project's stage file*: what `factory/stage.Containerfile` is, its rule, an example that adds `build-essential` and `cmake`, that only `main` counts, that the build has the network and no files of the repository so the project pins its own versions and checksums, that the sync, the checks and the agent take the `PATH` the image sets (so a tool the layer puts on its `PATH` is found by `make check`), where the project image and its identity show, and the stop `stage_image_failed` and what to do about it. The project guide: `stage-environment.md` names the images interface, its fake and the one place where the image in use is chosen. `docs/decisions.md`: one entry with feature decisions 1, 3 and 4 and their reasons. `README.md`: one sentence that a project can add tools to its stage image with that file.

## Smoke test

```bash
grep -rlE 'def stage_layer\(' src/factory/domain | wc -l
grep -rlF '"factory/stage.Containerfile"' src/factory | wc -l
grep -rhoE '"stage_image_failed"' src/factory/domain | sort -u
```

Expect: `1`, `1`, then the single line `"stage_image_failed"`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: The format check passed. Behaviours the Interface or Description states have no criterion yet, and two coders would read them differently:
   1. `ImageBuild.output_tail` is "the build's last 20 lines". No criterion tests it: neither a build with more than 20 lines of output, nor one with fewer. I suggest adding a criterion to the podman adapter's tests (7) or to the stop's detail (6).
   2. "The build's time limit is 30 minutes, one constant" has no criterion. Nothing checks that `build` gets 30 minutes from the wiring, and nothing checks that reaching the limit gives `passed=False`. Criterion 6 names the time limit only as a stop, without saying how the limit is detected. I suggest saying which side tests this: the adapter, or the stop through the fake.
   3. `path(image)` falls back to `/usr/local/bin:/usr/bin:/bin` when the image sets no `PATH`. Criterion 5 tests that only through a fake image. Criterion 7 says only that the podman adapter "reads the configured PATH". Please add the adapter's case where the inspect output has no `PATH`, and a case where it has one.
   4. Criterion 7 does not cover "rootless" in `build`. Please either add it to the adapter's argument list or drop it from the Interface.
   5. "It ends with the next start of `factory-run`" has no criterion. A stop that stands after a failed build and is gone after a start with a valid file or no file is behaviour that needs a test.
   6. "`factory-health` and `factory-watch` show it as they show the other stops" has no criterion. Please add one row per command, or say that the existing generic rendering of `RepositoryStopReason` already covers it, and name the test.
   7. Criterion 1 says "each with its own reason", but the reasons' texts are not stated. I suggest the test checks only that the refusal is raised and that the reasons differ across rows. Please confirm, or give the texts.
   8. Criterion 6 puts three different failures into one criterion: a rule break, a failed build and a time limit. The detail text differs between the rule break and the build failure (`the stage file did not build in <s> s:` plus the tail). Please state whether these are separate rows, and whether the time limit's detail is the same text as a failed build's.

   I would choose to add one criterion for each of items 1 to 3, 5 and 6, and to confirm 4 and 7 as described.
4. 2026-11-03 human: Answers, as you recommend:
   1. Add a criterion for the adapter: a build that prints 25 lines gives an output_tail of its last 20 lines in order, and one that prints 5 lines gives all 5.
   2. Add a criterion: the adapter's build that reaches its time limit gives passed=False (tested with a short limit through a stand-in podman, by the ROOMY rules of CLAUDE.md), and the wiring passes the one 30-minute constant to build.
   3. Add the adapter's two rows: inspect output with a PATH gives that PATH; without one gives /usr/local/bin:/usr/bin:/bin.
   4. Drop "rootless" from the Interface: the factory's podman is rootless already, and build adds no flag for it.
   5. Add a criterion: after a stage_image_failed stop, the next start of factory-run with a valid file, or with no file, holds no such stop.
   6. If an existing test already renders every RepositoryStopReason generically in factory-health and factory-watch, name it in your entry and add a row for stage_image_failed to it; otherwise one row per command.
   7. Confirmed: the test checks that each row is refused and that the reasons differ between rows; no fixed texts.
   8. Separate rows: the rule break, the failed build and the time limit. The time limit's detail uses the same text as a failed build ("the stage file did not build in <s> s:" and the tail).
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete. `stage_layer(text, base_identity) -> StageLayer` in `factory.domain`, with the rule, digest and identity stated. `STAGE_FILE` and the project tag are each defined once. The images interface has `build` and `path` with their DTO, one podman adapter and one fake. The stop reason `stage_image_failed` has its detail text. "Rootless" is dropped from `build`, from journal entry 4 item 4.
   - Criteria: each is testable by one test function. Every Interface rule has a criterion for both sides: the accepted and refused rows of 1, the digest in 2, no file and a valid file in 3 and 4, a stop for a rule break, a failed build and a time limit in 6 (separate rows, same detail text for the last two per entry 4 item 8). I wrote the human's answers from entry 4 into the story: new criteria 8 (`output_tail` with 25 and with 5 lines), 9 (the adapter's time limit gives `passed=False`; the wiring passes the 30-minute constant), 10 (`path` with and without a PATH in the inspect output), 11 (the stop ends with the next start, valid file or no file), 12 (`factory-health` row) and 13 (`factory-watch`). `make check` and `docs:` are now 14 and 15. Criterion 1 checks that each row is refused and that the reasons differ, not their texts (entry 4 item 7).
   - Existing tests, from entry 4 item 6: `tests/entry/test_health.py::test_every_stop_reason_makes_the_check_fail_until_it_is_cleared` is parametrized over stop reasons, so criterion 12 adds a `stage_image_failed` row to it. `tests/entry/test_watch.py` has no generic test of every stop reason, so criterion 13 is a test of its own for `factory-watch`.
   - Smoke test: the three grep commands are runnable and do not run pytest. Each Expect line (`1`, `1`, the single line `"stage_image_failed"`) is checkable.
   - Architecture: the rule is in domain, the images interface is in application, and podman is reached only through its adapter wrapper, which matches the layers and R5. The wiring is in one place. The earlier `PATH` tests change under the feature's leave for S0002.
   - Scope: within F0049's S0002 scope. Rebuilding on a changed `main` is left to S0003, and nothing in the story touches the feature's out-of-scope items.
7. factory: started tests as vm.
8. tester: I stopped before writing any test. The Interface leaves out names and seams that every criterion's test has to import or call, so any test I wrote now would fix my own guesses as the coder's specification. I read the work item, `docs/project-guide/stage-environment.md` (podman adapter, settings and wiring, preflight), `src/factory/entry/run.py`, the names in `src/factory/entry/wiring.py` and `src/factory/domain/stops.py`, and `tests/entry/test_health.py::test_every_stop_reason_makes_the_check_fail_until_it_is_cleared`. No files were created and `make test` was not run.

   Please answer each point below, or accept the choice I would make:

   1. **Where `stage_layer` lives and what it raises (criteria 1, 2).** The Interface says "a module of its own or `factory.domain.containers`" and "a refusal". I would choose `factory.domain.stage_layer`, with `StageLayer`, `STAGE_FILE` and the exception `StageLayerRefused(ValueError)` whose `str()` is the reason. The other option is `factory.domain.containers` with the same names.

   2. **The images interface, its DTO, adapter and fake (criteria 4 to 10).** There are no module or class names, and no constructor for the podman adapter. I would choose:
      - `factory.application.images`: `Images(ABC)` with `build` and `path`, `ImageBuild(passed: bool, duration: timedelta, output_tail: str)` with the lines joined by `\n`, and `IMAGE_BUILD_TIME_LIMIT = timedelta(minutes=30)`.
      - `factory.adapters.podman_images`: `PodmanImages(executable: str)`, running `<executable> build ...` and then `<executable> image prune -f` for the untagged images, and `<executable> image inspect --format '{{json .Config.Env}}' <image>` for `path`.
      - `factory.adapters.fake_images`: `FakeImages(paths: dict[str, str] = {}, build_result: ImageBuild | None = None)`, which records its `build` calls in a `builds` list.
      - `project_image_tag(stage_image: str) -> str` in `factory.domain.stage_layer`.

      Please confirm or correct each name, the prune command and the inspect format. The adapter test pins those exact arguments.

   3. **The seam of the start (criteria 3, 4, 5, 6, 9, 11).** These tests need to call the start with a fake `Images`, then read the image the container runs take, the identity, the `PATH`s and the stop. The Interface says only "one place of the wiring". I would choose:
      - a function in `factory.entry.wiring`, `project_image_settings(settings, git, images, stops) -> InstanceSettings | None`. It reads `STAGE_FILE` from `origin/main` through the `Git` wrapper. It returns the settings with `stage_image` and `image` replaced (the project tag and the layer's identity), or unchanged when there is no file. It raises or clears `stage_image_failed` through `StopService`, and returns `None` while the stop stands.
      - `run_instance` gains `images: Images | None = None` (podman by default) and calls that function before `build_tick`. With `None`, it runs no tick and leaves the stop in the health file, so that "no stage starts" can be checked.
      - the sync and agent `PATH`s come from `stage_environment_of(boundaries)` and `agent_environment(...)`, given `images.path(<image in use>)`.

      If you have another seam in mind (a field on `Boundaries`, a step in `RepositoryWaiter.prepare`), please name it.

   4. **The scope of `stage_image_failed`.** `_require_scope_of_reason` refuses a stop whose scope is not its reason's. The health row (criterion 12) builds its scope from `("preflight_failed", "disk_low")`, so a machine-scoped reason means that line of the earlier test must change. I would choose `machine`, because the image is the instance's, as with `preflight_failed`. The row then needs `stage_image_failed` added to that tuple, and I would make that change under criterion 12. The other option is `repository`, which needs only the new row.

   5. **The "different reasons" of criterion 1.** I will check that the 12 refused rows give pairwise distinct `str()` reasons, as entry 4, item 7 says. The 64 KiB rows: is "64 KiB" measured as 65536 bytes of the UTF-8 encoding of `text`? `text` is a `str`, so how should the "bytes that are not UTF-8" row reach `stage_layer`? I would choose 65536 encoded bytes. For the non-UTF-8 row I would test the start's reading of the file (a stage file on `main` holding `b"\xff"` gives `stage_image_failed`), not `stage_layer`. The other option is to make `stage_layer` take `bytes`.

   Once these are answered I will write all thirteen tests in one run.
9. 2026-11-04 human: All five as you would choose:
   1. factory.domain.stage_layer with StageLayer, STAGE_FILE and StageLayerRefused(ValueError), its str() the reason.
   2. Your names, as listed: factory.application.images (Images, ImageBuild with output_tail joined by \n, IMAGE_BUILD_TIME_LIMIT), factory.adapters.podman_images (PodmanImages(executable), build, then image prune -f, and image inspect --format '{{json .Config.Env}}'), factory.adapters.fake_images (FakeImages with builds), project_image_tag in factory.domain.stage_layer.
   3. Your seam: project_image_settings in factory.entry.wiring, run_instance gains images (podman by default) and runs no tick while the stop stands; the PATHs from images.path of the image in use.
   4. machine scope, as preflight_failed. Leave (feature decision 7): you may add stage_image_failed to the tuple of machine-scoped reasons in tests/entry/test_health.py for criterion 12, and nothing else in that module.
   5. 65536 bytes of the UTF-8 encoding; the non-UTF-8 row is tested at the start's reading of the file (b"\xff" on main gives stage_image_failed), not in stage_layer.
10. factory: started tests as vm.
11. tester: I wrote the tests for criteria 1–4, 6–9, 11 and 12. I stopped before criteria 5 and 13: the answers so far don't give either one a seam or an expected output, and any test I wrote now would fix my own guess as the coder's specification.

    Mapping so far:
    - criterion 1: tests/domain/test_stage_layer.py::test_a_stage_file_within_the_rule_is_accepted (template, FROM alone, lower case, comment and blank line, 64 KiB) and ::test_a_stage_file_that_breaks_the_rule_is_refused (debian, AS, --platform, second FROM, no FROM, RUN before, ARG OTHER before, 64 KiB + 1). The refusal reasons are checked to differ in ::test_each_broken_rule_gives_its_own_reason. The two padded files are checked to be 65536 and 65537 bytes in ::test_the_padded_files_lie_on_both_sides_of_64_kib. The bytes that are not UTF-8 are tested at the start (criterion 6), as entry 9, item 5 says.
    - criterion 2: tests/domain/test_stage_layer.py::test_the_digest_follows_every_byte_and_the_identity_is_stable. `STAGE_FILE` and `project_image_tag` are checked in ::test_the_stage_file_and_the_project_image_tag_are_named_once.
    - criterion 3: tests/entry/test_wiring_project_image.py::test_a_start_without_a_stage_file_builds_nothing_and_keeps_the_base
    - criterion 4: tests/entry/test_wiring_project_image.py::test_a_start_with_a_valid_stage_file_builds_it_once_and_takes_the_project_image. It checks the build's base, tag and time limit, and that the returned settings carry `stage_image` = the project tag and `image` = the layer's identity.
    - criterion 6: tests/entry/test_wiring_project_image.py::test_a_stage_file_that_does_not_build_stands_as_a_stop (rows failed and time-limit), ::test_a_stage_file_that_breaks_the_rule_stands_as_a_stop_and_builds_nothing (rows rule and not-utf-8, `b"\xff"` on main), and ::test_no_stage_starts_while_the_stage_image_stop_stands (run_instance with `images=`: only the stop stands, one build).
    - criterion 7: tests/adapters/test_podman_images.py::test_the_build_passes_the_base_the_network_the_tag_and_an_empty_context. It uses a stand-in podman that records the arguments and what the last argument's folder holds. It checks that `image prune -f` comes after the build.
    - criterion 8: tests/adapters/test_podman_images.py::test_the_output_tail_is_the_last_twenty_lines_in_order (rows 25 and 5). A failed build gives passed=False in ::test_a_build_that_fails_has_not_passed.
    - criterion 9: tests/adapters/test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed (ROOMY_LIMIT, ROOMY_BOUND_SECONDS). The 30-minute constant is checked in tests/entry/test_wiring_project_image.py::test_the_build_time_limit_is_thirty_minutes, and that the wiring passes it, in criterion 4's test.
    - criterion 10: tests/adapters/test_podman_images.py::test_path_is_the_images_configured_path_or_the_base_default (rows with-path and without-path; the inspect arguments are pinned as in entry 9).
    - criterion 11: tests/entry/test_wiring_project_image.py::test_the_next_start_ends_a_stage_image_stop (rows valid and none)
    - criterion 12: the row `stage_image_failed` in tests/entry/test_health.py::test_every_stop_reason_makes_the_check_fail_until_it_is_cleared. I also added the reason to the tuple of machine-scoped reasons there, under the leave of entry 9, item 4. Nothing else in that module changed; ruff format split the scope line over several lines.
    - criteria 5 and 13: not written; see the questions below.

    Files created: tests/domain/test_stage_layer.py, tests/adapters/test_podman_images.py, tests/entry/test_wiring_project_image.py. Changed: tests/entry/test_health.py (one row and the tuple). The wiring tests use a recording `Images` subclass of their own rather than `FakeImages`, because the shape of `FakeImages.builds` was never fixed.

    The run `uv run pytest -q <those files>` stopped with collection errors only: ModuleNotFoundError for `factory.domain.stage_layer`, `factory.adapters.podman_images` and `factory.application.images`. `project_image_settings` and run_instance's `images` keyword don't exist yet either. Because collection stopped, the new health row was not run. `make lint` is green.

    Questions:
    1. **Criterion 5: where the image's `PATH` enters.** Entry 9 says "the PATHs from images.path of the image in use", but no function takes that path. Today `SYNC_ENVIRONMENT` is a constant in `factory.application.stage_environment`, and `agent_environment(scripts, home)` adds the fixed `_SYSTEM_PATH`. Options:
       (a) `build_boundaries(settings, token, *, hosting=None, images=None)` sets a new field `Boundaries.image_path: str` (default `/usr/local/bin:/usr/bin:/bin`) from `images.path(settings.stage_image)`. `stage_environment_of(boundaries)` gives the sync run `{"PATH": boundaries.image_path, "HOME": WORK_HOME}`, and `agent_environment(scripts, home, path)` gains a third parameter that the handler wiring fills from `boundaries.image_path`. The test builds boundaries with `FakeImages(paths={IMAGE: "/opt/jdk/bin:..."})`, runs a sync through `FakeContainerRuns` and reads the PATH of the recorded call, then calls `agent_environment` with that path.
       (b) Only the explicit parameters: `stage_environment_of(boundaries, path)` and `agent_environment(scripts, home, path)`, with the caller in the wiring choosing the path. This tests the joining but not the wiring.
       I would choose (a).
    2. **Criterion 13: what factory-watch prints for a stop.** `factory-watch` shows no stop of any reason today. `run_watch` writes the event line and the board, and neither `Watcher` nor `BoardReader` reads the health status. So "as it shows the other stops" gives the test nothing to expect. Options:
       (a) Drop criterion 13: watch shows no stop, and `stage_image_failed` is no exception.
       (b) New behaviour: `run_watch` prints each standing stop as `factory-health` does (`<reason> (<scope>): <detail> (since <at>)`) before the event line. That would show every reason, which goes beyond this story.
       I would choose (a).

    Once these are answered I'll write the remaining tests and end with `doing`.
12. 2026-11-04 human: 1. (a): Boundaries.image_path from images.path(settings.stage_image), default /usr/local/bin:/usr/bin:/bin; stage_environment_of(boundaries) and agent_environment(scripts, home, path) take it, as you describe.
    2. (a): drop criterion 13; factory-watch shows no stop of any reason today, and that stays so in this story.
13. factory: started tests as vm.
14. tester: I wrote the last missing test, for criterion 5, as entry 12 answered. I dropped criterion 13 from the description as the human decided, so `make check` and `docs:` are now criteria 13 and 14. The Interface now says that only `factory-health` shows the stop.

    Mapping:
    - criterion 1: tests/domain/test_stage_layer.py::test_a_stage_file_within_the_rule_is_accepted, ::test_a_stage_file_that_breaks_the_rule_is_refused, ::test_each_broken_rule_gives_its_own_reason, ::test_the_padded_files_lie_on_both_sides_of_64_kib. The bytes that are not UTF-8 are tested at the start, under criterion 6.
    - criterion 2: tests/domain/test_stage_layer.py::test_the_digest_follows_every_byte_and_the_identity_is_stable. `STAGE_FILE` and `project_image_tag` are checked in ::test_the_stage_file_and_the_project_image_tag_are_named_once.
    - criterion 3: tests/entry/test_wiring_project_image.py::test_a_start_without_a_stage_file_builds_nothing_and_keeps_the_base
    - criterion 4: tests/entry/test_wiring_project_image.py::test_a_start_with_a_valid_stage_file_builds_it_once_and_takes_the_project_image
    - criterion 5: tests/entry/test_wiring_image_path.py::test_the_sync_and_the_agent_take_the_path_of_the_image_in_use. It has two rows: an image whose `PATH` is `/opt/jdk/bin:…`, and an image that sets none. It builds the boundaries with `images=FakeImages(paths=…)` and checks `Boundaries.image_path`, the `PATH` of the sync's `podman run` (recorded by a stand-in podman), and `agent_environment(scripts, home, boundaries.image_path)`.
    - criterion 6: tests/entry/test_wiring_project_image.py::test_a_stage_file_that_does_not_build_stands_as_a_stop (rows failed and time-limit), ::test_a_stage_file_that_breaks_the_rule_stands_as_a_stop_and_builds_nothing (rows rule and not-utf-8), ::test_no_stage_starts_while_the_stage_image_stop_stands
    - criterion 7: tests/adapters/test_podman_images.py::test_the_build_passes_the_base_the_network_the_tag_and_an_empty_context. A failed build gives passed=False in ::test_a_build_that_fails_has_not_passed.
    - criterion 8: tests/adapters/test_podman_images.py::test_the_output_tail_is_the_last_twenty_lines_in_order (rows 25 and 5)
    - criterion 9: tests/adapters/test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed checks the time limit. tests/entry/test_wiring_project_image.py::test_the_build_time_limit_is_thirty_minutes checks the constant. That the wiring passes it to `build` is checked in criterion 4's test.
    - criterion 10: tests/adapters/test_podman_images.py::test_path_is_the_images_configured_path_or_the_base_default
    - criterion 11: tests/entry/test_wiring_project_image.py::test_the_next_start_ends_a_stage_image_stop (rows valid and none)
    - criterion 12: the row `stage_image_failed` in tests/entry/test_health.py::test_every_stop_reason_makes_the_check_fail_until_it_is_cleared, plus the reason in that module's tuple of machine-scoped reasons (entry 9, item 4)

    Files created in this round: tests/entry/test_wiring_image_path.py. Earlier rounds created tests/domain/test_stage_layer.py, tests/adapters/test_podman_images.py and tests/entry/test_wiring_project_image.py.

    Earlier test files changed:
    - tests/entry/test_health.py (earlier round, under the leave in entry 9).
    - tests/entry/test_wiring_handlers.py::test_the_agent_environment_is_a_path_led_by_the_scripts_and_a_home: its call now passes `"/usr/local/bin:/usr/bin:/bin"` as the new third argument of `agent_environment`. I changed it under the Interface's leave, which says that rows of earlier tests that pin that `PATH` change. The test still checks the same thing.

    Run: `uv run pytest -q` over the new and changed files stopped with 4 collection errors. The modules the run could not import are `factory.domain.stage_layer`, `factory.application.images`, `factory.adapters.podman_images` and `factory.adapters.fake_images`. `project_image_settings`, run_instance's `images` keyword, build_boundaries' `images` keyword, `Boundaries.image_path` and `agent_environment`'s third parameter don't exist yet either. Because collection stopped, the test_health.py row and the changed test_wiring_handlers.py call were not run. `make lint` is green.

    The factory left out changes outside the write paths: factory/features/F0049-the-project-shapes-its-stage-image/in-progress/F0049-S0002-a-projects-stage-file-builds-its-image.md.

    `lint`: lint: green (0.1 s)
15. factory: started doing as vm.
16. coder: I built the whole story, and every test for it passes. `make check` is red only in four earlier test files. Each pins something this story must change, and I may not edit tests. So I stopped here. My changes are in the working tree.

    Built:
    - `src/factory/domain/stage_layer.py`: `STAGE_FILE`, `StageLayer`, `StageLayerRefused`, `project_image_tag`, `stage_layer`. The rule checks size first, then the U+FFFD that `show_file`'s decoding leaves for bytes that are not UTF-8, then the FROM count, the lines before the FROM, and the FROM's form. Each reason names the line it refuses.
    - `src/factory/application/images.py`: `Images`, `ImageBuild`, `IMAGE_BUILD_TIME_LIMIT`.
    - `src/factory/adapters/podman_images.py`: `PodmanImages`, with a keyword `profile` for the job's global options. Fake: `src/factory/adapters/fake_images.py`.
    - `run_podman` in `src/factory/adapters/podman_runs.py`, built on `run_or_raise`. Two existing tests forbid any other route: `test_wrapper_search` (only the listed wrappers import `process`) and `test_run_or_raise` (no second request builder in `podman_runs`).
    - `SYSTEM_PATH` in `factory.domain.containers`. `Boundaries.image_path` uses it as its default. The sync's `PATH` comes from `boundaries.image_path`. `agent_environment` and `production_environment` take a `path` argument, and `build_tick` passes `boundaries.image_path`.
    - `src/factory/entry/wiring.py`: `project_image_settings`, `with_image_path`, `build_images`, and `build_boundaries(..., images=)`.
    - The reason `stage_image_failed`, machine-scoped, in `src/factory/domain/stops.py`, with a row in `src/factory/domain/stop_table.py`. The contract schemas are regenerated at `RECORDS_CONTRACT = "4.1"`.

    Main choice: in `src/factory/entry/run.py`, `_ProjectImageStart` builds the one tick on the first iteration whose `RepositoryWaiter.prepare` succeeds. That iteration fetches, decides the image, builds the boundaries again on the chosen settings, then applies `with_image_path`. After a failure, no iteration runs again until the next start. I rejected building the image before the loop: the checkout may not exist yet at the start, and the repository-unavailable stop already handles that. `run_instance` takes `hosting` and `images` through `**replacements: Unpack[Replacements]` because ruff's `PLR0913` refuses a sixth argument, and existing callers keep their keywords. The second build calls `build_boundaries` without `images`, because the conftest fixture `on_the_manual_clock` patches it with the old signature.

    Questions. Each needs a test change by the tester; my choice is (a) each time:
    1. `tests/test_second_user_removed.py`, row `build-boundaries-parameters`, pins `build_boundaries`' parameters to exactly `["settings", "token", "hosting"]`. `tests/entry/test_wiring_image_path.py` (entry 12's answer) calls it with `images=`. (a) Add `"images"` to that row. (b) Drop `images` from `build_boundaries` and have the image-path test call `with_image_path(build_boundaries(...), FakeImages(...))`.
    2. The stop table. `tests/domain/test_stop_table.py::test_every_repository_stop_reason_is_the_reason_of_exactly_one_row` requires a row for the new reason, so I added `stage-image-failed` (limit `L55`, as `preflight-failed`) after `disk-low`. Two tests then fail. `::test_the_table_holds_the_fifteen_stops_in_order` pins 15 rows. `tests/test_stop_table.py:89` derives the scope from `("preflight_failed", "disk_low")`. (a) The tester adds the sixteenth row to the first test and `stage_image_failed` to that tuple, as entry 9 allowed for `test_health.py`. Please also confirm `L55` or name the right limit.
    3. The records contract. `RepositoryStopReason` is in `stop-record.schema.json`, and `docs/decisions.md` raises the minor version for an added value, so I set 4.1. `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` and `tests/domain/test_contract_version_4.py::test_the_records_contract_is_at_version_4_without_left_branch` pin `"4.0"`. (a) The tester changes those pins to `"4.1"`. (b) Keep 4.0 against the rule; then I revert `contract.py` and regenerate.

    Noticed, not touched:
    - The check containers keep the fixed `PATH` (`CHECK_ENVIRONMENT`). The Interface names only the sync and the agent, and passing a `path` into `ContainerMakeCommands` would need the patched `build_boundaries` signature. A project that adds a JDK will not find `java` in its checks. That is likely a story of its own.
    - A build that reaches its time limit loses its output: `run_or_raise` raises, so the stop's detail holds podman's no-end text instead of the tail.
    - When the image cannot be inspected, `with_image_path` falls back to `SYSTEM_PATH` and leaves the report to the preflight's stage-image item.
    - When the base identity is unknown (`settings.image` is `None`), the project settings keep `image=None`, so no preflight stamp is reused.

    The tester's edit to the Description (criterion 13 dropped) was left out by the factory, so the Description still lists the watch criterion.

    Refactor step: not done yet, because `make check` is not green.
17. 2026-11-04 human: 1. (a): add "images" to the build-boundaries-parameters row of tests/test_second_user_removed.py.
    2. (a): the sixteenth row in tests/domain/test_stop_table.py and stage_image_failed in the scope tuple of tests/test_stop_table.py; L55 as preflight-failed is right.
    3. (a): the records contract goes to 4.1 by the rule; the tester changes the two pins in tests/domain/test_contract.py and tests/domain/test_contract_version_4.py to "4.1".
    These leaves are feature decision 8: only those rows, pins and tuples in those modules.
    4. The checks' PATH is part of this story, not a later one: the check containers take boundaries.image_path too, in place of the fixed CHECK_ENVIRONMENT PATH, because make check is where a project's tools must be found. Criterion 5 gains a row for the check environment (the tester writes it); the existing rows that pin the checks' PATH change under the feature's S0002 leave (tests/adapters/test_make_commands_container.py and the others it names). If the patched build_boundaries in conftest stands in the way, the tester may adapt that fixture's stand-in to the new signature, and nothing else in tests/conftest.py (also decision 8).
    The other notes stay as they are (the time-limit tail, the inspect fallback, image=None).
18. factory: started doing as vm.
19. coder: I changed no code and no tests this round. The human's answer in entry 17 asks for test changes before the work can continue, so this goes to the tester. The code from my earlier run is already committed on the branch, with `make check` red only in the pinned rows below.

    Test changes for the tester (feature decision 8, entry 17):
    1. `tests/test_second_user_removed.py`, row `build-boundaries-parameters`: add `"images"`, which gives `["settings", "token", "hosting", "images"]`.
    2. `tests/domain/test_stop_table.py::test_the_table_holds_the_fifteen_stops_in_order`: add the sixteenth row `stage-image-failed` (limit `L55`, after `disk-low`). In `tests/test_stop_table.py`, near line 89, add `stage_image_failed` to the machine-scoped tuple `("preflight_failed", "disk_low")`.
    3. In `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` and `tests/domain/test_contract_version_4.py::test_the_records_contract_is_at_version_4_without_left_branch`, change the pins from `"4.0"` to `"4.1"`.
    4. Criterion 5 gets a new row for the check environment: the check containers take `boundaries.image_path` in place of the fixed `PATH` in `CHECK_ENVIRONMENT`. The rows that pin the checks' `PATH` change under the S0002 leave: `tests/application/test_container_environment_extra.py` (the two `check` rows that expect `CHECK_ENVIRONMENT`) and any others in `tests/adapters/test_make_commands_container.py`. The seam I would choose: `ContainerMakeCommands(..., path: str = SYSTEM_PATH)` as a new keyword, so the check's environment becomes `{**extra, **CHECK_ENVIRONMENT, "PATH": path}`. `build_boundaries` would read the image's path once before it builds the commands and pass it to both `ContainerMakeCommands` and `Boundaries.image_path`. The other option is a mutable path that `with_image_path` sets afterwards; I rejected it because the adapters stay immutable.
    5. The `on_the_manual_clock` fixture in `tests/conftest.py`: give its stand-in `built` the new signature, `images: Images | None = None` passed through to `original(settings, token, hosting=hosting, images=images)`. Then `src/factory/entry/run.py` can call `build_boundaries(..., images=...)` on the second build instead of patching the path in afterwards with `with_image_path`. Nothing else in that file changes.

    What I noticed but did not touch: the Description still lists the watch criterion that entry 12 dropped, because the factory left out the tester's edit to it. The tester can rewrite it while making these changes.

    After the tester's changes, my plan for the next round is to add the check's `PATH` along the seam above, use the new fixture signature to drop the `with_image_path` workaround in `run.py`, and then take `make check` to green and do the refactor step.
20. factory: started tests as vm.
21. tester: I made the test changes that the human approved in entry 17 and the coder listed in entry 19. They fall under feature decision 8.

    Earlier test files I changed, and what changed:
    1. `tests/test_second_user_removed.py`, row `build-boundaries-parameters`: the expected parameters are now `["settings", "token", "hosting", "images"]`.
    2. `tests/domain/test_stop_table.py`: `ROWS` gains the sixteenth row `("stage-image-failed", ("L55",), "health_status", "stage_image_failed", REPOSITORY_TEST)` after `disk-low`. The test keeps its name, `test_the_table_holds_the_fifteen_stops_in_order`.
    3. `tests/test_stop_table.py::test_repository_stop_reaches_the_health_status_and_the_factory_log`: `stage_image_failed` is added to the machine-scoped tuple. The line was too long for ruff E501, so the conditional is now wrapped in parentheses. It checks the same thing.
    4. `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` and `tests/domain/test_contract_version_4.py::test_the_records_contract_is_at_version_4_without_left_branch`: the pins go from `"4.0"` to `"4.1"`. That covers the `RECORDS_CONTRACT` check and the `committed_is_generated` rows, plus the module docstring.
    5. `tests/conftest.py`, fixture `on_the_manual_clock`: the stand-in `built` now takes `images: Images | None = None` and passes it to `original(settings, token, hosting=hosting, images=images)`. I also added the import `from factory.application.images import Images`. Nothing else in conftest changed.

    Criterion 5, the new check row: I changed my own test `tests/entry/test_wiring_image_path.py`. The test is now named `test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use`, with the same two rows, `image-path` and `no-image-path`. It now also runs `boundaries.project_commands.run("check", time_limit=CHECK_LIMIT)`. It then checks that the second recorded `podman run` is the check (it holds `factory-check`) and that its `--env PATH` is the image's `PATH`.

    Mapping for criterion 5: criterion 5: tests/entry/test_wiring_image_path.py::test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use. The mapping for the other criteria is as in entry 14.

    Rows I did not change: the `check` rows in `tests/application/test_container_environment_extra.py` (which expect `CHECK_ENVIRONMENT`) and `tests/adapters/test_make_commands_container.py:134`. They build `ContainerMakeCommands` without an image path, so they still hold under the seam the coder proposes, where the default is `SYSTEM_PATH` and `CHECK_ENVIRONMENT` is kept. If the coder's seam changes that, it is a new test change.

    Not done: the Description still lists the watch criterion that entry 12 dropped. The work item's Description is outside the write paths the factory takes from this stage, and the factory left out my earlier edit to it. Someone who may write there has to remove it.

    Files created: none.

    Run: `uv run pytest -q` over the changed files and `tests/entry/test_wiring_project_image.py` had one failure: `test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use[image-path]`. It fails at `env_words(check)["PATH"]`, which is `'/usr/local/bin:/usr/bin:/bin'` where `'/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin'` is expected. That is the right reason: the check's `PATH` is still fixed. Every module imported. The other changed tests passed. `make lint` is green.

    `lint`: lint: green (0.2 s)
22. factory: started doing as vm.
23. coder: I put the image's `PATH` into the check containers, which the human's answer in entry 17 (item 4) asked for. I also dropped the `with_image_path` workaround now that the conftest stand-in takes `images`. `make check` is green. On the first `make test`, `test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use[image-path]` was the only failure: the check's `PATH` was still the fixed one.

    Built this round:
    - `src/factory/adapters/make_commands.py`: `ContainerMakeCommands` takes a new keyword, `path: str = SYSTEM_PATH`. The check's environment is now `{**extra, **CHECK_ENVIRONMENT, "PATH": path}`. `CHECK_ENVIRONMENT` stays as it is, so the earlier `check` rows in `tests/application/test_container_environment_extra.py` and `tests/adapters/test_make_commands_container.py` still pass unchanged.
    - `src/factory/entry/wiring.py`: `build_boundaries` reads the image's path once, through the private `_image_path(settings, images)`, before it builds anything. Without `images` it uses `SYSTEM_PATH`. It passes that one value to both `ContainerMakeCommands(path=...)` and `Boundaries(image_path=...)`. I removed the public `with_image_path` and its `__all__` entry, and the import of `dataclasses.replace`, which nothing used any more.
    - `src/factory/entry/run.py`: `_ProjectImageStart._build_tick` now calls `build_boundaries(chosen, token, hosting=..., images=inputs.images)` directly.

    The rest of the story (stage layer, images interface, podman adapter, fake, stop reason, start seam) is as entry 16 describes. The earlier rounds already committed it on the branch.

    Main choice: the image's `PATH` is read once in `build_boundaries` and given to the check adapter's constructor, so the adapters stay immutable and the sync, the check and the agent all take the same value. I rejected setting the path after construction (`replace` on the boundaries, plus a setter on the check adapter). That would keep two sources for one value, and the check adapter would have to change after it is built.

    Refactor step: removing `with_image_path` was the refactor. Reading the whole diff against `main` found nothing else to change.

    Noticed, not touched:
    - The Description still lists the watch criterion that entry 12 dropped. The factory left out the tester's edit to it, and I did not edit it either, since the work item may be outside my write paths. Someone who may write there has to remove it.
    - These notes from entry 16 still stand, as entry 17 said: a build that reaches its time limit has podman's no-end text as its detail, not the tail. An image that cannot be inspected falls back to `SYSTEM_PATH`. With `image=None`, no preflight stamp is reused.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 42 known, 0 gone
24. factory: started review as vm.
25. reviewer: Round 0 review. I read the diff of `src/` and `tests/` against the work item and ran `make duplicates`. Its one new finding is vulture's `unused class 'FakeImages'` (src/factory/adapters/fake_images.py:23). That is a false positive: the class is the test fake and is used only by tests. I did not run `make check`: entry 23 says it was green after the coder. The contract went from 4.0 to 4.1 for the added `stage_image_failed` value, which is the minor bump `docs/decisions.md` asks for.

    Findings:
    1. criterion 4, src/factory/entry/run.py:570-588 (`_ProjectImageStart._build_tick`). No test covers the success path through `run_instance`. `test_a_start_with_a_valid_stage_file_builds_it_once_and_takes_the_project_image` checks only what `project_image_settings` returns, so if `_build_tick` passed `inputs.settings` instead of `chosen` to `build_boundaries`/`build_tick`, no test would fail. Fix (tester): add a `run_instance` test with a valid stage file on `main` and `FakeImages`. It should check that the tick's container runs (recorded `podman run` calls) take `<FACTORY_STAGE_IMAGE>-project`, that the preflight's stamp is keyed by the layer's identity, and that the build comes before the preflight.
    2. criterion 1 / Interface "at most 64 KiB of UTF-8", src/factory/domain/stage_layer.py:385. The rule treats any U+FFFD in the text as "not UTF-8", so a valid UTF-8 file that contains U+FFFD is refused with the wrong reason. It also measures the size after `show_file` has replaced each bad byte with three bytes. Fix (coder): decide UTF-8 validity and size on the file's bytes as they are read. For example, give the Git wrapper a strict read that reports undecodable bytes, and have `stage_layer` refuse on that, not on a character a valid file may hold.
    3. src/factory/adapters/podman_runs.py:53 (`run_podman`). It copies `PodmanRuns._query` (same file, ~line 203): the same `run_or_raise` call with `functools.partial(ContainerError, ...)` and `accepted=None`; only `cwd` differs. Fix (coder): give `run_podman` a `cwd` parameter and have `_query` call it, so one helper stays.
    4. tests/entry/test_wiring_project_image.py:33-52 (`_Build`, `_RecordingImages`). This is a second images fake that copies `BuildCall` and `FakeImages` from src/factory/adapters/fake_images.py, against the one fake the Interface names. Fix (tester): use `FakeImages(build_result=...)` and compare against `BuildCall`.
    5. tests/entry/test_wiring_project_image.py:197-216 (`test_no_stage_starts_while_the_stage_image_stop_stands`). It builds the settings by hand (token file, state directory, `with_dataset`, `no-claude`) as a copy of the `instance_settings` fixture in tests/conftest.py:505. Fix (tester): take the `instance_settings` fixture.
    6. tests/domain/test_stage_layer.py:43-66. The two sides of one rule, the 64 KiB limit included, are split over two test functions (`test_a_stage_file_within_the_rule_is_accepted` and `test_a_stage_file_that_breaks_the_rule_is_refused`). Fix (tester): make them rows of one parametrized test, where each row gives either the expected digest and identity or a refusal.
    7. criterion 13 added: it needs its test. The podman `path` raises `ContainerError` when inspect fails or prints no JSON, and `build_boundaries` then falls back to `/usr/local/bin:/usr/bin:/bin` (src/factory/adapters/podman_images.py:156-161, src/factory/entry/wiring.py:742-746). Both behaviours are built and kept by entry 17, but untested.
    8. criterion 14 added: it needs its test. `PodmanImages(..., profile="job")` puts `JOB_PODMAN_OPTIONS` before every podman call (src/factory/adapters/podman_images.py:115), and `build_images` passes the instance's profile; no test covers this.

    description corrected: Interface "The sync environment's and the agent environment's `PATH`" -> "The sync environment's, the check environment's and the agent environment's `PATH`" (entry 17, item 4).
    description corrected: Interface "`factory-health` and `factory-watch` show it as they show the other stops" -> "`factory-health` shows it as it shows the other stops (`factory-watch` shows no stop of any reason, and that stays so)" (entry 12, item 2).
    description corrected: criterion 5 "gives the sync environment that `PATH`" -> "gives the sync environment and the check environment that `PATH`" (entry 17, item 4).
    description corrected: criterion 13 (`factory-watch` shows the stop) -> removed (entry 12, item 2). The new criteria 13 and 14 take its place, and `make check` and `docs:` are now 15 and 16.
    description corrected: docs criterion -> it now also asks that the operator guide say the sync, the checks and the agent take the image's `PATH` (entry 17, item 4).

    Rejected as findings: `project_image_settings` and the start logic living in `factory.entry`, because the human chose that seam in entry 9, item 3. The time-limited build's detail holding podman's text rather than a tail, the inspect fallback, and `image=None`, because entry 17 keeps all three. `image prune -f` pruning every dangling image, because entry 9, item 2 names that command. The `Replacements` TypedDict in run.py, which is typed and documented.

    Earlier tests:
    - tests/conftest.py: the human's leave, entry 17, item 4 (the `on_the_manual_clock` stand-in only).
    - tests/domain/test_contract.py: the human's leave, entry 17, item 3 (the 4.1 pin).
    - tests/domain/test_contract_version_4.py: the human's leave, entry 17, item 3 (the pins and the module docstring's version).
    - tests/domain/test_stop_table.py: the human's leave, entry 17, item 2 (the sixteenth row).
    - tests/test_stop_table.py: the human's leave, entry 17, item 2 (the machine-scope tuple).
    - tests/test_second_user_removed.py: the human's leave, entry 17, item 1 (`images` in the parameter row).
    - tests/entry/test_health.py: the human's leave, entry 9, item 4 (the row and the machine-scope tuple).
    - tests/entry/test_wiring_handlers.py: the story's Interface leave for rows that pin the `PATH` (the call gains the explicit `PATH` argument; the test checks the same thing).
26. factory: started doing as vm.
27. coder: Round 1. I fixed finding 3. I stopped at finding 2, because every way to fix it needs a change to a test that another story wrote.

    Done (finding 3): `src/factory/adapters/podman_runs.py`. `run_podman(argv, time_limit, *, cwd=ROOT)` gains a `cwd` keyword, and `PodmanRuns._query` now calls `run_podman(..., cwd=self._workspace)`. So one helper stays. The command text is the same as before: `" ".join(argv)` equals `_command(arguments)`. `make check` is green with this change: lint, types, layers, sast, secrets, licenses and test all passed (test in 84.6 s), then `check: green`. Nothing else is in the working tree.

    Finding 2 (U+FFFD and the size after replacement) is not fixed. The reason is in the process wrapper: `factory.adapters.process._decode` decodes every output with `errors="replace"`. So `Git.show_file` cannot tell a byte that is not UTF-8 from a real U+FFFD, and it cannot give the file's true size. To fix it, the stage file has to be read strictly at the start. I built that: `ProcessRequest.strict_decoding`, `GitCli.show_file(..., *, strict=False)` raising a new `NotUtf8(GitError)`, and `project_image_settings` raising the stop with "the stage file is not UTF-8" on `NotUtf8`. With strict reading, the U+FFFD check leaves `stage_layer`. `make types` then failed in a test that another story wrote: `tests/application/test_tick_stop_records.py:232`. Its `_UnresolvableMainForStopRecords(GitCli)` overrides `show_file(self, ref, path)`, and mypy gives `[override]` because the new signature differs. I undid the strict read, so the code stands as round 0 left it.

    Options:
    (a) Keep `show_file`'s name and add the keyword `strict: bool = False`. The tester adds `*, strict: bool = False` to the override at `tests/application/test_tick_stop_records.py:232` and passes it through to `super().show_file`. Nothing else in that module changes. This is one line of signature, and the Git interface keeps its twenty-one operations.
    (b) Add a new Git operation, for example `show_utf8(ref, path) -> str | None` raising `NotUtf8`. The tester adds it to `OPERATIONS` in `tests/git_interface_support.py`, and the two tests named "twenty-one operations" (`tests/application/test_git_interface.py`, `tests/application/test_interfaces.py`) change their names or counts.
    (c) Reject finding 2: keep the U+FFFD check as it is, and say in the docs that a stage file must not hold U+FFFD.
    I would choose (a), with your leave for that one override.

    The reviewer's tester findings are still open for the tests stage: 1 (a `run_instance` test of the success path), 4 (use `FakeImages`/`BuildCall`), 5 (use the `instance_settings` fixture), 6 (accepted and refused as rows of one test), 7 (criterion 13) and 8 (criterion 14).

    Refactor step: I read my diff. It is the one helper change and needs nothing more. Description: unchanged by me. The reviewer already rewrote it in entry 25.
28. 2026-11-04 human: (c): keep the U+FFFD check in stage_layer. A stage file that holds U+FFFD, or bytes that are not UTF-8 (which reach the factory as U+FFFD), is refused with one reason that names both; the 64 KiB limit is measured on the UTF-8 encoding of the text as read. The operator guide says so in one sentence. Git.show_file and the process wrapper stay unchanged, so no leave is needed. The reviewer's tester findings go to the tests stage as usual.
29. factory: started doing as vm.
30. coder: Round 1, after the human's answer in entry 28 (option c). I changed one file and no tests.

    Built:
    - `src/factory/domain/stage_layer.py`: the U+FFFD check stays in `stage_layer`. Its refusal now names both cases in one reason: "the stage file holds U+FFFD or bytes that are not UTF-8, which read as U+FFFD". The comment on `_REPLACEMENT_CHARACTER` says why the two cannot be told apart: the reader decodes with replacement. The 64 KiB limit was already measured on the UTF-8 encoding of the text as read (`len(text.encode("utf-8"))`), so that code did not change. `Git.show_file` and the process wrapper are unchanged, as the answer says.

    Main choice: I kept the one check and only made its reason say that it covers both cases. I rejected a separate reason for a real U+FFFD, because after the reader's replacement no code can tell it from an undecodable byte.

    `make check`: green (test: 84.0 s, then `check: green`).

    Refactor step: the diff is one reason and one comment. Nothing to change.

    What the journal changed in the Description: entry 28 sets the rule. A stage file that holds U+FFFD, or bytes that are not UTF-8, is refused with one reason that names both. The 64 KiB limit is measured on the UTF-8 encoding of the text as read, and the operator guide gets one sentence about this, which is the documenter's. I did not rewrite the Description, because earlier edits to the work item from these stages were left out by the factory.

    Open for the tests stage: the reviewer's tester findings from entry 25:
    1. A `run_instance` test of the success path: the project image in the container runs, the preflight stamp keyed by the layer's identity, and the build before the preflight.
    2. `tests/entry/test_wiring_project_image.py` uses `FakeImages`/`BuildCall` in place of its own `_RecordingImages`.
    3. The same file uses the `instance_settings` fixture.
    4. The accepted and refused rows of `tests/domain/test_stage_layer.py` become one parametrized test.
    5. A test for criterion 13: podman `path` raises `ContainerError` on a failed inspect and on output that is not JSON, and `build_boundaries` then falls back to `/usr/local/bin:/usr/bin:/bin`.
    6. A test for criterion 14: the `job` profile's global options come before `build`, `image prune -f` and `image inspect`; the `rootless` profile has none.

    The code for criteria 13 and 14 is already built (`src/factory/adapters/podman_images.py`, `src/factory/entry/wiring.py` `_image_path`).

    Noticed, not touched: the notes that entry 17 kept still stand. A build that reaches its time limit gets podman's no-end text as its detail. An image that cannot be inspected falls back to the default `PATH`. With `image=None`, no preflight stamp is reused.
31. factory: started tests as vm.
32. tester: Round 1, test changes. I made the six tester findings from the reviewer's entry 25 that the coder's entry 30 lists, and added one refused row for the human's answer in entry 28. I changed only test files this story wrote. No test from another story was touched.

    Changes:
    - Finding 1 (success path through `run_instance`): new `tests/entry/test_wiring_project_image.py::test_a_run_with_a_valid_stage_file_runs_its_preflight_on_the_project_image`. It has a valid stage file on `main`, `FakeImages`, the agents installed, and a preflight stamp seeded at `main`. There are two rows. With a stamp keyed by the layer's identity, the stamp is reused and no stop stands. With a stamp keyed by the base's identity, the machine items run again, and the stand-in `podman`'s `image exists` names only `<FACTORY_STAGE_IMAGE>-project`. The base image appears in no podman call in either row, and exactly one `BuildCall` is recorded. I rejected checking a sync, check or agent `podman run` here: with no work item in progress, a tick starts none, and setting up a stage only for that seemed too much. The preflight's stage-image item is the container call that this run makes. Passing `inputs.settings` in place of `chosen` would fail both rows.
    - Finding 4: `_Build` and `_RecordingImages` are removed. The file uses `FakeImages(build_result=...)` and `BuildCall` from `factory.adapters.fake_images`.
    - Finding 5: `test_no_stage_starts_while_the_stage_image_stop_stands` takes the `instance_settings` fixture.
    - Finding 6: `tests/domain/test_stage_layer.py` now has one parametrized `test_a_stage_file_is_accepted_or_refused_by_its_rule` over the `ACCEPTED` and `REFUSED` rows. The 64 KiB / 64 KiB+1 rows are part of it. Entry 28 added a refused row `not-utf-8-or-u-fffd` (a text holding U+FFFD, which is how bytes that are not UTF-8 arrive), and `test_each_broken_rule_gives_its_own_reason` covers it too.
    - Finding 7 (criterion 13): new `tests/adapters/test_podman_images.py::test_path_raises_a_container_error_when_the_image_cannot_be_read`, with two rows: inspect exits 125, and inspect prints no JSON. A third row, `path-raises`, is added to `tests/entry/test_wiring_image_path.py::test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use`. It gives `build_boundaries` a `PodmanImages` on the recording stand-in, which prints no JSON. The sync, the check and the agent then take `/usr/local/bin:/usr/bin:/bin`. The test's parameter changed from `paths` to an `images_of` callable, and the earlier two rows check the same things.
    - Finding 8 (criterion 14): new `tests/adapters/test_podman_images.py::test_the_job_profile_puts_its_global_options_before_every_podman_command`, with `job` and `rootless` rows over `build`, `image prune` and `image inspect`.

    Criterion → test:
    criterion 1: tests/domain/test_stage_layer.py::test_a_stage_file_is_accepted_or_refused_by_its_rule, ::test_each_broken_rule_gives_its_own_reason, ::test_the_padded_files_lie_on_both_sides_of_64_kib
    criterion 2: tests/domain/test_stage_layer.py::test_the_digest_follows_every_byte_and_the_identity_is_stable (named-once constants: ::test_the_stage_file_and_the_project_image_tag_are_named_once)
    criterion 3: tests/entry/test_wiring_project_image.py::test_a_start_without_a_stage_file_builds_nothing_and_keeps_the_base
    criterion 4: tests/entry/test_wiring_project_image.py::test_a_start_with_a_valid_stage_file_builds_it_once_and_takes_the_project_image, ::test_a_run_with_a_valid_stage_file_runs_its_preflight_on_the_project_image
    criterion 5: tests/entry/test_wiring_image_path.py::test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use (rows image-path, no-image-path)
    criterion 6: tests/entry/test_wiring_project_image.py::test_a_stage_file_that_does_not_build_stands_as_a_stop, ::test_a_stage_file_that_breaks_the_rule_stands_as_a_stop_and_builds_nothing, ::test_no_stage_starts_while_the_stage_image_stop_stands
    criterion 7: tests/adapters/test_podman_images.py::test_the_build_passes_the_base_the_network_the_tag_and_an_empty_context
    criterion 8: tests/adapters/test_podman_images.py::test_the_output_tail_is_the_last_twenty_lines_in_order
    criterion 9: tests/adapters/test_podman_images.py::test_a_build_that_reaches_its_time_limit_has_not_passed; tests/entry/test_wiring_project_image.py::test_the_build_time_limit_is_thirty_minutes (and the BuildCall time limit in the criterion-4 tests)
    criterion 10: tests/adapters/test_podman_images.py::test_path_is_the_images_configured_path_or_the_base_default
    criterion 11: tests/entry/test_wiring_project_image.py::test_the_next_start_ends_a_stage_image_stop
    criterion 12: tests/entry/test_health.py::test_every_stop_reason_makes_the_check_fail_until_it_is_cleared (row stage_image_failed, from round 0)
    criterion 13: tests/adapters/test_podman_images.py::test_path_raises_a_container_error_when_the_image_cannot_be_read; tests/entry/test_wiring_image_path.py::test_the_sync_the_check_and_the_agent_take_the_path_of_the_image_in_use[path-raises]
    criterion 14: tests/adapters/test_podman_images.py::test_the_job_profile_puts_its_global_options_before_every_podman_command

    Files changed (none created): tests/entry/test_wiring_project_image.py, tests/domain/test_stage_layer.py, tests/adapters/test_podman_images.py, tests/entry/test_wiring_image_path.py.

    One run of `uv run pytest -q` over the four files: all 44 tests passed. The code already exists, so the new tests are green and not red. Every module imported. `make lint`: green. `make types`: green.

    `lint`: lint: green (0.1 s)
33. factory: started doing as vm.
