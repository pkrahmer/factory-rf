---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 394
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-21T07:40:24.795970Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T07:33:54.798989Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T07:33:54.806024Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-21T07:34:18.795988Z'
  stage: intake
  run: 08ce70a2d7824e8498829502272ede0b
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-21T07:34:40.896673Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-21T07:36:05.320018Z'
  stage: tests
  run: 6b2d6243f9d043b7a677c187c08734a7
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-21T07:36:26.016995Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-21T07:38:00.254092Z'
  stage: doing
  run: b409338cdbdf49a7b9c72a6950b59f46
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-21T07:38:21.227590Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-21T07:38:53.640303Z'
  stage: review
  run: 2fd7caa671cf437b97d4e3074e139d2b
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-21T07:39:14.428538Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-21T07:40:03.939302Z'
  stage: docs
  run: c50ca6abbb29416a8c5dc718c43e787f
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-21T07:40:24.795970Z'
  stage: smoke-test
---

# The operator guide opens with its contents and states the current rule without its history

## Description

`docs/operator-guide.md` is for the operator (`CLAUDE.md`, *Docs*), and it has about 1,500 lines and no contents list. Its first paragraph is the same build inventory as the README's (about 2,900 characters on one line, dated observations included) and ends with "The documenter stage extends this from each story's docs criterion", which is for agents. Across the guide, history stands where the operator needs the current rule: "Morning observations" with the planning ids WE3.1, WE3.3 and WE3.4, "treat it as the morning observation", "(R2)", "(decision 008 of factory-v2)", "(questionnaire 1, Q21)", "the five of before", "as before", "The token used to be a compose secret", and provenance notes such as "(seen at the tiny story of 2026-10-18 ...)", "(F0012-S0017)" and "(F0019-S0004 showed it)". The reasons behind these rules are in the decision log already. And the paragraph on the container's init (`init: true`, tini, catatonit, zombies after a killed run) stands under *The hosting-service token*, where an operator who sees `<defunct>` processes will not look. This story gives the guide an opening and a contents list, states each listed rule without its history, and gives the init a heading of its own (findings H3, M4 and M13 of the documentation review of 2026-10-20). The stop tables and the class names are F0038-S0007's and F0038-S0008's; the sections on mutation testing are F0032-S0001's.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes only `docs/operator-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, these changes and no other:
   - The paragraph under `# Operator guide` becomes exactly: "The guide for the person who runs the factory this repository implements: how to install and configure an instance, which stops it can reach and what to do about each. The machine's image is the usual way to run an instance (see "The machine's image")." It is followed by a list with one bullet per `##` section of the guide, in the guide's order, each bullet the section's exact title in double quotes and nothing else (`- "Install"`), as the guide cites sections. The inventory and the sentence on the documenter stage are gone.
   - *Install*: " (decision 008 of factory-v2)" is removed. *Configuration*: " (R2)" is removed.
   - "**Morning observations.**" becomes "**Checks on a running instance.**", and its table's cells lose the prefixes "WE3.1: ", "WE3.3: " and "WE3.4: ". "**Morning observation.**" (under *The hosting-service token*) becomes "**Checks on a running instance.**". No row of the table starts with a planning code.
   - "Without it the words are the five of before." becomes "Without it the shell is started as `/bin/sh -c <script> factory-login <token file> claude ...`." (checked against `src/factory/adapters/agent_launch.py`: without an API login file the words are the shell, `-c`, the script, `factory-login` and the token file).
   - "The same status before the limit is a death, as before." becomes "The same status before the limit is a death." The sentence "An instance without the setting runs exactly as before." is removed. "is refused as before." becomes "is refused.". "A commit that also changes another file clears the stop as before." becomes "A commit that also changes another file clears the stop." In **The project commands run as `agent`.**, "the commands run as the factory's user, as before." becomes "the commands run as the factory's user."
   - *Build it*: "The probe of 2026-10-17 built the image once under rootless Podman 5.8.3 in 42 s, without the pins (they were placeholders then). A build with the pins of `image/Dockerfile` is not observed yet; treat it as the morning observation." becomes "A build of the image with the pins of `image/Dockerfile` is not observed yet: check it once on a running instance."
   - *Claude Code*: "A maintenance feature after v1.1 updates the pin (questionnaire 1, Q21); until then it changes only when you edit the Dockerfile." becomes "The pin changes only when you edit the Dockerfile."
   - *The hosting-service token*: "The token used to be a compose secret with `uid`, `gid` and `mode`, but Compose ignores those three keys outside Swarm mode:" becomes "A compose secret cannot do it, because Compose ignores its `uid`, `gid` and `mode` outside Swarm mode:", and "A probe of 2026-10-17 read the token as the agent through that file." is removed.
   - The paragraph that begins "The service sets `init: true`" gets the heading `### The init` directly above it, inside *The container: compose, entrypoint and health check*; in it " (seen at the tiny story of 2026-10-18 under Docker Desktop)" is removed and "pile up as before" becomes "pile up".
   - *The health check and the restart policy*: "The probe of 2026-10-17 saw the health check run under Podman: it reported `starting`, then the text of the stop `repository_unavailable`, with exit 1. The morning observation that remains is `docker compose ps` over a container with a stop standing." becomes "Under Podman the health check reports `starting`, then the text of a stop in force, with exit 1. Not yet checked on a running instance: `docker compose ps` over a container with a stop in force."
   - *Container runtimes*: "(probe of 2026-10-17, Podman 5.8.3 on Windows)" becomes "(seen with Podman 5.8.3 on Windows)".
   - " (F0012-S0017)", " (seen by the coder of the tiny story, 2026-10-18)" and " (F0019-S0004 showed it)" are removed.
   - No heading of the guide is renamed or removed; `### The init` is the one heading added. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c -F -e 'orning observation' -e 'WE3.' -e 'decision 008' -e 'Q21' -e 'five of before' -e 'as before' -e 'used to be a compose secret' -e 'tiny story' -e 'F0012-S0017' -e 'F0019-S0004' -e 'probe of 2026-10-17' -e '(R2)' -e "documenter stage extends" docs/operator-guide.md || true
