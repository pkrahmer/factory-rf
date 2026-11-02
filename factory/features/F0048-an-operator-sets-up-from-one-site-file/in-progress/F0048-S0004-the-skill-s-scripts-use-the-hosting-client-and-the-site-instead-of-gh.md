---
stage: smoke-test
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 501
comments_read: [6584170311, 6584737120]
handed_over: null
claim: null
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
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-02T17:56:47.153594Z'
  stage: tests
  run: f43b1b78a114462dbfe375139ebf7eb1
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-02T17:57:07.996169Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-02T18:00:46.763221Z'
  stage: doing
  run: e6123964a1b6405bb7fa1ffc93c82daf
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-02T18:17:27.293214Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-02T18:17:45.185206Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-02T18:21:11.549704Z'
  stage: doing
  run: dfde80f43c644b108114069438aff388
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-02T18:21:32.449574Z'
  stage: review
- number: 15
  speaker: reviewer
  kind: result
  at: '2026-11-02T18:22:47.568648Z'
  stage: review
  run: 1bf33543ec68488daf356aa552f168df
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-02T18:23:08.313737Z'
  stage: doing
- number: 17
  speaker: coder
  kind: result
  at: '2026-11-02T18:23:29.308923Z'
  stage: doing
  run: 1d3b140a217d4f218cb5f52010719510
- number: 18
  speaker: factory
  kind: started
  at: '2026-11-02T18:23:50.525095Z'
  stage: tests
- number: 19
  speaker: tester
  kind: result
  at: '2026-11-02T18:26:00.164435Z'
  stage: tests
  run: bcf56fcb34ac425f8052d0c0932b2d47
- number: 20
  speaker: factory
  kind: started
  at: '2026-11-02T18:26:21.363845Z'
  stage: doing
- number: 21
  speaker: coder
  kind: result
  at: '2026-11-02T18:29:45.037295Z'
  stage: doing
  run: cce2c20a8afd4476a0a6bdc24cdba970
- number: 22
  speaker: factory
  kind: started
  at: '2026-11-02T18:30:05.829138Z'
  stage: review
- number: 23
  speaker: reviewer
  kind: result
  at: '2026-11-02T18:31:35.685252Z'
  stage: review
  run: b52fb4c7655848b69e6f7fe8c290742c
- number: 24
  speaker: factory
  kind: started
  at: '2026-11-02T18:31:56.214319Z'
  stage: docs
