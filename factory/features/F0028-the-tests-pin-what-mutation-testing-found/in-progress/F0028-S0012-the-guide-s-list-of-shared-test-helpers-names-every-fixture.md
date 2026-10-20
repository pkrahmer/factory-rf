---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 336
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T04:47:10.521431Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T04:47:10.527047Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T04:47:26.989642Z'
  stage: intake
  run: 42574c49871d4a3a8ff8f6f9ef0c64e0
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T04:47:47.501960Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T04:49:29.124210Z'
  stage: tests
  run: d4ebb1a72df741fd8523f87d3bb4b532
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T04:49:49.384262Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T04:50:58.011487Z'
  stage: doing
  run: 2f500571e53045e2b59a674de56d37d1
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T04:51:18.666636Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-20T04:51:38.124945Z'
  stage: review
  run: 92d151d6f2bf4515be189132cdfca50a
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-20T04:51:58.638978Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-20T04:52:31.565651Z'
  stage: docs
  run: 502588708921445e84bd94f4dfe0a3df
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-20T04:52:52.835564Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T04:53:15.857717Z'
  stage: smoke-test
  run: 83b49602feff4027be84e0b45d98de80
---

# The guide's list of shared test helpers names every fixture

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0028-S0011 gave the project guide's index, `docs/project-guide/README.md`, a section *Shared test helpers*, so that a tester finds a shared helper before writing a copy of it. It names every module `tests/*.py` whose name does not start with `test_`. But its line for `conftest.py` lists only 11 of the 25 fixtures `tests/conftest.py` defines, and the list reads as if it were complete. It leaves out `reopened_tmp_path`, `group_umask`, `local_settings`, `probe_settings`, `compose_service`, `hosted_environment`, `boundaries`, `definition`, `installed_agents`, `walk`, `layout`, `image_layout`, `records` and `recorder`. Among them are `walk`, `installed_agents` and `boundaries`, which F0028's own application stories built on. The section also does not name the one conftest below the root, `tests/application/handlers/conftest.py`, with its fixtures `snapshot_of`, `state_with`, `event_of`, `pull_request` and `work_item`. F0028's decision 13 names it as a shared place. A tester who reads the list today could write a second `walk` or `event_of`, which is the copy the section is meant to prevent. This story is for the tester and the reviewer. It completes the `conftest.py` line and adds a line for the handlers' conftest. The code, the tests and the other documents stay as they are. It changes no behaviour, so it has no criterion of its own beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The documenter checks against the functions decorated with `@pytest.fixture` in `tests/conftest.py` and `tests/application/handlers/conftest.py`, and their docstrings.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide/README.md`, *Shared test helpers*. The line ``- `conftest.py`:`` names every fixture of `tests/conftest.py` in backticks, the autouse `reopened_tmp_path` included, with what each holds where its name does not say it. A new line ``- `application/handlers/conftest.py`:`` names every fixture of `tests/application/handlers/conftest.py` in backticks, the same way, and says that they serve the handlers' tests under `tests/application/handlers/`. Its `work_item` is a published work item of the handlers' tests, not the root's started story. The section's opening paragraph adds one sentence: a story that adds a fixture to either conftest names it in that line through its docs criterion. Every other line of the section stays as it is. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because nothing an operator runs or decides changes.

## Smoke test

```bash
idx=docs/project-guide/README.md
missing=0
for pair in 'tests/conftest.py:conftest.py' 'tests/application/handlers/conftest.py:application/handlers/conftest.py'; do
  file=${pair%%:*}; entry=${pair#*:}
  line=$(grep -F -- "- \`$entry\`:" "$idx")
  for fx in $(grep -A1 '@pytest.fixture' "$file" | sed -n 's/^def \([a-z_]*\)(.*/\1/p'); do
    case $line in *"\`$fx\`"*) ;; *) echo "missing: $entry $fx"; missing=$((missing+1));; esac
  done
