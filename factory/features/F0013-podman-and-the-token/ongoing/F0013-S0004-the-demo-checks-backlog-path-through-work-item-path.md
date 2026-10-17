# The demo check's backlog path through work_item_path

## Assignment (as of log entry 1)

F0012-S0023's reviewer found, in round 3, that `src/factory/entry/check_demos.py` `_story_findings` builds a backlog story's repository path by hand: `f"{FEATURES_DIRECTORY}/{feature}/{_BACKLOG}/{story}"` at line 70. The domain already has `factory.domain.paths.work_item_path(feature, "backlog", story)` for this. The session let the story go forward and deferred the fix (F0012 decision 55). This story makes that one call. Behaviour does not change: a demo story is still checked at the path it will have in the project, and every finding line is unchanged. It is F0012's proposed draft S0032, taken in as F0013's fourth story (FEATURE decision 2).

## Interface

No new or changed public names. In `src/factory/entry/check_demos.py`:

- `_BACKLOG` is typed `LifecycleFolder` (imported from `factory.domain.paths`): `_BACKLOG: LifecycleFolder = "backlog"`;
- `_story_findings` computes `path` as `work_item_path(feature, _BACKLOG, story)`, `work_item_path` imported from `factory.domain.paths`; its comment on the path stays;
- `_is_backlog_story` keeps comparing with `_BACKLOG`, so the folder's name is spelled once in the module;
- `FEATURES_DIRECTORY` leaves the import from `factory.domain.paths`, which the module no longer uses.

Nothing else in the module changes. Tests: none new and none changed; the existing tests of `tests/test_demos.py` and `tests/entry/test_check_demos.py` pin the behaviour, so no leave is needed (FEATURE decision 12).

## Acceptance criteria

1. A demo story with a valid form is still found clean: `python -m factory.entry.check_demos` prints `demos ok` for this repository (the existing test of `tests/test_demos.py` passes unchanged).
2. A demo story whose form fails still yields its finding at `<demo>/features/<feature>/backlog/<story>`, and the finding names the problem as before: the existing tests of `tests/entry/test_check_demos.py` pass unchanged.
3. `src/factory/entry/check_demos.py` no longer composes the path `FEATURES_DIRECTORY/<feature>/backlog/<story>` itself, and the string literal `"backlog"` appears in it once, in `_BACKLOG`. The reviewer checks this in the diff; no structural test is written for it.
4. `make check` stays green.
5. docs: none. Nothing a reader sees changes, and the project guide's section on the demo check names no private helper.

## Demo

```bash
uv run python -m factory.entry.check_demos
```
Expect: `demos ok`.

```bash
grep -n 'work_item_path\|"backlog"' src/factory/entry/check_demos.py
```
Expect: three lines: `work_item_path,` in the import from `factory.domain.paths`, `_BACKLOG: LifecycleFolder = "backlog"`, and the call `work_item_path(feature, _BACKLOG, story)` in `_story_findings`.

## Log (append only)

1. 2026-10-17 human: created from F0012's proposed draft S0032 (feature acceptance of 2026-10-17).
