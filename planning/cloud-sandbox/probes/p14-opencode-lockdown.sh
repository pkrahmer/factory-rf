# P14: what does opencode contact at start, with and without F0047-S0007's lockdown?
# Question: with a provider file, do `enabled_providers` and the three switches
# OPENCODE_DISABLE_MODELS_FETCH, OPENCODE_DISABLE_AUTOUPDATE and OPENCODE_DISABLE_DEFAULT_PLUGINS stop
# opencode 1.19.3 from fetching the public model list (models.dev), checking for an update and loading
# plugins, and does a run still work? Every outbound connection of the container goes through a logging
# proxy on the job's loopback, which records the host of each CONNECT or GET and forwards it to the job's
# own proxy (PROBE_PROXY) or directly. Two runs, the same task: A without the switches, B with them. The
# comparison of the two host lists is the answer. Needs what P10 needs: LLM_KEY (a mounted secret, never
# printed), PROBE_LLM_BASE_URL, PROBE_NO_PROXY with the API's host, optionally PROBE_MODEL and the token
# endpoint (PROBE_TOKEN_URL, PROBE_TOKEN_SCOPE, PROBE_CLIENT_ID).
setup_env
apt_install podman runc netavark nftables curl ca-certificates jq python3-minimal util-linux
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
mask() { python3 -c '
import sys,os,re
t=sys.stdin.read()
for n in ("LLM_KEY","CLIENT_SECRET"):
    k=os.environ.get(n,"")
    if k: t=t.replace(k,"***"+n+"***")
t=re.sub(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]*","***JWT***",t)
sys.stdout.write(t)'; }

step "inputs (presence only)"
echo "LLM_KEY set: $([ -n "${LLM_KEY:-}" ] && echo yes || echo NO), length ${#LLM_KEY}"
echo "base url set: $([ -n "${PROBE_LLM_BASE_URL:-}" ] && echo yes || echo NO)"
echo "no_proxy for this job: $PROBE_NO_PROXY"
[ -n "${LLM_KEY:-}" ] && [ -n "${PROBE_LLM_BASE_URL:-}" ] || { echo "missing input: stopping"; echo "PROBE DONE"; exit 0; }

step "T: a bearer token, as in P10"
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
HOST=$(echo "$BASE" | sed -e 's#^[a-z]*://##' -e 's#/.*##')

step "metadata block (P2b's rule)"
cat > /tmp/probe.nft <<'EOF'
table inet probeblock {
  chain blockout { type filter hook output priority 0; policy accept; ip daddr 169.254.169.254 tcp dport 80 reject }
  chain blockfwd { type filter hook forward priority 0; policy accept; ip daddr 169.254.169.254 tcp dport 80 reject }
}
EOF
run nft -f /tmp/probe.nft

step "L: a logging proxy on 127.0.0.1:3128 (records the host of every CONNECT and GET, forwards upstream)"
cat > /tmp/logproxy.py <<'PY'
import os, socket, sys, threading
UP = os.environ.get("PROBE_PROXY", "")
LOG = sys.argv[1]
lock = threading.Lock()
def note(line):
    with lock:
        with open(LOG, "a") as f: f.write(line + "\n")
def pump(a, b):
    try:
        while True:
            d = a.recv(65536)
            if not d: break
            b.sendall(d)
    except OSError: pass
    finally:
        for s in (a, b):
            try: s.shutdown(socket.SHUT_RDWR)
            except OSError: pass
def upstream():
    h = UP.split("://", 1)[-1].rstrip("/")
    host, _, port = h.partition(":")
    return socket.create_connection((host, int(port or 3128)), timeout=20)
def serve(c):
    try:
        head = b""
        while b"\r\n\r\n" not in head and len(head) < 65536:
            d = c.recv(4096)
            if not d: return
            head += d
        first = head.split(b"\r\n", 1)[0].decode("latin1")
        parts = first.split(" ")
        method, target = parts[0], parts[1] if len(parts) > 1 else ""
        if method == "CONNECT":
            host, _, port = target.partition(":"); port = int(port or 443)
        else:
            rest = target.split("://", 1)[-1]; hostport = rest.split("/", 1)[0]
            host, _, port = hostport.partition(":"); port = int(port or 80)
        note(f"{method} {host}:{port}")
        if UP:
            u = upstream(); u.sendall(head)
        elif method == "CONNECT":
            u = socket.create_connection((host, port), timeout=20); c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        else:
            u = socket.create_connection((host, port), timeout=20); u.sendall(head)
        t = threading.Thread(target=pump, args=(u, c), daemon=True); t.start(); pump(c, u); t.join(5)
    except Exception as e:
        note(f"ERROR {e}")
    finally:
        try: c.close()
        except OSError: pass
s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", 3128)); s.listen(64)
while True:
    c, _ = s.accept(); threading.Thread(target=serve, args=(c,), daemon=True).start()
PY
python3 /tmp/logproxy.py /tmp/contacts.log & LP=$!
sleep 1; echo "logging proxy pid $LP, upstream: $([ -n "${PROBE_PROXY:-}" ] && echo "the job's proxy" || echo "none, direct")"
sh_run 'curl -sS -m 10 -x http://127.0.0.1:3128 -o /dev/null -w "self-test through the logging proxy: %{http_code}\n" https://deb.debian.org/ 2>&1 | tail -1'
sh_run 'cat /tmp/contacts.log'

step "C: the opencode runtime's files, as the factory writes them (provider block, agent, result block)"
mkdir -p /tmp/oc/home /tmp/oc/checkout /tmp/oc/state
[ -n "${PROBE_MODEL:-}" ] && MODEL=$PROBE_MODEL || MODEL=$(curl -sS -m 20 -H "Authorization: Bearer $LLM_KEY" "$BASE/models" 2>/dev/null | jq -r '(.data // .models // .)[] | (.id // .name // .)' | grep -i -E 'claude.*sonnet|claude|gpt' | grep -v -i -E 'embed|image|audio|mini|nano|haiku' | head -1)
echo "model: $MODEL"
write_config() {  # $1: the file, $2: extra top-level keys (JSON fragment with a trailing comma) or empty
cat > "$1" <<EOF
{
 "autoupdate": false, "share": "disabled", "snapshot": false, $2
 "provider": { "corp": { "npm": "@ai-sdk/openai-compatible",
   "options": { "baseURL": "$BASE", "apiKey": "{env:LLM_KEY}" },
   "models": { "$MODEL": { "limit": { "context": 128000, "output": 8192 } } } } },
 "small_model": "corp/$MODEL",
 "agent": { "factory-probe": { "mode": "primary",
   "prompt": "You are a test agent. Do exactly what the user asks. End your final message with this block, and nothing after it:\n<factory-result>\ndecision: <one of: doing, question>\nentry:\n<one sentence on what you did>\n</factory-result>",
   "tools": {"bash":true,"edit":true,"write":true,"read":true,"grep":true,"glob":true,"list":true,"patch":false,"todowrite":false,"todoread":false,"webfetch":false,"task":false},
   "permission": {"edit":"allow","bash":{"*":"allow"}} } }
}
EOF
}
write_config /tmp/oc/state/plain.json ""
write_config /tmp/oc/state/locked.json '"enabled_providers": ["corp"],'
chmod -R a+rwX /tmp/oc
IMG=docker.io/library/node:22-slim
PODMAN="podman --runtime=runc --storage-driver=vfs --cgroup-manager=cgroupfs --root /tmp/ps --runroot /tmp/pr"
echo "node image pull:"; $PODMAN pull -q $IMG 2>&1 | grep -v "level=warning" | tail -1
NP="localhost,127.0.0.1,${PROBE_NO_PROXY:-}"
LOGP=http://127.0.0.1:3128
# Every container call goes through the logging proxy, except the API host (no_proxy), as in the factory.
CRUN="$PODMAN run --rm --http-proxy=false --network=host --cap-drop=all --security-opt=no-new-privileges --pids-limit=512 --memory=3g -v /tmp/oc:/work -e HOME=/work/home -e LLM_KEY -e http_proxy=$LOGP -e https_proxy=$LOGP -e HTTP_PROXY=$LOGP -e HTTPS_PROXY=$LOGP -e no_proxy=$NP -e NO_PROXY=$NP --workdir /work/checkout $IMG"
step "C1: install opencode 1.19.3 through the logging proxy (npm)"
$CRUN sh -c 'npm install --global --prefix /work/npm opencode-ai@1.19.3 2>&1 | tail -2' 2>&1 | grep -v "level=warning" | mask | head -4
run $CRUN sh -c '/work/npm/bin/opencode --version'
echo "hosts the install contacted: $(cut -d' ' -f2 /tmp/contacts.log | cut -d: -f1 | sort -u | tr '\n' ' ')"

one_run() {  # $1: label, $2: config file, $3...: extra -e words
  label=$1; cfg=$2; shift 2
  : > /tmp/contacts.log; rm -rf /tmp/oc/home/.local /tmp/oc/home/.cache /tmp/oc/home/.config /tmp/oc/checkout/hello.txt
  s=$(date +%s)
  timeout 300 $CRUN "$@" -e OPENCODE_CONFIG=/work/state/$cfg sh -c '/work/npm/bin/opencode run --format json --auto --model corp/'"$MODEL"' --agent factory-probe "Create a file named hello.txt containing exactly the word hello. Then say what you did."' > /tmp/$label.out 2>/tmp/$label.err; rc=$?
  echo "exit $rc after $(( $(date +%s)-s )) s; events $(wc -l < /tmp/$label.out); hello.txt: $(cat /tmp/oc/checkout/hello.txt 2>/dev/null || echo MISSING)"
  echo "stderr (first lines, masked):"; head -6 /tmp/$label.err | mask | cut -c1-240
  echo "config complaints in stderr/events: $(grep -i -c -E 'unknown|invalid|unrecognized|enabled_providers' /tmp/$label.err /tmp/$label.out | tr '\n' ' ')"
  grep -i -E 'unknown|invalid|unrecognized|enabled_providers' /tmp/$label.err /tmp/$label.out | mask | head -4 | cut -c1-240
  python3 - /tmp/$label.out <<'PY' 2>&1 | mask
import json,re,sys
ev=[]
for line in open(sys.argv[1],errors="replace"):
    try: ev.append(json.loads(line))
    except Exception: pass
texts=[(e.get("part",e).get("text") or "") for e in ev if e.get("type")=="text"]
last=texts[-1] if texts else ""
m=re.search(r"<factory-result>\s*\n\s*decision:\s*(\w+)\s*\n\s*entry:\s*\n(.+?)\n</factory-result>\s*$",last.strip(),re.S)
print("result block parses:",bool(m))
PY
  sleep 2
  echo "HOSTS CONTACTED ($label): $(cut -d' ' -f2 /tmp/contacts.log | cut -d: -f1 | sort | uniq -c | sort -rn | awk '{printf "%s(%s) ", $2, $1}')"
  echo "note: the API host $HOST is in no_proxy and goes direct, so it is not in this list by design"
  echo "opencode's own log mentions of update/models.dev/plugin:"
  for f in $(find /tmp/oc/home -name '*.log' 2>/dev/null | head -2); do grep -i -E 'models\.dev|upgrade|update|plugin|fetch' "$f" | mask | head -6 | cut -c1-200; done
}

step "A: WITHOUT the lockdown (the factory of F0046 today)"
one_run A plain.json

step "B: WITH the lockdown of S0007: enabled_providers + the three switches"
one_run B locked.json -e OPENCODE_DISABLE_MODELS_FETCH=1 -e OPENCODE_DISABLE_AUTOUPDATE=1 -e OPENCODE_DISABLE_DEFAULT_PLUGINS=1

step "D: the switches one at a time, start only (opencode --version does not start the app; a 20 s run does)"
for sw in OPENCODE_DISABLE_MODELS_FETCH OPENCODE_DISABLE_AUTOUPDATE OPENCODE_DISABLE_DEFAULT_PLUGINS; do
  : > /tmp/contacts.log; rm -rf /tmp/oc/home/.local /tmp/oc/home/.cache
  timeout 60 $CRUN -e $sw=1 -e OPENCODE_CONFIG=/work/state/plain.json sh -c '/work/npm/bin/opencode run --format json --auto --model corp/'"$MODEL"' --agent factory-probe "Say pong."' >/dev/null 2>&1
  sleep 2; echo "$sw=1 alone: $(cut -d' ' -f2 /tmp/contacts.log | cut -d: -f1 | sort -u | tr '\n' ' ')"
done

kill $LP 2>/dev/null
echo; echo "VERDICT: compare HOSTS CONTACTED (A) with (B). S0007 is right if (B) lists neither models.dev nor an npm registry nor opencode.ai, and the run B ended with a parsing result block and hello.txt. A config complaint about enabled_providers means the key is not known to 1.19.3."
echo "PROBE DONE"
