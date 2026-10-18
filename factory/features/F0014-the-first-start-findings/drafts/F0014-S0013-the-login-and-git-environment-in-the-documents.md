# The login and the git environment in the documents

<!-- proposed by feature acceptance of 2026-10-18; refine before promoting -->

## Assignment (as of log entry 1)

F0014's feature acceptance read `README.md` and `docs/` as a newcomer and found five places that the feature's later stories left stale. Each story's documenter kept its own section true. Nobody owned the sections an earlier story had written, or the text a later story outdated:

- `docs/decisions.md`, "The agent's login is a token from a file", says that "the reason for the API key's absence is not recorded in the story". F0014's `FEATURE.md` ("Out of scope") does give it. The factory runs agents under the operator's own subscription login (R12), while an API key bills by use. Claude Code prefers an API key it finds over the subscription, so a stray key file would change who pays without a word. Nothing in v1.1 needs a key, and a team setup that wants one gets its own story.
- `docs/decisions.md`, "The factory's git runs no hooks", says "Now `git_environment` returns seven entries … `GIT_CONFIG_COUNT=3`". Since F0014-S0006 and F0014-S0010 it returns nine entries with `GIT_CONFIG_COUNT=4`. The F0010-S0003 entry already carries such a "since" note for `core.sharedRepository`.
- `docs/operator-guide.md`, "The agent runtime", begins with "it needs the `claude` program and a session you have already logged in to". Since F0014-S0004 the login is the token file. A session logged in by hand is only the fallback when the file is empty, as the same section's second paragraph says.
- `docs/operator-guide.md`, "The agent runs as a second user", gives the call as `sudo -n -u agent -- timeout --signal=KILL <limit>s env -i NAME=value ... claude ...`. Since F0014-S0003, a login shell stands between `env -i` and `claude` when `FACTORY_CLAUDE_LOGIN_FILE` is set: `/bin/sh -c <script> factory-login <file> claude ...`. The project guide has this right.
- `README.md`'s status paragraph ends with the Podman probe "up to the stop `repository_unavailable`; a run against a real repository with a token is not observed yet". It does not mention the first start of 2026-10-17, where the instances `shakedown` (Docker Desktop) and `shakedown-podman` (rootless Podman) became healthy on the todo demo's empty project. Nor does it mention that an agent run against a real repository is still to be observed at the shakedown run.

This story is documentation only. The documenter writes it from the docs criterion.

## Interface

None. No code, image file or test changes. The documenter changes `docs/decisions.md`, `docs/operator-guide.md` and `README.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: these five changes, and no others:
   - In `docs/decisions.md`, "The agent's login is a token from a file", the "Left out" bullet gives the API key's reason as above, citing F0014's FEATURE.md "Out of scope". It no longer says "not recorded".
   - "The factory's git runs no hooks" keeps its text as of its date and adds one parenthesis after "seven entries": "(nine since F0014-S0010, see "No nested repository in the work tree")".
   - In `docs/operator-guide.md`, "The agent runtime", the first sentence says that the call needs the `claude` program and the agent's login: the token file, or a session logged in by hand when there is none.
   - "The agent runs as a second user" gives the call with the login shell, `... env -i NAME=value ... /bin/sh -c <script> factory-login <login file> claude ...`. It says in one sentence that the shell is there only when `FACTORY_CLAUDE_LOGIN_FILE` is set, and that it `exec`s `claude`, so `timeout`'s kill still reaches `claude`.
   - `README.md`'s status paragraph replaces "a run against a real repository with a token is not observed yet". The new text says that the first start of 2026-10-17 brought two instances (Docker Desktop and rootless Podman) up healthy on an empty project, and that a real agent run is observed at the shakedown run.

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
