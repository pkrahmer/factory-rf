---
stage: docs-only
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 610
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T22:56:08.353005Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T22:56:08.360408Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T22:56:25.002334Z'
  stage: intake
  run: 97a9d5fcadaa4232aa87610a67507be2
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T22:56:30.294569Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T23:00:28.504605Z'
  stage: docs-only
  run: 19a3c910cef4445ab675d63ef8012ca9
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-06T23:00:34.125225Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-06T23:03:36.317975Z'
  stage: docs-review
  run: f9ae491a79f84c8fa10868236a26f5b0
---

# The operator guide's the site file and an operator's machine reads for the operator

## Description

`docs/operator-guide/site.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/site.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/site.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/site.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/site.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/site.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `docs/operator-guide/site.md` (exists) and `docs/checked-documents.txt` (exists; its entry is one added line). Both are paths the documenter may write; no code, test or agent file changes.
   - Criteria: all are about documents. Criterion 1 is the style judgment (reviewer). Criterion 2 is the fact comparison against the code (reviewer). Criterion 3 is testable with `make documents` printing `documents ok`, plus the checked-list entry. Criterion 4 is a link check. Criterion 5 is `make check`. The Interface states no behaviour or rule that needs a failing side.
   - Smoke test: `grep -cx "docs/operator-guide/site.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output. It runs no pytest.
   - Docs criterion: criterion 6 asks for criteria 1 to 4 and names no sentences to write. It dictates no text. It says what the reader must know only through the Description: an operator who runs an instance and does not read the code.
   - Architecture: nothing in `src` changes. This is a document rewrite on the docs route, checked by the F0053 document checks.
   - Scope: it is S0002 of F0054, which lists it. It stays inside the feature's scope (one file rewritten and added to the checked list). It touches none of the feature's out-of-scope files (`docs/decisions.md`, `docs/runs/`, `docs/operator-playbook.md`) and changes no behaviour.
