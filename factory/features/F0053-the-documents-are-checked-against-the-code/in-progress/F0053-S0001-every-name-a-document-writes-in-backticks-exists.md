---
stage: tests
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 585
comments_read: [6674965185, 6675118179]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T02:07:39.817288Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T02:07:39.823711Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T02:08:03.973696Z'
  stage: intake
  run: 416fb2a0fb164644bdf623d0c0bed8ba
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T02:12:05.409785Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T02:12:08.113561Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T02:12:32.622625Z'
  stage: intake
  run: a1db2cd2f186412e9bd23f987a89d05c
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T02:12:38.509322Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T02:14:42.675483Z'
  stage: tests
  run: 0c15460cc1c8447e8d6264402b70a32b
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T02:14:52.333588Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-06T02:20:07.301341Z'
  stage: doing
  run: d0cdf849536f49a9a34cc1a509d497fa
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-06T02:21:01.835106Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-06T02:21:05.888090Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-06T02:21:24.055797Z'
  stage: doing
  run: fab2e4b028b24d0ba8e64a78eb74d2af
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-06T02:21:31.052276Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-06T02:22:06.576121Z'
  stage: tests
  run: 9e7046ad5408479b82453881bc9968e5
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-06T02:22:42.046756Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-06T02:30:48.496434Z'
  stage: doing
  run: 586c5ff44cb64dac885b5e8fceee37e6
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-06T02:30:59.910503Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-06T02:32:43.370458Z'
  stage: review
  run: da950e68da4246e998db3be8a972e4d7
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-06T02:32:51.754335Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-06T02:35:50.457050Z'
  stage: doing
  run: f9166a4733784068b67dd3c5ef290204
---

# Every name a document writes in backticks exists

## Description

A document that names a module, a function or a file the code no longer has misleads its reader, and F0051's moves showed how fast such names go stale. This story adds a name check to the document check: in `README.md`, the operator guide and the project guide, every backticked dotted name that starts with `factory.` must be an importable module or an attribute of one, and every backticked repository path must exist. A relative Markdown link to a file must point to a file that exists, read from the document's folder (the human, 2026-11-05); a link to a web address or to a heading alone (`#...`) is not checked here. A placeholder in angle brackets (`<instance>`), a glob (`*`), a path under `/srv`, `/etc` or another absolute place, and a name inside a fenced code block are not checked. `docs/decisions.md` and `docs/runs/` are not read. Until S0004, the findings are only printed.

## Interface

