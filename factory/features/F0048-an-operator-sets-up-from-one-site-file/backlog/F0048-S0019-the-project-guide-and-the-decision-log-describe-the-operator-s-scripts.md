# The project guide and the decision log describe the operator's scripts

<!-- proposed by feature acceptance of 2026-11-03; refine before starting -->

## Description

F0048 added `operator/`: the site loader (`operator/bin/site`, `operator/lib/site.sh`), the hosting client (`operator/lib/hosting.sh`), `operator/job/job.sh`, the sanitiser (`operator/bin/sanitise`) and the skill's scripts under `operator/skill/kumpel/scripts/`. It also added twelve test modules `tests/test_operator_*.py` with their support modules. The operator guide describes all of this for the operator. The agents' documents do not, because no story's docs criterion named them for `operator/`. The project guide (`docs/project-guide/`) has no file for this domain, and its index names no file under `operator/`. So an agent whose story touches the scripts finds no domain file to read first, which is what `CLAUDE.md` tells it to do. The index's list of support modules ("Every module `tests/*.py` whose name does not start with `test_`") misses ten modules. Five of them are this feature's: `operator_support.py`, `operator_job_support.py`, `operator_skill_support.py`, `site_check_support.py` and `scripted_tick_support.py`. Five are older: `command_words_support.py`, `container_extra_support.py`, `opencode_provider_support.py`, `power_support.py` and `token_support.py`. A tester who looks there for a helper does not find them, and the feature already holds copies made that way (`gcloud_words` beside `words`, and `JOB` and `IMPERSONATE` defined twice). The decision log (`docs/decisions.md`) has entries for the feature's code-side decisions (10, 13, 15, 17, 20, 23 and the `-I` rule) but none for the site file's design (decisions 1 to 9, 11, 12 and 14 of `feature.md`), the died line (19) or the job's one image (24). Their reasons live only in an archived `feature.md`. This story writes those documents. It changes no code and no test; the copied test helpers stay as they are.

## Interface

None. The documenter writes `docs/project-guide/operator.md` (new), `docs/project-guide/README.md` and `docs/decisions.md`. No module under `src/factory/`, no script under `operator/` or `vm/` and no test changes.

## Acceptance criteria

1. `make check` stays green.
2. docs:
   - `docs/project-guide/operator.md`, new: a title, a sentence on what it covers, and sections for the following. Each describes what the scripts do today, with the paths and the names of the functions. *The layout*: the files under `operator/`, and that `operator/README.md` is the documenter's (decision 22). *The site file and its loader*: values stored literally, never executed; a file in a git work tree refused; only `SITE_` keys; the environment wins; status 1, 2 and 3; the folders `~/.config/kumpel/` and `~/.local/state/kumpel/`. *The hosting client*: `hosting_token`, `hosting_api` and `hosting_git`; `SITE_TOKEN_CMD` with `gh auth token` as the fallback; the token never in an argument list (curl's configuration on standard input, `GIT_CONFIG_*` for git). *`job.sh`*: its commands, the state file, the start script taken from `SITE_CODE_REF` with `git show`, no guessed values, no two executions at once. *The sanitiser*: the site's rules file and the leak check. *The skill's scripts*: every `python3` started with `-I`, each hosting read assigned to a variable before it is parsed, and comments posted only through `comment.sh` with the signature and the marker. *Tests of the scripts*: stand-ins on the `PATH` for `gcloud`, `gh` and `curl`; the real `git` with a local bare repository; the support modules that hold them, and the test modules by script.
   - `docs/project-guide/README.md`: a line for `operator.md` under *The files*. Under "Every module `tests/*.py` whose name does not start with `test_`", one line for each of the ten modules named in the Description, each saying what it holds, read from the module.
   - `docs/decisions.md`: one entry each, with date, decision, why and what was rejected (taken from the stories' journals where they name it), for:
     - the site file is data and lies outside every repository (decisions 1, 2, 3 and 11);
     - the hosting token comes from a command the site names and is never in an argument list (decisions 4, 5 and 14);
     - `job.sh` works from the site's values alone, never guesses, never overlaps, and runs the start script of the code it clones (decisions 6, 7 and 12);
     - a reset to a tag needs three things (decision 8);
     - the sanitiser's rules are the site's (decision 9);
     - a run that dies leaves its text in the factory log (decision 19);
     - the job keeps one image in memory, and a machine prunes after a rebuild (decision 24).
   - `README.md` and `docs/operator-guide.md`: none, because they already describe the scripts for the operator. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
test -f docs/project-guide/operator.md && echo present; grep -c '`operator.md`' docs/project-guide/README.md
```
Expect: `present`, then a number of at least `1`

```bash
for m in command_words_support.py container_extra_support.py opencode_provider_support.py operator_job_support.py operator_skill_support.py operator_support.py power_support.py scripted_tick_support.py site_check_support.py token_support.py; do grep -q "\`$m\`" docs/project-guide/README.md || echo "missing $m"; done; echo listed
```
Expect: `listed` alone, with no `missing` line before it

```bash
grep -c -i 'site file' docs/decisions.md; grep -c -- '--layers=false' docs/decisions.md; grep -c 'SITE_TOKEN_CMD' docs/decisions.md
```
Expect: three numbers, each at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