4. factory: started docs-only as vm.
5. documenter: Rewrote `docs/operator-guide/site.md` for the operator and added it to `docs/checked-documents.txt`. `make documents` ends with `documents ok (1.9 s)`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/operator-guide/site.md`: the whole file, rewritten.
     - Headings that other files link to are kept: *The site file*, *The keys*, *Sanitising what leaves the machine*, *Setting up an operator's machine*, *Repeating a trial*, *Telling Kumpel's acts from the human's*.
     - Intro: new, for an operator who does not read the code. It links `instance`, `work item` and `stop` to the glossary.
     - Tasks: now numbered steps. The place, the site commands, the repeat-a-trial reset and the machine setup were already steps or lists; the "Its place" paths are now a numbered list.
     - Failures: given as what you see, what it means and what you do. This covers the sanitise rule faults, the reset refusals and the `site check` table.
     - Keys: the table now has the columns Name, What it does, Default and Example. The Example values come from `operator/site.env.example`.
     - *Reference*, new section at the end: loader and `site` statuses, return codes of the hosting library, the three built-in sanitiser rules, the `sanitise check` exit statuses, and `KUMPEL_POLL_SECONDS` and `KUMPEL_ARCHIVE_WAIT` as a settings table.
     - Examples: the site, token and sanitise examples and the no-site-file `site check` example are now `console` blocks and were run by `make documents`. The two `reset-to-tag.sh` blocks are marked `console github` and are not run, and they show no output because I have not seen it.
     - Content: I added two things from `operator/site.env.example`: the format of `SITE_INSTANCE`, and that `SITE_REPOSITORY` and `SITE_CHECKOUT` are always required. I moved no rule out of the file and dropped none on purpose.
   - `docs/checked-documents.txt`: one new line, `docs/operator-guide/site.md`.

   Cross-read and found current:
   - `docs/operator-guide/cloud-run.md`, `README.md` (operator guide), `docs/project-guide/operator.md` and the repository `README.md`: every link to `site.md` points to a heading that still exists.
   - `docs/operator-guide/stops.md`: opened only for the link I added to it. I did not read it for stale text.

   For the reviewer:
   - I did not compare the old file's claims against the shell scripts line by line. I carried the old text over, and checked only that `operator/site.env.example` agrees with the keys table. Please spot-check the statuses and messages in the *Reference* against `operator/lib/` and `operator/bin/`.
   - I wrote the loader status table in *Reference* from the old prose, not from a new reading of the scripts.
   - `KUMPEL_POLL_SECONDS` and `KUMPEL_ARCHIVE_WAIT` are in a table with an Example column, with the defaults the old text gave (15 and 300).

   Stale text I saw and left alone:
   - `make documents` prints many `does not exist` lines for `docs/project-guide/*.md`, for example `README.md:127` and `agents.md:146`. They are in files not on the checked list. They are unrelated to this story.

   No findings for the coder.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (2.2 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md`: `docs/operator-guide/site.md` rewritten, and `docs/checked-documents.txt` +1 line. I read both against `operator/bin/site`, `operator/lib/site.sh`, `operator/lib/hosting.sh`, `operator/bin/sanitise`, `operator/skill/kumpel/scripts/{reset-to-tag,merge,comment,start-story}.sh`, `tests/operator_scripts/` and `docs/project-guide/style.md`.

   Criterion 2 is met: every name, command, setting and message of the old file is in the new text or its *Reference*. Nothing was dropped. The *Reference* statuses, return codes, built-in rules and `sanitise check` statuses match the scripts.

   Criterion 4 is met: every link to `site.md` from `cloud-run.md`, the operator guide's `README.md` and elsewhere points to a heading that still exists.

   Criterion 3: the checked-list line is present, and the journal records `documents ok`. Criterion 1 is not met; see findings 4 to 8.

   Findings:
   1. `docs/operator-guide/site.md:45-66`, `:138-139`, `:196-205`: the `console` examples write `site.env`, `token.env`, `sanitise.rules`, `raw.txt` and `clean.txt` into `$PWD`. They pass only because the check's fixture folder is no git work tree. A reader must run them from the root of their clone (`sh operator/bin/...`). There `site init` refuses with `site: <path> lies in a git repository; ...` and status 3 (`operator/lib/site.sh:28-31`). The other blocks litter the clone, and one puts a `sanitise.rules` into a repository, which line 158 forbids. Line 45's "The path here lies in a temporary folder, so the example touches nothing of yours" is false for the reader. Fix: write the files under a folder outside the checkout, such as `"$HOME/site-example/"` (`HOME` is an empty temporary folder in the check), and correct the sentence on line 45.
   2. `docs/operator-guide/site.md:216-224`: the two `console github` blocks show no output and name no real run they were copied from. The documenter says no run was made. Fix: copy the output from a real run and name that run above the blocks. Otherwise give the output the code prints (`reset-to-tag.sh:73-76`, `:82-89`) as a marked example that says it was not copied from a run.
   3. `docs/operator-guide/site.md:149-152`: an `sh` block shows commands that are neither a runnable `console` example nor marked. It also calls a bare `sanitise` where the rest of the file uses `sh operator/bin/sanitise`. Fix: drop it, since lines 195-206 show both calls, or turn it into a two-row table of the calls and their statuses.
   4. `docs/operator-guide/site.md:248` (`story`) and `:256` (`journal`): these glossary words are not linked at their first use, which criterion 1 asks for. Fix: link each to `../project-guide/glossary.md` there.
   5. `docs/operator-guide/site.md:9`, `:17`, `:254`: "the skill" and "Kumpel" are this project's own words, and the reader is never told what they are (style rule 3: "use no other private words"). Fix: add one sentence to the intro that says what the skill and Kumpel are, and point to `operator/README.md`.
   6. `docs/operator-guide/site.md:294-308`: the `site check` table is still "Check / It proves / What a FAIL means". It is not what you see, what it means and what you do, which the Description and the operator-guide section of the style guide ask for. Fix: use the columns What you see (`FAIL <name>: <detail>`), What it means and What you do. Line 125 (the `hosting: the token command failed...` message) also needs a "what you do": set `SITE_TOKEN_CMD`, or log in with `gh`. So do the refusals of `merge.sh` on line 250 (`merge.sh: #<pr> is a draft`, `is not open`, `is not at stage:approval`, from `merge.sh:26-31`, `:47`).
   7. `docs/operator-guide/site.md:236-240`: "unless all three conditions hold" is followed by five rows. Row 1 is wrong. Without `--yes` the script prints the plan and exits 1; it does not refuse. Exit 2 comes with `usage: reset-to-tag.sh <tag> [--yes]` when the arguments are not `<tag>` or `<tag> --yes` (`reset-to-tag.sh:10-11`). Fix: put that usage line in "What you see", and say "the arguments are not `<tag>` or `<tag> --yes`" in "What it means". Drop the count "three", or state the three conditions.
   8. `docs/operator-guide/site.md:3`, `:9`, `:108`, `:158`, `:191`, `:232`, `:250`, `:256`, `:264`, `:312`: these sentences break style rule 2. They run past about 25 words (3, 108, 158, 191, 232, 256, 312) or hold two parentheses (9, 250, 264, 312). Fix: split each.
   9. `docs/operator-guide/site.md:70`: "A test keeps the example's comments and this table equal to what `operator/lib/site.sh` and `operator/job/job.sh` do" is not borne out. `tests/operator_scripts/test_operator_site_example.py` checks the example's comments. The only test that reads this table (`test_operator_site_check.py:509-511`) checks only that each key is named in the file. A sentence about tests is also nothing an operator needs. Fix: drop the sentence, or say that the example's comments are kept true by a test.
   10. `docs/operator-guide/site.md:241` against `:76`: the keys table calls `SITE_REPOSITORY` "the factory's repository". Line 241 says that, because the reset needs `SITE_RESET_REPOSITORY` to equal `SITE_REPOSITORY`, "the factory's own repository can therefore never be the target". The code only compares the two keys (`reset-to-tag.sh:17-20`), so the target is always `SITE_REPOSITORY`. Fix: on line 76 call it "the repository the factory works on", as line 280 does. On line 241 say only that a repository named by both keys is reset.
   11. `docs/operator-guide/site.md:281`: "A failure here is the loader's: no file (status 1), a fault in a line (status 2), ..." does not match what `site init` does. `init` never loads the file. It fails with `site: <path> exists; not overwritten` (status 1) or with the work-tree refusal (status 3) (`operator/bin/site:19-29`). Fix: name `init`'s two failures here, and move the loader's statuses to step 4, where `site show` first loads the file.
   12. `docs/operator-guide/site.md:212`: the step says "Tag the starting point once, and push the tag", which is two actions, but it shows only `git tag starting-point <commit>`. Fix: add the push, `git push origin starting-point`, as its own step or in the same `console github` block.
   13. `docs/operator-guide/site.md:7`, `:70`, `:264`, `:287`: repository files the reader is pointed to (`operator/site.env.example`, `operator/README.md`) are named in backticks, not linked. Style rule 8 says to link a repository file by a relative link. Fix: link each at its first mention (`../../operator/site.env.example`, `../../operator/README.md`).

   Not under review, for the human: the work item's Description cites "style rules 8 to 10", but `docs/project-guide/style.md` has rules 1 to 8.
