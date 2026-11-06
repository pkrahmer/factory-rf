---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 604
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T20:12:38.578084Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T20:25:26.911115Z'
  stage: acceptance
  run: 5e1fec753f4e4abe9fcec41435d5fd95
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-06T20:29:23.671464Z'
  stage: done
stories: [F0053-S0001, F0053-S0002, F0053-S0003, F0053-S0004, F0053-S0005, F0053-S0006, F0053-S0007, F0053-S0008, F0053-S0009, F0053-S0010, F0053-S0011, F0053-S0012, F0053-S0013, F0053-S0014, F0053-S0015]
outcome: accepted
---

# Acceptance of The documents are checked against the code

## Recommendation

**not accepted.** The fourth acceptance's finding is closed. With `install.md`, the operator guide index and `shared.md` on the checked list, the four tests that S0015 changed pass, and so does every other earlier document test. Every check of `make documents` behaves as the feature promised (check 2, sections 1 to 3, 5 and 6). But the feature smoke test is still red at the gate in one place, and the cause is S0015's own new test. Its fixture `listed` appends the three pages without looking at the list. Once the repository's list names `docs/operator-guide/README.md`, which F0054-S0011 will do, the copy lists that page twice and `test_without_its_own_list_the_repository_list_reaches_the_output` fails, so `make check` goes red while `make documents` says `documents ok`. The proposed F0053-S0016 repairs it. As before, merging this pull request instead of closing it brings the story into the backlog.

## 1 Scope

Every scope item has its story, as A0001 to A0004 found: the name check (S0001), the settings check (S0002), the runnable examples (S0003) with the fixtures `checkout` and `instance` (S0006), the checked list and the report (S0004), and the agents' rules (S0005). S0007 carries out decision 5. Since A0004, the one story it proposed, S0015, is merged. It changed only tests:
- a new helper `write_checked_list` in `tests/support/check_documents_support.py`;
- the four earlier tests, which now write their own list first;
- the new module `tests/entry/test_check_documents_any_list.py`;
- the `shared.md` sentence about settings findings.

No story lies outside the scope. `feature.md`'s *Stories* list still names only S0001 to S0007, and that list is the human's.

Finding: the goal "the rewrite adds each file to the list as it rewrites it" now holds for `install.md` and `shared.md`, but not for the operator guide index. The test that S0015 wrote to guard the listing reads the repository's list itself (check 2, section 4) → F0053-S0016.

## 2 Feature smoke test

This is the walk-through of a writer who starts the rewrite as F0054 will. They list the three pages that F0054-S0001, S0011 and S0012 list first. They extend the *Configuration* section of `install.md`:
- a table in the style page's shape (`Name | What it does | Default | Example`);
- *The refusals*;
- a relative link to the settings module;
- an `instance` example (`factory-health`);
- a `checkout` example (`ls operator/vm/setup.sh`);
- a `console vm` block.

