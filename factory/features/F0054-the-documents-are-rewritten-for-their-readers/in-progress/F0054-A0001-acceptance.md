---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 631
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-07T09:53:31.858525Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-07T10:01:06.549460Z'
  stage: acceptance
  run: 98903ed23a974d879c7ed2f98b08801e
stories: [F0054-S0001, F0054-S0002, F0054-S0003, F0054-S0004, F0054-S0005, F0054-S0006, F0054-S0007, F0054-S0008, F0054-S0009, F0054-S0010, F0054-S0011, F0054-S0012, F0054-S0013, F0054-S0014, F0054-S0015, F0054-S0016, F0054-S0017, F0054-S0018, F0054-S0019, F0054-S0020, F0054-S0021, F0054-S0022, F0054-S0023]
outcome: null
---

# Acceptance of The documents are rewritten for their readers

## Recommendation

**accepted with stories.** All 22 files are rewritten. The README, the operator guide and the project guide are on `docs/checked-documents.txt`. `make check` and `make documents` pass, and every one of the 1,408 links in the checked documents and `operator/README.md` resolves. The one finding of weight is four references that name a heading the target page does not have. These are the three the human already knew of plus `agent-runtime.md:407`. One repair story gathers them, as decision 4 asks. No fact I checked is false, and no example fails. Wording, style and structure points are listed under 4 and 5 as notes for a later feature.

## 1 Scope

The scope is 22 files, one story each, and all 22 were built. S0001 to S0011 cover the operator guide's ten topic files and its index. S0012 to S0020 cover the project guide's nine pages and its index. S0021 covers the root `README.md` and S0022 covers `operator/README.md`. `docs/checked-documents.txt` lists all 21 files under `README.md` and `docs/`, plus `style.md` and `glossary.md`. Two notes:

- **`operator/README.md` is rewritten but not checked.** The Goal says "when the last story is merged, every document is checked". That is true for every file except this one. The check refuses the path (`operator/README.md is no document of the check`), so the human moved it to F0055-S0001 and F0055-S0004 (S0022, journal 6). This is a decision, not a gap. It is listed under 6.
- **S0023 is outside the feature's story list.** It is a code story: the document check now reads an indented example and reports a `console` block that has no command. It came from the crash S0001 found, and the human made it a story (S0001, journal 14). It follows decision 3 and leaves the scope as it was.

Out of scope was kept. No story changed `docs/decisions.md`, `docs/runs/` or `docs/operator-playbook.md`. Apart from S0023 no story changed behaviour, and S0023 changed only the document check.

## 2 Feature smoke test

What the feature promised a reader:
- every rewritten document is checked;
- its examples run;
- every link and every reference to a heading of another page leads somewhere.

I ran the gate first, then a walk over every link and every named heading.

```console
$ make check 2>&1 | tail -2
test: green (107.3 s)
check: green
$ make documents 2>&1 | tail -7
Report (not checked yet):
README.md:11: not run (suite)
docs/operator-guide/install.md:25: not run (vm)
docs/operator-guide/install.md:33: not run (suite)
docs/operator-guide/records.md:53: not run (vm)
docs/project-guide/pipeline.md:141: not run (vm)
documents ok (59.1 s)
$ uv run factory-check-story factory/features/F0054-the-documents-are-rewritten-for-their-readers/done/F0054-S0023-the-check-reads-an-indented-example-and-one-without-a-command.md
factory/features/F0054-the-documents-are-rewritten-for-their-readers/done/F0054-S0023-the-check-reads-an-indented-example-and-one-without-a-command.md: ok
$ uv run python walk.py        # every file of the checked list and operator/README.md: links, anchors, *heading* in [page](page.md)
24 documents, 1408 links, 179 heading references
docs/operator-guide/install.md:121: heading 'In a job' not in machine.md
exit 1
$ uv run python strict.py      # the same references, but the named heading must match exactly
docs/operator-guide/install.md:121: 'In a job' not a heading of machine.md
docs/operator-guide/work-items.md:66: 'What a work item cost' not a heading of records.md
docs/project-guide/machine.md:487: 'StageFinisher.finish' not a heading of pipeline.md
exact: 177
$ uv run python forms.py       # other forms: "X" under *Y* in [page], page.md, *X*, *X* of [page]
docs/operator-guide/agent-runtime.md:407: 'The stage environment' not a heading of install.md
docs/operator-guide/stops.md:53: 'In a job' not a heading of machine.md
docs/project-guide/README.md:283: 'The git wrapper' not a heading of agents.md
docs/project-guide/README.md:283: 'The stage environment' not a heading of hosting.md
checked 28
```

