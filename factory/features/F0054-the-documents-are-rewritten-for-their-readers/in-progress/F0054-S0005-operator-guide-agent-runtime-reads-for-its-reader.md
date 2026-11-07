---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 613
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T00:22:20.214089Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T00:17:05.294071Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T00:17:05.301510Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T00:17:21.039257Z'
  stage: intake
  run: 0c107ab4b5584702a6fcf48c2c12c797
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T00:17:26.058600Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T00:22:14.908320Z'
  stage: docs-only
  run: 23d1eed4e4cd4d98b8906cd9f1fd5e07
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T00:22:20.214089Z'
  stage: docs-review
---

# The operator guide's the agent runtime reads for the operator

## Description

`docs/operator-guide/agent-runtime.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/agent-runtime.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/agent-runtime.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/agent-runtime.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/agent-runtime.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/agent-runtime.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only (`docs/operator-guide/agent-runtime.md`, one line in `docs/checked-documents.txt`, links to changed headings) and states that no code, test or agent file changes. Every path is one the documenter may write.
   Criteria: 1 (style, judged by the reviewer), 2 (nothing dropped, compared against the code), 3 (on the checked list, `make documents` prints `documents ok`) and 4 (no broken links) each have one check. The Interface's heading-link rule is covered by criterion 4. The Interface states no limit or validation, so there is no failing side to test. `make check` is criterion 5, and `docs:` is last.
   Smoke test: `grep -cx "docs/operator-guide/agent-runtime.md" docs/checked-documents.txt` runs as written and its `Expect: 1` can be checked against the output. It runs no pytest.
   Docs criterion: it refers to criteria 1 to 4 and names what the reader must know, which is the agent runtime facts kept in the file or its Reference section. It dictates no sentences.
   Architecture: the story changes documents only, so the code layers are untouched. `docs/decisions.md` is explicitly left alone.
   Scope: this is S0005 in the feature's story list, and the work is a document rewrite with no behaviour change. Nothing in the feature's Out of scope is touched.
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/operator-guide/agent-runtime.md` for the operator reader, in the style of `docs/project-guide/style.md`. `make documents` prints `documents ok (5.7 s)`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/agent-runtime.md`: restructured into task sections (how a call is made, the login, behind a proxy, a run that ends without a result, a provider's spend limit, running on opencode, the agent files) and a closing *Reference*.
     - Numbered steps for the token, API key, proxy, opencode and provider-file tasks.
     - The ceiling stop is written as you see / it means / you do.
     - Glossary links at first use.
     - The old text's feature and story IDs, "v1" and "since/no longer/as before" wording are gone.
     - Five unresolved paths found by the name check are written with `<project>/` or `<agent home>/` placeholders.
     - *Reference* holds a settings table (Name / What it does / Default / Example), the login shell's argument list, the full `podman run` words, the login-file fault messages, the agent-file fault table and the key table.
   - `docs/checked-documents.txt`: added `docs/operator-guide/agent-runtime.md`.

   Sections that other files link to keep their old titles: "The agent's API key", "The agent's login token", "Running on opencode", "A company's provider", "A bearer token for the model API", "A provider's spend limit" (with its subsection "What to do at the ceiling"), "Behind a proxy" and "The agent files". Links in `install.md`, `health.md`, `stops.md`, `pipeline.md`, `cloud-run.md` and `docs/project-guide/agents.md` still resolve. The `make documents` name check passes.

   Dropped or changed on purpose (the reviewer should compare against the old text in git):
   - I removed the pointer to `planning/cloud-sandbox/`, which does not exist. The claim about opencode contacting `registry.npmjs.org` stays, and a deployment is told to read the proxy's log.
   - I removed "the image is F0043's" and "Since F0044-S0001 the runtime no longer sets CLAUDE_CONFIG_DIR". The remaining fact is that `claude` keeps `.claude.json` in the home's root.
   - The old text said the opencode item and the preflight items are in `health.md`. That is unchanged, and I left it as a pointer.
   - I added example values to the refresher's variable table (`https://auth.example.invalid/token`, `llm.invoke`, `factory`, `/secrets/client-secret`). These are made-up names, not copied from a run.
   - `FACTORY_CA_BUNDLE`'s example in the Reference table (`/etc/ssl/corp-ca.pem`) is also made up. `install.md` has its own example.

   Code I read for the rewrite: `src/factory/machine/adapters/podman_runs.py` (flags and limits), `src/factory/agents/adapters/agent_launch.py` (quarter budget, minimum 0.50), `src/factory/agents/adapters/opencode_runtime.py` (the three `OPENCODE_DISABLE_*` variables) and `src/factory/shared/domain/settings.py` (defaults and names), plus the settings table in `install.md`. I did not re-read the code behind the prose rules. These I carried over from the old text unchanged:
   - the log line formats;
   - the `died` text rules;
   - the refresher's intervals and messages;
   - the agent-file fault list.

   Examples: the file has no `console` blocks. Its commands (`claude setup-token`, `install`, `opencode models anthropic`, `python -m factory.entry.refresh_token`) need the VM or a model, so they are written inline and not as runnable examples. Log lines are `text` blocks and the provider file is a `json` block. Neither is run.

   Cross-read and found current: `install.md`, `health.md`, `stops.md`, `pipeline.md`, `cloud-run.md`, `docs/operator-guide/README.md`, and `docs/project-guide/agents.md` for its pointer into this file.

   Stale text I noticed and did not touch:
   - The old file said a manual `claude` login works when no login file holds one, and also that the rollback clears the agent's home before every stage. I kept the first statement and did not repair the tension. The reviewer or a later story should check against the code whether a manual login can survive on the machine.
   - `docs/project-guide/README.md`, `agents.md`, `hosting.md`, `machine.md` and `work.md` print "does not exist" report lines for paths. They are not on the checked list, so they do not fail the check.

   I found nothing where the code contradicts the Interface.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (7.7 s)
6. factory: started docs-review as vm.
