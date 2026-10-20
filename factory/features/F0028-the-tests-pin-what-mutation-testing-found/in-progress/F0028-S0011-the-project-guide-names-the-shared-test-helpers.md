---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 333
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-20T04:30:41.009703Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T04:25:41.935774Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T04:25:41.942833Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T04:26:02.479132Z'
  stage: intake
  run: d18535864ede4cf0be303c436846c294
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T04:26:22.853231Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T04:27:18.234180Z'
  stage: tests
  run: cb8835a79b3d4e8f85f5be0d938cded2
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T04:27:38.743258Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T04:28:46.461155Z'
  stage: doing
  run: 9028c0d354e44dd5bc2d6251896287dd
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T04:29:07.104269Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T04:29:30.709095Z'
  stage: review
  run: 6ad11c4e0f7c4194bf0ca7671d6c9591
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T04:29:51.402537Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T04:30:20.192484Z'
  stage: docs
  run: fe354c76a80741d6a5b32f13cd3b74cb
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T04:30:41.009703Z'
  stage: smoke-test
---

# The project guide names the shared test helpers

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

A tester who writes a new test module has to find the helpers the earlier tests share before it writes its own, or the reviewer counts a copy as a finding (`CLAUDE.md`, *Tests*). In F0028 that happened in three of nine stories: S0001 copied `_raising` of `tests/domain/test_settings.py`, S0002 copied `FORM`, `SMOKE` and `TICKS`, and S0009 copied the opencode login hint of `tests/application/test_agent_run_probe_opencode.py`. Each cost a review round and four more runs. The shared helpers live in 36 modules at the root of `tests/` besides `conftest.py` (`acceptance_support.py` to `write_path_support.py`, with `acceptance_walk.py`, `document_texts.py`, `human_clone.py`, `observing_runtime.py`, `run_process_recorder.py`, `shipped_agents.py` and `source_search.py`), and F0028 added three of them (`acceptance_support.py`, `evaluation_support.py`, `tick_support.py`) and grew two (`settings_support.py`, `probe_support.py`). The project guide names eleven of them, each where its domain needs it, and has no list a tester can read first. This story is for the tester and the reviewer: it adds that list to the guide. The code, the tests and the other documents stay as they are. It changes no behaviour, so it has no criterion of its own beyond the two closing ones; keeping the list current as modules are added is left to the documenter of each later story.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The reference the documenter checks against is the set of modules `tests/*.py` whose name does not start with `test_`, and each module's docstring and public names.

## Acceptance criteria

