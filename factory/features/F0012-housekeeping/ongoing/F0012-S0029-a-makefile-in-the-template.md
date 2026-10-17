---
stage: accept
pr: 180
blocked: null
comments_seen: 1
round: 0
attempts: 1
---
# A Makefile in the template

## Assignment (as of log entry 1)

The human decided on 2026-10-17 that what v1 learns while it builds v1.1 must also reach what v1.1 ships. `template/` holds a pipeline definition and a `CLAUDE.md` but no `Makefile`, so a new project (first the todo demo, plan step 3) writes its project commands from nothing and misses what F0012 made of `factory-rf`'s own: one shell per recipe, each target's time on its last line (H1, read by S0012), `make test` on every core with a JUnit report (H1), `make secrets` over the changed files only (H1), the duplicates report (H3) and `make mutants` (H5). This story adds `template/Makefile`, a Python example in that pattern: the contract's three targets `check`, `lint` and `test`, the other targets of `check`, and `duplicates` and `mutants`. `documents` is left out: it runs `factory-rf`'s own document check, which a project does not have. `duplicates` writes and counts the findings but compares them with no baseline, because the comparison is `factory-rf`'s own module, which a project does not have either (FEATURE decision 50). `mutants` finds the modules a feature changed by the subjects `work item <feature>-S<nnnn>: ...` of the commits on `origin/main`, which v1.1 writes on every commit of a work item's branch since F0012-S0030; it takes the feature from an acceptance's branch, `work-item/<feature>-A<nnnn>`. The story is built after F0012-S0030 and depends on it (FEATURE decision 51). Where a project decides, the file has placeholders: its package folder and its layers command. Its header names the development dependencies the targets need. `template/CLAUDE.md`'s *Checks* says what the targets do, as `factory-rf`'s `CLAUDE.md` does, and carries the Python row of `planning/lessons-for-the-skills.md` on mutation testing (2026-10-17, H5): mutmut's runs leave out the tests that read the source. The template is in the coder's write paths; the tests that pin the template's files change by the human's leave (FEATURE decision 49).

## Interface

`template/Makefile` (new), exactly this text; recipe lines start with one tab:

