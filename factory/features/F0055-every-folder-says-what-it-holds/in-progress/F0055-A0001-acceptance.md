---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 639
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-07T14:34:51.286210Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-11-07T14:48:22.910146Z'
  stage: acceptance
  run: 48815cb0854d4f36b369a026d1957c88
stories: [F0055-S0001, F0055-S0002, F0055-S0003, F0055-S0004, F0055-S0005, F0055-S0006, F0055-S0007]
outcome: null
---

# Acceptance of Every folder says what it holds

## Recommendation

**accepted with stories.** The feature does what `feature.md` promised. All 22 READMEs on `FOLDER_READMES` exist, are in their form and are on `docs/checked-documents.txt`. `make documents` ends `documents ok`, every module and operator script carries the SPDX line, and `make check` is green. Two holes in the guard are worth a story each, and neither one breaks a promise to a user. The guard still skips a listed README that is missing, so `make check` stays green when one is deleted (F0055-S0008). The README form check does not count any line that carries a link, so an opening with a link has no sentence limit and link lines may hold any amount of prose (F0055-S0009). Feature decision 6 meant to stop exactly that.

## 1 Scope

None. Each item in the Scope has its story, and every story is inside the Scope:

- the list and its guard, the check reading the READMEs, and the documenter's paths: S0001
- the four groups of READMEs: S0002 to S0005
- the heading references: S0006
- the license header: S0007

I read the code the stories name. `factory.shared.domain.folder_readmes` holds `FOLDER_READMES` (22 paths, after decision 11 took `operator/template/` off) and `readme_problems`. `factory.entry.check_documents._named_documents` reads them. `factory.shared.domain.heading_references` holds the heading check, and `tests/guards/test_license_headers.py` is the license guard.

The human's write-path change has landed. In `factory/pipeline.yml`, the documenter's `write_paths` hold the 22 exact paths with `operator/README.md`, and they use no folder pattern. The coder paths that S0003 opened for one story are gone again.

The Goal's done condition holds: every README on the list exists and is on the checked list, and `make check` is green.

Still open, and the human's by `feature.md`: `factory/README.md`, `factory/features/README.md` and `docs/runs/README.md`, due "after S0005's merge". None exists yet. The root README's `## The folders` line for `factory/` has no README link for that reason. `factory/archive/` (35 feature folders) is in no list and no Out of scope. It sits inside the human's `factory/`, so `factory/README.md` can explain it in one line.

## 2 The feature's smoke test

The walk-through a reader and a maintainer of the repository would do:

1. Does every listed folder show a README in its form, on the checked list?
2. Does every module and script name its license?
3. Does the document check pass?
4. Does a slip get caught? In a clone, I added a new area subfolder, a wrong module name and a wrong heading reference.

The script was run from a `mktemp -d` that removes itself:

```bash
repo=/work/checkout; cd "$repo"
echo "== 1 every listed folder has a README in its form, on the checked list"
uv run --quiet python - <<'PY'
from pathlib import Path
from factory.shared.domain.folder_readmes import FOLDER_READMES, readme_problems
listed = Path("docs/checked-documents.txt").read_text().split()
bad = 0
for path in FOLDER_READMES:
    folder = Path(path).parent
    subs = sorted(p.name for p in folder.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__")
    text = Path(path).read_text() if Path(path).exists() else None
    problems = readme_problems(str(folder), text, subs)
    if problems or path not in listed:
        bad += 1; print("PROBLEM", path, problems)
areas = sorted(p.name for p in Path("src/factory").iterdir() if (p / "__init__.py").exists())
missing = [a for a in areas if f"src/factory/{a}/README.md" not in FOLDER_READMES]
print(f"{len(FOLDER_READMES)} READMEs, {bad} with problems; areas without README: {missing}")
PY
echo "== 2 every module and script names its license"
uv run --quiet python - <<'PY'   # git ls-files; src/factory/*.py line 1, operator/ scripts outside template/ line 1 or after the shebang
...
PY
echo "== 3 the document check on the repository"
make documents 2>&1 | tail -3
echo "== 4 a newcomer's slip in a clone: a new folder, a wrong module, a wrong heading"
c=$(mktemp -d); git clone --quiet "$repo" "$c/r"
mkdir "$c/r/src/factory/watching/charts" && touch "$c/r/src/factory/watching/charts/x.py"
printf '\nThe board is described in factory.watching.domain.no_such_module, under *No such heading* in [the guide](../../../docs/project-guide/watching.md).\n' >> "$c/r/src/factory/watching/README.md"
cd "$c/r"
uv run --quiet --project "$repo" python - <<'PY'   # readme_problems on src/factory/watching with its real subfolders
...
PY
uv run --quiet --project "$repo" python -m factory.entry.check_documents --root "$c/r" 2>&1 | grep -v 'not run' | tail -8; echo "exit ${PIPESTATUS[0]}"
```