The scripts ran from a temporary directory that removed itself afterwards. I read each hit against the target page:

- `stops.md:53` writes *In a job* under *The idle shutdown*. That is right: it names the paragraph and its heading.
- The two `README.md:283` hits are false matches of my pattern. The line names *The git wrapper* in `hosting.md` and *The stage environment* in `machine.md`, and both headings exist.
- `agent-runtime.md:407` is wrong. It places *The stage environment* under *Configuration* in `install.md`, but the paragraph now stands under *Reference* (`install.md:239`). That is a fourth broken reference, besides the three the human named.

So the feature smoke test is red in one way only: four references to a heading (S0024). Every link resolves and every example that runs passes. The five examples that do not run are marked for the VM or the suite, as `style.md` allows.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

I gathered every "noticed, not touched" remark from the 23 journals and checked each one against today's tree.

**Resolved by a later story** (no action):
- the "Replaced in v1.2" and "Replaced from v1" sections and the v1.1 and v1.2 history (S0001, S0010, S0011, S0016). No such section is left.
- the false claim in `shared.md` that the operator guide has no `Default` column (S0001). `shared.md:252` is right now.
- `planning/cloud-sandbox/` in `agent-runtime.md` (S0003)
- the preflight list in `pipeline.md` without `metadata-block` and `copy` (S0017). `pipeline.md:495-502` is complete.
- the order of `opencode` in the table in `health.md` (S0006)
- the conflict between a manual `claude` login and the rollback (S0005). `agent-runtime.md:103` now says a manual login does not help.
- "(since F0044-S0010)" in `machine.md` (S0012)
- the unresolved `support/...` paths in the project guide's index (S0014 to S0018). The index is checked now.

**Still open, a false fact or a broken reference**, which goes into S0024:
- `agent-runtime.md:407` still points to "The stage environment" under *Configuration* (S0001, entries 5 to 41). The text moved to *Reference*.

**Still open, notes for a later feature** (no story, per decision 4):
- The docstring of `tests/guards/test_wrapper_search.py` says "the three wrappers", but the guard lists nine modules (S0012). This is a test text, the tester's.
- `hosting.md` does not describe six modules of the area: `application/opening.py`, `application/pushes.py`, `domain/hand_over.py`, `domain/post_texts.py`, `adapters/checkout_fixture.py` and `adapters/instance_fixture.py` (S0013).
- `tests/hosting/adapters/test_zfs_snapshots_diff.py` sits in the hosting folder but tests the machine area (S0013).
- Every story Description cites "style rules 8 to 10", but `style.md` has rules 1 to 8 (S0002, S0018). This is in the archived stories only.
- S0022's archived Interface, criterion 3 and smoke test (`Expect: 1`) still ask for the checked-list line that the human dropped in journal 6. Only the Description was rewritten (R5). The docs route runs no smoke test, so nothing failed. A reader of `done/` is misled.
- `uv run` prints "Bytecode compiled …" on stderr in the stage container (S0008), so examples call the installed command directly.
- `detect-secrets` flags the words `api_key` and `subscription` in a table row (S0016), and `test_no_file_names_a_removed_guide_file` matches a link text `work-items.md` (S0014). Both stalled a docs run once and both were fixed in the text. A later documenter will hit them again.
- `docs/decisions.md:1560` names the old one-file layout of the operator guide (S0004, S0007, S0009). It is history and out of scope.

