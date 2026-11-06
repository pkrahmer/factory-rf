---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 592
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T11:24:25.946306Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T11:35:10.566466Z'
  stage: acceptance
  run: 30d861d67cbf4ac68a8b6e038096f289
stories: [F0053-S0001, F0053-S0002, F0053-S0003, F0053-S0004, F0053-S0005, F0053-S0006, F0053-S0007]
outcome: null
---

# Acceptance of The documents are checked against the code

## Recommendation

**not accepted.** Every check the feature promised exists and works: the feature smoke test below is green, and so is `make check`. But no document can hold a runnable example. The shared test fixture `documents` copies the real documents into a folder that is no git repository, where neither fixture can be prepared. So one `console` block in any checked document turns five rows of `tests/entry/test_check_documents_operator_guide.py` red. I reproduced this in a clone (`5 failed, 7 passed`). S0003's docs stage stalled on it, and the style page now shows its own examples as `text`. The documenter's new rule (S0005) asks for exactly those blocks, so the goal's third bullet and the rewrite that depends on it are not reached. Proposed story F0053-S0008 is the repair. If the human would rather merge and take S0008 first, merging keeps the five proposed stories, and closing drops them.

## 1 Scope

Each of the five scope items has its story: the name check (S0001), the settings check (S0002), runnable examples with the fixtures `checkout` (S0003) and `instance` (S0006), the checked-files list and the report (S0004), and the agents' rules (S0005). S0007 (each area's package names its guide page) carries out feature decision 5 and is in the story list, so it is inside the feature. The human's change at S0005's merge is in place: `factory/story-form.md`'s docs criterion now says "what the reader must know afterwards, not the sentences to write". I read the code the stories name: `src/factory/shared/domain/documents.py` (773 lines), `src/factory/entry/check_documents.py`, `src/factory/shared/{application,adapters}/document_examples.py`, `src/factory/hosting/adapters/{checkout,instance}_fixture.py`, and `agents/agents/{documenter,reviewer,intake}.md`.

