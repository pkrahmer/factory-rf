---
stage: doing
blocked: question
round: 0
attempts: 0
crashes: 0
pull_request: 588
comments_read: [6681011738]
handed_over: null
claim: null
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
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-06T08:53:57.519164Z'
  stage: intake
  run: 53aef9b2d4e04e3285f9fb55b5df582d
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T08:54:02.639358Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-06T08:56:08.706243Z'
  stage: tests
  run: 0d326b3ade3148fda5ca1e5b361ae56f
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T08:56:14.014925Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-06T09:01:35.986893Z'
  stage: doing
  run: be07fe7e7de14ce2adfdf639b434a612
  blocked: question
---

# The examples start from a known instance

## Description

Many commands of the operator guide need more than a repository: `factory-health` reads a state folder, and a refusal needs a wrong setting. A copy of the repository cannot give that state, because it is not in the repository. This story adds a second fixture that a runnable example names, `console fixture=instance`: a valid instance, built fresh for each document from the factory's own git wrapper and settings, so that the documents' examples and the tests share one definition of "a known instance". It holds a settings file, a state folder with a healthy health file, and a local bare remote of the checkout. The fixture lives in `src/` (the check runs from there and may not import `tests/`), and a test keeps it working. Commands that need the hosting service, such as `factory-watch` with a story in progress, are not given a fixture: they are marked `console github` and only listed (the human, 2026-11-05: no switch to a fake hosting service in the production code).

## Interface

