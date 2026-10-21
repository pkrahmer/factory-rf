---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 392
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T07:16:35.228911Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T07:16:35.234782Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T07:16:57.095265Z'
  stage: intake
  run: deda32883f35419d949ea4219e79a4c8
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T07:17:18.876803Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T07:18:38.667964Z'
  stage: tests
  run: c699daf711754ebd9b43a6d7efa3d120
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T07:18:59.948844Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T07:20:32.216263Z'
  stage: doing
  run: f5077f9807ed4b8688a5d6c9083e51dc
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T07:20:52.969497Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T07:21:06.712971Z'
  stage: review
  run: 194e62c2e51b41f6aa78212a40880f9a
---

# The project guide names no planning code or v1 feature id as a pointer

## Description

The project guide's files point into planning records that left the tree on 2026-10-19 (they are kept at the tag `planning-history-2026-10-19`): requirement numbers that `CLAUDE.md` does not name (R20, R21, R22, R24, R28), "kept thing" numbers, "questionnaire 1, Q29", and v1's feature ids F0004 to F0009 used as references ("F0008's tests", "F0005 uses `read`", the table *Which feature uses which operation*). An agent cannot follow them, and the house rule is that an id comes with its short name (finding M6 of the documentation review of 2026-10-20, its part in the guide files). This story replaces each such pointer with the plain name of what it refers to, or removes it where the sentence already says it. These stay, because a reader can resolve them: the requirement numbers that `CLAUDE.md` names (R5, R8), the agents' rule numbers R10, R14 and R15 (in every `## Rules` of `claude/agents/`), and example ids such as `F0001-S0001`, `F0004-x` and `FEATURE=F0012`. `processes-and-checks.md` is not touched. The decision log's codes are F0038-S0005's.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes `docs/project-guide/README.md`, `agents.md`, `costs.md`, `git-and-hosting.md`, `stages.md` and `watching.md`, each only in the passages below.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: each old text below becomes its new text (`""` means it is removed with the space before it), and nothing else in the guide changes:
   - `README.md`, *Kill points*: "F0008's tests arm" → "the recovery tests arm".
   - `agents.md`: "(R24: no partial figure; the first call's alone would be one)" → "(no partial figure: the first call's alone would be one)"; "F0005 uses `read` to compose every task" → "Starting a stage uses `read` to compose every task"; " (questionnaire 1, Q29)" → ""; "(F0009 reads them;" → "(the acceptance reads them;".
   - `costs.md`: "discarded with the stage (F0008)." → "discarded with the stage."; "a reported zero stays zero (R24)." → "a reported zero stays zero.".
   - `git-and-hosting.md`: in "Who uses them: preparing a stage merges ...", " (F0005)" and " (F0007)" → "". The sentence "Who uses them: a stall or a crash reverts or resets (F0004, F0005, F0008); ..." becomes "Who uses them: a stall or a crash reverts or resets; the tick resets the checkout to the remote; the undo's revert is this wrapper's, and the rules for what to revert are the undo's (`write-guard.md`); a merge or a discard moves the story file." The heading *Which feature uses which operation* becomes *Which part uses which operation*, and its table's *Used by* cells name the part, not a feature: "F0004: the undo compares" → "the undo: compares"; "F0005: preparing a stage merges" → "the stage's preparation: merges"; "F0006: the tick looks" → "the tick: looks"; "also F0004, F0005 and F0008: a stall or a crash" → "also the undo, the stage's preparation and the crash recovery: a stall or a crash"; "F0007: a merge or a discard" → "the merge and the discard"; "F0023: the key of a known project-command result (S0002) is the tree" → "the known results: the key of a known project-command result is the tree". "F0027: after every agent run (`run_sealed`) and at the restore (the tick)" → "the sealed run and the restore: after every agent run (`run_sealed`) and at the restore (the tick)". Every other *Used by* cell that starts with a feature id names the part in its place the same way.
   - `stages.md`, *Status*: "reruns its stage at once, R20)" → "reruns its stage at once)"; "does not shorten a running claim (R21)." → "does not shorten a running claim.".
   - `watching.md`: "and R22 puts the human's act first" → "and the human's act comes first"; "the rerun after a crash (F0008) included" → "the rerun after a crash included"; " (kept thing 3)" → ""; " (R28, kept thing 12)" → "".
   - No guide file names *Which feature uses which operation* any more. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -E '\bR2[0-8]\b|kept thing|Q29|questionnaire 1|\bF000[4-9]([^-0-9]|$)|Which feature uses|F0023: |\| F00[0-9]{2}: ' docs/project-guide/*.md
```
Expect: nine lines, each ending in `:0`: `docs/project-guide/README.md:0`, `docs/project-guide/agents.md:0`, `docs/project-guide/costs.md:0`, `docs/project-guide/git-and-hosting.md:0`, `docs/project-guide/processes-and-checks.md:0`, `docs/project-guide/stages.md:0`, `docs/project-guide/watching.md:0`, `docs/project-guide/work-items.md:0`, `docs/project-guide/write-guard.md:0`

```bash
grep -c -F -e '### Which part uses which operation' -e 'the stage'"'"'s preparation: merges' docs/project-guide/git-and-hosting.md
grep -c -F 'the recovery tests arm' docs/project-guide/README.md
```
Expect: two lines, `2` and `1`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: seven lines, `0`, then `docs/project-guide/README.md`, `docs/project-guide/agents.md`, `docs/project-guide/costs.md`, `docs/project-guide/git-and-hosting.md`, `docs/project-guide/stages.md` and `docs/project-guide/watching.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is stated and correct for a documents-only story. It names the six guide files the documenter changes, and each one has old-to-new rows in criterion 3. I grepped the guide and every old passage is there: README.md:99, agents.md:88/213/303/307, costs.md:7/15, git-and-hosting.md:160/179/181/185-191, stages.md:21, watching.md:117/135/221.
   - Criteria: criterion 1 (no change outside the docs) is checkable by a diff. Criterion 2 is `make check`. Criterion 3 gives exact old and new strings, so a test can assert that each old string is gone and each new one is present. It also says the table cells that start with a feature id are rewritten, which the smoke regex `\| F00[0-9]{2}: ` pins. The heading rename and "no guide file names *Which feature uses which operation*" are checkable. There is no failing-side rule to cover, because the story states no validation or error. The `make documents` result is `documents ok`.
   - Smoke test: all four blocks are runnable. The first has nine files and `grep -c` prints `file:count` for each. In the second, the `-F` grep counts two lines in git-and-hosting.md (the heading and the preparation row) and one in README.md, matching "2 and 1". In the third, the story expects seven lines (one `0` and six docs paths) and each `Expect:` line is checkable against the output. The fourth is `make documents`. No pytest command is used, so the `-q` rule does not apply.
   - Architecture: nothing under `src/` changes, so the layer rules in CLAUDE.md are untouched. The documenter writes only `docs/`, which is its write path, and `processes-and-checks.md` is not touched.
   - Scope: this matches feature.md decision 6 and the *Scope* line for S0004 (M6, guide files only). R5 and R8 (named in CLAUDE.md), the agents' R10, R14 and R15, and example ids stay. The decision log is S0005's and the agent files are S0010's, so the story stays out of both. The only overlap is the `agents.md` sentence with "F0009 reads them". feature.md already orders S0010 after S0004 for that reason.
4. factory: started tests as self.
5. tester: No tests written, on purpose. The Interface says "None: nothing changes under `src/factory/`, in any test, ...". Criterion 1 forbids any change under `tests/`, and I made none.
   - criterion 1 (nothing under src/, tests/, image/, template/, demo/ or claude/ changes): no test function. Writing a test would itself break this criterion. The smoke test's `git diff --name-only origin/main -- src tests image template demo claude | wc -l` checks it, and this entry is the tester's statement that nothing changed there.
   - criterion 2 (`make check` stays green): no test function. It is the stage's check.
   - criterion 3 (docs: old texts become new texts, no guide file names *Which feature uses which operation*, `make documents` ends with `documents ok`): no test function. A pytest test of this would be a change under `tests/`, which criterion 1 forbids. The story's smoke test (the grep counts) and the docs stage's `make documents` check cover it.
   Files created: none. Modules the test run could not import: none, because no new test exists. I did not run `make test`, since it has no new red tests to show. `make lint`: green.

   `lint`: lint: green (0.6 s)
   `test`: test: green (62.5 s)
6. factory: started doing as self.
7. coder: Nothing built, on purpose. The Interface says "None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file". Criterion 1 forbids any change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`, and I made none. My working tree holds no change except the factory's own costs sidecar.
      - Main choice: I left the six guide files alone (`docs/project-guide/README.md`, `agents.md`, `costs.md`, `git-and-hosting.md`, `stages.md`, `watching.md`). `CLAUDE.md` says the documenter stage keeps `docs/project-guide/` true from each story's docs criterion and the coder does not write it, so criterion 3 belongs to the docs stage. Rejected: making criterion 3's text replacements here. That would have gone outside the coder's role.
      - Refactor: there is no diff, so nothing to refactor.
      - The journal did not change the meaning of the task, so `## Description` stays as it is.
      - Noticed, not touched: none.
      `make check`: check: green (test: green, 64.1 s).

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The only changes on the branch are the work item and its `.costs.jsonl` sidecar under `factory/`, which are out of scope.
   - 1, acceptance criteria: criterion 1 (nothing changes under src/, tests/, image/, template/, demo/ or claude/) holds, because the diff is empty. The tester's entry 5 and the coder's entry 7 both say so, as the criterion asks. Criterion 2: the factory's `make check` after the coder is green (entry 7, tree 61b5f6269707). Criterion 3 is the docs criterion. The documenter writes it next, and the smoke test and `make documents` check it. The Interface states no rule or limit, so there is no failing side to test. A pytest test of criterion 3 would break criterion 1, so having no tests is correct.
   - 2 to 4, architecture, security and quality: not applicable. No code, test or configuration changed, and no marker that silences a check was added.
   - 5, work item hygiene: the coder's entry 7 gives the main decision (it leaves criterion 3 to the documenter, because `CLAUDE.md` *Docs* gives `docs/project-guide/` to the documenter) and what it rejected. The Description still matches the story. The docs criterion lists each old and new passage exactly, so the documenter can work from it alone.

   Earlier tests: none. The diff changes, renames or deletes no test file that `main` holds (`git diff --name-status main...HEAD` lists only the work item and its sidecar).