Output:

```
== 1 every listed folder has a README in its form, on the checked list
22 READMEs, 0 with problems; areas without README: []
== 2 every module and script names its license
188 modules, 0 without header; 18 scripts, 0 without; tests with header: 0
NOTICE: kumpel-factory
LICENSE: ['Apache', 'License', 'Version']
== 3 the document check on the repository
docs/operator-guide/records.md:53: not run (vm)
docs/project-guide/pipeline.md:141: not run (vm)
documents ok (59.7 s)
== 4 a newcomer's slip in a clone: a new folder, a wrong module, a wrong heading
['src/factory/watching: charts/ is not named']
src/factory/watching/README.md:9: No such heading is no heading of docs/project-guide/watching.md
Report (not checked yet):
exit 1
```

The smoke test is green for what the feature promised. The new subfolder and the wrong heading were caught. The bare module name was not caught, because the name check reads names in backticks. With `` `factory.watching.domain.no_such_module` `` in a second run, it gave `src/factory/watching/README.md:9: factory.watching.domain.no_such_module does not exist`, exit 1.

The run also showed two holes in the guard, which I then confirmed one by one:

- **The appended prose line was not caught.** In step 4, the line `The board is described in …, under *No such heading* in [the guide](…)` comes after the subfolder list. Because it carries a link, `readme_problems` took it as a link line and gave no `line 9 is no part of the form`.
  - A README with eight lines of 200 words each, three sentences per line and a link in each, gives `[]`.
  - An opening `One. Two. Three. Four. Five, see [g](g.md).` gives `[]`. Without the link it gives `the opening is longer than two sentences`.
  - `docs/project-guide/style.md` says a folder README has "no other prose". Feature decision 6 says the guard checks "nothing else". Both are stricter than the code. This is F0055-S0009.
- **A missing README is skipped.** I deleted `src/factory/agents/README.md` and `security/README.md` in a clone and ran `tests/guards/`. The output was `SKIPPED … security/README.md is not written yet` and `SKIPPED … src/factory/agents/README.md is not written yet`, with no failure from the README guards. Only `tests/README.md`, `tests/support/README.md` and `tests/guards/README.md` are pinned to exist, by S0003's `tests/guards/test_test_folder_readmes.py`. This is F0055-S0008.

## 3 Mutation testing

By sweep, not run here.

## 4 What the stories noticed

- **S0001, coder and reviewer:** `folder_readmes` imports the large `documents` module. That is allowed, since both are domain modules. Not worth a story.
- **S0001, reviewer notes (entries 15, 39):** `_run` in `tests/entry/test_check_documents_folder_readmes.py` is a copy of `_run` in `tests/entry/test_check_documents_checked_files.py`. The human made moving it to `tests/support/check_documents_support.py` optional (entry 29), and it was not done. `ROOT = Path(__file__).parents[2]` is repeated across guards. The next story that touches those modules can make the move under the standing leave.
- **S0002, coder (entry 18):** The human told the tester to rewrite the story (entry 14). The factory dropped that rewrite, because the work item is outside the tester's write paths. The archived S0002 Description therefore still says "No code and no test changes", and criterion 1 still shows the subfolder line with a colon. The archive cannot change now. For the human: an answer that tells the tester to rewrite the story cannot land.
- **S0003, coder (entry 10):** On the tests route, no role could write `tests/README.md`. The human opened the coder's write paths for that one story (entry 11) and has closed them again since.
- **S0004 and S0006, coder and reviewer:** `make duplicates` reports 6 new findings. Five are outside this feature: `claude_runtime`/`opencode_runtime`, `hand_over`/`acceptance`, and three fields of `cost_records`. One is this feature's: `folder_readmes.readme_problems` reported as unused, because its only caller is the guard under `tests/`, as the Interface designed. It belongs in `security/duplicates-baseline.txt`, which is the human's file.
- **S0004, documenter:** `docs/decisions.md:1653` still says "the 23 paths". The human kept it as the record of the decision (S0004 entry 12).
- **S0005, documenter (entry 8):** The root README names `agents/` both in `## Where to read next` and in the new `## The folders`. See check 6.
- **S0006, coder and reviewer:** The heading check reads only the heading right before `in`/`of`. A quoted paragraph name before it is not checked (`agent-runtime.md:407` was fixed by hand). This is a known limit of the documented form, so I propose no story.
- **S0007, reviewer and smoke tester:** The Interface said 186 modules, and there are 188. The guard reads `git ls-files`, so nothing is wrong.
- **Mine:**
  - In `tests/README.md`, the subfolder sentences start in lower case (`- \`agents/\` the tests of …`), while the other 21 READMEs start them in upper case. It is cosmetic, and the guard does not check case.
  - S0007 changed `tests/vm/test_stage_image.py::test_the_first_line_names_the_build_command_with_the_runtime` to read line 2, so its name now says "first line" of a line that is second.

