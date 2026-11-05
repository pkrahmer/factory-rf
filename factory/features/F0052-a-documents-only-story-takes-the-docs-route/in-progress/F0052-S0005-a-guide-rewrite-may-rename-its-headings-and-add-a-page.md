---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 576
comments_read: [6672543099]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T23:44:05.953582Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T23:44:05.960465Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T23:44:35.723387Z'
  stage: intake
  run: 49897cb0793345fa860a8356242c8072
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T23:46:25.362068Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T23:46:27.738072Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T23:46:49.426688Z'
  stage: intake
  run: afbf83952cd34acd99fe95f73b65b0b1
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T23:46:54.852929Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-05T23:48:17.847463Z'
  stage: tests
  run: d2125cc592f946428cc59220eb3856e2
---

# A guide rewrite may rename its headings and add a page

## Description

The docs route exists so that the rewrite of the guides can run without a tester or a coder, but two guards written for an earlier regrouping of the guides block that rewrite. `tests/guards/test_project_guide_files.py` and `tests/guards/test_operator_guide_files.py` pin every earlier `##` and `###` heading of both guides, with its count, in their `HEADINGS` tables. The operator guide's table even requires the headings `## Replaced in v1.2` and `## Replaced from v1`, which rules 1 and 7 of `docs/project-guide/style.md` forbid. The project guide's guard also pins its file list, so a new page makes `make check` red. In the first story on the docs route, a new page did just that: the check stalled after `docs-only`, and the story had to take the code route through a tester, a coder and a question to the human. The rewrite stories in the backlog say "its headings may change", so each of them would leave the route the same way. This story removes the two heading tables and the tests that read them. It replaces the project guide's fixed file list with a rule read from the guide's index. Every page in the folder is named in the index's *The files*, every page named there exists, and every area of the package keeps its page. The searches for removed file names stay as they are, and so does the operator guide's list of topic files, because the rewrite adds no topic file. This is a story of the code route, since it changes only tests.

## Interface

- `tests/support/guide_files_support.py` (support module), one new function:

  ```python
  def index_problems(guide: Path, required: Sequence[str]) -> list[str]:
      """What the index `README.md` of `guide` and the folder's pages disagree on, one line each."""
  ```

  - A Markdown file of `guide` other than `README.md` that no line of the index's `## The files` section names as ``- `<name>` `` followed by any text with a word character and ending in a full stop (a colon after the name is allowed) gives the line `not in the index: <name>`.
  - A name that the section names and that is not a file of `guide` gives the line `missing: <name>`.
  - A name in `required` that is not a file of `guide` gives the line `missing: <name>`, once.
  - A guide with no problem gives `[]`. The lines are sorted.
- `tests/guards/test_project_guide_files.py`, an earlier story's test: `HEADINGS` and `test_every_earlier_heading_is_kept_as_often_as_before` go. `test_the_guide_holds_the_index_and_its_named_files` and `test_the_index_names_each_file_with_a_sentence` become one test of `index_problems(GUIDE, AREA_FILES) == []`; the surviving name is `test_the_guide_holds_the_index_and_its_named_files`, `test_the_index_names_each_file_with_a_sentence` goes, and the check `names == sorted(...)` is dropped. `REMOVED_FILES` and `test_no_file_names_a_removed_guide_file` stay.
- `tests/guards/test_operator_guide_files.py`, an earlier story's test: `HEADINGS` and `test_every_earlier_heading_is_kept_in_the_folder` go. The other tests stay.
- `tests/guards/test_guide_index_problems.py` (new): the rows of `index_problems` on guide folders written under `tmp_path`.
- The two earlier modules belong to earlier stories. Feature decision 7 gives the leave for changing them, and the tester names it in its entry.

## Acceptance criteria

