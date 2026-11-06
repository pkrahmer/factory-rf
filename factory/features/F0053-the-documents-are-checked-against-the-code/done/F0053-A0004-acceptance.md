---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 602
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T19:34:22.217262Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T19:48:02.659642Z'
  stage: acceptance
  run: c2168c47f9474dedb16f729a0d14686c
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-06T19:49:56.652131Z'
  stage: done
stories: [F0053-S0001, F0053-S0002, F0053-S0003, F0053-S0004, F0053-S0005, F0053-S0006, F0053-S0007, F0053-S0008, F0053-S0009, F0053-S0010, F0053-S0011, F0053-S0012, F0053-S0013, F0053-S0014]
outcome: accepted
---

# Acceptance of The documents are checked against the code

## Recommendation

**not accepted.** The third acceptance's finding is closed. A `console vm` block and a `checkout` example that reads a repository file now keep the suite green, and every check of `make documents` behaves as the feature promised (check 2, sections 1 to 3 and 5). But the feature smoke test is still red at the gate, on the one step the feature leaves to the rewrite: putting a right document on `docs/checked-documents.txt`. Listing the rewritten `install.md`, today's operator guide index or today's `shared.md` keeps `make documents` at `documents ok`. Yet it fails nine rows of four earlier tests, which each expect their page to be unlisted, so `make check` goes red. F0054-S0001 lists `install.md` and would stall at once. Proposed F0053-S0015 repairs it. As with the third acceptance, merging this pull request instead of closing it brings the story into the backlog.

## 1 Scope

Every scope item has its story, as A0001 to A0003 found: the name check (S0001), the settings check (S0002), the runnable examples (S0003) with the fixtures `checkout` and `instance` (S0006), the checked list and the report (S0004), and the agents' rules (S0005). S0007 carries out decision 5. Since A0003, the one story it proposed, S0014, is merged. It changed only tests. The `documents` fixture (`tests/conftest.py`) is now a per-test clone of the session fixture `tracked_files`, which `tests/support/documents_copy_support.py` builds from `git ls-files`. `test_the_operator_guide_folder_is_checked_per_file` leaves out the `not run` lines through `without_report_lines` (`tests/support/check_documents_support.py`). No story lies outside the scope. `feature.md`'s *Stories* list still names only S0001 to S0007, and that list is the human's.

Finding: the goal "the checks report on every file but block only the files on a list ...; the rewrite adds each file to the list as it rewrites it" holds for `make documents`, but not for the suite. Three earlier tests read the repository's list and assume their page is not on it (check 2, section 4) → F0053-S0015.

## 2 Feature smoke test

This is the walk-through of a writer who rewrites the install page as F0054-S0001 will. They put `docs/operator-guide/install.md` on the checked list. They replace its settings table with the style page's shape (`Name | What it does | Default | Example`), with every default in backticks or `none`. My script took the defaults from `SETTINGS` instead of typing them. They add *The refusals* with two messages in the form `<variable>: <fault>`, a relative link to the settings module, an `instance` example (`factory-health`, then a refusal of `factory-run` with its status), a `checkout` example (`ls operator/vm/setup.sh`) and a `console vm` block. First they get four things wrong (a default, a refusal, the link, the example's output), then they correct them. Then the suite reads the page. Then a wrong example goes into an unlisted page, to show that the suite still catches it. Last come the agents' rules and the area guide lines. The script ran in a temporary clone (`gc.auto 0`, each step committed, since the `checkout` fixture exports the committed state) through the real command, `uv run --project /work/checkout python -m factory.entry.check_documents --root <clone>`. The suite ran with the checkout's interpreter on `PATH`.

Command: `bash smoke.sh <its folder>` (with `edit.py` beside it, in a `mktemp -d` folder). Output:

