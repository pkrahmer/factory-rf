# Pre-check of the demo fixes for F0016 (finding 4), round 1

Checked: `planning/overnight/demo-fixes-F0016.md`, the human's change to `demo/`, against the shipped demo under `demo/todo-service/`, against the demo as the shakedown left it built (the clone at the session's `scratchpad/demo-todo`, read only), and against `tests/test_demos.py` with `factory.entry.check_demos`, which reads the shipped demo's stories.

## How the facts were checked

- **The shipped texts.** Every story the fixes touch (`F0001-S0001` to `S0004`, `F0002-S0001` to `S0003`, `F0003-S0001`), the three `feature.md` files (their decisions: 11, 6 and 2 today), and `demo/todo-service/project/CLAUDE.md`, `pyproject.toml` and `security/semgrep/python.yml`.
- **The built demo.**
  - Source: `src/app/api/main.py` (`build_repository`, `build_app`), `src/app/api/schemas.py` (`TodoUpdate`), `src/app/api/routes.py` (`PATCH`, `search`), `src/app/repository/sqlite.py`, `src/app/service/todo_service.py` (`stats`) and `src/app/__main__.py`.
  - Tests: `tests/repository/test_contract.py`, `tests/repository/test_sqlite.py`, `tests/api/test_imports.py`, `tests/api/test_todos.py`, `tests/test_main.py` and `tests/fakes.py`.
- **The check.**
  - `tests/test_demos.py` calls `check_demos` over the shipped demo. For each backlog story it runs the story form check: sections, a code block and `Expect:` per smoke test, criteria numbered without a gap, `make check` second to last, `docs:` last. No test reads `project/CLAUDE.md` or a `feature.md` beyond its existence.
  - Run today from a temporary folder: `demos ok`.
- The F0016 side: S0001's bullet compared word for word with the demo's. It differs only by "such as `tests/fakes.py`", as intended.

## Each change against the built code

- **F0001-S0001.**
  - The Interface sentence to replace is there verbatim.
  - The built test holds the no-inheritance rule as `TodoRepository not in repository_class.__mro__`, with the classes as inline `pytest.param`s. A module-level list, as the new criterion 22 asks, is the same test with its rows named once.
  - `TodoRepository` is a plain `Protocol` (not `runtime_checkable`), so `issubclass` raises `TypeError` against it. "Is not a subclass" can only be tested through `__mro__`, which the shakedown's tester found by itself. A parenthesis saves the next one the detour (D5, optional).
- **F0001-S0002.** The new criterion 5 adds the `done=None` row. `TodoService.list(done=None)` is the default, and the built service treats it as no filter.
- **F0001-S0003.**
  - The four `PATCH` rows of the new criterion 12 are the built test's rows (`[{}, {"title": None}, {"done": None}, {"title": None, "done": None}]`). `TodoUpdate`'s validator refuses both `None`.
  - The new criterion 14 holds on the built route: title first, then `done`.
  - Renumbering: old 14 to 24 become 15 to 25.
    - The old criterion 19 names the bodies of "2, 4, 7, 9 and 15". Its 15 (unknown id, 404) becomes 16, so the new 20 must *change* to "2, 4, 7, 9 and 16". The fix's "still names" reads as if nothing changed (D4).
    - The Tests paragraph's 20 and 21 become 21 and 22, and its 22 becomes 23, as the fix says.
- **F0001-S0004.**
  - The new criteria 10 to 13 hold on the built code:
    - 10: `__mro__`, as above.
    - 11: the built test reads a row through `Table(..., autoload_with=engine)` and a Core `select`, and gets `row.id == str(todo.id)`, a `str` `created_at` ending in `+00:00` and equal to the todo's time under `fromisoformat`, and `row.done is True`.
    - 12: rows `path-then-str` and `str-then-path`.
    - 13: `test_only_the_composition_root_imports_the_repository` counts `app.repository.*` too.
  - Criterion 11's "the ISO 8601 text of the UTC time" has two readings. The built repository writes `isoformat(timespec="microseconds")` (`2026-10-04T12:00:00.000000+00:00`) so that text order is time order. A tester who reads the phrase as `== todo.created_at.isoformat()` writes a test that the shakedown's code fails. The criterion should say what the built test checks (D2).
  - **Missing:** the Interface's Tests paragraph keeps "nothing else in that file changes". With the standing leave in the demo's `CLAUDE.md`, S0004's reviewer will again find S0001's `T0` and `_todo` copies in `test_contract.py`, as at 08:48 (round 3, a question). The tester may move them under the leave, but this sentence forbids exactly that. That is the contradiction the human had to override at 08:48 (D1).
  - Numbering: 10 to 13 new, then `make check` is 14 and `docs:` 15, so the form check stays green.
- **F0002-S0001.**
  - The new criterion 5 holds on the built `build_app`: `InMemoryTodoRepository()` per call without `TODO_DB`, `SqliteTodoRepository.from_path` with it. It kills the two survivors F0002's acceptance found (`create_app(None, ...)`, `TodoService(None)`).
  - Old 5 to 8 become 6 to 9. No criterion of the story names another by number.