- number: 25
  speaker: documenter
  kind: result
  at: '2026-11-02T18:32:36.255400Z'
  stage: docs
  run: 12c8828485ca411bacb2bf7f9eb719ba
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
17. `settings.sh get repository` with a JSON file and no site file at `FACTORY_SITE`, or with a site file that has a faulty line, prints the JSON file's repository and exits 0 (two rows); with the faulty file, the site file's message is on standard error.
18. `make check` stays green.
19. docs: `operator/README.md` (the *Needs* part: `gh` is no longer needed when a token command is set; the settings file holds the switches only when the site gives the repository and the checkout) and `docs/operator-guide.md` (the site file's section: `SITE_REPOSITORY` and `SITE_CHECKOUT` are read by the skill); the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_REPOSITORY=owner/repo\n' > "$d/site.env"
printf 'SITE_CHECKOUT=/path/to/checkout\n' >> "$d/site.env"
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
8. tester: Tests written for every criterion in `tests/test_operator_skill_scripts.py`. The scripts run under `sh` in `tmp_path` with a site file, a `curl` stand-in that answers by URL, and real bare remotes and clones for the git parts.

   - criterion 1: tests/test_operator_skill_scripts.py::test_status_lists_the_open_work_items_and_the_last_archive
   - criterion 2: tests/test_operator_skill_scripts.py::test_the_newest_comment_decides_the_state (the seven kinds, verdict, no comments at doing and at approval, marker+verdict, marker at approval, verdict at approval, unknown kind)
   - criterion 3: tests/test_operator_skill_scripts.py::test_a_pull_request_without_stage_label_and_many_comments
   - criterion 4: tests/test_operator_skill_scripts.py::test_the_last_archive_is_the_newest_archive_subject
   - criterion 5: tests/test_operator_skill_scripts.py::test_approval_prints_the_files_and_the_cost_from_the_api
   - criterion 6: tests/test_operator_skill_scripts.py::test_approval_prints_the_git_sections_from_the_checkout (with a `noqa` marker / `none`)
   - criterion 7: tests/test_operator_skill_scripts.py::test_settings_answer_the_repository_and_checkout_from_the_site_first
   - criterion 8: tests/test_operator_skill_scripts.py::test_settings_init_needs_no_arguments_when_the_site_gives_both
   - criterion 9: tests/test_operator_skill_scripts.py::test_start_story_moves_the_story_and_pushes_it
   - criterion 10: tests/test_operator_skill_scripts.py::test_start_story_refuses_an_id_in_no_backlog
   - criterion 11: tests/test_operator_skill_scripts.py::test_next_story_names_the_next_story_to_start
   - criterion 12: tests/test_operator_skill_scripts.py::test_status_without_a_token_source_stops
   - criterion 13: tests/test_operator_skill_scripts.py::test_no_script_calls_gh
   - criterion 14: tests/test_operator_skill_scripts.py::test_approval_prints_the_journal_sections
   - criterion 15: tests/test_operator_skill_scripts.py::test_approval_reads_the_branch_as_the_remote_holds_it
   - criterion 16: tests/test_operator_skill_scripts.py::test_the_scripts_ask_with_the_query_strings_of_the_interface

   Files:
   - Created: `tests/test_operator_skill_scripts.py`.
   - Changed, under the standing leave to move a shared test helper (the story's Interface asks for S0003's hosting stand-in to be shared through `tests/operator_support.py`):
     - `tests/operator_support.py` now holds `CURL_STAND_IN` and `hosting_env`, moved out of `tests/test_operator_hosting.py`.
     - `tests/test_operator_hosting.py` now imports both from there. Every test there keeps its name and checks the same thing.
     - The stand-in gained one optional input, `STAND_IN_CURL_ROUTES`: a JSON file of bodies keyed by the URL's path and query, or by the path alone; any other URL gets 404. When that variable is unset it behaves as before, so the S0003 tests are untouched in behaviour.

   Assumption for the coder and the reviewer: the Interface does not name the endpoint for the comments `approval.sh` reads. The tests serve it at `/repos/owner/repo/issues/4/comments` with any query, as `status.sh` reads a pull request's comments. Criterion 16 checks that every request to it carries `per_page=100`.

   Test run: one run of `uv run pytest -q tests/test_operator_skill_scripts.py tests/test_operator_hosting.py`; the last lines showed failures in the new tests, for the right reason:
   - `next-story.sh` still needs the JSON settings file.
   - `status.sh` still calls `gh`.
   - The scripts still contain `gh`.
   Every module imported; nothing failed at collection. I ran it once as the stage says, so I don't have the full count or confirmation that the moved hosting tests pass; the factory's `make test` records that.

   `make lint` is green. The type check was skipped, as the stage says.

   `lint`: lint: green (0.1 s)
   `test`: FAILED tests/test_operator_skill_scripts.py::test_no_script_calls_gh - AssertionError: assert ['approval.sh...status.sh:25'] == []
9. factory: started doing as vm.
10. coder: Stopped with the work done but `make check` red. The failure is in the work item's own smoke-test text, not in the code. I need your decision before I can hand forward.

    **The question.** `make secrets` (detect-secrets over the changed files) flags a "Base64 High Entropy String" at line 121 of this work item's file. That line is in the `## Smoke test` section, which intake wrote: the one `printf` that writes both `SITE_REPOSITORY` and `SITE_CHECKOUT` into the site file. Every other target is green: lint, sast, types, layers, licenses, and test (coverage 99.58 %). Options:
    - (a) Rewrite that one line of the smoke test as two `printf` lines: `printf 'SITE_REPOSITORY=owner/repo\n' > "$d/site.env"` and `printf 'SITE_CHECKOUT=/path/to/checkout\n' >> "$d/site.env"`. The meaning and the `Expect:` stay the same. I ran detect-secrets on those two lines in a temporary file and it found nothing. **This is the one I would choose.** I would make the edit myself in the next run, if the work item is in the coder's write paths; if not, you would make it.
    - (b) Put a `pragma: allowlist secret` on that line, or add a `.secrets.baseline` entry. Both need your leave under *Not without asking*.
    - (c) You change the text yourself on the branch.

    **What is built (in the working tree, for the factory's commit):**
    - `operator/skill/kumpel/scripts/settings.sh`:
      - It sources `lib/site.sh` and loads the site file only when that file exists, so with no site file the JSON file answers alone.
      - `get repository` and `get checkout` print `SITE_REPOSITORY` and `SITE_CHECKOUT` first, else the JSON file's value.
      - `show` takes the repository and the checkout from the site first, then the JSON file.
      - `init` with no arguments, when the site gives both values, writes only the switches; with two arguments it works as before.
    - `status.sh`:
      - The open pull requests, the newest comment and the last archive now come from `hosting_repo_api`. The comment is found from the issue's `comments` count, then `per_page=1&page=<c>`.
      - The state rules are unchanged, line for line.
      - `SITE_REPOSITORY` is set from `settings.sh get repository`, so a JSON-only setup still works.
    - `approval.sh`:
      - `== files` comes from `/pulls/<n>/files?per_page=100`; the cost comes from `/issues/<n>/comments?per_page=100`. Both API calls run before any output, so a missing token stops the script before it prints a section.
      - `hosting_git fetch -q` replaces `git fetch`. The git sections are unchanged.
    - `start-story.sh` and `next-story.sh`: they source both libraries and use `hosting_git pull` and `hosting_git push`.
    - All of these scripts now use `pwd -P`. `wait.sh` is unchanged.

    **Main choice.** JSON is parsed with inline `python3`, which `settings.sh` already needs. I rejected `jq`: it is not installed here, and it would add a new thing the operator needs.

    **Checks.** `uv run pytest -q tests/test_operator_skill_scripts.py tests/test_operator_hosting.py` passes. Both smoke-test commands give the expected output: the three `settings.sh` lines, and `0` from the `gh` grep.

    **Refactor.** I replaced a `set --` trick in `settings.sh init` with an explicit if/elif/else.

    **Noticed, not touched:**
    - `operator/README.md`'s *Needs* and `docs/operator-guide.md` are for the docs stage (criterion 18).
    - In `status.sh`, a failed `hosting_repo_api` inside the comment-count pipeline surfaces as a python JSON error after the hosting client's own message.
11. 2026-11-02 human: (c), done: the smoke test now writes the site file with your two `printf` lines (commit 231a93e57 on the branch, scanned clean first), and the quoted command in your entry is reworded too. The meaning and the `Expect:` are unchanged. Run `make check` again and hand on.
12. factory: started doing as vm.
13. coder: Ran `make check` again after the human's smoke-test fix (231a93e57), and it is green: `check: green`, coverage 99.58 %. The `make secrets` failure from my last run is gone. This run changed no code. The implementation from the last run was already committed on the branch, and I made no new edits.

    What is built (the diff against main is in these files only):
    - `operator/skill/kumpel/scripts/settings.sh`:
      - It sources `lib/site.sh` and loads the site file only when it exists.
      - `get repository` and `get checkout` answer from `SITE_REPOSITORY` and `SITE_CHECKOUT` first, then from the JSON file.
      - `show` takes the repository and the checkout from the site first.
      - `init` with no arguments works when the site gives both values, and then writes only the switches.
    - `operator/skill/kumpel/scripts/status.sh`:
      - The open pull requests, the newest comment and the last archive come from `hosting_repo_api`. The newest comment is the issue's `comments` count, then `per_page=1&page=<c>`.
      - The state rules are unchanged, line for line.
    - `operator/skill/kumpel/scripts/approval.sh`:
      - The files come from `/pulls/<n>/files?per_page=100` and the cost from `/issues/<n>/comments?per_page=100`. Both calls run before any output.
      - `hosting_git fetch -q` replaces `git fetch`; the git sections are unchanged.
    - `operator/skill/kumpel/scripts/start-story.sh` and `next-story.sh`: they pull and push through `hosting_git`.
    - All of these use `pwd -P` to find `lib/`.

    Main choice: JSON is parsed with inline `python3`, which the scripts already need. I rejected `jq`: it is not installed here, and the operator would have to install one more tool.

    Refactor: I read the diff again and found nothing to change.

    Journal: entry 11 changed only the smoke test's text (two `printf` lines), not what the task means, so `## Description` is unchanged.

    Noticed, not touched:
    - `operator/README.md` and `docs/operator-guide.md` are for the docs stage (criterion 18).
    - In `status.sh`, when `hosting_repo_api` fails inside `newest_comment`'s pipeline, the hosting client's message is followed by a Python JSON error.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
14. factory: started review as vm.
15. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (the five scripts under `operator/skill/kumpel/scripts/`, `tests/operator_support.py`, `tests/test_operator_hosting.py` and the new `tests/test_operator_skill_scripts.py`) against the work item. Group 1 (acceptance criteria) fails, so the review stops there. All gaps of group 1:

    1. `tests/test_operator_skill_scripts.py::test_the_newest_comment_decides_the_state`: criterion 2 limits the verdict marker to "the last three lines" of the comment, and the script reads only `tail -n 3` (`status.sh:40`). Only the inside side is tested. Fix: add a row where `<!-- kumpel verdict -->` is the fourth line from the end at `stage:doing`, which gives `working`.
    2. `tests/test_operator_skill_scripts.py::test_settings_init_needs_no_arguments_when_the_site_gives_both`: the Interface says `init` with no argument "writes only the switches", but the test compares only the keys it expects (`{key: data.get(key) for key in written}`). A file that also held `repository`/`checkout` would pass. Fix: assert `data == written`.
    3. Same test: criterion 8 refuses `init` with no argument "when [the site] does not" give both values, but only the row where the site gives neither is tested. Fix: add a row where the site gives `SITE_REPOSITORY` without `SITE_CHECKOUT`, expecting exit 2 and the usage line (the `site_gives_both` rule in `settings.sh`).
    4. criterion 17 added, and it needs its test. `settings.sh:12-15` lets the JSON file answer alone when there is no site file, and goes on past a faulty site file (`site_load || :`). No criterion pins either case, and the test of criterion 7 always writes a site file. The new criterion 17 has two rows: no site file, and a site file with a faulty line. In both, `get repository` prints the JSON file's value. With the faulty file, the site file's message is on standard error. The closing criteria are now 18 (`make check`) and 19 (docs).

    Everything else in group 1 holds:
    - Criteria 1, 3–7 and 9–16 each have a test that checks what the criterion names.
    - The journal's entry 13 records `check: green` after the coder.
    - The pull in `start-story.sh`/`next-story.sh` is untested by design, per the human's answer in journal entry 4.6.

    Earlier tests:
    - `tests/test_operator_hosting.py`: the standing leave to move a shared test helper. `CURL_STAND_IN` and `hosting_env` moved to `tests/operator_support.py`; every test keeps its name and checks the same thing.
    - `tests/operator_support.py`: the same standing leave, together with the Interface's "shared through `tests/operator_support.py`". It received the moved helpers. The stand-in's one addition, `STAND_IN_CURL_ROUTES`, does nothing when that variable is unset, so the earlier tests are unaffected.
16. factory: started doing as vm.
17. coder: Round 1: I changed no code. All four review findings (entry 15) are changes to tests, and the scripts already behave as each finding asks, so this goes to the tester:

    1. `tests/test_operator_skill_scripts.py::test_the_newest_comment_decides_the_state` needs one more row. Put `<!-- kumpel verdict -->` as the fourth line from the end, at `stage:doing`; the expected state is `working`. `status.sh` reads only `tail -n 3` of the newest comment.
    2. In `tests/test_operator_skill_scripts.py::test_settings_init_needs_no_arguments_when_the_site_gives_both`, assert that the whole written file equals the three switches (`data == written`). Today the test compares only the expected keys.
    3. The same test needs a row where the site gives `SITE_REPOSITORY` without `SITE_CHECKOUT`. The expected result is exit 2 and `usage: settings.sh init <owner/name> <checkout>` on standard error. `settings.sh` falls back to the usage line when `site_gives_both` fails.
    4. The new criterion 17 needs its test, with two rows:
       - No site file at `FACTORY_SITE`: `settings.sh get repository` prints the JSON file's repository and exits 0.
       - A site file with a faulty line: the same result, and the site file's message is on standard error.
       `settings.sh` loads the site file only when it exists and continues past a faulty one (`site_load || :`).

    Built (unchanged since entry 13, already committed on the branch):
    - `operator/skill/kumpel/scripts/settings.sh`
    - `operator/skill/kumpel/scripts/status.sh`
    - `operator/skill/kumpel/scripts/approval.sh`
    - `operator/skill/kumpel/scripts/start-story.sh`
    - `operator/skill/kumpel/scripts/next-story.sh`

    Main choice: the scripts parse JSON with inline `python3`, which `settings.sh` already needed. I rejected `jq` because it is not installed here and the operator would need one more tool.

    Journal: entry 15 added criterion 17, and the Description already carries it, so I did not rewrite `## Description`.

    Noticed, not touched:
    - In `status.sh`, when `hosting_repo_api` fails inside the `newest_comment` pipeline, the hosting client's message is followed by a Python JSON error.
    - `operator/README.md` and `docs/operator-guide.md` belong to the docs stage (criterion 19).
18. factory: started tests as vm.
19. tester: Made the four test changes that the review (entry 15) found and the coder's entry 17 named. All of them are in `tests/test_operator_skill_scripts.py`, which this story's tests stage wrote, so no other story's test changed.

    1. `test_the_newest_comment_decides_the_state` has a new row, `verdict-fourth-from-the-end`. At `stage:doing`, the comment has `<!-- kumpel verdict -->` as the fourth line from the end, and the expected state is `working`. This tests the outside side of criterion 2's "last three lines".
    2. `test_settings_init_needs_no_arguments_when_the_site_gives_both` now asserts that the whole written file equals the expected data (`data == written`), not only the expected keys. This tests the Interface's "writes only the switches".
    3. The same test has a new row, `site-gives-only-the-repository`. The site gives `SITE_REPOSITORY` without `SITE_CHECKOUT`, and the expected result is exit 2 with the usage line on standard error. To allow this row, the `site` parameter changed from a bool to the dict of site values. The test name and the other rows' checks are unchanged.
    4. Criterion 17 now has a test: `tests/test_operator_skill_scripts.py::test_settings_answer_from_the_json_file_without_a_usable_site_file`. It has two rows:
       - `no-site-file`: there is no file at `FACTORY_SITE`.
       - `faulty-site-file`: the site file is the one line `not a pair`.
       In both rows, `get repository` must print the JSON file's `json/repo` and exit 0. In the faulty row, standard error must also hold `site: <site file>:1: not a KEY=value line`.

    Criterion → test, for the changes:
    - criterion 2: tests/test_operator_skill_scripts.py::test_the_newest_comment_decides_the_state
    - criterion 8: tests/test_operator_skill_scripts.py::test_settings_init_needs_no_arguments_when_the_site_gives_both
    - criterion 17: tests/test_operator_skill_scripts.py::test_settings_answer_from_the_json_file_without_a_usable_site_file

    Files: I created none and changed `tests/test_operator_skill_scripts.py`. The scripts already exist, so the test run had no module it could not import. The one run, `uv run pytest -q tests/test_operator_skill_scripts.py`, passed every test, the new rows included. `make lint` is green.

    `lint`: lint: green (0.2 s)
    `test`: test: green (81.2 s)
20. factory: started doing as vm.
21. coder: Round 1: I changed no code. The review's four findings (entry 15) were test changes, and the tester made them (entry 19). The scripts already behave as the new rows and the criterion 17 test expect. `make check` is green with the tester's changes (coverage 99.58 %), and the working tree is clean.

    Built (unchanged since entry 13, already committed on the branch):
    - `operator/skill/kumpel/scripts/settings.sh`
    - `operator/skill/kumpel/scripts/status.sh`
    - `operator/skill/kumpel/scripts/approval.sh`
    - `operator/skill/kumpel/scripts/start-story.sh`
    - `operator/skill/kumpel/scripts/next-story.sh`

    Main choice: the scripts parse JSON with inline `python3`, which `settings.sh` already needed. I rejected `jq`: it is not installed here, and the operator would need one more tool.

    Refactor: there is no new diff this round, so there was nothing to change.

    Journal: entry 15 added criterion 17, and the Description already holds it, so I did not rewrite `## Description`.

    Noticed, not touched:
    - In `status.sh`, when `hosting_repo_api` fails inside the `newest_comment` pipeline, the hosting client's message is followed by a Python JSON error.
    - `operator/README.md` and `docs/operator-guide.md` belong to the docs stage (criterion 19).

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 0 new, 42 known, 0 gone
22. factory: started review as vm.
23. reviewer: Round 1 review. I read the work item, `git diff main...HEAD -- . ':!factory'` and its name-status, and `operator/lib/site.sh` and `operator/lib/hosting.sh` (S0001 and S0003) to check what the scripts call. The diff covers the five scripts under `operator/skill/kumpel/scripts/`, `tests/operator_support.py`, `tests/test_operator_hosting.py` and the new `tests/test_operator_skill_scripts.py`.

    no findings

    What I checked:
    - **The four findings of entry 15 are fixed in `tests/test_operator_skill_scripts.py`:**
      - The `verdict-fourth-from-the-end` row tests the outside side of the "last three lines" limit.
      - `data == written` pins "writes only the switches".
      - The `site-gives-only-the-repository` row gives exit 2 and the usage line.
      - `test_settings_answer_from_the_json_file_without_a_usable_site_file` tests criterion 17 with two rows.
    - **Group 1:** I went through criteria 1 to 17 and every rule of the Interface again. Each has a test that checks what it names, and every refused side has a row: no label, an unknown kind, no archive, no cost table, nothing set, `init` without the site's two values, an unknown id, no token. The pull through `hosting_git` is untested by design (journal 4.6). Journal entry 21 records `check: green` after the coder.
    - **Groups 2 and 3:** nothing under `src/` changed. The scripts reach the host only through `hosting_repo_api` and `hosting_git`. No `gh` is left, no marker silences a check, and the diff has no secrets.
    - **Group 4:** the comments explain why, not what. The JSON is parsed with inline `python3`, which the scripts already needed (`jq` was rejected).
    - **Group 5:** the Description matches what was built. The docs criterion (19) still names what the reader must know.

    Notes:
    1. `tests/test_operator_skill_scripts.py:make_bare_remote` is a second copy of `tests/git_support.py:make_remote`, with a `files` parameter added and the seed returned. It could become a parameter of the shared helper.
    2. `tests/test_operator_skill_scripts.py::test_settings_init_needs_no_arguments_when_the_site_gives_both` checks the `settings written:` line only when arguments are given, so the `site-gives-both` row leaves its standard output unchecked.
    3. `tests/test_operator_skill_scripts.py::test_settings_answer_the_repository_and_checkout_from_the_site_first` fills in the expected `show` text inside the test when `status == 1 and stdout is None`. A row value would read more plainly.

    Earlier tests:
    - `tests/test_operator_hosting.py`: changed under the standing leave to move a shared test helper. `CURL_STAND_IN` and `hosting_env` moved to `tests/operator_support.py`, and the file now imports them from there. Every test keeps its name and checks the same thing.
    - `tests/operator_support.py`: received the moved helpers under the same standing leave, together with the Interface's "shared through `tests/operator_support.py`". The stand-in's one addition, `STAND_IN_CURL_ROUTES`, does nothing when that variable is unset, so the earlier tests are unaffected.
24. factory: started docs as vm.
25. documenter: Docs round 1 for F0048-S0004. I wrote the two documents criterion 19 names. I changed only documents, so I did not run `make check`. The factory's checks after this stage decide. I ran no example, because I wrote none.

    Files changed:
    - `operator/README.md`, section *Needs*: `gh` is no longer required. The reader now needs `git`, `curl`, `python3`, a POSIX shell and a way to a token (`SITE_TOKEN_CMD`, or else a logged-in `gh` that is used only to print the token). I wrote `curl` because `hosting.sh` and the new tests use it.
    - `operator/README.md`, section *Installing*: the skill asks for nothing when the site file gives `SITE_REPOSITORY` and `SITE_CHECKOUT`. The settings file then holds the switches only, and `settings.sh init` takes no argument. Without the site's values the skill asks for the repository and the checkout, and the JSON file keeps them.
    - `docs/operator-guide.md`, the site file's section, before *The token source*: a paragraph on what the skill's scripts read from the site, the JSON-file fallback (a missing or faulty site file does not stop `settings.sh`), `init` needing arguments unless the site gives both values, and the hosting client's message when there is no token.

    Cross-read and found current against the diff:
    - The rest of `operator/README.md`: the scripts table at line 13 still matches the scripts' names and jobs.
    - The `docs/operator-guide.md` sections on the site file, its keys, and the hosting library (`hosting_repo_api`, `hosting_git`, the return codes, the message for a missing token).
    - The scripts' own header comments and the Interface: they agree with what I wrote.

    Stale text I noticed and left alone:
    1. `operator/skill/kumpel/references/answering.md:24` (`gh pr comment`) and `approving.md:18` (`gh pr merge`) still use `gh`. The skill's text is outside my write paths and the Description keeps it unchanged. The "no `gh`" rule in criterion 13 covers only `scripts/*.sh`. These two lines are a candidate for a later story.
    2. `operator/skill/kumpel/SKILL.md:12` says to ask the human for the repository and the checkout when the settings are missing. That is still true when the site gives none, and it leaves out the site-file path. The skill's text is not mine.
    3. The coder's note stands: in `status.sh`, a failed `hosting_repo_api` inside the `newest_comment` pipeline prints the hosting client's message, then a Python JSON error. That is a code matter, not a documentation finding.

    No findings against the code.

    The factory left out changes outside the write paths: operator/README.md.

    `check`: check: green (not run again: passed on tree 1a703605acf0 at 2026-11-02T18:28:09Z)
    `secrets`: secrets: green (1.4 s)
    `documents`: documents ok