- `factory.hosting.adapters.instance_fixture` (new): `class InstanceFixture(Fixture)` beside `CheckoutFixture`, constructed as `InstanceFixture(git: GitCli)`, with `prepare(folder: Path) -> dict[str, str]`: it builds the instance in `folder` (a settings file, a state folder with the health file `factory-health` reads, a local bare remote of the checkout, built with the factory's own git wrapper) and returns its environment.
- The environment holds `FACTORY_INSTANCE=docs` and `FACTORY_SNAPSHOTS=copy`, and every folder variable it sets lies under `folder`, so that `factory-health` prints `healthy` and a changed variable gives its real refusal.
- `factory.entry.check_documents` adds it to the name-to-fixture table under `instance` (`{"checkout": ..., "instance": InstanceFixture(...)}`); this is the one place the story wires. No change to the factory's own run and watch commands or settings: the fixture uses only what an operator could set.
- The runner of S0003 finds the fixture by name; an unknown name stays the finding of S0003.
- Tests: `tests/hosting/adapters/test_instance_fixture.py`.

## Acceptance criteria

1. With `fixture=instance`, `factory-health --state-directory "$FACTORY_STATE"` prints `healthy`.
2. With `FACTORY_INSTANCE=Factory-1` set in the block, `factory-run` prints `settings invalid: FACTORY_INSTANCE: is not a name` and exits 2.
3. The environment `prepare` returns holds `FACTORY_INSTANCE=docs` and `FACTORY_SNAPSHOTS=copy`, and every folder variable it sets lies under the folder given.
4. The state folder holds the health file that `factory-health` reads.
5. Each document gets a fresh fixture: two `prepare` calls for two documents give two different folders, and a file written into the first is absent from the second.
6. Every path the fixture creates lies under its folder.
7. The instance's remote URL is a path under the folder, and `git rev-parse --is-bare-repository` in it prints `true`.
8. `make check` stays green.
9. docs: `docs/project-guide/style.md` (or `shared.md`): the two fixtures, `checkout` and `instance`, what each holds, and the instance's fixed name; that a command needing the hosting service is marked `console github`. `docs/decisions.md`: an entry for having no fake hosting service in the production wiring, with its reason (no switch for tests in the production code) and what was rejected (a `world` fixture behind `FACTORY_HOSTING=fake`).

## Smoke test

```bash
uv run pytest tests/hosting/adapters/test_instance_fixture.py 2>&1 | tail -1 | grep -c passed
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
6. intake: accepted, with the human's answer (journal 4) carried into the story.
   - Interface: I rewrote it from journal 4. It now names `factory.hosting.adapters.instance_fixture.InstanceFixture(Fixture)`, constructed as `InstanceFixture(git: GitCli)`, with `prepare(folder: Path) -> dict[str, str]`. The environment it returns holds `FACTORY_INSTANCE=docs` and `FACTORY_SNAPSHOTS=copy`. The wiring is one entry in the table in `factory.entry.check_documents`, and the test module is `tests/hosting/adapters/test_instance_fixture.py`. The `document_fixtures` line is gone.
   - Criteria: I rewrote them as answers 2 to 5 of journal 4 ask. Criterion 1 is now two (1 the healthy output, 2 the refusal and exit 2). New criteria cover the environment (3), the health file (4) and freshness (5). The paths under the folder and the local bare remote are now two criteria (6 and 7). `make check` and `docs:` stay last. Each criterion is testable by one test function. Each rule has a failing side: the `Factory-1` refusal, and the file written in the first folder being absent from the second.
   - Smoke test: the command now names the new test path. It is runnable, and it is correct under the project's `-q` addopts, which gives a summary line. `Expect: 1` is checkable.
   - Architecture: the fixture sits in `hosting.adapters` beside `CheckoutFixture` because it needs git. It changes no setting and no run or watch wiring. That fits the layering.
   - Scope: it is within F0053 (S0006, runnable examples) and touches nothing under "Out of scope". The route is `tests`, since the Interface changes `src` code.
7. factory: started tests as vm.
8. tester: I wrote the tests for the instance fixture from the Interface and criteria 1 to 7, in one new module.

   Criterion → test (all in `tests/hosting/adapters/test_instance_fixture.py`):
   - criterion 1: `test_the_commands_of_a_block_on_the_instance_print_what_a_valid_instance_prints[healthy]`. It runs a `console fixture=instance` block through `ProcessExampleRunner` with `{"instance": InstanceFixture(checkout)}`. `factory-health --state-directory "$FACTORY_STATE"` must print `healthy`, which means no findings.
   - criterion 2: the same test, row `[a-wrong-instance-name-is-refused]`. `FACTORY_INSTANCE=Factory-1 factory-run; echo "exit $?"` must print `<time> settings invalid: FACTORY_INSTANCE: is not a name` and then `exit 2`. The two criteria share their setup, so they are rows of one test, as journal 4 says. `<time>` is there because `factory-run` stamps the line with the time; I checked by hand that it prints `2026-…Z settings invalid: …` and exits 2.
   - criterion 3: `test_the_environment_names_the_instance_docs_with_copied_snapshots_and_folders_inside`. Every value in the environment that is an absolute path counts as a folder variable, and it must lie under the folder given.
   - criterion 4: `test_the_state_folder_holds_the_health_file_factory_health_reads`, using `factory.entry.wiring.health_file($FACTORY_STATE)`.
   - criterion 5: `test_each_document_gets_a_fresh_instance_in_a_folder_of_its_own`. Two documents run through the runner. A recording `Fixture` wraps the real `InstanceFixture` (no mocking) and checks the two `prepare` folders differ. A marker written to `$FACTORY_STATE` in the first document must be absent in the second.
   - criterion 6: `test_the_fixture_creates_no_path_outside_its_folder`. It lists the paths under `tmp_path` before and after `prepare`; every new path must lie under the folder.
   - criterion 7: `test_the_instance_s_remote_is_a_bare_repository_under_the_folder`. `FACTORY_REPOSITORY_URL` must be a path under the folder, and `git rev-parse --is-bare-repository` in it (via `support.git_support.run_git`) must print `true`.
   - criteria 8 and 9 (`make check`, docs) have no test.

   Readings the coder should know:
   - I took "the instance's remote URL" to be `FACTORY_REPOSITORY_URL`. It is the only setting that names the remote.
   - Criterion 1 uses `$FACTORY_STATE`, so the environment must set `FACTORY_STATE`.
   - For criterion 2 to print only the instance refusal, the other settings in the environment must be valid: with an empty environment, `factory-run` refuses `FACTORY_REPOSITORY_URL: missing` first.
   - The commands run as installed scripts on the `PATH` the runner passes on (`.venv/bin` under `uv run`).

   Files created: `tests/hosting/adapters/test_instance_fixture.py`.

   The one run (`uv run pytest -q tests/hosting/adapters/test_instance_fixture.py`) failed at collection: `ModuleNotFoundError: No module named 'factory.hosting.adapters.instance_fixture'`. That module is the one the test runner could not import. `make lint`: green. I skipped the type check, as this stage says.

   `lint`: lint: green (0.1 s)
9. factory: started doing as vm.
10. coder: I stopped with `make check` red. The cause is a structural guard tripping on the new test module, and code cannot fix it.

    What I built (in the working tree):
    - `src/factory/hosting/adapters/instance_fixture.py` (new): `InstanceFixture(git: GitCli)`. Its `prepare(folder)` makes a bare clone of the checkout at `<folder>/remote.git`. It writes a healthy health file (`JsonHealthStatusFile(...).write(HealthStatus())`) into `<folder>/state`. It also writes the image id file, makes the agent home, workspace and copy base, and writes the settings file `<folder>/factory.env`. It returns the environment: `FACTORY_INSTANCE=docs`, `FACTORY_SNAPSHOTS=copy`, and every path variable under the folder. A `GitError` becomes a `FixtureError`, as in `CheckoutFixture`.
    - `src/factory/hosting/adapters/git_cli.py`: `GitCli.clone_bare(destination)`. It is not an operation of `Git`, for the same reason `export` is not.
    - `src/factory/watching/adapters/health_file.py`: `HEALTH_FILE_NAME = "health.json"`. It moved down from `factory.entry.wiring`, which now imports it and keeps `health_file()`. Main choice: the fixture in `hosting.adapters` may not import `factory.entry`, so the name moved to the module of the health file. I rejected the alternative of copying `"health.json"` into the fixture, because it would be a second definition of the same name.
    - `src/factory/entry/check_documents.py`: the table is now `{"checkout": CheckoutFixture(git), "instance": InstanceFixture(git)}`.

    State: all 7 tests in `tests/hosting/adapters/test_instance_fixture.py` pass. lint, types, layers, sast, secrets and licenses are green. `make test` fails on exactly one test:
    ```
    FAILED tests/guards/test_areas.py::test_a_test_module_in_an_area_folder_imports_only_moved_areas_and_its_own[hosting/adapters/test_instance_fixture.py]
    E   AssertionError: test_instance_fixture.py imports areas not yet moved: ['factory.entry.wiring', 'factory.entry.wiring.health_file']
    tests/guards/test_areas.py:263
    ```
    The new test module imports `health_file` from `factory.entry.wiring`. The guard forbids a test under `tests/<area>/` from importing `factory.entry`. No code change can satisfy both, and I do not edit tests.

    Question: how should the test change? The options I see:
    1. (my choice) The tester changes criterion 4's test to import `HEALTH_FILE_NAME` from `factory.watching.adapters.health_file` (or `JsonHealthStatusFile`). It then checks that `Path(environment["FACTORY_STATE"]) / HEALTH_FILE_NAME` is a file. This is the same name `factory-health` reads, through `wiring.health_file`.
    2. The tester moves the criterion 4 test to `tests/entry/`, where importing `factory.entry.wiring` is allowed. That would split the fixture's tests over two folders.
    3. The guard gets an exception for this test. That changes a test another story wrote, and the guard's purpose argues against it.

    With option 1 I would end the next round with `tests`, naming that one import change.

    I noticed one thing and left it alone: `DEFAULT_FIXTURE` (`"checkout"`) lives in `shared.domain.documents`, while the name `"instance"` is a private constant in `check_documents.py`. It may be worth having one place for the fixture names later. No refactor needed beyond what is above.
