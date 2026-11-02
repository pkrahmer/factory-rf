#!/bin/sh
# The factory's Cloud Run job, from the site's values: create, update, execute and delete it.
#   job.sh create  [--dry-run]   create the job; refused when it exists
#   job.sh update  [--dry-run]   update the job with the same settings; refused when it is missing
#   job.sh execute               start an execution; refused while one runs; print its name
#   job.sh delete  [--yes]       delete the job, which stops its running execution
# --dry-run prints the call, one argument per line, and runs no gcloud.
set -u
operator=$(dirname "$0")/..
repository=$operator/..
. "$operator/lib/site.sh"

image=docker.io/library/debian:trixie-slim
hosting_mount=/secrets/hosting-token
model_mount=/secrets-llm/client-secret
start_script=/tmp/job-start.sh
start_end=JOB_START_SH_END

usage() {
  echo "usage: job.sh create [--dry-run] | update [--dry-run] | execute | delete [--yes]" >&2
  exit 2
}

# Every call names its project and region, so gcloud's own defaults never pick them.
gcloud_call() {
  set -- "$@" "--project=$SITE_PROJECT" "--region=$SITE_REGION"
  if [ -n "${SITE_IMPERSONATE:-}" ]; then
    set -- "$@" "--impersonate-service-account=$SITE_IMPERSONATE"
  fi
  if [ "$dry_run" = yes ]; then
    printf '%s\n' gcloud "$@"
  else
    gcloud "$@"
  fi
}

require_job() {
  site_load || exit
  site_require SITE_PROJECT SITE_REGION SITE_JOB || exit
}

require_settings() {
  site_load || exit
  site_require SITE_PROJECT SITE_REGION SITE_RUN_AS SITE_CONNECTOR SITE_PROXY SITE_NO_PROXY \
    SITE_JOB SITE_INSTANCE SITE_REPOSITORY_URL SITE_CODE_URL SITE_CODE_REF \
    SITE_HOSTING_SECRET SITE_MODEL_SECRET SITE_MODEL_BASE_URL SITE_MODEL \
    SITE_LOGIN_URL SITE_LOGIN_SCOPE SITE_LOGIN_CLIENT_ID || exit
}

# The instance's name becomes a path in the shell text the job runs, so it holds no shell syntax.
check_instance() {
  case $SITE_INSTANCE in
    *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-]*)
      echo "job: SITE_INSTANCE may hold only letters, digits, '.', '_' and '-'" >&2
      exit 1
      ;;
  esac
}

# A value holding the env list's delimiter would split into entries of its own.
check_env_values() {
  for name in SITE_REPOSITORY_URL SITE_CODE_URL SITE_CODE_REF SITE_PROXY SITE_NO_PROXY SITE_MODEL \
    SITE_LOGIN_URL SITE_LOGIN_SCOPE SITE_LOGIN_CLIENT_ID SITE_IDLE_MINUTES; do
    case $(site_value "$name") in
      *@*)
        echo "job: $name holds '@', the delimiter of the job's env list" >&2
        exit 1
        ;;
    esac
  done
}

# NaN, infinity or a negative price would make the provider file invalid or wrong.
check_costs() {
  for name in SITE_MODEL_INPUT_COST SITE_MODEL_OUTPUT_COST; do
    case $(site_value "$name") in
      *[!0123456789.]* | *.*.* | .)
        echo "job: $name is not a number" >&2
        exit 1
        ;;
    esac
  done
}

job_root() {
  printf '%s' "/srv/factory/$SITE_INSTANCE"
}

env_list() {
  root=$(job_root)
  models="opus=site/$SITE_MODEL,sonnet=site/$SITE_MODEL,haiku=site/$SITE_MODEL"
  printf '^@^'
  printf '%s' "FACTORY_INSTANCE=$SITE_INSTANCE" \
    "@FACTORY_REPOSITORY_URL=$SITE_REPOSITORY_URL" \
    "@FACTORY_CODE_URL=$SITE_CODE_URL" \
    "@FACTORY_CODE_REF=$SITE_CODE_REF" \
    "@FACTORY_TOKEN_FILE=$hosting_mount" \
    "@HTTPS_PROXY=$SITE_PROXY" \
    "@https_proxy=$SITE_PROXY" \
    "@HTTP_PROXY=$SITE_PROXY" \
    "@http_proxy=$SITE_PROXY" \
    "@NO_PROXY=$SITE_NO_PROXY" \
    "@no_proxy=$SITE_NO_PROXY" \
    "@FACTORY_CONTAINER_ENV=HTTPS_PROXY,https_proxy,HTTP_PROXY,http_proxy,NO_PROXY,no_proxy" \
    "@FACTORY_OPENCODE_PROVIDER_FILE=$root/provider.json" \
    "@FACTORY_OPENCODE_MODELS=$models" \
    "@FACTORY_API_LOGIN_FILE=$root/api-login" \
    "@FACTORY_TOKEN_URL=$SITE_LOGIN_URL" \
    "@FACTORY_TOKEN_SCOPE=$SITE_LOGIN_SCOPE" \
    "@FACTORY_TOKEN_CLIENT_ID=$SITE_LOGIN_CLIENT_ID" \
    "@FACTORY_TOKEN_CLIENT_SECRET_FILE=$model_mount" \
    "@FACTORY_IDLE_SHUTDOWN_MINUTES=${SITE_IDLE_MINUTES:-60}"
}

