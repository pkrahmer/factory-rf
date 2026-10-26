---
stage: docs
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 468
comments_read: [6426528724]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T20:11:58.255677Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T20:11:58.261426Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T20:12:19.282629Z'
  stage: intake
  run: 0bf65c96bfeb4c08a3be8b80931dd8ad
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T20:12:40.062195Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-26T20:18:28.595943Z'
  stage: tests
  run: 02bd7ed9f1c24bda8cf54ee8074d9437
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-26T20:18:51.546096Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-26T20:25:08.050783Z'
  stage: doing
  run: 9b709544a35740aea01d0b6cfc5ed822
  blocked: question
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-26T20:26:26.443367Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-26T20:26:45.968641Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-26T20:26:59.337001Z'
  stage: doing
  run: 5c0948ef30a34d4ba5aeea407cd7979b
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-26T20:27:20.074710Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-10-26T20:32:59.566013Z'
  stage: tests
  run: 58f7e459a9b943c1883329ce3c2c1d78
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-26T20:33:19.846813Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-26T20:39:13.050548Z'
  stage: doing
  run: e246600b711c4e7dad481ec974836947
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-26T20:39:33.914096Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-26T20:40:11.606894Z'
  stage: review
  run: 794bb48d2afe4f1d82e83e2e0e300b51
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-26T20:40:32.113581Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-26T20:41:02.634142Z'
  stage: doing
  run: ad259a439b974c009d5a46cbc8829ba6
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-26T20:41:23.231453Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-10-26T20:47:12.294587Z'
  stage: tests
  run: 2d798f5d87024f0b9dc72922443d983b
- number: 21
  speaker: factory
  kind: started
  at: '2026-10-26T20:47:33.162898Z'
  stage: doing
- number: 22
  speaker: coder
  kind: result
  at: '2026-10-26T20:53:27.527768Z'
  stage: doing
  run: d859e7ea28e24188ae834fcff95288e5
- number: 23
  speaker: factory
  kind: started
  at: '2026-10-26T20:53:48.083294Z'
  stage: review
- number: 24
  speaker: reviewer
  kind: result
  at: '2026-10-26T20:54:31.807959Z'
  stage: review
  run: 12c10872da74475880e6d46b07d52377
---

# The setup script says how to install a changed unit

## Description

`vm/setup.sh` installs the unit `vm/factory.service` and the helper `vm/git-credential-factory` from the factory's checkout only in the run that made the clone, or when the installed file is missing (F0043-S0003): the checkout belongs to `factory`, so after the first run root takes nothing from it. A later run that finds an installed file different from the checkout prints `... differs from the checkout; not installed` and leaves it, and the operator guide then advises to remove the installed file and run the script again, which makes root install the checkout's text after all and so undoes the very rule. On `vm` the operator installed the unit by hand instead (`planning/overnight/gcp-trial-checklist-2026-10-26.md`). This story keeps the rule and makes the way out exact (decision 17 of `feature.md`): each of the two lines names what to do, and the operator guide says, in *The two passes* and *The rebuild after a merge*, how to install the new file from the operator's own copy of the ref, the same copy the rebuild already takes `vm/setup.sh` from. What stays: when and from where the script installs the two files, every other step, line and exit status of the script.

## Interface

No module under `src/factory/` changes. The coder changes `vm/setup.sh` (POSIX `sh`): the two lines on standard error become exactly:

```text
setup: tools: /usr/local/bin/git-credential-factory differs from the checkout; not installed; install it from your own copy of vm/git-credential-factory (operator guide, "The rebuild after a merge")
setup: service: /etc/systemd/system/factory@.service differs from the checkout; not installed; install it from your own copy of vm/factory.service (operator guide, "The rebuild after a merge")
```

The conditions under which the two files are installed do not change.

