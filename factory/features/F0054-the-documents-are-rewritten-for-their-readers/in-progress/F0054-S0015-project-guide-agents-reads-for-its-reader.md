---
stage: docs-review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 623
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T04:12:31.267176Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T04:12:31.274946Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T04:12:45.946559Z'
  stage: intake
  run: f9c96d4ca24f45e6a60fd82371ed819b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T04:12:50.736910Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T04:20:22.931582Z'
  stage: docs-only
  run: 5c566db6360b4027b5dcf3c149fc0cba
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T04:20:27.799744Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T04:23:01.847201Z'
  stage: docs-review
  run: 3a8f51c964b447be86869e162d367726
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T04:23:06.886506Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T04:28:51.045118Z'
  stage: docs-only
  run: fda00b98ea744d4daf825a3c1f08eb55
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T04:28:56.196925Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T04:31:26.305400Z'
  stage: docs-review
  run: 06f8ec87f4384267897206c11f862a27
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T04:31:31.337924Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T04:35:05.720809Z'
  stage: docs-only
  run: c695979eff25450eacc755a3f7cf42e2
---

# The project guide's page on the agents area reads for the developer

## Description

`docs/project-guide/agents.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/agents.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/agents.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/agents.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/agents.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/agents.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/agents.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/project-guide/agents.md`, `docs/checked-documents.txt` with its one line), and says no code, test or agent file changes. Every path it changes is one the documenter may write.
   - Criteria: on the docs route there are no tests, so criteria 1 and 2 are judged by the reviewer against `docs/project-guide/style.md` and the code. Criteria 3 to 5 are checked by `make documents` (`documents ok`, no broken link) and by the link rule. Criterion 6 is `make check`. The failing side is covered: a dropped fact, a broken link and a missing checked-list entry each fail a criterion.
   - Smoke test: `grep -cx "docs/project-guide/agents.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It does not run pytest.
   - Docs criterion (7): says docs are as criteria 1 to 5 and `docs/decisions.md` is unchanged. It names what the reader must know and dictates no sentences.
   - Architecture: a documents-only change to the project guide's page on the agents area. It touches nothing in `factory/`, `src/` or `tests/`, and the story does not use the `.claude/` or `planning/` paths.
   - Scope: within F0054's scope (S0015 is listed, one file per story). It touches nothing in the feature's out-of-scope list (`decisions.md`, `docs/runs/`, the operator playbook, behaviour changes).

   Route: docs-only.
4. factory: started docs-only as vm.
5. documenter: Changed files:
   - `docs/project-guide/agents.md`: rewritten for its reader in the style of `docs/project-guide/style.md`.
     - Each section now opens with the idea in two or three sentences, then a block of names and signatures, then one rule per bullet, then See also.
     - Exact detail moved into a *Reference* section at the end. It has nine parts: request and result, the login shell, the `claude` call, a resumed run, the opencode call, the opencode configuration (including the result block, provider file and lockdown switches).
     - Modules are linked once, by relative links.
     - The section heading *The agent definition reader* is kept, because `work.md` links to it.
     - I read the code to check these names and facts: `agent_launch.py`, the `AgentRuntime` and `AgentDefinitionReader` interfaces, `PROTECTED_PATHS`, the seven agent files' front matter, `agents/settings.json` and the template folder.
     - One fact I corrected: `AgentRuntime` also has `tool_uses(transcript)`, which the old page left out. It is now listed.
     - The `.claude`, `agents` and path examples that `make documents` flagged as missing files are now runnable `console` blocks. They also use the `<project>/factory/agents/` placeholder.
     - The old `bash` example for the agent reader is now a `console` example. It prints the last line of the error and uses `<message>` for the part of the error text that varies.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/agents.md`.

   Removed on purpose, because the style page forbids history (rule 1 and rule 7):
   - The two sections *Replaced in v1.2*.
   - The v1-to-v1.1 rename table *Replaced from v1*. The renamed words stay in the text as the current vocabulary.
   - Story and feature IDs (F00xx-S00xx) and "v1 / v1.1 / v1.2" provenance sentences, including "the texts come from v1 at commit f8bc9d2 so the baseline run compares". That sentence gave a reason, not a fact about the current code. The reviewer should confirm whether a line in `docs/decisions.md` should hold it; I wrote nothing there, since the story says `decisions.md` is untouched.
   - The remark that `FINISH_MESSAGE` asks for `question` "where v1 asked for `stuck`" is now "`question`, not a decision named `stuck`".
   - The remark "(a later story)" on waiting out a provider limit is now "until the application layer waits the limit out".
   - The sentence about the tiny story of 2026-10-18 (`.costs.jsonl` and `make secrets`) is shortened to the standing reason.

   Checks:
   - `make documents` ends with `documents ok (13.1 s)`.
   - I did not run `make check`: every changed file is a document, and the factory runs the checks after this stage.

   Cross-read:
   - `work.md` links to the heading *The agent definition reader*, and that heading still exists.
   - A grep for `agents.md#` found no other link into this page.

   Stale text I noticed and did not touch:
   - `docs/project-guide/README.md` and `docs/project-guide/machine.md` give "does not exist" findings in the unchecked-documents report. They are outside this story.
   - I could not check the correctness of every sentence moved verbatim into the Reference against the code. The reviewer should compare `claude_runtime.py` and `opencode_runtime.py` against the Reference.

   `check`: check: green
   `secrets`: secrets: green (0.5 s)
   `documents`: documents ok (13.3 s)
