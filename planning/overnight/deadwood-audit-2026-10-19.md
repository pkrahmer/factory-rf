# Deadwood audit of factory-rf's non-code files, 2026-10-19

For the human's cleanup (beside F0032 "mutation testing keeps only its sweep form", or on its own). Read from the checkout at `c4c699d5` (F0031-A0001 merged, 23:19). Scope: every tracked file outside `src/` and `tests/`: 1,105 of 1,742 tracked files (`image/secrets/` not opened or listed). The working tree matches the index: no untracked, modified or deleted file outside `src/` and `tests/`; `session-logs/` is git-ignored and `factory/stops.jsonl` was never committed.

How "dead" was checked: every path or name below was searched in `src/`, `tests/`, `claude/` (agents and `settings.json`), `CLAUDE.md`, `README.md`, `factory/pipeline.yml`, the `Makefile`, `pyproject.toml`, `.secrets.baseline`, `docs/` and `factory/features/`. **No test and no code reads any file under `planning/`.** The only live pointers into `planning/` from outside it are: `pyproject.toml` line 16 (a comment naming `planning/overnight/interfaces.md`) and line 54 (ruff's `extend-exclude` of `planning`); the `Makefile`'s `secrets` filter and `factory/pipeline.yml`'s `not_read` (both `planning/*`, a pattern, not a file); and `docs/decisions.md`, which cites `planning/overnight/podman-probe-2026-10-17.md` twice and `planning/overnight/first-start-checklist.md` five times as the source of decisions. `factory/features/` and `factory/v1/` cite planning files as history (first-start checklist 13 times, the restructure plan 11, lessons 11, and a few others); `docs/runs/.../night-log.md` cites nearly everything.

Verdicts: **keep** (read by an agent, a test, the factory or the human, or the record of a decision); **archive** (history worth a named place, out of the working tree); **delete** (superseded, duplicated, or the working note of a finished task; git history keeps it anyway); **merge** (its content belongs in another file). "Archive" below means one annotated tag on the last commit before the cleanup, proposed name `planning-history-2026-10-19` (question 1), so that every citation in the records still resolves with `git show planning-history-2026-10-19:<path>`.

## Totals

| Verdict | Files | Size |
| :- | -: | -: |
| keep | 502 | about 9.8 MB (of it `factory/v1/` 5.0 MB, `factory/features/` 2.7 MB, `docs/` 1.0 MB) |
| archive | 37 | about 0.4 MB |
| delete | 565 (+1 after 2026-10-20 05:00) | about 6.5 MB |
| merge | 3 | about 0.07 MB |

`planning/` shrinks from 652 tracked files (about 8.6 MB) to 47 (about 0.9 MB).

## The table

### planning/overnight/stories/ (206 files): drafts

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `stories/F0001-…` to `stories/F0017-…` (17 folders: `FEATURE.md`, `drafts/`) | 176 | v1-era drafts of v1.1's features F0001–F0017 | **delete** | Every one of the 176 files has a same-named file in `factory/v1/features/<same folder>/`; the v1 copy is the draft plus its journal and the decisions added during the build (e.g. F0002's `FEATURE.md` lacks decisions 15–17 and stories S0009–S0010). 5 files are byte-identical, the rest are older. Nothing cites a draft path except the night log. |
| `stories/F0019-the-write-guard-by-the-kernel/` (`feature.md`, `backlog/S0001`–`S0006`) | 7 | **A copy left behind.** F0019 was added to `factory/features/` on 2026-10-18 (`b14a121d` "F0019: add the feature and its stories") by copy, not `git mv` | **delete** | `factory/features/F0019-…/` holds the same feature plus S0007–S0012 and three acceptances, all done. |
| `stories/F0020-opencode-as-a-second-agent-runtime/deferred/F0020-S0009-the-factory-keeps-its-spend-within-a-window-before-each-run.md` | 1 | The one deferred story of F0020; F0020 itself is in `factory/features/` (moved) and accepted twice | **keep** until question 4 | Its number S0009 is not used in `factory/features/F0020-…/`; the precheck order note renamed another S0009 to S0012. It is the only copy of the idea. |
| `stories/F0027-…` (feature + S0001–S0004) | 5 | Drafted, pre-checked; "F0027 later (after the mutmut talk)", the human 21:59 | **keep**, with an edit (**merge**, below) | Not in `factory/features/`. Its decision 3 and **S0004** (`kept_ignored: ["mutants/*"]`, "F0024 needs `mutants/` across stages") exist only for the per-story mutation report, which is retired: no stage runs `make mutants` and F0032 makes `mutants/` fresh for every run. S0004 has no purpose left (question 5). |
| `stories/F0028-…` (feature + S0001–S0009) | 10 | Tests-only feature from the sweeps; queued after F0029 and F0030 | **keep** | Not in `factory/features/`. Its "check after the feature" (line 72) already says no acceptance runs `make mutants` (F0032 decision 11 calls it stale; it was fixed since). |
| `stories/F0029-…` (feature + S0001–S0002) | 3 | Queued first of the three (the human 21:59) | **keep** | Not in `factory/features/`. |
| `stories/F0030-…` (feature + S0001) | 2 | Queued second | **keep** | Not in `factory/features/`. F0032's change 4 edits its human's change 2 (the story-branch mode goes). |
| `stories/F0032-…` (feature + S0001) | 2 | Drafted tonight (23:03) | **keep** | Not in `factory/features/`. |
| (working tree only) empty folders `stories/F0020-…/backlog/` and `stories/F0025-…/backlog/` | 0 | Left by today's `git mv` of F0020 and F0025 | remove locally (`rmdir`) | Git does not track empty folders; F0025 is in `factory/features/` complete. F0031 left nothing. |

