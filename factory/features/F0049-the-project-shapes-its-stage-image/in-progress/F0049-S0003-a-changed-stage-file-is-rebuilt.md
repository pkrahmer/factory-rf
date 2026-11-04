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
  started_at: '2026-11-04T01:26:07.158256Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T01:26:07.151781Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T01:26:07.158256Z'
  stage: intake
---

# A changed stage file on main is rebuilt between stages

## Description

After S0002 the factory builds the project's stage file once, when `factory-run` starts. A merge that adds, changes or removes `factory/stage.Containerfile` on `main` would then reach the containers only after the operator restarts the service, and on a VM that is easy to forget. This story makes the factory follow `main`. Whenever it has fetched a new `origin/main`, and before it starts the next stage, it compares the stage file on that commit with the one the project image was built from. A new or changed file is built as at the start, and the stages after it run in the new image under its new identity, so the preflight and the reuse of passed checks start afresh. A removed file returns the instance to the base image and the base's identity. An unchanged file, or a new commit that does not touch it, builds nothing. A stage that is running is never interrupted: the change takes effect between stages. A failed build is the stop `stage_image_failed`, as in S0002, and the next `main` with a different file ends it and is tried again. The previous project image is removed once a new one is tagged, so a machine keeps one project image.

## Interface

- The check runs where the factory handles a new `origin/main` before it starts a stage (the same place as the preflight's probe of `main`, which runs once per commit). It reads the file from that commit with the git wrapper and compares `StageLayer.digest`, or its absence, with the one in use.
- A rebuild uses the images interface of S0002 with the same base and tag; the image in use, the identity and the containers' `PATH` change together, in the one place S0002 named, and only after the build passed.
- The stop `stage_image_failed` of a failed rebuild names the commit (its first 12 hex digits) in its detail. A later `origin/main` whose file has another digest, or no file, ends the stop and is handled as above; the same digest again does not retry the build.
- The factory log gets one line for each change, and none for an unchanged file: `stage image: built <identity> at <commit> in <s> s`, `stage image: back to the base at <commit>` and `stage image: failed at <commit>`.

## Acceptance criteria

1. A new `origin/main` whose stage file has the same digest as the one in use, and one that has no file while none is in use, build nothing and change neither the image nor the identity.
2. A new `origin/main` with a changed file builds it once before the next stage starts; that stage and every later one take the new image, its identity and its `PATH`, and the log holds `stage image: built <identity> at <commit> in <s> s`.
3. A new `origin/main` that adds a file to a project without one builds it; one that removes the file returns every later container to the base image under the base's identity, with the log line `stage image: back to the base at <commit>`, and builds nothing.
4. A `main` that moves while a stage runs changes nothing for that stage: its remaining containers take the image it started with, and the rebuild happens before the next stage.
5. A rebuild that fails stands as `stage_image_failed` with the commit in its detail, and the image in use stays the one before; a later `main` with the same digest does not build again, and one with another digest (or no file) builds (or returns to the base) and ends the stop. Rows: the same digest, another digest, the file removed.
6. After a passed rebuild, the images interface's removal of untagged images runs, so the previous project image does not stay.
7. `make check` stays green.
8. docs: `docs/operator-guide.md`: in *The project's stage file*, that a merged change takes effect before the next stage without a restart, the four log lines, and that a failed build waits for a new `main`. The project guide: `stage-environment.md` says where the factory compares the stage file on a new `main`. `docs/decisions.md`: one entry with feature decision 5 and its reason. `README.md`: none.

## Smoke test

```bash
grep -rhoE 'stage image: (built|back to the base at|failed at)' src/factory | sort -u
```

Expect: exactly the three lines `stage image: back to the base at`, `stage image: built` and `stage image: failed at`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
