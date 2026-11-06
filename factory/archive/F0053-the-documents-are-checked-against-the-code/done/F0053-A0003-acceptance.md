---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 600
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T13:48:23.509724Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T13:59:22.296410Z'
  stage: acceptance
  run: 11d55e7382104c358e8c76cff18f771d
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-06T14:03:20.179913Z'
  stage: done
stories: [F0053-S0001, F0053-S0002, F0053-S0003, F0053-S0004, F0053-S0005, F0053-S0006, F0053-S0007, F0053-S0008, F0053-S0009, F0053-S0010, F0053-S0011, F0053-S0012, F0053-S0013]
outcome: accepted
---

# Acceptance of The documents are checked against the code

## Recommendation

**not accepted.** The second acceptance's finding is closed: a settings table written by the style page, with backticked defaults and refusals in the form `<variable>: <fault>`, passes the check, and wrong values block a listed page (check 2, sections 2 and 3). But the feature smoke test ends red at the gate. A right document turns `make check` red in two ways that the feature itself invites. The first is one `console vm` block in any document, which decision 3 asks for and F0054's install story requires. The second is a `checkout` example that reads a repository file, which the style page says the fixture holds. The cause is the suite's copy of the documents (S0008), not the checks: `make documents` is right and `make check` is green today. But the rewrite's first story would stall on it. Proposed F0053-S0014 repairs it. If the human would rather take the story than close, merging this pull request brings the story into the backlog.

## 1 Scope

Every scope item has its story, as A0001 and A0002 found: the name check (S0001), the settings check (S0002), the runnable examples (S0003) with the fixtures `checkout` and `instance` (S0006), the checked list and the report (S0004), and the agents' rules (S0005). S0007 carries out decision 5. Since A0002, the one story it proposed, S0013, is merged. A `Default` cell is read through its backticks by `_backticked_or_plain` (`src/factory/shared/domain/documents.py`, `_default_findings`). Each refusal piece is stripped of whitespace and `:` at both ends (`_PIECE_EDGES`, `_is_held`). No story lies outside the scope. `feature.md`'s *Stories* list still names only S0001 to S0007. That list is the human's file.

Finding: the goal "a marked example is run by the check, like a notebook that the test runner executes" is reached in `make documents`. But the test runner's own guard (S0008) refuses right documents (check 2, section 4) → F0053-S0014.

## 2 Feature smoke test

The walk-through of a writer who rewrites the install page as F0054-S0001 will. They put `docs/operator-guide/install.md` on the checked list. They replace its settings table with the style page's shape (`Name | What it does | Default | Example`, every default typed by hand in backticks or `none`). They add *The refusals* with three messages in the form `<variable>: <fault>`, a sentence naming the settings module, an `instance` example (`factory-health`, then a refusal of `factory-run`), a `checkout` example and a `vm` block. First they get four things wrong (a default, a refusal, the module name, the example's output), then they correct them. Last, the suite reads the page, and the agents' rules and the area guide lines are checked. The script ran in a temporary clone through the real command, `uv run --project /work/checkout python -m factory.entry.check_documents --root <clone>`. Each step was committed, because the `checkout` fixture exports the committed state. The clone has `gc.auto 0`: in an earlier run, git's background `gc --auto` after a commit (the checkout holds 29,907 loose objects) repacked the clone while the `instance` fixture cloned it, and this gave a one-off `fixture instance could not be prepared`. In the check container nothing commits during the check, so this is my harness and not the feature. The suite ran with the checkout's interpreter and its `bin` on `PATH`, as `uv run` gives it.

Command: `bash smoke.sh <folder of edit.py>` (both in a temporary folder, since removed). Output:

