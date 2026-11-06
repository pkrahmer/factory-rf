---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 607
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-06T21:31:32.244027Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-06T21:41:16.889798Z'
  stage: acceptance
  run: b5d9513ab75d490b9b267a98011cac32
- number: 3
  speaker: factory
  kind: done
  at: '2026-11-06T21:43:11.099585Z'
  stage: done
stories: [F0053-S0001, F0053-S0002, F0053-S0003, F0053-S0004, F0053-S0005, F0053-S0006, F0053-S0007, F0053-S0008, F0053-S0009, F0053-S0010, F0053-S0011, F0053-S0012, F0053-S0013, F0053-S0014, F0053-S0015, F0053-S0016, F0053-S0017]
outcome: accepted
---

# Acceptance of The documents are checked against the code

## Recommendation

**accepted.** The feature smoke test is green from end to end, and this is the first time that holds. With eleven right pages on the repository's list and `install.md` rewritten, all 129 document tests and guards pass. A wrong default, an unknown refusal, a misspelt link and a wrong `instance` example each block the listed page. A code change to a default the listed page names gives its finding. Since S0017, a wrong example in an unlisted page is reported by `make documents` and no longer touches the suite. The fifth acceptance's finding is closed by S0016, and the coupling behind the third to fifth findings is removed by S0017 (feature decision 10). The feature's document tests fell from 40.8 s to 15.2 s. What remains is notes: one question about `factory-health` and the `instance` fixture (section 6), and one earlier support module changed under a leave that fits it loosely (section 6). No story is proposed.

## 1 Scope

Every scope item has its story, as A0001 to A0005 found:
- the name check (S0001);
- the settings check (S0002);
- the runnable examples (S0003), with the fixtures `checkout` and `instance` (S0006);
- the checked list and the report (S0004);
- the agents' rules (S0005).

