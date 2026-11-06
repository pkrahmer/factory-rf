---
stage: docs-only
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 583
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T01:39:43.565974Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T01:39:43.573036Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T01:40:08.668839Z'
  stage: intake
  run: 57eae0b55273448ab6ddfa4eca45b712
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T01:40:16.004706Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T01:43:08.202628Z'
  stage: docs-only
  run: e3f717bf302b421b8000f4becd4666fd
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T01:43:16.458324Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-06T01:43:48.800007Z'
  stage: docs-review
  run: b9e824ad5e3f466eba49ae99c68dd06e
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-06T01:43:57.339849Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-06T01:46:40.260137Z'
  stage: docs-only
  run: d1e45b241d3e4d2286de38f7b3aa856b
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-06T01:46:48.656428Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-06T01:47:22.303458Z'
  stage: docs-review
  run: 43c1f6358c1f4a908610983dfc12dd21
---

# The project guide says which lines of its index name a page
## Description

The guard `tests/guards/test_project_guide_files.py` reads a line of `## The files` in `docs/project-guide/README.md` as a page entry when the line starts with `` - ` ``, a name in backticks, and goes on to a sentence with a full stop (`INDEX_LINE` in `tests/support/guide_files_support.py`). The index does not say so. In F0052-S0007 the documenter started a list item with `` `## The files` ``. The guard read it as a page named "## The files" and reported it missing, and the docs-only stage stalled and cost a second run. The next feature rewrites this index on the docs route, where no tester reads the guard first. This story adds that rule to the index, in one or two sentences next to the sentence on the guard, so that a writer starts every other list item in the section with a word. The guard and its pattern stay as they are.

## Interface

- `docs/project-guide/README.md`, `## The files`, the paragraph that names the guard: it also says which lines the guard reads as a page entry (a list item that starts with a name in backticks and goes on to a sentence ending in a full stop), and that any other list item in this section must start with a word. The wording is the documenter's, by `docs/project-guide/style.md`.
- No code and no test changes.

## Acceptance criteria

1. `## The files` in `docs/project-guide/README.md` says that a list item starting with a name in backticks is read as a page entry, and that other list items start with a word.
2. The guard still passes: every page entry and every exception list item in the section reads as it did before. `uv run pytest tests/guards/test_project_guide_files.py` passes.
3. `make documents` prints `documents ok`.
4. `make check` stays green.
5. docs: `docs/project-guide/README.md`, *The files*, as above. `docs/decisions.md`: none, because nothing is decided. `docs/operator-guide/`: none, because the operator does not run the guards.

## Smoke test

```bash
sed -n '/^## The files/,/^## /p' docs/project-guide/README.md | grep -c 'backticks'
```
Expect: a number of at least `1`.

```bash
uv run pytest tests/guards/test_project_guide_files.py 2>&1 | tail -1 | grep -c " passed"
```
Expect: `1`

```bash
make documents 2>&1 | tail -1
```
Expect: `documents ok`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: the only path changed is `docs/project-guide/README.md`, section `## The files`, the paragraph naming the guard. It states what to say (which lines read as a page entry, and that other list items start with a word). No code or test changes. The path is one the documenter may write, so the route is docs-only.
   - Criteria: criterion 1 (the rule is in the section) is checkable by reading the text. Criterion 2 (guard still passes) names a command. Criterion 3 (`make documents` prints `documents ok`) names a command. Both sides of the rule are covered: a backtick-led item is a page entry, and any other item starts with a word. The closing `make check` and `docs:` criteria are last.
   - Smoke test: all three commands are runnable. The pytest command passes no `-q` and `pyproject.toml` `addopts` already sets `-q`, so `tail -1` shows the summary line and `grep -c " passed"` gives `1`. Each `Expect:` line is checkable: a count of at least 1, `1`, and `documents ok`.
   - Architecture: documents only, and the project guide is kept by the documenter. The guard and `INDEX_LINE` stay untouched.
   - Scope: it falls inside F0052's goal (the next feature's rewrite of the index takes the docs route). Nothing in "Out of scope" is touched.
