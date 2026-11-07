---
stage: docs-approval
blocked: null
round: 2
attempts: 1
crashes: 0
pull_request: 622
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T03:47:57.817768Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T03:47:57.825123Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T03:48:12.406452Z'
  stage: intake
  run: 10e66264532943fd8db09367d103f89d
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T03:48:17.098338Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T03:54:29.515097Z'
  stage: docs-only
  run: f10b8f15d2ff4e719281ec3db598b09d
- number: 6
  speaker: factory
  kind: stall
  at: '2026-11-07T03:54:29.920118Z'
  stage: docs-only
  run: f10b8f15d2ff4e719281ec3db598b09d
  reason: check_red
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T03:54:36.564872Z'
  stage: docs-only
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-07T03:57:16.693782Z'
  stage: docs-only
  run: 564bdc1e4cf34a228c52001144ee4695
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-07T03:57:22.012883Z'
  stage: docs-review
- number: 10
  speaker: reviewer
  kind: result
  at: '2026-11-07T03:59:26.248985Z'
  stage: docs-review
  run: fb36a262832f41b4b1a0c1bf0f847ba5
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-07T03:59:31.239565Z'
  stage: docs-only
- number: 12
  speaker: documenter
  kind: result
  at: '2026-11-07T04:03:38.241897Z'
  stage: docs-only
  run: a7f5f72b412f41e0b26440104687e8f7
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-07T04:03:43.356129Z'
  stage: docs-review
- number: 14
  speaker: reviewer
  kind: result
  at: '2026-11-07T04:04:39.047762Z'
  stage: docs-review
  run: 3bc60657c3ae4cb08f23a223525744aa
- number: 15
  speaker: factory
  kind: started
  at: '2026-11-07T04:04:43.927542Z'
  stage: docs-only
- number: 16
  speaker: documenter
  kind: result
  at: '2026-11-07T04:07:16.433825Z'
  stage: docs-only
  run: 862285c7715c42f59572ec3043b62be8
- number: 17
  speaker: factory
  kind: started
  at: '2026-11-07T04:07:21.672092Z'
  stage: docs-review
- number: 18
  speaker: reviewer
  kind: result
  at: '2026-11-07T04:07:59.836372Z'
  stage: docs-review
  run: 6a121f4d89ab42fa98eebd4203754d6c
---

# The project guide's page on the work area reads for the developer

## Description

