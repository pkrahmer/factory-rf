#!/bin/bash
# Runs one probe in a throwaway Cloud Run worker pool: deploy it with one instance, watch it, scale it to
# zero and back to one, read its log after each phase, delete it.
#
#   run_worker_pool.sh <name> <image> <script> [cpu] [memory]
#
# The same environment as run_probe.sh (PROBE_PROJECT, PROBE_REGION, PROBE_IMPERSONATE, PROBE_RUN_AS,
# PROBE_CONNECTOR, PROBE_PROXY, PROBE_NO_PROXY, PROBE_MODEL, PROBE_EXTRA_ARGS); nothing is written here.
# PROBE_WATCH_SECONDS (default 240): how long each phase is watched.
#
# Corrected at work 2026-10-31: `gcloud run worker-pools` is GA (no beta), `--instances` replaces `--scaling`, no connector flag.
# Written at home without a worker pool to try it on (2026-10-31). The gcloud words below are the best
# knowledge of the time, not tested: before the first run, read `gcloud run worker-pools --help`,
# `... deploy --help` and `... update --help`, and correct the words of `deploy`, the scaling flag and
# the log filter where they differ. Say in the response what you changed.
set -u
name=$1; image=$2; script=$3; cpu=${4:-2}; memory=${5:-4Gi}
region=${PROBE_REGION:-us-central1}
watch=${PROBE_WATCH_SECONDS:-240}
here=$(cd "$(dirname "$0")" && pwd)
pool="probe-$name"
impersonate=()
[ -n "${PROBE_IMPERSONATE:-}" ] && impersonate=(--impersonate-service-account="$PROBE_IMPERSONATE")
common=(--project="$PROBE_PROJECT" --region="$region" "${impersonate[@]}")

payload=$(cat "$here/lib.sh" "$here/$script" | gzip -9 | base64 | tr -d '\n')
deploy=(gcloud run worker-pools deploy "$pool" "${common[@]}" --image="$image"
  --cpu="$cpu" --memory="$memory" --instances=1
  --set-env-vars="^@^PROBE_PROXY=${PROBE_PROXY:-}@PROBE_NO_PROXY=${PROBE_NO_PROXY:-}@PROBE_MODEL=${PROBE_MODEL:-}"
  --command=sh --args="-c,echo $payload | base64 -d | gzip -d > /tmp/probe.sh; exec sh /tmp/probe.sh")
[ -n "${PROBE_RUN_AS:-}" ] && deploy+=(--service-account="$PROBE_RUN_AS")
[ -n "${PROBE_EXTRA_ARGS:-}" ] && deploy+=($PROBE_EXTRA_ARGS)
# Worker pools have no --vpc-connector flag (gcloud 590, 2026-10-31): only Direct VPC egress. PROBE_CONNECTOR is
# ignored; PROBE_NETWORK and PROBE_SUBNET (both optional) switch Direct VPC egress on.
[ -n "${PROBE_NETWORK:-}" ] && deploy+=(--network="$PROBE_NETWORK" --subnet="${PROBE_SUBNET:-$PROBE_NETWORK}" --vpc-egress=all-traffic)

cleanup() { gcloud run worker-pools delete "$pool" "${common[@]}" --quiet >/dev/null 2>&1; }
trap cleanup EXIT

since=$(date -u +%Y-%m-%dT%H:%M:%SZ)
logs() {  # every line the pool printed since $1
  gcloud logging read "resource.type=cloud_run_worker_pool AND resource.labels.worker_pool_name=$pool AND timestamp>=\"$1\"" \
    --project="$PROBE_PROJECT" "${impersonate[@]}" --order=asc --limit=4000 --format="value(timestamp,textPayload)" 2>/dev/null \
    | grep -a -v '^$' | grep -a -E 'probe:|=====BEGIN|PROBE DONE|SIGTERM' | cut -c1-260
}

echo "== deploying $pool ($image, $cpu cpu, $memory, one instance)"
if ! out=$("${deploy[@]}" 2>&1); then echo "DEPLOY FAILED:"; echo "$out" | tail -12; exit 2; fi
echo "== phase 1: one instance, watched for $watch s (the probe exits 0 after its checks: does the pool restart it?)"
sleep "$watch"
logs "$since"

mark=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "== phase 2: scaled to zero at $mark, watched for $watch s"
gcloud run worker-pools update "$pool" "${common[@]}" --instances=0 2>&1 | tail -2
sleep "$watch"
logs "$mark"

mark=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "== phase 3: scaled back to one at $mark, watched for $watch s"
gcloud run worker-pools update "$pool" "${common[@]}" --instances=1 2>&1 | tail -2
sleep "$watch"
logs "$mark"
echo "== deleting $pool"