1. `make check` stays green.
2. docs: the project guide's index, `docs/project-guide/README.md`, gets a section *Shared test helpers*, named in its *The files* line for `README.md`. It says that the helpers that more than one test module uses live in modules at the root of `tests/` (fixtures in `tests/conftest.py`), and that a test module imports them from there, as `CLAUDE.md`'s standing leave to move a shared test helper intends, and that a story that adds such a module names it in this list through its docs criterion. It then names every module `tests/*.py` whose name does not start with `test_`, `conftest.py` included, each with one line on what it holds (for example `tick_support.py`: `handlers_of` and `Failing`, the tick's handler factory and a handler that records each event and raises the error it is given, `ValueError("boom")` by default). `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because nothing an operator runs or decides changes.

## Smoke test

```bash
missing=0
for f in tests/*.py; do n=$(basename "$f"); case "$n" in test_*) continue;; esac; grep -qF -e "$n" docs/project-guide/README.md || { echo "missing: $n"; missing=$((missing+1)); }; done
echo "$missing"
```
Expect: `0` (every shared helper module at the root of `tests/` is named in the guide's index)

```bash
grep -c -F '## Shared test helpers' docs/project-guide/README.md
```
Expect: `1`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no module under `src/factory/` changes and the tester writes no test module. The reference is concrete: `tests/*.py` whose name does not start with `test_`. I listed them and found 37, `conftest.py` included. The Description says "35 besides `conftest.py`", but there are 36. The count is only background, and the criterion and smoke test name the set by rule, not by count. Not a finding.
   - Criteria: the story has no behaviour of its own and no Interface comment that states a rule. It has the two closing ones, and the docs criterion is specific. It names the file (`docs/project-guide/README.md`), the section title (*Shared test helpers*), the *The files* line for `README.md` that must name it, the content of the leading sentences, every module with one line each, and the `none` for the other three documents. `docs/project-guide/README.md` today has no such section (0 matches), so the smoke test starts red.
   - Smoke test: both commands run as written. The first loops over `tests/*.py` skipping `test_*` and counts the names missing from the index. The second counts the heading. Each `Expect:` line is checkable output (`0`, `1`).
   - Architecture: documentation only, so no layer is touched. It follows `CLAUDE.md`'s standing leave on shared test helpers and its Docs section, where the documenter keeps the guide.
   - Scope: it is within F0028 and not in its "Out of scope". The feature's scope lists `tests/tick_support.py` and the other support modules that this story names in the guide. The feature says the stories' docs criteria are `none`. That sentence is overridden by this proposed story, which the acceptance reviewer proposed and the human started. I did not raise it.
4. factory: started tests as self.
5. tester: No tests written, on purpose. The Interface says no module under `src/factory/` changes and the tester writes no test module. Neither criterion describes behaviour a test could check:
   - criterion 1 (`make check` stays green): no test function. The factory's own checks cover it.
   - criterion 2 (docs: a *Shared test helpers* section in `docs/project-guide/README.md`): no test function. This is the documenter's work. The documenter checks it against the set `tests/*.py` whose name does not start with `test_`, and the story's smoke test checks it too.

   Files created: none. Modules the test run could not import: none, because no new test refers to a missing module. I did not run `make test`: there is no new red test to confirm, and the factory runs it after this stage. `make lint` is green.

   Rejected: a pytest test that reads the guide's index for the module names. It would duplicate the smoke test and go against the Interface's "the tester writes no test module".

   Open: none. The coder has no code to write. The work is the docs criterion.

   `lint`: lint: green (0.0 s)
   `test`: test: green (40.6 s)
6. factory: started doing as self.
7. coder: No code written, on purpose. The Interface says no module under `src/factory/` changes, and the tester wrote no test. The only criterion with content is criterion 2, the docs criterion: a *Shared test helpers* section in `docs/project-guide/README.md`. The documenter stage writes that section. `CLAUDE.md` (*Docs*) says the coder does not write the four guides.

   - Built: nothing. The working tree has no changes outside the factory's own costs sidecar.
   - Main choice: I left the guide section to the documenter. The alternative, writing it here, would have gone against `CLAUDE.md`'s rule that the documenter keeps `docs/project-guide/`, and it is outside a coder's work. I rejected it.
   - Refactor: there is no diff to refactor, so nothing changed.
   - Journal: no entry changed the meaning of the task, and the Description is unchanged.
   - Noticed, not touched: intake found that the Description's count of helper modules is off ("35 besides `conftest.py`", where there are 36). The count is only background, and the smoke test counts by rule, not by number.

   `make check`: check: green (test: green (45.9 s), coverage 99.14 %).

   `check`: check: green (not run again: passed on tree 450879e8d6a9 at 2026-10-20T04:13:05Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   Reviewed `git diff main...HEAD -- . ':!factory'`. It is empty: the only changes on the branch are the work item and its `.costs.jsonl` sidecar. That is what this story intends. The Interface says no module under `src/factory/` changes and the tester writes no test module. Criterion 2 is the documenter's work (`CLAUDE.md`, *Docs*), so it is checked at the next stage against `tests/*.py` and by the smoke test.
   - Criterion 1: the coder's journal entry 7 reports `make check` green (coverage 99.14 %). Neither criterion has behaviour a test could pin, so no test is missing, and the Interface states no rule or limit.
   - Architecture, security and quality: nothing under review, because no code or test changed. The record's `duplicates: 5 new` comes from the tree on `main`, not from this diff, which changes nothing under `src/factory`.
   - Work item hygiene: entries 5 and 7 explain why no test and no code were written, and what was rejected (a pytest test reading the guide; the coder writing the section). The docs criterion still says everything the documenter needs: the file, the section title, the *The files* line, the leading sentences, one line per module (`conftest.py` included) and `none` for the other three documents.

   description corrected: "The shared helpers live in 35 modules at the root of `tests/` besides `conftest.py`" -> "The shared helpers live in 36 modules at the root of `tests/` besides `conftest.py`". Intake (entry 3) settled this, and listing `tests/*.py` without the `test_` modules gives 37 with `conftest.py`.

   Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
11. documenter: Changed one file: `docs/project-guide/README.md`. It now has a section *Shared test helpers*, placed before *Errors*, and the *The files* line for `README.md` lists it. The section says that helpers more than one test module uses live at the root of `tests/` (fixtures in `conftest.py`) and are imported from there. It also says a story that adds such a module names it in the list through its docs criterion. Then it gives one line for each of the 37 modules `tests/*.py` whose name does not start with `test_`, `conftest.py` included. I wrote the lines from each module's docstring and public names. For `conftest.py` I also checked that the `world` and `work_item` fixtures exist.

    Both smoke-test commands, run as written:
    - The missing-module loop prints `0`.
    - The heading count prints `1`.

    I did not run `make check`. Only a document changed, so the factory's own run after this stage decides.

    Cross-read, found current: `README.md`, `docs/operator-guide.md` and `docs/decisions.md`. The docs criterion says `none` for them, and the diff changes nothing under `src/` or `tests/`. The existing guide text on `proof_support.py` in *Kill points* and *Fault-injection paths* still matches that module, so the new line for it only points there.

    Code findings: none. The diff against `main` has nothing outside `factory/`.

    Stale text I saw and did not touch: none. The Description's helper count is already corrected by review.

    `check`: check: green (not run again: passed on tree 450879e8d6a9 at 2026-10-20T04:13:05Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
