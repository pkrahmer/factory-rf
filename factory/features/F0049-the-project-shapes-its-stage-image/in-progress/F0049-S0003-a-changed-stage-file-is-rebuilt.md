---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 528
comments_read: [6620015058]
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-04T01:28:22.048587Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-04T01:26:27.624676Z'
  stage: intake
  run: 9a99d43035f441629927f89ec1d7cde7
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-04T01:28:19.119808Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-04T01:28:22.048587Z'
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
3. intake: Questions (format check passed; the story is not yet buildable):

   1. Interface names no concrete module or signature. It says "where the factory handles a new origin/main", "the images interface of S0002" and "the one place S0002 named", but gives no module, class or method. S0002's code exists (`factory.domain.stage_layer.StageLayer`, `factory.entry.wiring` around lines 377-402), so please name the module and function where the comparison runs, the images-interface methods used for build and for removal of untagged images, and the holder of "image in use / identity / PATH". Proposal: name them as they stand in wiring.py and the S0002 images interface.
   2. The Interface says the `stage_image_failed` detail names the commit by its first 12 hex digits. Criterion 5 only says "the commit in its detail". Please add the 12-digit form to the criterion. I would choose: "detail contains the first 12 hex digits of the commit".
   3. The Interface's log line `stage image: failed at <commit>` has no criterion (criterion 2 covers `built`, criterion 3 covers `back to the base`). Add it to criterion 5. Also state whether `<commit>` in the log lines is the full id or the 12-digit form (I would choose 12 digits, as in the detail).
   4. The Interface says "none for an unchanged file" and that the same digest after a failure does not log again. No criterion checks that no log line is written in the unchanged cases. Add it to criterion 1, and to the same-digest row of criterion 5.
   5. Criterion 5's rows combine several behaviours. "Another digest ends the stop and builds" and "the file removed ends the stop and returns to the base" are two different outcomes in one test. Please say they are separate rows with their own expectations (stop ended, image/identity afterwards).
   6. Criterion 3 combines "adds a file to a project without one builds it" with "removes returns to the base". They need not be one test, so please split them into two.
   7. The smoke test greps only for the log-line text in the source. It shows the strings exist, not that a rebuild happens, but it is runnable and its Expect is checkable. I accept it as is, unless you want a stronger check.
4. 2026-11-04 human: 1. Yes: name them as they stand after S0002 (factory.domain.stage_layer, the Images interface's build and its prune after a build, project_image_settings and with_image_path in factory.entry.wiring, Boundaries.image_path, and the _ProjectImageStart seam in factory.entry.run). Where the comparison should run on each new origin/main, choose the place next to the preflight's probe of main, as the Interface says, and name it.
   2. Yes: the detail contains the first 12 hex digits of the commit.
   3. Yes: add stage image: failed at <commit> to criterion 5; <commit> is the 12-digit form in every log line.
   4. Yes: no log line in the unchanged cases of criterion 1 and in the same-digest row of criterion 5.
   5. Yes: separate rows, each with its own expectations (stop ended or not, image and identity afterwards).
   6. Yes: two tests, adding and removing.
   7. The smoke test stays as it is.
5. factory: started intake as vm.
