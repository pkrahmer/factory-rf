# The pipeline definition and the story check

A topic of the [operator guide](README.md). It covers the file that configures your pipeline, `factory/pipeline.yml`, and the command that checks a [story](../project-guide/glossary.md) before the factory starts it.

## The pipeline definition

The [pipeline definition](../project-guide/glossary.md) is the project's configuration: its [stages](../project-guide/glossary.md), the [roles](../project-guide/glossary.md) that work in them, the [project commands](../project-guide/glossary.md) and the limits. The factory reads it only as it stands on `origin/main`, so a change takes effect when it is merged.

This is the smallest useful definition. It loads:

```yaml
contract: '1.0'
roles:
  tester:
    write_paths: ['tests/*', '{work_item}']
  coder:
    write_paths: ['src/*', '{work_item}']
stages:
  testing: {role: tester, next: [doing], checks: [lint]}
  doing: {role: coder, next: [review], checks: [check]}
  review: {approval: true, next: [done, doing], round_cap: 3}
  done: {}
```

The order of the stages in the file is the pipeline's order. The first `next` of a stage is the forward move. The others are moves back.

### Change the definition

1. Edit `factory/pipeline.yml` in a clone of the project.
2. Check it against the rules below, most of all the stage `done` and the [lease](../project-guide/glossary.md).
3. Merge the change to `main`. The factory reads the new text at its next [tick](../project-guide/glossary.md).

A refused definition [stops](../project-guide/glossary.md) the factory with `pipeline_definition_invalid` until you fix it on `main` (see "The stop `pipeline_definition_invalid`" in [stops.md](stops.md)).

### The rules you meet most often

- The stage `done` must exist, with no role and no `next`. Write it `done: {}`; `done:` alone is refused.
- The contract major must be 1. Any minor is read.
- Every stage other than `done` needs a non-empty `next` and either a role or `approval: true`. Every name in `next` must be a stage.
- The lease: for each stage with a role, the role's `time_limit` plus the `time_limit` of every command in the stage's `checks` and `reports` must be at most the role's `lease_duration`. With the defaults, 40 + 10 (one check) + 10 (one report) = 60 fits. A stage with two checks and a report adds up to 70 and is refused. Raise the `lease_duration` or lower a limit.
- Values are taken only in their YAML type. A limit is an integer (not `'30'`, `30.0` or `true`). `approval` is `true` or `false` (not `'yes'` or `1`). Names and [write paths](../project-guide/glossary.md) are text.
- A key that is not listed is refused, so a misspelt key is never ignored. That holds for `tool_paths` too. An agent run may write only its write paths, and there is no folder for tool state.
- A given `project_commands` replaces the default set as a whole. List `check`, `lint` and `test` again if you still want them.
- Every role needs an agent file, a project's own or the installed one (see "The agent files" in [agent-runtime.md](agent-runtime.md)).

[docs/project-guide/pipeline.md](../project-guide/pipeline.md), "The rules of the definition", lists every fault.

### More than one route

A definition may hold more than one route and more than one [approval](../project-guide/glossary.md) stage. When you close a pull request at an approval stage, the story goes to that stage's second `next`. The stage whose first `next` is that approval counts the [rounds](../project-guide/glossary.md).

The smoke test of the template reads `smoke-test: {role: smoke-tester, next: [approval, doing, docs], round_cap: 3}`. A finding that is only a slip in a document goes from the smoke test straight to `docs`. There the documenter fixes it and hands back to the smoke test. This counts as a round against the `round_cap`, as a return to `doing` does.

### The docs route

A story that changes only documents skips the tests, doing and review stages. Documents are `README.md`, the files under `docs/` and `operator/README.md`.

1. The intake chooses the route. It picks `docs-only` when every path the story's Interface changes is one the documenter may write, and `tests` otherwise.
2. The documenter writes the whole change and runs `make documents`.
3. `make check` runs after `docs-only`. The factory reuses an earlier passed result only when no document that a test reads has changed.
4. The reviewer reads the documents against the story's criteria, the code and [the style page](../project-guide/style.md).
5. The story goes to `docs-approval`, where you decide, or back to the documenter with numbered findings.

If the documenter finds that the story needs more than documents, it hands the story to the tests stage and says what is needed. The story then takes the normal route.

The route works only when your definition holds the stages `docs-only`, `docs-review` and `docs-approval`, and the `next` of the intake lists `docs-only`. Without them the agents do nothing on it.

### Reuse a result with `not_read`

A passed result of a project command is reused while the files it reads stay the same. `not_read` lists the paths the command does not read, so that a change only there is no reason to run it again. The paths it names are left out of the tree that the key holds (see "The known results" in [health.md](health.md)).

