---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 393
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T07:24:30.689413Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T07:24:30.695613Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T07:24:49.123567Z'
  stage: intake
  run: d4d5f60cafb242b0bb5e0079f8f745d0
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T07:25:09.675925Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T07:26:31.008801Z'
  stage: tests
  run: f23fc265dea8406c8779a843227c2269
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T07:26:51.731788Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T07:28:27.452861Z'
  stage: doing
  run: 52c9f9cbb1e348e08f714632f85282b3
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T07:28:48.177418Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T07:29:06.322122Z'
  stage: review
  run: 1e9adf003bf0461eb71ef1af9b2b3e9c
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T07:29:29.347217Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T07:30:18.440649Z'
  stage: docs
  run: 183e5afc95a54301a8f2d5f55546745c
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-21T07:30:40.241479Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-21T07:31:11.824986Z'
  stage: smoke-test
  run: 11d749de11524233a3ed18b8084a397e
---

# The decision log marks two superseded entries, the removal of `factory/v1/`, and where its codes come from

## Description

`docs/decisions.md` is read before any change of the architecture (`CLAUDE.md`, *Architecture*), and an agent that searches it by topic finds the oldest entry first. Only the superseding entry says "this supersedes"; two superseded entries carry no mark and read as the current rule: *No `mutants` target, no mutmut*, superseded by *Mutation testing is limited to one feature's modules*, and *The four documents are checked by a command, outside `make check`; v1's words live in one section*, superseded for the docs stage by *The document check runs in the docs stage; the default identity has one home* and for the guide's layout by *The project guide is an index and one file per domain* (it still names `docs/project-guide.md`, one file). The handover entry, *factory-rf is built by v1.1 since the handover*, says v1's files "moved to `factory/v1/`" with no line for their removal on 2026-10-19. And the log cites planning codes (R-numbers, WE, L and Q codes, kept things, v1's features F0001 to F0017) without saying where they are defined. This story adds four lines (findings H7, M12 and the decision log's part of M6 of the documentation review of 2026-10-20). It renames no entry and changes no other text. The marks on the mutation entries after *Mutation testing is limited to one feature's modules* are F0032-S0001's. An index of the log and a status line on every entry (the review's structural proposal S2) are the human's to decide.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/decisions.md`, four additions, and no heading and no other line changes:
   - The header paragraph under `# Decisions` gains, at its end: "Older entries cite the planning records by code: the requirement numbers R1 to R34 (`CLAUDE.md` names R3, R5 to R13 and R17; an R14 or R15 beside an agent's rule is that rule's number in the agents' `## Rules`), the codes WE, L and Q, the kept things and v1's features F0001 to F0017. Those records are kept at the tag `planning-history-2026-10-19`."
   - Directly under the heading `` ## No `mutants` target, no mutmut ``, before its text, a paragraph of its own: "Superseded by *Mutation testing is limited to one feature's modules*."
   - Directly under the heading `` ## The four documents are checked by a command, outside `make check`; v1's words live in one section ``, before its `Date:` line, a paragraph of its own: "Superseded for the docs stage by *The document check runs in the docs stage; the default identity has one home*, and for the project guide's layout by *The project guide is an index and one file per domain*."
   - In *factory-rf is built by v1.1 since the handover*, directly after the bullet that begins "- Decision: v1's", one bullet: "- On 2026-10-19 `factory/v1/` was removed with the planning history; both are kept at the tag `planning-history-2026-10-19`."
   - Each title the new lines cite is a heading of the log. `make documents` ends with `documents ok`.

## Smoke test

```bash
f=docs/decisions.md
sed -n '/^## No `mutants` target, no mutmut$/,/^The acceptance reviewer/p' "$f" | grep -c -F "Superseded by *Mutation testing is limited to one feature's modules*."
sed -n '/^## The four documents are checked by a command/,/^Date:/p' "$f" | grep -c -F 'Superseded for the docs stage by *The document check runs in the docs stage; the default identity has one home*'
grep -c -F -e '- On 2026-10-19 `factory/v1/` was removed with the planning history' -e 'Those records are kept at the tag `planning-history-2026-10-19`.' "$f"
for t in "Mutation testing is limited to one feature's modules" 'The document check runs in the docs stage; the default identity has one home' 'The project guide is an index and one file per domain'; do grep -c -x -F "## $t" "$f"; done
```
Expect: six lines, `1`, `1`, `2`, `1`, `1` and `1` (both marks stand under their headings, the removal bullet and the header sentence are there, and each cited title is a heading)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/decisions.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for this story. It changes only `docs/decisions.md`, and the Interface says that nothing under `src/`, tests, image, template, demo or agents changes. There is no signature or behaviour to specify.
   - Criteria: each is checkable by one test or command. Criterion 1 is a path diff. Criterion 3 gives the exact text and place of each of the four additions, so there is nothing to interpret. The Interface states no rule, so there is no failing side to cover. I checked that the cited titles are headings of the log: *Mutation testing is limited to one feature's modules* (line 359), *The document check runs in the docs stage; the default identity has one home* (351), *The project guide is an index and one file per domain* (698). The headings *No `mutants` target, no mutmut* (13), *The four documents are checked by a command, ...* (343) and *factory-rf is built by v1.1 since the handover* (554) are also present. The bullet that begins "- Decision: v1's" exists at line 558.
   - Smoke test: the commands are runnable and each `Expect:` is checkable. The `sed` ranges end at the `^The acceptance reviewer` line (line 15) and at `^Date:` (line 345), and both exist. The expected counts follow from the criteria: `1`, `1`, `2` (two lines match), then one heading each. No pytest command is involved, so there is no `-q` issue.
   - Architecture: this is a documents-only change to the decision log, which the documenter keeps. Nothing touches the layers, the wrappers or the interfaces.
   - Scope: it matches `feature.md`, whose scope lists S0005 with findings H7, M12 and M6 for `docs/decisions.md`. It leaves out the mutation entries after *Mutation testing is limited to one feature's modules*, which are F0032's, and the S0009 items. It changes no test of another story.
4. factory: started tests as self.
5. tester: No tests written: this story only edits the docs, and criterion 1 forbids any change under `tests/`.
   - criterion 1: no test. The story requires that nothing changes under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. I changed nothing there; the smoke test's `git diff --name-only origin/main -- src tests ...` checks it.
   - criterion 2: no test. The factory checks it by running `make check`.
   - criterion 3 (docs): no test. The documenter makes the four additions to `docs/decisions.md`; the smoke test's greps and `make documents` check them.
   Files created: none. Modules the test run could not import: none (no new tests). I did not run `make test`: with no new tests, there is nothing to watch fail. `make lint` is green.

   `lint`: lint: green (0.6 s)
   `test`: test: green (63.9 s)
6. factory: started doing as self.
7. coder: No code written: this story only changes the docs. Its Interface is "None", and the documenter makes the four additions to `docs/decisions.md`.
   - criterion 1: I changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. `git status --short` shows only the factory's own `.costs.jsonl` sidecar.
   - criterion 2: I ran `make check` on the unchanged tree and it is green (`test: green (67.4 s)`, `check: green`).
   - criterion 3: left to the documenter, as the work item says. I did not write `docs/decisions.md`, because the coder does not write the four documents (`CLAUDE.md`, *Docs*).
   Main choice: I ended with no change rather than making the documentation edits early. The alternative I rejected was writing the four lines now, which would go against the doc ownership in `CLAUDE.md` and the story's Interface.
   Refactor: there is no diff, so there was nothing to refactor. The journal did not change the task's meaning, so `## Description` stays as it is.
   Noticed, not touched: nothing.

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The only changes on the branch are the work item's `.md` and its new `.costs.jsonl` sidecar, both under `factory/`.
   - 1. Acceptance criteria: criterion 1 holds, because nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed. The tester (entry 5) and the coder (entry 7) each say so. Criterion 2: the coder's entry records `check: green`. The Interface is "None" and states no rule or limit, so no failing side or boundary needs a test. Criterion 3 is the documenter's.
   - 2–4. Architecture, security, quality: no code in the diff, so nothing to judge.
   - 5. Work item hygiene: the Description matches what was built (nothing yet; the documenter makes the four additions). The coder's journal explains its one choice, leaving `docs/decisions.md` to the documenter, and what it rejected. The docs criterion is still correct against `docs/decisions.md` on this branch: the three titles it cites are headings at lines 359, 351 and 698. The three headings it edits under are at lines 13, 343 and 554. The bullet "- Decision: v1's" is at line 558, and the header paragraph under `# Decisions` is at line 3.
   - 6. Earlier tests: no test file is changed, renamed or deleted; `git diff --name-status main...HEAD` lists no file outside `factory/`.
10. factory: started docs as self.
11. documenter: Files changed: `docs/decisions.md` only, the four additions of criterion 3.
    - The header paragraph under `# Decisions` now ends with the sentence on the planning codes and the tag `planning-history-2026-10-19`. It was appended to the existing last line, so git shows that line as changed.
    - `## No `mutants` target, no mutmut` opens with its own paragraph "Superseded by *Mutation testing is limited to one feature's modules*."
    - `## The four documents are checked by a command, ...` opens, before its `Date:` line, with the paragraph naming the two entries that supersede it.
    - `## factory-rf is built by v1.1 since the handover` gains the bullet on the removal of `factory/v1/` on 2026-10-19, directly after the "- Decision: v1's" bullet.

    No heading and no other line changed.

    Checks run:
    - The smoke-test greps give `1`, `1`, `2`. `make documents` ends with `documents ok`.
    - I did not re-run the heading-count and path-diff smoke commands. The reviewer confirmed the three cited titles are headings of the log, and I touched nothing outside `docs/decisions.md`.
    - I did not run `make check`: only a document changed, so the factory's own run decides.

    Cross-read: I read the header, the three entries I edited and the handover entry against the story. They are consistent. The diff holds no code, so there was nothing else to cross-read.

    Stale text noticed and not touched: none. No findings.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test passed: I ran the three commands from the repository root exactly as written, and every one met its `Expect:` line. No findings.

    Command 1 (the marks under their headings, the removal bullet with the header sentence, and the cited titles as headings):
    ```
    1
    1
    2
    1
    1
    1
    ```
    Met: six lines, `1`, `1`, `2`, `1`, `1`, `1`.

    Command 2 (the path diff against `origin/main`):
    ```
    0
    docs/decisions.md
    ```
    Met: two lines, `0` and `docs/decisions.md`.

    Command 3 (`make documents 2>&1 | tail -n 1`):
    ```
    documents ok
    ```
    Met.

    Acceptance criteria, read again against the results:
    - Criterion 1: the path diff shows no change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. Entries 5 and 7 say the same.
    - Criterion 2: the smoke test does not run `make check`. The latest run recorded in the journal is green, and the factory runs the check itself.
    - Criterion 3: I read `git diff origin/main -- docs/decisions.md`. It holds exactly the four additions, each word for word as the criterion gives it and in the place it names:
      - the sentence at the end of the header paragraph (git shows that existing line as changed, because the sentence is added to it);
      - the paragraph of its own directly under `` ## No `mutants` target, no mutmut ``;
      - the paragraph of its own directly under the four-documents heading, before its `Date:` line;
      - the bullet directly after "- Decision: v1's" in the handover entry.
      
      No heading changed and no other line changed. Each cited title is a heading of the log (command 1).

    The smoke test contradicts no criterion. Nothing is open.
