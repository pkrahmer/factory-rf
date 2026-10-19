# The project guide names no planning code or v1 feature id as a pointer

## Description

The project guide's files point into planning records that left the tree on 2026-10-19 (they are kept at the tag `planning-history-2026-10-19`): requirement numbers that `CLAUDE.md` does not name (R20, R21, R22, R24, R28), "kept thing" numbers, "questionnaire 1, Q29", and v1's feature ids F0004 to F0009 used as references ("F0008's tests", "F0005 uses `read`", the table *Which feature uses which operation*). An agent cannot follow them, and the house rule is that an id comes with its short name (finding M6 of the documentation review of 2026-10-20, its part in the guide files). This story replaces each such pointer with the plain name of what it refers to, or removes it where the sentence already says it. These stay, because a reader can resolve them: the requirement numbers that `CLAUDE.md` names (R5, R8), the agents' rule numbers R10, R14 and R15 (in every `## Rules` of `claude/agents/`), and example ids such as `F0001-S0001`, `F0004-x` and `FEATURE=F0012`. `processes-and-checks.md` is not touched. The decision log's codes are F0038-S0005's.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes `docs/project-guide/README.md`, `agents.md`, `costs.md`, `git-and-hosting.md`, `stages.md` and `watching.md`, each only in the passages below.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: each old text below becomes its new text (`""` means it is removed with the space before it), and nothing else in the guide changes:
   - `README.md`, *Kill points*: "F0008's tests arm" → "the recovery tests arm".
   - `agents.md`: "(R24: no partial figure; the first call's alone would be one)" → "(no partial figure: the first call's alone would be one)"; "F0005 uses `read` to compose every task" → "Starting a stage uses `read` to compose every task"; " (questionnaire 1, Q29)" → ""; "(F0009 reads them;" → "(the acceptance reads them;".
   - `costs.md`: "discarded with the stage (F0008)." → "discarded with the stage."; "a reported zero stays zero (R24)." → "a reported zero stays zero.".
   - `git-and-hosting.md`: in "Who uses them: preparing a stage merges ...", " (F0005)" and " (F0007)" → "". The sentence "Who uses them: a stall or a crash reverts or resets (F0004, F0005, F0008); ..." becomes "Who uses them: a stall or a crash reverts or resets; the tick resets the checkout to the remote; the undo's revert is this wrapper's, and the rules for what to revert are the undo's (`write-guard.md`); a merge or a discard moves the story file." The heading *Which feature uses which operation* becomes *Which part uses which operation*, and its table's *Used by* cells name the part, not a feature: "F0004: the undo compares" → "the undo: compares"; "F0005: preparing a stage merges" → "the stage's preparation: merges"; "F0006: the tick looks" → "the tick: looks"; "also F0004, F0005 and F0008: a stall or a crash" → "also the undo, the stage's preparation and the crash recovery: a stall or a crash"; "F0007: a merge or a discard" → "the merge and the discard"; "F0023: the key of a known project-command result (S0002) is the tree" → "the known results: the key of a known project-command result is the tree".
   - `stages.md`, *Status*: "reruns its stage at once, R20)" → "reruns its stage at once)"; "does not shorten a running claim (R21)." → "does not shorten a running claim.".
   - `watching.md`: "and R22 puts the human's act first" → "and the human's act comes first"; "the rerun after a crash (F0008) included" → "the rerun after a crash included"; " (kept thing 3)" → ""; " (R28, kept thing 12)" → "".
   - No guide file names *Which feature uses which operation* any more. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -E '\bR2[0-8]\b|kept thing|Q29|questionnaire 1|\bF000[4-9]([^-0-9]|$)|Which feature uses|F0023: ' docs/project-guide/*.md
```
Expect: nine lines, each ending in `:0`: `docs/project-guide/README.md:0`, `docs/project-guide/agents.md:0`, `docs/project-guide/costs.md:0`, `docs/project-guide/git-and-hosting.md:0`, `docs/project-guide/processes-and-checks.md:0`, `docs/project-guide/stages.md:0`, `docs/project-guide/watching.md:0`, `docs/project-guide/work-items.md:0`, `docs/project-guide/write-guard.md:0`

```bash
grep -c -F -e '### Which part uses which operation' -e 'the stage'"'"'s preparation: merges' docs/project-guide/git-and-hosting.md
grep -c -F 'the recovery tests arm' docs/project-guide/README.md
```
Expect: two lines, `2` and `1`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: seven lines, `0`, then `docs/project-guide/README.md`, `docs/project-guide/agents.md`, `docs/project-guide/costs.md`, `docs/project-guide/git-and-hosting.md`, `docs/project-guide/stages.md` and `docs/project-guide/watching.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
