# What was left for v2 is named open and not planned

## Description

The documents say of five known gaps that they are "left for v2". On 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009: v1.1 evolves), and the decision log does not record that. Four of the gaps are closed, each by a story merged before this one: the project commands run as the agent user (F0040-S0002, which also replaced the operator guide's **Left for v2.** paragraph and marked the entry *The project commands run as the factory's user and are left for v2* replaced), the agent's home starts fresh before every run (F0040-S0004, which marked the decision log's "Left for v2." on the agent's writable home closed), the git-ignored paths are removed after every agent run (F0027-S0003, which rewrote the undo's *Limits* in `docs/project-guide/write-guard.md` and took out its "(left for v2)"), and the hook and its reading of a payload are gone (F0041). One gap is open and nothing plans it: the checkout's seal does not cover the clone's working folder (the checkout's parent) or the process environment `GitCli` passes on first, which the entry *The factory alone writes the checkout's `.git`* calls "Left for v2:". The paragraph on the agent's writable home also still says "Open: the kill of a timed-out agent under `sudo` ... the human has not chosen", which *The agent's own `timeout` kills a run under `sudo` at its time limit* settled on 2026-10-17. This story records the retirement in one new decision entry, which points each closed gap to the entry that closed it and names the open one "open, not planned"; it takes the words "Left for v2" out of the two paragraphs that still carry them and out of the line of *Every agent run and every project command starts from a fresh agent home* that quotes one of them, and points the settled question to its entry (finding H6 of the documentation review of 2026-10-20; the human's answers of 2026-10-20). The entry *The project commands run as the factory's user and are left for v2* gets a plain title that says what it now is, *The project commands first ran as the factory's user; replaced*, and a line that points to *The project commands run as the agent user, with the git folder sealed* (the human, 2026-10-20). The night logs under `docs/runs/` are the human's and stay as they are. Whether the open gap becomes v1.1 backlog is the human's decision; this story plans nothing.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/decisions.md`, a new last entry `## v2 is retired; nothing is left for v2`, dated with the story, in the bullet form. Decision: on 2026-10-19 v2 was retired as a rewrite (factory-v2's decision 009): v1.1 evolves, and nothing is left for a v2. Of the gaps the log and the guides left for v2, four are closed: the project commands run as the factory's user (*The project commands run as the agent user, with the git folder sealed*), the agent's writable home (*Every agent run and every project command starts from a fresh agent home*), the git-ignored paths the undo did not see (*The factory removes the git-ignored paths after every agent run and at the restore*), and the guard's reading of a hook payload it cannot read, which went with the hook (*The Claude Code hook is removed; the kernel and the undo are the write guard*). One is open and not planned: the checkout's seal does not cover the clone's working folder (the checkout's parent) or the process environment `GitCli` passes on first (*The factory alone writes the checkout's `.git`*). Why: a gap named "left for v2" reads as planned work, and no v2 will come. Open: whether the open gap becomes v1.1 backlog is the human's decision. Rejected: keeping "left for v2" in the documents.
   - `docs/decisions.md`, *The factory alone writes the checkout's `.git`*, the paragraph that begins "Rejected: a sticky bit on the checkout's root": "Left for v2: the clone's working folder" becomes "Open, not planned (see *v2 is retired; nothing is left for v2*): the clone's working folder", and "is the operator guide's morning observation" becomes "is one of the operator guide's checks on a running instance".
   - `docs/decisions.md`, the paragraph that begins "The agent's home stays writable by the agent": "Left for v2 (closed on 2026-10-20 by *Every agent run and every project command starts from a fresh agent home*)." becomes "Closed by *Every agent run and every project command starts from a fresh agent home*.", and the text from "Open: the kill of a timed-out agent under `sudo`." to the end of the paragraph becomes "The kill of a timed-out agent under `sudo` was settled later: see *The agent's own `timeout` kills a run under `sudo` at its time limit*."
   - `docs/decisions.md`, *The project commands run as the factory's user and are left for v2*: the heading becomes `## The project commands first ran as the factory's user; replaced`, and directly under it a paragraph of its own says "Replaced by *The project commands run as the agent user, with the git folder sealed*.", in place of F0040-S0002's mark "Replaced on 2026-10-20 by *The project commands run as the agent user, with the git folder sealed* (F0040-S0002). ", which is removed from the start of the paragraph that begins with it (the paragraph then begins "Date: 2026-10-16"). The rest of its text stays. In *The project commands run as the agent user, with the git folder sealed*, "It replaces *The project commands run as the factory's user and are left for v2*." becomes "It replaces *The project commands first ran as the factory's user; replaced*."
   - `docs/decisions.md`, *Every agent run and every project command starts from a fresh agent home*: "It closes the sentence *The agent's home stays writable by the agent (L69) ... Left for v2* of the entry of 2026-10-16." becomes "It closes the sentence on the agent's writable home (L69) in *The agent is started through `sudo -n -u agent -- env -i`, and a run's files are `0640`*."
   - No `README.md`, no `docs/operator-guide.md` and no file under `docs/project-guide/` says "left for v2", in any case (already true before the story; it stays so). `docs/decisions.md` says "Left for v2" nowhere, and "left for v2" only in the new entry's title and text and where a line cites its title. No document cites the old title. Every title that the new and the changed lines cite is a heading of the log. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -i 'left for v2' README.md docs/operator-guide.md docs/project-guide/*.md || true
```
Expect: eleven lines, each ending in `:0`: `README.md:0`, `docs/operator-guide.md:0`, `docs/project-guide/README.md:0`, `docs/project-guide/agents.md:0`, `docs/project-guide/costs.md:0`, `docs/project-guide/git-and-hosting.md:0`, `docs/project-guide/processes-and-checks.md:0`, `docs/project-guide/stages.md:0`, `docs/project-guide/watching.md:0`, `docs/project-guide/work-items.md:0`, `docs/project-guide/write-guard.md:0` (true already before the story, since F0040-S0002 and F0027-S0003; the story must keep it so)

```bash
f=docs/decisions.md
grep -c -F -e 'Left for v2' -e 'the human has not chosen' -e "the operator guide's morning observation" "$f" || true
grep -c -F "The project commands run as the factory's user and are left for v2" README.md docs/operator-guide.md docs/decisions.md docs/project-guide/*.md | grep -v -c ':0$' || true
for t in 'v2 is retired; nothing is left for v2' "The project commands first ran as the factory's user; replaced" "The agent's own \`timeout\` kills a run under \`sudo\` at its time limit" 'The project commands run as the agent user, with the git folder sealed' 'Every agent run and every project command starts from a fresh agent home' 'The factory removes the git-ignored paths after every agent run and at the restore' 'The Claude Code hook is removed; the kernel and the undo are the write guard' "The factory alone writes the checkout's \`.git\`" "The agent is started through \`sudo -n -u agent -- env -i\`, and a run's files are \`0640\`"; do grep -c -x -F "## $t" "$f"; done
```
Expect: eleven lines, `0`, `0`, then nine lines `1` (the old words are gone, no document names the old title, and the new entry, the renamed entry and every title the changed lines cite are headings of the log)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/decisions.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal
