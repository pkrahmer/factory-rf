# The demo's story texts after the shakedown (finding 4), the human's change to `demo/`

The shakedown of 2026-10-18 raised six questions in four of the todo demo's stories (night log, 08:16, 08:33, 08:36, 08:48, and the result section's item 4). Each was a side of a rule that the story's Interface states and no criterion pins; the human's answers are decisions 12 to 17 of the run's `factory/features/F0001-todo-service/feature.md` on `pkrahmer/factory-demo-todo`. Below, for every story under `demo/todo-service/features/`, the exact criterion text to add or change so that both sides of every such rule have a criterion, then the decisions to add to each `feature.md`, then the lines for the demo project's `CLAUDE.md` that match F0016-S0001. The two closing criteria (`make check`, docs) stay last in every story; the numbers below are after the change. After the change, `make test` in factory-rf must stay green (`tests/test_demos.py` runs the demo check over the shipped demo).

Not added, because they are no untested side of a stated rule but later work: the run's decision 14 (the committed OpenAPI schema shows FastAPI's default 422 body, not `{"detail": "<string>"}`) and decision 17 (the SQLite engines `from_path` creates are never disposed). Both wait as the acceptance's proposed stories F0001-S0005 and F0001-S0006 in the live demo's backlog; folding them into S0003 and S0004 is the human's product choice.

## F0001-todo-service

### F0001-S0001 Domain model and in-memory repository

