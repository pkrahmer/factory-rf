---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 641
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T15:06:28.399880Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T15:06:28.406925Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T15:06:50.924801Z'
  stage: intake
  run: 162835f69b1e4918a5ba14b8dbd1b009
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T15:06:55.954507Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-07T15:07:33.654163Z'
  stage: tests
  run: 51afc1090c0240be85ad5b71de1a994f
---

# A folder README keeps its opening and its link lines short

## Description

Feature decision 6 says a folder README stays a pointer: an opening of at most two sentences and nothing beside the links and the subfolder lines. `readme_problems` lets two things past it. A line that carries a relative link is taken as a link line and never counted, so an opening that carries a link escapes the two-sentence limit (`One. Two. Three. Four. Five, see [g](g.md).` gives `[]`), and a link line may hold any number of sentences of any length, after the subfolder list too (eight lines of 200 words, each with a link, give `[]`). Only the line limit bounds them. `docs/project-guide/style.md` already says "no other prose", so the code is laxer than the documents. This story closes both: the opening is the first paragraph after the title and counts its sentences whether or not it carries a link, and every other line that is no subfolder line and carries a relative link holds one sentence of at most 25 words. All 22 READMEs of today keep to these rules (measured at the feature's acceptance), so no README changes. The word limit of the opening itself and the number of link lines stay as they are (the human, 2026-11-07). No README changes in this story: the human shortened `docs/README.md`'s one long link line on main before it started, so all 22 READMEs keep to the new rules.

## Interface

- `factory.shared.domain.folder_readmes` (domain), changed:

```python
LINK_LINE_SENTENCES: Final = 1
LINK_LINE_WORDS: Final = 25

def readme_problems(folder: str, readme: str | None, subfolders: Sequence[str]) -> list[str]
```

- The opening is the paragraph right after the title: its consecutive non-blank lines, up to the first blank line. Its sentences are counted whether or not a line of it carries a relative link; more than `OPENING_SENTENCES` (two) gives `<folder>: the opening is longer than two sentences`, as today. A link in the opening still counts as the README's link to a guide.
- A link line is a line after the opening, outside code blocks, that is no subfolder line and carries a relative link (by `relative_link_targets`, as today). It holds at most `LINK_LINE_SENTENCES` sentence and at most `LINK_LINE_WORDS` words, words separated by whitespace with the link's markdown counted as written; past either limit it gives `<folder>: line <n> is a long link line`, `<n>` the 1-based line number in the whole README, blank lines counted.
- A line after the opening that is no subfolder line and carries no relative link stays `<folder>: line <n> is no part of the form`; a README without a title keeps having no opening.
- The tests are new rows of `tests/shared/domain/test_folder_readmes.py::test_a_readme_out_of_its_form_gives_one_line_per_rule` (written by F0055-S0001). The human's leave (2026-11-07): the tester adds rows to that test and changes none of its rows; every existing row keeps its result.

## Acceptance criteria

1. An opening that carries a relative link counts its sentences, rows of the test of the form: an opening of two sentences with a link gives no line; one of three sentences with a link gives `<folder>: the opening is longer than two sentences`.
2. A link line keeps its limits, rows of the same test: a link line of one sentence of 25 words gives no line; one of 26 words gives `<folder>: line <n> is a long link line`; one of two sentences gives the same line; a link line of 26 words after the subfolder list gives it too.
3. Every existing row of the test of the form keeps its result.
4. `make check` stays green.
5. docs: `docs/project-guide/style.md`, *Folder READMEs*: the reader learns that the opening is the first paragraph and counts its sentences with or without a link, and that a line with a link outside it is one sentence of at most 25 words. `docs/project-guide/shared.md`, *The folder READMEs*: the new finding of `readme_problems`.

## Smoke test

```bash
uv run python -c "from factory.shared.domain.folder_readmes import readme_problems; print(readme_problems('w', '# W\n\nOne. Two. Three, see [g](g.md).\n\n- \`a/\` One sentence.\n', ['a']))"
```
Expect: `['w: the opening is longer than two sentences']`

```bash
uv run python -c "from factory.shared.domain.folder_readmes import readme_problems; print(readme_problems('w', '# W\n\nOne.\n\n- \`a/\` One sentence.\n\nMore here, see [g](g.md). And more.\n', ['a']))"
```
Expect: `['w: line 7 is a long link line']`

```bash
uv run pytest tests/guards/test_folder_readmes.py 2>&1 | tail -1 | grep -c failed
```
Expect: `0`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `factory.shared.domain.folder_readmes`, the two constants `LINK_LINE_SENTENCES` and `LINK_LINE_WORDS`, and the `readme_problems` signature. It also states the opening as the paragraph up to the first blank line, the new finding text `line <n> is a long link line`, and how words and line numbers are counted.
   - Criteria: each is testable as a row of the existing parametrized test.
     - The opening is covered on both sides (two sentences with a link pass, three fail).
     - The link line is covered on both sides: 25 words pass, 26 words fail, two sentences fail, and 26 words after the subfolder list fail.
     - Criterion 3 keeps the existing rows' results. The Interface names the human's leave to add rows to that test and change none (2026-11-07).
     - The unchanged rules (a line without a link is "no part of the form", no title means no opening) stay pinned by the existing rows.
   - Smoke test: the commands are runnable. In the second one, `More here…` falls on line 7, so the expected `line 7` is right. The pytest command passes no `-q`, and the project's `addopts` already sets it. Its `grep -c failed` on the summary line gives `0`, so the Expect line can be checked.
   - Docs criterion: it names what the reader must know, in `style.md` *Folder READMEs* and `shared.md` *The folder READMEs*. It dictates no sentences.
   - Architecture: the change is confined to a pure `shared.domain` module with no I/O, as CLAUDE.md requires.
   - Scope: it fits feature decision 6 (a README stays a pointer) and is not in the feature's out-of-scope list. The route is `tests` because the Interface changes code under `src/`.
4. factory: started tests as vm.
5. tester: Added seven rows to `test_a_readme_out_of_its_form_gives_one_line_per_rule` in `tests/shared/domain/test_folder_readmes.py`, as the human allowed on 2026-11-07. I did not change any existing row. I also added a constant `GUIDE_LINK`, a constant `LONG_LINK_LINE_5` and a helper `_link_line(words)` to the same module. The helper builds one sentence with a relative link; the link `[the guide](../docs/README.md)` counts as two words, as written.

   - criterion 1: tests/shared/domain/test_folder_readmes.py::test_a_readme_out_of_its_form_gives_one_line_per_rule, rows `opening-of-two-sentences-with-a-link` (no line) and `opening-of-three-sentences-with-a-link` (the opening line)
   - criterion 2: the same test, rows `link-line-of-25-words` (no line), `link-line-of-26-words` and `link-line-of-two-sentences` (both `line 5 is a long link line`), `link-line-of-26-words-after-the-list` (`line 9 is a long link line`). The row `link-line-of-25-words-after-the-list` (no line) is the accepted side of that limit after the list.
   - criterion 3: the existing rows of the same test and of `test_a_readme_and_its_subfolders_give_what_they_disagree_on`, unchanged. All of them pass today.
   - criterion 4: `make check`, the coder's to keep green. `make lint` is green.
   - criterion 5: docs, not tested.

   Files: no new files. The only file changed is `tests/shared/domain/test_folder_readmes.py`, which F0055-S0001 wrote, under the leave quoted in the Interface.

   Run (`uv run pytest -q tests/shared/domain/test_folder_readmes.py`): four rows fail because the result is wrong. They are `opening-of-three-sentences-with-a-link`, `link-line-of-26-words`, `link-line-of-two-sentences` and `link-line-of-26-words-after-the-list`; each gets `[]` where one line is expected. Every other row passes. The test runner imported every module, since `factory.shared.domain.folder_readmes` already exists. The rows do not import the new constants `LINK_LINE_SENTENCES` and `LINK_LINE_WORDS`.

   `lint`: lint: green (0.1 s)
