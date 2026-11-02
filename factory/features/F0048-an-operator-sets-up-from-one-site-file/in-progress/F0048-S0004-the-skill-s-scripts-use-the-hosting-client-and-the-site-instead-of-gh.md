# The skill's scripts use the hosting client and the site instead of gh

## Description

The Kumpel skill's scripts (`operator/skill/kumpel/scripts/`) read the factory's state from the code host through the `gh` program and keep the repository and the checkout in a settings file of their own. At one site `gh`'s login did not see the project's repository, and the values it needs are the site's. This story moves the scripts onto the hosting client of S0003 and the site file of S0001: `status.sh` and `approval.sh` call the API through `hosting_repo_api`, `start-story.sh` and `next-story.sh` pull and push through `hosting_git`, and `settings.sh` answers `repository` and `checkout` from `SITE_REPOSITORY` and `SITE_CHECKOUT` first and keeps only the switches in its JSON file. What the scripts print stays as it is, line for line, so that the skill's text and its references need no change; `wait.sh` calls `status.sh` and is unchanged. A script that finds neither a token command nor a `gh` login stops with the hosting client's message.

## Interface

The scripts find the libraries relative to their real folder: `here=$(cd "$(dirname "$0")" && pwd -P)`, then `. "$here/../../../lib/site.sh"` and `. "$here/../../../lib/hosting.sh"` (the skill's folder is linked into the operator's skill folder, so `pwd -P` is what names the repository).

`operator/skill/kumpel/scripts/settings.sh`

- `get repository` and `get checkout` print `$SITE_REPOSITORY` and `$SITE_CHECKOUT` when the site file (or the environment) sets them, else the value of the JSON file as now; neither set: the error of today. `get <switch>`, `set <switch> on|off` and `show` keep their behaviour; `show` prints the repository and the checkout from whichever source answers.
- `init` takes no argument when the site gives both values, and writes only the switches; with arguments it works as today.

