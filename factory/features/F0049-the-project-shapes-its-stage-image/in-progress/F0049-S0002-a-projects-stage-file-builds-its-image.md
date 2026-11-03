---
stage: intake
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 527
comments_read: []
handed_over: null
claim: null
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
  - `build(layer: StageLayer, base: str, tag: str, time_limit: timedelta) -> ImageBuild`: builds `layer.text` with `--build-arg FACTORY_BASE=<base>`, `--network=host`, rootless and with an empty context directory, tags it `tag`, and removes images left without a tag after it. `ImageBuild` holds `passed`, `duration` and `output_tail` (the build's last 20 lines).
  - `path(image: str) -> str`: the `PATH` the image's configuration sets (podman's `image inspect`), or the base's default `/usr/local/bin:/usr/bin:/bin` when it sets none.
  - The build's time limit is 30 minutes, one constant.
- The project image is named in one place of the wiring: the image every container run takes, and the identity the preflight and the check reuse take. The sync environment's and the agent environment's `PATH` are built from `path(<the image in use>)` (the agent's with its scripts folder first), in place of the fixed `/usr/local/bin:/usr/bin:/bin`. Rows of earlier tests that pin that `PATH` change under the feature's leave.
- A new `RepositoryStopReason`, `stage_image_failed`, whose detail is the rule's reason or `the stage file did not build in <s> s:` followed by `output_tail`. While it stands no stage starts; `factory-health` and `factory-watch` show it as they show the other stops. It ends with the next start of `factory-run` (and, after S0003, with a new `main`).

## Acceptance criteria

1. `stage_layer` accepts and refuses by its rule; rows: the template of the Interface (accepted, with its digest and identity); `FROM ${FACTORY_BASE}` alone; `from $FACTORY_BASE` in lower case; a comment and a blank line before `ARG FACTORY_BASE`; refused, each with its own reason: `FROM debian:bookworm`, `FROM ${FACTORY_BASE} AS build`, `FROM --platform=linux/amd64 ${FACTORY_BASE}`, a second `FROM`, no `FROM`, a `RUN` before the `FROM`, `ARG OTHER` before the `FROM`, a file of 64 KiB (accepted) and of 64 KiB and one byte (refused), and bytes that are not UTF-8.
2. Two files that differ in one byte have different digests, and the same file has the same digest and identity at every call; the identity is `<base identity>+<12 hex digits>`.
3. A start whose `origin/main` holds no stage file builds nothing, and every container run takes the base image with the base's identity, exactly as before this story.
4. A start whose `origin/main` holds a valid stage file builds it once, with the base image as `FACTORY_BASE` and the tag `<FACTORY_STAGE_IMAGE>-project`, before the preflight runs; every following container run (sync, agent, check) takes the project image, and the preflight's stamps and the check reuse take the layer's identity.
5. The containers' `PATH` is the image's: a fake image whose `PATH` is `/opt/jdk/bin:/usr/local/bin:/usr/bin:/bin` gives the sync environment that `PATH` and the agent environment its scripts folder followed by it; an image that sets none gives `/usr/local/bin:/usr/bin:/bin`.
6. A stage file that breaks the rule, and one whose build fails or reaches its time limit, each stand as the stop `stage_image_failed` with its detail as the Interface states, and no stage starts while it stands; the base image is not used in its place.
7. The podman adapter's build passes `--build-arg FACTORY_BASE=<base>`, `--network=host`, `-t <tag>` and an empty context directory, and after a build runs the removal of untagged images; its `path` reads the image's configured `PATH`. Tested through the argument lists and a stand-in for `podman`, without a real container.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: a section *The project's stage file*: what `factory/stage.Containerfile` is, its rule, an example that adds `build-essential` and `cmake`, that only `main` counts, that the build has the network and no files of the repository so the project pins its own versions and checksums, where the project image and its identity show, and the stop `stage_image_failed` and what to do about it. The project guide: `stage-environment.md` names the images interface, its fake and the one place where the image in use is chosen. `docs/decisions.md`: one entry with feature decisions 1, 3 and 4 and their reasons. `README.md`: one sentence that a project can add tools to its stage image with that file.

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
