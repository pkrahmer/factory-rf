# Pre-check F0024, round 1: the feature, its human's changes and its decisions

The feature `F0024-mutation-testing-per-story`, its three stories and the drafter's brief, checked against v1.1's roles and forms, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml` (`[tool.mutmut]`), the `Makefile`, `.gitignore`, the plan's step 7a, the code the stories touch (`factory.adapters.process`, `factory.adapters.make_commands`, `StageFinisher`), mutmut 3.8.0's own source in the project's virtual environment, F0020's, F0022's and F0023's drafted stories and pre-checks, and `/state/records/project-commands.jsonl` read from the running container (read-only, 345 lines, 2026-10-18 12:22 to 2026-10-19 01:41). The stories' own results are in `F0024-S0001-1.md`, `F0024-S0002-1.md` and `F0024-S0003-1.md`.

The new `mutants` recipe was taken verbatim from change 1 into a copy of the `Makefile` and run in throwaway containers of v1.1's image (no network, no volume, no secret) in a git repository made there: a bare `origin`, `main` with story commits of two features, an acceptance branch and a story branch, S0001's prototype `check_mutants`, and a stand-in for `uv run mutmut` that keeps results in `mutants/` and selects mutants by name and pattern exactly as mutmut 3.8's `collect_source_file_mutation_data` does (including its assertion when nothing matches). Real mutmut could not be run: see *What was not measured*.

## The stories in short

| Story | Intake (predicted) | After it |
|---|---|---|
| S0001 `check_mutants` and `read_input` | question (4) | five edits, one optional (two refused names, the modules not chosen, `rerun_names` with a module twice, `argv`, the order of the lines) |
| S0002 the stopped line | accepted | none |
| S0003 the reviewer's and the acceptance reviewer's texts | accepted | one optional edit |

## Order and sizing

- The order is right: change 1 needs S0001's command; S0003's texts point to change 1's `CLAUDE.md` lines; change 2 needs S0002 and S0003 in the image. S0002 may run while change 1 lands: neither touches the other's files.
- Each story fits a coder's 40 minutes and a few dollars: S0001 three small modules and a moved helper; S0002 two lines; S0003 two texts (its documenter carries the most).
- Leaves: decision 15 is exact. `tests/entry/test_check_duplicates.py`, `tests/application/test_stage_finish.py`, `tests/domain/test_checks.py`, `tests/test_claude_agent_texts.py` and `tests/test_claude_agent_texts_review_leave.py` all pass unchanged against the prototypes (seen). F0023-S0002's `tests/domain/test_command_line.py` rows are `passed` and reused results, which the new suffix does not touch.
- No story touches the git interface's operations, `tests/application/test_interfaces.py`, the pipeline definition's models or load rules, the stage finisher's tests, the records contract or `tests/test_model_configuration.py`'s exceptions; S0001's two models are frozen and forbid unknown keys and pass that test (seen).

## The measured times (`/state/records/project-commands.jsonl`)

`check` passed 62 times, 47.0 s on average, 91.4 s at most (the two slowest, 83.3 s and 91.4 s at 01:16 and 01:19 on 2026-10-19, ran beside the drafter's mutmut run). `duplicates` 38 runs (33 passed, 5 failed with new findings), 3.1 s on average, 4.6 s at most. `documents` 0.2 s. `lint` 0.1 s. The feature's figures (59 and 36 runs) agree with the records as they were when it was drafted. Against 8 and 2 minutes the margins are five and twenty-six times. On a slower machine (the workplace's Podman host) `check` would have to be four times slower before it nears 8 minutes.

## The human's changes

- Write paths: right as stated. The coder's `src/*` and `claude/*` hold every file the stories write; the tester's `tests/*`; the documenter's `README.md` and `docs/*`. Nothing under `image/`, `template/`, `security/`, `factory/`, `pyproject.toml` or `.secrets.baseline`.
- Change 1, the `Makefile` (prototyped): the recipe works as described in every case tried. On `main`: `mutants: set FEATURE, ...`, exit 2. `FEATURE=F0099`: only the modules of `work item F0099-S<n>:` commits on `origin/main` (another feature's commit left out), and only the not-killed mutants of them run by name; with all of them killed the run is skipped and the report is complete. An acceptance branch `work-item/F0099-A0001` takes the feature from its name. A story branch `work-item/F0099-S0002`: with nothing changed, `mutants: no module under src/factory changed by F0099-S0002`, exit 0; with an edited tracked module and an untracked new one in the work tree, both patterns run; a module deleted in the work tree drops out. A stop (`MUTANTS_SECONDS=2`) ends with `mutants: partial, ... (stopped after 2 s)`; the trap leaves no `/tmp/tmp.*`, removes nothing it should not and makes `mutants/mutmut-stats.json`, written `0644`, group-writable. Through the real `MakeProjectCommands` the last line is `check_mutants`' line (make's `Error 1` line is skipped), the status `failed`, the exit status 2. Three faults, below:
  1. **A story or a feature whose modules have no mutant at all fails with mutmut's assertion.** mutmut 3.8 mutates only functions that carry no decorator other than `staticmethod` or `classmethod`, never module-level code. 17 modules of factory-rf have no such function today: the interfaces `application/git.py`, `hosting.py`, `agent_runtime.py`, `files.py`, `machine.py`, `application/boundaries.py`, the record models `domain/command_records.py`, `cost_records.py`, `events.py`, `fault_paths.py`, `kill_point_cases.py`, and the `__init__.py` files (whose mutants mutmut would name without `__init__` anyway). When every name the recipe passes is a pattern of such a module, `mutmut run` stops with `AssertionError: Filtered for specific mutants, but nothing matches` and the report's last line is `Filter: (...)`, a failed report (seen with the stand-in). That happens for a story that changes only such modules (F0023-S0002 changes `boundaries.py` beside others, so not there), and at an acceptance whose other mutants are all killed, where the pattern of such a module is then the only name left: a fully killed feature then gets three failed runs. Fix (tested): the recipe reads that one message as a run with nothing to check (point 1, edit A). Without the fix it is a harmless but misleading report line.
  2. **The factory's time limit does not stop mutmut.** `timeout` puts itself and mutmut into a process group of its own, so the factory's KILL of `make`'s group at the report's limit reaches neither, and `process.communicate()` waits until `timeout` ends them. Seen: a 12-second limit with `MUTANTS_SECONDS=30` returned after 30.1 s as `time_limit`, with mutmut's progress line as the last line and the trap not run. With 540 s inside 600 s the recipe's own stop always comes first, so nothing changes in practice; but decision 4's "a run killed there would leave its temporary folder" happens only when the recipe overran by more than 60 s outside `mutmut run`, and the 10-minute limit is not what bounds the run. Decision 4's text should say so (point 2, edit B).
  3. **Wording: the exit status.** A partial run makes `check_mutants` exit 1 and `make mutants` exit 2 (make's own status for a failed recipe; the records will show `"exit_status":2`). The Goal and the `CLAUDE.md` text say "exit status 1" (edit C).
  The rest of change 1 is right: the names go through the shell, not `$(shell ...)`, so a long list is no single argument; `set -f` keeps the patterns literal; a name with `ǁ` passes through `--names` and a shell variable unchanged (`C.UTF-8` in the image, seen). The long list costs little in mutmut: its filter takes about 10 s for 3,000 names against 13,000 mutants (timed in the image with mutmut's own expression), and every name is its own argument. The two `uv run mutmut results` calls only read `mutants/` (mutmut's `results` prints only result lines and writes nothing). `BRANCH :=` runs one `git rev-parse` at every `make` call, also for `make check`, which costs nothing and fails silently outside a repository. No test reads the root `Makefile`, so no test pins the old recipe. The anchors of the replacement (the comment line, the end of the recipe) and of the `CLAUDE.md` part exist.
- Change 1, the `chmod` of `mutants/`: right, and needed for the directories too (mutmut rewrites `.meta` files and mutant copies in place with `open(..., "w")`, which needs the file's group write bit; new files need the directory's). The checkout's folders carry the set-group-id bit, so a file either user makes stays in `factory-work`.
- Change 2, the pipeline definition: every stage stays within its lease. Doing 40 + 8 + 2 + 10 = 60 of 60, docs 40 + 8 + 3 + 2 = 53 of 60 (with F0023's `secrets`), tests 40 + 5 + 10 = 55. The changed definition (with F0023's `secrets` and `documents: 2`, without its `not_read`, which today's loader does not know) loads with today's `RuamelPipelineDefinitionReader`, `doing` reports `['duplicates', 'mutants']`; with `mutants: {time_limit: 11}` it refuses with `role coder at stage doing: 61 min exceed lease_duration 60 min` (seen). The order (after S0002, S0003 and the rebuild) is right; so is no `not_read` for `mutants`.
- Change 3, the check after the feature: right as a check. Step 2's `"status":"failed"` for a partial run is right; its exit status in the records is 2.

## The decisions

1. The modules of a story from the branch, read by the `Makefile`: right (prototyped). The report runs before the stage's result commit (`StageFinisher.finish` runs checks and reports before `_commit_and_push`), so the work tree holds the coder's changes.
2. A story's run takes all its modules' mutants, an acceptance's run only the not-killed ones by name: right about mutmut. Its source confirms the drafter's finding: in `_run`, a mutant with a result is skipped only when no name is given (`if not mutant_names and result is not None: continue`); with names or patterns every selected mutant runs again, sorted by its estimated worst-case time, fastest first. The reset of a changed function's results happens in `create_mutants_for_file`, inside the run, after the names are taken, as the decision says. One claim is too strong: "Each run shortens that list, so the acceptance's runs do go on". Only kills leave the list; every survived, timed-out, suspicious and test-less mutant runs again in every acceptance run (a timeout costs up to `(estimate + 1) × 15 × 2` CPU seconds, mutmut's defaults). A feature whose survivors and timeouts alone take more than about 375 s of a run (540 s less the fixed 165 s) stays partial after three runs, its slowest modules (`process.py`, `stage.py`, about 90 s a mutant on F0016's acceptance) never reached (point 3, edit D). A second, smaller residue: when the list is empty the run is skipped and the report reads the stories' last results, so a module changed after its last story report (by a human commit on `main`, or in a feature whose stories predate change 2) is reported as it was then.
3. A partial result is a failed report with a line of its own, never a pass: right (prototyped through `MakeProjectCommands`: `failed`, exit 2). Never reused under F0023: right, F0023 reuses only `passed`.
4. 540 s inside a report limit of 10 minutes: right as a pair, with the precision of fault 2 (edit B).
5. `check` 8 and `duplicates` 2 minutes, the leases kept: right against the records.
6. The reviewer reads the survivors from mutmut's results, the latest run of each module: right for a complete run of one story at a time. Two limits it should name: after a stopped run, the mutants it did not reach keep the result of an earlier run of their unchanged function; and mutmut maps tests to functions anew only for new tests (`Found N new tests, rerunning stats collection`), the stale map of the 2026-10-18 night log, so a survivor in a function that only changed tests reach can be false. A new test kills it on the next run, so the finding rule still converges (edit F).
7. A complete `mutants` result is a known result: right; in practice never reused, as the decision says.
8. One parser in the domain, mutmut's ten words: right; they are exactly the values of mutmut 3.8's `status_by_exit_code`, and `results --all true` prints `    <name>: <status>` and nothing else.
9. `read_input` in `factory.entry.inputs`: right; no behaviour of `check_duplicates` changes (seen). `check_documents._read` stays, it returns `None` for a missing file and is no copy.
10. The stopped line: right; see S0002's pre-check for when it shows.
11. The acceptance reviewer, at most three runs: right; about 30 of its 90 minutes. Its runs go on only as far as decision 2 allows (point 3).
12. The template and the demos stay: right.
13. `mutants/` of two users: right; see change 1.
14. A structural test needs the human's deselect: right, and it has a cost the feature should name. A change of `[tool.mutmut]`'s test arguments (its `test_selection` and `test_execution` fingerprint), and a fresh `mutants/`, make mutmut reset every result and run its stats over the whole suite in one process before any mutant; it saves those stats only when that run ends. If that stats run alone nears 540 s, every stopped run starts it again and no run gets further. The drafter's estimate for a cold run is about three more minutes, which fits; it is not measured (edit E, point 4).
15. The leaves: none needed, exact (seen).
16. Where F0024 touches F0020 to F0023: right. S0002 builds on F0023-S0002's `command_line` exactly as drafted there; F0023's change 1 has rewritten the `project_commands` block and change 2 edits it in place (the `duplicates` line matches F0023's). F0022-S0002 adds R15 to the `## Rules` of every agent and leaves `## Role` alone, so S0003's anchors stand; F0020's opencode runtime generates its agents from the same files, so S0003's texts reach it too. No story needs a note.
17. Testing without mutmut: right; no story, test or smoke test runs mutmut or makes a paid call.

## What was not measured

The per-story timing of a real `make mutants` run in a throwaway container could not be done. v1.1's image holds no development dependencies (`uv sync --frozen --no-dev`: no mutmut, libcst, pytest), mutmut needs libcst's parser, a compiled extension of which this machine holds only the Windows build (the project's `.venv`, and the uv cache has no Linux wheel), mutmut does not run on Windows (`set_start_method("fork")`), there is no network to fetch a wheel, and the only Linux environment with mutmut is the running instance's checkout volume, which the brief excludes. So the feature's 165 s fixed cost and 0.13 to 0.25 s per mutant stand as the drafter measured them, unchecked; the story counts of F0019 and F0021 (12 of 18 stories, 49 to 2,056 mutants) could not be rechecked either, since they need git. The human's change 3 is the first real measurement.

## Points for the human, with recommended answers

1. A story or feature whose modules have no mutant (fault 1, edit A): (a) the recipe reads mutmut's `Filtered for specific mutants, but nothing matches` as a run with nothing to check (one line changed, tested with the stand-in: the report is then `mutants: 0 killed, ... of 0 mutant(s) in <m> module(s)`, a stop still reads as stopped, any other failure still fails); (b) leave it, and say in the operator guide that the line `Filter: (...)` means the modules have no mutant. Recommended: (a). A fully killed feature should not fail its acceptance's report three times; a later mutmut with another message only brings back today's failed line, never a false pass.
2. The factory's limit and mutmut's process group (fault 2, edit B): (a) correct decision 4's text; (b) also give `timeout` a `--kill-after` and read its 137 as a stop. Recommended: (a). The recipe's own stop comes first, mutmut's fork server ends its workers on the TERM, and (b) adds a rule for a case not seen.
3. What the acceptance's runs re-run (decision 2, edit D): (a) keep re-running the survivors, timeouts and test-less mutants with the not-checked ones, as the plan's step 7a says, and correct the claim that each run shortens the list; (b) re-run only the not-checked mutants, so that every run goes on, and take the stories' survivors as they were. Recommended: (a); the plan asks for the survivors against the final code, and at about 5 % survivors F0021's size fits. Watch the first large feature's acceptance; (b) is a one-line change of `rerun_names` later if its runs stay partial.
4. The full stats run (decision 14, edit E): (a) name the cost in decision 14 and in S0003's operator-guide subsection, with the repair (one run by hand with a larger `MUTANTS_SECONDS` while the factory is idle); (b) say nothing until it happens. Recommended: (a).
5. The exit status wording (edit C): (a) correct it; (b) leave it. Recommended: (a).
6. The latest run of each module (decision 6, edit F): (a) name the two limits; (b) leave it. Recommended: (a); the reviewer's text needs no change, the decision log should say why a survivor can be false.
7. The project guide's length: 1,905 lines today; F0020's, F0022's and F0023's documenters add to it before F0024, whose three docs criteria add more to *Mutation testing*. The documenter's lesson splits a file before it passes 2,000 lines, while the plan puts the split at step 8. (a) look at the line count when F0023 is archived, and past about 1,950 lines build step 8 first; (b) leave it to F0024's documenters. Recommended: (a), as for F0023.
8. The stories' points: S0001's four questions and edit 5 (see `F0024-S0001-1.md`; all recommended (a)); S0003's optional edit (see `F0024-S0003-1.md`).

## Verdict

Feature accepted with edits: A (required for a fully killed feature's acceptance and for stories that change only interfaces or models), B to F (wording of the decisions and the `CLAUDE.md` text). S0001 refused at intake as drafted, accepted with its edits; S0002 and S0003 accepted.

Edit A, *The human's changes*, change 1, the code block: replace the line

```make
	  TMPDIR="$$temporary" timeout $(MUTANTS_SECONDS) uv run mutmut run $$names || { status=$$?; [ $$status -eq 124 ] || exit $$status; stopped="--stopped-after $(MUTANTS_SECONDS)"; }
```

with

```make
	  # mutmut mutates only functions without a decorator: a module of interfaces, models or constants has
	  # no mutant, and mutmut stops when no name matches one. That is a run with nothing to check.
	  TMPDIR="$$temporary" timeout $(MUTANTS_SECONDS) uv run mutmut run $$names 2>&1 | tee "$$temporary/run.txt" || { status=$$?; [ $$status -eq 124 ] || grep -qF 'Filtered for specific mutants, but nothing matches' "$$temporary/run.txt" || exit $$status; [ $$status -ne 124 ] || stopped="--stopped-after $(MUTANTS_SECONDS)"; }
```

and append to the paragraph after the block ("The names go through the shell ..."):

```markdown
 mutmut 3.8 mutates only functions without a decorator (other than `staticmethod` and `classmethod`), never module-level code: 17 modules of factory-rf have no mutant (the interfaces under `factory.application`, `boundaries.py`, the record models, the `__init__.py` files). When every name is a pattern of such a module, `mutmut run` stops with `Filtered for specific mutants, but nothing matches`; the recipe reads that as a run with nothing to check, and the report counts 0 mutants for those modules.
```

Edit B, decision 4, insert after "so a run killed there would leave its temporary folder and files the other user cannot write.":

```markdown
 The KILL does not reach mutmut either: `timeout` runs it in a process group of its own, so the factory waits until `timeout` ends it (seen in a throwaway container: a 12-second limit returned after the recipe's own 30-second stop). The recipe's stop, not the report's limit, bounds the run; the report's limit ends a run only when the steps around `mutmut run` overran by more than 60 s.
```

Edit C, `## Goal`: replace "(its own last line, exit status 1, a failed report)" with "(its own last line; `check_mutants` exits 1, so `make mutants` fails and the report is failed)". *The human's changes*, change 1, the `CLAUDE.md` block: replace "or `mutants: partial, ...` with exit status 1 while a mutant of those modules is not checked; a partial result is never a pass." with "or `mutants: partial, ...`, and the target fails, while a mutant of those modules is not checked or mutmut was stopped; a partial result is never a pass."

Edit D, decision 2, insert after "A list of names that leaves out the killed ones does go on, because each run kills some.":

```markdown
 Only kills leave the list: every survived, timed-out, suspicious and test-less mutant runs again in each acceptance run, against the final code, as the plan asks. A feature whose survivors and timeouts alone take more than about 375 s of a run (540 s less the fixed 165 s) stays partial after three runs, with its slowest modules not reached.
```

and in `## Goal` replace "Each run shortens that list, so the acceptance's runs do go on." with "Each run shortens that list by what it kills, so the acceptance's runs go on while the survivors fit in one run."

Edit E, decision 14, append:

```markdown
 Such a change has a cost of its own: a change of `[tool.mutmut]`'s test arguments, like a fresh `mutants/`, makes mutmut reset every result and run its stats over the whole suite in one process before any mutant, and it keeps those stats only when that run ends. If it alone nears 540 s, each stopped run starts it again. The repair is one run by hand with a larger `MUTANTS_SECONDS` while the factory is idle; the operator guide's *The mutation report of a story* says so (S0003).
```

and in S0003's docs criterion, the operator-guide subsection's sentence, append after "and what the acceptance re-runs.": " It also says that after a change of `[tool.mutmut]`'s test arguments, or with a fresh `mutants/`, the first run spends its time on mutmut's stats over the whole suite, and that one run by hand with a larger `MUTANTS_SECONDS` while the factory is idle repairs a run that never gets past them." (This is the one edit to a story's text the feature's corrections need; the human makes it with point 4.)

Edit F, decision 6, insert after "With one story in progress at a time, as the night routine starts them, that run is the story's own.":

```markdown
 Two limits: after a stopped run, the mutants it did not reach keep the result of an earlier run of their unchanged function; and mutmut 3.8 maps tests to functions anew only for new tests, so a survivor in a function that only changed tests reach can be false (the stale map of 2026-10-18). A new test kills it on the next run.
```
