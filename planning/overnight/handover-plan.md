# The handover of factory-rf from v1 to v1.1 (plan step 5)

Written on 2026-10-18 from the brief `planning/overnight/briefs/plan-handover.md`, checked against v1.1's code as it stands on the local checkout (F0016 accepted; F0017, the seal-test fixture, still to be built by v1). Nothing here has been done yet. Marks: **[H]** the human does it by hand, **[H-OK]** the session does it after the human's word, **[S]** the session does it.

## In short

One human commit on `main` turns factory-rf into a v1.1 project: it adds `factory/pipeline.yml`, `factory/story-form.md` and `factory/feature-form.md`, moves everything of v1 under `factory/` (the stage table, the two forms, the features F0001 to F0017) to `factory/v1/`, renames those paths in `.secrets.baseline`, teaches the `Makefile`'s `mutants` target v1.1's acceptance branch, and turns `CLAUDE.md` to v1.1's words with F0016's standing leave. Before it, v1's container is stopped (not removed) and the idle shakedown instance too; after it, a v1.1 instance `self` starts from this checkout's `image/compose.yml` with a new fine-grained token for factory-rf alone. The first self-built work item is a one-story warm-up (the documents name the handover), then 5a, the write guard by Landlock.

## Why v1's features must leave `factory/features/` (checked in the code)

v1.1 reads `factory/features/<F0000-slug>/{backlog,in-progress,done}/` and nothing else (`src/factory/domain/paths.py`, `folder_of`). v1's features have `done/` folders full of story files (`F0001-S0001-....md`), and v1.1's `done` is the same folder name:

- `AcceptanceReader._feature_acceptance` (`src/factory/application/acceptance_reading.py`) counts them as archived stories; with no v1.1 report covering them, `acceptance_status` (`src/factory/domain/acceptance.py`) returns `due`. Left in place, the first tick would see 16 or 17 features with their acceptance due and open `work-item/F0001-A0001` with an acceptance reviewer run (about $2 to $5 each, with `make mutants`), one after the other.
- The stale-branch cleanup ("A stale branch is deleted by the tick", operator guide) would also treat every v1 story in `done/` as an archived story and try to delete `work-item/<id>` for each (harmless, none exists, but it is v1.1 reading v1's work items, which decision 008 rules out).
- `drafts/`, `ongoing/`, `FEATURE.md` (upper case) and `ACCEPTANCE.md` are not read: `folder_of` gives `None` for `drafts`/`ongoing`, `feature.md` is looked up case-sensitively through `git show`, and `list_files` matches the prefix `factory/features/` with its slash, so `factory/v1/features/` is never listed.
- v1's branches (`ticket/...`, `acceptance/...`) are ignored: `work_item_of_branch` matches only `work-item/F0000-[SA]0000`. Labels are written as a projection and never read back. Pull requests are read only by a work item's branch.

So the move is required, not cosmetic. No test in `tests/` reads the repository's own `factory/` tree (searched: every `factory/features/...` in `tests/` is a path inside a temporary test repository; `tests/test_demos.py` reads `demo/` only; no test reads `CLAUDE.md` or the `Makefile` of this repository), and `make check`'s other tools do not look there (ruff leaves out `*.md`, mypy, import-linter, semgrep, bandit and vulture read `src`/`tests`). The one tool that does is `make secrets`; see the `.secrets.baseline` change below.

## 1. Preconditions, each with its check

Run from `C:/Dev/Projects/factory-rf` in Git Bash unless said otherwise. All must hold at the same moment, just before step 3.

| # | Precondition | Check | Expected |
|---|---|---|---|
| P1 | F0017 (the seal tests leave no folders) built and accepted by v1, its acceptance merged and archived; its drafts applied or deliberately parked. F0017 is v1's last work item here. | `git fetch -q origin && git ls-tree --name-only origin/main factory/features/ \| tail -2` and `git ls-tree -r --name-only origin/main factory/features/F0017-the-seal-tests-leave-no-folders/` | `F0017-...` present with `ACCEPTANCE.md`, `FEATURE.md` and `done/` only |
| P2 | No v1 story or acceptance in progress | `git ls-tree -r --name-only origin/main factory/features \| grep -E '/ongoing/'` | no output |
| P3 | No open pull request on factory-rf | `gh pr list --repo pkrahmer/factory-rf --state open` | no output |
| P4 | No v1 branch left on the remote | `git ls-remote --heads origin 'ticket/*' 'acceptance/*'` | no output (a leftover is harmless to v1.1; list it and delete it with the human's OK: `git push origin --delete <branch>`) |
| P5 | v1 is idle: no agent run, no stage between two commits | `cd C:/Dev/Projects/factory && export MSYS_NO_PATHCONV=1 && docker compose exec -T factory sh -c 'ps -eo pid,etime,args \| grep "[c]laude" \|\| echo none'` and `docker compose logs --since 15m factory \| tail -5` | `none`; the log shows only idle ticks |
| P6 | The local checkout is `origin/main`, clean, so that the image is built from accepted code | `git status --short && git rev-parse HEAD origin/main` | no status lines; the two ids equal |
| P7 | Disk | `df -h /c` and `docker system df` | at least 50 GB free on C: (v1.1 stops at 5 GB, `FACTORY_MIN_FREE_GB`; factory-rf's `make test` and `make mutants` are the big writers) |
| P8 | Usage | **[H]** the weekly limit in Claude's usage page (or `/usage` in Claude Code) | below 85 %, so that the first stories do not run into the human's 90 % rule; otherwise wait for the reset (2026-10-20 03:00 UTC) |
| P9 | GitHub settings of factory-rf as v1.1 needs them (v1's guide said "either" for branch deletion; v1.1 needs it off) | `gh api repos/pkrahmer/factory-rf --jq '{merge: .allow_merge_commit, squash: .allow_squash_merge, rebase: .allow_rebase_merge, delete_on_merge: .delete_branch_on_merge}'` | `merge: true, squash: false, rebase: false, delete_on_merge: false`; otherwise **[H]** fixes it in Settings → General → Pull Requests |
| P10 | The two host files the compose file mounts are in place (step 4) | `test -s image/secrets/hosting-token && test -s image/secrets/claude-token && echo both present` (tests the size only, reads nothing) | `both present` |

## 2. The commit, file by file

One commit on `main`, made in the local checkout, subject `Hand factory-rf over to v1.1: pipeline definition and forms, v1's history in factory/v1/`. The session makes it on the human's word **[H-OK]**, as it made the human's changes before.

### 2.1 Moved (with `git mv`, so that history follows)

```bash
mkdir -p factory/v1
git mv factory/stages.yml factory/v1/stages.yml
git mv factory/TICKET.md  factory/v1/TICKET.md
git mv factory/FEATURE.md factory/v1/FEATURE.md
git mv factory/features   factory/v1/features
```

After it `factory/features/` does not exist; v1.1 lists an empty set there (`ls-tree` of a missing path), which is a valid empty board. The first v1.1 feature creates it again.

**Choice: where v1's history goes.**

- (a) **`factory/v1/` — recommended.** Next to where it was, inside `factory/`, which is in no role's write path and already "Not without asking" in `CLAUDE.md`, so no agent edits it; mutmut's `also_copy` already copies `factory/`; the drafting briefs and night-log references stay findable by one prefix. Cost: the two `.secrets.baseline` paths are renamed (2.4).
- (b) `planning/v1-features/`: outside the secrets scan and ruff already, no baseline change; but it mixes finished history with the human's plans, and `planning/` is read by the session as live material.
- (c) Delete (git history only): smallest tree, but the night log, the decision log and the briefs cite `factory/features/F00xx/FEATURE.md` decisions that should stay one click away.
- (d) Leave the folders and rename each `done/` (to `v1-done/`): v1.1 would read 17 empty feature directories (`incomplete`, never due); works, but every v1.1 feature then sits among v1's, and any later reader change could pick them up again.

The parked v1 drafts (`F0003-S0011`, `F0008-S0007`, `F0010-S0025`, `F0011-S0007`) move with their features; none is in progress, and v1.1 reads no `drafts/`. If one is still wanted, it is redrafted in v1.1's form as a new story.

**Feature numbers.** v1.1's first feature is **F0018**, continuing v1's numbers, not a new F0001: the `Makefile`'s `mutants` target finds a feature's modules by the commit subjects `^(ticket|work item) <feature>-S0000:` on `origin/main`, so a v1.1 F0001 would also mutate the modules of v1's ticket F0001 commits. Unique ids also keep the night log and the pull requests unambiguous.

### 2.2 Added: `factory/pipeline.yml`

Exact text. It keeps v1's lanes as write paths (the coder `src/*`, `image/*`, `template/*`, `claude/*`; the tester `tests/*`; the documenter `README.md`, `docs/*`), v1's stages in v1.1's names (`ready` → `intake`, `demo` → `smoke-test`, `accept` → `approval`, `feature` → `acceptance`), v1's caps (`max_attempts: 2` → `attempts_cap: 2`, `max_rounds: 2` → `round_cap: 2`) and v1's project commands with their checks and reports (`duplicates` a report after the coder, `documents` a check of the docs stage).

```yaml
# factory-rf's pipeline definition: v1.1 builds this repository since the handover.
# Its predecessor is v1's stage table, kept as history in factory/v1/stages.yml: the same
# stages, write paths, caps and project commands, in v1.1's names. Every time is in minutes.
contract: "1.0"
attempts_cap: 2             # v1's max_attempts: agent runs that end without a result before the factory asks
crash_cap: 2
acceptance_stage: acceptance
project_commands:
  check: {time_limit: 15}       # the gate; two to five minutes here (pytest on every core)
  lint: {time_limit: 5}
  test: {time_limit: 10}
  duplicates: {time_limit: 5}   # similar and dead code against security/duplicates-baseline.txt, for the reviewer
  documents: {time_limit: 5}    # the four documents against the document check: a check of the docs stage only
# The write paths keep v1's lanes. Every stage's own work item is written by the factory
# (the journal, the state, the cost records); a role names it only when its agent edits the text.
# A role's time_limit plus the time_limits of its stage's checks and reports stay within its lease_duration.
roles:
  intake: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  tester: {write_paths: ["tests/*"], time_limit: 40, lease_duration: 60}
  coder: {write_paths: ["src/*", "image/*", "template/*", "claude/*"], time_limit: 40, lease_duration: 60}
  reviewer: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  documenter: {write_paths: ["README.md", "docs/*"], time_limit: 40, lease_duration: 60}
  smoke-tester: {write_paths: ["{work_item}"], time_limit: 40, lease_duration: 60}
  # make mutants over a feature's modules runs inside this agent run (F0014 and F0016 took 46 to 57 minutes).
  acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"], time_limit: 90, lease_duration: 100}
stages:
  intake: {role: intake, next: [tests]}
  tests: {role: tester, next: [doing], checks: [lint], reports: [test]}     # the new tests are red on purpose
  doing: {role: coder, next: [review, tests], checks: [check], reports: [duplicates]}
  review: {role: reviewer, next: [docs, doing], round_cap: 2}
  docs: {role: documenter, next: [smoke-test, doing], checks: [check, documents], round_cap: 2}
  smoke-test: {role: smoke-tester, next: [approval, doing], round_cap: 2}
  acceptance: {role: acceptance-reviewer, next: [approval]}
  approval: {approval: true, next: [done, doing]}   # the human: a merge accepts, a close sends back
  done: {}
```

Checked on 2026-10-18 with v1.1's own reader, in a temporary folder outside the repository: `RuamelPipelineDefinitionReader().parse` accepts it (every load-time rule: the `done` stage, names, the lease rule, project commands), the stage order is `intake … done` with `intake` first, and `FrontmatterAgentDefinitionReader` over `claude/` finds and reads all seven roles (`acceptance-reviewer`, `coder`, `documenter`, `intake`, `reviewer`, `smoke-tester`, `tester`), so neither `pipeline_definition_invalid` nor `agent_definition_invalid` will stand. The lease sums: tester 40 + 5 + 10 = 55, coder 40 + 15 + 5 = 60, documenter 40 + 15 + 5 = 60, acceptance 90 ≤ 100.

Choices in this file:

- **`round_cap: 2` — recommended** (v1's `max_rounds` on factory-rf, what its stories were sized for), not the template's 3. A third round costs about a story's price; at the cap the factory asks, and the human can grant one more round (F0012's answer at the send-back cap).
- **The acceptance reviewer's `time_limit: 90`, `lease_duration: 100` — recommended.** v1's single `lease_minutes: 60` stalled F0014's second acceptance once and left F0016's 14 minutes of room; in v1.1 the lease is per role, so the longer lease delays only a crashed acceptance's recovery, not every stage's (the reason the human kept v1's global lease at 60). Alternative: 60/60 as before, and the first long acceptance stalls.
- **`check: {time_limit: 15}` — recommended.** factory-rf's `make check` takes more than two minutes on a quiet machine and longer under load (games on the host, mutmut). 15 keeps the coder's and the documenter's sums at exactly 60. If a stall `time_limit` on `check` appears, raise `check` to 20 and both roles' `lease_duration` to 65.
- **The documenter keeps `docs/*` — recommended, as v1's lane, which the brief requires.** Known gap: `docs/*` (with `*` crossing `/`) also covers `docs/runs/`, which `CLAUDE.md` calls the human's and "outside every write path"; v1's lane had the same gap and no agent used it. The alternative, `["README.md", "docs/decisions.md", "docs/operator-guide.md", "docs/project-guide.md"]`, closes it but refuses any new document under `docs/`. Worth deciding with 5a, the write guard.
- `mutants` is not a project command: the engine never runs it; the acceptance reviewer runs `make mutants` in its own shell (`claude/agents/acceptance-reviewer.md`, check 3).

### 2.3 Added: `factory/story-form.md` and `factory/feature-form.md`

`factory/story-form.md` is required: `StoryFormChecker` stops every stage while it is missing (`src/factory/application/task.py`, `STORY_FORM_FILE` at `origin/main`). Its `## ` headings are the required sections (`required_sections`). Exact text, the demo's form with factory-rf's rules:

````markdown
# Story title

A story is one file, `factory/features/<F0018-slug>/backlog/<F0018-S0001-slug>.md`, without front matter. Its first line is its title, `# <what the story builds>`. It has the five sections below, in this order; the factory checks it against this form before a stage moves it forward (`factory-check-story <path>`). The human starts it by moving it to the feature's `in-progress/`; the factory archives it in `done/` when its pull request is merged.

## Description

What the story builds and why, for whom, in a paragraph: what changes, what stays as it is, and what the story leaves to a later one. Every behaviour named here has its own criterion.

## Interface

The modules under `src/factory/` (with their layer: `domain`, `application`, `adapters` or `entry`), the classes and functions the story adds or changes, with their signatures in a code block and their rules as bullets: each rule a sentence a test can check, with every limit on both sides. The test modules the tester writes, mirroring the package under `tests/`. A test another story wrote that this story changes, beyond the standing leave of `CLAUDE.md` (*Tests*), is named here with the leave the feature's `feature.md` gives for it. A change outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`) is the human's, named in `feature.md` under *The human's changes*, never here.

## Acceptance criteria

Numbered 1, 2, 3 and on; each one behaviour a test can check, with its input and its exact result. The sides of one rule (accepted and refused, below and at and above a limit) are one criterion, tested as rows of one parametrized test. The second-to-last criterion is `make check` stays green. The last starts with `docs:` and says what the documenter writes, in which of the four documents (`README.md`, `docs/operator-guide.md`, `docs/project-guide.md`, `docs/decisions.md`), or `none` with the reason.

## Smoke test

Shell blocks the smoke tester runs from the root of the checkout in the container (Linux, nothing listening), each followed by a line `Expect:` that says exactly what the built code prints. A block that needs a file, a repository or a process works in a temporary directory it removes (`d=$(mktemp -d); trap 'rm -rf "$d"' EXIT`) and stops what it started.

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
````

Checked: with this form, v1.1's `factory-check-story` (the real `factory.entry.check_story.main`, in a temporary root) passes a sample `factory/features/F0018-example/backlog/F0018-S0001-example.md` with the five sections, criteria ending in `make check ... green` and `docs:`, and a smoke-test block followed by `Expect:`.

`factory/feature-form.md` — **recommended**, though no code reads it (it is only a protected path, `FEATURE_FORM_FILE`): the drafting agents need a form to write `feature.md` against, and the shipped acceptance reviewer reads `feature.md`'s Goal, Scope and Out of scope (check 1) and its *Decisions taken for the human* (check 6). Exact text:

````markdown
# Feature title

A feature is one directory, `factory/features/<F0018-slug>/`, with this file as `feature.md` and its stories in `backlog/`. The factory reads its title (the first line) for the acceptance; the acceptance reviewer reads the rest. It has the sections below, in this order. The human writes it and keeps it; no stage edits it.

## Goal

Why the feature exists, for whom, and what is different when it is done, in a paragraph. Done when every story below is merged and `make check` is green.

## Scope

- What belongs to it, one bullet each.

## Out of scope

- What does not, so that no story drifts there.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: <title>

## The human's changes

What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`) and a story needs, with the exact lines and the story it must come before; or `None`, with the write paths checked.

## Decisions taken for the human

Numbered; each decision with its reason and where it was taken (a story's text, an answer on a pull request), for the human to confirm in one place. A leave to change a test another story wrote is one of them, naming the test modules.
````

### 2.4 Changed: `.secrets.baseline`

`make secrets` on `main` scans every tracked file, and on a branch the changed ones, against the baseline, whose two results are keyed by path: `factory/features/F0013-podman-and-the-token/done/F0013-S0001-the-token-in-a-folder-only-the-factory-can-enter.md` (and the stale `ongoing/` twin). After the move that file is a new path with a known "Secret Keyword" at line 115. Checked with detect-secrets' own API in a temporary folder: under the old baseline the moved file has **1 new** secret (red `make secrets`, and so a red `make check` on the handover commit and on `main`); with the paths renamed, **0 new**. The change, four occurrences:

```bash
sed -i 's|"factory/features/F0013-podman-and-the-token/|"factory/v1/features/F0013-podman-and-the-token/|g' .secrets.baseline
```

Only the path prefix changes; hash, line number and `generated_at` stay, so the hook does not rewrite the file. No other result in the baseline names `factory/`. (Alternative: leave `factory/v1/` out of the scan in the `Makefile`'s `grep -vE` and the baseline's `should_exclude_file` pattern; two files changed instead of one, and history leaves the scan. Not recommended.)

### 2.5 Changed: `Makefile` (the `mutants` target's feature)

v1.1's acceptance reviewer runs plain `make mutants` (its agent text) on the branch `work-item/F0018-A0001`. Today `FEATURE` is taken only from v1's `acceptance/<id>-<slug>`, so the target would print `mutants: set FEATURE, ...` and exit 2. The `MUTATED` subject grep already matches v1.1's commits (`work item F0018-S0001: doing ends: review`, `commit_subject` in `src/factory/application/handlers/recording.py`). Replace the three comment lines and the `FEATURE ?=` line:

```make
# Mutation testing of the modules under src/factory that one feature's commits changed:
# `make mutants FEATURE=F0012`. Slow, so not part of `check`; the feature acceptance runs it.
# Plain `make mutants` takes the feature from the acceptance's branch: v1.1's
# work-item/<feature id>-A<n>, or v1's acceptance/<feature id>-<slug> (kept for a rollback).
FEATURE ?= $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null | sed -n -e 's|^acceptance/\(F[0-9]\{4\}\)-.*|\1|p' -e 's|^work-item/\(F[0-9]\{4\}\)-A[0-9]\{4\}$$|\1|p')
```

Checked with `make` and the same expression (the branch name echoed in place of `git rev-parse`): `acceptance/F0016-the-shakedown-findings` → `F0016`, `work-item/F0018-A0001` → `F0018`, `work-item/F0018-S0001` → empty (a story's branch is no acceptance), `main` → empty, and `FEATURE=F0019` on the command line still wins. The factory checks out the branch by name (`git switch`), so `--abbrev-ref HEAD` gives the branch. No test reads this recipe. (Not in this commit, for later: the stale test map in `mutants/` that F0014's and F0016's acceptances hit; plan step 7a moves mutants to the story.)

### 2.6 Changed: `CLAUDE.md`

No test reads factory-rf's own `CLAUDE.md` (F0016 change 2 says so; confirmed by search). Five edits:

1. First paragraph, "the pipeline's rules reach every agent as a skill" was v1's mechanism; v1.1's agents get them in their agent files (decision log, the shipped agents' bodies). The paragraph becomes:

   ```
   The second implementation of the factory (github.com/pkrahmer/factory), planned and built by the factory itself: v1.1, v1 reimplemented by v1, and since the handover built by v1.1 itself. The pipeline's rules reach every agent in its instructions (the shipped agent files under `claude/agents/`), so this file holds only what is true of this project. `docs/project-guide.md` is the guide for agents: read it before you change anything.
   ```

   (Keep `github.com/pkrahmer/factory` once: the rename, plan step 9, turns it into `factory-v1`.)
2. `## Language`: `code, comments, docs, tickets, commit messages.` becomes `code, comments, docs, work items, commit messages.`
3. `## Vocabulary`, both bullets replaced by:

   ```
   - `factory/v1/` is v1's history: its stage table, its forms and its features F0001 to F0017, in v1's words. Nothing reads it and no stage writes it; leave it as it is.
   - Everything else, the pipeline's own files under `factory/` included (the pipeline definition, the story and feature forms, the features and their work items), uses the glossary's names: work item, journal, backlog, start, approval, pipeline definition, write paths, project commands, acceptance reviewer, smoke test, error (R3). Stall, lease, crash and `time_limit` keep the meanings the decision log gives them.
   ```
4. F0016's change 2, word for word as `factory/features/F0016-the-shakedown-findings/FEATURE.md` gives it (now under `factory/v1/`): in `## Not without asking (end the stage with `question`)` the words `change to a test you did not write,` become `change to a test you did not write beyond the standing leave under *Tests*,`; and `## Tests` gets as its last bullet, after the one that starts `- Test data and test helpers obey the code already built`, the template's bullet:

   ```
   - The standing leave to move a shared test helper: a helper, constant or fixture that a new test would copy from another story's test module, or that an earlier test module still holds as a copy of a shared one, may be moved to one shared place under `tests/` (a module at its root, or `tests/conftest.py` for a fixture), and the earlier tests that held it changed to use it from there, without asking, as long as every earlier test keeps its name and checks the same thing. The tester makes the move, never the coder, and its entry names each earlier test file it changed. Any other change to a test another story wrote still needs the human's leave.
   ```
5. `## Checks`, in the sentence on `make mutants FEATURE=<feature id>`, after "run by the feature acceptance, never part of `make check`;" insert the words ``on an acceptance's branch, `work-item/<feature id>-A<n>`, plain `make mutants` takes the feature from the branch;`` (so that the acceptance reviewer does not guess the variable).

### 2.7 Not in the commit

- `docs/operator-guide.md`'s *Replaced from v1* bullet "This repository's own `factory/` tree is v1's ... That holds until this repository moves to v1.1's layout." turns stale. It limits itself ("until"), so it misleads no one for a day; **recommended: leave it to the warm-up story (section 5)**, the documenter's file. If the human skips the warm-up, put this text in the commit instead (checked: `check_documents` over the four documents with it prints `documents ok`):

  ```
  - This repository's own v1 history lies in `factory/v1/`: v1's `stages.yml`, `TICKET.md` and `FEATURE.md`, and its features F0001 to F0017 with their `drafts/`, `ongoing/` and `done/` folders and `ACCEPTANCE.md` reports. Nothing reads it, and `factory-check-story` does not apply to it. Since the handover v1.1 builds this repository from `factory/pipeline.yml`, `factory/story-form.md` and the features under `factory/features/`.
  ```
- `src/`, `tests/`, `claude/`, `template/`, `image/`, `pyproject.toml`, `uv.lock`, `README.md`: unchanged. So the image (built from `pyproject.toml`, `uv.lock`, `README.md`, `src`, `claude`, `template`, `image/*`) is the same before and after the commit, and can be built first.

### 2.8 Checking the commit before it is pushed [S]

The world tests do not run on the Windows host (the pre-checker found that), so `make check` runs in a throwaway container of v1.1's own image, on a clone of the local checkout whose `main` holds the commit. There `HEAD` equals `origin/main`, so `make secrets` scans every tracked file, which is exactly what `main` will face:

```bash
cd C:/Dev/Projects/factory-rf
export MSYS_NO_PATHCONV=1
docker run --rm --init -v C:/Dev/Projects/factory-rf:/src:ro --entrypoint bash factory-self-factory \
  -c 'git -c safe.directory="*" clone -q /src /tmp/c && cd /tmp/c && make check && make documents'
```

Expected: the targets' green lines, `check: green`, `documents ok`. It runs as the image's `factory` user, `uv run` installs the dev dependencies into the clone (network), and `--rm` leaves nothing. Then on the host: `uv run factory-check-story` is not needed (no story yet); `git show --stat HEAD` lists exactly the files of 2.1 to 2.6. Push with `git push origin main`.

## 3. The instance

**Name: `self` — recommended.** The compose project becomes `factory-self` (container `factory-self-factory-1`, image `factory-self-factory`, volumes `factory-self_work`, `_state`, `_claude-home`), distinct from v1's `factory` and the demo's `factory-shakedown`. It does not name the repository, so the rename (plan step 9) does not force a new name and so new, empty volumes. (Alternative `rf`: shorter, but wrong after the rename.)

**The hosting token [H].** The compose file mounts one host file, `image/secrets/hosting-token` beside `image/compose.yml`, into every instance started from this checkout; today it holds the shakedown's token for `pkrahmer/factory-demo-todo`. **Recommended: a new fine-grained personal access token for factory-rf alone**, and the shakedown instance stopped (it is idle; the baseline run, step 10, gets a new repository and token anyway):

- github.com → Settings → Developer settings → Fine-grained tokens → Generate new token.
- Resource owner `pkrahmer`; Repository access: *Only select repositories* → `pkrahmer/factory-rf`.
- Repository permissions: **Contents: Read and write**, **Pull requests: Read and write**; **Metadata: Read-only** is added by GitHub. Nothing else: no Administration, no Issues (the factory's comments and labels go through the pull request permission; the shakedown ran with exactly these two), no Workflows (factory-rf has no `.github/workflows/`; a story that adds one would need it).
- An expiry date (90 days suggested).
- Replace the content of `image/secrets/hosting-token` with it, as one line. On Windows the file stays in your own user folder (operator guide, "The hosting-service token"). The session never opens, prints or copies this file; P10 tests only that it is not empty.

(Alternative: add `pkrahmer/factory-rf` to the demo token's repository access, so both instances could run with one file; broader, and its expiry is unknown here.)

**The agent's login [H, only if needed].** `image/secrets/claude-token` (a `claude setup-token` token) is mounted read-only for the user `agent`; the shakedown instance ran on it, and since F0014 the probe passes on the token file alone. Nothing to do unless the preflight's `agent-run-probe` fails naming the login file: then `claude setup-token` on the host, the new token into `image/secrets/claude-token`, and `docker compose ... up -d` again. No interactive `claude` login in the container is needed.

**The commands [S, after step 4 of section 7]:**

```bash
cd C:/Dev/Projects/factory-rf
docker stop factory-shakedown-factory-1          # the idle demo instance; restart: unless-stopped keeps it stopped
export FACTORY_REPOSITORY_URL=https://github.com/pkrahmer/factory-rf.git FACTORY_INSTANCE=self
export FACTORY_IMAGE=$(git rev-parse --short=12 HEAD)
docker compose -f image/compose.yml build        # before the commit (2.8 needs the image)
# ... the commit, its check (2.8), the push ...
docker compose -f image/compose.yml up -d
docker image tag factory-self-factory factory-self-factory:$FACTORY_IMAGE   # the way back for later rebuilds
```

Keep the two `export`s for every compose command of this instance (Compose refuses without them).

**The health check:**

```bash
docker compose -f image/compose.yml ps                                   # STATUS (healthy) after the 60 s start period
docker compose -f image/compose.yml exec factory python -m factory.entry.health   # prints: healthy
docker compose -f image/compose.yml exec factory sh -c 'test -z "${ANTHROPIC_API_KEY:-}" && echo subscription'   # no API key in the instance
```

**What to watch on the first ticks** (expected sequence, each with where it shows):

1. The entrypoint's four lines and `starting instance self` (`docker compose -f image/compose.yml logs --since 10m`).
2. The clone into `/work/checkout`, then the seal; no `cloning the checkout again` after the first clone (`docker compose -f image/compose.yml exec factory tail -n 40 /state/factory.log`).
3. No `repository_unavailable`: `origin/main` holds `factory/pipeline.yml`.
4. The preflight's machine items on the new image, the `agent-run-probe` (`claude -p` as `agent`, a few cents) included; then the probe of `lint` on `origin/main` (the first `uv run` syncs the checkout's `.venv`, a few minutes, inside its 10). Its line in `/state/records/project-commands.jsonl` ends `lint: green (...)`.
5. The pipeline loaded: no `pipeline_definition_invalid`, no `agent_definition_invalid` in `factory.entry.health`.
6. The evaluation is `idle`: `docker compose -f image/compose.yml exec factory factory-watch` shows the event `idle` and an empty board: no feature row, **no `acceptance_due`** (the proof that v1's features are out of sight), no work item.
7. Nothing on GitHub: `gh pr list --repo pkrahmer/factory-rf` empty, `git ls-remote --heads origin 'work-item/*'` empty.
8. The disk record of the start (`/state/records/`), and `healthy` stays over three health intervals.

## 4. v1: how it stops and how it stays the fallback

v1's container serves `REPOS` with exactly one entry (counted inside the container on 2026-10-18 without printing it; its `/work` holds `factory-rf` and run 4's old `factory-demo-todo` checkout). So v1 has nothing else to do, and **stopping its container is the change — recommended** over editing `REPOS` (an empty `REPOS` makes Compose and the entrypoint refuse to start; a placeholder repository would be a fiction):

```bash
cd C:/Dev/Projects/factory
docker compose stop          # SIGTERM; a running tick finishes first (the entrypoint's trap); P5 makes sure none is
docker compose ps -a         # factory-factory-1 Exited (0)
```

It must happen **before the push**: v1's next tick would pull a `main` without `factory/stages.yml` (its entrypoint would then only wait, but the tick between pull and wait is untested territory).

v1 stays the fallback by keeping everything it needs untouched:

- the stopped container `factory-factory-1` and its image `factory` (`stop`, never `down`); `restart: unless-stopped` keeps it stopped across Docker Desktop restarts;
- its volumes `factory_work` (its factory-rf checkout) and `factory_claude-home` (its login);
- `.env` unchanged (`REPOS`, `GH_TOKEN`, the identity; `compose.override.yml` stays `.off`, so no API key);
- **[H]** `GH_TOKEN`'s expiry, looked up on GitHub (Settings → Developer settings → the token), not in the file: it must outlive the fallback period;
- no `docker system prune` / `docker container prune` while v1 is the fallback (it removes stopped containers; `docker compose up -d` would recreate it, but why risk it). The trim-and-compact disk recipe does not touch containers.

Bringing it back is `docker compose start` from `C:/Dev/Projects/factory`, after the revert of section 6; its checkout fetches and fast-forwards `main`, finds `factory/stages.yml` again and ticks.

## 5. The first work item v1.1 builds on itself

How a story starts in v1.1 (the same as the shakedown, now on factory-rf): the session drafts `factory/features/F0018-<slug>/feature.md` and `backlog/F0018-S0001-<slug>.md` against the two new forms (drafting and pre-check briefs as before, but pointing at `factory/story-form.md`, `factory/feature-form.md`, the shipped agents in `claude/agents/` and `factory-check-story`, no longer at `TICKET.md` and v1's skills); `uv run factory-check-story <path>` prints `: ok` for each; commit `F0018: add the feature and its stories`, push; then `mkdir -p factory/features/F0018-<slug>/in-progress && git mv .../backlog/F0018-S0001-<slug>.md .../in-progress/`, commit `F0018-S0001: start`, push. The factory opens `work-item/F0018-S0001` and a draft pull request.

The options:

- **(A) 5a, the write guard by the kernel (Landlock)** — the plan's order (the human's word of 2026-10-17: first after the handover). Probed (ABI 7, `planning/overnight/write-guard-landlock-2026-10-17.md`). Large: a start wrapper for every agent run, the image, the preflight, the guard's cross-check run; several stories. Its effect lands only with a new image, so a fault cannot hurt the running instance; but as the very first self-built work item it mixes two unknowns, factory-rf's suite inside v1.1's container and a new security mechanism.
- **(B) Step 7, skip a project command whose result for that commit is known** — the session's earlier suggestion for a small first story. But the shakedown measured it: 28 `make check`s, each on a different commit, so it saves nothing as worded; the docs stage's `make check` also runs on the documenter's new commit. To save anything it would need "same code, only documents changed", which is a cleverer rule than the gain is worth now. Not recommended as worded.
- **(C) A one-story warm-up, F0018-S0001 "The documents name the handover"** — docs only: the operator guide's stale *Replaced from v1* bullet (2.7), the README's line on how this repository is built, and a decision-log entry for the handover (v1's history in `factory/v1/`, why: decision 008 and the `acceptance_due` the move prevents; feature numbers from F0018; v1 the fallback). Criteria: the three passages say so, `documents ok`, `make check` stays green, `docs:` the three. Cost about $1 (v1's docs-only stories: 6 runs, $0.54 to $0.67). It runs factory-rf's own `make check` through the tests, doing and docs stages inside v1.1's container for the first time, under the 15-minute limit, as the factory user and as `agent`, at the price of a docs story.

**Recommendation: (C) first, then (A) as F0019**, drafted while (C) runs. The first real tick on a repository whose `make check` takes minutes is the handover's real test; if something of the container, the user split or the limits does not fit factory-rf, it should show on a $1 story, not on 5a's first one. The human chooses.

## 6. What can go wrong on the first ticks, how the session sees it, and the way back

| What | Where the session sees it | What to do |
|---|---|---|
| The token cannot reach factory-rf (wrong repository, missing permission, expired) | `repository_unavailable` with `cannot prepare the checkout: ...` in `factory.entry.health`; `hosting-service` in a `preflight_failed` stop | **[H]** fix the token; the next iteration clears the stop |
| The agent's login fails | `preflight_failed` naming `agent-run-probe` and the login file | **[H]** `claude setup-token`, new `image/secrets/claude-token`, `up -d` |
| The pipeline definition or an agent file refused | `pipeline_definition_invalid` / `agent_definition_invalid` with the fault | a human commit to `factory/pipeline.yml` (it was checked with the real reader, so this means the text was changed on the way) |
| `lint` red on `main` | `main_branch_failing` with the last line | a fix on `main` (2.8 should have caught it) |
| v1.1 sees v1's features | `factory-watch` shows `acceptance_due:F00xx` or a feature row; an `acceptance` branch `work-item/F00xx-A0001` appears | stop the instance at once (`docker compose -f image/compose.yml stop`), check the move on `origin/main`; it means a path under `factory/features/` was left |
| `make check` red in the container, not on v1's (user, umask, `sudo`, `/tmp`) | the first story's `doing` stall `a red check`, the tail in the journal, `/state/records/project-commands.jsonl` | a v1.1 story, or a human fix on `main`; if the engine itself is at fault, the rollback below and v1 builds the fix |
| `make check` past 15 minutes | a stall `time_limit` on `check` | **[H]** raise `check` to 20 and the coder's and documenter's `lease_duration` to 65 |
| An agent run past 40 minutes | stall `the agent run reached its time limit` | the story is too big; split it, or raise that role's limit |
| The acceptance past 90 minutes (mutants) | a stall at `acceptance` | resumes from `mutants/`; raise to 120/130 if it recurs; step 7a is the real fix |
| A branch deleted on merge | a merged story starts again at `intake` | P9: "Automatically delete head branches" off |
| A write outside the write paths (`docs/runs/`, `planning/`) | the diff of a stage commit; the undo catches only what the write paths forbid, and `docs/*` allows `docs/runs/` | review at the approval; close with a reason |
| Disk | `disk_low`; the disk records | the trim-and-compact recipe; F0017 keeps `/tmp/pytest-of-*` from growing |
| Usage | the weekly limit at 90 % | pause new stories (the human's rule); nothing stops by itself before the limit |

How the session watches, every few minutes while a work item runs: `factory.entry.health`, `factory-watch`, `tail /state/factory.log`, `gh pr list` / `gh pr view <n> --comments`, and a night-log row per event, as in the shakedown.

**The rollback [H-OK].** It is needed only if v1.1 cannot build factory-rf at all, or a fault of the engine needs a fix v1.1 cannot make. In order:

1. Stop v1.1: `docker compose -f image/compose.yml stop` (with the two exports); keep its volumes for the evidence.
2. Leave or close v1.1's open pull requests (v1 ignores `work-item/` branches); a story in `in-progress/` stays v1.1's.
3. One revert commit on `main`: `git revert --no-commit <handover commit>`; if v1.1 has added features meanwhile, move them out of v1's sight in the same commit (`mkdir -p factory/v1.1 && git mv factory/features/F0018-<slug> factory/v1.1/features/F0018-<slug>` for each), because v1 would otherwise see a feature folder of another form; then `git commit -m "Roll the handover back: v1 builds factory-rf again"` and push. Nothing else touches the reverted files (all are protected or outside every write path), so the revert has no conflict unless the human changed them by hand.
4. Start v1: `cd C:/Dev/Projects/factory && docker compose start`; its log shows the pull and idle ticks.
5. To hand over again, revert the revert (and move `factory/v1.1/features/*` back) once the fix is merged; the preconditions of section 1 apply again.

For a later self-built image that misbehaves, the way back is the previous tag: `docker image tag factory-self-factory:<previous commit> factory-self-factory && docker compose -f image/compose.yml up -d` (no `--build`). So tag every image before a rebuild, as in section 3.

## 7. What the human does, in order

1. **[H]** Read this plan; choose: v1's history place (rec. `factory/v1/`), the feature form (rec. yes), `round_cap` 2, the acceptance's 90/100, the documenter's `docs/*` (rec. keep), the instance name (rec. `self`), the token (rec. new, factory-rf only), the first work item (rec. (C) then (A)).
2. **[H]** Wait for F0017 to be accepted by v1 (P1); confirm the usage (P8).
3. **[H]** Check or fix factory-rf's pull request settings (P9): merge commits on, squash and rebase off, automatically delete head branches **off**. Optional: a ruleset `work-items` for `work-item/**` with *Block force pushes* and *Restrict deletions* unchecked (the factory deletes those branches).
4. **[H]** Make the new fine-grained token (section 3) and put it into `image/secrets/hosting-token`; look up the expiry of v1's `GH_TOKEN`.
5. **[H]** Give the word for the session's steps: stop v1 and the shakedown instance, build the image, make, check and push the commit, start `self`.
6. **[S]** Preconditions P1 to P7 and P10; stop v1 (section 4) and the shakedown instance; build the image; the commit (section 2), its check (2.8), the push; `up -d`; the health check and the first ticks (section 3), each in the night log.
7. **[H]** Approve the first work item's drafts after their pre-check; the session starts it. Merge or close its pull request at the approval, as with every story.
8. **[H]** Later, after a few clean self-built stories: the rename (plan step 9) and, only then, retiring v1's container.
