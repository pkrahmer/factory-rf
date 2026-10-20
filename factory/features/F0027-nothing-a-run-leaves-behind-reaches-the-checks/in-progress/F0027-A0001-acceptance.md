---
stage: acceptance
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 356
comments_read: [6297132845]
handed_over: null
claim:
  instance: self
  stage: acceptance
  started_at: '2026-10-20T17:36:33.162209Z'
  lease_duration: 60
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-20T15:38:05.333239Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-10-20T16:44:35.650555Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-10-20T16:44:37.093008Z'
  stage: acceptance
- number: 4
  speaker: factory
  kind: crash
  at: '2026-10-20T17:25:59.173641Z'
  stage: acceptance
- number: 5
  speaker: factory
  kind: question
  at: '2026-10-20T17:25:59.173641Z'
  stage: acceptance
  blocked: crash_cap
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-20T17:36:15.127696Z'
  stage: acceptance
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-20T17:36:33.162209Z'
  stage: acceptance
stories: [F0027-S0001, F0027-S0002, F0027-S0003]
outcome: null
---

# Acceptance of Nothing a run leaves behind reaches the checks

## Journal

1. factory: started acceptance as self.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit 8c406d04d470c9c11a83352556d4dc5a9a91f306.
3. factory: started acceptance as self.
4. factory: crash 2: the run of stage acceptance ended without a result. Its work is discarded back to commit 9f6ba8ae52f9f4c39614d79f16de7ec7b29fab24.
5. factory: Stage acceptance crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
6. 2026-10-20 human: Rerun (2026-10-20). Both crashes were the restore's `git clean -X` failing on `.venv/lib/python3.12/site-packages/__pycache__/`, written 755 by a test child of the reviewer's `make check` (three test helpers start the checkout's Python without `-B` under the tests' umask 022). `main` now exports `UV_COMPILE_BYTECODE=1` in the `Makefile` (fd0fcd0b), so uv writes that bytecode group-writable at its sync. Note it as a finding: the three helper lines (`tests/adapters/test_claude_runtime_os_user.py:81`, `tests/confine_support.py:114`, `tests/process_support.py:29`) still lack `-B`.
7. factory: started acceptance as self.
