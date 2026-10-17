---
stage: review
pr: 155
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# One default identity, one way to find sudo, one way to read the arguments

## Assignment (as of log entry 1)

Three copies that the acceptances noticed and nobody owned, fixed without a change of behaviour, and the documents brought in line with the human's change H3 (the document check is now a check of the docs stage).

1. One default git identity (the parked draft F0010-S0025, taken in whole). The factory's default commit identity `factory <factory@noreply.invalid>` is written twice in `src/`: `DEFAULT_GIT_IDENTITY` in `src/factory/domain/settings.py` and the literal default of `GitOptions.identity` in `src/factory/domain/git.py`. The constant moves into `factory.domain.git`, beside `GitIdentity`; `GitOptions.identity` defaults to it and `factory.domain.settings` imports it from there. `GIT_USER_NAME` and `GIT_USER_EMAIL` still override each half on its own.
2. One way to find `sudo`. `ClaudeCodeRuntime` starts the fixed `SUDO_EXECUTABLE` (`/usr/bin/sudo`) while the preflight's `tool:sudo` item searches the `PATH`. `build_boundaries` now gives the runtime the `sudo` that the same `which` finds, and `/usr/bin/sudo` only when it finds none (the preflight then stops the machine with `tool:sudo` anyway; FEATURE decision 17).
3. One way to read the arguments. `check_documents.main`, `health.main` and `watch.main` pass `sys.argv[1:] if argv is None else argv` to `argparse`, which reads `sys.argv[1:]` itself when given `None`; each passes `argv`.

None of this changes behaviour. Criterion 6 already passes on today's code, because `argparse` reads `sys.argv[1:]` itself when given `None`; it pins that the commands still read the process's arguments, and the Demo's second command shows the change.

The docs criterion also rewrites the sentence that says `make check` does not run the document check: the human's `make documents` target is now a check of the docs stage (FEATURE decision 12), which supersedes F0011 decision 13 for that stage and takes in F0011-S0007's repair of the reference to "F0011, decision 13".

## Interface

- `factory.domain.git.DEFAULT_GIT_IDENTITY: GitIdentity`, equal to `GitIdentity(name="factory", email="factory@noreply.invalid")`, the one place in `src/factory` that holds the string literal `"factory@noreply.invalid"`. `GitOptions.identity` defaults to `DEFAULT_GIT_IDENTITY`. `factory.domain.settings` imports it from `factory.domain.git` and re-exports it explicitly (`from factory.domain.git import DEFAULT_GIT_IDENTITY as DEFAULT_GIT_IDENTITY`, since `mypy --strict` refuses an implicit re-export), so `factory.domain.settings.DEFAULT_GIT_IDENTITY` stays importable as the same object; `InstanceSettings.git_identity` and `read_settings` keep their defaults and overrides.
- `ClaudeCodeRuntime.sudo_executable -> str`, a read-only property: the executable given as `sudo_executable` (default `SUDO_EXECUTABLE`).
- `factory.entry.wiring.build_boundaries(settings, token, *, hosting=None, which: Callable[[str], str | None] = shutil.which) -> Boundaries`: its `agent_runtime` is a `ClaudeCodeRuntime` whose `sudo_executable` is `which("sudo")`, or `SUDO_EXECUTABLE` when that is `None`. Nothing else it builds changes. `run_instance` calls it as before.
- `factory.entry.check_documents.main`, `factory.entry.health.main` and `factory.entry.watch.main` call `parser.parse_args(argv)`; their arguments and behaviour do not change.

Tests: `tests/domain/test_default_git_identity.py` (criteria 1 to 4, with `modules()` and `string_literals()` of `tests/source_search.py`); a new test function in `tests/entry/test_wiring_boundaries.py` (criterion 5), with that module's `settings` fixture and `FakeHostingService` as `hosting`; `tests/entry/test_entry_arguments.py` (criterion 6, with `write_documents` and `clean_texts` of `tests/document_texts.py`). No existing test changes.

## Acceptance criteria

