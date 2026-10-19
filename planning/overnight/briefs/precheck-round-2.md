# Brief: pre-check round 2 of a drafted feature, after its edits (the human's word, 2026-10-19)

The feature named in your prompt (one of F0022 to F0026 under `planning/overnight/stories/`) was pre-checked in round 1 (`planning/overnight/precheck/<feature>-*-1.md`), then edited by fix agents with the human's answers (the closing decision of its `feature.md` names them), and its docs criteria were reworded to the split project guide (`docs/project-guide/README.md` and the files it names).

## Goal

Play v1.1's intake exactly on each story (the shipped `claude/agents/intake.md` with `factory/story-form.md`, both as they are on `main` now), and predict whether a later role would stop it. Check above all what the edits may have broken: a criterion renumbered but still referred to by its old number; a leave or an Interface sentence that no longer matches the criteria; a smoke test whose `Expect:` no longer follows from the edited text; a docs criterion that names a guide file or section that does not exist (check against `docs/project-guide/README.md`'s list); a contradiction between the story and the feature's decisions; anything round 1's verdict asked for that is missing. Check the code facts again against today's `main`, which moved since round 1 (F0020-S0001 to S0005 and F0025 merged): the records contract's version, the modules and tests the story names, the protected paths. Run each smoke test against today's code where it can run before the story, in a throwaway container if it needs Linux.

## Output

One file per story, `<story id>-2.md`, and `<feature id>-feature-2.md`, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`: the intake outcome, predicted stops, and a `## Verdict` line with the exact replacement text for each finding. Findings only, no restatement of round 1.

## Not

No git commands in the repository; no network; no sub-agents; no paid model call; no file other than your outputs and your temporary folder `C:/Users/pasca/AppData/Local/Temp/<short name given in your prompt>`, removed at the end; do not change the stories. The test suite does not run on Windows (`tests/conftest.py` imports Linux-only support): run tests and smoke tests in throwaway containers of the image `factory-self-factory` on a copy in your temporary folder (`MSYS_NO_PATHCONV=1 docker run --rm --network none --entrypoint /bin/sh -v <copy>:/src factory-self-factory -c '...'`), never in the running `factory-self-factory-1`; mount no volume and no secret; never read a token or key file. `factory-check-story` imports the Landlock adapter: stub it in your temporary folder.

## Reply

Per story its verdict line and each finding's fix in one line; whether the feature is ready to build.
