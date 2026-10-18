---
stage: acceptance
blocked: crash_cap
round: 0
attempts: 0
crashes: 2
pull_request: 226
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-10-18T17:31:19.105372Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-10-18T18:04:46.816289Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-10-18T18:04:48.291413Z'
  stage: acceptance
- number: 4
  speaker: factory
  kind: crash
  at: '2026-10-18T18:34:42.629819Z'
  stage: acceptance
- number: 5
  speaker: factory
  kind: question
  at: '2026-10-18T18:34:42.629819Z'
  stage: acceptance
stories: [F0019-S0001, F0019-S0002, F0019-S0003, F0019-S0004, F0019-S0005, F0019-S0006]
outcome: null
---

# Acceptance of The write guard by the kernel

## Journal

1. factory: started acceptance as self.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit 2f4512b15e7f5a3075b1b3656a6660a123a6d16b.
3. factory: started acceptance as self.
4. factory: crash 2: the run of stage acceptance ended without a result. Its work is discarded back to commit 5b401fe6a0620fd5a21b22b88e030251443a4f2a.
5. factory: Stage acceptance crashed 2 times, which is the crash cap of 2. The factory has not rerun it. Write a comment here and the stage reruns with the crash counter reset to 0 (your comment is copied into the journal). Close the pull request to discard the story instead: it goes back to the backlog as you wrote it, and its branch and bill are deleted.
