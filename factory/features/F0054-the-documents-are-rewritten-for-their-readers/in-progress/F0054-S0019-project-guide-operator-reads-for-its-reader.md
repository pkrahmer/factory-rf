---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 627
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T07:17:13.835688Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T07:17:13.843323Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T07:17:29.028461Z'
  stage: intake
  run: 41130474e6c645c3ae6261b17c0586cf
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T07:17:33.845270Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T07:21:23.325602Z'
  stage: docs-only
  run: 48190f388fe44fcdb507b75264b0ba5e
---

# The project guide's page on the operator's scripts reads for the developer

## Description

`docs/project-guide/operator.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/operator.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/operator.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/operator.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/operator.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/operator.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/operator.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths (`docs/project-guide/operator.md`, `docs/checked-documents.txt`), and every path is one the documenter may write (`docs/*`); no code, test or agent file changes, so the docs route fits.
   Criteria: each is checkable. 1 and 2 are judged by the reviewer against `style.md` and the old file, as the feature's decision 2 provides. 3 is `make documents` printing `documents ok` plus the list entry. 4 is the link rule, and `make documents` finds broken links. 5 is the links to changed headings. 6 is `make check`. Every Interface rule has a criterion; the rules are documents-only, with no failing-side limits.
   Smoke test: `grep -cx` on the checked list is runnable and `Expect: 1` can be checked against the output. It runs no pytest.
   Docs criterion: names what the reader must know (style, completeness against the code, checked status, links) and dictates no sentences.
   Architecture: the page is the project guide's page for the operator's scripts, a path the documenter may write; nothing in `src` changes.
   Scope: one file of the 22 in feature F0054, S0019, and nothing in the feature's Out of scope (no `decisions.md`, no behaviour change).
4. factory: started docs-only as vm.
5. documenter: Rewrote the project guide's page on the operator's scripts for its reader, in the form of docs/project-guide/style.md. `make documents` ends `documents ok (16.8 s)` and prints no finding for the page. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/project-guide/operator.md`: each section now opens with two or three plain sentences, then a code block with the names and signatures, then one rule per bullet. It has no feature or story id. The factory's own words are not yet linked to the glossary: the page has no link to glossary.md, and I have not checked that it needs one. The files and tests it names are linked by relative links, once, at their first mention. The headings are unchanged, so the section list in docs/project-guide/README.md and any link to a heading still hold. A new section, *Reference*, holds the status codes of the site scripts and the table of test modules by script.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/operator.md`.

   Checks against the code (operator/lib/site.sh, operator/lib/hosting.sh, operator/job/job.sh, operator/bin/sanitise, operator/skill/kumpel/scripts/comment.sh and reset-to-tag.sh):
   - Every name, command, setting and rule of the old file is kept, in the body or in the *Reference*.
   - Two claims were not changed. I did not open `sanitise` for its rules-file lookup or check `drop_noise` or `stop_line`.
   - Added from the code: `site_require` gives a bare name the `SITE_` prefix. `site_job_keys` is a variable, not a function; the old text listed it among functions, so I corrected that.
   - Dropped on purpose: the pointer to "decision 22 of F0048" and "the story that made it" for operator/README.md. It is history (style rule 1). The page now says only that the table of files is the documenter's, and does not copy it.
   - Not run: the page has no `console` blocks. Its code blocks are indented signature blocks, not commands to run, so no example is marked for the VM, GitHub or a model.

   Cross-read and found current: docs/project-guide/README.md (its line on operator.md and the section names still match), docs/operator-guide/site.md (the page points to its *Setting up an operator's machine*), and operator/README.md.

   Stale text I saw and did not touch, because it is unrelated to this story: `make documents` reports under "not checked yet" that docs/project-guide/README.md names many `support/*.py` files that do not exist (lines about 134 to 141) and `project/factory/pipeline.yml` and `story-form.md` (line 283). Those are for that file's own story.

   No findings for the coder.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (16.3 s)
