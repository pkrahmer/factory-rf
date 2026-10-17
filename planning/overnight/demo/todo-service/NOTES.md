# Notes on the todo demo (staging only, not committed into `demo/`)

Written on 2026-10-17 from the brief `planning/overnight/briefs/draft-demo-todo-service.md`. Source: v1's demo, `pkrahmer/factory` `demo/` (`README.md`, `project/`, `features/`), and run 4's cost records in v1's `docs/reference/data/demo-dispatches.jsonl` (first 59 lines) and `docs/reference/16-evidence/README.md` ("Run 4, item by item").

## The tree

```text
planning/overnight/demo/
├── README.md                                  the index, with the row `todo-service/` (H6's text)
└── todo-service/
    ├── README.md
    ├── NOTES.md                               this file, staging only
    ├── project/
    │   ├── .gitignore
    │   ├── .secrets.baseline
    │   ├── CLAUDE.md
    │   ├── Makefile
    │   ├── README.md
    │   ├── pyproject.toml
    │   ├── uv.lock
    │   ├── factory/pipeline.yml
    │   ├── factory/story-form.md
    │   ├── security/semgrep/python.yml
    │   ├── src/app/__init__.py
    │   └── tests/__init__.py
    └── features/
        ├── F0001-todo-service/feature.md, backlog/ S0001 to S0004
        ├── F0002-operations/feature.md, backlog/ S0001 to S0003
        └── F0003-search/feature.md, backlog/ S0001
```

## What changed from v1's demo, and why

### The form of every story

- File places: v1's folder of unstarted stories becomes `backlog/`, `FEATURE.md` becomes `feature.md` (v1.1's `FEATURE_FILE_NAME`), the ids and slugs stay (`F0001-S0001-domain-model-and-in-memory-repository.md`).
- Sections: v1's assignment section is `## Description` (its "as of log entry 1" suffix dropped), the demo section is `## Smoke test`, the append-only log is `## Journal`, empty: a backlog story carries no journal entries (rule 10 of the form check); the factory writes entry 1 when the story starts.
- No front matter, as rule 7 requires of a backlog story.
- Each `Expect:` line follows its code block after one blank line and starts with how many lines the block prints.
- Every story names its test files in the Interface (`Tests: ...`), so that the tester and the reviewer agree where a criterion is tested.

### The substance, story by story

What each story builds is v1's; these criteria changed so that v1.1's pipeline can build the story first-pass (both sides of every rule as rows of one parametrized test, every behaviour its own criterion, a smoke test that leaves nothing in `/tmp`):

- F0001-S0001: criterion 5 now holds both sides of the length rule (1 and 200 characters accepted, 201 refused) as one parametrized test, where v1 had "longer than 200" and "exactly 200" apart and no lower side; criteria 6 and 7 (the UTC conversion, the naive time) name both ways of building a todo; criteria 3, 4 and 16 say they are rows of one parametrized test; criterion 23 says the import test names only the forbidden imports. The docs criterion writes `docs/project-guide.md` (v1: `docs/architecture.md`). 25 criteria (v1: 26; two of v1's merged into criterion 5).
- F0001-S0002: v1's criteria 5 and 6 (the done filter, each side) are one parametrized criterion 5; v1's 14 is criterion 13 with four rows. The docs criterion writes `docs/project-guide.md`.
- F0001-S0003: the length rule's two sides are one criterion (3); the done filter's two sides one criterion (6); the three unknown-id 404s (GET, PATCH, DELETE; v1's 10, 16 and 18) one criterion (15) with three rows. New: criterion 18 (`get_service` hands each app its own service: the Interface's `dependencies.py` had no criterion of its own), 19 (every error body has `detail` as its only key, decision 6), 21 (the schema's paths and their tag). The Description says that the coder writes `docs/openapi.json` with `make openapi` (see choice 2). The smoke test runs the server in a temporary directory with a `trap` that kills it and removes the directory.
- F0001-S0004: the switch's two sides are one criterion (7, v1's 7 and 8); criterion 9 names `monkeypatch.chdir`; the Interface says that the tester's addition to `tests/repository/test_contract.py` is by the human's leave, and that the semgrep rule `project-no-sql-text` refuses SQL in strings, so the Interface's "no SQL in strings" is checked by `make sast` and not only by the reviewer. The smoke test keeps the database in a temporary directory and ends with `database file exists` instead of v1's `ls -l | cut` (a permission string depends on the umask).
- F0002-S0001: criterion 3 also holds `build_app({"TODO_DB": ""})`, the gap run 4's intake asked about (F0002 decision 6); criterion 6 says that `docs/openapi.json` must still equal the schema after a route is added, which the coder meets with `make openapi` (F0001-S0003's test would fail otherwise).
- F0002-S0002: v1's criteria 2 and 3 (the usage error) are one parametrized criterion 2 with four rows; criterion 1 adds "writes nothing to stderr"; criterion 3 says how `sys.argv` is set and what both cases return; criterion 4 names the deny-list import test.
- F0002-S0003: v1's criteria 5 and 6 (`/stats` on data and on an empty repository) are one parametrized criterion 5; criterion 7 is the `docs/openapi.json` criterion of F0002-S0001.
- F0003-S0001: criterion 8 holds both sides of the search length (200 characters accepted, 201 refused; v1 tested only the refused side); criteria 3 and 5 are rows of one parametrized test; criterion 10 is the `docs/openapi.json` criterion. The F0003 `feature.md` has no order sentence: it has one story.

