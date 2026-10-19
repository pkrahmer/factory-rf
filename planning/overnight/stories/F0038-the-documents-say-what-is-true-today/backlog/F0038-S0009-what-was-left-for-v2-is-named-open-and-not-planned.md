# What was left for v2 is named open and not planned

## Description

Four passages say that a known gap is "left for v2": the operator guide's **Left for v2.** over a security gap (the project commands run agent-written code as the factory's user, who can read the token file), `docs/project-guide/write-guard.md`'s "(left for v2)" on what the undo cannot see, and in `docs/decisions.md` the title *The project commands run as the factory's user and are left for v2* and "Left for v2." on the agent's writable home. On 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009: v1.1 evolves), and the decision log does not record that. The operator reads a known way to leak the token as work already planned, and nothing plans it now. The paragraph on the agent's writable home also still says "Open: the kill of a timed-out agent under `sudo` ... the human has not chosen", which *The agent's own `timeout` kills a run under `sudo` at its time limit* settled on 2026-10-17. This story names each gap open and not planned, records the retirement in one new decision entry, and points the settled question to its entry (finding H6 of the documentation review of 2026-10-20). Whether a gap becomes v1.1 backlog is the human's decision; this story plans none of them.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes `docs/operator-guide.md`, `docs/project-guide/write-guard.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/operator-guide.md`, *The hosting-service token*: "**Left for v2.**" becomes "**Open, not planned.**". The paragraph's last sentence ends with "see *The project commands run as the factory's user; open, not planned* and *v2 is retired; what was left for v2 is open* in `docs/decisions.md`." in place of "see `docs/decisions.md`.". The rest of the paragraph stays.
   - `docs/project-guide/write-guard.md`, *Limits*: "(left for v2)" becomes "(open, not planned)".
   - `docs/decisions.md`: the heading *The project commands run as the factory's user and are left for v2* becomes *The project commands run as the factory's user; open, not planned*. In its text, "is work for v2. Until then the operator guide says so" becomes "is open and not planned since v2 was retired (see *v2 is retired; what was left for v2 is open*). The operator guide says so".
   - `docs/decisions.md`, the paragraph that begins "The agent's home stays writable by the agent": "Left for v2." becomes "Open, not planned.", and the text from "Open: the kill of a timed-out agent under `sudo`." to the end of the paragraph becomes "The kill of a timed-out agent under `sudo` was settled later: see *The agent's own `timeout` kills a run under `sudo` at its time limit*."
   - `docs/decisions.md`, a new last entry `## v2 is retired; what was left for v2 is open`, dated with the story, in the bullet form: Decision: on 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009): v1.1 evolves, and nothing is left for a v2. What the log and the guides left for v2 is open and not planned: the project commands run as the factory's user, who can read the token file; the agent's home stays writable by the agent; the undo does not see ignored paths or anything outside the checkout. Why: a gap named "left for v2" reads as planned work. Open: whether any of the three becomes v1.1 backlog is the human's decision. Rejected: keeping "left for v2" in the documents.
   - No document under `docs/` and no `README.md` says "left for v2" outside the new entry and the citations of its title, and every title the changed passages cite is a heading of the log. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F -e '**Left for v2.**' -e '(left for v2)' -e 'are left for v2' -e 'Left for v2.' -e 'the human has not chosen' docs/operator-guide.md docs/project-guide/write-guard.md docs/decisions.md README.md || true
```
Expect: four lines, `docs/operator-guide.md:0`, `docs/project-guide/write-guard.md:0`, `docs/decisions.md:0`, `README.md:0`

```bash
f=docs/decisions.md
for t in "The project commands run as the factory's user; open, not planned" 'v2 is retired; what was left for v2 is open' "The agent's own \`timeout\` kills a run under \`sudo\` at its time limit"; do grep -c -x -F "## $t" "$f"; done
grep -c -F '**Open, not planned.**' docs/operator-guide.md
grep -c -F '(open, not planned)' docs/project-guide/write-guard.md
```
Expect: five lines, each `1`

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: four lines, `0`, then `docs/decisions.md`, `docs/operator-guide.md` and `docs/project-guide/write-guard.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
