# The documents record the proof run of a project's skill and coder

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

The human's change 2 of F0022, the proof run, took place on 2026-10-19 (night log rows 19:29 to 19:34), on the demo's own instance `skills-demo` against `pkrahmer/factory-demo-skills`. It showed both halves. The project coder's entry began `project coder:`. The intake's, tester's and coder's entries ended with `skill: journal-marker`. The log held no `agent_definition_invalid`. As `agent`, `mkdir` in the home's `skills/` was refused. After `factory/agents/coder.md` was removed from `main`, the shipped coder came back. The documents do not record any of this. Three passages are now out of date:
- `docs/operator-guide.md`, *A project's own skills*, says whether Claude Code loads a nested `.claude/skills/` "is not known (the feature's proof run looks)". The night log's rows of the proof run record no such look, so the sentence points to a check that never happened. The human corrects this story if the run did look.
- In the same paragraph, F0022-S0004 put two sentences on the nested folder before "A run reads them from its checkout". "Them" now reads as the nested folder, but it means the root `.claude/skills/`.
- `docs/decisions.md`, *The agents load a project's skills, and the agent's home gets none*, gives no evidence that Claude Code offers and loads a skill under `--tools …,Skill`. The feature's decision 15 left that to the proof run.

The story changes documents only. The nested folder stays open, as it is now.

## Interface

None: no module under `src/factory/` changes, and neither does any test, image, template, demo or agent file. The documenter changes `docs/operator-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *A project's own skills*, second paragraph:
   - "(the feature's proof run looks)" goes. The sentence says instead that whether Claude Code loads such a nested folder was not checked, and that the review and your merge see it in the diff.
   - "A run reads them from its checkout, the work item's branch." becomes "A run reads the root `.claude/skills/` from its checkout, the work item's branch."

   `docs/decisions.md`, the entry *The agents load a project's skills, and the agent's home gets none*: a new bullet `- Proven:` goes before its `Open:` bullet. It says, in one or two sentences, what the proof run of 2026-10-19 showed: on the todo demo's own instance (`skills-demo`), a project coder's entry began `project coder:` and the intake's, tester's and coder's entries ended with the project skill's line `skill: journal-marker`; once the project's coder was removed from that repository's `main`, the factory's reader gave the shipped coder again; and in a container of the same image (`self`), the agent could not make a folder in the home's `skills/`. The `Open:` bullet keeps the nested `.claude/skills/` and says that the proof run did not check it.

   No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "the feature's proof run looks" docs/operator-guide.md
```
Expect: `0`

```bash
grep -c 'A run reads them from its checkout' docs/operator-guide.md
```
Expect: `0`

```bash
sed -n "/^## The agents load a project's skills/,/^## /p" docs/decisions.md | grep -c 'skill: journal-marker'
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
