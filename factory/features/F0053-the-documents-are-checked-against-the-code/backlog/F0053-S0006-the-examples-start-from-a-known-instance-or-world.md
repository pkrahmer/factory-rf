# The examples start from a known instance or world

## Description

Most commands of the operator guide need more than a repository: `factory-health` reads a state folder, `factory-watch` reads settings, a remote and pull requests, a refusal needs a wrong setting. A snapshot of the repository cannot give that state, because it is not in the repository. This story adds two fixtures that a runnable example names (`console fixture=instance`, `console fixture=world`), built fresh for each document from the same fakes the tests use, so that the documents' examples and the tests share one definition of "a known instance". `instance` is a settings file, a state folder with a healthy health file and a local bare remote of the checkout. `world` is an instance with the fake hosting service, a sample feature with one story in progress and its pull request. The fixtures live in `src/` (the check runs from there and may not import `tests/`), next to the fakes that already live there, and are built from them; a test keeps them working.

## Interface

- `factory.shared.adapters.document_fixtures` (new): the fixtures `instance` and `world`, each a `Fixture` (S0003) built from the factory's own git wrapper and `FakeHostingService` (`factory.hosting.adapters.fake_hosting`), with fixed names: the instance `docs`, the feature `F0001-a-sample-feature`, the story `F0001-S0001-a-sample-story`.
- `instance` gives the environment of a valid instance (`FACTORY_INSTANCE=docs`, the folders under the fixture's folder, `FACTORY_SNAPSHOTS=copy`), so that `factory-health` prints `healthy` and a changed variable gives its real refusal.
- `world` adds the fake hosting service in a form the commands can reach without a network: the factory's wiring takes a fake hosting service when `FACTORY_HOSTING=fake` and `FACTORY_FAKE_HOSTING_FILE` names its state file, both refused outside a test or a document example (`FACTORY_DOCUMENT_EXAMPLE=1`).
- The runner of S0003 finds the fixtures by name; an unknown name stays the finding of S0003.
- Tests: `tests/shared/adapters/test_document_fixtures.py` (each fixture builds, and its first command gives the expected output).

## Acceptance criteria

1. With `fixture=instance`, `factory-health --state-directory "$FACTORY_STATE"` prints `healthy`, and with `FACTORY_INSTANCE=Factory-1` set in the block, `factory-run` prints `settings invalid: FACTORY_INSTANCE: is not a name` and exits 2.
2. With `fixture=world`, `factory-watch` prints the sample feature's line and its story, and `factory-check-story` on the sample story prints its `ok` line.
3. `FACTORY_HOSTING=fake` is refused by the settings without `FACTORY_DOCUMENT_EXAMPLE=1` (`FACTORY_HOSTING: is only for tests and document examples`), and accepted with it.
4. Each document gets a fresh fixture: a change one document's example makes is gone for the next document.
5. `make check` stays green.
6. docs: `docs/project-guide/style.md` (or `shared.md`): the three fixtures, what each holds, and its fixed names. `docs/decisions.md`: an entry for the fake hosting service behind `FACTORY_DOCUMENT_EXAMPLE`, with its reason (examples without a network) and what was rejected (examples against the real GitHub).

## Smoke test

```bash
uv run pytest tests/shared/adapters/test_document_fixtures.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal
