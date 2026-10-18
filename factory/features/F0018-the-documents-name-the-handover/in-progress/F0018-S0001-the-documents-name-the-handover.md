---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 216
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T12:34:27.210869Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T12:34:27.216318Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T12:34:40.587871Z'
  stage: intake
  run: 4c3f0741d6c44c90bfc61aaa11942ec9
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T12:35:00.726040Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T12:36:01.202329Z'
  stage: tests
  run: 9905dc3280b04639bcad08c06ff24a0e
---

# The documents name the handover

## Description

Since the handover of 2026-10-18 (commit `3bcee441`), v1.1 builds this repository itself, and v1's stage table, forms and features F0001 to F0017 lie in `factory/v1/`. Three passages still describe the time before: the README says that the first implementation builds this repository and that a stage's agent run is first observed at the shakedown run; its section *How it is built* names v1 as the builder; and the operator guide's bullet under *Replaced from v1* says that this repository's own `factory/` tree is v1's "until this repository moves to v1.1's layout". This story makes the three passages true and records the handover in the decision log. It is documentation only: the tester and the coder change nothing.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `README.md`, `docs/operator-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: in `README.md`, the opening paragraph says that this repository was built by the first implementation (github.com/pkrahmer/factory) until the handover of 2026-10-18 and is built by v1.1 itself since then, and it no longer says that a stage's agent run and a `time_limit` under `sudo` are first observed at the shakedown run (both were observed on 2026-10-18, on the todo demo); its section *How it is built* says that v1.1's instance builds the repository from `factory/pipeline.yml`, with its features and stories under `factory/features/`, and that v1's history lies in `factory/v1/`. In `docs/operator-guide.md`, the bullet that begins "This repository's own `factory/` tree is v1's" is replaced by one saying that this repository's v1 history lies in `factory/v1/` (v1's `stages.yml`, `TICKET.md`, `FEATURE.md` and its features F0001 to F0017), that nothing reads it and `factory-check-story` does not apply to it, and that since the handover v1.1 builds this repository from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`. `docs/decisions.md` gets a new entry at its end, *factory-rf is built by v1.1 since the handover*, dated 2026-10-18 (commit `3bcee441`), which says why v1's features left `factory/features/` (v1.1 reads no v1 work item, and v1's `done/` folders would have made each of v1's features count as due for an acceptance), why v1.1's features continue v1's numbers from F0018 (`make mutants` finds a feature's modules by its id in the commit subjects), and that v1 is stopped, not removed, as the fallback. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "until this repository moves to v1.1's layout" docs/operator-guide.md
```
Expect: `0`

```bash
grep -c "factory-rf is built by v1.1 since the handover" docs/decisions.md
```
Expect: `1`

```bash
grep -c "factory/v1/" README.md
```
Expect: a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is stated and consistent: no module, signature or comment-stated behaviour exists, so no Interface rule lacks a criterion. The documenter's three files (README.md, docs/operator-guide.md, docs/decisions.md) are named.
   Criteria: 1 (nothing under src/, tests/, image/, template/, claude/ changes) is checkable from the diff. 2 is the standing `make check` criterion. 3 is the docs criterion. It names exact passages to replace or add, the decision entry's title, date, commit and its three reasons, and the `check_documents` result. No rules with a failing side are stated, since this is documentation only.
   Smoke test: four commands (three greps and `check_documents`), all runnable from the repo root. Each has an Expect line that can be compared with the output.
   Architecture: documentation only, so the layers are untouched. The documenter's write paths cover README.md and docs/*, and the feature file confirms this.
   Scope: matches feature.md's Scope. Nothing in its Out of scope is touched: no src/tests/image/template/claude change, no factory/v1/ change, no planning/ change.
4. factory: started tests as self.
5. tester: No tests written. This story only changes documentation, and its Interface says no test changes. Criterion 1 says the tester changes nothing, so this entry confirms that.
   criterion 1: no test function. Nothing under src/, tests/, image/, template/ or claude/ was changed in this stage. `git status` shows only the factory's own `.costs.jsonl` sidecar of the work item.
   criterion 2: no test function. `make check` is the factory's own gate. `make lint` is green here, and the existing suite is unchanged.
   criterion 3 (docs): no test function. It is the documenter's work. Its executable checks are the smoke test's greps and `python -m factory.entry.check_documents`.
   Files created: none. Modules the test runner could not import: none, because no new test refers to a missing module. I skipped the `make test` run: no test was added, so none can fail for the right reason, and the factory runs `make test` after this stage anyway.
   Open: nothing. Next, the coder also changes nothing and ends with an entry saying so.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/application/test_repository_waiter.py::test_a_failing_clone_or_fetch_is_one_stop_naming_the_git_error[_deleted_after_clone-cannot fetch: git fetch --prune origin failed]