```make
# The contract between a project and the factory is three targets: `check`, `lint`, `test`.
# `check` is what every stage must pass; `lint` and `test` are what the tests stage runs on its
# own (the type check is skipped there, because the modules under test do not exist yet).
# `duplicates` and `mutants` are reports outside `check`. A Python example with a src layout.
#
# The development dependencies the targets need, pinned in pyproject.toml: ruff, mypy, semgrep,
# bandit, detect-secrets, pip-licenses, pytest, pytest-cov, pytest-xdist, pylint, vulture,
# mutmut, and the tool of the layers command (import-linter for `uv run lint-imports`).
# pyproject.toml configures them (coverage's `source` and `fail_under`, mypy's `strict`, and
# `[tool.mutmut]`, whose runs leave out the tests that read the source); security/semgrep holds
# the vendored semgrep rules and .secrets.baseline the reviewed findings of detect-secrets.
.PHONY: check lint types layers sast secrets licenses test duplicates mutants
.SILENT:

# What the project decides: the folder of its package, and the command that checks its layers.
SOURCE = src/<package>
LAYERS = <layers command>

# One shell per recipe, stopped by its first failing line, so that a recipe can time itself.
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

# `$(start)` opens a recipe and `$(green)` ends it with "<target>: green (<seconds> s)",
# the line the factory's records of project commands read.
start = started=$$(date +%s%N)
green = tenths=$$(( ($$(date +%s%N) - started) / 100000000 )); echo "$@: green ($$((tenths / 10)).$$((tenths % 10)) s)"

check: lint types layers sast secrets licenses test
	echo "check: green"

lint:
	$(start)
	uv run ruff check --output-format=concise .
	uv run ruff format --check --quiet .
	$(green)

types:
	$(start)
	uv run mypy
	$(green)

layers:
	$(start)
	$(LAYERS)
	$(green)

# Static analysis: semgrep with rule sets vendored under security/semgrep (copy the sets you
# want from github.com/semgrep/semgrep-rules; offline and pinned), plus bandit.
sast:
	$(start)
	SEMGREP_SEND_METRICS=off uv run semgrep scan --config security/semgrep --metrics=off \
	  --disable-version-check --quiet --error $(SOURCE)
	uv run bandit -q -r $(SOURCE)
	$(green)

# Secrets beyond the reviewed baseline, in the files changed against origin/main (committed,
# staged, unstaged or new); every tracked file on main itself or without origin/main.
secrets:
	$(start)
	if [ "$$(git rev-parse HEAD)" != "$$(git rev-parse --verify --quiet origin/main || true)" ] && base=$$(git merge-base HEAD origin/main 2>/dev/null); then
	  files=$$( { git diff --name-only --diff-filter=d "$$base"; git ls-files --others --exclude-standard; } | sort -u)
	else
	  files=$$(git ls-files)
	fi
	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline)$$' || true)
	if [ -n "$$files" ]; then uv run detect-secrets-hook --baseline .secrets.baseline $$files; fi
	$(green)

# Licences of the production dependencies against an allow list.
ALLOWED_LICENSES = MIT;MIT License;MIT-0;BSD;BSD License;BSD-2-Clause;BSD-3-Clause;3-Clause BSD License;ISC;ISC License;Apache-2.0;Apache 2.0;Apache Software License;PSF-2.0;Python Software Foundation License;MPL-2.0;Mozilla Public License 2.0 (MPL 2.0);GNU Library or Lesser General Public License (LGPL);Apache-2.0 OR BSD-3-Clause
licenses:
	$(start)
	uv export -q --frozen --no-dev --no-emit-project --format requirements-txt -o .licenses-requirements.txt
	uv run pip-licenses --from=mixed --allow-only="$(ALLOWED_LICENSES)" \
	  --packages $$(sed -n 's/^\([A-Za-z0-9_.-]*\)==.*/\1/p' .licenses-requirements.txt) > /dev/null
	rm -f .licenses-requirements.txt
	$(green)

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

# Similar code (pylint's duplicate-code) and dead code (vulture) in the package, written to
# .reports/ and counted on the last line, which a report records; never a failure for its findings.
duplicates:
	mkdir -p .reports
	uv run pylint --disable=all --enable=duplicate-code --output-format=json --exit-zero $(SOURCE) > .reports/similar-code.json
	uv run vulture $(SOURCE) --min-confidence 60 > .reports/dead-code.txt || [ $$? -eq 3 ]
	similar=$$(grep -c '"symbol": "duplicate-code"' .reports/similar-code.json || true)
	dead=$$(wc -l < .reports/dead-code.txt)
	echo "duplicates: $$similar similar code, $$dead dead code, in .reports/"

# Mutation testing of the modules of the package that one feature's stories changed:
# `make mutants FEATURE=F0001`. Slow, so not part of `check`; the feature acceptance runs it,
# and on an acceptance's branch (work-item/<feature id>-A<number>) FEATURE is that feature. A story's
# commits are those whose subject starts `work item <id>:`, or `<id>:` after a squash merge.
FEATURE ?= $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null | sed -n 's|^work-item/\(F[0-9]\{4\}\)-A[0-9]\{4\}$$|\1|p')
MUTATED = $(wildcard $(shell git log --format= --name-only -E --grep='^(work item )?$(FEATURE)-S[0-9]{4}([: ]|$$)' origin/main -- '$(SOURCE)/*.py' 2>/dev/null | sort -u))
mutants:
	$(start)
	if [ -z "$(FEATURE)" ]; then echo "mutants: set FEATURE, as in make mutants FEATURE=F0001"; exit 2; fi
	if [ -z "$(MUTATED)" ]; then echo "mutants: no module under $(SOURCE) changed by $(FEATURE)"; exit 0; fi
	uv run mutmut run $(foreach module,$(MUTATED),"$(subst /,.,$(patsubst src/%.py,%,$(module))).*")
	# mutmut generates mutants for every module; the ones outside the feature stay "not checked".
	uv run mutmut results | { grep -v ': not checked$$' || true; }
	$(green)
```

