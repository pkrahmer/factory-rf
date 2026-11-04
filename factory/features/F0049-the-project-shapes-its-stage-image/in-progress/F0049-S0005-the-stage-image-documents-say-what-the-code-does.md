---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 531
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs
  started_at: '2026-11-04T02:51:16.547907Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-04T02:47:43.349560Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-04T02:47:43.356327Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-04T02:48:04.403932Z'
  stage: intake
  run: d3e10aeda0b8496bb6a907edebf8c74f
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-04T02:48:10.520705Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-04T02:48:38.693193Z'
  stage: tests
  run: 7322f29916944d1f9e4dc27b2bc50983
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-04T02:48:44.549509Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-04T02:50:44.491525Z'
  stage: doing
  run: d2f1efcd56214ec194521d97ace62d15
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-04T02:50:50.446091Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-04T02:51:10.430935Z'
  stage: review
  run: 3484b19b9e944a3899b4cb277ba8da56
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-04T02:51:16.547907Z'
  stage: docs
---

# The stage image's documents say what the code does and why

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

Three stories wrote the documents of the project's stage image, each from its own criterion, and the feature acceptance F0049-A0001 found where they now differ from the code or leave out the human's reasons. In `docs/operator-guide.md`, *The stop `stage_image_failed`* says a build that reaches its 30-minute limit "gives the same text" as a failed build, its last 20 lines; the code gives `the stage file did not build in <s> s:` followed by podman's message that the command did not end within its time limit, and no build output (the coders noted it in F0049-S0002 entries 16 to 42, and the human kept the behaviour in entry 17). The same section says "A restart of `factory-run` also ends it"; a restart builds the same file again, so it ends the stop only when that build now passes (after a passing network fault, for instance) and raises it again otherwise. *The project's stage file* says that without the file "nothing changes"; the image and the identity stay the base's, but the containers now take the `PATH` the base image configures, read by `podman image inspect`, in place of the fixed `/usr/local/bin:/usr/bin:/bin`. In `docs/decisions.md`, the entry "A project adds a layer to the stage image with `factory/stage.Containerfile`" cites decisions 1, 3 and 4 of the feature but gives none of their reasons or rejected options, because its documenter may not read `feature.md`; and it still says the stop "ends with the next start", which the next entry replaced. This story writes the reasons into the story itself (below), so the documenter may carry them. No code changes.

## Interface

- No module under `src/factory/` changes, and no test: the story changes `docs/operator-guide.md` and `docs/decisions.md` only.
- The reasons the documenter carries into `docs/decisions.md`, from `feature.md` of F0049 (the human, 2026-11-04):
  - Decision 1, a Containerfile and not a list of packages. Why: Debian's own packages hold only Node 18 and Java 17, so a list of packages would need a recipe in the factory for every stack, and the shared image's growth would come back as a growing catalogue; a Containerfile covers every stack with no knowledge in the factory, and reading it from `main` alone, which the human merges, covers the build's commands running with the network. Rejected: a package list with a catalogue, `mise.toml` (language runtimes only, no system libraries), named stack images (the factory grows with every stack).
  - Decision 3, one image for every stage, named in one place of the code. Why: no second line exists yet, so its needs are unknown; the one place lets a later feature give a line or a role an image of its own without changing every caller.
  - Decision 4, the build sees no files. Why: what the image holds then comes only from the file's text and the network, so the file's hash and the base's identity name the image; the project pins its own versions and checksums. Taken for the human.
  - Decision 5, the factory rebuilds by hash between stages. A second reason beside the one the entry has: a Cloud Run job builds at every start anyway.

## Acceptance criteria

1. `docs/operator-guide.md`, *The stop `stage_image_failed`*: a build that reaches its time limit is described as giving `the stage file did not build in <s> s:` followed by podman's message that the build did not end within its limit, without build output; the phrase "gives the same text" is gone.
2. The same section: the sentence "A restart of `factory-run` also ends it." is replaced by one saying that a restart builds the same file again, which ends the stop when the build passes and raises it again when it fails.
3. `docs/operator-guide.md`, *The project's stage file*: the sentence on a project without the file names the base image, the base's identity and the `PATH` the base image configures (the default `/usr/local/bin:/usr/bin:/bin` only when it configures none), in place of "nothing changes".
4. `docs/decisions.md`, the entry "A project adds a layer to the stage image with `factory/stage.Containerfile`": its Why carries the reasons of decisions 1, 3 and 4 as the Interface states them, its Rejected line names the package list with a catalogue, `mise.toml` and named stack images beside the `repository` scope, and its sentence that the stop "ends with the next start" says that the next entry replaced it. The entry "The factory follows `main` for the stage file, between two stages" adds the Cloud Run reason of decision 5.
5. `make check` stays green.
6. docs: `docs/operator-guide.md` and `docs/decisions.md` as criteria 1 to 4 say; `README.md`: none, its one sentence on the stage file stays true; the project guide: none, `stage-environment.md` names the seams and they do not change.

## Smoke test

```bash
grep -c 'gives the same text' docs/operator-guide.md
grep -c 'A restart of `factory-run` also ends it' docs/operator-guide.md
grep -c 'mise.toml' docs/decisions.md
uv run python -m factory.entry.check_documents
```

Expect: `0`, `0`, `1`, then `documents ok`.

## Journal

