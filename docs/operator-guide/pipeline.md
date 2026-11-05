# The pipeline definition and the story check

A topic of the [operator guide](README.md).

## The pipeline definition

`factory/pipeline.yml` is the project's configuration: its stages, the roles that work in them and the limits. The factory reads it only as it stands on `origin/main`, so a change takes effect when it is merged. This definition loads:

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

The keys, with what a left-out key takes:

| Key | Meaning | Default |
|---|---|---|
| `contract` | the contract version, quoted: `'1.0'` | required |
| `stages` | name to stage; the order in the file is the pipeline's order | required |
| `roles` | name to role; the name is also the agent file's name | required |
| `project_commands` | name to `time_limit` in minutes and, optionally, `not_read` (see below) | `check`, `lint` and `test`, each 10 and `not_read: []` (the template's definition also names `sync`, 5 minutes) |
| `attempts_cap` | attempts before the human is asked | 2 |
| `crash_cap` | crashes before the human is asked | 2 |
| `acceptance_stage` | the stage of the feature acceptance | none |

A stage has `role` (none: no agent runs), `next` (the first name is the forward move), `approval` (the human decides), `checks` (project commands that must pass after the agent), `reports` (project commands run after green and only recorded) and `round_cap` (none: no cap). A role has `write_paths` (required), `lease_duration` (60 minutes) and `time_limit` (40 minutes, one agent run). A write path may hold `{work_item}`, the work item's own file, and `{feature}`, its feature's path (`factory/features/F0004-x`). The engine's protected paths (`factory/pipeline.yml`, the forms, `feature.md`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `.claude/`, `factory/agents/`) are outside every write path. Every limit is a positive whole number.

A definition may hold more than one route and more than one approval stage; a close of a pull request at an approval stage sends the story to that stage's second `next`, and the stage whose first `next` is that approval counts the rounds.

### The docs route

A story that changes only documents (`README.md`, files under `docs/`, `operator/README.md`) skips the tests, doing and review stages. The intake chooses the route: `docs-only` when every path the story's Interface changes is one the documenter may write, otherwise `tests`. The documenter writes the whole change and runs `make documents`; the reviewer reads the documents against the story's criteria and the code, and against the style page, `docs/project-guide/style.md`, once it exists. It then sends the story to `docs-approval`, where you decide, or back to the documenter with numbered findings.

If the documenter finds that the story needs more than documents, it hands the story to the tests stage and says what is needed; the story then takes the normal route. The route works only when your pipeline definition holds the stages `docs-only`, `docs-review` and `docs-approval` and the intake's `next` lists `docs-only`; the agents do nothing on it without them.

The template's smoke test reads `smoke-test: {role: smoke-tester, next: [approval, doing, docs], round_cap: 3}`. A finding that is only a slip in a document (`README.md` or a file under `docs/`) goes from the smoke test straight to `docs`, where the documenter fixes it and hands back to the smoke test; it counts as a rework round against the `round_cap`, as a return to `doing` does.

An unknown key is refused with `pipeline_definition_invalid`. That includes `tool_paths`, which earlier versions read: a definition that still holds it stops the factory until you remove the key. The write paths are all that an agent run may write; there are no further folders for tool state.

`not_read` of a project command lists the paths the command does not read, in the form of `write_paths` patterns: relative to the checkout, `*` also crosses `/`, case-sensitive. The default `[]` leaves nothing out. For example:

```yaml
project_commands:
  check: {time_limit: 10, not_read: ["README.md", "docs/*.md"]}
```

A pattern that cannot name a path inside the checkout (empty, starting with `/` or `~`, holding a `..` segment, or holding `{` or `}`) stops the definition from loading: `project command lint: not_read /etc/* must be a path pattern inside the checkout`. `not_read` is what lets a known result survive a change: the paths it names are left out of the tree that the key holds (see "The known results" in [health.md](health.md)), so a change only there is no reason to run the command again. List only what the command does not read at all. A linter, formatter or type checker that walks the whole tree reads every source file in every folder, so leave out file types it does not read, never a whole folder. A forgotten path costs one run; a path listed by mistake can let a reused `check` pass a fault.

kumpel-factory's own definition, `factory/pipeline.yml`, takes this, and only Markdown and JSON Lines files, because `make lint` reads every Python file of the tree, wherever it lies:

```yaml
project_commands:
  check: {time_limit: 8, not_read: ["README.md", "docs/*.md", "factory/features/*.md", "factory/features/*.jsonl", "factory/stops.jsonl", "planning/*", "session-logs/*"]}
```

Two warnings:

- A project whose `check` scans changed files for secrets keeps a scan of the left-out files only if something else runs it. kumpel-factory's docs stage runs `secrets` as a check of its own, with nothing left out.
- A command whose result depends on anything outside the tree and the image, such as dependencies fetched at run time with unpinned versions, is reused safely only when those versions are pinned in the tree (for example by a lockfile). Otherwise leave `not_read` empty and do not rely on reuse for it.

The rules you meet most often:

- The stage `done` must exist, with no role and no `next`. Write it `done: {}`; `done:` alone is refused.
- The contract major must be 1. Any minor is read.
- Every stage other than `done` needs a non-empty `next` and either a role or `approval: true`; every name in `next` must be a stage.
- The lease: for each stage with a role, the role's `time_limit` plus the `time_limit` of every command in the stage's `checks` and `reports` must be at most the role's `lease_duration`. With the defaults, 40 + 10 (one check) + 10 (one report) = 60 fits; a stage with two checks and a report adds up to 70 and is refused. Raise the `lease_duration` or lower a limit.
- Values are taken only in their YAML type: a limit is an integer (not `'30'`, `30.0` or `true`), `approval` is `true` or `false` (not `'yes'` or `1`), names and write paths are text. A write path must hold a character that is not whitespace.
- A key that is not listed is refused, so a misspelt key is never ignored. A given `project_commands` replaces the default set as a whole: list `check`, `lint` and `test` again if you still want them. `sync` is a project command with a `time_limit` like the others (`sync: {time_limit: 5}` in the template), and the stage environment reads that limit for its sync container; no stage lists it in `checks` or `reports`, so it never enters a lease. A definition without `sync` gives the sync the default limit of 10 minutes.
- Every role needs an agent file, a project's own or the installed one (see "The agent files" in [agent-runtime.md](agent-runtime.md)).

A refused definition raises the stop `pipeline_definition_invalid`, described in "The stop `pipeline_definition_invalid`" in [stops.md](stops.md). `docs/project-guide/pipeline.md`, "The rules of the definition", lists every fault.

## Checking a story before it starts

`factory-check-story` checks story files against where they sit and against your project's `factory/story-form.md`. Run it from the root of a checkout, with the paths relative to that root. The checkout must be laid out the v1.1 way: `factory/story-form.md`, a `feature.md` in each feature's directory, and the stories in `backlog`, `in-progress` or `done`.

In a project laid out the v1.1 way (the paths are placeholders):

```bash
uv run factory-check-story factory/features/F0001-example/backlog/F0001-S0001-example-story.md
```

prints `factory/features/F0001-example/backlog/F0001-S0001-example-story.md: ok` and exits 0 when the story fits the form.

`uv run python -m factory.entry.check_story <path>...` does the same. For each path, in the order given, it prints `<path>: ok`, or one line per finding: `<path>:<line>: <message>` where the finding has a line (a line of the story's text after the front matter, counted from 1), and `<path>: <message>` where it has none. Findings about where the file sits come first, then those about its content.

| Status | Meaning |
|---|---|
| 0 | every file is ok |
| 1 | at least one file has a finding |
| 2 | the command could not do its job: no path (it prints `usage: factory-check-story <path>...`), `factory/story-form.md` unreadable, or a file that does not exist or is not UTF-8 (`cannot read <path>: <reason>`). Nothing more is checked after such a file; what was printed before stays. |

A path must be `factory/features/<feature directory>/<backlog|in-progress|done>/<file>.md`. Otherwise the only line is `not a work item location: ...` and the file is not read (it need not exist). `drafts` and `ongoing` are v1's folders and not work item locations, so they are not accepted.

How a file is read depends on its folder and on whether it has front matter. A story in `backlog` is read as a specification: front matter there is a finding. A story in `in-progress` or `done` with front matter is read as a work item and its state is checked too. A story there with no front matter is a started story as you moved it on `main`, where the state lives on the work item's branch; it is checked like a backlog story, with no complaint about missing state.

Findings about the place, and what to do:

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
