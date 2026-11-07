---
stage: docs-review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 617
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T01:49:13.617905Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T01:39:43.325229Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T01:39:43.332643Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T01:40:00.049524Z'
  stage: intake
  run: 871a78ae3eb145c787aa0f4e5e53a45b
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T01:40:05.386752Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T01:44:13.135549Z'
  stage: docs-only
  run: 3ecbbb4af6f542db914fd938f7fce1d9
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T01:44:18.291999Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T01:45:55.424749Z'
  stage: docs-review
  run: 2df112b203084dc8b6373a0938816181
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T01:46:00.708607Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T01:49:08.700033Z'
  stage: docs-only
  run: 348f3079580a47f2bf5955ced173486b
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T01:49:13.617905Z'
  stage: docs-review
---

# The operator guide's the records, the bill and the watch reads for the operator

## Description

`docs/operator-guide/records.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/records.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/records.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/records.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/records.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/records.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only: `docs/operator-guide/records.md` (exists; covers the records contract, `factory-bill`, `factory-watch`), `docs/checked-documents.txt` (does not list it yet), link fixes. No code, tests or agent files.
   - Criteria: each is checkable by the reviewer or a command: style compliance (judged), old-versus-new fact comparison (judged), file on the checked list plus `make documents` printing `documents ok`, no dead links, `make check` green. No Interface rule states a limit, default or error, so no failing side is owed.
   - Smoke test: `grep -cx "docs/operator-guide/records.md" docs/checked-documents.txt` is runnable and `Expect: 1` is checkable. It prints 0 now and 1 after the story.
   - Docs criterion: criterion 6 says "as criteria 1 to 4", which name what the reader must know only by reference to style and facts, but it dictates no sentences. I accepted it, since it is the same shape across this feature.
   - Architecture: every path the Interface changes is one the documenter may write (`docs/*`), so the docs route applies. No `factory/` change.
   - Scope: within F0054's scope (one file, one story, S0009) and outside its out-of-scope list (`decisions.md` is untouched).
4. factory: started docs-only as vm.
5. documenter: Changed files:
   - `docs/operator-guide/records.md`: restructured, not rewritten from scratch.
     - Added an introduction that says what the page is for, with a list of its sections.
     - Linked the factory's own words to the glossary at their first use: work item, cost record, stop, pipeline definition, tick, instance, claim, lease.
     - Made the contract command a `console` example that shows its output (`contract: 5 schemas written`). The usage and exit-2 case stays in prose. I added a `console` example for `factory-bill not-an-id` (exit 2).
     - Marked the two `uv run factory-bill` lines as an `sh` block, since they need a project checkout.
     - Moved three sections of exact detail into a new *Reference* at the end: the refused tool calls (`denials`, `denied_paths`, `login`), the machine measures and the tool calls on the cost record. Their text is unchanged. Headings are now "Cost record: refused tool calls in the sidecar", "Cost record: the machine" and "Cost record: the tool calls". No other file links to the old headings (grepped).
     - Dropped the version-by-version history of the records contract (1.1 to 4.4) on purpose, per style rule 1. The current version `4.4` and the rule for major and minor bumps stay. The text points to `docs/decisions.md` for what each version changed.
   - `docs/checked-documents.txt`: added `docs/operator-guide/records.md`.

   Checked: `make documents` printed `documents ok (13.3 s)` with the file on the checked list, so its names, its settings and the `console` examples pass. `make check` was not run, because every changed file is a document.

   Not done:
   - I could not run the other commands by hand. Bash denied my compound command, and `factory-watch` and `factory-bill` need a remote.
   - The `factory-bill` and `factory-watch` prose is unchanged. I did not re-read it line by line against the code this round, so the reviewer should compare it against `src/factory/entry/` and the project-guide `watching.md`.
   - The `factory-bill` usage-error sentence is still a sentence. Only the not-an-id case is a runnable example.

   Cross-read and found current: `docs/operator-guide/README.md` line 15, the two links in `work-items.md` ("The cost table" heading is unchanged), and the references in `docs/project-guide/watching.md`.

   Stale text not touched: `docs/decisions.md:1560` still lists `records.md` among ten topic files. That is history and not mine to fix. `make documents` prints "does not exist" notes for `docs/project-guide/README.md` and others, which this story does not touch.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (13.6 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md`, which touches two files: `docs/operator-guide/records.md` and `docs/checked-documents.txt`. I read the diff against `docs/project-guide/style.md` and against the code: `src/factory/entry/contract.py`, `bill.py`, `watch.py`, `src/factory/pipeline/domain/stops.py` and `docs/decisions.md`. Criterion 3 is met: the file is on the checked list, and the journal shows `documents ok`. Criterion 4 is met: no other file linked to the three renamed headings. Criteria 1 and 2 are not met.

   Findings:
   1. `docs/operator-guide/records.md:5`: "a record of each stop" is false. `StopRecord` in `src/factory/pipeline/domain/stops.py:67` records only stops of the repository or the machine. A work item's stop is posted on its pull request (glossary, *stop*). Fix: say "a record of each stop of the repository or the machine".
   2. `docs/operator-guide/records.md:40`: "What each version changed is in the decision log" is not true. `docs/decisions.md` names 1.1, 2.0, 3.0, 4.0 and 4.2 to 4.4. It has nothing for 1.2 (`provider_limit`), 1.3 (`not_read`) or 4.1 (`stage_image_failed`). Fix: narrow the pointer to what the log holds, for example "why the contract changed is in the decision log". Dropped on purpose, per style rule 1: the version-by-version list of the old line 30, which is no longer in any document for 1.2, 1.3 and 4.1.
   3. `docs/operator-guide/records.md:27-32`: the old command `uv run python -m factory.entry.contract [<folder>]` lost its no-folder form. The prose says "regenerate", but the example only writes into `$PWD/schemas`. Nothing says where the command writes when no folder is given: `CONTRACT_FOLDER`, the package's `contract/` folder, in `contract.py:9`. Fix: add one sentence saying the command without a folder rewrites `src/factory/contract/` when run as `uv run python -m factory.entry.contract` from a checkout.
   4. `docs/operator-guide/records.md:48-51`: the `sh` block `uv run factory-bill F0001-S0001` / `uv run factory-bill` is neither a runnable example nor marked `vm`/`github`/`model`, which the Description requires. Style limits `sh` to commands that act on a real machine or cloud account. Fix: make it a `console github` block (it reads a remote's work item branches), with output copied from a real run and named, or a `console vm` block that names the run.
   5. `docs/operator-guide/records.md:46-55`: reading a bill is a task (fetch, then run `factory-bill`), but it is written as prose: "Run it from a checkout…", then "run `git fetch` first" two paragraphs later. Fix: numbered steps (1. `git fetch`, 2. `uv run factory-bill <id>`), each one action with its command.
   6. `docs/operator-guide/records.md` (criterion 1, style rule 3): several glossary words are not linked at their first use. These are story (line 18), acceptance (line 18), journal (line 23), stage (line 36), approval (line 38), feature and backlog (line 128), round cap (`round_cap`, line 102) and crash (line 130). Fix: link each to `../project-guide/glossary.md` at its first use.
   7. `docs/operator-guide/records.md:36,139` (style rule 3): "sidecar" is a private word that is not in the glossary. Fix: say "the cost file `<work item>.costs.jsonl`".
   8. `docs/operator-guide/records.md:131` (style rule 3 and "Name no module or class"): "builds its boundaries the same way" names the `Boundaries` class. Fix: say it uses the same settings as `factory-run`, without "boundaries".
   9. `docs/operator-guide/records.md:129` (style rule 3): "merged and not yet booked" uses a private word. Fix: say what the factory has not yet done, for example "merged, with the merge not yet recorded".
   10. `docs/operator-guide/records.md:135,137,141,170` (style rule 3): "the Factory Timeline" is named three times and never explained. Fix: say once what it is, for example "a page that shows a factory's records from GitHub" as on line 14, or drop the name.
   11. `docs/operator-guide/records.md:139,184` (style rules 1 and 7): "an older line has none of the three" and "(or the record is older than contract 4.4)" are version history. Fix: remove both phrases.
   12. `docs/operator-guide/records.md:128,129,130,131,139` (style rule 2): sentences run to 40–90 words and carry up to four parentheses. Line 129's first sentence has four. Line 131 is one bullet of three sentences with nested clauses. Fix: split them into sentences of about 25 words, one parenthesis at most each. Line 131 could become a table of exit status and meaning, like the one for `factory-bill` on lines 57-61.

   Open, not mine to fix: the documenter did not check the unchanged `factory-watch` prose line by line. I spot-checked its exit statuses, the `factory-watch: <fault>` and `settings invalid` messages, `is held by` and the `origin/main` git error against `src/factory/entry/watch.py` and `src/factory/pipeline/domain/evaluation.py:225`; they match.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's twelve findings in `docs/operator-guide/records.md`. This is the only file I changed. `make documents` printed `documents ok (13.3 s)`. I did not run `make check`, because I changed only a document.

   1. The introduction now says "a record of each stop of the repository or the machine".
   2. The version pointer now reads "Why the contract changed is in the decision log". The log does not cover versions 1.2, 1.3 and 4.1, and the version-by-version list stays dropped on purpose (style rule 1).
   3. The contract command now says that, run from a checkout without a folder, it rewrites `src/factory/contract/`. I took this from `CONTRACT_FOLDER` in `contract.py`.
   4. and 5. Reading a bill is now two numbered steps: `git fetch`, then `factory-bill`. The two commands stay in an `sh` block. I used `sh` rather than `console github` because I cannot run `factory-bill` against a remote, and I will not write an output I did not see. The text above the block says it reads your project's remote.
   6. I linked these glossary words at their first use: story, journal, stage, approval, feature, acceptance, round cap and crash. Backlog is still not linked, because it only appears in code spans such as `backlog`.
   7. "Sidecar" is gone, replaced by "cost file". I also renamed the heading "Cost record: refused tool calls in the sidecar" to "Cost record: refused tool calls". Nothing links to it; I grepped in round 0.
   8. "Builds its boundaries the same way" now reads "uses the same settings".
   9. "Merged and not yet booked" now reads "merged with the merge not yet recorded".
   10. The Factory Timeline is now named once, in the section on the records contract, as an example of a page that shows a factory's records from GitHub. The other mentions are gone.
   11. I removed "an older line has none of the three" and "(or the record is older than contract 4.4)".
   12. I split the long `factory-watch` bullets: the claim and lease bullet, the work item row bullet and the exit status bullet. The exit statuses are now a table, and the settings sentence is a separate bullet. The wording is the old wording.

   Cross-read and found current: `docs/operator-guide/README.md`, the links in `work-items.md`, `install.md` and `pipeline.md` that `records.md` points to, and `docs/project-guide/watching.md`.

   Stale text I saw and left alone:
   - `docs/decisions.md:1560` still lists `records.md` among ten topic files, which is history.
   - `make documents` prints "does not exist" notes for `docs/project-guide/work.md` ("factory/agents") and other paths. They are not part of this story.

   `check`: check: green
   `secrets`: secrets: green (0.3 s)
   `documents`: documents ok (13.5 s)
10. factory: started docs-review as vm.
