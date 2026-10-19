# Docs curation, 2026-10-20

A curator's review of the six documents: `README.md`, `docs/operator-guide.md`, `docs/project-guide/` (the index and 8 domain files), `docs/decisions.md`, `docs/operator-playbook.md` and `CLAUDE.md`. I read every document in full except the domain files of the project guide, which I sampled. I checked the claims against `src/factory`, `factory/pipeline.yml`, `template/`, `demo/`, the `Makefile`, `pyproject.toml` and git history, at `d20f20a8` (2026-10-20 00:12). `make documents` passes today (`documents ok`).

This report does not repeat what F0032 (mutation testing keeps only its sweep form) already plans. Its S0001 docs criterion covers four things: *Mutation testing* and *The report of a mutation run* in `processes-and-checks.md`, the index line of that file, *Mutation testing by sweep* in the operator guide, and the new decision entry with its two back-references. Its human's change 2 covers the `make mutants` sentence in `CLAUDE.md`'s *Checks*. Where F0032 leaves a gap, the finding says so.

## Overall judgement

The documents are accurate in detail. Spot checks held: the defaults, caps, stop table, stall reasons, preflight items, contract version, agent table and test paths all match the code. But they are written as a build record more than as a reader's guide. The two opening paragraphs, many dated provenance notes and planning codes, and a decision log with no index make it slow to find the current rule. A few passages went stale this week: the template now runs under the guard, `factory/v1/` is gone, and v2 is retired.

Counts: **7 high, 13 medium, 10 low.**

## Findings, ranked by reader impact

Format: **where**, what is wrong, why it matters, the smallest fix. "Owner" names the document that should hold the fact when two documents hold it.

### High

**H1. `docs/operator-guide.md:917`: stale, and contradicted by the code.**
It says a project made from `template/`, and the todo demo, "do not run under the guard as they are": their `licenses` recipe and coverage are said to write at the checkout's root, and "until then its `make check` ends with `Permission denied`". Commit `1936d62a` fixed both. `template/Makefile:75-78` and `demo/todo-service/project/Makefile:75-78` write `.reports/licenses-requirements.txt`, `demo/todo-service/project/pyproject.toml:103` sets `data_file = ".reports/.coverage"`, and `template/factory/pipeline.yml:10` and the demo's `pipeline.yml:11` name `tool_paths`.
*Why:* an operator who starts a project from the template is told to make a fix that is already made, and to expect a red `make check` that does not happen.
*Fix:* replace the paragraph with two sentences. The template and the todo demo keep their tools' files under `.reports/` and name their `tool_paths`. A project whose tools write elsewhere at the checkout's root moves those files into a tool path folder the same way.

**H2. `README.md:3`: the newcomer's first paragraph is a build inventory (2,988 characters on one line).**
It says the repository "is under construction" and that "what is built so far is the groundwork the pipeline will run on". It then lists some 30 parts and dated observations ("the probe of 2026-10-17", "observed on 2026-10-18"). Since the handover of 2026-10-18, v1.1 builds itself end to end, so "groundwork" is stale.
*Why:* a newcomer cannot tell from it what the factory is or whether it works. This is the document's one job (`CLAUDE.md:52`).
*Fix:* three or four sentences: what the factory does, that v1.1 builds this repository itself since 2026-10-18, and where to go next. The history already has its entry in the decision log (*factory-rf is built by v1.1 since the handover*). Owner of the inventory: none; `docs/project-guide/README.md` already maps each part.

**H3. `docs/operator-guide.md:3`: the same inventory again (2,882 characters on one line), almost word for word as `README.md:3`.**
It also tells the operator that "the documenter stage extends this from each story's docs criterion", which is for agents.
*Why:* the operator's guide opens with the build history instead of saying what the guide covers and where each task is. The guide has 1,468 lines and no contents list.
*Fix:* two sentences (who the guide is for, and that the image is the usual way to run an instance), then a short list of the top-level sections. Drop the inventory and the documenter sentence.

