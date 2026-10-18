---
stage: tests
pr: 204
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The login and the git environment in the documents

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0014's feature acceptance read `README.md` and `docs/` as a newcomer and found five places that the feature's later stories left stale. Each story's documenter kept its own section true. Nobody owned the sections an earlier story had written, or the text a later story outdated:

- `docs/decisions.md`, "The agent's login is a token from a file", says that "the reason for the API key's absence is not recorded in the story". F0014's `FEATURE.md` ("Out of scope") does give it. The factory runs agents under the operator's own subscription login (R12), while an API key bills by use. Claude Code prefers an API key it finds over the subscription, so a stray key file would change who pays without a word. Nothing in v1.1 needs a key, and a team setup that wants one gets its own story.
- `docs/decisions.md`, "The factory's git runs no hooks", says "Now `git_environment` returns seven entries … `GIT_CONFIG_COUNT=3`". Since F0014-S0006 and F0014-S0010 it returns nine entries with `GIT_CONFIG_COUNT=4`. The F0010-S0003 entry already carries such a "since" note for `core.sharedRepository`.
- `docs/operator-guide.md`, "The agent runtime", begins with "it needs the `claude` program and a session you have already logged in to". Since F0014-S0004 the login is the token file. A session logged in by hand is only the fallback when the file is empty, as the same section's second paragraph says.
- `docs/operator-guide.md`, "The agent runs as a second user", gives the call as `sudo -n -u agent -- timeout --signal=KILL <limit>s env -i NAME=value ... claude ...`. Since F0014-S0003, a login shell stands between `env -i` and `claude` when `FACTORY_CLAUDE_LOGIN_FILE` is set: `/bin/sh -c <script> factory-login <file> claude ...`. The project guide has this right.
- `README.md`'s status paragraph ends with the Podman probe "up to the stop `repository_unavailable`; a run against a real repository with a token is not observed yet". It does not mention the first start of 2026-10-17, where the instances `shakedown` (Docker Desktop) and `shakedown-podman` (rootless Podman) became healthy on the todo demo's empty project. The preflight's probe agent run passed there against the real repository; a stage's agent run end to end, and a `time_limit` under `sudo`, are still to be observed at the shakedown run.

This story is documentation only. The documenter writes it from the docs criterion.

## Interface

None. No code, image file or test changes. The documenter changes `docs/decisions.md`, `docs/operator-guide.md` and `README.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: these changes, and no others:
   - In `docs/decisions.md`, "The agent's login is a token from a file", the "Left out" bullet gives the API key's reason, citing F0014 decision 15 and F0014's FEATURE.md "Out of scope". The factory runs agents under the operator's own subscription login (R12), while an API key bills by use. Claude Code prefers an API key it finds over the subscription, so a stray key file would change who pays without a word. Nothing in v1.1 needs one, and a team setup that wants one gets its own story. The bullet no longer says "not recorded".
   - "The factory's git runs no hooks" keeps its text as of its date and adds one parenthesis after "seven entries": "(nine with `GIT_CONFIG_COUNT=4` since F0014-S0010, see "No nested repository in the work tree")".
   - In `docs/operator-guide.md`, "The agent runtime", the first sentence says that the call needs the `claude` program and the agent's login: the token file, or a session logged in by hand when there is none. The clause that the factory holds no API key of its own stays.
   - "The agent runs as a second user" gives the call with the login shell: `... env -i NAME=value ... /bin/sh -c <script> factory-login <login file> claude ...`. One sentence says that the shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set, and that it `exec`s `claude`, so `timeout`'s kill still reaches `claude`. The sentence on what the agent sees then names the token too: the run's allow-list environment, the runtime's three switches and, from the login shell, `CLAUDE_CODE_OAUTH_TOKEN`.
   - `README.md`'s status paragraph replaces "a run against a real repository with a token is not observed yet". The new text says that the first start of 2026-10-17 brought two instances (Docker Desktop and rootless Podman) up healthy on an empty project, the preflight's probe agent run included. It also says that a stage's agent run end to end, and a `time_limit` under `sudo`, are first observed at the shakedown run.

## Demo

```bash
grep -c 'not recorded in the story' docs/decisions.md; grep -c 'a session you have already logged in to' docs/operator-guide.md; grep -c 'factory-login' docs/operator-guide.md
```
Expect: three lines: `0`, `0`, and a number of at least `1`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-18 human: created.
2. intake: accepted
   - Interface: "None" is right for a documentation-only story. It names the three documents the documenter changes (`docs/decisions.md`, `docs/operator-guide.md`, `README.md`), and each is inside the documenter's write path. It states no behaviour and no rule, so no criterion is owed for one and none has a failing side.
   - Criteria: criterion 1 (nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes) is checkable by one diff. Criterion 2 is the gate. The docs criterion lists five edits, each with the section, the wording to add or replace and the text that must go. The tester and coder entries are told what to say. There is no behaviour with a failing side to cover.
   - Demo: the first command is runnable. The grep counts are currently 1 in `docs/decisions.md` and 1 in `docs/operator-guide.md` for the two phrases, so the expected 0 and 0 are real changes. `factory-login` is not yet in the operator guide (the project guide has it), so "at least 1" is checkable. The second command's module `src/factory/entry/check_documents.py` exists, and its `documents ok` line is a checkable expectation.
   - Architecture: nothing is placed. No module, layer or interface is touched.
   - Scope: S0013 is listed in `FEATURE.md` as documentation only, with `README.md`, `docs/decisions.md` and `docs/operator-guide.md` as its files. Decisions 34 to 36 cover it, and decision 36 (5) is the human's yes to this story's edit 1. Nothing in it falls under "Out of scope".
   No questions.
