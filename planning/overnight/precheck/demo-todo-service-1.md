# Pre-check: the todo demo draft against v1.1's own pipeline (1)

Brief: `planning/overnight/briefs/precheck-demo-todo-service.md`. Draft: `planning/overnight/demo/` (written from `planning/overnight/briefs/draft-demo-todo-service.md`). Read on 2026-10-17: the draft whole, `NOTES.md` first; v1.1's `template/factory/pipeline.yml`, `template/CLAUDE.md`, `claude/agents/*.md`, `claude/settings.json`; `src/factory/` (pipeline definition and its rules, story form and place checks, `check_story`, the make adapter and its target-time parser, write paths and the guard, the preflight probe on `main`, the opening of a pull request, `GitCli.checkout`, the claude runtime's arguments); F0012's `FEATURE.md` (H6, decisions 31, 49 to 52) and the drafts S0023, S0028, S0029, S0030 (S0011 to S0016 and S0024 checked for effects on the demo: none beyond the target-time lines, which the demo prints); v1's `demo/` and run 4 in `docs/reference/16-evidence/README.md`.

No git command was run, and no file but this one was written. Every run used a copy in `mktemp -d` with `trap 'rm -rf "$d"' EXIT`, `TMPDIR` inside it, and for `factory-rf`'s code `UV_PROJECT_ENVIRONMENT` inside it and `PYTHONDONTWRITEBYTECODE=1`, so neither `factory-rf/.venv` nor `__pycache__` was created.

## What ran, with the last lines