```text
== 1. today's documents, as merged
exit 0
Report (not checked yet):
documents ok (0.5 s)
(124 report lines 'does not exist' left out)
== 2. install.md listed, Configuration rewritten by the style page, with a wrong default, refusal, link and example
exit 1
docs/operator-guide/install.md: setting GIT_USER_NAME has the default '`somebody`' in the guide, 'factory' in the settings code
docs/operator-guide/install.md: refusal `<variable>: is frobnicated` is not held by the settings code
docs/operator-guide/install.md:68: the example printed 2026-11-06T19:38:21Z settings invalid: FACTORY_INSTANCE: is not a name
Report (not checked yet):
docs/operator-guide/install.md:82: not run (vm)
(125 report lines 'does not exist' left out)
== 3. the writer corrects the four
exit 0
Report (not checked yet):
docs/operator-guide/install.md:82: not run (vm)
documents ok (1.5 s)
(124 report lines 'does not exist' left out)
== 4. the suite reads the rewritten page
FAILED tests/entry/test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status
2 failed, 88 passed, 525 deselected in 29.17s
== 5. a wrong example in an unlisted page still fails the suite
docs/project-guide/machine.md:461: the example printed one
docs/operator-guide/install.md:82: not run (vm)
documents ok (1.6 s)
      1 5 failed, 1 passed in 8.19s
      5 E             + docs/project-guide/machine.md:461: the example printed one
== 6. the agents' rules and the way back from the code
1
1
shared docs/project-guide/shared.md exists
hosting docs/project-guide/hosting.md exists
work docs/project-guide/work.md exists
agents docs/project-guide/agents.md exists
watching docs/project-guide/watching.md exists
machine docs/project-guide/machine.md exists
pipeline docs/project-guide/pipeline.md exists
entry docs/project-guide/README.md exists
```

Step 2 filtered out the link line, because my filter dropped every `does not exist` line. Run again on that state, it is the first blocking line: `docs/operator-guide/install.md:54: src/factory/shared/domain/setings.py does not exist`, above `Report (not checked yet):`. All four mistakes block the listed page.

The two failures of step 4, with `--tb=short`:

```text
E             docs/operator-guide/install.md: missing
E             + docs/checked-documents.txt: docs/operator-guide/install.md is no document of the check
tests/entry/test_check_documents_operator_guide.py:89: AssertionError
E       assert 1 == 0
tests/entry/test_check_documents_settings.py:37: AssertionError
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-install-file]
FAILED tests/entry/test_check_documents_settings.py::test_settings_findings_are_printed_without_changing_the_exit_status
```

I took `install.md` off the list again and left the rewritten page as it was. Then the same two modules gave `7 passed`, so the listing is the cause, not the page. Next, on a clone with today's documents and nothing committed, I added the three pages that F0054-S0001, S0011 and S0012 list (`docs/operator-guide/install.md`, `docs/operator-guide/README.md`, `docs/project-guide/shared.md`) to the list. All three pass the checks today:

```text
documents ok (0.5 s)
FAILED tests/entry/test_check_documents_settings.py settings_findings_are_printed_without_changing_the_exit_status
FAILED tests/entry/test_check_documents_operator_guide.py the_operator_guide_folder_is_checked_per_file[no-install-file]
FAILED tests/entry/test_check_documents_operator_guide.py the_operator_guide_folder_is_checked_per_file[no-index]
FAILED tests/entry/test_check_documents_copies.py a_wrong_example_in_a_copied_document_fails_only_a_listed_one[unlisted-reported]
FAILED tests/entry/test_check_documents_suite_copy.py a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[vm]
FAILED tests/entry/test_check_documents_suite_copy.py a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[github]
FAILED tests/entry/test_check_documents_suite_copy.py a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[model]
FAILED tests/entry/test_check_documents_suite_copy.py a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[suite]
FAILED tests/entry/test_check_documents_suite_copy.py a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[wrong-example]
======================== 9 failed, 12 passed in 14.09s =========================
```

Run over every test whose name holds `document`, the same nine rows are the only failures. The one collection error, `tests/agent_files/__init__.py is not in the subpath of '/work/checkout'`, comes from my harness: the clone's tests ran with the checkout's installed package.