6. factory: started docs-review as vm.
7. reviewer: I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I compared the new `docs/project-guide/agents.md` with the old one on `main`, checked its claims against the code on the branch and judged its writing against `docs/project-guide/style.md`. Criteria 3 and 5 hold: the page is on `docs/checked-documents.txt`, the journal records `documents ok`, and the one heading other pages link to, *The agent definition reader*, is kept, along with *Calls in a container*, which `machine.md:288` names.

   Findings:
   1. `docs/project-guide/agents.md:340`: says "This repository's `secrets` recipe is the template's". `tests/agent_files/test_demo_makefile_secrets.py` compares the template with `demo/todo-service/project/Makefile`, not with this repository's Makefile. Fix: say the todo demo's recipe (`demo/todo-service/project/Makefile`) is the template's.
   2. `docs/project-guide/agents.md:520`: "The run's configuration and rules files". The opencode runtime writes only `opencode-<run>.json` (`files.config` in `src/factory/agents/adapters/opencode_runtime.py`), and line 122 of the page says there is no rules file. Fix: "The run's configuration file is the first call's and is removed only after the resume."
   3. `docs/project-guide/agents.md:383`: the list of "twelve patterns" gives the last one as `<project>/factory/agents/*`. In the code it is `f"{PROJECT_AGENTS_DIRECTORY}/*"`, which is `factory/agents/*` (`src/factory/agents/domain/write_paths.py:33`, `src/factory/shared/domain/paths.py:20`). Fix: quote the real pattern, for example as `PROJECT_AGENTS_DIRECTORY` + `/*`, and say in prose that it matches `<project>/factory/agents/` at the project's root.
   4. `docs/project-guide/agents.md:109`: the old page named `.local/share/opencode`, `.local/state/opencode`, `.cache/opencode` and `.config/opencode`. They are now "its folders under `.local` and `.cache`", and the journal does not list this as dropped on purpose (criterion 2). The sentence also does not parse ("in the agent's home and its configuration under `.config`"). Fix: name the four folders with a placeholder (`<home>/.local/share/opencode` and so on) in one sentence that parses.
   5. `docs/project-guide/agents.md:253` and `:270`: two parts of the old page's rule for editing agent files are gone. One is that a sentence outside `## Lessons` and the listed passages keeps its words when edited. The other is what sets the listed passages apart: they are the factory's own text, and the rest is the renamed original text. "Other fixed passages" no longer says why they are fixed. This is a rule for whoever edits an agent file, not only history (criterion 2). Fix: one sentence that the other sentences keep their words when edited, and a one-line pointer to *The shipped agents carry v1's texts, renamed, and `stuck` does not exist* in `docs/decisions.md` (style rule 1 allows one line).
   6. `docs/project-guide/agents.md:3`: says the factory's own words are "in italics" and in the glossary. No glossary word on the page is in italics or linked: stall (7), stage (17), dataset and base (101), work item and journal (255), pipeline definition and role (170), write paths (350), backlog (278), approval (332). Criterion 1 and style rule 3 fail. Fix: link each glossary word to `glossary.md` at its first use, and drop or correct the sentence about italics.
   7. Links on `docs/project-guide/agents.md` (Interface, criterion 4), in three parts:
      - Linked more than once: `decisions.md` (15, 131, 145, 570, 577), `wiring.py` (20, 119), `agent_runtime.py` (7, 176), `agent_launch.py` (72, 422), `machine.md` (24, 68) and `pipeline.md` (24, 204, 346, 363).
      - Named but never linked: `fake_agent_runtime` (14, 151, in a code block with nothing linked above it), `factory.watching.application.transcripts` (105), `factory.agents.domain.tokens`, `factory.agents.application.tokens`, `factory.agents.adapters.oauth_token` and `factory.shared.domain.errors` (140-142), `factory.agents.domain.provider_limits` (464), `factory.shared.adapters.validation_faults` (233), `factory.shared.domain.identifiers` (404), `factory.shared.domain.paths` (383), `tests/conftest.py` (149), `tests/support/claude_stand_in.py` (44), `tests/support/opencode_stand_in.py` (129), the `tests/guards/` and `tests/agent_files/` files (42, 142, 256, 257, 273, 275, 282-284, 300, 304, 333, 340), `tests/support/shipped_agents.py` (284) and the two `test_write_paths.py` files (361).
      - Linked after the code block instead of above it: `project_agents.py` is linked at 213, below its block at 210. `operator/template/factory/pipeline.yml` is first named at 282 but linked at 331.
      - Fix: link each file once, at its first mention, by a relative link, above any code block that names it.
   8. `docs/project-guide/agents.md:300`: `test_claude_agent_texts_review_groups.py` starts below the repository root (style rule 8). Fix: `tests/agent_files/test_claude_agent_texts_review_groups.py`, linked.
   9. `docs/project-guide/agents.md:137`: `python -m factory.entry.refresh_token` is shown as a bare command. It is neither a runnable `console` example nor a marked block (reviewer *Documents* item, Description). Fix: either a `console` example of what it prints when run without its settings, or an `sh` block with a sentence saying where it runs.
   10. Style rules 2 and 7 and the project-guide section form, in `docs/project-guide/agents.md`:
       - Sentences well over 25 words, or with more than one parenthesis: 264, 266, 272, 336 (about 60 words), 342 and 119.
       - "The moved constants" (93) is history (rule 7).
       - *Matching and placeholders* (365) opens with bullets: it has no two or three plain sentences and no signatures of `matches_any` and `is_writable`.
       - Fix: split those sentences, write "the constants defined in `agent_launch`", and give that section its opening sentences and a signature block.

   Dropped on purpose, and acceptable as history (style rules 1 and 7):
   - the two *Replaced in v1.2* sections and the *Replaced from v1* rename table;
   - the feature and story IDs, the version history, the commit `f8bc9d2` and "step 5 of the cycle";
   - the `factory/features/F0004-x` example;
   - the protected-path examples `factory/agentsx/coder.md`, `src/x.claude/a` and `src/pyproject.toml`, which line 386 now states as rules.

   The added `tool_uses` line matches `src/factory/agents/application/agent_runtime.py:34`.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the ten findings of the review, all in `docs/project-guide/agents.md`. `docs/checked-documents.txt` already holds the page's line from round 0, so I did not touch it. `make documents` ends with `documents ok (13.2 s)`, and no finding names `agents.md`. I did not run `make check`, because every file I changed is a document.

   How I handled each finding:
   1. Finding 1 (the secrets recipe): the page now says the todo demo's recipe, `demo/todo-service/project/Makefile`, is the template's. It links that file and `test_demo_makefile_secrets.py`.
   2. Finding 2 (the opencode configuration): the sentence now says "The run's configuration file is the first call's and is removed only after the resume."
   3. Finding 3 (the twelfth protected pattern): it is now written as `PROJECT_AGENTS_DIRECTORY` + `/*`, with a link to `paths.py` where the constant is defined. A sentence says the pattern matches `<project>/factory/agents/` at the project's root.
   4. Finding 4 (the opencode folders): they are named again as `<home>/.local/share/opencode`, `<home>/.local/state/opencode`, `<home>/.cache/opencode`, and the configuration in `<home>/.config/opencode`.
   5. Finding 5 (the editing rule): I restored it. Besides the lessons, the passages listed are the factory's own text and are pinned by tests. Every other sentence outside `## Lessons` keeps its words when edited. A one-line pointer to the decision log entry *The shipped agents carry v1's texts, renamed, and `stuck` does not exist* gives the reason.
   6. Finding 6 (the glossary): I replaced the "in italics" sentence. I linked these glossary words at their first use: stall, stage, dataset, base, role, pipeline definition, journal, work item, backlog and write paths. I did not link "approval": its only appearances are inside code spans.
   7. Finding 7 (links):
      - Every file the page names is linked once, at its first mention, and above any code block that shows it.
      - Later mentions of `decisions.md`, `wiring.py`, `agent_runtime.py`, `agent_launch.py`, `machine.md` and `pipeline.md` are plain text, or "the decision log".
      - `project_agents.py` is now linked in the sentence above its block.
      - The `operator/template/factory/pipeline.yml` link moved to its first mention.
      - The `FakeAgentRuntime`, token, `oauth_token`, `validation_faults`, `identifiers`, `provider_limits`, `transcripts`, `conftest`, stand-in and `tests/` files are now linked.
   8. Finding 8 (the review-groups test): it now carries its full path, `tests/agent_files/test_claude_agent_texts_review_groups.py`, as a link.
   9. Finding 9 (`refresh_token`): it is an `sh` block now, with a sentence saying it runs on the host beside the factory with the operator's settings.
   10. Finding 10 (style):
       - I split the long sentences at old lines 119, 264, 266, 272, 336 and 342 into bullets of one idea each.
       - "The moved constants" became "The constants defined in `agent_launch`".
       - *Matching and placeholders* now opens with two plain sentences and a block holding the signatures of `matches_any`, `is_writable` and `expand_write_paths`.

   Cross-read: `work.md` still links *The agent definition reader*, a heading that is kept. `machine.md:288` names *Calls in a container*, also kept. I checked the new link targets: they all exist, and `make documents` finds no broken link.

   Stale text I noticed and did not touch (not this story's):
   - The unchecked-documents report still lists "does not exist" findings in `docs/project-guide/README.md` and `docs/project-guide/machine.md`.
   - The rewrite moved the Reference text over as it was. I did not re-read `claude_runtime.py` and `opencode_runtime.py` line by line against it.
   - I wrote nothing in `docs/decisions.md`. The old sentence that the texts come from v1 so the baseline run compares still holds no line in the decision log. I removed it as history; the reviewer may decide whether a decisions line should carry it.

   `check`: check: green
   `secrets`: secrets: green (0.5 s)
   `documents`: documents ok (13.1 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`. I checked the new `docs/project-guide/agents.md` against the code on the branch and against `docs/project-guide/style.md`.

    The ten round-0 findings are fixed as the documenter's entry 9 says. I checked those lines again:
    - the secrets recipe now names `demo/todo-service/project/Makefile`;
    - the opencode resume names one configuration file;
    - the twelfth protected pattern is `PROJECT_AGENTS_DIRECTORY` + `/*`;
    - the four opencode folders are named;
    - the editing rule is back, with its pointer to the decision log;
    - the glossary words that finding named are linked;
    - the files that finding named are linked once;
    - the review-groups test has its full path;
    - `refresh_token` is a marked `sh` block;
    - the named long sentences are split.

    These claims match the code: the agent table against the front matter of `agents/agents/*.md`, the settings bullets against `agents/settings.json`, `LOCKDOWN_SWITCHES`, `LEFT_OUT_TOOLS` and the body layout of the agent files. Criteria 3 and 5 hold: the page is on `docs/checked-documents.txt`, the journal records `documents ok`, and the headings other pages link to (*The agent definition reader*, *Calls in a container*) are kept.

    Findings:
    1. `docs/project-guide/agents.md:486`: "Until the application layer waits the limit out, it is a stall like `died`" is false. `PatientRuns` (`src/factory/agents/application/provider_limits.py:21`, called at `src/factory/pipeline/application/stage.py:131`) waits out the limit and resumes the run until the waits reach `ceiling`. Only a run that still ends `provider_limit` at the ceiling is a stall. Fix: say that, and point to *PatientRuns* in `pipeline.md`.
    2. `docs/project-guide/agents.md:480`: `ProviderLimit` is described with only `status` and `message`, read from two variables. The model also has `cooldown` and `ceiling` (`src/factory/agents/domain/provider_limits.py:51-52`), read from `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` and `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` (`src/factory/shared/domain/settings.py:63-64`). Fix: name all four fields and all four variables.
    3. `docs/project-guide/agents.md:261` and `:263` have two errors:
       - "`intake`, `tester`, `coder`, `reviewer` and `documenter` have more" is false: `smoke-tester` (3 bullets) and `acceptance-reviewer` (4 bullets) also have more lessons, as lines 270-271 say.
       - "The lessons that go beyond those two:" reads as the complete list, but it leaves out `intake`'s three lessons, `reviewer`'s two, `coder`'s helper search and its never-change-a-test lesson, `tester`'s both-sides and test-data lessons, and `documenter`'s guide-size lesson (`agents/agents/*.md`, `## Lessons`).
       - Fix: say that every agent has more, and either list them all or introduce the list as a selection ("Among them:").
    4. Criterion 1 and style rule 3: these glossary words are not linked to `glossary.md` at their first use: instance (20), crash (161), tick (220), project command (261), story (268), feature (278), round (279), acceptance (283), stage environment (339) and take (360). Fix: link each one at its first use.
    5. Interface, criterion 4: these names are never linked, or not at their first mention:
       - `factory.shared.adapters.process`, `git_cli` and `make_commands` (42) are named but never linked;
       - `agents/settings.json` is first named at 290 but linked only at 324;
       - `operator/README.md` (294) is never linked.
       - Fix: link each once, at its first mention, by a relative link.
    6. Style rule 8: three plain later mentions give paths that start below the repository root: `wiring.py` (119), `agent_runtime.py` (178) and `test_claude_agent_texts.py` (287). Fix: write them from the root, for example `src/factory/entry/wiring.py`, as was done for round-0 finding 8.
    7. Style rule 2: these sentences run well over about 25 words, or hold two parentheses:
       - 88, the `make_state_directory` sentence;
       - 280, the `intake` step 2 sentence;
       - 338, the second sentence, which also has two parentheses;
       - 343, the helper sentence;
       - 348, the first sentence, about 50 words.
       - Fix: split each into sentences of one idea.

    Dropped on purpose, and acceptable (checked in round 0): the *Replaced* sections, the rename table, the IDs and version history, and the commit `f8bc9d2`.
12. factory: started docs-only as vm.
13. documenter: Round 2: I fixed the seven findings of the round-1 review. All edits are in `docs/project-guide/agents.md`. `docs/checked-documents.txt` already holds the page's line. `make documents` ends with `documents ok (13.2 s)`. I did not run `make check`, because the only file I changed is a document.

    How I handled each finding:
    1. Provider-limit stall: the page now says `PatientRuns` waits the limit out and resumes the run until the waits reach the ceiling. Only a run that still ends `provider_limit` at the ceiling is a stall. It points to *PatientRuns* in `pipeline.md`.
    2. `ProviderLimit`: all four fields (`status`, `message`, `cooldown`, `ceiling`) and all four variables (`FACTORY_PROVIDER_LIMIT_STATUS`, `_MESSAGE`, `_COOLDOWN_MINUTES`, `_CEILING_MINUTES`) are named. I checked them against `src/factory/agents/domain/provider_limits.py:51-52` and `src/factory/shared/domain/settings.py:61-64`.
    3. Lessons: "every agent has more" replaces the false list of five agents. The list is introduced as "Among the lessons that go beyond those two:", so it reads as a selection. I did not add the lessons it leaves out.
    4. Glossary: I linked these words to `glossary.md` at their first use: instance, crash, tick, project command, story, feature, round, acceptance, stage environment and take. The `sync` sentence in the template section is now two clauses, so the stage environment link reads cleanly.
    5. Links:
       - `git_cli.py`, `make_commands.py` and `process.py` are linked at the sentence that names them.
       - `agents/settings.json` is linked at its first mention, in the section on skills; the later mention is plain.
       - `operator/README.md` is linked at its mention in the docs-route section.
    6. Root paths: the later mentions of `wiring.py`, `agent_runtime.py` and `test_claude_agent_texts.py` now start at the repository root.
    7. Long sentences: I split five of them into short ones or bullets.
       - the `make_state_directory` sentence;
       - the `intake` step 2 sentence;
       - the smoke test `next` sentence;
       - the helper-leave sentence;
       - the `make secrets` sentence.

    Cross-read: headings other pages link to are unchanged (*The agent definition reader*, *Calls in a container*). I checked the new link targets: `git_cli.py`, `make_commands.py` and `process.py` exist at the paths I linked, and `make documents` finds no broken link.

    Stale text I noticed and did not touch, because it is unrelated to this story:
    - `make documents` still reports "does not exist" findings in `docs/project-guide/README.md` and `docs/project-guide/machine.md`. Those files are not yet on the checked list.
    - I carried the Reference sections over from the old page and did not re-read `claude_runtime.py` and `opencode_runtime.py` line by line against them in this round.
    - I wrote nothing in `docs/decisions.md`. The old sentence that the texts come from v1 so the baseline run compares still has no line in the decision log. The reviewer may decide whether it needs one.

    `check`: check: green
    `secrets`: secrets: green (0.5 s)
    `documents`: documents ok (13.0 s)