1. `factory.domain.git.DEFAULT_GIT_IDENTITY == GitIdentity(name="factory", email="factory@noreply.invalid")`.
2. `GitOptions().identity is DEFAULT_GIT_IDENTITY`, and `factory.domain.settings.DEFAULT_GIT_IDENTITY is factory.domain.git.DEFAULT_GIT_IDENTITY`.
3. The string literal `"factory@noreply.invalid"` occurs exactly once among the string literals of the modules under `src/factory`, in `factory.domain.git`.
4. `read_settings` with neither `GIT_USER_NAME` nor `GIT_USER_EMAIL` gives `git_identity == DEFAULT_GIT_IDENTITY`; with only `GIT_USER_NAME=Ann` it gives `GitIdentity(name="Ann", email="factory@noreply.invalid")`.
5. `build_boundaries` with a `which` that returns `/opt/tools/sudo` for `"sudo"` gives an agent runtime whose `sudo_executable` is `/opt/tools/sudo`; with a `which` that returns `None` for it, `/usr/bin/sudo`. Two rows of one parametrized test.
6. `main()` with `sys.argv` set (monkeypatched) to the program name and the given arguments ends as `main(<those arguments>)` ends: `check_documents` with `--root <a folder of clean documents from tests/document_texts.py>` returns 0; `health` with `--state-directory <a folder holding an empty health status>` returns 0; `check_documents` with `--colour` and `watch` with `--follow` each raise `SystemExit` with code 2 (argparse's refusal). Four rows of one parametrized test.
7. `make check` stays green.
8. docs: the project guide's section *The document check* says that v1's pipeline configuration for this repository runs it as a check of the docs stage through `make documents` (red holds the work item at the docs stage), that `make check` does not run it, and gives the reason by pointing to the decision log; the decision log gets an entry of 2026-10-17 that supersedes the F0011-S0005 entry for the docs stage: the check runs where the four documents are written, so a missing row or a v1 word is found before the human sees the pull request. The same entry says that `DEFAULT_GIT_IDENTITY` now lives in `factory.domain.git` and is the one default, which settles the "Known duplicate" of the 2026-10-16 identity entry, and the project guide's `GitOptions` table names `DEFAULT_GIT_IDENTITY` as the default of `identity`. The project guide's text about which `sudo` the runtime starts (*The agent runtime*, *The `claude -p` runtime*) says that the wiring gives it the `sudo` on the `PATH`, as the preflight's item finds it, and `/usr/bin/sudo` when there is none. Outside `## Replaced from v1` no v1 word of the document check is used (not the file name of v1's configuration), and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from factory.domain import git, settings
print(git.GitOptions().identity is git.DEFAULT_GIT_IDENTITY, settings.DEFAULT_GIT_IDENTITY is git.DEFAULT_GIT_IDENTITY, git.DEFAULT_GIT_IDENTITY)
"
grep -rn --include='*.py' 'factory@noreply.invalid' src/factory
```
Expect: the first command prints `True True name='factory' email='factory@noreply.invalid'`. The second prints exactly one line, in `src/factory/domain/git.py`.

```bash
grep -rn --include='*.py' 'sys.argv\[1:\] if argv is None else argv)' src/factory/entry/check_documents.py src/factory/entry/health.py src/factory/entry/watch.py; echo "status $?"
```
Expect: the single line `status 1`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: the single line `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.git.DEFAULT_GIT_IDENTITY` and its explicit re-export in `factory.domain.settings`, `ClaudeCodeRuntime.sudo_executable`, `build_boundaries(..., which=shutil.which)`, the three `main` functions calling `parser.parse_args(argv)`). The tests are named by file.
   - Criteria: each can be tested by one test function. Criteria 1 to 3 pin the identity (value, identity of the object, a single literal in `src`). Criterion 4 covers the unset and the partly overridden identity. Criterion 5 covers the `which` found and not found sides, as two rows. Criterion 6 covers the success rows and the refusal rows, with exit code 2. The Interface comment on the `sudo` fallback to `/usr/bin/sudo` has criterion 5. The docs criterion 8 lists what each document must say.
   - Demo: all three commands run. Each `Expect:` line can be checked: the printed values and the one grep line, `status 1` for the absent argv expression, and `documents ok`.
   - Architecture: the constant sits in `factory.domain`, the `which` injection is in `factory.entry.wiring`, and the runtime only gets a property. No layer rule is touched.
   - Scope: within F0012 items 1.2 and 1.9, taken from decisions 3, 12, 16 and 17 of FEATURE.md. It does not touch any "Out of scope" item.
3. tester: Wrote the tests for criteria 1 to 6. They follow the Interface's test plan, and no existing test changed.
   - criterion 1: tests/domain/test_default_git_identity.py::test_the_default_identity_is_factory_at_noreply_invalid
   - criterion 2: tests/domain/test_default_git_identity.py::test_git_options_and_settings_share_the_one_default_identity
   - criterion 3: tests/domain/test_default_git_identity.py::test_the_default_email_is_written_once_in_src_in_the_git_domain_module (uses `modules()` and `string_literals()` of tests/source_search.py; the list of holding modules must be exactly `["factory.domain.git"]`)
   - criterion 4: tests/domain/test_default_git_identity.py::test_read_settings_defaults_the_identity_and_overrides_each_half_alone
   - criterion 5: tests/entry/test_wiring_boundaries.py::test_the_built_agent_runtime_starts_the_sudo_on_the_path_or_usr_bin_sudo (two rows: found `/opt/tools/sudo`, and `None` → `/usr/bin/sudo`; uses the module's `settings` fixture and `FakeHostingService` as `hosting`)
   - criterion 6: tests/entry/test_entry_arguments.py::test_main_without_arguments_reads_the_process_arguments (four rows: check_documents `--root` with clean documents → 0; health `--state-directory` with an empty `HealthStatus` written through `health_store` → 0; check_documents `--colour` and watch `--follow` → SystemExit code 2. `sys.argv` is monkeypatched to the program name plus its arguments.)

   Files created: tests/domain/test_default_git_identity.py and tests/entry/test_entry_arguments.py. Appended one test to tests/entry/test_wiring_boundaries.py.

   Result of `make test`:
   - tests/domain/test_default_git_identity.py fails at collection with an ImportError: `DEFAULT_GIT_IDENTITY` cannot yet be imported from `factory.domain.git`.
   - Both rows of the sudo test fail because `build_boundaries` has no `which` keyword yet and `ClaudeCodeRuntime` has no `sudo_executable` property.
   - The criterion 6 test already passes on today's code, as the ticket expects. I confirmed this with one extra run of that module alone, beyond the single `make test` run the stage asks for.

   `make lint` is green. Two lint fixes on the way:
   - I reversed the equality in criterion 1's assertion (SIM300).
   - I put the program name into each command-line builder, so the parametrized test has fewer positional arguments (PLR0917).

   Nothing needed interpreting, and nothing is open.

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/domain/test_default_git_identity.py - ImportError while importing...
4. coder: I removed the three copies without changing behaviour. `make check` is green and all three Demo commands print what they should. Everything is in one commit on the branch.
      - Identity: `DEFAULT_GIT_IDENTITY` is now defined in `src/factory/domain/git.py`, next to `GitIdentity`, and `GitOptions.identity` defaults to it. `src/factory/domain/settings.py` imports it and re-exports it.
      - sudo: `ClaudeCodeRuntime.sudo_executable` is a new read-only property in `src/factory/adapters/claude_runtime.py`. `build_boundaries` in `src/factory/entry/wiring.py` takes a keyword `which`, defaulting to `shutil.which`, and gives the runtime `which("sudo") or SUDO_EXECUTABLE`.
      - Arguments: `check_documents.main`, `health.main` and `watch.main` now call `parser.parse_args(argv)`. I removed the `import sys` from `check_documents` and `health`, which no longer use it.
      - Main decision: the Interface asks for the re-export to be written `from factory.domain.git import DEFAULT_GIT_IDENTITY as DEFAULT_GIT_IDENTITY`. ruff refuses that line (PLC0414, an alias that does not rename). I re-export through an `__all__` in `settings.py` instead, listing `DEFAULT_GIT_IDENTITY`, `InstanceSettings`, `read_setting_file` and `read_settings`, with a one-line comment saying why. `git_cli.py` and `wiring.py` already do the same. The `__all__` only decides which imported names are re-exported; the names `settings.py` defines itself stay importable, and mypy confirms it. I rejected a `# noqa: PLC0414`: `CLAUDE.md` does not allow lint markers outside `process.py`. I also rejected `DEFAULT_GIT_IDENTITY = git.DEFAULT_GIT_IDENTITY`: it would look like a second definition.
      - Refactor: I read the diff and found nothing to clean up, so there is no separate refactor commit. My one work commit is labelled `refactor(domain,entry)` because the ticket changes no behaviour.
      - Open: the docs part of criterion 8 (project guide, decision log) is left to the documenter.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
