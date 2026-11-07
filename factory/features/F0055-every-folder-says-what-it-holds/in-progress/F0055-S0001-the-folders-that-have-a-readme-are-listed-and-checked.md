---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 632
comments_read: [6705414222, 6705474496]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T10:04:39.228213Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T10:04:39.235457Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-07T10:04:57.555123Z'
  stage: intake
  run: a68300c45fd44c088e1cc80f13b0fc27
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-07T10:06:44.203580Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-07T10:06:46.495587Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-07T10:07:05.127664Z'
  stage: intake
  run: 7b2be5e0daf24820b37ce99477b081c6
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T10:07:09.965913Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-07T10:10:33.081377Z'
  stage: tests
  run: 3e230f03b651466d959e847c3351ced4
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-07T10:14:23.889133Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T10:14:26.254552Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-07T10:15:03.152206Z'
  stage: tests
  run: 3f4256f068f34b6e979f73365a105d0c
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T10:15:08.069062Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-07T10:26:11.919571Z'
  stage: doing
  run: 12dc6cac235b499b82a11940e364fd01
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T10:26:19.111509Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T10:28:03.801780Z'
  stage: review
  run: 21ae9eb163824f228f437efcce7fe4c7
---

# The folders that have a README are listed and checked

## Description

The repository is to give every folder a reader would ask about a short `README.md` (feature decision 1). This story builds what keeps those READMEs true; the READMEs themselves come in the later stories. It adds one constant that lists every folder that must have a README, a guard over that list, and the document check's reading of those READMEs, so that they can be put on `docs/checked-documents.txt` and their names and links are checked like the guides'. It also teaches the documenter that it may write them. A README that is on the list but does not exist yet is no finding of the document check; the guard reports it, and the guard is written so that the later stories can turn it green one group at a time. Nothing else the check reads or prints changes.

## Interface

- `factory.shared.domain.folder_readmes` (domain, new):

  ```python
  FOLDER_READMES: Final[tuple[str, ...]]

  def readme_problems(folder: str, readme: str | None, subfolders: Sequence[str]) -> list[str]:
      """What a folder's README and its subfolders disagree on, one line each, sorted."""
  ```

  - `FOLDER_READMES` holds the paths, relative to the root, of every folder of feature decision 1, each ending in `/README.md`: `agents/README.md`, `docs/README.md`, `operator/bin/README.md`, `operator/claude/README.md`, `operator/job/README.md`, `operator/lib/README.md`, `operator/opencode/README.md`, `operator/skill/README.md`, `operator/template/README.md`, `operator/vm/README.md`, `security/README.md`, `src/factory/README.md`, the README of each of the eight packages under `src/factory/` (`agents`, `entry`, `hosting`, `machine`, `pipeline`, `shared`, `watching`, `work`), `tests/README.md`, `tests/support/README.md` and `tests/guards/README.md`, in this order.
  - `readme_problems`: `readme` `None` gives `["<folder>: no README.md"]`. Otherwise every name in `subfolders` that no line ``- `<name>/` `` followed by a sentence names gives `<folder>: <name>/ is not named`, and every such line whose name is not in `subfolders` gives `<folder>: <name>/ does not exist`. The README's shape is checked too, so that it stays a pointer and never becomes documentation (feature decision 6). Each of these gives one line: a heading line (`#` followed by a space) other than the first line `# <title>` (`<folder>: has a section`); a fenced code block (`<folder>: has a code block`); more than two sentences between the title and the list (`<folder>: the opening is longer than two sentences`); no relative link (`<folder>: links to no guide`); a subfolder line of more than one sentence or more than 25 words (`<folder>: <name>/ has a long line`); a line that is neither the title, the opening, a link line, a list line nor blank (`<folder>: line <n> is no part of the form`); and more than 10 lines plus one per subfolder, blank lines left out (`<folder>: is longer than <limit> lines`). The limits are constants in the module. A README with no problem gives `[]`. Definitions: the title is the first line, `# ` and a text. A subfolder line starts with `- ` and a backticked name ending in `/`. A link line is a line that contains a relative Markdown link and is not a subfolder line; it may start with `- `. The opening is the non-blank lines between the title and the first link line or subfolder line. Any other non-blank line after the first link line or subfolder line is "no part of the form".