| Command (on a copy) | Last lines |
|---|---|
| `uv lock --check --offline` in `project/` | `Resolved 111 packages in 0.76ms`, status 0: `uv.lock` matches `pyproject.toml` |
| `uv sync --frozen -q`, then `make check -o secrets` | `lint: green (0.1 s)`, `types: green (0.6 s)`, `Contracts: 1 kept, 0 broken.`, `layers: green (0.3 s)`, `sast: green (2.9 s)`, `licenses: green (0.3 s)`, `no tests ran in 2.79s`, `test: green (3.7 s)`, `check: green`, status 0 (coverage warns `No data was collected` once per worker) |
| `detect-secrets-hook --baseline .secrets.baseline` over every file of the copy but `uv.lock` and the baseline (what `make secrets` does without git) | no output, status 0 |
| `make duplicates` | `duplicates: 0 similar code, 0 dead code, in .reports/`, status 0 |
| `make mutants` (no `FEATURE`, no repository) | `mutants: set FEATURE, as in make mutants FEATURE=F0001`, status 2 |
| `make openapi` on the empty project | `ModuleNotFoundError: No module named 'app.api'`, status 2 (expected: the target serves F0001-S0003 on) |
| `RuamelPipelineDefinitionReader().parse(project/factory/pipeline.yml)` | loads; stages `intake, tests, doing, review, docs, smoke-test, acceptance, approval, done`; first `intake`; commands `check, duplicates, lint, test`; coder `['src/*', 'docs/openapi.json']`, `time_limit` 40, `lease_duration` 60 |
| today's `factory.entry.check_story.main` over the eight stories at `factory/features/<feature>/backlog/<story>.md`, with `factory/story-form.md` | eight lines `<path>: ok`, status 0 |
| S0023's `check_demos`, emulated clause by clause (below) over `demo/README.md` + `demo/todo-service/{README.md,project,features}` | `demos ok` |
| `factory-rf`'s own `detect-secrets-hook` (its baseline) over every file the demo adds to `demo/` | no output, status 0: committing `demo/` keeps `factory-rf`'s `make secrets` green (the demo's `uv.lock` hashes raise nothing) |
| `factory-rf`'s `ruff check` and `ruff format --check` from a root holding `demo/` | `All checks passed!`, format status 0 |
| Probe: a contract fixture `def repository(request: pytest.FixtureRequest) -> TodoRepository: return request.param()` under the demo's `mypy` | `error: Returning Any from function declared to return "TodoRepository"  [no-any-return]`; with `factory: Callable[[], TodoRepository] = request.param; return factory()`: `Success`, `1 passed`, `test: green` |
| Probe: `bandit -q -r $(SOURCE)` without `-c pyproject.toml` and without `[tool.bandit]` | `sast: green (4.7 s)` |

Not run: `make secrets` and `make mutants` with a repository (both call git); the smoke tests (no code exists). `make mutants`' feature lookup was checked by reading it against S0030 and the code (below).

## The pipeline, the targets and the write paths

- **Budgets and the lease.** Every role keeps the defaults (`time_limit` 40, `lease_duration` 60). Minutes at each stage: tests 40 + `lint` 5 + `test` 10 = 55; doing 40 + `check` 10 + `duplicates` 5 = 55; docs 40 + 10 = 50; intake, review, smoke-test, acceptance 40. All within 60; the reader's lease rule passes. Per-run budgets are the shipped agents' (intake 1, tester 2, coder 4, reviewer 3, documenter 1.5, smoke tester 2, acceptance reviewer 8 USD); run 4's clean stages cost 0.09 to 0.28 USD, so none of the eight stories comes near.
- **Targets the pipeline calls.** `check`, `lint`, `test`, `duplicates` exist. `MakeProjectCommands` judges by exit status, keeps the last line that is not `make:`, and parses `<target>: green (<s> s)`; every target in `check` prints it, `check` ends `check: green`, and `duplicates` ends with its count line (no green line, as in S0029; its record then has no target times). The preflight probe on `main` is `make lint` only, so the empty project's `make test` matters only to the human's setup step ("must end with `check: green`"), which the exit-5 rule makes green.
- **`make mutants` after S0030.** The commit that carries a story's source is `work item <id>: doing ends: review` (S0030); the README tells the session to merge with a merge commit, so these commits reach `origin/main` and `git log --grep='^(work item )?F0001-S[0-9]{4}([: ]|$)' -- 'src/app/*.py'` lists their modules (git's pathspec `*` crosses `/`, so `src/app/domain/model.py` is found). After a squash merge the subject is the pull request's title, `F0001-S0001: <title> (#n)` (`opening.py`: `f"{work_item}: {heading}"`), which the pattern also matches. The session's own `F0001-S0001: start` matches too but touches only `factory/`, which the pathspec drops. The acceptance runs on the named branch `work-item/F0001-A0001` (`GitCli.checkout` uses `git switch --force-create`, never a detached head), so `FEATURE` comes from the branch. Agents never commit (`claude/settings.json` denies `git commit`; R10), so no source lands under another subject. mutmut 3.8 reads `source_paths`, `pytest_add_cli_args_test_selection`, `pytest_add_cli_args` and `also_copy` (checked in its `configuration.py`); `also_copy = ["docs/"]` brings `docs/openapi.json` beside the mutated copy, and `tests/`, `pyproject.toml`, `uv.lock` are copied by default.
- **Write paths.** Every file a stage must write lies inside its write paths: intake, reviewer, smoke tester the work item; tester `tests/*` (also `tests/<layer>/__init__.py`, `tests/conftest.py`, and F0001-S0004's addition to `tests/repository/test_contract.py`); coder `src/*` and `docs/openapi.json` (`make openapi` writes through the shell, which the `Edit|Write` guard does not see, and the undo after the stage accepts it); documenter `README.md`, `docs/*` (`docs/project-guide.md`, `docs/api.md`, and `docs/project-guide/<domain>.md` if the documenter follows its split lesson: `fnmatch`'s `*` crosses `/`); acceptance reviewer the report and `factory/features/<feature>/backlog/*`. What the targets write (`.reports/`, `.coverage`, `.import_linter_cache/`, `mutants/`, `.venv/`) is ignored by `.gitignore`; `.licenses-requirements.txt` is removed by its recipe. The smoke tests write only under `mktemp -d`. No story needs `pyproject.toml`, `Makefile`, `uv.lock` or `CLAUDE.md` changed (all protected): the layers contract already names every layer, and every dependency is present.

## Per story: the predicted outcome by role

Shorthand: *pass* = the role ends forward without a question or a finding.

### F0001-S0001 Domain model and in-memory repository

- Intake: pass. Every Interface rule has a criterion with its failing side (blank, too long, naive time, unknown id, duplicate id).
- Tester: pass on `make lint`, with two traps the tests stage cannot see because it skips the type check: (1) criterion 22 fixes the fixture's return type `-> TodoRepository`, and `return request.param()` then fails `mypy --strict` (`no-any-return`, probed above); (2) the Tests line makes the factories zero-argument (`here only InMemoryTodoRepository`), which is what forces F0001-S0004 into a question (see there).
- Coder: pass if the tester assigned `request.param` to a typed variable; otherwise `make check` is red on a test, and the coder must end with `question` (R9): one round `doing → tests → doing` and a human answer. Required edit 2 removes the trap.
- Reviewer: likely pass. Risk: the Interface says the rules hold "however a todo is built (the constructor, `new`, `with_title`, ...)", criterion 4 names the three ways for the blank rule but criterion 5 (length) names none; a tester who tests length through `Todo.new` only leaves the constructor's and `with_title`'s refused side untested, which the reviewer's check 1 counts. Recommended edit A.
- Documenter: pass (`docs/project-guide.md` and the README pointer, both in `docs/*` and `README.md`).
- Smoke tester: pass. Block 1 prints `True 'Buy milk' 2026-10-04T12:00:00+00:00` then `False 'Write the next story' 2026-10-04T12:01:00+00:00` (`a` is older, the title stripped); block 2 the two `InvalidTitle - ...` lines.
- Verdict: first-pass likely once required edits 1 and 2 are made; without edit 2, a plausible doing → tests round.

### F0001-S0002 Service layer with filtering

- Intake: pass, with one weak spot: the Interface's default `clock: Clock = utc_now` has no criterion (criterion 14 tests `utc_now` alone, not that `TodoService(repository)` uses it). The intake's lesson counts "a default" as a behaviour that needs a criterion. Run 4 passed the same text clean, so the risk is low. Recommended edit B.
- Tester, coder, reviewer, documenter: pass. A test may import `InMemoryTodoRepository` (tests are outside the import-linter graph).
- Smoke tester: pass. Block 1 `['Buy milk']`, `['Write the next story']`, `Write story S0003 2026-10-04T12:00:00+00:00` (with the fixed clock both todos tie on `created_at`, but each filtered list holds one todo, so the random `uuid4` tie-break cannot change a line); block 2 `InvalidTitle`, `TodoNotFound`, `[]`.
- Verdict: first-pass.

### F0001-S0003 HTTP API

- Intake: pass, with one gap the v1.1 intake's lessons ("every clause ... the value for every kind") may ask about: the route table lists 422 for `PATCH` and `DELETE /todos/{todo_id}`, but only `GET /todos/not-a-uuid` has a criterion (9). Run 4's intake passed the same gap, but v1.1's intake carries the stricter lessons. Recommended edit C.
- Tester: pass. Criterion 20 fails at the tests stage, as it should (`docs/openapi.json` does not exist yet).
- Coder: pass. `CLAUDE.md` (*Docs*) tells it to run `make openapi`, and the file is in its write paths; error handlers, `Annotated[..., Depends(...)]` (no ruff `B008`), 204 with an empty body: all standard in FastAPI 0.141.
- Reviewer: pass. Criterion 19 repeats bodies that criteria 2, 4 and 15 already fix exactly. That is redundant, not a gap.
- Documenter: pass (`docs/api.md`, README).
- Smoke tester: pass. Five lines: compact JSON with `"title":"Buy milk"` and `"done":true`, `[]`, `{"detail":"title must not be blank"}`, `204`, `{"detail":"todo <id> not found"}`. `curl` is in the image (`image/Dockerfile`). The `trap` stops the server and removes the folder.
- Verdict: first-pass.

### F0001-S0004 SQLite repository and persistence switch

- Intake: pass (the test change is named and is "by the human's leave", as the intake's lesson asks).
- Tester: **question, as drafted.** The tester may add one factory to S0001's list and change nothing else in the file, and criterion 1 asks for `SqliteTodoRepository` "on a file under `tmp_path`". A zero-argument factory list, which S0001's Tests line suggests (`here only InMemoryTodoRepository`), gives the factory no `tmp_path`. The only ways around it break a rule: an in-memory SQLite (not a file), a file outside `tmp_path` (`CLAUDE.md`), or a change to the fixture (not allowed). Run 4's S0004 took one review rework; this is a likely cause. Required edit 1 makes S0001's factories take `tmp_path`.
- Coder: pass. `make sast`'s `project-no-sql-text` refuses `text()` and `exec_driver_sql`, so Core statements are the only way; criterion 9's empty current directory holds (coverage's data file is fixed at start, bytecode goes beside the source).
- Reviewer, documenter: pass.
- Smoke tester: pass. Three lines: the created todo, the same todo listed after the restart (`kill` of `uv run` stops uvicorn, as the drafter's step 8 showed; uvicorn sets `SO_REUSEADDR` for the same port), `database file exists`.
- Verdict: first-pass once required edit 1 is made; as drafted, a tests-stage question.

### F0002-S0001 Health endpoint

- Intake: pass. Run 4's intake question (an empty `TODO_DB`) is answered by criterion 3.
- Tester: pass. Criterion 6 maps to F0001-S0003's existing test, which passes at the tests stage and goes red only once the coder adds the route.
- Coder: pass (`make openapi` again).
- Reviewer, documenter: pass.
- Smoke tester: pass. `{'status': 'ok', 'version': '0.1.0', 'storage': 'memory'}`: field order is `HealthRead`'s, and the version comes from the editable install's metadata.
- Verdict: first-pass.

### F0002-S0002 Version command

- All roles pass. Coverage misses the `sys.exit(main())` line under `if __name__ == "__main__":`; the total stays far above 90 %. Under mutmut, criterion 4's deny list holds on the rewritten copy.
- Smoke tester: `app 0.1.0` / `exit 0`; the usage line (stderr, which the Bash tool shows) / `exit 2`.
- Verdict: first-pass.

### F0002-S0003 Todo statistics

- All roles pass. "counts over the repository's list in one pass" has no criterion, but it describes how the counts are computed, not what they are, and run 4 passed it clean.
- Smoke tester: `{'open': 2, 'done': 1, 'total': 3}`.
- Verdict: first-pass.

### F0003-S0001 Title search

- All roles pass. Both sides of the length limit are criterion 8. `Straße`/`STRASSE` holds under `casefold`.
- Smoke tester: `['Buy Milk', 'MILK run']`, `422 ['detail']`. Consecutive requests through `TestClient` take milliseconds, so `utc_now` cannot tie them.
- Verdict: first-pass.

### The three acceptances

- F0001-A0001, F0002-A0001, F0003-A0001: `make mutants` runs on the acceptance branch with `FEATURE` from the branch name, over the modules of the feature's `doing ends` commits. F0001's run is the longest (about ten modules, FastAPI tests) but should fit the acceptance reviewer's 40 minutes. The import tests are deny lists, so mutmut's own imports do not fail them, and `docs/openapi.json` is copied. The reviewer's JUnit lesson finds `.reports/junit.xml`. No write outside the report and `backlog/`.

## S0023's demo check, clause by clause

Over the tree as the session will commit it (`demo/README.md`, `demo/todo-service/{README.md,project/,features/}`; `NOTES.md` is staging only and would not be read either way, since it is neither under `features/` nor a demo folder):

| Clause | Result |
|---|---|
| `demo/` exists; `demo/README.md` present | no finding |
| every folder `demo/<name>/` (one: `todo-service`) | — |
| the index names `` `todo-service/` `` on a line | no finding: the table row starts `` | `todo-service/` | `` |
| `README.md`, `project/`, `features/` present | no finding |
| `project/factory/pipeline.yml` present and accepted by `RuamelPipelineDefinitionReader().parse` | no finding |
| `project/factory/story-form.md` present | no finding |
| every file under `features/` is `<feature>/feature.md` or `<feature>/backlog/<story>.md` | no finding (3 `feature.md`, 8 backlog stories, nothing else) |
| each story: `check_story_place("factory/features/<feature>/backlog/<story>.md", feature_file_exists=True)` | no finding (ids match their feature folders, names `F0000-S0000-slug.md`) |
| each story: `parse_specification` then `check_story_form(..., folder="backlog")` | no finding: title line, the five sections of the form, criteria numbered from 1, `make check` + `green` second-to-last, `docs:` last, an `Expect:` after each of the 13 smoke-test blocks, no front matter, no journal entry |

**Findings it would print: none** (`demos ok`, status 0). The demo also adds nothing that `factory-rf`'s own `make check` would flag (secrets, ruff, the four-document check, the repository-wide tests: all are scoped to `src/`, `tests/` or the four documents).

## The drafter's sixteen choices

1. Documents (`docs/project-guide.md`, `docs/api.md`, `docs/openapi.json`). **Agree.** It matches the template and the documenter's lessons.
2. The coder writes `docs/openapi.json`. **Agree.** It is the only way the coder's own `make check` can be green after a route change. The documenter's `docs/*` also covers the file, which does no harm.
3. `make duplicates` as a report of `doing` (55 of 60 minutes). **Agree.** It is what S0029's `CLAUDE.md` bullet tells a project to do.
4. No pip-audit. **Agree.** It needs the network; the template has no audit target.
5. Pinned versions (SQLAlchemy 2.1). **Agree.** `uv lock --check` is green, the licences pass, and the story says "SQLAlchemy Core" without a version.
6. `make test` accepts exit status 5. **Agree for the demo, and carry it back into S0029** (required edit 3). Without it, the template's `make check` is red on every empty project, and step 2 of the demo README's setup ("must end with `check: green`") would fail. Accepting 5 cannot hide a failure once one test exists.
7. The layers output unfiltered. **Agree.** The factory keeps only the tail and the last line, where the banner does not reach; a broken contract shows its detail.
8. Coverage leaves out `...` lines. **Agree.** It is harmless: a protocol method whose body is a docstring alone counts no statement anyway, and the rule only matters when the coder writes `...`.
9. The secrets baseline generated outside a repository. **Agree.** It holds no result, and both `make secrets` and `factory-rf`'s own scan pass with it.
10. Guidance paragraphs in the story form. **Agree.** `required_sections` reads only the `## ` headings, and the acceptance reviewer writes its proposals "following `factory/story-form.md` in full", so the guidance helps.
11. Structural tests as deny lists. **Agree.** It is better than S0029's "leave out the tests that read the source", because nobody has to know the test names in advance. One leftover: the demo `Makefile`'s header (line 10) still says mutmut's "runs leave out the tests that read the source", which contradicts `pyproject.toml`'s comment and `CLAUDE.md`. Recommended edit E.
12. No feature form. **Agree.** Nothing reads it and S0023 does not require it.
13. Criteria rewritten for first-pass building. **Agree.** But then cost and time cannot be compared one-to-one with run 4 (F0001-S0003 has three more criteria). The README says "the stories were the same, in v1's form"; edit D says what differs.
14. Smoke tests clean up after themselves. **Agree.** The `trap 'rm -rf "$d"'` string is the shipped agents' own lesson. `claude/settings.json` denies `Bash(rm -rf *)`, but the `rm` sits inside the quoted `trap` argument, not as a command of its own, so the rule should not match.
15. The baseline's measure: "time" read as start-to-archive. **Better answer: agent minutes, compared only for stories that were first-pass in run 4 too.** Start-to-archive holds the simulated human's waits (52 of F0001-S0001's 62 minutes) and v1's tick pause (three full two-minute pauses per story in run 4, since shortened in v1). Neither belongs to v1.1's pipeline. Run 4's F0001-S0001, F0001-S0004 and F0002-S0001 were not first-pass, so their numbers are no first-pass baseline. Recommended edit D. The human decides, since the plan's words are "cost and time".
16. The index row. **Agree.**

### Divergences from S0029's template `Makefile`

| Divergence | Where it goes |
|---|---|
| `test`: `\|\| [ $$? -eq 5 ]` and its two comment lines | carried back into S0029 (required edit 3); the demo keeps it |
| `sast`: `bandit -q -c pyproject.toml -r` (and `[tool.bandit] targets = ["src"]` in `pyproject.toml`) | fixed in the demo (recommended edit F): the table only repeats the target the command line already gives, and the template has neither; probed green without them |
| header line 4 and `.PHONY` name `openapi`; the `openapi` target | the project's own; stays in the demo only |
| header line 10 (mutmut's runs "leave out the tests that read the source") | the template's words, untrue for the demo: fixed in the demo (recommended edit E) |

## Points for the human, with recommended answers

1. **S0001's factories take `tmp_path`** (required edit 1). Recommended: yes. Without it, S0004's tester must ask or break a rule.
2. **The `request.param` trap in the demo's `CLAUDE.md`** (required edit 2). Recommended: yes. The tests stage skips `mypy`, so the coder is the first to meet it, and the coder cannot fix a test.
3. **Exit status 5 in S0029's template `make test`** (required edit 3, a change to an F0012 draft, which is the human's). Recommended: yes, before S0029 starts. Otherwise the demo and the template differ on purpose and the template's empty project is red.
4. **The baseline's "time"** (choice 15, edit D). Recommended: cost and agent minutes per story, for the five stories that were clean in run 4 (F0001-S0002, F0001-S0003, F0002-S0002, F0002-S0003, F0003-S0001), within 25 %. Start-to-archive is recorded with its conditions and not compared.
5. **Three criteria the stricter v1.1 intake may ask for** (edits A, B, C: the length rule through every constructor, the default clock, the 422 of a bad id on `PATCH` and `DELETE`). Recommended: take them. Each costs one test row, and an intake question costs a round and a human answer. They move the stories further from run 4's text (point 4 already handles the comparison).
6. **The two Makefile cleanups** (edits E, F). Recommended: take them; neither changes behaviour.
7. Choices 1 to 5, 7 to 14 and 16 as the drafter took them. Recommended: confirm.

## Verdict

Verdict: the demo passes S0023's check (`demos ok`), `make check` is green on the empty project, and the pipeline definition loads within the lease. Six stories are predicted first-pass as drafted. F0001-S0004 is predicted to stop with a tests-stage question, and F0001-S0001 carries a plausible `doing → tests` round. Three edits are required (1 and 2 for those two stories, 3 to settle the Makefile divergence in S0029), six are recommended (A to F).

## Required edits

### Edit 1: S0001's factories take `tmp_path`, and S0004 adds a file-backed one

File `planning/overnight/demo/todo-service/features/F0001-todo-service/backlog/F0001-S0001-domain-model-and-in-memory-repository.md`, line 113.

Old:

```text
Tests: `tests/domain/test_model.py`, `tests/domain/test_errors.py`, `tests/domain/test_imports.py`, and the repository behaviour as one contract suite in `tests/repository/test_contract.py`, run through a `repository` fixture that is parametrized over a module-level list of repository factories, here only `InMemoryTodoRepository`. A later repository joins the suite by adding itself to that list. Fixed ids are built with `UUID(int=n)`.
```

New:

```text
Tests: `tests/domain/test_model.py`, `tests/domain/test_errors.py`, `tests/domain/test_imports.py`, and the repository behaviour as one contract suite in `tests/repository/test_contract.py`, run through a `repository` fixture that is parametrized over a module-level list of repository factories, each a `Callable[[Path], TodoRepository]` that the fixture calls with the test's `tmp_path`; here the list holds one factory, which returns `InMemoryTodoRepository()`. A later repository, also one that keeps a file under `tmp_path`, joins the suite by adding its factory to that list, with no other change to the file. Fixed ids are built with `UUID(int=n)`.
```

File `planning/overnight/demo/todo-service/features/F0001-todo-service/backlog/F0001-S0004-sqlite-repository-and-persistence-switch.md`, line 32.

Old:

```text
Tests: by the human's leave, the tester adds `SqliteTodoRepository` on a file under `tmp_path` to the list of repository factories in `tests/repository/test_contract.py` (F0001-S0001), so the whole contract suite runs against both repositories; nothing else in that file changes. The other tests go into `tests/repository/test_sqlite.py` and `tests/api/test_main.py`.
```

New:

```text
Tests: by the human's leave, the tester adds one factory to the list of repository factories in `tests/repository/test_contract.py` (F0001-S0001), which returns `SqliteTodoRepository.from_path(tmp_path / "todo.db")` for the `tmp_path` the fixture passes it, so the whole contract suite runs against both repositories; nothing else in that file changes. The other tests go into `tests/repository/test_sqlite.py` and `tests/api/test_main.py`.
```

### Edit 2: the `request.param` trap in the demo's `CLAUDE.md`

File `planning/overnight/demo/todo-service/project/CLAUDE.md`, line 27.

Old:

```text
- Tests pass `mypy --strict` once the code exists: never use the value of a call to a function typed `-> None` (no `assert f() is None`); call it as a statement.
```

New:

```text
- Tests pass `mypy --strict` once the code exists: never use the value of a call to a function typed `-> None` (no `assert f() is None`); call it as a statement. A fixture's `request.param` is `Any`: assign it to a variable of its type before you return or call it (`factory: Callable[[Path], TodoRepository] = request.param`), since returning it from a fixture typed `-> TodoRepository` fails mypy's `no-any-return`, and the tests stage does not run the type check.
```

### Edit 3: exit status 5 in S0029's template `make test`

File `factory/features/F0012-housekeeping/drafts/F0012-S0029-a-makefile-in-the-template.md`, in the Interface's `make` block (recipe lines start with one tab).

Old:

```make
# Every core (pytest-xdist), short tracebacks, no banner; coverage as pyproject.toml sets it,
# with the lines that miss; the time of every test in the JUnit report .reports/junit.xml.
test:
	$(start)
	mkdir -p .reports
	uv run pytest -q --no-header --tb=short -p no:cacheprovider -n auto --dist load \
	  --junit-xml=.reports/junit.xml --cov --cov-report=term-missing:skip-covered
	$(green)
```

New:

```make
# Every core (pytest-xdist), short tracebacks, no banner; coverage as pyproject.toml sets it,
# with the lines that miss; the time of every test in the JUnit report .reports/junit.xml.
# Exit status 5 is pytest's "no tests collected": green for the empty project, impossible
# once the first test exists.
test:
	$(start)
	mkdir -p .reports
	uv run pytest -q --no-header --tb=short -p no:cacheprovider -n auto --dist load \
	  --junit-xml=.reports/junit.xml --cov --cov-report=term-missing:skip-covered || [ $$? -eq 5 ]
	$(green)
```

Same file, criterion 7.

Old:

```text
7. `make test` calls the stand-in once with arguments that start with `run pytest` and hold `-n auto` and `--junit-xml=.reports/junit.xml`, and leaves the folder `.reports` in the copy's folder.
```

New:

```text
7. `make test` calls the stand-in once with arguments that start with `run pytest` and hold `-n auto` and `--junit-xml=.reports/junit.xml`, and leaves the folder `.reports` in the copy's folder; with a stand-in that exits 5 (pytest's status when it collects no test, as on an empty project), it exits with status 0 and ends with a line matching `^test: green \(\d+\.\d s\)$`.
```

(Criterion 6's rows stay true: a stand-in that exits 1 still fails `[ 1 -eq 5 ]`, prints no `green`, and is called once.)

## Recommended edits

### Edit A: the length rule through every way of building a todo

File `.../F0001-todo-service/backlog/F0001-S0001-domain-model-and-in-memory-repository.md`, line 121.

Old:

```text
5. The length rule on both sides, as rows of one parametrized test: a title of 1 character and one of exactly 200 characters are accepted, also when surrounded by whitespace; a title of 201 characters after stripping raises `InvalidTitle` whose message is `title must be at most 200 characters`.
```

New:

```text
5. The length rule on both sides, as rows of one parametrized test, from `Todo(...)`, `Todo.new` and `with_title` alike: a title of 1 character and one of exactly 200 characters are accepted, also when surrounded by whitespace; a title of 201 characters after stripping raises `InvalidTitle` whose message is `title must be at most 200 characters`.
```

### Edit B: the default clock

File `.../F0001-todo-service/backlog/F0001-S0002-service-layer-with-filtering.md`, lines 225 to 227.

Old:

```text
14. `utc_now()` returns a timezone-aware datetime with a zero UTC offset, no more than a second away from `datetime.now(UTC)`.
15. `make check` stays green.
16. docs: `docs/project-guide.md` describes the service layer: what `TodoService` owns (the use cases, the clock, the done filter) and that it reaches storage only through the repository protocol.
```

New:

```text
14. `utc_now()` returns a timezone-aware datetime with a zero UTC offset, no more than a second away from `datetime.now(UTC)`.
15. A `TodoService` built without a clock stamps with `utc_now`: a todo created through `TodoService(repository)` has a timezone-aware `created_at` with a zero UTC offset, no more than a second away from `datetime.now(UTC)`.
16. `make check` stays green.
17. docs: `docs/project-guide.md` describes the service layer: what `TodoService` owns (the use cases, the clock, the done filter) and that it reaches storage only through the repository protocol.
```

### Edit C: the 422 of a malformed id on every route that takes one

File `.../F0001-todo-service/backlog/F0001-S0003-http-api.md`, line 90.

Old:

```text
9. `GET /todos/not-a-uuid` returns 422 and a body whose only key is `detail`, a string starting with `path.todo_id: `.
```

New:

```text
9. `GET`, `PATCH` (with `{"done": true}`) and `DELETE` of `/todos/not-a-uuid` each return 422 and a body whose only key is `detail`, a string starting with `path.todo_id: `: three rows of one parametrized test.
```

### Edit D: the baseline's measure

File `planning/overnight/demo/todo-service/README.md`, section *The shakedown run and the baseline run*.

Old:

```text
It passes when every story and acceptance is accepted, every stop reached the human, and the cost and the time of each first-pass story are within 25 % of run 4's above.
```

New:

```text
It passes when every story and acceptance is accepted, every stop reached the human, and the cost and the agent minutes of each story that is first-pass in both runs are within 25 % of run 4's above; run 4's first-pass stories are F0001-S0002, F0001-S0003, F0002-S0002, F0002-S0003 and F0003-S0001. The minutes from start to archive are recorded beside them but not compared: they hold the human's waits and the tick's pause, which differ between v1 and v1.1. The stories' criteria were rewritten for v1.1 (both sides of every rule as rows of one test, three new criteria in F0001-S0003), so the comparison is of the same stories, not of the same texts.
```

Same file, section *What a run looks like*.

Old:

```text
v1 called the smoke test the demo stage; the stories were the same, in v1's form.
```

New:

```text
v1 called the smoke test the demo stage; the stories built the same things, in v1's form and with v1's criteria.
```

### Edit E: the demo Makefile's header on mutmut

File `planning/overnight/demo/todo-service/project/Makefile`, line 10.

Old:

```make
# `[tool.mutmut]`, whose runs leave out the tests that read the source); security/semgrep holds
```

New:

```make
# `[tool.mutmut]`, which copies docs/ beside the mutated source); security/semgrep holds
```

### Edit F: bandit as the template runs it

File `planning/overnight/demo/todo-service/project/Makefile`, line 54 (one leading tab).

Old:

```make
	uv run bandit -q -c pyproject.toml -r $(SOURCE)
```

New:

```make
	uv run bandit -q -r $(SOURCE)
```

File `planning/overnight/demo/todo-service/project/pyproject.toml`, lines 110 to 113: remove these four lines (the section, its table, its key and the blank line after it).

Old:

```toml
# --- SAST --------------------------------------------------------------------
[tool.bandit]
targets = ["src"]

```

New: nothing.