List only what the command does not read at all. A linter, formatter or type checker that walks the whole tree reads every source file in every folder, so leave out file types it does not read, never a whole folder. A forgotten path costs one run. A path listed by mistake can let a reused `check` pass a fault.

A pattern follows the form of `write_paths` patterns: relative to the checkout, `*` also crosses `/`, case-sensitive. For example:

```yaml
project_commands:
  check: {time_limit: 10, not_read: ["notes/*.md", "notes/*.jsonl"]}
```

A pattern that cannot name a path inside the checkout stops the definition from loading. Such a pattern is empty, starts with `/` or `~`, holds a `..` segment, or holds `{` or `}`:

```text
project command lint: not_read /etc/* must be a path pattern inside the checkout
```

kumpel-factory's own definition, `factory/pipeline.yml`, leaves out the Markdown and JSON Lines files that no test reads, and folders that hold no code and that no test reads. `make lint` reads every Python file of the tree, wherever it lies, so no folder with code is left out. `README.md` and `docs/` stay in the key, because the guide guards under `tests/guards/` and other tests of `make test` read the real documents. A documents-only change can therefore turn `make check` red. Of `docs/` only `docs/runs/*` is left out.

```yaml
project_commands:
  check: {time_limit: 8, not_read: ["docs/runs/*", "factory/features/*.md", "factory/features/*.jsonl", "factory/archive/*", "factory/stops.jsonl", "planning/*", "session-logs/*"]}
```

Two warnings:

- A project whose `check` scans changed files for secrets keeps a scan of the left-out files only if something else runs it. kumpel-factory's docs stage runs `secrets` as a check of its own, with nothing left out.
- A command whose result depends on anything outside the tree and the image is reused safely only when those versions are pinned in the tree, for example by a lockfile. Dependencies fetched at run time with unpinned versions are such a case. Otherwise leave `not_read` empty and do not rely on reuse for it.

### Reference

The keys of the definition:

