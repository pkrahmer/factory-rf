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
  started_at: '2026-10-19T21:22:58.323204Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T21:22:58.315978Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T21:22:58.323204Z'
  stage: intake
---

# The git wrapper leaves out a path that starts with a dash

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

`GitCli.work_tree_id(left_out)` (S0001) removes the left-out paths from its temporary index with `git update-index --force-remove -- <paths>`. The `--` is what makes git read a path that starts with `-` as a path and not as an option. No test has such a path, so the feature acceptance's `make mutants` found a surviving mutant that replaces `--` with another word: every test still passes. The acceptance ran the case by hand on today's code and it works, so this story adds the missing criterion and its test, and expects no code change. It is for the operator whose project holds a file such as `-notes.md` in a folder its `not_read` names: without the `--`, the key would fail and the command would run every time. Nothing else of `work_tree_id` changes; S0001's tests stay as they are.

## Interface

No module under `src/factory/` changes. `factory.adapters.git_cli` (`adapters`): `GitCli.work_tree_id(left_out=())` as S0001 built it. The rule this story pins:

- A left-out path that starts with `-` or `--` is removed from the tree as a literal path, as any other listed path is, and the call raises no error.

Tests (the tester writes them): `tests/adapters/test_git_cli_work_tree_dash.py`, with the `checkout` fixture of `tests/conftest.py` and `CHECKOUT`, `run_git` and `write_files` of `tests/git_support.py`, as `tests/adapters/test_git_cli_work_tree.py` uses them. No earlier test changes.

## Acceptance criteria

1. On a work tree whose root holds `a.md`, `-x.md` and `--y.md` (rows of one parametrized test): `work_tree_id(["-x.md", "--y.md"])` equals `work_tree_id()` after `-x.md` and `--y.md` are removed from the work tree. `work_tree_id(["-x.md"])` equals `work_tree_id()` after only `-x.md` is removed, and `--y.md` still counts. `work_tree_id(["-*"])` equals `work_tree_id()` after `-x.md` and `--y.md` are removed, and `a.md` still counts. `work_tree_id(["a.md"])` equals `work_tree_id()` after only `a.md` is removed, and both dash files still count.
2. `make check` stays green.
3. docs: none. `docs/project-guide/git-and-hosting.md` already says that the left-out paths are removed as literal paths with `update-index --force-remove --`.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
git init -q --initial-branch=main "$d/w"
printf 'a\n' > "$d/w/a.md"
printf 'x\n' > "$d/w/-x.md"
printf 'y\n' > "$d/w/--y.md"
uv run -q python - "$d/w" <<'EOF'
import sys
from pathlib import Path
from factory.adapters.git_cli import GitCli

w = Path(sys.argv[1])
git = GitCli(w)
left = git.work_tree_id(["-x.md", "--y.md"])
(w / "-x.md").unlink()
(w / "--y.md").unlink()
print(left == git.work_tree_id())
EOF
```
Expect: `True`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