Findings:
- **Goal not reached in practice (weight: blocks acceptance).** No document the check reads holds a `console` block today (`grep -rn '^```console' docs README.md` prints nothing), and none can. A block in a real document makes `test_the_operator_guide_folder_is_checked_per_file` red in the tests' non-git copy, because the `checkout` fixture cannot be prepared there (S0003 journal 56 and 58). I appended a `$ echo hi` / `hi` block to `docs/project-guide/shared.md` in a clone and ran that test module with `tests/entry/test_check_documents.py`: `5 failed, 7 passed`. The mechanism runs on planted documents (check 2), but the documents themselves cannot use it. → F0053-S0008.
- **Defaults and refusals are compared nowhere yet.** Today's `install.md` tables are `Variable | Required | Meaning`, with the defaults and refusals written in prose. So the settings check compares names only (`docs/project-guide/shared.md`, *The settings check*, says so). This is by the human's answer (S0002 journal 4): the rewrite brings the `Default` column. But the style page does not name the exact header cells the check reads, and if the rewrite misses them, the check compares nothing and says nothing (criterion 6). → F0053-S0009, F0053-S0011.

## 2 Feature smoke test

The walk-through of a writer of the documents. Today's documents give a report and nothing blocks. A page on the checked list gets runnable examples on both fixtures, a missing name, a missing link, a wrong example, an unknown fixture, a `vm` block and a suite block. Then the settings table loses a row while `install.md` is unlisted, and after that `install.md` and `docs/decisions.md` are listed. Last come the agents' rules and the area guide lines. The script ran in a temporary clone of the checkout, through the real command `uv run python -m factory.entry.check_documents --root <clone>`. Each stage committed its change, because the `checkout` fixture exports the committed state.

Command: `bash "$tmp/feature_smoke.sh"` (the script was written in a `mktemp -d` folder; its document holds the blocks named above). First run:

```text
== 1. today's documents: report only, nothing blocks
exit 0
127
documents ok (<s> s)
== 2. a listed page with runnable examples, a missing name and a wrong example
exit 1
docs/project-guide/style.md:150: factory.shared.domain.nothing_here does not exist
docs/project-guide/style.md:150: docs/project-guide/gone.md does not exist
docs/project-guide/style.md:163: the example printed one
docs/project-guide/style.md:170: the example printed 2026-11-06T11:29:04Z settings invalid: FACTORY_INSTANCE: is not a name
docs/project-guide/style.md:175: no fixture nowhere
docs/project-guide/style.md:179: not run (vm)
docs/project-guide/style.md:184: not run (suite)
0
== 3. the settings table loses a row: reported while install.md is unlisted, blocking once listed
exit 0
Report (not checked yet):
docs/operator-guide/install.md: setting GIT_USER_NAME is read by the settings code and missing from the guide
documents ok (<s> s)
exit 1
docs/checked-documents.txt: docs/decisions.md is no document of the check
docs/operator-guide/install.md:71: git@github.com:owner/project.git does not exist
docs/operator-guide/install.md: setting GIT_USER_NAME is read by the settings code and missing from the guide
== 4. the agents' rules and the way back from the code
1
1
1
8
guides checked
```

The line-170 finding was my script's fault, not the feature's. `factory-run` puts a time before its refusal, and the S0006 test expects `<time> settings invalid: ...` (`tests/hosting/adapters/test_instance_fixture.py:74`); S0006's criterion 2 leaves out the time, which is loose but harmless. With `<time> ` in the expected line, section 2 printed:

```text
== 2. a listed page with runnable examples, a missing name and a wrong example
exit 1
docs/project-guide/style.md:150: factory.shared.domain.nothing_here does not exist
docs/project-guide/style.md:150: docs/project-guide/gone.md does not exist
docs/project-guide/style.md:163: the example printed one
docs/project-guide/style.md:175: no fixture nowhere
docs/project-guide/style.md:179: not run (vm)
docs/project-guide/style.md:184: not run (suite)
0
```

Every behaviour the feature promised showed. The two blocks that share one folder passed (`note.txt` written in one block is there in the next). `<now>` matched `date`. The `instance` fixture printed `healthy` and gave the real refusal with exit 2. The wrong example, the unknown fixture, the missing module and the missing link blocked in a listed page. `vm` and `suite` blocks were listed as not run. A settings finding is only reported in an unlisted file and blocks once the file is listed. A listed `docs/decisions.md` blocks. All eight packages name an existing guide page. Green. Two side observations: the settings findings carry no line number (`docs/operator-guide/install.md: setting ...`), unlike every other finding, and listing `install.md` is at once blocked by a false positive, the git address on line 71 (→ F0053-S0010).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

From the coder, documenter and reviewer entries, with who owns them now:
- S0003 docs stall (journal 56, 58): runnable blocks in a real document break the suite's non-git copies. → F0053-S0008.
- S0002 coder and reviewer: a settings table that loses its `Name`/`Variable` header passes silently (criterion 6 was added by the reviewer to keep earlier tests green, not by the human). The suggestion to raise it at S0004 was not taken up. → F0053-S0009.
- S0001 reviewer and documenter: `factory.env`/`factory.local.env` and `git@host:owner/name.git` were false positives. S0004 fixed the first; the git address and `factory.log` are still reported. → F0053-S0010.
- S0003 reviewer (journal 53, last round): the example runner's tests give every command 1 s and a local `ELAPSED_BOUND_SECONDS = 15`, against `CLAUDE.md`'s `ROOMY_LIMIT` rule, which is a flake risk under `make test`. S0004 reviewer: `CHECKED_LIST` and `REPORT_HEADING` are written again in tests (three modules). S0006 reviewer: `SETTINGS_FILE` is repeated in its test. → F0053-S0012.
- S0003 coder: `documents.py` keeps growing (590, then 690 lines during the story; 773 now). The human left the split for later (S0003 journal 17). No story: it is the human's to schedule.
- S0003 coder: `runs_the_suite` does not read `make documents` as a suite command. A block running it would rerun the check inside the check until the 60 s limit ends it. No story: no document does it, and the limit bounds it.
- S0003, S0002 (several entries): the archived stories' `## Interface` sections are stale in places: S0002 does not name `GuideTable.heading`, `guide_tables` or `refusal_findings` (entry 9); S0003 says "an adapter test with the fake containers". No stage could fix them. They are under `done/` now and stay as history. The code and `docs/project-guide/shared.md` describe what was built.
- S0006 coder and documenter: the `instance` fixture's stage image (`localhost/factory-stage:docs`) and image id are placeholders, so an example cannot start a container. `docs/project-guide/style.md` says so. No story.
- S0002 documenter: `docs/project-guide/README.md:27` says the settings are described in `hosting.md` and `machine.md`, a claim nobody checked. Left for the rewrite.
- S0005 coder: `docs/project-guide/agents.md` named the intake's route step as 6, now 7. I find no such stale number today (`grep "step 6"` gives nothing on the route step). Closed.
- S0004 coder: the take dropped the coder's `docs/checked-documents.txt` (outside its write paths), and the documenter wrote it. Closed, and the file holds the two pages.

## 5 Documentation

Read from the top as a newcomer, with `make documents` run on the repository (it prints 127 report lines and `documents ok (0.4 s)`):
- `README.md` (line 22) describes `factory.entry.check_documents` by the checks it made before this feature, plus the examples. It names neither the name and settings checks nor the checked files and the report, though it says the command "ends with `documents ok` when nothing blocks". → F0053-S0011.
- `docs/project-guide/style.md` says settings are tables with the columns "name, what it does, default, example". The settings check counts only a first column `Name`/`Variable`, compares only under a `Default` cell, and reads refusals only under `The refusals` with first column `Refusal`. Those rules are written only in `shared.md`, the machinery page. → F0053-S0011.
- `docs/project-guide/style.md`, *Runnable examples*: the two demonstration blocks are fenced as `text`, "so that they are not run in every copy of this guide". The real reason is the suite failure of check 1. → F0053-S0008 makes them `console` again.
- The report lists real stale names that the rewrite will meet, of two kinds. One: 84 paths in `docs/project-guide/README.md` are written relative to `tests/` (`support/time_limits.py`), against style rule 8. Two: paths of a project's repository are written without `<project>/`, such as `factory/stage.Containerfile` in `README.md:24`, `docs/operator-guide/machine.md` and `stops.md`, and `factory/agents/`. Rewriting is out of scope here (the next feature), so there is no story. The list is in the report of `make documents`.
- The four F0053 entries in `docs/decisions.md` (S0006, the feature's decisions 1 to 4, S0005) agree with `feature.md`. `docs/project-guide/agents.md` describes the reviewer's `### Documents` item (line 309), and `docs/project-guide/README.md` has the sentence on the area guide lines. No contradiction between the stories' texts found.

## 6 Decisions taken for the human

From `feature.md`, accepted with the feature unless revisited: (1) checks live in `make documents`, not `make check`; (2) report everywhere, block only the files on `docs/checked-documents.txt`; (3) an example says where it runs, `vm`/`github`/`model`/`suite` blocks are listed and not run; (4) `docs/decisions.md` and `docs/runs/` are exempt; (5) relative links to files, one guide line per area package.

Taken in the stories, by the human's answers:
- S0001 (4): `Reference(document, line, name, kind)`, `named_references(document, text, top_level)`; relative links are resolved from the document's folder.
- S0002 (4, 9): defaults are compared only in a table with a `Default` column; refusals are read only from a table under `The refusals` with first column `Refusal`; `GuideTable` carries its nearest heading.
- S0003 (4, 9, 12, 17, 43): `examples` returns `Examples(runnable, skipped)`; the runner uses real short commands in `tmp_path`, without containers; a fourth review round was granted at the round cap; the split of `documents.py` was left for later.
- S0004 (4, 11): a listed path that does not exist, or is no checked document, blocks; the name check skips `$` texts and file-named `factory.*` names, and reads node ids up to `::`; the first list is the style page and the glossary.
- S0005 (4, 11, 33): the reviewer's *Documents* item is a `###` subsection; a fourth review round was granted at the round cap.
- S0006 (4, 11): `InstanceFixture(git: GitCli)`; `INSTANCE_FIXTURE` is a public constant beside `DEFAULT_FIXTURE`; no fake hosting service in the production wiring (decision log entry).

Defaults nobody chose, for the human to accept or revisit:
- S0002 criterion 6, added by the reviewer: a guide without a settings table gives no settings finding (→ F0053-S0009 proposes the reverse).
- Settings findings name `install.md` without a line number.
- The example time limit is 60 s per command, and an example that runs past it ends the document's later blocks.
- A block that runs `make documents` is not read as `suite`.

Earlier tests changed, with their leaves (from the reviewers' *Earlier tests* lines):
- S0001: `tests/entry/test_check_documents_operator_guide.py`: human's leave, journal 11 (2a).
- S0002: `tests/conftest.py` and `tests/entry/test_check_documents_operator_guide.py`: standing leave (the `documents` fixture moved).
- S0003: `tests/entry/test_check_documents.py`: human's leave, journals 9 (1) and 12 (1). `tests/entry/test_check_documents_guide_files.py` and `tests/entry/test_check_documents_operator_guide.py`: journal 17 (2). `tests/guards/test_wrapper_search.py`: journal 17 (1). `tests/entry/test_check_documents_references.py`, `tests/support/check_documents_support.py` and `tests/support/document_texts.py`: standing leave.
- S0004: `tests/entry/test_check_documents_operator_guide.py` and `tests/entry/test_check_documents_references.py`: human's leave, journal 11. `tests/shared/domain/test_document_references.py`: none needed (rows added).
- S0005: `tests/agent_files/test_claude_agent_texts_review_groups.py`: the human's leave in the Interface (2026-11-05). `tests/agent_files/test_claude_agent_texts_mutants.py`: human's answer, journal 11.
- S0006, S0007: none (new test files only).

Every changed earlier test has its leave named. No finding.

## 7 Slow checks

The project offers nothing beyond `make check` that applies here: `make duplicates` is the coder's record, `make documents` was run above, and `make mutants` is check 3's. `make check` ran green as I found it (`test: green (103.9 s)`, coverage 99.22 %, `check: green`). In `.reports/junit.xml` (10,705 test cases), the slowest tests are the time-limit tests of other features at about 10 s each (`test_podman_timeout_status`, `test_process_session::test_time_limit_ends_every_process_of_the_group`, `test_claude_runtime_provider_limit`). The feature's own tests are cheap. The slowest are `test_shared_bodies[remote_document]` (2.4 s), and the two limit rows of `tests/shared/adapters/test_document_examples.py` (1.0 s each, their 1 s limit, see F0053-S0012). Disk: from the feature's start (23.5 GB free, 1.4 GB used) to this acceptance (22.8 GB free, 1.4 GB used), the used space of `/srv/factory/vm` is unchanged. The 0.7 GB less free space is on the shared filesystem that `/tmp` and the state also sit on, which hold 0.0 GB, so it is outside the factory's folders. The feature's changes, a few source and document files, explain none of it, and none of it shows in the factory's own use.

## 8 Cost

The stories cost 106 runs, 158.8 min, 886 turns and $33.98, plus one run of unknown cost (in S0002, whose doing stage crashed once and stalled once, journals 13 and 15). By story: S0001 14 runs, $4.27; S0002 13 runs, $4.18 + unknown; S0003 26 runs, 45.2 min, $10.23; S0004 14 runs, $4.63; S0005 19 runs, $5.86; S0006 14 runs, $3.76; S0007 6 runs, $1.05. S0003 stands out: almost a third of the cost, four review rounds and a docs stall. Its journal shows why. Three times the tester or coder stopped for the human's leave to change earlier tests (journals 9, 12, 17). The reviewer then found test gaps over four rounds, mostly rows for the failing sides (journals 25, 33, 41, 45), and the round cap was passed (journal 42). The docs stage stalled on the runnable-block problem of check 1 (journal 56). S0005 also passed the round cap (journal 32), over the place of `make documents` in the documenter's steps.

Human interventions: 16 questions answered (14 questions, 2 round caps), 1.1 h waited. S0003 needed the human most, with five answers. Most of them were leaves for earlier tests that the new examples broke, the same coupling that S0008 now proposes to remove. S0007 needed none.

## Proposed stories

- `F0053-S0008-a-runnable-example-in-the-documents-keeps-the-suite-green.md`: the tests' copy of the documents becomes a git repository, so that a real `console` block runs instead of breaking the suite. This is the repair the recommendation rests on.
- `F0053-S0009-a-configuration-section-without-its-settings-table-is-a-finding.md`: the settings check reports a missing settings table instead of silently comparing nothing (reverses S0002's criterion 6, a reviewer's default).
- `F0053-S0010-the-name-check-reads-log-files-and-git-addresses.md`: `factory.log`, `.jsonl` names and scp-style git addresses stop being false positives. One of them blocked `install.md` on the list in check 2.
- `F0053-S0011-the-guides-say-what-shapes-the-checks-read.md`: the style page names the table shapes the settings check reads, and the README names what the document check checks. Documents only.
- `F0053-S0012-the-example-runners-tests-use-the-roomy-limit.md`: the example runner's tests use `ROOMY_LIMIT`, and the repeated test constants are kept once. Tests only.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: not accepted; 5 stories proposed (F0053-S0008 to F0053-S0012)

   1 Scope: every scope item has its story, and S0007 carries out decision 5. The gap: no document can hold a runnable example yet. One `console` block in a real document turns 5 rows of `tests/entry/test_check_documents_operator_guide.py` red, because the `documents` fixture's copy is not a git repository (reproduced in a clone: 5 failed, 7 passed). This is the S0008 repair. Defaults and refusals are not compared until the rewrite adds the table shapes.
   2 Feature smoke test: green. I ran it in a temporary clone through `check_documents --root`. It covered: report only on today's documents, both fixtures with shared folders across blocks and the placeholders, blocking in a listed page, `vm`/`suite` blocks listed as not run, a settings finding reported while `install.md` is unlisted and blocking once listed, a listed `decisions.md` refused, the agents' rules, and 8 guide lines. One finding of the script's own, fixed with a `<time>` placeholder.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the silent pass with no settings table (S0009); false positives for `factory.log` and git addresses (S0010); 1 s limits in the example runner's tests and repeated test constants (S0012). Owned elsewhere or closed: the `documents.py` split (the human's), stale Interfaces in `done/`, placeholder stage image, `make documents` not read as a suite command.
   5 Documentation: the README describes the check as it was before this feature. The style page does not name the header cells the settings check reads, and shows its examples as `text` (S0011, S0008). The 127 report lines (84 paths relative to `tests/`, project paths without `<project>/`) are left for the rewrite.
   6 Decisions: the five decisions of `feature.md`, the human's answers per story, and four defaults nobody chose are listed for the human. Every changed earlier test has its leave named, so no finding.
   7 Slow checks: nothing beyond `make check`, which is green (test 103.9 s, coverage 99.22 %). The slowest tests are the 10 s limit tests of other features. Disk use under /srv/factory/vm is unchanged at 1.4 GB; the 0.7 GB less free space is outside the factory's folders.
   8 Cost: 106 runs, 158.8 min, $33.98 + 1 unknown. S0003 stands out ($10.23, 26 runs, four review rounds, a docs stall, 5 of the 16 human answers, most of them leaves for earlier tests). 16 answers in all (14 questions, 2 round caps), 1.1 h waited.

   Side effects of my run: running pytest in the clone pointed the checkout's `.venv` editable install at the clone. `uv sync --frozen` restored it to /work/checkout, checked through the `.pth` file and `make documents`. The temporary folder is removed.