### The features

- `feature.md` keeps v1's sections (*Goal*, *Scope*, *Out of scope*, *Stories*, *Decisions taken for the human*), without v1's folder comment. The story lists use `S0001: <title>`. The order sentence says "start one at a time, the next when the one before is archived in `done/`".
- F0001 decision 11 is new (the coder's write path for `docs/openapi.json`); F0002 decision 4 is reworded (v1 named the reference's fourth story); F0002 decision 6 is new (an empty `TODO_DB`).

### The project

- `CLAUDE.md`: the template's (`template/CLAUDE.md` after F0012-S0028 and S0029) filled with v1's demo project: v1's *Architecture* and *Tests* bullets, the template's Python bullets (the `-> None` trap, `type[BaseModel]` and `setattr`, low-entropy hexadecimal values, the time-limit bullet of S0028), the two *Checks* bullets of S0029 with `uv run lint-imports` and `src/app` filled in. Added from `planning/lessons-for-the-skills.md`, general and Python rows the template does not carry: search for a helper first (*Architecture*); every limit on both sides, the sides as rows of one parametrized test, shared setup a fixture; test data valid under the code already built; structural tests as deny lists (the mutation-testing row, see choice 11); make targets in the foreground with the shell tool's largest timeout (*Checks*); a story that changes another story's test names it (*Not without asking*). Left out: the project-guide split row (the guide of a small service stays short), the rows that are `factory-rf`'s own (`human.push_file`, pipeline definitions in tests). v1's "security review for API stories" bullet is gone: `make sast` now runs semgrep and bandit, and pip-audit is gone (choice 4).
- `Makefile`: S0029's template text with `SOURCE = src/app` and `LAYERS = uv run lint-imports`, plus `openapi` (v1's target, timed like the others) and the exit status 5 of pytest accepted in `test` (v1's rule: no test collected is green on the empty project, impossible once the first test exists). The header names `openapi`.
- `pyproject.toml`: v1's, with every dependency pinned with `==` (the development pins are `factory-rf`'s; the production pins are what `uv lock` resolved on 2026-10-17), the template's tools added (semgrep, detect-secrets, pip-licenses, pytest-xdist, pylint, vulture), pip-audit removed, `addopts` without `-q`, `tmp_path_retention_policy = "failed"`, coverage excluding the `...` bodies of a protocol, and `[tool.mutmut]` with `-p no:cov`.
- `uv.lock`: generated with `uv lock` from that `pyproject.toml` in a temporary directory (111 packages).
- `factory/pipeline.yml`: the template's, with two changes (choices 2 and 3).
- `factory/story-form.md`: new; its five headings are those of the form check (`## Description`, `## Interface`, `## Acceptance criteria`, `## Smoke test`, `## Journal`), each with a paragraph of guidance.
- `security/semgrep/python.yml`: new; three of the four rules of `factory-rf`'s own file, renamed `project-...` (not the YAML rule: the project reads no YAML), plus `project-no-sql-text`.
- `.secrets.baseline`: new, generated by `detect-secrets scan` (no findings).
- `.gitignore`: v1's without the pip-audit files, with `.import_linter_cache/`, `.licenses-requirements.txt` and `.reports/`.
- `README.md`, `src/app/__init__.py`, `tests/__init__.py`: v1's; the README says "smoke test" and lists the new checks. `pyproject.toml` names the README, so the package does not build without it.

### The READMEs

