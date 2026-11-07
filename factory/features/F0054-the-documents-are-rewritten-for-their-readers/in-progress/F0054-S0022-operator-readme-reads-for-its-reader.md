---
stage: docs-review
blocked: null
round: 2
attempts: 1
crashes: 0
pull_request: 630
comments_read: [6705071034]
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T09:51:06.472872Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T09:25:27.205799Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T09:25:27.213456Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T09:25:42.661061Z'
  stage: intake
  run: 909f335fda7046d79c5bb6b009ebde27
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T09:25:47.414080Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: question
  at: '2026-11-07T09:28:59.277469Z'
  stage: docs-only
  run: a68cff5061064f26a19cc9fd35a1bce2
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-11-07T09:30:47.803902Z'
  stage: docs-only
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-07T09:30:50.272505Z'
  stage: docs-only
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-07T09:33:05.445761Z'
  stage: docs-only
  run: 26ddd06a1e0d4511ac11b3af7ba15bc2
- number: 9
  speaker: factory
  kind: stall
  at: '2026-11-07T09:33:05.829927Z'
  stage: docs-only
  run: 26ddd06a1e0d4511ac11b3af7ba15bc2
  reason: check_red
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T09:33:12.788776Z'
  stage: docs-only
- number: 11
  speaker: documenter
  kind: result
  at: '2026-11-07T09:39:35.979719Z'
  stage: docs-only
  run: 3c28904ff60e4988ba5f5376230097ad
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T09:39:41.026135Z'
  stage: docs-review
- number: 13
  speaker: reviewer
  kind: result
  at: '2026-11-07T09:41:05.115798Z'
  stage: docs-review
  run: b4dbd49596eb48a0aeb7fbb3b209493a
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T09:41:10.143568Z'
  stage: docs-only
- number: 15
  speaker: documenter
  kind: result
  at: '2026-11-07T09:45:40.828324Z'
  stage: docs-only
  run: a7e35df3e23744f0ae2f7ac41920b199
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T09:45:45.972880Z'
  stage: docs-review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-11-07T09:46:38.706449Z'
  stage: docs-review
  run: f535638cd5ec436b95229b8df62ebff9
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-07T09:46:44.168153Z'
  stage: docs-only
- number: 19
  speaker: documenter
  kind: result
  at: '2026-11-07T09:50:58.772832Z'
  stage: docs-only
  run: b2db598c0e0640a388f6522f2f0a5ffb
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-07T09:51:06.472872Z'
  stage: docs-review
---

# The operator folder's README reads for its reader

## Description

