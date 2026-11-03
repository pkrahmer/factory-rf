---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 508
comments_read: [6592252694]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-11-03T00:43:16.431688Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-03T00:37:52.416522Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-03T00:37:52.423165Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-03T00:38:12.217816Z'
  stage: intake
  run: 8b36bd80e4ae4d96bae6655be9e84bfe
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-03T00:40:03.625516Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-03T00:40:06.684588Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-03T00:40:23.750123Z'
  stage: intake
  run: 44324a0e74c344db9e2dd14b3b2ae243
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-03T00:40:29.410854Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-03T00:43:10.321861Z'
  stage: tests
  run: a59e41e79ac0464ca5ef4cd7c253757c
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-03T00:43:16.431688Z'
  stage: doing
---

# Kumpel signs everything it does

## Description

The Kumpel skill acts on the code host with the human's own token, so its comments, its start commits and its merges look exactly like the human's: on GitHub they carry the human's account, and the factory copies a comment's text into the journal as an entry of the human. Nobody can later tell what the human decided from what the skill decided for them. This story makes the skill sign every act, without a second account and without a change to the factory: a comment ends with a visible signature line and a marker, a start commit has Kumpel as its author, and a merge commit says Kumpel merged it. The signature is text, so it reaches the journal with the comment. Posting goes through one new script, `comment.sh`, so the skill cannot post unsigned; the references say to use it, and they no longer name `gh`. `status.sh` still recognises a verdict when the signature follows it.

## Interface

`operator/skill/kumpel/scripts/comment.sh <pr> <file>` (`sh`, the site and the hosting client of S0001 and S0003)

- Posts the file's text as a comment on pull request `<pr>` through `hosting_repo_api POST /issues/<pr>/comments` with the JSON body `{"body": <text>}`, the text followed by a blank line, the line `— Kumpel, for the human who owns this project` and the line `<!-- kumpel -->`. Prints `commented #<pr>` and exits 0.
- A file that does not exist or is empty: `comment.sh: nothing to post in <file>` on standard error, exit 1, no request. A failing request: the hosting client's message, exit 1. Wrong arguments: `usage: comment.sh <pull request> <file>`, exit 2.
- A text that already ends with the signature and the marker is posted as it is (not signed twice).

`operator/skill/kumpel/scripts/start-story.sh`: the start commit's author and committer are `Kumpel <kumpel@noreply.invalid>` (set for that one commit, not in the checkout's configuration). Every other line stays.

`operator/skill/kumpel/scripts/merge.sh` (S0008): the merge call's body adds `"commit_title": "Merge pull request #<pr> from <head branch>"` (the head branch is the pull request's `head.ref`, from the read `merge.sh` already makes) and `"commit_message": "Merged by Kumpel after the six approval checks."`. Every other rule of S0008 stays.

`operator/skill/kumpel/scripts/status.sh`: a newest comment holds a verdict when `<!-- kumpel verdict -->` is anywhere in its body (today: in its last three lines). The other states keep their rules.

References: `references/answering.md` (*How to post*) and `references/approving.md` (the verdict and a finding) say to post with `comment.sh`; no reference names `gh pr comment`. `SKILL.md` names `comment.sh` in its list of scripts.

