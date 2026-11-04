# No stage runs mutation testing

## Goal

The human's decision of 2026-10-19 (the night log, `docs/runs/2026-10-12-overnight/night-log.md`, the row of 22:20): mutation testing runs only as sweeps outside the factory, and the `mutants` target stays for the sweeps. The coder's stage stopped reporting `make mutants` earlier that day (`factory/pipeline.yml`). The acceptance reviewer still runs it in its check 3, *Mutation score*, up to three times, and every acceptance of 2026-10-19 spent one to four runs of up to 540 s there. The large features still ended partial (F0019 to F0023). The reviewer still has a paragraph on reading a report that no stage writes any more. The project template still says that the feature acceptance runs `make mutants`, and the documents still describe the report after the coder, the reviewer's reading and the acceptance's runs. This feature is for the human, who pays for every acceptance and runs the sweeps, and for every project made from the template. When it is done, no shipped agent runs or reads mutation testing. The acceptance's check 3 becomes *Mutation testing*, with the one line `By sweep, not run here.`, so the report keeps its eight sections. The documents say that mutation testing runs by sweep. The acceptance reviewer's time limit can shrink to that of the other roles (the human's change 3). Done when every story below is merged and `make check` is green.

## Scope

- `claude/agents/acceptance-reviewer.md`: check 3, check 7's first sentences, the recommendation's and the proposals' words on survivors and mutants, steps 1 and 3 of its stage (S0001).
- `claude/agents/reviewer.md`: the paragraph on the mutation report goes (S0001).
- `template/CLAUDE.md` and `template/Makefile`: `make mutants` is for a sweep by hand, never run by a stage (S0001).
- `tests/test_claude_agent_texts_mutants.py` (rewritten) and `TEMPLATE_RULES_LINES` of `tests/test_claude_files.py` (S0001, under decision 7).
- `docs/operator-guide.md`, `docs/project-guide/processes-and-checks.md`, `docs/project-guide/agents.md` and `docs/decisions.md`, from the story's docs criterion, which also takes the two passages of F0024-S0005 that stay true (decision 8).

## Out of scope

- The `mutants` target of every `Makefile`, its recipe and `MUTANTS_SECONDS`; `python -m factory.entry.check_mutants` and `factory.domain.mutants`; `[tool.mutmut]` in `pyproject.toml`: unchanged, for the sweeps.
- Every module under `src/`: nothing changes there.
- `template/factory/pipeline.yml` and the todo demo's `factory/pipeline.yml`: unchanged. `mutants/*` stays in their `tool_paths`, and neither names a `mutants` command (decision 9).
- How a sweep runs (its brief under `planning/`, F0028's sweeps): the human's, outside the factory.
- The baseline run: its checkout is fixed at `baseline-v1.1`, whose acceptances still run `make mutants`; nothing here reaches it.
- F0030 (the kill at a time limit ends the command's whole session): it stays, and only its docs criterion meets this feature (decision 11).
- Every paid call: no story and no smoke test makes one.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`. The human's changes 1 and 2 may come at once. Change 3 comes after S0001 is merged and `self` is rebuilt.

- S0001: The shipped agents neither run nor read mutation testing

## The human's changes

Checked against `factory/pipeline.yml`: the coder writes `src/*`, `image/*`, `template/*` and `claude/*`, the tester `tests/*`, the documenter `README.md` and `docs/*`. S0001 changes `claude/agents/acceptance-reviewer.md`, `claude/agents/reviewer.md`, `template/CLAUDE.md` and `template/Makefile` (the coder's) and two test modules (the tester's). No new dependency, no `.secrets.baseline` entry, no `security/` change, no suppression marker, no `Makefile` or `pyproject.toml` change. No story adds a structural test that reads `src/`, so `[tool.mutmut]` stays as it is. Outside the write paths:

1. **`CLAUDE.md`, *Checks***, at once: the bullet still says that the factory runs `make mutants` as a report after the coder. In the bullet that begins `` - `make lint` and `make test` run those two alone.``, everything from `` `make mutants` runs mutmut and is never part of `make check`.`` to the end of the bullet becomes:

   ```markdown
   `make mutants` runs mutmut and is never part of `make check`. No stage and no agent runs it: mutation testing runs only as sweeps outside the factory, which the human starts on a fresh copy, with `mutants/` made anew for every run (the human, 2026-10-19). On a story's branch, `work-item/<story id>`, it mutates every module under `src/factory` that the branch changes against `origin/main`, the work tree included; with `FEATURE=<feature id>` it runs, of the modules the feature's story commits changed, the mutants that are not killed. It stops mutmut after `MUTANTS_SECONDS` (540 s). Its last line is `check_mutants`'s: `mutants: <k> killed, <s> survived, ...`, or `mutants: partial, ...`, and the target fails while a mutant of those modules is not checked or mutmut was stopped; a partial result is never a pass. mutmut leaves out the structural tests listed in `pyproject.toml`, which read the source it rewrites. The pipeline knows these six targets (`check`, `lint`, `test`, `secrets`, `duplicates`, `documents`).
   ```

   If decision 9's `mutants` line stays in `factory/pipeline.yml`, the last sentence stays as it is today: seven targets, `mutants` among them.

2. **`factory/pipeline.yml`**, at once (decision 9). The line `  mutants: {time_limit: 10}     # mutmut over the modules a story changes; no stage reports it for now (the human, 2026-10-19)` goes. `"mutants/*"` leaves `tool_paths`: no agent run writes `mutants/` any more, so the kernel refuses it.

3. **`factory/pipeline.yml`, the acceptance reviewer**, after S0001 is merged and `self` is rebuilt, so that no acceptance on the old text meets the shorter limit (decision 10). The comment `  # make mutants re-runs, inside this agent run, the mutants the stories' reports left not killed.` and the line below it become:

   ```yaml
     # Mutation testing runs only by sweep, outside the factory (the human, 2026-10-19); without make mutants
     # the acceptances of 2026-10-19 took at most about 22 minutes, so it has the other roles' limits.
     acceptance-reviewer: {write_paths: ["{work_item}", "{feature}/backlog/*"], time_limit: 40, lease_duration: 60}
   ```

4. **The todo demo** (`demo/todo-service/project/`, outside every write path), with change 1 or later; the baseline run is not touched, as its checkout is fixed at its tag. In `CLAUDE.md`, *Checks*: ``and lists the surviving mutants: run by the feature acceptance, never part of `make check`;`` becomes ``and lists the surviving mutants: for a sweep by hand, never run by a stage and never part of `make check`;``. In `Makefile`, line 103: ``# `make mutants FEATURE=F0001`. Slow, so not part of `check`; the feature acceptance runs it,`` becomes ``# `make mutants FEATURE=F0001`. Slow, so not part of `check`; a sweep by hand runs it, never a stage,``. Both are the template's new texts. No test reads either line (`tests/test_demo_makefile_secrets.py` compares only the `secrets` recipe).

5. **F0024's backlog** (`factory/features/F0024-mutation-testing-per-story/backlog/`), before S0001 starts (decision 8). **F0024-S0005** (*The documents describe the mutation report as it runs*) is removed. Its first passage, the recipe's copy of the other files under `src/`, and its third, the two runs measured at F0024's acceptance, are in S0001's docs criterion. Its second passage, mutmut going on after the factory's kill, describes a report that no stage runs any more, and F0030 removes the fault. **F0024-S0004** (*The fault lines of `check-mutants` and `check-duplicates` are pinned*) stays as it is: `check_mutants` stays for the sweeps, and the story changes no agent text and no document of this feature.

6. **F0030's draft** (`planning/overnight/stories/F0030-a-command-stopped-at-its-time-limit-leaves-no-process-running/`), if this feature is merged first (decision 11). In S0001's criterion 9, the sentence for `docs/operator-guide.md` (*The mutation report of a story*, the `Permission denied` paragraph) goes, as S0001 here removes that paragraph. The sentence for *Mutation testing* becomes: "the paragraph on the stop at `MUTANTS_SECONDS`: a `make mutants` that the factory or a caller kills at a time limit leaves no mutmut running, as it stays in the session." Its decisions 12 to 15 are moot, as the night log says.

## Decisions taken for the human

1. **No shipped agent runs or reads mutation testing** (the human, night log, 2026-10-19 22:20). The acceptance reviewer's text is shipped to every project, so the change holds for the template's projects too: it does not depend on whether the project has a `mutants` target. A rule only for factory-rf would need a switch in the pipeline definition, more than the gain. (S0001)
2. **Check 3 stays, as one line, and is not dropped** (the task's two options). The line is `By sweep, not run here.` under `## 3 Mutation testing`. Dropping check 3 would renumber checks 4 to 8 and the sections `## 1 Scope` to `## 8 Cost`. Then *Do the eight checks* in `tests/test_claude_agent_texts.py`, check 7's start `7. **The slow checks.**` in `tests/test_acceptance_reviewer_disk.py` and the numbering of every report already in `done/` would change, all for one line saved per report. Rejected too: a list of the modules the feature changed, for the next sweep. `make mutants FEATURE=<id>` finds those modules itself. Recommended: the line; the human may choose the drop. (S0001)
3. **"Never run `make mutants` or mutmut" in the text, not only its absence.** A project's `CLAUDE.md` may still say that the feature acceptance runs the target (the todo demo until the human's change 4, every project made from the old template). The shipped text says plainly that the acceptance does not. (S0001)
4. **The entry loses `make mutants <killed>/<total>`.** No code reads the entry's parts. The factory writes the pull request's description from the recommendation, the entry and the proposed stories, as free text. (S0001)
5. **The reviewer's paragraph goes, not kept dormant.** It applies only when the coder's entry has a `mutants` line. No stage writes that line since 2026-10-19, and the decision of 22:20 ends the per-story report for good. Kept, it would cost every review its tokens and keep the documents describing a reading that never happens. (S0001)
6. **The template's words change with the agents.** `template/CLAUDE.md` says ``run by the feature acceptance``, and the shipped acceptance reviewer no longer runs it, so a new project would be told something false. `template/factory/pipeline.yml` stays: it names no `mutants` command, and `mutants/*` in its `tool_paths` harms nothing for a project's own sweeps. (S0001)
7. **The leave to change tests other stories wrote**, beyond the standing leave of `CLAUDE.md`. The tester makes exactly these changes and nothing else in those modules:
   - `tests/test_claude_agent_texts_mutants.py` (F0024-S0003) is rewritten. Its docstring becomes `"""No shipped agent runs or reads mutation testing; the acceptance's check 3 says it is done by sweep."""`. `_REVIEWER_MUTANTS`, `_ACCEPTANCE_MUTATION_SCORE`, `_OLD_ACCEPTANCE_SENTENCE` and their three tests go: `test_agent_role_holds_the_mutation_report_text`, `test_reviewer_mutants_paragraph_sits_between_item_6_and_the_findings_paragraph` and `test_acceptance_reviewer_holds_the_mutation_score_check_once`. S0001's criteria 1 to 3 replace them, with the template's `Makefile` line of criterion 4 in the same module.
   - `tests/test_claude_files.py`: in `TEMPLATE_RULES_LINES`, ``run by the feature acceptance, never part of `make check`;`` becomes ``for a sweep by hand, never run by a stage and never part of `make check`;``. The strings are wrapped again as ruff's line length needs, and every other line and every test stays as it is.
   - Unchanged, and they must pass: `tests/test_claude_agent_texts.py`, `tests/test_acceptance_reviewer_disk.py`, `tests/test_claude_agent_texts_review_leave.py`, `tests/test_template_makefile.py`. `tests/domain/test_command_line_time_limit.py` and `tests/application/test_stage_time_limited_report.py` use `mutants` only as sample data of a stopped command; they stay.
8. **F0024-S0005 is removed, and its true parts move here** (night log: "becomes mostly moot"). S0001 rewrites the same two sections of the documents. A separate documentation story would edit sections that this feature removes or rewrites, and describe a report killed by the factory, which no stage runs any more. F0024-S0004 stays: it pins the fault lines of a tool the sweeps keep. (Feature; the human's change 5)
9. **Open, the human's: `mutants` and `mutants/*` leave factory-rf's `factory/pipeline.yml`** (the human's change 2). Recommended: both go. No stage names the command, so its line only says "no stage reports it", and a later reader may take it as something the factory runs. A sweep runs on a fresh copy, so no agent run needs to write `mutants/`, and with it out the kernel refuses an agent's stray `make mutants`. Option: keep both, as a record and against a return of the report; then change 1 keeps "seven". The baseline run reads its own pipeline definition, the demo's, so neither choice reaches it.
10. **Open, the human's: the acceptance reviewer's `time_limit` 90 and `lease_duration` 100 shrink to 40 and 60** (the human's change 3). Measured from the cost records `factory/features/*/done/*-A*.costs.jsonl` of 2026-10-19 (UTC):

    | acceptance | minutes | model minutes | `make mutants` runs |
    |---|---|---|---|
    | F0021-A0001 | 37.8 | 9.4 | 3 |
    | F0021-A0002 | 27.3 | 6.7 | 2 |
    | F0021-A0003 | 68.6 | 6.7 | 2, and six mutmut runs of up to 530 s |
    | F0025-A0001 | 21.9 | 8.3 | red before it scored |
    | F0025-A0002 | 17.8 | 6.0 | red before it scored |
    | F0020-A0001 | 47.6 | 9.5 | 4 |
    | F0026-A0001 | 18.2 | 10.3 | 1, to its end |
    | F0022-A0001 | 28.3 | 9.0 | 2 |
    | F0023-A0001 | 37.3 | 8.5 | 2 |
    | F0024-A0001 | 18.3 | 9.3 | several, and the 3 s kill experiments |
    | F0026-A0002 | 8.8 | 3.7 | 1, to its end |
    | F0020-A0002 | 35.6 | 6.8 | 3 |

    The number of runs comes from each report's section 3. For the six whose runs all stopped at 540 s (F0021-A0001 and A0002, F0020-A0001 and A0002, F0022-A0001, F0023-A0001), the rest after 540 s per run is 8.6 to 19.3 minutes. The five whose runs ended early or failed (F0024-A0001, F0025-A0001 and A0002, F0026-A0001 and A0002) took 22 minutes at most in all, which bounds them. F0021-A0003 was mostly mutmut and says nothing more. The model's own time was at most 10.3 minutes. So an acceptance without mutmut took at most about 22 minutes. That is an estimate, as the records do not split the shell's time by command. 40 minutes leaves almost twice that, and a lease of 60 matches every other role. A crashed acceptance then blocks its feature for 60 minutes instead of 100. Recommended: 40 and 60, after S0001 is merged and `self` is rebuilt; before that, an acceptance would still run `make mutants` on the old text. Option: keep 90 and 100 until three acceptances without mutmut have been measured.
11. **The order with F0030.** The two are independent in code. If this feature is merged first, F0030-S0001's docs criterion names a paragraph that S0001 removes; the human's change 6 rewrites it. If F0030 is merged first, S0001's docs criterion removes F0030's sentence with the paragraph, which is right: no factory user writes `mutants/` any more. (Feature)
12. **One story.** The coder replaces nine passages in four text files and writes no code. The tester rewrites one module of about sixty lines and changes one string of another. The documenter has the largest part, two sections rewritten and one decision entry. Each fits the 40-minute `time_limit`. (Feature)
13. **The number and the name.** F0031 is the first number above every folder in `factory/features/` (F0018 to F0026) and `planning/overnight/stories/` (F0001 to F0030; F0028 is another drafter's). The folder name says what the feature makes true. (Feature)
