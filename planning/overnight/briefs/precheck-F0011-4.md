# Brief: F0011 pre-check round 4, against what F0010's repairs changed

## Goal

F0011's five drafts passed pre-check round 3 (`planning/overnight/precheck/F0011-3.md`) at commit `f2fb640`. Since then F0010's repair stories S0018 to S0024 changed the code, the tests and the documents (list below). Decide, story by story, whether any of these changes makes a F0011 story stop at one of v1's roles, or makes one of its statements false. Do not re-audit what did not change.

## Inputs (read these; nothing else unless a step needs a named source file)

- The drafts: `C:\Dev\Projects\factory-rf\factory\features\F0011-proof-and-documents\drafts\` (five files) and `FEATURE.md` beside `drafts\`.
- Round 3's report: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0011-3.md`.
- What changed since `f2fb640`: run `git -C C:\Dev\Projects\factory-rf diff f2fb640..origin/main -- src tests docs README.md CLAUDE.md claude` (read-only git is allowed for this one command and `git show`). The changed files are `README.md`, `CLAUDE.md`, `claude/settings.json`, `docs/operator-guide.md`, `docs/project-guide.md`, `src/factory/entry/run.py`, `tests/adapters/claude_stand_in.py`, `tests/adapters/test_claude_runtime_os_user.py`, `tests/application/test_scheduler.py`, `tests/entry/test_run.py`, `tests/test_claude_files.py`, `tests/test_claude_settings_git.py`.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\` (`factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, each `<name>\SKILL.md`) and `C:\Dev\Projects\factory\claude\agents\*.md`, only where a finding needs the exact rule.
- `C:\Dev\Projects\factory-rf\planning\lessons-for-the-skills.md`: the lessons so far, as a checklist.

## Check in particular

- S0005 (the four documents): its document check reads `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` and `docs/decisions.md` with lists of replaced phrases and v1 words, and requires table rows by id. Run its lists, as the draft states them, against today's four documents, and name every line the new text would now report or every required row it no longer finds. Say whether the story's own documentation work still covers each.
- S0004 (the stop table) and S0001 to S0003 (kill points, fault paths): any stop, log line, end reason or name they rely on that `entry/run.py` (S0019: status 2 and two lines when the state directory cannot be written), the scheduler (S0021: every error of an iteration counts as idle) or the runtime (S0022, S0024: a timed-out call with a `sudo:` line, a `sudo:` line only at column 0) changed.
- A test name or wording the whole-code searches refuse (round 3 found `retrying`): check the new test names F0011 asks for against `tests/test_test_names.py` and `tests/test_retrying_wording.py` as they are now.
- Each Demo whose output depends on a changed file: run it against today's code in a temporary directory outside the repository with `uv run --project C:\Dev\Projects\factory-rf python ...` and say what it prints.

## Output

One file, `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0011-4.md`: per story, the predicted stops caused by the changes (or "none"), a `## Verdict` line, and the exact replacement text for each refusal and each recommended edit.

## Not

- No git command other than the read-only `diff` and `show` named above. No file other than the output. Do not change the drafts.

## Reply

The verdict per story and, for each refusal or edit, its fix in one line.

Model: opus.
