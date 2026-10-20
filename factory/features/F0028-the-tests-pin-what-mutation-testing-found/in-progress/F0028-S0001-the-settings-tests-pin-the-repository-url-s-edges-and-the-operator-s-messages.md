---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 312
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-20T01:15:06.523958Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T01:09:54.209799Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T01:09:54.214909Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-20T01:10:10.298044Z'
  stage: intake
  run: e6b1c5d5b85943d1991c3f4b66816da6
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-20T01:10:30.772873Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-20T01:12:37.875032Z'
  stage: tests
  run: d7339cc599c448bfb4fce20241f162e5
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-20T01:12:58.152346Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-20T01:14:45.682058Z'
  stage: doing
  run: e299c0010a8b468084d26b05bf8d70be
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-20T01:15:06.523958Z'
  stage: review
---

# The settings tests pin the repository URL's edges and the operator's messages

## Description

The mutation sweep of 2026-10-19 (`planning/overnight/mutation-sweep-2026-10-19.md`) left 19 mutants of `factory.domain.settings` alive. Two kinds are behaviour no test pins. First, the edges of the rule that refuses a repository URL holding a password: a `user:x@` in the URL's *path*, a second `://` in its path, and a user name that holds an `@` before the `:`. Every test of the rule today puts the password in the authority of a plain URL, so a change that judged the whole URL, or the last `://` instead of the first, or the first `@` instead of the last, would pass. Second, the messages an operator reads when a setting is refused: today the tests check only which variable is named (and "is shorter than the cool-down" as a substring), never the fault itself. This story pins both as criteria. The code already behaves this way, so the coder has nothing to change: only the tester's work, as in F0025-S0003. The other settings survivors stay as they are (the sweep's `split("/", 2)` variant of the authority split is equivalent: the first part is the same). The messages of internal guards (the sweep's optional story 5) are not part of this feature.

## Interface

No module under `src/factory/` changes. The behaviour pinned, all of `factory.domain.settings.read_settings(environ, read_file)` (`domain`):

- The password rule judges only the authority: the text after the *first* `://` up to the next `/`. Within it, the user information is everything before the *last* `@`, and the URL is refused when that holds a `:`. A `:` and `@` in the path count for nothing; a second `://` in the path counts for nothing; a user name with an `@` before the password's `:` is still refused.
- Each refusal of criterion 2 raises `SettingsInvalid` whose `variable` names the variable, whose `fault` is the exact text that criterion gives, and whose `str()` is `<variable>: <fault>`. The other refusals of `read_settings` keep the tests they have.

Tests (the tester writes them): `tests/domain/test_settings_url_edges.py`, which uses `BASE` of `tests/settings_support.py` as it is. A URL whose authority holds `<user>:<password>@` is built by concatenation, as `tests/domain/test_settings.py` does (`"https://user:" + "example-value" + "@github.com/..."`), so that `make secrets` finds no credential in the test. No constant's name holds `password`, `secret` or `token` (ruff's S105 and detect-secrets take such a string for a secret); the expected faults stand in the rows. No earlier test changes.

## Acceptance criteria

1. The password rule at the URL's edges (rows of one parametrized test, each `read_settings({**BASE, "FACTORY_REPOSITORY_URL": <url>})`):
   - Accepted, `repository_url` equal to the URL: `https://github.com/owner/a:b@c/project.git` (a `:` and an `@` in the path), `"https://github.com/owner/x://u:" + "p@y.git"` (a second `://` in the path), `https://u@x@github.com/owner/project.git` (an `@` in the user name, no password).
   - Refused, `SettingsInvalid` with `variable` `FACTORY_REPOSITORY_URL` and `fault` exactly `holds a password; use the token file`: `https://u@x:y@github.com/owner/project.git` (the user name `u@x`, the password `y`).
2. The operator's messages (rows of one parametrized test; each row the variables added to `BASE`, the `read_file` given or `None`, and the expected `variable` and `fault`; every row also checks that `str(error)` is `<variable>: <fault>`):
   - `FACTORY_REPOSITORY_URL` `a/b,c/d`, and `a b`: `FACTORY_REPOSITORY_URL`, `names more than one repository`.
   - `FACTORY_REPOSITORY_URL` `"https://user:" + "example-value" + "@github.com/owner/project.git"`: `FACTORY_REPOSITORY_URL`, `holds a password; use the token file`.
   - `FACTORY_INSTANCE` `Factory-1`: `FACTORY_INSTANCE`, `is not a name`. `FACTORY_AGENT_USER` `Agent`: `FACTORY_AGENT_USER`, `is not a name`.
   - `FACTORY_PROVIDER_LIMIT_COOLDOWN_MINUTES` `30` with `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES` `20`: `FACTORY_PROVIDER_LIMIT_CEILING_MINUTES`, `is shorter than the cool-down`.
   - No other variable, and a `read_file` that raises `PermissionError("denied")`: `FACTORY_IMAGE_ID_FILE`, `cannot read /opt/factory/image-id: denied`. A `read_file` that returns `"  \n"`: `FACTORY_IMAGE_ID_FILE`, `/opt/factory/image-id is empty`.
