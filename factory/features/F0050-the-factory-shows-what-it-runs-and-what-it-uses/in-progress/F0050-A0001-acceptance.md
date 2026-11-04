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
  started_at: '2026-11-04T20:52:01.427505Z'
  lease_duration: 60
journal:
- number: 1
  speaker: factory
  kind: started
  at: '2026-11-04T20:50:16.505539Z'
  stage: acceptance
- number: 2
  speaker: factory
  kind: crash
  at: '2026-11-04T20:51:59.833506Z'
  stage: acceptance
- number: 3
  speaker: factory
  kind: started
  at: '2026-11-04T20:52:01.427505Z'
  stage: acceptance
stories: [F0050-S0001, F0050-S0002, F0050-S0003, F0050-S0004, F0050-S0005, F0050-S0006, F0050-S0007, F0050-S0008]
outcome: null
---

# Acceptance of The factory shows what it runs and what it uses

## Journal

1. factory: started acceptance as vm.
2. factory: crash 1: the run of stage acceptance ended without a result. Its work is discarded back to commit e2779058da94711faf7d42938951dd69e8efe50b.
3. factory: started acceptance as vm.