grep -c -x -F '### The init' docs/operator-guide.md
```
Expect: two lines, `0` and `1`

```bash
uv run -q python - <<'EOF'
import re
from pathlib import Path

text = Path("docs/operator-guide.md").read_text(encoding="utf-8")
opening = text.split("\n## ", 1)[0]
titles = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
listed = re.findall(r'^- "(.+)"$', opening, flags=re.MULTILINE)
print(listed == titles, len(opening.split("\n\n")[1]) <= 400)
EOF
```
Expect: `True True` (the contents list names every `##` section in order, and the opening paragraph has at most 400 characters)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: two lines, `0` and `docs/operator-guide.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is right for a documents-only story. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes, and criterion 1 pins that.
   - Criteria: criterion 3 is a list of exact old-to-new replacements, and each can be checked against the text. The contents-list bullet format and the 400-character limit on the opening paragraph are stated. I grepped the guide, and the quoted passages are there: "Morning observations" at line 227, "Morning observation." at 430, "The service sets `init: true`" at 437, and "The probe of 2026-10-17" at 352. The guide has 39 `##` sections for the contents list. The Interface states no rule with a failing side, because nothing is validated or refused, so that check has nothing to fail.
   - Smoke test: all four blocks are runnable. The first grep prints `0` because `|| true` covers grep's exit 1 on no match, and the second prints `1`. The Python block does not call pytest, so the `-q` rule does not apply. Each `Expect:` line can be checked against the output.
   - Architecture: the story changes only `docs/operator-guide.md`, which is the documenter's write path under `CLAUDE.md`, *Docs*.
   - Scope: the story stays within `feature.md`. It takes S0006's findings H3, M4 with L9, and M13. The stop tables, class names and mutation sections are left to S0007, S0008 and F0032, as the feature says.
4. factory: started tests as self.
5. tester: No tests written, as the story requires. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage, and I created no files.
   - criterion 1 (nothing under src/, tests/, image/, template/, demo/ or claude/ changes): no test function. A test file would itself break this criterion. The third smoke-test block checks it (`git diff --name-only origin/main -- src tests image template demo claude`).
   - criterion 2 (`make check` stays green): no test function. The factory's checks cover it.
   - criterion 3 (docs: the listed changes to `docs/operator-guide.md`): no test function. It belongs to the documenter, and the factory's `make documents` and the smoke-test blocks check it.
   Modules the test run could not import: none. I added no tests, so there is no red specification for the coder, and I did not run `make test`. `make lint` is green (`lint: green (0.2 s)`).
   Nothing in the criteria needed interpreting, so there are no open questions.

   `lint`: lint: green (0.7 s)
   `test`: test: green (64.9 s)
