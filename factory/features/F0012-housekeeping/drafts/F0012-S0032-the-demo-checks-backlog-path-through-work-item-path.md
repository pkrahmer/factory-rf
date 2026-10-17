# The demo check's backlog path through work_item_path

<!-- proposed by feature acceptance of 2026-10-17; refine before promoting -->

## Assignment (as of log entry 1)

F0012-S0023's reviewer found, in round 3, that `src/factory/entry/check_demos.py` `_story_findings` builds a backlog story's repository path by hand: `f"{FEATURES_DIRECTORY}/{feature}/{_BACKLOG}/{story}"` at line 70. The domain already has `factory.domain.paths.work_item_path(feature, "backlog", story)` for this. The session let the story go forward and deferred the fix (FEATURE decision 55). This story makes that one call. Behaviour does not change: a demo story is still checked at the path it will have in the project, and every finding line is unchanged. If `_BACKLOG` has no other use left in the module, it goes too.

## Interface

No new or changed public names. In `src/factory/entry/check_demos.py`, `_story_findings` computes `path` as `work_item_path(feature, "backlog", story)`, imported from `factory.domain.paths`. `"backlog"` is a `LifecycleFolder`. The module's other uses of `_BACKLOG` (`_is_backlog_story`) keep a constant, unless the coder makes it read the same name the path uses.

## Acceptance criteria

1. A demo story with a valid form is still found clean by `python -m factory.entry.check_demos`, which prints `demos ok` for this repository.
2. A demo story whose form fails still yields its finding at `<demo>/features/<feature>/<story>`, and the finding names the problem as before. The existing tests of `tests/entry/test_check_demos.py` pass unchanged.
3. `src/factory/entry/check_demos.py` no longer composes the path `FEATURES_DIRECTORY/<feature>/backlog/<story>` itself. The reviewer checks this in the diff; no structural test is written for it.
4. `make check` stays green.
5. docs: none. Nothing a reader sees changes, and the project guide's section on the demo check names no private helper.

## Demo

```bash
uv run python -m factory.entry.check_demos
```
Expect: `demos ok`.

```bash
grep -n 'work_item_path' src/factory/entry/check_demos.py
```
Expect: an import line and one call in `_story_findings`.

## Log (append only)

1. 2026-10-17 feature acceptance of F0012: proposed.