```text
== 1. today's documents, as merged
exit 0
Report (not checked yet):
documents ok (0.5 s)
(124 report lines 'does not exist' left out)
== 2. install.md listed, Configuration rewritten by the style page, with a wrong default, refusal, module and example
exit 1
docs/operator-guide/install.md:72: factory.shared.domain.setings does not exist
docs/operator-guide/install.md: setting GIT_USER_NAME has the default '`somebody`' in the guide, 'factory' in the settings code
docs/operator-guide/install.md: refusal `<variable>: is frobnicated` is not held by the settings code
docs/operator-guide/install.md:84: the example printed 2026-11-06T13:54:54Z settings invalid: FACTORY_INSTANCE: is not a name
Report (not checked yet):
docs/operator-guide/install.md:94: not run (vm)
(124 report lines 'does not exist' left out)
== 3. the writer corrects the four
exit 0
Report (not checked yet):
docs/operator-guide/install.md:93: not run (vm)
documents ok (1.5 s)
(124 report lines 'does not exist' left out)
== 4. the suite reads the rewritten page
E             + docs/operator-guide/install.md:89: the example printed ls: cannot access 'operator/vm/setup.sh': No such file or directory
E             + docs/operator-guide/install.md:93: not run (vm)
[the same two lines for each of the four rows below, with the lines shifted by the row's change]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-stops-section]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-install-section]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-configuration-section]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-index]
4 failed, 5 passed in 5.71s
== 5. the agents' rules and the way back from the code
1
1
shared docs/project-guide/shared.md True
hosting docs/project-guide/hosting.md True
work docs/project-guide/work.md True
agents docs/project-guide/agents.md True
watching docs/project-guide/watching.md True
machine docs/project-guide/machine.md True
pipeline docs/project-guide/pipeline.md True
entry None False
```

A second script isolated the `vm` cause. In a fresh clone it appended only one `console vm` block (`$ systemctl is-active factory-vm` / `active`) to `docs/project-guide/machine.md`, an unlisted page, and committed it. Then it ran the check and `python -m pytest tests/entry/ -k check_documents`:

```text
Report (not checked yet):
docs/project-guide/machine.md:462: not run (vm)
documents ok (0.5 s)
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-stops-section]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-install-section]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-configuration-section]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-install-file]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-index]
5 failed, 76 passed, 525 deselected in 4.75s
```

What it shows:
- Sections 1 to 3 are green, and S0013 works: hand-typed backticked defaults and `<variable>: <fault>` refusals give no finding. A wrong default, an unknown refusal, a misspelt module and a wrong example each block the listed page. The `instance` fixture runs `factory-health` and shows `factory-run`'s refusal with status 2. The `vm` block is listed, not run, and does not block.
- Section 4 is the finding. `test_the_operator_guide_folder_is_checked_per_file` (`tests/entry/test_check_documents_operator_guide.py:73`) compares the whole output and leaves out only the `does not exist` lines and the report heading (line 93). A `not run (vm)` line, which `make documents` never blocks on, fails every row that compares output. The suite's copy (`documents`, `tests/conftest.py:610`) holds only `README.md` and `docs/`, not the tracked files that the `checkout` fixture exports. So a right `ls operator/vm/setup.sh` fails in the suite. Both are right documents, and both turn `make check` red. F0054-S0001 says "Every command the file shows is a runnable example or is marked for the VM, GitHub or a model", so its docs stage would meet this at once → F0053-S0014.
- Section 5: the reviewer's `### Documents` item is there, the documenter speaks of runnable examples, and the seven area packages name existing guide pages. `factory.entry` names `docs/project-guide/README.md` (my pattern took lowercase names only, hence `None`).

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

New from S0013:
- Coder (entry 7) and reviewer (entry 17): a backticked `` `none` `` also counts as no default, which follows from reading the cell as the name cell is read. Listed under 6. No story.
- Documenter (entry 19): it named `docs/project-guide/machine.md:362` (`factory/stage.Containerfile`) and `docs/project-guide/work.md:13` (`factory/agents`) as stale. It also wrote that the report lists "two lines" of `does not exist`. The report holds 128 such lines in the checkout (124 in a clean clone), as A0002 counted. The two named lines are real. The count in the journal is wrong, but it changes nothing. The paths are the rewrite's.