None of these is a broken promise. I propose no story beyond the two below.

## 5 The documentation as a whole

I read `README.md`, `docs/README.md` and the 22 folder READMEs from the top. In the project guide I read `style.md` *Folder READMEs*, `shared.md` *The folder READMEs* and *A reference to another page's heading*, and `README.md` *Shared test helpers*.

They agree with each other and with the code on:

- the 22 paths, and why `operator/template/` has no README
- the form
- the blocking rule
- the definition of a relative link
- the root of `tests/` holding its `README.md`

The License section of the README matches `LICENSE`, `NOTICE` and the guard. `make documents` runs every example green (two `vm` examples are not run, as before).

Findings:

- `style.md` says a folder README has "no other prose", but the code lets prose through on any line that carries a link (check 2). The documents are the stricter side, so they do not mislead a reader into breaking the form. F0055-S0009 brings the code up to them.
- `shared.md` says truly that "A README that does not exist yet is skipped". With every README written, that sentence now describes the hole of F0055-S0008, which updates it.
- The root README's `agents/` appears twice, once in *Where to read next* and once in *The folders*, with different words. Both are true. The human's answer in S0005 entry 4 asked for both "Where to read next stays as it is" and "the new section does not repeat it", which cannot both hold for `agents/`. See check 6.

## 6 Decisions taken for the human

For the human to accept or revisit:

1. Feature decisions 1 to 11, as `feature.md` lists them:
   - a README where a reader would ask
   - the README form, without a colon
   - the list as code
   - the helpers' list stays in the guide
   - S0001's leave
   - a README stays a pointer, with checked limits
   - Apache 2.0
   - a one-line SPDX header, with the copyright only in `NOTICE`
   - code and scripts, not tests
   - a new area cannot come without a README
   - no README in `operator/template/`
2. S0001 entry 9: the 25 words count only the sentence after the backticked name. `<n>` is the 1-based line number with blank lines counted. A subfolder line is a dash, the name in backticks ending in `/`, a space and a sentence ending in a period. Sentences are counted by their closing marks.
3. S0001 entry 29: one more round past the round cap. The reviewer's two notes became optional, and only one was done.
4. S0002 entry 14: the subfolder line has no colon. Criterion 3, which covers the layout link, the `contract/` sentence and `entry` without subfolder lines, has no test and was left to the reviewer.
5. S0003 entries 4, 11 and 16:
   - the tests route
   - the coder's write paths opened for one story, now closed
   - `tests/guards/README.md` links *Shared test helpers*
   - the human's `CLAUDE.md` change: the root of `tests/` holds `conftest.py`, its `README.md` and folders
6. S0004 entry 12: `decisions.md` keeps "the 23 paths" as a record, while `shared.md` says 22.
7. S0005 entry 4: `## The folders` has ten top folders and says which are the human's. *Where to read next* stays as it is. **To revisit:** "the new section does not repeat it" does not hold for `agents/`, which is now in both. Either drop the `agents/` line from *Where to read next* (a documents-only change), or accept the repeat.
8. S0005 entry 24: the glossary-link rule. A glossary word's first prose use in `README.md`, `docs/README.md` and `security/README.md` is a link, checked by script. This rule lives in that journal only, not in `style.md`.
9. S0006 entry 4 and S0007 entry 4: the criteria that intake proposed were accepted as written.
10. `readme_problems` is reported unused by `make duplicates` by design. Its entry in `security/duplicates-baseline.txt` is the human's to add.

Earlier tests changed, each with its leave:

- `tests/guards/test_old_layer_packages_removed.py`: S0002, the human's leave in S0002 entry 14. Renamed to `test_the_package_holds_only_its_init_its_readme_the_areas_entry_and_contract`.
- `tests/guards/test_tests_layout.py::test_the_root_holds_only_conftest_and_packages`: S0003, the leave in its Interface and entry 4.
- `tests/entry/test_check_documents_checked_files.py`: S0006, one test and constants added, no earlier row changed, the story's Interface allowing it.
- `tests/vm/test_stage_image.py::test_the_first_line_names_the_build_command_with_the_runtime`: S0007, the leave in its Interface ("an earlier test whose only failure is the one added header line").

S0001 used no leave under decision 5: reviewer, "Earlier tests: none". I checked the stories' commits with `git log --name-status` and found no other earlier test file changed. No earlier test was changed without a leave.

## 7 The slow checks

Beyond `make check`, the project offers `make documents`, which ran green (59.7 s, in check 2), and `make duplicates`, a report: `duplicates: 6 new, 39 known, 4 gone`. Check 4 says what those findings are. There is no image scan and no SBOM. `make mutants` was not run (check 3).

