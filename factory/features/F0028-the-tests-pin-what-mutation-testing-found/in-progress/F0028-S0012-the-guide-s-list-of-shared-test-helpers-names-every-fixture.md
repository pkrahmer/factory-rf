# The guide's list of shared test helpers names every fixture

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0028-S0011 gave the project guide's index, `docs/project-guide/README.md`, a section *Shared test helpers*, so that a tester finds a shared helper before writing a copy of it. It names every module `tests/*.py` whose name does not start with `test_`. But its line for `conftest.py` lists only 11 of the 25 fixtures `tests/conftest.py` defines, and the list reads as if it were complete. It leaves out `reopened_tmp_path`, `group_umask`, `local_settings`, `probe_settings`, `compose_service`, `hosted_environment`, `boundaries`, `definition`, `installed_agents`, `walk`, `layout`, `image_layout`, `records` and `recorder`. Among them are `walk`, `installed_agents` and `boundaries`, which F0028's own application stories built on. The section also does not name the one conftest below the root, `tests/application/handlers/conftest.py`, with its fixtures `snapshot_of`, `state_with`, `event_of`, `pull_request` and `work_item`. F0028's decision 13 names it as a shared place. A tester who reads the list today could write a second `walk` or `event_of`, which is the copy the section is meant to prevent. This story is for the tester and the reviewer. It completes the `conftest.py` line and adds a line for the handlers' conftest. The code, the tests and the other documents stay as they are. It changes no behaviour, so it has no criterion of its own beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The documenter checks against the functions decorated with `@pytest.fixture` in `tests/conftest.py` and `tests/application/handlers/conftest.py`, and their docstrings.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide/README.md`, *Shared test helpers*. The line ``- `conftest.py`:`` names every fixture of `tests/conftest.py` in backticks, the autouse `reopened_tmp_path` included, with what each holds where its name does not say it. A new line ``- `application/handlers/conftest.py`:`` names every fixture of `tests/application/handlers/conftest.py` in backticks, the same way, and says that they serve the handlers' tests under `tests/application/handlers/`. Its `work_item` is a published work item of the handlers' tests, not the root's started story. The section's opening paragraph adds one sentence: a story that adds a fixture to either conftest names it in that line through its docs criterion. Every other line of the section stays as it is. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because nothing an operator runs or decides changes.

## Smoke test

```bash
idx=docs/project-guide/README.md
missing=0
for pair in 'tests/conftest.py:conftest.py' 'tests/application/handlers/conftest.py:application/handlers/conftest.py'; do
  file=${pair%%:*}; entry=${pair#*:}
  line=$(grep -F -- "- \`$entry\`:" "$idx")
  for fx in $(grep -A1 '@pytest.fixture' "$file" | sed -n 's/^def \([a-z_]*\)(.*/\1/p'); do
    case $line in *"\`$fx\`"*) ;; *) echo "missing: $entry $fx"; missing=$((missing+1));; esac
  done
done
echo "$missing"
```
Expect: `0` and no `missing:` line (every fixture of both conftests is named in its line of the guide). Before the documenter's edit it prints 19 `missing:` lines and `19`.

```bash
missing=0
for f in tests/*.py; do n=$(basename "$f"); case "$n" in test_*) continue;; esac; grep -qF -e "$n" docs/project-guide/README.md || { echo "missing: $n"; missing=$((missing+1)); }; done
echo "$missing"
```
Expect: `0` (every shared helper module at the root of `tests/` is still named, as F0028-S0011 left it)

## Journal
