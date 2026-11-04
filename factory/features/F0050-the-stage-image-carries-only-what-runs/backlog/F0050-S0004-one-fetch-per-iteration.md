# One fetch per iteration

## Description

Since F0049-S0003 and S0004 the factory fetches twice in every iteration: once before the tick, where it compares the stage file on a new `main` (`_ProjectImageStart._follow_main` in `factory.entry.run`), and once more at the start of the tick itself (`factory.application.tick`). The second fetch finds nothing new in almost every case, but it costs a call to the remote and its time in every iteration, and both places raise and clear `fetch_failed` on their own. This story makes the factory fetch once per iteration: the fetch before the tick serves the tick too, and `fetch_failed` is raised and cleared in one place. What the tick sees of `origin/main` and of the work-item branches does not change.

## Interface

- One iteration of `factory-run` calls `Git.fetch` once. The coder decides which of the two places keeps it and how the other learns that the fetch was made; the tick still works on a fresh `origin/main` and fresh work-item branches.
- A failed fetch stands as `fetch_failed` (S0004 of F0049), raised in one place, and ends the iteration without a tick; a passed fetch clears it.
- `factory-watch` and every other caller of the tick keep fetching as today, when they run the tick without the fetch before it.

## Acceptance criteria

1. One iteration of `factory-run` with a passed fetch calls `Git.fetch` exactly once and runs the tick on what that fetch brought: rows for a new commit on `main` and for a new commit on a work-item branch, each seen by the same iteration's tick.
2. One iteration with a failed fetch calls `Git.fetch` once, raises `fetch_failed` with the fetch's first line in its detail, and runs no tick; the next iteration with a passed fetch clears the stop and runs the tick.
3. A tick run without the fetch before it (as `factory-watch` runs it) still fetches once.
4. `make check` stays green.
5. docs: `docs/project-guide/` in the file on the tick or the stage environment: where the iteration fetches, once. `docs/operator-guide.md` and `docs/decisions.md`: none, unless an existing sentence says the tick fetches; then that sentence follows. `README.md`: none.

## Smoke test

```bash
grep -rn 'git.fetch()' src/factory/application src/factory/entry | wc -l
uv run pytest tests/entry tests/application -q -k fetch 2>&1 | tail -1
```

Expect: a number not larger than before the story (3 on `main` when it was written), then a line that ends in `passed` with no `failed`.

## Journal
