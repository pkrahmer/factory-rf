---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 522
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T12:44:26.901103Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T12:44:26.907736Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-03T12:44:52.694432Z'
  stage: intake
  run: 0bd46d9614b343c0ae41b534ea0cc8cb
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-03T12:44:58.330927Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-11-03T12:45:12.348407Z'
  stage: tests
  run: c4d6c7a4ac564f5bb928914b5963c341
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-03T12:45:20.200450Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-11-03T12:47:08.343309Z'
  stage: doing
  run: e6076e247e3f4917b436b4e87d333ffe
---

# The decision log gives the feature's own reasons for the operator's scripts

<!-- proposed by feature acceptance of 2026-11-03; refined with the human's answers of 2026-11-03 (decision 27) -->

## Description

F0048-S0019 wrote seven entries for F0048's lasting decisions in `docs/decisions.md`, from *The site file is data and lies outside every repository* to *The job keeps one image in memory, and a machine prunes after a rebuild*. Its documenter did not open `feature.md` or the stories' journals. So it wrote each entry's "Why" and "Rejected" from the scripts and the operator guide, and asked in its entry 19 for the entries to be checked against the feature's decisions. The acceptance F0048-A0004 made that check. No entry contradicts what the scripts do. Some entries leave out the reason the human gave, and some "Rejected" lines name options that no decision and no journal names. This story adds the missing reasons and the one lasting rejection a journal names, and keeps each entry's heading and its "Decision" line. The reasons to add, taken from F0048's `feature.md` and journals:

