---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 519
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T11:35:40.812641Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T11:35:40.819882Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-03T11:36:05.816957Z'
  stage: intake
  run: 3e7946b57b4840c5b6128984b909b43c
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-03T11:36:31.326274Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-03T11:36:59.892158Z'
  stage: tests
  run: 00e95af8d4ea47f3af805099debdf4b7
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-03T11:37:05.399791Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-03T11:40:35.873920Z'
  stage: doing
  run: 3636e6408d594364ab0ef3b37c8ab4d9
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-03T11:40:43.579583Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-11-03T11:41:10.600209Z'
  stage: review
  run: 2448efc442c34a408c696752665da186
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-03T11:41:16.363816Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-11-03T11:41:30.725832Z'
  stage: doing
  run: 0415260e0fff42839bc8439d7b9ea410
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-03T11:41:36.497332Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-03T11:42:04.743285Z'
  stage: tests
  run: fb3d3cb265db408488c71520285420ad
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-03T11:42:10.684298Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-03T11:45:31.323520Z'
  stage: doing
  run: 1d63cd24fc6448f48fae18e59991732c
---

# The project guide and the decision log describe the operator's scripts

<!-- proposed by feature acceptance of 2026-11-03; the human added part B on 2026-11-03 (decision 25) -->

## Description

F0048 added `operator/`: the site loader (`operator/bin/site`, `operator/lib/site.sh`), the hosting client (`operator/lib/hosting.sh`), `operator/job/job.sh`, the sanitiser (`operator/bin/sanitise`) and the skill's scripts under `operator/skill/kumpel/scripts/`. It also added twelve test modules `tests/test_operator_*.py` with their support modules. The operator guide describes all of this for the operator. The agents' documents do not, because no story's docs criterion named them for `operator/`. The project guide (`docs/project-guide/`) has no file for this domain, and its index names no file under `operator/`. So an agent whose story touches the scripts finds no domain file to read first, which is what `CLAUDE.md` tells it to do. The index's list of support modules ("Every module `tests/*.py` whose name does not start with `test_`") misses ten modules. Five of them are this feature's: `operator_support.py`, `operator_job_support.py`, `operator_skill_support.py`, `site_check_support.py` and `scripted_tick_support.py`. Five are older: `command_words_support.py`, `container_extra_support.py`, `opencode_provider_support.py`, `power_support.py` and `token_support.py`. A tester who looks there for a helper does not find them, and the feature already holds copies made that way (`gcloud_words` beside `words`, and `JOB` and `IMPERSONATE` defined twice). The decision log (`docs/decisions.md`) has entries for the feature's code-side decisions (10, 13, 15, 17, 20, 23 and the `-I` rule) but none for the site file's design (decisions 1 to 9, 11, 12 and 14 of `feature.md`), the died line (19) or the job's one image (24). Their reasons live only in an archived `feature.md`. This story writes those documents. It changes no code and no test; the copied test helpers stay as they are.

**Part B: the repository's new name.** On 2026-11-03 the human renamed the repository from `pkrahmer/factory-rf` to `pkrahmer/kumpel-factory` (decision 25). GitHub redirects the old URLs, but the current texts still give the old name: the README's title, the operator guide's example URLs and its "factory-rf's own" passages, the project guide's opening and its template line, and two texts of the Kumpel skill. Part B gives them the new name. History keeps the old one: archived work items, the decision log's earlier entries, `planning/` and `docs/runs/` stay as they are. `CLAUDE.md` is the human's and is changed by the human.

## Interface

Part A: the documenter writes `docs/project-guide/operator.md` (new), `docs/project-guide/README.md` and `docs/decisions.md`.

Part B: the coder changes the old name in `operator/skill/kumpel/SKILL.md` (the factory instance it works beside is `kumpel-factory` v1.2 or later) and in `operator/skill/kumpel/references/standing-orders.md` (the rules come from running the factory's own build with the human; the sentence keeps its dates). The documenter changes it in `README.md`, `docs/operator-guide.md` and `docs/project-guide/`. No module under `src/factory/` and no other script changes.

Tests: one new text test over the two skill texts: neither contains `factory-rf`.

## Acceptance criteria

1. (B) `operator/skill/kumpel/SKILL.md` and `operator/skill/kumpel/references/standing-orders.md` contain no `factory-rf`; one row per file. Every other line of both stays, and the tests that pin `SKILL.md` stay green.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/operator.md`, new: a title, a sentence on what it covers, and sections for the following. Each describes what the scripts do today, with the paths and the names of the functions. *The layout*: the files under `operator/`, and that `operator/README.md` is the documenter's (decision 22). *The site file and its loader*: values stored literally, never executed; a file in a git work tree refused; only `SITE_` keys; the environment wins; status 1, 2 and 3; the folders `~/.config/kumpel/` and `~/.local/state/kumpel/`. *The hosting client*: `hosting_token`, `hosting_api` and `hosting_git`; `SITE_TOKEN_CMD` with `gh auth token` as the fallback; the token never in an argument list (curl's configuration on standard input, `GIT_CONFIG_*` for git). *`job.sh`*: its commands, the state file, the start script taken from `SITE_CODE_REF` with `git show`, no guessed values, no two executions at once. *The sanitiser*: the site's rules file and the leak check. *The skill's scripts*: every `python3` started with `-I`, each hosting read assigned to a variable before it is parsed, and comments posted only through `comment.sh` with the signature and the marker. *Tests of the scripts*: stand-ins on the `PATH` for `gcloud`, `gh` and `curl`; the real `git` with a local bare repository; the support modules that hold them, and the test modules by script.
   - `docs/project-guide/README.md`: a line for `operator.md` under *The files*. Under "Every module `tests/*.py` whose name does not start with `test_`", one line for each of the ten modules named in the Description, each saying what it holds, read from the module.
   - `docs/decisions.md`: one entry each, with date, decision, why and what was rejected (taken from the stories' journals where they name it), for:
     - the site file is data and lies outside every repository (decisions 1, 2, 3 and 11);
     - the hosting token comes from a command the site names and is never in an argument list (decisions 4, 5 and 14);
     - `job.sh` works from the site's values alone, never guesses, never overlaps, and runs the start script of the code it clones (decisions 6, 7 and 12);
     - a reset to a tag needs three things (decision 8);
     - the sanitiser's rules are the site's (decision 9);
     - a run that dies leaves its text in the factory log (decision 19);
     - the job keeps one image in memory, and a machine prunes after a rebuild (decision 24).
   - Part B: `README.md`'s title becomes `# kumpel-factory`. In `docs/operator-guide.md` the example URLs become `https://github.com/pkrahmer/kumpel-factory.git`, and the passages that say "factory-rf's own" say "kumpel-factory's own". In `docs/project-guide/` the old name becomes the new one. Nothing else in these files changes for part B, and `docs/decisions.md` gets one entry for the rename (decision 25), which may name the old name. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
test -f docs/project-guide/operator.md && echo present; grep -c '`operator.md`' docs/project-guide/README.md
```
Expect: `present`, then a number of at least `1`

```bash
for m in command_words_support.py container_extra_support.py opencode_provider_support.py operator_job_support.py operator_skill_support.py operator_support.py power_support.py scripted_tick_support.py site_check_support.py token_support.py; do grep -q "\`$m\`" docs/project-guide/README.md || echo "missing $m"; done; echo listed
```
Expect: `listed` alone, with no `missing` line before it

```bash
grep -c -i 'site file' docs/decisions.md; grep -c -- '--layers=false' docs/decisions.md; grep -c 'SITE_TOKEN_CMD' docs/decisions.md
```
Expect: three numbers, each at least `1`

```bash
git grep -c 'factory-rf' -- README.md docs/operator-guide.md docs/project-guide operator src claude vm template; echo "exit $?"
```
Expect: `exit 1` alone (no file listed)

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names the concrete files (operator.md, project-guide README.md, decisions.md for the documenter; SKILL.md and standing-orders.md for the coder) and the one new text test. No signatures are needed, since no code changes. I read the two skill texts: each holds exactly one `factory-rf` (SKILL.md:8, standing-orders.md:3), and no test under tests/ or file under operator/ pins the old name, so the change cannot break a pinned test.
   Criteria: criterion 1 is testable by one parametrized test with one row per file, and its failing side is the old name present. Criterion 3 is the docs criterion: each part names a file, the sections, the ten support modules and the seven decision entries, and the document check plus the smoke commands can verify them. The Interface states no conversion, limit or error rule that lacks a criterion.
   Smoke test: the five commands are runnable. The two greps and the loop print the stated outputs. The `git grep` path list gives exit 1 only once the old name is gone, and it leaves out docs/decisions.md, which may name it. The `check_documents` command is the project's own. None runs pytest, so the `-q` rule does not apply. Each Expect line is checkable.
   Architecture: the story changes no code and no layer. It writes within the roles' write paths: the coder under operator/, the documenter under README.md and docs/. CLAUDE.md, planning/ and docs/runs/ are left alone.
   Scope: the story is inside F0048's scope (the last Scope bullet names S0019) and breaks nothing in Out of scope. Decisions 22 and 25 of feature.md match the Description.
4. factory: started tests as vm.
5. tester: I wrote the one text test the Interface asks for: a parametrized test with one row per skill text, which checks that the text contains no `factory-rf`.

   criterion 1: tests/test_operator_skill_name.py::test_the_skill_texts_do_not_name_the_old_repository (rows `skill` for operator/skill/kumpel/SKILL.md and `standing-orders` for operator/skill/kumpel/references/standing-orders.md). The rest of criterion 1 ("every other line of both stays, and the tests that pin `SKILL.md` stay green") is covered by the existing tests/test_operator_texts.py and tests/test_operator_skill_signature.py. I did not change them.
   criterion 2: no test; `make check` is the coder's gate.
   criterion 3: no test; it is the docs criterion, checked by the docs stage's document check and the smoke test.

   Files created: tests/test_operator_skill_name.py (a new module, so that no other story's test file changes; it uses `ROOT` from tests/operator_support.py).
   Modules the test run could not import: none. The code under test is the two texts, so both rows fail for the right reason: each file still contains `factory-rf` (SKILL.md:8 and standing-orders.md:3), and `uv run pytest -q tests/test_operator_skill_name.py` showed 2 failed with an AssertionError.
   `make lint` is green after ruff sorted the import block. I skipped the type check, as the stage says.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: I changed the repository's name in the two skill texts, as part B of the Interface asks. Each file had one line with `factory-rf`, and that line is the only one I changed:
   - operator/skill/kumpel/SKILL.md:8 now says "(kumpel-factory v1.2 or later)".
   - operator/skill/kumpel/references/standing-orders.md:3 now says "running kumpel-factory's own build with the human". The dates stay.

   Main choice: I replaced only the name and kept the rest of each sentence word for word, so every other line stays and the tests that pin `SKILL.md` are not affected. I rejected rewording the sentences (for example "the factory's own build"): the Interface asks only that the name be the new one.

   Refactor: the diff is two one-word substitutions, and nothing needed changing.

   `make check` is green (test: green, check: green), including tests/test_operator_skill_name.py.

   Noticed but not touched: the old name is still in README.md, docs/operator-guide.md and docs/project-guide/. Those files are the documenter's under part B and the docs criterion. The journal did not change the meaning of the task, so I did not rewrite the Description.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 42 known, 0 gone
8. factory: started review as vm.
9. reviewer: 1. tests/test_operator_skill_name.py:9: `SKILL_DIRECTORY = ROOT / "operator" / "skill" / "kumpel"` is a second copy of the constant `SKILL` at tests/test_operator_skill_signature.py:22, which is the same skill directory. This is the kind of copy the Description says the feature already holds too many of. Fix (the tester's, under the standing leave): move the skill directory constant to tests/operator_skill_support.py, which already holds `SCRIPTS` under that directory, and have both test modules import it from there. Each earlier test keeps its name and what it checks.

   What I checked and found sound:
   - Criterion 1 has one parametrized test with one row per file (`skill`, `standing-orders`). Each row fails while `factory-rf` is present (the tester's run before the code change shows this) and passes now. The coder's `make check` was green (journal entry 7).
   - The diff changes exactly one line in each skill text, and the line keeps its dates.
   - `git grep factory-rf` finds nothing left under operator/, src/, claude/, vm/ or template/. The only remaining hits are in README.md and docs/, which the documenter changes under part B.
   - Architecture: no change under src/. Security: no secrets and no suppression markers. Work item: the Description, Interface and docs criterion match what was built.

   Earlier tests: none. The diff only adds tests/test_operator_skill_name.py and changes no test file that `main` holds.
10. factory: started doing as vm.
11. coder: The reviewer's one finding is a copied test helper, so it is a change to tests. I changed no code this round.

    The tester should make this move under the standing leave in `CLAUDE.md`. Move the skill directory constant (`ROOT / "operator" / "skill" / "kumpel"`) into tests/operator_skill_support.py, which already builds `SCRIPTS` under that same directory. Then have two modules import it from there:
    - tests/test_operator_skill_signature.py, where it is `SKILL` at line 22 (the earlier test file);
    - tests/test_operator_skill_name.py, where it is `SKILL_DIRECTORY` at line 9.

    `SCRIPTS` could then be built from the moved constant. Every earlier test keeps its name and what it checks.

    I confirmed the copy: both constants name the same directory.

    Code state: the two skill texts are as I left them in entry 7, each with one line changed (operator/skill/kumpel/SKILL.md:8 and operator/skill/kumpel/references/standing-orders.md:3). `make check` was green there. I did not run it this round because nothing under my write paths changed.

    What the journal changed: nothing in the meaning of the task, so the Description stays as written.

    Noticed but not touched: the old name is still in README.md, docs/operator-guide.md and docs/project-guide/. Those files are the documenter's under part B.
12. factory: started tests as vm.
13. tester: I moved the copied helper that the reviewer found (entry 9), as the coder named it in entry 11. CLAUDE.md's standing leave covers this move.

    - tests/operator_skill_support.py now defines `SKILL = ROOT / "operator" / "skill" / "kumpel"`, and `SCRIPTS` is built from it as `SKILL / "scripts"`.
    - tests/test_operator_skill_signature.py is an earlier story's test file, changed under the standing leave. It now imports `SKILL` from operator_skill_support instead of defining it. I removed `ROOT` from its operator_support import because nothing else in the module used it. Every test keeps its name and still checks the same thing.
    - tests/test_operator_skill_name.py imports `SKILL` from operator_skill_support in place of its own `SKILL_DIRECTORY`.

    I left the separate `SKILL` constant in tests/test_operator_texts.py alone. It is the path to SKILL.md, not to the directory, and neither the reviewer nor the coder named it.

    The criterion mapping is the same as in entry 5:
    - criterion 1: tests/test_operator_skill_name.py::test_the_skill_texts_do_not_name_the_old_repository, with rows `skill` and `standing-orders`.
    - criteria 2 and 3: no test. `make check` is the gate for criterion 2, and the docs stage checks criterion 3.

    Files created: none this round. Changed: tests/operator_skill_support.py, tests/test_operator_skill_signature.py, tests/test_operator_skill_name.py. Modules the test run could not import: none.

    `uv run pytest -q tests/test_operator_skill_name.py tests/test_operator_skill_signature.py`: all 20 tests passed. `make lint`: lint: green.

    `lint`: lint: green (0.1 s)
14. factory: started doing as vm.
15. coder: Round 1 had one finding, the copied skill directory constant. The tester fixed it in entry 13 by moving it to tests/operator_skill_support.py as `SKILL`, so there was nothing left for me to change in code this round.

    What I built is still what entry 7 describes: one line changed in each skill text, operator/skill/kumpel/SKILL.md:8 ("kumpel-factory v1.2 or later") and operator/skill/kumpel/references/standing-orders.md:3 ("kumpel-factory's own build", dates kept).

    Main choice: I swapped only the name and kept the rest of each sentence word for word. I rejected rewording the sentences (for example "the factory's own build"), because the Interface asks only for the new name.

    I ran `make check` on the tester's changed tests (tests/operator_skill_support.py, tests/test_operator_skill_signature.py, tests/test_operator_skill_name.py) together with my two text changes, and it is green: test: green, check: green.

    Refactor: no new diff this round, so nothing to change.

    The journal did not change the meaning of the task, so the Description stays as written.

    Noticed but not touched: the old name is still in README.md, docs/operator-guide.md and docs/project-guide/. Those files are the documenter's under part B. tests/test_operator_texts.py has its own `SKILL` constant, but it is the path to SKILL.md, not to the directory, so it is not a copy of the moved one.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
