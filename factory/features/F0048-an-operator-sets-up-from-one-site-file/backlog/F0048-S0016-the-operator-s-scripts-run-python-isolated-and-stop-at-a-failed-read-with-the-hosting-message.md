# The operator's scripts run Python isolated and stop at a failed read with the hosting message

<!-- proposed by feature acceptance of 2026-11-03; refine before starting -->

## Description

The operator's scripts parse the code host's answers and their own JSON files with inline Python: `python3 -c '...'` and `python3 - <<'PY'`, in 20 places in `operator/bin/site`, `operator/job/job.sh` and six of the skill's scripts. Both forms put the current folder first on Python's import path. A script run from a project checkout, where the factory's agents write files, would therefore import a planted `json.py` instead of the standard library, and run it with the operator's environment, the site's token command included. Only `operator/bin/sanitise` and one call in `job.sh` use `-I` (isolated mode), which leaves the current folder, `PYTHON*` variables and the user's site packages out. This story makes every Python start in those scripts isolated. In the same scripts, `status.sh` pipes `hosting_repo_api` straight into Python at three reads, so a failing read prints the hosting client's message followed by a `JSONDecodeError` traceback. S0008 fixed the same pattern in `merge.sh` and `reset-to-tag.sh` by assigning the answer first. This story does the same in `status.sh`. What every script prints on success stays line for line, so that the skill's text needs no change.

## Interface

`operator/bin/site`, `operator/job/job.sh` and `operator/skill/kumpel/scripts/{status,settings,approval,comment,merge,reset-to-tag}.sh`:

- Every start of `python3` passes `-I` as its first option: `python3 -I -c '...' ARGS` and `python3 -I - ARGS <<'PY'`. The programs, their arguments and their output are unchanged.

`operator/skill/kumpel/scripts/status.sh`:

- The reads `GET /issues/<n>`, `GET /issues/<n>/comments?per_page=1&page=<count>` and `GET /commits?per_page=20` are each assigned to a variable first and parsed after. A failing read stops the script with exit 1, and the hosting client's message (`hosting: GET /repos/<repository>/...: <status> <message>`) is the last line on standard error. No Python traceback is printed. The read of the pull-request list keeps its behaviour.

Tests: `tests/test_operator_python_isolation.py`, with the stand-ins of `tests/operator_support.py` and `tests/operator_skill_support.py`; the `status.sh` rows are added to the module that tests `status.sh` today (`tests/test_operator_skill_scripts.py`, the standing leave covers only new rows that keep every earlier test's name and check).

## Acceptance criteria

1. A `json.py` that writes a marker file when it is imported lies in the working folder of each script, one row per script: `settings.sh show`, `settings.sh init` (the site gives both values), `status.sh`, `comment.sh 7 <file>`, `site check` (stand-ins answering as in S0009's tests) and `job.sh create --dry-run`. Each run leaves no marker file and prints the same lines as the same run from a folder without `json.py`.
2. A text check over the files of the Interface: every line that starts `python3` as a command passes `-I` as its first option. Rows: one per file. A file with a `python3 -c` without `-I` fails its row.
3. `status.sh` with one work-item pull request, where one read is answered 500: rows for `GET /issues/<n>`, for the comments page and for `GET /commits`. Each prints `hosting: GET /repos/owner/repo/<path>: 500 <message>` as the last line on standard error, prints no line that contains `Traceback`, and exits 1. With every read answered 200, the output is the same as before (the existing rows of `status.sh`'s test stay green).
4. `make check` stays green.
5. docs: `docs/decisions.md`: one entry stating that the operator's scripts start Python with `-I` and why (a folder an agent writes may be the working folder), with the rejected alternative (`cd` to the script's folder before each call). `docs/operator-guide.md`: none, because the behaviour the operator sees stays the same; `README.md` and the project guide: none.

## Smoke test

```bash
r=$(pwd); d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'open("%s/imported", "w").close()\n' "$d" > "$d/json.py"
printf 'SITE_REPOSITORY=owner/repo\nSITE_CHECKOUT=%s\n' "$d" > "$d/site.env"
(cd "$d" && HOME="$d" XDG_CONFIG_HOME="$d/config" FACTORY_SITE="$d/site.env" sh "$r/operator/skill/kumpel/scripts/settings.sh" init >/dev/null 2>&1)
test -e "$d/imported"; echo "imported: $?"
```

Expect: `imported: 1`

## Journal
