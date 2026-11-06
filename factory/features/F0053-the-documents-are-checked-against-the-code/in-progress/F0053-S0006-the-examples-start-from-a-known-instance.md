---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 588
comments_read: [6681011738]
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-11-06T08:53:34.042028Z'
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
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-06T08:49:39.000043Z'
  stage: intake
  run: 4f80d96912dd4c0185d82abf9e5851bf
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-06T08:53:31.534026Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-06T08:53:34.042028Z'
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
3. intake: Format check passed. Questions:
   1. Interface: it names no signature. `document_fixtures` gets "the fixture `instance`, a `Fixture` (S0003)", but not the object or function a coder writes (its name, parameters such as the folder the runner gives it, return type) or how it is registered so the S0003 runner "finds it by name". `src/factory/shared/adapters/document_examples.py` already exists; should the fixture register there or in the new module? I would choose: `def instance(folder: Path) -> Fixture`, plus the name-to-fixture table S0003 reads, named in the Interface.
   2. Interface behaviour without a criterion: `FACTORY_SNAPSHOTS=copy` and "the folders under the fixture's folder" (settings file, state folder with a healthy health file, bare remote of the checkout) are stated, but no criterion tests them. Criterion 1 only tests the output of two commands. I would add: a criterion that the environment holds `FACTORY_INSTANCE=docs` and `FACTORY_SNAPSHOTS=copy` with every folder variable under the fixture's folder, and one that the state folder holds the health file `factory-health` reads.
   3. Criterion 1 holds two behaviours (the healthy side and the refusal side) with two commands; one test function cannot reasonably cover both. I would split it into 1a (`healthy`) and 1b (refusal text and exit 2).
   4. Criterion 3 holds two claims (no file outside the runner's folder; the remote is a local bare repository, not a network address). I would split them, each with a testable check (for example: the remote URL is a path under the folder and `git rev-parse --is-bare-repository` prints `true`).
   5. Criterion 2 (fresh fixture per document) does not say how a test sees it: I would state that two builds for two documents give different folders and a file written into the first is absent from the second.
   Architecture and scope look right (`shared.adapters`, no wiring change, in S0006's place in the feature); the route would be `tests`.
4. 2026-11-06 human: 1. Follow the pattern S0003 set: `InstanceFixture(git: GitCli)`, a class implementing `Fixture`, whose `prepare(folder) -> dict[str, str]` builds the instance in `folder` and returns its environment. It needs git for the bare remote, so it lives beside `CheckoutFixture` in `factory.hosting.adapters.instance_fixture`, not in `factory.shared.adapters.document_fixtures` as the Interface says. `factory.entry.check_documents` adds it to the name-to-fixture table under `instance` (`fixtures = {"checkout": ..., "instance": InstanceFixture(...)}`). "No change to the factory's wiring" means the factory's own run and watch commands; the document check's table is the one place this story wires. The test module becomes `tests/hosting/adapters/test_instance_fixture.py`.
   2. Yes to both criteria: the environment holds `FACTORY_INSTANCE=docs` and `FACTORY_SNAPSHOTS=copy`, and every folder variable it sets lies under the fixture's folder; the state folder holds the health file that `factory-health` reads.
   3. Yes: 1a (`factory-health --state-directory "$FACTORY_STATE"` prints `healthy`) and 1b (`FACTORY_INSTANCE=Factory-1` makes `factory-run` print `settings invalid: FACTORY_INSTANCE: is not a name` and exit 2), one row each of one parametrized test if they share the setup.
   4. Yes: 3a, every path the fixture creates lies under its folder; 3b, the remote URL is a path under the folder and `git rev-parse --is-bare-repository` in it prints `true`.
   5. Yes: two `prepare` calls for two documents give two different folders, and a file written into the first is absent from the second.
5. factory: started intake as vm.
