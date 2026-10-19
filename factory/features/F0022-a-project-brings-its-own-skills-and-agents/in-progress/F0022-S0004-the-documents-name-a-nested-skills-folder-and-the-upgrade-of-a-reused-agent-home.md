---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 284
comments_read: []
handed_over: null
claim:
  instance: self
  stage: docs
  started_at: '2026-10-19T20:34:45.458740Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T20:29:37.310835Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T20:29:37.317717Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T20:29:59.286344Z'
  stage: intake
  run: 79a9706a59a0431ebe70eaa12858e59b
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T20:30:19.979524Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T20:32:06.401545Z'
  stage: tests
  run: c3cf987070584f3cb18a8bad46c56259
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T20:32:27.773536Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T20:33:42.946340Z'
  stage: doing
  run: 8b09ff6203404f7b9e4cfda0751d9958
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T20:34:04.093787Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T20:34:24.904423Z'
  stage: review
  run: 301d88d98c3d4d108688f838ddf2ff55
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T20:34:45.458740Z'
  stage: docs
---

# The documents name a nested skills folder and the upgrade of a reused agent home

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0022's acceptance read the documents as a whole and found four passages that leave out what the feature itself recorded. (1) `docs/operator-guide.md`, *A project's own skills*, says "`.claude/*` is a protected path that no stage writes". That holds only for the root folder. The feature's decision 12 leaves open that a stage may write a `.claude/skills/` in a subfolder inside its write paths (`src/.claude/skills/...`), and that later runs may load it if Claude Code finds nested skills. An operator reading the guide would think every skill is the human's. (2) The guide does not say what the human's change 1 of the feature says. After the first image with the new entrypoint, a `skills/` or `commands/` folder that an earlier agent run made in a reused `claude-home` volume, without group write, cannot be removed by `factory`. The entrypoint then stops under `set -e`, and the instance restarts with `rm: cannot remove ...` in its log. (3) `docs/decisions.md`, the entry *The agents load a project's skills, and the agent's home gets none*, says neither that it supersedes the word "skills" in the open point of the F0012-S0025 entry, nor what decision 12 left open. (4) `docs/project-guide/agents.md` ends *The seven agents* with "To change what an agent is told, edit its file under `claude/agents/`; there is no other copy". That passage is about the shipped agents, but since S0001 a project may carry its own copy. The story changes documents only.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes `docs/operator-guide.md`, `docs/decisions.md` and `docs/project-guide/agents.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *A project's own skills*, second paragraph: after the sentence on `.claude/*`, a sentence that the protection covers the repository's root `.claude/` only. A stage may write a `.claude/skills/` inside its own write paths (for example `src/.claude/skills/`). Whether Claude Code loads such a nested folder is not known (the feature's proof run looks), and the review and the human's merge see it in the diff. `docs/operator-guide.md`, *The agent runs as a second user*, the paragraph on the agent's home, after its sentence on a `claude-home` volume made by an earlier image: on such a volume a `skills/` or `commands/` folder an agent run made without group write cannot be removed by the entrypoint. The instance then restarts with `rm: cannot remove ...` in `docker logs`. The fix is to remove both folders as root through the volume (`docker run --rm -u root -v factory-<instance>_claude-home:/h alpine rm -rf /h/skills /h/commands`, for example `factory-self_claude-home`) and start the instance again. `docs/decisions.md`, the entry *The agents load a project's skills, and the agent's home gets none*: its `Open:` bullet adds the nested `.claude/skills/` of decision 12, with `src/.claude/skills/` as its example. A sentence says the entry supersedes "skills" in the open point of the entry dated 2026-10-17 (F0012-S0025). `docs/project-guide/agents.md`, *The seven agents*: "there is no other copy" becomes "there is no other copy of a shipped agent", followed by a sentence that a project's own agent is its file under `factory/agents/` on `origin/main` (see *A project's own agents*). No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
sed -n "/^### A project's own skills/,/^### /p" docs/operator-guide.md | grep -c 'src/.claude/skills'
```
Expect: `1`

```bash
grep -c 'rm: cannot remove' docs/operator-guide.md
```
Expect: `1`

```bash
sed -n "/^## The agents load a project's skills/,/^## /p" docs/decisions.md | grep -c 'src/.claude/skills'
```
Expect: `1`

```bash
grep -c 'there is no other copy of a shipped agent' docs/project-guide/agents.md
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: states "None" and names the three documents the documenter changes (`docs/operator-guide.md`, `docs/decisions.md`, `docs/project-guide/agents.md`). No module or signature exists to check, and no `# comment` states a behaviour.
   Criteria: criterion 1 (nothing outside the docs changes) can be checked by one diff check and has a failing side, since any change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` breaks it. Criterion 2 is `make check` and criterion 3 is the docs criterion. Each document change in criterion 3 names its section and its exact wording. `check_documents` must print `documents ok`. I found no Interface rule that lacks a criterion.
   Smoke test: all five commands are runnable. I confirmed that the sections they read exist: `### A project's own skills` (operator-guide.md:998), `## The agents load a project's skills...` (decisions.md:757) and the sentence "there is no other copy" (project-guide/agents.md:254). Each `Expect:` is a count or a fixed string. The first four counts are 0 today, so they fail now and pass after the documenter's edit. The documenter must put `src/.claude/skills` on exactly one line in each of those two sections, and `rm: cannot remove` on exactly one line in the guide.
   Architecture: documents only, so no layer is touched. The wording follows the glossary and the guide's section names. The `*The agent runs as a second user*` section exists (operator-guide.md:125).
   Scope: the story is within F0022. It carries in decision 12's open point and the human's change 1, and it adds no behaviour. It stays inside the documenter's write paths (`docs/*`). It does not touch `feature.md`, `factory/`, `planning/` or `docs/runs/`.
