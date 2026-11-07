---
stage: review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 632
comments_read: [6705414222, 6705474496]
handed_over: null
claim:
  instance: vm
  stage: review
  started_at: '2026-11-07T10:44:48.248914Z'
  lease_duration: 60
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
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T10:28:08.859752Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-07T10:32:46.752909Z'
  stage: doing
  run: 18f6f4149156497cb901a69315899819
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-07T10:32:52.122835Z'
  stage: review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-07T10:34:19.372120Z'
  stage: review
  run: 29ddc7d7620b48bcb063a873398c379e
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-07T10:34:24.725385Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-07T10:39:18.811416Z'
  stage: doing
  run: 5bd98b7ee0744f90942490afe12bf924
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-07T10:39:23.980499Z'
  stage: tests
- number: 23
  speaker: tester
  kind: result
  at: '2026-11-07T10:40:06.979228Z'
  stage: tests
  run: 6422c9e797e2418194922323e8c02445
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-07T10:40:12.308493Z'
  stage: doing
- number: 25
  speaker: coder
  kind: result
  at: '2026-11-07T10:44:43.532466Z'
  stage: doing
  run: 84a2478c1aaa439d91402f411c8479f0
- number: 26
  speaker: factory
  kind: started
  at: '2026-11-07T10:44:48.248914Z'
  stage: review
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
9. The shape rules hold from the first line and for every fence, as more rows of the test of criterion 2: a first line that is a heading other than `# <title>` (`## A`) gives `has a section`; a first line of prose gives `line 1 is no part of the form`; a `~~~` fence and a fence indented by spaces each give `has a code block`; a README whose only link is a web address (`https://…`) gives `links to no guide`.
10. `make check` stays green.
11. docs: `docs/project-guide/shared.md`, the document check: the reader learns which READMEs the check reads and where their list lives. `docs/project-guide/README.md`: the guard of the folder READMEs among the guards. `docs/project-guide/style.md`, a new section *Folder READMEs*: the form of a folder README and its limits (feature decisions 2 and 6), and that anything needing explanation belongs in the guide page the README links to. `docs/decisions.md`: one entry for feature decisions 1 to 3, with the rejected option: a README in every folder, which would cost about 25 more files that all say the same.

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
16. factory: started doing as vm.
17. coder: Round 1: I fixed both review findings from entry 15 in `src/factory/shared/domain/folder_readmes.py` and changed nothing else. `make check` is green (`check: green`, `test: green (106.6 s)`).

    1. **Line 1 is now checked** (finding 1). `_read` now looks at the first line. It is passed over only when it is the title, that is `# ` followed by a non-blank text (`_TITLE`). If it is not the title, the README has no opening. So `_Reading` starts with `past_opening=True`, and every line goes through `_read_line`, line 1 included:
       - a heading that is not a title (`## A`, or `# ` alone) gives `has a section`;
       - a line of prose gives `line 1 is no part of the form`;
       - a link line still counts as a link.
       
       I checked these by hand: `## A` + link gives `['x: has a section']`, and `prose.` + link gives `['x: line 1 is no part of the form']`.
    2. **Fences come from the shared reader** (finding 2). I removed the private `_FENCE` toggle and the `in_fence` field. The fenced lines now come from `factory.shared.domain.sections`, through `split_lines`, `code_blocks` and `lines_outside_blocks`. A `~~~` fence and an indented fence now give `has a code block`. Lines inside such a fence are not read as opening, heading or prose lines. I checked both cases by hand: each gives `['x: has a code block']`.

    Main decision: I made a missing title mean there is no opening. Every line is then held to the form, as after the list. I rejected only patching the first line and leaving the opening logic as it was. With that, a README without a title would still have its prose counted as an opening and get no line finding, which goes against the Interface's definition of the opening as the lines after the title.

    Refactor pass: I simplified the first version of the loop. It had a flag-or-index expression inside the loop; now `has_title` is computed once and sets `past_opening` before the loop. Nothing else needed changing.

    Open, as the reviewer noted:
    - Criterion 2 has no row for a first line that is not `# <title>`. The fix is in the code, but no test pins it. A row "a first line that is not `# <title>`" (heading → `has a section`, prose → `line 1 is no part of the form`) needs a criterion from the human or the reviewer, and the tester to write it.
    - Criterion 2 also has no row for a `~~~` fence or an indented fence.

    I changed no test.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 39 known, 4 gone