The commands the guide gives (the documenter writes them; the zone and the VM's name are the guide's own of step 6 of *On GCP, step by step*): on the operator's computer, in the checkout of the ref the instance runs, `gcloud compute scp --zone=europe-west3-a --tunnel-through-iap vm/setup.sh vm/factory.service vm/git-credential-factory factory-vm:`; on the VM from the operator's own account, before the script, for the file the script named: `sudo install -m 0644 factory.service /etc/systemd/system/factory@.service` or `sudo install -m 0755 git-credential-factory /usr/local/bin/git-credential-factory`; then the script as in the rebuild, which runs `systemctl daemon-reload` and reports the file found.

Tests (the tester writes them): a new test at the tester's choice, for example `tests/test_vm_setup_install_hint.py`, reading the script through `tests/vm_support.py`. One earlier test change, with the human's leave (journal entry 8): in `tests/test_vm_setup_text.py` the helper `_install_conditions` counts a line as an install only when its command is `install` (`^\s*install\s` after the indentation), so that the new line, which names `install` and the path, is not taken for one; `test_the_checkout_files_are_installed_only_in_the_run_that_cloned` keeps its name, checks the same rule and still finds `differs from the checkout; not installed` in both steps. No other earlier test changes (decision 23 of `feature.md`).

## Acceptance criteria

