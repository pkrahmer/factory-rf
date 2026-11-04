---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 531
comments_read: []
handed_over: null
claim: null
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
