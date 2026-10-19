# Mutation testing per story

## Goal

`make mutants` runs today only at a feature's acceptance, over every module the feature's stories changed, inside the acceptance reviewer's agent run. That does not fit a large feature: the agent's shell tool ends a command after 10 minutes, so the target stops mutmut after 540 s. F0012's acceptance had about 12,000 mutants. F0019's three acceptances and F0021's one each ended partial (F0021: 2,806 of about 5,750 mutants checked in three runs of 540 s). Measured first (2026-10-19, `main` at 1149c3a0), from the archived stories of F0019 and F0021, the mutmut 3.8 cache that the acceptances left in v1.1's checkout (`mutants/`, read-only), and one run in a throwaway container of v1.1's image. Of the 18 stories, 6 changed no module under `src/factory`. The other 12 changed 1 to 8 modules, with 49 to 2,056 mutants (median about 850). One run costs a fixed 165 s (28 s listing the tests, 131 s of mutmut's clean test run, 5 s generating), plus 0.13 to 0.25 s of wall time per mutant on 20 cores. The lower rate is F0021's acceptance: 2,806 mutants, 5,969 worker-seconds. The higher one is the container run of F0021-S0002's seven modules: 1,718 of 1,858 mutants in 436 s, 7,848 worker-seconds, beside the live factory's `make check`. So a story costs 3 to 11.5 minutes. Eight of the twelve fit in 540 s. Four would end partial: F0021-S0001 (2,056 mutants) and F0021-S0002 (1,858; at 600 s the container run had 140 left) by their size, and F0019-S0002 and F0019-S0003 by slow mutants in `process.py`, `pipeline_definition.py` and the write-path modules, which run most of the suite each. The measurement also showed why the acceptances' second and third runs got no further: mutmut 3.8 runs again every mutant that a name or a pattern selects, cached result or not, fastest first. So `CLAUDE.md`'s "a second run goes on from the results kept in `mutants/`" does not hold, and a run stopped at its limit reaches the same mutants every time. This feature makes mutation testing a record per story. The factory runs `make mutants` as a report after the coder, beside `duplicates`, with a time limit of its own, over the modules the story's branch changes. The reviewer reads the story's survivors while the story is still open. The acceptance re-runs, by name, only the mutants that the stories left not killed, against the final code. Each run shortens that list, so the acceptance's runs do go on. A partial result is recorded as partial (its own last line, exit status 1, a failed report), never as a pass, and a report never fails a stage. The engine learns no target name and no stage name. It gains one generic rule: the journal line of a report stopped at its time limit says so. It is for the operator and the human, who see untested code while its story is open instead of at the end of a feature, and for the acceptance, which reads a complete score. Done when every story below is merged and `make check` is green. The real check is the human's change 3 after the feature: one ordinary story of factory-rf whose coder entry carries a `mutants` line.

## Scope

