---
stage: docs-only
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 616
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T01:20:39.829429Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T01:20:39.836540Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T01:20:55.732384Z'
  stage: intake
  run: 85aa48470a8a40dfbc7509742ac9debc
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T01:21:00.656623Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T01:25:59.653888Z'
  stage: docs-only
  run: a0761340663e45caaa25bf1d5f38b880
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T01:26:05.034788Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T01:27:49.784131Z'
  stage: docs-review
  run: 9f403fbcea604dd4bea6612e03f45e55
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T01:27:54.763611Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T01:30:48.134042Z'
  stage: docs-only
  run: cd4b16c0cd0f4cf2bcfa6b830ce656b2
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T01:30:53.112330Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T01:31:48.510450Z'
  stage: docs-review
  run: 309152586ca84b47813dc26d52df0cd5
---

# The operator guide's the pipeline definition reads for the operator

## Description

`docs/operator-guide/pipeline.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/pipeline.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/pipeline.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/pipeline.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/pipeline.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/pipeline.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only, `docs/operator-guide/pipeline.md` and `docs/checked-documents.txt`, and states that no code, test or agent file changes. Every path is one the documenter may write, so the story takes the docs route.
   Criteria: all six concern documents only. Criteria 1 and 2 are judged by the reviewer against the style guide and the code. Criterion 3 is checked by `make documents` printing `documents ok`, and criterion 4 by link resolution. Criterion 5 is `make check`. The Interface states no limits, defaults or error rules, so there is no failing side to cover.
   Smoke test: the `grep -cx` command is runnable from the repository root and its `Expect: 1` can be checked against the output. It runs no pytest, so no `-q` issue arises.
   Docs criterion: criterion 6 refers back to criteria 1 to 4, which say what the reader gets (a rewritten operator guide page that is accurate, complete and checked). It dictates no sentences.
   Architecture: documentation only, no code placement. It sits in the operator guide, where CLAUDE.md puts operator material. `docs/decisions.md` is left alone, as the feature requires.
   Scope: this is S0008 of F0054's list. It is one file, and it avoids the feature's Out of scope items (`decisions.md`, `docs/runs/`, the playbook).
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/operator-guide/pipeline.md` for the operator and added it to `docs/checked-documents.txt`. `make documents` ends with `documents ok (12.6 s)`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/pipeline.md`:
     - Tasks are numbered steps: change the definition, the docs route, and the story check.
     - The rules and `not_read` are regrouped under task headings.
     - The settings are four-column tables (Name, What it does, Default, Example) under *Reference*, one table each for the definition, a stage, a role and a project command.
     - The `factory-check-story` example is now a `console` block that was run. It builds a story in a temporary folder, shows `ok`, the `not a work item location` line and the usage line. The old example used a placeholder path.
     - The headings "The pipeline definition", "The rules you meet most often" and "Checking a story before it starts" are kept, because `stops.md`, `health.md`, `records.md` and `work.md` link to them by name. I checked each of those links against the new file.
   - `docs/checked-documents.txt`: added `docs/operator-guide/pipeline.md`.

   Removed or changed against the code:
   - "earlier versions read `tool_paths`" is gone, as is "v1.1 way" and "once it exists" for the style page. `tool_paths` is now only one example of an unknown key, which is refused.
   - I moved every name, setting and rule of the old text into the new page. The `not_read` warnings and the kumpel-factory example are kept.
   - New facts that I read in `src/factory/pipeline/domain/pipeline_definition.py`: the names `human`, `factory` and `question` are reserved for stages and roles; every name in `checks` and `reports` must be a project command; `acceptance_stage` must name a stage with a role.
   - Dropped on purpose: the old table row saying the template "also names `sync`, 5 minutes" in the `project_commands` default. It is replaced by the `sync` bullet in *Reference*: the template sets 5 minutes and a definition without `sync` gets 10.
   - The protected-path list now matches `PROTECTED_PATHS` in `src/factory/agents/domain/write_paths.py`.
   - I rewrote the file's paths so that the name check passes: `factory/features/<feature>` and `<project>/factory/agents/`.

   No rejected options to name; this story adds nothing to `docs/decisions.md`.

   Cross-read and found current:
   - `docs/operator-guide/stops.md`, `health.md`, `records.md` and `README.md`: their links to this page resolve.
   - `docs/project-guide/style.md` and `docs/project-guide/work.md`: their references to this page resolve.

   Stale text I noticed and did not touch, because it is unrelated to this story:
   - `docs/operator-guide/records.md` line 30 holds a long version history of the records contract. It is also a "since" note that style rule 1 forbids, for the story that rewrites that file.
   - `uv run factory-check-story` prints a "Bytecode compiled" line on stderr in some environments. That is why the example calls `factory-check-story` directly.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (13.0 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/operator-guide/pipeline.md` and `docs/checked-documents.txt`. I read it against the work item, `docs/project-guide/style.md`, `docs/project-guide/glossary.md`, `src/factory/pipeline/domain/pipeline_definition.py`, `src/factory/agents/domain/write_paths.py`, `src/factory/pipeline/application/stage.py` and `src/factory/machine/application/stage_environment.py`.

   The facts are true of the code:
   - the reserved names `human`, `factory` and `question`
   - checks and reports must name project commands
   - `acceptance_stage` needs a stage with a role
   - the defaults 60/40/10/2/2
   - `round_cap` defaults to none
   - `next` defaults to empty
   - an approval stage has no role
   - `write_paths` may not be empty
   - the protected paths match `PROTECTED_PATHS`
   - `sync` falls back to 10 minutes
   - the lease example adds up (40+10+10+10=70>60)

   Criterion 2 holds. Every name, setting and rule of the old file is still in the new text or in *Reference*. The one row dropped on purpose (`sync` in the `project_commands` default) is named in entry 5 and is covered by the `sync` bullet. The links from `health.md` and `records.md` to "The pipeline definition" and the other kept headings still resolve. `docs/checked-documents.txt` lists the file, and the factory's `make documents` was `documents ok`.

   Findings:
   1. `docs/operator-guide/pipeline.md`, several lines: glossary words are not linked at their first use, which breaks criterion 1 and style rule 3. The words are "story" l.3, "stops" l.33, "write paths" l.41, "approval stage" and "rounds" l.50, "stalls" l.109, "crashes" l.110, "acceptance" l.111, "claim" l.130, "work item" l.141, "stage environment" l.146, and "feature" and "backlog" l.150. Fix: link each at its first use to `../project-guide/glossary.md`, as l.7 and l.30–31 already do.
   2. `docs/operator-guide/pipeline.md` l.155: step 2 shows `factory-check-story factory/features/F0001-example/backlog/F0001-S0001-example-story.md` as an indented code block. It is neither a runnable `console` example nor marked for the VM, GitHub or a model, which the Description requires. Fix: put the commands of the example at l.161–171 under the steps as indented `console` blocks (create the story, then run the check, with its output). Or drop the bare block and point step 2 at the runnable example.
   3. `docs/operator-guide/pipeline.md` l.181, exit status row 2: one sentence of about 35 words with two parentheses breaks style rule 2 (about 25 words, at most one parenthesis). Fix: split it into one sentence per cause: no path (it prints the usage line); `factory/story-form.md` unreadable; a missing or non-UTF-8 file, which prints `cannot read <path>: <reason>`.

   Rejected as findings:
   - `python -m factory.entry.check_story` (l.159) names a module, but it is a command the operator runs, and criterion 2 keeps it.
   - The sync bullet's "the container that prepares the tools after a checkout" matches `_SYNC_SCRIPT`, which runs the checkout and then `make sync`.
   - The l.86 sentence is about 27 words, which is within "about 25".
