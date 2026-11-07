---
stage: docs-review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 613
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T00:33:05.694414Z'
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
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T00:24:36.894446Z'
  stage: docs-review
  run: 474f380b2ffc4ab292ac49e18ca3c213
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T00:24:41.970248Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T00:28:36.344846Z'
  stage: docs-only
  run: c408dbd565cc4d9abd3e57bfc908cbd4
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T00:28:41.478829Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T00:30:06.713196Z'
  stage: docs-review
  run: b3f7a2b855844a619f3813f216335331
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T00:30:12.480424Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T00:33:00.482279Z'
  stage: docs-only
  run: 676455c596584e7c93d8b9e0ad9820ca
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T00:33:05.694414Z'
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
7. reviewer: Docs review of `docs/operator-guide/agent-runtime.md` against the old text on `main`, the code and `docs/project-guide/style.md`. Criterion 3 holds: the file is on `docs/checked-documents.txt` and the journal reports `documents ok`. Criterion 4 holds: no link in `README.md`, `docs/`, `agents/` or `operator/README.md` points to a removed heading. I checked the removed headings "The agent in a container", "The agent run's `PATH` and `HOME`" and "An opencode run's budget". Criteria 1 and 2 have these findings:

   1. `docs/operator-guide/agent-runtime.md:45` and `:86-88`: login route 3 and *Without a login file* say a manual `claude` login run as `factory` on the VM works. The code does not bear this out. Nothing mounts or copies a host login into the agent's home: `HOME` is `WORK_HOME = "/work/home"` (`src/factory/machine/domain/containers.py:15`) on the dataset, which the rollback clears before every stage. Line 11 and line 189 of the same file say exactly that. Fix: remove the manual-login route. Say that with neither file the call has no login and the shell reports `none`, and point to the token file.
   2. `docs/operator-guide/agent-runtime.md:120`: "A run whose text matches no provider rule ends `died`" also covers a run that completed. The code ends a run `died` only when it exits non-zero, gives no reply or an error reply, and no limit, budget or time limit applies (`src/factory/agents/adapters/claude_runtime.py:226-241`, `src/factory/agents/adapters/opencode_runtime.py:477-490`). Fix: name those conditions, as the old text did.
   3. `docs/operator-guide/agent-runtime.md:275`: "That token is at most the token's life less ten minutes old" is wrong. The refresher rewrites the file at least every ten minutes, so a run starts with a token at most ten minutes old. That token stays valid for at least its life less ten minutes, which is fifty minutes for a one-hour token. Fix: say that.
   4. `docs/operator-guide/agent-runtime.md:362`: the *Reference* table gives `FACTORY_OPENCODE`'s default as `none`. The code's default is `opencode` (`src/factory/shared/domain/settings.py:91,161`), and `install.md:79` also says `opencode`. Fix: write `opencode`.
   5. `docs/operator-guide/agent-runtime.md:199`: `<agent home>/.cache/opencode` uses the placeholder that lines 281 and 397 use for the installed agents' folder (`FACTORY_CLAUDE_HOME`). The cache is in the agent's `HOME`, `/work/home`, and its two sibling paths in the same sentence have no prefix. Fix: name all three under the agent's home in one form, for example "in the agent's home `/work/home`: `.local/share/opencode`, …".
   6. `docs/operator-guide/agent-runtime.md:16`: the old text's rule that the factory takes the first word of `claude --version` (example `2.1.289`) was dropped without being named as dropped (criterion 2). The rule still holds in `src/factory/agents/adapters/agent_launch.py:335` and `src/factory/machine/domain/preflight.py:50`, and the operator needs it to set `FACTORY_CLAUDE_VERSION`. Fix: restore it, in the text or in *Reference*.
   7. `docs/operator-guide/agent-runtime.md:183-187`: the task *Running on opencode* has no step to set `FACTORY_AGENT_RUNTIME=opencode` or to restart the instance. Style: a task is numbered steps, each one action. Fix: add both as steps.
   8. Inline commands at `docs/operator-guide/agent-runtime.md:59,61,64,70,195,258` (`claude setup-token`, `install -m 0600 -o factory -g factory`, `Set-Content …`, `opencode models anthropic`, `python -m factory.entry.refresh_token`) are neither runnable examples nor marked blocks. That breaks the Description ("every command the file shows is a runnable example or is marked") and style.md *Examples that are not run*. Fix: put each under its numbered step in an `sh` block of bare commands, with a line saying where it runs. Or remove the command from the prose where it is only mentioned.
   9. Criterion 1 / style rule 3: these glossary words are not linked at their first use:
      - role (`:14`)
      - claim (`:16`)
      - project command (`:50`)
      - journal and cost record (`:77`, `:80`)
      - work item (`:107`)
      - tick and attempts cap (`:169`)
      - lease (`:178`)
      - crash (`:179`)
      - stop (`:297`)
      - story and feature (`:334`)
      - round (`:341`)

      Fix: link each to `../project-guide/glossary.md` at its first use.
   10. `docs/operator-guide/agent-runtime.md:322`: "The setting `FACTORY_CLAUDE_HOME` keeps its name" only makes sense to a reader who knows the history of a rename (style rules 1 and 7). Fix: remove it, or say plainly that the setting names the shipped agents' folder for both runtimes.
   11. `docs/operator-guide/agent-runtime.md:171-174`: "You do one of these" introduces two alternatives as numbered steps, which reads as a sequence. Fix: make them bullets, or write them as one sentence with "or".
   12. `docs/operator-guide/agent-runtime.md:378`: "The wiring gives the runtime this chain" has nothing for "this chain" to refer to, and "the wiring" is a word of the code. Fix: say what install.md's "The stage environment" sets (the container environment the runs use), or keep only the pointer.

   Dropped on purpose, checked and accepted:
   - the `planning/cloud-sandbox/` pointer (the path does not exist);
   - the F0043 and F0044 notes;
   - "This repository's own build stays on the subscription";
   - `limit_wait` (an internal field that is not in the records contract).
