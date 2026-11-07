# Records, costs and the view of the remote

A topic of the [operator guide](README.md).

The factory writes records as it works: the state of each [work item](../project-guide/glossary.md), a [cost record](../project-guide/glossary.md) for each agent run and a record of each [stop](../project-guide/glossary.md). This page tells you which records a program outside the factory may rely on, how to read what a work item cost with `factory-bill`, and how to see what the factory would do next with `factory-watch`. The exact fields and limits are in the *Reference* at the end.

- [The records contract](#the-records-contract)
- [What a work item cost: `factory-bill`](#what-a-work-item-cost-factory-bill)
- [Looking at the remote: `factory-watch`](#looking-at-the-remote-factory-watch)
- [Reference](#reference)

## The records contract

A reader outside the factory, such as a page that shows a factory's records from GitHub, may rely on these records and on nothing else:

| Record | Where | Schema |
|---|---|---|
| the front matter of a work item | the story file; for an acceptance report, its file | `work-item-state`; `acceptance-state` for an acceptance report |
| one line of a work item's cost records | `<work item>.costs.jsonl` | `cost-record` |
| one line of the stop records | `factory/stops.jsonl` | `stop-record` |
| the pipeline definition | `factory/pipeline.yml` | `pipeline-definition` |

The Markdown body of a work item, the text of the journal entries included, is for people. Never parse it.

The schemas are JSON Schema files (draft 2020-12) in `src/factory/contract/`, named `<schema>.schema.json`. They are generated from the models that validate each record and are never written by hand. A story that changes one of those models regenerates them in the same change; `make check` fails when a committed file differs from what the models give. The files are package data, so they ship in the wheel, and a reader in another repository can fetch them from `main`.

To regenerate the schemas, or to write them into another folder, run the command below. It prints how many schemas it wrote.

```console
$ python -m factory.entry.contract "$PWD/schemas"
contract: 5 schemas written
```

With two or more arguments the command prints `usage: python -m factory.entry.contract [<folder>]` to standard error, writes nothing and exits with status 2.

**Where a work item's records are.** While the work item is in progress they are on its branch `work-item/<id>`: the factory writes the front matter and the sidecar there at every stage. From the merge on they are on `main`, moved to `done/` by the archive commit. A work item in `in-progress/` on `main` without a merge shows only the state it had at its start.

**The approval.** A work item enters the approval with its last `result` record in the journal. No record marks the entry, so a reader takes the approval's start from that record's `at` and its end from the `done` record's `at`.

**The version.** Each schema carries the records contract's version in `x-records-contract`, now `4.4`. The major version rises for a change that can break a reader: a field removed or renamed, a type narrowed, a meaning changed. The minor version rises for an added optional field or value. This version is not the `contract` of the [pipeline definition](../project-guide/glossary.md), which is the version of the definition's own format (see "The pipeline definition" in [pipeline.md](pipeline.md)). What each version changed is in [the decision log](../decisions.md).

**Unknown properties.** The schemas say `additionalProperties: false` for what this version of the factory writes. A reader still ignores a property it does not know, since a later minor version may add one.

## What a work item cost: `factory-bill`

Every agent run writes a cost record beside its work item; it holds the run's duration, the time the model took, the turns, the tokens and the cost. `factory-bill` adds the records up and prints the bill. Run it from a checkout of your project:

```sh
uv run factory-bill F0001-S0001
uv run factory-bill
```

With an id it prints the cost table, an empty line and `Cost: <line>`. With no argument it does that for every work item in flight, each block headed by its id and separated from the next by an empty line. A work item in flight is one that has a branch `work-item/<id>` on the remote.

The command reads the remote-tracking refs only (`origin/<the work item's branch>`, or `origin/main` for an archived work item), never your working tree and never the journal. It does not fetch: run `git fetch` first to see the latest records. Two checkouts that have fetched the same remote show the same bill.

| Exit status | Meaning |
|---|---|
| 0 | the bill was printed (with no argument, also when nothing is in flight) |
| 1 | `no work item <id>`: no file of that id on the remote |
| 2 | `not a work item id: <argument>`, or more than one argument (`usage: factory-bill [<work item id>]`) |

```console
$ factory-bill not-an-id; echo "status $?"
not a work item id: not-an-id
status 2
```

A work item with a file but no cost records has a bill of 0 runs and $0.00.

### The cost table

```
| stage | runs | min | model min | turns | in | cached | out | USD |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: |
| tests | 1 | 1.0 | 0.7 | 7 | 62 | 1000 | 300 | 0.35 |
| doing | 2 | 2.5 | 1.8 | 5 | 10 | 500 | 100 | 1.20 + 1 unknown |
| **total** | 3 | 3.5 | 2.5 | 12 | 72 | 1500 | 400 | 1.55 + 1 unknown |
```

One row per stage, in the order the stage first ran; a stage that runs again (`doing`, `review`, `doing`) is one row. The last row is the total.

| Column | Meaning |
|---|---|
| runs | agent runs, every one counted whatever its end: a run that died, ran past its time limit or spent its budget is in the bill |
| min | the runs' duration in minutes, one decimal |
| model min | the minutes the model took, from each run's `model_seconds`, one decimal; `min` less `model min` is the time of the tools and the factory; a run without `model_seconds` adds nothing |
| turns | the turns the runtime reported |
| in | input tokens plus cache-creation tokens |
| cached | tokens read from the cache |
| out | output tokens |
| USD | the cost in dollars, two decimals |

Figures are rounded half up.

When the factory posts the table on the pull request (see "The hand-over at the approval" in [work-items.md](work-items.md)), a line follows it after an empty line:

```
Human: 2 questions answered (question 1, crash_cap 1), 1.5 h waited
```

It counts the questions that stopped the work item for you: the agent's question and the stops `round_cap`, `send_back` and `crash_cap`. A question counts once you have answered it, by a comment or by closing the pull request; the close counts as an answer too. The parenthesis names each cause and how many were answered, and is left out when none was. The hours are the time from each question to your next record in the journal, summed. A question you have not answered yet counts in neither figure. The wait can be up to one tick too long, because a comment is dated when the factory copied it from the pull request, not when you wrote it. `1 questions answered` is the wording for one as well. `factory-bill` prints the table only, without this line.

### The cost line

The line under the table sums the same figures: `3 runs, 3.5 min, 12 turns, 72 tokens in (1500 more from cache), 400 out, $1.55 + 1 unknown`.

### An unknown cost

A run whose cost the runtime did not report (a run that died, or one the time limit ended) has an unknown cost. It is not counted as $0.00: it is left out of the sum and shown as `+ <n> unknown` after the dollars, where `<n>` is the number of such runs. Unknown turns and tokens are left out of their sums in the same way, without a mark; so the figures are a lower bound when `unknown` is shown.

## Looking at the remote: `factory-watch`

`factory-watch` is the window on what the factory would do next. It evaluates once, as a [tick](../project-guide/glossary.md) would after its fetch, except that it judges its own [instance](../project-guide/glossary.md)'s [claim](../project-guide/glossary.md) by the [lease](../project-guide/glossary.md), since a tick never looks while its own stage runs. It prints two things: the event of that evaluation, and the board. It has no options; `--help` shows its usage.

It reads the remote-tracking refs as the last tick left them. It fetches nothing, so after a push to the remote the output stays the same until a tick has fetched. It writes nothing: no file in the checkout, nothing to the remote or the hosting service, no health status entry, no log line. It loads the pipeline definition at the head commit of `origin/main` and raises or clears no stop. The one hosting-service read it makes is the one an idle tick makes: the pull request (and its comments) of a waiting work item.

```
event: <key>  <detail, when there is one>

features
F0001  Todo service  backlog=1  in-progress=2  done=3  acceptance=-
work items
F0001-S0001  Domain model  in-progress  stage=tests  blocked=-  claim=factory-1  running_since=2026-10-14T09:30:00Z  pull_request=7
```

- The first line is `event: <key>`, followed by two spaces and the detail when the event has one.
- A feature row counts the story files in `backlog`, `in-progress` and `done`; `.gitkeep`, `feature.md` and files that are not work item names do not count, and a feature with no story file has no row. The title is the first `# ` title of the feature's `feature.md` on `origin/main`, else the directory's name. `acceptance` is the feature's acceptance status (`incomplete`, `due`, `in_flight`, `merged_unrecorded`, `accepted` or `refused`; see "When a feature acceptance is due" in [work-items.md](work-items.md)), or `-` when the pipeline definition has no `acceptance_stage`.
- A work item row exists for each story in `in-progress/` and for each running acceptance (one that is opened, waiting with a question or at its approval, or merged and not yet booked), with its title (the first `# ` title of the body, else the id), its stage, what it waits for (`blocked`), the instance holding its claim, since when (`running_since`, the claim's start in UTC) and its pull request. An absent value is `-`. The rows are in id order, so an acceptance's row comes after its feature's stories and before the stories of a later feature. An acceptance's title is `Acceptance of <feature title>`, its folder `in-progress`, and its state is the one on its branch.
- A claim of the instance `factory-watch` runs as shows as `event: idle:-  <work item> is held by <instance>` while its lease runs, because the instance may be running that stage, and as `event: crash:<work item>` once the lease has run out. The tick itself still reruns its own claim at its first look after a restart, whatever the claim's age. A stage that waits out a provider limit holds its claim past its lease, so it shows as a crash here while it waits; the factory log's line of the wait tells the two apart. A live stage that uses every limit can show as a crash for up to about a minute past its lease. The board's rows are the same either way.
- Exit status: 0 after printing; 1 when the pipeline definition on `origin/main` is invalid or an agent file is refused (the fault goes to standard error as `factory-watch: <fault>`, or `factory-watch: agent <name>: <fault>` for an agent file; standard output stays empty, no stop is raised); 2 for an unknown option, and when the environment is invalid or the token file cannot be read: then `factory-watch: settings invalid: <variable>: <fault>` goes to standard error (never a traceback) and standard output stays empty. `factory-watch` reads the same environment as `factory-run` (see the table of *Configuration* in [install.md](install.md)) and builds its boundaries the same way, so it looks at the instance the container runs. It needs the same two path settings, `FACTORY_CLAUDE_HOME` and `FACTORY_IMAGE_ID_FILE`, so run it with the environment file of the service (`operator/vm/setup.sh` writes it). A repository whose `origin/main` does not resolve (a clone that never fetched) ends with a git error.

## Reference

The optional keys of a cost record. `factory-bill` prints none of them; they are for a reader of the records on GitHub or in the Factory Timeline. A reader ignores a key it does not know.

### Cost record: refused tool calls in the sidecar

A completed record in the sidecar (`<work item>.costs.jsonl`) can carry two more keys: `denials`, the number of tool calls the agent runtime reported as refused in that run, and `denied_paths`, the files those calls named, each once, in the order reported. A third key, `login`, says which login the run's calls were handed: `subscription`, `none` or the value that names the API key; a runtime with no login file leaves it out. A run that got no reply (it died or ran past its time limit) has neither of those two keys; an older line has none of the three. Only the tool calls the runtime reports as refused are counted. A refusal that is only text in a tool's output, such as a write the kernel refuses, is not in them. `factory-bill` does not print these keys.

### Cost record: the machine

A completed cost record can carry `machine`, an object with the machine's measures at that run, so that the records on GitHub and the Factory Timeline show a machine that grows or is too small. A `started` record has none. Each field is a number, or `null` when the machine cannot give it (a missing cgroup file, an image without a size); a failed reading never fails the run. When nothing can be read the record holds `"machine": null`.

| Field | Meaning |
|---|---|
| `base_image_bytes` | Size of the base image (`FACTORY_STAGE_IMAGE`) the run's image was built on. |
| `project_layer_bytes` | Size of the project image minus the base's; `0` for a project without a stage file. `null` when the project image is smaller than its base. |
| `store_free_bytes` | Free space of the file system that holds podman's image store. |
| `dataset_free_bytes` | Free space of the stage's dataset (`FACTORY_WORKSPACE`); on ZFS it respects the dataset's quota. |
| `memory_peak_since_boot_bytes` | `memory.peak` of the cgroup v2 slice of the user that runs the containers (`/sys/fs/cgroup/user.slice/user-<uid>.slice/`), read at the record's completion. |
| `memory_total_bytes` | The machine's memory, `MemTotal` of `/proc/meminfo`. |
| `cpu_seconds` | CPU time the slice used during the run (`usage_usec` of `cpu.stat`, end minus start). |
| `cpu_wait_seconds` | Time the slice's work waited for a CPU during the run (the `total` of the `some` line of `cpu.pressure`, end minus start). |
| `memory_wait_seconds` | The same for memory (`memory.pressure`). |

The two image sizes are measured when the factory builds or adopts an image (at its start, and after a changed stage file), not at every run, so they change only after a build or a return to the base. The other values are read at the run's start and end; nothing is sampled during the run.

**The memory peak is not the run's own.** The kernels in use (6.8 on the VM) cannot reset `memory.peak`, so the value is the highest use since the slice began, which on a VM with lingering is since boot. The first record in which it rises names the run that raised it; the records after it repeat the value until something goes higher.

**The CPU time and the waits are the run's own, but they count every container of the factory user.** They are differences of the kernel's running totals, so two instances that run at once on one machine see each other's load. A reading that is missing at the start, or a total that is lower at the end than at the start (the slice began again), gives `null`.

How to read them:

- `cpu_seconds` divided by the record's `duration_seconds` is the number of cores the run used on average.
- A `cpu_wait_seconds` or `memory_wait_seconds` above zero means work waited for the CPU or for memory: the machine is too small for that load.
- `store_free_bytes` and `dataset_free_bytes` falling from record to record show the disk filling before it is full.

Under the `job` container profile the containers run as root, so the user slice the factory looks at may be another cgroup than the containers': the measures there may be `null` or another slice's.

### Cost record: the tool calls

A completed cost record can carry `tools`, the run's tool calls summed up without their content, so that the records on GitHub and the Factory Timeline show where a run spent its turns and time, and how often its calls failed. It is read from the run's transcript (Claude Code's session file, opencode's event stream) before the transcript is copied or thrown away, so it is written whether or not `FACTORY_TRANSCRIPT_DIR` is set. A `started` record has none.

`tools` is a list with one entry per tool, sorted by `tool`:

| Field | Meaning |
|---|---|
| `tool` | The tool's name as the runtime gives it (`Bash`, `Read`, `Edit`, `bash`). A name that is longer than 64 characters or holds anything but letters, digits, `_`, `-`, `.` and `:` is counted under `other`, together with a tool really named `other`. |
| `calls` | How many times the run called it. |
| `failed` | How many of those calls failed: Claude Code's `tool_result` with `is_error`, opencode's tool state `error`. Never above `calls`. |
| `seconds` | The seconds the calls took: Claude Code's `timestamp` of the `user` line that holds the call's `tool_result` minus that of the `assistant` line that holds its `tool_use`; other lines of the session file (`api-request-blob`, `attachment` and the like) are not read, and when an id appears on two lines of the right type the first one counts. opencode's `time.end` minus `time.start`. `null` when the runtime gave no times. |

A call with no result counts as a call, not as failed, and adds no seconds. `[]` means the run made no tool call. `"tools": null` means the calls could not be read (or the record is older than contract 4.4); the run does not fail for it.

The entries hold no command, no file content, no path and no argument of any call: only the tool's name and three numbers.
