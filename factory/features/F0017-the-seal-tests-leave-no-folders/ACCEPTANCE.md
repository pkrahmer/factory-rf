---
stage: accept
pr: 215
blocked: null
comments_seen: 0
round: 0
attempts: 0
stories: [F0017-S0001]
---
# Acceptance of The seal tests leave no folders

## Verdict

**accepted with drafts.** The one story, S0001, delivers all three scope items. The feature demo shows the promise end to end: with the real `tests/conftest.py`, five failing sessions that leave `.git` at `0o020` (what the `_close` mutant does) leave no `garbage-*` folder, and the root comes out with a plain `rm -rf`. Without it, two `garbage-*` folders build up and `rm -rf` fails. The human's change 1 is in the `Makefile`, and a real `make mutants FEATURE=F0014` run (4 timeouts) left `/tmp/pytest-of-factory` and `/tmp` as it found them. One gap is worth a story: no document explains that `make mutants` now runs under a temporary root of its own, or why.

## 1 Scope

None. Each of the three scope items has its story, S0001, and the code matches its Interface:
- `reopen(root)` in `tests/tmp_path_support.py` works top down, with links neither changed nor followed and a missing root no error.
- The autouse fixture `reopened_tmp_path` is in `tests/conftest.py`. Nothing else in that file changed.
- The child-pytest test is `tests/test_tmp_path_reopening.py::test_a_test_that_closes_folders_in_its_tmp_path_leaves_them_open_after_its_teardown`.
- The project-guide sentence is at `docs/project-guide.md:221` and the decision-log entry at `docs/decisions.md:528`.

No story strays outside the scope. Nothing under `src/` changed, and no earlier test module changed. The Goal's second half, that a `make mutants` run leaves nothing in `/tmp/pytest-of-<user>`, belongs to the human's change 1, not to a story. That change is on `main` (`Makefile`, the `mutants:` recipe, `temporary=$$(mktemp -d)`, the `EXIT` trap, `TMPDIR="$$temporary" timeout …`), exactly as FEATURE.md words it. The Goal's "done when S0001 is merged and `make check` is green" holds: `make check` printed `check: green` on this branch (`test: green (34.9 s)`, coverage 99.47 %).

## 2 Feature demo

The feature exists for whoever runs factory-rf's tests. The demo runs a failing test five times, the way a test fails under the `_close` mutant, in sessions that share one pytest root. It compares the project's `tests/conftest.py` loaded (`-p conftest`, `PYTHONPATH=tests`) with the same runs without it. The project's own `tmp_path_retention_policy = failed` applies, so each failed folder is kept, and pytest removes everything older than three sessions. The script lives outside the repository, in `/tmp/f0017-scripts/feature_demo.sh`. It builds a scratch project under `mktemp -d` holding this test:

```python
def test_seal_under_the_mutant(tmp_path: Path) -> None:
    git = tmp_path / "checkout" / ".git"
    (git / "objects").mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    git.chmod(0o020)
    assert False, "the mutant closed .git"
```

For each variant, it runs this five times with `TMPDIR` set to a root of the variant's own:

`.venv/bin/python -m pytest -q -p no:cacheprovider -c pytest.ini --rootdir <project> [-p conftest] test_mutant_seal.py`

It then lists `pytest-of-factory` and tries `rm -rf` with no `chmod`.

```
$ /tmp/f0017-scripts/feature_demo.sh
== with-conftest: five sessions, TMPDIR=/tmp/tmp.rWNCbeRvQU/with-conftest
session 1: exit 1 / 1 failed in 0.02s
session 2: exit 1 / 1 failed in 0.02s
session 3: exit 1 / 1 failed in 0.02s
session 4: exit 1 / 1 failed in 0.02s
session 5: exit 1 / 1 failed in 0.02s
left in /tmp/tmp.rWNCbeRvQU/with-conftest/pytest-of-factory:
      1 pytest-2
      1 pytest-3
      1 pytest-4
      1 pytest-current
rm -rf (no chmod): removed
== without-conftest: five sessions, TMPDIR=/tmp/tmp.rWNCbeRvQU/without-conftest
session 1: exit 1 / 1 failed in 0.01s
session 2: exit 1 / 1 failed in 0.01s
session 3: exit 1 / 1 failed in 0.01s
session 4: exit 1 / 1 failed, 6 warnings in 0.01s
session 5: exit 1 / 1 failed, 9 warnings in 0.01s
left in /tmp/tmp.rWNCbeRvQU/without-conftest/pytest-of-factory:
      2 garbage-<uuid>
      1 pytest-2
      1 pytest-3
      1 pytest-4
      1 pytest-current
rm -rf (no chmod): FAILED
```

