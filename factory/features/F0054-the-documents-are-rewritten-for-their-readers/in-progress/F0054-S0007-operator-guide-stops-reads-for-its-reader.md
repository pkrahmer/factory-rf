---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 615
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T01:07:22.774460Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T01:01:31.999464Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T01:01:32.006481Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T01:01:46.356028Z'
  stage: intake
  run: b042b84a37d0422eba00902f2941d37f
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T01:01:51.170541Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T01:07:17.199797Z'
  stage: docs-only
  run: 1598991e93134c2cac63d9b5a3a148bf
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T01:07:22.774460Z'
  stage: docs-review
---

# The operator guide's the stops reads for the operator

## Description

`docs/operator-guide/stops.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/stops.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/stops.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/stops.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/stops.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/stops.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths (`docs/operator-guide/stops.md`, `docs/checked-documents.txt`); it changes only documents the documenter may write, with no code, test or agent file.
   Criteria: criteria 1 to 4 are checkable against the files (style rules and the old-versus-new comparison by the reviewer, `make documents` printing `documents ok`, links resolving). The Interface states no behaviour or rule beyond the document list, so no failing side is missing.
   Smoke test: `grep -cx "docs/operator-guide/stops.md" docs/checked-documents.txt` is runnable, and its `Expect: 1` can be checked against the output. It runs no pytest.
   Docs criterion: criterion 6 says "as criteria 1 to 4", so it names what the reader must know (the stops, from the code) and dictates no sentences.
   Architecture: documents only; it matches the docs route and the CLAUDE.md docs split.
   Scope: it is one of the 22 per-file stories of F0054 (S0007), and `decisions.md` is untouched, which is outside the Out of scope list.
4. factory: started docs-only as vm.
5. documenter: Changed files:
   - `docs/operator-guide/stops.md`: rewritten for the operator. Each stop section now reads as what you see, what it means, what you do. Numbered steps are used for tasks, and the end of the file has a *Reference* section.
   - `docs/checked-documents.txt`: added the line `docs/operator-guide/stops.md`.

   The Interface requires the headings that other files link to, so I kept them: "The stops" (the document check requires it), "The stop records on main", "A stall: the stall note", "The factory's own questions", "An event that keeps failing", "The stop `pipeline_definition_invalid`", "The stops of the tick" and "Stops that cannot be done". The stop table keeps every `STOP_TABLE` id in backticks, with its destination.

   Code checked and corrections made:
   - The old text said the stall causes are "the ten listed below". `_STALL_SENTENCES` in `src/factory/hosting/domain/post_texts.py` has nine, and the old list also had nine. The new text says nine, with a table of them in *Reference*.
   - I took the cause wording from `post_texts.py`: "the agent run reached its time limit" and "merging the main branch conflicts and the merge was aborted".
   - I read nothing else in the code. The other claims were carried over from the old file unchanged.

   Moved to *Reference*:
   - the nine stall causes;
   - the rules that shape a failed push's reason;
   - the wording of a probe of `main` that fails without printing anything.

   Removed on purpose:
   - The paragraph on the 2026-11-04 outage, with its date and its link to `planning/outage-2026-11-04.md`. Style rule 7 forbids history, and `planning/` is the human's. The behaviour it described is kept under "During an outage of the hosting service". I dropped "now", "as before" and "Only the line is new", and I did not add a pointer to the decision log, because I found no entry that names this outage.
   - Example ids such as `F0001-S0001`, replaced by `<id>` placeholders (rule 1).

   Other changes:
   - I wrote `<project>/factory/stage.Containerfile`, because `make documents` flagged the bare path as missing in this repository. This is the placeholder prefix the style page requires for a path in the project the factory runs on.
   - I split the old "The stops of the tick" prose into the subsections `fetch_failed`, `checkout_restore_failed`, "A work item file that cannot be read", "The low disk" and "The preflight in the tick".
   - I added a link from the first use of each factory word to the glossary: stop, tick, work item, journal, claim, role, approval, take, write paths, stall, crash, pipeline definition, rounds and instance.

   The file has no `console` blocks. Its blocks are factory log lines, comment texts and a table, all `text`, so none is run.

   `make documents` ends `documents ok (11.6 s)`. I did not run `make check`, because I changed only documents.

   Cross-read against the file: the links into `stops.md` from `health.md`, `pipeline.md`, `agent-runtime.md`, `work-items.md`, `install.md`, `machine.md`, `site.md`, `README.md` and the project guide. Every heading they cite still exists. I did not read the cited files in full.

   Stale text I noticed and did not touch:
   - `docs/project-guide/shared.md:99` and `docs/project-guide/README.md:20` refer to the section *The stops* by name. That is still correct.
   - `docs/decisions.md:1560` mentions *Replaced in v1.2* in the operator guide index. That is unrelated to this story.

   Findings for the coder: none.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (12.1 s)
6. factory: started docs-review as vm.