done
echo "$missing"
```
Expect: `0` and no `missing:` line (every fixture of both conftests is named in its line of the guide). Before the documenter's edit it prints 19 `missing:` lines and `19`.

```bash
missing=0
for f in tests/*.py; do n=$(basename "$f"); case "$n" in test_*) continue;; esac; grep -qF -e "$n" docs/project-guide/README.md || { echo "missing: $n"; missing=$((missing+1)); }; done
echo "$missing"
```
Expect: `0` (every shared helper module at the root of `tests/` is still named, as F0028-S0011 left it)

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: no module changes. It names the two conftest files and the `@pytest.fixture` functions the documenter checks against, so there is no signature to pin. Nothing under `src/factory/` changes.
   - Criteria: the closing `make check` criterion and one docs criterion, as the Description says (no behaviour changes). The docs criterion has three checkable parts: the `conftest.py` line names every fixture in backticks, the new `application/handlers/conftest.py` line does the same and says that `work_item` is a published work item, and the opening paragraph gains one sentence. It states no limit, default or rejected input, so no failing side needs a criterion.
   - Smoke test: both commands are runnable bash using grep, sed and case over the repo files. Each `Expect:` line is checkable. The first expects `0` with no `missing:` line and says it prints 19 `missing:` lines and `19` before the edit. The second expects `0` for the shared helper modules.
   - Architecture: a documentation-only change to the project guide's index. The layers are untouched. It matches CLAUDE.md's rule that the documenter keeps `docs/project-guide/` true and that the other three documents are not touched.
   - Scope: it is within F0028, which names the shared place in decision 13. It is not in the feature's "Out of scope", because no code or test changes. Its "none" for the other documents agrees with the feature, whose docs criteria are `none` for the same reason. Here the guide's own docs criterion is the one change.
4. factory: started tests as self.
5. tester: No test written, which is what the work item asks for. Its Interface says "the tester writes no test module", and the story changes no behaviour. Neither criterion gets a test function:
   - criterion 1 (`make check` stays green): the factory's own checks cover it; there is no test function for it.
   - criterion 2 (docs, `docs/project-guide/README.md` *Shared test helpers*): the documenter's criterion. The story's smoke test checks it (every `@pytest.fixture` of `tests/conftest.py` and `tests/application/handlers/conftest.py` named in its line). It is not a pytest test.

   Files created: none. Modules the test runner could not import: none. Because no new test exists, there is nothing red: `make test` passed (`test: green (40.6 s)`, coverage 99.14 %) and `make lint` passed (`lint: green`). The coder or documenter has no test specification to meet beyond keeping `make check` green.

   Rejected: writing a pytest test that parses the guide and compares it with the conftest fixtures. It would test a document rather than the code, and the Interface rules out a test module.

   `lint`: lint: green (0.0 s)
   `test`: test: green (46.0 s)
6. factory: started doing as self.
7. coder: No code changed, which is what the work item asks for. The Interface says no module under `src/factory/` changes. The tester wrote no test, so `make test` has no failing test to meet. The one change is to `docs/project-guide/README.md`, *Shared test helpers*. That is criterion 2, the docs criterion. CLAUDE.md gives that file to the documenter stage, and the coder does not write it.

   - Built: nothing. No paths changed.
   - `make check`: run on the unchanged tree. It ends with `test: green (46.1 s)` and `check: green`, with 99.14 % coverage.
   - Main choice: hand the story forward without touching anything, so the documenter makes the guide edit. Rejected: editing `docs/project-guide/README.md` here. That would be the documenter's work, and it is outside what the coder writes.
   - Refactor: no diff, so nothing to refactor.
   - The journal did not change the meaning of the task. `## Description` stays as it is.
   - Noticed, not touched: the first smoke test should still print 19 `missing:` lines until the documenter adds the 14 fixtures of `tests/conftest.py` and the 5 of `tests/application/handlers/conftest.py` to their lines of the guide.

   `check`: check: green (not run again: passed on tree 450879e8d6a9 at 2026-10-20T04:13:05Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The only changes are the work item and its `.costs.jsonl` sidecar under `factory/`. That is what the Interface asks for: no module under `src/factory/` changes, and the tester writes no test module.
   - Criterion 1: the coder's entry 7 says the factory's `make check` was green (`check: green`, coverage 99.14 %).
   - Criterion 2: this is the documenter's guide edit, and the docs stage makes it next. I checked its premises against the tree:
     - `tests/conftest.py` defines 25 `@pytest.fixture` functions. The 14 the Description says are missing from the guide (`reopened_tmp_path` through `recorder`) are exactly the ones the guide's `conftest.py` line leaves out.
     - `tests/application/handlers/conftest.py` defines the 5 fixtures the Description names (`snapshot_of`, `state_with`, `event_of`, `pull_request`, `work_item`).
     - So the Description, the docs criterion and the smoke test's expected 19 `missing:` lines before the edit all match the code.
   - Architecture, security and quality: nothing to judge, since no code changed.
   - Hygiene: entries 5 and 7 explain why nothing was built and what each stage rejected. The Description still matches the story.
   - `duplicates: 5 new` (entry 7): this story changed nothing under `src/factory`, so none of those findings come from it.

   Earlier tests: none. The diff changes, renames or deletes no test file.
10. factory: started docs as self.
11. documenter: Documenter: no findings. Only documents changed, so I did not run `make check`; the factory's checks run after this stage.

    Changed:
    - `docs/project-guide/README.md`, *Shared test helpers*: the `conftest.py` line now names all 25 fixtures of `tests/conftest.py`, with what each holds. It groups them by use, and `reopened_tmp_path` is marked autouse. The line stays one line, because the story's smoke test greps a single line.
    - `docs/project-guide/README.md`, same section: a new line `application/handlers/conftest.py` names its 5 fixtures (`snapshot_of`, `state_with`, `event_of`, `pull_request`, `work_item`). It says they serve only the handlers' tests under `tests/application/handlers/`. It also says its `work_item` is a published work item of those tests, not the root's started story.
    - `docs/project-guide/README.md`, opening paragraph: one added sentence. A story that adds a fixture to either conftest names it in that conftest's line through its docs criterion.

    Checks I ran:
    - Smoke test 1 prints `0`, with no `missing:` line. It printed 19 before the edit.
    - Smoke test 2 prints `0`, so every shared helper module at the root of `tests/` is still named.

    Cross-read and current: `README.md`, `docs/operator-guide.md` and `docs/decisions.md`. The docs criterion says none for these. The diff against `main` outside `factory/` is empty, so no name or behaviour changed that they could contradict. Every other line of the guide's *Shared test helpers* section is unchanged.

    Stale text noticed but not mine to fix: none.

    Skills set aside: none.

    `check`: check: green (not run again: passed on tree 450879e8d6a9 at 2026-10-20T04:13:05Z)
    `secrets`: secrets: green (0.2 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test: no findings. I ran both commands from the repository root exactly as written, in order.

    Command 1 checks that every `@pytest.fixture` of both conftests is named in its line of the guide. Output:
    ```
    0
    ```
    Met its `Expect:` line: it printed `0` and no `missing:` line.

    Command 2 checks that every shared helper module at the root of `tests/` is still named. Output:
    ```
    0
    ```
    Met its `Expect:` line: it printed `0`.

    Checked against the acceptance criteria:
    - Criterion 2 (docs): `git diff main...HEAD -- docs` changes only `docs/project-guide/README.md`.
      - The `conftest.py` line names all 25 fixtures of `tests/conftest.py`, and `reopened_tmp_path` is marked autouse. `grep` finds 25 `@pytest.fixture` decorators, each followed by a `def`, so the command's extraction missed none.
      - The new `application/handlers/conftest.py` line names its 5 fixtures. It says they serve only the tests under `tests/application/handlers/`, and that its `work_item` is a published work item of those tests, not the root's started story.
      - The opening paragraph has gained the one sentence the criterion asks for.
      - Every other line of the section is unchanged.
      - `README.md`, `docs/operator-guide.md` and `docs/decisions.md` are unchanged.
    - Criterion 1 (`make check` stays green): the smoke test does not contradict it. I did not run `make check` here; the factory's checks cover it.

    Findings: none.
