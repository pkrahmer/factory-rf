---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 280
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-19T19:09:22.418535Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T19:08:38.014815Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T19:08:38.021500Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T19:09:01.860400Z'
  stage: intake
  run: 1954926014f04202a4728400b340dfdc
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T19:09:22.418535Z'
  stage: tests
---

# The operator guide names opencode wherever it names the runtime

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0020 added a section on running on opencode to `docs/operator-guide.md`. The guide's older passages still speak of the agent runtime as if Claude Code were the only one, and an operator who reads them for an opencode instance is sent the wrong way:

- *The agent runtime* opens with "The factory runs each agent as a `claude -p` call".
- The configuration table calls `FACTORY_CLAUDE` "The agent runtime's executable" and `FACTORY_CLAUDE_VERSION` "The version of the agent runtime the image pins".
- *The kernel refuses every other write* names `~/.claude` as "the runtime's own folder" and not opencode's three folders.
- *The machine's image* lists Claude Code, `uv` and the Debian tools as its pinned versions and leaves out opencode.
- *Update the pins* has no line for `OPENCODE_VERSION`, though *Running on opencode* sends the operator there ("Change both together, as for Claude Code (see "Update the pins")"). It does not say that the models in `image/Dockerfile`, the compose defaults of `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` in `image/compose.yml` and the pins of `tests/test_opencode_image.py` must change with it.
- The preflight's closing paragraph names only `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE` and `FACTORY_CLAUDE_VERSION` as the variables to check first.

The documenter of S0008 noticed the pins and left them; nobody owned them. This story corrects these passages. It changes no code and no test, and adds no new section.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`:
   - *The agent runtime*: the opening sentence says that the factory runs each agent as a `claude -p` call under Claude Code, or as an `opencode run` call under opencode (see "Running on opencode"). The passage that follows stays about Claude Code and says so.
   - Configuration table: `FACTORY_CLAUDE` is "Claude Code's executable, used when the runtime is `claude`". `FACTORY_CLAUDE_VERSION` is "the version of Claude Code the image pins", and the preflight fails without it only under Claude Code.
   - *The kernel refuses every other write*: the bullet on `~/.claude` says it is Claude Code's own folder. A bullet beside it names opencode's three folders (`.local/share/opencode`, `.local/state/opencode`, `.cache/opencode`) and the folders of `FACTORY_OPENCODE_FOLDERS`, which an opencode run may write instead.
   - *The machine's image*: the opening paragraph names opencode among the pinned tools.
   - *Update the pins*: a bullet for opencode. It names the `OPENCODE_VERSION` default and the `FACTORY_OPENCODE_MODELS` value in `image/Dockerfile` and the defaults of `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` in `image/compose.yml`, which change with it; says to check the model ids with `opencode models anthropic`; and says that `tests/test_opencode_image.py` pins the version and the model ids as well, so it changes with them and is run with `tests/test_image.py`.
   - The preflight's closing paragraph names `FACTORY_OPENCODE`, `FACTORY_OPENCODE_VERSION` and `FACTORY_OPENCODE_MODELS` as the variables to check first under opencode.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "The agent runtime's executable" docs/operator-guide.md; sed -n '/^### Update the pins/,/^### Claude Code/p' docs/operator-guide.md | grep -c "OPENCODE_VERSION"
```
Expect: `0`, then a number of at least `1`

```bash
grep -c "the runtime's own folder" docs/operator-guide.md; grep -c ".local/state/opencode" docs/operator-guide.md
```
Expect: `0`, then a number of at least `2`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: it says "None" and names no module. That fits a docs-only story; it states no conversion, format, ordering or default of its own.
   - Criteria: criterion 1 (nothing outside the guide changes) and criterion 2 (`make check`) are each testable. The docs criterion lists one concrete edit per passage, each with the exact phrase or value to use. It states no limit, validation or rejected input, so no failing side is owed. The guide's headings match the passages the story names: *The agent runtime*, *The kernel refuses every other write*, *The machine's image*, *Update the pins*, and the preflight section.
   - Smoke test: all three blocks run as written. I checked the current counts in `docs/operator-guide.md` and the headings the `sed` range uses. "The agent runtime's executable" appears once and "the runtime's own folder" appears once, so the Expect values of `0` are reachable by the edit. `.local/state/opencode` appears once now, so the Expect of at least `2` needs the new bullet to mention it, as criterion 3 requires. `### Update the pins` and `### Claude Code` both exist, in that order, so the `sed` range is valid. Each `Expect:` line is a number or a string that the output can be checked against.
   - Architecture: the story changes only `docs/operator-guide.md`, which is the documenter's write path. It touches no layer, no code and no test. It names `tests/test_opencode_image.py` and `image/` only as text for the guide to cite.
   - Scope: F0020's scope lists `docs/operator-guide.md` under each story's docs criterion. The story adds no new section and does not touch Out of scope items. It corrects older passages that S0008's `Running on opencode` section left inconsistent.
4. factory: started tests as self.
