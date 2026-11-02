---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 506
comments_read: [6588966186, 6589156211]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-02T21:29:28.103490Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-02T21:29:28.109550Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-02T21:29:51.865212Z'
  stage: intake
  run: 6a60427a8c3941cc9174c185c0ccf7f1
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-02T21:32:13.472005Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-02T21:32:31.392250Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-02T21:33:00.283228Z'
  stage: intake
  run: 5a2e2a8824f540a788ca415cf0b32964
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-02T21:33:21.144109Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-11-02T21:37:28.344607Z'
  stage: tests
  run: e87058f2e51d4a3981077b0dd8fb60c7
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-11-02T21:41:52.265681Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-11-02T21:42:10.532906Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-11-02T21:44:03.251234Z'
  stage: tests
  run: d86787a902184022909ef2d0a0c006dd
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-02T21:44:25.441962Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-02T21:47:50.248954Z'
  stage: doing
  run: c8c1a72330734868b5f31e8b32cba16e
---

# Merging an approved story and resetting a trial repository to a tag are commands

## Description

Two acts of whoever drives a factory run were done by hand with the hosting API on 2026-11-02, and both are easy to get wrong. Merging a story: it must be an open, ready pull request at the approval stage, merged with a merge commit (the factory reads a story's state from its branch), and the next story may be started only after the factory has archived the merged one. Resetting a trial repository to its starting-point tag so that a run can be repeated: it closes the run's pull requests, deletes its work-item branches and moves `main` back by force, the one act of these scripts that cannot be undone. This story adds `merge.sh` and `reset-to-tag.sh` to the skill's scripts. Merging checks before it acts and waits for the archive commit. The reset needs `--yes`, a repository that the site names as resettable and that is the repository the commands work on (so the factory's own repository can never be its target), and a tag that exists; it works through the API, with no checkout. Neither script judges whether a story deserves a merge: that stays with the skill's rules (`references/approving.md`).

## Interface

`operator/skill/kumpel/scripts/merge.sh <pr> <id>` and `reset-to-tag.sh <tag> [--yes]` (`sh`, the site and the hosting client of S0001 and S0003; the API calls through `hosting_repo_api`)

- `merge.sh`: reads `GET /pulls/<pr>`. It stops with exit 1 and `merge.sh: #<pr> is not open` when the state is not `open`, with `merge.sh: #<pr> is a draft` when it is a draft, and with `merge.sh: #<pr> is not at stage:approval` when no label is `stage:approval`; it also stops with `merge.sh: #<pr> is not the pull request of <id>` when the head branch is not `work-item/<id>`. Otherwise it calls `PUT /pulls/<pr>/merge` with `{"merge_method":"merge"}`; when the answer is not a success it prints the message of `hosting_api` and exits 1. It then polls `GET "/commits?per_page=20"` every `${KUMPEL_POLL_SECONDS:-15}` seconds for at most `${KUMPEL_ARCHIVE_WAIT:-300}` seconds for a commit subject `work item <id>: merged, archived`. It prints `merged #<pr>` after the merge and `archived <id>` when the commit is there (exit 0); when the wait ends first it prints `merge.sh: merged, but no archive commit for <id> after <N> s` and exits 1.
- `reset-to-tag.sh`: needs `SITE_REPOSITORY` and `SITE_RESET_REPOSITORY`; it exits 1 with `reset-to-tag.sh: <repository> is not the site's resettable repository` unless they are equal, and 2 with the `site_require` message when one is unset. It resolves the tag with `GET /git/ref/tags/<tag>` (an `object.type` of `tag` is followed once with `GET /git/tags/<sha>` to its `object.sha`; a `commit` is the commit); a tag that does not exist exits 1 with `reset-to-tag.sh: no tag <tag>`.
- Without `--yes` it prints the plan and exits 1: `would close <n> open work-item pull request(s)`, `would delete <m> work-item branch(es)`, `would move main to <the first 7 characters of the commit>`, then `run again with --yes`. With `--yes` it does it in this order, printing one line for each: `closed #<n>` for each open pull request whose head branch starts with `work-item/` (`PATCH /pulls/<n>` with `{"state":"closed"}`), `deleted <branch>` for each ref of `GET /git/matching-refs/heads/work-item/` (`DELETE /git/refs/heads/<branch>`), `moved main to <7 characters>` (`PATCH /git/refs/heads/main` with `{"sha":"<commit>","force":true}`). A failing call stops the script there with its message and exit 1, so that a half reset is visible.
- The open pull requests are listed with `GET /pulls?state=open&per_page=100`, without paging.
- It never touches another branch, a tag, or a pull request that is not a work item's.

