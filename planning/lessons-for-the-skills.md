# Lessons for the skills

The rules `factory-rf`'s `CLAUDE.md` gained while v1 built v1.1, sorted by where each belongs so that later projects benefit too. Started on 2026-10-14 by the human's decision; the session adds a row whenever a new rule goes into `CLAUDE.md`.

## How it is used

1. Done at F0010's fresh pre-check (2026-10-16): the general rows go into the agents F0010-S0017 ships as v1.1's own, each in the role that applies it, as a part of their own after v1's verbatim texts (`planning/v1-texts/` stays an unchanged copy, since Q29 compares v1.1's baseline run with v1's on the same instructions); the Python rows go into a `template/CLAUDE.md` for Python projects beside `template/factory/pipeline.yml` (F0010-S0012, which ships it).
2. The project-only rows stay in `factory-rf`'s `CLAUDE.md`.
3. v1's own skills (`factory/claude/skills/`) are read-only by the folder rule; updating them is the human's call.

## The lessons

| Lesson | Kind | Where it belongs | Since |
|---|---|---|---|
| Run `make check` and every make target in the foreground and read its output; never start one in the background, never wait with `pgrep -f` (it matches its own command line) | general | every role skill | 2026-10-14, F0007-S0009, F0008-S0002 |
| A stage whose change the factory checks right after it (the documenter's documents) does not run the same check itself | general | documenter skill | 2026-10-17, the human's go to speed up F0012 |
| A test that waits for a time limit leaves the started process room to start (tests run in parallel; a one-second limit can kill a child before it writes anything) | Python | tester skill | 2026-10-17, F0012 H3 (two flaky tests under pytest-xdist) |
| Mutation testing (mutmut) runs only as sweeps outside the factory, on a fresh copy with a fresh `mutants/`; no stage runs it and it is never part of `make check`. It leaves out the structural tests that read the source, because mutmut rewrites the source with its own import | Python | template `pyproject.toml` and `CLAUDE.md` | 2026-10-17, F0012 H5 (the first trial stopped on the import whitelist test); 2026-10-19, the human (F0031: per-story and acceptance runs cost more time than they found) |
| `dataclasses.replace(x, **{name: value})` fails `mypy --strict` (`arg-type` on every field); one typed `Callable[[T], T]` per parametrized row instead | Python | template `CLAUDE.md`, tester skill | 2026-10-17, F0012-S0016 (the coder's question) |
| One test checks that every model is frozen and forbids unknown keys; a new model needs no test of its own for those, and a model reading a tool's output is a listed exception with `extra="ignore"` | project | `factory-rf`'s `CLAUDE.md` | 2026-10-17, F0012 H7 after S0018 |
| A question is recorded on one tick and posted on the next; a test that reads or answers it runs one more tick after the blocking one | project | `factory-rf`'s `CLAUDE.md` | 2026-10-17, F0012-S0021 (the coder's question) |
| A story's text is scanned by detect-secrets on `main` and on its branch: quote no `secret`/`token` key with a value (`secrets: green`, a compose block naming `secrets/hosting-token`); give such values as prose | general | the drafting brief, intake | 2026-10-17, F0012-S0029 and F0013-S0001 |
| Give a long project command (`make check`, over two minutes) the shell tool's largest timeout, so that the tool does not move it to the background | general | every role skill | 2026-10-16, F0010's second acceptance |
| Before writing a helper, search for one that does the same and reuse or extend it; the reviewer counts a second copy as a finding | general | coder and reviewer skills | 2026-10-14 |
| Every clause of an Interface rule has its own criterion, on both sides (an ordering, the second branch of an "or", a "when longer than", the value for every kind an enum names, an exact value beyond its first part) | general | intake skill; the planning briefs | 2026-10-14, four F0006 stories |
| Every behaviour the Assignment, the Interface or a feature decision states has its own criterion | general | intake skill | 2026-10-13, F0001-S0016 |
| Every stated limit is tested on both sides; the sides of one rule are rows of one parametrized test, shared setup a fixture | general (Python example) | tester and reviewer skills | 2026-10-13 and 2026-10-14 |
| Test data a test builds (a work item text, a state, a definition, a push) is valid under the readers and validators already built, unless the test is about that rule | general | tester skill | 2026-10-14, F0007-S0005, S0009, S0010, F0008-S0004; in `CLAUDE.md` Tests since 2026-10-16, F0011-S0001 |
| A story that changes a test another story wrote names that test and has the human's word; the tester makes the change, never the coder | general | intake, tester and coder skills | 2026-10-13 |
| The project guide is an index plus one file per domain, each well under the 2,000 lines the file tool reads by default | general | documenter skill; the project-guide form (R17) | 2026-10-14 |
| Never use the value of a call to a function typed `-> None` | Python | template `CLAUDE.md` | 2026-10-12, F0001-S0001 |
| Refused fields of a Pydantic model are tested through a variable typed `type[BaseModel]`; frozen fields through `setattr` with the name in a variable; an abstract class through a variable typed `type[object]` | Python | template `CLAUDE.md` | 2026-10-12 to 14 |
| Fake commit ids and other hex test values are low-entropy (`"a" * 40`), so detect-secrets stays green without a baseline entry | Python (any stack with detect-secrets) | template `CLAUDE.md` | 2026-10-13, F0001-S0011 |
| `human.push_file` pushes only changed text (an unchanged file makes an empty commit) | project | `factory-rf`'s `CLAUDE.md` | 2026-10-14 |
| A pipeline definition written in a test passes every load-time rule unless the test is about that rule | project | `factory-rf`'s `CLAUDE.md` | 2026-10-14 |
| The linters exclude the human's planning folder (`extend-exclude` in `[tool.ruff]`), so a script kept there never blocks a stage | project | `factory-rf`'s `pyproject.toml` | 2026-10-18, F0014-S0001 (the tester stalled on two scripts in `planning/`) |
| A standing leave to move a shared test helper (a helper, constant or fixture copied from another story's tests) to one shared place under `tests/`, every earlier test keeping its name and what it checks; the tester moves it, the reviewer lists each earlier test file changed and its leave | any | template `CLAUDE.md`, the shipped tester, coder and reviewer | 2026-10-18, F0016 (the shakedown run: copied helpers cost a review round and a question per story) |
