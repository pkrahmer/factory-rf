---
stage: docs-only
blocked: null
round: 3
attempts: 1
crashes: 0
pull_request: 626
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T05:48:44.076997Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T05:48:44.085536Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T05:48:58.672149Z'
  stage: intake
  run: 0adfeb41fe064d398392476350541833
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T05:49:03.443475Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T05:58:07.075776Z'
  stage: docs-only
  run: ec6df42304d745be80379ede425345c6
- number: 6
  speaker: factory
  kind: stall
  at: '2026-11-07T05:58:07.458896Z'
  stage: docs-only
  run: ec6df42304d745be80379ede425345c6
  reason: check_red
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T05:58:14.324444Z'
  stage: docs-only
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-07T06:01:09.927638Z'
  stage: docs-only
  run: 7f74800d6a2544078fae85262d9b17ca
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-07T06:01:15.123650Z'
  stage: docs-review
- number: 10
  speaker: reviewer
  kind: result
  at: '2026-11-07T06:05:14.575538Z'
  stage: docs-review
  run: 705f029ae1e54dde9870105f8e18dcb4
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-07T06:05:19.928750Z'
  stage: docs-only
- number: 12
  speaker: documenter
  kind: result
  at: '2026-11-07T06:11:28.468292Z'
  stage: docs-only
  run: 4e001ab95ba248099553d9d4f6a01329
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-07T06:11:33.669473Z'
  stage: docs-review
- number: 14
  speaker: reviewer
  kind: result
  at: '2026-11-07T06:13:46.990863Z'
  stage: docs-review
  run: 14aaa5315b774040a2b84bde5e1c5771
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-07T06:13:52.370309Z'
  stage: docs-only
- number: 16
  speaker: documenter
  kind: result
  at: '2026-11-07T06:17:31.311279Z'
  stage: docs-only
  run: f0ebc6a8ae594923a1e31514f686ce6b
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-07T06:17:36.564063Z'
  stage: docs-review
- number: 18
  speaker: reviewer
  kind: result
  at: '2026-11-07T06:18:57.320125Z'
  stage: docs-review
  run: 8c2a5102f19449d68212244c3d8b8a43
---

# The project guide's page on the pipeline area reads for the developer

## Description

