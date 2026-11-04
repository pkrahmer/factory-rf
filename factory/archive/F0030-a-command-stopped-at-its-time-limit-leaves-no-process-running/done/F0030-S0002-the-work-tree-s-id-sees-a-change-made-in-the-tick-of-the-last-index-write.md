---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 369
comments_read: [6303767591]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T23:04:13.776606Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T23:04:13.782804Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T23:04:33.651815Z'
  stage: intake
  run: 83df897c3be344e7b46ee1bb9243676b
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T23:05:52.546211Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T23:06:10.541077Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T23:06:31.331049Z'
  stage: intake
  run: bd118f63e5884337bf761844911254ee
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T23:06:51.630055Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-20T23:09:40.110337Z'
  stage: tests
  run: 6e4ca5bc08ed4d87a635e0cfecb7fe38
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T23:10:01.027845Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-20T23:12:47.316179Z'
  stage: doing
  run: 1f303dc15dcf414aa89670a2f7e73325
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-20T23:13:08.135749Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-20T23:13:27.298735Z'
  stage: review
  run: 8d5828725ea346e39a041130e63d2d06
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-20T23:13:47.891146Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-10-20T23:14:08.976290Z'
  stage: docs
  run: dc9d476c997e491491492e859fd89bdd
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-20T23:14:29.714199Z'
  stage: smoke-test
- number: 16
  speaker: smoke-tester
  kind: result
  at: '2026-10-20T23:14:52.468677Z'
  stage: smoke-test
  run: 0924069c43d54d2aa75d271ea380de9d
- number: 17
  speaker: factory
  kind: done
  at: '2026-10-20T23:16:13.733571Z'
  stage: approval
---

# The work tree's id sees a change made in the tick of the last index write

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

`GitCli.work_tree_id` builds its tree in a temporary index that copies the checkout's own index with `shutil.copyfile`, so the copy gets the time of the copy as its modification time. Git rehashes a file whose cached stat data still matches only when the file's modification time is not older than the index file's ("racily clean"). The copy's new time removes that guard: a tracked file changed to the same size within the timestamp tick of the last index write keeps matching stat data, git trusts it, and the tree the id names is the tree before the change. `tests/adapters/test_git_cli_work_tree.py::test_the_work_tree_id_is_the_tree_a_commit_records[tracked-ignored-file]` failed this way once under `make check` (F0030-S0001, journal entries 8 and 10, whose coder named the cause). F0030's acceptance reproduced it with plain git: with `copyfile` the temporary index wrote the old tree, with `copy2` the tree of the commit. The id is the key of a known project-command result (F0023), so a stale id could let the factory reuse a passed check for a tree that changed. This story copies the index with its timestamps. The signature of `work_tree_id`, its other rules and the existing tests stay as they are.

## Interface

`factory.adapters.git_cli` (adapters; changed):

```python
def work_tree_id(self, left_out: Sequence[str] = ()) -> TreeId:
    """Stage the work tree in a temporary index, drop the paths left out, write its tree."""
```

- The temporary index is a copy of the checkout's own index with its modification time (`shutil.copy2`, not `shutil.copyfile`), so git's racily-clean rule applies to the copy as it does to the own index.
- Unchanged: a checkout without an index starts from an empty temporary index; `add --all`, `update-index --force-remove --` and `write-tree` as today; the checkout's index, `HEAD`, refs and work tree stay as they are.

Tests (the tester writes them): `tests/adapters/test_git_cli_work_tree_tick.py` (new). The test makes the race certain instead of waiting for it: it sets `core.trustctime false` in the checkout's configuration (`tmp_path / CHECKOUT`, as `tests/adapters/test_git_cli_work_tree.py` reaches it) through `run_git` (a change's ctime is never the cached one otherwise), and sets the modification times of the file and of `.git/index` with `os.utime(..., ns=...)` to one fixed past value. Earlier tests changed: none.

## Acceptance criteria

