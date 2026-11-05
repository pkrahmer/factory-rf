# Style samples: today's text and three new styles

Two real paragraphs from each document, first as they read today, then rewritten in three styles. The facts stay the same in every version; only the writing changes. The style you chose in the first quiz is marked "chosen", but every option is open again.

---

## The operator guide

### Sample 1: "Install" (`docs/operator-guide/install.md`)

**Today:**

> Install v1.1 only on a repository v1 has not worked in, or whose v1 work items are archived or discarded: v1.1 starts fresh, and nothing detects a v1 work item.
>
> Install the factory with `uv sync`, then check the installation with `make check`; it ends with the line `check: green`. `operator/vm/setup.sh` is the way to run an instance (see "The machine" in [machine.md](machine.md)): it makes the VM, installs the factory and the service, and the stage image carries the agent runtime and the pinned tools. Then set the instance's environment as described under "Configuration".

**A. Numbered steps** (chosen):

> 1. Install the factory's packages:
>
>        uv sync
>
> 2. Check the installation. The last line must be `check: green`:
>
>        make check
>
> 3. Prepare the VM with `operator/vm/setup.sh`. It creates the VM, installs the factory and its service, and builds the image the agents run in. See "The machine".
> 4. Set the instance's settings, as "Configuration" describes.
>
> Use a repository that the older factory never worked in. The factory does not recognise the older factory's work items.

**B. Plain prose:**

> You install the factory with `uv sync`. Then you run `make check`. When everything works, its last line is `check: green`.
>
> An instance runs on a Linux VM. The script `operator/vm/setup.sh` prepares it: it creates the VM, installs the factory and its service, and builds the image the agents run in (see "The machine"). Then you set the instance's settings, as "Configuration" describes.
>
> Use a repository that the older factory never worked in. The factory does not recognise the older factory's work items.

**C. Compact reference:**

> - **Install:** `uv sync`
> - **Check:** `make check`; the last line is `check: green`
> - **VM:** `operator/vm/setup.sh` creates the VM, the factory, its service and the agents' image ("The machine")
> - **Settings:** see "Configuration"
> - **Repository:** a fresh one; the older factory's work items are not recognised

### Sample 2: "A stall by a red check" (`docs/operator-guide/stops.md`)

**Today:**

> When the agent decides to move forward and the stage has checks, the factory runs them itself, in the order of the pipeline definition, and stops at the first that is red. A check is green only when its make target exits 0. A red check is a stall that costs one attempt; the stage, the round and the crash count stay. On the pull request you see the stall note with the cause `a check is red after the stage` and, after a colon, the check's name; below the sentence, in a code block, come the last 15 lines of its output (all of them when it printed fewer). The block keeps GitHub from rendering the output as Markdown.

**A. Numbered steps** (chosen; for a stop: what you see, what it means, what you do):

> **What you see.** A comment on the pull request: `Stalled (attempt 1 of 2): a check is red after the stage: check`, with the last 15 lines of the check's output below it.
>
> **What it means.** The agent finished its stage, but one of the stage's checks failed. A check passes only when its make target exits with 0. The factory ran the checks in the order of the pipeline definition and stopped at the first that failed.
>
> **What you do.**
> 1. Read the output in the comment. It usually names the failing test or tool.
> 2. Do nothing if the cause is one the agent can fix: the factory tries the stage again on the next tick.
> 3. After the second failed attempt the factory asks you. Write a comment with your answer to retry, or close the pull request to send the story back to the backlog.

**B. Plain prose:**

> When an agent finishes its stage, the factory runs the stage's checks itself. It runs them in the order of the pipeline definition and stops at the first that fails. A check passes only when its make target exits with 0.
>
> A failed check is a stall. The factory tries the stage again on the next tick, up to two attempts. On the pull request you see a comment that says `a check is red after the stage`, names the check, and shows the last 15 lines of its output.

**C. Compact reference:**

> - **Cause:** a check of the stage failed (its make target did not exit with 0)
> - **Comment:** `Stalled (attempt n of 2): a check is red after the stage: <check>`, with the last 15 lines of output
> - **The factory:** tries again on the next tick; after two attempts it asks you
> - **You:** read the output; answer with a comment to retry, or close the pull request

---

## The project guide

### Sample 1: "The take" (`docs/project-guide/machine.md`)

**Today:**

> In the container environment the agent works on the dataset and may write anywhere it reaches; nothing of that survives but what the take copies. `TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths)` (`factory.pipeline.application.take`) applies the write paths' refusal rule (see *The take's rule*, `pipeline.md`): what the role may write goes from the dataset at `mount_point` into the work tree `boundaries.checkout`, the rest stays in the dataset. `changed_paths` are those of `Snapshots.changed_paths()`, relative to `mount_point`. `ContainerEnvironment.take` calls it (see *The container environment*).

**A. Idea first, then the API** (chosen):

> After an agent's run, the factory copies back only what the agent's role may write. The agent works on its own copy of the repository (the dataset), and everything else it changed is dropped. This copy step is the take.
>
>     TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths) -> TakeReport
>
> - A path goes back when the role's write paths allow it and no protected path forbids it.
> - `changed_paths` come from `Snapshots.changed_paths()`, relative to `mount_point`.
> - The work item's state and journal are restored from the stage-start commit.
>
> See also: *The take's rule* (`pipeline.md`), *The container environment*.

**B. Reference card:**