Tests: `tests/test_operator_skill_signature.py`, with the `curl` stand-in of `tests/operator_support.py` (recording the request's body) and a real local bare remote for the start commit.

## Acceptance criteria

1. `comment.sh 7 <file>` with the text `Yes, as you propose.` sends one `POST` to `/repos/<repository>/issues/7/comments` whose JSON `body` is the text, a blank line, the signature line and `<!-- kumpel -->`, in that order; it prints `commented #7` and exits 0.
2. A text that already ends with the signature line and the marker is sent unchanged (the signature appears once).
3. The refusals, as rows of one parametrized test: a missing file and an empty file (message, exit 1, no request); a request answered 404 (the hosting client's message, exit 1); no argument and one argument (usage, exit 2).
4. `start-story.sh F0001-S0002` pushes a start commit whose author and committer are `Kumpel <kumpel@noreply.invalid>`, and the clone's `user.name` and `user.email` are unchanged afterwards.
5. `merge.sh` sends the merge body with `merge_method` `merge`, the `commit_title` and the `commit_message` of the Interface (S0008's merge test gains these fields; a row per field).
6. `status.sh` prints `verdict posted` for a newest comment whose body holds `<!-- kumpel verdict -->` followed by the signature line and `<!-- kumpel -->` (five lines after the verdict marker), and still prints `waits: <kind>` when that comment holds a factory marker of a known kind as well. Two more rows: a newest comment without the verdict marker does not print `verdict posted`; the marker at the top of a long body (more than three lines follow it) prints `verdict posted`.
7. No file under `operator/skill/kumpel/` holds `gh pr comment` (a test over the folder's text).
8. `SKILL.md`, `references/answering.md` and `references/approving.md` each contain `comment.sh` (a test over the three files).
9. `make check` stays green.
10. docs: `operator/README.md` (the scripts table: `comment.sh`; a sentence that Kumpel signs its comments, commits and merges); `docs/operator-guide.md`, the skill's part: how a reader tells Kumpel's acts from the human's (the signature line in a comment and in the journal, the commit author, the merge message); `README.md` and the other documents: none.

## Smoke test

```bash
grep -c "Kumpel <kumpel@noreply.invalid>" operator/skill/kumpel/scripts/start-story.sh
grep -rl "gh pr comment" operator/skill/kumpel | wc -l
```

Expect: two lines, a number of at least `1`, then `0`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
3. intake: Format check passed. Questions:

   1. The Interface states that `references/answering.md` (*How to post*) and `references/approving.md` (the verdict and a finding) say to post with `comment.sh`, and that `SKILL.md` names `comment.sh` in its list of scripts. No criterion tests either. Criterion 7 only tests that `gh pr comment` is absent. Two coders could read this two ways and both would pass. Should I add a criterion before the two closing ones? For example: "`SKILL.md`, `references/answering.md` and `references/approving.md` each contain `comment.sh` (a test over the three files)". I would add it.

   2. Criterion 5 and the Interface give `commit_title` as `Merge pull request #<pr> from <head branch>`. They don't say where `merge.sh` gets the head branch. Does it read it from the pull request that S0008's approval checks already fetch, or from somewhere else? The criterion needs a PR stand-in that supplies a head ref, so the story should name the source. I would choose the pull request's `head.ref` from the same read S0008 already makes.

   3. Criterion 6 tests only the accepting side of `status.sh`'s new rule (`<!-- kumpel verdict -->` anywhere in the body). The Interface changes the rule from "last three lines" to "anywhere". Should there be a row where the newest comment has no verdict marker and does not print `verdict posted`? Should there be a row with the marker at the top of a long body, to show that "anywhere" really replaced "last three lines"? I would add both as rows.

   I found no other gaps. The Interface is concrete, `hosting_repo_api` exists in `operator/lib/hosting.sh`, the smoke test commands are runnable and its `Expect:` line is checkable, and the story is inside the feature's scope as S0012.
4. 2026-11-03 human: All three as you propose. 1: add the criterion, `SKILL.md`, `references/answering.md` and `references/approving.md` each contain `comment.sh` (a test over the three files), before the two closing criteria. 2: the head branch is the pull request's `head.ref` from the read S0008's `merge.sh` already makes. 3: add both rows to criterion 6, a newest comment without the verdict marker (no `verdict posted`), and the marker at the top of a long body (`verdict posted`).
5. factory: started intake as vm.
6. intake: accepted. I carried in the human's answers from journal entry 4 (all three as I proposed); that is their edit, not mine: (1) a new criterion 8, "`SKILL.md`, `references/answering.md` and `references/approving.md` each contain `comment.sh`", before the closing two, which are now 9 and 10; (2) the Interface's `merge.sh` line now says the head branch is the pull request's `head.ref`, from the read `merge.sh` already makes; (3) criterion 6 gained two rows, a newest comment without the verdict marker (no `verdict posted`) and the marker at the top of a long body (`verdict posted`).
   - Interface: `comment.sh`, `start-story.sh`, `merge.sh` and `status.sh` are named with concrete behaviour, messages and exit codes. `hosting_repo_api` exists in `operator/lib/hosting.sh`. The head branch source is now stated.
   - Criteria: each is testable by one test function. Every Interface behaviour has one: signing (1), no double signing (2), the refusals on both sides (3), the start commit author and unchanged config (4), the merge body fields (5), the verdict rule on both sides (6), the references and `SKILL.md` naming `comment.sh` (8), no `gh pr comment` (7).
   - Smoke test: both commands are runnable, and the `Expect:` line (a number of at least 1, then 0) can be checked against the output. Neither runs pytest.
   - Architecture: scripts and references under `operator/skill/kumpel/`, a test under `tests/` with the shared stand-ins. Nothing in `src/factory/` changes.
   - Scope: this is S0012 of the feature's scope and its stories list, and not in its Out of scope.
7. factory: started tests as vm.
8. tester: Wrote the tests of every criterion. `make lint` is green. I skipped the type check, as this stage's instructions say.

   Criterion → test:
   - criterion 1: tests/test_operator_skill_signature.py::test_a_comment_is_posted_with_the_signature_and_the_marker
   - criterion 2: tests/test_operator_skill_signature.py::test_a_signed_text_is_posted_unchanged
   - criterion 3: tests/test_operator_skill_signature.py::test_a_comment_that_cannot_be_posted_is_refused. Rows: missing-file, empty-file, 404, none, one.
   - criterion 4: tests/test_operator_skill_signature.py::test_the_start_commit_is_kumpels_and_the_clone_keeps_its_identity. The run's environment carries no GIT_AUTHOR_*/GIT_COMMITTER_* variables, so the identity has to come from the script. The clone has its own `user.name`/`user.email`, and the test checks they are unchanged afterwards.
   - criterion 5: tests/test_operator_merge_reset.py::test_an_approved_pull_request_is_merged_and_its_archive_awaited (S0008's merge test, as the criterion names it). It is now parametrized with one row per field: merge-method, title (`Merge pull request #5 from work-item/F0001-S0001`), message. The PUT is still checked to go to `/pulls/5/merge` once.
   - criterion 6: tests/test_operator_skill_signature.py::test_a_verdict_marker_anywhere_in_the_newest_comment_is_a_posted_verdict. Rows: signed-verdict (five lines after the verdict marker), signed-verdict-and-factory-marker (`waits: question`), no-verdict-marker (`working`), verdict-marker-at-the-top.
   - criterion 7: tests/test_operator_skill_signature.py::test_no_file_of_the_skill_posts_with_gh
   - criterion 8: tests/test_operator_skill_signature.py::test_the_skill_names_the_comment_script (one row per file)

   Files created:
   - tests/test_operator_skill_signature.py
   - tests/operator_skill_support.py, a shared support module.

   Earlier test files I changed:
   - tests/test_operator_skill_scripts.py, under CLAUDE.md's standing leave to move a shared test helper. Its `Operator` machine, the constants SCRIPTS/REPOSITORY/PREFIX/API_URL/ACCESS_COMMAND/GIT_VARIABLES/ARCHIVE and the helpers `make_bare_remote`, `pull`, `comment_routes`, `commits`, `status_routes` moved to tests/operator_skill_support.py. Its `operator` fixture moved to tests/conftest.py, which builds it with `make_operator`. Every test there keeps its name and checks the same thing.
   - tests/test_operator_skill_scripts.py, beyond that leave: I removed the row `verdict-fourth-from-the-end` from `test_the_newest_comment_decides_the_state`. It expected `working` for a verdict marker with three lines after it. The Interface's new rule ("anywhere in its body") says that case is `verdict posted`, and criterion 6's verdict-marker-at-the-top row now covers it. If you want that row kept and turned to `verdict posted` instead, say so.
   - tests/test_operator_merge_reset.py: the change to S0008's merge test described under criterion 5, which the criterion names.

   The run, `uv run pytest -q` on the three files, failed as expected. Criteria 1–3 fail because the script `comment.sh` does not exist. Criterion 4 fails on the old author. Criterion 5 fails in the title and message rows. Criterion 6 fails in the top-of-body row. Criterion 8 fails because the skill's three files don't mention `comment.sh` yet. Every module imported; the test runner had no import errors.

   Open: none.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
