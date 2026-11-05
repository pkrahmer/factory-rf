# Glossary

The words the factory gives its own meaning, one entry each, sorted alphabetically. Other documents explain no word of this list again; they link here at the word's first use in a file.

- **acceptance**: the review of a whole feature after its last story is done. The acceptance reviewer writes a report and may propose further stories.
- **approval**: the last stage of a story, where the human reads the pull request. They merge it, or close it with a reason that sends the story back.
- **attempts cap**: how many stalls one stage may have before the factory asks the human. It is set in the pipeline definition.
- **backlog**: the folder of stories that wait for the human. A story leaves it only when the human starts it.
- **base**: the one snapshot of the dataset, moved forward at the start of every stage. The dataset is rolled back to it before each run.
- **claim**: the factory's mark that it works on a work item, written to the work item's front matter and pushed. Only the push that succeeds holds the claim.
- **cost record**: one line in the work item's cost file for one agent run. It holds the tokens and the cost of that run.
- **crash**: the factory process dies in the middle of a stage. The next tick finds the claim and runs the stage again.
- **dataset**: the ZFS dataset a stage runs on. It is mounted at `/work` in every container.
- **feature**: a goal that is split into a few stories. It has a folder with a `feature.md` that the human writes.
- **instance**: one running copy of the factory with its own name, state and settings. It is set by `FACTORY_INSTANCE`.
- **journal**: the numbered list of entries at the end of a work item. The factory, each stage's agent and the human all add entries, and nothing is edited afterwards.
- **lease**: the time for which a claim holds. When it runs out without a result, the claim counts as expired and another tick may take the work item over.
- **pipeline definition**: the file `factory/pipeline.yml`. It lists the stages, their roles, their checks, their caps and their write paths.
- **project command**: a command the factory runs on the project, such as `make check`. The pipeline definition names each one.
- **role**: the part an agent plays in a stage, such as tester, coder, reviewer or documenter. An agent file describes it.
- **round**: one trip of a work item back to an earlier stage, such as from review to doing. The work item counts its rounds.
- **round cap**: how many rounds a stage allows. When it is passed, the factory asks the human and does not loop again.
- **stage**: one step of the pipeline, such as tests, doing or review. One role works in it, and its decision names the next stage.
- **stage environment**: the interface behind which the container environment stands. A stage asks it for a dataset, a container and a take.
- **stall**: a stage that ends without a result the factory can keep. The run may have ended early, or its decision, form, checks or merge failed. The factory records it, and the stage runs again until the attempts cap.
- **stop**: the factory refusing to go on and saying why. A stop of one work item is posted on its pull request; a stop of the repository or the machine goes to the health status.
- **story**: one work item of a feature. It has a description, an interface, acceptance criteria and a journal.
- **take**: what the factory copies from the dataset into its own work tree after the agent's run. Only the changed paths that the role may write go back.
- **tick**: one pass of the factory over the repository. It looks at every work item and moves each at most one step.
- **work item**: a story, or a feature's acceptance report, as a file in a feature's folder. Its folder, `backlog/`, `in-progress/` or `done/`, tells where it stands.
- **write paths**: the paths in the pipeline definition that a role may change. The take drops every other change.