4. factory: started docs-only as vm.
5. documenter: Changed `docs/project-guide/README.md`, `## The files`: the paragraph that names the guard now also says which lines the guard reads as a page entry (a list item that starts with a name in backticks and goes on to a sentence ending in a full stop) and that every other list item in the section must start with a word, with `## The files` as the example of what goes wrong. The rule matches `INDEX_LINE` in `tests/support/guide_files_support.py`; neither it nor the guard was touched. I ran `tests/guards/test_project_guide_files.py` and it passes. I did not run `make documents`; the factory runs it after this stage. The existing list items in that section all start with a word or an italic title, so they stay valid. Cross-read: the rest of `docs/project-guide/README.md` against the story. Nothing else is stale, and I saw no unrelated stale text. No decisions.md entry was written, so there is no Why or Rejected line to flag.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the work item, `INDEX_LINE` in `tests/support/guide_files_support.py` (`^- `([^`]+)`[^.]*\w[^.]*\.`), the guard `tests/guards/test_project_guide_files.py` and `docs/project-guide/style.md`. The facts are right. The guard reads a line as a page entry only when it starts with `` - ` `` and a backticked name, followed by text that holds a word and a full stop. A list item that starts any other way is never read as a page. The docs criterion's subject is covered. Two points remain, both about the writing:

   1. `docs/project-guide/README.md:17`, the sentence that starts "It reads a list item in this section as a page entry…": it is about 55 words, two clauses joined by a semicolon, which breaks style rule 2 (split a sentence of more than about 25 words). Fix: split it at the semicolon into two sentences. The first says which lines the guard reads as a page entry. The second says "Every other list item in this section starts with a word, so that…".
   2. `docs/project-guide/README.md:17`, "every other list item in this section must start with a word": three of the four exception items right below it start with an asterisk (`- *Kill points* …`, `- *Replaced from v1* …`, `- *The machine* …`), not a plain word. A writer reading the raw Markdown will see the rule broken by the lines right under it. The guard only refuses a backtick at the start. Fix: say what the guard allows, for example "starts with a word, plain or in italics, never with a name in backticks". That stays true of `INDEX_LINE` and meets criterion 1.

   Rejected as findings:
   - The example "a heading such as `## The files` is never read as a page" can stay. It names the very case that stalled the earlier story, and the guard does not read it.
   - Criteria 2 to 4 are met. Entry 5 of the journal records `check: green`, `secrets: green` and `documents ok`, and the diff touches no code or test.
8. factory: started docs-only as vm.
9. documenter: Round 1, fixing the reviewer's two findings. Changed `docs/project-guide/README.md`, `## The files`, the paragraph that names the guard. (1) I split the long sentence at the semicolon: the first sentence says which list items the guard reads as a page entry, and the second says every other list item starts with a word. (2) The second sentence now says "a word, plain or in italics, never with a name in backticks". That matches the italic-led exception items below it and `INDEX_LINE`. I changed "a heading such as `## The files`" to "text such as `## The files`", because the offending case was a list item that began with that text, not a heading. I ran `tests/guards/test_project_guide_files.py` (3 passed) and `make documents` (documents ok). I did not run `make check`, because I changed only a document. I touched no code or test. Cross-read: the rest of `docs/project-guide/README.md` is current. I saw no stale text outside this story. No `docs/decisions.md` entry was written, so there is no Why or Rejected line to flag.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok
10. factory: started docs-review as vm.
11. reviewer: Round 1. I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the work item, `INDEX_LINE` in `tests/support/guide_files_support.py` (`^- `([^`]+)`[^.]*\w[^.]*\.`) and `docs/project-guide/style.md`.

    Facts: true of the branch. A list item is read as a page entry only when it starts with `` - ` `` and a name in backticks, followed by text that holds a word and ends in a full stop. The four exception items below the paragraph start with "The heading" or with an italic title, so the new rule matches them. Both of round 0's findings are fixed: the 55-word sentence is split, and italics are now allowed. Criterion 1 and the docs criterion are met. Journal entry 9 records `check: green`, `secrets: green` and `documents ok` for criteria 2 to 4.

    1. `docs/project-guide/README.md:15`, the sentence "Every other list item in this section starts with a word, plain or in italics, never with a name in backticks, so that text such as `## The files` is never read as a page." It has about 35 words and three ideas: what an item starts with, what it never starts with, and why. Style rule 2 says one idea per sentence and to split a sentence of more than about 25 words. The "so that" clause also reads backwards: a list item that starts with `## The files` in backticks is exactly the one that is read as a page. Fix: split it into two sentences, for example "Every other list item in this section starts with a word, plain or in italics. A list item that starts with a name in backticks, such as `## The files`, is read as a page and fails the guard when no such page exists."

    Rejected as findings:
    - The first new sentence ("It reads a list item … ends in a full stop.") has about 30 words but only one idea. It stood unchanged in round 0, where it was not flagged.
