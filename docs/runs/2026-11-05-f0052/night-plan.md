# Night plan, 2026-11-05: the documents features

The human approved this plan on 2026-11-05, about 21:55Z.

## Order

1. F0052 (a documents-only story takes the docs route): S0001, S0002, S0003, then its acceptance. At S0002's merge, the human's change: the docs route in `factory/pipeline.yml` (with `docs-only: next: [docs-review, tests]`) and `intake: next: [tests, docs-only]`.
2. F0053 (the documents are checked against the code): S0001, S0002, S0003, S0006, S0004, S0005, S0007, then its acceptance. At S0005's merge, the human's change: the docs criterion in `factory/story-form.md`. If S0003 asks: the examples run as processes inside the check container, through the one process module, not as containers of their own.
3. F0054 (the documents are rewritten for their readers): only after F0052 and F0053 are accepted, and only while the usage allows.

## Limits

- No spending cap (subscription).
- A story starts only while the 5-hour window is at or below 95 % and the weekly at or below 90 %; above them, the story in flight finishes and nothing new starts.

## The heartbeat

- A coded watcher (`night_watch.sh` in the session's scratchpad) polls the VM every 2 minutes and wakes Claude only on an approval stage, a posted question, a stop, a new `iteration failed`, or after 3 hours. A new stage alone wakes nobody.
- An emergency heartbeat every 30 minutes checks only that the watcher still runs (its beat file is under 10 minutes old) and that nothing waits unseen; it is silent when all is well.
- After each wake-up that changed something, the status block goes to the human by push notification.

## At each approval

The six checks, the merge, the archive commit, factory-vm moved to `origin/main` (only with no PR open and no claim held), the next start, the watcher again. Questions within the feature's decisions are answered; real alternatives wait for the human, and other work goes on.

## Frugal

One eval per feature after its acceptance, not per story; transcripts copied at a feature's end; the board read for the current feature only.

## Stops for the human

A question with real alternatives, a stop or stall without a clear cause, a round cap, a fault in the code that F0054 finds.
