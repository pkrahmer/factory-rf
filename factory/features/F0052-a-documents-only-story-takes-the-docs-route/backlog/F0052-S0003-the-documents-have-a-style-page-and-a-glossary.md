# The documents have a style page and a glossary

## Description

The documenter and the reviewer need one written standard for how the documents read. The human chose it on 2026-11-05 (`planning/doc-style-drafts.md`, with samples in `planning/doc-style-samples.md`): seven rules for every document, numbered steps for the operator guide, "idea first, then the API" for the project guide, and "what it is for, then try it" for the README. This story writes that standard into the repository as `docs/project-guide/style.md`, and the glossary that its third rule needs as `docs/project-guide/glossary.md`: each word the factory gives its own meaning, explained once in plain words. The project guide's index names both. It is the first story on the docs route, and it rewrites no other document.

## Interface

- `docs/project-guide/style.md` (new): the seven rules for all documents; a section per document (operator guide, project guide, README) with its reader, its rules and one example in the chosen style; as in `planning/doc-style-drafts.md`, in the page's own words.
- `docs/project-guide/glossary.md` (new): one entry per factory word, at least: work item, feature, story, acceptance, stage, role, journal, backlog, approval, pipeline definition, write paths, project command, dataset, base, take, stage environment, stall, stop, crash, lease, claim, round, round cap, attempts cap, cost record, instance, tick. Each entry is one to three plain sentences, sorted alphabetically.
- `docs/project-guide/README.md`, *The files*: one line each for `style.md` and `glossary.md`.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/style.md` holds the seven common rules and the three document sections, each with its reader, its rules and an example.
2. `docs/project-guide/glossary.md` holds an entry for every word the Interface lists, alphabetically, each of at most three sentences.
3. `docs/project-guide/README.md` names both files in *The files*.
4. The two new pages follow their own rules: no feature or story ID, no version history, no sentence of more than about 25 words (the reviewer judges).
5. `make documents` prints `documents ok`.
6. docs: as criteria 1 to 3. `README.md` and the operator guide: none; their rewrite is the next feature. `docs/decisions.md`: an entry for the choice of style, naming the human's choice of 2026-11-05.

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
