---
stage: docs-review
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 615
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-07T01:18:23.283600Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T01:01:31.999464Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T01:01:32.006481Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T01:01:46.356028Z'
  stage: intake
  run: b042b84a37d0422eba00902f2941d37f
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T01:01:51.170541Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T01:07:17.199797Z'
  stage: docs-only
  run: 1598991e93134c2cac63d9b5a3a148bf
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T01:07:22.774460Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T01:10:03.912055Z'
  stage: docs-review
  run: 0e21600d445b4e71b21834f4857cdafd
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T01:10:08.841954Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T01:13:49.462281Z'
  stage: docs-only
  run: 62daa489044d4a4eb60665b44af9ad89
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T01:13:54.617208Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T01:15:19.954591Z'
  stage: docs-review
  run: 197b6e36946d4f3b99cb92a35ea7bf7c
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T01:15:24.966962Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T01:18:18.022203Z'
  stage: docs-only
  run: ec2ed89b54804fe9ae213a41d8a44518
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T01:18:23.283600Z'
  stage: docs-review
---

# The operator guide's the stops reads for the operator

## Description

`docs/operator-guide/stops.md` is rewritten for its reader, an operator who runs an instance, knows Linux and does not read the code, in the style of `docs/project-guide/style.md` (numbered steps for tasks; each stop as what you see, what it means, what you do; settings as tables of name, what it does, default and example). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/operator-guide/stops.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- `docs/checked-documents.txt`: one line, `docs/operator-guide/stops.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/operator-guide/stops.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/operator-guide/stops.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
5. `make check` stays green.
6. docs: as criteria 1 to 4. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/operator-guide/stops.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths (`docs/operator-guide/stops.md`, `docs/checked-documents.txt`); it changes only documents the documenter may write, with no code, test or agent file.
   Criteria: criteria 1 to 4 are checkable against the files (style rules and the old-versus-new comparison by the reviewer, `make documents` printing `documents ok`, links resolving). The Interface states no behaviour or rule beyond the document list, so no failing side is missing.
   Smoke test: `grep -cx "docs/operator-guide/stops.md" docs/checked-documents.txt` is runnable, and its `Expect: 1` can be checked against the output. It runs no pytest.
   Docs criterion: criterion 6 says "as criteria 1 to 4", so it names what the reader must know (the stops, from the code) and dictates no sentences.
   Architecture: documents only; it matches the docs route and the CLAUDE.md docs split.
   Scope: it is one of the 22 per-file stories of F0054 (S0007), and `decisions.md` is untouched, which is outside the Out of scope list.
4. factory: started docs-only as vm.
5. documenter: Changed files:
   - `docs/operator-guide/stops.md`: rewritten for the operator. Each stop section now reads as what you see, what it means, what you do. Numbered steps are used for tasks, and the end of the file has a *Reference* section.
   - `docs/checked-documents.txt`: added the line `docs/operator-guide/stops.md`.

   The Interface requires the headings that other files link to, so I kept them: "The stops" (the document check requires it), "The stop records on main", "A stall: the stall note", "The factory's own questions", "An event that keeps failing", "The stop `pipeline_definition_invalid`", "The stops of the tick" and "Stops that cannot be done". The stop table keeps every `STOP_TABLE` id in backticks, with its destination.

   Code checked and corrections made:
   - The old text said the stall causes are "the ten listed below". `_STALL_SENTENCES` in `src/factory/hosting/domain/post_texts.py` has nine, and the old list also had nine. The new text says nine, with a table of them in *Reference*.
   - I took the cause wording from `post_texts.py`: "the agent run reached its time limit" and "merging the main branch conflicts and the merge was aborted".
   - I read nothing else in the code. The other claims were carried over from the old file unchanged.

   Moved to *Reference*:
   - the nine stall causes;
   - the rules that shape a failed push's reason;
   - the wording of a probe of `main` that fails without printing anything.

   Removed on purpose:
   - The paragraph on the 2026-11-04 outage, with its date and its link to `planning/outage-2026-11-04.md`. Style rule 7 forbids history, and `planning/` is the human's. The behaviour it described is kept under "During an outage of the hosting service". I dropped "now", "as before" and "Only the line is new", and I did not add a pointer to the decision log, because I found no entry that names this outage.
   - Example ids such as `F0001-S0001`, replaced by `<id>` placeholders (rule 1).

   Other changes:
   - I wrote `<project>/factory/stage.Containerfile`, because `make documents` flagged the bare path as missing in this repository. This is the placeholder prefix the style page requires for a path in the project the factory runs on.
   - I split the old "The stops of the tick" prose into the subsections `fetch_failed`, `checkout_restore_failed`, "A work item file that cannot be read", "The low disk" and "The preflight in the tick".
   - I added a link from the first use of each factory word to the glossary: stop, tick, work item, journal, claim, role, approval, take, write paths, stall, crash, pipeline definition, rounds and instance.

   The file has no `console` blocks. Its blocks are factory log lines, comment texts and a table, all `text`, so none is run.

   `make documents` ends `documents ok (11.6 s)`. I did not run `make check`, because I changed only documents.

   Cross-read against the file: the links into `stops.md` from `health.md`, `pipeline.md`, `agent-runtime.md`, `work-items.md`, `install.md`, `machine.md`, `site.md`, `README.md` and the project guide. Every heading they cite still exists. I did not read the cited files in full.

   Stale text I noticed and did not touch:
   - `docs/project-guide/shared.md:99` and `docs/project-guide/README.md:20` refer to the section *The stops* by name. That is still correct.
   - `docs/decisions.md:1560` mentions *Replaced in v1.2* in the operator guide index. That is unrelated to this story.

   Findings for the coder: none.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (12.1 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md` (`docs/operator-guide/stops.md`, `docs/checked-documents.txt`) against the work item, the old file on `main`, `docs/project-guide/style.md` and the code. I checked these against the code and found them right: the `STOP_TABLE` ids and destinations, the nine stall sentences, the texts of the stall note, the error report, the draft pull request description, the round-cap and findings questions, the "cannot handle" reasons, the push retry waits (5/15/45 s) and their log line, `push_reason`'s rules, the handler-error line (cap 3, 300 characters), PyGithub's retry (5, factor 2), the ten-minute machine stop, the pipeline-definition fault texts and the project agent's detail. Every heading that other files link to is kept (criterion 4). The checked-documents line is present (criterion 3). The documenter dropped the outage paragraph and the example ids on purpose and named both, which is right under style rules 1 and 7.

   Findings:
   1. `docs/operator-guide/stops.md:176`: the attempts-cap example reads `The last time: the agent gave no result`. That is none of the nine causes. `pipeline/application/handlers/questions.py:57` inserts the latest stall entry's text, which `pipeline/application/stalls.py:136` writes as `Stage <stage> stalled (attempt <n> of <cap>): <cause>`. Fix: show `The last time: Stage doing stalled (attempt 2 of 2): the agent gave no valid decision and entry`.
   2. `docs/operator-guide/stops.md:171`: the crash-cap row says "`factory: ` and the text below", but only the attempts-cap text follows. The crash-cap question (`crash_cap_question`, `src/factory/hosting/domain/post_texts.py:115`) is shown under "The crash cap" in `docs/operator-guide/work-items.md:234`. Fix: point the row to that section, or quote the text below.
   3. `docs/operator-guide/stops.md:39`: the example detail `origin unreachable` is not a git message, and line 269 says the detail of `fetch_failed` is git's message. Fix: use a real git message, such as the `fatal: unable to access ...: Could not resolve host: github.com` that line 342 uses.
   4. `docs/operator-guide/stops.md:312` (criterion 2): the old file's list of registered handlers is in neither the new text nor *Reference* (`comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate`, `pull_request_lookup`, `crash`, `expired`, `acceptance_due`). So is its link to "An expired lease" in `work-items.md` (old line 241). The old stall note sentence "the take does not bring it from the dataset" (old line 97) is also gone. Journal entry 5 does not name any of these as dropped on purpose. Fix: move them into *Reference*, or name them in the entry as dropped on purpose.
   5. `docs/operator-guide/stops.md:32` and `:361`: style.md's operator guide rule says "Name no module or class". Line 32 names `STOP_TABLE` in `factory.pipeline.domain.stop_table`. Line 361 says "the factory raises `CannotHandle`". Fix: drop line 32's sentence about the source, or keep only the rule about underscores. At line 361, describe what the operator sees (the report's `cannot handle ...` error).
   6. `docs/operator-guide/stops.md` (criterion 1, glossary links at first use): "stall" is first used at line 5 but linked only at 119, "pipeline definition" at line 19 but linked at 123, and "round" at line 30/143 but linked at 186. The glossary words "stage" (line 5), "story" and "backlog" (line 9), "attempts cap" (line 124) and "round cap" (line 164) are never linked. Fix: link each at its first use.
   7. `docs/operator-guide/stops.md:79,87,124,150,160,173,312,361` (style rule 3, no private words): "the dispatcher", "the evaluation" and "the `ask` handler" are internal names that are not in the glossary, and the operator does not read the code. Fix: say what the factory does ("the factory counts the error", "the factory asks"), or explain each once.
   8. `docs/operator-guide/stops.md:53,97,119,160,245,287,361` (style rule 2): these sentences run well past 25 words, and lines 53 and 245 hold two parentheses each. Fix: split them, one idea and at most one parenthesis per sentence.
   9. `docs/operator-guide/stops.md:300` ("The preflight in the tick") and `:359` ("Stops that cannot be done"): these describe stops without the three parts that style.md asks of every stop (what you see, what it means, what you do). Fix: give each the **You see** / **It means** / **You do** form, as the other stop sections have.
   10. Work item journal entry 5: the documenter says "I read nothing else in the code. The other claims were carried over from the old file unchanged." The Description says the facts come from the code, not from the old text. Findings 1 to 3 are carried-over claims that the code contradicts. Fix: check the remaining carried-over claims against the code and name the ones checked.
8. factory: started docs-only as vm.
9. documenter: Round 1: fixed the reviewer's ten findings, each in `docs/operator-guide/stops.md`. That is the only file I changed. `docs/checked-documents.txt` already has its line. `make documents` ends `documents ok (11.7 s)`. I did not run `make check`, because I changed only documents.

   1. Attempts-cap example: now reads `The last time: Stage doing stalled (attempt 2 of 2): the agent gave no valid decision and entry`. I checked it against `stalls.py` and `questions.py`.
   2. Crash-cap row: it now points to "The crash cap" in `work-items.md`, which quotes the question (`crash_cap_question`).
   3. Example detail for `fetch_failed`: now a real git message, `fatal: unable to access ...: Could not resolve host: github.com`.
   4. Criterion 2:
      - Added a Reference section, "The events the factory handles". It lists every event kind (`comment`, `ask`, `merged`, `closed`, `reject`, `hand_over`, `duplicate`, `pull_request_lookup`, `crash`, `expired`, `acceptance_due`) and links to "A restart during a stage" and "An expired lease" in `work-items.md`.
      - Restored the old stall sentence as "The take does not copy the rest from the dataset."
   5. Module and class names: removed `STOP_TABLE` with its module path. The "cannot be done" section no longer says `CannotHandle`; it says the report's last error starts with `cannot handle`.
   6. Glossary links: now at the first use of stall, stage, backlog, story, pipeline definition, `round`, attempts cap and round cap. I took the duplicate links out of later places.
   7. Private words: "dispatcher", "evaluation" and "`ask` handler" are replaced by what the factory does. For example, "the factory counts what goes wrong with each event" and "the factory has asked".
   8. Long sentences: split the ones at the old lines 53, 97, 119, 160, 245, 287 and 361. Each now has one idea and at most one parenthesis.
   9. "The preflight in the tick" and "Stops that cannot be done" now have **You see** / **It means** / **You do**.
   10. Carried-over claims: I checked these against the code this round.
      - The stall note format and its two follow-up texts (`stall_note` in `post_texts.py`), and the attempts-cap and crash-cap questions.
      - The `stall` entry text (`stalls.py`).
      - The `no detail given` constant, `stop cleared <reason>` and the `stops recorded` commit subject.
      - The reviewer had already confirmed the rest.
      I did not re-check claims such as the exact line counts of a stall's output block. Those stay as the reviewer found them right.

   Cross-read: the headings that other files link to are unchanged, and `make documents` resolves the names.

   Stale text I saw and did not touch: `docs/operator-guide/work-items.md:232` cites "An expired lease" without a link, which is fine. The earlier note about `docs/decisions.md:1560` still stands, unrelated.

   No findings for the coder.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (12.0 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 review. I read `git diff main...HEAD -- README.md docs operator/README.md` (`docs/operator-guide/stops.md` and `docs/checked-documents.txt`), the work item, `docs/project-guide/style.md` and the glossary. I checked the round-0 fixes against the code.

    The ten round-0 findings are fixed, and the code bears them out:
    - Line 176 matches `attempts_cap_question` (`src/factory/hosting/domain/post_texts.py:104`) and the stall text.
    - Line 171 points to "The crash cap" (`work-items.md:234`).
    - Line 39 uses a real git message.
    - The events list at line 410 matches `EventKind` (`src/factory/pipeline/domain/events.py:12`), with `run` covered as "the events of a stage run".
    - `STOP_TABLE` and `CannotHandle` are gone.
    - "dispatcher", "evaluation" and "`ask` handler" are gone.
    - "The preflight in the tick" and "Stops that cannot be done" now have **You see** / **It means** / **You do**.

    Every heading that other files cite exists: `work-items.md` (217, 234, 249, 140, 88), `health.md`, `install.md`, `machine.md` and `agent-runtime.md`. The `checked-documents.txt` line is there.

    Named as dropped on purpose under criterion 2, as a result of round-0 finding 7: the old line 109 "the evaluation makes the event `ask` with the detail `attempts cap`" and the old line 239 "The tick calls the dispatcher once per pass". Both are internal wording, and the new text says what the factory does. No finding.

    Findings:
    1. `docs/operator-guide/stops.md:119`: "dataset" is a glossary word and appears here for the first time without a link (style rule 3). It came in with the restored sentence "The take does not copy the rest from the dataset." Fix: link it to `../project-guide/glossary.md`, or say "from the agent's copy of the repository".
    2. `docs/operator-guide/stops.md:293`: one sentence of about 42 words with two parentheses ("(the checkout's parent)" and "(exactly the minimum is enough)"). This breaks style rule 2. Fix: split it, for example "At the start of every tick, before the fetch, the factory reads the free space of the work directory and of the state directory. The work directory is the checkout's parent. The stop stands when one has less than `FACTORY_MIN_FREE_GB`; exactly the minimum is enough."
    3. `docs/operator-guide/stops.md:132`: the **You see** sentence runs about 42 words and holds a parenthesis (rule 2). Fix: one sentence for the cause and the check's name, one for the code block with the last 15 lines.
    4. `docs/operator-guide/stops.md:325`: the sentence runs about 43 words, with a long parenthesis (rule 2). Fix: give the two causes their own sentence ("The hosting service may be down, or git may fail in the checkout while the report resolves the branch.").
    5. `docs/operator-guide/stops.md:337`: the sentence runs about 40 words, with a parenthesis that lists four items (rule 2). Fix: say first which pushes are tried again, then list the recorded changes in a second sentence.
    6. `docs/operator-guide/stops.md:62,271,283`: each has a sentence of 33 to 35 words (rule 2): "Each tick, right after it restored the checkout ...", "That fetch compares the project's stage file ... and no tick runs in that iteration" and "The restore throws away every uncommitted change ...". Fix: split each into two sentences, one idea each.
    7. `docs/operator-guide/stops.md:88,119,152,205,206`: each has a sentence of about 28 to 33 words (rule 2). They are: "Two files with one id are both read: ...", "Only then does it post the note and write ... label too.", "Every report that ran adds one line ...; the line has the same form ...", "When the diff builds a behaviour ..." and "When a story's Description has gone stale ...". Fix: split each at its semicolon, colon or "and", one idea each.
    8. `docs/operator-guide/stops.md:147-150`: the numbered steps are not one action each, as the operator guide's style asks. Step 1 ("Below the attempts cap, nothing") is a case, not an action. It is also an alternative to steps 2 to 4, not a step before them. Fix: say first, as a sentence, that below the cap there is nothing to do. Then number only the steps at the cap: read the 15 lines and run `make check` on the branch, fix the cause, answer on the pull request.
12. factory: started docs-only as vm.
13. documenter: Round 2: fixed the reviewer's eight findings in `docs/operator-guide/stops.md`, the only file I changed. `docs/checked-documents.txt` already has its line. `make documents` ends `documents ok (11.8 s)`. I changed only documents, so I did not run `make check`.

    1. "dataset" in the stall section is now linked to the glossary.
    2. The disk sentence is split into three: when the factory reads the free space, what the work directory is, and when the stop stands (exactly the minimum is enough). The parentheses are gone.
    3. The red-check **You see** is split into two sentences: the cause and the check's name, then the code block with the last 15 lines.
    4. The sentence about a report that cannot be posted is rewritten: it names the two causes in a sentence of their own, and the retry follows in the next one.
    5. The sentence on retried pushes is split. It first says which pushes are tried again, then lists the recorded changes, then names the two failures that count.
    6. The sentences on the stop records, the stall note's label, the stage-file fetch and the restore are each split into two, one idea each.
    7. The sentences on two files with one id, the report line, the added criterion and the corrected description are split at their semicolon, colon or "and".
    8. The red-check **You do** now says in a sentence that below the attempts cap there is nothing to do. It numbers only the three steps at the cap: read the 15 lines and run `make check` on the branch, fix the cause, answer on the pull request.

    Code claims: this round I rewrote wording only and changed no fact. I checked no claim against the code beyond what rounds 0 and 1 covered.

    Cross-read: no heading that another file links to changed, and `make documents` resolves the names.

    Stale text I noticed and did not touch: `docs/decisions.md:1560` mentions *Replaced in v1.2* in the operator guide index, which this story does not cover.

    No findings for the coder.

    `check`: check: green
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok (12.0 s)
14. factory: started docs-review as vm.