They make one mistake in each of the first four (a default, a refusal, the link, the example's output) and then correct them. Then the suite reads the listed pages. Then a wrong example goes into an unlisted page, to show that the suite still catches it. Last come the agents' rules and the area guide lines.

The script ran in a temporary clone (`gc.auto 0`, each step committed) through the real command, `python -m factory.entry.check_documents --root <clone>`, and pytest, both from the checkout's `.venv/bin`. The script's `check` prints the exit status and the output without the `does not exist` report lines and the `not run` lines. It counts the left-out lines and then prints the `install.md` ones again, so a link line shows below the heading even when it blocks.

Command: `bash smoke.sh` (with `addition.md` beside it, in a `mktemp -d` folder). Output:

```text
== 1. the three pages the rewrite lists first, listed with today's text
exit 0
Report (not checked yet):
documents ok (0.5 s)
(124 'does not exist' report lines left out)
== 2. install.md gets a style-page table, refusals, a link and examples, each with one mistake
exit 1
docs/operator-guide/install.md: setting GIT_USER_NAME has the default '`somebody`' in the guide, 'factory' in the settings code
docs/operator-guide/install.md: refusal `<variable>: is frobnicated` is not held by the settings code
docs/operator-guide/install.md:89: the example printed healthy
Report (not checked yet):
docs/operator-guide/install.md:86: src/factory/shared/domain/setings.py does not exist
(125 'does not exist' report lines left out)
== 3. the writer corrects the four
exit 0
Report (not checked yet):
documents ok (1.3 s)
(124 'does not exist' report lines left out)
== 4. the suite reads the listed, rewritten pages
tests/entry/test_check_documents_any_list.py:99: in test_without_its_own_list_the_repository_list_reaches_the_output
E   AssertionError: assert ['docs/checke...d: missing\n'] == ['docs/checke...d: missing\n']
E     
E     At index 1 diff: 'docs/checked-documents.txt: docs/operator-guide/README.md is no document of the check\n' != 'docs/operator-guide/README.md: missing\n'
E     Left contains one more item: 'docs/operator-guide/README.md: missing\n'
E     Use -v to get more diff
FAILED tests/entry/test_check_documents_any_list.py::test_without_its_own_list_the_repository_list_reaches_the_output
1 failed, 249 passed, 1333 deselected in 43.97s
== 5. a wrong example in an unlisted page still fails the suite
exit 0
docs/project-guide/machine.md:461: the example printed one
documents ok (1.4 s)
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-install-file]
FAILED tests/entry/test_check_documents_operator_guide.py::test_the_operator_guide_folder_is_checked_per_file[no-index]
FAILED tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[vm]
FAILED tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[github]
FAILED tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[model]
FAILED tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[suite]
FAILED tests/entry/test_check_documents_suite_copy.py::test_a_skipped_block_leaves_the_output_as_it_was_and_a_wrong_example_adds_its_line[wrong-example]
12 failed, 238 passed, 1333 deselected in 47.46s
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

Two shorter scripts settle what the first one leaves open. Their output:

```text
== a misspelt link in a listed install.md, raw output with line numbers
exit 1
1:docs/operator-guide/install.md:74: src/factory/shared/domain/setings.py does not exist
2:Report (not checked yet):
== only the operator guide index listed, the new module
documents ok (0.5 s)
1 failed, 5 passed in 5.37s
== every page that has no finding today, listed
docs/operator-guide/README.md docs/operator-guide/cloud-run.md docs/operator-guide/install.md docs/operator-guide/records.md docs/operator-guide/site.md docs/operator-playbook.md docs/project-guide/operator.md docs/project-guide/pipeline.md docs/project-guide/shared.md docs/project-guide/watching.md
FAILED tests/entry/test_check_documents_any_list.py::test_without_its_own_list_the_repository_list_reaches_the_output
1 failed, 249 passed, 1333 deselected in 33.09s
```

In that last run `make documents` itself refused only `docs/operator-playbook.md` (`is no document of the check`), which is right: the playbook is the human's and no document of the check. The other nine pages pass the checks today.

What it shows:
- Sections 1, 2, 3 and 5 are green. A wrong default, an unknown refusal, a misspelt link and a wrong example each block the listed page. The link blocks too: it is line 1, above the heading, in the raw output. The `instance` fixture runs `factory-health`, and the `vm` block and the `checkout` example keep the suite green. A wrong example in an unlisted page is reported by `make documents` (exit 0) and fails the suite, so S0008's guard still bites.
- A0004's finding is closed. With the three pages listed, all four tests that S0015 changed pass, and so does every earlier document test.
- Section 4 is the finding. With the operator guide index on the repository's list, and that page alone is enough, S0015's `test_without_its_own_list_the_repository_list_reaches_the_output` fails. Its fixture `listed` (`tests/entry/test_check_documents_any_list.py:28`) appends the three pages unconditionally. The copy then lists `docs/operator-guide/README.md` twice, and the check prints its `is no document of the check` line twice. With nine right pages listed it is still the only failure. F0054-S0011 lists that page ("`docs/checked-documents.txt`: one line, `docs/operator-guide/README.md`"), and as a docs-route story it cannot change the test, so its docs stage would stall → F0053-S0016.
- Section 6: the reviewer's `### Documents` item is there, the documenter's rule "Every example is runnable, and you ran it" is there, and the eight packages name existing guide pages.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

New from S0015:
- Reviewer, entry 17, note 3: `write_checked_list` commits through `commit_all`, a plain `git commit`. A text that equals the copy's list gives an empty commit and fails. Today the repository's list starts with comment lines, so no test hits this. It is the same dependency on the repository's list as the section 2 finding → part of F0053-S0016.
- Reviewer, entry 17, notes 1 and 2: `_settings_steps`, `_no_index_steps` and `_shared_example_steps` restate the steps of the earlier tests. `_SHARED` repeats `UNLISTED` of `test_check_documents_copies.py`, and `_NO_INDEX` repeats the `no-index` line of `test_check_documents_operator_guide.py`. These are notes below a finding, and no story. A later tester may move them under the standing leave.
- Coder, entries 11 and 15, and tester, entry 13: the `docs/operator-guide/` literals in `MISSING_LINES` and `NO_INDEX` predate S0015. No story.
- Documenter, entry 19: `docs/project-guide/machine.md:362` (`factory/stage.Containerfile`) and `docs/project-guide/work.md:13` (`factory/agents`) are report lines. They belong to the rewrite.
- Reviewer, entries 9 and 17: the round-1 findings were three path constants copied from `factory.shared.domain.documents`. That is the same kind as S0014's round (duplicate test helpers). It cost a coder run that only handed over and a second coder run that only reran `make check` (check 8).

Still open from A0001 to A0004, owned elsewhere or below a story:
- `src/factory/shared/domain/documents.py` is 804 lines, and its split is the human's to schedule.
- `matches` of `documents.py` is still called only by tests.
- `make duplicates` stays at `6 new, 39 known, 4 gone` (S0015 coder, entries 7 and 15).
- `_link_name` and `_is_address` are two address rules in one module.
- `tests/entry/test_check_documents_todays_names.py` belongs under `tests/shared/domain/`.
- The report lines of `docs/project-guide/README.md` and the deliberate example paths of `docs/project-guide/agents.md` are left for the rewrite.
- The sandbox refused `rm -rf` of a `mktemp -d` folder in S0014. This time the first command of mine that held one was refused too. The scripts' own `trap 'rm -rf "$d"' EXIT` ran.

## 5 The documentation as a whole

- `docs/project-guide/shared.md:144`, *The settings check*, now says that settings and refusal findings follow the checked list, and section 2 confirms it. A0004's stale sentence is gone.
- `README.md:26` says "The document checks block in every file", then that the name, settings and example findings block only in listed files. Read with line 24, "document checks" are the first family (missing document, own words, stops and kill points). This is consistent, though a newcomer could stumble on the reuse of "document checks" for one family. It is prose for the rewrite (F0054-S0021).
- `style.md:32` and `shared.md` say what blocks where, and both match the code.
- A section the feature made necessary that nobody wrote: no document tells the writer of a document test to write the list it needs rather than read the repository's. S0015 built that rule into four tests, but the project guide names only `MISSING_LINES` for `support/check_documents_support.py` (`docs/project-guide/README.md:62`), which now also holds `write_checked_list`, `append_block`, `findings_from`, `without_report_lines` and `drop_settings_row`. S0015's own new test broke this unwritten rule (section 2). This is the docs criterion of F0053-S0016.
- `docs/operator-guide/install.md:9` still says `operator/vm/setup.sh` "makes the VM", the sentence the Goal names. That is prose and the rewrite's (out of scope).

## 6 Decisions taken for the human

From `feature.md`, accepted with the feature unless revisited:
1. The checks live in `make documents`.
2. Report everywhere, block only the files on `docs/checked-documents.txt`.
3. An example says where it runs; `vm`, `github`, `model` and `suite` blocks are listed, not run.
4. `docs/decisions.md` and `docs/runs/` are exempt.
5. Relative links, one guide line per area package.
6. The leaves for S0008, S0009 and S0012.
7. The leave for S0014.
8. The leave for S0015.

A0001 to A0004 list the answers and defaults of S0001 to S0014, and they stand. Those still open for the human to accept or revisit:
- settings findings carry no line number;
- the example time limit is 60 s per command;
- a block running `make documents` is not read as `suite`;
- the skip for a missing *Configuration* section sits in the entry;
- one `_is_address` rule replaces the old `://` test;
- a backticked `` `none` `` counts as no default;
- in S0014's criterion 2, only `machine.md` lines at or after the appended block count.

Taken in S0015, with no question asked:
- The tester moved the settings test's private `_drop_row` to the support module as `drop_settings_row`, under the standing leave to move a shared helper (entry 5).
- The coder kept the check's output as it is, rather than silence the `is no document of the check` line for the repository's list, because criterion 2 relies on that line (entries 7 and 15).
- The documenter took the listed and unlisted behaviour of settings findings from the criteria and the existing section, not from a fresh read of `src/` (entry 19). Section 2 bears it out.

New for the human: F0053-S0016 changes the fixture `listed` and the helper `write_checked_list`, both written by S0015. The standing leave does not cover them, so the story asks for a decision 9 in `feature.md` before it starts.

Earlier tests changed in S0015, each with its leave named in reviewer entry 17:
- `tests/entry/test_check_documents_copies.py`, `test_check_documents_operator_guide.py`, `test_check_documents_settings.py` and `test_check_documents_suite_copy.py`: feature decision 8.
- `_drop_row` moved unchanged to `drop_settings_row`: the standing leave to move a shared test helper.
- `tests/support/check_documents_support.py`: additions only.

No finding.

## 7 The slow checks

The project offers nothing beyond `make check` that applies. `make duplicates` is the coder's record (check 4), `make documents` ran in check 2, and `make mutants` is check 3's. `make check` ran green as I found it (`test: green (109.5 s)`, coverage 99.22 %, `check: green`).

`.reports/junit.xml` holds 10,756 test cases, 7 more than at A0004. The slowest take 10.0 s each and belong to other features: `test_podman_timeout_status` rows, `test_claude_runtime_resume` and `test_opencode_events`. This feature's slowest is `test_document_examples::test_the_folder_and_the_home_are_gone_once_the_document_has_run[past-the-limit]` (10.0 s), which waits out `ROOMY_LIMIT`. The feature's document tests take 40.8 s together over 633 cases (33.5 s over 627 at A0004). S0015's six new rows take 6.4 s, the slowest `test_a_test_that_writes_its_list_keeps_its_outcome_when_the_repository_lists_more_pages[install]` at 2.2 s. `make test` went from 108.4 s at A0004 to 109.5 s, which is within run-to-run noise.

Disk: since the previous record (A0004's acceptance), free space under `/srv/factory/vm` fell from 21.9 GB to 21.7 GB, and used space stayed at 1.4 GB. The state and `/tmp` hold 0.0 GB at both. The 0.2 GB went on the shared filesystem outside the factory's folders. S0015's change (test files and one paragraph) explains none of it. My own clones came after the record and removed themselves.

## 8 Cost

The stories cost 183 runs, 238.8 min, 1383 turns, 4,557,337 tokens in (33,380,786 more from cache), 639,015 out and $51.18, plus one run of unknown cost (S0002's crash, as A0001 found). S0015 added 10 runs, 10.7 min and $2.16 to A0004's sum. That is less than S0014's $3.23, but it is still ten runs for a change with no code. Its journal tells why. Review round 0 found three path constants copied from `factory.shared.domain.documents`, and that took a coder run that only handed the story over (entry 11), a tester run (entry 13), and a second coder run that only reran `make check` (entry 15). It is the same pattern as S0014. The tester could have caught both rounds by searching `src/factory` for the constants first. Over the whole feature, S0003 still stands out ($10.23, 26 runs, four review rounds, a docs stall), as A0001 found.

Human interventions: 20 questions answered (18 questions, 2 round caps), 1.4 h waited. That is unchanged since A0004: S0015 asked nothing, because the human gave its leave beforehand as decision 8. S0003 needed the human most, with five answers, most of them leaves for earlier tests. That pattern continues as leaves written into `feature.md` before a story starts: S0008, S0009, S0012, S0014, S0015 and now S0016.

## Proposed stories

- `F0053-S0016-a-page-already-listed-keeps-the-document-tests-green.md`: S0015's fixture `listed` adds only the pages the list does not yet name, and `write_checked_list` commits only when the text changed. Then listing the operator guide index (F0054-S0011), or any right page, keeps `make check` green. The project guide gets the rule that a document test writes the list it needs. It needs a decision 9 in `feature.md`, and it must be merged before F0054-S0011.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: not accepted; 1 story proposed
   1. Scope: every scope item has its story, and S0015 closed A0004's gap for `install.md` and `shared.md`. The gap remains for the operator guide index: S0015's own new test reads the repository's checked list, so listing that page breaks it → F0053-S0016.
   2. Feature smoke test: red at one step. A wrong default, refusal, link or example each block a listed page, and the corrected page gives `documents ok`. With `docs/operator-guide/README.md` on the list, `test_without_its_own_list_the_repository_list_reaches_the_output` fails (`1 failed, 249 passed`), because the fixture `listed` lists that page a second time. F0054-S0011 lists that page, so its docs stage would stall. With nine right pages listed it is the only failure.
   3. Mutation testing: by sweep, not run here.
   4. What the stories noticed: reviewer note 3 of S0015 (`write_checked_list` makes an empty commit when the text is unchanged) is folded into S0016. The duplicated step functions and constants in the new module, the `docs/operator-guide/` literals, the stale `machine.md:362` and `work.md:13`, and the earlier open items get no story.
   5. Documentation: `shared.md`'s settings sentence is now true. No document says that a document test writes the list it needs, and `docs/project-guide/README.md:62` names only `MISSING_LINES` for `check_documents_support.py`. Both are in S0016's docs criterion.
   6. Decisions: feature decisions 1 to 8 and the earlier defaults are listed for the human. S0015's earlier-test changes each have their leave (decision 8, plus the standing leave for `drop_settings_row`). S0016 needs a decision 9 before it starts.
   7. Slow checks: nothing beyond `make check`, which was green as found (109.5 s, 99.22 %). There are 10,756 cases, and the document tests take 40.8 s. Free disk fell 0.2 GB on the shared filesystem; used space stayed at 1.4 GB, and the feature does not explain the drop.
   8. Cost: 183 runs, 238.8 min, $51.18, plus one unknown. S0015 cost 10 runs and $2.16; a review round over three copied constants took two coder runs that built nothing. Human interventions: 20 answered (18 questions, 2 round caps), 1.4 h waited, unchanged since A0004. S0003 needed the human most.
3. factory: done (pull request merged); cost: 1 runs, 12.7 min, 37 turns, 85043 tokens in (1965916 more from cache), 26667 out, $1.61