`template/CLAUDE.md`, *Checks*: its one bullet is replaced by these two, and nothing else in the file changes:

```text
- `make check` must be green before any stage reports done. It runs `make lint` (ruff check and format check), `make types` (`mypy --strict`), `make layers` (<the layers command>), `make sast` (semgrep with the rules in `security/semgrep`, and bandit over <the package folder>), `make secrets` (detect-secrets against `.secrets.baseline`, over the files changed against `origin/main`, every tracked file on `main` itself), `make licenses` (pip-licenses against an allow list for the production dependencies) and `make test` (pytest on every core with pytest-xdist, coverage as `pyproject.toml` sets it, a JUnit report in `.reports/junit.xml`). Each target ends with the line `<target>: green (<seconds> s)`; `make check` ends with `check: green`.
- `make lint` and `make test` run those two alone. `make duplicates` writes similar code (pylint's duplicate-code) and dead code (vulture) in <the package folder> to `.reports/` and counts them on its last line: a report, never a check. `make mutants FEATURE=<feature id>` runs mutmut over the modules of <the package folder> that the feature's story commits on `origin/main` changed (`work item <id>: ...`, or the pull request's title `<id>: ...` after a squash merge), and lists the surviving mutants: run by the feature acceptance, never part of `make check`; mutmut rewrites the source with its own import, so its runs leave out the tests that read the source (`pytest_add_cli_args` in `[tool.mutmut]` of `pyproject.toml`). The pipeline definition names `check`, `lint` and `test`; a project that wants the duplicates report after the coder adds `duplicates` to its `project_commands` and to the `reports` of the stage `doing`.
```

Tests:

