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
  instance: self
  stage: intake
  started_at: '2026-10-21T07:24:30.695613Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T07:24:30.689413Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T07:24:30.695613Z'
  stage: intake
---

# The decision log marks two superseded entries, the removal of `factory/v1/`, and where its codes come from

## Description

`docs/decisions.md` is read before any change of the architecture (`CLAUDE.md`, *Architecture*), and an agent that searches it by topic finds the oldest entry first. Only the superseding entry says "this supersedes"; two superseded entries carry no mark and read as the current rule: *No `mutants` target, no mutmut*, superseded by *Mutation testing is limited to one feature's modules*, and *The four documents are checked by a command, outside `make check`; v1's words live in one section*, superseded for the docs stage by *The document check runs in the docs stage; the default identity has one home* and for the guide's layout by *The project guide is an index and one file per domain* (it still names `docs/project-guide.md`, one file). The handover entry, *factory-rf is built by v1.1 since the handover*, says v1's files "moved to `factory/v1/`" with no line for their removal on 2026-10-19. And the log cites planning codes (R-numbers, WE, L and Q codes, kept things, v1's features F0001 to F0017) without saying where they are defined. This story adds four lines (findings H7, M12 and the decision log's part of M6 of the documentation review of 2026-10-20). It renames no entry and changes no other text. The marks on the mutation entries after *Mutation testing is limited to one feature's modules* are F0032-S0001's. An index of the log and a status line on every entry (the review's structural proposal S2) are the human's to decide.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/decisions.md`, four additions, and no heading and no other line changes:
   - The header paragraph under `# Decisions` gains, at its end: "Older entries cite the planning records by code: the requirement numbers R1 to R34 (`CLAUDE.md` names R3, R5 to R13 and R17; an R14 or R15 beside an agent's rule is that rule's number in the agents' `## Rules`), the codes WE, L and Q, the kept things and v1's features F0001 to F0017. Those records are kept at the tag `planning-history-2026-10-19`."
   - Directly under the heading `` ## No `mutants` target, no mutmut ``, before its text, a paragraph of its own: "Superseded by *Mutation testing is limited to one feature's modules*."
   - Directly under the heading `` ## The four documents are checked by a command, outside `make check`; v1's words live in one section ``, before its `Date:` line, a paragraph of its own: "Superseded for the docs stage by *The document check runs in the docs stage; the default identity has one home*, and for the project guide's layout by *The project guide is an index and one file per domain*."
   - In *factory-rf is built by v1.1 since the handover*, directly after the bullet that begins "- Decision: v1's", one bullet: "- On 2026-10-19 `factory/v1/` was removed with the planning history; both are kept at the tag `planning-history-2026-10-19`."
   - Each title the new lines cite is a heading of the log. `make documents` ends with `documents ok`.

## Smoke test

```bash
f=docs/decisions.md
sed -n '/^## No `mutants` target, no mutmut$/,/^The acceptance reviewer/p' "$f" | grep -c -F "Superseded by *Mutation testing is limited to one feature's modules*."
sed -n '/^## The four documents are checked by a command/,/^Date:/p' "$f" | grep -c -F 'Superseded for the docs stage by *The document check runs in the docs stage; the default identity has one home*'
grep -c -F -e '- On 2026-10-19 `factory/v1/` was removed with the planning history' -e 'Those records are kept at the tag `planning-history-2026-10-19`.' "$f"
for t in "Mutation testing is limited to one feature's modules" 'The document check runs in the docs stage; the default identity has one home' 'The project guide is an index and one file per domain'; do grep -c -x -F "## $t" "$f"; done
```
Expect: six lines, `1`, `1`, `2`, `1`, `1` and `1` (both marks stand under their headings, the removal bullet and the header sentence are there, and each cited title is a heading)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/decisions.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
