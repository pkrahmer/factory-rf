# The agents area

The agent runs: the two runtimes, prompts, write paths, tool uses, provider limits and tokens. [The guide page](../../../docs/project-guide/agents.md) explains it.

- `adapters/` The claude and opencode runtimes, the agent-files reader, the shared launch and the fake runtime.
- `application/` The agent-runtime interface, the project's agent files, write paths, provider limits and tokens.
- `domain/` The data of a run, its prompt, write paths, tool uses, provider limits and tokens.
