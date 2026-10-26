---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 468
comments_read: [6426528724]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-10-26T20:26:45.968641Z'
  lease_duration: 60
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

Tests (the tester writes them): a new test at the tester's choice, for example `tests/test_vm_setup_install_hint.py`, reading the script through `tests/vm_support.py`. No earlier test changes (decision 23 of `feature.md`): `tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned` still finds `differs from the checkout; not installed` in both steps.

## Acceptance criteria

1. The two lines (rows of one parametrized test over the script's text with its comment lines dropped, the steps cut as `tests/vm_support.py` cuts them, one row per step `tools` and `service`): the step's text holds its line of the Interface exactly once, on a line that sends it to standard error (`>&2`), and no other line of the script holds `differs from the checkout`.
2. The rule is unchanged (the existing `tests/test_vm_setup_text.py::test_the_checkout_files_are_installed_only_in_the_run_that_cloned`, unchanged): each of the two files is installed only under the condition that the run cloned or the installed file is missing.
3. The script stays valid (one test): `sh -n vm/setup.sh` exits 0.
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