Why: the "no inheritance" rule holds for every repository, and S0004 had to ask for leave to turn this criterion into one test with a row per class (the run's decision 16, 08:36).

- Interface, the `Tests:` paragraph: the sentence "A later repository, also one that keeps a file under `tmp_path`, joins the suite by adding its factory to that list, with no other change to the file." becomes:

  > A later repository, also one that keeps a file under `tmp_path`, joins the suite by adding its factory to that list and its class to a second module-level list, of repository classes, with no other change to the file.

- Criterion 22 becomes:

  > 22. No repository class inherits the protocol: `InMemoryTodoRepository` is not a subclass of `TodoRepository`, as a row of one parametrized test in `tests/repository/test_contract.py` over the module-level list of repository classes (here one class); and the contract suite's `repository` fixture is annotated as returning `TodoRepository`, so `make check` (mypy) proves each repository satisfies the protocol.

### F0001-S0002 Service layer with filtering

Why: the Interface says `list(done=None)` means no filter; criterion 4 tests `list()` only, and criterion 5 the two other values. The same kind of gap as the `null` rows.

- Criterion 5 becomes:

  > 5. The done filter, as rows of one parametrized test over two completed and two open todos created alternately: `list(done=True)` returns only the completed todos, `list(done=False)` only the open ones, and `list(done=None)` all four, each in creation order.

### F0001-S0003 HTTP API

Why: the intake question of 08:16 (the run's decision 12): the Interface rejects a `PATCH` that sets neither field "(both absent or `null`)", but criterion 12 had rows only for `{}` and `{"title": null}`. And the Interface's "`PATCH` applies `title` first (rename), then `done`" had a criterion for an invalid title only, none for two valid fields.

- Interface, after "A `TodoUpdate` that sets neither field (both absent or `null`) is rejected with 422.", add: "A field sent as `null` counts as not set."
- Criterion 12 becomes:

  > 12. `PATCH /todos/{id}` with `{}`, `{"title": null}`, `{"done": null}` and `{"title": null, "done": null}` (four rows of one parametrized test) returns 422 and a body whose only key is `detail`, a string; a `GET` of the todo afterwards shows it as before.

- A new criterion 14, after criterion 13 (the old 14 to 24 become 15 to 25, and criterion 20, the old 19, still names "the bodies of criteria 2, 4, 7, 9 and 16"):

  > 14. `PATCH /todos/{id}` with `{"title": " New title ", "done": true}` on an open todo returns 200 and the todo titled `New title` and completed, with the same id and `created_at`; a `GET` afterwards shows both changes.

- Interface, the `Tests:` paragraph: "`tests/api/test_openapi.py` (criteria 20 and 21); `tests/api/test_imports.py` (criterion 22, ...)" becomes "(criteria 21 and 22)" and "(criterion 23, naming only the forbidden import)".

### F0001-S0004 SQLite repository and persistence switch

Why: the three intake questions of 08:33 and the review question of 08:36 (the run's decisions 15 and 16): the storage format the Interface states was never read back, `from_path(path: str | Path)` had no row for `str`, "`app.api.main` stays the only `app.api` module that imports `app.repository`" had no criterion of its own, and no test held "no inheritance" for `SqliteTodoRepository`.

- Interface, the `Tests:` paragraph: "the tester adds one factory to the list of repository factories in `tests/repository/test_contract.py` (F0001-S0001), which returns `SqliteTodoRepository.from_path(tmp_path / "todo.db")` for the `tmp_path` the fixture passes it, so the whole contract suite runs against both repositories; nothing else in that file changes." becomes:

  > the tester adds one factory to the list of repository factories in `tests/repository/test_contract.py` (F0001-S0001), which returns `SqliteTodoRepository.from_path(tmp_path / "todo.db")` for the `tmp_path` the fixture passes it, so the whole contract suite runs against both repositories, and adds `SqliteTodoRepository` to that file's list of repository classes, so its no-inheritance test has a row for it; nothing else in that file changes.

- Four new criteria after criterion 9, so that `make check` becomes 14 and docs 15:

  > 10. `SqliteTodoRepository` is not a subclass of `TodoRepository`: its row of the no-inheritance test in `tests/repository/test_contract.py`, beside the row of `InMemoryTodoRepository`.
  >
  > 11. The stored format: a row of `todos` read back with a Core `select` has `id == str(todo.id)` (hyphenated), `created_at` the ISO 8601 text of the UTC time with the offset `+00:00`, also for a todo created with another offset, and `done` a `bool`, `True` for a completed todo and `False` for an open one (rows of one parametrized test).
  >
  > 12. `from_path(path)` and `from_path(str(path))` each open the same file and see the todos written through the other, as rows of one parametrized test.
  >
  > 13. `app.api.main` is still the only `app.api` module that imports `app.repository`, now that it imports `app.repository.sqlite` too: F0001-S0003's import test in `tests/api/test_imports.py` still passes.

## F0002-operations

### F0002-S0001 Health endpoint

Why: the Interface says `app = build_app(os.environ)` and that `build_app` passes the chosen repository's storage kind; nothing checked that `build_app` hands the service the repository it chose (F0002's acceptance: `create_app(None, ...)` and `create_app(TodoService(None), ...)` survived, its proposed story F0002-S0004).

- A new criterion 5, after criterion 4 (the old 5 to 8 become 6 to 9):

  > 5. `build_app` hands the todo routes the repository the environment chose, as rows of one parametrized test: a todo `POST`ed through `build_app({"TODO_DB": p})` (`p` under `tmp_path`) is listed by `GET /todos` of a second `build_app({"TODO_DB": p})`; a todo `POST`ed through `build_app({})` is listed by the same app and not by a second `build_app({})`.

### F0002-S0002 Version command

Why: the Interface states `if __name__ == "__main__": sys.exit(main())`; every test called `main` in-process, so the guard was the one line coverage missed and its deletion went unnoticed (F0002's acceptance, its proposed story F0002-S0005).

- Interface, the `Tests:` line becomes: "Tests: `tests/test_main.py` (the module is outside the layers), calling `main` with `capsys`, and running the module as a child process with the interpreter that runs the tests."
- A new criterion 5, after criterion 4 (the old 5 and 6 become 6 and 7):

  > 5. Run as a module, as rows of one parametrized test: `subprocess.run([sys.executable, "-m", "app", "--version"], capture_output=True, text=True, check=False)` exits 0 with stdout `app <version>` and a newline and an empty stderr; without an argument it exits 2 with an empty stdout and stderr `usage: python -m app --version` and a newline.

### F0002-S0003 Todo statistics

Why: the Interface says "`stats` counts over the repository's list in one pass"; no criterion holds it.

- Interface, the `Tests:` line becomes: "Tests: `tests/service/test_stats.py` (with a repository that counts its calls, a fake of `TodoRepository` in that module around `InMemoryTodoRepository`) and `tests/api/test_stats.py`."
- A new criterion 5, after criterion 4 (the old 5 to 9 become 6 to 10):

  > 5. `stats()` reads the repository once: with a repository that counts its calls, one `stats()` call makes exactly one `list_all` call and no other call.

## F0003-search

### F0003-S0001 Title search

Why: the Interface says `None` means no title filter, and criterion 3 has rows only for empty and blank texts; and the length limit is on the text as sent (the schema's `max_length`), before the service strips it, which F0003's acceptance found unpinned (its proposed story F0003-S0002). The criterion below pins the Interface as written; counting the stripped text instead would be a change of the Interface and the human's product choice.

- Criterion 3 becomes:

  > 3. `list(search=None)`, `list(search="")` and `list(search="   ")` return the same todos as `list()`: three rows of one parametrized test.

- Criterion 8 becomes:

  > 8. The length limit on both sides, counted on the text as sent, as rows of one parametrized test: `GET /todos?search=<200 characters>` returns 200 and `[]` on the data of criterion 1; `GET /todos?search=<201 characters>` returns 422 and a body whose only key is `detail`, a string starting with `query.search: `; and `GET /todos?search=<197 spaces>milk` (201 characters as sent, 4 after stripping) also returns 422 with such a body.

## Decisions to add to the features' `feature.md`

### `demo/todo-service/features/F0001-todo-service/feature.md`, after decision 11

> 12. In a `PATCH` body a field sent as `null` counts as not set: `{}`, `{"title": null}`, `{"done": null}` and `{"title": null, "done": null}` are each a 422. A body with both fields valid applies both, the title first. (S0003, story text; the shakedown's intake question on demo #4, 2026-10-18)
>
> 13. Test helpers, constants and fixtures that more than one test module needs live once, in a module at the `tests/` root or in `tests/conftest.py`; the standing leave in `CLAUDE.md` lets the tester move one there and change the earlier tests that held it, keeping what each checks. (`CLAUDE.md`; the shakedown's decision 13, the human's answer on demo #4)
>
> 14. The SQLite table `todos` stores `id` as the UUID's hyphenated text, `created_at` as ISO 8601 text in UTC (offset `+00:00`) and `done` as a boolean; a test reads a row back with a Core `select` to hold it. (S0004, story text; the shakedown's decision 15)
>
> 15. No repository inherits the `TodoRepository` protocol; one parametrized test in `tests/repository/test_contract.py` holds it, a row for each repository class, and a later repository adds its row there. (S0001 and S0004, story text; the shakedown's decision 16)
>
> 16. `SqliteTodoRepository.from_path` takes a `str` or a `Path`, both tested. (S0004, story text; the shakedown's intake question on demo #5)
>
> 17. `list(done=None)` is no filter, as `list()` is. (S0002, story text)

### `demo/todo-service/features/F0002-operations/feature.md`, after decision 6

> 7. `build_app` is tested with todos, not only through `/health`: the repository it chooses is the one the todo routes use. (S0001, story text; F0002's acceptance at the shakedown, 2026-10-18)
>
> 8. `python -m app` is tested as a child process with the interpreter that runs the tests; it is a short command, not a server, so it fits the rule that tests start no server. (S0002, story text; F0002's acceptance at the shakedown)
>
> 9. `stats` reads the repository once, with one `list_all`. (S0003, story text)

### `demo/todo-service/features/F0003-search/feature.md`, after decision 2

> 3. The search limit of 200 characters counts the text as sent, before stripping, as the schema's `max_length` does; a padded search of more than 200 characters is a 422 even if its stripped text is shorter. (S0001, story text; F0003's acceptance at the shakedown, 2026-10-18)
>
> 4. `search=None` means no title filter, like an empty or blank text. (S0001, story text)

## `demo/todo-service/project/CLAUDE.md`, matching F0016-S0001

1. In `## Tests`, a new last bullet after the one that starts `- A test that waits for a time limit`, one line in the file (the template's text, with the demo's shared modules as examples):

   ```
   - The standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier test module still holds as a copy of a shared one, may be moved to one shared place under `tests/` (a module at its root such as `tests/fakes.py`, or `tests/conftest.py` for a fixture), and the earlier tests that held it changed to use it from there, without asking, as long as every earlier test keeps its name and checks the same thing. The tester makes the move, never the coder, and its entry names each earlier test file it changed. Any other change to a test another story wrote still needs the human's leave.
   ```

2. In `## Not without asking (end the stage with `question`)`, the first bullet

   ```
   - New dependency, new top-level package, change to `factory/`, change to a test you did not write, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
   ```

   becomes

   ```
   - New dependency, new top-level package, change to `factory/`, change to a test you did not write beyond the standing leave under *Tests*, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
   ```

   and its second bullet

   ```
   - A story that changes a test another story wrote names that test in its Interface; that is the human's leave, and the tester makes the change, never the coder.
   ```

   becomes

   ```
   - A story that changes a test another story wrote beyond the standing leave names that test in its Interface; that is the human's leave, and the tester makes the change, never the coder.
   ```

The live demo repository (`pkrahmer/factory-demo-todo`) is a separate copy; these lines reach it only when the human copies the demo source there again.