| Name | What it does | Default | Example |
|---|---|---|---|
| `contract` | the contract version, quoted | required | `'1.0'` |
| `stages` | name to stage; the order in the file is the pipeline's order | required | `doing: {role: coder, next: [review]}` |
| `roles` | name to role; the name is also the agent file's name | required | `coder: {write_paths: ['src/*']}` |
| `project_commands` | name to `time_limit` in minutes and, optionally, `not_read` | `check`, `lint` and `test`, each 10 minutes and `not_read: []` | `check: {time_limit: 8}` |
| `attempts_cap` | [stalls](../project-guide/glossary.md) of one stage before the human is asked | 2 | `attempts_cap: 3` |
| `crash_cap` | [crashes](../project-guide/glossary.md) before the human is asked | 2 | `crash_cap: 3` |
| `acceptance_stage` | the stage of the feature [acceptance](../project-guide/glossary.md); it needs a role | none | `acceptance_stage: acceptance` |

The keys of a stage:

| Name | What it does | Default | Example |
|---|---|---|---|
| `role` | the role that works in the stage; without one no agent runs | none | `role: coder` |
| `next` | the stages a decision may name; the first is the forward move | empty (only `done` may have none) | `next: [review, tests]` |
| `approval` | the human decides in this stage; it has no role | `false` | `approval: true` |
| `checks` | project commands that must pass after the agent | empty | `checks: [check]` |
| `reports` | project commands run after green and only recorded | empty | `reports: [duplicates]` |
| `round_cap` | rounds the stage allows before the human is asked | none (no cap) | `round_cap: 3` |

The keys of a role:

| Name | What it does | Default | Example |
|---|---|---|---|
| `write_paths` | the paths the role may write; at least one, and each holds a character that is not whitespace | required | `['src/*', '{work_item}']` |
| `time_limit` | minutes one agent run may take | 40 | `time_limit: 30` |
| `lease_duration` | minutes a [claim](../project-guide/glossary.md) holds | 60 | `lease_duration: 90` |

The keys of a project command:

| Name | What it does | Default | Example |
|---|---|---|---|
| `time_limit` | minutes the command may run | 10 | `time_limit: 8` |
| `not_read` | the paths the command does not read (see "Reuse a result with `not_read`") | `[]`, nothing left out | `["docs/runs/*"]` |

Further rules:

- A write path may hold `{work_item}`, the [work item](../project-guide/glossary.md)'s own file, and `{feature}`, its [feature](../project-guide/glossary.md)'s path, such as `factory/features/<feature>`.
- The protected paths are outside every write path: `factory/pipeline.yml`, the story and feature forms, every `feature.md`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `.claude/` and the project's `<project>/factory/agents/`.
- Every limit and cap is a positive whole number.
- `human`, `factory` and `question` cannot be a stage name or a role name.
- Every name in `checks` and `reports` must be a project command.
- `sync` is a project command like the others (`sync: {time_limit: 5}` in the template). The [stage environment](../project-guide/glossary.md) reads its limit for the container that prepares the tools after a checkout. No stage lists it, so it never enters a lease. A definition without `sync` gives it 10 minutes.

## Checking a story before it starts

`factory-check-story` checks story files against where they sit and against your project's `factory/story-form.md`. Run it from the root of a checkout, with the paths relative to that root. The checkout needs `factory/story-form.md`, a `feature.md` in each feature's directory, and the stories in [`backlog`](../project-guide/glossary.md), `in-progress` or `done`.

1. Go to the root of the checkout.
2. Run the command with one or more paths, as in the example below.
3. Read the lines it prints. A story that fits the form prints `<path>: ok`. Every finding is a line of its own, and the table below says what to do.

`python -m factory.entry.check_story <path>...` does the same; use it with `uv run` in the factory's own checkout. The example builds a story in a new folder, so you can see both results.

```console
$ mkdir -p factory/features/F0001-example/backlog
$ printf '# Feature\n' > factory/features/F0001-example/feature.md
$ printf '# A story\n\n## Description\n\nText.\n\n## Interface\n\nText.\n\n## Acceptance criteria\n\n1. It works.\n2. `make check` stays green.\n3. docs: none.\n\n## Smoke test\n\n```sh\necho hi\n```\nExpect: `hi`\n\n## Journal\n' > factory/features/F0001-example/backlog/F0001-S0001-example-story.md
$ factory-check-story factory/features/F0001-example/backlog/F0001-S0001-example-story.md
factory/features/F0001-example/backlog/F0001-S0001-example-story.md: ok
$ factory-check-story docs/pipeline.md
docs/pipeline.md: not a work item location: expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md
$ factory-check-story
usage: factory-check-story <path>...
```

For each path, in the order given, the command prints `<path>: ok`, or one line per finding. A finding with a line reads `<path>:<line>: <message>`, where the line counts from 1 in the story's text after the front matter. A finding without a line reads `<path>: <message>`. Findings about where the file sits come first, then those about its content.

The exit status:

| Status | Meaning |
|---|---|
| 0 | every file is ok |
| 1 | at least one file has a finding |
| 2 | the command could not do its job. There was no path, and it prints the usage line. Or `factory/story-form.md` is unreadable. Or a file does not exist or is not UTF-8, and it prints `cannot read <path>: <reason>`. Nothing more is checked after such a file; what was printed before stays. |

### Where a story may sit

A path must be `factory/features/<feature directory>/<backlog|in-progress|done>/<file>.md`. Otherwise the only line is `not a work item location: ...` and the file is not read, so it need not exist. `drafts` and `ongoing` are not work item locations.

How a file is read depends on its folder and on whether it has front matter:

- A story in `backlog` is read as a specification. Front matter there is a finding.
- A story in `in-progress` or `done` with front matter is read as a work item, and its state is checked too.
- A story there without front matter is a started story as you moved it on `main`, where the state lives on the work item's branch. It is checked like a backlog story, with no complaint about missing state.

### The findings

Findings about the place:

| Finding | What to do |
|---|---|
| `the file name "<name>" is not F0000-S0000[-slug].md` | rename the file; an acceptance's name is not a story's |
| `the feature directory "<directory>" is not F0000[-slug]` | rename the directory |
| `the story <id> is in the directory of feature <id>` | move the story to its own feature's directory, or fix its id |
| `the feature file feature.md is missing in factory/features/<directory>` | add the feature's `feature.md` |

Findings about the content follow the form check (`docs/project-guide/work.md`, "The form check of a story"):

| Finding | What to do |
|---|---|
| `the story has no title line` | start the story with a `# Title` line |
| `missing section: ## <heading>` | add the section your story form lists |
| `criterion numbered <n> where <m> is expected` | renumber the criteria 1, 2, 3 |
| `the second-to-last criterion must contain "make check" and "green"`; `the last criterion must start with "docs:"` | make those the two closing criteria |
| `the Smoke test has no code block`; `the code block opened at line <n> is not followed by an "Expect:" line` | give each block of the smoke test an `Expect:` line after it |
| `journal entry numbered <n> where <m> is expected` | renumber the journal entries |
| `a backlog story carries no front matter: <keys>`; `a backlog story carries no journal entries` | remove the front matter or the entries; the factory writes them when the story starts |
| `the story has no state`; `the journal data lists <n> entries but the text shows <m>` | for a file with front matter in `in-progress` or `done`: the state is damaged, so restore the file from its work item's branch |
| a reader fault such as `unknown key: <key>` or `front matter is not valid YAML` | fix the front matter; no form findings are given until it reads |
