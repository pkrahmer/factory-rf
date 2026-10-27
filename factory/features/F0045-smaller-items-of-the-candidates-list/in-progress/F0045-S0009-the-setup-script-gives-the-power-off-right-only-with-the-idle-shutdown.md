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
  started_at: '2026-10-27T01:01:51.937422Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-27T01:01:51.932153Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-27T01:01:51.937422Z'
  stage: intake
---

# The setup script gives the power-off right only with the idle shutdown

## Description

S0008 (the factory powers its machine off after an idle stretch) makes the factory run `sudo -n /usr/bin/systemctl poweroff` when `FACTORY_IDLE_SHUTDOWN_MINUTES` is set; the user `factory` has no right to it on a machine `vm/setup.sh` made (F0043-S0003). This story gives the script one option, `--idle-shutdown <minutes>`, and one step, `poweroff`: with the option, the step writes one `sudoers` file that allows exactly that command, checked with `visudo -cf` as the steps `sudoers` and `caches` check theirs (F0043's decision 7, S0002), and the environment file gains the line `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`; without the option, the step removes the file if an earlier run wrote it, and the environment file holds no such line. So the right exists exactly while the option is used, and the factory's setting comes from the same run (decisions 9 and 12 of `feature.md`). What stays: every other option, step, file and line of the script and of `vm/factory.service`; the script still never starts or stops the service and never powers the machine off itself.

## Interface

No module under `src/factory/` changes. The coder changes `vm/setup.sh` (POSIX `sh`):

- Option `--idle-shutdown <minutes>`: the value is one or more ASCII digits with a value of at least 1; an option without its value, or a value that is not such a number (`0`, `x`, `-5`, `1.5`), prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2, before any step and before the root check, as every other argument fault; the usage names the option. Without the option the idle shutdown is off.
- Step `poweroff`, right after the step `caches` (S0002) and before the step `folders`, one line on standard output beginning `setup: poweroff: `:
  - with the option: `/etc/sudoers.d/factory-poweroff`, owner root, mode `0440`, holding exactly one rule, `factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff`, checked with `visudo -cf`; a failed check removes the file and exits 1, as the step `sudoers` does; the file is written only when its content differs;
  - without the option: `rm -f /etc/sudoers.d/factory-poweroff`, and the line says that the idle shutdown was not asked.
- The environment file `/srv/factory/<instance>/factory.env`: with the option, one more line after the line `XDG_RUNTIME_DIR=...`, the last one: `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`; without the option, no line of that name. Every other line is unchanged.
- The script runs `systemctl poweroff` nowhere: the words appear only in the rule.

Tests (the tester writes and changes them; the leave is decision 29 of `feature.md`): new rows or tests in F0043-S0003's `tests/test_vm_setup.py` (the runs) and `tests/test_vm_setup_text.py` (the text), or a new module at the tester's choice, for example `tests/test_vm_setup_idle_shutdown.py`, reading `vm/setup.sh` as those modules do; `STEPS` of `tests/vm_support.py` gains `poweroff` right after `caches`, and the rows that list the options the usage names gain `--idle-shutdown`.

## Acceptance criteria

1. The script stays valid: `sh -n vm/setup.sh` exits 0.
2. The option's faults and its accepted values (rows of one parametrized test, each run with `sh vm/setup.sh --device /dev/null --repository-url https://example.invalid/r.git <words>` in `tmp_path` with a stand-in `id` first on `PATH` that prints `1000`): `--idle-shutdown` without a value, `--idle-shutdown 0`, `--idle-shutdown x`, `--idle-shutdown -5` and `--idle-shutdown 1.5` each exit 2 with the first line of standard error beginning `setup.sh: ` and a line beginning `usage: setup.sh` after it, and print nothing on standard output; `--idle-shutdown 1` and `--idle-shutdown 30` each exit 2 with exactly `setup.sh: run as root` on standard error (the option was accepted; the root check comes after the options).
3. The usage (one test): `sh vm/setup.sh --help` exits 0 and its standard output holds `--idle-shutdown`.
4. The step's place and text (rows of one parametrized test over the script's text with its comment lines dropped, the step's text cut as F0043-S0003's criterion 4 cuts it): the first `setup: caches: `, the first `setup: poweroff: ` and the first `setup: folders: ` come in that order; the step `poweroff`'s text holds `/etc/sudoers.d/factory-poweroff`, `chmod 0440`, `visudo -cf` and `rm -f /etc/sudoers.d/factory-poweroff`; the script holds the rule `factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff` exactly once, inside the step `poweroff`; the words `systemctl poweroff` appear on no other line of the script.
5. The environment file's line (one test over the text with its comment lines dropped): `FACTORY_IDLE_SHUTDOWN_MINUTES=` appears exactly once, after the first `XDG_RUNTIME_DIR=` and before the first `factory@.service`; every name of `ENVIRONMENT` of `tests/test_vm_setup_text.py` still appears exactly once, in its order.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, `## The machine`, `### The script`: the option `--idle-shutdown <minutes>` with its rule, and the step `poweroff` in the numbered list of steps (what it writes or removes, and its line), the count of steps following; `### The idle shutdown` (written by S0008): how to turn it on and off with the script (run it again with or without the option, then `systemctl restart factory@<instance>`), and that the right is removed by a run without the option. `docs/decisions.md`: the entry "The machine powers itself off after an idle stretch, an option off by default" (S0008) gains one line on the right: one `sudoers` rule for `/usr/bin/systemctl poweroff`, written only with the option and removed without it (F0045-S0009). `docs/project-guide/`, `README.md`: none (no module changes).

## Smoke test

```bash
sh -n vm/setup.sh && echo syntax-ok
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
(cd "$d" && sh "$OLDPWD/vm/setup.sh" --device /dev/null --repository-url https://example.invalid/r.git --idle-shutdown 0 >out 2>err; echo "status $?"; head -1 err | grep -c '^setup.sh: '; wc -c < out)
grep -c 'factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff' vm/setup.sh
```
Expect: five lines: `syntax-ok`; `status 2`; `1`; `0`; `1`

## Journal

1. 2026-10-27 human: created.
2. factory: started intake as vm.