What it shows:
- Sections 1, 2, 3 and 5 are green. A wrong default, an unknown refusal, a misspelt link and a wrong example each block the listed page. The `instance` fixture runs `factory-health` and shows `factory-run`'s refusal with status 2. The `vm` block and the `checkout` example that reads `operator/vm/setup.sh` keep the suite green, which closes A0003's finding (S0014). A wrong example in an unlisted page still fails `test_the_operator_guide_folder_is_checked_per_file`, so S0008's guard still bites.
- Section 4 and the second run are the finding. `test_settings_findings_are_printed_without_changing_the_exit_status` (`tests/entry/test_check_documents_settings.py:25`) still pins the rule from before the checked list. The `no-install-file` and `no-index` rows delete a page that the list may name. The suite copy test reuses the `no-index` change. `test_check_documents_copies.py:13` takes `shared.md` as its unlisted page. Each reads the repository's list. A right document on the list therefore turns `make check` red, and a docs-route story cannot change the tests → F0053-S0015.
- Section 6: the reviewer's `### Documents` item is there, the documenter speaks of runnable examples, and the eight packages name existing guide pages.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

New from S0014:
- Tester (entry 8), reviewer (entries 12 and 20): criterion 2's "no line about `machine.md`" is read as "no line at or after the appended block". Today's `machine.md` already gives two `does not exist` lines (264 and 362) in the full copy. Accepted by the reviewer and listed under 6. No story.
- Coder (entry 10) and smoke tester (entry 24): the sandbox refused `rm -rf` of their own `mktemp -d` clones (`/tmp/tmp.713FltQTdB`, `/tmp/tmp.feI3YSB3Un`). It refused mine too (`/tmp/tmp.na2eFcBBWp`, 327 MB), against the lesson "leave nothing behind in `/tmp`". The permission rules are in `.claude/`, the human's files. No story. The human may want to allow `rm -rf` of a `/tmp/tmp.*` folder.
- Smoke tester (entry 24): the sandbox refused `git commit` in a throwaway clone, a step of S0014's own smoke test. It did not matter there, because `tracked_files_repository` copies the working tree. My commits in a throwaway clone were allowed, so the rule differs between roles. The proposed story's smoke test commits nothing.
- Coder (entry 18): `_append_example` in `test_check_documents_copies.py` is not a leftover copy (reviewer, entry 20). It is also the place where that module's unlisted page reads the repository's list, which is part of S0015.
- Documenter (entry 22): `docs/project-guide/machine.md:362` and `docs/project-guide/work.md:13` are stale again. They belong to the rewrite.

Still open from A0001 to A0003, owned elsewhere or below a story: `src/factory/shared/domain/documents.py` is 804 lines, and its split is the human's to schedule. `matches` of `documents.py` is still called only by `tests/shared/domain/test_document_examples.py`. `make duplicates` stays at `6 new, 39 known, 4 gone` (S0014 coder). `_link_name` and `_is_address` are two address rules in one module. `tests/entry/test_check_documents_todays_names.py` belongs under `tests/shared/domain/`. The 84 report lines of `docs/project-guide/README.md` and the deliberate example paths of `docs/project-guide/agents.md` are left for the rewrite.

## 5 The documentation as a whole

- `docs/project-guide/style.md`, *Runnable examples*, now says that the suite runs the examples on a copy of the tracked files, and that a block that is not run fails neither. That matches the code (check 2), so A0003's finding is closed.
- `style.md` and `README.md:26` say a finding blocks "only in a file listed in `docs/checked-documents.txt`". They do not say that the suite then still depends on which file is listed. After S0015 that is true without a sentence, so no repair is needed.
- `docs/project-guide/shared.md:144`, *The settings check*: "Like the name lines they do not change the exit status." That was true before the checked list. `shared.md:130` and the code (check 2) now block on a listed `install.md`. A0003 left this for F0054's `shared.md` story. The test that pins the old rule is now part of S0015, so its docs criterion takes the sentence.
- `docs/operator-guide/install.md:9` still says `operator/vm/setup.sh` "makes the VM", the sentence the Goal names. That is prose and the rewrite's (out of scope).