## 5 The documentation as a whole

I read `README.md`, the indexes of both guides and the parts the walk led me to as a newcomer would. I checked these claims against the code:
- the five console commands in `README.md` (the same five as `[project.scripts]` in `pyproject.toml`);
- the `not_read` example in `pipeline.md` (the same as `factory/pipeline.yml:10`);
- the preflight order (`pipeline.md` against `machine.md` and `entry/wiring.py`);
- the operator guide's `Default` columns (checked by the settings check).

I found no contradiction between two pages, and no example that does not run: the example check passes and the five unrun examples are marked. The only defect a reader would hit is the four references of S0024.

One note for a later feature, not a story: `make documents` checks names, settings and examples, but not a reference in prose to a heading of another page (*X* in [page](page.md)). That is how the four broken references got past 23 reviews. A check for it would belong with F0055's work on the check. There is no section the feature made necessary that nobody wrote.

## 6 Decisions taken for the human

From `feature.md`:
1. One story per file.
2. The reviewer checks the facts against the old file and the code.
3. A wrong claim is fixed in the document. A fault in the code becomes its own story (this is how S0023 came about).
4. The acceptance proposes at most one repair story, only for a false fact, a broken link or reference, or an example that does not run.

From the story journals:
5. **S0001, journal 14.** The two `make mutants` commands stay inline in the prose and are not examples, because only the human starts a sweep. The indented-fence crash became S0023, and the blocks stayed at column 0 until then.
6. **S0001, journal 20.** In `install.md`, `setup.sh` comes first. `uv sync` and `make check` are only the check of a development clone.
7. **S0003, journal 12 (option A).** A command that acts on a real machine or a cloud account, where no run can be copied, stands in an `sh` block of bare commands under its step, and the text above it says where it runs. The rule went into `style.md`.
8. **S0001, journal 32.** The round cap of docs-review is raised to 3 (`factory/pipeline.yml:38`).
9. **The standing word for the night of 2026-11-06 to 07.** There is no stop at a round cap while the findings are real (S0003, S0009, S0011, S0017 to S0021). Several answers add a by-script self-check: sentence length, a glossary word linked at its first use, a file linked once, completeness of `tests/support/`.
10. **S0018, journal 40.** The style round on `pipeline.md` is the last one, and its facts are settled.
11. **S0022, journal 6 (option 1).** `operator/README.md` stays off the checked list. F0055-S0001 and F0055-S0004 make it a checked document.
12. **S0023, journal 4.** These rows were added: the less-indented line keeps its indentation, and the finding blocks in a listed file and is only reported in an unlisted one.
13. **Dropped without a decision-log line (S0015).** The sentence that the agent texts come from v1 so the baseline run compares was removed as history. Whether `docs/decisions.md` should carry it is the human's call.

Earlier tests changed: none. Every reviewer entry says "the diff changes no test file". The one exception is S0023, which only added rows to `tests/shared/domain/test_document_examples.py` and `tests/entry/test_check_documents_examples.py`, under its Interface's leave ("Adding rows to these earlier modules needs no further leave"). No earlier row changed.

## 7 The slow checks

Nothing is offered beyond `make check` and `make documents` (59.1 s, green), other than `make mutants` (check 3).

The JUnit report of my `make check` has 10,782 tests, 923.6 s of test time over the workers, and 107.3 s of wall time. The slowest tests are the time-limit tests at the `ROOMY_LIMIT` of ten seconds:
- `test_podman_s_timeout_status_at_the_limit_is_a_timed_out_run[255-at-the-limit]` and `[137-at-the-limit]` (10.02 s each)
- `test_a_call_past_its_time_limit_ends_time_limit_though_it_named_the_limit`
- `test_command_reaching_its_time_limit_is_killed`
- `test_the_folder_and_the_home_are_gone_once_the_document_has_run[past-the-limit]` (each 10.01 s)