Green. With the fixture, pytest's own cleanup removed `pytest-0` and `pytest-1` and left no `garbage-*`. Without it, every session from the fourth on warns about the folders it cannot remove, and the leftovers pile up. This is the night log's situation in miniature.

The Goal's second half, the human's change 1, measured on a real run around `make mutants FEATURE=F0014` (the feature that changed `git_cli.py`, so the `_close` mutants run). `MUTANTS_SECONDS=480` stayed inside the shell's 10 minutes:

```
$ ls -A /tmp/pytest-of-factory | wc -l; ls -d /tmp/tmp.*
0
$ make mutants FEATURE=F0014 MUTANTS_SECONDS=480     # 12:03:39 → 12:11:42 UTC
5918/12267  🎉 5634 🫥 0  ⏰ 4  🤔 0  🙁 280  🔇 0  🧙 0
mutants: stopped after 480 s; the results below are partial, run it again to go on
exit 0
$ ls -A /tmp/pytest-of-factory | wc -l; ls -d /tmp/tmp.*
0
```

The 4 timeouts (⏰) are runs that mutmut stopped, and so exactly the locked `pytest-*` folders that FEATURE decision 7 is about. The stop at `MUTANTS_SECONDS` is the trap's other case. Afterwards `/tmp/pytest-of-factory` was still empty, and no `mktemp` folder was left in `/tmp`.

## 3 Mutation score

`make mutants FEATURE=F0017` printed `mutants: no module under src/factory changed by F0017` and exited 0: **0/0**. The feature changed only `tests/` and `docs/`, and mutmut mutates `src/factory` only. Two consequences:
- The new helper `reopen` is not measured by mutation. Its rows pin each mode exactly, which leaves little room for a surviving change.
- Its two defensive branches have no test, and coverage counts `src/factory` only, so nothing reports that gap. One branch is a root that is a symbolic link. The other is a root that is a file. See 4.

For context only, not this feature's: the F0014 run above listed 280 survivors in its partial results, among them two in `_close` (`x__close__mutmut_5`: `mode & SHARED_WRITE` → `mode | SHARED_WRITE`, an all but equivalent mutant; `x__close__mutmut_10`: the `RepositoryUnsealed` message → `None`). They belong to F0014's modules and its acceptance. No draft here.

## 4 What the stories noticed

- Reviewer (entry 5): the `reopen` branches for a root that is a symbolic link and for a root that is a file are defensive and never reached. The Interface names neither case, and no test covers them. Low weight: `tmp_path` is always a real folder. No draft. If the human wants them pinned, two rows of `test_reopen_of_a_missing_root_changes_nothing`'s kind would do it.
- Reviewer (entry 5): did not run `make check` itself and relied on the coder's `check: green`. The factory's gate ran it after review anyway, and it is green here.
- Coder (entry 4): nothing noticed; there was nothing to build.
- Documenter (entry 6): "Nothing stale seen outside this story".
- Demo (entry 7): nothing open.

## 5 Documentation as a whole

One finding. The human's change 1 is documented nowhere but in the `Makefile`'s own comment. `docs/project-guide.md`'s *Mutation testing* section (line 1734 on) describes what `make mutants` runs and how its ends look, but not that the recipe:
- runs mutmut with `TMPDIR` set to a `mktemp -d` folder,
- opens and removes that folder in an `EXIT` trap, also after a stop at `MUTANTS_SECONDS`,
- and so leaves `/tmp/pytest-of-<user>` as it found it.

`docs/decisions.md` has no entry for decision 7 or for the ways it rejected (`tmp_path_retention_policy=none`, `--basetemp`, a session sweep, `PYTEST_DEBUG_TEMPROOT`). The entry *The tests reopen their tmp_path after every test* names only the `garbage-*` cause. It never says that the locked `pytest-*` folders, half of the night log's count, are handled elsewhere, so a reader could think the fixture covers both. Nothing contradicts behaviour, so this is not a misleading contradiction. It is a section the feature made necessary that nobody could write, because no stage writes the `Makefile` and the documenter saw only S0001's diff. Draft F0017-S0002.

Otherwise none. I read `README.md` and the three guides for tmp folders, `pytest-of`, `garbage` and `mutants`. The new project-guide sentence and the decision entry agree with each other and with the code. `docs/operator-guide.md:427` (pytest's `0700` folders left out of the disk record's size) is still true. The early *No `mutants` target, no mutmut* entry is superseded explicitly by *Mutation testing is limited to one feature's modules*.

## 6 Decisions taken for the human