3. `make check` stays green.
4. docs: none. The operator guide already says that a repository URL with a password is refused and names the token file, and this story changes no behaviour and no message.

## Smoke test

```bash
uv run -q python - <<'EOF'
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings

base = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "factory-1"}
for url in (
    "https://github.com/owner/a:b@c/project.git",
    "https://github.com/owner/x://u:" + "p@y.git",
    "https://u@x:y@github.com/owner/project.git",
):
    try:
        print(read_settings({**base, "FACTORY_REPOSITORY_URL": url}).repository_url == url)
    except SettingsInvalid as error:
        print(error)
EOF
```

Expect: three lines, `True`, `True` and `FACTORY_REPOSITORY_URL: holds a password; use the token file`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names no change under src/factory/ and pins `factory.domain.settings.read_settings(environ, read_file)` (domain) in test file `tests/domain/test_settings_url_edges.py`. The password rule's clauses are concrete: authority after the first `://` up to the next `/`, user information before the last `@`, refused on a `:`. The error shape is `SettingsInvalid` with `variable`, `fault` and `str()` as `<variable>: <fault>`.
   Criteria: each is testable by one parametrized test function. Criterion 1 covers every clause of the rule on both sides. Accepted rows: `:` and `@` in the path, a second `://` in the path, and an `@` in the user name with no password. The refused row is `u@x:y@`. Criterion 2 gives the exact fault text for every message (multiple repositories, password, the two "not a name" cases, ceiling shorter than cool-down, unreadable image-id file, empty image-id file), and each row also checks `str()`. Criterion 3 is `make check`; criterion 4 is `docs: none`, which is justified because no message or behaviour changes.
   Smoke test: the command is runnable (inline Python via `uv run`). The Expect line gives three checkable lines (`True`, `True`, and the exact refusal text).
   Architecture: the story touches only `tests/domain/`, which mirrors the package layout. It reads `BASE` from `tests/settings_support.py`, and credential-like URLs are built by concatenation to keep `make secrets` quiet.
   Scope: it matches S0001 in feature.md's Scope, and nothing in Out of scope is touched (internal-guard messages and the equivalent `split("/", 2)` variant are excluded). The story changes no earlier test.
4. factory: started tests as self.
5. tester: Wrote the tests for the password rule's edges and the operator's messages, as the Interface specifies. Each criterion has one parametrized test:
   criterion 1: tests/domain/test_settings_url_edges.py::test_the_password_rule_judges_only_the_authority (rows: `:` and `@` in the path accepted, a second `://` in the path accepted, an `@` in the user name with no password accepted, `u@x:y@` refused with variable `FACTORY_REPOSITORY_URL` and the exact fault)
   criterion 2: tests/domain/test_settings_url_edges.py::test_a_refused_setting_names_its_variable_and_its_fault (8 rows: `a/b,c/d`, `a b`, the password URL, `FACTORY_INSTANCE` `Factory-1`, `FACTORY_AGENT_USER` `Agent`, ceiling 20 below cool-down 30, image-id file unreadable with `PermissionError("denied")`, image-id file `"  \n"`; each row checks `variable`, `fault` and `str(error)`)
   criterion 3: `make check`, the factory's gate; criterion 4: docs none, nothing to test.
   File created: tests/domain/test_settings_url_edges.py. It uses `BASE` from tests/settings_support.py unchanged. URLs holding a credential are built by concatenation. No earlier test was changed.
   Imports: the test run imported every module. As the story says, the code already behaves this way, so these tests pass now rather than failing: the single `make test` run finished `test: green`. The coder has nothing to implement.
   The first `make lint` failed for two reasons. Ruff's S105 flagged a fault constant whose name held `PASSWORD`, so the fault text now stands in the rows, as the Interface asks. Some lines were too long; I fixed them with `ruff format`. After that, `make lint` is green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: test: green (39.9 s)
6. factory: started doing as self.
7. coder: Built nothing: this story pins behaviour the code already has, and the Interface says no module under `src/factory/` changes. I ran `make check` on the committed state, which includes the tester's `tests/domain/test_settings_url_edges.py`. It passed (`test: green (41.2 s)`, `check: green`), and the new tests pass against the current `factory.domain.settings.read_settings`.
   Main choice: I left `src/factory` alone. The alternative I rejected was touching `factory.domain.settings`, for example tidying the authority split. That would go beyond the description and would change exactly the code these tests are meant to pin. With no diff, there was nothing to refactor.
   The journal did not change the meaning of the task, so `## Description` stays as it is.
   Noticed but did not touch: nothing.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
