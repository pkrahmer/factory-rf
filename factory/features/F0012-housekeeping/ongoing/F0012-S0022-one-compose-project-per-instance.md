---
stage: ready
pr: null
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