- `factory.shared.domain.documents`: a frozen model `Reference(document: str, line: int, name: str, kind: Literal["module", "path", "link"])`; `named_references(document: str, text: str, top_level: frozenset[str]) -> list[Reference]` (pure), which finds the backticked names and paths of one document with their line numbers, and `unresolved(references: list[Reference], exists: Callable[[Reference], bool]) -> list[str]`, which gives one finding per reference that `exists` refuses, as `<document>:<line>: <name> does not exist`. A relative link's target is a `Reference` of kind `link` too, resolved against the document's folder (`../` included), with the part after a `#` left off.
- A backticked text is a path when it contains `/`, has no whitespace, does not start with `/` or `~`, holds no `://`, and either its first segment is in `top_level` (the checkout's top-level entries, passed by the command) or its last segment has a file extension. A dotted name is a module reference only when it starts with `factory.`.
- The command `factory.entry.check_documents` fills in `document` (the path relative to the checkout) and `top_level`, and gives `exists` its real meaning: a module or attribute found by `importlib`, a path found under the checkout. It reads `README.md`, `docs/operator-guide/` and `docs/project-guide/`.
- A section headed `## Replaced from v1` or `## Replaced in v1.2` is not checked; it ends at the next `##` heading.
- Tests: `tests/shared/domain/test_document_references.py` (the pure functions) and `tests/entry/test_check_documents_references.py` (the command over a temporary checkout).

## Acceptance criteria

1. `named_references` finds `factory.a.b`, `factory.a.b.C.method` and a repository path such as `operator/vm/setup.sh` in backticks, with their lines; `claude/agents/reviewer.md` with `top_level` lacking `claude` is a path; it leaves out a placeholder in angle brackets, a glob, an absolute path (`/srv/factory`, `/etc/...`), `origin/main`, `os.path`, and anything inside a fenced block (one row per case). A link target with a `#fragment` (`[x](a.md#h)`) is the reference `a.md`.
2. A document that names a missing module, a missing attribute or a missing path, or links to a missing file (`[x](../../src/factory/nothing.py)`), gets one finding each; `[x](a.md#h)` with `a.md` missing is one finding; `../` is resolved from the document's folder (`docs/project-guide/`); a link to `https://...` or to `#a-heading` gets none, in the form of the Interface; existing ones get none (rows of one test).
3. `docs/decisions.md`, `docs/runs/` and the two *Replaced* sections give no finding, whatever they name; a missing name after a *Replaced* section's end (the next `##` heading) is reported.
4. The command prints the findings after today's findings of the document check, and its exit status does not change for them until S0004; it reads `README.md`, `docs/operator-guide/` and `docs/project-guide/`, shown by one planted missing name in each.
5. `named_references` gives no link reference for a link to an absolute path (`[x](/srv/a.md)`), to a `mailto:` address (`[x](mailto:a@example.org)`), or with a placeholder in angle brackets or a glob in its target (`[x](<instance>.md)`, `[x](*.md)`) (rows of the criterion 1 test).
6. `make check` stays green.
7. docs: `docs/project-guide/shared.md`, *The document check*: the name check. `docs/operator-guide/pipeline.md`: none. `docs/decisions.md`: none (the feature's decisions go in at S0004).

## Smoke test

```bash
uv run python -m factory.entry.check_documents | grep -c "does not exist"
```
Expect: a number alone (the count of findings, possibly `0`)

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: 1. The Interface does not define `Reference`. `unresolved(references, exists)` must print `<document>:<line>: <name> does not exist`, but `named_references(text)` takes only the text, so no document name enters. Which fields does `Reference` have (name, line, kind: module / path / link, document)? Who sets the document: `named_references` gets a `document` argument, or the command fills it in? I would choose a frozen model `Reference(document, line, name, kind)` and `named_references(document, text)`.
   2. "A repository path" is undefined. What makes a backticked string a path to check: a slash plus a file extension, a first segment that is a top-level folder of the checkout, or something else? Without a rule, `a/b` in prose, a command such as `make lint`, or a name such as `src/factory/...` give two coders different results. I would choose: contains `/`, has no whitespace, and its first segment is a top-level entry of the checkout (the check is done by the command, so `named_references` needs that rule written in the Interface).
   3. Criterion 1 lists only four cases for `named_references`. Rows are missing for a module name that does not start with `factory.` (not checked), a path under `/srv` or `/etc` (named in the Description), and a link target with a `#fragment` (the Interface says the fragment is left off). I would add one row for each.
   4. Criterion 2 has no row for the link side with a `#` after a file (`[x](a.md#h)` resolves `a.md`; missing `a.md` is a finding), and none for the relative path resolved from the document's folder (`../` against `docs/project-guide/`). I would add both.
   5. The Interface sentence "A section headed `## Replaced from v1` or `## Replaced in v1.2` is not checked" has criterion 3, but not for where such a section ends (the next `##` heading). I would add that a finding after the section is reported again.
   6. The checked document set (`README.md`, the operator guide, the project guide) is in the Description only. Criterion 3 covers `docs/decisions.md` and `docs/runs/`, but nothing tests that the command reads the operator-guide and project-guide folders and `README.md`. I would add that to criterion 4's test in `tests/entry/test_check_documents_references.py`.

   Format check passed. Architecture (pure rules in `shared.domain.documents`, I/O in `entry`) and scope (within feature scope, S0001) are fine. The smoke test is runnable, but its `Expect: counted` holds for any output, even if the command crashes in a pipeline; I would make it `grep -c "does not exist"` exit 0 and print a number, e.g. `Expect:` the digits alone.
4. 2026-11-06 human: 1. Yes: a frozen model `Reference(document, line, name, kind)`, with `kind` one of module, path and link, and `named_references(document, text, top_level)`. The command fills in `document` (the path relative to the checkout) and `top_level` (point 2).
   2. A backticked text is a repository path when it contains `/`, has no whitespace, does not start with `/` or `~`, holds no `://`, and either its first segment is in `top_level` (a `frozenset[str]` of the checkout's top-level entries, which the command passes) or its last segment has a file extension. The second half catches a path whose first folder was renamed, such as `claude/agents/reviewer.md`. `origin/main` and `pkrahmer/kumpel-factory` are not paths. One row each in criterion 1: `operator/vm/setup.sh` (path), `claude/agents/reviewer.md` with `top_level` lacking `claude` (path), `origin/main` (not a path), `/srv/factory` (not a path).
   3. Yes to all three rows: `os.path` (not checked), a path under `/srv` or `/etc` (not checked), `[x](a.md#h)` (the link target is `a.md`).
   4. Yes to both rows: `[x](a.md#h)` with `a.md` missing is one finding; `../` is resolved from the document's folder (`docs/project-guide/`).
   5. Yes: a *Replaced* section ends at the next `##` heading, and a missing name after it is reported again.
   6. Yes: criterion 4's test also shows that the command reads `README.md`, `docs/operator-guide/` and `docs/project-guide/`, with one planted missing name in each.
   Smoke test: yes, make it print the number of findings, with `Expect:` a number alone.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story. I wrote exactly these, nothing of my own: the `Reference(document, line, name, kind)` model, `named_references(document, text, top_level)` and the path rule (point 1, 2) into the Interface; the extra rows in criterion 1 (`claude/agents/reviewer.md`, `origin/main`, `/srv/factory`, `os.path`, the `#fragment` link) from points 2 and 3; the rows in criterion 2 (`a.md#h` with `a.md` missing, `../` from the document's folder) from point 4; the end of a *Replaced* section at the next `##` in the Interface and criterion 3 (point 5); the three read locations in the Interface and criterion 4 (point 6); the smoke test now prints the finding count, with `Expect:` a number alone.
   - Interface: names concrete modules and signatures (`factory.shared.domain.documents`, `factory.entry.check_documents`); it changes only `src` and tests, so the route is tests, not docs-only.
   - Criteria: each is testable by a test function, and each rule has its failing side (missing module, attribute, path or link; exempt places; a name after a *Replaced* section is reported again).
   - Smoke test: runnable (`grep -c` prints a number); the `Expect:` can be checked against the output. The command uses no pytest.
   - Architecture: the pure rules in `shared.domain`, the I/O (`importlib`, filesystem, `top_level`) in `entry`, as CLAUDE.md asks.
   - Scope: within the feature's S0001; `docs/decisions.md` and `docs/runs/` are excluded, as the feature's "Out of scope" says.
7. factory: started tests as vm.
8. tester: Wrote the tests for the name check. They are red on purpose: the test run could not import `Reference` from `factory.shared.domain.documents` (ImportError at collection), and `named_references` does not exist yet either. `make lint` is green.

   Criterion → test:
   - criterion 1: tests/shared/domain/test_document_references.py::test_named_references_finds_backticked_names_paths_and_links (one row per case: module, attribute, `operator/vm/setup.sh`, `claude/agents/reviewer.md` outside `top_level`, a placeholder in a path and in a module name, a glob, `/srv/factory`, `/etc/...`, `origin/main`, `os.path`, a fenced block, `[x](a.md#h)` → `a.md` of kind link)
   - criterion 2: tests/entry/test_check_documents_references.py::test_a_missing_name_path_or_link_target_gets_one_finding (missing module, attribute, path, `../../src/factory/nothing.py`, `a.md#h`, and `../README.md` resolved from `docs/project-guide/`), and tests/entry/test_check_documents_references.py::test_an_existing_name_path_or_link_and_a_web_or_heading_link_get_no_finding (an existing module, attribute and path, `../../operator/vm/setup.sh` resolved from the folder, an existing link with a fragment, `https://...`, `#a-heading`). These are the two sides of one rule, but I kept them as two parametrized tests: the missing rows assert the finding line and the existing rows assert there is none.
   - criterion 3: tests/entry/test_check_documents_references.py::test_the_decision_log_runs_and_replaced_sections_are_not_checked (rows: decision log, `docs/runs/`, `## Replaced from v1`, `## Replaced in v1.2`, and a missing name after the next `##` heading, which is reported)
   - criterion 4: tests/entry/test_check_documents_references.py::test_name_findings_follow_todays_findings_and_leave_the_exit_status (one missing name planted in each of `README.md`, `docs/operator-guide/machine.md` and `docs/project-guide/README.md`; rows: no finding today → exit 0, one finding today → exit 1, with today's line printed before the name findings)
   - criteria 5 and 6: not tests (make check, docs).

   Choices I made:
   - In the link rows, the tests check the finding's `<document>:<line>: ` prefix and the count, not the name. The Interface does not say whether a link's name is printed as written or as resolved.
   - When there is no finding today, the tests do not check whether `documents ok` is printed alongside the name findings. The criteria leave that open.

   Files created: tests/shared/domain/test_document_references.py, tests/entry/test_check_documents_references.py. No earlier test file changed.

   Open, for the coder: two existing tests from another story will probably go red, and I did not change them. `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file` copies only the repository's docs into `tmp_path` and expects exactly `documents ok\n`. Under the new check, every repository path those docs name (`src/factory/...`) is missing under that temporary root, so the command prints name findings and the output no longer matches. `tests/entry/test_check_documents_guide_files.py` may be in the same position. Changing either needs the human's leave (a `question`, then `tests`).

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
10. coder: I stopped with the code written and `make check` red. Two tests fail because of the tests themselves, not the code, and I may not change either one.

    What I built (left in the working tree):
    - `src/factory/shared/domain/documents.py`: `Reference`, `named_references`, `unresolved` and `UNCHECKED_SECTIONS` (the two *Replaced* headings). The fenced-block and section helpers come from `factory.shared.domain.sections`. A link's name is its target, resolved against the document's folder without its `#fragment`.
    - `src/factory/entry/check_documents.py`: prints today's findings (or `documents ok`), then the name findings, and keeps the exit status as today's findings set it. It reads `README.md` and every `*.md` file under `docs/operator-guide/` and `docs/project-guide/`. `top_level` holds the root's entries. A module name exists when its longest importable prefix (found through `importlib`) has the rest as attributes. A path or link exists when it lies under the root and exists there.
    - With those, the new tests are green: `tests/shared/domain/test_document_references.py` and `tests/entry/test_check_documents_references.py`. lint, types, layers, sast, secrets and licenses are green too, and coverage is 99 %.

    Failures in `make check` (from `--tb=short`):
    1. `tests/guards/test_agent_folder_names.py::test_no_file_names_the_old_agent_folder[claude/agents/]`: `E AssertionError: assert ['tests/share...eferences.py'] == []`, `E Left contains one more item: 'tests/shared/domain/test_document_references.py'`. The guard refuses any file that names the old agent folder. The new test's row `path-with-extension-outside-top-level` writes that folder's name literally, as criterion 1 asks. The guard file itself avoids this by building the name from parts.
    2. `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`, all six rows, e.g. `[as-it-is]`: `E AssertionError: assert 'documents ok...s not exist\n' == 'documents ok\n'` at `tests/entry/test_check_documents_operator_guide.py:97`. Its fixture copies only the documents into `tmp_path`. Every repository path they name (`operator/vm/setup.sh`, `src/factory/...`) is therefore missing there, and criterion 4 asks the command to print those findings. The tester predicted this failure in entry 8. That test belongs to another story, so changing it needs your leave.

    Question, for both:
    - (1) I propose the tester, whose own test file this is, builds the string from parts in that row (`"claude" + "/agents/reviewer.md"`), as `test_agent_folder_names.py` does. The other option is an exception in the guard, which I would not choose.
    - (2) Options:
      - (a) The test compares only the lines that do not end in ` does not exist`, so it still checks exactly today's output and exit status.
      - (b) Its fixture also copies or symlinks the top-level folders the documents name, so the name findings match the real repository's.
      - (c) The command prints name findings only behind a flag. I rule this out because it contradicts criterion 4.

      I would choose (a), and I would end with `tests` naming both changes.

    Noticed, not touched: on the real repository the command prints 152 name findings, and the smoke test prints `152`. Many are false positives of the agreed path rule:
    - example paths in prose (`src/a/b.py`, `docs/a.txt`)
    - paths of the project the factory runs on (`project/factory/pipeline.yml`, `factory/agents/`)
    - paths relative to `tests/` (`support/*_support.py`)
    - pytest node ids (`tests/...py::test_...`)
    - `$XDG_CONFIG_HOME/...`
    - the unit name `factory.service`, which reads as a module

    These are for S0004 to settle; the exit status does not change for them now. The refactor step is not done yet, because `make check` is not green.
11. 2026-11-06 human: 1. Yes: the tester builds that row's string from parts (`"claude" + "/agents/reviewer.md"`), as `tests/guards/test_agent_folder_names.py` does. No exception in the guard.
    2. (a), with the human's leave: the tester changes `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file` to compare only the lines that do not end in ` does not exist`, with the same exit status, and nothing else in that module. Its entry names the change. End with `tests`, naming both changes.
    The 152 findings and their false positives stay printed only. S0004 settles them before any file blocks.
12. factory: started doing as vm.
13. coder: Your answer in entry 11 asks for two test changes. The tester has to make them, so I changed no code and no test.
    - `tests/shared/domain/test_document_references.py`, row `path-with-extension-outside-top-level`: build the old agent folder's path from parts (`"claude" + "/agents/reviewer.md"`), as `tests/guards/test_agent_folder_names.py` does, so that the guard `test_no_file_names_the_old_agent_folder` passes again.
    - `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file`: compare only the output lines that do not end in ` does not exist`. The exit status check stays the same, and nothing else in that module changes.

    The code from my earlier run (entry 10) is committed, so the tester's change starts from it:
    - `src/factory/shared/domain/documents.py` and `src/factory/entry/check_documents.py` are already in place.
    - Both new test modules pass against that code.

    After the tests change I will run `make check` again and do the refactor step, which is still open.

    The 152 name findings on the real repository stay printed only, as you decided. S0004 settles them.
14. factory: started tests as vm.
15. tester: Made the two test changes the human approved in entry 11, as the coder's entry 13 named them. Nothing else changed.

    - `tests/shared/domain/test_document_references.py` (my own file from entry 8), row `path-with-extension-outside-top-level` of `test_named_references_finds_backticked_names_paths_and_links`: the old agent folder's path is now built from parts in a module constant, `OLD_AGENT_FILE = "claude" + "/agents/reviewer.md"`, the way `tests/guards/test_agent_folder_names.py` does it. The row's text and expected reference use that constant. It checks the same case as before, and the guard `test_no_file_names_the_old_agent_folder` no longer finds the file.
    - `tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file` (another story's test, changed with the human's leave in entry 11, answer 2(a)): the output check now compares only the printed lines that do not end in ` does not exist`. The exit status check is unchanged, and nothing else in the module changed.

    Criterion → test mapping: unchanged from entry 8.

    Files created: none. Files changed: the two above.

    Test run: `uv run pytest -q` on both changed files plus `tests/guards/test_agent_folder_names.py`. All 22 tests passed against the coder's committed code. No module failed to import. `make lint`: green (0.2 s).

    `lint`: lint: green (0.2 s)
16. factory: started doing as vm.
17. coder: `make check` is green now that the tester has made the two test changes the human allowed in entry 11. I ran `make check` once on the committed code, which passed, and again after the refactor, which also passed.

    What I built (the code is from entry 10):
    - `src/factory/shared/domain/documents.py`:
      - `Reference(document, line, name, kind)` and `UNCHECKED_SECTIONS` (the two *Replaced* headings).
      - `named_references(document, text, top_level)`: backticked `factory.` names, backticked paths by the agreed rule, and relative link targets. A link target is resolved against the document's folder with `posixpath`, and its `#fragment` is dropped.
      - `unresolved(references, exists)`: prints `<document>:<line>: <name> does not exist`.
      - Fenced blocks and section ranges come from `factory.shared.domain.sections`, which already existed.
    - `src/factory/entry/check_documents.py`:
      - It reads `README.md` and every `*.md` file under `docs/operator-guide/` and `docs/project-guide/`, and passes the root's entries as `top_level`.
      - A module or attribute exists when its longest importable prefix (found with `importlib`) holds the rest as attributes. A path or link exists when it lies under the root and exists there.
      - The name findings are printed after today's findings (or after `documents ok`). Only today's findings set the exit status.

    Refactor (this run):
    - `_without_replaced_section` and `_checked_lines` built the same set of exempt line numbers, so both now use one helper, `_section_lines(text, headings)`.
    - The module docstring now lists names among what the check checks.
    - No behaviour changed.

    Main design decision: links are resolved inside the domain function, so a link's `name` is the path from the checkout root. The command then checks paths and links the same way. I rejected keeping the raw link target and resolving it in the command: the Interface says the link target is resolved against the document's folder, and doing that in `named_references` keeps the command free of path rules.

    Noticed, not touched: on the real repository the command prints about 152 name findings (the smoke test prints that number). Many are false positives of the agreed rule:
    - example paths in prose
    - paths of the project the factory runs on (`project/factory/pipeline.yml`)
    - paths relative to `tests/`
    - pytest node ids
    - `$XDG_CONFIG_HOME/...`
    - `factory.service`, which reads as a module

    The human left these for S0004 (entry 11). Nothing in the journal changed what the task means beyond the tests the human answered, so the Description stays as it is.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
18. factory: started review as vm.
19. reviewer: Review, round 0. I read the diff against main and the work item. `make check` was green after the coder (entry 17).

    Findings:
    1. criterion 5 added: it needs its test. `src/factory/shared/domain/documents.py` `_link_name` skips links that start with `/` or `mailto:` and links whose target holds `<`, `>` or `*`, but no criterion named that behaviour. The new criterion 5 names it, and the closing criteria are now 6 and 7. Fix: the tester adds those four rows to `test_named_references_finds_backticked_names_paths_and_links`.
    2. `tests/entry/test_check_documents_references.py`, `test_a_missing_name_path_or_link_target_gets_one_finding` and `test_an_existing_name_path_or_link_and_a_web_or_heading_link_get_no_finding`: criterion 2 says "rows of one test", but the two sides of the rule are two test functions. Fix: one parametrized test whose rows each carry their expected findings (`[]` for the existing ones).
    3. Same file, the three link rows (`missing-link`, `missing-link-with-fragment`, `link-resolved-from-folder-missing`): they check only the `<document>:<line>: ` prefix and the count, never the name. The Interface settles the name as the target resolved against the document's folder without its fragment, so the "form of the Interface" in criterion 2 goes untested for links. `[x](../README.md)` would also give one finding if `../` were resolved from the root. Fix: assert the whole line with `src/factory/nothing.py`, `docs/project-guide/a.md` and `docs/README.md`.
    4. Same file, criterion 2 and Interface ("the command fills in … `top_level`"): every missing-path row has a file extension, so no test shows that the command passes the checkout's top-level entries. Fix: a row with a missing path that has no extension but starts with a top-level folder (`operator/nothing_here/`), expecting one finding.
    5. `tests/shared/domain/test_document_references.py`, `test_named_references_finds_backticked_names_paths_and_links`: three failing sides of the Interface's path rule have no row: a backticked text with whitespace (`make -C operator/vm`), one starting with `~` (`~/.config/factory/site.env`) and one holding `://` (`https://example.org/a.md` in backticks). The code refuses all three in `_is_path`, but these are rule sides, not limits. Fix: one row each, expecting `[]`.
    6. `src/factory/shared/domain/documents.py`, `UNCHECKED_SECTIONS`: it writes the literal `"Replaced from v1"` a second time instead of using the existing `REPLACED_SECTION` constant. Fix: `UNCHECKED_SECTIONS: Final = (REPLACED_SECTION, "Replaced in v1.2")`.

    Checked and fine:
    - Architecture: the pure rules are in `shared.domain`; `importlib` and the filesystem are in `entry`, as the Interface says.
    - Security: no markers, no shell, nothing built from strings.
    - A *Replaced* section ends at the next `## ` heading through `sections()`.
    - The Description matches what was built.
    - The docs criterion still holds.

    Earlier tests:
    - `tests/entry/test_check_documents_operator_guide.py`: changed under the human's leave in journal entry 11, answer 2(a). The change is only the comparison that leaves out the ` does not exist` lines, which is within that leave.
20. factory: started doing as vm.
21. coder: Round 1. I fixed the one code finding from the review (entry 19). Findings 1 to 5 are test changes, so they go to the tester. `make check` is green after my change.

    Code (finding 6):
    - `src/factory/shared/domain/documents.py`: `UNCHECKED_SECTIONS` now reuses the existing constant, as `(REPLACED_SECTION, "Replaced in v1.2")`, instead of writing `"Replaced from v1"` a second time. Behaviour is unchanged. Nothing else in the code changed.

    For the tester (findings 1 to 5, all in the tests; I changed no test):
    1. Criterion 5 needs its rows in `tests/shared/domain/test_document_references.py::test_named_references_finds_backticked_names_paths_and_links`, one each, all expecting `[]`: `[x](/srv/a.md)`, `[x](mailto:a@example.org)`, `[x](<instance>.md)` and `[x](*.md)`.
    2. In `tests/entry/test_check_documents_references.py`, merge `test_a_missing_name_path_or_link_target_gets_one_finding` and `test_an_existing_name_path_or_link_and_a_web_or_heading_link_get_no_finding` into one parametrized test. Each row carries its expected findings, with `[]` for the existing ones, as criterion 2 says ("rows of one test").
    3. In the same file, the rows `missing-link`, `missing-link-with-fragment` and `link-resolved-from-folder-missing` should check the whole finding line, names included. The resolved names are `src/factory/nothing.py`, `docs/project-guide/a.md` and `docs/README.md`.
    4. In the same file, add a row with a missing path that has no file extension but starts with a top-level folder (`operator/nothing_here/`), expecting one finding. It shows that the command passes `top_level`.
    5. In `tests/shared/domain/test_document_references.py`, add one row each expecting `[]` for backticked text with whitespace (`make -C operator/vm`), text starting with `~` (`~/.config/factory/site.env`) and text holding `://` (`https://example.org/a.md`).

    The current code already handles every one of these rows as the Interface says. For finding 3, the command prints a link's name as the target resolved from the checkout root, without its fragment.

    Refactor step: nothing more to change beyond finding 6. The Description already has the reviewer's criterion 5, so I did not rewrite it.

    Noticed, not touched: on the real repository the command still prints about 152 name findings. The human has left those for S0004.

    `check`: check: green