### planning/overnight/precheck/ (186 files)

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `precheck/F0001-*` to `precheck/F0026-*` (rounds 1–3 of features and stories) | 170 | Pre-checks of features that are built and accepted | **delete** | Each pre-check's edits were applied to the draft before it moved (the closing decision of each `feature.md` names them); every feature F0001–F0026 is in `factory/v1/features/` or `factory/features/` with its acceptance. Five records cite `precheck/…` paths as history; the tag resolves them. |
| `precheck/demo-todo-service-1.md`, `precheck/demo-fixes-F0016-1.md` | 2 | Pre-checks of the demo draft and of the shakedown fixes | **delete** | Both applied: `demo/` carries them (`d38945f4`, 2026-10-18; `e3541374`, 2026-10-17). |
| `precheck/proposed-2026-10-19-order.md` | 1 | The order of the 13 proposed stories of 2026-10-19 | **delete** | Approved by the human 19:26 and recorded in the night log; built except F0023-S0003/S0004 and F0024-S0004 (the last removed by F0032 change 3). The backlogs and the night log hold the order. |
| `precheck/F0027-*`, `F0028-*`, `F0029-*` | 13 | Pre-checks of the three queued drafts | **keep** until each feature moves | Their features are not built; delete each set when its feature moves into `factory/features/`. |

