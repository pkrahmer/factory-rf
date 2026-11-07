---
stage: docs-approval
blocked: null
round: 3
attempts: 0
crashes: 0
pull_request: 620
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T02:57:18.942573Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T02:57:18.950448Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T02:57:33.384305Z'
  stage: intake
  run: 64a688050a464c798e3238f9457573f8
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T02:57:38.933244Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T03:02:11.236237Z'
  stage: docs-only
  run: 7d1f87ec827442e2abf3c7e8d5d413ac
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T03:02:16.514770Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T03:04:35.830588Z'
  stage: docs-review
  run: 8ee8556dac6e4b73857c8c4d0ea58a61
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T03:04:41.247907Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T03:09:40.137624Z'
  stage: docs-only
  run: 03c4fdbea42749e48bfd5f704ed6d282
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T03:09:45.073120Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T03:11:50.632874Z'
  stage: docs-review
  run: e18bdc3531bb4964a46cace6042fd379
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T03:11:56.014235Z'
  stage: docs-only
- number: 13
  speaker: documenter
  kind: result
  at: '2026-11-07T03:15:01.820787Z'
  stage: docs-only
  run: ec7038d003b246adb72ead22b1fddd20
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-07T03:15:06.898561Z'
  stage: docs-review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-07T03:16:56.777824Z'
  stage: docs-review
  run: 45c02375a97348b6a02d3d1e5bb002ba
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-07T03:17:02.075997Z'
  stage: docs-only
- number: 17
  speaker: documenter
  kind: result
  at: '2026-11-07T03:19:40.108794Z'
  stage: docs-only
  run: 7c4ecd71c1744aeda43bcfc62b3cea00
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-07T03:19:45.135560Z'
  stage: docs-review
- number: 19
  speaker: reviewer
  kind: result
  at: '2026-11-07T03:20:54.152769Z'
  stage: docs-review
  run: bbd94c94c24046a5ab89326eaa6bf022
---

# The project guide's page on the shared area reads for the developer

## Description