1. 2026-11-04 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: no module or signature changes, by design (docs only). It names `docs/operator-guide.md` and `docs/decisions.md` and states the reasons of decisions 1, 3, 4 and 5 in full for the documenter. It states no behaviour that needs a test.
   - Criteria: criteria 1 to 4 each name a section and the exact text that must be gone or present. I checked the current files: "gives the same text" and "A restart of `factory-run` also ends it" each occur once, and the decisions entry still says "ends with the next start". Each criterion can be checked by one test function, and none has a failing side beyond the text being absent. Criterion 5 (`make check`) and criterion 6 (`docs:`) are the last two.
   - Smoke test: the greps and `uv run python -m factory.entry.check_documents` (the module exists) are runnable. `grep -c` prints 0 when nothing matches, so the Expect `0`, `0`, `1`, then `documents ok` can be checked line by line. `mise.toml` has no match in `docs/decisions.md` today, so the count of 1 is met only after the change. No pytest command is used, so the `-q` rule does not apply.
   - Architecture: nothing in the code layers is touched. The change stays in the docs the documenter keeps. The story needs nothing from `factory/`, `CLAUDE.md` or the project guide.
   - Scope: the story fits F0049. It corrects the documents of S0002 and S0003 and carries decisions 1, 3, 4 and 5 of `feature.md`. It leaves out the feature's Out of scope items (per-line images, an open build context, a registry).
4. factory: started tests as vm.
5. tester: No tests written, on purpose. The story's Interface says "No module under `src/factory/` changes, and no test: the story changes `docs/operator-guide.md` and `docs/decisions.md` only", and the intake found that it "states no behaviour that needs a test". Criteria 1 to 4 are about document text that only the documenter may write. A test of that text would fail in the doing stage, the coder cannot make it pass (`docs/` is outside the coder's write paths), so `make check` would stay red until the docs stage. I rejected writing such tests because they would contradict the Interface and block the coder.
   - criterion 1 (time-limit text in *The stop `stage_image_failed`*): no test. The smoke test's `grep -c 'gives the same text'` and the docs stage check it.
   - criterion 2 (restart sentence): no test. The smoke test's `grep -c 'A restart of \`factory-run\` also ends it'` checks it.
   - criterion 3 (project without the stage file: base image, identity, `PATH`): no test. The docs stage checks it.
   - criterion 4 (decisions entries: reasons of decisions 1, 3, 4 and 5, Rejected line, the replaced stop sentence): no test. The smoke test's `grep -c 'mise.toml'` and `check_documents` check it.
   - criterion 5 (`make check` green): no test of its own. The factory's checks cover it.
   - criterion 6 (docs): the documenter's criterion.
   Files created: none. Modules the test runner could not import: none, because no test was added and so `uv run pytest` was not run. `make lint` is green, and the working tree is unchanged. The coder has nothing to implement: no code changes, and the documenter writes criteria 1 to 4.

   `lint`: lint: green (0.2 s)
6. factory: started doing as vm.
7. coder: Nothing built, on purpose. The Interface says that no module under `src/factory/` and no test changes, because the story changes only `docs/operator-guide.md` and `docs/decisions.md`. Both are outside the coder's write paths: the documenter writes them in the docs stage from criteria 1 to 4. The tester wrote no tests, so `make test` had no failures to work from.
      - Paths changed: none. The working tree is unchanged.
      - Main choice: hand the work item forward with no change. I rejected writing the document corrections myself: `CLAUDE.md` gives `docs/` to the documenter, and a write there would be dropped from the take anyway. I also rejected adding code or tests to have something to show, because that would be outside the Interface (R13).
      - Refactor: no diff, so nothing to refactor.
      - Description: the journal did not change the task's meaning, so `## Description` is unchanged.
      - Noticed but not touched: the stale texts the criteria name are still in place for the documenter. These are "gives the same text" and "A restart of `factory-run` also ends it" in `docs/operator-guide.md`, and "ends with the next start" in `docs/decisions.md`, which also has no mention of `mise.toml` yet.
      - `make check`: green. It ended with `test: green (86.3 s)`, then `check: green`, at 99.51 % coverage.

   `check`: check: green (not run again: passed on tree da88284d442d at 2026-11-04T02:41:58Z)
   `duplicates`: duplicates: 0 new, 43 known, 0 gone
8. factory: started review as vm.
9. reviewer: no findings

   Review of `git diff main...HEAD -- . ':!factory'`: the diff is empty. The branch changes only the work item and its `.costs.jsonl` sidecar. That matches the Interface ("No module under `src/factory/` changes, and no test"). Criteria 1 to 4 are text in `docs/operator-guide.md` and `docs/decisions.md`. Only the documenter writes those files, from this story's criteria.
   - Group 1 (criteria): criteria 1 to 4 have no pytest test. I accept the tester's reason in entry 5: a test of document text would stay red in the doing stage, because the coder cannot write `docs/`. The smoke test's three greps and `check_documents` check these criteria after the docs stage. Criterion 5: the coder's `make check` was green (entry 7). The Interface states no rule with a failing side and no limit.
   - I checked the Description's claims against the code. They hold, so the documenter can write from them:
     - `src/factory/entry/wiring.py:449` builds `the stage file did not build in <s> s:` followed by the build's output tail.
     - `src/factory/application/images.py:37` and `src/factory/domain/containers.py:17` give the image's `PATH`, or `/usr/local/bin:/usr/bin:/bin` when the image sets none.
     - The stale texts the criteria name are still in place: `docs/operator-guide.md:513` ("nothing changes"), `:564` ("gives the same text"), `:568` ("A restart of `factory-run` also ends it"), and `docs/decisions.md:1462` ("ends with the next start"). `mise.toml` is not in `docs/decisions.md` yet.
   - Group 2 (architecture), group 3 (security) and group 4 (quality): nothing to judge, because no code changed.
   - Group 5 (work item hygiene): entries 5 and 7 say why no test or code was written and what was rejected. The Description matches the plan. Criterion 6 names the two documents to change and says why `README.md` and the project guide need no change.
   - Item 6 (earlier tests): none changed.
10. factory: started docs as vm.
