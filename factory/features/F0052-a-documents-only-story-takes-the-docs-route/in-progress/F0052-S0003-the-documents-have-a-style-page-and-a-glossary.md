---
stage: docs-only
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 574
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T23:01:53.344731Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T23:01:53.351464Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T23:02:10.005208Z'
  stage: intake
  run: 4faa5f9a78d545808b9ecdeb60ad8887
---

# The documents have a style page and a glossary

## Description

The documenter and the reviewer need one written standard for how the documents read. The human chose it on 2026-11-05 (`planning/doc-style-drafts.md`, with samples in `planning/doc-style-samples.md`): seven rules for every document, numbered steps for the operator guide, "idea first, then the API" for the project guide, and "what it is for, then try it" for the README. This story writes that standard into the repository as `docs/project-guide/style.md`, and the glossary that its third rule needs as `docs/project-guide/glossary.md`: each word the factory gives its own meaning, explained once in plain words. The project guide's index names both. It is the first story on the docs route, and it rewrites no other document.

## Interface

- `docs/project-guide/style.md` (new): the seven rules for all documents; a section per document (operator guide, project guide, README) with its reader, its rules and one example in the chosen style; as in `planning/doc-style-drafts.md`, in the page's own words. One more rule for all documents (the human, 2026-11-05): a file of the repository is linked by a relative link, such as `[process.py](../../src/factory/shared/adapters/process.py)`, never by a GitHub URL and never to a line (`#L42`); a code block holds no links, so the file it shows is linked once above it.
- `docs/project-guide/glossary.md` (new): one entry per factory word, at least: work item, feature, story, acceptance, stage, role, journal, backlog, approval, pipeline definition, write paths, project command, dataset, base, take, stage environment, stall, stop, crash, lease, claim, round, round cap, attempts cap, cost record, instance, tick. Each entry is one to three plain sentences, sorted alphabetically.
- `docs/project-guide/README.md`, *The files*: one line each for `style.md` and `glossary.md`.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/style.md` holds the seven common rules, the rule on relative links to files and the three document sections, each with its reader, its rules and an example.
2. `docs/project-guide/glossary.md` holds an entry for every word the Interface lists, alphabetically, each of at most three sentences.
3. `docs/project-guide/README.md` names both files in *The files*.
4. The two new pages follow their own rules: no feature or story ID, no version history, no sentence of more than about 25 words (the reviewer judges).
5. `make documents` prints `documents ok`.
6. `make check` stays green.
7. docs: as criteria 1 to 3. `README.md` and the operator guide: none; their rewrite is the next feature. `docs/decisions.md`: an entry for the choice of style, naming the human's choice of 2026-11-05.

## Smoke test

```bash
test -f docs/project-guide/style.md && test -f docs/project-guide/glossary.md && echo both
```
Expect: `both`

```bash
grep -c "style.md\|glossary.md" docs/project-guide/README.md | awk '{print ($1 >= 2) ? "named" : "missing"}'
```
Expect: `named`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/project-guide/style.md` and `glossary.md` new, the `README.md` index lines); no code, so no signatures are needed. The glossary lists the required words, sorted alphabetically. The source drafts exist in `planning/`.
   - Criteria: each is checkable by reading the files or running a command. 1 covers the seven rules, the relative-link rule and the three sections with reader, rules and example. 2 covers the entries, alphabetical order and the three-sentence limit. 3 covers the index. 4 covers the pages' own rules (the reviewer judges length). 5 and 6 are commands. 7 is the docs criterion. The relative-link rule has its criterion in 1.
   - Smoke test: both commands are runnable (`test -f`, `grep -c` piped to awk), and each Expect line (`both`, `named`) is exact. No pytest is involved.
   - Architecture: every changed path is a document under `docs/`, which the documenter may write. Nothing outside the doc areas is touched, and `planning/` is only read.
   - Scope: within the feature's S0003 scope. The rewrite of the guides and the README stays out, as the feature requires.
   Route: docs-only, because every path the Interface changes is one the documenter may write.