**H4. `docs/project-guide/agents.md:268-295`: the quoted `template/factory/pipeline.yml` is out of date.**
It lacks the `tool_paths` line (and its comment) that `template/factory/pipeline.yml:9-10` has.
*Why:* an agent, or an operator, who copies the definition from the guide gets one under which every `make check` hits `Permission denied` (the kernel allows no write outside the write paths and tool paths).
*Fix:* replace the copy with a pointer to the file and one sentence on what it holds (copies go stale; this one did). Or add the two lines.

**H5. `README.md:26`: "v1's history ... lies in `factory/v1/`".**
`factory/v1/` was removed on 2026-10-19 (commit `8cd72eea`; git tracks no file under it any more, and only empty folders are left in the working copy). It is kept at the tag `planning-history-2026-10-19`. `CLAUDE.md:9` and `docs/operator-guide.md:1468` already say so.
*Why:* it sends the newcomer to a folder that is not there.
*Fix:* "... is kept at the tag `planning-history-2026-10-19`."

**H6. "Left for v2" names open gaps as planned work, but v2 is retired.**
On 2026-10-19 v2 was retired as a rewrite (factory-v2 decision 009: v1.1 evolves). The decision log does not record that. The passages:
- `docs/operator-guide.md:390`, **Left for v2.**, over a known security gap: the project commands run agent-written code as the factory's user, who can read the token file.
- `docs/project-guide/write-guard.md:113`, "(left for v2)", on what the undo cannot see.
- `docs/decisions.md:287`, the title *The project commands run as the factory's user and are left for v2*, and `:297`, "Left for v2" on the agent's writable home.

*Why:* the operator reads a known way to leak the token as something already planned. Nothing plans it now.
*Fix:* say "Open, not planned:" in all four places. Add one decision entry, *v2 is retired; what was left for v2 is open*, that names these items. Whether they become v1.1 backlog is the human's call; the documenter only records the decision once it is made.

**H7. `docs/decisions.md`: the log cannot be searched by topic, and superseded entries read as current.**
It has 140 entries in 819 lines, newest last, with no index, no numbers and no dates in the headings. `CLAUDE.md:29` tells every agent to read it before changing the architecture. Only the superseding entry ever says "this supersedes ...". The old entry carries no mark:
- `:13` *No `mutants` target, no mutmut* reads as the current rule. It is superseded by `:351`, which is superseded by `:800`, which is superseded by `:813`.
- `:335` *The four documents are checked by a command, outside `make check`* still names `docs/project-guide.md`, a single file. It is superseded for the docs stage by `:343` and for the guide's layout by `:685`, and carries no mark.
- `:351` and `:800` do carry "Superseded by" lines. That is two entries out of five chains.

*Why:* an agent that greps the log for a topic finds the oldest rule first and has no sign that it is dead.
*Fix (smallest):* put a `Superseded by *<title>*.` line under each superseded heading: `:13`, `:335`, and the two F0032 will add to. The index is structural improvement S2.

### Medium

**M1. `docs/operator-guide.md`: one stop is described in up to three tables.**
- *The stops you will see here* (`:417-426`), six rows.
- *The stops* (`:629-645`), all 15 rows. This is the one `make documents` pins.
- *The stops of the tick* (`:834-839`), four rows.

`checkout_restore_failed` is described at `:423`, `:632` and `:839`, and `pipeline_definition_invalid` at `:424`, `:633` and `:837`. Each also has a section of its own (`:798`, `:820`).
*Why:* an operator looking up a stop does not know which table is complete. The three wordings drift (`:423` only says "As there").
*Fix:* *The stops* owns the stop id, its destination and what you do. Replace the table at `:417-426` with one sentence that points there. Keep at `:834` only the fact the main table lacks: the tick does not touch the checkout while the stop stands.

**M2. `docs/operator-guide.md`: implementation names an operator does not need.**
About 25 lines name classes and modules. Examples: `TimestampedFactoryLog` (`:515`), `PatientRuns` (`:233`), `machine_extras` (`:430`), `StopService.post` (`:683`), `AcceptanceReader` (`:1189`), `HandOverHandler` and `factory.application.handlers.hand_over` (`:1195`), `SplitByWorkItemKind` (`:1210`), `AcceptanceMerged`, `AcceptanceClosed`, `NOT_YET_HANDLED` (`:1376`), and `DuplicateHandler` and `PullRequestLookupHandler` (`:1395`).
*Why:* they make the guide longer and tie it to refactors. The project guide already owns these names (`watching.md:94-96`, `:117`).
*Fix:* drop them from the operator guide and keep only what the operator sees: log lines, comments, commit subjects, stop ids.

