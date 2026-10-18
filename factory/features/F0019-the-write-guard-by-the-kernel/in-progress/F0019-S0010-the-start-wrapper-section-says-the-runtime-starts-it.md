---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 231
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-18T20:17:27.845408Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T20:16:45.862815Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T20:16:45.868511Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T20:17:08.179405Z'
  stage: intake
  run: 844ab25542b1472cacced9ccd906d55a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T20:17:27.845408Z'
  stage: tests
---

# The project guide's start wrapper section says the runtime starts it

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's second acceptance read the documents as a whole and found one stale sentence that two documenters had already noticed (S0007's entry 11 and S0009's entry 11). Neither could change it, because their criteria said "no other passage changes". `docs/project-guide.md`, section *The start wrapper*, ends its first paragraph with "Nothing starts it yet: the runtime will." Since S0004, `ClaudeCodeRuntime` has started every agent run through `factory-confine` when it is built with `confine_executable`, and `build_boundaries` builds it that way by default. `docs/operator-guide.md` (*The agent runtime*) and `README.md` already say so. The same section's second paragraph describes `confinement_item`, the preflight item. S0007's criterion placed it in *The kernel's write guard*, and its reviewer and smoke tester passed it where it landed. This story replaces the stale sentence with one that is true and points to where the runtime builds the command, and it moves the `confinement_item` paragraph, unchanged, to the end of *The kernel's write guard*. It is documentation only: no code, test, template or agent file changes.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes `docs/project-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/project-guide.md`, section *The start wrapper*, first paragraph: the sentence "Nothing starts it yet: the runtime will." becomes a sentence saying that `ClaudeCodeRuntime` starts every agent run through it when built with `confine_executable`, which `build_boundaries` passes by default, and that the command line is in *The `claude -p` runtime*. The paragraph that begins "`confinement_item(abi, environment, find)`" moves, word for word, from *The start wrapper* to the end of *The kernel's write guard*. No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "Nothing starts it yet" docs/project-guide.md
```
Expect: `0`

```bash
sed -n '/^## The start wrapper/,/^### /p' docs/project-guide.md | grep -c "confine_executable"
```
Expect: `1`

```bash
sed -n '/^## The start wrapper/,$p' docs/project-guide.md | grep -c "^\`confinement_item(abi, environment, find)\`"; sed -n '/^## The kernel.s write guard/,/^## The start wrapper/p' docs/project-guide.md | grep -c "^\`confinement_item(abi, environment, find)\`"
```
Expect: `0`, then `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: "None" is correct for a documentation-only story. It names no module and states no behaviour or rule, so nothing needs a criterion. It limits the documenter to `docs/project-guide.md`.
   - Criteria: three, each checkable. (1) No change under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` is checkable from the diff. (2) `make check` is the closing criterion. (3) The docs criterion names the stale sentence, which I confirmed at line 1335 of `docs/project-guide.md`. It also names the replacement's content (`ClaudeCodeRuntime`, `confine_executable`, the `build_boundaries` default, the pointer to *The `claude -p` runtime*) and the paragraph to move, which I confirmed at line 1337 and which currently sits in *The start wrapper*. The destination, the end of *The kernel's write guard*, begins at line 1300. The criterion ends with `documents ok`. The story states no limits or error rules, so there is no failing side to cover.
   - Smoke test: all four commands are runnable. I checked the sed ranges against the current headings. After the edit, `confine_executable` appears only on the new sentence's line in the start wrapper range, because the paragraph is a single line. The `confinement_item` paragraph is one line too, so the count of 0 in the start wrapper range and 1 in the write guard range is checkable. Each `Expect:` line gives an exact value.
   - Architecture: it fits. It changes only the project guide, which the documenter owns. The facts it states match the guide's own *Confinement* paragraph (line 327), the operator guide and the README.
   - Scope: it matches the feature's scope ("`docs/project-guide.md` ... from each story's docs criterion"). It touches nothing in "Out of scope" and removes the stale-text note raised by S0007 and S0009.
4. factory: started tests as self.