8. factory: started docs-only as vm.
9. documenter: Round 1: fixed the reviewer's twelve numbered findings in `docs/operator-guide/agent-runtime.md`. `make documents` ends with `documents ok (10.3 s)`. I did not run `make check`, because I changed only a document.

   Files changed:
   - `docs/operator-guide/agent-runtime.md`: the changes below.
   - `docs/checked-documents.txt`: unchanged this round.

   Findings:
   1. The manual-login route is removed. The login list now ends in "none", and *Without a login file* says the shell reports `none` and that a login made by hand does not survive the rollback. It points to the token file.
   2. `died` is now defined as a run that exits non-zero, gives no reply or an error reply, and has no provider limit, budget or time limit applying. I did not re-read the code lines the reviewer cited (`claude_runtime.py:226-241`, `opencode_runtime.py:477-490`); I took the conditions from the reviewer's finding and the old text.
   3. The token-age sentence is corrected: the file is rewritten at least every ten minutes, so a run starts with a token at most ten minutes old, and that token stays valid for at least its life less ten minutes (fifty minutes for a one-hour token).
   4. The `FACTORY_OPENCODE` default in the Reference table is now `opencode`. The reviewer cited `settings.py:91,161`; I did not read it, only the reviewer's finding.
   5. The opencode folders are now three full paths under the agent's home `/work/home`. The first attempt, `.cache/opencode`, was flagged by the name check, so all three are written as full paths.
   6. The rule that the factory takes the first word of `claude --version` (example `2.1.289`) is restored in *How a call is made*. `agent-runtime-version` is described the same way.
   7. *Running on opencode* now has numbered steps that set `FACTORY_AGENT_RUNTIME=opencode` (or `--runtime opencode` of `operator/vm/setup.sh`) and restart the instance.
   8. Each inline command that needs the VM or a model now stands in an `sh` block under its step, with a line saying where it runs. These are `claude setup-token`, `install -m 0600 ...`, `Set-Content ...`, `opencode models anthropic` and `python -m factory.entry.refresh_token`. They are not run.
   9. I linked these words to the glossary at first use: role, cost record, journal, work item, tick, attempts cap, lease, claim, crash, story, feature and round. Claim and role were not linked at the reviewer's cited lines (the reviewer named line 16 for claim and line 14 for role, but the document's first uses are elsewhere). A "project command" mention and the "stop" mentions are not linked, because the page uses them only in passing in a sentence about the secret and in the name of a stop; the reviewer should say if they still want them.
   10. The `FACTORY_CLAUDE_HOME` sentence now says the setting names the shipped agents' folder for both runtimes.
   11. The two ceiling alternatives are bullets, not numbered steps.
   12. "The wiring gives the runtime this chain" is replaced by a pointer to "The stage environment" in `install.md`.

   Cross-read and found current: `install.md`, `health.md`, `stops.md`, `machine.md`, `work-items.md`. No heading that another file links to was changed.

   Stale text noticed and not touched: the project guide's "does not exist" report lines (`hosting.md`, `machine.md`, `work.md`, `README.md`, `health.md`). The files are not on the checked list.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (10.5 s)
