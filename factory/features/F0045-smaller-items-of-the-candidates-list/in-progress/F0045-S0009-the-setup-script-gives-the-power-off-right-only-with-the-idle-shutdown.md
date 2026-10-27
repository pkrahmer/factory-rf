---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 474
comments_read: [6431120801]
handed_over: null
claim: null
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-27T01:02:15.888262Z'
  stage: intake
  run: 8ca06c368be54368a089cef29f704fbc
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-27T01:04:35.763018Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-27T01:04:53.582306Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-27T01:05:19.292937Z'
  stage: intake
  run: 90618514c63f403c978f3c65cddb33d3
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-27T01:05:41.426664Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-27T01:13:34.429846Z'
  stage: tests
  run: 1d30e4dbe4a749bca6d4c28f002bae94
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-27T01:13:54.810572Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-27T01:20:47.781000Z'
  stage: doing
  run: c7f4c3400afb4aa6ae3d085a3dbafe45
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-27T01:21:08.808867Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-27T01:22:18.537965Z'
  stage: review
  run: 5b6c4edfa96948ca98754284038ae045
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-27T01:22:39.238098Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-27T01:23:03.721214Z'
  stage: doing
  run: a99c137f3199460c9654b060d2a4e2df
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-27T01:23:24.464107Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-27T01:29:13.125796Z'
  stage: tests
  run: ca15ad1578e74049b54073a006cb4620
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-27T01:29:33.482299Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-27T01:35:37.549576Z'
  stage: doing
  run: ee6fbd0156304776a870618e84d9f640
---

# The setup script gives the power-off right only with the idle shutdown

## Description

