---
stage: docs-only
blocked: null
round: 3
attempts: 0
crashes: 0
pull_request: 617
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T01:55:18.375060Z'
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
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T01:50:45.105247Z'
  stage: docs-review
  run: 6447226898b74d798e48f1bf81bf2623
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T01:50:50.324621Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T01:53:49.736818Z'
  stage: docs-only
  run: 74c1af9baf704ce9b5602bc535b645b2
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T01:53:54.631694Z'
  stage: docs-review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T01:55:13.055844Z'
  stage: docs-review
  run: 11d19d0c3dfb45c889ee8508c0541359
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T01:55:18.375060Z'
  stage: docs-only
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
11. reviewer: Round 1 review of `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/operator-guide/records.md` and `docs/checked-documents.txt`. I read the new file against `docs/project-guide/style.md` and against `src/factory/entry/bill.py`, `contract.py`, `watch.py` and `src/factory/watching/application/costs.py` (`in_flight`).

    What is fixed from round 0:
    - Findings 1 to 3 and 6 to 11 are fixed.
    - Finding 5 is fixed: the bill is now two numbered steps.

    What is met:
    - Criterion 3: the file is on the checked list, and the journal shows `documents ok`.
    - Criterion 4: no link points to the renamed headings.
    - Criterion 2: the only thing dropped on purpose is the version-by-version list of the records contract (style rule 1), as named in round 0.

    Round-0 finding 4 is still open, and finding 12 is only partly fixed.

    Findings:
    1. `docs/operator-guide/records.md:49-54`: the text says "It reads your project's remote, so no run can be shown here", which is false. `factory-bill` reads only the checkout's remote-tracking refs (`BillService._ref_of`, `in_flight` in `costs.py`). I ran `uv run factory-bill <id>` in this stage's own checkout, and it printed a full table and `Cost:` line. So the `sh` block does not fit the style's rule for `sh`, which covers only commands where no run can be copied. The block also stands at column 0 after the list, not under step 2. Fix: remove the false sentence. Make the block a `console vm` block with output copied from a real run, indented under step 2, and have the text above it name where it ran.
    2. `docs/operator-guide/records.md:132` (style rule 2): "Each row has these columns: …" is about 45 words long and has three parentheses. Fix: a table with the columns column and meaning, with one row each for the title, `stage`, `blocked`, `claim`, `running_since` and `pull_request`.
    3. `docs/operator-guide/records.md:131` (style rule 2): the first sentence is about 38 words. The `acceptance` sentence is about 40 words, and its one parenthesis holds both a list of six values and a link. Fix: split each into sentences of about 25 words. Put the status values in their own sentence and the link in another.
    4. `docs/operator-guide/records.md:133`: "A claim of the instance `factory-watch` runs as shows in one of two ways." does not parse. Fix: "The claim of the instance that `factory-watch` runs as shows in one of two ways."
    5. `docs/operator-guide/records.md:117` (style rule 2): "It evaluates once, as a tick would after its fetch, except that … since a tick never looks while its own stage runs." is about 33 words long. Fix: two sentences: "It evaluates once, as a tick would after its fetch. It judges its own instance's claim by the lease, because a tick never looks while its own stage runs."
    6. `docs/operator-guide/records.md:135` (style rule 3): "provider limit" is a private word that is not in the glossary and is not explained. Fix: say it in plain words, for example "a usage limit of the model's provider", or link the page of the operator guide that explains it.
    7. `docs/operator-guide/records.md:36` (style rule 3): "moved to `done/` by the archive commit" uses a private word without explaining it. Fix: "moved to `done/` by the commit the factory makes after the merge".
    8. `docs/operator-guide/records.md:27`: "Run as `uv run python -m factory.entry.contract` from a checkout, without a folder, it rewrites `src/factory/contract/`, …" is a dangling sentence with two stacked conditions. The code it describes is `CONTRACT_FOLDER` in `contract.py:9`. Fix: "Without a folder, the command rewrites `src/factory/contract/`, where the committed schemas are; run it as `uv run python -m factory.entry.contract` from a checkout."