1. `index_problems` on a folder under `tmp_path` gives these results, one row each of one parametrized test. A folder whose index names each page gives `[]`. A page that the index does not name gives `["not in the index: extra.md"]`. A named page that is missing gives `["missing: gone.md"]`. A required page that is missing gives `["missing: shared.md"]`. An index line for a page with no sentence (``- `page.md` ``) counts as not naming it. A heading renamed in a page gives `[]`. An index line with a colon (``- `page.md`: A sentence.``) gives `[]`. A folder with a missing `a.md` named by the index and an unnamed `z.md` gives `["missing: a.md", "not in the index: z.md"]`. A page that the index names and `required` names, and that is missing, gives `["missing: shared.md"]` once. A folder with `README.md` and `notes.txt`, neither named, gives `[]`. A page named only in a bullet of another section gives `["not in the index: other.md"]`.
2. `index_problems(docs/project-guide, AREA_FILES)` on the repository gives `[]`.
3. No test under `tests/guards/` reads a list of the guides' headings. `tests/guards/test_project_guide_files.py` and `tests/guards/test_operator_guide_files.py` hold no `HEADINGS` table, and every test that remains in them keeps its name.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *The files*: one sentence saying that a guard requires every page of the folder to be named in this section and every area to have its page, and that headings are free. `docs/operator-guide/`: none, because the operator does not run the guards. `docs/decisions.md`: one entry. It says the headings of the guides are no longer pinned. The reason is that the regrouping the tables guarded is done, and a rewrite in the style page must rename headings without a test change. Rejected: keeping the tables and changing their rows in each rewrite story, which would cost every rewrite a tester and a coder.

## Smoke test

```bash
grep -c "^HEADINGS" tests/guards/test_project_guide_files.py tests/guards/test_operator_guide_files.py | awk -F: '{s += $2} END {print s}'
```
Expect: `0`

```bash
uv run pytest tests/guards/test_project_guide_files.py tests/guards/test_operator_guide_files.py tests/guards/test_guide_index_problems.py 2>&1 | tail -1 | grep -c " passed"
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: 1. The line format in the Interface does not match the index. The Interface says an index line is ``- `<name>` <a sentence>.``. Every line of `docs/project-guide/README.md`, *The files*, is ``- `<name>`: <sentence>.`` with a colon, and the current guard's pattern `^- `name`[^.]*\w[^.]*\.` tolerates it. A coder who follows the Interface literally fails criterion 2. Options: (a) the line is `` - `<name>` `` followed by anything with a word character and ending in a full stop, so the colon is allowed. This is the existing pattern, and I would choose it. (b) The colon is required. Please state the format exactly, because criterion 1's "no sentence" row depends on it. Give the colon case in the criterion, as a row that gives `[]`.
   2. Two clauses of the Interface have no criterion. (i) "The lines are sorted": there is no row with two problems, for example `["missing: a.md", "not in the index: z.md"]`. (ii) "A name in `required` that is not a file of `guide` gives `missing: <name>`, once": there is no row where the same name is also named by the index and missing. Without a row for the case where `required` and the index both name a missing page, a coder can pass every listed row with a duplicate line. Please add a row for each.
   3. Two further sides have no criterion. (i) Which files count as pages: "A Markdown file of `guide` other than `README.md`". No row shows that `README.md` itself needs no index line, or that a non-Markdown file is ignored. I would add both rows, with `README.md` and `notes.txt` unnamed and the result `[]`. (ii) Whether a name in the index that sits outside the section `## The files` (for example in another section's bullet) counts as naming. Please add a row, or say that the rule is not meant to be tested.
   4. Criterion 3 says "every test that remains in them keeps its name". Criterion 5 and the Interface merge `test_the_guide_holds_the_index_and_its_named_files` and `test_the_index_names_each_file_with_a_sentence` into one test, so the other name goes. The Interface does not say which name survives. Please name the surviving test. I would keep `test_the_guide_holds_the_index_and_its_named_files`. Please also say whether the check that the folder holds no file other than the index and the named ones (`names == sorted(...)`) is dropped. `index_problems` ignores non-Markdown files, so it would be.

   The rest checks out: the route (`tests`) is right because the Interface changes only tests, the story is within feature decision 7, and the two smoke test commands are runnable. Pytest's `addopts` sets `-q`, and the command passes no second `-q`. The Expect lines are checkable.
4. 2026-11-05 human: 1. (a): an index line is ``- `<name>` `` followed by any text with a word character and ending in a full stop, so the colon is allowed. This is the existing pattern. Criterion 1 gets a row with the colon form (``- `page.md`: A sentence.``) that gives `[]`.
   2. Yes to both rows: (i) two problems give the sorted `["missing: a.md", "not in the index: z.md"]`; (ii) a page that the index names and `required` names, and that is missing, gives `["missing: shared.md"]` once.
   3. (i) Yes: a folder with `README.md` and `notes.txt`, neither named, gives `[]`. (ii) A name counts only inside `## The files`: a page named only in a bullet of another section gives `["not in the index: other.md"]`. One row.
   4. The surviving test is `test_the_guide_holds_the_index_and_its_named_files`; `test_the_index_names_each_file_with_a_sentence` goes, and criterion 3 holds for every other test. The check `names == sorted(...)` is dropped: `index_problems` replaces it and ignores non-Markdown files.
