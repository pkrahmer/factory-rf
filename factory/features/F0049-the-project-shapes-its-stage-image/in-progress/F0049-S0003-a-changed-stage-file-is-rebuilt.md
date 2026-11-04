---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 528
comments_read: [6620015058, 6620208635]
handed_over: null
claim: null
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
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-04T01:29:00.554423Z'
  stage: intake
  run: 66017b2814ed4632b278549ab569c80e
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-04T01:29:06.139795Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-04T01:32:50.109830Z'
  stage: tests
  run: 73430809bd294243911d6133f64d45c9
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-04T01:32:55.536824Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-04T01:39:12.941930Z'
  stage: doing
  run: f4e3529a1b0f4ddabda59d9a4b65f05f
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-04T01:41:04.786790Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-04T01:41:07.843102Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-04T01:41:27.243129Z'
  stage: doing
  run: de6b50e26a06469cb4a688f4a9869387
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-04T01:41:33.235692Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-04T01:42:21.619653Z'
  stage: tests
  run: 29e233b18d0e462484ec04ca8047237f
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-04T01:42:27.921971Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-04T01:46:19.213174Z'
  stage: doing
  run: 3ea6b28b6be4433c919199598b7630b7
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-04T01:46:24.743217Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-04T01:49:42.377090Z'
  stage: review
  run: 45d2c5ce71e6491fbdbf88349a1524b3
---

# A changed stage file on main is rebuilt between stages

## Description

After S0002 the factory builds the project's stage file once, when `factory-run` starts. A merge that adds, changes or removes `factory/stage.Containerfile` on `main` would then reach the containers only after the operator restarts the service, and on a VM that is easy to forget. This story makes the factory follow `main`. Whenever it has fetched a new `origin/main`, and before it starts the next stage, it compares the stage file on that commit with the one the project image was built from. A new or changed file is built as at the start, and the stages after it run in the new image under its new identity, so the preflight and the reuse of passed checks start afresh. A removed file returns the instance to the base image and the base's identity. An unchanged file, or a new commit that does not touch it, builds nothing. A stage that is running is never interrupted: the change takes effect between stages. A failed build is the stop `stage_image_failed`, as in S0002, and the next `main` with a different file ends it and is tried again. The previous project image is removed once a new one is tagged, so a machine keeps one project image.

## Interface

- The check runs in `factory.entry.run._ProjectImageStart.prepare`, before each tick and so before any stage starts, next to where `Preflight.run` (`factory.application.preflight`) probes `main` once per commit. It fetches, reads the file from `origin/main` with `Git.show_file`, and compares `factory.domain.stage_layer.StageLayer.digest`, or its absence, with the one in use.
- A rebuild calls `Images.build(layer, base, tag, time_limit)` of `factory.application.images` (which removes untagged images after it) with the same base and tag, through `factory.entry.wiring.project_image_settings`; the image in use, the identity and the containers' `PATH` (`Boundaries.image_path`, built by `build_boundaries`) change together, in the new tick `_ProjectImageStart` builds, and only after the build passed. A tick that is running keeps the boundaries it started with.
- The stop `stage_image_failed` of a failed rebuild has the first 12 hex digits of the commit in its detail. A later `origin/main` whose file has another digest, or no file, ends the stop and is handled as above; the same digest again does not retry the build.
- The factory log gets one line for each change, and none for an unchanged file; `<commit>` is the first 12 hex digits in every line: `stage image: built <identity> at <commit> in <s> s`, `stage image: back to the base at <commit>` and `stage image: failed at <commit>`.

## Acceptance criteria

