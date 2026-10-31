# Request (2026-10-31): what can this opencode do?

For the opencode session at work. Read `DESIGN.md` in this folder first: it plans a skill that lets you run the factory with the human the way Claude Code did tonight. Before it is designed further, the thin layer for opencode needs facts about the opencode you are. Find them out by reading your own documentation, your configuration and by small harmless tries. Answer in this file, under *Response*, and push. Change nothing else.

## Questions

1. **Version.** `opencode --version`; and whether this is upstream opencode or the company's fork, and its line.
2. **Skills.** Does this opencode load skills (`SKILL.md` files with a front matter, as Claude Code's), and from where (`.opencode/skill/`, `.claude/skills/`, `~/.config/opencode/...`)? Is there a tool that loads one on demand? If yes, try a tiny one in a temporary folder outside any repository and say what happened.
3. **Agents and commands.** Custom agents (`.opencode/agent/*.md`?) and custom commands (`.opencode/command/*.md`?): where they live, project-level and user-level, their front-matter keys, and whether a command can take arguments (for example `/operator merge off`).
4. **The shell tool's limits.** The longest a single shell command may run (its default timeout and its maximum, if there is one) and what happens when it is exceeded. Try a `sleep 300` and, if it passes, a `sleep 600`; say how long each took and what came back.
5. **A turn that waits.** Inside one turn, call a shell command that sleeps two minutes and prints `continue`, three times in a row. Does the turn stay open, can the human interrupt it, and what did the three calls cost (if opencode shows it)?
6. **Context and compaction.** How large is the model's context window here, and does opencode compact a long session by itself? At what point?
7. **Toggles.** Which settings of opencode itself does the human already switch (the config file's keys), and can a command change a value in a file the agent then reads? A plain JSON or TOML file in `~/.config/factory-operator/` would do; say whether anything speaks against that.
8. **GitHub and the cloud from here.** Is `gh` installed and logged in for the company's GitHub? Is `gcloud` logged in with an identity that may read Cloud Logging of the factory's job and run `gcloud run jobs execute`? Which of these needs the proxy?

## Rules

No company value in this repository: no host, project id, account, token, proxy address or model name; write `<placeholders>`. No secret printed or committed. Only this file changes; commit it with the message `planning: operator skill: what this opencode can do`, stage only it, push to `main`.

## Response

(empty)