4. factory: started tests as self.
5. tester: No tests written. This story changes only documents: its Interface says "None", and criterion 1 says no test changes. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage, and the tester's working tree changes no file.
   criterion 1 (nothing outside the docs changes): no test function. It is a check on the diff, and the coder and reviewer confirm it. This entry is the tester's confirmation.
   criterion 2 (`make check` stays green): no test function. This is the stage's own check. `make test` passed (99.12 % coverage, `test: green`) and `make lint` passed.
   criterion 3 (docs): no test function. The documenter stage covers it, through `make documents` and the smoke test.
   Files created: none. Modules the test run could not import: none. No red tests on this branch: there is no code for the coder to write, so the coder should change nothing and confirm criterion 1.

   `lint`: lint: green (0.0 s)
   `test`: test: green (46.1 s)
6. factory: started doing as self.
7. coder: No code written. This story changes documents only: its Interface says "None", and the tester left no red tests. The documenter makes the three document changes in criterion 3.
   criterion 1: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage. `git diff --stat main` over those paths is empty, and my working tree changes no file. This entry is the coder's confirmation.
   criterion 2: `make check` ran in the foreground and ended `check: green` (coverage 99.12 %, `test: green (47.0 s)`).
   Main choice: I changed nothing, as the story asks. I rejected writing the document passages myself: `docs/` is the documenter's to change, not the coder's (CLAUDE.md, *Docs*).
   Refactor: there is no diff, so nothing to refactor.
   The journal did not change the meaning of the task, so `## Description` is unchanged.
   Noticed, not touched: nothing.

   `check`: check: green (not run again: passed on tree 4dd869fc6664 at 2026-10-19T20:22:35Z)
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar under `factory/`. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed.
   1. Acceptance criteria: criterion 1 holds, because the diff outside `factory/` is empty, and the tester (entry 5) and the coder (entry 7) each say so. Criterion 2: the coder's entry records `check: green`. Criterion 3 is the documenter's. The Interface states no rule or limit, so no failing side is left untested. There is no mutation report line to read.
   2. to 4. Architecture, security and quality: there is no code, so none apply.
   5. Work item hygiene: entries 5 and 7 explain the main choice, which was to change nothing, and the rejected option, the coder writing `docs/`. The Description matches: documents only. I checked that the docs criterion still names passages that exist on this branch: `docs/project-guide/agents.md:254` holds "there is no other copy", and both guides have *A project's own agents* (`docs/project-guide/agents.md:179`, `docs/operator-guide.md:987`). The volume name `factory-<instance>_claude-home` matches the one in feature.md change 1 (`factory-self_claude-home`).
   6. Earlier tests: no test file changed, renamed or deleted (`git diff --name-status main...HEAD` lists only the work item's two files).

   The coder's `duplicates: 5 new` record cannot come from this branch, since it changes nothing under `src/factory`. It is outside this review's scope.
10. factory: started docs as self.
