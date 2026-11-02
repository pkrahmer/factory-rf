# Merging an approved story and resetting a trial repository to a tag are commands

## Description

Two acts of whoever drives a factory run were done by hand with the hosting API on 2026-11-02, and both are easy to get wrong. Merging a story: it must be an open, ready pull request at the approval stage, merged with a merge commit (the factory reads a story's state from its branch), and the next story may be started only after the factory has archived the merged one. Resetting a trial repository to its starting-point tag so that a run can be repeated: it closes the run's pull requests, deletes its work-item branches and moves `main` back by force, the one act of these scripts that cannot be undone. This story adds `merge.sh` and `reset-to-tag.sh` to the skill's scripts. Merging checks before it acts and waits for the archive commit. The reset needs `--yes`, a repository that the site names as resettable and that is the repository the commands work on (so the factory's own repository can never be its target), and a tag that exists; it works through the API, with no checkout. Neither script judges whether a story deserves a merge: that stays with the skill's rules (`references/approving.md`).

## Interface

`operator/skill/kumpel/scripts/merge.sh <pr> <id>` and `reset-to-tag.sh <tag> [--yes]` (`sh`, the site and the hosting client of S0001 and S0003; the API calls through `hosting_repo_api`)

- `merge.sh`: reads `GET /pulls/<pr>`. It stops with exit 1 and `merge.sh: #<pr> is not open` when the state is not `open`, with `merge.sh: #<pr> is a draft` when it is a draft, and with `merge.sh: #<pr> is not at stage:approval` when no label is `stage:approval`; it also stops with `merge.sh: #<pr> is not the pull request of <id>` when the head branch is not `work-item/<id>`. Otherwise it calls `PUT /pulls/<pr>/merge` with `{"merge_method":"merge"}`; when the answer is not a success it prints the message of `hosting_api` and exits 1. It then polls `GET "/commits?per_page=20"` every `${KUMPEL_POLL_SECONDS:-15}` seconds for at most `${KUMPEL_ARCHIVE_WAIT:-300}` seconds for a commit subject `work item <id>: merged, archived`. It prints `merged #<pr>` after the merge and `archived <id>` when the commit is there (exit 0); when the wait ends first it prints `merge.sh: merged, but no archive commit for <id> after <N> s` and exits 1.
- `reset-to-tag.sh`: needs `SITE_REPOSITORY` and `SITE_RESET_REPOSITORY`; it exits 1 with `reset-to-tag.sh: <repository> is not the site's resettable repository` unless they are equal, and 2 with the `site_require` message when one is unset. It resolves the tag with `GET /git/ref/tags/<tag>` (an `object.type` of `tag` is followed once with `GET /git/tags/<sha>` to its `object.sha`; a `commit` is the commit); a tag that does not exist exits 1 with `reset-to-tag.sh: no tag <tag>`.
- Without `--yes` it prints the plan and exits 1: `would close <n> open work-item pull request(s)`, `would delete <m> work-item branch(es)`, `would move main to <the first 7 characters of the commit>`, then `run again with --yes`. With `--yes` it does it in this order, printing one line for each: `closed #<n>` for each open pull request whose head branch starts with `work-item/` (`PATCH /pulls/<n>` with `{"state":"closed"}`), `deleted <branch>` for each ref of `GET /git/matching-refs/heads/work-item/` (`DELETE /git/refs/heads/<branch>`), `moved main to <7 characters>` (`PATCH /git/refs/heads/main` with `{"sha":"<commit>","force":true}`). A failing call stops the script there with its message and exit 1, so that a half reset is visible.
- It never touches another branch, a tag, or a pull request that is not a work item's.

Tests: `tests/test_operator_merge_reset.py` with the `curl` stand-in of S0003's tests, which records every request (method, URL, body from its standard input) and answers from fixtures per row.

## Acceptance criteria

1. `merge.sh 5 F0001-S0001` for an open, ready pull request labelled `stage:approval` with the head `work-item/F0001-S0001` sends one `PUT /pulls/5/merge` with the body `{"merge_method":"merge"}`, prints `merged #5`, polls, and with the archive commit in the answer prints `archived F0001-S0001` and exits 0.
2. The refusals, as rows of one parametrized test: a closed pull request, a draft, one without the `stage:approval` label, and one whose head is another work item each print their message, exit 1 and send no `PUT`.
3. A merge the host refuses (405 with `{"message":"Pull Request is not mergeable"}`) prints `hosting: PUT /pulls/5/merge: 405 Pull Request is not mergeable`, exits 1 and does not poll.
4. The archive wait, with `KUMPEL_POLL_SECONDS=0` and `KUMPEL_ARCHIVE_WAIT=0`: a commit list without the archive subject prints the `no archive commit` line with `after 0 s` and exits 1; the archive subject in the third poll's answer gives `archived` (the stand-in answers per call number).
5. `reset-to-tag.sh` with `SITE_REPOSITORY` and `SITE_RESET_REPOSITORY` different, or the second unset, sends no request that changes anything and exits as the Interface says (two rows).
6. Without `--yes` it sends only `GET` requests, prints the plan with the counts of the fixture (two open work-item pull requests and a third that is not a work item, three `work-item/` branches) and exits 1.
7. A tag that does not exist (404) exits 1 with `reset-to-tag.sh: no tag <tag>` and sends no change; an annotated tag is followed to its commit, a lightweight one is used directly (two rows, the commit of the move is the same).
8. With `--yes` the requests that change come in the order of the Interface: a `PATCH` closing each work-item pull request (and none for the other), a `DELETE` for each `work-item/` ref, and a `PATCH` of `/git/refs/heads/main` with `{"sha":"<commit>","force":true}` last; the printed lines are `closed #<n>`, `deleted <branch>` and `moved main to <7 characters>`.
9. A failing call stops the script: with the third `DELETE` answered 422, the later `DELETE`s and the move are not sent, the message of `hosting_api` is printed and the exit status is 1.
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
