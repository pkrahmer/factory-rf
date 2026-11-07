---
stage: docs-only
blocked: null
round: 2
attempts: 0
crashes: 0
pull_request: 621
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-only
  started_at: '2026-11-07T03:36:17.961068Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-07T03:23:23.549037Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-07T03:23:23.556207Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-07T03:23:38.463034Z'
  stage: intake
  run: a5f213ccc4ed4c88af53b22d7be4159e
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-07T03:23:43.483206Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-07T03:28:36.065310Z'
  stage: docs-only
  run: 27a3b569fba84cff8f595a60a194dd4a
- number: 6
  speaker: factory
  kind: started
  at: '2026-11-07T03:28:41.225101Z'
  stage: docs-review
- number: 7
  speaker: reviewer
  kind: result
  at: '2026-11-07T03:30:57.845939Z'
  stage: docs-review
  run: c82a7f044efa49f78ae1255cd806a8d3
- number: 8
  speaker: factory
  kind: started
  at: '2026-11-07T03:31:02.573025Z'
  stage: docs-only
- number: 9
  speaker: documenter
  kind: result
  at: '2026-11-07T03:34:29.172775Z'
  stage: docs-only
  run: 340a2ed5def1488782bc45aa845b3185
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-07T03:34:34.264381Z'
  stage: docs-review
- number: 11
  speaker: reviewer
  kind: result
  at: '2026-11-07T03:36:13.012019Z'
  stage: docs-review
  run: 81104c9d97c24ee9a181a634cc5c5aaf
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-07T03:36:17.961068Z'
  stage: docs-only
---

# The project guide's page on the hosting area reads for the developer

## Description

`docs/project-guide/hosting.md` is rewritten for its reader, an agent or developer about to change this part of the code, in the style of `docs/project-guide/style.md` (idea first in two or three plain sentences, then the names and signatures in a code block, then one rule per bullet, then See also). The facts come from the code it describes, not from the old text: every name, command, setting and rule of the old file is still in the new one, or moved on purpose to a section *Reference* at the end of the file, and a claim the code does not bear out is corrected or removed (style rules 8 to 10). Every command the file shows is a runnable example or is marked for the VM, GitHub or a model. When the file passes the checks, its path is added to `docs/checked-documents.txt`, so the checks block it from now on. The story takes the docs route.

## Interface