Still open from A0001 and A0002, owned elsewhere or below a story: `src/factory/shared/domain/documents.py` is 804 lines now, and its split is the human's to schedule. `matches` (`documents.py:799`) is still called only by a test. `make duplicates` stays at `6 new, 39 known, 4 gone` (S0013 coder), unchanged since A0002. `_link_name` and `_is_address` are two address rules in one module. `tests/entry/test_check_documents_todays_names.py` belongs under `tests/shared/domain/`, and `tests/entry/test_check_documents_copies.py:20` writes the list's path as a literal. The 84 report lines of `docs/project-guide/README.md` and the deliberate example paths of `docs/project-guide/agents.md` are left for the rewrite.

Mine: git's background `gc --auto` can break a `GitCli.clone_bare` of a repository that is being repacked (check 2). It does not happen in a check container. No story.

## 5 The documentation as a whole

- `docs/project-guide/style.md`, *The operator guide*, and `docs/project-guide/shared.md`, *The settings check*, now agree with each other and with the code on both S0013 rules. A0002's finding is closed.
- `style.md:32`: "The test suite runs the examples of every document the check reads ... Every example must be right wherever it stands." *The fixture* says that `checkout` is "a copy of the repository's tracked files". In the suite it is not, and a skipped block fails the suite (check 2). A writer who follows the page gets a red `make check` → F0053-S0014, whose docs criterion repairs the paragraph.
- `shared.md`, *The settings check*, says that the settings and refusal findings, "like the name lines", "do not change the exit status". *The checked documents and the report*, in the same file, says that they block a listed document, and section 2 shows they do. This is a stale sentence from before the checked list, in a page the rewrite takes over. It misleads an agent, not an operator. No story: the human can name it in F0054's `shared.md` story.
- `docs/operator-guide/install.md:9` still says `operator/vm/setup.sh` "makes the VM", the sentence the Goal names. That is prose, which is the rewrite's (out of scope).
- `docs/project-guide/README.md:62` still names only `MISSING_LINES` of `tests/support/check_documents_support.py` (A0002). That is minor, and the rewrite's.

## 6 Decisions taken for the human

From `feature.md`, accepted with the feature unless revisited: (1) the checks live in `make documents`; (2) report everywhere, block only the files on `docs/checked-documents.txt`; (3) an example says where it runs, and `vm`, `github`, `model` and `suite` blocks are listed, not run; (4) `docs/decisions.md` and `docs/runs/` are exempt; (5) relative links, one guide line per area package; (6) the leaves for S0008, S0009 and S0012. A0001 and A0002 list the answers of S0001 to S0012, and they stand.

Taken in S0013, with no question to the human:
- The coder reused `_backticked_or_plain` for the `Default` cell. A backticked `` `none` `` is therefore no default too.
- The coder rejected stripping only the `": "` after a placeholder. Every piece loses whitespace and `:` at both ends, which is criterion 4, added by the reviewer.

Still open from A0001 and A0002 for the human to accept or revisit: settings findings carry no line number; the example time limit is 60 s per command; a block running `make documents` is not read as `suite`; the skip for a missing *Configuration* section sits in the entry; one `_is_address` rule replaces the old `://` test.

New for the human: F0053-S0014 changes two earlier tests (the `documents` fixture and `test_the_operator_guide_folder_is_checked_per_file`). No standing leave covers that, so the story asks for one in `feature.md`, as decision 6 gave for S0008.

Earlier tests changed in S0013: none. The reviewer's entries 9 and 17 say that only rows and two imports were added to `tests/shared/domain/test_document_settings.py`, a file whose earlier rows are unchanged. No finding.

## 7 The slow checks