# The job's image has no python3, so the provider file is made here and travels as text.
provider_json() {
  python3 -c '
import json, sys

base_url, model, input_cost, output_cost = sys.argv[1:]


def number(text):
    value = float(text)
    return int(value) if value.is_integer() else value


entry = {
    "name": model,
    "context": 200000,
    "output": 16000,
    "input_cost": number(input_cost),
    "output_cost": number(output_cost),
}
provider = {
    "id": "site",
    "base_url": base_url,
    "api_key_env": "ANTHROPIC_API_KEY",
    "models": {model: entry},
    "small_model": "site/" + model,
}
print(json.dumps(provider))
' "$SITE_MODEL_BASE_URL" "$SITE_MODEL" "${SITE_MODEL_INPUT_COST:-0}" "${SITE_MODEL_OUTPUT_COST:-0}"
}

# The start script comes from the ref the job will run, never from this working tree, so the
# wrapper and the code it starts are one version.
check_code_ref() {
  if ! git -C "$repository" rev-parse --verify --quiet "$SITE_CODE_REF^{commit}" >/dev/null; then
    echo "job: $SITE_CODE_REF is not known here; fetch it first" >&2
    exit 1
  fi
}

write_wrapper() {
  root=$(job_root)
  provider=$(provider_json) || exit 1
  git -C "$repository" show "$SITE_CODE_REF:vm/job-start.sh" >"$work/job-start.sh" || exit 1
  if grep -qx "$start_end" "$work/job-start.sh"; then
    echo "job: vm/job-start.sh holds the line $start_end; the wrapper cannot carry it" >&2
    exit 1
  fi
  {
    echo "mkdir -p $root"
    echo "cat >$root/provider.json <<'PROVIDER_JSON_END'"
    printf '%s\n' "$provider" PROVIDER_JSON_END
    echo "cat >$start_script <<'$start_end'"
    cat "$work/job-start.sh"
    echo "$start_end"
    echo "exec sh $start_script"
  } >"$work/wrapper.sh"
}

wrapper_text() {
  gzip -c -n "$work/wrapper.sh" | base64 | tr -d '\n'
}

# A dry run shows the wrapper's size, not its text, which would fill the screen.
wrapper_argument() {
  text=$(wrapper_text)
  if [ "$dry_run" = yes ]; then
    text="<wrapper: ${#text} bytes>"
  fi
  printf '%s' "-c,echo $text | base64 -d | gzip -d | sh"
}

job_call() {
  gcloud_call run jobs "$1" "$SITE_JOB" \
    "--image=$image" \
    --execution-environment=gen2 \
    "--cpu=${SITE_CPU:-8}" \
    "--memory=${SITE_MEMORY:-32Gi}" \
    "--task-timeout=${SITE_TIMEOUT:-14400}" \
    --max-retries=0 \
    "--vpc-connector=$SITE_CONNECTOR" \
    --vpc-egress=all-traffic \
    "--service-account=$SITE_RUN_AS" \
    "--set-secrets=$hosting_mount=$SITE_HOSTING_SECRET:latest,$model_mount=$SITE_MODEL_SECRET:latest" \
    "--set-env-vars=$(env_list)" \
    --command=sh \
    "--args=$(wrapper_argument)"
}

# describe's own error stays hidden on create, where "not found" is the expected answer.
job_exists() {
  gcloud_call run jobs describe "$SITE_JOB" >/dev/null 2>"$work/describe.err"
}

create_or_update() {
  verb=$1
  shift
  dry_run=no
  case $* in
    '') ;;
    --dry-run) dry_run=yes ;;
    *) usage ;;
  esac
  require_settings
  check_instance
  check_env_values
  check_costs
  check_code_ref
  work=$(mktemp -d) || exit 1
  trap 'rm -rf "$work"' EXIT
  write_wrapper
  if [ "$dry_run" = no ]; then
    if job_exists; then
      if [ "$verb" = create ]; then
        echo "job: $SITE_JOB exists; use update" >&2
        exit 1
      fi
    elif [ "$verb" = update ]; then
      cat "$work/describe.err" >&2
      echo "job: $SITE_JOB does not exist; use create" >&2
      exit 1
    fi
  fi
  job_call "$verb"
}

# Two executions of one instance would share its repository and its pull requests.
running_execution() {
  printf '%s\n' "$1" | while IFS='	' read -r name count; do
    case $count in
      '' | *[!0-9]*) ;;
      *)
        if [ "$count" -ge 1 ]; then
          printf '%s\n' "$name"
          break
        fi
        ;;
    esac
  done
}

execute() {
  [ $# -eq 0 ] || usage
  dry_run=no
  require_job
  rows=$(gcloud_call run jobs executions list "--job=$SITE_JOB" \
    "--format=value(metadata.name,status.runningCount)") || exit
  running=$(running_execution "$rows")
  if [ -n "$running" ]; then
    echo "job: an execution of $SITE_JOB is still running: $running; two executions of one instance must not overlap" >&2
    exit 1
  fi
  name=$(gcloud_call run jobs execute "$SITE_JOB" --async "--format=value(metadata.name)") || exit
  printf '%s\n' "$name"
  state=${XDG_STATE_HOME:-$HOME/.local/state}/kumpel
  mkdir -p "$state" && printf '%s\n' "$name" >"$state/last-execution"
}

delete() {
  dry_run=no
  case $* in
    '') confirmed=no ;;
    --yes) confirmed=yes ;;
    *) usage ;;
  esac
  require_job
  if [ "$confirmed" = no ]; then
    echo "job: would delete $SITE_JOB and stop its running execution; run again with --yes" >&2
    exit 1
  fi
  gcloud_call run jobs delete "$SITE_JOB" --quiet
}

[ $# -ge 1 ] || usage
command=$1
shift
case $command in
  create | update) create_or_update "$command" "$@" ;;
  execute) execute "$@" ;;
  delete) delete "$@" ;;
  *) usage ;;
esac