- **The site file** (decisions 3 and 11; S0001):
  - A name that is not a `SITE_` key is refused with its line number, so a typo or a pasted secret does not pass silently.
  - `~/.config/kumpel/` holds the site file, its sanitiser rules and the skill's `settings.json`, and `job.sh`'s state file lies in `~/.local/state/kumpel/`, because Kumpel is the product and one folder holds what one machine knows.
  - Rejected (S0001's journal): collecting the pairs in one pass and exporting them at the end, because POSIX `sh` would need a list joined by a delimiter, and that breaks on values that contain the delimiter. So the loader reads the file twice, once to check and once to export.
- **The hosting token** (the Goal, decisions 5 and 14):
  - The skill's scripts called `gh`, whose login did not see the project's repository at work.
  - With `SITE_TOKEN_CMD` unset, `gh auth token` keeps the home setup as it is.
  - Tests of the scripts use the real `git`, and what `hosting_git` gives git is read back through `git config` and git's own trace, not through a stand-in.
- **`job.sh`** (decisions 6 and 7; S0005):
  - The job's wrapper only writes the provider file and hands over to `vm/job-start.sh`. The `PATH` and the private token folder are fixed in that script, so the job's arguments carry no logic.
  - `create` refuses a job that exists.
  - An overlap is refused because a platform that cannot cancel an execution makes an overlap expensive.
  - Rejected (S0005's journal): the wrapper calling `python3` inside the job, because the job's image, `debian:trixie-slim`, has no `python3`; `provider_json` runs on the operator's machine.
- **The reset to a tag** (decision 8): the factory's own repository must never be its target.

Five "Rejected" options were named in no decision and no journal. The human went through each on 2026-11-03 (decision 27):
- Kept as the human's, marked `(the human, 2026-11-03)`: in the site file entry, "keeping the values in the repository, as an ignored file"; in the token entry, "a token stored in the site file"; in the reset entry, "a prompt on the terminal".
- Kept and folded into decision 12's reason: in the `job.sh` entry, "reading the script from the working tree or from the code host at run time" becomes "reading the start script from any source other than `SITE_CODE_REF`: the working tree, or the code host at run time (the script would not be of the commit the job runs; decision 12)".
- Reworded, because as written it contradicts `job.sh`, which has defaults for the job's sizes: in the site file entry, "a second source of defaults inside the scripts, which would guess where the file is silent" becomes "defaults for the site's names (project, region, job, repository); the job's sizes are the only defaults, and the example's comments name them (decision 21)".

Earlier entries of the log, the code, the tests and every other document stay as they are.

## Interface

Documents only. The documenter changes the seven F0048 entries of `docs/decisions.md` that S0019 wrote, and nothing else. No script, no module under `src/factory/` and no test changes. No new test: the change is checked by the document check and the smoke test.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/decisions.md`, in the seven F0048 entries S0019 wrote, and nowhere else:
   - *The site file is data and lies outside every repository*: its "Why" names the typo or pasted secret, and the one folder that holds what one machine knows, with `~/.local/state/kumpel/`. Its "Rejected" names the one-pass collection and its delimiter.
   - *The hosting token comes from a command the site names ...*: its "Why" names `gh`'s login that did not see the project's repository at work and the home setup the fallback keeps. Its "Decision" or "Why" names the real `git` in the tests, read back through `git config` and git's trace.
   - *`job.sh` works from the site's values ...*: its "Decision" names the wrapper that only writes the provider file and hands over, and `create` refusing a job that exists. Its "Why" names the platform that cannot cancel an execution. Its "Rejected" names `python3` in the job's image.
   - *A reset to a tag needs three things*: its "Why" says the factory's own repository must never be the target.
   - The five "Rejected" options are handled as the Description says: three keep their words and gain `(the human, 2026-11-03)`, the `job.sh` one reads as given there, and the site file's "second source of defaults" is replaced by the given wording.
   - Every other line of the log stays. `uv run python -m factory.entry.check_documents` prints `documents ok`. `README.md`, `docs/operator-guide.md` and the project guide: none, since they describe what the scripts do, which does not change.

## Smoke test

```bash
for p in 'pasted secret' 'what one machine knows' 'did not see' 'home setup' 'cannot cancel' 'trixie-slim' 'delimiter' "factory's own repository"; do printf '%s: ' "$p"; grep -c -- "$p" docs/decisions.md; done
```
Expect: eight lines, one per phrase, each ending in a number of at least `1`

```bash
grep -c -- 'a second source of defaults' docs/decisions.md; grep -c -- 'other than `SITE_CODE_REF`' docs/decisions.md; grep -c -- '(the human, 2026-11-03)' docs/decisions.md
```
Expect: `0`; then a number of at least `1`; then a number of at least `3`

```bash
git diff --stat main...HEAD -- docs README.md
```
Expect: one changed file, `docs/decisions.md`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: documents only. It names the one file (`docs/decisions.md`) and the seven F0048 entries from S0019, and says that no script, module or test changes. No signatures are needed. I confirmed the entries exist (the log's lines ~1384 to 1408).
   - Criteria: the docs criterion lists each entry, the reason or rejection it must gain, and the three kinds of "Rejected" handling, each with its wording. Each is checkable by grep. The Interface states no rule with a failing side. `make check` is the first criterion and `docs:` is last.
   - Smoke test: the commands are runnable (`grep -c`, `git diff --stat`, and `check_documents`, which exists in `src/factory/entry`). Each `Expect:` is a count or a literal output. The current log gives 0 for `pasted secret`, `what one machine knows`, `home setup`, `cannot cancel`, `trixie-slim`, `delimiter` and `factory's own repository`, so those probes fail before the work and can pass after it. `did not see` is already 1, so that probe proves little, but it is not wrong. `a second source of defaults` is 1 now and must reach 0.
   - Architecture: the change touches only the decision log, which the documenter owns. No layer is involved.
   - Scope: within F0048's scope line for S0021 (decision 27 of `feature.md`). It touches none of the feature's Out of scope items. Earlier entries, code and the other documents stay as they are.
   The story names no test. Tests is the only forward decision available, so I am ending with it.
4. factory: started tests as vm.
5. tester: No tests written: the story changes only documents.
   - criterion 1 (`make check` stays green): no test of its own. The coder's `make check` checks it.
   - criterion 2 (docs: the seven F0048 entries of `docs/decisions.md`): no test. The Interface says "No new test: the change is checked by the document check and the smoke test". The documenter's `make documents` and the smoke test's greps check it.
   Files created: none. Modules the test run could not import: none, because no test was added, so I did not run the tests. `make lint` is green.

   `lint`: lint: green (0.1 s)
6. factory: started doing as vm.
7. coder: No code built. The story changes only documents. Its Interface says that no script, no module under `src/factory/` and no test changes, and the tester wrote no tests. So the doing stage had nothing to make pass.
   - What I did: ran `make check` on the branch as it is. It ends `test: green (83.0 s)` and `check: green` (coverage 99.56 %), so criterion 1 holds.
   - Main choice: I left `docs/decisions.md` alone, though the work is to rewrite its seven F0048 entries. The rejected alternative was to write those entries myself in this stage. I rejected it because `CLAUDE.md` gives the decision log to the documenter stage, which keeps the docs from each story's docs criterion. The coder does not write the docs. Criterion 2 (every reason, rejection and rewording the Description lists) is therefore still open for the documenter.
   - Refactor: there is no diff to refactor.
   - Description: no journal entry changed the meaning of the task, so I left it as it is.
   - Noticed, not touched: intake noted that the smoke test's `did not see` probe already counts 1 on `main`, so it proves little. I left it as it is.

   `check`: check: green (not run again: passed on tree 676ce2a5aa50 at 2026-11-03T11:54:59Z)
   `duplicates`: duplicates: 0 new, 42 known, 0 gone