1. A new `origin/main` whose stage file has the same digest as the one in use, and one that has no file while none is in use, build nothing, change neither the image nor the identity, and write no `stage image:` log line.
2. A new `origin/main` with a changed file builds it once before the next stage starts; that stage and every later one take the new image, its identity and its `PATH`, and the log holds `stage image: built <identity> at <commit> in <s> s`.
3. A new `origin/main` that adds a file to a project without one builds it: the later containers take the project image, its identity and its `PATH`.
4. A new `origin/main` that removes the file returns every later container to the base image under the base's identity, with the log line `stage image: back to the base at <commit>`, and builds nothing.
5. A `main` that moves while a stage runs changes nothing for that stage: its remaining containers take the image it started with, and the rebuild happens before the next stage.
6. A rebuild that fails stands as `stage_image_failed` with the first 12 hex digits of the commit in its detail and the log line `stage image: failed at <commit>`, and the image in use stays the one before. Each row has its own expectations (stop ended or not, image and identity afterwards, log lines): a later `main` with the same digest (the stop stands, no build, no log line); another digest (the stop ends, it builds); the file removed (the stop ends, the base and its identity, no build).
7. After a passed rebuild, the images interface's removal of untagged images runs, so the previous project image does not stay.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`: in *The project's stage file*, that a merged change takes effect before the next stage without a restart, the four log lines, and that a failed build waits for a new `main`. The project guide: `stage-environment.md` says where the factory compares the stage file on a new `main`. `docs/decisions.md`: one entry with feature decision 5 and its reason. `README.md`: none.

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
6. intake: accepted, after carrying the human's answers (journal entry 4) into the story.
   - Interface: concrete now. The check is `factory.entry.run._ProjectImageStart.prepare`, next to `Preflight.run`'s probe of main. It reads the file with `Git.show_file` and compares `StageLayer.digest`. It rebuilds with `Images.build(layer, base, tag, time_limit)` through `wiring.project_image_settings` and `build_boundaries`. `Boundaries.image_path` changes with the new tick. Entry 4 also named `with_image_path`, but that function does not exist in `src`, so I left it out. The coder decides the mechanism for the digest in use and the new tick.
   - Criteria: edited per entry 4.
     - 1: no log line is written in the unchanged cases.
     - 3 and 4: adding and removing are now two criteria (old 3 split).
     - 5: the old 4, renumbered.
     - 6: the old 5. It has the 12-digit commit in the detail, the `failed at` log line and separate rows with their own expectations: same digest, another digest, file removed.
     - 7, 8 and 9: the old 6, 7 and 8, renumbered. `make check` and `docs:` stay last.
     - Each criterion is testable by one test function. Each rule has both sides: changed or unchanged, failed or passed, kept or ended stop.
   - Smoke test: unchanged, as the human said. It is runnable and its Expect names the three exact lines, so it can be checked.
   - Architecture: the layers hold. The comparison and wiring sit in `factory.entry`, and the `Images` and `Git` interfaces are used as they are.
   - Scope: within feature decision 5 and the feature's S0003 scope. Nothing in "Out of scope" is touched.
   - Open for the coder: the commit in the log lines and the detail is the first 12 hex digits.