- New: `tests/test_template_makefile.py`. The behaviour tests copy `template/Makefile` into `tmp_path / "project"` and run `make <target>` there with `run_process` (`factory.adapters.process`), stderr merged, the environment of `os.environ` without `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `FEATURE`, `SOURCE` and `LAYERS` (an outer `make`, such as `make mutants FEATURE=F0012` running the tests through mutmut, passes its variables on through `MAKEFLAGS`), with `tmp_path / "bin"` first on `PATH`; that folder holds the recording stand-in of `tests/adapters/claude_stand_in.py`, written with `write_stand_in(tmp_path / "bin", steps)` and renamed from `claude` to `uv`: it plays one `Step` (its `stdout` and `exit_status`) per call, in the order the recipe calls the tools, and records each call in `tmp_path / "bin"`, outside `project` (so that `git ls-files --others` never lists it); `read_calls(tmp_path / "bin")` gives the calls' arguments. Variables a target needs are given on the command line (`SOURCE=src/todo`, `LAYERS=uv run lint-imports`). A git repository the test needs is made with `run_git` in the copy's folder; `origin/main` is set with `git update-ref refs/remotes/origin/main <commit>`. The text tests read `template/Makefile` itself.
- By the human's leave (FEATURE decision 49), and no other change to an earlier story's test, in `tests/test_claude_files.py`: `TEMPLATE_RULES_LINES` gets the two bullets of *Checks* in place of the one; `test_template_holds_only_the_rules_file_and_the_pipeline_definition` is renamed `test_template_holds_only_the_rules_file_the_makefile_and_the_pipeline_definition`, expects the entries `["CLAUDE.md", "Makefile", "factory", "factory/pipeline.yml"]` and checks that `template/Makefile` is a file.

## Acceptance criteria

1. `template/` holds exactly `CLAUDE.md`, `Makefile`, `factory` and `factory/pipeline.yml` (the renamed test of the Interface).
2. The `.PHONY` line of `template/Makefile` names exactly `check lint types layers sast secrets licenses test duplicates mutants`, in that order, and the file has no target `documents`.
3. The prerequisites of `check` are exactly `lint types layers sast secrets licenses test`, in that order, and its one recipe line is `echo "check: green"`.
4. The file has the placeholder lines `SOURCE = src/<package>` and `LAYERS = <layers command>`.
5. The comment lines at the top of the file, before its first line that is not a comment, name each of `ruff`, `mypy`, `semgrep`, `bandit`, `detect-secrets`, `pip-licenses`, `pytest`, `pytest-cov`, `pytest-xdist`, `pylint`, `vulture`, `mutmut` and `import-linter`: thirteen rows of one parametrized test.
6. Each of `lint`, `types`, `layers`, `sast`, `licenses` and `test`, run with a stand-in `uv` that exits 0 for every call, exits with status 0 and ends with a line matching `^<target>: green \(\d+\.\d s\)$`; run with a stand-in that exits 1 for every call, it exits with a status other than 0, prints no line containing `green`, and the stand-in was called exactly once (the recipe stops at its first failing line). Twelve rows of one parametrized test.
7. `make test` calls the stand-in once with arguments that start with `run pytest` and hold `-n auto` and `--junit-xml=.reports/junit.xml`, and leaves the folder `.reports` in the copy's folder; with a stand-in that exits 5 (pytest's status when it collects no test, as on an empty project), it exits with status 0 and ends with a line matching `^test: green \(\d+\.\d s\)$`.
8. `make secrets` in a git repository whose tracked files are `.secrets.baseline`, `Makefile`, `README.md`, `src/todo/a.py` and `uv.lock` calls `uv run detect-secrets-hook --baseline .secrets.baseline` with these files, and ends with `secrets: green (<seconds> s)` in every row: on `main` with `origin/main` at `HEAD`, the files `Makefile README.md src/todo/a.py`; with no `origin/main`, the same three; on a branch `work-item/F0001-S0001` from `origin/main` with one commit changing `src/todo/a.py`, an untracked `src/todo/b.py` and an unstaged change of `uv.lock`, the files `src/todo/a.py src/todo/b.py`; on such a branch whose one commit changes only `uv.lock`, no call of the stand-in; and on the branch whose commit changes `src/todo/a.py`, a stand-in that exits 1 (detect-secrets found a secret) gives a status other than 0 and no line containing `green`. Five rows of one parametrized test. <!-- pragma: allowlist secret -->
9. `make duplicates SOURCE=src/todo` ends with the line `duplicates: <n> similar code, <k> dead code, in .reports/`, where `<n>` is the number of messages with `"symbol": "duplicate-code"` that the stand-in printed for `pylint` (as pylint's JSON, indented by 4) and `<k>` the number of lines it printed for `vulture`: no message and no line with vulture's status 0 give `0 similar code, 0 dead code` and status 0; two messages and two lines with vulture's status 3 (vulture's status for findings) give `2 similar code, 2 dead code` and status 0; two lines with vulture's status 1 give a status other than 0 and no line that starts with `duplicates:`; a stand-in that exits 1 for `pylint` gives a status other than 0, no line that starts with `duplicates:`, and exactly one call. Four rows of one parametrized test.
10. `make mutants SOURCE=src/todo`, in a git repository whose `origin/main` holds a commit with the subject `work item F0003-S0001: doing ends: review` (the subject F0012-S0030's code gives a stage's end) that adds `src/todo/items.py`, a commit with the subject `F0003-S0002: Lists (#7)` (a squash merge's subject) that adds `src/todo/lists.py`, and a commit with the subject `work item F0004-S0001: doing ends: review` that adds only `README.md`: on the branch `work-item/F0003-A0001` it calls the stand-in with `run mutmut run todo.items.* todo.lists.*` and then with `run mutmut results`, prints the line `todo.items.x_add__mutmut_1: survived` that the stand-in printed for `run mutmut results` and not its line `todo.other.x_f__mutmut_1: not checked`, and ends with `mutants: green (<seconds> s)`; on that branch with `FEATURE=F0004` given, it prints `mutants: no module under src/todo changed by F0004`, exits with status 0 and does not call the stand-in; on the branch `work-item/F0003-S0002` (a story's, not an acceptance's) and in a folder that is no git repository, it prints `mutants: set FEATURE, as in make mutants FEATURE=F0001`, exits with status 2 and does not call the stand-in. Four rows of one parametrized test.
11. `template/CLAUDE.md` is the text of `TEMPLATE_RULES_LINES` with the two bullets of the Interface as its *Checks* (the existing `test_template_rules_file_is_the_python_project_text`).
12. `make check` stays green.
13. docs: in the project guide, section *The shipped agents, settings and template*, *The template* says that `template/` holds three files, and a bullet on `template/Makefile` says what its targets are (the contract's three, the other targets of `check`, `duplicates` without a baseline, `mutants` by feature id from the commit subjects `work item <id>: ...` and from an acceptance's branch), that a project fills in `SOURCE` and `LAYERS`, and that its header names the development dependencies; the operator guide's paragraph on the shipped agents and the template (which says that a new project starts from `template/` in the image) names the `Makefile` beside the pipeline definition and the `CLAUDE.md`; the decision log records why `documents` is left out and `duplicates` has no baseline in the template (both are `factory-rf`'s own modules). No other document changes, no v1 word of the document check is used outside a `## Replaced from v1` section, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
make -f template/Makefile mutants 2>/dev/null; echo "status $?"
```
Expect: two lines, `mutants: set FEATURE, as in make mutants FEATURE=F0001` and `status 2`.

```bash
make -f template/Makefile lint 2>&1 | tail -1
```
Expect: one line `lint: green (<seconds> s)`, the template's `lint` run for real over this repository.

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_template_makefile.py tests/test_claude_files.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: `template/Makefile` is given as exact text, and the two replacement bullets for `template/CLAUDE.md` *Checks* are exact text. The test changes in `tests/test_claude_files.py` are named (the one rename, the new `TEMPLATE_RULES_LINES` bullets), with the human's leave in FEATURE decision 49. The new test module and its stand-in harness are specified concretely: `run_process`, `write_stand_in`, `read_calls`, the cleaned environment, and how `origin/main` is set up.
   - Criteria: 13 criteria. Each is testable by one function or one parametrized test, and the row counts add up (13 header names, 6 targets × 2 sides = 12 rows, 5 for secrets, 4 for duplicates, 4 for mutants). Every behaviour the Interface comments state has a criterion: the timed last line, exit status 5 on an empty project, secrets over the changed files with the `uv.lock` and baseline exclusion, the duplicates count lines, mutants by commit subject (both the `work item` and the squash-merge forms) and by acceptance branch. Every rule has its failing side: a stand-in that exits 1 (and called exactly once), a secret found, vulture status 1, pylint failing, and mutants with no FEATURE, with a story branch, and outside a git repository.
   - Demo: all three commands are runnable. The `mutants` run with no FEATURE on a ticket branch gives status 2 and the stated line. `lint` runs for real over this repository, which `make lint` already keeps clean. The pytest line is checkable. Every Expect line says something the output can be checked against.
   - Architecture: the change only adds a file under `template/` (inside the coder's write paths) and a tests module at the `tests/` root, where a module outside the layers belongs. No `src/factory` module changes, so the layering is not touched. Layers stay a project placeholder, as CLAUDE.md R8 requires.
   - Scope: this is the "What v1.1 ships to new projects" item of FEATURE.md's Scope. Its dependency on S0030 is stated in the story and in FEATURE decision 51. `documents` and the baseline comparison are left out, with reasons in decisions 50 and 53. None of it falls under Out of scope.
3. stage tests stalled: Stuck: the write guard refuses every write by the tester. Creating `tests/test_template_makefile.py` with the Write tool failed with `PreToolUse:Write hook error: [factory-guard tester]: guard: no lane configured for 'tester' in factory/stages.yml`. That is a problem in the pipeline's configuration, not a path outside my lane. Fixing it means changing `factory/stages.yml`, which is the human's file (R15). I did not use shell writes to get around the guard.

   Where I stopped:
   - **Done before the guard error:** I edited `tests/test_claude_files.py` with a shell script, exactly as the Interface allows (FEATURE decision 49), for criteria 1 and 11:
     - `TEMPLATE_RULES_LINES` now has the two *Checks* bullets in place of the one. I checked that the joined strings equal the Interface's two bullet lines exactly.
     - The test is renamed to `test_template_holds_only_the_rules_file_the_makefile_and_the_pipeline_definition`. It now expects `["CLAUDE.md", "Makefile", "factory", "factory/pipeline.yml"]` and checks that `template/Makefile` is a file.
     - This change is still in the working tree. I tried to revert it after the error, but `git checkout` was denied. If the guard decides it was outside my lane, the factory may undo it.
   - **Not written:** `tests/test_template_makefile.py` (criteria 2–10) was fully drafted but not saved. The plan for it:
     - Text tests read `template/Makefile`: the `.PHONY` list and no `documents` target, the prerequisites and one recipe line of `check`, the `SOURCE`/`LAYERS` placeholders, and a 13-row test of the tool names in the header.
     - Behaviour tests copy the Makefile to `tmp_path/project` and run `make` through `run_process`. Stderr is merged, `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `FEATURE`, `SOURCE` and `LAYERS` are removed from the environment, and `tmp_path/bin` comes first on `PATH`. That folder holds the `claude_stand_in`, renamed to `uv`.
     - Planned rows: 6 targets × pass/fail, two tests for `make test`, 5 rows for secrets, 4 for duplicates, 4 for mutants. Git repositories are built with `run_git`, `write_files` and `commit_all`, and `origin/main` is set with `update-ref`.
   - **Not run:** `make test` and `make lint`.

   Open for the human: give the `tester` role a lane in `factory/stages.yml` (it should include `tests/*` and the story file), then run the tests stage again.; denied: Write: /work/factory-rf/tests/test_template_makefile.py; partial work committed