8. factory: started docs-only as vm.
9. documenter: Round 1: fixed the reviewer's three findings in `docs/operator-guide/pipeline.md`. `make documents` ends with `documents ok (13.0 s)`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/pipeline.md`:
     1. Glossary links at first use, to `../project-guide/glossary.md`: story, stops, write paths, approval, rounds, stalls, crashes, acceptance, claim, work item, feature, backlog and stage environment. The link for write paths now sits in the rules list, where the term first appears. I removed the later link in the *Reference* table. I did not add a separate link for "approval stage", because `approval` is already linked at its first prose use.
     2. Step 2 of "Checking a story before it starts" no longer shows a bare, unrunnable command block. It now points to the runnable `console` example below it, which I ran earlier. The sentence that introduces the example now says "The example builds".
     3. Exit status 2 is split into one sentence per cause: no path (the usage line), an unreadable `factory/story-form.md`, and a file that is missing or not UTF-8 (`cannot read <path>: <reason>`).

   Cross-read and found current: the earlier cross-read from round 0 stands. `stops.md`, `health.md`, `records.md` and `README.md` link to headings I kept.

   Stale text I noticed and did not touch, because it is unrelated to this story: `docs/operator-guide/records.md` line 30 carries a long version history that style rule 1 forbids. That belongs to the story that rewrites that file.

   No rejected options to name; this story adds nothing to `docs/decisions.md`.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (13.1 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 of the docs review. I read `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/operator-guide/pipeline.md` and `docs/checked-documents.txt`, against the work item, `docs/project-guide/style.md` and `docs/project-guide/glossary.md`. I also checked it against `src/factory/entry/check_story.py` (the usage text, `cannot read <path>: <reason>`, `_FAILURE = 2`), `src/factory/agents/domain/write_paths.py` (`PROTECTED_PATHS`), `factory/pipeline.yml` (the `not_read` line and `sync: {time_limit: 5}`) and `pyproject.toml` (the `factory-check-story` script).

    The three findings of entry 7 are fixed:
    - The glossary links were added at first use for story, stops, write paths, approval, rounds, stalls, crashes, acceptance, claim, work item, feature, backlog and stage environment.
    - Step 2 of "Checking a story before it starts" now points to the runnable `console` example. No bare command block is left.
    - The exit status 2 row is split into one sentence per cause.

    Criteria 2 to 4 still hold:
    - The old text's names, settings and rules are in the new file. The `sync` row was dropped on purpose, as entry 5 says, and is covered by the bullet at l.146.
    - The protected paths match `PROTECTED_PATHS`.
    - The linked headings still exist: "The agent files" in `agent-runtime.md`, "The stop `pipeline_definition_invalid`" in `stops.md`, "The known results" in `health.md` and "The rules of the definition" in `docs/project-guide/pipeline.md`.
    - `docs/checked-documents.txt` lists the file.

    Findings:
    1. `docs/operator-guide/pipeline.md` l.210, "renumber the journal entries": the glossary word "journal" is used here for the first time and is not linked. This breaks criterion 1 and style rule 3. Fix: link "journal" at l.210 to `../project-guide/glossary.md`, as l.141 does for work item.

    Rejected as findings:
    - The tense mix in the l.178 table cell ("There was no path, and it prints the usage line"): no style rule covers it.
    - The inline `python -m factory.entry.check_story` at l.156: entry 7 already rejected it, and the reason still holds.
    - `attempts_cap` and `round_cap` at l.52, l.109 and l.122 are key names in code, not prose uses of the glossary words.