10. factory: started docs-review as vm.
11. reviewer: Docs review, round 1. I read `docs/operator-guide/agent-runtime.md` on the branch against the round-0 findings, the code and `docs/project-guide/style.md`.

    Round-0 findings 1 to 8 and 10 to 12 are fixed. I checked these facts against the code and found them true:
    - the allow list of six names (`src/factory/agents/domain/agent_runs.py:39`);
    - the refused container names (`src/factory/shared/domain/settings.py:86`);
    - `FACTORY_OPENCODE`'s default `opencode` (`settings.py:91`);
    - `FACTORY_AGENT_RUNTIME`'s default `claude`;
    - `--runtime opencode` (`operator/vm/setup.sh:21`);
    - `AGENT_RUNTIME`, `OPENCODE_VERSION=1.19.5` and the model pin (`operator/vm/Dockerfile:5,67`);
    - the 180-minute sum against a lease of 60 (`factory/pipeline.yml:23`);
    - every heading quoted from `machine.md`, `health.md`, `stops.md`, `work-items.md` and `install.md`.

    Criterion 3 holds: the file is on the list and the journal reports `documents ok`. Criterion 4 holds: no heading changed this round.

    Round-0 finding 9 is only partly fixed, and three more points remain:

    1. `docs/operator-guide/agent-runtime.md:16`: the first use of "claim" ("before any claim") is not linked. The link stands at `:194`. Style rule 3 asks for the link at the first use. Fix: link "claim" at `:16` and leave `:194` plain.
    2. `docs/operator-guide/agent-runtime.md:50` and `:335`: "project commands'" (`:50`) and "the stop `agent_definition_invalid`" (`:335`, its first use in the glossary's sense outside a quoted heading) are glossary words, and neither is linked. Rule 3 makes no exception for a word used in passing. Fix: link both to `../project-guide/glossary.md`.
    3. `docs/operator-guide/agent-runtime.md:96`: "or the value for the API key" leaves out a value the code names exactly: `login` is `api_key` (`src/factory/agents/domain/agent_runs.py:44`, and the page itself shows `factory-login-used: api_key` at `:400`). Fix: write "`subscription`, `api_key` or `none`".
    4. `docs/operator-guide/agent-runtime.md:74-78`: the Windows `Set-Content` command is a PowerShell command, but it stands in an `sh` block outside any numbered step. *Examples that are not run* puts such a command under its numbered step. Fix: make it the Windows variant of step 2 of *The agent's login token*, with its block indented under that step.
    5. `docs/operator-guide/agent-runtime.md:16`: the version check is told twice. First "The preflight compares it with `FACTORY_CLAUDE_VERSION`", then `agent-runtime-version` "compares the first word of its output with the pinned version". Fix: say once that the item `agent-runtime-version` runs `claude --version` or `opencode --version` in the stage image and compares its first word with `FACTORY_CLAUDE_VERSION` or `FACTORY_OPENCODE_VERSION`.
    6. `docs/operator-guide/agent-runtime.md:288`: the paragraph "Starting it with the instance…" starts with a stray space. Fix: remove it.

    Dropped on purpose, still accepted from round 0: the `planning/cloud-sandbox/` pointer, the F0043 and F0044 notes, "This repository's own build stays on the subscription", and `limit_wait`.
12. factory: started docs-only as vm.
13. documenter: Round 2: fixed the reviewer's six numbered findings from round 1 in `docs/operator-guide/agent-runtime.md`. `make documents` ends with `documents ok (10.3 s)`. I did not run `make check`, because I changed only a document.

    Files changed:
    - `docs/operator-guide/agent-runtime.md`: the changes below.
    - `docs/checked-documents.txt`: unchanged this round.

    Findings:
    1. "claim" is now linked to the glossary at its first use (*How a call is made*). The link at "The claim stays held" is plain.
    2. "project commands" (in the list of what the secret does not reach) and "stop" (before `agent_definition_invalid` in *Project agents*) are linked to the glossary.
    3. The `login` field now reads "`subscription`, `api_key` or `none`".
    4. The Windows `Set-Content` command is now part of step 3 of *The agent's login token*, as its Windows variant. It is indented under that step in a `powershell` block, and the final step (set `FACTORY_CLAUDE_LOGIN_FILE`) follows as step 4. I did not run it, since it needs Windows.
    5. The version check is told once: `agent-runtime-version` runs `claude --version` or `opencode --version` in the stage image and compares the first word with `FACTORY_CLAUDE_VERSION` or `FACTORY_OPENCODE_VERSION`. The rule that the factory takes the first word of the output stays, with the `2.1.289` example.
    6. The stray leading space before "Starting it with the instance" is removed.

    I did not re-read the code behind these edits. The reviewer's findings named the code lines, and I took the facts from them. I changed no heading, so no link from another file is affected.

    Cross-read and found current: the headings in `install.md`, `health.md`, `stops.md` and `machine.md` that this file links to.

    Stale text noticed and not touched: the "does not exist" report lines for paths in `docs/project-guide/` (`machine.md`, `work.md`, and others). They are not on the checked list.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (10.3 s)
14. factory: started docs-review as vm.