`operator/README.md` is rewritten for its reader, a developer who opens the `operator/` folder (the skill staged there and the folder's scripts), in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. `docs/checked-documents.txt` stays unchanged: the check does not read `operator/README.md` yet, so its runnable examples are run by hand, and adding its path to the list is left to F0055 (the human, journal 6). The story takes the docs route.

## Interface

- `operator/README.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `operator/README.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `operator/README.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `operator/README.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "operator/README.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `operator/README.md` and `docs/checked-documents.txt` (one line, `operator/README.md`) and states that no code, test or agent file changes. Both paths are ones the documenter may write, so the story takes the docs route.
   - Criteria: all concern documents only. Criterion 1 is the reviewer's judgment against style.md. Criterion 2 is the reviewer's comparison of old and new file against the code. Criterion 3 is checked by the file being on the list and `make documents` printing `documents ok`. Criterion 4 is a link check. Criterion 5 is `make check`. The story states no code rules, so there is no failing side to cover.
   - Smoke test: `grep -cx "operator/README.md" docs/checked-documents.txt` is runnable and its `Expect: 1` can be checked against the output. It runs no pytest.
   - Docs criterion: criterion 6 points to criteria 1 to 4, which say what the document must satisfy (facts kept or moved to Reference, claims corrected, examples runnable or marked, links intact). It quotes no sentences to write. `docs/decisions.md` is named as unchanged.
   - Architecture: only a document and the checked list change. No layer or module is touched.
   - Scope: within F0054, where S0022 is listed and the story is one file. `operator/README.md` is not in the feature's "Out of scope" list, and the story changes no behaviour.
4. factory: started docs-only as vm.
5. documenter: I rewrote `operator/README.md` but could not finish criterion 3. `docs/checked-documents.txt` is unchanged and `operator/README.md` is not on it, because the check refuses that line.

   **Where I stopped.** I added the line `operator/README.md` to `docs/checked-documents.txt` and ran `make documents`. It failed with `docs/checked-documents.txt: operator/README.md is no document of the check`. `checked_list_findings` in `src/factory/shared/domain/documents.py` accepts only the documents the check reads: the README, the operator guide files and the project guide files (constants at lines 23-41). `operator/README.md` is not among them. I took the line out again, so `make documents` now ends `documents ok (58.8 s)`.

   **What the story needs.** The Interface says no code changes. Criterion 3 cannot be met without one: the document set in `documents.py` must include `operator/README.md`, and probably its tests under `tests/` as well. I could not tell whether that is a code story or whether the Interface is wrong, so I am asking instead of ending with `tests` (the docs-only route's way out for a story that needs code).

   Options:
   1. (My choice.) Keep this story docs-only and drop the checked-list part of criterion 3 and of the Interface. A separate story then makes `operator/README.md` a document of the check, and a follow-up adds the line to the list.
   2. Change the Interface so the story takes the code route: tester, then coder, to make `operator/README.md` a document of the check. I then end with `tests` on the next run and the list line goes in at the docs stage.
   3. You make the change to `documents.py` yourself and re-run this stage.

   **What I changed.** `operator/README.md` is rewritten, and it is the only changed file.
   - It is headed "The operator folder". It starts with what the folder is and for whom, and says that the skill is a trial and where the plan is.
   - Its sections are *Installing* (numbered steps), *What you need*, *How Kumpel's acts are told from yours*, and a *Reference* with the file table and the settings table. `docs/operator-guide/site.md` refers to the heading *Installing*, so I kept it.
   - Every file, command, setting and rule of the old text is kept. The signature strings, `KUMPEL_SETTINGS`, the settings file path and the switch defaults (`merge` off, `answer` and `start_next` on) were checked against `settings.sh`.
   - Dropped on purpose, per style rules 1 and 7: the "Second version, 2026-11-01" paragraph, the trial notes, the "Story" column of the table (feature and story IDs), and "(for the trial)". The trial wording survives as one paragraph about the skill's status.
   - Added because the code has them: the `vm/` files (`setup.sh`, `factory.service`, `Dockerfile`, `git-credential-factory`, `job-start.sh`) and `template/`, which the old table's "each file" claim left out. The old table also had no `settings.sh` row in the installing text, which I now cover in step 5.
   - Glossary links on first use of instance, work item and stop. The one runnable `console` example, `site init`, was run by hand. Every command that touches a machine, an account or `~` is in an `sh` block.

   **Cross-read, found current.** No link needs changing. `docs/operator-guide/site.md` (lines 7, 279, 302) points to this file and to *Installing*. `docs/project-guide/operator.md` and `agents.md` link only the file. `docs/operator-guide/pipeline.md` line 56 names the file as a document.

   **Checks.** `make documents` ended `documents ok (58.8 s)`. The new file is not on the checked list, so its examples were not checked by that run. Only documents changed, so I did not run `make check`.

   **Stale text I saw and did not touch.** `operator/skill/kumpel/SKILL.md` repeats "Second version, 2026-11-01" and "kumpel-factory v1.2 or later". That is the skill's file, not a document I may write. The old README linked nothing in `planning/`; I kept `planning/operator-skill/DESIGN.md` as a plain path because the folder belongs to the human.
6. 2026-11-07 human: Option 1. This story stays docs-only: the rewritten operator/README.md is its whole change, and the checked-list part of criterion 3 and of the Interface is dropped. Leave docs/checked-documents.txt unchanged. Making operator/README.md a document of the check is now part of F0055-S0001, and F0055-S0004 adds the line to the checked list. Since the check does not read this file yet, run each runnable console example of the page by hand once more before you end, and quote the results in your entry. The reviewer reviews the page as it is, without criterion 3's list line.
7. factory: started docs-only as vm.
8. documenter: Following the human's answer (option 1), this round changes no file. `operator/README.md` stays as I rewrote it in the first round. It is the story's whole change. `docs/checked-documents.txt` is unchanged, on purpose: F0055-S0001 makes the file a document of the check and F0055-S0004 adds the list line. The story's criterion 3 and its Interface list line therefore do not apply here, and the reviewer judges the page without them.

   Runnable examples, run by hand because the check does not read this page yet. The page has one `console` example, `sh operator/bin/site init`, in step 1 of *Installing*. I ran it from the repository root with `HOME` and `XDG_CONFIG_HOME` set to a temporary directory that removed itself afterwards. It printed `site: wrote /tmp/tmp.DB6w1e00oa/kumpel/site.env; edit it, then run: site check` and exited with 0. The file `kumpel/site.env` appeared under that directory. This matches the page's example, where `<path>` stands for the file's location. All other commands on the page are in `sh` blocks, marked as touching the machine, an account or `~`. I did not run those. `git status` showed no change in the repository from the run.

   `make documents` ended `documents ok (58.8 s)` in the first round, and no document has changed since. I did not run `make check`, because only documents changed.

   Cross-read, found current: `docs/operator-guide/site.md` (points to this file and to the heading *Installing*, which is kept), `docs/project-guide/operator.md` and `agents.md` (link only the file), and `docs/operator-guide/pipeline.md` (names the file).

   Stale text I saw and did not touch: `operator/skill/kumpel/SKILL.md` repeats "Second version, 2026-11-01" and "kumpel-factory v1.2 or later". That is the skill's file, not a document I may write.
9. factory: Stage docs-only stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
   src/factory/work/domain/acceptance.py                  195      1     52      1    99%   367
   ------------------------------------------------------------------------------------------------
   TOTAL                                                11211     55   2254     52    99%

   157 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.21%
   ======================================================================================= short test summary info ========================================================================================
   FAILED tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path[vm/setup.sh] - AssertionError: assert ['operator/README.md'] == []
   FAILED tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path[vm/job-start.sh] - AssertionError: assert ['operator/README.md'] == []
   FAILED tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path[vm/Dockerfile] - AssertionError: assert ['operator/README.md'] == []
   FAILED tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path[vm/factory.service] - AssertionError: assert ['operator/README.md'] == []
   FAILED tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path[vm/git-credential-factory] - AssertionError: assert ['operator/README.md'] == []
   FAILED tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path[template/] - AssertionError: assert ['operator/README.md'] == []
   make: *** [Makefile:89: test] Error 1
10. factory: started docs-only as vm.
11. documenter: This round fixes the red check from the last run. The stall came from `tests/guards/test_root_operator_folders_removed.py::test_no_file_names_the_old_root_path`. The guard found `operator/README.md` naming `vm/setup.sh`, `vm/job-start.sh`, `vm/Dockerfile`, `vm/factory.service`, `vm/git-credential-factory` and `template/` at the root. Those are the old root places of files that now sit under `operator/`.

    Changed `operator/README.md`, the story's whole change:
    - The six file-table rows for the VM files and the template now read `operator/vm/...` and `operator/template/`. The rows name the real paths and the guard no longer finds the old ones.
    - The table's other rows are relative to `operator/`, so I added one sentence under the *Files* heading. It says paths are relative to `operator/`, and rows that start with `operator/` are paths from the repository root.

    I did not change `docs/checked-documents.txt`. The human's answer (journal 6) dropped the list line from this story: F0055-S0001 makes the page a document of the check and F0055-S0004 adds the line. Criterion 3's list part and the Interface's list line therefore do not apply here.

    Checks:
    - `uv run pytest -q tests/guards/test_root_operator_folders_removed.py` passed (22 tests).
    - `make documents` ended `documents ok (58.9 s)` after my last edit.
    - I did not run `make check`, because only a document changed. The factory runs it after this stage.
    - The one runnable `console` example on the page, `site init`, was run by hand in the previous round and printed `site: wrote <tmp>/kumpel/site.env; edit it, then run: site check`, exit 0. This round touched only the file table, so I did not run it again.

    Cross-read and found current:
    - `docs/operator-guide/site.md` points to this file and to the heading *Installing*, which is kept.
    - `docs/project-guide/operator.md` and `agents.md` link only the file.
    - `docs/operator-guide/pipeline.md` names the file.

    Stale text I saw and did not touch: `operator/skill/kumpel/SKILL.md` repeats "Second version, 2026-11-01" and "kumpel-factory v1.2 or later". That is the skill's own file, not a document I may write.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (59.0 s)
12. factory: started docs-review as vm.
13. reviewer: Reviewed `operator/README.md` on the branch against the operator files it describes and against `docs/project-guide/style.md`. The human's answer (journal 6) dropped the checked-list line, so `docs/checked-documents.txt` was not under review.

    These facts match the code:
    - the signature strings in `comment.sh:21`, `start-story.sh:20`, `merge.sh:55`;
    - `site: wrote ...; edit it, then run: site check` and `site: ready` in `operator/bin/site:29,96`;
    - the `settings.sh init` rules, the switch defaults (`merge` off, `answer` and `start_next` on) and `KUMPEL_SETTINGS`;
    - the rows for the `operator/vm/` files and `operator/template/`;
    - the links to `docs/operator-guide/site.md` (*Setting up an operator's machine*) and to the glossary.

    Criterion 2: everything else from the old file is kept or moved to *Reference*. These were dropped on purpose under style rules 1 and 7: the "Second version, 2026-11-01" paragraph, the `planning/operator-skill/TRIAL-1.md` reference with the todo demo trial, the table's Story column, "(for the trial)" and "(the human, 2026-10-31)". I accept all of them.

    Criterion 4: no link breaks. *Installing* is kept, and `docs/operator-guide/site.md` refers to it.

    Findings:
    1. `operator/README.md:5` (and the table): the page's first use of story, feature, approval ("six approval checks", line 72) and stage are not linked to the glossary, nor is pipeline definition (the `operator/template/` row). Criterion 1 and style rule 3 want that. Fix: link each at its first use, as instance, work item and stop already are.
    2. `operator/README.md:3` and `:5`: two sentences are over the 25 words of style rule 2. Line 3 ("This folder holds ... set up a VM.") has about 33; line 5 ("It watches ... on request.") has about 37 and a parenthesis. Fix: split each sentence.
    3. `operator/README.md:3`: the list of what the folder holds leaves out `template/`, the start of a new project that the *Files* table lists. Nobody runs it next to an instance, and no listed group covers it. Fix: name the template in that sentence, or say the list is only the main parts.
    4. `operator/README.md:5`: `planning/operator-skill/DESIGN.md` exists but is a plain path. Style rule 8 asks for a relative link to a file of the repository, and a link writes nothing in `planning/`. Fix: `[DESIGN.md](../planning/operator-skill/DESIGN.md)`.
    5. `operator/README.md` *Reference › Files*, the sentence under the heading and the first 19 rows: those rows use paths below the root (`lib/site.sh`), while the last six start with `operator/`. Style rule 8 wants paths from the repository root, and the mixed table needs a sentence to explain it. Fix: write every row from the root (`operator/site.env.example`, `operator/lib/site.sh`, ...) and drop the sentence.
    6. `operator/README.md` step 5: one `sh` block holds two commands that are alternatives. A reader who runs the block as shown runs `init` twice. Fix: two blocks, each with its own lead line, as step 4 does for the two tools.
    7. `operator/README.md` *Reference › Settings file*:
       - The Example cells `merge on`, `answer off` and `start_next off` are not commands, and the page never says how to change a switch. The code has `settings.sh set <switch> on|off` and the command `/kumpel <switch> on|off` (`operator/claude/commands/kumpel.md`). Fix: write the examples as `/kumpel merge on`, or as `sh operator/skill/kumpel/scripts/settings.sh set merge on`, and say so once above the table.
       - `KUMPEL_SETTINGS` is an environment variable that names the file, not a key in it. Fix: give it its own row under a heading for the environment variable, or retitle the table *Settings*.

    Description corrected: "When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on." -> "`docs/checked-documents.txt` stays unchanged: the check does not read `operator/README.md` yet, so its runnable examples are run by hand, and adding its path to the list is left to F0055 (the human, journal 6)."

    Open: the Interface line for `docs/checked-documents.txt` and the list part of criterion 3 still name the list line. Journal 6 dropped both, and the review rules let me rewrite only the Description, so I left them as they are.
14. factory: started docs-only as vm.
15. documenter: Round 1 fixes the reviewer's seven findings (journal 13). The only file changed is `operator/README.md`. `docs/checked-documents.txt` stays unchanged, as the human decided in journal 6.

    1. Glossary links: story, feature, approval and pipeline definition are now linked at their first use. Stage is part of the "approval" link's sentence. I kept the merge-commit message literal in its code span and put the approval link in the sentence after it.
    2. Long sentences: the two over-long sentences in the intro are split.
    3. The intro now names the template of a new project.
    4. `planning/operator-skill/DESIGN.md` is now a relative link. I wrote nothing in `planning/`.
    5. Every row of the Files table now starts with `operator/`, and I dropped the sentence that explained the mixed paths.
    6. Installing step 5 now has two separate `sh` blocks, one for `init` and one for `init <owner/name> <checkout>`. Each has its own lead line.
    7. The Reference section *Settings file* is now *Settings*. A sentence above the tables says to change a switch with `/kumpel <switch> on|off` or with `settings.sh set <switch> on|off`. I checked both against `operator/claude/commands/kumpel.md` and `settings.sh`. The switch examples are now `/kumpel merge on` and so on. `KUMPEL_SETTINGS` has its own table, headed "The environment variable".

    Checks: `make documents` ended `documents ok (58.2 s)` after my last edit. I did not run `make check`, because only a document changed. The one runnable `console` example, `sh operator/bin/site init`, is unchanged. It was run by hand in the first round and printed `site: wrote <tmp>/kumpel/site.env; edit it, then run: site check` with exit 0. This round did not touch that step.

    Cross-read and found current:
    - `docs/operator-guide/site.md` points to this file and to the heading *Installing*, which is kept.
    - `docs/project-guide/operator.md` and `agents.md` link only the file.
    - `docs/operator-guide/pipeline.md` names the file.

    Stale text I saw and did not touch:
    - `operator/skill/kumpel/SKILL.md` repeats "Second version, 2026-11-01" and "kumpel-factory v1.2 or later". That is the skill's own file, not a document I may write.
    - The story's Interface line for `docs/checked-documents.txt` and the list part of criterion 3 still name the list line. Journal 6 dropped both, and I may not edit them.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (57.8 s)
16. factory: started docs-review as vm.
17. reviewer: Round 1 docs-review of `operator/README.md` on the branch. I checked it against the operator files it describes and against `docs/project-guide/style.md`. As the human decided in journal 6, `docs/checked-documents.txt` was not under review.

    The seven findings of journal 13 are fixed, and I checked each fix against the code:
    - Glossary links now cover story, feature, approval and pipeline definition.
    - The long intro sentences are split, and the intro names the template.
    - `DESIGN.md` is a relative link.
    - Every row of the Files table is written from the repository root.
    - Step 5 is two `sh` blocks.
    - The Settings section matches `settings.sh set <switch> on|off` (`operator/skill/kumpel/scripts/settings.sh:7`) and `/kumpel` (`operator/claude/commands/kumpel.md`). `KUMPEL_SETTINGS` has its own table, and its default is `~/.config/kumpel/settings.json` (`settings.sh:9`).
    - The `operator/template/` row matches the folder: `CLAUDE.md`, `Makefile` and `factory/pipeline.yml`.

    Criterion 2 holds. What was dropped is still the same set I accepted in journal 13. Criterion 4 holds: *Installing* is kept, and `docs/operator-guide/site.md` links to it.

    Findings:
    1. `operator/README.md:74`: "The checks are those of the [approval] stage." The code does not bear this out. The glossary says the approval stage is where the human reads the pull request, and the factory has no six checks there. The six checks are Kumpel's own: it judges them on a story at `stage:approval` (`operator/skill/kumpel/references/approving.md:3-5`, `scripts/approval.sh:2`). Fix: say that these are the six checks Kumpel judges on a story at the approval stage, and link `operator/skill/kumpel/references/approving.md` where they are listed.
    2. `operator/README.md` steps 2, 4 and 5 (lines 23, 36-42, 48-54): the text above these `sh` blocks does not say where they run. Style.md, *Examples that are not run*, requires it: "The text above the block says where it runs." These commands use paths relative to the repository root (`operator/bin/site`, `operator/opencode/...`, `operator/skill/kumpel/scripts/settings.sh`), and they write to `~`. Only steps 1 and 3 say "from the root of this repository" or "on the operator's machine". Fix: in each of steps 2, 4 and 5, say that it runs on the operator's machine from the root of this repository, as step 3 does. Or say it once above step 1 for every step and drop the repeats.
18. factory: started docs-only as vm.
19. documenter: Round 2 fixes the two findings of journal 17. The only file changed is `operator/README.md`. `docs/checked-documents.txt` stays unchanged, as the human decided in journal 6.

    1. Approval line (the page's section *How Kumpel's acts are told from yours*): the sentence "The checks are those of the approval stage" is replaced. It now says these are the six checks Kumpel judges on a story at the approval stage (glossary link kept) and links `skill/kumpel/references/approving.md`, which lists them. I confirmed the file exists.
    2. Where the commands run: steps 2, 4 and 5 (both `init` variants) now say, in the text above the block, that they run on the operator's machine from the root of this repository, as steps 1 and 3 already did.

    Checks: `make documents` ended `documents ok (58.3 s)` after my last edit. I did not run `make check`, because only a document changed. The one runnable `console` example, `sh operator/bin/site init` in step 1, is untouched. It was run by hand in round 0 and printed `site: wrote <tmp>/kumpel/site.env; edit it, then run: site check`, exit 0. The `sh` blocks touch the machine or `~` and are not run.

    Cross-read and found current: `docs/operator-guide/site.md` (links this file and the kept heading *Installing*), `docs/project-guide/operator.md` and `agents.md` (link only the file), `docs/operator-guide/pipeline.md` (names the file).

    Stale text I saw and did not touch:
    - `operator/skill/kumpel/SKILL.md` repeats "Second version, 2026-11-01" and "kumpel-factory v1.2 or later". That is the skill's own file, not a document I may write.
    - The story's Interface line for `docs/checked-documents.txt` and the list part of criterion 3 still name the list line. Journal 6 dropped both, and I may not edit them.

    `check`: check: green
    `secrets`: secrets: green (0.3 s)
    `documents`: documents ok (59.2 s)
20. factory: started docs-review as vm.