`operator/skill/kumpel/scripts/status.sh` prints what it printed: one line `#<n> <work item> <stage:...|stage:?> <state>` for each open pull request whose head branch starts with `work-item/` and, last, `last archive: <subject>`; the state is `waits: <kind>` for the kinds it knew (`question`, `attempts_cap`, `round_cap`, `crash_cap`, `stall`, `expiry`, `error`, read from the factory's marker in the newest comment), `verdict posted`, `waits: approval` or `working`, by the rules it has now.

- The open pull requests come from `hosting_repo_api GET "/pulls?state=open&per_page=50"`; the stage is the label that starts with `stage:`.
- The newest comment of a pull request: `hosting_repo_api GET /issues/<n>` gives its `comments` count `c`; for `c` of 0 there is none, else `GET "/issues/<n>/comments?per_page=1&page=<c>"`.
- The last archive: `hosting_repo_api GET "/commits?per_page=20"`, the newest subject that starts with `work item ` and ends with `: merged, archived`, else `no archive commit in the last 20`.

`operator/skill/kumpel/scripts/approval.sh <n> <id>` prints the sections it printed (`== files`, `== tests changed`, the journal sections, `== Expect lines`, `== new markers`, `== cost`), with these sources: the changed files from `hosting_repo_api GET "/pulls/<n>/files?per_page=100"` (one name per line); the git sections from the checkout after `hosting_git fetch -q`; the cost from the newest comment among the first 100 of the pull request that contains `:cost_table:`, as now.

`operator/skill/kumpel/scripts/start-story.sh <id>` and `next-story.sh` call `hosting_git pull -q --no-rebase` and (the first) `hosting_git push -q` where they called `git pull` and `git push`; every other line stays.

No script calls `gh` any more (`grep -n '\bgh\b'` over the scripts finds only comments).

Tests: `tests/test_operator_skill_scripts.py`: each script runs in `tmp_path` with the site file, stand-ins for `curl` (answering by URL from fixtures: JSON files of the test) and a real local bare remote and clone for the git parts (no fake git, `CLAUDE.md` *Tests*). The hosting stand-in of S0003's tests is shared through `tests/operator_support.py`.

## Acceptance criteria

1. `status.sh` with two open pull requests (`work-item/F0001-S0001` labelled `stage:doing`, newest comment without a marker; `work-item/F0001-S0002` labelled `stage:approval`) and one that is not a work item prints, in that order, `#<n> F0001-S0001 stage:doing working`, `#<m> F0001-S0002 stage:approval waits: approval`, and the `last archive:` line; the pull request that is not a work item is not listed.
2. The states, as rows of one parametrized test over the newest comment: a body ending `<!-- factory key=abc:question:1 -->` gives `waits: question`; likewise `attempts_cap`, `round_cap`, `crash_cap`, `stall`, `expiry` and `error`; a body whose last three lines contain `<!-- kumpel verdict -->` gives `verdict posted`; no comments gives `working` (or `waits: approval` at `stage:approval`).
3. A pull request with no `stage:` label prints `stage:?`; a pull request with 25 comments is asked for page 25 with `per_page=1` (the stand-in records the URL).
4. The `last archive:` line is the newest of the 20 commit subjects that starts with `work item ` and ends with `: merged, archived`; with none it reads `last archive: no archive commit in the last 20`.
5. `approval.sh 4 F0001-S0001` prints the `== files` section from the files endpoint (one name per line, in the API's order) and the cost line from the newest comment that contains `:cost_table:` (the row that starts `| **total`), and `no cost table yet` when no comment of the first 100 does.
6. `approval.sh`'s git sections come from the checkout: a local bare remote with a branch `work-item/F0001-S0001` and a story file in `in-progress/` gives the `== tests changed` lines with their status letters, the `== Expect lines` and `== new markers` (`none` when the diff adds none), exactly as before the change (a fixture whose expected text is the old script's output).
7. `settings.sh get repository` and `get checkout` print the site's values when `SITE_REPOSITORY` and `SITE_CHECKOUT` are set, and the JSON file's when they are not; with the site's values and a JSON file that holds others, the site's win (two rows); with neither it exits non-zero with the message of today.
8. `settings.sh init` with no argument writes a file with the three switches at their defaults (`merge` off, `answer` on, `start_next` on) when the site gives both values, and exits 2 with the usage line when it does not; `settings.sh init owner/repo /path` works as before.
9. `start-story.sh F0001-S0003` moves the story from `backlog/` to `in-progress/` (making the folder when it is gone), commits `F0001-S0003: start`, and pushes to the bare remote through `hosting_git` (a token command is set and git is real; a local remote ignores the header); the remote's `main` holds the commit afterwards.
10. `start-story.sh` for an id that is in no `backlog/` prints `start-story.sh: no story <id> in any backlog/` to standard error and exits 1, as before.
11. `next-story.sh` prints `next: <id>` for the first story of the feature's *Stories* list that is still in `backlog/` when nothing is in progress, `busy: <id>` when a work item is in progress, and `none` when nothing is left (three rows), as before.
12. With no token command and no `gh`, `status.sh` exits non-zero with `hosting: the token command failed; see SITE_TOKEN_CMD in the site file` and prints no `#` line.
13. No script under `operator/skill/kumpel/scripts/` calls `gh` (a test over their text that ignores comment lines).
14. `make check` stays green.
15. docs: `operator/README.md` (the *Needs* part: `gh` is no longer needed when a token command is set; the settings file holds the switches only when the site gives the repository and the checkout) and `docs/operator-guide.md` (the site file's section: `SITE_REPOSITORY` and `SITE_CHECKOUT` are read by the skill); the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_REPOSITORY=owner/repo\nSITE_CHECKOUT=/path/to/checkout\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" KUMPEL_SETTINGS="$d/settings.json" sh operator/skill/kumpel/scripts/settings.sh init
FACTORY_SITE="$d/site.env" KUMPEL_SETTINGS="$d/settings.json" sh operator/skill/kumpel/scripts/settings.sh show
```

Expect: three lines: `settings written: <the file's path>`, `repository owner/repo, checkout /path/to/checkout` and `switches: merge off, answer on, start_next on`.

```bash
grep -n -v '^[[:space:]]*#' operator/skill/kumpel/scripts/*.sh | grep -c -w gh
```

Expect: one line, `0`.

## Journal
