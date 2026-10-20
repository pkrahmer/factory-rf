# The contract between a repository and the factory is three targets: `check`, `lint`, `test`.
# `check` is the gate every stage must pass; `lint` and `test` are what the tests stage runs on
# its own (the type check is skipped there, because the modules under test do not exist yet).
# What each target runs is the repository's business; this file is a Python example. `types` and
# `layers` are in `check`, not in `lint`: the tests stage runs `lint` only.
.PHONY: check lint types layers sast secrets licenses test duplicates documents mutants
.SILENT:

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

# The exit status is import-linter's own: no pipe, so a broken contract fails the target.
layers:
	$(start)
	uv run lint-imports
	$(green)

# Static analysis: semgrep with rule sets vendored under security/semgrep (copy the sets you
# want from github.com/semgrep/semgrep-rules; offline and pinned), plus bandit.
sast:
	$(start)
	SEMGREP_SEND_METRICS=off uv run semgrep scan --config security/semgrep --metrics=off \
	  --disable-version-check --quiet --error src
	uv run bandit -q -c pyproject.toml -r src
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
	files=$$(printf '%s\n' $$files | grep -vE '^(uv\.lock|\.secrets\.baseline|planning/.*|docs/runs/.*|.*\.costs\.jsonl)$$' || true)
	if [ -n "$$files" ]; then uv run detect-secrets-hook --baseline .secrets.baseline $$files; fi
	$(green)

# Licences of the production dependencies against an allow list.
ALLOWED_LICENSES = MIT;MIT License;MIT-0;BSD;BSD License;BSD-2-Clause;BSD-3-Clause;3-Clause BSD License;ISC;ISC License;Apache-2.0;Apache 2.0;Apache Software License;PSF-2.0;Python Software Foundation License;MPL-2.0;Mozilla Public License 2.0 (MPL 2.0);GNU Library or Lesser General Public License (LGPL);Apache-2.0 OR BSD-3-Clause
licenses:
	$(start)
	mkdir -p .reports
	uv export -q --frozen --no-dev --no-emit-project --format requirements-txt -o .reports/licenses-requirements.txt
	uv run pip-licenses --from=mixed --allow-only="$(ALLOWED_LICENSES)" \
	  --packages $$(sed -n 's/^\([A-Za-z0-9_.-]*\)==.*/\1/p' .reports/licenses-requirements.txt) > /dev/null
	rm -f .reports/licenses-requirements.txt
	$(green)

# Short tracebacks, no banner; coverage (branch, `fail_under` in pyproject.toml) with the lines
# that miss, for files that miss any.
test:
	$(start)
	mkdir -p .reports
	# The tests set their own umask (tests/conftest.py); uv syncs .venv under the caller's.
	uv run pytest -q --no-header --tb=short -p no:cacheprovider -n auto --dist load 	  --junit-xml=.reports/junit.xml --cov --cov-report=term-missing:skip-covered
	$(green)

# Similar code (pylint's duplicate-code) and dead code (vulture) in src/factory, against the
# accepted findings in security/duplicates-baseline.txt; a record, never a check.
duplicates:
	mkdir -p .reports
	uv run pylint --disable=all --enable=duplicate-code --output-format=json --exit-zero src/factory > .reports/similar-code.json
	uv run vulture src/factory --min-confidence 60 --ignore-decorators "@field_validator,@model_validator" --ignore-names model_config > .reports/dead-code.txt || [ $$? -eq 3 ]
	uv run python -m factory.entry.check_duplicates --baseline security/duplicates-baseline.txt .reports/similar-code.json .reports/dead-code.txt

# The four documents against the document check: a check of the docs stage, not of `check`.
documents:
	uv run python -m factory.entry.check_documents

# Mutation testing (mutmut), for a sweep by hand: no stage and no agent runs it (the human,
# 2026-10-19). MODULES names dotted modules or packages, each run by its pattern <name>.*, as in
# make mutants MODULES='factory.domain.disk factory.application'. FEATURE=<feature id> takes instead
# the modules under src/factory that the feature's story commits on origin/main changed, which needs
# a checkout with its history; MODULES given by hand wins. MUTANTS_SECONDS stops mutmut after that
# many seconds (no stop when it is empty); MUTANTS_CHILDREN caps its workers (mutmut's default is
# every core the machine reports, also inside a container limited to fewer).
FEATURE ?=
MUTANTS_SECONDS ?=
MUTANTS_CHILDREN ?=
FEATURE_MODULES = $(wildcard $(shell git log --format= --name-only -E --grep='^(ticket|work item) $(FEATURE)-S[0-9]{4}:' origin/main -- 'src/factory/*.py' 2>/dev/null | sort -u))
MODULES ?= $(if $(FEATURE),$(foreach module,$(FEATURE_MODULES),$(subst /,.,$(patsubst src/%.py,%,$(module)))))
mutants:
	if [ -z "$(FEATURE)$(MODULES)" ]; then echo "mutants: set MODULES or FEATURE, as in make mutants MODULES=factory.domain.disk or make mutants FEATURE=F0012"; exit 2; fi
	if [ -z "$(strip $(MODULES))" ]; then echo "mutants: no module under src/factory changed by $(FEATURE)"; exit 0; fi
	# mutmut stops a mutant's pytest at its time limit, which leaves that run's folder locked for
	# three days under pytest's root in /tmp: give each run a root of its own and remove it after.
	temporary=$$(mktemp -d)
	trap 'chmod -R u+rwX "$$temporary" 2>/dev/null || true; rm -rf "$$temporary" || true' EXIT
	umask 022   # the seal refuses a group-writable checkout
	# Nothing is kept between runs (the human, 2026-10-19): mutmut makes mutants/ anew, copies the
	# other files under src/ (the contract's schemas) afresh and runs its stats again.
	rm -rf mutants
	set -f   # the names below are mutmut's patterns, never file names
	stopped=""
	# mutmut mutates only functions without a decorator: a module of interfaces, models or constants has
	# no mutant, and mutmut stops when no name matches one. That is a run with nothing to check.
	TMPDIR="$$temporary" $(if $(MUTANTS_SECONDS),timeout $(MUTANTS_SECONDS)) uv run mutmut run $(if $(MUTANTS_CHILDREN),--max-children $(MUTANTS_CHILDREN)) $(foreach module,$(MODULES),$(module).*) 2>&1 | tee "$$temporary/run.txt" || { status=$$?; [ $$status -eq 124 ] || grep -qF 'Filtered for specific mutants, but nothing matches' "$$temporary/run.txt" || exit $$status; [ $$status -ne 124 ] || stopped=yes; }
	# mutmut generates mutants for every module; those outside MODULES stay "not checked".
	uv run mutmut results | { grep -v ': not checked$$' || true; }
	if [ -n "$$stopped" ]; then echo "mutants: stopped after $(MUTANTS_SECONDS) s, so the mutants it did not reach are not checked"; exit 1; fi