6. factory: started doing as self.
7. coder: No code written, as the story requires. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage, and I created no files. The working tree shows only the factory's `.costs.jsonl` sidecar.
   - What I built: nothing. The Interface is "None", and the tester added no tests, so there was nothing failing to make pass. Every change in criterion 3 is to `docs/operator-guide.md`, which the documenter owns.
   - Main choice: I left `docs/operator-guide.md` untouched and left it to the docs stage. I rejected making the criterion-3 edits here, because `CLAUDE.md`, *Docs*, says the coder does not write the four documents and criterion 1 pins this stage to no change.
   - Refactor: there is no diff, so there was nothing to refactor.
   - Description: no journal entry changed the meaning of the task, so `## Description` is unchanged.
   - Noticed but not touched: nothing.

   `check`: check: green (`make check` run in the foreground; test: green (68.3 s), coverage 99.14 %)

   `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
   `duplicates`: duplicates: 0 new, 38 known, 0 gone
8. factory: started review as self.
9. reviewer: no findings

   - Scope: `git diff main...HEAD -- . ':!factory'` is empty. The branch changes only the work item and its `.costs.jsonl` sidecar. Criterion 1 holds: nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed, and the tester and the coder each say so in entries 5 and 7.
   - Criterion 2: the factory's `make check` after the coder was green (entry 7: `check: green`, `duplicates: 0 new, 38 known, 0 gone`).
   - Criterion 3 (docs): I checked that the documenter can carry it out as written against the current `docs/operator-guide.md`.
     - Every quoted passage is in the guide: lines 3, 7, 13, 117, 227, 231–248 (`WE3.1`, `WE3.3`, `WE3.4`), 255, 305, 352, 367, 409, 430, 435, 437, 460, 515, 528, 668, 757, 1421 and 1503.
     - The smoke test's grep for `as before`, `probe of 2026-10-17`, `orning observation` and `tiny story` finds no occurrence outside the listed replacements.
     - The section the new opening cites, `## The machine's image`, exists (line 332).
     - `### The init` would sit inside `## The container: compose, entrypoint and health check` (line 389), between `### The hosting-service token` (405) and `### The health check and the restart policy` (450).
     - The replacement for "the five of before" matches `login_argv` in `src/factory/adapters/agent_launch.py:120-130`: without an API file it returns `/bin/sh`, `-c`, the script, `factory-login` and the token-file word.
   - Description, Interface and criteria agree. The journal states the main choice: the coder left the guide to the docs stage, and entry 7 gives the reason.

   Earlier tests: none. The diff changes no test file.
10. factory: started docs as self.
11. documenter: Changed one file, `docs/operator-guide.md`. I made every edit in criterion 3 and no others.
    - Opening: the paragraph under `# Operator guide` is now the exact text the criterion gives (252 characters). A contents list follows it, with one bullet for each of the 39 `##` sections in order, each a quoted exact title. The build inventory and the sentence on the documenter stage are gone.
    - History taken out, each as the criterion words it:
      - "(decision 008 of factory-v2)", "(R2)" and "Q21".
      - "Morning observations" and "Morning observation" are now "Checks on a running instance", and the table's `WE3.x:` prefixes are gone.
      - The "five of before" sentence now says the shell is started as `/bin/sh -c <script> factory-login <token file> claude ...`. The reviewer checked this against `login_argv` in `src/factory/adapters/agent_launch.py`.
      - All the "as before" phrases, the sentence "An instance without the setting runs exactly as before", and the probe and provenance notes (2026-10-17, F0012-S0017, F0019-S0004, "tiny story").
    - The compose secret sentence is reworded as the criterion words it.
    - The health check, build and container-runtime passages are reworded as the criterion words them.
    - `### The init` is added as the one new heading. It sits directly above the paragraph that begins "The service sets `init: true`", inside the container section.
    - Checks run:
      - The smoke-test grep prints `0` and the `### The init` count prints `1`.
      - The contents and opening check prints `True` for the list and 252 for the paragraph length (limit 400).
      - Only `docs/operator-guide.md` changed outside `factory/`.
      - `make documents` ends with `documents ok`.
    - Not run: `make check`, because only a document changed. The factory's checks decide.
    - Cross-read: the README and `docs/` were not otherwise read against the diff, because the story changes no code. The cited section "The machine's image" exists in the guide.
    - Stale text noticed and left alone, because it belongs to other stories:
      - Further dated observations remain in the guide, for example "(seen at the first start of 2026-10-17 under Docker Desktop and Podman)" in the checks table. The criterion does not list them.
      - The stop tables and class names are F0038-S0007's and F0038-S0008's. The mutation sections are F0032-S0001's.
    - Findings for the coder: none.

    `check`: check: green (not run again: passed on tree 61b5f6269707 at 2026-10-21T07:02:46Z)
    `secrets`: secrets: green (1.4 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