Tests: `tests/test_operator_merge_reset.py` with the `curl` stand-in of S0003's tests, which records every request (method, URL, body from its standard input) and answers from fixtures per row.

## Acceptance criteria

1. `merge.sh 5 F0001-S0001` for an open, ready pull request labelled `stage:approval` with the head `work-item/F0001-S0001` sends one `PUT /pulls/5/merge` with the body `{"merge_method":"merge"}`, prints `merged #5`, polls, and with the archive commit in the answer prints `archived F0001-S0001` and exits 0.
2. The refusals, as rows of one parametrized test: a closed pull request, a draft, one without the `stage:approval` label, and one whose head is another work item each print their message, exit 1 and send no `PUT`.
3. A merge the host refuses (405 with `{"message":"Pull Request is not mergeable"}`) prints `hosting: PUT /pulls/5/merge: 405 Pull Request is not mergeable`, exits 1 and does not poll.
4. The archive wait, with `KUMPEL_POLL_SECONDS=0` and `KUMPEL_ARCHIVE_WAIT=0`: a commit list without the archive subject prints the `no archive commit` line with `after 0 s` and exits 1; the archive subject in the third poll's answer gives `archived` (the stand-in answers per call number).
5. `reset-to-tag.sh` with `SITE_REPOSITORY` and `SITE_RESET_REPOSITORY` different, with `SITE_RESET_REPOSITORY` unset, or with `SITE_REPOSITORY` unset, sends no request that changes anything and exits as the Interface says (three rows).
6. Without `--yes` it sends only `GET` requests, prints the plan with the counts of the fixture (two open work-item pull requests and a third that is not a work item, three `work-item/` branches) and exits 1.
7. A tag that does not exist (404) exits 1 with `reset-to-tag.sh: no tag <tag>` and sends no change; an annotated tag is followed to its commit, a lightweight one is used directly (two rows, the commit of the move is the same).
8. With `--yes` the requests that change come in the order of the Interface: a `PATCH` closing each work-item pull request (and none for the other), a `DELETE` for each `work-item/` ref, and a `PATCH` of `/git/refs/heads/main` with `{"sha":"<commit>","force":true}` last; the printed lines are `closed #<n>`, `deleted <branch>` and `moved main to <7 characters>`.
9. A failing call stops the script, as rows of one parametrized test: a close `PATCH`, the third `DELETE` and the move of `main` answered 422 each print the message of `hosting_api`, exit 1 and send none of the later requests (after a failing close, no further close, no `DELETE` and no move; after the third `DELETE`, no later `DELETE` and no move; after a failing move, nothing).
10. A reset that finds nothing to close or delete still moves `main` and prints only the `moved` line.
11. No request touches a ref other than `heads/work-item/*` and `heads/main` and no tag (a test over every request of the rows above).
12. `make check` stays green.
13. docs: `operator/skill/kumpel/references/approving.md` (the *Then* part names `merge.sh`), `operator/README.md` (the scripts table) and `docs/operator-guide.md` (a section *Repeating a trial*: the starting-point tag, `reset-to-tag.sh`, the three conditions, that a force-push cannot be undone); `README.md` and the other documents: none.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_REPOSITORY=owner/repo\nSITE_RESET_REPOSITORY=owner/other\nSITE_TOKEN_CMD=echo t\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh operator/skill/kumpel/scripts/reset-to-tag.sh starting-point --yes; echo "exit $?"
```

Expect: two lines, `reset-to-tag.sh: owner/repo is not the site's resettable repository` (standard error) and `exit 1`.

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf 'SITE_REPOSITORY=owner/repo\nSITE_TOKEN_CMD=echo t\n' > "$d/site.env"
FACTORY_SITE="$d/site.env" sh operator/skill/kumpel/scripts/reset-to-tag.sh starting-point --yes; echo "exit $?"
```

Expect: two lines, `site: missing SITE_RESET_REPOSITORY in <the file's path>` (standard error) and `exit 2`.

## Journal