7. factory: started tests as vm.
8. tester: Wrote the tests for criteria 1 to 7 in one new file. Criteria 8 and 9 (`make check`, docs) get no test.

   How the tests work: they drive `factory.entry.run.run_instance` with a replacement `build_tick` that `factory.entry.run` looks up, the same seam `tests/entry/test_run.py` uses. Each tick that is built records three things after its stage's action: the image it got (`settings.stage_image`), the identity (`settings.image`) and the PATH (`boundaries.image_path`). It also records how many builds had been asked for so far. Between iterations, the scheduler's sleep pushes the next change to `main` from the human's clone. Builds go through `ScriptedImages`, a test subclass of `FakeImages` that ends each build as scripted and gives the PATH of each passed build its own value. The tests only compare `stage image:` log lines written after the first iteration, so whether the start's own build writes a line is left open.

   - criterion 1: tests/entry/test_run_project_image_rebuild.py::test_a_new_main_that_leaves_the_stage_file_as_it_is_builds_nothing_and_logs_nothing (rows: same-digest, no-file)
   - criterion 2: tests/entry/test_run_project_image_rebuild.py::test_a_changed_stage_file_is_built_once_before_the_next_stage_and_taken_by_every_later_one
   - criterion 3: tests/entry/test_run_project_image_rebuild.py::test_a_stage_file_added_to_a_project_without_one_is_built_and_taken
   - criterion 4: tests/entry/test_run_project_image_rebuild.py::test_a_removed_stage_file_returns_to_the_base_and_builds_nothing
   - criterion 5: tests/entry/test_run_project_image_rebuild.py::test_a_main_that_moves_during_a_stage_changes_its_image_only_from_the_next_stage (the tick that is running pushes to `main` itself, then records)
   - criterion 6: tests/entry/test_run_project_image_rebuild.py::test_a_failed_rebuild_stands_as_a_stop_until_main_brings_another_stage_file (rows: same-digest, another-digest, file-removed, each with its own expectations for the stop, the builds, the image afterwards and the log lines)
   - criterion 7: tests/entry/test_run_project_image_rebuild.py::test_a_passed_rebuild_builds_under_the_same_tag_so_the_previous_image_is_removed. Through the interface this means a second `Images.build` call with the same base, tag and time limit; `Images.build` removes untagged images after itself.

   Points for the coder:
   - Criterion 6 does not say whether a tick runs while the stop stands. The test does not decide it: it checks only that any tick that runs before the stop ends keeps the old image, PATH and identity.
   - The built line is checked as `in 3 s` for a build that lasted 3 s, so no rounding is involved.
   - `<commit>` is the first 12 hex digits of `main` after each push.

   Files created: tests/entry/test_run_project_image_rebuild.py. No earlier test file changed.

   Test run: the one run, `uv run pytest -q tests/entry/test_run_project_image_rebuild.py | tail -5`, collected the file without errors. Every module it imports exists, so none failed to import. The five lines shown were failures: criterion 5, the three rows of criterion 6, and criterion 7. They fail because only the start builds today. The failures for criteria 2 to 4 and the count line were above the tail and not seen. Criterion 1 is expected to pass already, since the current code does nothing on a new `main`. `make lint` is green; the type check was skipped as the stage says.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: Question: `tests/entry/test_run_project_image_rebuild.py` can't pass against any code, because of a wrong path in the test. `World.__init__` sets `self.remote = tmp_path / "origin"`. But the `remote` fixture (`tests/conftest.py`, through `copy_remote`) returns `tmp_path / "origin" / "remote.git"`. So `_commit(self.remote)` runs `git rev-parse main` outside any repository. All 10 tests in the file fail in the scheduler's first sleep with `E   AssertionError: git rev-parse main failed: fatal: not a git repository (or any of the parent directories): .git` (`tests/entry/test_run_project_image_rebuild.py:125` in `_commit`, from `tests/git_support.py:107`). That is before any expectation is checked.

    Options:
    (a) The tester changes that one line to `self.remote = tmp_path / "origin" / "remote.git"`. Better still, `World` takes the `remote` fixture as a parameter instead of building the path itself. I would choose this.
    (b) Some other change to the test.

    I ran the file with only that line changed, in a scratch copy, and then put the test back as the tester wrote it. All 10 tests passed, as did `tests/entry/test_wiring_project_image.py` and `tests/entry/test_run.py` (53 tests). If you answer (a), the next coder run ends with `tests`, naming that change.

    What I built (left in the working tree):
    - `src/factory/entry/run.py`: `_ProjectImageStart.prepare` now runs `_follow_main` before every tick, after the repository waiter. That fetches, reads the stage file on `origin/main` and compares it with the last one it handled.
      - Same file: it does nothing. That also means it does not retry a file that failed.
      - Changed file: `_choose` calls `project_image_settings` and builds a new tick with new boundaries, but only when the build passed.
      - Failed build: the tick is dropped, so no tick runs while the stop stands. This matches the start behaviour from before.
      - It writes `stage image: back to the base at <commit>` when the file is removed while a project image is in use.
    - `src/factory/entry/wiring.py`:
      - New `StageImageReport` (log, clock, 12-digit commit).
      - New `stage_image_report(git, log, clock)`: resolves `origin/main`, and raises `GitError` when it is missing.
      - New `stage_file_on_main(git)`.
      - `project_image_settings` replaces its `clock=` keyword with `report=`. With a report, it writes the `built … in <s> s` and `failed at <commit>` lines and prefixes the stop's detail with `at <commit>: `. Without one, the detail and the behaviour are the same as before, so S0002's tests are unchanged.
      - `_whole_seconds` is shared by the fault text and the built line.

    Main choice: I compare the stage file's text, not `StageLayer.digest`. Equal text means equal digest, and the text also covers a file that breaks the rule, which has no digest. I rejected computing the digest separately, because a refused file would then need its own case. I moved the clock into the report because a sixth parameter broke ruff's PLR0913, and only the run passes either one.

    Refactor: done once. I folded the clock into the report and named the second boundaries `chosen_boundaries`.

    Noticed, not touched:
    - A failed fetch in `prepare` now fails that iteration through the scheduler's catch-all, which logs `iteration failed`. Before, only the first iteration fetched.
    - The start's own build also writes a `stage image: built` line. The tests leave that open.

    `make check`: lint, types, layers, sast, secrets and licenses are green. `make test` is red only on those 10 tests.

    The factory left out changes outside the write paths: tests/entry/test_run_project_image_rebuild.py.