**M3. `docs/operator-guide.md:1376-1378`: a hypothetical case written into the current rule.**
"Should a future kind have none, the event leads to this:" is followed by a one-sentence paragraph that does not finish the thought.
*Why:* it reads like a broken paragraph, about a case that cannot happen today (`NOT_YET_HANDLED` is empty).
*Fix:* delete from "Should a future kind" to the end of `:1378`. `watching.md:96` already holds that rule for agents.

**M4. `docs/operator-guide.md`: history where the operator needs the current rule.**
- "Morning observations" with the planning ids WE3.1, WE3.3 and WE3.4 (`:192-210`, `:385`), and "treat it as the morning observation" (`:307`, `:415`, `:503`).
- "questionnaire 1, Q21" (`:322`) and "decision 008 of factory-v2" (`:7`).
- "the five of before" (`:109`), "as before" (`:214`, `:262`, `:1452`), "The token used to be a compose secret" (`:364`).
- "seen at the tiny story of 2026-10-18" (`:392`, `:708`), "(F0019-S0004 showed it)" (`:1370`), "(F0012-S0017)" (`:619`), "the probe of 2026-10-17 ..." (`:307`, `:415`, `:481`).

*Why:* the guide is about what the factory does now. Codes like WE3.3 and Q21 point into planning records the reader does not have. History belongs in the decision log (`CLAUDE.md:52`), which already holds most of these reasons (for example *The token is a bind mount ...* at `decisions.md:411`).
*Fix:* rename "Morning observations" to "Checks on a running instance" and drop the WE ids. Delete the provenance notes in parentheses. Where a "used to" sentence explains a rule, keep the rule and point to its decision entry.

**M5. `docs/project-guide/README.md:11-19`: the index misses six modules.**
They are `factory.application.dispatcher` (the dispatcher, described at `watching.md:84-96` but not indexed), `factory.domain.tick_status` (`ERROR_CAP`), `factory.adapters.preflight_stamp_file`, `factory.entry.health` (`factory-health`), `factory.application.project_agents` (described in `agents.md`) and `factory.application.provider_limits` (described in `stages.md`). I checked each against every module under `src/factory`.
*Why:* an agent finds where a module lives through the index (`CLAUDE.md:3`), and a missing name means reading every file.
*Fix:* add each module to the "It also names" list of the file that describes it: `watching.md` for the dispatcher, tick status, stamp file and health entry; `agents.md` for project agents; `stages.md` for provider limits. Pinning this is structural improvement S4.

**M6. Planning codes and v1 feature ids used as pointers, with nothing left to resolve them.**
- The requirement numbers R3 to R34: 12 in `CLAUDE.md`, 35 in `decisions.md`, 13 in the guide files.
- WE, L, Q and "kept thing n" codes: 37 in `decisions.md` and 4 in the guide, for example `watching.md:221` "(R28, kept thing 12)".
- v1's feature ids F0001 to F0017 used as references: the table *Which feature uses which operation* (`git-and-hosting.md:181-188`, F0004 to F0008), "(F0008)" at `watching.md:117`, and "F0008's tests" at `project-guide/README.md:51`.

Their sources left the tree on 2026-10-19 (the tag `planning-history-2026-10-19`). Example ids such as `F0001-S0001` are fine.
*Why:* an agent cannot follow them, and the house rule is that an id comes with its short name.
*Fix:* in the guide files, replace each with the plain name of what it refers to. The table at `git-and-hosting.md:181-188` could name the domain ("the undo", "the stage's preparation", "the tick") instead of a feature. In `decisions.md`, add one sentence to the header saying where R-numbers, WE codes and F0001 to F0017 are defined (the tag). In `CLAUDE.md`, the R-numbers can stay, as they are the human's file; the same header sentence covers them.