The project offers nothing beyond `make check` that applies: `make duplicates` is the coder's record (check 4), `make documents` ran in check 2, and `make mutants` is check 3's. `make check` ran green as I found it (`test: green (101.1 s)`, coverage 99.22 %, `check: green`). `.reports/junit.xml` holds 10,738 test cases, 8 more than at A0002 (S0013's rows). The slowest take 10.0 s each: `test_podman_timeout_status` rows of another feature, and this feature's `test_document_examples::test_the_folder_and_the_home_are_gone_once_the_document_has_run[past-the-limit]`, which waits out `ROOMY_LIMIT` as `CLAUDE.md` asks. The next test of the feature takes about 1 s.

Disk: since the previous record (an acceptance, 22.2 GB free, 1.4 GB used under `/srv/factory/vm`), the free space is 22.1 GB and the used space is unchanged at 1.4 GB. The state and `/tmp` hold 0.0 GB at both. The 0.1 GB less free space is on the shared filesystem, outside the factory's folders. S0013's change, two code lines, three test functions and two paragraphs, explains none of it, and none needs explaining.

## 8 Cost

The stories cost 162 runs, 209.9 min, 1238 turns and $45.79, plus one run of unknown cost (S0002's crash, as A0001 found). S0013 added 10 runs, 7.6 min and $1.72 to A0002's sum. One review round added a criterion (the strip at both ends), and the tester added one row for it. No story since A0002 stands out. Over the whole feature, S0003 stands out ($10.23, 26 runs, four review rounds, a docs stall), as A0001 found.

Human interventions: 19 questions answered (17 questions, 2 round caps), 1.2 h waited, unchanged since A0002, since S0013 needed none. S0003 needed the human most, with five answers, most of them leaves for earlier tests. S0014 will need one more leave before it starts.

## Proposed stories

- `F0053-S0014-a-skipped-block-or-a-checkout-example-keeps-the-suite-green.md`: the suite's copy of the documents holds the repository's tracked files, and `test_the_operator_guide_folder_is_checked_per_file` leaves out `not run` lines. Then a `vm` block and a `checkout` example that reads a file keep `make check` green, and a wrong example still fails it. This is needed before F0054's first story.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: not accepted; 1 story proposed
   1. Scope: every scope item has its story, and S0013 closed A0002's settings finding. But the goal "examples run like a notebook the test runner executes" breaks in the suite's own guard (S0008), which refuses right documents → F0053-S0014.
   2. Feature smoke test: red at the gate. `make documents` behaves as promised. The settings table in the style page's shape with backticked defaults and `<variable>: <fault>` refusals passes, and a wrong default, refusal, module or example blocks a listed page. But one `console vm` block in any document fails 5 rows of `test_the_operator_guide_folder_is_checked_per_file`. A `checkout` example that reads a repository file (`ls operator/vm/setup.sh`) fails 4. So `make check` goes red on right documents, and F0054-S0001 requires such blocks → F0053-S0014.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: S0013's backticked `none` counts as no default (listed under 6). The S0013 documenter's "two lines" of report is really 128, and the two paths it named are real and the rewrite's. A0001 and A0002's items are still open: the split of `documents.py` (804 lines), the dead `matches`, two address rules, and test tidiness. No story.
   5. Documentation: `style.md` and `shared.md` agree on S0013's rules. `style.md:32` and *The fixture* promise a copy of the tracked files and right examples passing everywhere, which the suite contradicts (in S0014's docs criterion). `shared.md` *The settings check* still says that settings findings "do not change the exit status", while they block a listed page. That is for F0054's `shared.md` story.
   6. Decisions: feature decisions 1 to 6 and the earlier answers stand. S0013's defaults are the reuse of `_backticked_or_plain` and the strip at both ends. S0013 changed no earlier test. S0014 needs a new leave in `feature.md` for the `documents` fixture and one earlier test.
   7. Slow checks: none beyond `make check` (green, 101.1 s, 99.22 %). Slowest tests are 10.0 s (`ROOMY_LIMIT` waits). Disk: used space unchanged at 1.4 GB, free 22.2 → 22.1 GB on the shared filesystem, nothing the feature explains or needs to.
   8. Cost: 162 runs, 209.9 min, $45.79 plus 1 unknown. S0013 cost 10 runs and $1.72 with one review round. S0003 still stands out ($10.23). 19 answers (17 questions, 2 round caps), 1.2 h waited, none since A0002. S0003 needed the human most.
   Note: a first smoke run gave a one-off `fixture instance could not be prepared`. It came from git's background `gc --auto` in my throwaway clone, not from the feature, and the final run sets `gc.auto 0`.
3. factory: done (pull request merged); cost: 1 runs, 10.9 min, 49 turns, 95515 tokens in (3390775 more from cache), 36476 out, $2.17