1. The two lines (rows of one parametrized test over the script's text with its comment lines dropped, the steps cut as `tests/vm_support.py` cuts them, one row per step `tools` and `service`): the step's text holds its line of the Interface exactly once, on a line that sends it to standard error (`>&2`), and no other line of the script holds `differs from the checkout`.
2. The rule is unchanged (the existing `tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned`, its helper narrowed as the Interface says): each of the two files is installed only under the condition that the run cloned or the installed file is missing.
3. The script stays valid (the existing `tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu`): `sh -n vm/setup.sh` exits 0.
4. `make check` stays green.
5. docs: `docs/operator-guide.md`, `## The machine`, `### The script`, *The two passes*: the paragraph on a later run quotes the two new lines and gives the install commands of the Interface instead of "remove the installed file and run the script again", with the reason (root installs nothing from the checkout `factory` can write; the operator's own copy is the trusted text); `### The rebuild after a merge`: the copy to the VM names the three files, and the last paragraph says that when a merge changed `vm/factory.service` or `vm/git-credential-factory`, the operator installs it with the commands of the Interface before running the script; the advice to remove the installed file goes from both sections. `docs/decisions.md`: the entry "The factory runs on the host, and the stage image carries the tools alone" gains one closing line: "Since v1.2 F0045-S0003 a later run names the operator's own copy as the way to install a changed unit or helper; removing the installed file is no longer advised." `docs/project-guide/`, `README.md`: none.

## Smoke test

```bash
sh -n vm/setup.sh && echo syntax-ok
grep -c 'differs from the checkout; not installed; install it from your own copy of vm/' vm/setup.sh
grep -c 'remove the installed file and run the script again' docs/operator-guide.md
```
Expect: three lines: `syntax-ok`; `2`; `0`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: only `vm/setup.sh` changes, and the two lines at 348 (`tools`) and 392 (`service`) are given as exact text with their `>&2`. The install conditions are stated unchanged, and the guide commands are concrete (`gcloud compute scp`, `sudo install -m 0644|0755`).
   Criteria: 1 is one parametrized test, one row per step. It also checks that no other line holds `differs from the checkout`, which covers the old wording going. 2 is the existing test, unchanged, so the pass side of the install rule is covered. 3 is `sh -n`. 4 and 5 are the closing criteria. The failing side of the rule (a differing file is not installed) is the one the existing test pins, and the story adds no new rule. The docs criterion is a document check, not a tested behaviour.
   Smoke test: all three commands run. `sh -n` gives `syntax-ok`. The `grep -c` on the setup script gives 2 once the lines change (currently 0). The `grep -c` on the guide currently gives 2 (lines 443 and 703), and the docs criterion removes both, giving 0. The `Expect:` line is checkable. The command does not run pytest, so the `-q` addopts rule does not apply.
   Architecture: no `src/factory` change. `vm/setup.sh` is the coder's write path, and the guide and decision log are the documenter's.
   Scope: it matches the S0003 line of `feature.md` and decision 17. Decision 23 says no earlier test changes. Nothing in Out of scope is touched.
4. factory: started tests as vm.
5. tester: Wrote the tests for the two lines on standard error and for the script's syntax. No earlier test changed.
   criterion 1: tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy (rows `tools`, `service`). The test runs over the script's text with its comment lines dropped (the `code` fixture) and cuts the steps with `vm_support.step_texts`. Each step holds its exact line from the Interface once, on a line with `>&2`. The script has exactly two lines holding `differs from the checkout`, and each of them is one of the two new lines.
   criterion 2: tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned (the existing test, unchanged).
   criterion 3: tests/test_vm_setup_install_hint.py::test_the_setup_script_parses (`sh -n vm/setup.sh` exits 0).
   criteria 4 and 5: `make check` and docs; no test.
   Files created: tests/test_vm_setup_install_hint.py.
   Modules not importable: none. Both rows of the criterion 1 test fail with `assert 0 == 1` because `vm/setup.sh` still prints the old lines (348 and 392). The syntax test passes now, as it should, since the story changes no syntax. `make lint` is green.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy[service] - assert 0 == 1
6. factory: started doing as vm.
7. coder: Stopped before implementing: the new test and an earlier test contradict each other. I left the working tree unchanged. I had edited `vm/setup.sh` and then reverted it.

   What I tried: in `vm/setup.sh` (lines 348 and 392) I changed the two echo lines to the Interface's exact text. Each line was single-quoted, because the text contains `"The rebuild after a merge"`. With that change, `tests/test_vm_setup_install_hint.py` passes. But all four rows of the earlier `tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned` fail:
   ```
   tests/test_vm_setup_text.py:567: in test_the_checkout_files_are_installed_only_in_the_run_that_cloned
   E   assert None is not None
   ```
   Cause: the helper `_install_conditions` (tests/test_vm_setup_text.py:525) treats every line that matches `(?<![\w-])install\s` and contains the target path as an install command. The Interface's line holds both `install it from your own copy of ...` and the path (`/usr/local/bin/git-credential-factory` or `/etc/systemd/system/factory@.service`). So the echo line counts as an install. It sits under `else`, `_enclosing_if` returns None, and the test fails. Any script that prints the exact Interface line on one line (which criterion 1 requires) breaks criterion 2's test. Decision 23 says no earlier test changes.

   Options:
   A. With the human's leave, the tester narrows `_install_conditions` so that only an `install` command counts, not an echo. For example, the line starts with `install` after its indentation, or the regex is `^\s*install\s`. The test keeps its name and checks the same rule. The script change is then the two echo lines exactly as in the Interface. **This is what I would choose.**
   B. Change the Interface's wording so that a line naming the path does not hold the word `install` followed by a space (for example "put it in place from your own copy of ..."). Criterion 1's test text and the smoke test's `grep` pattern would change with it.
   C. Restructure the script so that the echo sits under an `if` of its own whose condition satisfies the earlier test's checks. That bends the script around a test heuristic and changes the structure the Interface says stays. I reject it.

   Not touched: nothing else. `make check` is otherwise green apart from these four rows.
8. 2026-10-26 human: A: the human's leave for exactly this: the tester narrows `_install_conditions` in `tests/test_vm_setup_text.py` so that only a line whose command is `install` (`^\s*install\s` after the indentation) counts, not an echo; the test keeps its name and checks the same rule. The script change stays the two echo lines exactly as in the Interface.
9. factory: started doing as vm.
10. coder: Sent back to the tester for the test change the human allowed in entry 8. I changed no code and left the working tree clean.

    Test change, in one sentence: in `tests/test_vm_setup_text.py`, narrow the helper `_install_conditions` (line 525) so that a line counts as an install command only when its command is `install` (`^\s*install\s` after the indentation), not when it is an echo that mentions `install`, while `test_the_checkout_files_are_installed_only_in_the_run_that_cloned` keeps its name and checks the same rule.

    Once that change is in, I will make the script change. It is only the two echo lines in `vm/setup.sh` (lines 348 and 392), set to the Interface's exact text and single-quoted, as entry 7 describes.

    What the journal changed: criterion 2's test is no longer left entirely unchanged. With the human's leave, its helper is narrowed as above. The rule it checks stays the same, and the Description's meaning stays the same, so I did not rewrite `## Description`.
11. factory: started tests as vm.
12. tester: I made only the test change the human approved in entry 8, which the coder named in entry 10.

    Changed: `tests/test_vm_setup_text.py`, the helper `_install_conditions`. Its line filter was `re.search(r"(?<![\w-])install\s", line)` and is now `re.search(r"^\s*install\s", line)`. A line now counts as an install of the target only when its command is `install` after the indentation. An `echo` that mentions "install it from your own copy of …" together with the path no longer counts. `test_the_checkout_files_are_installed_only_in_the_run_that_cloned` keeps its name and checks the same rule (criterion 2). `ruff format` then put the list comprehension on one line.

    Criterion mapping (unchanged since entry 5):
    criterion 1: tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy (rows `tools`, `service`)
    criterion 2: tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned (its helper narrowed as above, with the human's leave)
    criterion 3: tests/test_vm_setup_install_hint.py::test_the_setup_script_parses
    criteria 4 and 5: `make check` and docs; no test.

    Files created: none. Earlier test file changed: tests/test_vm_setup_text.py, with the human's leave in entry 8.
    Modules not importable: none.

    `make test`: all four rows of the earlier test pass against the current script, whose `install` commands start their lines. The only failures are the two rows of the criterion 1 test (`assert 0 == 1`), because `vm/setup.sh` still prints the old lines. `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: FAILED tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy[service] - assert 0 == 1
13. factory: started doing as vm.
14. coder: Changed only `vm/setup.sh`: the two lines that report a differing installed file (line 348 for step `tools`, line 392 for step `service`) now read exactly as the Interface gives them, still sent to standard error with `>&2`. No condition, step, other line or exit status changed. Both rows of `tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy` now pass. The narrowed `tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned` from entry 12 also passes. `make check` is green (`check: green`), and `grep -c` on the smoke test's pattern now gives 2.

    Main choice: I put the Interface's lines in single quotes, because the text contains `"The rebuild after a merge"`. I rejected the alternative of keeping double quotes and escaping the inner quotes as `\"`: the line in the script would then no longer match the Interface's text exactly, and that exact text is what criterion 1's test looks for.

    Refactor: I read the diff (two lines changed) and found nothing to change.

    What the journal changed: with the human's leave in entry 8, criterion 2's test helper was narrowed. The rule it checks and the meaning of the Description stay the same, so I did not rewrite `## Description`.

    Noticed but not touched: `docs/operator-guide.md` still advises removing the installed file, in *The two passes* and *The rebuild after a merge*. `docs/decisions.md` still needs its closing line. Both are for the documenter, under criterion 5.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
15. factory: started review as vm.
16. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (`vm/setup.sh`, `tests/test_vm_setup_install_hint.py`, `tests/test_vm_setup_text.py`) against the work item.

    Groups 1 to 3 hold. Criterion 1: the parametrized test has rows `tools` and `service`. Each step holds its Interface line exactly once, on a `>&2` line, and the only two `differs from the checkout` lines are the two new ones. Criterion 2: the earlier test still passes, and its narrowed helper still finds the `install` lines at `vm/setup.sh:345` and `vm/setup.sh:389`. Criterion 3 is covered by `sh -n`. The script change is only the two echo lines, single-quoted and exactly as the Interface gives them, so the install conditions are unchanged. The coder's `make check` was green (entry 14). No `src/` change and no suppression markers. Group 4 fails:

    1. `tests/test_vm_setup_install_hint.py:38` `test_the_setup_script_parses`: duplicates the `sh -n vm/setup.sh` exit-0 check that `tests/test_vm_setup.py:23` `test_the_script_parses_and_starts_with_its_shebang_and_set_eu` already makes. That would be criterion 3's one test, so this is a second copy of an existing test (round 0, so it is a finding). Fix: the tester removes the new test, together with the `Path`, `ProcessRequest`, `run_process` and `SETUP` imports that only it uses. Criterion 3 then maps to the existing test.

    Earlier tests:
    - `tests/test_vm_setup_text.py`: changed under the human's leave in journal entry 8. Only `_install_conditions` changed: its filter became `^\s*install\s` and `ruff format` joined the comprehension onto one line. The test keeps its name and its rule, so the change stays within the leave.

    Seen while reading, not reviewed as a group because group 4 failed first: criterion 2 still calls the earlier test "unchanged", and the Interface still says "No earlier test changes". Since entry 8 both are out of date. They are worth fixing in the same round.
17. factory: started doing as vm.
18. coder: Sent back to the tester for the reviewer's finding in entry 16, which is a change to tests only. I changed no code.

    The test change: in `tests/test_vm_setup_install_hint.py`, remove `test_the_setup_script_parses` and the imports that only it uses (`Path`, `ProcessRequest`, `run_process`, `SETUP`). I checked that `tests/test_vm_setup.py:23` `test_the_script_parses_and_starts_with_its_shebang_and_set_eu` already runs the same `sh -n vm/setup.sh` and asserts exit status 0, so the new test is a second copy. Criterion 3 now maps to that existing test.

    What the journal changed: the Description was out of date in the places the reviewer named. I rewrote those three spots in the work item and nothing else.
    - The Interface's test paragraph now says the one earlier test change the human allowed in entry 8: `_install_conditions` in `tests/test_vm_setup_text.py` counts a line only when its command is `install` (`^\s*install\s`). Before, it said "No earlier test changes".
    - Criterion 2 now says the test's helper was narrowed, instead of "unchanged".
    - Criterion 3 now names the existing test, instead of "one test".
    The Description has no "as of" heading, so there was none to update. The meaning of the task is the same.

    Code: `vm/setup.sh` stays as entry 14 left it: the two Interface lines, single-quoted, sent with `>&2`. The reviewer found nothing to change there, so this round has no refactor.

    Noticed but not touched: the docs part of criterion 5 is still open (`docs/operator-guide.md`, *The two passes* and *The rebuild after a merge*, and the closing line in `docs/decisions.md`). That is the documenter's work.

    The factory left out changes outside the write paths: factory/features/F0045-smaller-items-of-the-candidates-list/in-progress/F0045-S0003-the-setup-script-says-how-to-install-a-changed-unit.md.
19. factory: started tests as vm.
20. tester: I made only the test change the coder named in entry 18, which answers the reviewer's finding in entry 16.

    Changed: in `tests/test_vm_setup_install_hint.py` I removed `test_the_setup_script_parses`. It was a second copy of the `sh -n vm/setup.sh` exit-0 check that `tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu` already makes. I also removed the imports only it used (`Path`, `ProcessRequest`, `run_process`, `SETUP`) and dropped "and its syntax" from the module docstring. `ruff format` removed a trailing blank line. No other test changed.

    Criterion mapping:
    criterion 1: tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy (rows `tools`, `service`)
    criterion 2: tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned (its helper `_install_conditions` narrowed to `^\s*install\s` in entry 12, with the human's leave in entry 8)
    criterion 3: tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu (an existing test)
    criteria 4 and 5: `make check` and docs; no test.

    Files created: none. Changed: tests/test_vm_setup_install_hint.py, which this story wrote.
    Modules not importable: none.

    `make test` is green (`test: green`), because `vm/setup.sh` already holds the two lines from entry 14. `make lint` is green.

    Still open: the factory dropped the coder's entry-18 rewrite of the Description, because the work item is outside the coder's write paths. Criterion 2 therefore still says "unchanged", criterion 3 still says "one test", and the Interface still says "No earlier test changes". This tests stage cannot write the work item either. Someone with write access to the work item should bring those three places up to date.

    `lint`: lint: green (0.2 s)
    `test`: test: green (155.1 s)
21. factory: started doing as vm.
22. coder: Round 1: this round had no code to write. The reviewer's only finding in entry 16 was a duplicate test, and the tester already removed it in entry 20. I changed nothing in the working tree.

    What I built: `vm/setup.sh` stays as entry 14 left it. Lines 348 (`tools`) and 392 (`service`) are now the Interface's exact lines, single-quoted and sent with `>&2`. No install condition, step, other line or exit status changed. `make check` is green on this round (`test: green (157.1 s)`, `check: green`). That includes `tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy` (both rows) and the narrowed `tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned`.

    Main choice (unchanged since entry 14): I used single quotes because the text contains `"The rebuild after a merge"`. I rejected double quotes with `\"` escapes, because then the script's text would no longer match the Interface's line exactly, and that exact text is what criterion 1's test looks for.

    Refactor: I read the diff again (two echo lines in the script). There was nothing to change.

    What the journal changed: entry 8 (the human's leave to narrow `_install_conditions`) and entry 20 (criterion 3 now maps to the existing `tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu`) leave three places in `## Description` out of date:
    - The Interface's "No earlier test changes".
    - Criterion 2's "unchanged".
    - Criterion 3's "(one test)".

    The work item is outside my write paths, and the factory dropped my rewrite in round 0 (entry 18). So I left the Description alone, and it needs someone who may write it. The meaning of the task is the same.

    Noticed but not touched: criterion 5's docs are still open for the documenter. They are `docs/operator-guide.md` (*The two passes* and *The rebuild after a merge*, where the advice to remove the installed file must go) and the closing line in `docs/decisions.md`.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
23. factory: started review as vm.
24. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`, which covers `vm/setup.sh`, the new `tests/test_vm_setup_install_hint.py` and `tests/test_vm_setup_text.py`, against the work item. I checked the code against each criterion myself.

    no findings

    - Criterion 1: `tests/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy` has one row for `tools` and one for `service`. It runs over the `code` fixture (the script without comment lines), cut into steps by `vm_support.step_texts`. Each step's Interface line appears exactly once, on a `>&2` line. Only two lines of the script contain `differs from the checkout`, and both are the new lines.
    - The script change is only the two echo lines at `vm/setup.sh:348` and `vm/setup.sh:392`. They are single-quoted so they can hold the double-quoted section name, and they match the Interface text byte for byte. The install conditions and the `install` commands at 345 and 389 are untouched.
    - Criterion 2: the earlier test, with its narrowed helper, still finds those `install` lines inside the clone-or-missing `if` blocks.
    - Criterion 3: the existing `tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu` runs `sh -n` on the script.
    - Checks: the coder's `make check` was green (entry 22). The diff adds no `src/` change and no suppression markers. Criterion 5 still describes the docs work correctly.

    Description corrections. The Interface and criteria had not caught up with journal entries 8 and 20. The coder's rewrite was dropped because it is outside the coder's write paths (entry 18):
    - description corrected: Interface, "No earlier test changes (decision 23 …): … still finds …" -> one earlier test change, with the human's leave (entry 8): `_install_conditions` counts a line only when its command is `install` (`^\s*install\s`); the test keeps its name and its rule; no other earlier test changes.
    - description corrected: criterion 2, "the existing … test, unchanged" -> "the existing … test, its helper narrowed as the Interface says".
    - description corrected: criterion 3, "(one test)" -> "(the existing `tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu`)".

    Earlier tests:
    - `tests/test_vm_setup_text.py`: changed under the human's leave in journal entry 8. Only the `_install_conditions` filter changed, from `(?<![\w-])install\s` to `^\s*install\s`, and `ruff format` joined the comprehension onto one line. The test keeps its name and its rule, so the change stays within the leave.
