# The project guide names the recovery's commit subjects

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

F0028-S0006 pinned the subjects of a story's recovery commits in tests: `RecoveryHandler.handle` commits a crash as `work item <id>: crash of stage <stage> recorded` and an expiry as `work item <id>: expiry of stage <stage> recorded` (`src/factory/application/recovery.py:102`). Its documenter noticed that no document names these two subjects. `docs/project-guide/watching.md`, *A crash is discarded and the stage is rerun*, step 4, says only that the recorder "makes one commit on top of the remote's head", while the same file names the subject of every other handler commit (`close recorded`, `sent back`, `handed over at <stage>`, `comments from the pull request`, `merged, archived`, the move-back, and `pull request opened` for the draft step 4b and `ask_crash_cap` make). This story is for the agent who reads the guide before changing `recovery.py`, or who reads a branch's log after a crash. It adds the two subjects to step 4. The code, the tests and the other documents stay as they are. It changes no behaviour, so it has no criterion of its own beyond the two closing ones.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The reference the documenter checks against is `src/factory/application/recovery.py:100-104` (the entry kind and the subject) and `tests/application/test_recovery_subjects.py`, which pins them.

## Acceptance criteria

1. `make check` stays green.
2. docs: `docs/project-guide/watching.md`, *A crash is discarded and the stage is rerun*, step 4: the commit's subject is `work item <id>: crash of stage <stage> recorded` for a `crash` and `work item <id>: expiry of stage <stage> recorded` for an `expired`, where `<stage>` is the stage the work item was in. Step 4b keeps its `pull request opened`. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because they describe what an operator sees and decides, and no subject or behaviour changes.

## Smoke test

```bash
g=docs/project-guide/watching.md
for s in 'crash of stage <stage> recorded' 'expiry of stage <stage> recorded' 'pull request opened'; do grep -qF -e "$s" "$g" && echo found || echo "missing: $s"; done
```
Expect: three lines `found` (both recovery subjects and the draft's subject are in the guide)

```bash
uv run -q python - <<'EOF'
from factory.application.handlers.recording import commit_subject
print(commit_subject("F0001-S0001", "crash of stage doing recorded"))
EOF
```
Expect: `work item F0001-S0001: crash of stage doing recorded` (the form the guide now gives)

## Journal
