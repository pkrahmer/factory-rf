---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-05T23:44:05.960465Z'
  lease_duration: 60
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

  - A Markdown file of `guide` other than `README.md` that no line of the index's `## The files` section names as ``- `<name>` <a sentence>.`` gives the line `not in the index: <name>`.
  - A name that the section names and that is not a file of `guide` gives the line `missing: <name>`.
  - A name in `required` that is not a file of `guide` gives the line `missing: <name>`, once.
  - A guide with no problem gives `[]`. The lines are sorted.
- `tests/guards/test_project_guide_files.py`, an earlier story's test: `HEADINGS` and `test_every_earlier_heading_is_kept_as_often_as_before` go. `test_the_guide_holds_the_index_and_its_named_files` and `test_the_index_names_each_file_with_a_sentence` become one test of `index_problems(GUIDE, AREA_FILES) == []`. `REMOVED_FILES` and `test_no_file_names_a_removed_guide_file` stay.
- `tests/guards/test_operator_guide_files.py`, an earlier story's test: `HEADINGS` and `test_every_earlier_heading_is_kept_in_the_folder` go. The other tests stay.
- `tests/guards/test_guide_index_problems.py` (new): the rows of `index_problems` on guide folders written under `tmp_path`.
- The two earlier modules belong to earlier stories. Feature decision 7 gives the leave for changing them, and the tester names it in its entry.

## Acceptance criteria

1. `index_problems` on a folder under `tmp_path` gives these results, one row each of one parametrized test. A folder whose index names each page gives `[]`. A page that the index does not name gives `["not in the index: extra.md"]`. A named page that is missing gives `["missing: gone.md"]`. A required page that is missing gives `["missing: shared.md"]`. An index line for a page with no sentence (``- `page.md` ``) counts as not naming it. A heading renamed in a page gives `[]`.
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
