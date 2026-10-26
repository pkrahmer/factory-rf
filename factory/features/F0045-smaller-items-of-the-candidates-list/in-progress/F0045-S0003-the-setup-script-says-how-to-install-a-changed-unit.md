---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-10-26T20:11:58.261426Z'
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
