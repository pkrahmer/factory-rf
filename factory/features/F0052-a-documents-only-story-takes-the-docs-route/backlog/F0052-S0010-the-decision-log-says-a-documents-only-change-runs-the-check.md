# The decision log says that a documents-only change runs the check again
<!-- proposed by feature acceptance of 2026-11-06; refine before starting -->

## Description

`docs/decisions.md` contradicts itself on what happens to `make check` after a documents-only change. The entry *A documents-only story takes the docs route* still says, in its bullet on the smoke test, that "`make check` reuses its result when only documents changed". The later line under *A known result is not checked again* (F0052-S0008) says the opposite: `check`'s `not_read` keeps `README.md` and `docs/*.md` in the key, so a documents-only change runs `make check` again. The second is what the shipped `factory/pipeline.yml` does: the third acceptance of F0052 changed `not_read`, and the fourth acceptance's smoke test shows the key changing after a documents-only change. A reader of the docs route's entry learns the old rule. This story corrects that one bullet, so that it agrees with the known results' entry and names it. The rest of the entry stays as it is. The decision log is out of scope for the rewrite (F0054), so no later story will fix this.

## Interface

- `docs/decisions.md`, entry *A documents-only story takes the docs route*, the bullet that starts "There is no smoke test on the docs route": its last clause says that `make check` runs after `docs-only`, and that a passed result is reused only when nothing outside `check`'s `not_read` changed, which a changed document under `README.md` or `docs/` (other than `docs/runs/`) always is. It names the known results' decision of F0052-S0008. The wording is the documenter's, by `docs/project-guide/style.md`.
- No other line of `docs/decisions.md` changes. No code and no test changes.

## Acceptance criteria

1. In `docs/decisions.md`, the entry *A documents-only story takes the docs route* no longer says that `make check` reuses its result when only documents changed; it says that a documents-only change runs `make check` again, and names F0052-S0008. An entry that still holds "reuses its result when only documents changed" fails this criterion.
2. `git diff main -- docs/decisions.md` changes only lines inside that entry's bullet on the smoke test; a change to any other line of the file fails this criterion.
3. `make documents` prints `documents ok`.
4. `make check` stays green.
5. docs: `docs/decisions.md`, as above. `docs/operator-guide/`: none, because F0052-S0008 already wrote it there. `docs/project-guide/`: none, because it does not describe the reuse of the check. `README.md`: none.

## Smoke test

```bash
grep -c 'reuses its result when only documents changed' docs/decisions.md
```
Expect: `0`

```bash
sed -n '/^## A documents-only story takes the docs route/,/^## The documents follow/p' docs/decisions.md | grep -c 'F0052-S0008'
```
Expect: `1`

```bash
make documents 2>&1 | tail -1
```
Expect: `documents ok`

## Journal