**M7. `docs/operator-playbook.md:152-200`: *What changed against the draft* is revision history (49 lines, a quarter of the file).**
It is written in review-aid codes (W3, M10, S1, U2, P3, Q6, L) that no reader of `docs/` can resolve. Also `:5`: "Once the human accepts it, it lives at `docs/operator-playbook.md`, and `CLAUDE.md`'s *Docs* names it". Both are done (`CLAUDE.md:52`).
*Why:* the playbook is read at each stop; the changelog is noise there.
*Fix:* move the section to `planning/` (the human's) or the night log. Shorten `:5` to its last two sentences. The playbook's rules are the human's, so this is a human edit, or a story whose docs criterion names the playbook.

**M8. `docs/operator-playbook.md:34`: stale.**
"F0031 (no stage runs mutation testing) takes it out of the acceptance reviewer's text; until it is merged, `CLAUDE.md` already says so." F0031 is merged and accepted (`9d7a75ea`; `factory/features/F0031-*/done/`).
*Fix:* keep the first two sentences of the paragraph and drop the rest.

**M9. `docs/operator-playbook.md:107` and `:115`: they will contradict the `Makefile` once F0032 lands, and F0032 does not name the playbook.**
Both say `make mutants` "now removes nested repositories" under `mutants/` when it exits. F0032's new recipe (its human's change 1) drops that `find ... .git` trap and removes `mutants/` before each run instead. S0001's docs criterion lists four documents and not the playbook, and no stage keeps the playbook (`CLAUDE.md:52`).
*Fix:* add the playbook to F0032-S0001's docs criterion before it starts, or make it a human edit with change 1: "`make mutants` now starts from an empty `mutants/`". The same edit can give `:102-104` the sweep's command, `make mutants MODULES=<modules> MUTANTS_SECONDS=<s> MUTANTS_CHILDREN=2`.

**M10. `README.md:12`: a 1,300-character paragraph that lists the seven commands with their exit statuses.**
It tells the newcomer to "run `uv run factory-run` (with the settings in the environment ...)". But the checkout is always `/work/checkout` and the state directory `/state` (`operator-guide.md:48`), so an instance runs in the image (compose), not from a development clone.
*Why:* a newcomer who follows it gets a refused start. The exit-status details are already in the operator guide (`:56`, `:407`, `:1158`).
*Fix:* a seven-row table, one phrase per command, and one sentence: "An instance runs in the container: see *The container: compose, entrypoint and health check* in the operator guide." Owner of the exit statuses: the operator guide.

**M11. `README.md:16-22`: *Where to look next* does not name `docs/operator-playbook.md`, the fifth document (`CLAUDE.md:52`).**
*Fix:* one bullet: "`docs/operator-playbook.md`: how the human runs the factory day to day."

**M12. `docs/decisions.md:545-554`: the handover entry says v1's files "moved to `factory/v1/`", with no line for their removal on 2026-10-19.**
*Fix:* one line: "On 2026-10-19 `factory/v1/` was removed with the planning history; both are kept at the tag `planning-history-2026-10-19`."

**M13. `docs/operator-guide.md:392`: a paragraph on the container's init (`init: true`, tini, catatonit, zombies after a killed run) stands under *The hosting-service token*.**
*Why:* an operator who sees `<defunct>` processes will not look under the token's section.
*Fix:* give it a `###` heading of its own, *The init*, inside the same `##` section. `:214` cites "The container: compose, entrypoint and health check" for it, and that citation stays valid.

### Low

**L1. `docs/operator-guide.md:703`: the example of a report stopped at its time limit is `` `mutants`: 1718/1858 mutants ... ``.**
No stage runs `mutants` now. F0032 leaves the suffix but not this example. *Fix:* use `test` or `duplicates` as the example.

**L2. `docs/operator-guide.md:84`: "The recipe stops mutmut after 540 s (`MUTANTS_SECONDS`), so the largest runs end `partial`."**
This becomes false with F0032 (no stop unless asked, and no `partial`). The section is F0032's to rewrite, but its criterion does not name this sentence. *Fix:* make sure F0032-S0001's documenter drops it; the intake can add it to the criterion.

**L3. `docs/operator-guide.md:76`: "calls three targets: `check` ..., `lint` ... and `test`".**
The factory calls the project commands its pipeline definition names. Three is the default, and factory-rf's definition names six (`factory/pipeline.yml:9-15`). *Fix:* "calls the project commands of its pipeline definition (by default `check`, `lint` and `test`)".