- `tests/guards/test_folder_readmes.py` (new): for each path of `FOLDER_READMES` whose README exists, `readme_problems` on the real folder gives `[]`, its subfolders read from the folder (hidden folders and `__pycache__` left out). A README that does not exist yet is skipped with its path in the reason, so the guard turns green group by group as the later stories write them. One test checks that every path of `FOLDER_READMES` ends in `/README.md` and names a folder that exists. One more test checks that every package directly under `src/factory/` (a folder with an `__init__.py`) has its `README.md` on `FOLDER_READMES`, so that a new area cannot be added without one (the human, 2026-11-07).
- `factory.entry.check_documents`: `_named_documents` also returns each path of `FOLDER_READMES` whose file exists, and `operator/README.md`, so the name check reads them and `docs/checked-documents.txt` may list them. `operator/README.md` is not on `FOLDER_READMES` and keeps its own form; it was rewritten by F0054-S0022 and could not be listed yet (the human, 2026-11-07). A listed path of `FOLDER_READMES` that does not exist yet stays the finding `checked_list_findings` gives today.
- `agents/agents/documenter.md`: where it names the files the documenter may write, it also names the folder READMEs of `FOLDER_READMES` (`factory.shared.domain.folder_readmes`), with one rule: a folder README points to the guides, and whatever needs explaining goes into the guide page it links to, never into the README. The human's leave (feature decision 5): the tester changes the earlier tests that pin the documenter's text only so far as this one sentence requires, and any other earlier test whose only failure is this sentence; every changed test keeps its name and what it checks, and the entry names each one.
- The documenter's `write_paths` in `factory/pipeline.yml` are the human's change at this story's merge (feature.md, *The human's changes*), not this story's.

## Acceptance criteria

