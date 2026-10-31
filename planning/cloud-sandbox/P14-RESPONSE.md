# P14 response (2026-10-31): the probe has a bug, S0007 is not yet judged

For whoever corrects `probes/p14-opencode-lockdown.sh`. Result: `results/p14-opencode-lockdown.txt`; summary: the
last section of `capabilities.md`.

## Verdict

None. opencode never ran, so the two host lists are both empty and say nothing about S0007's key
`enabled_providers` or its three switches. The run itself worked (job created, run, deleted; token request 200;
logging proxy self-test passed; the install of opencode-ai 1.19.3 contacted only the package mirror and the npm
registry through the logging proxy; the binary printed 1.19.3). No model call was made, so no cost was reported.

## The bug and the fix

1. In `one_run`, the extra words (`-e OPENCODE_CONFIG=...`, and for run B the three `-e OPENCODE_DISABLE_...=1`)
   are appended to `$CRUN`, whose last word is the image name. Podman reads everything after the image as the
   command, so the container ran `node OPENCODE_CONFIG=/work/state/plain.json ...` and failed with
   "Unknown regular expression flags" in runs A and B and in section D. Build the `podman run` words with the
   image and the command last, for example keep the options in one variable and the image in another:
   `$PODMAN_RUN_OPTIONS "$@" $IMG sh -c '...'`.
2. Section D's one-switch loop has the same placement and the same failure.
3. The probe's "config complaints" count matches its own search pattern against the node error, so it reported 2
   per run. After the fix, match only opencode's stderr and events, and print the lines.
4. The metadata-block rule file in the probe is written with both chains on one line each; nft rejects it
   ("syntax error, unexpected '}'"), so the rule was not in force. Write it one statement per line, as in
   `p2b-network-followup.sh` and `p10-opencode.sh`. This does not affect the host list.

## Nothing wrong found in the reading

Decisions 7, 14, 15 and 16 of the feature, the README's "Reproducing a probe" section and the probe's header
agree with each other, and decision 14 names this probe.

## To judge S0007 after the fix

S0007 is right if run B lists neither a models catalogue host nor an npm registry nor the vendor's site, ends with
a parsing result block and creates `hello.txt`, and no line complains about `enabled_providers`. Run it with
the same inputs as P10 (the model API's host in `PROBE_NO_PROXY`, the mounted secret, the token variables).

## Answer from home (2026-10-31, after the fix)

Your report was exact, and the bug was mine: `CRUN` ended in the image name, so every run's `-e` words became the container's command, and I wrote the nft chains on one line. Both are fixed on `main` in commit `d85390191`: the options and the image are two variables now, each run puts its `-e` words between them (`$CRUN "$@" -e OPENCODE_CONFIG=... $IMG sh -c ...`, the same in section D), the nft file is one statement per line as in P10, and the "config complaints" count is gone; the probe prints opencode's own lines about the configuration instead. Nothing else in the probe changed.

Please run it again, with the same inputs as the first time:

1. `git pull --ff-only`, read the probe once more and confirm it does what your section *The bug and the fix* asked. If it does not, stop and write what is missing below this answer.
2. Run it exactly as before: `planning/cloud-sandbox/probes/run_probe.sh opencode-lockdown docker.io/library/debian:trixie-slim p14-opencode-lockdown.sh 4 8Gi`, with the P10 environment (the API's host in `PROBE_NO_PROXY`, the mounted secret, the token variables), taken from your shell history or notes, never from a file in this repository.
3. Keep the first run's file as `results/p14-opencode-lockdown-run1-failed.txt` and write the new log to `results/p14-opencode-lockdown.txt`, read from top to bottom with the same masking rules as before (company hosts become `<company-host>`; the "HOSTS CONTACTED" lines stay otherwise intact).
4. Replace the P14 section at the end of `capabilities.md` with the new findings: the two host lists side by side, whether run B still worked (`result block parses`, `hello.txt`), what opencode 1.19.3 said about `enabled_providers`, which of the three switches changed the host list on its own (section D), the cost the run reported, and your one-sentence verdict against the probe's own VERDICT line.
5. Delete this file in the same commit: its content then lives in that section. Commit the three files (the two result files, `capabilities.md`) and the deletion with the message `planning: cloud sandbox: P14 second run, what opencode contacts with and without S0007's lockdown`, stage only those, push to `main`, and report in the chat as before.

The same rules bind: no company value in any file of this repository, no secret printed or committed, no change outside `planning/cloud-sandbox/`, nothing created in the cloud project beyond the one throwaway job the script makes and deletes.
