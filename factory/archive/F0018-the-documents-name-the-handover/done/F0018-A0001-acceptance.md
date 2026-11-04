---
stage: done
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 217
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-18T12:53:24.988465Z'
  stage: acceptance
- number: 2
  speaker: acceptance-reviewer
  kind: result
  at: '2026-10-18T12:57:29.238152Z'
  stage: acceptance
  run: 0831282e309e4b1aab8b7133cbe3dd4d
- number: 3
  speaker: factory
  kind: done
  at: '2026-10-18T12:58:14.493265Z'
  stage: done
stories: [F0018-S0001]
outcome: accepted
---

# Acceptance of The documents name the handover

## Recommendation

**Accepted with stories.** All three Scope items are built and true: the README's opening and *How it is built*, the operator guide's `factory/` bullet, and the decision-log entry. The feature smoke test is green, and `make check` is green inside v1.1's own container, which was the feature's second purpose. The Goal also promises true documents "for the agents", and two passages outside the Scope still say that v1's configuration runs this repository: `docs/project-guide.md` (*The document check*) and `docs/decisions.md` (*Three top-level paths*). Neither misleads an operator or contradicts behaviour a user relies on. S0002 proposes the repair.

## 1 Scope

One story, S0001, covers all three Scope items. Commit `7f624592` (the merge of #216) changes `README.md` (lines 3 and 26), `docs/operator-guide.md` (line 1162) and `docs/decisions.md` (new last entry, line 545). It also changes the `Makefile` (the human's umask fix `27bdaa73`, merged from `main`) and the human's night log. Nothing under `src/`, `tests/`, `image/`, `template/`, `claude/` or `factory/v1/` changed, so the Out of scope holds.

One small change goes beyond the literal Scope: the documenter also corrected the operator guide's intro (line 3), which had the same "first observed at the shakedown run" sentence as the README. The new text agrees with the README, and I count it as within the Goal.

Goal gap: the Goal says the documents become true "for the newcomer, the operator and the agents". `docs/project-guide.md:1710` still says "v1's pipeline configuration for this repository runs it as a check of the docs stage through `make documents`"; since the handover that is `factory/pipeline.yml` (`docs: checks: [check, documents]`). `docs/decisions.md:11` still says "The coder's write paths in `factory/stages.yml` name them"; that file now lies in `factory/v1/`, and the coder's write paths are in `factory/pipeline.yml:20`. The documenter's entry 14 recorded `docs/project-guide.md` as "cross-read and found current", so this was missed, not left on purpose. Proposed as S0002.

## 2 Feature smoke test

The feature's purpose, end to end: what a newcomer and an operator now read, checked against the tree and the real commands (`factory-check-story`, `check_documents`). The script ran from a `mktemp -d` folder that removes itself, with the checkout as the working directory: `bash "$d/smoke.sh"`.

```
## 1 the README and the operator guide name the handover
1        # "until the handover of 2026-10-18 and is built by v1.1 itself" in README.md
0        # "shakedown" in README.md
1        # "Since the handover of 2026-10-18, v1.1's instance builds this repository from `factory/pipeline.yml`"
1        # "This repository's v1 history lies in `factory/v1/`" in docs/operator-guide.md
## 2 the tree is what they describe
feature-form.md features pipeline.yml story-form.md v1        # ls factory
FEATURE.md TICKET.md features stages.yml                       # ls factory/v1
17                                                             # v1's features F0001 to F0017
## 3 v1.1 builds from it: the story form checks the archived story
factory/features/F0018-the-documents-name-the-handover/done/F0018-S0001-the-documents-name-the-handover.md: ok
exit 0
## 4 nothing reads factory/v1 and factory-check-story does not apply to it
factory/v1/features/F0001-boundaries/done/F0001-S0001-kill-points.md: not a work item location: expected factory/features/<feature>/<backlog|in-progress|done>/<file>.md
exit 1
0        # grep -rn "factory/v1" src/ | wc -l
## 5 the decision log has the entry, last
545:## factory-rf is built by v1.1 since the handover
## 6 the document check
documents ok
exit 0
## 7 what the agents' guide says about this repository's pipeline
1710:v1's pipeline configuration for this repository runs it as a check of the docs stage through `make documents`, so a
11:`image/` (Dockerfile, compose file, entrypoint), `template/` (v1.1's own project template) and `claude/` (the agent and skill files v1.1
```

(The `ls` lines are joined, and the `#` notes added, for reading. The output is otherwise as printed.)

Steps 1 to 6 are green: every claim the feature made holds, and `factory-check-story` accepts v1.1's layout and refuses v1's location. That replaces the old bullet's `cannot read factory/story-form.md`. Step 7 shows the two stale passages of check 1.

`make check`, as I found it (umask `0002` in this stage's shell): `test: green (38.3 s)`, total coverage 99.44 %, `check: green`.

## 3 Mutation score

```
$ make mutants
mutants: no module under src/factory changed by F0018
```

No mutants: the feature changed no module under `src/factory`, so there is no score (0/0) and no survivors.

## 4 What the stories noticed

- Documenter (entry 14): wording that still says something is observed only at the shakedown run. It appears at `docs/decisions.md:462` ("Observed only at the shakedown run: the tests cannot be a second user"), `docs/decisions.md:504` ("the reaping is a morning observation of the shakedown") and `docs/operator-guide.md:259` ("Under Podman this is first observed at the shakedown"). The decision log's own later entries (lines 508, 516, 523) date the shakedown to 2026-10-18 on the todo demo. Whether the second user, the reaping and the Podman init were actually observed there is the human's fact, not one I can find in the repository. So these passages are not in S0002; see 6, item 6.
- Smoke-tester (entry 16) repeated the documenter's two open points: the inferred *Rejected* line (6, item 4) and the shakedown wording above.
- Coder (entry 10) and reviewer (entry 12): nothing noticed.
- The coder's first run (entry 7) found the real fault of this feature: `make check` was red inside v1.1's container because of umask `0002`. The human fixed it on `main` (`27bdaa73`). That is owned and closed.

## 5 The documentation as a whole

I read `README.md`, the operator guide's intro and *Replaced from v1*, the project guide's references to this repository, and the decision log's handover entry, as a newcomer would. README and operator guide now agree with each other and with the tree. The handover is explained once at length (decisions) and briefly in two places (README, operator guide), and those three places do not contradict each other.

Contradictions left behind:
- `docs/project-guide.md:1710` against `factory/pipeline.yml:31`.
- `docs/decisions.md:11` against the moved `factory/stages.yml`.

The examples in the operator guide's `factory-check-story` section (line 741 on) now hold for this repository too: step 3 of the smoke test runs one on a real story. No section is missing.

## 6 Decisions taken for the human

1. The first work item v1.1 builds on itself is this documentation story, before 5a (the write guard): the human's choice on the handover plan, option C. (`feature.md`, decision 1)
2. v1's history stays in `factory/v1/`, and v1.1's features continue from F0018 because `make mutants` finds modules by the feature id in commit subjects. (`feature.md`, decision 2)
3. The human's answer to the coder's question (S0001 entry 8): neither running the factory under umask 022 nor forcing the item forward. Instead, `make test` and `make mutants` run pytest under `umask 022` (`27bdaa73` on `main`), and the seal's refusal of a group-writable checkout stays as it is.
4. The documenter's *Rejected* bullet in the new decision-log entry ("leaving v1's features in place ...; restarting the numbers at F0001 ...", `docs/decisions.md`, last line). The documenter inferred it from the stated reasons; the human did not say it. Accept it or reword it.
5. The documenter wrote "its stages" in the README's *How it is built*, not "stage table" or `stages.yml`, because `check_documents` refuses those v1 words in the README. The operator guide's bullet names `stages.yml`, which sits under *Replaced from v1*, where v1 words are allowed.
6. Open for the human: whether the shakedown of 2026-10-18 observed the second user, the reaping and the Podman init (4, first item). If yes, a docs story like S0002 can date those passages; if no, they stay true as they are.

Earlier tests changed: none. Reviewer entry 12 says "Earlier tests: none", and `git diff 26d9c43b..7f624592 -- tests` is empty.

## 7 The slow checks

The project offers nothing beyond `make check`, `make mutants`, `make duplicates` and `make documents`: no image scan and no SBOM target. `make duplicates` (coder entry 10): `0 new, 39 known, 0 gone`. `make documents`: `documents ok`.

Disk: now `/work 0.4 GB used` (985.6 GB free), against `disk start: /work 0.0 GB used` (986.9 GB free); `/state` and `/tmp` are 0.0 GB at both. The growth is the instance's own checkout since its start (`/work/checkout` 496 MB: `.venv` 449 MB, `.mypy_cache` 19 MB, `.git` 9.4 MB, `.reports` 0.9 MB), not the feature, which changed four documents. The free-space drop of 1.3 GB is larger than `/work`'s growth, so other users of the shared volume took the rest. My `make check` left pytest's retained folders, 114 MB in `/tmp/pytest-of-agent` (pytest keeps the last three sessions). This stage's permissions refused my attempt to delete them, so they are still there; they come from the check, not from the feature.

Slowest tests (from `.reports/junit.xml`; 4726 tests, 372 s summed over the workers, 38.3 s wall clock):
- `tests/adapters/test_claude_runtime_resume.py::test_model_duration_of_a_resumed_run_adds_the_known_calls[resume ended by the time limit]`: 5.0 s
- `tests/test_fault_paths_7_to_13.py::test_acceptance_container_lost_in_review_reruns_once_and_books_result`: 3.3 s and 3.1 s
- `tests/adapters/test_process.py::test_grandchild_is_killed_with_the_child_at_the_time_limit`: 3.0 s
- `tests/adapters/test_make_commands.py::test_command_reaching_its_time_limit_is_killed`: 3.0 s

All of these wait for time limits by design.

## 8 Cost

7 runs, 4.4 min, 37 turns, $1.10, below F0017-S0001's $1.55 for six runs. The seventh run is the coder's question: the first doing run (`e7c5560f`, 116.5 s wall clock against 31 s of model time, $0.23) ran `make check`, found it red under umask 0002, and asked (entry 7). The second doing run, after the human's fix, cost $0.06. That question was worth its price: it found the first real fault of v1.1's container on factory-rf. The smoke-tester's run ($0.23) and the tester's ($0.17) are high for a docs-only story, because each read the whole story and its criteria. The reviewer's run is about the same price ($0.17 for 3 turns), and most of that is cache creation (19k tokens). Nothing else stands out.

## Proposed stories

- `F0018-S0002-the-agents-guide-names-the-pipeline-definition.md`: repairs the two passages that still say v1's configuration runs this repository (`docs/project-guide.md:1710`, `docs/decisions.md:11`), so the Goal's "for the agents" holds. Docs only, one documenter run.

## Journal

1. factory: started acceptance as self.
2. acceptance-reviewer: accepted with stories; 1 story proposed; make mutants 0/0
   1 Scope: all three Scope items are built, and the Out of scope holds. Goal gap: the Goal promises true documents "for the agents", but `docs/project-guide.md:1710` ("v1's pipeline configuration for this repository") and `docs/decisions.md:11` (`factory/stages.yml`) still describe the time before the handover. Proposed as S0002.
   2 Feature smoke test: green. The README and operator-guide claims hold against the tree, `factory-check-story` accepts the archived story and refuses a `factory/v1/` path, `src/` never reads `factory/v1`, and the decision entry is last with `documents ok`. Its last step shows the two stale passages. `make check` was green as I found it (umask 0002, coverage 99.44 %).
   3 Mutation score: `mutants: no module under src/factory changed by F0018`, so there are no mutants and no survivors.
   4 Noticed: the documenter's stale "observed at the shakedown" wording (`decisions.md:462`, `:504`, `operator-guide.md:259`) depends on facts only the human knows and is listed for them, not proposed. The coder's umask fault was fixed on main (`27bdaa73`).
   5 Documentation: README and operator guide agree with each other and with the tree. The only contradictions left are the two passages under 1.
   6 Decisions for the human: feature decisions 1 and 2; the umask answer (`27bdaa73`, the seal stays); the documenter's inferred *Rejected* bullet in the new decision entry; "its stages" chosen to pass `check_documents`; the open shakedown question. No earlier test was changed.
   7 Slow checks: none beyond the make targets; `duplicates` 0 new. `/work` grew 0.0 to 0.4 GB, which is the instance's checkout and `.venv` (496 MB), not the feature. The 114 MB of pytest folders in `/tmp/pytest-of-agent` from my `make check` remain, because the stage's permissions refused their deletion. Slowest test: the resume time-limit test, 5.0 s.
   8 Cost: 7 runs, $1.10. The extra run is the coder's question (116 s, $0.23) that found the umask fault. Worth it; nothing else stands out.
3. factory: done (pull request merged); cost: 1 runs, 4.0 min, 26 turns, 63776 tokens in (1066692 more from cache), 14140 out, $1.01
