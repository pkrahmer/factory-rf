# The decision log and the contract's history match the feature

<!-- proposed by feature acceptance of 2026-11-04; refine before starting -->

## Description

Two texts that F0050 left behind no longer say what the factory does. First, the decision log's S0005 entry, "A run's transcript is kept in the transcript folder" (`docs/decisions.md:1523`), says that "a `tmpfiles.d` rule on a VM and a lifecycle rule on a bucket" remove old transcripts (feature decision 10). Feature decision 11 then dropped the VM's rule, and `docs/operator-guide.md` (*Transcripts*, *On a VM*) says there is none. The log has no entry for decision 11, because S0007's docs criterion asked for none. Second, the records contract's version list in `docs/operator-guide.md` (*The records contract*, *The version*) goes from `4.0` straight to `4.2`. `4.1` came with F0049-S0002 (commit `4796912ee`) and added the stop reason `stage_image_failed` to the `reason` of `stop-record`. The F0050-S0002 documenter saw the gap and could not tell what `4.1` was. This story repairs both texts. It changes no code and no test.

## Interface

- No module under `src/factory/` changes, and no test is written: the criteria are about documents only. The document check of the docs stage (`make documents`) and `make check` are the gate.
- `docs/decisions.md`: a new entry for feature decision 11, in the log's form (Date, Decision, Why, and Rejected when the story names a rejected option). The S0005 entry's sentence about deletion gets a pointer to it. The log's history is not rewritten: the old sentence stays and says that S0007 replaced its VM half.
- `docs/operator-guide.md`: the version list names `4.1`.

## Acceptance criteria

1. `docs/decisions.md` has one entry whose Decision says that a VM keeps no retention of transcripts, with no `tmpfiles.d` rule and no option for an age, and that a Cloud Run bucket keeps its lifecycle rule. Its Why gives the human's reason of 2026-11-04 (about 5 MB per feature). It names F0050-S0007.
2. The S0005 entry's sentence on the `tmpfiles.d` rule is followed by a note that the VM's half was replaced, naming the new entry. No other sentence of that entry changes.
3. The version list of the records contract in `docs/operator-guide.md` has, between `4.0` and `4.2` and in the list's own wording, `` `4.1` added the stop reason `stage_image_failed` to the `reason` of `stop-record` ``.
4. `make check` stays green.
5. docs: as criteria 1 to 3, in `docs/decisions.md` and `docs/operator-guide.md`. `README.md` and the project guide: none.

## Smoke test

```bash
grep -c '`4\.1` added' docs/operator-guide.md
grep -c 'tmpfiles.d' docs/decisions.md | awk '{print ($1>=2)}'
grep -c 'F0050-S0007' docs/decisions.md | awk '{print ($1>=1)}'
```

Expect: `1`, then `1`, then `1` (on `main` before the story: `0`, `0`, `0`).

## Journal