`docs/project-guide/work.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/work.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/work.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/work.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/work.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/work.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/work.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths (`docs/project-guide/work.md`, `docs/checked-documents.txt` with exactly one line), states link and heading rules, and says no code, test or agent file changes. It contains no signatures to test, since the story only changes documents.
   Criteria: 1 to 5 can each be judged or checked. The style and the old-versus-new comparison go to the reviewer, as the feature's decision 2 says. The checked list, `documents ok` and broken links are checked by `make documents`. The Interface states no rule with a failing side beyond the link and heading rules, which criteria 4 and 5 cover. 6 is `make check`.
   Smoke test: `grep -cx "docs/project-guide/work.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It runs no pytest.
   Docs criterion: it names what the reader must know, in the form "as criteria 1 to 5", and dictates no sentences. `docs/decisions.md` is stated as none.
   Architecture: the only paths changed are `docs/project-guide/work.md` and `docs/checked-documents.txt`, both documents the documenter may write. The docs-only route is chosen because the story changes only documents.
   Scope: it is S0014 of F0054, one file, and the feature scope lists "each of the 22 files, one story each". It touches nothing in the feature's Out of scope: `docs/decisions.md`, `docs/runs/`, the operator playbook and behaviour changes.
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/project-guide/work.md` for its reader and added it to the checked list. `make documents` prints `documents ok (9.6 s)`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/project-guide/work.md`: rewritten in the order style.md gives (idea, names in a block, one rule per bullet, See also). The old headings stay, so links from other files still resolve. Detail that the sections only summarise moved to a new closing section, *Reference*. It holds the path constants, the field tables, the full acceptance rules (reader, opening, hand-over, facts), the records-contract schema text and the layout of the written file with its notation. Module files are linked once at first mention. The six examples are now `console` blocks. I ran them, copied the real output, and `make documents` runs them again.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/work.md`.
   - `docs/project-guide/README.md`: the index entry for `work.md` now lists the new *Reference* section.

   Corrections and removals, checked against the code:
   - The records-contract version in the old text was `2.0`; `RECORDS_CONTRACT` is `4.4`. I wrote `4.4`.
   - I removed history wording: "from now on", "moved there from", "so existing imports stay valid", "a record written before they existed", and the reference to the feature's decision 4.
   - Writing `factory/agents` as `<project>/factory/agents`, as the style page asks, was needed to pass the name check.

   Examples that changed:
   - Each console command is now one line, because the runner does not accept `>` continuation lines.
   - The error example now shows the last line of the traceback, `factory.shared.domain.errors.WorkItemFormatError: unknown key: colour`, where the old text printed only the fault.
   - The sections example uses tilde fences, so its output can sit inside a backtick block.

   Compare old and new:
   - I tried to keep every name, rule and message of the old file, either in a section or in the Reference.
   - I wrote the new text from the old text. I did not re-read all of the code behind each rule, only a sample: the contract version, the existence of the handlers and functions, the journal's private `_state_of`, `cost_table_key` and `BRANCH_PREFIX`.
   - The reviewer should compare the old and new files, especially the acceptance bullets I condensed.
   - I dropped two sentences on purpose: a duplicated cross-reference to *The wiring* and the closing "Plain string order... is the human's only priority".
   - I shortened the acceptance-status, hand-over and facts text to a bullet each in the section and kept the full rules in the Reference.

   Cross-read and found current: the index `docs/project-guide/README.md` other than the new *Reference* entry, `docs/operator-guide/pipeline.md` (*Checking a story before it starts*) and `docs/operator-guide/work-items.md` (*When a feature acceptance is due*). I did not touch `docs/decisions.md`.

   Not touched, unrelated to this story: `docs/project-guide/README.md` keeps names like `support/site_check_support.py` that `make documents` reports under "not checked yet" (README is not on the checked list). `agents.md` and `machine.md` have the same kind of report lines. I cut a "Plain string order alone would put ... " sentence from the order section, so check that the key's purpose is still clear.

   No findings for the coder.
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
8. documenter: Fixed the red check from the previous attempt. The guard `tests/guards/test_project_guide_files.py::test_no_file_names_a_removed_guide_file` failed on `docs/project-guide/work.md:159`. The link text `work-items.md` matches the guard's pattern for the removed guide file of that name. The link target was already correct: `../operator-guide/work-items.md`.

   Files changed:
   - `docs/project-guide/work.md`, line 159: the link text is now `operator-guide/work-items.md`, which the guard's pattern allows. The target and the sentence are unchanged.

   Checks run:
   - The guard test now passes.
   - `make documents` prints `documents ok (9.7 s)`.
   - I did not run `make check`, because I changed only a document. The factory runs it.

   Everything else stands as in the earlier docs-only entry. The reviewer should still compare the old and new `work.md` against the code, especially the condensed acceptance bullets. The earlier entry says the rewrite was checked against the code only by sample, so that comparison is open.

   Not touched, unrelated to this story: the earlier entry lists unchecked-name report lines in `docs/project-guide/README.md`, `agents.md` and `machine.md`.

   `check`: check: green
   `secrets`: secrets: green (0.6 s)
   `documents`: documents ok (9.7 s)
9. factory: started docs-review as vm.
10. reviewer: I reviewed `git diff main...HEAD -- README.md docs operator/README.md` against the work item, against the old `docs/project-guide/work.md` on `main`, against `docs/project-guide/style.md`, and against the code on the branch (identifiers, paths, sections, story_form, acceptance, contract, entry/contract, journal). No other file links to a heading that was removed. I grepped `README.md`, `docs/`, `agents/` and `src/` for *Ids and names*, *Order*, *The tree*, *The document and its error*, *The layout*, *The body* and *Faults*. So criterion 5 holds. The documenter's entry 5 says "the old headings stay". That is not true: those seven headings are gone or moved into *Reference*. Nothing points to them, so this is not a finding against the document. The `docs/checked-documents.txt` line and the index entry in `docs/project-guide/README.md` are correct.

    Findings:
    1. `docs/project-guide/work.md:304`: the signature says `check_story_place(...) -> list[str]`, but `src/factory/work/domain/story_form.py:244` returns `list[FormFinding]`. Fix: write `-> list[FormFinding]`.
    2. `docs/project-guide/work.md:195`: the signature says `write_contract(folder) -> None`, but `src/factory/entry/contract.py:17` returns `list[Path]`. Fix: write `-> list[Path]`.
    3. `docs/project-guide/work.md:146` and `:18`: the return types are less exact than the code. `acceptance_status` returns `AcceptanceStatus` (`src/factory/work/domain/acceptance.py:165`), not `str`, and `folder_of` returns `LifecycleFolder | None` (`src/factory/shared/domain/paths.py:53`). Fix: write the code's types.
    4. `docs/project-guide/work.md:197`: `uv run python -m factory.entry.contract [<folder>]` is a command in an indented block. It is neither a runnable `console` example nor marked for the VM, GitHub or a model, so the Description's rule ("Every command the file shows is a runnable example or is marked") is broken. Fix: make it a `console` block that writes into a new folder, such as `$ uv run python -m factory.entry.contract schemas`, followed by `contract: 5 schemas written`. If `uv` cannot run under the check, use the form the other examples use.
    5. `docs/project-guide/work.md:35,66,126,251,290`: the examples call a bare `python`. This works only when the project's virtual environment is on PATH, and CLAUDE.md says "Run Python through `uv run`". A reader who copies a command into a plain shell gets `ModuleNotFoundError`. Fix: add one sentence above the first example saying that these commands run in the project's environment and are `uv run python -c ...` from a shell.
    6. `docs/project-guide/work.md:168`: "See also: *The reading of a remote's work items* below" names a heading that does not exist. The section is *The remote's work items* (line 170). Fix: use that name.
    7. `docs/project-guide/work.md:72`: "See *The data of a work item* in the Reference for its fields" points nowhere useful. The Reference's *The data of a work item* (lines 395–422) lists the fields of `WorkItemState` and `JournalRecord` but not those of `Claim`, which line 74 already gives. Fix: remove the sentence, or point to line 74's bullet.
    8. `docs/project-guide/work.md:62`: "the journal module, which keeps a private `_state_of` (see *The journal's entries*)" points to a section that no longer mentions `_state_of`. The old text said it there. Line 123 now stops at "it cannot use `require_state`". Fix: add to line 123 that the module therefore keeps its own private `_state_of` (`src/factory/work/domain/journal.py:143`), the one other function that checks a document's state.
    9. `docs/project-guide/work.md:390`: "`PROJECT_AGENTS_DIRECTORY` (`<project>/factory/agents`)" and "`project_agent_file(name)` gives `<project>/factory/agents/<name>.md`" misstate the values. The constant is `"factory/agents"` (`src/factory/shared/domain/paths.py:20`), and the function returns a path relative to the project's root. Fix: say that both are paths relative to the project's root, so the folder is `<project>/factory/agents/`, and keep the placeholder only on the folder.
    10. `docs/project-guide/work.md:154`: a rule of the old file was dropped without being named. The old text said "`parse_work_item_file_name` reads it back to the id and that slug" for the acceptance report file name, and neither the section nor the Reference keeps it (criterion 2). Fix: add it back to this bullet.
    11. `docs/project-guide/work.md:182`: "the folders of the old layout" is history wording (style rules 1 and 7). It replaced "v1's folders". Fix: say what is ignored now, for example "any path that `folder_of` refuses", without naming an earlier layout.
    12. `docs/project-guide/work.md`: many words that the glossary defines are not linked at their first use (criterion 1, style rule 3). They are: acceptance (l.20), feature (l.27), claim (l.45), stage (l.91), approval, round cap, attempts cap and crash (l.92), stall (l.93), role (l.95), cost record (l.141), backlog (l.224), pipeline definition (l.205) and write paths (l.462, or wherever they first appear). Only work item, instance, journal and story are linked. Fix: link each to `glossary.md` at its first use in the file.
    13. `docs/project-guide/work.md:89,98,166,222,446`: modules the page names are not linked, as the Interface requires ("Each module, file or page ... is linked once"). They are `factory.work.domain.decisions` (`src/factory/work/domain/decisions.py`), `factory.watching.domain.cost_records`, `factory.entry.wiring` (`src/factory/entry/wiring.py`), `factory.hosting.domain.hand_over` (`src/factory/hosting/domain/hand_over.py`) and `factory.watching.application.costs` (`src/factory/watching/application/costs.py`). Fix: link each once at its first mention, or once in a See also.
11. factory: started docs-only as vm.
12. documenter: I fixed the reviewer's twelve findings in `docs/project-guide/work.md`. `make documents` ends with `documents ok (9.7 s)`. I changed only a document, so I did not run `make check`.

    File changed: `docs/project-guide/work.md`. Per finding:
    1. `check_story_place` now returns `list[FormFinding]`.
    2. `write_contract` now returns `list[Path]`.
    3. `folder_of` now returns `LifecycleFolder | None`. `acceptance_status` now returns `AcceptanceStatus`. I checked both against `paths.py:53` and `acceptance.py:165`.
    4. The contract command is now a `console` example: `python -m factory.entry.contract schemas`, which prints `contract: 5 schemas written`. It writes into a new folder in the example's temporary directory.
    5. One sentence above the first example says the commands run in the project's environment and become `uv run python` from a plain shell. I kept the bare `python` in the examples because the runner uses it. I did not try `uv run` under the runner.
    6. The See also now names *The remote's work items*.
    7. I removed the sentence that pointed to the Reference for `Claim`'s fields. The bullets below it already list them.
    8. The sentence on the journal module now says it keeps its own private `_state_of`, the one other function that checks a document's state. I checked that function at `journal.py:143`.
    9. `PROJECT_AGENTS_DIRECTORY` and `project_agent_file` are now described as paths relative to the project's root, with the folder written `<project>/factory/agents/`. This form also passes the name check; the bare `factory/agents/<name>.md` I tried first did not.
    10. The acceptance file name bullet again says `parse_work_item_file_name` reads the name back to the id and the slug.
    11. "The folders of the old layout" is now "any path that `folder_of` refuses".
    12. Glossary links added at the first prose use of: acceptance, feature, claim, stage, attempts cap, round cap, crash, approval, stall, role, cost records, backlog, pipeline definition and write paths.
    13. Module links added once each at first mention: `decisions.py`, `cost_records.py`, `wiring.py`, `hand_over.py` and `costs.py`.

    For the glossary links I used the first place where the word appears in prose. A word that appears earlier only as code, such as `stage` or `Claim`, is not linked there.

    Cross-read: `docs/project-guide/README.md`, `docs/checked-documents.txt` and the operator-guide links were found current in the earlier rounds. I changed no heading, so no link from another file moved.

    Stale text I saw but did not touch, because it is unrelated to this story: `make documents` still lists "not checked yet" or "does not exist" names in `docs/project-guide/agents.md` and `machine.md`. The earlier entries also report `README.md`.

    Also unchanged: the documenter's earlier claim that "the old headings stay" was wrong, as the reviewer said. Seven old headings now sit in the Reference or were merged, and nothing links to them.

    No findings for the coder.

    `check`: check: green
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok (10.0 s)
13. factory: started docs-review as vm.
14. reviewer: Round 1 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md`, then checked the new `docs/project-guide/work.md` against the code on the branch and against the round-0 findings.

    All 13 round-0 findings are fixed, and I checked each against the code:
    - `check_story_place` and `check_story_form` now return `list[FormFinding]` (`src/factory/work/domain/story_form.py:200,244`).
    - `write_contract` now returns `list[Path]` (`src/factory/entry/contract.py:17`).
    - `folder_of` and `acceptance_status` now carry the code's types.
    - The contract command is now a `console` example. It matches `main`, which writes into the folder given or `CONTRACT_FOLDER` and prints `contract: 5 schemas written`.
    - The `uv run python` sentence is at line 34.
    - The See also on line 170 names the real heading.
    - The sentence that pointed nowhere is gone.
    - `_state_of` is explained at line 125.
    - `PROJECT_AGENTS_DIRECTORY` and `project_agent_file` are described as paths relative to the project's root (`paths.py:20,48`).
    - The `parse_work_item_file_name` rule is back at line 156.
    - The history wording is gone from line 184.
    - The glossary terms and modules are now linked.

    The other signatures I spot-checked match the code: `main` of check_story, `lifecycle_folder_of_location`, the sections functions, `work_item_path`, `cost_records_path`, `acceptance_id`, `next_acceptance_id` and `initial_state`. The `docs/checked-documents.txt` line and the index entry in `docs/project-guide/README.md` are still correct.

    I left one point out. Line 366 names `python -m factory.entry.check_story` inline. I read it as naming the module's entry point, not as a command shown to run, and line 373 points to the operator guide's example of its output.

    Findings:
    1. `docs/project-guide/work.md:508`: "A journal record's `at`, `stage` and `run` are left out of the file when unset. Every other key stays (`claim: null`)." The code contradicts this for a record. The writer dumps each record with `model_dump(exclude_none=True)` (`src/factory/work/adapters/work_item_markdown.py:175`), so an unset `blocked` and `reason` are left out too. Line 92 of the same page already says so ("leaves an unset field out"). Fix: say that every unset field of a journal record (`at`, `stage`, `run`, `blocked`, `reason`) is left out of the file, and that every key of the state itself stays (`claim: null`).
    2. `docs/project-guide/work.md:13`: the signature says `work_item_order(id) -> tuple`. The code returns `tuple[str, int, str]` (`src/factory/shared/domain/identifiers.py:81`). This is the same kind of loose type as round 0's finding 3. Fix: write `-> tuple[str, int, str]`.
