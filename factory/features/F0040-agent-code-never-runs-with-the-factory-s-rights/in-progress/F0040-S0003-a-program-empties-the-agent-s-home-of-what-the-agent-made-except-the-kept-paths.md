---
stage: tests
blocked: question
round: 1
attempts: 0
crashes: 0
pull_request: 364
comments_read: [6301083856]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T20:43:50.813233Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T20:43:50.818872Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-20T20:44:13.374019Z'
  stage: intake
  run: aededd05a142486587cf5c03dd8750ed
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-20T20:45:31.730167Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-20T20:45:49.765270Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-20T20:46:09.647182Z'
  stage: intake
  run: c88ed764cf694fb3b4e077be7113d898
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T20:46:30.195974Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-20T20:50:13.512303Z'
  stage: tests
  run: b24f1ab9600447d4a037680e3a509a92
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-20T20:50:34.610462Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-20T20:54:18.147666Z'
  stage: doing
  run: fc4d4f4e52e9432ea7c9cb897a1483cc
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-20T20:54:39.935250Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-20T20:56:42.409778Z'
  stage: review
  run: 397d4de8577644b09d9c00b3aed5e4d5
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-20T20:57:04.021829Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-20T20:58:51.415749Z'
  stage: doing
  run: 6052f4273cd84c22a46788b372d28106
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-20T20:59:12.502290Z'
  stage: tests
- number: 16
  speaker: tester
  kind: question
  at: '2026-10-20T21:00:58.495903Z'
  stage: tests
  run: 1784501eddbd4da9a61630a40e0a0b8b
  blocked: question
---

# A program empties the agent's home of what the agent made, except the kept paths

## Description

The agent's home (`/home/agent`, its `.claude` a volume per instance) keeps everything every agent run left there: the full transcripts of all earlier runs in `~/.claude/projects/`, opencode's sessions in `~/.local/share/opencode/opencode.db`, the tools' caches, and any file a run wrote in `~/.claude` that Claude Code reads on every later run, such as a user `CLAUDE.md` or a `rules/` folder (seen on 2026-10-20 under `factory-confine` with a stage's rules, see `feature.md`). This story builds the program that clears it, `python -I -m factory.entry.fresh_home --home <folder> [--keep <path>]...`, which S0004 runs as the agent's user before every run and every project command. It runs as the user whose files it removes, so it decides by ownership: it removes every file, link and other entry of its own user in the home, and every folder of its own that is empty once its contents are gone, and it leaves every entry of another user (the factory's agents, `settings.json`, `skills/`, `commands/`, `.config/opencode`, and the mounted login files) as it is. It also keeps the kept paths and everything beneath them: the logins the factory hands over and the folders an operator names and uv's package cache, which the human chose to keep (the feature's decision 9; S0004 lists them). The rule is pure and lies in the domain; the walk lies in an adapter; the command line in the entry. The program has no default home, so no call can clear a home it was not named. Starting it, and when, are S0004's.

## Interface

`factory.domain.agent_home` (`domain`, new):

```python
FRESH_HOME_PREFIX = "factory-fresh-home:"
HomeFate = Literal["keep", "descend", "remove"]


def inside_home(relative: str) -> bool:
    """Whether `relative` names a path inside a home: not empty, not absolute, no `.` or `..`."""


def kept_paths(
    home: Path,
    *,
    login_files: Sequence[Path | None],
    state_files: Sequence[str],
    folders: Sequence[str],
) -> list[str]:
    """The paths, relative to `home`, that a fresh home keeps, in order and without repeats."""


def fate(relative: str, *, owned: bool, folder: bool, kept: Sequence[str]) -> HomeFate:
    """What the program does with the entry `relative` of the home."""


def removed_when_empty(relative: str, *, owned: bool, kept: Sequence[str]) -> bool:
    """Whether a folder the walk descended into is removed once it is empty."""
```

- `inside_home` is false for `""`, for a path that starts with `/`, and for one with an empty, `.` or `..` segment (`a//b`, `./a`, `a/..`); true otherwise. `factory.domain.settings` uses it for `FACTORY_OPENCODE_FOLDERS` in place of its own check, with the same refusal text as today.
- `kept_paths`: first each of `login_files` that is not `None` and lies inside `home` (`Path.is_relative_to`), as its path relative to `home` in `/` form; a file outside `home` is left out. Then `state_files`, then `folders`, as given. A repeat is dropped, the first kept. An entry of `state_files` or `folders` that is not `inside_home` raises `ValueError` naming it.
- `fate`: `keep` when `relative` is a kept path or lies beneath one (`relative` starts with `<kept>/`). Otherwise `descend` when `folder` is true (a real folder; a link is never one), whether or not a kept path lies beneath it. Otherwise `remove` when `owned`, and `keep` when not: an entry that is not a real folder is never walked, also when a kept path would lie beneath its name.
- `removed_when_empty`: true when `owned` and no kept path lies beneath `relative`; false otherwise.