18. factory: started review as vm.
19. reviewer: Review, round 1. I read the work item, the whole diff outside `factory/` (`src/factory/shared/domain/folder_readmes.py`, `src/factory/entry/check_documents.py`, `agents/agents/documenter.md`, the four new test files), and the helpers it now uses in `factory.shared.domain.sections` and `factory.shared.domain.documents`. The coder's round-1 fixes for both round-0 findings are in the code. Line 1 is now checked (`_read`, `_TITLE`), and fences now come from `sections.code_blocks` / `lines_outside_blocks`, whose `_FENCE_OPENING` accepts `~~~` and indented fences. But no test pins either fix.

    Findings:
    1. criterion 9 added: it needs its test. The diff now builds behaviour no criterion names, and pinning it needs no change under `src/`. These are more rows of the criterion-2 test `test_a_readme_out_of_its_form_gives_one_line_per_rule` in `tests/shared/domain/test_folder_readmes.py`: a first line `## A` gives `has a section`; a first line of prose gives `line 1 is no part of the form`; a `~~~` fence and an indented fence each give `has a code block`; a README whose only link is `https://…` gives `links to no guide`. The closing criteria are renumbered to 10 (`make check`) and 11 (docs).
    2. `src/factory/shared/domain/folder_readmes.py:45` (`_RELATIVE_LINK`): this is a second, different copy of the relative-link reading in `factory.shared.domain.documents` (`_LINK_TARGET` and `_link_name`, lines 101 and 499-505). That reading refuses targets that start with `/` or `#`, `mailto:`, anything with `://`, and placeholders or globs. The copy refuses only a scheme or `#`, so a root-absolute link such as `[guide](/docs/operator-guide/README.md)` counts as relative here. A README whose only link is root-absolute then gets no `links to no guide`, against the Interface's "no relative link", while the document check does not treat that same link as relative. Fix: decide "relative link" through one shared public helper in `documents.py` (made from `_LINK_TARGET` / `_link_name`) and drop `_RELATIVE_LINK`. Then a row "only link root-absolute → `links to no guide`" can be pinned; that row needs this code change, so I did not add it as a criterion. The coder should ask for it, or the tester adds it with criterion 9's rows.

    Checked and found sound:
    - Group 1: criteria 1 to 8 each have a test that tests what the criterion names. The boundary rows are there on both sides: an opening of 2 and 3 sentences, a subfolder line of 25 and 26 words, the line limit at 12 and at 13. The criterion-7 test pins the unchanged `checked_list_findings` finding. The journal shows `make check` green after the coder (entry 17).
    - Group 2: the layering holds. `folder_readmes` is a pure domain module in `shared` and now reuses `sections`; the wiring is in `entry`.
    - Group 3: no silencing markers, no secrets, no shell or SQL built from strings.
    - Group 4: apart from finding 2, the names, docstrings and why-comments (`_OPERATOR_README`, the no-title comment in `_read`) are fine.
    - Group 5: the Description still matches what was built. The journal gives the main decision (one pass; a missing title means no opening) and what was rejected. The docs criterion is unchanged and still fits.
    - The diff changes no document under `README.md`, `docs/` or `operator/README.md`.

    Earlier tests: none. Every test file in the diff is new (status `A`).
20. factory: started doing as vm.
21. coder: Round 2. I dealt with both findings in the reviewer's entry 19. Finding 1 needs only tests, so I am handing it on. Finding 2 needed code, and that is now done. `make check` is green (`test: green (105.9 s)`, `check: green`).

    Tests, for the tester: criterion 9 needs its rows in `tests/shared/domain/test_folder_readmes.py::test_a_readme_out_of_its_form_gives_one_line_per_rule`. They are a first line `## A` (gives `has a section`), a first line of prose (`line 1 is no part of the form`), a `~~~` fence and a fence indented by spaces (each `has a code block`), and a README whose only link is `https://…` (`links to no guide`). The reviewer also offered one more row, to go with criterion 9's rows: a README whose only link is root-absolute, such as `[guide](/docs/operator-guide/README.md)`, gives `links to no guide`. The code now gives that result. I checked it by hand: `/docs/a.md` gives `['x: links to no guide']` and `../docs/a.md` gives `[]`.

    What I built for finding 2 (the second copy of the relative-link reading):
    - `src/factory/shared/domain/documents.py`: a new public `relative_link_targets(line)` returns the relative targets of a line's Markdown links. It uses the document check's own `_LINK_TARGET`. The test of whether a target is relative moved out of `_link_name` into the private `_is_relative_link_target`, and `_link_name` now calls it. A target starting with `#`, `/` or `mailto:`, one containing `://`, and placeholders and globs are still refused, as before.
    - `src/factory/shared/domain/folder_readmes.py`: I removed `_RELATIVE_LINK`. `_read_line` now asks `relative_link_targets(line)`, so the README form and the document check decide "relative link" the same way.

    Main decision: I made the shared helper return a line's relative targets, built from the existing `_LINK_TARGET` and the refusals in `_link_name`. I rejected a public predicate on a single target: `folder_readmes` would then have needed its own copy of the link regex to find the targets.

    Refactor pass: I made the predicate private again (`_is_relative_link_target`), because only `documents.py` uses it. Nothing else needed changing.

    I changed no test and did not rewrite the Description. The reviewer's entry 19 had already added criterion 9 to it.

    Noticed but not touched: `folder_readmes` now imports `documents`, which imports pipeline-domain tables. That is allowed, since both are domain layers, but it makes the small module depend on a big one.