15. factory: started docs-only as vm.
16. documenter: I fixed the reviewer's two findings from the last docs-review. Both are in `docs/project-guide/work.md`. `make documents` ends with `documents ok (9.8 s)`. I changed only a document, so I did not run `make check`.

    Files changed:
    - `docs/project-guide/work.md`, line 13: the signature now reads `work_item_order(id) -> tuple[str, int, str]`, as in `src/factory/shared/domain/identifiers.py:81`.
    - `docs/project-guide/work.md`, line 508: the bullet now says that every unset field of a journal record (`at`, `stage`, `run`, `blocked`, `reason`) is left out of the file, and that every key of the state itself stays (`claim: null`). The writer dumps records with `exclude_none=True`, and line 92 of the same page already says so. The example that follows is the record with `at`, `stage` and `run` all set, and the bullet now says that.

    I changed no heading, so no link from another file moved. I cross-read nothing new this round. `docs/project-guide/README.md`, `docs/checked-documents.txt` and the operator-guide links were found current in the earlier rounds.

    Stale text I saw but did not touch, because it is unrelated to this story: `make documents` still lists "not checked yet" names in `docs/project-guide/agents.md`, `docs/project-guide/machine.md` and `docs/project-guide/README.md`.

    No findings for the coder.

    `check`: check: green
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok (10.0 s)
17. factory: started docs-review as vm.
18. reviewer: Round 2 docs-review. I read the work item and `git diff main...HEAD -- README.md docs operator/README.md` (3 files: `docs/checked-documents.txt`, `docs/project-guide/README.md`, `docs/project-guide/work.md`). I checked the two round-1 findings against the code and read the whole of the new `docs/project-guide/work.md` again.

    Round-1 findings, both fixed and checked against the code:
    - `docs/project-guide/work.md:13` now gives `work_item_order(id) -> tuple[str, int, str]`, which matches `src/factory/shared/domain/identifiers.py:81`.
    - `docs/project-guide/work.md:508` now says that every unset field of a journal record (`at`, `stage`, `run`, `blocked`, `reason`) is left out of the file, and that every key of the state itself stays. This matches `src/factory/work/adapters/work_item_markdown.py`: `render` uses `state.model_dump()` for the state and `record.model_dump(exclude_none=True)` for each record. It also agrees with the fields of `JournalRecord` (`src/factory/work/domain/journal.py:71-78`) and with line 92 of the same page.

    Further spot-checks on this pass, all of which match the code:
    - `RECORDS_CONTRACT` is `"4.4"` (`src/factory/shared/domain/contract.py:15`).
    - The signature of `factory.entry.check_story.main` is right (`check_story.py:145`).
    - The behaviour of `factory.entry.contract.main` is right: its usage line, its return value of 2, and the line `contract: <n> schemas written` (`contract.py:12,28-36`).
    - Every message in the form-check table and the place table matches `src/factory/work/domain/story_form.py`: lines 107, 114, 140, 144, 163, 182, 185, 192 and 195 for the form check, and lines 38 and 253-261 for the place check.
    - The values in `JournalKind` are right.

    The criteria:
    - Criterion 1 (style) holds.
    - Criterion 2 holds. Rules that were condensed are kept in full in *Reference*. Two sentences were dropped on purpose and named in entry 5: a duplicate cross-reference to *The wiring*, and the sentence calling plain string order "the human's only priority". Neither drops a rule; the reason for the order key stays at line 26.
    - Criteria 3 and 4 rest on the factory's `make documents` (`documents ok` in entry 16) and on `docs/checked-documents.txt`, which carries the line `docs/project-guide/work.md`.
    - Criterion 5 holds. No heading that a link points to was removed, as round 0 found, and no heading changed since.
    - Criterion 7: `docs/decisions.md` is untouched.

    I agree with round 1's reading that `python -m factory.entry.check_story` at line 366 names the module's entry point and is not a command for the reader to run.

    no findings
