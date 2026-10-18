# The factory timeline: plan (2026-10-19)

Renamed from "the status map" by the human on 2026-10-19: the page is a timeline (stages across, time down), not a map. Older notes say "status map".

The human's idea of 2026-10-17 ("The status map" in `planning/overnight/restructure-after-f0011.md`, the mockup in `planning/overnight/status-map-mockup/`), planned for v1.1's records. The map was deferred until after the baseline run (step 10); this plan and a proof of concept come first, so that F0021's records contract is checked against a real reader while it is built.

## The idea

A running factory leaves its whole state on GitHub: the work items with their journals, a cost line per agent run, the pipeline definition, the pull requests. The timeline draws it as one picture. The stages are columns, taken from `factory/pipeline.yml`. Time runs down the page. Each work item is a path through the columns, with its runs, its waits for the human, its stalls and its send-backs. The map shows where time and money go and what waits for the human, without anyone reading a log.

## Where it lives

A separate repository, **`pkrahmer/factory-timeline`**: one static HTML page and the tests of its reading code.

- It reads any factory's repository, not only `factory-rf`, so it does not belong to one factory's tree.
- It depends on the factory only through the records contract (F0021-S0006). A release of the map names the contract versions it reads (`x-records-contract` major 1).
- factory-rf's own build rules (Python, `make check`, the layer contracts) do not fit a browser page; the map gets its own small checks (a JavaScript linter and unit tests of the reading functions with Node's built-in test runner, no build step).
- Other names weighed: `factory-map` (the first name; the page has a time axis, not two spatial ones), `factory-trace` (developer jargon), `factory-flow` (generic), `factory-board` (collides with `factory-watch`'s board), `factory-viewer` (says less), `factory-dashboard` (suggests metrics tiles).

## What it reads (data only from front matter and JSON sidecars)

| Source | What the map takes from it |
|---|---|
| `factory/pipeline.yml` | the stages in order (the columns), each stage's role, `next`, `round_cap`, `approval`; the roles' write paths and time limits for the stage panel |
| `factory/features/<F>/feature.md` | the feature's title (its first heading) and its text for the feature panel |
| a work item's front matter | `stage`, `blocked`, `round`, `attempts`, `crashes`, `pull_request`, and the `journal:` records (`number`, `speaker`, `kind`, `at`, `stage`, `run`; after F0021 also `blocked` and `reason`) |
| `<work item>.costs.jsonl` | one line per run, joined to the journal by `run`: `started_at`, `duration_seconds`, `model_seconds`, `cost_usd`, `turns`, `end_reason`, `instance`; after F0021-S0004 `denials` |
| `factory/stops.jsonl` (after F0021-S0003) | the machine stops, `raised` and `cleared` with their times, drawn as bands across the whole map |
| `claude/agents/<role>.md` | the agent's text, for the stage panel |

The Markdown body is only displayed: the story's chapters folded, the journal's entry *n* shown beside the record with `number: n`. No state, time, cost or outcome is ever taken from prose. The one split of text the map does is the body at its `## ` headings, for folding, and the journal list at its numbers, for display.

**Derived, from the records alone:**

- *A stage visit*: from a `started` record to the next record of that stage that ends the run (`result`, `question`, `stall`, `crash`, `expiry`); its run's cost line gives the minutes and the dollars.
- *A wait for the human*: from a `question` record to the next `comment` record by `human`. With F0021-S0001 the question record names its cause (`blocked`), so the map colours the wait by cause (a question, the round cap, the attempts cap, the crash cap).
- *The approval wait*: from the record that enters `approval` to `done`.
- *A send-back*: a `started` record whose stage comes before the stage of the previous visit in the pipeline's order (`send_back` and `move_back` records when the code writes them).
- *The factory's own wait*: the gap between a record and the next `started` (ticks, leases).

## How it reads

- **The GitHub REST API from the browser**, with a fine-grained read-only token for the one repository (Contents: read; Pull requests: read). The token is entered for each session and kept in memory only; it is never stored, put in a URL or sent anywhere but `api.github.com`.
- The file list from `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1`. Each file is re-read only when its blob `sha` changed. The tree itself is re-read with `If-None-Match` (a `304` costs no rate limit), every 30 seconds while the page is visible.
- Pull requests (later): their comments for the question and answer texts, linked from the waits.
- **Where the page runs:** opened from disk or from any static server. **Not as a claude.ai artifact**: an artifact's security policy blocks requests to every host but a few script CDNs. The review copy published as an artifact therefore carries a *snapshot*: the same raw files, embedded at build time by a small script, read by the same code path as the live mode. The snapshot is private (the artifact is) and holds no token.
- No server, no GitHub Pages (a private repository's Pages site is public outside Enterprise Cloud), no file published by the factory.

## The layout (decided with the human on 2026-10-17)

- Header: the repository, the feature picker, the time range, the totals (work items, runs, agent cost, the hours waited for the human).
- Left: the work items at their start times, with a status badge (running, waiting for the human, stalled, done). One scroll area with the map.
- The map: the stage columns; each visit a bar in its column from its start to its end (height is time); the waits hatched; the stalls outlined; the questions as dots; a curve from each visit to the next; a step to the left is a send-back.
- The right panel shows the selection. *A work item*: its state, its pull request, its cost and send-backs, its story chapters folded, and its journal grouped by stage visit, each with time, minutes, cost and outcome. *A stage*: its configuration from the pipeline, its runs, minutes and cost, and the agent's text. *The feature*: its counts and its text. *Nothing*: the factory's totals and, after F0021-S0003, its stops.
- Later: the instance's log and health through a read-only telemetry stream, as a hint to re-read only, never a source of state.

## The proof of concept (this step)

One HTML file, `planning/factory-timeline-poc/factory-timeline.html`, built from the mockup's design with v1.1's records:

1. It reads raw files (the pipeline, `feature.md`, the work items, the cost sidecars, the agent files) through one loader with two sources: the live GitHub API (a repository and a token, entered on the page) and an embedded snapshot.
2. It parses the front matter with `js-yaml` (from cdnjs, pinned) and the sidecars line by line with `JSON.parse`.
3. It derives the visits, waits and send-backs as above and draws the map and the panels.
4. A snapshot of factory-rf's `main` (F0018, F0019 and F0021 as far as built) is embedded by `planning/factory-timeline-poc/snapshot.py.txt` (kept as text, so `make lint` does not read it), and the result is published as a private artifact for the human's review.

What the PoC is to show: that the records alone give the map (no prose parsed), which fields the map misses (input for F0021-S0006's contract), and whether the layout works for a real feature of 12 stories, 3 acceptances and a day's run.

## After the PoC

1. The human's review of the PoC.
2. The fields the map missed go into F0021's contract story, before it starts, or into a later story.
3. `factory-timeline` is created by the human. Its first version is the PoC split into a page and a module of pure reading functions with tests, reading the contract's JSON Schemas from factory-rf to check its fixtures.
4. Built as a factory feature itself (the map is a JavaScript project: a template for it is part of the template work after step 10), or by hand, the human's choice.

## What the PoC showed (2026-10-19)

Published for review: https://claude.ai/artifact/VzazQBxJg41qR9FeGLZWSd (snapshot of `main` at `da5c3bf3` and the branch of F0021-S0001). Source: `planning/factory-timeline-poc/factory-timeline.src.html` and `snapshot.py.txt`; the built `factory-timeline.html` is not committed (its run ids are 32-character hex values, which `make secrets` would flag).

1. **The records alone give the map.** Visits, waits, send-backs, stalls, costs and the human's hours come from the front matter and the sidecars; the Markdown is only displayed. F0019: 15 work items, $39.98, 12 questions, 46 minutes waited for the human; S0004 alone 25 runs, 7 send-backs (counting the coder's send-backs to the tester), 6 waits.
2. **A running work item's records are on its branch.** On `main` an in-progress work item has no journal until the merge; the map reads `work-item/<id>` for each in-progress item (one ref request with `If-None-Match` per poll). The records contract should say so.
3. **The factory's own questions carry no cause yet.** A question by `factory` (a cap) shows as "a cap" until F0021-S0001 adds `blocked` to the record. Stalls at a stage start (a failed merge of `main`) come before any `started` record, so they mark the map without a visit; F0021-S0001's `reason` will name them.
4. **The approval wait** is taken from the last `result` to the `done` record; an explicit record when the work item enters approval would make it exact (a field for the contract story to weigh, not needed now).
5. **A claude.ai artifact cannot read GitHub** (its security policy), so the review copy carries a snapshot; the live mode works from disk or a static server.
