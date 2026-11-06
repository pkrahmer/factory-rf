---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 598
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T13:18:31.986017Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T13:26:55.001541Z'
  stage: acceptance
  run: 9945c6b6ffc64f31b1d53bf9c8650cd7
stories: [F0053-S0001, F0053-S0002, F0053-S0003, F0053-S0004, F0053-S0005, F0053-S0006, F0053-S0007, F0053-S0008, F0053-S0009, F0053-S0010, F0053-S0011, F0053-S0012]
outcome: null
---

# Acceptance of The documents are checked against the code

## Recommendation

**accepted with stories.** The first acceptance's gap is closed. A real `console` block now runs in a real document: the style page's own examples run on every `make documents`. A wrong example in a copied document turns the suite red, and the right one keeps it green. `docs/operator-guide/install.md` can go on the checked list today without a single finding. `make check` is green, and the feature smoke test shows every promised check working. One finding has weight, and it is no broken promise: the settings check compares a `Default` cell with its backticks and a refusal with the colon of `<variable>: <fault>`. So the shapes the guide itself uses give false findings once the rewrite adds those columns. They fail loudly, not silently. Proposed story F0053-S0013 repairs it before the rewrite meets it.

## 1 Scope

Every scope item of `feature.md` has its story, as the first acceptance (F0053-A0001) found: the name check (S0001), the settings check (S0002), the runnable examples (S0003) with their fixtures `checkout` and `instance` (S0006), the checked-files list and the report (S0004), and the agents' rules (S0005). S0007 carries out decision 5. The five stories that A0001 proposed were all started and merged:

- S0008: the `documents` fixture (`tests/conftest.py:610`) is a git repository with one commit, and the style page's two demonstration blocks are `console` again (`docs/project-guide/style.md:22`, `:39`).
- S0009: no counting settings table gives one finding (`NO_SETTINGS_TABLE`, `settings_findings`). A missing *Configuration* section is skipped in `factory.entry.check_documents._settings_guide_findings`.
- S0010: `.log` and `.jsonl` are file names, and `_is_address` makes a text with a `:` before its first `/` no path.
- S0011: the style page names the table shapes the settings check reads, and `README.md:24-26` names the name, settings and example checks, the checked list and the report.
- S0012: the example runner's tests use `ROOMY_LIMIT`. The constants are imported or kept once in `tests/support/check_documents_support.py`.

`feature.md`'s *Stories* list still names only S0001 to S0007, and decision 6 gives the leaves of S0008, S0009 and S0012. That list is the human's file. S0011's intake noted the gap and did not block on it. No story lies outside the scope.

Finding: the goal's second bullet (defaults and refusal messages agree with the settings code) is met by the code, but not for the shapes a writer uses (check 2, sections 5 and 6) → F0053-S0013.

## 2 Feature smoke test

The walk-through of a writer who rewrites the install page. It starts from today's documents. The writer puts `docs/operator-guide/install.md` on the checked list and adds examples on both fixtures, a wrong module, a dead link, a wrong example, a `vm` block, the git address and `factory.log`. Then they rename the settings table's first column, add a defaults table and a refusals table, and fix them. Last, the suite holds them to an example in an unlisted page, and the agents' rules and the area guide lines are checked. The script ran in a temporary clone through the real command, `uv run --project /work/checkout python -m factory.entry.check_documents --root <clone>`. Each step was committed, since the `checkout` fixture exports the committed state. The suite ran with the checkout's interpreter (`/work/checkout/.venv/bin/python -m pytest`), so the checkout's editable install was not touched.

Command: `bash "$d/feature_smoke.sh"` (in a `mktemp -d` folder, since removed). Output:

```text
== 1. today's documents: the style page's own console blocks run, nothing blocks
exit 0
documents ok (0.5 s)
127
0
== 2. install.md goes on the checked list as it is today
exit 0
(no finding for docs/operator-guide/install.md)
== 3. the writer adds examples on both fixtures, a wrong module, a vm block, the address and log file
exit 1
docs/operator-guide/install.md:120: factory.shared.domain.nothing_here does not exist
docs/operator-guide/install.md:121: docs/operator-guide/gone.md does not exist
docs/operator-guide/install.md:133: the example printed 42
Report (not checked yet):
docs/operator-guide/install.md:137: not run (vm)
== 4. the writer fixes the example; the settings table's first column is renamed
exit 1
docs/operator-guide/install.md: no settings table (first column Name or Variable) in Configuration
docs/operator-guide/install.md:135: not run (vm)
== 5. the column is back; a defaults table with a wrong default and a refusals table with an unknown refusal
exit 1
docs/operator-guide/install.md: setting GIT_USER_NAME has the default '`somebody`' in the guide, 'factory' in the settings code
docs/operator-guide/install.md: setting GIT_USER_EMAIL has the default '`factory@noreply.invalid`' in the guide, 'factory@noreply.invalid' in the settings code
docs/operator-guide/install.md: refusal `<variable>: is not an absolute path` is not held by the settings code
docs/operator-guide/install.md: refusal `<variable>: is frobnicated` is not held by the settings code
docs/operator-guide/install.md:147: not run (vm)
== 6. both are corrected
exit 1
docs/operator-guide/install.md: setting GIT_USER_NAME has the default '`factory`' in the guide, 'factory' in the settings code
docs/operator-guide/install.md: setting GIT_USER_EMAIL has the default '`factory@noreply.invalid`' in the guide, 'factory@noreply.invalid' in the settings code
docs/operator-guide/install.md: refusal `<variable>: is not an absolute path` is not held by the settings code
docs/operator-guide/install.md:146: not run (vm)
docs/operator-guide/install.md:146: not run (vm)
== 7. the suite holds the writer to the examples of an unlisted page too
exit 0
docs/operator-guide/install.md: setting GIT_USER_NAME has the default '`factory`' in the guide, 'factory' in the settings code
docs/operator-guide/install.md: setting GIT_USER_EMAIL has the default '`factory@noreply.invalid`' in the guide, 'factory@noreply.invalid' in the settings code
docs/operator-guide/install.md: refusal `<variable>: is not an absolute path` is not held by the settings code
docs/operator-guide/install.md:142: the example printed 42
docs/operator-guide/install.md:146: not run (vm)
4 failed, 7 passed in 2.58s
4 failed, 7 passed in 2.56s
== 8. the agents' rules and the way back from the code
0
1
      7 ok
```

What it shows:
- Sections 1 to 4 are green. The style page's own `console` blocks run with no finding. `install.md` passes the list as it stands, so the git address and `factory.log` are no longer false positives (S0010). On the `instance` fixture, `factory-health` printed `healthy` and `factory-run` gave `<time> settings invalid: FACTORY_INSTANCE: is not a name` with status 2. A missing module, a dead link and a wrong example block in a listed page. The `vm` block is listed and not run. A renamed first column gives the S0009 finding, not silence.
- Sections 5 and 6 are the finding. Correct defaults written in backticks, as `install.md` writes every default today (`` Default `/work/checkout` ``), are reported as wrong. A refusal written as the message `<variable>: <fault>`, as the style page and `install.md` describe it, is "not held". `refusal_findings` passes only the bare fault text (`is not an absolute path` → no finding; `<variable>: is not an absolute path` and `FACTORY_STATE: is not an absolute path` → a finding each). A table naming every setting with its default in backticks gives 17 false findings. The checks fail loudly, so nothing drifts silently, but the rewrite would meet this on its first settings table → F0053-S0013. The doubled `not run` line in section 6 comes from my script: it printed the last line twice.
- Section 7: my script left the step-5 settings findings in `install.md`, and those report lines failed the suite in both runs. In a fresh clone I repeated it with only the example: `41 passed` as found; one wrong `console` block appended to the unlisted `install.md` gave `4 failed, 37 passed` (`test_the_operator_guide_folder_is_checked_per_file[no-stops-section]`, `[no-install-section]`, `[no-configuration-section]`, `[no-index]`); the right one gave `41 passed`. So the suite holds a wrong example in any document, as `style.md:32` says, and a right one keeps it green (S0008).
- Section 8: the first line counted `console` in `agents/agents/documenter.md`. The documenter's rule speaks of "runnable" examples (lines 57, 65), so the count of 0 says nothing. The reviewer's `### Documents` item is there, and the seven area packages name existing guide pages (`factory.entry` names the index).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