- `demo/README.md`: H6's text of F0012's `FEATURE.md`, with the row `` `todo-service/` ``.
- `todo-service/README.md`: v1's demo README in v1.1's words and commands: the token file and the instance's two variables instead of `.env`, `REPOS` and `GH_TOKEN`; `docker compose -f image/compose.yml` with the project per instance (F0012-S0022); the agent's login as `agent`; `factory-watch`, `factory-health` and `factory-bill` instead of v1's board and cost lines; starting a story by moving it from `backlog/` to `in-progress/`; the acceptance as a work item with its own pull request, merged or closed by the session; the stops of v1.1 in the stop conditions. Run 4's numbers are from its cost records (per work item: agent runs, agent minutes, cost, minutes from start to archive, what happened); v1's demo README's two other runs (the clean run and the acceptances) follow them. New sections: the shakedown run and the baseline run (plan steps 4 and 10).

## Choices taken for the human, to confirm

1. **The documents.** The project keeps the template's `docs/project-guide.md` (the guide for agents: layers, domain model, service) in place of v1's `docs/architecture.md`, and keeps v1's `docs/api.md` (what the schema cannot say) and `docs/openapi.json`. Taken for the human, to confirm.
2. **The coder writes `docs/openapi.json`.** v1.1's template gives the coder `src/*` only, and the documenter `docs/*`; F0001-S0003's test that the committed schema equals the app's would fail at the coder's `make check`, and the undo would revert the coder's `make openapi`. So the coder's write paths are `["src/*", "docs/openapi.json"]` (F0001 decision 11). The other way, the documenter runs `make openapi`, leaves `make check` red between `doing` and `docs`. Taken for the human, to confirm.
3. **`make duplicates` is a report of `doing`**, with `time_limit: 5` among the `project_commands` (40 + 10 + 5 = 55 minutes within the lease of 60), as the template's `CLAUDE.md` describes; it puts the count line into the coder's journal entry, which the reviewer reads. Taken for the human, to confirm; without it the pipeline definition is the template's but for choice 2.
4. **No pip-audit.** v1's `make check` ran pip-audit, which needs the network; the template has no audit target, and its `sast`, `secrets` and `licenses` take the place of v1's checks. Taken for the human, to confirm.
5. **Pinned versions.** Production: `fastapi==0.141.1`, `pydantic==2.14.1`, `sqlalchemy==2.1.5`, `uvicorn[standard]==0.54.0`; `httpx==0.28.1`; the rest at `factory-rf`'s pins; `requires-python = ">=3.12,<3.13"`, `hatchling==1.32.4`. SQLAlchemy is 2.1, not the 2.0 v1's story named, so the story says "SQLAlchemy Core" without a version. Taken for the human, to confirm.
6. **`make test` accepts pytest's exit status 5** (no test collected), unlike S0029's template recipe, so that `make check` is green on the empty project. Taken for the human, to confirm (the template may want the same).
7. **The layers output is not filtered.** `LAYERS = uv run lint-imports` prints import-linter's banner (about 25 lines) on every `make check`; v1 piped it through `grep`. Kept as the template has it, so a broken contract shows its details. Taken for the human, to confirm.
8. **Coverage leaves out `...` lines** (`exclude_also`), so the repository protocol's method bodies do not count as missed. Taken for the human, to confirm.
9. **The secrets baseline** was generated outside a git repository (`detect-secrets scan` then lists no files); it holds no result, and `generated_at` is 2026-10-17. Taken for the human, to confirm.
10. **The story form** carries a paragraph of guidance under each heading. The form check reads only the headings. Taken for the human, to confirm.
11. **Structural tests are deny lists.** The stories' import tests (F0001-S0001 criterion 23, F0001-S0003 criterion 22, F0002-S0002 criterion 4) name only what a module must not import, so they hold on mutmut's rewritten copy and `[tool.mutmut]` needs no `--deselect`; `CLAUDE.md` says so and tells an agent that needs one to ask. This applies the mutation-testing lesson without knowing the test names in advance. Taken for the human, to confirm.
12. **No feature form.** `factory/feature-form.md` is a protected path, but nothing reads it and S0023 does not require it; the demo ships none, and `feature.md` follows v1's sections. Taken for the human, to confirm.
13. **The criteria rewritten for first-pass building** (listed above, story by story), among them three new criteria in F0001-S0003 and the answer to run 4's intake question in F0002-S0001. They keep each story's substance but change its text from v1's, which matters for the comparison with run 4. Taken for the human, to confirm.
14. **Smoke tests clean up after themselves**: the two server blocks work in `mktemp -d` with a `trap` that kills the server and removes the directory (the smoke tester's lesson of F0012-S0011). Taken for the human, to confirm.
15. **The baseline's measure.** The README states the baseline run's pass rule from the plan (every work item accepted, every stop reached the human, cost and time per first-pass story within 25 % of run 4's) and lists run 4's numbers per work item; "time" is read as the minutes from start to archive, the only time per story run 4 recorded besides agent minutes. Taken for the human, to confirm.
16. **The demo index row** names the kind `web service`, the stack, 8 stories in 3 features and 3 acceptances, and "the todo run (plan step 10), measured against v1's run 4". Taken for the human, to confirm.

## The commands I ran, with their last lines

No git command was run (the session's instruction). Every check ran in a temporary directory that removed itself (`tempfile.TemporaryDirectory()`), on a copy of `project/`.

1. `uv lock` on a copy of `pyproject.toml` with the four production pins and `httpx` left open, to find the versions: `Resolved 111 packages in 2.49s`; `fastapi 0.141.1`, `sqlalchemy 2.1.5`, `uvicorn 0.54.0`, `httpx 0.28.1`, `starlette 1.8.0`, `pydantic 2.14.1`.
2. `uv lock` on the pinned `pyproject.toml`, the lock file copied into `project/`: `Resolved 111 packages in 36ms`.
3. On a copy of the empty project: `uv sync --frozen -q` (exit 0); `uv run detect-secrets scan` (exit 0, `"results": {}`; git's `fatal: not a git repository` on stderr, as the copy is no repository); then each target:
   - `make lint`: `All checks passed!`, `lint: green (0.0 s)`
   - `make types`: `Success: no issues found in 2 source files`, `types: green (0.6 s)`
   - `make layers`: `Contracts: 1 kept, 0 broken.`, `layers: green (0.3 s)`
   - `make sast`: `sast: green (2.8 s)`
   - `make licenses`: `licenses: green (0.3 s)`
   - `make test`: `no tests ran in 3.34s`, `test: green (4.2 s)` (with coverage's warning `No data was collected`, once per worker)
   - `make duplicates`: `duplicates: 0 similar code, 0 dead code, in .reports/`
   - `uv run detect-secrets-hook --baseline .secrets.baseline <every file of the copy but uv.lock and the baseline>`: exit 0, no output.
4. `make check -o secrets` on a copy of the final project (`-o secrets` skips the one target that needs a git repository): `lint: green (0.1 s)`, `types: green (1.1 s)`, `layers: green (0.5 s)`, `sast: green (4.4 s)`, `licenses: green (0.5 s)`, `test: green (5.3 s)`, `check: green`, exit 0. Before it, a probe on the same copy (a module with a protocol stub and one test, then removed) showed the `...` exclusion: `TOTAL 5 0 0 0 100%`, `1 passed in 5.06s`, `test: green (6.6 s)`.
5. The pipeline reader, `RuamelPipelineDefinitionReader().parse` of `project/factory/pipeline.yml`: loads; first stage `intake`; stages `intake, tests, doing, review, docs, smoke-test, acceptance, approval, done`; project commands `check, duplicates, lint, test`; the coder's `time_limit` 40 and `lease_duration` 60.
6. The story check, two ways, over the eight stories at the paths they will have (`factory/features/<feature>/backlog/<story>.md`):
   - S0023's `backlog_story_findings`, which does not exist yet, done by hand as S0023 states it: `check_story_place(path, feature_file_exists=...)`, then `FrontmatterWorkItemReader().parse_specification` and `check_story_form(document, <project/factory/story-form.md>, folder="backlog")`: no finding for any of the eight.
   - Today's `factory.entry.check_story.main(<the eight paths>, root=<a temporary copy laid out as factory/story-form.md and factory/features/>)`: eight lines `<path>: ok`, status 0.
7. The word check: `factory.domain.documents._wording` (the `GLOSSARY_FORBIDDEN` words and the `REPLACED_PHRASES`) over every file of the staging folder but `uv.lock`: no finding. This file's `## Replaced from v1` section is the one place with v1's words.
8. `uv run --no-project python -c "import time; time.sleep(30)" &`, then `kill` of that `uv` process: its child was gone a second later, so the smoke tests' `kill $pid` of `uv run uvicorn` stops the server (F0001-S0004 restarts it on the same port).

Not run: `make secrets` and `make mutants` (both call git, and the copy is no repository); `python -m factory.entry.check_demos` (F0012-S0023 is not built yet); the smoke tests themselves (no code exists).

What the checks left behind, and removed: `uv run` in `factory-rf` (for steps 5 to 7) created `factory-rf/.venv`, which did not exist before, and rewrote 21 bytecode files under `src/factory/*/__pycache__`; both were removed. The three pytest runs left `/tmp/pytest-of-factory/pytest-14` to `pytest-16` and four `uv-*.lock` files in `/tmp`; removed. pytest keeps three of its folders, so the older ones it deleted in `/tmp/pytest-of-factory` (if any existed) are gone; the folder itself stays, empty. uv's package cache in the home directory holds the packages of `uv.lock`.

## What I could not place

- v1's twelve paths with a deliberate defect each (its maintainers' mode): v1.1's shakedown run (plan step 4) takes their place in the README, without the list; the paths belong to the fault-injection paths of `factory-rf`, not to this demo.
- v1's `scripts/demo-check.sh` (the check of the target repository before a run): v1.1 has no such script; the README's step 6 (the health status) and the preflight take its place.
- The three stories run 4's F0001 acceptance proposed (F0001-S0005 to S0007, built after run 4): not part of the demo, as in v1's.
- Whether v1.1 lets the session's own commit subject `F0001-S0001: start` disturb `make mutants`: the grep matches it, but the commit touches no file under `src/app`, so it adds no module; noted, not changed.
- The agent's login survives a `docker compose down` only if `/home/agent` is a volume; the README says it may need repeating, as the operator guide does.

## Replaced from v1

v1's words in the demo, and what the demo says instead:

| v1 | v1.1 |
|---|---|
| ticket | story, work item |
| `drafts/`, `ongoing/` | `backlog/`, `in-progress/` |
| promote | start |
| `## Assignment (as of log entry 1)` | `## Description` |
| `## Demo` | `## Smoke test` |
| `## Log (append only)` with entry 1 | `## Journal`, empty |
| `FEATURE.md` | `feature.md` |
| `template/stages.yml`, `TICKET.md`, `FEATURE.md` | `factory/pipeline.yml`, `factory/story-form.md` |
| acceptor, `ACCEPTANCE.md` | acceptance reviewer, the acceptance work item `F0001-A0001` |
| the stage `accept` | the approval |
| hardening mode | the shakedown run |
| `docs/architecture.md` | `docs/project-guide.md` |

## The pre-check's edits (2026-10-17)

From `planning/overnight/precheck/demo-todo-service-1.md`, applied with its exact old and new texts:

- Required edit 1: F0001-S0001's Tests line (factories are `Callable[[Path], TodoRepository]`, called with `tmp_path`) and F0001-S0004's Tests line (its factory returns `SqliteTodoRepository.from_path(tmp_path / "todo.db")`).
- Required edit 2: `project/CLAUDE.md`, the `request.param` trap added to the `mypy --strict` bullet.
- Required edit 3: F0012-S0029's Interface `make test` (exit status 5) and its criterion 7, in both copies (`factory/features/F0012-housekeeping/drafts/` and `planning/overnight/stories/F0012-housekeeping/drafts/`, byte-identical); decision 54 added to both copies of F0012's `FEATURE.md`.
- Edit A: F0001-S0001 criterion 5 names `Todo(...)`, `Todo.new` and `with_title`.
- Edit B: F0001-S0002 gets criterion 15 (the default clock); the later criteria are renumbered 16 and 17.
- Edit C: F0001-S0003 criterion 9 covers `GET`, `PATCH` and `DELETE` of a malformed id.
- Edit E: `project/Makefile` header line on mutmut now says it copies `docs/`.
- Edit F: `project/Makefile` runs `bandit -q -r $(SOURCE)`; `[tool.bandit]` and its comment line removed from `project/pyproject.toml`.
- Edit D (the baseline's time) is NOT applied: the human decides.

Drafter's choices: 1 to 5, 7 to 14 and 16 are confirmed by the pre-check. Choice 6 (`make test` accepts exit status 5) is kept and carried into S0029 (required edit 3, decision 54). Choice 15 (the baseline's measure) is open for the human (edit D).

- Edit D applied by the session: the human answered on 2026-10-17 that the baseline compares cost and agent minutes of the stories first-pass in both runs; start-to-archive minutes are recorded, not compared (choice 15 settled).