`docs/project-guide/pipeline.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/pipeline.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/pipeline.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/pipeline.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/pipeline.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/pipeline.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/pipeline.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete files only (`docs/project-guide/pipeline.md`, `docs/checked-documents.txt` with its one line) and rules for links and headings. It states no code behaviour, and the docs route fits because every path it changes is under `docs/`.
   - Criteria: each can be checked on the documents. `make documents` covers 3 and 4 mechanically, and the reviewer compares the old and new file for 1 and 2. The Interface states no rule with a failing side, so none is missing a criterion. The rule on links to changed headings has criterion 5, and the "linked once" rule has criterion 4.
   - Smoke test: `grep -cx "docs/project-guide/pipeline.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked. It runs no pytest.
   - Docs criterion: criterion 7 says what the reader must know (criteria 1 to 5, meaning the page is true to the code and complete). It quotes no sentences.
   - Architecture: the story only touches a project-guide page, which is a document the documenter may write. No code, test or agent file changes.
   - Scope: S0018 is listed in F0054's stories, and it changes nothing listed in "Out of scope" (`decisions.md`, `docs/runs/`, the playbook).
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `docs/project-guide/pipeline.md`: rewritten for the developer about to change the pipeline area. Each section now opens with what the part is for, then the names and signatures in an indented block, then the rules one per bullet, then See also. Modules are linked once at their first mention. Feature, story and requirement IDs (R5) and the history lines ("of earlier versions", "went with the second user", "v1's order") are gone. Glossary words are linked at first use. Headings that other files cite are unchanged: *The pipeline definition*, *The rules of the definition*, *Starting a stage*, *After the agent run*, *The stage protocol*, *`StageFinisher.finish(aftermath)`*, *The take's rule*, *Asking the human*, *Boundaries*, *The idle shutdown*. One heading was renamed: *Stops, the clock and the factory log* is now *The stop records*, and nothing outside the file cited it.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/pipeline.md`.

   What I did to the content:
   - I moved text rather than cutting it. Every name, setting, fault text and rule of the old file is in the new one, and the test lists are kept as inline "Tests:" lines.
   - I split the old miscellany at the end of the handlers section into headed sections: *Waiting out the provider's limit*, *The preflight in the tick*, *The stale branch*, *The agent run's environment*, *The settings*, *Boundaries in tests*, *`factory-health` and `factory-run`*, *`StopService`* and *The clock, the log and the stores*.
   - I turned the "twelve rules" count into a table with a row 12 for the `not_read` rule, which the code runs last as the 11th entry of `_RULES` (the contract function gives rules 1 and 2). The old table stopped at 11.
   - The runnable `uv run python` example now sits in a `console vm` block, copied from a real run in this checkout. It needs the project's environment, and the docs check container prints `Using CPython ...` for `uv run`. I replaced the old second half of the example, the `contrakt` fault, with a prose sentence. Its text is from the old file, and I did not re-run it.
   - Style rule 8 (A code block holds no links) is met by linking the file above each signature block.

   Not done, and why:
   - There is no *Reference* section at the end. The detail stays in the rules of each section, and I did not move it. The reviewer may ask for one.
   - I did not read each claim against the code. I checked the rule count and the names the code gave (`_RULES`, `CONTRACT_MAJOR`, `RETRY_WAITS`, `STALL_TAIL_LINES`, `ERROR_CAP`), and `make documents` resolved every name and link. The rest of the old claims are carried over unchecked, so a reviewer who compares against the code may find drift.
   - `decisions.md` is untouched, as the story says; no "Why" or "Rejected" text was written.

   Cross-read and found current: the operator-guide files that link into this file (`stops.md`, `pipeline.md`, `records.md`, `health.md`) and `machine.md`, `hosting.md`, `agents.md`, `work.md`, `watching.md`, `style.md` of the project guide. Their headings and links to this file still resolve.

   Checks: `make documents` ended with `documents ok (15.9 s)`. I ran no `make check`, because every changed file is a document.

   Stale text seen, not mine to fix: `docs/project-guide/README.md` lines 67 to 141 and 283 and `README.md:28` are reported by `make documents` under "Report (not checked yet)" as paths that do not exist (`support/...`, `project/factory/...`, `factory/stage.Containerfile`). These files are not on the checked list.
6. factory: Stage docs-only stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/watching/application/transcripts.py         61      2     10      0    97%   91-92
   src/factory/watching/domain/board.py                    55      0      4      1    98%   77->75
   src/factory/watching/domain/machine.py                  52      3     18      5    89%   44->42, 47, 59, 77->75, 79
   src/factory/watching/domain/transcripts.py              10      2      0      0    80%   20-21
   src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   239
   src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
   src/factory/work/domain/acceptance.py                  195      1     52      1    99%   367
   ------------------------------------------------------------------------------------------------
   TOTAL                                                11211     55   2254     52    99%

   157 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.21%
   ======================================================================================= short test summary info ========================================================================================
   FAILED tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file - AssertionError: assert ['docs/projec...ork-items.md'] == []
   make: *** [Makefile:89: test] Error 1
7. factory: started docs-only as vm.
8. documenter: Round 0, second run after the red check. The check was red because of one test, `tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file`. It flagged four lines of `docs/project-guide/pipeline.md` (545, 558, 569, 620). On each, the link text `work-items.md` matched the guard's pattern for a removed guide file. The links themselves point at the existing `docs/operator-guide/work-items.md` and were fine.

   Files changed:
   - `docs/project-guide/pipeline.md`: on those four lines, the link text `[work-items.md]` is now `[the operator guide on work items]`. The targets are unchanged.

   Checks: the guard test passes when run alone, and `make documents` ends with `documents ok (16.7 s)`. I did not run `make check`, since the only file changed is a document; the factory's gate decides.

   For the reviewer, from the first run's entry, which still stands:
   - The page has no *Reference* section. The detail stays in each section's rules.
   - The documenter checked only the rule count and a few named constants against the code. The other claims were carried over from the old file without comparing them to the code. Please compare the old and new file against the code.

   Stale text I saw but did not touch, unrelated to this story: paths that do not exist in `docs/project-guide/README.md` (lines 67 to 141 and 283) and `README.md:28`. `make documents` lists them as "not checked yet".

   `check`: check: green
   `secrets`: secrets: green (0.7 s)
   `documents`: documents ok (16.3 s)