From A0001, still open and owned elsewhere: the split of `src/factory/shared/domain/documents.py` (798 lines now) is the human's to schedule; the `instance` fixture's stage image is a placeholder; `runs_the_suite` does not read `make documents` as a suite command.

New from S0008 to S0012:
- S0009 coder (entry 7): the guard that skips the settings check for a missing *Configuration* section has no test of its own. It is covered indirectly: the `no-configuration-section` row of `test_the_operator_guide_folder_is_checked_per_file` compares the whole output, and with no guard it would print the extra finding. Closed.
- S0010 coder (entries 7, 15): `_link_name` keeps its own `://` and `mailto:` tests beside the new `_is_address`. That is two address rules in one module. Small; the split of `documents.py` is the place for it. No story.
- S0010 reviewer note (entry 17): `tests/entry/test_check_documents_todays_names.py` now tests only `named_references`, so it belongs under `tests/shared/domain/`, and it repeats the `top_level` set of `check_documents.py:105`. S0012 tester, coder, reviewer and documenter: `tests/entry/test_check_documents_copies.py:20` still writes the literal `docs/checked-documents.txt`. These are test tidiness, and each needs the human's leave. No story: not worth a run on their own, and the human can add them to a later test story.
- `make duplicates` (run here: `6 new, 39 known, 4 gone`): one of the new ones is the feature's own. `matches` (`src/factory/shared/domain/documents.py:793`, from S0003) is called only by `tests/shared/domain/test_document_examples.py`, because the runner uses `first_difference`. It is dead code in production, unbaselined since S0003. The other five are in other features' code. No story; it belongs with the split.
- Documenters of S0009, S0010 and S0011: stale report lines that the rewrite will meet. `docs/project-guide/machine.md:362` and `README.md:24` name `factory/stage.Containerfile` without `<project>/`, `docs/project-guide/work.md:13` names `factory/agents`, and `docs/operator-guide/machine.md:58` names `planning/cloud-sandbox/`, which does not exist. In the checkout the report holds 128 `does not exist` lines (125 in a clean clone, which has no `.venv` or `.reports`): 84 in `docs/project-guide/README.md` (paths written below `tests/`) and 15 in `docs/project-guide/agents.md`. Those 15 include the deliberate example paths of the write-path rules (`src/..x/a.py`, `docs/CLAUDE.md`), which will need a `<project>/` placeholder or a code block when `agents.md` is listed. This is left for the rewrite, as `feature.md` says.
- S0008 coder (entry 16): other tests that copy `ROOT` without `.git` may need the same change. The tester found none (entry 21). Closed.

## 5 The documentation as a whole