From FEATURE.md (*Decisions taken for the human*) and the story's log. No story log recorded a further answer or default.
1. The cause analysis: `make test` leaves nothing behind under the built code. The `garbage-*` folders come from the `_close` mutant, and the locked `pytest-*` folders from mutmut's stopped runs (FEATURE 1).
2. One autouse fixture for every test that uses `tmp_path`, not one for the seal tests alone (FEATURE 2).
3. The work sits in the helper `reopen` in a support module, and the fixture is thin. The fixture is proven in a child pytest with `-p conftest`, not with `pytester` and not with a structural test (FEATURE 3).
4. No `sudo`, no second user, no caught error (FEATURE 4).
5. `reopen` adds only the owner's bits, keeps setgid and the group and others bits, follows no link, and treats a missing root as no error (FEATURE 5).
6. **The leave for `tests/conftest.py`**, taken by the session for the human and marked "to confirm". The earlier tests' own `finally` blocks and reopening fixtures stay, now redundant (FEATURE 6).
7. `make mutants` runs under a temporary root of its own (the human's change 1, in place). The rejected options are `retention_policy=none`, `--basetemp`, a sweep and `PYTEST_DEBUG_TEMPROOT` (FEATURE 7).
8. `pyproject.toml`'s `tmp_path_retention_policy = "failed"` stays (FEATURE 8).
9. The 58 leftover folders were to wait for pytest's three-day lock or the human's OK. At 12:03 UTC today, `/tmp/pytest-of-factory` in this container was empty, so the question looks settled. Please confirm nothing is left on the machine you care about (FEATURE 9).
10. One story, all of it the tester's. The coder had nothing to build (FEATURE 10).

## 7 Slow checks

The project has no slow check beyond `make check` and `make mutants`: no image scan, no SBOM. `make documents` printed `documents ok` in the documenter's run. As the one check that bears on this feature's Goal, I ran `make mutants FEATURE=F0014` for its effect on `/tmp` (see 2). It left nothing behind. The run's results stay in the git-ignored `mutants/`, where a later run goes on from them.

## 8 Cost

6 runs, 4.5 min, $1.55 for the one story (37 turns, 170k tokens in, 17k out). Nothing stands out. That is cheap even for a single story, because the coder had nothing to build and every other stage confirmed it in one pass with no rework round.

## Proposed stories

- `drafts/F0017-S0002-make-mutants-temporary-root-documented.md`: the project guide's *Mutation testing* section and the decision log describe the human's change 1, `make mutants` under a temporary root of its own, and why. It is the one part of the feature no story documented (finding 5).

## Log (append only)

1. acceptor: accepted with drafts; 1 draft proposed; make mutants 0/0 (F0017 changed no module under src/factory)
   1. Scope: none. S0001 delivers all three scope items as its Interface states, with nothing under `src/` or the earlier tests touched. The human's change 1 (the `mutants:` recipe's `mktemp -d`, `EXIT` trap and `TMPDIR`) is on `main`. `make check` is green on this branch (99.47 %).
   2. Feature demo: green. I ran five failing sessions whose test leaves `.git` at `0o020`. With `-p conftest` they leave no `garbage-*` folder, and a plain `rm -rf` removes the root. Without it, 2 `garbage-*` folders build up and `rm -rf` fails. A real `make mutants FEATURE=F0014 MUTANTS_SECONDS=480` run (4 timeouts, stopped at 480 s) left `/tmp/pytest-of-factory` empty and no `/tmp/tmp.*` behind.
   3. Mutation score: 0/0, because the feature changed only `tests/` and `docs/`. The F0014 run's `_close` survivors (`mutmut_5`, `mutmut_10`) are F0014's, so no draft.
   4. Noticed: the reviewer saw that `reopen`'s branches for a root that is a symbolic link and for a root that is a file have no test. They are low weight and get no draft. Nothing else was left open.
   5. Docs: the human's change 1 is documented only in the `Makefile`'s comment. Neither the project guide's *Mutation testing* section nor the decision log explains the temporary root, decision 7 or the ways it rejected. The reopen entry names only the `garbage-*` cause. This is draft F0017-S0002.
   6. Decisions: FEATURE decisions 1–10 are gathered in the report. Decision 6 (the leave for `tests/conftest.py`) is marked to confirm. Decision 9 (the 58 leftover folders) looks settled, because `/tmp/pytest-of-factory` was empty at 12:03 UTC.
   7. Slow checks: the project has none beyond `make check` and `make mutants`. I ran `make mutants FEATURE=F0014` to check `/tmp` before and after.
   8. Cost: 6 runs, 4.5 min, $1.55. Nothing stands out: there was no rework round, and the coder had nothing to build.
