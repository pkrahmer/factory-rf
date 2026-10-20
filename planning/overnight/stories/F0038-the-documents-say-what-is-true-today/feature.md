# The documents say what is true today

## Goal

A curator reviewed the documents on `main` of 2026-10-20 (`planning/overnight/docs-curation-2026-10-20.md`) and found them accurate in detail but written as a build record more than as a reader's guide: an inventory where the README and the operator guide should open, passages gone stale this week (the template now runs under the write guard, `factory/v1/` is gone, v2 is retired), planning codes nobody can resolve, one stop in three tables, and class names in the operator's guide. The review ranks 7 high, 13 medium and 10 low findings. This feature holds the fixes of the high and medium findings that are still open on `main` after the stories merged since the review (F0023-S0005, F0025-S0004 and S0005, F0031-S0002, F0020-S0013 and S0014; F0031-S0003 running), for the newcomer, the operator and the agents who read the documents. Each story is documents only, one documenter run, a few files, with the exact old and new text where the change is small. When it is done, the README and the operator guide open with what they are, each stop is listed in one table, the operator guide names what the operator sees, the project guide and the decision log point to nothing that left the tree, and every known gap that was "left for v2" is named open. Done when every story below is merged and `make check` is green.

## Scope

- `README.md`: its first paragraph, its commands as a table, the playbook in *Where to look next* (S0002; findings H2, M10, M11).
- `docs/operator-guide.md`: the template and demo paragraph (S0001; H1), the opening, a contents list and the current rule without history, and the init's own heading (S0006; H3, M4 with L9, M13), class and module names and the hypothetical handler case (S0007; M2, M3), the stop tables (S0008; M1).
- `docs/project-guide/`: the template's pipeline definition as a pointer and `factory-health` described and indexed (S0003; H4, the rest of M5), the planning codes and v1 feature ids in the guide files (S0004; M6), every passage of v1.1's own in the shipped agents (S0010; folded in from F0034-S0003).
- `docs/decisions.md`: two superseded marks, the removal of `factory/v1/`, the header sentence on the codes (S0005; H7, M12, M6), a new entry on v2's retirement that points each closed gap to the entry that closed it and names the one open gap, the replaced entry on the project commands renamed *The project commands first ran as the factory's user; replaced*, and the settled kill under `sudo` pointed to its entry (S0009; H6).

## Out of scope

