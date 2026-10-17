---
stage: review
pr: 172
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# One compose project per instance

## Assignment (as of log entry 1)

`image/compose.yml` names its project `factory`, with the service `factory` and the volumes `work`, `state` and `claude-home`. v1's compose file, in the folder `factory`, has the same project name, service and volume names. So `docker compose -f image/compose.yml up` would replace v1's running container and mount v1's volumes `factory_work` and `factory_claude-home` (v1's checkout and v1's own `claude` login) into v1.1, and a second instance of v1.1 on the same machine would take the first one's. The human's word (item 1.6) is a project name per instance: `name: factory-${FACTORY_INSTANCE:?...}`, so that each instance gets its own container and volumes (`factory-<instance>_work` and so on). Compose refuses to start when `FACTORY_INSTANCE` is unset, as the service's environment already does. The file is under `image/`, in the coder's write paths.

## Interface

`image/compose.yml`: the first key is `name: factory-${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}`, in place of `name: factory`. Nothing else in the file changes: the service `factory`, its environment, volumes, health check and secret stay.

Tests: new test functions in a new module `tests/test_compose_project.py`, reading the file with ruamel.yaml's safe loader as `tests/test_compose.py` does. No existing test changes.

## Acceptance criteria

1. The compose file's `name` is exactly `factory-${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}`: it starts with `factory-`, refers to `FACTORY_INSTANCE` with `:?` and a message, and has no default (`:-`).
2. The `:?` message of `name` is the same text as the `:?` message of `FACTORY_INSTANCE` in the service's environment.
3. The tests of `tests/test_compose.py` and `tests/test_image_users.py` still pass: the service, its environment, volumes and secret are as before.
4. `make check` stays green.
5. docs: the operator guide's section *The container: compose, entrypoint and health check* says that the project is named `factory-<instance>`, that the volumes are therefore `factory-<instance>_work`, `factory-<instance>_state` and `factory-<instance>_claude-home`, that two instances on one machine (and v1 beside v1.1) get their own container and volumes, and that renaming an instance means new, empty volumes; the decision log records the per-instance name and the collision with v1 it prevents. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run python -c "
from pathlib import Path
from ruamel.yaml import YAML
loaded = YAML(typ='safe').load(Path('image/compose.yml').read_text(encoding='utf-8'))
print(loaded['name'])
print(sorted(loaded['volumes']))
"
```
Expect: two lines: `factory-${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}` and `['claude-home', 'state', 'work']`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: one concrete change, `name:` in `image/compose.yml` (line 2, now `factory`), to `factory-${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}`. The service's environment at line 19 has exactly that `:?` message, so criterion 2 can be tested. The test module `tests/test_compose_project.py` is named, and the loader is the one `tests/test_compose.py` uses.
   - Criteria: each one is testable by a single test function. 1 covers the exact string, the `factory-` prefix, the `:?` with a message and no `:-`, so the refused default is covered. 2 compares the two messages. 3 is the existing tests staying green. 4 is `make check`. 5 is the docs criterion, whose section exists at `docs/operator-guide.md` line 175. The rule that compose refuses to start when `FACTORY_INSTANCE` is unset is the `:?` form, and criterion 1 tests it.
   - Demo: runnable with `uv run python -c`. Its Expect line gives two exact lines that the output can be compared with.
   - Architecture: only a file under `image/` changes, which is inside the coder's write paths. No layer is involved.
   - Scope: in the feature's scope, item 1.6 (S0022), with the tests and the docs inside the story. Nothing is in "Out of scope".
3. tester: Wrote the tests for the per-instance compose project name in the new module `tests/test_compose_project.py`. It loads `image/compose.yml` with ruamel.yaml's safe loader, the same way `tests/test_compose.py` does. No existing test was changed.
   - criterion 1: tests/test_compose_project.py::test_the_project_is_named_after_the_required_instance_without_a_default. It checks that `name` is exactly `factory-${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}`, that it starts with `factory-`, that it uses `:?` with a message and has no `:-` default, and that `name` is the file's first key, as the Interface says.
   - criterion 2: tests/test_compose_project.py::test_the_project_name_refuses_with_the_same_message_as_the_service_environment. It checks that the `:?` message in `name` is the same text as the one for `FACTORY_INSTANCE` in the service's environment.
   - criterion 3: no new test. The criterion is that the existing tests in tests/test_compose.py and tests/test_image_users.py keep passing, and they do on this run.
   - criteria 4 and 5: `make check` and the docs, which the later stages handle.
   Files created: tests/test_compose_project.py.
   `make test`: both new tests fail as intended, because `name` is still `factory`. Every module imported; the tests read a file, so nothing was missing. `make lint` is green.
   I did not have to interpret any criterion.

   `make lint`: lint: green (0.0 s)
   `make test`: FAILED tests/test_compose_project.py::test_the_project_name_refuses_with_the_same_message_as_the_service_environment
4. coder: In `image/compose.yml`, `name: factory` is now `name: factory-${FACTORY_INSTANCE:?set FACTORY_INSTANCE to this instance's name}`. Nothing else in the file changed. This is commit da2bcaa.
      - Design: I reused the `:?` message of the service's `FACTORY_INSTANCE` word for word, so compose refuses an unset instance with the same text in both places. I did not add a comment in the file: the header comment stays the only one, and the reason for the change goes into the decision log at the docs stage.
      - Rejected: a default such as `:-default`. It would let two unnamed instances, or v1.1 beside v1, share a project again.
      - Refactor: nothing to change in a one-line diff.
      - `make check` is green. Both tests in `tests/test_compose_project.py` pass, and so do `tests/test_compose.py` and `tests/test_image_users.py`.
      - Open: criterion 5 (the operator guide's container section and the decision log) is left to the docs stage.

   `make check`: check: green
   `make duplicates`: duplicates: 0 new, 39 known, 0 gone
