---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 461
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-26T15:58:59.323803Z'
  lease_duration: 60
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
