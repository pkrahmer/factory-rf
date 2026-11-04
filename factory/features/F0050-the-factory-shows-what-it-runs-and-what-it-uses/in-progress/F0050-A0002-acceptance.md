---
stage: acceptance
blocked: null
round: 0
attempts: 0
crashes: 1
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: acceptance
  started_at: '2026-11-04T23:13:50.081285Z'
  lease_duration: 60
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T23:11:57.171834Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-11-04T23:13:48.429173Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-11-04T23:13:50.081285Z'
  stage: acceptance
stories: [F0050-S0001, F0050-S0002, F0050-S0003, F0050-S0004, F0050-S0005, F0050-S0006, F0050-S0007, F0050-S0008, F0050-S0009, F0050-S0010, F0050-S0011, F0050-S0012]
outcome: null
---

# Acceptance of The factory shows what it runs and what it uses

## Journal

1. factory: started acceptance as vm.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit b3db17e4e86a4f6081415ef1d65e51a3dc80fdaa.
3. factory: started acceptance as vm.
