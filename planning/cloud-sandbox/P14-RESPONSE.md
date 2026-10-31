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
