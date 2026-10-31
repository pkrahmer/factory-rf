# P21: the trial project in a job. Two questions before the first real story (F0047's end):
#   1. Does the demo project's `make sync` and `make check` pass in the factory's stage image, in a job,
#      with the factory's container words (root, every capability dropped, native overlay on a tmpfs)?
#   2. Does the factory's write path to the hosting service work with the token it will use: push a
#      branch, open a draft pull request, add a label, comment, read the comments, close the pull
#      request, delete the branch? Nothing touches `main`; everything made is removed at the end.
# Inputs: PROBE_PROXY and PROBE_NO_PROXY as for every probe; GIT_TOKEN, a mounted secret (never printed),
# the token the factory will use; PROBE_LLM_BASE_URL, reused as the repository, written <owner>/<repo>
# (as in P20). The repository's name and the token's owner are never printed. Needs no model.
# Run it with 8 cpu and 32Gi.
setup_env
apt_install podman nftables git make curl ca-certificates jq python3 procps
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
t0=$(date +%s)
since() { echo "$(( $(date +%s) - $1 )) s"; }
R=${PROBE_LLM_BASE_URL:-}
hide() { sed "s|$R|<repo>|g"; }
API="https://api.github.com/repos/$R"
gh() {  # gh <method> <path> [json body]: prints the HTTP status; the body is in /tmp/gh.json
  if [ -n "${3:-}" ]; then
    curl -sS -m 30 -o /tmp/gh.json -w '%{http_code}' -X "$1" -H "Authorization: Bearer $GIT_TOKEN" -H "Accept: application/vnd.github+json" -d "$3" "$API$2" 2>&1 | tail -1
  else
    curl -sS -m 30 -o /tmp/gh.json -w '%{http_code}' -X "$1" -H "Authorization: Bearer $GIT_TOKEN" -H "Accept: application/vnd.github+json" "$API$2" 2>&1 | tail -1
  fi
}
message() { jq -r '.message // empty' /tmp/gh.json 2>/dev/null | hide | cut -c1-200; }

step "inputs (presence only)"
echo "GIT_TOKEN set: $([ -n "${GIT_TOKEN:-}" ] && echo yes || echo NO); repository given: $([ -n "$R" ] && echo yes || echo NO)"
[ -n "${GIT_TOKEN:-}" ] && [ -n "$R" ] || { echo "missing input: stopping"; echo "PROBE DONE"; exit 0; }
echo "token kind: $(printf %s "$GIT_TOKEN" | cut -d_ -f1)_"

step "A1: the demo project, cloned with the token through the proxy"
AUTH="Authorization: Basic $(printf 'x-access-token:%s' "$GIT_TOKEN" | base64 | tr -d '\n')"
mkdir -p /srv/work/home
GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c http.extraHeader="$AUTH" clone -q "https://github.com/$R.git" /srv/work/checkout 2>&1 | hide | tail -2
echo "clone: $(git -C /srv/work/checkout ls-files 2>/dev/null | wc -l) files, at $(git -C /srv/work/checkout rev-parse --short HEAD 2>/dev/null)"
for f in factory/pipeline.yml factory/story-form.md Makefile uv.lock; do
  echo "has $f: $([ -f /srv/work/checkout/$f ] && echo yes || echo NO)"
done
echo "Makefile targets check, lint, test, sync: $(grep -c -E '^(check|lint|test|sync):' /srv/work/checkout/Makefile) of 4"

step "A2: runc 1.5.2, podman storage on a tmpfs, the stage image (S0006, S0009)"
RUNC_SHA256=599f6f94ff8c5057241eff0d54c3c74f95c34935b6457b33fe545defc61e9488
curl -sSL -m 120 -o /tmp/runc.amd64 https://github.com/opencontainers/runc/releases/download/v1.5.2/runc.amd64
if echo "$RUNC_SHA256  /tmp/runc.amd64" | sha256sum -c - >/dev/null 2>&1; then
  install -m 0755 /tmp/runc.amd64 /usr/local/bin/runc
else
  echo "runc checksum failed: stopping"; echo "PROBE DONE"; exit 0
fi
mkdir -p /var/lib/containers
mount -t tmpfs tmpfs /var/lib/containers; echo "tmpfs mount exit $?"
P="podman --runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay"
GIT_TERMINAL_PROMPT=0 git clone -q https://github.com/pkrahmer/factory-rf.git /srv/code
s=$(date +%s)
$P build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=probe -t factory-stage:probe /srv/code > /tmp/build.log 2>&1; rc=$?
echo "stage image build exit $rc after $(since $s)"
if [ $rc -ne 0 ]; then grep -v -i "level=warning" /tmp/build.log | tail -10 | cut -c1-240; fi