11. 2026-11-04 human: (a): the tester makes World take the remote fixture (or sets self.remote to tmp_path / "origin" / "remote.git"), in this story's own test module. Your other choices stand: comparing the text, the report holding the clock, the built line at the start too. A failed fetch in prepare that logs iteration failed and retries at the next tick is acceptable for now.
12. factory: started doing as vm.
13. coder: Test change for the tester, per the human's answer in entry 11, option (a). In `tests/entry/test_run_project_image_rebuild.py`, `World.__init__` (line 152) must point `self.remote` at the bare repository the `remote` fixture returns. Either `World` takes the `remote` fixture as a parameter, or the line becomes `self.remote = tmp_path / "origin" / "remote.git"`. Today `_commit(self.remote)` runs `git rev-parse main` outside a repository, so all 10 tests fail in the scheduler's first sleep before any expectation is checked.

    No code changed in this run. The implementation from entry 10 is committed on the branch as it was: `src/factory/entry/run.py` (`_ProjectImageStart.prepare` → `_follow_main`) and `src/factory/entry/wiring.py` (`StageImageReport`, `stage_image_report`, `stage_file_on_main`, `project_image_settings(report=)`). In entry 10 I ran the whole file in a scratch copy with only that line changed, and all 10 tests passed.

    The human's answer keeps my earlier choices, so nothing else changes:
    - comparing the file's text rather than `StageLayer.digest`
    - the report holding the clock
    - the `built` line also at the start
    - a failed fetch in `prepare` that logs `iteration failed` and retries at the next tick

    The Description stays as it is: the answer is about the test, not the task's meaning.

    Once the tester makes the change and sends the item back, the next coder run needs only `make check` and the refactor read.
14. factory: started tests as vm.
15. tester: Made the test change the human approved in entry 11, option (a), as the coder named it in entry 13. I changed one line in `tests/entry/test_run_project_image_rebuild.py`: in `World.__init__`, `self.remote = tmp_path / "origin"` is now `self.remote = tmp_path / "origin" / "remote.git"`. That is the bare repository the `remote` fixture returns (`copy_remote(remote_template, tmp_path / "origin")`). So `_commit(self.remote)` now runs `git rev-parse main` inside the repository.

    Rejected: passing the `remote` fixture into `World`, the human's other option. I tried it first, but `make lint` refused it with PLR0917 (6 positional arguments > 5) on `World.__init__` and on the `world` fixture. I undid it and used the one-line path change instead, which the answer also allows.

    No other test changed. Every test keeps its name and still checks the same thing. The criterion-to-test mapping in entry 8 still holds.

    Test run: `uv run pytest -q tests/entry/test_run_project_image_rebuild.py | tail -5` passed all 10 tests (`..........`) against the coder's implementation already on the branch. Every module imported. `make lint` is green.

    Files changed: tests/entry/test_run_project_image_rebuild.py. No files created.

    `lint`: lint: green (0.1 s)