1. `readme_problems` gives these results, rows of one parametrized test: no README (`["<folder>: no README.md"]`); a README that names each subfolder (`[]`); a subfolder not named; a named subfolder that does not exist; both, sorted; a line ``- `x/` `` without a sentence, which counts as not naming `x/`.
2. The shape rules give their lines, rows of one parametrized test, each at and past its limit: a `##` section; a code block; an opening of two sentences (none) and of three (one); no relative link; a subfolder line of 25 words (none) and of 26 (one), and of two sentences (one); a free line of prose after the list; a README at the line limit (none) and one line past it (one).
3. Every path of `FOLDER_READMES` ends in `/README.md` and names a folder that exists in the repository (one test). Every package directly under `src/factory/` has its README on `FOLDER_READMES` (one test, which passes on today's repository).
4. The guard of the Interface passes on today's repository, where none of the new READMEs exist yet, and skips each with its path.
5. With a README written for one listed folder in a copy of the minimal documents (`tests/support/minimal_documents_support.py`), the document check reads it: a missing module it names is a finding, reported while the README is unlisted and blocking once it is listed (rows of one test); and the same with `operator/README.md` in the minimal documents, whose form the shape rules of `readme_problems` do not apply to.
6. `agents/agents/documenter.md` names the folder READMEs among the files the documenter may write, with the rule that a README points to the guides (one test).
7. A listed path of `FOLDER_READMES` with no file gives the same finding of `checked_list_findings` as today.
8. The guard's subfolder reading leaves out hidden folders and `__pycache__`, through a helper in the guard module, with a parametrized test.
9. `make check` stays green.
10. docs: `docs/project-guide/shared.md`, the document check: the reader learns which READMEs the check reads and where their list lives. `docs/project-guide/README.md`: the guard of the folder READMEs among the guards. `docs/project-guide/style.md`, a new section *Folder READMEs*: the form of a folder README and its limits (feature decisions 2 and 6), and that anything needing explanation belongs in the guide page the README links to. `docs/decisions.md`: one entry for feature decisions 1 to 3, with the rejected option: a README in every folder, which would cost about 25 more files that all say the same.

## Smoke test

```bash
uv run python -c "from factory.shared.domain.folder_readmes import FOLDER_READMES, readme_problems; print(len(FOLDER_READMES), readme_problems('x', None, []))"
```
Expect: `23 ['x: no README.md']`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: 1. Interface, `factory.entry.check_documents`: `_named_documents` also returns `operator/README.md`. No criterion tests it. Criterion 5 only covers a README of `FOLDER_READMES`. Should I add: "with `operator/README.md` in the minimal documents, a missing module it names is a finding"? I would choose yes.
   2. Interface: "A listed path of `FOLDER_READMES` that does not exist yet stays the finding `checked_list_findings` gives today." No criterion tests it. Should I add one: a listed path of `FOLDER_READMES` with no file gives the same finding as today? I would choose yes.
   3. Interface, guard: "its subfolders read from the folder (hidden folders and `__pycache__` left out)". No criterion tests it. Criterion 4 only says the guard passes and skips. Should I add one that a hidden folder and `__pycache__` are not counted as subfolders? If the guard has no test for that, I suggest it be a helper function in the module with a parametrized test. I would choose yes.
   4. Interface, `readme_problems`: "link line" and "opening" are not defined. For example, does a link line begin with `[` or `- [`, and is the opening the non-blank lines between the title and the first link or list line? Two coders could read them differently. Criterion 2 pins only some of the rows. Please state the form of a link line, for example "a line that contains a relative Markdown link and is not a subfolder line". I would choose that.

   The format check passed. Scope, architecture (domain constant in `shared`, wiring in `entry`) and the docs criterion (it names what the reader must know) are fine. The smoke test is runnable and its `Expect:` line is checkable. The count of 23 paths matches the list.
4. 2026-11-07 human: Yes to all four, as you propose.
   1. Add a row to criterion 5: with operator/README.md in the minimal documents, a missing module it names is a finding, reported while it is unlisted and blocking once listed. operator/README.md keeps its own form: the shape rules of readme_problems do not apply to it.
   2. Add a criterion: a listed path of FOLDER_READMES with no file gives the same finding of checked_list_findings as today.
   3. Add a criterion: the guard's subfolders leave out hidden folders and __pycache__, through a helper in the guard module with a parametrized test.
   4. Definitions for readme_problems, to write into the Interface: the title is the first line, '# ' and a text. A subfolder line starts with '- ' and a backticked name ending in '/'. A link line is a line that contains a relative Markdown link and is not a subfolder line; it may start with '- '. The opening is the non-blank lines between the title and the first link line or subfolder line. Any other non-blank line after the first link line or subfolder line is 'no part of the form'.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story.
   - Interface: concrete (`factory.shared.domain.folder_readmes`, `readme_problems`, `_named_documents`, the guard module, `documenter.md`). I wrote the definitions of title, subfolder line, link line, opening and "no part of the form" into the `readme_problems` bullet (entry 4, answer 4).
   - Criteria: each is testable by one test. Every rule has both sides: each shape limit at and past its limit, and the missing-README case. Three criteria are added from entry 4: the operator/README.md row in criterion 5 (answer 1), a new criterion 7 for a listed path with no file (answer 2), and a new criterion 8 for the guard helper that leaves out hidden folders and `__pycache__` (answer 3). They stand before the two closing criteria, which are now 9 and 10.
   - Smoke test: the command is runnable and has no pytest `-q` issue. Its `Expect:` line (`23 ['x: no README.md']`) can be checked against the output, and the list has 23 paths.
   - Docs criterion: it names what the reader must know in four places (shared.md, the project guide README, the style page, decisions.md) and dictates no sentences.
   - Architecture: a domain constant in `shared` and the wiring in `entry` fit the layering. `check_documents` already sits in `entry`.
   - Scope: within feature.md's S0001 scope. The write_paths change stays with the human, and the leave for the documenter's tests is stated in the Interface (feature decision 5). Route: `tests`, because the Interface changes code and tests.
7. factory: started tests as vm.
8. tester: I wrote the tests for every criterion. I stop at step 4: to write the boundary rows of criterion 2, I had to decide two counts the Interface leaves open. Two coders could count them differently, and a row at 25 words passes or fails depending on which count is used.

   1. "A subfolder line of more than 25 words": which words count? (a) only the sentence after the backticked name; (b) the whole line without the leading `- `, so the name counts as one word; (c) every token of the line, `-` included. With (b) a line I count as 25 words is 26, and the at-limit row fails. I would choose (a), and the tests use it now: the line is ``- `lib/` `` and then a sentence of 25 words (no finding) or 26 words (one finding).
   2. The `<n>` in "line <n> is no part of the form": (a) the 1-based line number in the whole README, blank lines counted, like an editor's line number; (b) the number among the non-blank lines only. I would choose (a). The test expects `line 10` for a line of prose after the list in a 10-line README that has blank lines.

   What I settled myself without asking, from the Interface's literal text, for you to confirm along with the answer: a subfolder line is ``- `name/` `` plus a space and a sentence that ends with a period (``- `bin/` holds files of the operator.``). Sentences are counted by their closing periods. The rows of criterion 2 check only how often their own line appears, so an extra finding of another rule on the same text does not fail them.

   If you answer (a) to both, the tests stay as they are and the next run ends with `doing`.

   Mapping, as written:
   - criterion 1: tests/shared/domain/test_folder_readmes.py::test_a_readme_and_its_subfolders_give_what_they_disagree_on (rows: no-readme, every-subfolder-named, subfolder-not-named, named-subfolder-missing, both-sorted, line-without-a-sentence)
   - criterion 2: tests/shared/domain/test_folder_readmes.py::test_a_readme_out_of_its_form_gives_one_line_per_rule (rows: section, code-block, opening of two and of three sentences, no-relative-link, subfolder line of 25 and of 26 words and of two sentences, free-prose-after-the-list, at the line limit of 12 and one line past it)
   - criterion 3: tests/guards/test_folder_readmes.py::test_every_listed_readme_is_a_readme_of_a_folder_that_exists and ::test_every_package_under_the_factory_package_has_its_readme_listed
   - criterion 4: tests/guards/test_folder_readmes.py::test_a_folder_readme_agrees_with_its_folder (one row per path of `FOLDER_READMES`; a README that is not written yet is skipped with its path in the reason)
   - criterion 5: tests/entry/test_check_documents_folder_readmes.py::test_a_missing_name_in_a_readme_blocks_when_listed_and_is_reported_otherwise (rows: folder README and `operator/README.md`, each listed and not listed; the `operator/README.md` text has a section and prose after it, and no shape finding may appear)
   - criterion 6: tests/agent_files/test_claude_agent_texts_folder_readmes.py::test_the_documenter_may_write_the_folder_readmes_which_point_to_the_guides (exactly one line of documenter.md names "write", "folder readme", `factory.shared.domain.folder_readmes`, "points to the guides" and "guide page")
   - criterion 7: tests/entry/test_check_documents_folder_readmes.py::test_a_listed_folder_readme_that_does_not_exist_is_no_document_of_the_check
   - criterion 8: tests/guards/test_folder_readmes.py::test_the_subfolders_leave_out_hidden_folders_and_pycache (it tests the guard's helper `_subfolders`)

   Files created: tests/shared/domain/test_folder_readmes.py, tests/guards/test_folder_readmes.py, tests/entry/test_check_documents_folder_readmes.py, tests/agent_files/test_claude_agent_texts_folder_readmes.py.

   Test run (`uv run pytest -q` on the four files): 3 collection errors, in the first three files; their common import is the missing module `factory.shared.domain.folder_readmes`. The tail I read did not show the error text or the documenter test's result. I expect that test to fail because documenter.md does not yet have the sentence.

   `make lint`: green, after `ruff format` on the new files.

   I changed no earlier test. Which earlier documenter tests the new sentence breaks depends on how the coder words it, so I can't name them yet. Under the leave in feature decision 5, I make that change after the coder's run names them.
9. 2026-11-07 human: (a) to both: the 25 words count only the sentence after the backticked name, and <n> is the 1-based line number in the whole README, blank lines counted. What you settled yourself is confirmed: a subfolder line is a dash, the backticked name ending in /, a space and a sentence ending with a period; sentences are counted by their closing periods; each row of criterion 2 checks only its own line. Keep the tests as they are.
10. factory: started tests as vm.
11. tester: In journal entry 9 the human answered (a) to both questions. The 25 words count only the sentence after the backticked name. `<n>` is the 1-based line number in the whole README, with blank lines counted. The human confirmed the rest and said to keep the tests as they are, so I left the tests committed in the last tests run unchanged. I checked again that the two boundary rows match that answer. The free prose sits on line 10, counting blank lines. The line limit is 12: the title, the opening, eight link lines and two subfolder lines, with two subfolders.

    Mapping:
    - criterion 1: tests/shared/domain/test_folder_readmes.py::test_a_readme_and_its_subfolders_give_what_they_disagree_on
    - criterion 2: tests/shared/domain/test_folder_readmes.py::test_a_readme_out_of_its_form_gives_one_line_per_rule
    - criterion 3: tests/guards/test_folder_readmes.py::test_every_listed_readme_is_a_readme_of_a_folder_that_exists and tests/guards/test_folder_readmes.py::test_every_package_under_the_factory_package_has_its_readme_listed
    - criterion 4: tests/guards/test_folder_readmes.py::test_a_folder_readme_agrees_with_its_folder
    - criterion 5: tests/entry/test_check_documents_folder_readmes.py::test_a_missing_name_in_a_readme_blocks_when_listed_and_is_reported_otherwise
    - criterion 6: tests/agent_files/test_claude_agent_texts_folder_readmes.py::test_the_documenter_may_write_the_folder_readmes_which_point_to_the_guides
    - criterion 7: tests/entry/test_check_documents_folder_readmes.py::test_a_listed_folder_readme_that_does_not_exist_is_no_document_of_the_check
    - criterion 8: tests/guards/test_folder_readmes.py::test_the_subfolders_leave_out_hidden_folders_and_pycache (tests the guard's helper `_subfolders`)
    - criteria 9 and 10 (`make check`, docs): no tests.

    Files, all created in the previous tests run and unchanged in this one: tests/shared/domain/test_folder_readmes.py, tests/guards/test_folder_readmes.py, tests/entry/test_check_documents_folder_readmes.py, tests/agent_files/test_claude_agent_texts_folder_readmes.py.

    Test run (`uv run pytest -q` on the four files): 3 collection errors, in the first three files. Their common import is the missing module `factory.shared.domain.folder_readmes`; the tail I read shows only the three ERROR lines, not the error text. The documenter test is expected to fail because documenter.md does not yet have the sentence; the tail did not show its result.

    `make lint`: green.

    Open: I changed no earlier test. Which earlier documenter-text tests the new sentence breaks depends on how the coder words it. Under the leave of feature decision 5, I make that change once the coder's run names those tests.

    `lint`: lint: green (0.2 s)
12. factory: started doing as vm.
13. coder: I built the folder README list and its checks. `make test` passes in full (no earlier test broke) and `make check` is green.

    - `src/factory/shared/domain/folder_readmes.py` (new): `FOLDER_READMES` holds the 23 paths in the Interface's order. `readme_problems` makes one pass over the README's lines into a private `_Reading`, then builds the subfolder lines and the shape lines from it and sorts them. The limits are module constants: `OPENING_SENTENCES`, `SUBFOLDER_LINE_SENTENCES`, `SUBFOLDER_LINE_WORDS` and `BASE_LINES`.
      - It counts sentences by their closing `.`, `!` or `?` followed by a space or the line's end, so a dotted module name in backticks does not count.
      - A relative link is a Markdown link whose target has no scheme and is not an `#anchor`.
      - Lines inside a code fence are skipped. A heading gives "has a section" and nothing else.
      - The line limit counts every non-blank line, the lines inside a code fence included.
      - A subfolder line without a sentence (``- `x/` ``) still ends the opening, but it names nothing.
      - The 25 words count only the sentence after the name, and `<n>` is the line number in the whole README, as the human answered in entry 9.
    - `src/factory/entry/check_documents.py`: `_named_documents` also returns each path of `FOLDER_READMES` that exists, and `operator/README.md`. No shape rule is applied there. A listed README that does not exist is left out, so `checked_list_findings` gives the same finding as before.
    - `agents/agents/documenter.md`: after the "Write only README and `docs/`" bullet, a new bullet says the documenter may also write the folder READMEs of `FOLDER_READMES` in `factory.shared.domain.folder_readmes`. A folder README points to the guides, and whatever needs explaining goes into the guide page it links to. No earlier documenter test fails with this sentence, so the tester has no change to make under feature decision 5.

    Main decision: I used a single line-by-line pass that records what it finds, then derived the problem lines from that record. I rejected a separate regex pass for each rule. It would have read the opening, the code fences and the list again for each rule and would disagree at the edges, for example a heading inside a fence.

    Refactor pass: I renamed `in_list` to `past_opening`, because the flag marks the end of the opening and not a list. Nothing else needed changing.

    Noticed but not touched:
    - The real `operator/README.md` and `docs/README.md` are now read by the name check. Whatever names in them do not resolve show up in the report of `make documents` until they are listed. That is the docs stage's concern.
    - The documenter's `write_paths` stay the human's change at merge, as the Interface says.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 39 known, 4 gone
14. factory: started review as vm.
15. reviewer: Review, round 0. I read the work item, the diff (`src/factory/shared/domain/folder_readmes.py`, `src/factory/entry/check_documents.py`, `agents/agents/documenter.md`, the four new test files) and the new findings of `make duplicates`, which I ran.

    Findings:
    1. `src/factory/shared/domain/folder_readmes.py:98-102` (`_read`): the loop starts at line 2 and never looks at line 1. A README whose first line is `## Something` or prose, or that has no `# <title>` at all, gives no finding. The Interface defines the title as the first line, `# ` and a text, and says a heading line other than that title gives `<folder>: has a section`, and a line that is neither the title, the opening, a link line, a list line nor blank gives `line <n> is no part of the form`. Fix: check line 1. A heading that is not `# <text>` gives `has a section`, and a line 1 that is no heading gives `line 1 is no part of the form`. Story gap as well: criterion 2 has no row for a first line that is not the title. The fix needs a code change, so I add no criterion myself: the coder should ask for a row "a first line that is not `# <title>`" (or the human adds it), and the tester writes it.
    2. `src/factory/shared/domain/folder_readmes.py:40,76-80` (`_FENCE`, the `in_fence` toggle): this is a second, narrower copy of the fence reading in `factory.shared.domain.sections` (`opening_fence`, `code_blocks`, `lines_outside_blocks`, used by `documents.py`). It sees only ```` ``` ```` at column 0. A `~~~` fence, or an indented one, gives no `has a code block`, and inside the opening its lines may give no finding at all, which goes against the Interface's "a fenced code block". Fix: find the fenced lines with `sections.code_blocks` / `lines_outside_blocks` (or `opening_fence`) and drop the private toggle.

    Checked and found sound:
    - Group 1: criteria 1 to 8 each have a test that tests what the criterion says. The boundary rows are there: opening of 2 and 3 sentences, subfolder line of 25 and 26 words and of two sentences, line limit 12 and 13. The journal shows `make check` green after the coder (entry 13).
    - Group 2: the layering holds (pure domain module in `shared`, wiring in `entry`). `_named_documents` lists no document twice, because `docs/README.md` lies outside the two guide folders it reads with `rglob`.
    - Group 3: no silencing markers, no secrets, no shell built from strings.
    - `make duplicates`: its one new finding in this diff is `readme_problems` flagged as unused. That is expected, since its caller is the guard under `tests/`, as the Interface designs.
    - Group 5: the Description, the journal (the one-pass design, with per-rule regexes rejected) and the docs criterion match what was built.
    - The diff changes no document under `README.md`, `docs/` or `operator/README.md`.

    Earlier tests: none. Every test file in the diff is new (status `A`).