step "A3: the demo's make sync and make check in containers of the stage image"
NP="localhost,127.0.0.1${PROBE_NO_PROXY:+,$PROBE_NO_PROXY}"
PX=""
if [ -n "${PROBE_PROXY:-}" ]; then
  PX="--env http_proxy=$PROBE_PROXY --env https_proxy=$PROBE_PROXY --env HTTP_PROXY=$PROBE_PROXY --env HTTPS_PROXY=$PROBE_PROXY --env no_proxy=$NP --env NO_PROXY=$NP"
fi
RUN="$P run --rm --http-proxy=false --network=host --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=4g --env HOME=/work/home $PX --volume /srv/work:/work --workdir /work/checkout"
if [ $rc -eq 0 ]; then
  s=$(date +%s)
  timeout 420 $RUN --timeout 420 factory-stage:probe make sync > /tmp/sync.log 2>&1; rc=$?
  echo "make sync exit $rc after $(since $s)"; grep -v -i "level=warning" /tmp/sync.log | tail -3 | cut -c1-200
  s=$(date +%s)
  timeout 660 $RUN --timeout 660 factory-stage:probe make -k check > /tmp/check.log 2>&1; rc=$?
  echo "make -k check exit $rc after $(since $s)"
  echo "--- every target's line:"; grep -E "^[a-z]+: (green|red)|^check: green|make: \*\*\*" /tmp/check.log | head -12 | cut -c1-200
  echo "--- the test target's last lines:"; grep -v -i "level=warning" /tmp/check.log | grep -B1 -A3 "^test: green\|Required test coverage" | tail -5 | cut -c1-200
  echo "--- failed tests and E lines (first 30):"; grep -E "^FAILED|^ERROR|^E  " /tmp/check.log | head -30 | cut -c1-240
  echo "--- what detect-secrets flagged (type and place only):"; grep -E "Secret Type|Location" /tmp/check.log | head -8 | cut -c1-200
fi

step "B: the factory's write path, on a throwaway branch (nothing touches main)"
id=p21-$(head -c 4 /dev/urandom | od -An -tx1 | tr -d ' \n')
branch=probe/$id
cd /srv/work/checkout
git -c user.name=probe -c user.email=probe@example.invalid commit -q --allow-empty -m "P21: a throwaway commit"
s=$(date +%s)
GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c http.extraHeader="$AUTH" push -q origin "HEAD:refs/heads/$branch" 2>&1 | hide | tail -2
echo "push of a new branch: exit $? after $(since $s)"
base=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null | sed 's|origin/||'); [ -n "$base" ] || base=main
code=$(gh POST /pulls "{\"title\":\"P21 probe ($id)\",\"head\":\"$branch\",\"base\":\"$base\",\"body\":\"A throwaway pull request of a probe; it is closed at once.\",\"draft\":true}")
echo "create a draft pull request: $code $(message)"
n=$(jq -r '.number // empty' /tmp/gh.json 2>/dev/null)
if [ -n "$n" ]; then
  echo "ready for review (draft false): $(gh PATCH /pulls/$n '{"draft":false}') $(message)"
  echo "add a label: $(gh POST /issues/$n/labels "{\"labels\":[\"$id\"]}") $(message)"
  echo "remove the label: $(gh DELETE /issues/$n/labels/$id) $(message)"
  echo "post a comment: $(gh POST /issues/$n/comments '{"body":"P21: a comment of a probe. <!-- factory -->"}') $(message)"
  echo "list the comments: $(gh GET /issues/$n/comments) $(jq -r 'if type=="array" then "\(length) comment(s), author present: \(.[0].user.login != null)" else "" end' /tmp/gh.json 2>/dev/null)"
  echo "read the pull request's merge state: $(gh GET /pulls/$n) $(jq -r '"mergeable_state \(.mergeable_state), state \(.state)"' /tmp/gh.json 2>/dev/null)"
  echo "close it: $(gh PATCH /pulls/$n '{"state":"closed"}') $(message)"
  echo "reopen it: $(gh PATCH /pulls/$n '{"state":"open"}') $(message)"
  echo "close it again: $(gh PATCH /pulls/$n '{"state":"closed"}') $(message)"
fi
echo "delete the label from the repository: $(gh DELETE /labels/$id) $(message)"
GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c http.extraHeader="$AUTH" push -q origin --delete "$branch" 2>&1 | hide | tail -2
echo "delete the branch: exit $?"
echo "branches named probe/ left: $(GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c http.extraHeader="$AUTH" ls-remote origin "refs/heads/probe/*" 2>/dev/null | wc -l)"
rm -f /tmp/gh.json

echo; echo "total $(since $t0)"
echo "VERDICT: the demo project is ready for the trial if make sync and every check target are green in the stage image, and the token suffices if every step of B answers 2xx (201 for creates, 200 for reads and updates, 204 or 200 for deletes) and no probe/ branch is left. A 403 or 404 in B names the permission the token lacks."
echo "PROBE DONE"