- `src/factory/domain/mutants.py` (new): `MutantResult`, `parse_results`, `MutationReport`, `mutation_report`, `rerun_names` (S0001).
- `src/factory/entry/check_mutants.py` (new): the command `python -m factory.entry.check_mutants` that the human's `mutants` recipe calls (S0001).
- `src/factory/entry/inputs.py` (new): `read_input` and `UnreadableInput`, moved out of `check_duplicates` so that both commands read their files one way (S0001).
- `src/factory/entry/check_duplicates.py`: reads its inputs through `read_input`, with unchanged behaviour (S0001).
- `src/factory/domain/checks.py`: `command_line` (F0023-S0002's) says when a command was stopped at its time limit (S0002).
- `claude/agents/reviewer.md`: the reviewer reads the story's surviving mutants (S0003).
- `claude/agents/acceptance-reviewer.md`: the acceptance reviewer runs `make mutants` again while it is partial (S0003).
- The tests each story names, under `tests/`.
- `docs/operator-guide.md`, `docs/project-guide/` and `docs/decisions.md`, from each story's docs criterion.

## Out of scope

- The template's and the demos' `Makefile` and pipeline definitions: they keep the feature-level `mutants` target of today (decision 12). A project opts in after the real check on factory-rf.
- A status of its own for a partial result: `CheckStatus` stays `passed`, `failed` and `time_limit`, judged by the exit status alone (decision 3).
- A gentler stop at a command's time limit (a TERM before the KILL in `factory.adapters.process`): the recipe stops mutmut itself before the report's limit (decision 4).
- Running only the mutants of the functions a story changed: mutmut 3.8 resets those results only while it runs, after the names would have been chosen (decision 2).
- A report's whole output in the journal or in a file of the factory's: only the last line reaches the journal, as today. The reviewer lists the survivors from mutmut's own results (decision 6).
- Raising a lease or the coder's `time_limit`: the plan says the leases stay. The room comes from `check` and `duplicates` (decision 5).
- Every paid call: no story and no smoke test makes one; the real check is the human's change 3.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: `check_mutants` reports a mutation run of chosen modules and names what is left to run
- S0002: A report stopped at its time limit says so in its journal line
- S0003: The reviewer reads the story's surviving mutants, and the acceptance reviewer runs the report until it is complete

## The human's changes

Checked against `factory/pipeline.yml`: the coder writes `src/*`, `image/*`, `template/*` and `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. All three stories stay inside those write paths; the agent texts under `claude/agents/` are the coder's. No new dependency (mutmut is already a development dependency), no `.secrets.baseline` entry, no `security/` change, no suppression marker. No story adds a structural test that reads the source, so `[tool.mutmut]` in `pyproject.toml` stays as it is. What the feature needs outside the write paths is the `Makefile`, `CLAUDE.md`, `factory/pipeline.yml` and one change of permissions in the running container:

1. After S0001 is merged and before S0003 starts (the recipe calls `python -m factory.entry.check_mutants`, and S0003's reviewer text points to the `CLAUDE.md` lines below), one commit on `main`.
   - In the `Makefile`, everything from the comment line `# Mutation testing of the modules under src/factory that one feature's commits changed:` to the end of the `mutants` recipe becomes:

     ```make
     # Mutation testing (mutmut) of the modules under src/factory that one story or one feature changed.
     # Slow, so not part of `check`. On a story's branch, work-item/<story id>, it mutates the modules
     # the branch changes against origin/main, the work tree included: the factory runs it as a report
     # after the coder. With FEATURE=<feature id>, or on an acceptance's branch (v1.1's
     # work-item/<feature id>-A<n>, or v1's acceptance/<feature id>-<slug>, kept for a rollback), it
     # re-runs, of the modules the feature's story commits changed, only the mutants that are not
     # killed: what the stories left, against the final code.
     BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null)
     FEATURE ?= $(shell echo '$(BRANCH)' | sed -n -e 's|^acceptance/\(F[0-9]\{4\}\)-.*|\1|p' -e 's|^work-item/\(F[0-9]\{4\}\)-A[0-9]\{4\}$$|\1|p')
     STORY := $(shell echo '$(BRANCH)' | sed -n 's|^work-item/\(F[0-9]\{4\}-S[0-9]\{4\}\)$$|\1|p')
     MUTANTS_SECONDS ?= 540
     FEATURE_MODULES = $(shell git log --format= --name-only -E --grep='^(ticket|work item) $(FEATURE)-S[0-9]{4}:' origin/main -- 'src/factory/*.py' | sort -u)
     STORY_MODULES = $(shell { git diff --name-only $$(git merge-base origin/main HEAD) -- 'src/factory/*.py'; git ls-files --others --exclude-standard -- 'src/factory/*.py'; } | sort -u)
     MUTATED = $(wildcard $(if $(FEATURE),$(FEATURE_MODULES),$(STORY_MODULES)))
     MODULES = $(foreach module,$(MUTATED),$(subst /,.,$(patsubst src/%.py,%,$(module))))
     mutants:
     	if [ -z "$(FEATURE)$(STORY)" ]; then echo "mutants: set FEATURE, as in make mutants FEATURE=F0012, or run it on a story's branch"; exit 2; fi
     	if [ -z "$(MUTATED)" ]; then echo "mutants: no module under src/factory changed by $(or $(FEATURE),$(STORY))"; exit 0; fi
     	# mutmut stops a mutant's pytest at its time limit, which leaves that run's folder locked for
     	# three days under pytest's root in /tmp: give each run a root of its own and remove it after.
     	temporary=$$(mktemp -d)
     	umask 022   # as for make test: the seal refuses a group-writable checkout
     	# A mutant that drops a working folder can make a test's repository in mutants/ itself; the
     	# factory cannot remove the agent's folder there and stops, so the run removes it. mutants/ is
     	# written by the factory's report and by the acceptance reviewer, two users of one group.
     	trap 'chmod -R u+rwX "$$temporary" 2>/dev/null || true; rm -rf "$$temporary" || true; find mutants -name .git -prune -exec rm -rf {} + 2>/dev/null || true; chmod -R g+w mutants 2>/dev/null || true' EXIT
     	set -f   # the names below are mutmut's patterns, never file names
     	# mutmut runs again every mutant a name selects: a story's run takes all of its modules'
     	# mutants; a feature's run takes only those not killed, so each of its runs goes on.
     	if [ -n "$(FEATURE)" ]; then
     	  uv run mutmut results --all true > "$$temporary/results.txt"
     	  names=$$(uv run python -m factory.entry.check_mutants --names "$$temporary/results.txt" $(MODULES))
     	else
     	  names="$(foreach module,$(MODULES),$(module).*)"
     	fi
     	# An agent's shell command ends after 10 minutes and the report's limit is 10 minutes: stop
     	# mutmut before both, so that this recipe ends itself and says what it reached.
     	stopped=""
     	if [ -n "$$names" ]; then
     	  TMPDIR="$$temporary" timeout $(MUTANTS_SECONDS) uv run mutmut run $$names || { status=$$?; [ $$status -eq 124 ] || exit $$status; stopped="--stopped-after $(MUTANTS_SECONDS)"; }
     	fi
     	uv run mutmut results --all true > "$$temporary/results.txt"
     	uv run python -m factory.entry.check_mutants $$stopped "$$temporary/results.txt" $(MODULES)
     ```

     The names go through the shell (`$$(...)`), not through make's `$(shell ...)`, because a feature's list can be long and one line of a recipe is a single argument to bash. With no name left (every mutant of the feature's modules killed) the run is skipped, because `mutmut run` without a name would run every unchecked mutant of the whole package. The two `uv run mutmut results` calls read `mutants/` only.
   - In `CLAUDE.md`, *Checks*, in the bullet on `make lint` and `make test`, the part from `` `make mutants FEATURE=<feature id>` runs mutmut `` up to `which read the source it rewrites.` becomes:

     ```markdown
     `make mutants` runs mutmut and is never part of `make check`. On a story's branch, `work-item/<story id>`, it mutates every module under `src/factory` that the branch changes against `origin/main`, the work tree included: the factory runs it as a report after the coder (`mutants` in `factory/pipeline.yml`), and the coder does not run it. With `FEATURE=<feature id>`, or on an acceptance's branch, `work-item/<feature id>-A<n>`, it re-runs, of the modules the feature's story commits changed, only the mutants that are not killed: what the stories left, against the final code. It stops mutmut after `MUTANTS_SECONDS` (540 s, inside the shell tool's 10 minutes and the report's 10-minute limit). Its last line is `check_mutants`'s: `mutants: <k> killed, <s> survived, ...`, or `mutants: partial, ...` with exit status 1 while a mutant of those modules is not checked; a partial result is never a pass. mutmut runs again every mutant a name selects, so a stopped story's run starts over, while each acceptance run shortens its list. List the survivors of one module with `uv run mutmut results | grep -F 'factory.application.stage.'` and read one with `uv run mutmut show <name>`. mutmut leaves out the structural tests listed in `pyproject.toml`, which read the source it rewrites.
     ```

   - Before the next run of `make mutants` by the factory (the earliest is change 2), the files the acceptances left in `mutants/` are the agent's and not writable by the group (`mutmut-stats.json` is `-rw-r--r--`). The factory's report would fail to write them. Once, on the host: `MSYS_NO_PATHCONV=1 docker exec -u root factory-self-factory-1 chmod -R g+w /work/checkout/mutants`. That keeps the cache (its tests' durations and its results). Removing `mutants/` instead would cost one cold run of about three more minutes.

2. After S0002 and S0003 are merged and `self` is rebuilt (S0002's journal line and S0003's agent texts reach the running factory only through the image), one commit on `main`, `factory/pipeline.yml`, after F0023's change 1:
   - In `project_commands`, `check`'s `time_limit: 15` becomes `time_limit: 8`; its `not_read` stays as F0023's change 1 left it.
   - The `duplicates` line becomes, and right after it comes one new line:

     ```yaml
       duplicates: {time_limit: 2}   # similar and dead code against security/duplicates-baseline.txt, for the reviewer
       mutants: {time_limit: 10}     # mutmut over the modules a story changes, for the reviewer; it stops itself after 540 s
     ```

   - The `doing` stage becomes:

     ```yaml
       doing: {role: coder, next: [review, tests], checks: [check], reports: [duplicates, mutants]}
     ```

   - The comment above `acceptance-reviewer` becomes:

     ```yaml
       # make mutants re-runs, inside this agent run, the mutants the stories' reports left not killed.
     ```

   The leases: doing 40 + 8 + 2 + 10 = 60 of 60; docs 40 + 8 + 3 + 2 = 53 of 60; tests unchanged at 55. `check` took 47.2 s on average and 91.4 s at most in 59 factory runs (`/state/records/project-commands.jsonl`, 2026-10-19), `duplicates` 3.1 s and 4.6 s at most in 36 runs, so 8 and 2 minutes leave a margin of five and twenty-five times. `mutants` gets no `not_read`: every stage changes the journal, so it would hardly ever be reused, and a reuse would be correct (decision 7).

3. The check after the feature, after change 2: the next ordinary story of factory-rf that changes a module under `src/factory` (no extra cost; the plan's short smoke run).
   1. Let the story run to its review as usual.
   2. Expected: the coder's journal entry ends with three lines: `` `check`: check: green ``, `` `duplicates`: duplicates: <n> new, <k> known, <g> gone `` and `` `mutants`: mutants: <k> killed, <s> survived, <t> timed out, <n> without tests, 0 not checked, <o> other of <total> mutant(s) in <m> module(s) ``, or the same with `partial, ` after `mutants: ` and ` (stopped after 540 s)` at the end. `MSYS_NO_PATHCONV=1 docker exec factory-self-factory-1 tail -n 3 /state/records/project-commands.jsonl` shows the `mutants` run with its `duration_seconds` (expected 180 to 600) and `"status":"passed"` (or `"failed"` when partial).
   3. The reviewer's entry names each survivor in the story's own lines as a finding, or the equivalent ones under `Notes:`, or says the line was partial.
   4. If the `mutants` line reads `Permission denied`, a file in `mutants/` is not writable by the group: run the `chmod` of change 1 again, and say so in the story's pull request.
   5. At the next feature's acceptance, `make mutants` re-runs only the not-killed mutants of the feature's modules. Its last line should be complete after one or two runs. A run that stays partial and lists `process.py` or `pipeline_definition.py` mutants is the slow kind named in the Goal, not a fault of this feature.

## Decisions taken for the human

1. **The modules of a story are the ones its branch changes, read by the `Makefile`, not by the engine.** On `work-item/<story id>`, `git diff --name-only <merge base with origin/main>` against the work tree, plus the untracked modules, under `src/factory`. The report runs before the stage's result commit, so the coder's changes are still in the work tree. A deleted module drops out through `$(wildcard ...)`, as today. The engine runs `mutants` like any other report and knows neither the target nor the branch form. (The human's change 1)
2. **A story's run takes every mutant of its modules. An acceptance's run takes, by name, only the mutants that are not killed.** mutmut 3.8 runs again every mutant that a name or a pattern selects, fastest first, and keeps no place to resume a pattern from. That is why F0021's runs 2 and 3 both stopped at 2,806 and F0019's second runs finished no new mutant. A list of names that leaves out the killed ones does go on, because each run kills some. Such a list cannot serve a story: mutmut resets the results of a changed function only when it regenerates the mutants inside the run, after the list would have been chosen, so the story's changed functions would be missing from its first run. At the acceptance the same reset shows up as `not checked` in the report after the run, and the next run's list takes those mutants in. A module with no mutant in the results yet (a fresh `mutants/`, a new module) is run by its pattern `<module>.*`. Rejected: running only the changed functions (above) and running every unchecked mutant of the package (about 10,000 in today's cache). (S0001, the human's change 1)
3. **A partial result is a failed report with a line of its own, never a pass.** `check_mutants` exits 1 and its last line starts `mutants: partial, ` whenever a mutant of the chosen modules is still `not checked`, and it ends ` (stopped after <s> s)` when the recipe stopped mutmut. It exits 0 only when every mutant of those modules has a result. Survivors do not change the exit status. The factory then records a partial run as `failed` in `project-commands.jsonl` and, under F0023, in `known-results.jsonl`, and a report never stalls a stage, so mutants stay a record for the reviewer. No fourth `CheckStatus`: the engine judges a command by its exit status alone (R7, F0012). (S0001)
4. **The story-sized limit: the recipe stops mutmut after 540 s, inside a report limit of 10 minutes.** `MUTANTS_SECONDS` stays 540, so the agent's shell tool at the acceptance and the factory's report share one recipe. The 60 s between the two limits are for `mutmut results`, the report line and the `EXIT` trap. The factory stops a command at its time limit with a KILL of its process group, which runs no trap, so a run killed there would leave its temporary folder and files the other user cannot write. S0002's line is the backstop for that case, and decision 13 the repair. Rejected: a TERM before the KILL in `factory.adapters.process` (F0019's module, decision 30 of F0010, all commands affected) and a longer limit (decision 5). (S0002, the human's changes 1 and 2)
5. **The leases stay; `check` gives 7 minutes and `duplicates` 3.** The doing stage's lease of 60 is already full (40 + 15 + 5). The plan keeps the leases and the coder's 40 minutes, so the room comes from the two commands with the widest margin: `check` 15 → 8 (91.4 s at most in 59 runs) and `duplicates` 5 → 2 (4.6 s at most in 36 runs). That gives `mutants` 10. The docs stage, which also runs `check`, drops from 60 to 53. (The human's change 2)
6. **The reviewer lists the survivors from mutmut's own results, not from the journal.** Only a report's last line reaches the journal, as today. The survivors stay in `mutants/` in the checkout, which `git clean` keeps because it is ignored, so the reviewer reads them with `uv run mutmut results`, filtered by the modules of the diff, and `uv run mutmut show <name>`, as `CLAUDE.md` says (change 1). Those results are the latest run of each module. With one story in progress at a time, as the night routine starts them, that run is the story's own. A survivor in a line the story added or changed that breaks a rule the work item states is a finding, so the tester adds the test while the story is open. An equivalent survivor, a message text, or a line the story did not change is a note for the acceptance. A partial line is a note. Rejected: the report's whole output in the journal (a long list in every coder entry) and a file of the factory's under `.reports/` (one more name the engine would learn). (S0003)
7. **A complete `mutants` result is a known result like any report** (F0023 decision 8). The same tree, pipeline definition and image give the same mutants, the same tests and the same results, and the survivors stay in `mutants/`, so a reuse is correct. A partial run exits 1, is never reused and runs again at the next doing stage. `mutants` gets no `not_read`: every stage changes the journal, so a reuse would hardly ever happen, and what is left out matters little for a report that never stalls a stage. (The human's change 2)
8. **One parser of mutmut's result lines, in the domain, and one command.** `mutmut results --all true` prints `    <name>: <status>`. `parse_results` takes those lines and refuses any other with exit status 2, as `check_duplicates` refuses a changed pylint or vulture text, so a change in mutmut's output is seen and not read as "nothing left". A mutant's module is its name without the last dotted part (`factory.application.stage.xǁStageRunnerǁrun__mutmut_3` belongs to `factory.application.stage`). The ten statuses are mutmut 3.8's own words. The report lists the survived, timed-out, suspicious and segfault mutants and counts the rest. (S0001)
9. **`read_input` moves into `factory.entry.inputs`.** `check_duplicates` holds the one way the factory's commands read a text file (UTF-8; `OSError` and `UnicodeDecodeError` give exit 2 and one line on standard error). `check_mutants` needs the same, and `CLAUDE.md` counts a second copy as a finding. The move changes no behaviour and no test of `check_duplicates`. (S0001)
10. **The journal line of a command stopped at its time limit says so.** `command_line` appends ` (stopped at its time limit after <whole seconds> s)` to a `time_limit` result. A passed line, a reused line (F0023) and a failed line stay as they are. A failed report's own last line already says what it is (`duplicates: 1 new, ...`, `1 failed`, `mutants: partial, ...`), and `tests/application/test_stage_finish.py` pins a failed report's line. A green check is never `time_limit`, and a red one stalls with its tail, so in practice only a report shows the new words. (S0002)
11. **What the acceptance reviewer does with it.** It runs `make mutants` again while the last line says `partial`, at most three runs in all, about 30 of its 90 minutes, as today's acceptances did by hand. It reports the score of the last line, says whether it is partial, and groups the survivors, telling the ones the stories' reviews passed on as notes from the new ones. The shipped text names no target form beyond `make mutants` and stays true for a project whose target is still the feature-level one. (S0003)
12. **The template and the demos stay as they are.** `template/Makefile` and `demo/todo-service/project/Makefile` keep the feature-level `mutants` target, and their pipeline definitions get no `mutants` report. The per-story form is factory-rf's until the human's change 3 has shown it on a real story; a later story can carry it into the template. `check_mutants` is factory-rf's own module, like `check_duplicates` (the 2026-10-17 entry *The template's Makefile has no `documents` target and its `duplicates` has no baseline*). (Feature)
13. **`mutants/` belongs to two users.** The factory runs its reports as `factory`. The acceptance reviewer and the reviewer run as `agent`, both in the group `factory-work`. The recipe keeps `umask 022` for the tests' repositories, so its `EXIT` trap makes what it wrote group-writable (`chmod -R g+w mutants`, its own files only). The files that earlier acceptances left are fixed once by the human (change 1). A run killed by the factory's time limit skips the trap. The next run of the other user then fails with `Permission denied` on its report line, and the same `chmod` as root repairs it (change 3, step 4; the operator guide from S0003). (The human's change 1)
14. **A structural test still needs the human's deselect.** mutmut's clean test run fails on a test that reads the source it rewrites (`Failed to run clean test`, the report's last line, status failed). That is today's rule, under the `[tool.mutmut]` list in `pyproject.toml`. No story of this feature adds such a test. A later story that does names its deselect line under its feature's human's changes. (Feature)
15. The leaves to change tests other stories wrote, beyond the standing leave of `CLAUDE.md`: none. S0001 moves a private helper of `check_duplicates`, and `tests/entry/test_check_duplicates.py` passes unchanged. S0002 adds its rows in new test modules: F0023-S0002's `tests/domain/test_command_line.py` and `tests/application/test_stage_finish.py` stay as they are and pass. S0003 adds a test module of its own. (Feature)
16. **Where F0024 touches F0020 to F0023.** All four are built first. S0002 extends F0023-S0002's `command_line` in `factory.domain.checks`, and F0023's reuse never produces a `time_limit` result, so the two suffixes never meet. F0023's change 1 has already rewritten the `project_commands` block, and change 2 here edits that block in place. F0020's and F0022's stories change neither `checks.py`, the stage's reports, the two agent texts' paragraphs named in S0003, nor the `mutants` recipe. F0022 lets a project replace a shipped agent file. factory-rf has none of its own, so S0003's texts are the ones its runs read. (Feature)
17. **Testing, and what only the real run shows.** S0001 is tested on mutmut result texts written by the tests, without running mutmut. S0002 on a fake project command that returns a `time_limit` result. S0003 on the texts. No test, smoke test or story runs mutmut or makes a paid call. Only the human's change 3 shows the report's real time on a story, the reviewer reading real survivors, and the acceptance's shortened list. (Feature)
