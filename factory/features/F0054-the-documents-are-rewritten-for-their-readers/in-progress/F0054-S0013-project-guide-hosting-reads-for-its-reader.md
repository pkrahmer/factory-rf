---
stage: docs-review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 621
comments_read: []
handed_over: null
claim: null
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