Read from the top as a newcomer, with `make documents` green:
- `README.md:24-26` now names every check of the command, the checked list and the report, and agrees with `docs/project-guide/shared.md`, *The checked documents and the report*. A0001's finding is closed.
- `docs/project-guide/style.md`, *The operator guide*, names the table shapes the settings check reads (S0011), and they agree with `shared.md`, *The settings check*, and with the code. But the page asks for a refusal as "the message in backticks, with a `<placeholder>` for what varies", and the message is `<variable>: <fault>` (`install.md:13`). The check refuses that form (check 2). The page says nothing on backticks in a `Default` cell either, while every default in today's `install.md` is backticked. A writer who follows the guide gets false findings → F0053-S0013.
- `style.md:32` (S0008, the human's answer in S0008 entry 26) says that a wrong example fails `make documents` only in a listed file and fails the suite in any file. Both halves are true (check 2, section 7).
- `docs/operator-guide/install.md:9` still says `operator/vm/setup.sh` "makes the VM". That is the very sentence the feature's Goal names as untrue. No check of this feature can catch it, because it is prose about behaviour. It is the rewrite's (out of scope here). No story.
- `docs/project-guide/README.md:62` says `support/check_documents_support.py` holds `MISSING_LINES`. It now also holds `TOPIC_FILES`, `REPORT_HEADING` (S0012), `TIME_LINE` and `line_of`. That is minor, in a page the rewrite takes over. No story.
- `shared.md:149` ("Today's operator guide has no `Default` column and no refusal table, so it gives no settings finding") is still true. No contradiction between the stories' texts found.

## 6 Decisions taken for the human

From `feature.md`, accepted with the feature unless revisited: (1) the checks live in `make documents`; (2) report everywhere, block only the files on `docs/checked-documents.txt`; (3) an example says where it runs, and `vm`, `github`, `model` and `suite` blocks are listed, not run; (4) `docs/decisions.md` and `docs/runs/` are exempt; (5) relative links, one guide line per area package; (6) the leaves for S0008, S0009 and S0012. A0001's report lists the answers of S0001 to S0007 in full. They stand unchanged.

Taken in S0008 to S0012, by the human's answers:
- S0008 (19): the leave to make the copy in `test_todays_documents_with_the_first_list_give_a_report_and_pass` (S0004's test) a git repository.
- S0008 (26): option (a). The writer is told that a wrong example fails the suite in any document the check reads, and the fixture's machinery stays out of the style page.
- S0012 (4): `CHECKED_DOCUMENTS` and `SETTINGS_FILE` are imported, not repeated, and `REPORT_HEADING` is kept once.

Defaults nobody chose, for the human to accept or revisit:
- S0009 coder: the skip for a missing *Configuration* section sits in the entry (`_settings_guide_findings`), not in `settings_findings`. This keeps the domain signature the Interface fixed. It also skips the refusal check there.
- S0010 coder: one rule (`_is_address`, a `:` before the first `/`) replaces the old `://` test for paths.
- Still open from A0001: settings findings carry no line number; the example time limit is 60 s per command; a block running `make documents` is not read as `suite`.
- The settings check compares a `Default` cell and a refusal piece literally. Nobody chose this for the backticked forms; F0053-S0013 proposes the reverse.

Earlier tests changed, with their leaves (from the reviewers' *Earlier tests* lines):
- S0008: `tests/conftest.py` (fixture `documents`), feature decision 6. `tests/entry/test_check_documents_checked_files.py`, the human's leave in entry 19.
- S0009: `tests/shared/domain/test_document_settings.py` (row `no-settings-table`) and `tests/support/document_texts.py` (`operator_install` gets a settings table), decision 6 through the Interface.
- S0010: none needed. Rows were added to `tests/shared/domain/test_document_references.py`.
- S0011: none.
- S0012: `tests/shared/adapters/test_document_examples.py`, decision 6. `tests/entry/test_check_documents_checked_files.py`, `tests/entry/test_check_documents_copies.py` and `tests/support/check_documents_support.py`, the standing leave to move a shared helper plus journal 4. `tests/entry/test_check_documents_operator_guide.py`, `tests/entry/test_check_documents_references.py` and `tests/hosting/adapters/test_instance_fixture.py`, journal 4 and decision 6.

Every changed earlier test has its leave named. No finding.

## 7 The slow checks

The project offers nothing beyond `make check` that applies: `make duplicates` is the coder's record (run here, check 4), `make documents` ran above, and `make mutants` is check 3's. `make check` ran green as I found it (`test: green (104.4 s)`, coverage 99.22 %, `check: green`). `.reports/junit.xml` holds 10,730 test cases. The slowest take about 10 s each, the time-limit tests of other features (`test_podman_timeout_status`, `test_process_session::test_time_limit_ends_every_process_of_the_group`). Among the feature's 621 test cases (19.7 s together), the slowest is `test_document_examples::test_the_folder_and_the_home_are_gone_once_the_document_has_run[past-the-limit]` at 10.0 s. S0012 gave its command `ROOMY_LIMIT`, because the command must write its record before it is killed, as `CLAUDE.md` asks. That is the cost of the rule, not a fault. The next is `test_todays_documents_with_the_first_list_give_a_report_and_pass` (1.2 s).

Disk: from the previous record (`disk start`: 23.0 GB free, 1.4 GB used under `/srv/factory/vm`) to this acceptance (22.2 GB free, 1.4 GB used), the factory's used space is unchanged. The state and `/tmp` hold 0.0 GB at both. The 0.8 GB less free space is on the shared filesystem, outside the factory's folders. The feature's changes, a few source, test and document files, explain none of it.

## 8 Cost

The stories cost 152 runs, 202.3 min, 1190 turns and $44.07, plus one run of unknown cost (S0002's crash, as A0001 found). S0001 to S0007 cost 106 runs and $33.98 (A0001). The five repair stories cost 46 runs and $10.09: S0008 14 runs, 14.3 min, $3.18; S0009 10 runs, $2.29; S0010 10 runs, $2.11; S0011 5 runs, $1.26; S0012 7 runs, $1.25. S0003 still stands out over the whole feature ($10.23, 26 runs, four review rounds, a docs stall). Among the repairs, S0008 cost the most. Its docs stage stalled once (entry 12): S0004's own copy of the repository was not a git repository either, and that needed a leave the Interface had not named (entries 16 to 19). Its review then found that criterion 5's lesson was false and asked the human which truth should hold (entries 25, 26). S0009 and S0010 each took one extra test round for a reviewer's test finding.

Human interventions: 19 questions answered (17 questions, 2 round caps), 1.2 h waited. Three answers came after A0001 (S0008 two, S0012 one), and S0009, S0010 and S0011 needed none. S0003 needed the human most over the whole feature, with five answers, most of them leaves for earlier tests. Since A0001, S0008 needed the human most, for the leave and for the truth of criterion 5.

## Proposed stories

- `F0053-S0013-the-settings-check-reads-a-backticked-default-and-a-refusal-with-its-variable.md`: the `Default` cell is read through its backticks like the name cell, and a refusal's pieces lose their surrounding `:` and whitespace. Then the shapes the guide and the style page use pass, and the rewrite's first settings table is not buried in 17 false findings.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0053-S0013)

   1 Scope: every scope item has its story, and the five repairs from A0001 (S0008 to S0012) are merged. The only gap is in the goal's second bullet: defaults and refusals are compared, but not in the shapes the guide uses (→ S0013).
   2 Feature smoke test: ran in a temporary clone through `check_documents --root` and the suite. Green for every promise. The style page's `console` blocks run. `install.md` passes the list as it stands. Both fixtures work. A wrong module, a dead link and a wrong example block. `vm` is listed and not run. A renamed first column gives the S0009 finding. A wrong example in an unlisted page fails the suite (`4 failed, 37 passed`), and the right one gives `41 passed`. The finding: a correct default in backticks and a refusal written as `<variable>: <fault>` are false findings, 17 of them for a full backticked defaults table.
   3 Mutation testing: by sweep, not run here.
   4 Noticed: still untouched are `_link_name`'s own address tests beside `_is_address`, the dead `matches` in `documents.py` (`make duplicates`), the placement and repeated `top_level` of `test_check_documents_todays_names.py`, and the literal at `test_check_documents_copies.py:20`. No stories for these; the split of `documents.py` stays the human's. The S0009 guard is covered indirectly.
   5 Documentation: the README and the style page now agree with the code on what is checked. The style page's refusal and default advice leads into the S0013 false findings. `install.md:9` still says setup.sh "makes the VM", which is prose and the rewrite's. `docs/project-guide/README.md:62` is minor and stale.
   6 Decisions: the six decisions of `feature.md`, the human's answers in S0008 (19, 26) and S0012 (4), and the defaults nobody chose (where the S0009 guard sits, the single `_is_address` rule, settings findings without a line number, the 60 s limit, the literal comparison of defaults and refusals). Every changed earlier test has its leave named, so no finding.
   7 Slow checks: nothing beyond `make check`, which is green (104.4 s, 99.22 %). The feature's slowest test is the `past-the-limit` row of the example runner, at 10 s, which is the cost of the ROOMY_LIMIT rule. Disk used under /srv/factory/vm is unchanged at 1.4 GB. The 0.8 GB less free space is outside the factory's folders.
   8 Cost: 152 runs, 202.3 min, $44.07 + 1 unknown. The repairs cost 46 runs and $10.09. S0003 is still the outlier ($10.23). Among the repairs, S0008 cost most ($3.18): a docs stall, an unnamed leave and a false criterion. 19 answers in all (17 questions, 2 round caps), 1.2 h waited, 3 of the answers since A0001.