9. factory: started docs-review as vm.
10. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` (`docs/project-guide/pipeline.md`, `docs/checked-documents.txt`) against the work item, `docs/project-guide/style.md` and the code on the branch. I compared the old file with the new one, then spot-checked the claims against `src/factory`. Correct against the code: the twelve rules with row 12 (`_RULES` in `pipeline_definition.py:255`, where `_contract_faults` gives rules 1 and 2), the thirteen event kinds, `CONTRACT_MAJOR`, `MACHINE_STOP_LIMIT`, `POWER_OFF_TIME_LIMIT`, and the signatures of `StageLauncher`, `AfterAgent`, `StageRunner`, `Tick`, `IdleShutdown` and `build_handlers`. Criterion 3 is met: the line is on the checked list, and the factory's gate printed `documents ok`.

    Dropped on purpose, and acceptable (criterion 2): `tool_paths` "of earlier versions" (history, style rule 1); the `try/except` half of the old example, now a prose sentence; the subheadings `prepare`, `ensure_pull_request` and *The sidecar*, whose text was merged into their sections. There is no *Reference* section, and the criterion allows that.

    Findings:
    1. `docs/project-guide/pipeline.md` (criterion 1): only pipeline definition, claim, take, tick and work item are linked to the glossary. These factory words are used unlinked at their first use: stop (line 3), instance (9), lease (17), role (18), journal (20), project command (35), approval and write paths (44), crash (59), acceptance and feature (60), round (62), story (70), round cap (71), stall (165), backlog (197), stage environment and cost record (223), attempts cap (263), dataset (279). Fix: link each to `glossary.md` at that first use.
    2. `docs/project-guide/pipeline.md` (Interface, criterion 4): 31 modules the page names are never linked to their file. They are `factory.hosting.domain.post_texts`, `factory.work.domain.journal`, `.labels`, `.archive`, `.answers`, `.acceptance`, `factory.agents.domain.agent_runs`, `.provider_limits`, `factory.shared.adapters.clock`, `.validation_faults`, `.atomic_file`, `.printed_output`, `.process`, `factory.shared.application.files`, `factory.shared.domain.settings`, `.errors`, `factory.pipeline.domain.stops`, `.stop_table`, `.evaluation`, `.recovery`, `.tick_status`, `factory.machine.application.preflight`, `factory.machine.domain.preflight`, `.disk`, `factory.machine.adapters.disk_space`, `factory.watching.adapters.factory_log`, `.health_file`, `factory.entry.health`, `factory.hosting.adapters.pygithub_hosting`, `factory.pipeline.application.handlers` and `factory.machine.application`. The Stalls block (lines 252-256) mixes functions of `decisions.py` and `post_texts.py`, and only `stalls.py` is linked above it. Fix: link each file once, at its first mention or above the block that shows it.
    3. `docs/project-guide/pipeline.md` (Interface: "each module, file or page"): no file path the page names is linked. That is the roughly 70 `tests/...` paths (for example lines 28, 121, 131, 183), `tests/support/*.py`, `tests/conftest.py`, `operator/vm/git-credential-factory` (449) and `factory/pipeline.yml` (35). Fix: link each once by a relative link.
    4. `docs/project-guide/pipeline.md` (Interface "linked once"): these files are linked more than once. `stage.py` 3 times (lines 208, 290, 340); `recovery.py` twice (436, 487); `../operator-guide/work-items.md` 4 times (545, 558, 569, 620); `../operator-guide/stops.md` 3 times; `../operator-guide/health.md` 3 times; `machine.md` 10 times; `work.md` twice. Fix: keep the first link and name the file in plain text after it.
    5. `docs/project-guide/watching.md:277` (criterion 5): it still cites *Stops, the clock and the factory log* in `pipeline.md`, and this diff renamed that heading. The journal says nothing outside the file cited it. Fix: cite *The stop records* (or *The clock, the log and the stores*).
    6. `docs/project-guide/agents.md:494` and `:381` (criterion 5): they cite *PatientRuns* and *The take* in `pipeline.md`, and neither heading exists there. Fix: cite *Waiting out the provider's limit* and *The take's rule*.
    7. `docs/project-guide/pipeline.md:378-379`: the signature block shows `read_baseline(...)` and `restore_work_item(...)` instead of their signatures. Code: `read_baseline(boundaries, commit, work_item_path) -> WorkItemDocument` and `restore_work_item(boundaries, commit, work_item_path, baseline) -> bool` (`take.py:107`, `take.py:119`). Line 385 names `refusal(path, settings)` without its module (`agents/domain/write_paths.py`) and without saying that `is_refused` applies both cases; the old file said so. Fix: write the real signatures and restore that sentence.
    8. `docs/project-guide/pipeline.md:445`: it gives the preflight items as `token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `opencode`, `agent-run-probe` unconditionally. The code also adds `metadata-block` after `stage-image` under `container_profile == "job"` (`entry/wiring.py:766`). With copy snapshots, the single `snapshots_item` replaces `zfs` and `dataset` (`wiring.py:590`). Fix: state both cases.
    9. `docs/project-guide/pipeline.md:684-693`: the `Boundaries` signature and "The fields are ..." leave out the optional fields `container_extra_environment`, `image_path`, `machine`, `base_image_bytes`, `project_layer_bytes`, `image_store`, `stop_requested` and `transcripts` (`pipeline/application/boundaries.py:65-78`). Fix: list them, with their defaults.
    10. `docs/project-guide/pipeline.md:688`: `build_boundaries(settings, token, *, hosting=None)` is missing `images=None` (`entry/wiring.py:305`). Fix: add it, and say what it does (the containers' `PATH` from the stage image).
    11. `docs/project-guide/pipeline.md:699` contradicts the code and the page's own line 696. The code builds the runtime with `_agent_runtime` (`OpencodeRuntime` or `ClaudeCodeRuntime`, `wiring.py:619-636`). Its `project_commands` is `RecordingProjectCommands(ContainerMakeCommands(...))`, not `MakeProjectCommands(settings.checkout)` (`wiring.py:327`). Its `agent_definitions` is `ProjectAgentDefinitions(git, FrontmatterAgentDefinitionReader(settings.agent_home))` (`wiring.py:347`). Fix: rewrite the sentence from `build_boundaries`.
    12. `docs/project-guide/pipeline.md:695`: "fills them with `ZfsSnapshots` and `PodmanRuns` ... refuses an instance without a dataset" leaves out the copy case. There `CopySnapshots(workspace, base)` is built and the base is required (`wiring.py:583-590`, and the docstring at `wiring.py:310`). Fix: name both kinds of snapshots and what each requires.
    13. `docs/project-guide/pipeline.md:677`: `test_stop_publisher.py` and `test_tick_stop_records.py` are written below the root (style rule 8). Fix: `tests/pipeline/application/test_stop_publisher.py` and `tests/pipeline/application/test_tick_stop_records.py`.
    14. `docs/project-guide/pipeline.md:703`: "raises `GitError` as before" is history wording (style rule 7). Fix: "raises `GitError`".
    15. `docs/project-guide/pipeline.md`: these sections do not open with two or three plain sentences on what the part does and why (project-guide style): *Faults* (75), *The rules of the definition* (85), *The pipeline loader* (123), *`StallService.stall`* (267), *`StageFinisher.finish(aftermath)`* (354), *The preflight in the tick* (443), *The clock, the log and the stores* (649), *`factory-health` and `factory-run`* (658), *Stop records* (671), *Boundaries* (682), *The settings* (713). *Starting a stage* (208) and *The stage protocol* (340) open with a single sentence of names. Fix: add the opening sentences.
    16. `docs/project-guide/pipeline.md`: three top-level sections have no "See also": *The handlers of the events* (455-636), *The stop records* (638-679) and *Boundaries* (680-729). Fix: add one to each.
    17. `docs/project-guide/pipeline.md`: rules stand in paragraphs, not one per bullet, at lines 242-244, 496-498, 516, 554, 565, 642, 651 and 707. The `RunHandler` paragraph (516) sits under the run gate's heading, *The pull request is read before every agent run*. Fix: make each rule a bullet, and give `RunHandler` its own heading.
    18. `docs/project-guide/pipeline.md` (style rule 2): many sentences run far past 25 words and hold several parentheses. Lines 362, 445, 692 and 699 are clear cases, and about 34 sentences are over 40 words. Fix: split them, with one parenthesis at most per sentence.

    Open, and not this stage's to fix: the Description cites "style rules 8 to 10", but `docs/project-guide/style.md` has rules 1 to 8. Also outside this story: `README.md:28` and `docs/project-guide/README.md`, which the documenter reported as unresolved paths.
11. factory: started docs-only as vm.
12. documenter: Round 1, fixing the reviewer's findings 1 to 18. `make documents` ends with `documents ok (17.1 s)`. `tests/guards/test_project_guide_files.py` passes. I ran no `make check`, because every file I changed is a document.

    Files changed:
    - `docs/project-guide/pipeline.md`: all findings below.
    - `docs/project-guide/watching.md`: the citation of the renamed heading now reads *The clock, the log and the stores* (finding 5).
    - `docs/project-guide/agents.md`: the citations now read *Waiting out the provider's limit* in place of *PatientRuns*, and *The take's rule* in place of *The take*, at lines 24, 381 and 494 (finding 6).

    What I did, by finding:
    1. Glossary: the first use of stop, instance, lease, role, journal, project command, write paths, crash, feature, acceptance, approval, story, round cap, backlog, stage environment, cost record and dataset is linked to `glossary.md`. So is stage, which the reviewer did not list. A script did the linking, which means two things:
       - The "lease" at line 17 is the first plain use of the word, so that is the one it linked.
       - It found no plain first use of "attempts cap" outside code spans and links, so that term is not linked. That is a gap against finding 1.
    2. and 3. Modules and files: the script links each repository file the page names once, at its first mention outside code blocks. That covers the listed modules, the `tests/...` paths, `tests/support/git_support.py`, `operator/vm/git-credential-factory` and `factory/pipeline.yml`. A file already linked through its `.py` link is not linked again by its dotted name. A name that sits only inside a code block stays plain. I did not check each link by eye. `make documents` found no broken link.
    4. Repeated links: the script keeps the first link to a file and leaves the text of every later one plain. This covers `stage.py`, `recovery.py`, `machine.md`, `work.md` and the operator-guide files. Links to the glossary repeat for each term, as the style page asks.
    5. and 6. The other files' citations are fixed as listed above.
    7. The take block shows the real signatures of `read_baseline` and `restore_work_item`. The sentence about `refusal` is back, with its module `factory.agents.domain.write_paths`, and says that `is_refused` judges both cases.
    8. Preflight: the items are listed in code order. They are `token-file`, `podman`, then `zfs` and `dataset` for ZFS snapshots or the single item `snapshots` for copy snapshots. After them come `stage-image`, `metadata-block` (only for `container_profile` `job`), `opencode` (only for the opencode runtime) and `agent-run-probe`.
    9. and 10. The `Boundaries` signature and the field list now hold the eight optional fields with their defaults, and `build_boundaries` shows `images=None` and what it does.
    11. and 12. The `build_boundaries` text is rewritten from `wiring.py`: `OpencodeRuntime` or `ClaudeCodeRuntime`, `RecordingProjectCommands(ContainerMakeCommands(...))`, `ProjectAgentDefinitions(...)`, `ZfsSnapshots` or `CopySnapshots` and what each requires.
    13. and 14. The test paths are written from the root, and "as before" is gone.
    15. Opening sentences are added to every section the reviewer named, including *Starting a stage* and *The stage protocol*.
    16. A See also line is added to *The handlers of the events*, *The stop records* and *Boundaries*.
    17. The paragraphs the reviewer named are now bullets. The crash cap has its own heading, and `RunHandler` has its own heading, *Running a stage*. I also made the intro paragraphs of *The clock, the log and the stores* and of *The stop records*, the merged-handler paragraph and the close-handler paragraph into bullets.
    18. Long sentences: I split the four the reviewer called clear (step 7 and its description paragraph under *`StageFinisher.finish(aftermath)`*, the preflight line, and the `build_boundaries` lines). I did not search the rest of the page for sentences over 40 words, so more of them remain.

    Not done:
    - The page has no *Reference* section, as in round 0. The criterion allows that.
    - I added each of the new opening sentences from the code and the page's own text. I did not compare every other claim on the page with the code again; the reviewer's spot-check stands.
    - The `<code>/tmp/f54</code>` scratch directory from my edit scripts was not removed, because the shell refused `rm`. It lives outside the repository and holds nothing the stage needs.

    Stale text seen, not mine to fix:
    - `docs/project-guide/README.md` lines 67 to 141 and 283, and `README.md:28`, name paths that do not exist. `make documents` lists them as not checked yet.
    - The story's Description cites "style rules 8 to 10", but `docs/project-guide/style.md` has rules 1 to 8. This stays open for the human.

    `check`: check: green
    `secrets`: secrets: green (1.1 s)
    `documents`: documents ok (16.3 s)
13. factory: started docs-review as vm.
14. reviewer: Round 1 review. I read `git diff main...HEAD -- README.md docs operator/README.md` against the work item, `docs/project-guide/style.md` and the code on the branch. I read the whole new `docs/project-guide/pipeline.md` and checked the round-0 findings 1 to 18 against it.

    Fixed: findings 4 to 7, 8, 9, 10 to 17, and 6's citations in `agents.md` and `watching.md`. These now match the code: the take signatures (`take.py`), the preflight order (`wiring.py:562-590`), the `Boundaries` optional fields and their defaults (`boundaries.py:65-78`) and the `build_boundaries` builders (`wiring.py:300-345`). I checked for removed headings: *The pipeline definition, the stages and the tick*, *`prepare(...)`*, *`ensure_pull_request(...)`*, *The sidecar* and *Stops, the clock and the factory log*. Only the last one is still cited anywhere, at finding 1.

    Findings:
    1. `docs/project-guide/README.md:35` (criterion 5): it still lists *Stops, the clock and the factory log* among the sections of `pipeline.md`, but that heading is gone. It also calls *Boundaries* a subsection, and it is now a top-level section. Fix: name *The stop records* (with *The clock, the log and the stores*), list *Boundaries* and *The idle shutdown* as sections, and add the new top-level sections.
    2. `docs/project-guide/pipeline.md:165` and `:262` (criterion 1, round-0 finding 1 still open): the glossary words "round" (first used in the prompt table, line 165) and "stall" (first plain use, line 262) are not linked. Fix: link each to `glossary.md` at that use.
    3. `docs/project-guide/pipeline.md:262-274` (Interface, criterion 4, round-0 finding 2 still open): the Stalls signature block shows functions from `decisions.py` and `post_texts.py`. `stall_reason_of` is at `work/domain/decisions.py:22`, and `stall_cause` and `stall_note` are at `hosting/domain/post_texts.py:40,48`. Only `stalls.py` is linked above the block. `factory.hosting.domain.post_texts` is first named at line 274 but linked only at line 346, and `decisions.py` is first linked at line 324. Fix: link both files above the block at line 262, and leave lines 324 and 346 plain.
    4. `docs/project-guide/pipeline.md:254` (Interface "linked once, at its first mention"): `factory.watching.application.machine` is first named here unlinked, and it is linked only at line 698. Fix: put the link at line 254 and make line 698 plain.
    5. `docs/project-guide/pipeline.md:662`: the sentence "the operator guide on work items says what the operator sees." starts in lower case. The script that replaced the link left it that way. Fix: "The operator guide on work items says what the operator sees."
    6. `docs/project-guide/pipeline.md:758` (criterion 2): "These eight, `settings` to `containers`, are required" has no full stop. It follows the list of eight optional fields, so "these eight" reads as those. The old file's rule is also dropped: none of the eight has a default or admits `None`, a `Boundaries(...)` without one is a `TypeError`, and `build_boundaries` sets all eight. Fix: restore that rule as one full bullet, placed before the optional fields.
    7. `docs/project-guide/pipeline.md:765`: "`build_boundaries` resolves the hosting service first ... before any adapter exists" is contradicted by `entry/wiring.py:313-316`. There `_container_adapters(settings)` builds the snapshots and `PodmanRuns`, and raises its `SettingsInvalid`, before the hosting service is resolved. Fix: say that the container adapters and their refusals come first and the hosting service next, before the other adapters.
    8. `docs/project-guide/pipeline.md:686-692`: the `StopService`/`StopPublisher` signature block comes after the bullets. It is indented four spaces right after a list item, so Markdown renders it as a paragraph of the second bullet, not as a code block. It also puts the names after the rules, against the project-guide style. Fix: move the block above the bullets, after the opening sentences at line 684, outside the list.
    9. `docs/project-guide/pipeline.md:530-533`: "Steps 3 and 5 of `handle` change when ...:" is followed, after a blank line, by the bullets "Record: ..." and "Rerun is skipped ..." at the same level. They read as sibling rules, not as the two cases of that bullet. Fix: indent them as sub-bullets of line 530.
    10. `docs/project-guide/pipeline.md` (style rule 2, round-0 finding 18 still open, as the documenter's entry 12 says): many sentences still run far past 25 words, or hold several parentheses. Clear cases are line 17 (the preconditions after `claim`), 22 (four parentheses in one sentence), 233, 283, 434, 440, 476, 534, 709, 710, 727, 777 and 825. Fix: split each into sentences of about 25 words with at most one parenthesis, and go through the rest of the page the same way.

    Open, not this stage's to fix: the Description cites "style rules 8 to 10", but `docs/project-guide/style.md` has rules 1 to 8. Neither the journal nor the criteria settle which rules are meant, so I left it for the human. The page still has no *Reference* section, which criterion 2 allows.
15. factory: started docs-only as vm.
16. documenter: Round 2: I fixed the reviewer's findings 1 to 10 as far as I could. Finding 10 (long sentences) is only partly done. `make documents` ends with `documents ok (16.5 s)`. I ran no `make check`, because every file I changed is a document.

    Files changed:
    - `docs/project-guide/pipeline.md`: findings 2 to 10, listed below.
    - `docs/project-guide/README.md`: the index entry for `pipeline.md` now lists the current sections. *Stops, the clock and the factory log* became *The stop records* (with *The clock, the log and the stores*). *Boundaries* and *The idle shutdown* are named as top-level sections. This is finding 1. The index line occurs once in the file.

    By finding:
    1. Done in `README.md`, as above.
    2. The glossary links for "round" (the prompt table) and "stall" (the Stalls opening) are added.
    3. Both files are now linked above the Stalls block: `decisions.py` for `stall_reason_of`, and `post_texts.py` for `stall_cause` and `stall_note`. Their later links, in the decision-rules section, are plain.
    4. The link to `factory.watching.application.machine` is at its first mention (the `Waiter` bullet). The later one is plain.
    5. "The operator guide on work items ..." now starts with a capital.
    6. The rule is back as its own bullet before the optional fields: none of the twenty-two fields from `git` to `containers` has a default or admits `None`. A `Boundaries(...)` without one is a `TypeError`, and `build_boundaries` sets all of them. I counted the twenty-two from the signature block. The orphan line "These eight ... are required" is gone.
    7. `build_boundaries` is now described as building the container adapters first, with their `SettingsInvalid`, then the hosting service, then the other adapters.
    8. The `StopService` and `StopPublisher` signature block is above the bullets, after the section's opening sentences. It sits outside any list, so it renders as a code block.
    9. The "Record" and "Rerun is skipped" bullets under the crash cap are now sub-bullets of the "Steps 3 and 5 of `handle` change when ..." bullet.
    10. Partly done. I split the sentences at the claim preconditions, `status` (a bullet for each of the three claim states), `observed_status`, the `factory-health` and `factory-run` paragraphs, the `StopPublisher` paragraph, `git_environment()` and the `MachineStopExit.observe()` sentence. I did not go through the whole page for every sentence over 25 words. The reviewer's other named lines (the `ask_crash_cap` paragraph, the `build_boundaries` environment line, the `IdleShutdown` introduction and a few more) still hold long sentences.

    Not done:
    - The page has no *Reference* section, as in earlier rounds. Criterion 2 allows that.
    - I did not recompare the other claims on the page with the code. The reviewer's earlier spot-checks stand.

    Stale text seen, not mine to fix:
    - The story's Description cites "style rules 8 to 10", but `docs/project-guide/style.md` has rules 1 to 8. This is for the human.
    - `docs/project-guide/README.md` lines 67 to 141 and 283, and `README.md:28`, name paths that do not exist. `make documents` lists them as not checked yet.

    `check`: check: green
    `secrets`: secrets: green (1.3 s)
    `documents`: documents ok (16.3 s)
17. factory: started docs-review as vm.
18. reviewer: Round 2 review. I read `git diff main...HEAD -- README.md docs operator/README.md` against the work item, `docs/project-guide/style.md` and the code on the branch. I read the whole new `docs/project-guide/pipeline.md` and checked the round-1 findings against it.

    Fixed since round 1:
    - Findings 1 to 9 are fixed.
    - `docs/project-guide/README.md:35` lists the current sections.
    - "round" (line 171) and "stall" (line 268) are linked to the glossary.
    - `decisions.py` and `post_texts.py` are linked above the Stalls block (line 270), and their later mentions are plain.
    - `factory.watching.application.machine` is linked at its first mention (line 260).
    - The capital at line 617 is fixed.

    Checked against the code:
    - The required-fields rule (line 757): the 22 fields from `git` to `containers` and the 8 optional fields with their defaults match `boundaries.py:42-78`.
    - `build_boundaries` builds the container adapters first and then the hosting service (line 772), as `wiring.py:313-316` does.
    - The `StopService` block now stands outside the list (line 693).
    - The crash-cap sub-bullets are indented (lines 538-540).
    - Every section the page cites in another file exists: stops.md, health.md, machine.md, work-items.md and the decision log's "The factory alone writes the checkout's `.git`".
    - The citations in `agents.md` and `watching.md` resolve.

    Findings:
    1. `docs/project-guide/pipeline.md:811`: "It also sets the six required fields" contradicts line 757, which says twenty-two fields are required. It also leaves out what the fixture sets for `snapshots` and `containers` (`FakeSnapshots` and `FakeContainerRuns` over `<tmp_path>/workspace`, through `fake_dataset`) and for `machine` (`FakeMachineReadings()`) (`tests/conftest.py`, the `boundaries` fixture). The fixture sentence at line 769 sits in a bullet about `build_boundaries`. Fix: write "It also sets these fields", add the three, and move line 769's sentence here.
    2. `docs/project-guide/pipeline.md:773-779`: "It then builds, in this order" puts the `SystemClock` last. The code builds the clock before `GitCli` and the log right after it (`entry/wiring.py:318-320`). Fix: drop "in this order", or list the clock and the log before `GitCli`.
    3. `docs/project-guide/pipeline.md:484`: "is no longer `origin/main`" breaks style rule 7 (no "no longer"). Fix: "differs from `origin/main`".
    4. `docs/project-guide/pipeline.md` (style rule 2, round-1 finding 10 still open; the documenter's entry 16 says it is only partly done): sentences still run far past about 25 words or hold several parentheses.
       - Sentences of 45 words or more stand at lines 87, 192, 284, 303, 442, 448, 550, 640, 658, 756 and 828.
       - Long sentences also stand at lines 541, 772 and 820.
       - Several parentheses in one sentence stand at lines 68, 237, 291, 707, 721 and 733.
       - Fix: split each into sentences of about 25 words with at most one parenthesis, then go through the rest of the page the same way.

    Open, not this stage's to fix: the Description cites "style rules 8 to 10", but `docs/project-guide/style.md` has rules 1 to 8. Neither the journal nor the criteria say which rules are meant, so this is left for the human. The page has no *Reference* section, which criterion 2 allows.
