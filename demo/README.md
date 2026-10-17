# Demos

Each folder is one demo: a project of one kind that v1.1 builds from an empty repository, with the stories a session starts while it plays the human. `python -m factory.entry.check_demos` checks every folder, and `make check` runs that check.

Every demo holds:

- `README.md`: what it builds, what it needs, the prompt for the session that plays the human, what a run looks like and costs;
- `project/`: the empty project the factory builds into, with its `CLAUDE.md`, `Makefile`, `pyproject.toml` and lock file, `factory/pipeline.yml` and `factory/story-form.md`;
- `features/`: the features and their stories in v1.1's work item form, `features/<F0001-slug>/feature.md` and `features/<F0001-slug>/backlog/<F0001-S0001-slug>.md`.

| Demo | Kind | Stack | What it builds | Stories | Baseline of |
|---|---|---|---|---|---|