`factory.adapters.home_files` (`adapters`, new):

```python
def own_entry(path: Path) -> bool:
    """Whether the entry at `path`, not followed if it is a link, belongs to this process's user."""


def clear_home(home: Path, kept: Sequence[str], *, owned: Callable[[Path], bool] = own_entry) -> list[str]:
    """Remove what `fate` gives `remove` and the folders left empty; the faults, `<relative>: <reason>`."""
```

- The walk lists each folder's entries in name order and asks `fate` for each, with `folder` true only for a real folder (a link to a folder is not one) and `owned` from `owned(path)`. `remove` unlinks the entry. `descend` walks into the folder; before that, a folder that is `owned` gets the owner's read, write and search bits added, so a folder an agent closed to itself is still walked. After its walk a folder for which `removed_when_empty` is true and which is empty is removed.
- No link is followed. The mode of an entry that is not `owned` is never changed. `home` itself is never removed.
- An `OSError` at an entry is recorded as `<relative>: <strerror>` and the walk goes on with the next entry; the list holds the faults in the order met, `[]` when there are none.

`factory.entry.fresh_home` (`entry`, new):

```python
def main(
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    owned: Callable[[Path], bool] | None = None,
) -> int:
    """Clear the home named by `--home` of this user's entries but the kept paths; 0 when done."""
```

- The arguments are exactly `--home <folder>` followed by any number of `--keep <path>`. Any other shape writes `factory-fresh-home: usage: fresh_home --home <folder> [--keep <path>]...` and returns 2. A `--home` that is not absolute, is `/`, or is not an existing folder writes `factory-fresh-home: --home <folder> is not an absolute folder other than /` and returns 2. A `--keep` that is not `inside_home` writes `factory-fresh-home: --keep <path> is not a path inside the home` and returns 2. In each of these cases nothing is removed.
- Otherwise it calls `clear_home(home, kept, owned=owned or own_entry)`, writes one line `factory-fresh-home: <fault>` per fault and returns 1 when there is one, 0 when there is none. It writes nothing on success.
- `python -m factory.entry.fresh_home` runs `main()` and exits with its status. No console script is added (`pyproject.toml` stays as it is).

