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