**L4. `docs/operator-guide.md:44`: "A blank value of the three optional variables above counts as unset."**
Twenty rows up, "the three" is not clear. *Fix:* name them.

**L5. `docs/operator-playbook.md:86`: "Podman needs its restart service".**
`operator-guide.md:499` says that on Windows the service cannot be enabled and the operator restarts the instance by hand. *Fix:* "Podman on Windows: start the machine and the instance by hand (operator guide, *Podman: the restart*)".

**L6. `docs/project-guide/processes-and-checks.md:31`: `#### Known results` stands directly under `## Project commands`.**
It skips a heading level, so outlines nest it wrongly. *Fix:* `###`. F0032 edits the same file elsewhere, so put this after F0032 to avoid a conflict.

**L7. "gate" for the `check` command (`operator-guide.md:76`, `processes-and-checks.md:45` and `:121`, `CLAUDE.md:60`).**
The glossary renamed v1's "gate" to approval (`agents.md`, *Replaced from v1*), so the word now means two things. *Fix:* "the full check" in the docs. `CLAUDE.md` is the human's file.

**L8. `factory/pipeline.yml:5` and `:19`: comments in v1's words ("v1's `max_attempts`", "v1's lanes").**
This goes against `CLAUDE.md:10`. It is the human's file, so it is a human's change, not a docs story.

**L9. `docs/operator-guide.md:7`: the rule rests on "decision 008 of factory-v2", a record the operator does not have.**
*Fix:* state the rule alone. The reason can go into the decision log.

**L10. `docs/decisions.md`: the entries come in three forms.**
Five seed entries have no date, 98 are prose after a `Date:` line, and 38 use `- Decision:` / `- Why:` / `- Rejected:` bullets. *Fix:* use the bullet form for new entries; leave old entries as they are.

## Larger structural improvements (at most five)

What pins the documents today:
- `make documents` (`factory.domain.documents.check_documents`, run by `python -m factory.entry.check_documents`) checks only the four paths in `DOCUMENT_PATHS` and the guide files beside the index.
- The operator guide must keep the headings *Install*, *Configuration* and *The stops*, plus one table row per stop in `STOP_TABLE` with the id in backticks and its destination in words.
- The project guide index must keep *Kill points* and *Fault-injection paths*, plus one row per `KILL_POINT_CASES` id and per `FAULT_PATHS` test name.
- Every checked file must avoid the words in `GLOSSARY_FORBIDDEN` and the phrases in `REPLACED_PHRASES`, except inside a section titled exactly *Replaced from v1*.
- The decision log must only have sections.
- The tests that touch documents (`tests/domain/test_documents*.py`, `tests/entry/test_check_documents*.py`, `tests/document_texts.py`) use texts they build themselves, so no test reads the real documents. Moving text inside the documents breaks no test; `make documents` is the gate.
- Nothing checks the "see *X*" cross-references between sections.

**S1. One stops reference and an operator guide without internals.**
Add a contents list at the top. Merge the stop material into *The stops*: one table, then one subsection per stop in the table's order. That material is now in `:417-426`, `:625-695`, `:798-853` and `:1393-1403`. Move the internals named in M2 and the failure-mode internals (for example `:1237-1241` and `:1357`) to `watching.md`.
*Cost:* about 250 to 350 lines move or merge, and about 40 quoted cross-references ("see "The stops of the tick"") must follow the new titles, with no checker to catch a miss. Pinned: the three section names, the 15 stop rows and the glossary words. The guide shrinks from 1,468 lines to about 1,100.

**S2. A decision log with an index and a status on every entry.**
- An index at the top, grouped by the project guide's domains (git and hosting, processes and checks, agents, write guard, work items, costs, stages, watching), each line a title.
- A line under each heading: `Status: current`, `superseded by *X*` or `open`.
- The header sentence of M6.

