# The factory can be configured for a corporate environment

## Goal

The factory is built for public use: github.com, the Anthropic API, the public package indexes. An operator who runs an instance inside a company network meets three things that the code gives no way to set: opencode can only reach a model through a provider it already knows (the per-run configuration holds no `provider` section), the containers drop every environment name outside a fixed list (so a proxy, a package mirror or a company CA cannot reach them), and the operator's own settings have no file that `vm/setup.sh` leaves alone (it rewrites `factory.env` at every run, so a model map for the company's proxy would be lost). This feature adds three options, each off by default and each read from the operator's machine: a provider file for opencode (an OpenAI-compatible endpoint, its models and prices, and its own small model), a list of environment names and a CA bundle for the containers, and an environment file beside `factory.env` that the script never writes. With none of them set the factory behaves exactly as before: the per-run file, the container command lines and the unit are unchanged. No company value (an address, a model id, a token) is written into this repository. Done when every story below is merged and `make check` is green.

## Scope

- `FACTORY_OPENCODE_PROVIDER_FILE`: a JSON file on the VM that the opencode runtime merges into every run's configuration (S0001).
- `FACTORY_CONTAINER_ENV` and `FACTORY_CA_BUNDLE`: names passed from the factory's environment into every container, and a read-only CA bundle (S0002).
- `/srv/factory/<instance>/factory.local.env`: an optional second environment file of the unit, never written by `vm/setup.sh` (S0003).
- The operator guide's passages on opencode's login, which describe v1.1's agent home (S0001's docs criterion).

## Out of scope

- A `base_url` for the hosting client: the work's GitHub Enterprise is on github.com, whose API is the client's default (the human, 2026-10-26).
- The factory's code from a repository other than the one it works on: a later feature (`planning/v1.2-candidates.md`). Until then an instance at work runs on an imported copy of this repository, not a fork.
- Reading a secret store from the factory: the operator places the secrets by hand (the machine chapter, step 8).
- Any change to the Claude Code runtime, the pipeline definition or the records contract.
- A proxy or an allow-list of the agent's network.
- Any company value in this repository, in a test or in a document: tests and documents use `example.invalid` and made-up model ids.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: The opencode runtime merges a provider file into every run's configuration
- S0002: The containers pass the environment names the operator lists and trust the operator's CA bundle
- S0003: The unit reads an environment file that the setup script never writes
- S0004: The opencode probe no longer advises a login kept in the agent's home (from A0001)
- S0005: The feature's documents agree with what was built and with each other (from A0001)

## The human's changes

None. Checked against `factory/pipeline.yml`: the coder writes `src/*`, `template/*`, `claude/*` and `vm/*` (S0003's two files are under `vm/`), the tester `tests/*`, the documenter `README.md` and `docs/*`. `pyproject.toml`, `Makefile` and `.secrets.baseline` are not touched, and no dependency is added.

## Decisions taken for the human

1. Every option is off by default, and a story's first criterion is the unchanged default (S0001, S0002, S0003).
2. The provider file is a file on the VM and its path is a setting, so no company value reaches the repository. Its content is validated into a Pydantic model; an unknown key is refused (S0001).
3. The proxy's key is read through opencode's `{env:NAME}` form from the variable the operator names. With `ANTHROPIC_API_KEY` the factory's login shell already exports it from `FACTORY_API_LOGIN_FILE`, so the key stays in the one file the operator already places (S0001).
4. The provider file must name a `small_model`, and the run's configuration sets opencode's `small_model` to it, because opencode otherwise uses a small model hosted by its own service for tasks such as titles (S0001).
5. A model's price is optional in the file. Without it opencode reports a cost of 0 for a custom model and the budget stop never fires; the operator guide says so (S0001).
6. The containers' allow-list stays closed. `FACTORY_CONTAINER_ENV` names the extra names, and a name that the factory's environment does not hold is skipped, not an error (S0002).
7. A CA bundle is mounted read-only into the agent, sync and check containers and named by `NODE_EXTRA_CA_CERTS`, `SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE` (S0002).
8. The second environment file is read after `factory.env`, so a value in it wins, and it is optional (a leading `-` in the unit) (S0003).
9. The real opencode is never run by a test. Whether opencode 1.19.3 accepts the provider block is shown by the preflight's `agent-run-probe` on the machine, not by the suite (S0001).
10. S0004's leave (the human, 2026-10-26): the shared helper `opencode_sso_hint` in `tests/probe_support.py` changes its text to the new hint, and with it what `tests/application/test_agent_run_probe_opencode.py` and `tests/application/test_agent_run_probe_factory_user.py` check; those earlier tests may change only that way.
11. **A0002's proposed story, done on `main` by the human to spare extra rounds for small items (as F0044's decision 43).** F0046-A0002 accepted the feature and proposed F0046-S0006 (the project guide and the decision log agree with the feature's constructors and its login rule), documents only. Its docs criterion is done on `main` instead: the two runtime signatures in `docs/project-guide/agents.md` and the wiring table's `ContainerMakeCommands` with the sentence below it in `docs/project-guide/stage-environment.md` (checked against the constructors in `src/`); the superseded bullet of *The agent runtime is chosen per instance* in `docs/decisions.md` (`FACTORY_OPENCODE_FOLDERS` is read nowhere under `src/`); the probe's `none` texts and the empty detail, and the comma, in `docs/operator-guide.md`. `make documents` prints `documents ok`. The story is removed from the backlog unbuilt.