S0008 (the factory powers its machine off after an idle stretch) makes the factory run `sudo -n /usr/bin/systemctl poweroff` when `FACTORY_IDLE_SHUTDOWN_MINUTES` is set; the user `factory` has no right to it on a machine `vm/setup.sh` made (F0043-S0003). This story gives the script one option, `--idle-shutdown <minutes>`, and one step, `poweroff`: with the option, the step writes one `sudoers` file that allows exactly that command, checked with `visudo -cf` as the steps `sudoers` and `caches` check theirs (F0043's decision 7, S0002), and the environment file gains the line `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`; without the option, the step removes the file if an earlier run wrote it, and the environment file holds no such line. So the right exists exactly while the option is used, and the factory's setting comes from the same run (decisions 9 and 12 of `feature.md`). What stays: every other option, step, file and line of the script and of `vm/factory.service`; the script still never starts or stops the service and never powers the machine off itself.

## Interface

No module under `src/factory/` changes. The coder changes `vm/setup.sh` (POSIX `sh`):

- Option `--idle-shutdown <minutes>`: the value is one or more ASCII digits with a value of at least 1; an option without its value, or a value that is not such a number (`0`, `x`, `-5`, `1.5`), prints `setup.sh: <what is wrong>` and the usage to standard error and exits 2, before any step and before the root check, as every other argument fault; the usage names the option. Without the option the idle shutdown is off.
- Step `poweroff`, right after the step `caches` (S0002) and before the step `folders`, one line on standard output beginning `setup: poweroff: `:
  - with the option: `/etc/sudoers.d/factory-poweroff`, owner root, mode `0440`, holding exactly one rule, `factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff`, checked with `visudo -cf`; a failed check removes the file and exits 1, as the step `sudoers` does; the file is written only when its content differs;
  - without the option: `rm -f /etc/sudoers.d/factory-poweroff`, and the line is exactly `setup: poweroff: not asked; the factory gets no power-off right`.
- The environment file `/srv/factory/<instance>/factory.env`: with the option, one more line after the line `XDG_RUNTIME_DIR=...`, the last one: `FACTORY_IDLE_SHUTDOWN_MINUTES=<minutes>`; without the option, no line of that name. Every other line is unchanged.
- The script runs `systemctl poweroff` nowhere: the words appear only in the rule.

Tests (the tester writes and changes them; the leave is decision 29 of `feature.md`): new rows or tests in F0043-S0003's `tests/test_vm_setup.py` (the runs) and `tests/test_vm_setup_text.py` (the text), or a new module at the tester's choice, for example `tests/test_vm_setup_idle_shutdown.py`, reading `vm/setup.sh` as those modules do; `STEPS` of `tests/vm_support.py` gains `poweroff` right after `caches`, and the rows that list the options the usage names gain `--idle-shutdown`.

## Acceptance criteria

1. The script stays valid: `sh -n vm/setup.sh` exits 0.
2. The option's faults and its accepted values (rows of one parametrized test, each run with `sh vm/setup.sh --device /dev/null --repository-url https://example.invalid/r.git <words>` in `tmp_path` with a stand-in `id` first on `PATH` that prints `1000`): `--idle-shutdown` without a value, `--idle-shutdown 0`, `--idle-shutdown x`, `--idle-shutdown -5` and `--idle-shutdown 1.5` each exit 2 with the first line of standard error beginning `setup.sh: ` and a line beginning `usage: setup.sh` after it, and print nothing on standard output; `--idle-shutdown 1` and `--idle-shutdown 30` each exit 2 with exactly `setup.sh: run as root` on standard error (the option was accepted; the root check comes after the options).
3. The usage (one test): `sh vm/setup.sh --help` exits 0 and its standard output holds `--idle-shutdown`.
4. The step's place and text (rows of one parametrized test over the script's text with its comment lines dropped, the step's text cut as F0043-S0003's criterion 4 cuts it): the first `setup: caches: `, the first `setup: poweroff: ` and the first `setup: folders: ` come in that order; the step `poweroff`'s text holds `/etc/sudoers.d/factory-poweroff`, `chmod 0440`, `visudo -cf` and `rm -f /etc/sudoers.d/factory-poweroff`; the script holds the rule `factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff` exactly once, inside the step `poweroff`; the words `systemctl poweroff` appear on no other line of the script.
5. The environment file's line (one test over the text with its comment lines dropped): `FACTORY_IDLE_SHUTDOWN_MINUTES=` appears exactly once, after the first `XDG_RUNTIME_DIR=` and before the first `factory@.service`; every name of `ENVIRONMENT` of `tests/test_vm_setup_text.py` still appears exactly once, in its order.
6. The refused check (one test over the step's text, cut as in criterion 4): the branch of a failed `visudo -cf` runs `rm -f /etc/sudoers.d/factory-poweroff`, prints its message with `>&2` and ends `exit 1`.
7. The write (rows of one parametrized test over the step's text): the step compares the file with its wanted text before writing and reports `found` or `wrote`; the file is written by root with mode `0440` (the step's `chmod 0440` or `install -m 0440` on `/etc/sudoers.d/factory-poweroff`).
8. The line without the option (one test over the step's text): it holds exactly `setup: poweroff: not asked; the factory gets no power-off right`.
9. The environment file's line is the last line the script writes to the file, and it is written only inside the `--idle-shutdown` branch (one test over the text with its comment lines dropped).
10. The empty value (a row of criterion 2's parametrized test, run the same way): `--idle-shutdown ''` (a value of no digits, which "one or more ASCII digits" refuses) exits 2 with the first line of standard error beginning `setup.sh: ` and a line beginning `usage: setup.sh` after it, and prints nothing on standard output.
11. `make check` stays green.
12. docs: `docs/operator-guide.md`, `## The machine`, `### The script`: the option `--idle-shutdown <minutes>` with its rule, and the step `poweroff` in the numbered list of steps (what it writes or removes, and its line), the count of steps following; `### The idle shutdown` (written by S0008): how to turn it on and off with the script (run it again with or without the option, then `systemctl restart factory@<instance>`), and that the right is removed by a run without the option. `docs/decisions.md`: the entry "The machine powers itself off after an idle stretch, an option off by default" (S0008) gains one line on the right: one `sudoers` rule for `/usr/bin/systemctl poweroff`, written only with the option and removed without it (F0045-S0009). `docs/project-guide/`, `README.md`: none (no module changes).

## Smoke test

```bash
sh -n vm/setup.sh && echo syntax-ok
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
(cd "$d" && sh "$OLDPWD/vm/setup.sh" --device /dev/null --repository-url https://example.invalid/r.git --idle-shutdown 0 >out 2>err; echo "status $?"; head -1 err | grep -c '^setup.sh: '; wc -c < out)
grep -v '^[[:space:]]*#' vm/setup.sh | grep -c 'factory ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff'
```
Expect: five lines: `syntax-ok`; `status 2`; `1`; `0`; `1`

## Journal

1. 2026-10-27 human: created.
2. factory: started intake as vm.
3. intake: 1. The Interface says "a failed check removes the file and exits 1, as the step `sudoers` does". No criterion tests that failing side. Criterion 4 only checks that the text holds `visudo -cf`. Should a criterion be added (for example a run with a stand-in `visudo` that fails, expecting exit 1 and no `/etc/sudoers.d/factory-poweroff`), or should the clause be dropped from the Interface? I would add the criterion if the existing runs in `tests/test_vm_setup.py` can stand in `visudo` and the sudoers directory; otherwise I would reword the clause so that criterion 4 can test it as text (the step's text holds a `rm -f` after the failed `visudo -cf`).
   2. The Interface says "the file is written only when its content differs" and "owner root, mode `0440`". Neither has a criterion. Criterion 4 only checks that `chmod 0440` appears, and nothing checks the owner or the compare-before-write. I would add one text criterion for each, or a run criterion if the runs can reach them.
   3. The Interface says that without the option "the line says that the idle shutdown was not asked". No criterion pins that line, so two coders will word it two ways. Which words should the line hold, or should a criterion require only the prefix `setup: poweroff: `?
   4. The Interface says the environment file's new line is "the last one", after `XDG_RUNTIME_DIR=...`. Criterion 5 only requires it after the first `XDG_RUNTIME_DIR=` and before the first `factory@.service`. That does not test "last". Should it say "the last line the script writes to the file"? Also, the Interface says that without the option the environment file holds no such line. No criterion covers that side. Text can show only that the line is written conditionally. Should one be added, for example that the line is inside the `--idle-shutdown` branch?
   5. The smoke test's last command is `grep -c ... vm/setup.sh`, and the Expect says `1`. That grep counts comment lines too, while criterion 4 drops them. A comment that quotes the rule would make the count 2. Should the command drop comment lines (`grep -v '^[[:space:]]*#' vm/setup.sh | grep -c ...`), or should the Interface say that no comment may quote the rule?
4. 2026-10-27 human: All as text criteria, the way F0045-S0002's step `caches` was pinned:
   1. Add a text criterion: the step's refused branch runs `rm -f /etc/sudoers.d/factory-poweroff`, prints its message with `>&2` and ends `exit 1`. No stand-in `visudo` run.
   2. Add text criteria: the step compares the file with its wanted text before writing and reports `found` or `wrote`; the file is written by root with mode `0440` (the step's `chmod 0440` or `install -m 0440` on that path).
   3. The line is exactly `setup: poweroff: not asked; the factory gets no power-off right` (as the step `sudoers` says `not asked`); a criterion pins it.
   4. Yes to both: the new line is the last line the script writes to the environment file, and it is written only inside the `--idle-shutdown` branch (text criterion).
   5. The smoke command drops comment lines: `grep -v '^[[:space:]]*#' vm/setup.sh | grep -c ...`; the Expect stays `1`.
5. factory: started intake as vm.
6. intake: accepted, after carrying in the human's answer (journal entry 4) as the human's own edit; nothing of mine added.
   - Interface: concrete. It names `vm/setup.sh` (POSIX sh), the option with its value rule and exit 2 before the root check, the step `poweroff` between `caches` and `folders`, the file's path, owner, mode and exact rule, the environment line, and the ban on `systemctl poweroff` outside the rule. Per answer 3 I wrote the exact no-option line into the Interface: `setup: poweroff: not asked; the factory gets no power-off right`.
   - Criteria: each is testable by one test function. Every Interface rule now has its own criterion on both sides. Faults and accepted values are criterion 2, the usage is 3, the step's place and text are 4. The refused check is the new 6 (`rm -f`, `>&2`, `exit 1`, per answer 1). Compare-before-write with `found`/`wrote`, and root with mode 0440, are the new 7 (answer 2). The exact not-asked line is the new 8 (answer 3). The env line being last and only inside the option's branch is the new 9 (answer 4). The env line's place after `XDG_RUNTIME_DIR=` is criterion 5. `make check` and `docs:` are now 10 and 11, still last (R5).
   - Smoke test: runnable. Per answer 5 the last command now drops comment lines before `grep -c`. The Expect line still has five checkable lines. There is no pytest command, so there is no `-q` issue.
   - Architecture: no module under `src/factory/` changes, and the layers are not touched. The change is in `vm/setup.sh`, the coder's write path, and its tests follow F0043-S0003's text-test pattern.
   - Scope: inside S0009 of the feature (decisions 9 and 12). The test changes have the human's leave in decision 29. It adds no start or stop of the service and no power-off by the script. Nothing from "Out of scope" is touched.
7. factory: started tests as vm.
8. tester: Wrote the tests for the option `--idle-shutdown` and the step `poweroff`. They are red on purpose.

   Criterion → test:
   - criterion 1: tests/test_vm_setup.py::test_the_script_parses_and_starts_with_its_shebang_and_set_eu (existing test, unchanged; it runs `sh -n`)
   - criterion 2: tests/test_vm_setup_idle_shutdown.py::test_the_idle_shutdown_takes_a_whole_number_of_minutes_of_at_least_one (rows: without-value, zero, letter, negative, fraction, one, thirty)
   - criterion 3: tests/test_vm_setup.py::test_help_prints_the_usage_to_standard_output_and_exits_0 (`OPTIONS` gained `--idle-shutdown`, so test_an_argument_fault_prints_the_usage_and_exits_2 now also checks that the usage line names the option)
   - criterion 4: tests/test_vm_setup_idle_shutdown.py::test_the_poweroff_step_follows_caches_and_writes_or_removes_its_rule
   - criterion 5: tests/test_vm_setup_idle_shutdown.py::test_the_idle_shutdown_setting_is_the_environment_file_s_line_after_the_others
   - criterion 6: tests/test_vm_setup_idle_shutdown.py::test_a_refused_visudo_check_removes_the_poweroff_rule_and_ends_the_script
   - criterion 7: tests/test_vm_setup_idle_shutdown.py::test_the_poweroff_step_writes_its_rule_only_when_its_text_differs (rows: compared-before-written, wrote, found, root-0440)
   - criterion 8: tests/test_vm_setup_idle_shutdown.py::test_without_the_option_the_step_says_the_factory_gets_no_power_off_right
   - criterion 9: tests/test_vm_setup_idle_shutdown.py::test_the_idle_shutdown_setting_is_written_last_and_only_with_the_option
   - criteria 10 and 11: no test (`make check`; the docs stage)

   How criteria 7 and 9 are read as text:
   - **Criterion 7:** a "found" line and a "wrote <path>" text must both be in the step, as for `caches`. "By root" means the step's write lines use neither `runuser` nor `as_factory`.
   - **Criterion 9:** the variable is the one assigned in the `--idle-shutdown)` case arm. Either the `if` the line is indented under tests that variable, or the line itself tests it before the name. After the line, the step `environment` assigns no other upper-case name.

   Files created: tests/test_vm_setup_idle_shutdown.py.

   Earlier test files changed:
   - Interface leave (decision 29 of `feature.md`):
     - tests/vm_support.py: `STEPS` gained `poweroff` after `caches`.
     - tests/test_vm_setup.py: `OPTIONS` gained `--idle-shutdown`.
   - Standing leave to move a shared test helper (CLAUDE.md, *Tests*). These helpers moved to tests/vm_support.py:
     - from tests/test_vm_setup_text.py: `VALUE_END`, `ENVIRONMENT`, `_name_positions` (now `name_positions`), `_indent` (now `indent`), `_enclosing_if` (now `enclosing_if`). That file now imports them.
     - from tests/test_vm_setup_caches.py: `COMPARISONS`, `_compares` (now `compares`), `_writes` (now `writes_path`).

     Every earlier test keeps its name and checks the same thing.

   Test run (`make test`, once): it fails as intended.
   - Every test that cuts the script into steps errors with "no 'setup: poweroff: ' text", because the step does not exist yet.
   - The run rows of criterion 2 fail on their results.
   - No module failed to import.

   `make lint`: green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/test_vm_setup_text.py::test_the_folders_step_refuses_a_link_at_state_or_repo[exit-1] - AssertionError: no 'setup: poweroff: ' text
9. factory: started doing as vm.
10. coder: `vm/setup.sh` now has the option `--idle-shutdown <minutes>` and the step `poweroff`, and `make check` is green. I changed no other file and no test.

    What I built:
    - **Option:** `--idle-shutdown <minutes>` is in the usage line and the option list. The case arm reads `need_value "$@"; need_minutes "$1" "$2"; idle_shutdown=$2`. The new function `need_minutes` sits beside `need_value` and refuses a value that is not all digits, or is all zeros, through `fault` (exit 2, before the root check). With no option, `idle_shutdown` stays empty and the idle shutdown is off.
    - **Step `poweroff`:** it runs between `caches` and `folders` and copies the pattern of `caches`.
      - With the option: it stages the one rule, compares it with `unchanged`, then runs `cp`, `chmod 0440` and `visudo -cf`. If the check fails, it runs `rm -f`, prints a message to stderr with `>&2` and ends `exit 1`. It reports `wrote` or `found ... unchanged`.
      - Without the option: it runs `rm -f /etc/sudoers.d/factory-poweroff` and prints exactly `setup: poweroff: not asked; the factory gets no power-off right`.
    - **Environment file:** after the staged heredoc, `if [ -n "$idle_shutdown" ]` appends `FACTORY_IDLE_SHUTDOWN_MINUTES=$idle_shutdown` to the staging file. So it is the last line, written only with the option, and every other line is unchanged.
    - **Checks:** `sh -n` passes. The smoke test gives `status 2`; the first stderr line starts with `setup.sh: `; stdout is 0 bytes; the rule count is `1`.

    Main choice: I check the minutes in the case arm, through `need_minutes`, so an empty value such as `--idle-shutdown ""` is refused too. I rejected checking after the loop with `[ -n "$idle_shutdown" ]`. That check would read an empty value as "off" and accept it silently.

    Refactor: I read the diff and found nothing to change. The step is a copy of the `caches` pattern on purpose: the criteria read each step's text, so a shared function for "write a sudoers file" would change three steps and is beyond this story.

    Noticed, not touched: the three steps `sudoers`, `caches` and `poweroff` now repeat the same five lines (copy, chmod, visudo, rm, exit). Merging them would make a story of its own.

    Journal: the human's answer (entry 4) was already carried into the Description by intake, so I did not rewrite it.

    `check`: check: green
    `duplicates`: duplicates: 2 new, 42 known, 0 gone
11. factory: started review as vm.
12. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (vm/setup.sh, tests/test_vm_setup_idle_shutdown.py, tests/vm_support.py, tests/test_vm_setup_text.py, tests/test_vm_setup_caches.py, tests/test_vm_setup.py) against the work item. Criteria 1 to 9 each have a test that checks what the criterion says. The limit "at least 1" is tested on both sides (`0` refused, `1` accepted). The step `poweroff` copies the pattern of the step `caches` (stage, `unchanged`/`cmp`, `cp`, `chmod 0440`, `visudo -cf`, and on refusal `rm -f`, `>&2`, `exit 1`). The environment line is appended to the staged file only under `if [ -n "$idle_shutdown" ]`. The coder's `make check` was green (entry 10). The script has three copies of the sudoers block. I do not count that as a finding: criteria 4, 6 and 7 read the block's text inside each step, so a shared function would break them.

    1. criterion 10 added: it needs its test. Location: vm/setup.sh `need_minutes` (the `''|*[!0-9]*` arm) and tests/test_vm_setup_idle_shutdown.py::test_the_idle_shutdown_takes_a_whole_number_of_minutes_of_at_least_one. The problem: the Interface's rule "one or more ASCII digits" is not tested on its zero-digit side. The coder built the refusal of an empty value on purpose (entry 10), but no criterion or row checks `--idle-shutdown ''`. The "without-value" row covers a missing word, not a word with no digits. The fix: add the row `["--idle-shutdown", ""]` with `accepted=False` to that parametrized test. Criteria 10 and 11 are renumbered to 11 and 12.

    Earlier tests:
    - tests/test_vm_setup.py: the human's leave (the story's Interface, decision 29 of `feature.md`). `OPTIONS` gained `--idle-shutdown`.
    - tests/vm_support.py: the human's leave (the story's Interface, decision 29 of `feature.md`) for `STEPS` gaining `poweroff`. The standing leave to move a shared test helper covers the added `VALUE_END`, `ENVIRONMENT`, `COMPARISONS`, `name_positions`, `indent`, `enclosing_if`, `compares` and `writes_path`. Their bodies are unchanged.
    - tests/test_vm_setup_text.py: the standing leave to move a shared test helper. `VALUE_END`, `ENVIRONMENT`, `_name_positions`, `_indent` and `_enclosing_if` moved to tests/vm_support.py. Every test keeps its name and what it checks.
    - tests/test_vm_setup_caches.py: the standing leave to move a shared test helper. `COMPARISONS`, `_compares` and `_writes` moved to tests/vm_support.py (`_writes` is now `writes_path`, same body). Every test keeps its name and what it checks.
13. factory: started doing as vm.
14. coder: Round 1: the reviewer added only a test. I changed no code and no test.

    The reviewer's finding 1 (journal entry 12) added criterion 10: `--idle-shutdown ''` exits 2. Its first line of standard error begins `setup.sh: `, a line beginning `usage: setup.sh` follows it, and nothing is printed on standard output. `vm/setup.sh` already behaves this way. `need_minutes` refuses an empty value through its `''|*[!0-9]*` arm, which calls `fault`. I ran it once by hand, the way criterion 2 runs the script: in a temporary directory, with a stand-in `id` that prints `1000`. It gave status 2, then `setup.sh: --idle-shutdown takes a whole number of minutes, not `, then the usage, and 0 bytes on standard output.

    For the tester: add the row `pytest.param(["--idle-shutdown", ""], False, id="empty")` to `tests/test_vm_setup_idle_shutdown.py::test_the_idle_shutdown_takes_a_whole_number_of_minutes_of_at_least_one`.

    What I built: nothing new this round. The work in `vm/setup.sh` is unchanged from journal entry 10. The main choice still stands: the minutes are checked in the option's case arm through `need_minutes`, so an empty value is refused. I rejected checking after the loop, because that check would read an empty value as "off" and accept it.

    The Description already lists criterion 10, so I did not rewrite it.

    Noticed, not touched:
    - The fault message for an empty value ends with a trailing space (`not `). It is harmless, and no criterion pins it.
    - The three copies of the sudoers block (in the steps `sudoers`, `caches` and `poweroff`) remain. Merging them is a story of its own (journal entry 10).

    I did not run `make check` this round, because nothing changed since the green run in journal entry 10.
15. factory: started tests as vm.
16. tester: Approved test change (coder's journal entry 14; reviewer's finding 1 in entry 12, which added criterion 10): I added the row `pytest.param(["--idle-shutdown", ""], False, id="empty")` to `tests/test_vm_setup_idle_shutdown.py::test_the_idle_shutdown_takes_a_whole_number_of_minutes_of_at_least_one`. It sits right after the row `without-value`. Nothing else changed.

    Why: the Interface says the value is "one or more ASCII digits". Until now no row tested the side with no digits. A missing word (`without-value`) is a different case from an empty word.

    Criterion → test:
    - criterion 10: tests/test_vm_setup_idle_shutdown.py::test_the_idle_shutdown_takes_a_whole_number_of_minutes_of_at_least_one[empty]. It runs the same way as criterion 2's rows and expects exit 2, the first stderr line beginning `setup.sh: `, a line beginning `usage: setup.sh` after it, and empty stdout.
    - Criteria 1 to 9: unchanged from journal entry 8.

    Files created: none. The file changed is tests/test_vm_setup_idle_shutdown.py, this story's own module.

    Modules the test run could not import: none.

    `make test` (once): green, `test: green (164.6 s)`. The new row passes, because `vm/setup.sh` already refuses an empty value through `need_minutes`.

    `lint`: lint: green (0.2 s)
    `test`: test: green (163.1 s)
17. factory: started doing as vm.
18. coder: Round 1, after the tester added the row for criterion 10 (journal entry 16). I changed no code and no test this round. The only finding was the reviewer's finding 1 in journal entry 12, which asked for that test. It is now in place, and `vm/setup.sh` already passes it.

    What I built: nothing new this round. The work in `vm/setup.sh` is still what journal entry 10 describes:
    - the option `--idle-shutdown <minutes>`, checked by `need_minutes` in its case arm;
    - the step `poweroff`, between `caches` and `folders`, which writes or removes `/etc/sudoers.d/factory-poweroff`;
    - the line `FACTORY_IDLE_SHUTDOWN_MINUTES=` added to the environment file only with the option.

    Main choice, still as in entry 10: the minutes are checked in the option's case arm, so an empty value is refused with exit 2. I rejected checking after the argument loop, because that check would read an empty value as "off" and accept it without a word.

    Refactor: there was no new diff this round, so there was nothing to change.

    The journal changed nothing in the task's meaning that the Description does not already say. It already lists criterion 10, so I did not rewrite it.

    Noticed, not touched:
    - The fault message for an empty value ends with a trailing space (`... not `). No criterion pins that text.
    - The steps `sudoers`, `caches` and `poweroff` each hold their own copy of the same sudoers block. Merging them would be a story of its own.

    `check`: check: green (`make check` run this round; test: green (165.0 s))

    `check`: check: green
    `duplicates`: duplicates: 2 new, 42 known, 0 gone
