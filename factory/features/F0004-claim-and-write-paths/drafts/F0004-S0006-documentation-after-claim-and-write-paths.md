# Documentation after claim and write paths

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

This story repairs the two status sentences that F0004's stories left stale. Each documenter wrote their own story's sections correctly: the claim service, the write paths, the guard command, the undo, and the operator guide's claims and `factory-guard` sections. Each one judged the opening sentences current for their story. Read as a whole, two places now leave out F0004 or contradict the rest:

- **`README.md`.** "The built parts so far are …" names nothing of F0004. "The one command so far checks a story before it starts" contradicts the operator guide's "The commands to run so far are `factory-check-story` (you run it) and `factory-guard` (the agent runtime runs it)". The human decided on 2026-10-14 (F0003-S0010) that the README *summarises* the built parts instead of listing them, so the list stops going stale with each feature. The README still lists them. Replace the enumeration with a short summary that points to `docs/project-guide.md` for the parts. Name both commands, saying that the operator runs `factory-check-story` and the agent runtime runs `factory-guard`.
- **`docs/operator-guide.md`, opening paragraph.** "Parts are built: …" leaves out the claim with its lease and the write paths with the guard and the undo. Add them, or summarise as the README does.

This story is documentation only: no code and no test changes. The tester writes no tests, the coder has nothing to build, and the work is the documenter's, from the docs criterion. If the human would rather make these edits by hand, this draft can be dropped.

## Interface

None: no code changes.

## Acceptance criteria

1. `make check` stays green.
2. docs:
   - `README.md` summarises the built parts instead of listing them, and points to `docs/project-guide.md` for each part.
   - The README names both commands, `factory-check-story` (the operator runs it) and `factory-guard` (the agent runtime runs it). It no longer says there is one command.
   - The opening paragraph of `docs/operator-guide.md` names the claim with its lease and the write paths with the guard and the undo among the built parts, or summarises them the way the README does.

## Demo

```bash
grep -c "factory-guard" README.md
```
Expect: one line, a number of at least `1`.

```bash
grep -c "one command so far" README.md
```
Expect: one line, `0` (grep exits 1 for no match; the printed count is what counts).

```bash
sed -n '3p' docs/operator-guide.md | grep -ci "claim"
```
Expect: one line, `1`: the operator guide's opening paragraph mentions the claim.

## Log (append only)

1. 2026-10-14 human: created.