1. 2026-11-02 human: created.
2. factory: started intake as vm.
3. intake: 1. The Interface does not name the request that lists the open pull requests for `reset-to-tag.sh`. The stand-in `curl` answers from fixtures per URL, so the coder and the tester must read the same request. It gives no URL (for example `GET /pulls?state=open&per_page=100`), and it does not say whether the script follows pages. Suggestion: name `GET /pulls?state=open&per_page=100`, without paging, and add a sentence saying so.

   2. Interface rule: `reset-to-tag.sh` exits 2 with the `site_require` message when `SITE_REPOSITORY` or `SITE_RESET_REPOSITORY` is unset. Criterion 5 only covers the unset `SITE_RESET_REPOSITORY`, and the smoke test does too. The side where `SITE_REPOSITORY` is unset has no criterion. Suggestion: make criterion 5 three rows (different, reset repository unset, repository unset).

   3. Interface rule: a failing call stops the script and prints the message of `hosting_api`. Criterion 9 tests only a failing `DELETE`. A failing close `PATCH`, a failing move of `main`, and a failing `GET` (the lookup of the tag or the list of pull requests) have no criterion. Suggestion: widen criterion 9 into rows for a failing close, delete and move, with the later requests not sent in each row. Alternatively, say that the other calls are deliberately not tested.

   Findings of the format check: none (it passed).

   The other checks are fine. `merge.sh` has a criterion for each message and for both sides of the wait. The smoke tests are runnable and their `Expect:` lines are checkable. The scripts sit in the skill's `operator/` folder, as the feature's scope says.
