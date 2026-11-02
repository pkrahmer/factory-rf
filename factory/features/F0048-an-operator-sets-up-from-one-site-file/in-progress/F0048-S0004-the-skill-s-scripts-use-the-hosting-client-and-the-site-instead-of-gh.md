---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 501
comments_read: [6584170311]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-02T17:50:35.816820Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T17:46:40.252102Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T17:46:40.258739Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T17:47:03.117753Z'
  stage: intake
  run: 4ba55cfcfc5742ff8c277fcc544b1932
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T17:49:24.474902Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T17:49:42.481721Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T17:50:14.833731Z'
  stage: intake
  run: d2d896714b8447b689cba697f768faca
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T17:50:35.816820Z'
  stage: tests
---

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
2. The states, as rows of one parametrized test over the newest comment: a body ending `<!-- factory key=abc:question:1 -->` gives `waits: question`; likewise `attempts_cap`, `round_cap`, `crash_cap`, `stall`, `expiry` and `error`; a body whose last three lines contain `<!-- kumpel verdict -->` gives `verdict posted`; no comments gives `working` (or `waits: approval` at `stage:approval`). The order is today's: a factory marker of one of the seven kinds first (whatever else the comment holds), then the verdict marker, then `waits: approval` at `stage:approval`, else `working`; a marker of another kind falls through to the next rule. One row each for: a comment with both a marker (`question`) and the verdict marker gives `waits: question`; a marker comment at `stage:approval` gives `waits: <kind>`; a verdict comment at `stage:approval` gives `verdict posted`; a marker whose kind is not one of the seven, at `stage:doing`, gives `working`.
3. A pull request with no `stage:` label prints `stage:?`; a pull request with 25 comments is asked for page 25 with `per_page=1` (the stand-in records the URL).
4. The `last archive:` line is the newest of the 20 commit subjects that starts with `work item ` and ends with `: merged, archived`; with none it reads `last archive: no archive commit in the last 20`.
5. `approval.sh 4 F0001-S0001` prints the `== files` section from the files endpoint (one name per line, in the API's order) and the cost line from the newest comment that contains `:cost_table:` (the row that starts `| **total`), and `no cost table yet` when no comment of the first 100 does.
6. `approval.sh`'s git sections come from the checkout: a local bare remote with a branch `work-item/F0001-S0001` and a story file in `in-progress/` gives the `== tests changed` lines with their status letters, the `== Expect lines` and `== new markers` (`none` when the diff adds none), exactly as before the change (a fixture whose expected text is the old script's output).
7. `settings.sh get repository` and `get checkout` print the site's values when `SITE_REPOSITORY` and `SITE_CHECKOUT` are set, and the JSON file's when they are not; with the site's values and a JSON file that holds others, the site's win (two rows); `show` with the site's values and a JSON file that holds others prints `repository <site's>, checkout <site's>` (a row); with neither, `show` prints `no settings at <the file's path>; run: settings.sh init <owner/name> <checkout>` and exits 1, and `get repository` exits non-zero.
8. `settings.sh init` with no argument writes a file with the three switches at their defaults (`merge` off, `answer` on, `start_next` on) when the site gives both values, and exits 2 printing `usage: settings.sh init <owner/name> <checkout>` to standard error when it does not; `settings.sh init owner/repo /path` works as before.
9. `start-story.sh F0001-S0003` moves the story from `backlog/` to `in-progress/` (making the folder when it is gone), commits `F0001-S0003: start`, and pushes to the bare remote through `hosting_git` (a token command is set and git is real; a local remote ignores the header); the remote's `main` holds the commit afterwards.
10. `start-story.sh` for an id that is in no `backlog/` prints `start-story.sh: no story <id> in any backlog/` to standard error and exits 1, as before.
11. `next-story.sh` prints `next: <id>` for the first story of the feature's *Stories* list that is still in `backlog/` when nothing is in progress, `busy: <id>` when a work item is in progress, and `none` when nothing is left (three rows), as before.
12. With no token command and no `gh`, `status.sh` exits non-zero with `hosting: the token command failed; see SITE_TOKEN_CMD in the site file` and prints no `#` line.
13. No script under `operator/skill/kumpel/scripts/` calls `gh` (a test over their text that ignores comment lines).
14. `approval.sh` prints the journal sections: the headers `== what the journal says about the smoke test, the findings and the leaves (<item>)` and `== the journal's last entry` appear, and a journal line holding `Met` or `Findings` appears under the first.
15. `approval.sh`'s git sections read the branch as it is on the bare remote after `hosting_git fetch -q`: a commit pushed to the remote by another clone, which the script's checkout has not seen, shows in the sections.
16. The stand-in sees the query strings `state=open&per_page=50` for the pull requests, `per_page=20` for the commits and `per_page=100` for the comments `approval.sh` reads (no case beyond 100 comments).
17. `make check` stays green.
18. docs: `operator/README.md` (the *Needs* part: `gh` is no longer needed when a token command is set; the settings file holds the switches only when the site gives the repository and the checkout) and `docs/operator-guide.md` (the site file's section: `SITE_REPOSITORY` and `SITE_CHECKOUT` are read by the skill); the other documents: none.

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

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: 1. The Interface says `settings.sh show` prints the repository and the checkout "from whichever source answers", but no criterion tests it. Only the smoke test runs `show`. Please add a criterion, for example `show` with the site's values and a JSON file holding others prints the site's. I would add it as a row of criterion 7.
   2. Criterion 7 says "the message of today" when neither source is set. Criterion 8 says "the usage line" for `init` without arguments. Neither text is in the story, so a test cannot check them. Please give both texts verbatim in the criteria. I would copy them from the current `settings.sh`.
   3. Criterion 2 leaves the precedence of the states to "the rules it has now". The test needs these cases decided:
      - a comment that carries both a factory marker and `<!-- kumpel verdict -->`;
      - a marker comment at `stage:approval`;
      - a verdict comment at `stage:approval`;
      - a marker whose kind is not one of the seven.
      Please state the order in the Interface, or add a row for each case. I would choose: marker kind first, then verdict, then approval or working. An unknown kind would fall through to the next rule.
   4. `approval.sh` prints "the journal sections" and runs `hosting_git fetch -q`, but no criterion covers either. Criterion 6 names only tests changed, Expect lines and new markers. Please add a criterion for the journal sections (names and content), and one that the git sections read the fetched branch, not a stale local one.
   5. Criterion 5 says the cost comes from "the first 100" comments, but no case has the cost table beyond comment 100. Please add one: either that the request carries `per_page=100`, or that a table beyond the first 100 is not found. The Interface also fixes `per_page=50` for the pull requests and `per_page=20` for the commits. Only the page-25 URL is checked (criterion 3). Please add a criterion that the stand-in sees these query strings, or drop the numbers from the Interface.
   6. Criterion 9 says `start-story.sh` and `next-story.sh` call `hosting_git pull -q --no-rebase`, and the first also calls `hosting_git push -q`. No criterion checks that the pull goes through `hosting_git`. Criterion 9 only checks the pushed commit. Please add one that the token reaches git through `GIT_CONFIG_*` for the pull as well, or say that the two scripts' calls are untested by design.
4. 2026-11-02 human: 1. Yes, a row of criterion 7 for `show` (the site's values win over the JSON file's).
   2. Yes, copy both texts verbatim from today's `settings.sh` into criteria 7 and 8.
   3. The order of today's `status.sh`: a factory marker of one of the seven kinds first (whatever else the comment holds), then the verdict marker, then `waits: approval` at `stage:approval`, else `working`. An unknown kind falls through to the next rule. Add a row for each of your four cases.
   4. Yes to the journal sections: one criterion that the section headers appear and that a journal line holding `Met` or `Findings` appears under them (names and content as today's script prints them). The fetch: one criterion that the git sections read the branch as it is on the bare remote after a commit the local clone has not seen.
   5. Add one criterion that the stand-in sees the query strings `state=open&per_page=50`, `per_page=20` for the commits and `per_page=100` for the comments; no case beyond 100 comments.
   6. Untested by design: the pull and the push go to a local bare remote, where the header does no work, and S0003 tests what `hosting_git` gives git. Criterion 9 checks the pushed commit, which is enough.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: concrete scripts, libraries and `hosting_repo_api`/`hosting_git` calls named, with their endpoints and query strings. Every Interface behaviour now has a criterion: `show` (7), the journal sections (14), the fetch (15), the query strings (16), the pull and push through `hosting_git` (9, untested by design for the pull, per journal 4.6).
   - Criteria: each is testable by one test function. I carried the human's answers (journal 4) into the story as their edit, not as mine. Criterion 2 gained the precedence (marker kind, then verdict, then approval or working, unknown kind falls through) and one row for each of the four cases. Criterion 7 gained a `show` row and today's text for `show` with nothing set (verbatim from `settings.sh`). Criterion 8 gained the usage line verbatim. New criteria 14 (journal sections), 15 (fetch reads the remote) and 16 (query strings). `make check` and `docs:` are now 17 and 18. Failing sides are covered: no marker or label, an unknown marker kind, no archive commit, no cost table, nothing set, `init` without arguments, an unknown story id, no token.
   - Smoke test: both commands are runnable and use only `settings.sh` and grep. Each `Expect:` is checkable: three exact lines, and `0`. No pytest command, so the `-q` rule does not apply.
   - Architecture: shell scripts under `operator/` use the shell libraries of S0001 and S0003. Nothing is added under `src/factory/`. The write paths cover `operator/*`.
   - Scope: within F0048 scope (the skill's scripts use the client and the site). It touches no "Out of scope" item and no test of another story.
   Open point for the tester: today's `settings.sh get` with no settings file raises a Python error and prints no message of its own. So criterion 7 requires only a non-zero exit for `get repository` when nothing is set, and the exact text only for `show`.
7. factory: started tests as vm.