## 6 Decisions taken for the human

From `feature.md`, accepted with the feature unless revisited: (1) the checks live in `make documents`; (2) report everywhere, block only the files on `docs/checked-documents.txt`; (3) an example says where it runs, and `vm`, `github`, `model` and `suite` blocks are listed, not run; (4) `docs/decisions.md` and `docs/runs/` are exempt; (5) relative links, one guide line per area package; (6) the leaves for S0008, S0009 and S0012; (7) the leave for S0014. A0001 to A0003 list the answers and defaults of S0001 to S0013, and they stand. Those still open for the human to accept or revisit:
- settings findings carry no line number;
- the example time limit is 60 s per command;
- a block running `make documents` is not read as `suite`;
- the skip for a missing *Configuration* section sits in the entry;
- one `_is_address` rule replaces the old `://` test;
- a backticked `` `none` `` counts as no default.

Taken in S0014:
- The human's answer (entry 4) added criterion 5, that two copies of the session repository are separate.
- The tester's reading of criterion 2 (entry 8), accepted by the reviewer: only `machine.md` lines at or after the appended block count.
- The `<line>` of criteria 1 and 2 is matched as `\d+`.
- `--local` is not spelt out, because `git clone` of a local path already is local (entry 16).
- The coder measured `make test` before on a separate clone of `main`: 106.8 s before, 105.6 s after (entry 10).

New for the human: F0053-S0015 changes four earlier tests. The standing leave does not cover them, so the story asks for a decision 8 in `feature.md` before it starts, as decision 7 did for S0014.

Earlier tests changed in S0014, each with its leave named in reviewer entry 20:
- `tests/conftest.py` (`documents`), under feature decision 7;
- `test_the_operator_guide_folder_is_checked_per_file`, under feature decision 7;
- `tests/entry/test_check_documents_copies.py` (`_append_block` and `_findings_from` moved to `tests/support/check_documents_support.py`), under the standing leave to move a shared helper;
- `tests/support/check_documents_support.py`, additions only.

No finding.

## 7 The slow checks

