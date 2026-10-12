# The contract between a repository and the factory is three targets: `check`, `lint`, `test`.
# `check` is the gate every stage must pass; `lint` and `test` are what the tests stage runs on
# its own (the type check is skipped there, because the modules under test do not exist yet).
# What each target runs is the repository's business; this file is a Python example. `types` and
# `layers` are in `check`, not in `lint`: the tests stage runs `lint` only.
.PHONY: check lint types layers sast secrets licenses test
.SILENT:

check: lint types layers sast secrets licenses test
	echo "check: green"

lint:
	uv run ruff check --output-format=concise .
	uv run ruff format --check --quiet .
	echo "lint: green"

types:
	uv run mypy
	echo "types: green"

# The exit status is import-linter's own: no pipe, so a broken contract fails the target.
layers:
	uv run lint-imports
	echo "layers: green"

# Static analysis: semgrep with rule sets vendored under security/semgrep (copy the sets you
# want from github.com/semgrep/semgrep-rules; offline and pinned), plus bandit.
sast:
	SEMGREP_SEND_METRICS=off uv run semgrep scan --config security/semgrep --metrics=off \
	  --disable-version-check --quiet --error src
	uv run bandit -q -c pyproject.toml -r src
	echo "sast: green"

# Secrets beyond the reviewed baseline (`uv run detect-secrets scan > .secrets.baseline` once).
secrets:
	uv run detect-secrets-hook --baseline .secrets.baseline $$(git ls-files | grep -vE '^(uv\.lock|\.secrets\.baseline|planning/.*|docs/runs/.*)$$')
	echo "secrets: green"  # pragma: allowlist secret (the word, not a key)

# Licences of the production dependencies against an allow list.
ALLOWED_LICENSES = MIT;MIT License;MIT-0;BSD;BSD License;BSD-2-Clause;BSD-3-Clause;3-Clause BSD License;ISC;ISC License;Apache-2.0;Apache 2.0;Apache Software License;PSF-2.0;Python Software Foundation License;MPL-2.0;Mozilla Public License 2.0 (MPL 2.0);GNU Library or Lesser General Public License (LGPL);Apache-2.0 OR BSD-3-Clause
licenses:
	uv export -q --frozen --no-dev --no-emit-project --format requirements-txt -o .licenses-requirements.txt
	uv run pip-licenses --from=mixed --allow-only="$(ALLOWED_LICENSES)" \
	  --packages $$(sed -n 's/^\([A-Za-z0-9_.-]*\)==.*/\1/p' .licenses-requirements.txt) > /dev/null
	rm -f .licenses-requirements.txt
	echo "licenses: green"

# Short tracebacks, no banner; coverage (branch, `fail_under` in pyproject.toml) with the lines
# that miss, for files that miss any.
test:
	uv run pytest -q --no-header --tb=short -p no:cacheprovider \
	  --cov --cov-report=term-missing:skip-covered
	echo "test: green"