Tests (the tester writes them): `tests/domain/test_agent_home.py`, `tests/adapters/test_home_files.py`, `tests/entry/test_fresh_home.py`. Every home is a folder under `tmp_path`; a test that needs an entry of another user passes `owned` that answers false for the paths it names, since the tests cannot `chown`. No test runs the program on a real home (the human's change 1). `tests/domain/test_settings*.py` stays unchanged and green. Under the leave of the feature's decision 14, `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` expects `{"factory.entry.wiring", "factory.entry.confine", "factory.entry.leftovers", "factory.entry.fresh_home"}`: the program runs as the agent's user and imports its adapter directly, as `factory.entry.confine` and `factory.entry.leftovers` do. Nothing else in that test changes.

## Acceptance criteria

1. `inside_home` (rows of one parametrized test): `.config/sso` and `a` are true; `""`, `/a`, `a//b`, `./a`, `a/.`, `a/..` and `..` are false.
2. `FACTORY_OPENCODE_FOLDERS=.config/sso,a/../b` is refused by `read_settings` with `SettingsInvalid` naming `FACTORY_OPENCODE_FOLDERS` and `holds a/../b, which is not a folder inside the agent's home`, as today, and `.config/sso` alone gives `[".config/sso"]`.
3. `kept_paths(Path("/home/agent"), login_files=[Path("/home/agent/.claude-token"), None, Path("/run/key")], state_files=[".claude/.credentials.json"], folders=[".config/sso", ".claude-token"])` gives `[".claude-token", ".claude/.credentials.json", ".config/sso"]`. A `folders` entry `/abs` raises `ValueError` whose message holds `/abs` (rows of one parametrized test with the valid case). So does a `state_files` entry `../x`, which raises `ValueError` whose message holds `../x`.
4. `fate` (rows of one parametrized test, `kept` `[".claude-token", ".config/sso"]`): `.claude-token` not owned and not a folder is `keep`; `.config/sso` owned folder is `keep`; `.config/sso/login` owned file is `keep`; `.config` owned folder is `descend`; `.claude` not owned folder is `descend`; `.claude/projects` owned folder is `descend`; `.claude/CLAUDE.md` owned file is `remove`; `.claude/settings.json` not owned file is `keep`; `.config-old` owned file is `remove` (a name that only begins like a kept path); `.config` owned and not a folder (a link or a file) is `remove`, and not owned and not a folder is `keep`, although `.config/sso` lies beneath its name.
5. `removed_when_empty` (rows of one parametrized test, same `kept`): `.cache` owned is true; `.config` owned is false (a kept path lies beneath it); `.claude` not owned is false.
6. `clear_home` on a home in `tmp_path` holding `.claude/agents/a.md`, `.claude/settings.json`, `.claude/CLAUDE.md`, `.claude/rules/x.md`, `.claude/projects/p/t.jsonl`, `.claude/.credentials.json`, `.config/opencode/`, `.config/sso/login`, `.cache/uv/f`, `.profile` and `.claude-token`, with `kept` `[".claude-token", ".claude/.credentials.json", ".config/sso"]` and `owned` false for `.claude`, `.claude/agents`, `.claude/agents/a.md`, `.claude/settings.json` and `.config/opencode`: afterwards the home holds exactly `.claude`, `.claude/agents`, `.claude/agents/a.md`, `.claude/settings.json`, `.claude/.credentials.json`, `.config`, `.config/opencode`, `.config/sso`, `.config/sso/login` and `.claude-token`, and the faults are `[]`.
7. A folder the agent closed: an owned `.claude/projects` with mode `0o000` holding a file is removed whole, and `clear_home` gives `[]`.
8. Links (rows of one parametrized test): an owned link `.claude/link` to a folder outside the home is removed, and the folder it pointed to and its file stay; a link to a kept path is removed and the kept path stays; with `kept` `[".config/sso"]`, an owned link `.config` to a folder outside the home that holds `sso/login` and `work.py` is removed, and that folder and both its files stay.
9. A fault: with an `owned` that raises `PermissionError(13, "Permission denied")` for `.cache/a` and answers true otherwise (the tests cannot make an unremovable entry without root), `clear_home` gives `[".cache/a: Permission denied"]`, the walk goes on, and `.cache/b` beside it is removed.
10. `main` (rows of one parametrized test, `stderr` a `StringIO`): `["--home", <home>]` over a home holding only owned files returns 0, writes nothing, and leaves the home empty. `["--home", <home>, "--keep", "a"]` keeps `a`. `[]` and `["--keep", "a"]` return 2 with the usage line. `["--home", "relative"]`, `["--home", "/"]` and `["--home", <missing folder>]` return 2 with `factory-fresh-home: --home <folder> is not an absolute folder other than /`. `["--home", <home>, "--keep", "../x"]` returns 2 with `factory-fresh-home: --keep ../x is not a path inside the home`. In each row that returns 2, the home's files are all still there.
11. `main` with the `owned` of criterion 9 returns 1 and writes `factory-fresh-home: .cache/a: Permission denied`.
12. Modes of entries that are not `owned`: a not-owned folder `.claude/agents` at mode `0o500` and a not-owned file `.claude/settings.json` at mode `0o444` keep their modes after `clear_home`.
13. An owned folder that holds an entry that is not `owned`: an owned `.cache/x/` holding a not-owned file `.cache/x/f`, beside a kept path outside it, stays with its file after `clear_home`, and an owned empty folder `.cache/y` is gone.
14. The home itself stays: `clear_home` on a home in `tmp_path` that holds only owned files and folders, with `kept` `[]`, gives `[]` and leaves the home an existing, empty folder.
15. `main` refuses the other shapes of arguments too (rows of the parametrized test of criterion 10): `["--home"]`, `["--home", <home>, "--keep"]` and `["--home", <home>, "--kept", "a"]` return 2 with the usage line, and the home's files are all still there.
16. `make check` stays green.
17. docs: `docs/project-guide/agents.md`, a new section *The fresh home* after *The shared launch module*: the program, its arguments and exit statuses, the rule of `fate` and `removed_when_empty` (the user's own entries go, other users' stay, kept paths and what lies beneath them stay), that it never follows a link and has no default home, and that S0004 starts it. `docs/project-guide/README.md`: the index names the new modules under the agents domain. `docs/decisions.md`: none in this story; S0004 writes the entry.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir -p "$d/h/.claude/projects/p" "$d/h/.config/sso" "$d/h/.cache/uv"
touch "$d/h/.claude/CLAUDE.md" "$d/h/.claude/projects/p/t.jsonl" "$d/h/.claude/.credentials.json" "$d/h/.config/sso/login" "$d/h/.cache/uv/f" "$d/h/.claude-token"
uv run python -I -m factory.entry.fresh_home --home "$d/h" --keep .claude-token --keep .claude/.credentials.json --keep .config/sso; echo "status $?"
(cd "$d/h" && find . -mindepth 1 | LC_ALL=C sort)
uv run python -I -m factory.entry.fresh_home --home / ; echo "status $?"
```
Expect: `status 0`, then the lines `./.claude`, `./.claude-token`, `./.claude/.credentials.json`, `./.config`, `./.config/sso`, `./.config/sso/login`, then `factory-fresh-home: --home / is not an absolute folder other than /` and `status 2`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: Format check passed. The story is not buildable yet. Three Interface rules have no criterion, and a coder and a tester could read each one two ways:

   1. `kept_paths` raises `ValueError` for an entry of `state_files` or `folders` that is not `inside_home`. Criterion 3 tests only a `folders` entry (`/abs`). The `state_files` side has no test. Proposed: extend criterion 3 with a row `state_files=["../x"]` that raises `ValueError` naming `../x`.

   2. `clear_home` states "The mode of an entry that is not `owned` is never changed", but no criterion tests it. Criterion 6 checks only which entries remain. Proposed: a new criterion with a not-owned folder, for example `.claude/agents`, at mode `0o500`, and a not-owned file at mode `0o444`. After `clear_home`, both modes are unchanged. Or say that criterion 6 covers it by asserting those modes.

   3. Two `clear_home` rules are untested: "folders left empty are removed" and "an owned folder holding an entry that is not `owned` stays". The second is decision 13's case, a factory-owned `.config/opencode` inside the agent's `.config`. In criterion 6, `.config` stays only because `.config/sso` is kept, so it never tests the not-owned reason. Proposed: a criterion with an owned `.cache/x/` holding a not-owned file `.cache/x/f` and a kept path outside it. Afterwards `.cache/x` and its file stay, and an owned empty folder `.cache/y` is gone.

   Everything else is fine:
   - **Interface:** the modules and signatures are concrete. Each fate rule from `fate` and `removed_when_empty` has a criterion row.
   - **Criteria:** each is testable by one function, except the gaps above.
   - **Smoke test:** the commands are runnable. The `Expect:` list matches `LC_ALL=C` sort order, where `-` sorts before `/`.
   - **Architecture:** the pure rule is in the domain, the walk in an adapter, and the command line in the entry. The `test_wiring` leave is covered by decision 14.
   - **Scope:** inside the feature and not in its Out of scope.

   My recommendation is to take all three proposals.
4. 2026-10-20 human: Answers (2026-10-20): take all three proposals.
   1. Criterion 3 gains the row `state_files=["../x"]`, which raises `ValueError` naming `../x`.
   2. A new criterion: a not-owned folder (for example `.claude/agents`, mode `0o500`) and a not-owned file (mode `0o444`) keep their modes after `clear_home`.
   3. A new criterion: an owned `.cache/x/` holding a not-owned file `.cache/x/f`, beside a kept path outside it; afterwards `.cache/x` and its file stay, and an owned empty folder `.cache/y` is gone.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete modules and signatures (`factory.domain.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`); every rule of `inside_home`, `kept_paths`, `fate`, `removed_when_empty`, `clear_home` and `main` is stated precisely.
   - Criteria: each is testable by one test function. Every rule has its failing side: `inside_home` false rows, `kept_paths` ValueError for `folders` and `state_files`, `fate` remove/keep/descend rows, `main` usage, home and keep refusals with the home untouched, and the fault path. Interface rules that had no criterion now have one. I carried in the human's answer (journal entry 4, "take all three proposals") and wrote only that into the story: (1) criterion 3 gains the `state_files=["../x"]` row; (2) new criterion 12 on the unchanged modes of not-owned entries; (3) new criterion 13 on an owned folder holding a not-owned file, and the removal of an owned empty folder. The two closing criteria are now 14 (`make check`) and 15 (`docs:`). The Description needed no rewrite.
   - Smoke test: the commands are runnable and use no pytest. The `Expect:` list matches the `LC_ALL=C` sort order and the two statuses (0 and 2) can be checked.
   - Architecture: the pure rule is in the domain, the walk in an adapter, and the command line in the entry. The `test_wiring` leave is granted by the feature's decision 14. `settings` reuses `inside_home` downward, which the layers allow.
   - Scope: within F0040's Scope (S0003 lines) and not in its Out of scope. No `pyproject.toml`, dependency or `factory/` change.
7. factory: started tests as self.
8. tester: Wrote the tests for every acceptance criterion. They fail for the right reasons: the three new test modules cannot import their modules, and the wiring test fails on its assertion because `factory.entry.fresh_home` does not exist yet. `make lint` is green. I skipped the type check, as the stage says.

   Criterion → test:
   - criterion 1: tests/domain/test_agent_home.py::test_a_path_is_inside_a_home_only_when_relative_without_empty_dot_or_parent_segments
   - criterion 2: tests/domain/test_agent_home.py::test_the_opencode_folders_setting_refuses_a_path_outside_the_home. It goes here because `tests/domain/test_settings*.py` must stay unchanged.
   - criterion 3: tests/domain/test_agent_home.py::test_kept_paths_are_the_logins_inside_the_home_then_state_files_then_folders (rows: valid, `/abs` in `folders`, `../x` in `state_files`)
   - criterion 4: tests/domain/test_agent_home.py::test_the_fate_of_an_entry_follows_kept_paths_folders_and_ownership
   - criterion 5: tests/domain/test_agent_home.py::test_an_empty_folder_is_removed_only_when_owned_and_above_no_kept_path
   - criterion 6: tests/adapters/test_home_files.py::test_clear_home_keeps_kept_paths_and_foreign_entries_and_removes_the_rest
   - criterion 7: tests/adapters/test_home_files.py::test_an_own_folder_closed_to_its_owner_is_removed_whole. It uses the default `owned`, since the test user owns its files.
   - criterion 8: tests/adapters/test_home_files.py::test_an_own_link_is_removed_and_never_followed (three rows, `kept` `[".config/sso"]`)
   - criterion 9: tests/adapters/test_home_files.py::test_a_fault_at_an_entry_is_recorded_and_the_walk_goes_on
   - criterion 10: tests/entry/test_fresh_home.py::test_main_clears_the_named_home_or_refuses_its_arguments_untouched. It compares stderr by `splitlines()`, so it does not decide whether there is a trailing newline.
   - criterion 11: tests/entry/test_fresh_home.py::test_main_writes_each_fault_and_returns_one
   - criterion 12: tests/adapters/test_home_files.py::test_the_modes_of_foreign_entries_stay_as_they_are
   - criterion 13: tests/adapters/test_home_files.py::test_an_own_folder_holding_a_foreign_entry_stays_and_an_own_empty_one_goes
   - criteria 14 and 15: not test criteria.

   Files created:
   - tests/domain/test_agent_home.py
   - tests/adapters/test_home_files.py
   - tests/entry/test_fresh_home.py
   - tests/home_files_support.py: shared helpers `build_home`, `listing`, `owned_but` and `refusing`, which the adapter and entry tests both use.

   Earlier test file changed: tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer now also expects `factory.entry.fresh_home` in the set. The story's Interface names this change under the feature's decision 14. Nothing else in that test changed.

   Modules the test run could not import: `factory.domain.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/entry/test_fresh_home.py - ImportError while importing test module '/work/checkout/tests/entry/test_fresh_home.py'.
9. factory: started doing as self.
10. coder: Implemented the fresh home in three layers. `make check` is green (`check: green`, coverage 99.12 %).

    Built:
    - `src/factory/domain/agent_home.py` (new):
      - `FRESH_HOME_PREFIX` and `HomeFate`.
      - `inside_home` and `kept_paths`. `kept_paths` keeps the logins inside the home, then the state files, then the folders, drops repeats with `dict.fromkeys`, and raises `ValueError` naming a path outside the home.
      - `fate` and `removed_when_empty`, which share one private `_beneath_or_at` test (equal, or starts with `<above>/`).
    - `src/factory/domain/settings.py`: `_opencode_folder` now calls `inside_home` instead of its own segment check. The refusal text is unchanged.
    - `src/factory/adapters/home_files.py` (new):
      - `own_entry` compares `lstat().st_uid` with `os.geteuid()`.
      - `clear_home` runs a private `_Walk`. It lists each folder in name order and decides "real folder" with `stat.S_ISDIR(lstat())`, so it never follows a link. On `remove` it unlinks the entry. On `descend` it first adds `S_IRWXU` to an owned folder and never changes the mode of a foreign one. After the walk it removes the folder when `removed_when_empty` holds and the folder is empty.
      - An `OSError` at an entry, or when listing a folder, is recorded as `<relative>: <strerror>` and the walk goes on.
    - `src/factory/entry/fresh_home.py` (new): `main` parses exactly `--home <folder>` followed by pairs of `--keep <path>`. It refuses before removing anything, with exit 2 and the three lines the Interface gives. Otherwise it writes one line per fault and returns 1, or returns 0 and writes nothing. `python -m factory.entry.fresh_home` exits with the status of `main()`. It imports its adapter directly, as `confine` and `leftovers` do, which the updated wiring test expects.

    Main choice: the walk is a small private class that holds `home`, `kept`, `owned` and the fault list. I rejected a recursive free function that passes all four down on every call: the class keeps each method short and has one place to record faults. In the entry I parse the arguments by hand (fixed positions, then pairs) as `factory.entry.leftovers` does. I rejected argparse because its own usage and error output would not match the exact lines the Interface demands.

    Refactor pass: two over-long docstring lines were shortened for lint. Nothing else needed changing.

    Noticed but not touched:
    - I did not run the story's smoke test. The tool permission layer refused the command, probably because it includes `--home /` (the program refuses that call, but CLAUDE.md is strict about running `fresh_home` by hand). The smoke-test stage will run it.
    - If listing the home itself fails, the fault is recorded under the relative name `.`. No criterion covers that case.
    - The journal changed nothing in the Description beyond the criteria the intake already wrote in.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 33 known, 3 gone
11. factory: started review as self.
12. reviewer: Review, round 0. Group 1 (acceptance criteria) fails, so I stopped there. I read the diff against the Interface and the criteria. Criteria 1 to 13 each have a test that checks what the criterion says, and the coder's `make check` was green (entry 10). `make duplicates` reports one new finding from this story: `kept_paths` is unused. That is expected, because the Interface defines it for S0004.

    1. criterion 14 added: it needs its test. The Interface's rule "`home` itself is never removed" (`clear_home`) had no criterion. The "clears" row of criterion 10 also passes if the home is gone, because `listing` uses `rglob`, which returns nothing for a missing folder. Fix: a test where a home holding only owned files and folders, with `kept` `[]`, ends as an existing, empty folder.
    2. criterion 15 added: it needs its test. `src/factory/entry/fresh_home.py` `_parse` has two refusals that no test reaches: the odd-length shape (`--keep` with no path) and an option after `--home` that is not `--keep`. The second matters: a misspelled `--kept a` must refuse rather than clear the home without keeping `a`. Fix: add rows `["--home"]`, `["--home", <home>, "--keep"]` and `["--home", <home>, "--kept", "a"]` to the parametrized test of criterion 10. Each returns 2 with the usage line and leaves the home's files in place.
    3. `src/factory/entry/fresh_home.py` `_home`: the refusal of `/` compares `Path(folder) == Path("/")`. `--home //` gets past it, because pathlib keeps a leading `//` as its own root. So does `--home /home/..`, because pathlib does not collapse `..`. Both name the root, are absolute and are existing folders, so the program would walk all of `/`. Criterion 10 tests only the spelling `/`. Fix: refuse a home whose resolved path is `/` (`home.resolve() == Path("/")`) and give criterion 10 rows `//` and `/home/..` that expect the `--home ... is not an absolute folder other than /` line. This needs a code change, so I left it as a finding rather than adding a criterion. If the coder reads the Interface's "is `/`" as only the literal spelling, it is a question for the human.

    The renumbered closing criteria are now 16 (`make check`) and 17 (`docs:`).

    Earlier tests:
    - `tests/entry/test_wiring.py`: changed under the human's leave in the feature's decision 14, which the story's Interface repeats. Only the expected set gains `factory.entry.fresh_home`; nothing else in the test changed.
13. factory: started doing as self.
14. coder: Round 1. I fixed the one finding that needed code. The other two findings need only tests, so this goes to the tester. `make check` is green (`check: green`, coverage 99.12 %).

    What I built:
    - `src/factory/entry/fresh_home.py` `_home` (finding 3): the program now refuses a home whose resolved path is `/`. It used to compare the spelling with `Path("/")`. `--home //`, `--home /home/..` and a link to `/` now get the line `--home <folder> is not an absolute folder other than /` and status 2. Before this change they passed the check and the program walked the whole root. A one-line comment says why the path is resolved.
    - Main choice: the program resolves the path only to check it, and still walks the `home` as given. I rejected walking the resolved path. It would change which names faults are reported under, and nothing asked for that.

    For the tester:
    1. Criterion 14 (finding 1): `clear_home` on a home in `tmp_path` that holds only owned files and folders, with `kept` `[]`, gives `[]`. Afterwards the home is an existing, empty folder.
    2. Criterion 15 (finding 2): new rows in the parametrized test of criterion 10 (`tests/entry/test_fresh_home.py::test_main_clears_the_named_home_or_refuses_its_arguments_untouched`). The rows are `["--home"]`, `["--home", <home>, "--keep"]` and `["--home", <home>, "--kept", "a"]`. Each returns 2 with the usage line and leaves the home's files in place. These rows also cover `fresh_home.py` line 50, which coverage reports as missed.
    3. Finding 3: the reviewer asked for criterion 10 rows `["--home", "//"]` and `["--home", "/home/.."]`, each returning 2 with `factory-fresh-home: --home <spelling> is not an absolute folder other than /`. I could not write them into the Description myself: the work item is not in my write paths (`Permission denied`). Please add them to the same parametrized test. The Interface's "is `/`" should then read "resolves to `/`".

    What the journal changed:
    - The reviewer's entry 12 added criteria 14 and 15. The Description already holds them.
    - The Description does not hold finding 3's rows or the new wording "resolves to `/`" in the Interface. Someone with write access to the work item needs to make that change.

    Refactor pass: nothing needed changing.

    Noticed but not touched:
    - The `/home/..` row relies on `/home` existing on the test machine. If that is a concern, the tester could use a link in `tmp_path` that points to `/`, which the code now refuses too.
15. factory: started tests as self.
16. tester: Tests for criteria 14 and 15 are written. I stopped before adding the rows for finding 3, because no criterion names them yet.

    Question: should criterion 10 get the rows `["--home", "//"]` and `["--home", "/home/.."]`? Each would return 2 with `factory-fresh-home: --home <spelling> is not an absolute folder other than /` and leave the home's files in place. In the Interface, "is `/`" would then read "resolves to `/`".
    - (a) Yes. You, or the reviewer, add those rows to criterion 10 and change the Interface wording. I write them as rows of `test_main_clears_the_named_home_or_refuses_its_arguments_untouched`. I would use a link in `tmp_path` pointing to `/` instead of `/home/..` only if you name it, since that is a different case. **This is the option I would choose.** The coder already refuses these spellings (entry 14). Without a criterion, nothing pins that refusal, and a program that walks all of `/` is the case that matters most.
    - (b) No. "Is `/`" means only the literal spelling, criterion 10 stays as it is, and the coder's check that resolves the path stays untested.
    I cannot do (a) without a criterion. It is a case the criteria leave open, and the work item's Description is not mine to change.

    What I did:
    - criterion 14: tests/adapters/test_home_files.py::test_the_home_itself_stays_once_emptied (new). A home holding only owned files and folders, `kept` `[]`, gives `[]`, and the home is left as an existing, empty folder. It uses the default `own_entry`, as the test of criterion 7 does.
    - criterion 15: tests/entry/test_fresh_home.py::test_main_clears_the_named_home_or_refuses_its_arguments_untouched gets three new rows: `home-without-folder` (`["--home"]`), `keep-without-path` (`["--home", <home>, "--keep"]`) and `unknown-option` (`["--home", <home>, "--kept", "a"]`). Each expects 2, the usage line, and the home's files still there.

    Files created: none. I changed only test files this story wrote: tests/adapters/test_home_files.py and tests/entry/test_fresh_home.py.

    Modules the test run could not import: none. The code exists, so the new tests passed at once instead of failing first. `make test`: test: green (64.1 s). `make lint`: lint: green.