12. factory: started docs-only as vm.
13. documenter: Round 2: I fixed the reviewer's eight findings in `docs/operator-guide/records.md`, the only file I changed. `make documents` printed `documents ok (13.7 s)`, and the new block is listed as `records.md:53: not run (vm)`. I did not run `make check`, because I changed only a document.

    1. The `sh` block is now a `console vm` block, indented under step 2. I removed the false sentence. The text names where the run took place: the factory's VM, in this work item's own checkout, after a fetch. The output is copied from my real run of `uv run factory-bill F0054-S0009`, and the text says the numbers change with every run. The run's output also had an empty line before `Cost:`, which I kept.
    2. The row columns of the work item board are now a table (column, meaning).
    3. I split the feature row sentence into three. I put the `acceptance` status values in their own sentence and the link to `work-items.md` in another.
    4. The claim bullet now begins "The claim of the instance that `factory-watch` runs as".
    5. The `factory-watch` introduction is now two sentences.
    6. "Provider limit" is now "the model provider's usage limit".
    7. "Archive commit" is now "the commit the factory makes after the merge".
    8. The contract command sentence now reads "Without a folder, the command rewrites `src/factory/contract/`, where the committed schemas are; run it as `uv run python -m factory.entry.contract` from a checkout."

    Cross-read and found current: the `factory-bill` exit table against my run, and the `factory-watch` links to `work-items.md` and the glossary.

    Stale text I saw and did not touch: `docs/decisions.md:1560` still lists `records.md` among ten topic files, which is history. `make documents` prints "does not exist" notes for paths in other documents, which this story does not touch.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (13.4 s)
14. factory: started docs-review as vm.
15. reviewer: Round 2 review of `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/operator-guide/records.md` and `docs/checked-documents.txt`. I read the new file against `docs/project-guide/style.md` and against `src/factory/entry/bill.py`, `src/factory/entry/watch.py` and `src/factory/shared/domain/errors.py`. I also compared it with the old text on `main`.

    What is fixed from round 1:
    - Findings 2 to 8 are fixed.
    - Finding 1 is fixed in its form. The block is a `console vm` block, indented under step 2. The false sentence is gone, and the output format matches `_block` in `bill.py`: the table, an empty line, then `Cost: <line>`.

    What is met:
    - Criterion 3: the file is on the checked list, and the journal shows `documents ok`.
    - Criterion 4: no link points to a renamed heading.
    - The `factory-bill` exit table matches `bill.py`: 0, 1 for `no work item <id>`, and 2 for `not a work item id` and for the usage line.

    Findings:
    1. `docs/operator-guide/records.md:162` (criterion 2: a claim the code contradicts): the row for exit 2 puts "an unknown option" together with the settings faults. It says standard error then gets `factory-watch: settings invalid: <variable>: <fault>`. For an unknown option the code does something else. `argparse` in `watch.py` (`parser.parse_args`) exits 2 with its own `usage: factory-watch [-h]` and `factory-watch: error: unrecognized arguments: <option>`. The old text on `main` (line 166) kept the two cases apart, and the table merged them. Fix: give the unknown option its own sentence or row, "2: an unknown option; standard error gets the usage line and `factory-watch: error: unrecognized arguments: <option>`". Keep the `settings invalid` sentence for the environment and the token file only.
    2. `docs/operator-guide/records.md:51` (style: "the text above it says where it ran"): "in the checkout of this work item" means nothing to the operator. "This work item" is the story that wrote the page, and the reader cannot tell which work item or repository it is. Fix: name the run itself, for example "This run took place on the factory's VM, in a checkout of the factory's own repository, after `git fetch`, for one of its work items. Its numbers change with every run."
    3. `docs/operator-guide/records.md:5,155,174,217` (style rule 2: about 25 words per sentence): four sentences are still too long.
       - Line 5, sentence 2, about 37 words: "This page tells you which records … with `factory-watch`." Fix: list the three topics as their own short sentence, or rely on the list of sections below it.
       - Line 155, sentence 2, about 39 words, "A stage that waits for the model provider's usage limit … tells the two apart." Fix: put the clause after the semicolon in its own sentence.
       - Line 174, sentence 1, about 44 words, which lists `denials` and `denied_paths` in one sentence. Fix: one sentence for each key. Also drop the last sentence, "`factory-bill` does not print these keys.", which repeats line 170.
       - Line 217, the `seconds` cell, whose first sentence is about 50 words. Fix: split the Claude Code rule, the lines that are not read and the duplicate-id rule into three sentences.
       I should have named these sentences in round 0, since they stood there unchanged.

    Dropped on purpose (criterion 2), unchanged since round 0: the version-by-version list of the records contract (style rule 1).

    Open, not mine to fix: `docs/decisions.md:1560` still lists `records.md` among ten topic files, as the documenter noted. The round cap of `docs-review` is 3, so one more round remains.
16. factory: started docs-only as vm.