S0007 carries out decision 5. S0008 to S0017 came out of the acceptances. Two stories have been merged since A0005:
- S0016 (A0005's proposal): the fixture `listed` adds only the pages the list does not yet name, and `write_checked_list` commits only a changed text.
- S0017 (feature decision 10): the check's tests run on documents they write. The new module is `tests/support/minimal_documents_support.py` (`minimal_documents`, `add_and_commit`) with the fixture `minimal`, and the guard `tests/guards/test_document_tests_write_their_documents.py` is new. `documents_copy_support.py` and the fixtures `tracked_files` and `documents` are gone.

Neither story touched `src/`. No story lies outside the scope. The Goal's "the rewrite adds each file to the list as it rewrites it" now holds for any right page (check 2, section 5). `feature.md`'s *Stories* list names only S0001 to S0007; that list is the human's.

Finding: none.

## 2 Feature smoke test

This is the walk-through of a writer who starts the rewrite as F0054 will:
1. They list every page that has no finding today.
2. They extend the *Configuration* of the listed `install.md` with five things, the first four each with one mistake: a `Default` table in the style page's shape, *The refusals*, a relative link to the settings module, and an `instance` example (`factory-health --state-directory "$FACTORY_STATE"`). The fifth is a `console vm` block.
3. They correct the four mistakes.
4. They run the document tests against the changed list and documents.
5. They put a wrong example into an unlisted page.
6. They change the code's default that the listed page names.
7. Last, they check the agents' rules and the area guide lines.

The script ran in a temporary clone (`gc.auto 0`, each step committed) through the real command, `python -m factory.entry.check_documents --root <clone>`, and pytest, both from the checkout's `.venv/bin`. Step 7 runs the clone's own `src` through `PYTHONPATH`. The script's `show` prints the blocking lines above the heading in full and the report without the `does not exist` and `not run` lines, which it counts.

Command: `bash smoke.sh` (in a `mktemp -d` folder that removes itself). Output:

```text
== 1. today's documents and list
exit 0
Report (not checked yet):
documents ok (0.5 s)
(125 report lines left out; )
== 2. every page without a finding today is listed (beside style.md and glossary.md)
docs/project-guide/style.md docs/project-guide/glossary.md docs/operator-guide/README.md docs/operator-guide/cloud-run.md docs/operator-guide/install.md docs/operator-guide/records.md docs/operator-guide/site.md docs/project-guide/operator.md docs/project-guide/pipeline.md docs/project-guide/shared.md docs/project-guide/watching.md 
exit 0
Report (not checked yet):
documents ok (0.5 s)
(125 report lines left out; )
== 3. install.md, listed, gets a Default table, refusals, a link, an instance example and a vm block, each but the last with one mistake
exit 1
docs/operator-guide/install.md:82: src/factory/shared/domain/setings.py does not exist
docs/operator-guide/install.md: setting FACTORY_CHECKOUT has the default '`/work/elsewhere`' in the guide, '/work/checkout' in the settings code
docs/operator-guide/install.md: refusal `<variable>: is frobnicated` is not held by the settings code
docs/operator-guide/install.md:85: the example printed healthy
Report (not checked yet):
(126 report lines left out; install.md:91: not run (vm))
== 4. the writer corrects the four
exit 0
Report (not checked yet):
documents ok (1.1 s)
(126 report lines left out; install.md:91: not run (vm))
== 5. the document tests, with the real list naming eleven pages and install.md rewritten
129 passed in 13.03s
== 6. a wrong example in an unlisted page: reported, never blocking; the suite does not run it
exit 0
Report (not checked yet):
docs/project-guide/machine.md:461: the example printed one
documents ok (1.3 s)
(126 report lines left out; install.md:91: not run (vm))
129 passed in 12.94s
== 7. the code changes the default the listed install.md names: the check follows the code
exit 1
docs/operator-guide/install.md: setting FACTORY_CHECKOUT has the default '`/work/checkout`' in the guide, '/work/moved' in the settings code
Report (not checked yet):
docs/project-guide/machine.md:461: the example printed one
(126 report lines left out; install.md:91: not run (vm))
== 8. the agents' rules and the way back from the code
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

The suite of steps 5 and 6 is every `tests/entry/test_check_documents*.py`, `tests/shared/adapters/test_document_examples.py`, and the three guards `test_document_tests_write_their_documents.py`, `test_project_guide_files.py` and `test_operator_guide_files.py`.

What it shows:
- Every promise of the Goal holds against the real entry points. Wrong names, defaults, refusals and examples block a listed page, the `vm` block is listed as not run, and the check follows the code (step 7).
- A0005's finding is closed. With eleven pages listed, among them the operator guide index that F0054-S0011 will list, the document tests stay green (step 5).
- S0017 holds. A wrong example in an unlisted page is a report line of `make documents` (exit 0), and the suite no longer runs it (step 6). At A0005 the same step failed twelve tests.
- The ten pages that pass today could all be listed at once. `docs/operator-playbook.md` was never a candidate: my loop reads only the README and the two guide folders.

A first run of mine wrote a plain `factory-health` in the `instance` block. It printed `no health status: /state/health.json is missing`, because `factory-health` reads `/state` unless `--state-directory` is given. A0005's run of the same plain command printed `healthy`. `style.md:55` tells the writer to pass `--state-directory "$FACTORY_STATE"`, which the run above does, so the documents are right. The open point is in section 6.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

New from S0016 and S0017:
- S0017, coder entry 10 and tester entries 8, 15 and 23: the tester's stage runs `make lint` and skips `make types`. `mypy --strict` errors in the tester's new files therefore surfaced only at the coder, who may not edit tests, and that cost a human question (entry 11) and three runs. The tester's checks are set in `factory/pipeline.yml` and the tester's instructions, which are the human's, so there is no story. The human may want the tester to run `make types` over the files it wrote.
- S0017, reviewer entry 27, and the guard's own code: `test_document_tests_write_their_documents.py` checks four names, not paths. Criterion 5 ("runs it on a path outside `tmp_path`") holds only as far as those names reach. A test that called `main([])` from the repository root, or built `Path(__file__).parents[2]`, would pass the guard. Today the one `main([])` call (`tests/entry/test_check_documents.py:68`) first runs `chdir` into `tmp_path`. This is a note, not a story.
- S0017, coder entry 17: the coder had no like-for-like "before" time for `make test`. Section 7 supplies it from A0005's JUnit report.
- S0017, coder entry 17: in a `--shared` clone run with `PYTHONPATH`, two rows of `tests/hosting/adapters/test_instance_fixture.py` failed. They pass in `make check`. In my own clone runs I put `.venv/bin` on `PATH`, and the `instance` examples ran. Most likely the console script `factory-health` was missing from that `PATH`. That is the environment, not the code.
- S0016 and S0017, documenter entries 19 and 29: the report lines `docs/project-guide/machine.md:264`, `:362` and `work.md:13` (and `machine.md:298`, which is gone now) belong to the rewrite (F0054-S0014 and S0017).
- S0017, reviewer entries 19 and 27: round 0 found copied helpers again (`_page`, `_settings_rows`, `_stops`, `_project_guide` and `_texts` copied `tests/support/document_texts.py`). That is the third time in this feature, after S0014 and S0015 (section 8).

Still open from A0001 to A0005, owned elsewhere or below a story:
- `src/factory/shared/domain/documents.py` is 804 lines, and its split is the human's to schedule.
- `matches` (`documents.py:799`) is still called only by tests. `make duplicates` lists it as new dead code and stays at `6 new, 39 known, 4 gone`. The target exits 1 on new findings, and it is a record, never a check.
- `_link_name` and `_is_address` are two address rules in one module.
- `tests/entry/test_check_documents_todays_names.py` still belongs under `tests/shared/domain/`.
- The sandbox again refused a command that ended in a plain `rm -rf` of a `mktemp -d` folder. Every script I ran removed its folders through `trap`.

## 5 The documentation as a whole

- `docs/project-guide/shared.md:140`, *How the check is tested*, is new (S0017). It matches the code: `minimal_documents`, `add_and_commit`, `append_block`, `write_checked_list` and `drop_settings_row` exist as described. `clean_texts` reads the four tables when called, and the real documents are checked only by `make documents`.
- `style.md`, *Runnable examples*, now says that the suite runs none of the documents' examples, which step 6 bears out. The other pages no longer name the `documents` fixture, `tracked_files` or `documents_copy_support`; the only mention left is the guard's own description.
- `docs/project-guide/README.md:62` and `:92-93` list the support modules with what they hold, which closes A0005's "only `MISSING_LINES`" point.
- `style.md:52` says "The commands never run in the real checkout or the real state". A command whose default path is the real one, such as `factory-health` without `--state-directory`, still reads `/state` of the machine that runs the check, as A0005's `healthy` and my `missing` show. `style.md:55` gives the right command, so a writer who follows the page is safe. The sentence overstates the isolation, and section 6 asks the human about it.
- Unchanged since A0005, and for the rewrite (out of scope): `README.md:26` reuses "document checks" for the first family only, and `docs/operator-guide/install.md:9` still says `setup.sh` "makes the VM", the sentence the Goal names. They belong to F0054-S0021 and F0054-S0001.
- No contradictions between stories, and no example that no longer runs: `make documents` on today's tree is `documents ok`, with style.md and the glossary listed.

## 6 Decisions taken for the human

From `feature.md`, accepted with the feature unless revisited:
1. The checks live in `make documents`.
2. Report everywhere, block only the files on `docs/checked-documents.txt`.
3. An example says where it runs; `vm`, `github`, `model` and `suite` blocks are listed, not run.
4. `docs/decisions.md` and `docs/runs/` are exempt.
5. Relative links, and one guide line per area package.
6. to 9. The leaves for S0008, S0009, S0012, S0014, S0015 and S0016.
10. The check's tests run on documents they write, with its leave for S0017.

A0001 to A0005 list the answers and defaults of S0001 to S0015, and they stand. These are still open for the human to accept or revisit:
- settings findings carry no line number;
- the example time limit is 60 s per command;
- a block running `make documents` is not read as `suite`;
- the skip for a missing *Configuration* section sits in the entry;
- one `_is_address` rule replaces the old `://` test;
- a backticked `` `none` `` counts as no default;
- in S0014's criterion 2, only `machine.md` lines at or after the appended block count.

Taken in S0016 and S0017:
- S0016: `listed` looks at the list before it appends, and `write_checked_list` returns without a commit when the text is unchanged (tester entry 5, reviewer entries 9 and 17).
- S0017, the human's answer (entry 11): no re-export from `documents.py`; the tests patch the tables by name.
- S0017, tester entry 15: beyond the literal wording of that answer, the tester also patches each table in its defining module, so that the minimal documents and the check see the same row.
- S0017, tester entry 8: the tester removed the coupling-only tests (`any_list`: three tests, `suite_copy`: two, `copies`: one, `checked_files`: one) and named what covers each, under decision 10. It renamed `test_an_example_reads_the_tracked_files_of_the_repository` to `test_an_example_reads_a_file_git_tracks_in_the_repository` so that the smoke test's grep prints 0.
- S0017, tester entry 23: the tester chose its own `ROOT` pattern over the reviewer's `re.S` suggestion.

A question for the human, with no story: should `factory-health` read the state directory from `FACTORY_STATE` when `--state-directory` is not given? `install.md:20` calls `FACTORY_STATE` "the state directory (`health.json`, ...)", but `factory-health` reads `/state` unless given the flag (`src/factory/entry/health.py:29`, `health.md:29`). The options I see:
- (a) Leave the code and make `style.md:52` say that a command's own default paths are not redirected. This is the smallest change.
- (b) Make `factory-health` default to `FACTORY_STATE`. Then a plain `factory-health` in an `instance` example would read the fixture's state, and an operator would need no flag.

I would choose (b), as a story for the human's next feature, since it changes a console script's behaviour.

Earlier tests changed, each with the leave named by its reviewer:
- S0016 (reviewer entry 17): the fixture `listed` in `tests/entry/test_check_documents_any_list.py` and `write_checked_list` in `tests/support/check_documents_support.py`, under decision 9.
- S0017 (reviewer entry 27): `tests/conftest.py` (`tracked_files` and `documents` removed, `minimal` added), `test_check_documents_any_list.py`, `_checked_files.py`, `_copies.py`, `_operator_guide.py`, `_settings.py`, `_suite_copy.py` and `_todays_names.py`, and `tests/support/documents_copy_support.py` (deleted), all under decision 10.
- S0017, `tests/support/document_texts.py`, under "the standing leave to move a shared test helper". This leave fits loosely. No helper moved: the module changed from binding the four tables at import to reading them when called, and the constant `SETTINGS_TABLE` became the private `_settings_table()`. The tester and the reviewer argued that every builder keeps its name and signature and gives the same text when nothing is patched, and `make check` is green. Decision 10's leave covers "the tests and fixtures its Interface names", and the Interface does not name `document_texts`. The reviewer itself said that a tester who found the change beyond decision 10 should ask. This is a note of low weight for the human to accept or revisit; it changes no outcome.

## 7 The slow checks

The project offers nothing beyond `make check` that applies here:
- `make duplicates` is the coder's record (section 4);
- `make documents` ran in section 2;
- `make mutants` is check 3's.

`make check` ran green as I found it: `test: green (104.4 s)`, coverage 99.20 %, `check: green`.

`.reports/junit.xml` holds 10,768 test cases, 12 more than at A0005. The slowest take about 10 s each, and all but one belong to other features: the `test_podman_timeout_status` rows and `test_claude_runtime_provider_limit`. This feature's slowest is still `test_document_examples::test_the_folder_and_the_home_are_gone_once_the_document_has_run[past-the-limit]` (10.0 s), which waits out `ROOMY_LIMIT`.

The tests whose class names `document` now take 15.2 s over 643 cases. At A0005 they took 40.8 s over 633. That is the measurement S0017's coder could not make like for like, and it shows the story's purpose met: no real example runs in `make check` any more. `make test` went from 109.5 s at A0005 to 104.4 s.

Disk: since the previous record (A0005's acceptance), free space under `/srv/factory/vm` fell from 21.7 GB to 21.4 GB. Used space stayed at 1.4 GB, and the state and `/tmp` hold 0.0 GB at both records. The 0.3 GB went on the shared filesystem outside the factory's folders. The changes of S0016 and S0017 (test files and documents, one support module deleted) explain none of it. My clones came after the record and removed themselves.

## 8 Cost

The stories cost 207 runs, 275.7 min, 1,580 turns, 5,158,088 tokens in (39,199,161 more from cache), 735,606 out and $58.44, plus one run of unknown cost (S0002's crash, as A0001 found). Since A0005 two stories added 24 runs, 36.9 min and $7.26:
- S0016: 10 runs, 14.2 min, $2.08.
- S0017: 14 runs, 22.7 min, $5.19. Its journal shows three causes:
  - Intake asked four questions (entry 3), all of them form: an untested `add_and_commit`, an untestable time criterion, and missing rows.
  - The tester skipped `make types`, so seven `attr-defined` errors reached the coder. That took a coder question (entry 10), the human's answer (entry 11), a coder run that only relayed it, a tester run and a coder run.
  - Review round 0 found copied helpers, which took one more relay, tester and coder cycle (entries 21 to 25). The tester's first run alone was $1.57.

Over the whole feature, S0003 still stands out ($10.23, 26 runs, four review rounds, a docs stall), as A0001 found. Three stories in a row (S0014, S0015 and S0017) lost a cycle to copied test helpers that a search of `tests/support/` would have caught.

Human interventions: 22 questions answered (20 questions, 2 round caps), and 1.5 h waited. That is two answers and 0.1 h more than at A0005, both from S0017: the intake answer (entry 4) and the type-check answer (entry 11). S0003 still needed the human most, with five answers, most of them leaves for earlier tests. Since then the human has written those leaves into `feature.md` before each story starts (decisions 6 to 10), and S0016 needed no answer at all.

## Proposed stories

None. The feature keeps its promises, and the only change I see worth making, `factory-health` reading `FACTORY_STATE` (section 6), changes a console script's behaviour. Whether to make it is the human's call, outside this feature's scope.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted; 0 stories proposed

   1 Scope: no gap. Every scope item has its story (S0001 to S0007). Since A0005, S0016 (an already-listed page keeps the tests green) and S0017 (the check's tests run on documents they write, decision 10) are merged, neither touching `src/`.
   2 Feature smoke test: green end to end, the first time this feature's smoke test passed. With eleven right pages listed and `install.md` extended, each of four mistakes blocks the listed page: a wrong default, an unknown refusal, a misspelt link, a wrong `instance` example. The `vm` block is listed as not run, and a changed code default gives its finding. All 129 document tests and guards pass. A wrong example in an unlisted page is only reported and no longer touches the suite (A0005 saw 12 failures there).
   3 Mutation testing: by sweep, not run here.
   4 Noticed: the tester skips `make types`, so S0017's type errors reached the coder and cost a human question. The tester's checks are the human's files, so no story. The S0017 guard checks four names, not paths. Copied test helpers cost a review cycle for the third story in a row. Still open from earlier: `documents.py` at 804 lines, the unused `matches`, `duplicates` at 6 new.
   5 Documentation: the new *How the check is tested* (shared.md) and the style.md lines match the code. `style.md:52` overstates the isolation: a plain `factory-health` reads the machine's `/state`, but `style.md:55` gives the right command. The README's "document checks" and `install.md:9` "makes the VM" are left for the rewrite.
   6 Decisions: feature decisions 1 to 10, and the open defaults from A0001 to A0005. Taken in S0016 and S0017: the human's answer (no re-export), the extra patch in each table's defining module, and the coupling-only tests removed with what covers each. A question for the human: should `factory-health` default to `FACTORY_STATE`? I would choose yes, as a later story. `tests/support/document_texts.py` was changed under the standing leave to move a helper, which fits loosely: it is a low-weight note to accept or revisit.
   7 Slow checks: nothing beyond `make check`, which is green (`test: green (104.4 s)`, coverage 99.20 %). The feature's document tests fell from 40.8 s to 15.2 s, and `make test` from 109.5 s to 104.4 s. Disk: 0.3 GB less free on the shared filesystem with used space unchanged; S0016 and S0017 explain none of it.
   8 Cost: 207 runs, 275.7 min, $58.44 plus one unknown. S0017 stands out at $5.19 over 14 runs: intake questions, a type-check question and a duplicate-helper cycle. Human: 22 answers (20 questions, 2 round caps), 1.5 h waited. S0003 still needed the human most.
3. factory: done (pull request merged); cost: 1 runs, 9.6 min, 35 turns, 111194 tokens in (2170410 more from cache), 32096 out, $1.97
