---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 632
comments_read: [6705414222]
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