1. A change in the tick of the last index write is seen (rows of one parametrized test over the `checkout` fixture, with `core.trustctime false`; `kept.log` holds `one\n` with its modification time set to a fixed past value `P` and is committed with `GitCli.commit`; then it is written again and its modification time and that of `.git/index` are set to `P`). Row `same-size`: the new text is `two\n`. Row `other-size`: the new text is `three\n`. In both rows `work_tree_id()` equals `HEAD^{tree}` after the next `GitCli.commit("edit")`. Before this story the row `same-size` fails.
2. `make check` stays green.
3. docs: `docs/project-guide/git-and-hosting.md`, the row of `work_tree_id`: the temporary index is a copy of the checkout's own with its modification time, so git rehashes a file changed in the tick of the last index write. `docs/decisions.md`: an entry *The work tree's id copies the index with its timestamps*, dated with the story. Cause: the flaky row above and the reproduction of F0030's acceptance. Rejected: a fresh index filled by `git read-tree HEAD` (it would rehash every file on every call); `git update-index --really-refresh` on the copy (it rehashes every file as well). `README.md`: none, nothing a newcomer does changes.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git -C "$d" init -q && git -C "$d" config core.trustctime false && printf 'one\n' > "$d/kept.log" && touch -d @1600000000 "$d/kept.log"
uv run -q python - "$d" <<'PY'
import os, subprocess, sys
from pathlib import Path
from factory.adapters.git_cli import GitCli
from factory.domain.git import GitOptions
d = Path(sys.argv[1])
git = GitCli(d, GitOptions())
git.commit("kept")
(d / "kept.log").write_text("two\n")
for path in (d / "kept.log", d / ".git" / "index"):
    os.utime(path, ns=(1_600_000_000_000_000_000,) * 2)