5. factory: started intake as vm.
6. intake: accepted, with the human's answers (journal entry 4) carried into the story. I made these edits in the story and changed nothing else: the Interface now states the index line format (colon allowed, per 4.1a). Criterion 1 gained the rows from 4.1 to 4.3. Those are the colon form, the two sorted problems, the `required` plus index duplicate that appears once, `README.md` and `notes.txt` unnamed, and a name outside `## The files`. The Interface also names the surviving test `test_the_guide_holds_the_index_and_its_named_files` and drops `test_the_index_names_each_file_with_a_sentence` and the `names == sorted(...)` check (4.4).
   - Interface: names concrete modules and one signature, `index_problems(guide, required)` in `tests/support/guide_files_support.py`, and the edits to two named guard modules and one new one. Each line of its behaviour is now stated exactly.
   - Criteria: each is testable by one parametrized or plain test. Each rule has its failing side: not in the index, missing, required missing, and a sentence-less line. Sorting and the duplicate case now have rows. Criterion 3 holds for the remaining tests, and the surviving name is given.
   - Smoke test: both commands are runnable. Pytest's `addopts` sets `-q` and the command passes no second one, so `tail -1 | grep -c " passed"` can be met. Each `Expect:` line is checkable.
   - Architecture: the changes are tests and a support module, in the places CLAUDE.md prescribes: `tests/support/*_support.py` and `tests/guards/`. A new support module function is shared and no test module is imported by another.
   - Scope: within feature decision 7, which gives the leave to change the two earlier guard modules. The tester must name that leave in its entry. The project guide's file-list rule is replaced by the index rule, which is the story's own description.
   Route: tests, because the Interface changes test files and a support module, none of which the documenter may write.
7. factory: started tests as vm.
8. tester: I wrote the tests from the Interface and the criteria. The story changes only tests and a test support module, so I also wrote `index_problems` in `tests/support/guide_files_support.py`, as the tester of F0051-S0010 wrote that module. This means the tests are green and not red. There is nothing left for the coder to implement except running `make check`. The documenter still has the docs criterion.

   Criteria → tests:
   - criterion 1: tests/guards/test_guide_index_problems.py::test_index_problems_name_what_index_and_folder_disagree_on. It has 12 rows: every-page-named, page-not-named, named-page-missing, required-present, required-missing, line-without-sentence, heading-renamed, colon-after-name, two-problems-sorted, named-and-required-missing-once, index-and-non-markdown-ignored, named-outside-the-files. The required-present row is the passing side of the `required` rule.
   - criterion 2: tests/guards/test_project_guide_files.py::test_the_guide_holds_the_index_and_its_named_files (now `index_problems(GUIDE, AREA_FILES) == []`)
   - criterion 3: structural. `HEADINGS`, `test_every_earlier_heading_is_kept_as_often_as_before`, `test_every_earlier_heading_is_kept_in_the_folder` and `test_the_index_names_each_file_with_a_sentence` are removed, and so are the `names == sorted(...)` check and `NAMED_FILES`. A grep finds no `HEADINGS` or `guide_headings` under `tests/guards/`. Every remaining test keeps its name. The smoke test's first command checks this.
   - criterion 4: `make check`, the coder's run.
   - criterion 5: docs, the documenter's.

   Files:
   - created: tests/guards/test_guide_index_problems.py.
   - changed in the support module: tests/support/guide_files_support.py. Added `index_problems` with a private `_the_files_section` and `INDEX_LINE`, which is the earlier guard's pattern with the name captured. Removed `guide_headings`, which nothing uses any more, and updated the module docstring.
   - changed, earlier stories' tests, under the leave of feature decision 7: tests/guards/test_project_guide_files.py and tests/guards/test_operator_guide_files.py. Removed the unused `pytest` imports and changed the first module's docstring.

   Behaviour on cases the criteria leave open:
   - A line in *The files* that names a page without a sentence counts neither as naming the page nor as a `missing:` line. That only matters for a missing page, and it is untested.
   - An index with no `## The files` section names nothing.

   Run: `uv run pytest -q` on the three guard files gave 17 passed. No module failed to import. `make lint` is green, and `mypy --strict` on the four files found no issues.

   `lint`: lint: green (0.2 s)