4. tester: Tests written for every criterion. The tester lane in `factory/stages.yml` now exists, so this run finished what the stalled run left. The `tests/test_claude_files.py` change from that run was already committed in a398d663. I checked it against the Interface and left it as it is.

   Criterion → test:
   - criterion 1: tests/test_claude_files.py::test_template_holds_only_the_rules_file_the_makefile_and_the_pipeline_definition (renamed by the human's leave, FEATURE decision 49)
   - criterion 2: tests/test_template_makefile.py::test_phony_line_names_the_targets_and_there_is_no_documents_target
   - criterion 3: tests/test_template_makefile.py::test_check_runs_the_other_targets_and_says_green
   - criterion 4: tests/test_template_makefile.py::test_package_folder_and_layers_command_are_placeholders
   - criterion 5: tests/test_template_makefile.py::test_header_names_the_development_dependency (13 rows; each name is matched as a whole word, so `pytest` is not found inside `pytest-cov`)
   - criterion 6: tests/test_template_makefile.py::test_target_is_timed_green_and_stops_at_its_first_failing_line (6 targets × statuses 0 and 1 = 12 rows)
   - criterion 7: tests/test_template_makefile.py::test_test_runs_pytest_on_every_core_with_a_junit_report and ::test_test_is_green_when_no_test_is_collected
   - criterion 8: tests/test_template_makefile.py::test_secrets_scans_the_changed_files_or_every_tracked_file (5 rows: main, no-origin, branch, lock-only, secret-found)
   - criterion 9: tests/test_template_makefile.py::test_duplicates_counts_similar_and_dead_code (4 rows: none, findings, vulture-fails, pylint-fails)
   - criterion 10: tests/test_template_makefile.py::test_mutants_runs_mutmut_over_the_modules_the_feature_changed (4 rows: acceptance-branch, no-module, story-branch, no-repository; each row is a frozen `MutantsCase` dataclass, to stay under ruff's limit on positional arguments)
   - criterion 11: tests/test_claude_files.py::test_template_rules_file_is_the_python_project_text (unchanged; it reads the new `TEMPLATE_RULES_LINES`, whose *Checks* now holds the two bullets)
   - criterion 12: the factory's `make check` after the coder. Criterion 13 is for the docs stage.

   Harness, as the Interface says:
   - A `project` fixture copies `template/Makefile` into `tmp_path/project`.
   - `_make` runs `make` there through `run_process`, with stderr merged and a time limit of 120 s. The environment is `os.environ` without MAKEFLAGS, MFLAGS, MAKELEVEL, FEATURE, SOURCE and LAYERS, with `tmp_path/bin` first on PATH.
   - In `tmp_path/bin`, `write_stand_in` writes the stand-in and the test renames it from `claude` to `uv`. `read_calls` gives the calls.
   - Repositories are built with `run_git`, `write_files` and `commit_all`. `origin/main` is set with `git update-ref refs/remotes/origin/main <rev-parse HEAD>`.

   Files: created `tests/test_template_makefile.py`; `tests/test_claude_files.py` was changed in the earlier run.

   Red run (`make test`, run once): `tests/test_template_makefile.py` fails with errors, because `template/Makefile` does not exist yet. The fixture's copy fails and the text tests cannot read the file. The changed tests in `test_claude_files.py` fail on the template's file list and on the *Checks* text. No module was missing: the imports `factory.adapters.process`, `adapters.claude_stand_in`, `git_support` and `shipped_agents` already exist.

   `make lint`: green. The type check was skipped, as this stage says.

   Not decided by me: only the call counts the criteria name are asserted (the fail rows of criterion 6, and the pylint-fails row of criterion 9).

   `make lint`: lint: green (0.0 s)
   `make test`: ERROR tests/test_template_makefile.py::test_mutants_runs_mutmut_over_the_modules_the_feature_changed[no-repository]
5. coder: Added the template's Makefile and its Checks text. Commit a0f3004f.

   What I built:
   - `template/Makefile` (new): the Interface's text, copied verbatim out of the ticket's `make` block. The copy kept the tab-indented recipe lines (49 lines with a leading tab, none indented with spaces).
   - `template/CLAUDE.md`: the one *Checks* bullet is replaced by the Interface's two bullets. Nothing else in the file changed.

   Main decision: I copied both texts out of the ticket with a script instead of retyping them, so they match the Interface byte for byte. Retyping was rejected because a stray space instead of a tab, or a changed character, would break the exact-text tests. I wrote no new code under `src/factory`.

   Verification:
   - `tests/test_template_makefile.py` and `tests/test_claude_files.py`: all pass.
   - The demo works: `make -f template/Makefile mutants` prints `mutants: set FEATURE, as in make mutants FEATURE=F0001` and status 2, and `make -f template/Makefile lint` ends `lint: green (0.0 s)`.
   - `make check`: `check: green`.

   Refactor: none needed. The diff is two template files whose text the Interface fixes exactly.

   Open: criterion 13 (the project guide, the operator guide and the decision log) is for the docs stage. I noticed nothing else outside the ticket.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
6. reviewer: no findings.

   What I checked, in `git diff main...HEAD -- . ':!factory'`:
   - **Interface text.** `template/Makefile` is byte for byte the Interface's `make` block: I diffed the committed file against the block extracted from the ticket, and they are identical. Its recipe lines start with a tab. `template/CLAUDE.md` changes only its *Checks*: the one bullet becomes the Interface's two bullets.
   - **Criteria 1–11, one by one.**
     - Each criterion has its test, named as the tester's entry 4 lists them.
     - The parametrized row counts match the criteria: 13, 12, 5, 4 and 4.
     - The failing sides are tested:
       - criterion 6: a stand-in exiting 1 makes the target fail with exactly one call;
       - criterion 7: exit 5 is green, and exit 1 is red through the criterion 6 rows;
       - criterion 8: the secret-found row, and the lock-only row with no call;
       - criterion 9: vulture status 1, and pylint failing with exactly one call;
       - criterion 10: a story branch and a folder that is not a git repository give status 2 with no call, and `FEATURE=F0004` with no module gives status 0 with no call.
     - Both sides of the `origin/main` choice in `make secrets` are tested: on main or with no origin it reads every tracked file, on a branch only the changed files. The exclusion of `uv.lock` and `.secrets.baseline` is checked in the main row.
     - The test harness follows the Interface: `run_process`, stderr merged, the six variables dropped from the environment, and the stand-in in `tmp_path/bin` renamed to `uv`. It reuses the existing `run_git`, `write_files`, `commit_all` and `write_stand_in`/`read_calls`, so no helper is duplicated.
     - The `tests/test_claude_files.py` change is exactly the one FEATURE decision 49 allows: the rename, the new file list with the `Makefile` check, and the two bullets in `TEMPLATE_RULES_LINES`.
   - **Checks.** The coder's entry records `make check: check: green` and `duplicates: 0 new`.
   - **Architecture.** Nothing under `src/factory` changes, and the new test module sits at the `tests/` root, which fits a module outside the layers.
   - **Security.** The diff adds no suppression marker and no secret.
   - **Ticket hygiene.** The log's main decision is stated: the texts were copied by script rather than retyped. `Assignment` matches what was built. Criterion 13 (docs) still describes what the docs stage must write.

   One thing to know about the diff, not a finding against this story:
   - The diff also shows `image/Dockerfile` and `docs/operator-guide.md` (the Claude Code pin `2.1.296`, the base image digest and the Debian package pins). Those changes come from the human's own commit b642dd31 on this branch, not from the coder.
   - The documenter should know that the operator guide already changed on this branch before adding criterion 13's sentence about the template.
7. documenter: criterion 13 written. I ran `python -m factory.entry.check_documents`, which prints `documents ok`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/project-guide.md`, *The template*: it now says `template/` holds three files. A new bullet on `template/Makefile` covers:
     - the contract's three targets and the other targets of `check`;
     - the one shell per recipe, the `<target>: green (<seconds> s)` last line, the JUnit report and the changed-files `secrets`;
     - `duplicates` with no baseline, and `mutants` by feature id from the commit subjects (`work item <id>: ...`, or `<id>: ...` after a squash merge) and from an acceptance's branch;
     - no `documents` target;
     - the `SOURCE` and `LAYERS` placeholders, and the header that names the development dependencies.
   - `docs/operator-guide.md`: the paragraph on the shipped agents and the template now names the `Makefile` beside the pipeline definition and the `CLAUDE.md`, and says that `SOURCE` and `LAYERS` are filled in.
   - `docs/decisions.md`: a new entry on why `documents` is left out and why `duplicates` has no baseline in the template. Both are `factory-rf`'s own modules (F0012 decisions 50 and 53).

   Cross-read and found current: the other parts of the project guide's template section (the pipeline definition, the no-forms paragraph) and `template/CLAUDE.md` against the diff. The Makefile text matches the Interface and the code is consistent with it.

   Not touched: the diff shows `image/Dockerfile` pin changes from the human's commit b642dd31. They are unrelated to this story, and the operator guide's pins were already updated in that commit.

   No findings.

   `make check`: check: green
   `make documents`: documents ok
8. demo: Demo run from the repository root on branch `ticket/F0012-S0029-a-makefile-in-the-template`. I ran the three commands as written, in order.

   1. `make -f template/Makefile mutants 2>/dev/null; echo "status $?"`
   ```
   mutants: set FEATURE, as in make mutants FEATURE=F0001
   status 2
   ```
   Met its Expect line. The current branch is a ticket branch, not `work-item/<feature>-A<nnnn>`, so no feature is found and the target refuses with status 2.

   2. `make -f template/Makefile lint 2>&1 | tail -1`
   ```
   lint: green (0.0 s)
   ```
   Met its Expect line. I ran it again without `tail`: it prints ruff's `All checks passed!` before the green line, so ruff really ran over the repository (`ruff check --output-format=concise .` and `ruff format --check --quiet .`). The 0.0 s comes from ruff's cache.

   3. `uv run pytest --no-header -p no:cacheprovider tests/test_template_makefile.py tests/test_claude_files.py`
   ```
   ...............................................................          [100%]
   63 passed in 2.06s
   ```
   Met its Expect line: 63 passed, with no failed, error or skipped count.

   Against the acceptance criteria: `template/` holds exactly `CLAUDE.md`, `Makefile` and `factory/` (criterion 1). The Makefile has the placeholder `SOURCE = src/<package>` (criterion 4). Nothing in the demo contradicts any criterion. No findings.