Keep one file and keep the titles. Other documents cite entries by title, and `CLAUDE.md:29`, `CLAUDE.md:58` and the shipped agent texts name `docs/decisions.md` by path. So reject a split into `docs/decisions/`.
*Cost:* about 150 lines of index plus 140 status lines, and nothing moves. Pinned: only "has sections". A later check could require a status line under every heading: a code story in `documents.py` and `tests/domain/test_documents*.py`.

**S3. A README of about 40 lines for the newcomer.**
What it is, the status in two sentences, the development loop (`uv sync`, `make check`), "an instance runs in the container", a table of the commands, and the five documents with their readers.
*Cost:* the three long lines (`:3`, `:12`, `:14`) become about 25 short ones, and the inventory is dropped. Pinned: only the glossary words, and `--follow` must stay inside *Replaced from v1*.

**S4. The project guide index pinned to the package.**
A structural test that every module under `src/factory` is named in `docs/project-guide/README.md`, and every module named there exists. It would fail today on the six modules of M5.
*Cost:* a docs story first (add the six names), then a test-only story: about 30 lines in a new `tests/test_project_guide_index.py` (the tester's). It reads the source tree, so it needs `[tool.mutmut]`'s list of left-out structural tests in `pyproject.toml`, which is a human's change. Doing it in `documents.py` instead would need a new input to `check_documents`, which today takes only texts, so a test is cheaper.

**S5. The playbook trimmed and checked like the other documents.**
Remove its changelog (M7, 49 lines) and its dated provenance. Then add `docs/operator-playbook.md` to the wording check, as a guide file is checked today: forbidden v1 words and replaced phrases only.
*Cost:* about 50 lines removed, which is the human's edit, because the playbook's rules are the human's. Then a code story: `documents.py` (a fifth path, checked for wording only), `factory.entry.check_documents` (which files it reads), `tests/domain/test_documents*.py`, `tests/entry/test_check_documents*.py` and the builders in `tests/document_texts.py`. Today the playbook has no forbidden word, so the check would pass at once.

## How I would cut the fixes into documenter stories

Each story below changes only `README.md` and `docs/*`, the documenter's write paths, and fits one documenter run inside the 40-minute `time_limit`. Each docs criterion names the exact lines, because the documenter works from that criterion alone. They are documents-only stories, so the pre-check of playbook section 2 still applies. Run them one at a time, after F0032-S0001 is merged: it edits `processes-and-checks.md`, the index, the operator guide's mutation section and `decisions.md`, and running them later avoids merge conflicts in those files.

1. **The operator guide matches the template, the demo and the pipeline definition**: H1, L1, L3, L4. Four passages in the operator guide.
2. **The README tells a newcomer what the factory is and where to go next**: H2, H5, M10, M11 (S3 if the human wants the full rewrite). `README.md` only.
3. **The project guide names every module and no planning code**: H4, M5, the guide part of M6, L6. Four guide files and the index.
4. **The operator guide opens with what it covers and says the current rule**: H3, M3, M4, M13, L9. Operator guide only, about 20 passages.
5. **The decision log marks what is superseded and where its codes come from**: H7, M12, the header sentence of M6. `decisions.md` only. The full index of S2 is a second story of its own, since it touches 140 headings.
6. **Open gaps are named as open**: H6. It needs the human's decision first (what v2's retirement means for each gap); then the operator guide, `write-guard.md` and one new decision entry.
7. **One stops reference**: M1 and M2, which is S1. The largest; split it into "the stop tables become one" and "the internals move to `watching.md`" if a pre-check finds it over 40 minutes.

Not documenter stories:
- M7, M8, M9 and L5 are in the playbook, and no stage keeps it unless a docs criterion names it. Fold M9 into F0032-S0001's docs criterion before it starts. Make the rest one human edit, or one story whose criterion names the playbook.
- L7 in `CLAUDE.md` and L8 in `factory/pipeline.yml` are human's changes.
- S4 and S5's check are code and test stories: the coder writes `src/factory`, the tester writes `tests/`.

## Method notes

- I ran `uv run --offline python -m factory.entry.check_documents` once (result: `documents ok`). `uv` rebuilt the editable `factory` package inside the git-ignored `.venv`. No tracked file changed.
- I did not open `image/secrets/`, and used no network, no sub-agent and no container. My temporary folder `C:/Users/pasca/AppData/Local/Temp/curate` is removed.