seen = git.work_tree_id()
git.commit("edit")
print(seen == subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD^{tree}"], capture_output=True, text=True).stdout.strip())
PY
```
Expect: `True` (before this story the same block printed `False`)

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: 1. Scope: is this story within F0030? `feature.md` lists a single story, S0001, and its Scope names only `src/factory/domain/sessions.py`, `src/factory/adapters/process.py`, S0001's two test modules and the two docs files. Its Goal is the kill at a time limit. This story changes `src/factory/adapters/git_cli.py` (`work_tree_id`) and adds `tests/adapters/test_git_cli_work_tree_tick.py`. It fixes a different fault, the racily-clean index copy, and only its origin (S0001's flaky row) ties it to the feature. `feature.md` is the human's file, so I do not widen it. Options: (a) the human adds S0002 and its files to the feature's Stories and Scope, then restarts intake; (b) the human confirms the story stays as it is and I accept it on that word; (c) the story moves to its own feature. I would choose (a).

   The rest of the story is buildable, so this is the only blocker.
   - Format check: passed.
   - Interface: concrete. It names `GitCli.work_tree_id` with an unchanged signature and the one change, `shutil.copy2` instead of `shutil.copyfile`.
   - Criteria: criterion 1 is one parametrized test with two rows, `same-size` and `other-size`, each checked against `HEAD^{tree}`. The copy2 clause has its criterion. The "no index starts empty" rule is unchanged and the story says so.
   - Smoke test: runnable, and its `Expect:` line is `True`, which can be checked.
   - Architecture: the change is inside the adapters layer, in the git wrapper, as `CLAUDE.md` requires.
4. 2026-10-20 human: Answer (2026-10-21): (a), done on `main`: F0030's `feature.md` now lists S0002 and S0003 under *Stories* (proposed by the acceptance) and names S0002's files (`src/factory/adapters/git_cli.py`'s `work_tree_id`, `tests/adapters/test_git_cli_work_tree_tick.py`) and S0003's documents under *Scope*. Accept the story.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete. It names `factory.adapters.git_cli.GitCli.work_tree_id` with an unchanged signature, and one change: `shutil.copy2` instead of `shutil.copyfile`. It also lists what stays as it is.
   - Criteria: criterion 1 is one parametrized test with rows `same-size` and `other-size`, each checked against `HEAD^{tree}` after `GitCli.commit("edit")`. The copy2 clause is covered by the `same-size` row, which fails before the change. The unchanged rules (no index starts empty, etc.) add no new behaviour. The two closing criteria (`make check`, `docs:`) are present.
   - Smoke test: runnable. The block builds a throwaway repo and calls the real `GitCli`. Its `Expect:` line is `True`, which the output can be checked against. It runs no pytest, so the `-q` question does not arise.
   - Architecture: the change is inside `factory.adapters`, in the git wrapper, as `CLAUDE.md` requires. The new test module sits under `tests/adapters/`, mirroring the package.
   - Scope: journal entry 4 carries the human's answer to my question 1. F0030's `feature.md` now lists S0002 and names its files under *Scope*. The story is in scope. The story changes no earlier test and adds no dependency or suppression marker.
7. factory: started tests as self.
8. tester: I wrote the test for criterion 1. It fails in the row the story expects, and `make lint` is green.

   - criterion 1: tests/adapters/test_git_cli_work_tree_tick.py::test_a_change_in_the_tick_of_the_last_index_write_is_seen, with rows `same-size` (`two\n`) and `other-size` (`three\n`).
   - criterion 2 (`make check` stays green): no test of its own. The factory's checks cover it.
   - criterion 3 (docs): no test. This is the documenter's work.

   What the test does: it uses the `checkout` fixture and sets `core.trustctime false` through `run_git`. It writes `kept.log` as `one\n`, sets the file's modification time to a fixed past value P, and commits with `GitCli.commit("kept")`. It then rewrites the file with the row's text and sets the modification times of both the file and `.git/index` to P with `os.utime(..., ns=...)`. Finally it checks that `work_tree_id()` equals `HEAD^{tree}` after `GitCli.commit("edit")`.

   Files created: tests/adapters/test_git_cli_work_tree_tick.py. I changed no earlier test.

   Modules the test run could not import: none. `factory.adapters.git_cli` already exists. The test fails for the right reason, a wrong result: `[same-size]` fails with an AssertionError because the id names the old tree. `[other-size]` passes, as the story says it does before the change. Skills: none used.

   `lint`: lint: green (0.5 s)
   `test`: FAILED tests/adapters/test_git_cli_work_tree_tick.py::test_a_change_in_the_tick_of_the_last_index_write_is_seen[same-size] - AssertionError: assert 'eef991509a20...d5ba5d5c0dd69' == '11bdcc0ae77a.....
9. factory: started doing as self.
10. coder: I copied the temporary index with its timestamps. `make check` is green, and the new test passes in both rows.

    - What I built: in `src/factory/adapters/git_cli.py`, `GitCli.work_tree_id` now copies the checkout's own index with `shutil.copy2` instead of `shutil.copyfile`, so the copy keeps the index's modification time. Git's racily-clean rule then applies to the copy as it does to the own index. I added to the comment above the copy why it keeps that time. The signature and the other rules are unchanged: an empty temporary index when the checkout has none, then `add --all`, `update-index --force-remove --` and `write-tree`.
    - Main choice: `copy2`, as the Interface names it. I rejected copying with `copyfile` and then setting the time with `shutil.copystat` or `os.utime`: it does the same thing in two steps instead of one.
    - Refactor: I read my diff once. It is one call plus the comment, and nothing needed changing.
    - Description: unchanged. The journal (entries 3 to 6) settled only the story's scope in F0030, not what the task means.
    - Noticed, not touched: the docs criterion (`docs/project-guide/git-and-hosting.md` and the `docs/decisions.md` entry) is the documenter's work.
    - Skills: none used.

    `check`: check: green
    `duplicates`: duplicates: 6 new, 33 known, 3 gone
11. factory: started review as self.
12. reviewer: no findings

    - Acceptance criteria: criterion 1 is `tests/adapters/test_git_cli_work_tree_tick.py::test_a_change_in_the_tick_of_the_last_index_write_is_seen`, one parametrized test with rows `same-size` (`two\n`) and `other-size` (`three\n`). Each row sets `core.trustctime false` through `run_git`, commits `kept.log` with its modification time at P through `GitCli.commit`, rewrites it, sets the times of the file and of `.git/index` to P, and compares `work_tree_id()` with `HEAD^{tree}` after `commit("edit")`. That makes the racily-clean case certain. The tester's run in entry 8 showed `same-size` failing before the change. The coder's `make check` in entry 10 is green. The Interface adds no new limit or refused input: its one rule, `copy2`, is pinned by the `same-size` row, and the other rules are listed as unchanged.
    - Architecture: the one change is in the git wrapper (`src/factory/adapters/git_cli.py:427`, `shutil.copyfile` -> `shutil.copy2`). There is no new import or process call.
    - Security: there is no new marker, secret or command string.
    - Quality: the comment added above the copy says why the copy keeps the index's time. The test module reuses `CHECKOUT`, `run_git` and `write_files` from `tests/git_support.py`. Nothing else under `tests/` sets file times, so `_set_past_time` copies no existing helper.
    - Work item hygiene: the Description matches what was built (only the copy changed, signature and other rules as before). The coder's entry gives the main choice and what was rejected (`copyfile` plus `copystat`/`utime`). The docs criterion still names what the documenter must write.

    Earlier tests: none. The diff only adds `tests/adapters/test_git_cli_work_tree_tick.py`, with status `A`.
13. factory: started docs as self.
14. documenter: I wrote the two documents the docs criterion names. I found no findings: the code matches the Interface (`src/factory/adapters/git_cli.py` copies the index with `shutil.copy2`), and the added comment there explains why.

    Files changed:
    - `docs/project-guide/git-and-hosting.md`: the `work_tree_id` row now says the temporary index is a copy of the checkout's own with its modification time (`shutil.copy2`). Git's racily-clean rule therefore applies to the copy, and it rehashes a file changed in the tick of the last index write.
    - `docs/decisions.md`: new entry *The work tree's id copies the index with its timestamps*, dated 2026-10-20 (F0030-S0002). It gives the cause (the flaky row from F0030-S0001 and F0030's acceptance reproduction), the decision, and the rejected `git read-tree HEAD` and `update-index --really-refresh`.
    - `README.md`: not changed, as the criterion says (`none`).

    Cross-read and found current against the diff: `docs/project-guide/git-and-hosting.md` (the other rows and the F0023 line at 191), `docs/project-guide/processes-and-checks.md` (the `work_tree_id` use in `KnownResults`), `docs/project-guide/stages.md` (`not_read` and `left_out`), `docs/operator-guide.md` (the `tree` key, line 618) and `README.md`. None of them mentions the index copy or `copyfile`.

    Stale text I noticed and did not touch: none.

    I ran no example and no `make check`: I changed only documents, so the factory's checks after this stage decide. The smoke test in the story is the example to run next.

    `check`: check: green (not run again: passed on tree 4c5c6c3d981c at 2026-10-20T23:11:32Z)
    `secrets`: secrets: green (1.4 s)
    `documents`: documents ok
15. factory: started smoke-test as self.
16. smoke-tester: Smoke test passed with no findings.

    I ran the one block under `## Smoke test` exactly as written, from the repository root, in a single bash shell. It made its own `mktemp -d` folder and removed it on exit through its trap.

    Command: the whole block (a throwaway repo with `core.trustctime false`; `kept.log` committed with `GitCli.commit`, rewritten to the same size, and the times of the file and `.git/index` set to the same past value; then `work_tree_id()` compared with `HEAD^{tree}` after `commit("edit")`).

    ```
    True
    exit=0
    ```

    Expect: `True`. Met.

    Acceptance criteria, read again against the run:
    1. A change in the tick of the last index write is seen: the smoke test runs the `same-size` case (`one\n` to `two\n`) against the real `GitCli` and prints `True`, so the id names the changed tree. Nothing contradicts the `other-size` row. The branch's change is `shutil.copy2(own_index, index)` at `src/factory/adapters/git_cli.py:427`, as the Interface says.
    2. `make check` stays green: the smoke test contradicts nothing here. Entries 10 and 14 report `check: green`, and the factory runs the gate itself.
    3. docs: `docs/decisions.md:970` has the entry *The work tree's id copies the index with its timestamps*, and `docs/project-guide/git-and-hosting.md` is changed. `README.md` is untouched, as the criterion asks. Nothing contradicts it.

    Findings: none. I fixed nothing and changed no file. Skills: none used.
17. factory: done (pull request merged); cost: 7 runs, 4.7 min, 34 turns, 119540 tokens in (476898 more from cache), 9948 out, $0.99
