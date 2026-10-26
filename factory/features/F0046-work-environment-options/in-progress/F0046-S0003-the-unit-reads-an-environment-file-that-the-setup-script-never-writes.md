---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 461
comments_read: [6420707346, 6420833778]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T15:58:19.805370Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T15:58:19.810836Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T15:58:38.008996Z'
  stage: intake
  run: 089113d3ed59492e90a50c7694787463
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T15:58:59.323803Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-10-26T15:59:47.489230Z'
  stage: tests
  run: 30d92d476e554ddc807b61fb6ec0b861
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-26T16:01:06.465968Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-26T16:01:24.230072Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-26T16:05:27.041476Z'
  stage: tests
  run: 2d2ef23351dd49b7b3e8c4d19496b520
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-26T16:06:45.613841Z'
  stage: tests
---

# The unit reads an environment file that the setup script never writes

## Description

`vm/setup.sh` rewrites `/srv/factory/<instance>/factory.env` at every run, from its arguments and the pins of `vm/Dockerfile`, and an edit by hand is lost at the next run. An operator who needs values the script does not know (a model map for a company's proxy, the path of a provider file, the proxy names of S0002) has no place for them. This story adds one: the unit `vm/factory.service` reads `/srv/factory/%i/factory.local.env` after `factory.env`, optionally, so a value in it wins and its absence is no fault. The script never creates, changes or removes that file, and says so in its closing text. Unchanged: every variable the script writes, the unit's other lines, the script's steps and their order, and every run of the script on a machine without the file. Nothing under `src/` changes.

## Interface

No module under `src/factory/` changes. The coder changes `vm/factory.service` and `vm/setup.sh`.

`vm/factory.service`, section `[Service]`: the line `EnvironmentFile=/srv/factory/%i/factory.env` is followed by the line `EnvironmentFile=-/srv/factory/%i/factory.local.env`. No other line changes.

`vm/setup.sh`: the final `setup: done:` line is followed by one more line, `setup: local: <instance folder>/factory.local.env is yours: the script never writes it; the unit reads it after factory.env`, printed to standard output with the folder of the run's `--instance`. No step creates, reads, changes or removes the file, and the thirteen step names and their order stay as they are.

Tests (the tester writes them): `tests/test_vm_local_environment.py`, through `tests/vm_support.py` (`SERVICE`, `setup_code`, `run_setup`).

## Acceptance criteria

1. `vm/factory.service` holds exactly two `EnvironmentFile=` lines, in this order: `EnvironmentFile=/srv/factory/%i/factory.env` and `EnvironmentFile=-/srv/factory/%i/factory.local.env`, and every other line is as before.
2. The code of `vm/setup.sh` (`setup_code`) names `factory.local.env` only in the closing line and in no command: no `rm`, `cp`, `install`, `tee`, `touch`, redirection or `stage` mentions it (rows of one test, one per command word).
3. A run of the script that ends in `setup: done:` prints the `setup: local:` line after it, with the instance's folder; a run with `--instance other` names `/srv/factory/other/factory.local.env`.
4. A file `factory.local.env` that exists in the instance's folder before a run is byte-identical after it, and a run without the file leaves none (the run in a temporary folder through `run_setup`).
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, *The environment file*: the second file, its order, that a value in it wins, that it is optional and that the script never writes it; the layout table of `/srv/factory/<instance>` gains the row `factory.local.env`. `docs/decisions.md`: an entry *The operator's own environment file*, from the feature's decision 8. `README.md` and `docs/project-guide/`: none.

## Smoke test

```bash
grep -n '^EnvironmentFile=' vm/factory.service
```
Expect: two lines, `EnvironmentFile=/srv/factory/%i/factory.env` and `EnvironmentFile=-/srv/factory/%i/factory.local.env`, in this order

```bash
grep -c 'factory.local.env' vm/setup.sh
```
Expect: `1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names the two files to change (`vm/factory.service` `[Service]`, `vm/setup.sh`), the exact unit line, the exact closing line and the helpers (`SERVICE`, `setup_code`, `run_setup` exist in `tests/vm_support.py`); no `src/` module changes.
   Criteria: 1 and 2 are static checks, 2 with one row per command word; 3 covers the default and `--instance other`; 4 covers the present and absent file; every rule has its failing side (a second or misplaced EnvironmentFile line, a command that mentions the file, a changed or created file). Criterion 5 and the docs criterion are the closing ones.
   Smoke test: both commands are runnable. Neither runs pytest, so the `-q` rule doesn't apply. Each `Expect:` is checkable: the two ordered lines, and a count of 1. The count holds because no line of `vm/setup.sh` names the file today and the story adds one line.
   Architecture: only `vm/` files change, which the coder's write paths allow. The layers are untouched.
   Scope: it matches the feature's S0003 and decision 8 (read after `factory.env`, optional with `-`). Nothing falls under "Out of scope".
4. factory: started tests as vm.
5. tester: Question on criteria 3 and 4 before I write any test. As written, they can't be run in a test, and I'd have to choose the method myself.

   Both ask for "a run of the script that ends in `setup: done:`", done "in a temporary folder through `run_setup`". But `vm/setup.sh` hard-codes the instance folder as `base=/srv/factory/$instance`. It also refuses to run unless `id -u` says root, and its thirteen steps call apt-get, dpkg-query, zpool, zfs, useradd, loginctl, runuser, systemctl, visudo, install, git and uv. It writes under `/etc/sudoers.d`, `/etc/systemd/system` and `/home/factory`. `run_setup` only sets the working directory and `PATH`, so the run never reaches the steps unless it is root on a real machine. Even then, the file under test sits in `/srv/factory/<instance>`, outside `tmp_path`. No existing test runs the script past its root check (`tests/test_vm_setup.py`).

   Options:
   A. Run only the script's closing lines. Take the code from the `setup: done:` printf to the end of `setup_code()` and run it with `sh` in `tmp_path` with `instance=vm` and `instance=other`. This is how `tests/test_vm_setup_writes.py` already runs `function_text` pieces. Criterion 3 then checks that the `setup: local:` line follows the `setup: done:` line on stdout and names `/srv/factory/<instance>/factory.local.env`. For criterion 4, the tail runs with a `factory.local.env` in `tmp_path` (it stays byte-identical) and without one (none appears). Criterion 2's static rows remain the real check that no step touches the file.
   B. Run the full script on a copy. A stand-in on `PATH` replaces each of the commands above, and `/srv/factory`, `/etc` and `/home/factory` are rewritten into `tmp_path`. This is a faithful run, but it means many stand-ins and a rewritten script. It is brittle, and the tests would pin the internals of every step.
   C. Reword criteria 3 and 4 as static checks: the closing line's text in `setup_code()`, plus criterion 2. Drop the "run" wording.

   I'd choose A: it runs the real closing text and stays inside `tmp_path`. In its criterion 4 the instance folder is `tmp_path` standing in for `/srv/factory/<instance>`.

   Criteria 1 and 2 are clear, and I'll write them with the others once this is answered. No files were created in this stage.
6. 2026-10-26 human: A, as you describe it: run the script's closing text (from the `setup: done:` printf to the end of `setup_code()`) with `sh` in `tmp_path`, for `instance=vm` and `instance=other`; `tmp_path` stands in for `/srv/factory/<instance>` in criterion 4. Criterion 2's static rows stay the check that no step touches the file. Read criteria 3 and 4 that way.
7. factory: started tests as vm.
8. tester: The tests for every criterion are written, as the answer in entry 6 asked. They are in the working tree, but I can't hand forward yet: another story's test will fail as soon as the coder adds the unit line that criterion 1 requires.

   The conflict: `tests/test_vm_service.py::test_each_section_holds_exactly_its_keys[service]` reads the unit with `configparser` (`strict=False`) and expects exactly one `("EnvironmentFile", "/srv/factory/%i/factory.env")`. With the second line `EnvironmentFile=-/srv/factory/%i/factory.local.env`, that parser keeps only the last value. The row then fails, so `make check` (criterion 5) can't go green. The coder may not edit tests, and the standing leave doesn't cover this change, so it needs your word.

   Options:
   A. In that test's `service` row, leave `EnvironmentFile` out of the expected list and skip `EnvironmentFile` keys in `[Service]`, as it already does for `Description` in `[Unit]`. `test_the_unit_reads_the_local_file_after_the_environment_file_and_nothing_else` in the new file then pins both lines and their order.
   B. Change the row's expected value to `-/srv/factory/%i/factory.local.env`. That is what `configparser` keeps, but it reads as if the unit had only that one file.
   C. Leave the test as it is and drop or reword criterion 1. That goes against the story.

   I'd choose A. If you agree, I'll make exactly that change in `tests/test_vm_service.py`.

   Mapping, per entry 6 (3 and 4 run the script's closing text, from the `setup: done:` printf to the end of `setup_code()`, with `sh` in `tmp_path`):
   criterion 1: tests/test_vm_local_environment.py::test_the_unit_reads_the_local_file_after_the_environment_file_and_nothing_else (the two lines in order, and the whole unit text pinned)
   criterion 2: tests/test_vm_local_environment.py::test_the_script_names_the_local_file_only_in_its_closing_line, and tests/test_vm_local_environment.py::test_no_command_of_the_script_mentions_the_local_file (rows rm, cp, install, tee, touch, redirection, stage)
   criterion 3: tests/test_vm_local_environment.py::test_the_closing_text_names_the_instance_s_local_file_after_done (rows vm, other; `base=/srv/factory/<instance>`)
   criterion 4: tests/test_vm_local_environment.py::test_the_closing_text_leaves_the_local_file_as_it_found_it (rows present, absent; `base` and cwd are `tmp_path`, standing in for the instance folder)

   Created: tests/test_vm_local_environment.py. No earlier test file was changed.

   `make test` (one run): red as intended. It failed on the unit test, the closing-line-mention test and both closing-text rows, each on a wrong result (no `setup: local:` line, one `EnvironmentFile=` line). After that run I made one fix that the run did not cover: the closing-text test took the last two output lines by index, so the failure would have been an `IndexError`. It now pads the output so the failure is an assertion. The command-word rows and both criterion-4 rows already pass, because today nothing names or touches the file; they guard against the change rather than drive it.

   `make lint`: green. No module failed to import, since nothing under `src/` is involved.
9. 2026-10-26 human: A: in `tests/test_vm_service.py`, the `service` row leaves `EnvironmentFile` out of its expected keys and skips `EnvironmentFile` in `[Service]`, as it does for `Description` in `[Unit]`; the new test pins both lines and their order. That earlier test may change only that way.