The JUnit report of my `make check` run (`.reports/junit.xml`) has 10,900 tests and 923 s of summed test time. The slowest tests are the 10-second time-limit tests, such as `tests/machine/adapters/test_podman_timeout_status.py` and `tests/shared/adapters/test_document_examples.py::…[past-the-limit]`, none of them this feature's. This feature's tests (folder READMEs, license headers, heading references) sum to 0.4 s.

Disk: the previous record, `disk start`, showed 17.5 GB free and 1.5 GB used on `/srv/factory/vm`. Now, at `disk acceptance`, it shows 16.8 GB free and 1.5 GB used. The free space dropped 0.7 GB on all three mounts, which share one pool, while the dataset's used space did not change. The feature added about 30 small text files and a few modules, which explains none of the 0.7 GB. The growth lies outside the stage dataset: images, snapshots or caches on the pool. It is worth a look by the human if it continues.

## 8 Cost

The stories took 81 runs, 122.2 min, 588 turns, 1,884,703 tokens in (13,403,199 more from cache) and 233,974 out, for $19.54.

S0001 stands out: 19 runs, 38.6 min and $6.48, a third of the feature. Its journal says why:

- the tester asked about two counts the Interface left open (entry 8)
- review sent it back three times over edge cases of the README form; the reviewer added criteria 9 and 10
- the round cap was reached (entry 28)

S0005 is next by runs: 13 runs and $2.43. It went through six docs-review rounds over glossary links and hit the round cap of docs-review (entry 23). The other five stories cost $1.69 to $2.78 each.

The human answered 13 questions (11 questions, 2 at the round cap) and the stories waited 0.6 h for them. S0001 and S0003 needed the human most, three answers each:

- S0001: the counts of the form, then the round cap.
- S0003: a structural problem. Its READMEs were documents, but the story needed a guard change, so it took the tests route, where no role could write `tests/README.md`. The human had to widen the coder's write paths for that one story, then settle two document findings that traced back to the answers.

## Proposed stories

- **F0055-S0008, A listed folder README that is missing fails the guard:** the guard still skips a missing README, so deleting one leaves `make check` green. This drops the skip, now that all 22 exist (test-only, with a leave the human gives).
- **F0055-S0009, A folder README keeps its opening and its link lines short:** an opening that carries a link escapes the two-sentence limit, and a line with a link may hold any amount of prose. This brings `readme_problems` up to decision 6 and `style.md`. All 22 READMEs of today already keep to the new rules.

## Journal

1. factory: started acceptance as vm.
2. acceptance-reviewer: accepted with stories; 2 stories proposed
   1 Scope: no gap. Every item in the Scope has its story (S0001 to S0007), and all 22 listed READMEs exist and are on the checked list. Still open, by `feature.md`, the human's: factory/README.md, factory/features/README.md and docs/runs/README.md.
   2 Smoke test: green. 22 READMEs with no problems, 188 modules and 18 scripts carry the SPDX line, `make documents` is ok, and a new subfolder and a wrong heading in a clone are caught. Two holes found: a missing listed README is skipped, not failed, and a line that carries a link escapes the form's limits (an opening of five sentences with a link gives []).
   3 Mutation testing: by sweep, not run here.
   4 Noticed:
   - the `_run` test helper is copied in two test modules (moving it was made optional and not done)
   - `readme_problems` is reported as unused by `make duplicates` by design; its baseline entry is the human's
   - the archived S0002 Description is stale, because the tester's rewrite could not land
   - `tests/README.md` writes its subfolder lines in lower case
   - `test_stage_image`'s "first line" test now reads line 2
   - the Interface's module count was off (186 for 188)
   5 Docs: consistent with each other. style.md's "no other prose" is stricter than the code (S0009). shared.md's skip sentence describes the hole (S0008). The root README names `agents/` twice.
   6 Decisions: feature decisions 1 to 11 and ten answers from the journals, listed. To revisit: S0005's "Where to read next stays" and "the new section does not repeat it" conflict for `agents/`. Four earlier tests changed, each under a named leave; none without one.
   7 Slow checks: `make documents` ok (59.7 s). `make duplicates` reports 6 new, 1 of them this feature's. No scan, no SBOM. Disk free dropped 0.7 GB on the pool with dataset use unchanged at 1.5 GB, which the feature's text files do not explain.
   8 Cost: 81 runs, 122.2 min, $19.54. S0001 took a third ($6.48, 19 runs: two open counts, three review rounds, the round cap). The human answered 13 questions (11 questions, 2 at the round cap) and the stories waited 0.6 h. S0001 and S0003 needed the human most, 3 answers each; S0003's because no role could write tests/README.md on the tests route.
   Proposed: F0055-S0008 (a missing listed README fails the guard) and F0055-S0009 (the opening and link lines of a folder README keep their limits). Both pass `factory-check-story`, and both smoke tests are red today.