### planning/overnight/briefs/ (138 files)

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `briefs/F0001.md` … `F0011.md`, `audit-*`, `improve-*`, `round3-F0001.md`, `cross-check-1.md`, `apply-*`, `seed.md`, `skeleton.md`, `interfaces.md`, `fault-paths.md`, `quiz-working-answers.md` | 56 | Briefs of the first nights' phases 1–4 (2026-10-12 to 10-14) | **delete** | Finished tasks; their outputs are archived or built. |
| `briefs/draft-F00nn.md`, `briefs/precheck-F00nn-*.md` (F0001–F0026), `draft-F0012-S0028-S0029.md`, `precheck-F0001-S00nn.md` etc. | 68 | Per-feature drafting and pre-check briefs | **delete** | Every feature they name is built. |
| `briefs/draft-template.md`, `precheck-template.md`, `audit-template.md`, `improve-template.md`, `cross-check-template.md` | 5 | `{{FID}}` templates of phases 2–4 | **delete** (or **merge**, question 6) | Written for v1's roles and phases ("pre-check with v1's own roles"); the drafts since F0019 were briefed one by one, and F0027–F0032 had no brief file at all. `improve-*` and `audit-*` are no longer a phase. |
| `briefs/precheck-round-2.md` | 1 | Generic round-2 pre-check brief (2026-10-19) | **delete** (or **merge** into one generic pre-check brief, question 6) | Names "one of F0022 to F0026"; those are built. |
| `briefs/draft-demo-todo-service.md`, `precheck-demo-todo-service.md`, `plan-handover.md`, `plan-baseline-run.md`, `probe-F0019.md`, `security-review-write-guard.md`, `stack-template-designs.md` | 7 | One-off briefs | **delete** | Each output exists: `demo/`, `handover-plan.md`, `baseline-run-plan.md`, `probe-F0019-2026-10-18.md`, `security-review-2026-10-19.md`, `templates/`. |
| `briefs/mutation-sweep.md` | 1 | The sweep brief, still used ("sweep everything left in idle time", the human 22:20) | **keep**, with an edit (**merge**, below) | Cited by the three sweep reports and by F0032's change 5. Its first sentence, "Feature acceptances run `make mutants` only over the modules a feature changed", is false since F0031; after F0032 a sweep can call `make mutants MODULES=… MUTANTS_CHILDREN=…`. |

### planning/overnight/ other groups and top-level files

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `audits/` (`F0001-1.md` … `F0011-3-handling.md`) | 40 | Audits of F0001–F0011's drafts and their handling notes, first night | **delete** | F0001–F0011 built by v1 and accepted (`factory/v1/features/`); the audits' findings went into the drafts. Only `docs/runs/.../report.md` cites `audits/F0001-`. |
| `demo/` (`README.md`, `todo-service/` with `NOTES.md`, `features/`, `project/` incl. `Makefile`, `uv.lock`, `.secrets.baseline`, two `.py` files) | 26 | The staging copy of the todo demo (2026-10-17) | **delete** | `demo/` is the live demo, checked by `tests/test_demos.py` over the repository. 10 files are identical, 15 are older than `demo/` (stories, `CLAUDE.md`, `Makefile`, pipeline, `pyproject.toml`). The stale copy shows up in every search for `mutants` (its `Makefile`, `CLAUDE.md`, `uv.lock`). `NOTES.md`'s choices were confirmed or applied (its "pre-check's edits" section). |
| `status-map-mockup/` (`factory-status-map.html` 0.7 MB, `assemble.py.txt`, three parts) | 5 | The status map proof of concept | **delete** | Now the Factory Timeline, repository `pkrahmer/factory-timeline`, and its PoC artifact. One F0014 record cites the folder (history). Largest single file under `planning/`. |
| `skeleton.md`, `skeleton-answers.md`, `interfaces.md`, `traceability.md`, `cross-check-1.md`, `fault-paths.md`, `drafter-reports.md` | 7 | The first night's plan of v1.1 (F0001–F0011): skeleton, interface sheet, traceability of the handover conditions, the fault-path table | **archive** | All built. These are the only files that cite the v2 planning (`factory-v2/planning/v1.1/handover.md`, `overnight-run-plan.md`, `decisions/005…`, `006…`): no live file in factory-rf names `factory-v2`. `pyproject.toml` line 16 cites `interfaces.md` (edit below). `skeleton-answers.md` is the record of the main session's working answers, confirmed in questionnaire 1. |
| `handover-plan.md` | 1 | Plan step 5, the handover | **archive** | Done 2026-10-18 (README: "Since the handover of 2026-10-18"); one feature record cites it. |
| `first-start-checklist.md`, `podman-probe-2026-10-17.md` | 2 | First start of v1.1 and the Podman probe | **archive** (or keep, question 3) | `docs/decisions.md` cites them seven times as the source of F0013/F0014 decisions; 13 feature records cite the checklist. Both features built. |
| `opencode-probe-2026-10-17.md`, `write-guard-landlock-2026-10-17.md`, `landlock_probe.py.txt`, `probe-F0019-2026-10-18.md` | 4 | Probes behind F0019 and F0020 | **archive** | F0019 and F0020 built and accepted; F0019's records cite the Landlock probe and `probe-F0019`. |
| `demo-fixes-F0016.md` | 1 | The demo's criterion texts after the shakedown | **archive** | Applied to `demo/` (`d38945f4`); four F0016 records cite it. |
| `morning-2026-10-19.md` | 1 | The morning's 37 questions | **delete** | Answered: F0022–F0025 were built with those answers (their `feature.md` decisions), the baseline-run plan's Q1–Q7 heads that file as "Decided by the human (2026-10-19 morning)", and the evening's answers (21:59, 23:03) settled the rest. The night log holds the record. |
| `night-plan-2026-10-19.md` | 1 | The plan of last night | **delete after Mon 2026-10-20 05:00** | The night ran; but its *standing order* (planning in spare capacity) holds until the weekly reset, Mon 2026-10-20 05:00. After that, nothing in it is live. |
| `baseline-run-plan.md` | 1 | Step 10, the baseline todo run | **keep** | Running now (tag `baseline-v1.1`, night log 22:05 onward). Archive when the run's result is recorded. |
| `restructure-after-f0011.md` | 1 | Despite its name, the **build order of the whole plan** (steps 0–10) plus the deferred tree move | **keep**, with an edit (**merge**, below) | Steps 9 (rename) and 10 (baseline) are still ahead; 11 feature records cite it. Its step 7a still says "mutation testing per story, not per feature". |
| `mutation-sweep-2026-10-19.md`, `-part2.md`, `-part3.md` | 3 | The three sweep reports | **keep** until F0028 is built, then **archive** | F0028's decisions cite their survivors; "sweep everything left" (the human 22:20) continues from part 3's state. |
| `security-review-2026-10-19.md` | 1 | Reading-only security review of the write guard | **keep** until triaged (question 7) | F0027 is built from two of its routes; F0027 is "later". The human said its container tests are not needed (21:59); whether its other rows are closed is not written anywhere. |
| `templates/java-gradle.md`, `templates/typescript-npm.md` | 2 | Designs of two more stack templates, for the human's review | **keep**, with an edit (**merge**, below) | Not reviewed yet. Both still design a "per-story form (F0024's form)" of mutation testing with a 540 s stop (java-gradle lines 25, 82, 120, 146–152, 213, 277; typescript-npm lines 126–128, 194, 205, 207), now retired. |
| `operator-playbook-revised.md` | 1 | The playbook revised from the draft, the review aid and the human's answers | **merge** into `docs/operator-playbook.md` | The human 23:03 (Q6): "the accepted playbook goes to `docs/operator-playbook.md`", named in `CLAUDE.md` *Docs*. |
| `playbook-review-aid.md` | 1 | Review aid for the draft playbook | **merge** (then delete) | Its answers are folded into the revised playbook. |

