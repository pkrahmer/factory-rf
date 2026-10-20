# The decision log says why an un-ignored path is accepted

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0027's `feature.md` decision 7 accepts that an agent can un-ignore a path inside its write paths, and adds no rule against it. A nested `.gitignore` with `!__pycache__/` in `src/` makes a `.pyc` there untracked and not ignored. `remove_ignored()` then keeps it, and it is committed with the result and shows in the pull request's diff, where the reviewer and the human see it. The undo removes it when it lies outside the stage's write paths. Inside the tool paths no `.gitignore` takes effect, since git does not read the rules of an ignored folder. An agent cannot write the protected root `.gitignore` or `.git/info/exclude` (the kernel's rules and the seal). That reason reached no document. The entry *The factory removes the git-ignored paths after every agent run and at the restore* in `docs/decisions.md` names the feature's decisions 2 and 4 to 7 in its date line, but it says nothing of decision 7. So a later story that finds an un-ignored file in a diff has no record that this was weighed and accepted, and may add a rule the feature chose not to add. This story adds one bullet to that entry. No code, test or other document changes.

## Interface

None: documents only (`docs/decisions.md`). No module under `src/factory/` and no test changes.

## Acceptance criteria

1. Nothing under `src/` or `tests/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/decisions.md`, the entry *The factory removes the git-ignored paths after every agent run and at the restore*, gains a bullet that starts `Accepted: an agent can un-ignore a path`, after its `Rejected:` bullet and before its `Test children (F0027-S0004)` bullet. It says that a nested `.gitignore` in a write path with a negated rule (`!__pycache__/`) makes the path untracked and not ignored, so `remove_ignored()` keeps it. It says why that is accepted: the path is committed with the result and shows in the pull request's diff; the undo removes it outside the stage's write paths; no `.gitignore` takes effect inside an ignored tool path, because git does not read the rules of an ignored folder; and an agent cannot write the root `.gitignore` or `.git/info/exclude`. So nothing is hidden, and no rule is added (F0027 decision 7). `README.md`, `docs/operator-guide.md` and `docs/project-guide/`: none, since no behaviour changes.

## Smoke test

```bash
grep -c "Accepted: an agent can un-ignore a path" docs/decisions.md
```
Expect: `1`

```bash
git diff --name-only origin/main -- src tests | wc -l
```
Expect: `0`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
