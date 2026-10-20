---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 364
comments_read: [6301083856]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-20T20:46:30.195974Z'
  lease_duration: 60
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
14. `make check` stays green.
15. docs: `docs/project-guide/agents.md`, a new section *The fresh home* after *The shared launch module*: the program, its arguments and exit statuses, the rule of `fate` and `removed_when_empty` (the user's own entries go, other users' stay, kept paths and what lies beneath them stay), that it never follows a link and has no default home, and that S0004 starts it. `docs/project-guide/README.md`: the index names the new modules under the agents domain. `docs/decisions.md`: none in this story; S0004 writes the entry.

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
