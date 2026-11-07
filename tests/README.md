# The tests

The pytest suite of the factory: the folders mirror the package as `tests/<area>/<layer>/`, beside a few special folders. [CLAUDE.md](../CLAUDE.md), *Tests*, says how the tests are laid out and written.

- `agent_files/` the tests of the agent files under `agents/` and of the template under `operator/template/`.
- `agents/` the tests of the agents area, one folder per layer.
- `entry/` the tests of the commands and the wiring in `factory.entry`.
- `guards/` the structural guards: searches over the source and the tests, and the layout of the suite.
- `hosting/` the tests of the hosting area, one folder per layer.
- `machine/` the tests of the machine area, one folder per layer.
- `operator_scripts/` the tests of the operator's scripts under `operator/`.
- `pipeline/` the tests of the pipeline area, one folder per layer.
- `shared/` the tests of the shared area, one folder per layer.
- `support/` the helpers, constants and stand-ins that several test modules share.
- `vm/` the tests of the machine's files under `operator/vm/`.
- `watching/` the tests of the watching area, one folder per layer.
- `work/` the tests of the work area, one folder per layer.
