---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 437
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T08:23:26.935345Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T08:23:26.940839Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-25T08:23:44.766570Z'
  stage: intake
  run: 193bff25c1d843d09e7042ef58b353cc
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-25T08:24:05.105201Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-25T08:30:53.349642Z'
  stage: tests
  run: d9f2d1afeb27481589e71ab2fce8e787
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-25T08:31:14.073910Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-25T08:34:53.903274Z'
  stage: doing
  run: d4c9d65504df427b8d4d656aecf0aa37
---

# The chapter "The machine" names all three secrets in every place

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

The operator guide's chapter `## The machine` disagrees with itself on which secrets the VM needs. *On GCP, step by step*, step 8, and decision 10 of `feature.md` say that all three files must exist in `/home/factory/.secrets` (`hosting-token`, `claude-token`, `anthropic-api-key`), because `vm/setup.sh` writes all three paths into `factory.env`, the factory mounts every login file that is set (`login_paths` in `factory.adapters.agent_launch`), and podman refuses to mount a missing file (exit status 125). But *The script*, "The two passes", tells the operator to place "the token, and the login file for your runtime (`claude-token` or `anthropic-api-key`)". An operator who follows that section and places two files gets agent runs that stop at podman's mount. Step 8 itself gives the wrong reason: it says "An empty `anthropic-api-key` means no key: podman refuses to mount a missing file". The emptiness rule and the missing-file rule are two separate facts, and that sentence joins them with "because". The chapter's *The stage image* also sends the operator to *Update the pins* under "The machine's image" for `vm/Dockerfile`. That list names eight Debian packages including `sudo`, but `vm/Dockerfile` has seven and no `sudo`, so an operator who follows it looks for a pin that is not there. This story corrects those three passages. Nothing else in the chapter changes. What stays: every other sentence of the chapter, `vm/setup.sh`, and the code. The chapter of v1.1's image, which F0044 (the layers go) removes, stays too.

## Interface

None: nothing changes under `src/factory/`, in any test, under `vm/`, `image/`, `template/` or `claude/`. The documenter changes `docs/operator-guide.md` only. No test reads the documents: the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `docs/operator-guide.md`, chapter `## The machine`; the smoke test and `make documents` check these, and no test does:
   - "The two passes" (under *The script*) tells the operator to place all three files, `hosting-token`, `claude-token` and `anthropic-api-key`, in `/home/factory/.secrets`. It says that all three must exist whatever the runtime, and that the key file stays empty with the `claude` runtime. It no longer contains the words "the login file for your runtime".
   - *On GCP, step by step*, step 8, gives the two facts as two sentences. First: all three files must exist, because the factory mounts every login file the environment file names and podman refuses to mount a missing one (exit status 125). Second: an empty `anthropic-api-key` means no key. It no longer contains "means no key: podman".
   - *The stage image* names the seven Debian packages of `vm/Dockerfile` (`git`, `make`, `curl`, `ca-certificates`, `procps`, `nodejs`, `npm`). It says that `sudo` is pinned in `image/Dockerfile` alone, and that a changed pin is checked with `uv run pytest tests/test_stage_image.py tests/test_image.py`.
   - No other section of the guide changes, and `make documents` ends with `documents ok`.

## Smoke test

```bash
c=$(awk '/^## The machine$/{on=1; next} /^## /{on=0} on' docs/operator-guide.md); printf '%s\n' "$c" | grep -c -F 'the login file for your runtime'; printf '%s\n' "$c" | grep -c -F 'means no key: podman'
```
Expect: two lines: `0`, `0`

```bash
awk '/^#### The two passes$/{on=1; next} /^#/{on=0} on' docs/operator-guide.md | grep -c -F 'anthropic-api-key'
awk '/^### The stage image$/{on=1; next} /^#/{on=0} on' docs/operator-guide.md | grep -c -F 'tests/test_stage_image.py tests/test_image.py'
```
Expect: two lines, each a number of at least `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: it says "None" and names the one file that changes (`docs/operator-guide.md`, by the documenter). No module or signature is needed, and none is stated.
   Criteria: criterion 1 (no change under `src/`, `tests/`, `vm/`, `image/`, `template/`, `claude/`) and criterion 2 (`make check`) are checkable. The three docs bullets each have a verifiable pass side (all three files in "The two passes", two sentences in step 8, seven packages plus the `sudo` and pytest sentences in "The stage image") and a verifiable fail side (the phrases `the login file for your runtime` and `means no key: podman` must be gone). I found those phrases in the guide at lines 493 and 618. Line 444 of "The stage image" does send the operator to "Update the pins" and does not yet name the pytest command.
   Smoke test: the awk/grep commands match the guide's headings (`## The machine`, `#### The two passes`, `### The stage image`), and each `Expect:` line is checkable. The pytest-`-q` rule does not apply, because no command runs pytest. The `make documents` command ends with `documents ok`, which `check_documents.py` prints.
   Architecture: this is a documentation change only, and the docs stage owns `docs/operator-guide.md`. No layer is touched.
   Scope: the story stays inside the F0043 chapter "The machine". It follows decision 10 and the chapter-writing split of decision 2, and it touches nothing listed in Out of scope. `image/` and `vm/` are explicitly left unchanged.
4. factory: started tests as vm.
5. tester: No tests written. This story changes only the documents: the Interface says "None", and the criteria say that no test reads the documents.
   criterion 1 (nothing under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/` changes): no test. I changed nothing in the working tree, under `tests/` or anywhere else. `git status` was clean before the runs.
   criterion 2 (`make check` stays green): no test of its own. The factory's checks cover it. `make test` ran once and ended with `test: green (196.1 s)` (coverage 99.20 %). `make lint` ended with `lint: green`.
   criterion 3 (docs, `docs/operator-guide.md` chapter `## The machine`): no test, as the criterion says. The smoke test and `make documents` check it after the docs stage.
   Files created: none. Every module imported, because no new test imports anything.
   Open: nothing. The coder has no red test to turn green. Per criterion 1, the coder ends with an entry saying that nothing under those paths changed.

   `lint`: lint: green (0.2 s)
   `test`: test: green (194.0 s)
6. factory: started doing as vm.
7. coder: Nothing built. Criterion 1: nothing changed under `src/`, `tests/`, `vm/`, `image/`, `template/` or `claude/`. The story only corrects `docs/operator-guide.md`, which the documenter writes, and the tester left no red test. The working tree was clean when I started and is still clean.
   Main choice: I made no code change. The other option was to edit the guide here, and I rejected it: CLAUDE.md gives the documents to the documenter stage, and the Interface says "None". The journal did not change what the task means, so I left the Description as it was. There was no diff, so there was nothing to refactor.
   Noticed, not touched: nothing.

   `check`: check: green (test: green (196.2 s), coverage 99.20 %)

   `check`: check: green (not run again: passed on tree 63d480b4dec3 at 2026-10-25T08:00:52Z)
   `duplicates`: duplicates: 11 new, 36 known, 2 gone
