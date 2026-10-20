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
  instance: self
  stage: intake
  started_at: '2026-10-20T23:04:13.782804Z'
  lease_duration: 60
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