- **F0002-S0002.** The built `__main__` prints `usage: python -m app --version` to stderr and returns 2 without arguments, and prints `app <version>` with `--version`.
  - The child-process test is allowed. The demo's ruff ignores `S603` and `S607` under `tests/**`, bandit scans `src/app` only, and semgrep refuses only `shell=True`.
  - The test does not make coverage count the guard line: pytest-cov 7 does not follow a child process by itself. It does make the guard's deletion fail a test, which is the point of the "Why".
  - Old 5 and 6 become 6 and 7.
- **F0002-S0003.** The built `stats` makes one `list_all` call. A counting fake in `tests/service/test_stats.py` fits the demo's rule "fake the repository through its protocol". Old 5 to 9 become 6 to 10. The old 5's "the data of criterion 2" keeps its number.
- **F0003-S0001.**
  - The new criterion 3 adds `None`.
  - The new criterion 8's padded row (197 spaces and `milk`, 201 characters as sent) is a 422 on the built route, since `Query(max_length=200)` counts before the service strips.
  - Both criteria are replaced in place, with no renumbering.
- **The decisions.** The `feature.md` numbers continue the existing ones (F0001 after 11, F0002 after 6, F0003 after 2). Each matches its story change. F0001's 13 matches the standing leave.
- **`project/CLAUDE.md`.**
  - Its last `## Tests` bullet starts with `- A test that waits for a time limit`, and the two *Not without asking* bullets are there verbatim, so the three changes apply as written.
  - The demo's own rule "Before writing a helper, search `src/app` and `tests/` for one ..." stays, and with the leave it no longer forces a question.

## Needed before which story, and in which order

- **None of F0016's stories needs them.** No story reads `demo/`, and `demo/*` is in no stage's write path. Apply them as your own commit in factory-rf, any time after S0001's text is final (now, with no edit to it from its pre-check), so that the demo's bullet stays S0001's word for word. `make test` stays green when the renumbering is exact: `tests/test_demos.py` checks the form only. Run `uv run python -m factory.entry.check_demos` once after the edit.
- **The live demo** (`pkrahmer/factory-demo-todo`) should get the new `CLAUDE.md` lines only with an image that holds S0001 and S0002. This is FEATURE's own reason for your change 2: without S0002's reviewer item, the leave would reach the tester with nothing that watches it. Copy the demo source there again only after F0016 is merged and the image is rebuilt.

## Points for the human, with the recommended answers

- **H1. D1, the missing change.** Recommended: **apply it.** Without it, the next demo run's F0001-S0004 asks the same question as at 08:48, despite the standing leave.
- **H2. D2, the stored time's exact text.** Recommended: **apply it**, stating what the built test checks, instead of choosing a format. A fixed format such as `isoformat(timespec="microseconds")` in the Interface would be a product decision. Take it only if you want the text itself pinned.
- **H3. D4 and D5.** Wording only. Recommended: apply both.
- **H4. Decisions 14 and 17 of the run** (OpenAPI 422 body, engine disposal) stay out, as the file says. Recommended: **agree.** They are new behaviour, not untested sides.

## Verdict

`demo fixes: pass with edits (D1 needed, D2 recommended, D3 optional, D4 and D5 wording)`

## Replacement texts

### D1 (needed): F0001-S0004 keeps the standing leave open

In the F0001-S0004 section, replace the quoted new Tests paragraph with

> the tester adds one factory to the list of repository factories in `tests/repository/test_contract.py` (F0001-S0001), which returns `SqliteTodoRepository.from_path(tmp_path / "todo.db")` for the `tmp_path` the fixture passes it, so the whole contract suite runs against both repositories, and adds `SqliteTodoRepository` to that file's list of repository classes, so its no-inheritance test has a row for it; nothing else in that file changes, except a move of a shared test helper under the standing leave of `CLAUDE.md`.

### D2 (recommended): F0001-S0004 criterion 11 says what is checked

Replace the quoted criterion 11 with

> 11. The stored format: a row of `todos` read back with a Core `select` has `id == str(todo.id)` (hyphenated); `created_at` a `str` that ends with `+00:00` and that `datetime.fromisoformat` reads back equal to the todo's `created_at`, also for a todo created with another offset; and `done` a `bool`, `True` for a completed todo and `False` for an open one (rows of one parametrized test).

### D3 (optional): F0001-S0001's Interface names the leave too

In the F0001-S0001 section, replace the quoted new sentence with

> A later repository, also one that keeps a file under `tmp_path`, joins the suite by adding its factory to that list and its class to a second module-level list, of repository classes, with no other change to the file but a move of a shared test helper under the standing leave of `CLAUDE.md`.

### D4 (wording): F0001-S0003's renumbering

In the F0001-S0003 section, replace

```text
(the old 14 to 24 become 15 to 25, and criterion 20, the old 19, still names "the bodies of criteria 2, 4, 7, 9 and 16")
```

with

```text
(the old 14 to 24 become 15 to 25, and criterion 20, the old 19, then names "the bodies of criteria 2, 4, 7, 9 and 16" in place of "... and 15", since the old 15 is now 16)
```

### D5 (wording): how "not a subclass" is tested

In the F0001-S0001 section's new criterion 22, after "`InMemoryTodoRepository` is not a subclass of `TodoRepository`", add

> (`TodoRepository` is not in its `__mro__`; `issubclass` refuses a protocol that is not `runtime_checkable`)
