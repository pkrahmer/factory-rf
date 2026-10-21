---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 396
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T07:55:07.953434Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T07:55:07.960454Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T07:55:36.253315Z'
  stage: intake
  run: 7cf5413a4e934e369ddc48c2d6562b0c
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T07:55:57.765976Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T07:57:36.270893Z'
  stage: tests
  run: 4182b4ab1aad445d87af556377d40304
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T07:57:57.527474Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T07:59:41.744625Z'
  stage: doing
  run: e78567894a6b47e5a7cf7ff95afa0665
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T08:00:02.964507Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T08:00:29.356580Z'
  stage: review
  run: 1a3518573eaa4386bbe56582dc89ecdc
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T08:00:50.736527Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T08:01:27.113310Z'
  stage: docs
  run: b425183decab437a94614fac6a4e8924
---

# The operator guide lists each stop in one table

## Description

`docs/operator-guide.md` describes one stop in up to three tables: *The stops you will see here* (six rows, under *The container: compose, entrypoint and health check*), *The stops* (all fifteen rows, the one `make documents` pins) and *The stops of the tick* (four rows). `checkout_restore_failed` and `pipeline_definition_invalid` are each in all three, and each also has a section of its own. An operator who looks up a stop cannot tell which table is complete, and the wordings drift: three rows of the first table only say "See ..." and "As there". This story makes *The stops* the one table of stop ids, destinations and what to do (finding M1 of the documentation review of 2026-10-20). The six-row table gives way to one sentence that points there, and the facts its rows hold that no other passage holds move into the sections *The stops* already points to. The four-row table gives way to a short paragraph that keeps only what *The stops* lacks: the tick does not touch the checkout while `pipeline_definition_invalid` or `agent_definition_invalid` stands, an expired or revoked token shows as `fetch_failed` and nothing is lost, and what can make `checkout_restore_failed`. The merge of all stop material into one reference and a contents list per stop (the review's structural proposal S1) are the human's to decide; the table of *Stops that cannot be done* (its last errors) stays.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, and no other file:
   - The subsection *The stops you will see here*, its heading and its table, is replaced by one sentence at the end of *The health check and the restart policy*: the stops this container can show in its health status are in "The stops", with what to do about each.
   - What its rows say that the guide says nowhere else is kept in the section the matching row of *The stops* points to: the details `confinement: ...` and `the probe on main could not run: <message>` of `preflight_failed`, and that with an agent user a missing `sudo` rule ends the probe's `lint` as `the probe on main could not run: project command lint failed: <sudo> refused the command: ...`, in "The preflight's items"; the detail forms `lint is red on main at <12 characters of the commit>: <last line of the output>` and `lint reached its time_limit on main at <commit>` of `main_branch_failing` in "The stamp and the probe of the main branch"; and the four detail forms of `repository_unavailable` (`cannot prepare the checkout: <git's message>`, with its hint that the clone failed and `FACTORY_REPOSITORY_URL` and the credentials are to be checked, `cannot fetch: <git's message>`, `the repository has no main branch yet`, `origin/main has no factory/pipeline.yml yet`) in "The wait for a repository that is not ready". A detail already written there is not written twice.
   - In *The stops of the tick*, the table is replaced by a paragraph that names the four stops in backticks (`fetch_failed`, `pipeline_definition_invalid`, `agent_definition_invalid`, `checkout_restore_failed`), points to "The stops" for what to do, and keeps: an expired or revoked token shows as `fetch_failed`, and nothing is lost; the sentence "The tick does not touch the checkout while `pipeline_definition_invalid` or `agent_definition_invalid` stands."; `checkout_restore_failed` comes, for example, from an untracked file or directory the factory cannot remove, or from an ignored folder it cannot empty, and its detail is git's message; and the repair the table's row of `checkout_restore_failed` gives: when an agent run left the path, the stage that ran ends without a result and, once the checkout is repaired, is recorded as a crash and run again; repair with `chmod -R g+w <path>` as root on the path git's message names, or remove it as root; a second run that leaves the same path again reaches the crash cap (`crash_cap`).
   - *The stops*, its table of fifteen rows and every other section stay as they are, and no citation of a removed heading is left: no passage cites "The stops you will see here". `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F -e '| Stop | Meaning | What to do |' -e 'The stops you will see here' -e '| As there. |' docs/operator-guide.md || true
grep -c -F '| Stop | Destination | What you do |' docs/operator-guide.md
```
Expect: two lines, `0` and `1`

```bash
for s in 'the probe on main could not run' 'lint reached its time_limit on main' 'origin/main has no factory/pipeline.yml yet' 'cannot prepare the checkout' 'The tick does not touch the checkout while' 'refused the command' 'chmod -R g+w <path>'; do grep -q -F -e "$s" docs/operator-guide.md && echo found || echo "missing: $s"; done
```
Expect: seven lines `found`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/operator-guide.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is correct for a documents-only story. It names the one file the documenter changes (`docs/operator-guide.md`) and states that nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. There are no signatures to judge.
   - Criteria: each one is checkable by one test or check.
     - Criterion 1 is the empty `git diff` over the code paths.
     - Criterion 2 is `make check`.
     - Criterion 3 is a set of checkable text facts. The old headings and the "As there." rows are gone. The named detail forms and the `chmod -R g+w <path>` repair are present. The sentence about the tick not touching the checkout is kept. The fifteen-row table is unchanged. `make documents` ends with `documents ok`.
     - The failing side of each rule is covered. The old table and the old heading must be absent, and no passage may cite the removed heading.
     - The moves of the detail forms name their target sections: "The preflight's items", "The stamp and the probe of the main branch", "The wait for a repository that is not ready". I confirmed all three exist in the guide at lines 515, 548 and 562.
   - Smoke test: the commands are runnable grep, git and make commands, and each `Expect:` line is checkable. The first `grep -c` counts both old `| Stop | Meaning | What to do |` tables (lines 506 and 927) plus the old heading and the "As there." rows. The `0` therefore needs both tables gone, and the `1` pins the surviving *The stops* table (line 720). No pytest is run, so the `-q` concern does not apply.
   - Architecture: this is docs only and touches no layer. The edit stays within the documenter's write paths (`docs/*`).
   - Scope: the story is within F0038's scope, "the stop tables (S0008; M1)". The review's proposals S1 and S2 are left to the human, as the feature's Out of scope requires. Decision 8 of the feature (move the detail forms, do not drop them) is covered by criterion 3. I did not check that the guide's exact wording matches the quoted detail forms. The documenter and the smoke test will show that.
4. factory: started tests as self.
5. tester: No tests written. This story changes documents only. Its Interface says nothing changes in any test, and criterion 1 says nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes.
   - criterion 1: no test. It is the empty `git diff` over those paths, checked by the smoke test. As the criterion asks: the tester changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`.
   - criterion 2: no test. It is the `make check` the factory runs.
   - criterion 3 (docs): no test. The documenter's change to `docs/operator-guide.md` is checked by `make documents` and the smoke test's greps. A pytest that pins the guide's wording would be a change under `tests/`, which criterion 1 rules out.

   Files created: none. Modules the test runner could not import: none, since no new tests exist. `make lint` is green. I did not run `make test` because no test was added or changed, so nothing new could fail. The factory runs it after this stage. Nothing is open for the coder: the documenter does the work.

   `lint`: lint: green (0.8 s)
   `test`: test: green (72.9 s)
6. factory: started doing as self.
7. coder: No code written. This story changes documents only. Its Interface says nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file, and the documenter alone changes `docs/operator-guide.md`.
   - Criterion 1: as it asks, the coder changed nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`. The working tree holds only the factory's `.costs.jsonl` sidecar.
   - Criterion 2: `make check` is green (`test: green (73.7 s)`, `check: green`).
   - Main choice: hand forward without touching the guide. I rejected editing `docs/operator-guide.md` myself, because `CLAUDE.md` gives the docs to the documenter stage and the story names the documenter as the one who changes it.
   - Refactor: no diff, so nothing to refactor.
   - Description: no journal entry changed the meaning of the task.
   - Noticed but did not touch: nothing.

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar. This fits a story whose Interface is "None" and whose only change is the documenter's edit to `docs/operator-guide.md`.
   - Criterion 1: holds. Nothing changed under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/`, and the tester's entry (5) and the coder's entry (7) each say so.
   - Criterion 2: the coder's entry (7) records `check: green` and `duplicates: 0 new, 38 known, 0 gone`.
   - Criterion 3 (docs): this is the documenter's work. Every heading it names still exists in `docs/operator-guide.md`:
     - "The health check and the restart policy" (492)
     - "The stops you will see here" (504), the one to be removed
     - "The preflight's items" (515)
     - "The stamp and the probe of the main branch" (548)
     - "The wait for a repository that is not ready" (562)
     - "The stops" (716)
     - "The stops of the tick" (923)
   - Checklist groups 2 to 4 (architecture, security, quality): no code changed, so nothing to judge.
   - Work item hygiene: the Description still matches the task, since nothing has been built yet beyond the documents the documenter writes. The docs criterion says exactly what the reader must know after this story.

   Earlier tests: none. The diff changes, renames or deletes no test file that `main` holds.
10. factory: started docs as self.
11. documenter: Files changed: `docs/operator-guide.md` only, as the docs criterion asks.
    - *The stops you will see here* (heading and six-row table) is gone. One sentence at the end of *The health check and the restart policy* points to "The stops".
    - "The preflight's items": a new paragraph after the items keeps the `preflight_failed` details `confinement: ...` and `the probe on main could not run: <message>`. It also keeps the missing-`sudo`-rule form `the probe on main could not run: project command lint failed: <sudo> refused the command: ...`.
    - "The stamp and the probe of the main branch": a new bullet holds the two forms of `main_branch_failing`, `lint is red on main at <12 characters of the commit>: <last line of the output>` and `lint reached its time_limit on main at <commit>`. The existing "(probed earlier)" bullet already had its own form and is untouched.
    - "The wait for a repository that is not ready": a list of the four `repository_unavailable` details. The first carries its hint (the clone failed, so check `FACTORY_REPOSITORY_URL` and the credentials).
    - *The stops of the tick*: the four-row table is replaced by two paragraphs. They name the four stops and point to "The stops". They keep what the table said that *The stops* lacks: the expired or revoked token shows as `fetch_failed` and nothing is lost; the tick does not touch the checkout while `pipeline_definition_invalid` or `agent_definition_invalid` stands; what can cause `checkout_restore_failed`; the crash-and-rerun behaviour; the `chmod -R g+w <path>` repair; and the `crash_cap`.

    Not changed: the fifteen-row *The stops* table and every other section. No passage cites the removed heading. The contents list at the top never named it.

    Checks: `make documents` ends `documents ok`. I ran no `make check`, since only a document changed. I did not run the story's other smoke-test greps by hand.

    Cross-read and found current against the story: the contents list at the top of the guide, *The stops* and its follow-on sections, and the health check text.

    Findings for the coder: none. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed.

    Stale text noticed and not touched: *The stops* table writes ids with hyphens (`fetch-failed`), while the removed tables and the guide's other sections use underscores. The paragraph after the table says the health status uses the same words with underscores, so this is deliberate. That the table names stops for the human, not the code, is the review's S1 question, which is the human's to decide.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
    `secrets`: secrets: green (1.5 s)
    `documents`: documents ok
