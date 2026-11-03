---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-03T00:37:52.423165Z'
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

`operator/skill/kumpel/scripts/merge.sh` (S0008): the merge call's body adds `"commit_title": "Merge pull request #<pr> from <head branch>"` and `"commit_message": "Merged by Kumpel after the six approval checks."`. Every other rule of S0008 stays.

`operator/skill/kumpel/scripts/status.sh`: a newest comment holds a verdict when `<!-- kumpel verdict -->` is anywhere in its body (today: in its last three lines). The other states keep their rules.

References: `references/answering.md` (*How to post*) and `references/approving.md` (the verdict and a finding) say to post with `comment.sh`; no reference names `gh pr comment`. `SKILL.md` names `comment.sh` in its list of scripts.

Tests: `tests/test_operator_skill_signature.py`, with the `curl` stand-in of `tests/operator_support.py` (recording the request's body) and a real local bare remote for the start commit.

## Acceptance criteria

1. `comment.sh 7 <file>` with the text `Yes, as you propose.` sends one `POST` to `/repos/<repository>/issues/7/comments` whose JSON `body` is the text, a blank line, the signature line and `<!-- kumpel -->`, in that order; it prints `commented #7` and exits 0.
2. A text that already ends with the signature line and the marker is sent unchanged (the signature appears once).
3. The refusals, as rows of one parametrized test: a missing file and an empty file (message, exit 1, no request); a request answered 404 (the hosting client's message, exit 1); no argument and one argument (usage, exit 2).
4. `start-story.sh F0001-S0002` pushes a start commit whose author and committer are `Kumpel <kumpel@noreply.invalid>`, and the clone's `user.name` and `user.email` are unchanged afterwards.
5. `merge.sh` sends the merge body with `merge_method` `merge`, the `commit_title` and the `commit_message` of the Interface (S0008's merge test gains these fields; a row per field).
6. `status.sh` prints `verdict posted` for a newest comment whose body holds `<!-- kumpel verdict -->` followed by the signature line and `<!-- kumpel -->` (five lines after the verdict marker), and still prints `waits: <kind>` when that comment holds a factory marker of a known kind as well.
7. No file under `operator/skill/kumpel/` holds `gh pr comment` (a test over the folder's text).
8. `make check` stays green.
9. docs: `operator/README.md` (the scripts table: `comment.sh`; a sentence that Kumpel signs its comments, commits and merges); `docs/operator-guide.md`, the skill's part: how a reader tells Kumpel's acts from the human's (the signature line in a comment and in the journal, the commit author, the merge message); `README.md` and the other documents: none.

## Smoke test

```bash
grep -c "Kumpel <kumpel@noreply.invalid>" operator/skill/kumpel/scripts/start-story.sh
grep -rl "gh pr comment" operator/skill/kumpel | wc -l
```

Expect: two lines, a number of at least `1`, then `0`.

## Journal

1. 2026-11-03 human: created.
2. factory: started intake as vm.