- The low findings L1 to L10 (L1 is F0031-S0003's; L9 is done with M4 in S0006, as M4 names the same passage).
- The review's five structural proposals, the human's to decide: S1 (one stops reference with a subsection per stop, and the operator guide's internals moved to `watching.md`; S0007 and S0008 do only the smallest part), S2 (an index of the decision log and a status line on every entry), S3 (a README of about 40 lines), S4 (a test that pins the project guide's index to the package; a human's change to `[tool.mutmut]` comes with it), S5 (the playbook trimmed and added to the wording check of `make documents`).
- Everything F0032 (mutation testing keeps only its sweep form) rewrites: *Mutation testing* and *The report of a mutation run* in `processes-and-checks.md`, its index line, the operator guide's *Mutation testing by sweep* and its 540 s sentence (L2), the mutation entries of the decision log after *Mutation testing is limited to one feature's modules*, and the playbook's two `make mutants` passages (finding M9, F0032's human's change 6).
- Already fixed on `main`, so dropped: H5 (`README.md` names the tag `planning-history-2026-10-19`, not `factory/v1/`); five of the six modules of M5 (F0025-S0004 and S0005 indexed them); H7's "two F0032 will add to" (F0032-S0001's docs criterion adds those lines).
- `docs/operator-playbook.md` (M7, M8): the human's file, under *The human's changes*.
- `CLAUDE.md`'s R-numbers (M6): they stay, and S0005's header sentence covers them; the agents' rule numbers R10, R14 and R15 stay.
- Every file outside `README.md` and `docs/`: no story changes code, a test, the image, the template, a demo or an agent file.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`. F0032-S0001 is merged (decision 2); by the human's answers all start after F0037, F0030, F0027, F0041, F0040, F0029-S0003 and F0039 are merged, with a pre-check right before.

- S0001: The operator guide says the template and the todo demo run under the write guard
- S0002: The README says what the factory is, that an instance runs in the container, and where to go next
- S0003: The project guide points to the template's pipeline definition and describes `factory-health`
- S0004: The project guide names no planning code or v1 feature id as a pointer
- S0005: The decision log marks two superseded entries, the removal of `factory/v1/`, and where its codes come from
- S0006: The operator guide opens with its contents and states the current rule without its history
- S0007: The operator guide names what the operator sees, not the classes behind it
- S0008: The operator guide lists each stop in one table
- S0009: What was left for v2 is named open and not planned
- S0010: The project guide names every passage of v1.1's own in the shipped agents

## The human's changes

Checked against `factory/pipeline.yml`: the documenter writes `README.md` and `docs/*`, and every story changes only files there. No `Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md` or `.secrets.baseline` change. Outside the stories, in the human's playbook, which no stage keeps (`CLAUDE.md`, *Docs*); at any time, before or after any story:

1. **`docs/operator-playbook.md`, the second paragraph (finding M7).** "Revised on 2026-10-19 from the draft of 2026-10-18, its review aid and the human's answers. Once the human accepts it, it lives at `docs/operator-playbook.md`, and `CLAUDE.md`'s *Docs* names it as the fifth document. " is removed; the paragraph keeps its last two sentences ("Its rules are the human's: ..." and "Each rule marked **(could be code)** ...").
2. **`docs/operator-playbook.md`, *What changed against the draft* (finding M7).** The section, from its heading to the end of the file (49 lines in review-aid codes W, M, S, U, P3, Q and L), moves out of the playbook, to `planning/` or the night log.
3. **`docs/operator-playbook.md`, section 2, the paragraph that begins "**Mutation testing is not part of a feature.**" (finding M8).** F0031 is merged and accepted, so its last sentence, "F0031 (no stage runs mutation testing) takes it out of the acceptance reviewer's text; until it is merged, `CLAUDE.md` already says so.", is removed. The paragraph keeps "No stage and no acceptance runs `make mutants`. Mutation testing runs only as sweeps outside the factory (section 4)."

## Decisions taken for the human

1. **Re-checked on `main` of 2026-10-20 after the merges, and dropped what is fixed.** H5 is fixed (`README.md`, *How it is built*, names the tag). Of M5's six modules only `factory.entry.health` is still missing from the index, and no guide file describes it, so S0003 adds a paragraph to `watching.md` as well. Everything else the review lists as high or medium was still open, line for line. (Feature)
2. **Every story starts after F0032-S0001 is merged.** F0032-S0001 edits `processes-and-checks.md`, the index, the operator guide and the decision log; the review advises this order to avoid merge conflicts, and S0005 leaves the mutation entries' marks to it. (Feature)
3. **The review's seven stories, cut to nine of one documenter run each.** Its story 3 is split into S0003 (two gaps: the template pointer and `factory-health`) and S0004 (the codes, a list of exact replacements); its story 7 into S0007 (the class names, with M3, whose paragraph holds `NOT_YET_HANDLED`) and S0008 (the stop tables), as the review proposes if a pre-check finds it over 40 minutes. S0004 touches six guide files, each in one to six exact replacements. (Feature)
4. **H6 is drafted as "Open, not planned", and the human confirms the wording before S0009 starts.** The review says the documenter records it once the human has decided what v2's retirement means for each gap. The retirement itself is decided (factory-v2's decision 009, 2026-10-19), and "open, not planned" says only that, planning none of the three gaps. Option: the human turns a gap into v1.1 backlog first, and S0009's entry names it. (S0009)
5. **S0009 also points the stale "Open: the kill of a timed-out agent under `sudo`" to the entry that settled it.** It stands in the same paragraph S0009 edits, and *The agent's own `timeout` kills a run under `sudo` at its time limit* (2026-10-17) settled it; the review did not list it. (S0009)
6. **S0004 keeps the requirement numbers that `CLAUDE.md` names (R5, R8) and the agents' rule numbers (R10, R14, R15).** A reader resolves them in `CLAUDE.md` and in every `## Rules` of `claude/agents/`; only R20, R21, R22, R24, R28, the kept things, Q29 and v1's feature ids as pointers go. Example ids (`F0001-S0001`, `F0004-x`, `FEATURE=F0012`) stay. (S0004)
7. **S0007 keeps the names the operator reads in messages.** `SettingsInvalid`, `CannotHandle`, `PushFailed` and `HostingServiceError` appear in reports and refusals, `STOP_TABLE` says what pins *The stops*, and `factory.domain.settings.read_settings` names the one reader of the settings. All other class and module names go, and the project guide already names each. (S0007)
8. **S0008 moves, not drops, what only the six-row table said.** The detail forms of `preflight_failed`, `main_branch_failing` and `repository_unavailable` go to the sections *The stops* points to, so nothing an operator needs is lost with the table. (S0008)
9. **S0006 takes L9 with M4.** M4 lists "decision 008 of factory-v2" itself, so the low finding is the same edit, and " (R2)" in *Configuration*, a planning code the review did not list, goes with it. "A commit that also changes another file clears the stop as before" loses "as before" too. (S0006)
10. **Smoke tests use `make documents 2>&1 | tail -n 1` and `git diff --name-only origin/main`.** The first is the docs stage's own check; the second pins that each story touches only the files it names. Neither was run here: the throwaway container has no network for `uv`'s sync and the copy has no `.git`; `python -m factory.entry.check_documents` printed `documents ok` on today's copy. (Feature)
11. **The number and the name.** F0038 is the first number above every folder in `factory/features/` (F0018 to F0026, F0031) and `planning/overnight/stories/` (F0027 to F0037). (Feature)

## Folded in by the human (2026-10-20)

F0034-S0003 "the project guide names every passage of v1.1's own in the shipped agents" (proposed by F0034-A0002) is folded into this feature; its text, refined, is now `backlog/F0038-S0010-...md`, and `folded/` is gone. The fresh pre-check of 2026-10-20 takes it up as S0010, a story of its own: it needs a search of `git log` that S0004's list of exact replacements does not, and it rewrites the sentence of `agents.md` whose neighbour S0004 changes, so it runs after S0004.

## The human's answers (2026-10-20)

- Order: F0038 is built last, after F0037, F0030, F0027, F0041, F0040, F0029-S0003 and F0039, with a fresh pre-check just before it starts (its quotes will have moved).
- Decision 4 (S0009): when F0038 runs, gaps 1 and 2 are fixed by F0040, gap 4 by F0027, and the hook (gap 5) is gone with F0041. Only gap 3, the clone's working folder and the environment git is started with, stays, named "open, not planned". The "left for v2" sentences of the fixed gaps go or point to the feature that fixed them. The fresh pre-check adapts S0009 to what is then true.
- S0009 also points the stale "Open: the kill of a timed-out agent under sudo" sentence of `docs/decisions.md` to the entry that settled it.
- S0009's criterion on the night logs in `docs/runs/` is dropped: they are the human's history.
- F0034-S0003 is folded in (see above).

## The human's answers to the fresh pre-check (2026-10-20)

- F0034-S0003 becomes S0010, a story of its own, last in the order (the human, 2026-10-20).
- S0009's new entry is titled *v2 is retired; nothing is left for v2*. The replaced entry *The project commands run as the factory's user and are left for v2* is renamed too, *The project commands first ran as the factory's user; replaced*, with a line that points to *The project commands run as the agent user, with the git folder sealed* (the human, 2026-10-20).
- F0027-S0003 removes "(left for v2)" from `docs/project-guide/write-guard.md`, *Limits*; S0009 does not touch that file (the human, 2026-10-20).
- S0007 removes the made-up handler case in *An event that keeps failing*; F0039-S0005 stays as it is (the human, 2026-10-20).