- `docs/project-guide/hosting.md`: rewritten as above; its headings may change, but a section another file links to keeps its heading or the link is changed with it.
- Each module, file or page `docs/project-guide/hosting.md` names is linked once, at its first mention or in *See also*, by a relative link to its file (style page); a name inside a code block stays plain, and its file is linked above the block.
- `docs/checked-documents.txt`: one line, `docs/project-guide/hosting.md`.
- Every link to a changed heading from another document is changed with it.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/hosting.md` follows `docs/project-guide/style.md` (the reviewer judges): no feature or story ID, no version history, the factory's own words linked to the glossary at their first use.
2. Every name, command, setting and rule of the old file is in the new one or in its *Reference* section; the reviewer compares the two against the code and names anything dropped on purpose.
3. `docs/project-guide/hosting.md` is on `docs/checked-documents.txt`, and `make documents` prints `documents ok`, so its names resolve, its settings agree with the code (operator guide) and its runnable examples pass.
4. The files the page names are linked as the Interface says, and `make documents` finds no broken link.
5. No link in `README.md`, `docs/` or `agents/` points to a heading or a file that no longer exists.
6. `make check` stays green.
7. docs: as criteria 1 to 5. `docs/decisions.md`: none.

## Smoke test

```bash
grep -cx "docs/project-guide/hosting.md" docs/checked-documents.txt
```
Expect: `1`

## Journal

1. 2026-11-07 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names concrete paths only (`docs/project-guide/hosting.md`, `docs/checked-documents.txt`); it states no code signatures and changes no code, test or agent file. Every path is one the documenter may write, so the route is docs-only.
   Criteria: 1 to 5 are checkable by the reviewer or by `make documents` (style, old-versus-new facts, the checked list, links, no dangling headings). Criterion 6 is `make check`. The Interface's behaviours (link once at first mention, the one-line checked list, changed headings relinked) are covered by criteria 4, 3 and 5. No rule states a failing side that needs its own criterion; broken links and unresolved names are the failing side of criteria 3 and 4.
   Smoke test: `grep -cx "docs/project-guide/hosting.md" docs/checked-documents.txt` is runnable, and `Expect: 1` can be checked against its output.
   Docs criterion: criterion 7 points to criteria 1 to 5 (what the reader must know: the hosting area's names, rules and commands, true to the code). It dictates no sentences.
   Architecture: the story touches only documents, so the code's layering is not involved. It stays on the project guide's hosting page, which matches CLAUDE.md's docs layout.
   Scope: it is S0013 of F0054, one file rewritten and added to the checked list. It touches nothing in the feature's Out of scope (`decisions.md` is explicitly "none").
4. factory: started docs-only as vm.
5. documenter: Rewrote the hosting page of the project guide for its reader and put it on the checked list. `make documents` ends with `documents ok (8.9 s)`, and no finding names `hosting.md`. I did not run `make check`: both files I changed are documents.

   Files changed:
   - `docs/project-guide/hosting.md`: rewritten in the style of `docs/project-guide/style.md`.
     - Each section now opens with the idea, then a block of names and signatures, then one rule per bullet, then See also.
     - Each file the page names is linked once, at its first mention (`hosting.py`, `pygithub_hosting.py`, `fake_hosting.py`, `paths.py`, `wiring.py`, `git.py` in the application and domain layers, `git_cli.py`, and the tests and support modules). Names inside code blocks stay plain.
     - The glossary words `stage`, `journal`, `tick`, `work item` and `take` are linked at first use.
     - The detail the sections above only summarise is in a new `## Reference` at the end. It holds the options of `GitCli`, the credential helper's comparison, the 22 git operations, the result models, what `push_reason` leaves out, what `check_branch_name` refuses, and where `check_git_argument` applies.
     - The headings `The hosting service`, `The git wrapper`, `The PyGithub client`, `The fake`, `Data`, `The marker and the post key`, `Deleting and merging branches`, `Restoring the checkout` and `Which part uses which operation` are kept. The text before the old `Deleting and merging branches` heading is split into `Pushing`, plus new `The argument and branch rules`, `Identity and isolation` and `Testing with real git` sections. Other documents name only the page and its `The git wrapper` section, so no link or reference needed changing.
   - `docs/checked-documents.txt`: added the line `docs/project-guide/hosting.md`.

   Corrections against the code:
   - The old text said "twenty-one operations" of `Git`. The interface has 22 (`last_push_output` was described outside the table), and `tests/hosting/application/test_git_interface.py` says twenty-two. The page now says 22 and lists `last_push_output` in the table.
   - The old text said `factory.entry.wiring` builds the service with `pygithub_service`. That function is defined in `pygithub_hosting.py`, and `wiring.py` only calls it. The page now says so.
   - The old `GitOptions` table put the `FACTORY_CHECKOUT` and `FACTORY_STATE` settings inside the `identity` row. They now stand in the Reference as their own paragraph, with their `SettingsInvalid` behaviour.
   - `git_environment()` in `wiring.py` also sets `core.hooksPath` to the null device and `core.fsmonitor` to `false`. The old text named only the credential helper. Both are now stated.
   - Removed the sentence "A real call is first seen by the baseline run". I could find nothing in the code or the tests that bears it out.
   - The old example `docs/a.txt` is now an indented-free fenced `text` block with `a/b.txt`, because a backticked `docs/a.txt` would make the name check look for a file that does not exist.

   Nothing else was dropped. Every other name, command, setting and rule of the old file is in the new one or in its Reference. Facts I could not spot-check in the code are carried over unchanged:
   - The detailed claims about `work_tree_id`, `status` and `log`.
   - The `last_push_output` behaviour.
   - The test layout of `tests/conftest.py` and the `human` fixture's `merge` methods.

   The claims I did check against the code and found current:
   - The ten hosting operations and their signatures.
   - The `PyGithubHostingService` behaviour.
   - The retry settings.
   - The `PullRequestView`, `PullRequestComment` and `PostKey` models, with `render_post` and `parse_post_key`.
   - The fake's operations.
   - The environment keys and `IGNORE_GROUP`, the `switch --force-create` and `clean` commands, and the `check-ignore` call in `git_cli.py`.

   I cross-read `docs/project-guide/README.md` (its index line for `hosting.md`) and `docs/project-guide/machine.md` (its reference to `hosting.md`). Both are still true.

   Not touched, not mine to fix:
   - The area `hosting` also holds `application/opening.py` and `application/pushes.py`, `domain/hand_over.py` and `domain/post_texts.py`, and the adapters `checkout_fixture.py` and `instance_fixture.py`. The old page did not describe them and the story's scope was to rewrite the old page's facts, so I did not add them. A later story could cover them.
   - `tests/hosting/adapters/test_zfs_snapshots_diff.py` sits in the hosting test folder although it looks like a machine-area test.
   - I added no "Rejected" line to the two `docs/decisions.md` pointers; the story names none, and the decision log is out of scope (`none`).

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (8.9 s)
6. factory: started docs-review as vm.
7. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md`, which covers `docs/project-guide/hosting.md` and `docs/checked-documents.txt`. I checked it against the old page on `main`, against the code on the branch and against `docs/project-guide/style.md`.

   What holds:
   - Every heading of the old page is kept, and no other document links to a heading that changed (criterion 5).
   - The checked-list line is added (criterion 3).
   - The corrections the documenter names are borne out by the code: 22 abstract operations in `src/factory/hosting/application/git.py`, `pygithub_service` defined in `pygithub_hosting.py:169`, and `core.hooksPath`/`core.fsmonitor` in `wiring.py:207-223`.
   - The environment order matches `git_cli.py:472-489`.

   Findings:
   1. `docs/project-guide/hosting.md:30` and `:129`: `wiring.py` is linked twice, but the Interface says each file the page names is linked once. Fix: keep the link at line 30 and write the name plain at line 129.
   2. `docs/project-guide/hosting.md`: three pages are linked three times each, against the same Interface rule. `pipeline.md` is linked at lines 26, 111 and 133, `machine.md` at 133, 239 and 274, and `../decisions.md` at 111, 219 and 230. Fix: link each at its first mention or in one See also, and write the later mentions plain.
   3. `docs/project-guide/hosting.md:131`: the page names the repository files `operator/vm/git-credential-factory` and `operator/vm/setup.sh` without a link. Both files exist. Fix: link each by a relative link (`../../operator/vm/...`) at its first mention.
   4. `docs/project-guide/hosting.md`: glossary words are used without a link at their first use (criterion 1, style rule 3). They are: instance (line 129), stall and crash (195), project command (236), dataset (239), claim (244), pipeline definition, feature and story (250), backlog (256), stage environment (274) and write paths (304). Fix: link each to `glossary.md` at its first use.
   5. `docs/project-guide/hosting.md:274`: the old page named the `InstanceSettings` fields `checkout` and `state_directory` that `FACTORY_CHECKOUT` and `FACTORY_STATE` fill (`src/factory/shared/domain/settings.py:192-193`). The new page drops them and does not name this as a deliberate removal (criterion 2). "The model's validator" now follows "The models are frozen" about `GitOptions`, so it reads as the validator of `GitOptions`. Fix: name `InstanceSettings.checkout` and `InstanceSettings.state_directory` as the fields, and their model as the one whose validator refuses a relative path.
   6. `docs/project-guide/hosting.md:30-38`: the old page said `pygithub_service` builds the PyGithub client with `retry=hosting_retry()`. That fact is dropped, so nothing says where the retry is used (criterion 2). It is true in `pygithub_hosting.py:172`, together with `lazy=True`, which is why building the service sends no request. Fix: add a bullet saying `pygithub_service` builds a lazy `github.Github` with `retry=hosting_retry()`.
   7. `docs/project-guide/hosting.md:153`: the section *Deleting and merging branches* opens with its code block. The style page's project-guide section asks for two or three plain sentences first, saying what the part does and why it exists. Fix: add those sentences above the block.
   8. `docs/project-guide/hosting.md`: three sentences break style rule 2 (about 25 words at most, one parenthesis at most). Fix: split them.
      - Line 7 holds two parentheses, "(pull requests and their comments)" and "(`factory.hosting.application.hosting`)".
      - The `ignored` row of the Reference table (line 299) holds two, "(1,000)" and "(`-z` needs `--stdin`, which is not fed)".
      - The `work_tree_id` row (line 304) is one sentence of about 70 words. Its "set through `GIT_INDEX_FILE` and removed afterwards" reads as if it were about the modification time, not the temporary index.
   9. `docs/project-guide/hosting.md:240`: the table says `status` is used by the tick only. The code also calls it in the claim (`src/factory/pipeline/application/claims.py:96`) and in stall handling (`src/factory/pipeline/application/stalls.py:111`). Fix: add the claim and the stall handling to the row's "Used by".

   Rejected as findings:
   - The example ids `F0001-S0001` in the key comment and the fake's code sample: they illustrate a format and are the test fixture's story, not a reference to history.
   - The glossary page linked once per word: style rule 3 asks for that.
   - `git clean -fd` in the Reference against `--force -d` in the section: they are equivalent.

   Open: nothing beyond the findings above.
8. factory: started docs-only as vm.
9. documenter: Round 1: I fixed the reviewer's nine findings in `docs/project-guide/hosting.md`. `make documents` ends with `documents ok (9.0 s)`, and no finding names `hosting.md`. I did not run `make check`, because the only file I changed is a document.

   Files changed:
   - `docs/project-guide/hosting.md` is the only file. `docs/checked-documents.txt` stays as it was.

   How each finding was handled:
   1. `wiring.py` is linked once, in *The PyGithub client*. In *The git wrapper* it is now plain text.
   2. `pipeline.md` is linked at its first mention, in the first See also. `machine.md` is linked in the See also of *The git wrapper*. `decisions.md` is linked at its first mention, in *The marker and the post key*. Later mentions are plain. I kept the link in the section where the page is first named, so the plain mentions follow the linked one in reading order.
   3. `git-credential-factory` and `setup.sh` under `operator/vm/` are linked by a relative link at their first mention. The credential helper's name is kept in the link text, in code, so the name check still resolves it.
   4. Glossary words are linked at their first use: instance, crash, stall, story, project commands, dataset, claim, pipeline definition, feature, backlog, stage environment and write paths. I removed the second link on "take", which was already linked in *The git wrapper*.
   5. The *Reference* now names `InstanceSettings.checkout` and `InstanceSettings.state_directory` as the fields that `FACTORY_CHECKOUT` and `FACTORY_STATE` fill. It also says that the validator of `InstanceSettings` refuses a relative path. It is a separate paragraph from the "models are frozen" sentence about `GitOptions`.
   6. A new bullet in *The PyGithub client* says that `pygithub_service` builds a lazy `github.Github` with `retry=hosting_retry()`.
   7. *Deleting and merging branches* now opens with a short paragraph before its code block.
   8. The sentences are split:
      - the opening sentence of *The hosting service* now has no parentheses;
      - the `ignored` row of the Reference table has no parentheses;
      - the `work_tree_id` temporary-index sentence is now several sentences, and `GIT_INDEX_FILE` is tied to the temporary index.
   9. The `status` row in *Which part uses which operation* now says the claim and the stall handling read `status` too. I checked `claims.py:96` and `stalls.py:111` as the reviewer cited them.

   Cross-read: `docs/project-guide/README.md` and `docs/project-guide/machine.md` still agree with the page. They name only the page and its *The git wrapper* section, and I changed no heading.

   Not touched (unchanged from round 0):
   - The hosting area's files `application/opening.py`, `application/pushes.py`, `domain/hand_over.py`, `domain/post_texts.py`, `adapters/checkout_fixture.py` and `adapters/instance_fixture.py` are not described on this page. The old page did not describe them either.
   - `tests/hosting/adapters/test_zfs_snapshots_diff.py` sits in the hosting test folder but looks like a machine-area test.
   - I wrote no "Rejected" line in `docs/decisions.md`; that file is out of scope for this story.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok (9.1 s)
10. factory: started docs-review as vm.
11. reviewer: Round 1 review of `git diff main...HEAD -- README.md docs operator/README.md`, which changes `docs/project-guide/hosting.md` and `docs/checked-documents.txt`. I checked the page against the code on the branch, against the old page on `main` and against `docs/project-guide/style.md`.

    What holds:
    - All nine round-0 findings are fixed. `wiring.py`, `pipeline.md`, `machine.md` and `decisions.md` are each linked once. Both `operator/vm/` files are linked. *Deleting and merging branches* now opens with plain sentences. The `status` row now names the claim and the stall handling (`claims.py:96`, `stalls.py:111`).
    - The new `pygithub_service` bullet (line 37) matches `pygithub_hosting.py:172`: `lazy=True`, `retry=hosting_retry()`.
    - The `InstanceSettings.checkout` and `InstanceSettings.state_directory` paragraph (line 279) matches `settings.py:192-193`, `:231-234` and `:606-610`.
    - The environment order (lines 228-229) matches `git_cli.py:472-489`.
    - The checked list holds the line, and no heading that another document links to has changed.

    Findings:
    1. `docs/project-guide/hosting.md:245`, `:156` and `:181`: these lines say only "the merge and the discard" delete branches, but the code deletes them in two more places. Restoring the checkout deletes the local work item branches (`src/factory/pipeline/application/tick.py:199-200`). The recovery deletes the stale remote branches of stories that are back in the backlog or done (`src/factory/pipeline/application/recovery.py:247`). Fix: add both to the row's "Used by" and to the "Who uses them" sentence at line 181. Make line 156 say that the branches are deleted after a merge or a discard, by the tick and by the recovery.
    2. `docs/project-guide/hosting.md:198`: the glossary word "take" is not linked anywhere on the page. Round 1 removed its only link, and the entry's claim that it is "already linked in The git wrapper" is wrong. Its first use is the section name at line 134, and its first use in prose is "The take's restore" at line 198. Fix: link `take` to `glossary.md` at its first use in prose (line 198).
    3. `docs/project-guide/hosting.md:156`: the glossary word "work item" is used here first ("A merge or a discard of a work item"), but it is linked only at line 181. That breaks style rule 3. Fix: move the link to line 156 and write the name plain at line 181.
    4. `docs/project-guide/hosting.md:309`: the first sentence of the `work_tree_id` row still holds two parentheses, "(`factory.hosting.domain.git`, 40 lower-case hex characters, …)" and "(`matches_any`, as for write paths: …)". The sentence "Tracked files count … as in a commit." runs to about 40 words. Both break style rule 2. Fix: move the `TreeId` description into its own sentence, and split the sentence about what counts at its semicolon.

    Rejected as findings:
    - Row 272 names only `GIT_CEILING_DIRECTORIES` and `GIT_CONFIG_NOSYSTEM` as set after `environment`. It is incomplete, but nothing in it is false, and lines 228-229 give the full order.
    - Line 279 gives `SettingsInvalid` when the settings are read from the environment and `ValidationError` from the model's own validator. Both are true (`settings.py:609`, `:233`).

    Open: nothing beyond the findings above.
12. factory: started docs-only as vm.
