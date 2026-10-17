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

## Docs
- `README.md` is for the newcomer: what it is, how to run it, where to look next. `docs/project-guide.md` is the guide for agents and `docs/decisions.md` the decision log. The documenter stage keeps them true from each story's docs criterion; the coder does not write them.
- Docstrings: one per module (its purpose, a sentence) and one per public class and function in <the packages that form the interface>; none on private names or where the signature says it all. Comments say why, never what.

## Checks
- `make check` must be green before any stage reports done. It runs <lint, types, sast, secrets, licenses, tests with coverage>. `make lint` and `make test` run <subset>; the pipeline knows only these three targets.

## Not without asking (end the stage with `question`)
- New dependency, new top-level package, change to `factory/`, change to a test you did not write, a new entry in `.secrets.baseline` or a `pragma: allowlist secret`, a `nosemgrep` or `nosec` marker, a licence outside the allow list.