22. factory: started tests as vm.
23. tester: Round 2, tests for criterion 9. The coder's entry 21 says criterion 9, which the reviewer added, needs only its test. As step 0 says for such a criterion, I wrote its rows into the criterion-2 test. I changed no other test.

    Mapping:
    - criterion 9: tests/shared/domain/test_folder_readmes.py::test_a_readme_out_of_its_form_gives_one_line_per_rule, with five new rows:
      - `first-line-a-heading-other-than-the-title`: `## A` as line 1 gives `has a section`.
      - `first-line-of-prose`: line 1 is prose and gives `line 1 is no part of the form`.
      - `tilde-fence`: a `~~~` fence gives `has a code block`.
      - `fence-indented-by-spaces`: a fence indented by three spaces gives `has a code block`.
      - `only-link-a-web-address`: a README whose only link is `https://example.org/guide` gives `links to no guide`.

    To build these rows, the file's own `_readme` helper takes a new `title` keyword. Its default is the old title, so the existing rows did not change.

    Files changed: `tests/shared/domain/test_folder_readmes.py`, a file this story's tester wrote. I created no new files.

    Run: `uv run pytest -q tests/shared/domain/test_folder_readmes.py` passed all 22 tests. The code was already in place from rounds 1 and 2, so none of the new rows failed first. `make lint` is green. The test run could import every module.

    Not tested: a README whose only link is root-absolute (`[guide](/docs/operator-guide/README.md)` gives `links to no guide`). The reviewer offered this row in entry 19 and the coder built the behaviour in round 2. But it is in no criterion, and criterion 9 names only the `https://…` case. The tester tests only what the criteria say, so this row needs to be added to criterion 9 (by the reviewer or the human) before I write it. Once added, it is one more row of the same test.

    `lint`: lint: green (0.2 s)
24. factory: started doing as vm.
25. coder: Round 2, after the tester's criterion-9 rows (entry 23). I ran `make check` on the working tree as the tester left it, and it is green (`test: green (106.6 s)`, `check: green`). Every new row of `tests/shared/domain/test_folder_readmes.py::test_a_readme_out_of_its_form_gives_one_line_per_rule` passes against the code from rounds 1 and 2, so I changed no code.

    What is built:
    - `src/factory/shared/domain/folder_readmes.py`
    - `src/factory/shared/domain/documents.py`: the public `relative_link_targets`, and the private `_is_relative_link_target` that `_link_name` shares.
    - `src/factory/entry/check_documents.py`: `_named_documents` now also reads the folder READMEs and `operator/README.md`.
    - `agents/agents/documenter.md`

    Main decision: this round needed no code, so I made none. I rejected adding code or tests for the root-absolute link row beyond what the criteria name.

    Refactor pass: I read the diff under `src/` again and found nothing to change.

    Still open:
    - The root-absolute link row (`[guide](/docs/operator-guide/README.md)` gives `links to no guide`) is in no criterion. The code already gives that result: `relative_link_targets` refuses targets that start with `/`. But no test pins it. Criterion 9 names only the `https://…` case. If the row is wanted, the reviewer or the human must add it to criterion 9, and then the tester writes it as one more row of the same test.
    - Noticed but not touched, as in entry 21: `folder_readmes` imports the large `documents` module. Both are domain layers, so this is allowed.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 7 new, 39 known, 4 gone
26. factory: started review as vm.
