# The factory package

The code of the factory: seven areas, each in three layers, plus the command line and the generated schemas. [The project guide](../../docs/project-guide/README.md), *The code's layout*, says which area holds what.

- `agents/` the agent runs, the two runtimes, prompts, write paths, tool uses, provider limits and tokens.
- `contract/` the JSON schemas of the records contract, generated from the models and never edited by hand.
- `entry/` the commands and the wiring of the concrete adapters.
- `hosting/` git, the hosting service, pushes, the hand-over and the opening of pull requests.
- `machine/` containers, images, snapshots, disks, the project's commands and the preflight.
- `pipeline/` the pipeline definition, the stages, the tick and its handlers, claims, stops and recovery.
- `shared/` what every other area uses: errors, times, identifiers, paths, settings and the document check.
- `watching/` what shows the factory and what it costs: the board, the watcher, cost records, bills and transcripts.
- `work/` work items, their journal, the story form, answers, the archive and the feature acceptance.