### planning/ (top level)

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `operator-playbook.md` | 1 | The draft playbook of 2026-10-18 | **merge** (superseded by the revised one, then delete) | Last night's plan still ran by it; the revised version replaces it. Its rule 9 still uses "mutants" as the example. |
| `lessons-for-the-skills.md` | 1 | Rules gained while building, sorted by where they belong for later projects | **keep**, with an edit (**merge**, below) | Live (the session adds a row with every new `CLAUDE.md` rule); `planning/v1-texts/README.md` and 11 records cite it. Rows at lines 18 and 22 say mutation testing "runs at the feature acceptance" and "runs per story (the engine, after the coder …)": both retired. |
| `questionnaires/01-working-answers.md` | 1 | The human's quiz answers of 2026-10-13 on the first night's working answers | **archive** | Record of decisions for F0001–F0011, all built; the binding ones are in `CLAUDE.md` and `docs/decisions.md` (e.g. abstract base classes, 2026-10-13). |
| `v1-texts/` (`README.md`, 7 agents, 13 skills) | 21 | Verbatim copy of v1's role and stage texts at `pkrahmer/factory` `f8bc9d2`, for F0010-S0016 | **archive** | F0010-S0016 is built; the shipped texts are `claude/agents/`. The source exists in v1's own repository. Note: after the rename, "`pkrahmer/factory` at `f8bc9d2`" points at the wrong repository (it becomes v1's new name); the tag keeps the copy reachable either way. |

### docs/

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `docs/operator-guide.md`, `docs/decisions.md`, `docs/project-guide/` (9) | 11 | The documents | **keep** | `factory.domain.documents.DOCUMENT_PATHS`, `make documents`, agents read the guide (`CLAUDE.md`). F0032-S0001 rewrites their mutation passages. |
| `docs/runs/2026-10-12-overnight/night-log.md`, `report.md` | 2 | The human's run record since 2026-10-12 | **keep** | Live (every act is a row); the human's (`CLAUDE.md`). The folder name says 2026-10-12 though the log runs to tonight (question 8). |

### factory/

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `factory/pipeline.yml`, `story-form.md`, `feature-form.md` | 3 | The pipeline definition and forms | **keep** | Read by the factory and the intake. |
| `factory/features/` (F0018–F0026, F0031) | 164 | Work items, journals, cost sidecars | **keep** | The factory's records. `F0024-…/backlog/F0024-S0004-…` is removed by F0032's change 3; the rest of F0024 stays as the record of a decision since reversed. |
| `factory/v1/` (`stages.yml`, `FEATURE.md`, `TICKET.md`, `features/F0001–F0017`) | 223 | v1's history of v1.1's build | **keep** (question 2) | `CLAUDE.md` *Vocabulary*: "Nothing reads it and no stage writes it; leave it as it is." Confirmed: no code or test reads it. `.secrets.baseline` names one file in it. It is the largest group (5.0 MB). |

### The rest

| Path or group | Files | What it is | Verdict | Evidence |
| :- | -: | :- | :- | :- |
| `demo/` | 25 | The shipped todo demo | **keep** | `tests/test_demos.py` runs `check_demos` over it; `tests/test_demo_makefile_secrets.py` reads its `Makefile`. Its `mutants` recipe is the project's own (F0032 decision 10). |
| `template/` | 3 | The project template | **keep** | `tests/test_claude_files.py`, `test_template_makefile.py`, `test_image.py`, `test_claude_agent_texts*.py` read it. |
| `image/` (6, without `secrets/`) | 6 | Dockerfile, compose, entrypoint, sudoers, gitconfig, credential helper | **keep** | Each pinned by a `tests/test_image*.py`, `test_compose_*.py`, `test_entrypoint*.py`. |
| `claude/` (7 agents, `settings.json`) | 8 | The shipped agent texts | **keep** | `tests/shipped_agents.py`, the image. |
| `security/semgrep/python.yml`, `security/duplicates-baseline.txt` | 2 | SAST rules, accepted duplicate findings | **keep** | `make sast`, `make duplicates`. (The morning's Q34, three findings reported gone, is still open in the baseline.) |
| `README.md`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `uv.lock`, `LICENSE`, `.python-version`, `.gitignore` | 8 | Root files | **keep** | All live. Stale passages: `Makefile`'s `mutants` comment ("the factory runs it as a report after the coder", the acceptance-branch mode) and `CLAUDE.md`'s story-branch sentence, both replaced by F0032's changes 1 and 2; `pyproject.toml` line 16 (edit below). `README.md` and `CLAUDE.md` say `factory-rf`, for the rename (step 9). |
| `.secrets.baseline` | 1 | detect-secrets baseline | **keep**, with an edit | It holds an entry for `factory/v1/features/F0013-podman-and-the-token/ongoing/F0013-S0001-…md`, a path that no longer exists (the same file is in `done/`, which has its own entry). |

## The proposed cleanup

Every file below is the human's: `planning/` and `docs/runs/` by `CLAUDE.md`, and `factory/`, the `Makefile`, `pyproject.toml`, `CLAUDE.md` and `.secrets.baseline` because they lie outside every write path in `factory/pipeline.yml` (coder `src/*`, `image/*`, `template/*`, `claude/*`; tester `tests/*`; documenter `README.md`, `docs/*`; the rest only `{work_item}` and `{feature}/backlog/*`). So the cleanup is **human's changes, not a story**, with one optional docs story for the playbook. Nothing here touches F0032's files, and it can go before or after F0032.

### Human's change A: the tag and the deletions (one commit, between two stories)

1. `git tag -a planning-history-2026-10-19 -m "planning/ before the cleanup" <the commit before this one>` and push the tag.
2. `git rm` the **delete** rows: the drafts of F0001–F0017 and the F0019 copy (183 files); the pre-checks of F0001–F0026, the two demo pre-checks and the order note (173); all briefs but `mutation-sweep.md` (137); `audits/` (40); `planning/overnight/demo/` (26); `status-map-mockup/` (5); `morning-2026-10-19.md` (1). 565 files, about 6.5 MB.
3. `git rm` the **archive** rows (37 files, about 0.4 MB): `skeleton.md`, `skeleton-answers.md`, `interfaces.md`, `traceability.md`, `cross-check-1.md`, `fault-paths.md`, `drafter-reports.md`, `handover-plan.md`, `first-start-checklist.md`, `podman-probe-2026-10-17.md`, `opencode-probe-2026-10-17.md`, `write-guard-landlock-2026-10-17.md`, `landlock_probe.py.txt`, `probe-F0019-2026-10-18.md`, `demo-fixes-F0016.md`, `planning/questionnaires/`, `planning/v1-texts/`. A short `planning/README.md` (new, 5 lines) says what `planning/` holds now and that the history is at the tag.
4. Locally: `rmdir` the two empty `backlog/` folders under `planning/overnight/stories/`.
5. After Mon 2026-10-20 05:00: `git rm planning/overnight/night-plan-2026-10-19.md`.

The citations in `docs/decisions.md`, `factory/features/`, `factory/v1/` and the night log stay as they are: they are history, and the tag resolves them.

### Human's change B: the edits to live files (one commit)

1. `pyproject.toml` line 16: "built by the stories named in planning/overnight/interfaces.md (factory.entry)" becomes "each built by the story that introduced it (factory.entry)" or is dropped.
2. `.secrets.baseline`: remove the entry for the `ongoing/` path of F0013-S0001 (then `make secrets` on `main` to confirm green).
3. `planning/lessons-for-the-skills.md` rows 18 and 22: one row instead, "Mutation testing runs only as sweeps outside the factory, on a fresh copy with a fresh `mutants/`; no stage runs it", with the structural-tests deselect kept.
4. `planning/overnight/briefs/mutation-sweep.md`: replace its first sentence (no acceptance runs `make mutants`); after F0032, name `make mutants MODULES=… MUTANTS_SECONDS=… MUTANTS_CHILDREN=…` as the way to run it.
5. `planning/overnight/stories/F0027-…`: drop S0004 and decision 3 (and `kept_ignored` from its human's changes), or mark them withdrawn, if question 5 is answered so.
6. `planning/overnight/templates/*.md`: replace the per-story mutation sections by the sweep form (or leave it to their review, question 9).
7. `planning/overnight/restructure-after-f0011.md`: step 7a gets one line "superseded on 2026-10-19: sweeps only (F0031, F0032)"; optionally rename the file to `planning/build-order.md`, since it is the plan's build order and no longer about the restructure (11 records cite the old name; the tag resolves them).
8. The playbook: `planning/overnight/operator-playbook-revised.md` becomes `docs/operator-playbook.md` (`git mv`), `CLAUDE.md` *Docs* names it as the fifth document, and `planning/operator-playbook.md` and `planning/overnight/playbook-review-aid.md` are removed. `docs/*` is the documenter's write path, so either the human commits the move as the playbook's owner, or a one-story docs feature does it (the documents check, `DOCUMENT_PATHS`, knows four documents; adding the fifth to it is a code change and not needed for the move).

### Later, as each item finishes

- When F0027, F0028 and F0029 move into `factory/features/`: remove their pre-checks under `planning/overnight/precheck/`.
- When F0028 is built: the three sweep reports go to the tag (a second tag, or the next cleanup).
- When the baseline run's result is recorded: `baseline-run-plan.md` likewise.
- At the rename (step 9): question 2.

## Questions for the human

Independent ones first; the recommendation is marked **(rec)**.

**1. Where does the archive live?**
- a. **(rec)** An annotated tag `planning-history-2026-10-19` on the commit before the cleanup. Pro: nothing in the working tree; every citation resolves with `git show <tag>:<path>`; survives the rename. Con: a reader must know the tag (the new `planning/README.md` names it).
- b. A `docs/history/` folder. Pro: visible in the tree. Con: keeps 0.4 MB of old planning under `docs/`, which the documenter's write path covers, and `not_read` would need it.
- c. Plain git history, no tag. Pro: nothing to do. Con: a deleted path is found only with `git log --all -- <path>`.

**2. `factory/v1/` (223 files, 5.0 MB, the largest group).**
- a. **(rec)** Keep it as `CLAUDE.md` says, until the rename; decide then. Pro: no change to a decided rule; the rename is the natural cut. Con: 5 MB stay.
- b. Move it to the tag now. Pro: the biggest single cut. Con: changes `CLAUDE.md` *Vocabulary* and the `.secrets.baseline` entry; the v1.1 feature history F0001–F0017 leaves the tree.

**3. The two planning files `docs/decisions.md` cites (first-start checklist, Podman probe).**
- a. **(rec)** Archive them with the rest; the citations stay as history. Pro: one rule for all. Con: a reader of `decisions.md` must use the tag.
- b. Keep both in `planning/overnight/`. Pro: the citations stay one click away. Con: two finished working notes stay.

**4. F0020-S0009, the deferred story "the factory keeps its spend within a window before each run".**
- a. **(rec)** Keep the draft where it is until the baseline run is done, then decide. Pro: the only copy of an idea that the baseline's cost numbers may make relevant. Con: one stray file in a folder whose feature has moved.
- b. Drop it to the tag now. Pro: the F0020 draft folder is gone. Con: the idea lives only in history.

**5. F0027-S0004 and decision 3 (`kept_ignored: ["mutants/*"]`).**
- a. **(rec)** Withdraw S0004 and decision 3: nothing needs `mutants/` across stages once no stage runs mutation testing. Pro: F0027 shrinks to three stories. Con: an edit to a pre-checked draft.
- b. Keep S0004 as a generic "a project keeps the ignored folders it names". Pro: a feature other projects may want. Con: no user today; F0027's pre-check justified it only by F0024.

**6. The brief templates.**
- a. **(rec)** Delete the five `{{FID}}` templates and `precheck-round-2.md`; if a drafting routine is wanted again, write one generic `draft.md` and one `precheck.md` from `draft-F0026.md` and `precheck-F0026-1.md` before deleting them. Pro: one current pattern instead of six old ones. Con: one small write-up.
- b. Delete them all with no replacement. Pro: nothing to keep. Con: the next drafting helper starts from the night log.

**7. The security review of 2026-10-19.**
- a. **(rec)** Keep it until F0027 is built, then archive it. Pro: F0027 is its follow-up. Con: none.
- b. Say now which of its other rows are closed, then archive. Pro: no open finding hides in `planning/`. Con: a review of 34 lines for you.

**8. `docs/runs/2026-10-12-overnight/`, which now runs from 2026-10-12 to 2026-10-19.**
- a. **(rec)** Leave it; start a new folder with the next run (the baseline or the rename). Pro: no broken citations. Con: the name understates its span.
- b. Rename it `docs/runs/2026-10-12-to-19/`. Pro: honest name. Con: the night plan, the playbook and many records cite the path.

**9. The stack-template designs (`templates/java-gradle.md`, `typescript-npm.md`).**
- a. **(rec)** Fix their per-story mutation sections when you review them. Pro: one pass. Con: they mislead a reader until then.
- b. Fix them now in change B. Pro: no stale design. Con: edits to a text you have not reviewed.

**10. The playbook move (change B, item 8).** Depends on whether the revised playbook is accepted as it stands.
- a. **(rec)** Accept it and move it as the owner, in change B. Pro: one commit; the rules are yours. Con: a document under `docs/` that the documenter did not write.
- b. A one-story docs feature that moves it and names it in the documents. Pro: the documenter keeps `docs/` true. Con: a story for a move; `CLAUDE.md` is still yours to change.