The project offers nothing beyond `make check` that applies. `make duplicates` is the coder's record (check 4), `make documents` ran in check 2, and `make mutants` is check 3's. `make check` ran green as I found it (`test: green (108.4 s)`, coverage 99.22 %, `check: green`). `.reports/junit.xml` holds 10,749 test cases, 11 more than at A0003 (S0014's rows). The slowest take 10.0 s each. They are `test_podman_timeout_status`, `test_podman_images` and `test_opencode_resume_session` rows of other features, and this feature's `test_document_examples::test_the_folder_and_the_home_are_gone_once_the_document_has_run[past-the-limit]`, which waits out `ROOMY_LIMIT`. The feature's document tests take 33.5 s together over 627 cases. The next slowest is `test_a_matching_example_in_a_copied_document_gives_no_finding[unlisted]` at 1.9 s. S0014's session copy left `make test` where it was (106.8 s before, 105.6 s after).

Disk: since the previous record (a stage start, 22.7 GB free, 1.4 GB used under `/srv/factory/vm`), free space fell to 21.9 GB and used space stayed at 1.4 GB. The state and `/tmp` hold 0.0 GB at both. The 0.8 GB went on the shared filesystem, outside the factory's folders, and S0014's change (test files only) explains none of it. The throwaway clones that S0014's coder and smoke tester could not remove (check 4) may account for part of it, if they lie on that filesystem. My own clone, 327 MB, came after the record.

## 8 Cost

The stories cost 173 runs, 228.1 min, 1327 turns and $49.02, plus one run of unknown cost (S0002's crash, as A0001 found). S0014 added 11 runs, 18.2 min and $3.23 to A0003's sum, nearly twice S0013's $1.72 for a change that touched only tests. Its journal tells why: an intake question, then one review round with three findings that were all duplicate test helpers (`copy_of`, `_append_block`, `_findings_from`). That round took a coder run that only handed over, a tester run, and a second coder run that built nothing and reran `make check`. Over the whole feature, S0003 still stands out ($10.23, 26 runs, four review rounds, a docs stall), as A0001 found.

Human interventions: 20 questions answered (18 questions, 2 round caps), 1.4 h waited. Since A0003 that is one more question and about 0.2 h more, both from S0014's intake (entry 3), which asked for the criterion that copies are separate. S0003 needed the human most, with five answers, most of them leaves for earlier tests. That pattern repeats: S0008, S0009, S0012, S0014 and now S0015 each need a leave for earlier tests in `feature.md` before they start.

## Proposed stories

- `F0053-S0015-listing-a-right-document-keeps-the-suite-green.md`: the four earlier tests that read the repository's checked list write their own through a shared `write_checked_list`. Then listing a right page (`install.md`, the operator guide index, `shared.md`) keeps `make check` green, and `shared.md` loses its stale "do not change the exit status" sentence. Needed before F0054-S0001, which lists `install.md`.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: not accepted; 1 story proposed
   1. Scope: every scope item has its story, and S0014 closed A0003's finding. But "the rewrite adds each file to the list as it rewrites it" breaks in the suite: three earlier tests read the repository's checked list and expect their page to be unlisted → F0053-S0015.
   2. Feature smoke test: red at the gate. `make documents` behaves as promised. A style-page settings table, a refusals table, an `instance` example, a `checkout` example and a `vm` block pass, and a wrong default, refusal, link or example blocks the listed page. A wrong example in an unlisted page still fails the suite. But listing the rewritten `install.md` fails 2 earlier rows. Listing today's `install.md`, operator guide index and `shared.md` (`documents ok`) fails 9 rows of `test_check_documents_settings`, `_operator_guide`, `_copies` and `_suite_copy`. So `make check` goes red on right documents, and F0054-S0001 lists `install.md` → F0053-S0015.
   3. Mutation testing: by sweep, not run here.
   4. Noticed: the S0014 tester's reading of criterion 2 (lines at or after the block) was accepted. The sandbox refuses `rm -rf` of a `mktemp -d` folder for coder, smoke tester and me: my `/tmp/tmp.na2eFcBBWp` (327 MB) is left, and the rule is in the human's `.claude/`. The sandbox also refused the smoke tester's `git commit` in a throwaway clone. The stale paths at `machine.md:362` and `work.md:13` are the rewrite's. Still open from earlier acceptances: the split of `documents.py` (804 lines), the test-only `matches`, two address rules, duplicates 6/39/4.
   5. Documentation: `style.md` now matches the suite copy, closing A0003's item. `shared.md:144` still says settings findings "do not change the exit status", and the test that pins that rule is in S0015's scope, so its docs criterion takes the sentence. `install.md:9` "makes the VM" is the rewrite's.
   6. Decisions: feature decisions 1 to 7 and the earlier defaults stand (listed). From S0014: criterion 5 from the human's answer, the reading of criterion 2, `\d+` for `<line>`, no `--local`. S0014's earlier-test changes each have a named leave (decision 7, or the standing leave). S0015 needs a new decision 8 leave for four earlier tests.
   7. Slow checks: none beyond `make check` (green, `test: green (108.4 s)`, 99.22 %, 10,749 cases). Slowest tests are 10.0 s `ROOMY_LIMIT` waits, and the feature's document tests total 33.5 s. Disk: used stays at 1.4 GB, free 22.7 → 21.9 GB on the shared filesystem. S0014 (tests only) explains none of it, and the clones that S0014's agents could not remove may explain some.
   8. Cost: 173 runs, 228.1 min, $49.02 plus 1 unknown. S0014 cost 11 runs and $3.23, nearly double S0013, from an intake question and a review round over three duplicate test helpers. S0003 still stands out ($10.23). 20 answers (18 questions, 2 round caps), 1.4 h waited, one more since A0003 (S0014's intake). S0003 needed the human most.
3. factory: done (pull request merged); cost: 1 runs, 13.6 min, 46 turns, 116512 tokens in (3130267 more from cache), 34758 out, $2.25
