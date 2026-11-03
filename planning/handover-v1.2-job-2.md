# Handover: the second trial at work (`v1.2-job-2`)

For the colleague who runs the factory's Cloud Run job at work for the first time with this version. You need no history: read this page, then the operator guide's chapters it names.

## What this is

Kumpel's factory builds software from small, written stories. A person writes a story into a project's repository. The factory picks it up, and its agents (intake, tester, coder, reviewer, documenter, smoke tester) work through it, each in a throwaway container. The result is a pull request that waits for a person's approval. Questions the agents cannot answer alone arrive as comments on that pull request. Nothing is merged without a person.

At work the factory runs as a Cloud Run job: an execution installs what it needs, clones the factory's code at a fixed tag, works on the project's stories and ends itself when it has nothing to do for a while.

## What this trial is for

Version `v1.2-job-2` adds one thing for the operator: **all of a machine's own values live in one site file**, outside every repository, and a handful of commands work from it alone. `site check` says whether a machine is ready, and `job.sh` creates, starts, watches and deletes the job.

The code is tested on a VM at home and on stand-ins, but three things can only be seen in a real job at work. Please bring them back:

1. **The memory peak.** The job's default is now 4 vCPUs and 16 GiB. The stage image (about 2.4 GB) sits in the job's memory. An earlier trial used 4.7 GiB of 32. Read the execution's memory peak in the Cloud Run console.
2. **gcloud's wording for a missing job.** Run `site check` once *before* the first `job.sh create`, and copy its `job` line.
3. **The usage-limit text, if a limit is hit.** A run that dies now writes one line `run <id> of <work item> (<stage>) died: <text>` to the factory log. Copy any such line.

## Before you start

From whoever runs the platform you need (the guide's *What the platform must provide first*): the cloud project and region, a network connector whose proxy reaches the code host and the model API, the service account the job runs as, two secrets (the hosting token and the model key; only their names go into the site file), and the code host's bot user with push access to the trial repository and read access to the factory's code.

On your machine: `gcloud`, `git`, `curl`, `python3` and a POSIX shell.

The tag must be in the copy of the factory's code at work. Someone with access to both repositories runs, in any clone:

```bash
git fetch https://github.com/pkrahmer/kumpel-factory.git tag v1.2-job-2
```

```bash
git push <the work copy's URL> v1.2-job-2
```

## The steps

Follow `docs/operator-guide.md`, *Setting up an operator's machine*, step by step. In short:

1. Clone the factory's code at work and check out `v1.2-job-2`.
2. `sh operator/bin/site init` writes the site file. Fill it in: every key is described in the guide's *The keys*, and its comments say which keys a job needs. Set `SITE_CODE_REF=v1.2-job-2`. Beside it, write `sanitise.rules` with the site's own names (the guide's *Sanitising what leaves the machine*); without it, the log commands cannot sanitise.
3. `sh operator/bin/site show` lists which keys are set (never their values).
4. `sh operator/bin/site check` until it ends with `site: ready`. **Copy the `job` line now** (point 2 above). Fix each `FAIL` from the first one down; the guide's table *The checks* says what each means.
5. `sh operator/job/job.sh create --dry-run` prints the call without running it. Read it once, then `sh operator/job/job.sh create`.
6. `sh operator/job/job.sh execute`. The job needs a few minutes to install, clone and build before the factory runs.
7. `sh operator/job/job.sh status` and `sh operator/job/job.sh log --quiet` while it runs (the guide's *Watching the job*; the log arrives one to two minutes late).
8. Drive one story through it, by hand on the pull request or with the skill (`operator/README.md`, *Installing*).
9. `sh operator/job/job.sh delete --yes` when you are done.

## What to send back

- the `job` line of step 4;
- the output of `sh operator/job/job.sh log 200 --quiet` and of `sh operator/job/job.sh status`, which are sanitised by the site's own rules;
- the execution's memory peak and its duration;
- any `died:` line, and anything that surprised you.

## Rules that matter

- **No company value goes into any repository**: no project, host, account or secret name. The site file lives outside every repository, and the loader refuses one inside a work tree.
- **Never paste a token or a key** into a file, a comment or a chat. The site names only a command that prints the token (`SITE_TOKEN_CMD`) and the secrets' names.
- **Send only sanitised output.** `job.sh log` and `job.sh status` sanitise; for anything else, `sh operator/bin/sanitise check <file>` says whether it is clean.
- **When the factory stops**, its log or `status` names the stop. The guide's chapter *The stops* says what each one means and what to do.

## Where to look

- `docs/operator-guide.md`: *The site file*, *Setting up an operator's machine*, *On Cloud Run*, *The stops*.
- `operator/README.md`: the map of the operator's folder and the skill.
- Questions: to the person who handed this over.