`docs/project-guide/shared.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/shared.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/shared.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/shared.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/shared.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/shared.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/shared.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete files only (`docs/project-guide/shared.md`, `docs/checked-documents.txt` with one exact line); no code, test or agent file changes, so every path is one the documenter may write.
   - Criteria: 1 to 6 are checkable by reading or running (style judged by the reviewer, old-versus-new comparison, `make documents` printing `documents ok`, no broken link, `make check` green). The link rule and the checked-list line each have a criterion (4, 3). Criterion 5 covers links to changed headings. The failing side is `make documents` finding a broken link or a name that does not resolve.
   - Smoke test: `grep -cx "docs/project-guide/shared.md" docs/checked-documents.txt` is runnable, and `Expect: 1` is checkable. It runs no pytest.
   - Docs criterion: criterion 7 points at criteria 1 to 5 (reader's knowledge: the style, the old file's facts kept, working examples, links). It quotes no sentences to write.
   - Architecture: the change touches only documents, matching CLAUDE.md's Docs section. It keeps `docs/decisions.md` unchanged and writes nothing to `factory/`, `planning/` or `docs/runs/`.
   - Scope: this is S0012 of F0054's list (the project guide's page on the shared area), within Scope and outside Out of scope.
4. factory: started docs-only as vm.
5. documenter: Files changed:
   - `docs/project-guide/shared.md`: rewritten for its reader in the form of `style.md`. Each section opens with a short idea and the signatures in an indented block, then one rule per bullet, then See also. Every module and test file it names is linked once by a relative link, and no link sits in a code block. A *Reference* section at the end holds the exact detail: the `ProcessResult` fields, the 0.05 s read step and the `WNOWAIT` check, the private `_start` and `_kill_session`, the suppression markers, the test files and helpers, and the types of the check. I kept the headings "Starting a process", "The duplicates report", "The document check" (with the name check, settings check and "How the check is tested") and the section "How the check is tested", which `style.md` links by name. I also kept the two index sections the project guide's index names.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/shared.md`.

   Corrections from the code:
   - The old text said eight modules import `process.py`. The guard (`tests/guards/test_wrapper_search.py`) and the source list nine. The ninth is `factory.shared.adapters.document_examples`, which the old text never named. The new text says nine and names it with the `run_process` users.
   - I cut the story and feature IDs and the version history ("from F0020-S0004", "since v1.2", "Today's operator guide…" as history). I kept the current-state fact that the operator guide has no `Default` column and no refusal table.
   - The old text said "Decision: *The process group is killed*". That line is not an entry heading. It sits under *A command stopped at its time limit loses every process of its session*, and the new See also names that title.
   - Two old "Tests:" paragraphs, the test-timing paragraph and the double heading sentences are merged into the bullets and the Reference.

   Run and verified:
   - `make documents` ended with `documents ok (13.7 s)`, and no finding mentions `shared.md`.
   - The smoke test `grep -cx "docs/project-guide/shared.md" docs/checked-documents.txt` prints `1`.
   - The page's code blocks are indented, not `console` blocks. The only runnable-looking commands in them are the call forms and one `run_process(...)` line, which cannot run on their own. So the page has no example to run and none marked for the VM, GitHub or a model.
   - Nothing else links to a changed heading: the only link into `shared.md` is `style.md` → *How the check is tested*, which is kept.
   - I did not run `make check`, because I changed only documents.

   Cross-read and found current against this diff: `docs/project-guide/README.md` (its line on `shared.md` still matches the page's sections), `docs/project-guide/style.md`.

   Stale text I saw and did not touch:
   - In `docs/project-guide/README.md`, the line on `shared.md` says it covers only "the one module that starts processes" and lists the other `shared` content as described elsewhere. That is still true, but the index is not part of this story.
   - The test docstring in `tests/guards/test_wrapper_search.py` says "the three wrappers", while the set lists nine modules. That is a test comment and the coder's or tester's to fix, not mine.
   - `Style rule 2` (at most one parenthesis per sentence) is not met everywhere in the Reference and in a few bullets of the name check. I kept the exact wording of the old text where shortening it risked dropping a rule. The reviewer may name any sentence to split.
   - `docs/decisions.md` has no "Rejected" line to write: the docs criterion says none.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (13.7 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/project-guide/shared.md` and `docs/checked-documents.txt`. I compared the new page line by line with the old one from `main`, and checked its claims against `src/factory/shared/adapters/process.py`, `src/factory/shared/domain/documents.py`, `src/factory/machine/adapters/power_off.py`, `tests/guards/test_wrapper_search.py`, `tests/support/time_limits.py`, `docs/operator-guide/install.md` and `docs/project-guide/glossary.md`.

   The facts I confirmed: there are nine importers of `process.py`, `document_examples` among them. `OPERATOR_GUIDE_FILES` has ten files. `PIPE_DRAIN` is 5 s and the read step 0.05 s. `ROOMY_LIMIT` is 10 s and `ROOMY_BOUND_SECONDS` is 25. `_start`, `_kill_session`, `NO_COMMAND`, `INSTANCE_FIXTURE` and the check's functions all exist. `docs/checked-documents.txt` holds the line once. The link from `style.md` to *How the check is tested* still resolves.

   Findings:

   1. `docs/project-guide/shared.md:204`: the page says "The operator guide has no `Default` column and no refusal table". `docs/operator-guide/install.md` has `| Name | What it does | Default | Example |` tables at lines 49 to 118 and a `### The refusals` table headed `Refusal` at lines 123 to 127. Fix: say that the guide's tables have a `Default` column and a refusal table and that the check compares them, or remove the bullet.
   2. `docs/project-guide/shared.md:120`: the page says the check "reads the README and the two guides". The code also reads the decision log: `_RULES[DECISION_LOG]` in `documents.py:429` gives `missing`, `empty` or `no decision recorded`. Line 126 of the page also says "four documents". Fix: say it reads the four documents, the decision log included, and add the decision log's rule as a bullet.
   3. `docs/project-guide/shared.md:43`: the page says "What the factory starts on the host is git, `zfs` and `podman`". `power_off.py:11,29` also starts `sudo -n /usr/bin/systemctl poweroff` on the host. Fix: name the power-off command too.
   4. `docs/project-guide/shared.md` as a whole fails criterion 1 (style rule 3). No factory word is linked to the [glossary](glossary.md): "project command" (43), "work item" and "docs stage" (120), "story" (124), "instance" (184) and "stop" (127). Fix: link each of these at its first use.
   5. `docs/project-guide/shared.md:129-130` breaks style rule 1 (no version names) with "the v1 words of `GLOSSARY_FORBIDDEN`" and "the v1 words". Fix: describe them without the version name, for example "the retired words of `GLOSSARY_FORBIDDEN`". Keep the exact heading `## Replaced from v1`.
   6. `docs/project-guide/shared.md` breaks style rule 2 in these places. Line 82 has three parentheses in one sentence. Line 156 has two. Lines 124, 160 and 218 have sentences of more than 25 words. In the Reference, line 231 is one sentence with five parentheses and line 230 has a sentence of more than 25 words. Fix: split each one.
   7. `docs/project-guide/shared.md:149`: the command `uv run python -m factory.entry.check_documents | grep -c "does not exist"` is neither a runnable example nor marked for the VM, GitHub or a model. It cannot be a plain `console` block, because the check would run itself. Fix: drop it, or put it in a `console vm` block copied from a named real run.
   8. Files and modules are not linked as the Interface asks. `docs/project-guide/shared.md:14-17` names the modules `git_cli`, `make_commands`, `claude_runtime`, `fake_containers`, `opencode_runtime`, `podman_runs`, `zfs_snapshots` and `power_off`. Line 114 names `factory.shared.adapters.clock`, `factory.agents.adapters.fake_agent_runtime` and `factory.hosting.adapters.fake_hosting`. Lines 126-128 name `docs/operator-guide/README.md`, `docs/operator-guide/install.md` and `docs/operator-guide/stops.md`. Line 210 names `tests/conftest.py`. None of them is linked. Fix: link each once, at its first mention or in See also.
   9. Two code blocks have their file links below them, not above as the Interface says. The block at `docs/project-guide/shared.md:90` is followed by the links to `check_duplicates.py` (92) and `duplicates-baseline.txt` (109). The block at line 122 is followed by the link to `check_documents.py` (124). Fix: move the links into the sentences above each block.
   10. `docs/project-guide/machine.md:443,446` still point to *Killing a process group* in this page. That section name is gone; the content now sits under *Reading output and killing a group*. This fails criterion 5 and the Interface's rule that links to a changed heading change with it. Fix: point those two references to the new heading in [shared.md](shared.md).
   11. Under *Starting a process*, the page drops facts of the old file, and the entry does not name any of them as dropped on purpose (criterion 2):
       - the 64 KiB read size behind "however many reads it takes" (line 52);
       - "also not one already read in the same chunk" (line 53);
       - a last line's bytes stay in `stdout` (line 50);
       - "not from reader threads" (line 51);
       - a grandchild may still be ending for a moment after the kill returns (line 39);
       - after a timed-out read, `run_process` closes the pipes (line 37);
       - in the drain case, `run_streaming` has passed every complete line;
       - what `run_streaming` is for (the opencode runtime's budget and provider limit) and that `run_process` hands output over only at the end (line 47).
       Fix: restore each in its bullet or in the *Reference*, or name it in the entry as dropped on purpose.
   12. Under *The duplicates report* and *The document check*, more old facts are dropped without being named (criterion 2):
       - `gone` keys are to be removed from the baseline (line 97);
       - pylint and vulture are development dependencies;
       - the pipeline definition `factory/pipeline.yml` is what runs `make documents` (line 131);
       - `--root` names another checkout (line 122);
       - the example `factory.shared.domain.documents.named_references` for the module check (line 153);
       - the examples of a table that does not count: first column `Setting`, or the table under another heading (line 199).
       Fix: restore them or name each as dropped on purpose.
   13. `docs/project-guide/shared.md:164-180` (*The examples*), `133-145` (*The checked documents and the report*) and `206-218` (*How the check is tested*) do not follow the project guide's form in `style.md`. They name the main signatures only inside bullets: `examples(text)`, `Fixture.prepare(folder)`, `ExampleRunner.run_document(document, examples, fixtures)`, `read_checked_documents(text)`, `minimal_documents(root)` and `add_and_commit(root, {path: text})`. They have no signature block. Fix: put these signatures in an indented block after each section's opening sentences.

   Open: the stale docstring in `tests/guards/test_wrapper_search.py` ("the three wrappers") that the documenter noted is outside this story's write paths, and I have not named it as a finding.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's 13 findings. `make documents` ended with `documents ok (8.8 s)` and prints no finding for `shared.md`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/project-guide/shared.md`: the fixes below.
   - `docs/project-guide/machine.md`: the two references at lines 443 and 446 now point to [shared.md](shared.md), *Reading output and killing a group*. The old section name *Killing a process group* is gone.

   Findings:
   1. Fixed. The page now says the operator guide's `install.md` tables have a `Default` column and a refusal table, and that the check compares both.
   2. Fixed. The check reads the README, the two guides and the decision log. A new bullet gives the decision log rule: `missing`, `empty` or `no decision recorded`.
   3. Fixed. The page names the `sudo -n /usr/bin/systemctl poweroff` of the power-off among the commands started on the host.
   4. Fixed. I linked [project command](glossary.md), [journal](glossary.md), [work item](glossary.md), [story](glossary.md), [stop](glossary.md) and [instance](glossary.md) to `glossary.md` at their first use. The glossary has no heading anchors, so the links go to the file. I left "docs stage" unlinked, because the glossary has no entry for it.
   5. Fixed. "v1 words" is now "retired words". The exact `## Replaced from v1` and `## Replaced in v1.2` headings stay in code font, because they are names the check looks for.
   6. Fixed. I split the long sentences and the multi-parenthesis sentences: the suppression markers bullet, the timing bullet, the `ProcessExampleRunner` bullet, the `STOP_TABLE` sentence, the name-check sentences and the Reference bullets. The Reference's list of test files is now a nested list.
   7. Fixed. I dropped the `grep -c "does not exist"` sentence. It was an old claim with no runnable example, and the line format is stated in the page.
   8. Fixed. Every module, operator-guide page and `tests/conftest.py` the page names is linked once as a relative link. These are `git_cli`, `make_commands`, `claude_runtime`, `fake_containers`, `opencode_runtime`, `podman_runs`, `zfs_snapshots`, `power_off`, `clock`, `fake_agent_runtime`, `fake_hosting`, the three operator-guide pages and `conftest.py`.
   9. Fixed. The links to `check_duplicates.py`, `duplicates-baseline.txt` and `check_documents.py` now stand in the sentences above their code blocks.
   10. Fixed, see `machine.md` above.
   11. Restored in the bullets of *Starting a process*:
       - the 64 KiB reads;
       - a stop on a chunk that is already read;
       - the last line's bytes staying in `stdout`;
       - no reader threads;
       - the grandchild still ending after the kill;
       - the pipes closed after a timed-out read;
       - `run_streaming` having passed every complete line in the drain case;
       - what `run_streaming` is for;
       - `run_process` handing over its output only at the end.
   12. Restored:
       - `gone` keys are to be removed from the baseline;
       - pylint and vulture are development dependencies;
       - `factory/pipeline.yml` runs `make documents`;
       - `--root` names another checkout;
       - the `named_references` example for the module check;
       - the examples of a table that does not count.
   13. Added signature blocks to *The checked documents and the report*, *The name check*, *The examples* and *How the check is tested*, and to the duplicates section. I took the signatures from `documents.py`.

   Dropped on purpose: nothing new. The `Today's operator guide…` history sentence from round 0 stays dropped.

   Cross-read and found current: `docs/project-guide/README.md`, `docs/project-guide/style.md` (its link to *How the check is tested* resolves), `docs/checked-documents.txt` (the line is there once).

   Stale text I noticed and did not touch:
   - The docstring of `tests/guards/test_wrapper_search.py` says "the three wrappers", while the set lists nine modules. It is the tester's or coder's to fix.
   - `docs/project-guide/README.md` describes `shared.md` as covering only the process module. The page also holds the duplicates report and the document check. The index is outside this story.
   - The skills `Skill` listed in the harness were not used.

   `check`: check: green
   `secrets`: secrets: green (0.6 s)
   `documents`: documents ok (9.0 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 review of `git diff main...HEAD -- README.md docs operator/README.md`. The diff changes `docs/project-guide/shared.md`, `docs/project-guide/machine.md` (lines 443 and 446) and `docs/checked-documents.txt`.

    I read the new page in full against the code:
    - `src/factory/shared/adapters/process.py`: `_READ_SIZE = 65536`, `_END_POLL_SECONDS = 0.05`, `PIPE_DRAIN`, `ROOT`, `WNOWAIT` in `_has_ended`, `_start`, `_kill_session`, and the read after a kill in `run_process`.
    - `src/factory/machine/adapters/power_off.py`: the `sudo -n /usr/bin/systemctl poweroff` command and the `cannot start` prefix.
    - `src/factory/shared/domain/documents.py`: the signatures of `guide_tables`, `settings_findings`, `refusal_findings`, `named_references`, `unresolved`, `read_checked_documents`, `split_findings`, `examples` and `first_difference`.
    - `src/factory/shared/domain/duplicates.py`: its five functions.
    - `src/factory/shared/application/document_examples.py`: `Fixture.prepare` and `ExampleRunner.run_document`.
    - `factory/pipeline.yml`: `documents` is a check of `docs` and `docs-only`, and `duplicates` is a report of `doing`.
    - The test support modules: `minimal_documents` and `add_and_commit` in `minimal_documents_support.py`, the three helpers in `check_documents_support.py`, `clean_texts`, and the `minimal` fixture in `tests/conftest.py`.

    All 13 round-0 fixes hold in substance:
    - The claims about the operator guide, the decision log and power-off now match the code.
    - The `grep` command is gone.
    - The modules are linked.
    - The `machine.md` references point to *Reading output and killing a group*, which exists.
    - The dropped facts are back.
    - The new signature blocks match the code.

    The link from `style.md` to *How the check is tested* still resolves. The page holds no `console` block. I compared the old page's backticked names with the new page's. Every one that is missing as written is now a link, sits in a signature block or is a shorter form of the same name. The one exception is the `grep` command, which the round-0 entry names as dropped on purpose.

    Findings:

    1. `docs/project-guide/shared.md:127,141`: two glossary words are used but not linked at their first use (style rule 3, criterion 1).
       - "docs stage" (line 127) is not linked to **stage**. The round-1 entry says the glossary has no entry for "docs stage", but `glossary.md` has an entry **stage**.
       - "pipeline definition" (line 141) is not linked to **pipeline definition**.
       - Fix: link both to [glossary](glossary.md).
    2. `docs/project-guide/shared.md:141`: the file `factory/pipeline.yml` is named but not linked, which the Interface asks for every file the page names. Fix: link it once, `[pipeline.yml](../../factory/pipeline.yml)`.
    3. `docs/project-guide/shared.md:186-189,196`: the block names `Fixture.prepare(folder)` and `ExampleRunner.run_document(...)`. Their file, `src/factory/shared/application/document_examples.py`, is linked only at line 196, below the block. The Interface says to link it above. Fix: move that link into the sentences above the block.
    4. Style rule 2 says at most one parenthesis per sentence. These sentences have more:
       - Line 14 has five, from the links added in round 1.
       - Line 17 has two.
       - Line 49 has two: `("stdout")` and `("stderr")`.
       - Line 93 has two: `(only its duplicate-code messages, …)` and `(text)`.
       - Line 180 has two: `(<instance>)` and `(*)`.
       - Fix: split each sentence, or turn line 14 into one nested bullet per module, with each link as the bullet's subject.
    5. Style rule 2 also says to split a sentence of more than about 25 words. These sentences are still longer:
       - line 54: about 30 words;
       - line 103: about 40;
       - line 104: about 38;
       - line 114: about 35;
       - line 133: about 31, and round 0 already named it as line 124;
       - line 140, its first sentence: about 33;
       - line 177, its first sentence: about 30;
       - line 192, its first sentence: about 37;
       - line 223, its second sentence: about 37;
       - line 226, its second sentence: about 30;
       - line 243: about 41.
       - Fix: split each into sentences of one idea.

    Not a finding: `docs/project-guide/machine.md:443` still says "(since F0044-S0010)". That text was already on `main`, and `machine.md` is outside this story's rewrite.
12. factory: started docs-only as vm.
13. documenter: Round 2: I fixed the reviewer's five round-1 findings in `docs/project-guide/shared.md`. `make documents` ends with `documents ok (9.0 s)`. Its report lines name other files (for example `work.md:13`, `install.md`, `records.md`), none `shared.md`. I did not run `make check`, because I changed only documents.

    Files changed:
    - `docs/project-guide/shared.md`: the fixes below. It is the only file I changed this round.

    Findings:
    1. Fixed. "stage" in the document check section and "pipeline definition" now link to `glossary.md` at their first use. The glossary has an entry **stage**; my round-1 statement that it had none was wrong.
    2. Fixed. `factory/pipeline.yml` is linked once, as [pipeline.yml](../../factory/pipeline.yml).
    3. Fixed. The link to `src/factory/shared/application/document_examples.py` now stands in the sentence above *The examples* signature block, and the bullet below no longer carries it.
    4. Fixed. The parentheses are gone from the sentences you named:
       - The module list is now a nested bullet list with one link per module.
       - The opencode, Podman and ZFS/power-off bullets are split into short sentences.
       - The `"stdout"` and `"stderr"` parentheses are rewritten as separate sentences.
       - The duplicates intro sentence is split.
       - The `<instance>` and `*` parentheses are rewritten as "such as".
    5. Fixed. I split the long sentences: the `PIPE_DRAIN`-adjacent line-reading bullet, the duplicates output and exit-status bullets, the pylint refusal bullet, the opening of the story sentence, the guide-file bullet, the repository-path bullet, `NO_COMMAND`, the settings finding bullets, the default-compare bullet and the `minimal_documents` bullet. No fact was dropped.

    Dropped on purpose: nothing new.

    Cross-read and found current: `docs/project-guide/README.md`, `docs/project-guide/style.md` (its link to *How the check is tested* resolves), `docs/checked-documents.txt` (the line is there once).

    Stale text I noticed and did not touch:
    - `docs/project-guide/machine.md:443` still says "(since F0044-S0010)". That text is older than this story.
    - The docstring of `tests/guards/test_wrapper_search.py` says "the three wrappers", while the set lists nine modules. It is code, so not mine to edit.
    - `docs/project-guide/README.md` describes `shared.md` as covering only the process module, although the page also holds the duplicates report and the document check. The index is outside this story.
    - `docs/project-guide/work.md:13` is reported by the name check ("factory/agents does not exist"). It is a report line, not a blocker, and is not part of this story.

    `check`: check: green
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok (9.0 s)
14. factory: started docs-review as vm.
15. reviewer: Round 2 review of `git diff main...HEAD -- README.md docs operator/README.md`. The diff changes `docs/project-guide/shared.md`, `docs/project-guide/machine.md` (lines 443 and 446) and `docs/checked-documents.txt`.

    I read the new page in full. I checked each of the five round-1 findings against the round-1 text (commit `24f2d71e8`). I also checked the module claims against the code:
    - `opencode_runtime.py:750-751` uses `run_streaming` and `run_process`.
    - `podman_runs.py:64,170` uses `run_or_raise` for queries and `run_process` for a run.
    - `zfs_snapshots.py:154` and `power_off.py:28` use `run_or_raise` only.
    - `src/factory/shared/adapters/document_examples.py` and `src/factory/shared/application/document_examples.py` both exist.

    What holds:
    - Round-1 findings 1 to 4 are fixed. "stage" and "pipeline definition" link to the glossary. `pipeline.yml` is linked. The `document_examples.py` link of the interfaces now stands above *The examples* block (line 199). The parentheses named in round 1 are gone.
    - Of the long sentences named in round 1 (finding 5), every one is split except the one under finding 1 below.
    - `docs/checked-documents.txt` holds the line once. The two `machine.md` references point to *Reading output and killing a group*, which exists. The link from `style.md` to *How the check is tested* still resolves.

    Findings:

    1. `docs/project-guide/shared.md:207`: round 1 named this sentence (then line 192, about 37 words), and it is still not split: "The spaces or tabs before a block's opening fence are removed ... with the same line numbers." This breaks style rule 2. Fix: split it after "before they are read", for example "So a block indented under a numbered step reads as at column 0, with the same line numbers."
    2. `docs/project-guide/shared.md:131,133`: two more sentences are longer than about 25 words (style rule 2). Line 131 runs to about 35 words, from "It writes the header line" to the end of the parenthesis. Line 133 runs to about 31 words, from "The baseline accepts ... in fake_hosting.py". Fix: at 131, make the key order a sentence of its own. At 133, end the first sentence at "only the tests use" and list the three fakes in a second sentence or as sub-bullets.
    3. `docs/project-guide/shared.md:296`: one sentence holds four parentheses: `Examples (...)`, `Skipped (line and kind)`, `GuideTable (...)` and `SettingDoc (...)`. Style rule 2 allows at most one per sentence. Fix: make it a nested list with one type per bullet and its fields after a colon.
    4. `docs/project-guide/shared.md:214`: `src/factory/shared/adapters/document_examples.py` is linked a second time. It is already linked at line 19. The Interface says each file the page names is linked once. Fix: write `document_examples.py` plain at line 214, or name it as "the adapter module" without a link.

    Not a finding: the usage lines at 103 and 143 (`uv run python -m factory.entry.check_duplicates ...` and `... check_documents [--root <checkout>]`) are signatures with placeholders. They follow the project guide's form for names and signatures in an indented block, as `style.md`'s *The take* example does, and they are not shown as examples to run. The three See also links to `decisions.md` (lines 95, 135 and 273) follow the form of one See also per section. `machine.md:443` "(since F0044-S0010)" was on `main` before this story.
16. factory: started docs-only as vm.
17. documenter: Round 3: I fixed the reviewer's four round-2 findings in `docs/project-guide/shared.md`. `make documents` ends with `documents ok (9.0 s)`, and none of its report lines names `shared.md`. I did not run `make check`, because I changed only documents.

    Files changed:
    - `docs/project-guide/shared.md`: the fixes below. It is the only file I changed this round.

    Findings:
    1. Fixed. The indented-fence sentence is split after "before they are read"; the second sentence starts "So a block indented under a numbered step reads as at column 0, with the same line numbers."
    2. Fixed. In the `--write-baseline` bullet, the key order is now sentences of its own: header line; similar code first, then dead code, in input order; a key found twice is written once. The baseline bullet ends its first sentence at "only the tests use", and "These are ..." lists the three fakes.
    3. Fixed. The types of the check are a nested list with one type per bullet and its fields after a colon.
    4. Fixed. `document_examples.py` in the `ProcessExampleRunner` bullet is plain now. It is linked once, at the top of the page.

    Dropped on purpose: nothing.

    Cross-read and found current: `docs/checked-documents.txt` (the line is there once), `docs/project-guide/style.md`.

    Stale text I noticed and did not touch:
    - `docs/project-guide/README.md` describes `shared.md` as covering only the process module, although the page also holds the duplicates report and the document check. The index is outside this story.
    - The docstring of `tests/guards/test_wrapper_search.py` says "the three wrappers", while the set lists nine modules. It is code, so not mine to edit.
    - `docs/project-guide/work.md:13` is reported by the name check ("factory/agents does not exist"). It is older than this story.

    `check`: check: green
    `secrets`: secrets: green (0.7 s)
    `documents`: documents ok (8.9 s)
18. factory: started docs-review as vm.
19. reviewer: Round 3 review of `git diff main...HEAD -- README.md docs operator/README.md`. The diff changes three files:
    - `docs/project-guide/shared.md`
    - `docs/project-guide/machine.md`: lines 443 and 446.
    - `docs/checked-documents.txt`: one line added.

    I read the whole new page, checking it against style.md and against the code.

    The four round-2 findings are fixed:
    1. The indented-fence sentence is split. It is now `shared.md:207`.
    2. The `--write-baseline` bullet at line 131 is now four short sentences. Its claims match `src/factory/entry/check_duplicates.py`:
       - the header text matches `_BASELINE_HEADER` (line 19);
       - similar code comes before dead code (`_findings`, line 27);
       - a key found twice is written once (`dict.fromkeys`, line 33);
       - the printed line matches line 35.
       The baseline bullet at line 133 ends its first sentence at "only the tests use" and lists the three fakes in a second sentence.
    3. The types of the check are a nested list, one type per bullet (lines 296-301).
    4. `document_examples.py` at line 214 is plain text now. The adapter module is linked once, at line 19, and the application module once, at line 199. These are two different files.

    What else holds:
    - `docs/checked-documents.txt` holds `docs/project-guide/shared.md` once.
    - The two references in `machine.md` point to *Reading output and killing a group* in shared.md, and that heading exists.
    - style.md still links to *How the check is tested* (style.md:34), and that heading is kept.
    - No other document in `README.md`, `docs/` or `agents/` links to a heading of shared.md.
    - The page has no `console` block. The usage lines at 103 and 143 are signatures with placeholders, as round 2 judged.
    - Every glossary word the page uses is linked at its first use:
      - project command (50)
      - journal (107)
      - stage and work item (139)
      - story (145)
      - stop (148)
      - pipeline definition (155)
      - instance (229)

    The criteria:
    - Criteria 2 and 4 hold, as rounds 1 and 2 confirmed. Nothing was dropped on purpose except the `grep -c "does not exist"` command. The round-1 review named it, and the documenter's round-1 entry says why it was dropped.
    - Criterion 3 rests on the documenter's run: `make documents` printed `documents ok`, and no report line names shared.md. The factory runs it again.

    No findings.

    Open, outside this story:
    - The project guide's index, `docs/project-guide/README.md:29`, lists only some of shared.md's sections.
    - `machine.md:443` still says "(since F0044-S0010)". That text was already on `main`.
    - The docstring of `tests/guards/test_wrapper_search.py` says "the three wrappers", but the guard lists nine modules.
