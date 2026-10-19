# The documents repair what the feature's stories left stale

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0021's acceptance read the four documents from the top and found five passages that its stories left stale or wrong. Each story saw only its own sections. First, the project guide's journal example still shows the output it printed before `JournalRecord` gained `blocked` and `reason`. Second, the operator guide's table of the factory's own questions gives a stray "Comment reads" cell for two questions; the table is the one this feature gave a `blocked` column. Third, the project guide's `Boundaries` field list stops at `settings`. Fourth, the decision entry on the stop records gives another reason for leaving out the detail than the feature's decision 2, and leaves out one of decision 1's rejected places. Fifth, the operator guide's opening summary names neither the stop records nor the records contract. This story repairs exactly these five passages and changes no code, no test and no other passage.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide.md`, the journal example under *The journal's data*: the printed record reads `number=2 speaker='intake' kind='result' at=None stage=None run=None blocked=None reason=None`, which is what the example prints today.
   - `docs/project-guide.md`, *Boundaries*: the field list names `disk`, `disk_records` and `stop_records` after `settings`. Each is optional, and each gets one clause pointing to the paragraph that describes it.
   - `docs/operator-guide.md`, *The factory's own questions*, the table: the "Comment reads" cell of "The form has findings" reads `` `factory: ` and the findings question (`The work item's form has findings, so the stage cannot move forward: ...`) ``. The cell of "The round cap" reads `` `factory: ` and the round-cap question (`This work item has now been sent back <n> times, more than <cap>. ...`) ``. No other cell changes.
   - `docs/operator-guide.md`, the opening paragraph: one clause names the stop records published to `factory/stops.jsonl` on `main` and the records contract under `src/factory/contract/`.
   - `docs/decisions.md`, "The stops reach main as raised and cleared records":
     - The reason for leaving the detail out names `make secrets`. It reads every tracked file on `main`, a git error's text can hold a commit id or a URL, and a red `make secrets` on `main` would raise `main_branch_failing`.
     - The "Rejected" line adds a GitHub issue or comment, since the hosting-service interface does pull requests only (R10).
   - No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "run=None blocked=None reason=None" docs/project-guide.md
```

Expect: `1`

```bash
grep -E '^\| (The form has findings|The round cap) \|' docs/operator-guide.md | grep -c 'time_limit'
```

Expect: `0`

```bash
awk '/^## The stops reach main as raised and cleared records/{p=1;next} /^## /{p=0} p' docs/decisions.md | grep -c 'make secrets'
```

Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```

Expect: `documents ok`

## Journal
