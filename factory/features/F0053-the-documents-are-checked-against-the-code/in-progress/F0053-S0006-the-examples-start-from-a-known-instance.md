---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-06T08:49:17.620701Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T08:49:17.613833Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T08:49:17.620701Z'
  stage: intake
---

# The examples start from a known instance

## Description

Many commands of the operator guide need more than a repository: `factory-health` reads a state folder, and a refusal needs a wrong setting. A copy of the repository cannot give that state, because it is not in the repository. This story adds a second fixture that a runnable example names, `console fixture=instance`: a valid instance, built fresh for each document from the factory's own git wrapper and settings, so that the documents' examples and the tests share one definition of "a known instance". It holds a settings file, a state folder with a healthy health file, and a local bare remote of the checkout. The fixture lives in `src/` (the check runs from there and may not import `tests/`), and a test keeps it working. Commands that need the hosting service, such as `factory-watch` with a story in progress, are not given a fixture: they are marked `console github` and only listed (the human, 2026-11-05: no switch to a fake hosting service in the production code).

## Interface

- `factory.shared.adapters.document_fixtures` (new): the fixture `instance`, a `Fixture` (S0003) built from the factory's own git wrapper, with the fixed instance name `docs`.
- `instance` gives the environment of a valid instance (`FACTORY_INSTANCE=docs`, the folders under the fixture's folder, `FACTORY_SNAPSHOTS=copy`), so that `factory-health` prints `healthy` and a changed variable gives its real refusal.
- No change to the factory's wiring or settings: the fixture uses only what an operator could set.
- The runner of S0003 finds the fixture by name; an unknown name stays the finding of S0003.
- Tests: `tests/shared/adapters/test_document_fixtures.py` (the fixture builds, and its first command gives the expected output).

## Acceptance criteria

1. With `fixture=instance`, `factory-health --state-directory "$FACTORY_STATE"` prints `healthy`, and with `FACTORY_INSTANCE=Factory-1` set in the block, `factory-run` prints `settings invalid: FACTORY_INSTANCE: is not a name` and exits 2.
2. Each document gets a fresh fixture: a change one document's example makes is gone for the next document.
3. The fixture's folder holds no file outside the temporary folder the runner gave it, and the instance's remote is a local bare repository, not a network address.
4. `make check` stays green.
5. docs: `docs/project-guide/style.md` (or `shared.md`): the two fixtures, `checkout` and `instance`, what each holds, and the instance's fixed name; that a command needing the hosting service is marked `console github`. `docs/decisions.md`: an entry for having no fake hosting service in the production wiring, with its reason (no switch for tests in the production code) and what was rejected (a `world` fixture behind `FACTORY_HOSTING=fake`).

## Smoke test

```bash
uv run pytest tests/shared/adapters/test_document_fixtures.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