**Disk.** Since the feature's start, free space fell from 21.6 GB to 17.6 GB, about 4 GB. The three mount points show the same free figure, so they are one file system. `/srv/factory/vm` grew by only 0.1 GB of use (1.4 to 1.5 GB), and the state directory and `/tmp` show 0.0 GB. The feature changed documents, one domain module and two test modules, which explains a few megabytes at most. About 3.9 GB of the drop is not explained by the feature or by any path in the record. Podman's image or build storage, or the snapshots of the dataset outside these paths, are the likely holders. The operator should look.

## 8 Cost

The 23 stories cost 241 runs, 334.4 min, 2,563 turns and $96.69, about $4.20 per story.

- **S0018** (`project-guide/pipeline.md`, 895 lines, the longest page) stands out. It took $13.56, 22 runs and 53.1 min, 14 % of the total. Its journal shows four docs-review rounds past the cap, mostly on sentence length and parentheses. The human extended twice and called the second "the last one on style" (journals 24 and 40).
- **S0001** cost $7.15 and 18 runs. As the first story it set the patterns: unrun commands, the indented-example crash and the order of setup.
- **S0020** (the project guide's index) cost $7.12 and 32.6 min. Its completeness lists were checked by script.
- Every other story cost between $1.88 and $6.26.
- S0014, S0016 and S0022 each stalled once on a red `make check` after a docs-only run: a guard on an old file name, detect-secrets, and the guard on the old root folder. Each cost one more run.

**Human interventions.** The human answered 15 questions: 4 by `question` and 11 at a `round_cap`, with 0.7 h waited in all. S0001 needed the human most, with three answers. One was the `make mutants` question with the S0023 split (journal 14), and two were round-cap extensions (journals 20 and 32). S0003 and S0018 had two answers each.

## Proposed stories

- `backlog/F0054-S0024-the-cross-references-name-existing-headings.md`: the one repair story decision 4 allows. It corrects the four references to a heading that does not exist as written: `install.md:121`, `work-items.md:66`, `project-guide/machine.md:487` and `agent-runtime.md:407`.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 1 story proposed (F0054-S0024)
   1 Scope: all 22 files were rewritten. Every file except `operator/README.md` is on the checked list; that one moved to F0055 by the human's decision (S0022, journal 6). S0023, a fix to the check, is outside the story list but follows decision 3. Nothing went out of scope.
   2 Smoke test: `make check` and `make documents` pass, and all 1,408 links resolve. A script over the heading references found four that name a heading that does not exist: the three already known, plus `agent-runtime.md:407`, which puts "The stage environment" under *Configuration* in `install.md` when it now stands under *Reference*.
   3 Mutation testing: By sweep, not run here.
   4 What the stories noticed: most items were fixed by later stories. `agent-runtime.md:407` is still open and goes into S0024. Notes for a later feature, not stories: the "three wrappers" docstring, six hosting modules not described, a test module in the wrong area folder, "style rules 8 to 10" in the story texts, and S0022's archived Interface and smoke test not rewritten after the human's answer.
   5 Documentation as a whole: I found no contradiction and no failing example. The check does not verify prose references to headings on other pages, which is how the four got past 23 reviews. That is a note for later.
   6 Decisions for the human: 13 listed: the 4 in `feature.md`, the answers from the story journals (unrun `sh` blocks, round cap 3, the standing word for the night, `operator/README.md` left to F0055) and one sentence dropped without a decision-log line (S0015). No earlier test was changed; S0023 only added rows, under the leave in its Interface.
   7 Slow checks: there is nothing beyond `make check` and `make documents`. The slowest tests are the five 10 s time-limit tests. Free disk space fell by 4.0 GB (21.6 to 17.6 GB), but the recorded paths grew by only 0.1 GB; the feature does not explain the other 3.9 GB, so the operator should look.
   8 Cost: 241 runs, 334.4 min, $96.69 in all, about $4.20 per story. S0018 stands out at $13.56 and 22 runs, from style rounds past the cap. The human answered 15 questions (4 asked by agents, 11 at a round cap) and waited 0.7 h; S0001 needed the human most, with three answers.