16. factory: started doing as vm.
17. coder: `make check` is green, so the item goes to review. This run changed no code. The implementation committed earlier on the branch (entry 10) now passes all 10 tests in `tests/entry/test_run_project_image_rebuild.py`, after the tester's one-line fix in entry 15. The S0002 tests and `tests/entry/test_run.py` also pass. Coverage is 99.51 %.

    What I built (entry 10, unchanged):
    - `src/factory/entry/run.py`:
      - `_ProjectImageStart.prepare` runs `_follow_main` before every tick, after the repository waiter. That fetches, reads the stage file on `origin/main` and compares it with the last one it handled. The same text does nothing, which also means a file that failed is not tried again.
      - `_choose` builds the image through `project_image_settings`. Only when the build passed does it build a new tick on new boundaries: image, identity and `PATH` change together. A tick that is running keeps the boundaries it started with.
      - A failed build drops the tick, so no tick runs while the stop stands.
      - When a project image was in use and the file is removed, it writes `stage image: back to the base at <commit>`.
    - `src/factory/entry/wiring.py`:
      - New `StageImageReport` holds the log, the clock and the commit's first 12 hex digits. New `stage_image_report` resolves `origin/main` and raises `GitError` when it is missing. New `stage_file_on_main`.
      - `project_image_settings` takes `report=` in place of `clock=`. With a report it writes `stage image: built <identity> at <commit> in <s> s` and `stage image: failed at <commit>`, and the stop's detail starts with `at <commit>: `. Without a report it behaves as before.
      - `_whole_seconds` is shared by the fault text and the built line.

    Main choice: I compare the stage file's text, not `StageLayer.digest`. Equal text means an equal digest, and the text also covers a file that breaks the rule and so has no digest. I rejected computing the digest separately, because a refused file would then need its own case. The human confirmed this in entry 11.

    Refactor: I read the diff once against `main`. Nothing needed changing. There is no existing helper for the 12-digit commit: other modules slice `[:12]` inline, and I left them alone.

    What the journal changed: only the test path (entries 11 and 15). The Description stays as it is.

    Noticed, not touched:
    - A failed fetch in `prepare` now fails that iteration through the scheduler's catch-all, which logs `iteration failed` and retries at the next tick. The human accepted this for now in entry 11.
    - The start's own build also writes a `built` line.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 42 known, 0 gone
18. factory: started review as vm.
19. reviewer: Review, round 0. I read the work item, `git diff main...HEAD -- . ':!factory'` (`src/factory/entry/run.py`, `src/factory/entry/wiring.py`, `tests/entry/test_run_project_image_rebuild.py`) and the code it calls: `stage_layer`, `Images.build`, `build_tick`, `Tick` and `TickStatus`.

    Groups 1 to 3 hold:
    - Group 1, the criteria: criteria 1 to 7 each have a test that checks what the criterion says. The three rows of criterion 6 each have their own expectations. The 12-digit commit is checked in the stop's detail and in every log line. The coder's `make check` was green (entry 17).
    - Comparing the text instead of `StageLayer.digest` is equivalent, because the digest is the sha256 of the text (`src/factory/domain/stage_layer.py:43`). The human accepted it in entry 11.
    - Criterion 7 rests on `Images.build` removing untagged images (`src/factory/application/images.py:31`).
    - Group 2, architecture, and group 3, security: no findings.

    `make duplicates` reports 1 new finding: `FakeImages` unused in `src/factory/adapters/fake_images.py`. This diff does not touch that file, so it is not a finding here.

    Findings:
    1. `tests/entry/test_run_project_image_rebuild.py:124` `_commit`: copies `remote_commit` of `tests/git_support.py:174` (`git rev-parse` of a branch in the bare remote). Fix: use `remote_commit(remote, "main")` and slice it to 12.
    2. `tests/entry/test_run_project_image_rebuild.py:128` `_remove_stage_file`: copies `remove_from_main` of `tests/application/test_tick_preflight.py:80`, plus the fetch, checkout and push of `HumanClone._on_branch` and `_push` (`tests/human_clone.py:57`). It also sets its own committer instead of `TEST_IDENTITY`. Fix: add a `HumanClone.remove_file(branch, path)` beside `push_file` in `tests/human_clone.py` and use it here.
    3. `tests/entry/test_run_project_image_rebuild.py:211` `World._lines`: copies `log_lines` of `tests/log_support.py:6` (reads `state/factory.log`, empty when missing). Fix: filter `log_lines(tmp_path)` by `MARK`.
    4. `src/factory/entry/run.py:201-205`: the `_ProjectImageStart` docstring says the tick's status "lives in memory and counts across ticks". But `_choose` builds a new `Tick` on every change of the stage file, so the error counts (`TickStatus`, `src/factory/application/tick.py:85`) start again at zero. Neither the docstring nor the journal says so. Fix: either carry the previous tick's status into the new tick, or say in the docstring that a rebuild resets the error counts.
    5. Work item, criterion 9: it asks for "the four log lines", but the Interface and the smoke test name three (`built`, `back to the base at`, `failed at`). The documenter writes from this criterion. Fix: change it to "the three log lines".

    Earlier tests: none. The diff adds `tests/entry/test_run_project_image_rebuild.py` and changes no test file that `main` holds.