4. 2026-11-02 human: All three as you propose: 1 `GET /pulls?state=open&per_page=100`, without paging, said in one sentence; 2 criterion 5 gets the three rows; 3 criterion 9 gets rows for a failing close, delete and move, each with the later requests not sent.
5. factory: started intake as vm.
6. intake: accepted
   - Interface: `merge.sh <pr> <id>` and `reset-to-tag.sh <tag> [--yes]` name the requests, bodies, messages and exit codes. With journal entry 4 the Interface now also names the pull request listing, `GET /pulls?state=open&per_page=100`, without paging.
   - Criteria: every message and rule has a criterion on both sides. Merge refusals, the host refusal, the archive wait on both sides, the three resettable-repository cases (criterion 5, now three rows), the tag cases, `--yes`, the empty reset and the ref-scope check are covered. Criterion 9 is now rows for a failing close, delete and move, each with the later requests not sent. A failing `GET` (the tag lookup or the pull request list) still has no criterion. Entry 4 widened criterion 9 only to close, delete and move, and I did not add more.
   - Smoke test: both commands are runnable (no pytest involved) and each `Expect:` line is checkable against the output and exit status.
   - Architecture: the scripts sit in the skill's `operator/` folder and use the S0001 site loader and the S0003 hosting client. No `src/factory/` code changes.
   - Scope: within the feature's scope item for `merge.sh` and `reset-to-tag.sh`, and not in its "Out of scope". It matches decision 8.

   Edits carried in from journal entry 4 (the human's answer): the sentence naming the pull request listing in the Interface, the three rows of criterion 5, and the rows of criterion 9. I changed nothing else, and the Description is unchanged.
7. factory: started tests as vm.
8. tester: Tests are written, but I had to interpret two criteria, so I'm asking before handing on.

   **Question 1: criterion 3's message and the Interface disagree.** The Interface says `merge.sh` makes its API calls through `hosting_repo_api` and prints the message of `hosting_api`. For `PUT /pulls/5/merge` that message is `hosting: PUT /repos/owner/repo/pulls/5/merge: 405 Pull Request is not mergeable`, because `hosting_repo_api` passes the full `/repos/<repository>` path. Criterion 3 quotes `hosting: PUT /pulls/5/merge: 405 Pull Request is not mergeable`. The options:
   - (a) The message keeps the full path, as `hosting_api` prints it, and criterion 3 is reworded to match. The same holds for the messages of criterion 9.
   - (b) The scripts print the short path, which means they do not pass on `hosting_api`'s own message.
   - (c) The test accepts either form.

   I would choose (a). The tests currently assert (a): `tests/test_operator_merge_reset.py::test_a_merge_the_host_refuses_stops_without_polling` and the three rows of `test_a_failing_call_stops_the_reset_there`.

   **Question 2: the wait for criterion 4's second row.** Criterion 4 puts `KUMPEL_POLL_SECONDS=0` and `KUMPEL_ARCHIVE_WAIT=0` on both rows. With a wait of 0, a third poll can never happen. My reading: the "no archive commit … after 0 s" row uses `KUMPEL_ARCHIVE_WAIT=0`. The "archive subject in the third poll's answer" row uses `KUMPEL_POLL_SECONDS=0` with `KUMPEL_ARCHIVE_WAIT=60`. The other merge tests also run with `KUMPEL_POLL_SECONDS=0` and `KUMPEL_ARCHIVE_WAIT=60`, so they finish quickly. I'd keep that. The other option is that a wait of 0 still allows a fixed number of polls, which the Interface does not state.

   Mapping (all in `tests/test_operator_merge_reset.py`):
   - criterion 1: `test_an_approved_pull_request_is_merged_and_its_archive_awaited`
   - criterion 2: `test_a_pull_request_that_is_not_ready_for_the_merge_is_refused` (rows closed, draft, not-at-approval, another-work-item)
   - criterion 3: `test_a_merge_the_host_refuses_stops_without_polling`
   - criterion 4: `test_the_merge_waits_for_the_archive_commit` (rows no-archive-commit, archive-commit-in-the-third-poll)
   - criterion 5: `test_a_repository_the_site_does_not_name_as_resettable_is_not_reset` (rows another-resettable-repository, no-resettable-repository, no-repository)
   - criterion 6: `test_without_yes_the_reset_prints_its_plan_and_changes_nothing`
   - criterion 7: `test_a_tag_that_does_not_exist_changes_nothing` and `test_the_tag_is_followed_to_its_commit` (rows annotated, lightweight)
   - criterion 8: `test_with_yes_the_reset_closes_deletes_and_moves_in_this_order`
   - criterion 9: `test_a_failing_call_stops_the_reset_there` (rows close, third-delete, move-of-main)
   - criterion 10: `test_a_reset_with_nothing_to_close_or_delete_only_moves_main`
   - criterion 11: `test_no_change_touches_another_ref_or_a_tag` (one row per run of the merge and reset rows that sends requests)
   - criteria 12 and 13: no test (`make check`, docs).

   Files created: `tests/test_operator_merge_reset.py`. No other test file changed.

   The stand-in: S0003's `CURL_STAND_IN` (from `tests/operator_support.py`) answers only by URL, with 200 or 404. These criteria need answers per method, per call number and with any status. So I put a small router named `curl` in front of it, inside the test module. The router reads the request from curl's configuration and picks the status and body for that call's method, path and call number. It then runs S0003's stand-in unchanged as `recording-curl`, which records every request. I checked the router by hand: `hosting_repo_api` through it gives the expected bodies, the 422 and 404 messages, and the recorded method, route and body.

   Not importable: none. Both scripts are missing (`operator/skill/kumpel/scripts/merge.sh`, `reset-to-tag.sh`), so every test fails with `sh: cannot open …`. `make lint` is green. I did not run the type check, as this stage says.
9. 2026-11-02 human: Both as you propose. 1: (a), the message keeps the full path as `hosting_api` prints it; criterion 3 and the messages of criterion 9 are read with the full `/repos/<repository>/...` path. 2: your reading; the no-archive row runs with `KUMPEL_ARCHIVE_WAIT=0`, the third-poll row with `KUMPEL_POLL_SECONDS=0` and `KUMPEL_ARCHIVE_WAIT=60`, and the other merge tests keep 0 and 60. The router in front of S0003's stand-in is fine.
10. factory: started tests as vm.
11. tester: The human's answer in entry 9 confirmed both of my readings. The test file from the earlier tests run already asserts them: messages with the full `/repos/<repository>/...` path, and the archive-wait rows at 0 s and 60 s. So I did not change any test. I rewrote the Description so it says what the answer decided:
    - Criterion 3 now quotes `hosting: PUT /repos/<repository>/pulls/5/merge: 405 …`.
    - Criterion 9 now says its messages carry the full path.
    - Criterion 4 now gives `KUMPEL_ARCHIVE_WAIT=0` for the no-archive row and `KUMPEL_ARCHIVE_WAIT=60` for the third-poll row.

    Mapping (all in `tests/test_operator_merge_reset.py`):
    - criterion 1: `test_an_approved_pull_request_is_merged_and_its_archive_awaited`
    - criterion 2: `test_a_pull_request_that_is_not_ready_for_the_merge_is_refused` (rows: closed, draft, not-at-approval, another-work-item)
    - criterion 3: `test_a_merge_the_host_refuses_stops_without_polling`
    - criterion 4: `test_the_merge_waits_for_the_archive_commit` (rows: no-archive-commit, archive-commit-in-the-third-poll)
    - criterion 5: `test_a_repository_the_site_does_not_name_as_resettable_is_not_reset` (rows: another-resettable-repository, no-resettable-repository, no-repository)
    - criterion 6: `test_without_yes_the_reset_prints_its_plan_and_changes_nothing`
    - criterion 7: `test_a_tag_that_does_not_exist_changes_nothing` and `test_the_tag_is_followed_to_its_commit` (rows: annotated, lightweight)
    - criterion 8: `test_with_yes_the_reset_closes_deletes_and_moves_in_this_order`
    - criterion 9: `test_a_failing_call_stops_the_reset_there` (rows: close, third-delete, move-of-main)
    - criterion 10: `test_a_reset_with_nothing_to_close_or_delete_only_moves_main`
    - criterion 11: `test_no_change_touches_another_ref_or_a_tag` (rows run-1 to run-8)
    - criteria 12 and 13: no test (`make check`, docs)

    Files: `tests/test_operator_merge_reset.py`, created in the earlier tests run and unchanged in this one. No other test file changed. The `curl` router inside the test module, which runs in front of S0003's stand-in, has the human's approval.

    Not importable: none. Every test fails on purpose because `operator/skill/kumpel/scripts/merge.sh` and `reset-to-tag.sh` do not exist yet. I ran `uv run pytest -q tests/test_operator_merge_reset.py` once: all rows fail. `make lint` is green. I skipped the type check, as this stage says.

    The factory left out changes outside the write paths: factory/features/F0048-an-operator-sets-up-from-one-site-file/in-progress/F0048-S0008-merging-an-approved-story-and-resetting-a-trial-repository-to-a-tag-are-commands.md.

    `lint`: lint: green (0.1 s)
    `test`: FAILED tests/test_suite_held_once.py::test_each_shared_helper_and_constant_is_held_once[vm-setup-helpers] - AssertionError: in_order
12. factory: started doing as vm.
13. coder: Implemented both scripts. Every test in `tests/test_operator_merge_reset.py` passes (28). `make check` is red, and only for a reason in that test module, so I'm handing it back for one test change.

    **Test change needed:** `tests/test_operator_merge_reset.py` defines its own top-level `in_order`, and `tests/test_suite_held_once.py::test_each_shared_helper_and_constant_is_held_once[vm-setup-helpers]` asserts that only `vm_support.py` defines `in_order`. The failure: `FAILED tests/test_suite_held_once.py::test_each_shared_helper_and_constant_is_held_once[vm-setup-helpers] - AssertionError: in_order`. The change: drop the module's `in_order` and call `vm_support.in_order("\n".join(printed(result)), [...])` at its five call sites. That falls under the standing leave to use a shared helper; renaming it locally would keep a second copy. Every other part of `make check` was green in the same run: lint, types, layers, sast, secrets, licenses, and the rest of the tests at 99.58 % coverage.

    Built:
    - `operator/skill/kumpel/scripts/merge.sh`: refuses unless the pull request is open, not a draft, labelled `stage:approval` and on `work-item/<id>`. Then it merges with `{"merge_method":"merge"}` and polls `/commits?per_page=20` for `work item <id>: merged, archived`.
    - `operator/skill/kumpel/scripts/reset-to-tag.sh`: needs the site's repository to be equal to its resettable repository. It resolves the tag, following an annotated tag once, and lists the open work-item pull requests and the `work-item/` refs. Without `--yes` it prints the plan. With `--yes` it closes, deletes, then moves `main` by force, and stops at the first failure.
    - Both scripts use `hosting_repo_api` and the site's `SITE_REPOSITORY` directly, not `settings.sh get repository`, so they work with no settings file. They are mode 644 like their sibling scripts and are run with `sh`.

    Main choice: the archive wait in `merge.sh` is ended by the clock (`date +%s` against the start), not by adding up the pauses. With `KUMPEL_POLL_SECONDS=0`, a sum of pauses would never grow and the wait would never end. A wait of 0 still makes one poll. Rejected: a counter of polls (wait divided by pause), which has no answer for a pause of 0.

    Second choice: `reset-to-tag.sh` says `no tag <tag>` only when the tag lookup fails with a 404. Any other failure, such as a missing token or a 401, prints the hosting client's own message. Rejected: reporting every failed lookup as a missing tag.

    Refactor: I read the diff and found nothing to change.

    The smoke test's two commands were run by hand and print exactly the expected lines and exits (`... is not the site's resettable repository` / `exit 1`, `site: missing SITE_RESET_REPOSITORY in <path>` / `exit 2`).

    Noticed, not touched:
    - The tester's rewrite of `## Description` after entry 9 was dropped by the factory (entry 11's note). Criteria 3, 4 and 9 still read with the short path and a wait of 0 on both rows. The tests and code follow the human's answer in entry 9: the full `/repos/<repository>/...` path, and a wait of 60 for the third-poll row. I do not have the work item in my write paths.
    - A failing GET of the pull-request list or the branch list stops the reset with the hosting message, followed by Python's JSON error. No criterion covers this.
    - The docs criterion (13) is the documenter's.