> | | |
> | :-- | :-- |
> | Purpose | copy back from the dataset what the role may write; drop the rest |
> | Module | `factory.pipeline.application.take` |
> | Entry | `TakeService(boundaries, mount_point).take(stage_start, work_item_path, changed_paths)` |
> | Input | `changed_paths` from `Snapshots.changed_paths()` |
> | Output | `TakeReport(left, restored_work_item)` |
> | Errors | `WorkItemFormatError` when the work item is unreadable at the stage-start commit |
> | Called by | `ContainerEnvironment.take` |
> | See also | *The take's rule* (`pipeline.md`) |

**C. Today's prose, cleaned:**

> In the container environment, the agent works on the dataset. It may write anywhere it reaches, but only what the take copies survives.
>
> `TakeService.take` (in `factory.pipeline.application.take`) applies the refusal rule of the write paths. What the role may write goes from the dataset into the work tree. The rest stays in the dataset and is lost at the next rollback. The changed paths come from `Snapshots.changed_paths()`. `ContainerEnvironment.take` calls it.

### Sample 2: "The hosting service" (`docs/project-guide/hosting.md`)

**Today:**

> The factory reaches the hosting service (pull requests and their comments) only through the `HostingService` interface (an abstract base class) in `factory.hosting.application.hosting`. Nothing else may call it, and the application layer knows no concrete client. `PyGithubHostingService` (`factory.hosting.adapters.pygithub_hosting`) is the one client; `FakeHostingService` (`factory.hosting.adapters.fake_hosting`) is the one fake. Build comments from the service's data with `PullRequestComment.from_body`, so that `by_factory` and `key` always agree with the body.

**A. Idea first, then the API** (chosen):

> The factory talks to GitHub about pull requests and their comments through one interface. That keeps GitHub out of the rest of the code, and lets the tests use a fake.
>
>     factory.hosting.application.hosting.HostingService      # the interface
>     factory.hosting.adapters.pygithub_hosting.PyGithubHostingService   # the one client
>     factory.hosting.adapters.fake_hosting.FakeHostingService           # the one fake
>
> - No other module calls GitHub, and the application layer knows no concrete client.
> - Build a comment from the service's data with `PullRequestComment.from_body`, so that `by_factory` and `key` always agree with the body.
>
> See also: *The git wrapper*.

**B. Reference card:**

> | | |
> | :-- | :-- |
> | Purpose | pull requests and their comments, behind one interface |
> | Interface | `HostingService` in `factory.hosting.application.hosting` |
> | Client | `PyGithubHostingService` in `factory.hosting.adapters.pygithub_hosting` |
> | Fake | `FakeHostingService` in `factory.hosting.adapters.fake_hosting` |
> | Rule | build comments with `PullRequestComment.from_body` |
> | See also | *The git wrapper* |

**C. Today's prose, cleaned:**

> The factory reaches the hosting service only through the `HostingService` interface in `factory.hosting.application.hosting`. The service covers pull requests and their comments. Nothing else may call it, and the application layer knows no concrete client.
>
> `PyGithubHostingService` is the one client, and `FakeHostingService` the one fake. Build comments with `PullRequestComment.from_body`. Then `by_factory` and `key` always agree with the body.

---

## The README

### Sample 1: the opening (`README.md`)

**Today:**

> The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test, one agent at a time (on Claude Code, or on opencode when the operator chooses it for an instance), and the human approves each story on its pull request. This repository is its second implementation, v1.1. The first (github.com/pkrahmer/factory) built it until the handover of 2026-10-18; since then v1.1 builds this repository itself (see *How it is built*). `docs/project-guide/README.md` maps every part of the code.

**A. What it is for, then try it** (chosen):

> kumpel-factory builds software from stories. You describe a feature as a few short stories. The factory hands each story to AI agents in turn: one writes the tests, one the code, one reviews it, one updates the docs. Then it opens a pull request, and you approve it or send it back.
>
> It runs on a Linux VM or as a Cloud Run job, with Claude Code or opencode as the agents.

**B. Plain and factual:**

> The factory takes a feature, split into stories, through tests, code, review, documentation and a smoke test. One agent works at a time, on Claude Code or opencode. The human approves each story on its pull request. This repository is built by the factory itself.

**C. Bullet overview:**

> - **What:** a pipeline that turns stories into reviewed pull requests
> - **How:** one AI agent per stage: tests, code, review, docs, smoke test
> - **You:** write the stories, answer the agents' questions, approve
> - **Runs on:** a Linux VM or a Cloud Run job, with Claude Code or opencode

### Sample 2: after the first commands (`README.md`, *Getting started*)

**Today:**

> When it works, `make check` ends with the line `check: green`. An instance runs on a VM that `operator/vm/setup.sh` prepares: see *The machine* in `docs/operator-guide/machine.md`; the guide's topic files also give the exit statuses of the commands you run.

**A. What it is for, then try it** (chosen):

> When it works, `make check` ends with `check: green`.
>
> To run the factory on your own repository, set up a VM with `operator/vm/setup.sh`. The operator guide walks you through it: start with [Installing and running an instance](docs/operator-guide/install.md).

**B. Plain and factual:**

> When it works, `make check` ends with the line `check: green`. An instance runs on a VM that `operator/vm/setup.sh` prepares. The operator guide describes the setup in *The machine* (`docs/operator-guide/machine.md`).

**C. Bullet overview:**

> - **Works when:** `make check` ends with `check: green`
> - **Run an instance:** `operator/vm/setup.sh`, see `docs/operator-guide/machine.md`
> - **Read next:** `docs/operator-guide/` (operating), `docs/project-guide/` (changing the code)
