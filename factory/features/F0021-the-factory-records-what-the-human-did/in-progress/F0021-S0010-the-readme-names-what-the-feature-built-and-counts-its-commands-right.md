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
  started_at: '2026-10-19T02:10:38.363701Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T02:10:38.357659Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T02:10:38.363701Z'
  stage: intake
---

# The README names what the feature built and counts its commands right

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0021's second acceptance read `README.md` and `docs/` from the top, as a newcomer would. The four documents agree on what the feature built, but the README, which a newcomer reads first, says nothing about it, and contradicts itself on one count. First, the README's summary of what is built names the stops and the health status and the cost records with the bill. It does not name what F0021 added to them: the cause on a journal's question and stall records, the `Human:` line under the cost table, the stop records published to `factory/stops.jsonl` on `main`, and the records contract under `src/factory/contract/`. Second, the README's paragraph on the `python -m` commands names `factory.entry.check_documents` and (under *Where to look next*) `factory.entry.check_demos`, but not `factory.entry.contract`, the command a later story runs whenever it changes a model the contract covers. Third, *Getting started* says "Seven commands exist", matching the seven `[project.scripts]` in `pyproject.toml`, and the next paragraph says "Beside the six console commands". The six dates from before F0019 added `factory-confine`. Fourth, the operator guide's "The records contract" says what the command prints on success. It does not say what it does with two or more arguments: it prints its usage line to standard error, writes nothing and exits with 2. That is pinned since F0021-S0009, whose documenter offered the sentence. This story repairs exactly these four passages and changes no code, no test and no other passage.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes `README.md` and `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `README.md`, the summary of what is built (the paragraph under the title): one sentence names four things and points to `docs/operator-guide.md`, "The records contract". They are the cause recorded on a blocking question and on a stall, the `Human:` line under the cost table (questions answered and hours waited), the stop records published to `factory/stops.jsonl` on `main`, and the records contract of generated JSON Schemas under `src/factory/contract/`.
   - `README.md`, *Getting started*: "Beside the six console commands" reads "Beside the seven console commands". It then names `uv run python -m factory.entry.contract [<folder>]` with one clause: it regenerates the records contract's schemas, and a story that changes a model the contract covers runs it. `factory.entry.contract` appears in `README.md` exactly once.
   - `docs/operator-guide.md`, "The records contract": after "The command prints `contract: 5 schemas written`.", one sentence says that with two or more arguments it prints `usage: python -m factory.entry.contract [<folder>]` to standard error, writes nothing and exits with status 2.
   - No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "six console commands" README.md
```

Expect: `0`

```bash
grep -c "seven console commands" README.md; grep -c "factory.entry.contract" README.md; grep -c "factory/stops.jsonl" README.md
```

Expect: three lines, `1`, `1` and `1`.

```bash
grep -c "usage: python -m factory.entry.contract \[<folder>\]" docs/operator-guide.md
```

Expect: `1`

```bash
uv run -q python -m factory.entry.contract one two 2>/dev/null; echo "status $?"
```

Expect: `status 2`

```bash
uv run python -m factory.entry.check_documents
```

Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
