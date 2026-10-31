# P17: does a real opencode task run in the factory's own stage image, as the job will run it?
# P10 and P14 ran opencode 1.19.3 in `node:22-slim`. The factory runs it in the stage image (`vm/Dockerfile`:
# Debian's Node 18, opencode from npm), as the job's root with every capability dropped (F0047 decision 3),
# with podman's native overlay on a tmpfs (decision 19), F0046's provider block and S0007's lockdown. This
# probe builds that image and runs one small task in it with the factory's container words.
# Needs what P14 needs: LLM_KEY (a mounted secret, never printed), PROBE_LLM_BASE_URL, PROBE_NO_PROXY with
# the API's host, optionally PROBE_MODEL and the token endpoint (PROBE_TOKEN_URL, PROBE_TOKEN_SCOPE,
# PROBE_CLIENT_ID). Run it with 8 cpu and 32Gi.
setup_env
apt_install podman nftables git make curl ca-certificates jq python3 procps
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
t0=$(date +%s)
since() { echo "$(( $(date +%s) - $1 )) s"; }
mask() { python3 -c '
import sys,os,re
t=sys.stdin.read()
for n in ("LLM_KEY","CLIENT_SECRET"):
    k=os.environ.get(n,"")
    if k: t=t.replace(k,"***"+n+"***")
t=re.sub(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*","***JWT***",t)
sys.stdout.write(t)'; }

step "inputs (presence only)"
echo "LLM_KEY set: $([ -n "${LLM_KEY:-}" ] && echo yes || echo NO); base url set: $([ -n "${PROBE_LLM_BASE_URL:-}" ] && echo yes || echo NO)"
[ -n "${LLM_KEY:-}" ] && [ -n "${PROBE_LLM_BASE_URL:-}" ] || { echo "missing input: stopping"; echo "PROBE DONE"; exit 0; }

step "T: a bearer token, as in P10 and P14"
if [ -n "${PROBE_TOKEN_URL:-}" ] && [ -n "${PROBE_CLIENT_ID:-}" ]; then
  export CLIENT_SECRET="$LLM_KEY"
  code=$(curl -sS -m 30 -x "$PROBE_PROXY" -o /tmp/tok.json -w '%{http_code}' --request POST --url "$PROBE_TOKEN_URL" \
    --header 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "client_id=$PROBE_CLIENT_ID" --data-urlencode "scope=$PROBE_TOKEN_SCOPE" \
    --data-urlencode "client_secret=$CLIENT_SECRET" --data-urlencode "grant_type=client_credentials" 2>&1 | tail -1)
  echo "token endpoint status: $code"
  T=$(jq -r '.access_token // empty' /tmp/tok.json 2>/dev/null)
  if [ -n "$T" ]; then export LLM_KEY="$T"; echo "using the fetched token"; else echo "no token obtained: the mounted value is used as is"; fi
  rm -f /tmp/tok.json
else echo "no token endpoint given: the mounted value is used as the bearer key"; fi
BASE=${PROBE_LLM_BASE_URL%/}

step "M: the metadata block (S0006's rule)"
cat > /tmp/block.nft <<'NFT'
table inet factory_block {
  chain blockout {
    type filter hook output priority 0; policy accept;
    ip daddr 169.254.169.254 tcp dport 80 reject
  }
  chain blockfwd {
    type filter hook forward priority 0; policy accept;
    ip daddr 169.254.169.254 tcp dport 80 reject
  }
}
NFT
run nft -f /tmp/block.nft

step "1: runc 1.5.2 and podman storage on a tmpfs (S0006, S0009)"
RUNC_SHA256=599f6f94ff8c5057241eff0d54c3c74f95c34935b6457b33fe545defc61e9488
curl -sSL -m 120 -o /tmp/runc.amd64 https://github.com/opencontainers/runc/releases/download/v1.5.2/runc.amd64
if echo "$RUNC_SHA256  /tmp/runc.amd64" | sha256sum -c -; then
  install -m 0755 /tmp/runc.amd64 /usr/local/bin/runc
else
  echo "runc failed: stopping"; echo "PROBE DONE"; exit 0
fi
mkdir -p /var/lib/containers
mount -t tmpfs tmpfs /var/lib/containers; echo "tmpfs at /var/lib/containers: exit $?"
P="podman --runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay"

step "2: the stage image from a fresh clone of factory-rf"
GIT_TERMINAL_PROMPT=0 git clone -q https://github.com/pkrahmer/factory-rf.git /srv/code; echo "clone exit $?, at $(git -C /srv/code rev-parse --short HEAD)"
s=$(date +%s)
$P build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=probe -t factory-stage:probe /srv/code > /tmp/build.log 2>&1; rc=$?
echo "build exit $rc after $(since $s)"
if [ $rc -ne 0 ]; then
  grep -v -i "level=warning" /tmp/build.log | tail -15 | cut -c1-240; echo "PROBE DONE"; exit 0
fi
sh_run "$P run --rm --network=host --http-proxy=false --cap-drop=all --security-opt=no-new-privileges factory-stage:probe sh -c 'node --version; opencode --version; id -u'"

step "3: the provider block as F0046 writes it, with S0007's lockdown"
if [ -n "${PROBE_MODEL:-}" ]; then
  MODEL=$PROBE_MODEL
else
  MODEL=$(curl -sS -m 20 -H "Authorization: Bearer $LLM_KEY" "$BASE/models" 2>/dev/null | jq -r '(.data // .models // .)[] | (.id // .name // .)' | grep -i -E 'claude.*sonnet|claude|gpt' | grep -v -i -E 'embed|image|audio|mini|nano|haiku' | head -1)
fi
echo "model: $MODEL"
mkdir -p /srv/work/home /srv/work/checkout /srv/work/state
cat > /srv/work/state/opencode.json <<JSON
{
 "autoupdate": false, "share": "disabled", "snapshot": false,
 "enabled_providers": ["corp"],
 "provider": { "corp": { "npm": "@ai-sdk/openai-compatible",
   "options": { "baseURL": "$BASE", "apiKey": "{env:ANTHROPIC_API_KEY}" },
   "models": { "$MODEL": { "limit": { "context": 128000, "output": 8192 } } } } },
 "small_model": "corp/$MODEL",
 "agent": { "factory-probe": { "mode": "primary",
   "prompt": "You are a test agent. Do exactly what the user asks, using your tools. End your final message with this block, and nothing after it:\n<factory-result>\ndecision: <one of: doing, question>\nentry:\n<one sentence on what you did>\n</factory-result>",
   "tools": {"bash":true,"edit":true,"write":true,"read":true,"grep":true,"glob":true,"list":true,"patch":false,"todowrite":false,"todoread":false,"webfetch":false,"task":false},
   "permission": {"edit":"allow","bash":{"*":"allow"}} } }
}
JSON
printf '%s' "$LLM_KEY" > /srv/work/state/api-key
printf 'def add(a, b):\n    return a - b\n' > /srv/work/checkout/calc.py
NP="localhost,127.0.0.1${PROBE_NO_PROXY:+,$PROBE_NO_PROXY}"
PX=""
if [ -n "${PROBE_PROXY:-}" ]; then
  PX="--env http_proxy=$PROBE_PROXY --env https_proxy=$PROBE_PROXY --env HTTP_PROXY=$PROBE_PROXY --env HTTPS_PROXY=$PROBE_PROXY --env no_proxy=$NP --env NO_PROXY=$NP"
fi
# The factory's words for an agent call in the job profile (S0002, S0009); the call's shell reads the login.
RUN="$P run --rm --http-proxy=false --network=host --timeout 600 --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=4g --env HOME=/work/home --env OPENCODE_CONFIG=/work/state/opencode.json --env OPENCODE_DISABLE_MODELS_FETCH=1 --env OPENCODE_DISABLE_AUTOUPDATE=1 --env OPENCODE_DISABLE_DEFAULT_PLUGINS=1 --env PYTHONDONTWRITEBYTECODE=1 $PX --volume /srv/work:/work --workdir /work/checkout"
TASK='calc.py has a bug: add subtracts. Fix it, then run: python3 -c "import calc; print(calc.add(2, 3))" and report what it printed.'
cat > /srv/work/state/call.sh <<CALL
ANTHROPIC_API_KEY=\$(cat /work/state/api-key)
export ANTHROPIC_API_KEY
exec opencode run --format json --auto --model corp/$MODEL --agent factory-probe "\$(cat /work/state/task.txt)"
CALL
printf '%s' "$TASK" > /srv/work/state/task.txt

step "4: one real task: fix a bug, run python to show it, end with the result block"
s=$(date +%s)
timeout 660 $RUN factory-stage:probe sh /work/state/call.sh > /tmp/run.out 2>/tmp/run.err; rc=$?
echo "opencode exit $rc after $(since $s); events $(wc -l < /tmp/run.out)"
echo "--- stderr (first lines, masked):"; head -8 /tmp/run.err | mask | cut -c1-240
echo "--- calc.py now:"; cat /srv/work/checkout/calc.py
echo "--- calc.py owned by $(stat -c '%U:%G' /srv/work/checkout/calc.py)"
python3 - /tmp/run.out <<'PY' 2>&1 | mask
import json, re, sys
from collections import Counter
ev = []
for line in open(sys.argv[1], errors="replace"):
    try:
        ev.append(json.loads(line))
    except Exception:
        pass
print("event types:", dict(Counter(e.get("type") for e in ev)))
cost = 0.0
steps = 0
for e in ev:
    if e.get("type") == "step_finish":
        p = e.get("part", e)
        steps += 1
        cost += float(p.get("cost", 0) or 0)
print("steps:", steps, "cost reported:", round(cost, 6))
tools = [(e.get("part", e).get("tool"), (e.get("part", e).get("state") or {}).get("status")) for e in ev if e.get("type") == "tool_use"]
print("tool calls:", tools)
texts = [(e.get("part", e).get("text") or "") for e in ev if e.get("type") == "text"]
last = texts[-1] if texts else ""
print("last text (first 400 chars):", last[:400].replace("\n", "\\n"))
m = re.search(r"<factory-result>\s*\n\s*decision:\s*(\w+)\s*\n\s*entry:\s*\n(.+?)\n</factory-result>\s*$", last.strip(), re.S)
print("STRICT RESULT BLOCK PARSES:", bool(m), ("decision=" + m.group(1)) if m else "")
PY
rm -f /srv/work/state/api-key

echo; echo "total $(since $t0)"
echo "VERDICT: the stage image runs the factory's agents in the job if opencode exits 0, calc.py returns a + b, the agent reports that python printed 5, and the strict result block parses."
echo "PROBE DONE"
