# <project>

<One sentence: what this repository is.> Built by the factory (github.com/pkrahmer/factory); the pipeline's rules reach every agent in its instructions, so this file holds only what is true of this project.

## Language
- Everything in this repository is English: code, comments, docs, work items, commit messages.

## Architecture
- <Layers, dependency direction, what is pure, where wiring happens.>
- <Typing and validation rules.>

## Tests
- <Framework; where tests live; fixtures; what may be faked and what may not.>
- Tests pass `mypy --strict` once the code exists: never use the value of a call to a function typed `-> None` (no `assert f() is None`); call it as a statement.
- To test that a Pydantic model refuses an unknown or a wrong-typed field, construct it through a variable typed `type[BaseModel]`; assign to a field of a frozen model with `setattr(instance, field, value)`, the field's name in a variable; call an abstract class through a variable typed `type[object]`. None of these needs a `type: ignore`.
- Fake commit ids and other hexadecimal test values are low-entropy (`"a" * 40`), so that `make secrets` stays green without a baseline entry.
- A test that waits for a time limit gives the process it starts room to start: the tests may run on every core at once, so a child can need more than a second before it does anything. Give it a limit of a few seconds and an upper bound on the elapsed time with room above it; never check that a one-second limit is met to the tenth.
- The standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier test module still holds as a copy of a shared one, may be moved to one shared place under `tests/` (a module at its root, or `tests/conftest.py` for a fixture), and the earlier tests that held it changed to use it from there, without asking, as long as every earlier test keeps its name and checks the same thing. The tester makes the move, never the coder, and its entry names each earlier test file it changed. Any other change to a test another story wrote still needs the human's leave.

## Docs
- `README.md` is for the newcomer: what it is, how to run it, where to look next. `docs/project-guide.md` is the guide for agents and `docs/decisions.md` the decision log. The documenter stage keeps them true from each story's docs criterion; the coder does not write them.
- Docstrings: one per module (its purpose, a sentence) and one per public class and function in <the packages that form the interface>; none on private names or where the signature says it all. Comments say why, never what.

## Checks
- `make check` must be green before any stage reports done. It runs `make lint` (ruff check and format check), `make types` (`mypy --strict`), `make layers` (<the layers command>), `make sast` (semgrep with the rules in `security/semgrep`, and bandit over <the package folder>), `make secrets` (detect-secrets against `.secrets.baseline`, over the files changed against `origin/main`, every tracked file on `main` itself), `make licenses` (pip-licenses against an allow list for the production dependencies) and `make test` (pytest on every core with pytest-xdist, coverage as `pyproject.toml` sets it, a JUnit report in `.reports/junit.xml`). Each target ends with the line `<target>: green (<seconds> s)`; `make check` ends with `check: green`.
- `make lint` and `make test` run those two alone. `make duplicates` writes similar code (pylint's duplicate-code) and dead code (vulture) in <the package folder> to `.reports/` and counts them on its last line: a report, never a check. `make mutants FEATURE=<feature id>` runs mutmut over the modules of <the package folder> that the feature's story commits on `origin/main` changed (`work item <id>: ...`, or the pull request's title `<id>: ...` after a squash merge), and lists the surviving mutants: for a sweep by hand, never run by a stage and never part of `make check`; mutmut rewrites the source with its own import, so its runs leave out the tests that read the source (`pytest_add_cli_args` in `[tool.mutmut]` of `pyproject.toml`). The pipeline definition names `check`, `lint`, `test` and `sync`; a project that wants the duplicates report after the coder adds `duplicates` to its `project_commands` and to the `reports` of the stage `doing`.

## Not without asking (end the stage with `question`)
- New dependency, new top-level package, change to `factory/`, change to a test you did not write beyond the standing leave under *Tests*, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
