#!/bin/bash
# Runs one probe as a throwaway Cloud Run job: create it, run it once, print its log, delete it.
#
#   run_probe.sh <name> <image> <script> [cpu] [memory] [gen1|gen2]
#
# Everything environment-specific comes from the environment, nothing is written into this file:
#   PROBE_PROJECT      the project id
#   PROBE_REGION       the region (default us-central1)
#   PROBE_IMPERSONATE  (optional) a service account to impersonate for every call
#   PROBE_RUN_AS       (optional) the service account the job runs as (default: the project's default)
#   PROBE_CONNECTOR    (optional) a serverless VPC connector, full resource name
#   PROBE_PROXY        (optional) an HTTP proxy URL the job's scripts use for downloads
#   PROBE_EXTRA_ARGS   (optional) more arguments for `gcloud run jobs create`, split on spaces
#                      (for example a volume: --add-volume=name=d,type=ephemeral-disk,size=10Gi ...)
#
# The job has no ingress, no schedule and no retries; it is deleted at the end, also when it failed.
set -u
name=$1; image=$2; script=$3; cpu=${4:-2}; memory=${5:-4Gi}; gen=${6:-gen2}
region=${PROBE_REGION:-us-central1}
here=$(cd "$(dirname "$0")" && pwd)
job="probe-$name"
impersonate=()
[ -n "${PROBE_IMPERSONATE:-}" ] && impersonate=(--impersonate-service-account="$PROBE_IMPERSONATE")
common=(--project="$PROBE_PROJECT" --region="$region" "${impersonate[@]}")

# The script is shipped inside the job's arguments: lib.sh and the probe, gzipped and base64-coded.
payload=$(cat "$here/lib.sh" "$here/$script" | gzip -9 | base64 | tr -d '\n')
create=(gcloud run jobs create "$job" "${common[@]}" --image="$image"
  --execution-environment="$gen" --cpu="$cpu" --memory="$memory" --max-retries=0 --task-timeout=1500
  --set-env-vars="PROBE_PROXY=${PROBE_PROXY:-}"
  --command=sh --args="-c,echo $payload | base64 -d | gzip -d > /tmp/probe.sh; sh /tmp/probe.sh")
[ -n "${PROBE_RUN_AS:-}" ] && create+=(--service-account="$PROBE_RUN_AS")
[ -n "${PROBE_EXTRA_ARGS:-}" ] && create+=($PROBE_EXTRA_ARGS)
[ -n "${PROBE_CONNECTOR:-}" ] && create+=(--vpc-connector="$PROBE_CONNECTOR" --vpc-egress=all-traffic)

cleanup() { gcloud run jobs delete "$job" "${common[@]}" --quiet >/dev/null 2>&1; }
trap cleanup EXIT

echo "== creating $job ($image, $cpu cpu, $memory, $gen)"
if ! out=$("${create[@]}" 2>&1); then echo "CREATE FAILED:"; echo "$out" | grep -v "WARNING: This command" | tail -12; exit 2; fi
exec_name=$(gcloud run jobs execute "$job" "${common[@]}" --async --format="value(metadata.name)" 2>&1 | grep -v "WARNING: This" | tail -1)
echo "== execution $exec_name"
for _ in $(seq 1 100); do
  state=$(gcloud run jobs executions describe "$exec_name" "${common[@]}" --format="value(status.runningCount,status.succeededCount,status.failedCount,status.completionTime)" 2>/dev/null | tail -1)
  case "$state" in *Z*) break;; esac
  sleep 15
done
echo "== final state: [$state] (running, succeeded, failed, completion)"
gcloud run jobs executions describe "$exec_name" "${common[@]}" --format="value(status.conditions[0].message)" 2>/dev/null | head -3 | cut -c1-300
sleep 8
gcloud logging read "resource.type=cloud_run_job AND labels.\"run.googleapis.com/execution_name\"=$exec_name" \
  --project="$PROBE_PROJECT" "${impersonate[@]}" --order=asc --limit=6000 --format="value(textPayload)" 2>/dev/null \
  | grep -a -v '^$' | awk '/=====BEGIN-RESULTS=====/{p=1;next} p'
