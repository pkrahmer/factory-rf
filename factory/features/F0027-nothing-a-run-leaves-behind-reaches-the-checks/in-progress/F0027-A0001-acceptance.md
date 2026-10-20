---
stage: acceptance
blocked: crash_cap
round: 0
attempts: 0
crashes: 2
pull_request: null
comments_read: []
handed_over: null
claim: null
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
