# P10: opencode inside a Podman container, talking to an OpenAI-compatible model API.
# Question: does the factory's opencode runtime work in the job: provider block, the pinned opencode
# version, the proxy / no-proxy split (the model API is internal, the package registries are not),
# streaming and tool calls, and does a real agent run end with the <factory-result> block the factory
# parses strictly? Needs: LLM_KEY (a secret mounted as an environment variable, never printed),
# PROBE_LLM_BASE_URL (ending in the API's /v1 equivalent), optionally PROBE_MODEL.
# Every output that could contain the key goes through mask().
setup_env
apt_install podman runc netavark nftables curl ca-certificates busybox-static jq python3-minimal util-linux
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
mrun() { echo "\$ $*"; out=$("$@" 2>&1); rc=$?; echo "$out" | mask | head -"${LINES_MAX:-25}"; echo "[exit $rc]"; }

step "inputs (presence only)"
echo "LLM_KEY set: $([ -n "${LLM_KEY:-}" ] && echo yes || echo NO), length ${#LLM_KEY}"
echo "base url set: $([ -n "${PROBE_LLM_BASE_URL:-}" ] && echo yes || echo NO)"
echo "no_proxy for this job: $PROBE_NO_PROXY"
[ -n "${LLM_KEY:-}" ] && [ -n "${PROBE_LLM_BASE_URL:-}" ] || { echo "missing input: stopping"; echo "PROBE DONE"; exit 0; }
step "T: obtain a bearer token (client-credentials grant) if a token endpoint was given"
if [ -n "${PROBE_TOKEN_URL:-}" ] && [ -n "${PROBE_CLIENT_ID:-}" ]; then
  export CLIENT_SECRET="$LLM_KEY"
  code=$(curl -sS -m 30 -x "$PROBE_PROXY" -o /tmp/tok.json -w '%{http_code}' --request POST --url "$PROBE_TOKEN_URL" \
    --header 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode "client_id=$PROBE_CLIENT_ID" --data-urlencode "scope=$PROBE_TOKEN_SCOPE" \
    --data-urlencode "client_secret=$CLIENT_SECRET" --data-urlencode "grant_type=client_credentials" 2>&1 | tail -1)
  echo "token endpoint status: $code"
  jq -r '"token_type=\(.token_type) expires_in=\(.expires_in) access_token_length=\(.access_token|length // 0)"' /tmp/tok.json 2>&1 | mask | head -2
  jq -r 'select(.error!=null) | "error=\(.error) codes=\(.error_codes) description=\(.error_description|.[0:200]|gsub("\n";" "))"' /tmp/tok.json 2>&1 | mask | head -3
  T=$(jq -r '.access_token // empty' /tmp/tok.json 2>/dev/null)
  if [ -n "$T" ]; then export LLM_KEY="$T"; echo "using the fetched token as the bearer key from here on"; else echo "no token obtained: the later steps use the mounted value as is"; fi
  rm -f /tmp/tok.json
else echo "no token endpoint given: the mounted value is used as the bearer key"; fi
BASE=${PROBE_LLM_BASE_URL%/}
HOST=$(echo "$BASE" | sed -e 's#^[a-z]*://##' -e 's#/.*##')

step "metadata block (same rule as P2b), proven from the job"
cat > /tmp/probe.nft <<'EOF'
table inet probeblock {
  chain blockout {
    type filter hook output priority 0; policy accept;
    ip daddr 169.254.169.254 tcp dport 80 reject
  }
  chain blockfwd {
    type filter hook forward priority 0; policy accept;
    ip daddr 169.254.169.254 tcp dport 80 reject
  }
}
EOF
run nft -f /tmp/probe.nft
sh_run 'curl -sS -m 5 -o /dev/null -w "metadata after block: %{http_code}\n" -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/id 2>&1 | tail -1'

step "A1: the API host: DNS and TCP, direct (no proxy), and through the proxy"
sh_run "getent hosts $HOST | head -1"
sh_run "curl -sS -m 10 -o /dev/null -w 'no key, direct: %{http_code}\n' $BASE/models 2>&1 | tail -1"
sh_run "curl -sS -m 10 -x $PROBE_PROXY -o /dev/null -w 'no key, via proxy: %{http_code}\n' $BASE/models 2>&1 | tail -1"
step "A2: list models with the key (status and ids only; the body is not printed)"
code=$(curl -sS -m 20 -o /tmp/models.json -w '%{http_code}' -H "Authorization: Bearer $LLM_KEY" "$BASE/models" 2>&1 | tail -1)
echo "GET /models: $code"
jq -r '(.data // .models // .)[] | (.id // .name // .)' /tmp/models.json 2>/dev/null | head -60 | tr '\n' ' '; echo
echo "model count: $(jq -r '(.data // .models // .) | length' /tmp/models.json 2>/dev/null)"
code=$(curl -sS -m 20 -o /tmp/meta.json -w '%{http_code}' -H "Authorization: Bearer $LLM_KEY" "${BASE%/}/models_metadata" 2>&1 | tail -1)
echo "GET /models_metadata: $code; keys of the first entry: $(jq -r '(.data // .models // .) | .[0] | keys | join(",")' /tmp/meta.json 2>/dev/null | head -c 400)"

# choose the models: PROBE_MODEL, else the first id that looks like a strong chat model
if [ -n "${PROBE_MODEL:-}" ]; then MODEL=$PROBE_MODEL; else
  ids=$(jq -r '(.data // .models // .)[] | (.id // .name // .)' /tmp/models.json 2>/dev/null)
  MODEL=""
  for pat in 'claude.*sonnet' 'claude' 'gpt-5' 'gpt-4\.1' 'gpt-4o' 'gemini.*pro' 'gpt'; do
    MODEL=$(echo "$ids" | grep -i -E "$pat" | grep -v -i -E 'embed|image|audio|tts|whisper|realtime|mini|nano|haiku|flash' | head -1); [ -n "$MODEL" ] && break
  done
  [ -z "$MODEL" ] && MODEL=$(echo "$ids" | head -1)
fi
echo "chosen model: $MODEL"
SMALL=$MODEL

step "B1: raw chat completion, no tools (status, finish reason, usage keys)"
jq -n --arg m "$MODEL" '{model:$m,messages:[{role:"user",content:"Reply with the single word: pong"}],max_tokens:50}' > /tmp/req1.json
code=$(curl -sS -m 90 -o /tmp/resp1.json -w '%{http_code}' -H "Authorization: Bearer $LLM_KEY" -H 'Content-Type: application/json' -d @/tmp/req1.json "$BASE/chat/completions" 2>&1 | tail -1)
echo "status $code"; jq -c '{finish:(.choices[0].finish_reason), reply:(.choices[0].message.content|tostring|.[0:80]), usage:.usage, model:.model}' /tmp/resp1.json 2>&1 | mask | head -3
step "B2: raw chat completion WITH a tool definition (does the model call it?)"
jq -n --arg m "$MODEL" '{model:$m,messages:[{role:"user",content:"What is the weather in Berlin? Use the tool."}],tools:[{type:"function",function:{name:"get_weather",description:"weather for a city",parameters:{type:"object",properties:{city:{type:"string"}},required:["city"]}}}],tool_choice:"auto",max_tokens:200}' > /tmp/req2.json
code=$(curl -sS -m 90 -o /tmp/resp2.json -w '%{http_code}' -H "Authorization: Bearer $LLM_KEY" -H 'Content-Type: application/json' -d @/tmp/req2.json "$BASE/chat/completions" 2>&1 | tail -1)
echo "status $code"; jq -c '{finish:(.choices[0].finish_reason), calls:[.choices[0].message.tool_calls[]?|{n:.function.name,a:.function.arguments}], usage:.usage}' /tmp/resp2.json 2>&1 | mask | head -3
step "B3: streamed completion with usage (events, [DONE], usage chunk)"
jq -n --arg m "$MODEL" '{model:$m,messages:[{role:"user",content:"Count from 1 to 5."}],stream:true,stream_options:{include_usage:true},max_tokens:80}' > /tmp/req3.json
code=$(curl -sS -N -m 90 -o /tmp/resp3.txt -w '%{http_code}' -H "Authorization: Bearer $LLM_KEY" -H 'Content-Type: application/json' -d @/tmp/req3.json "$BASE/chat/completions" 2>&1 | tail -1)
echo "status $code; data lines: $(grep -c '^data:' /tmp/resp3.txt); done marker: $(grep -c 'data: \[DONE\]' /tmp/resp3.txt); usage chunk: $(grep -c '"usage"' /tmp/resp3.txt)"
grep '"usage"' /tmp/resp3.txt | tail -1 | cut -c1-240 | mask
step "B4: the same call with a bad key (the error shape the runtime would see)"
code=$(curl -sS -m 20 -o /tmp/resp4.json -w '%{http_code}' -H "Authorization: Bearer not-a-key" -H 'Content-Type: application/json' -d @/tmp/req1.json "$BASE/chat/completions" 2>&1 | tail -1); echo "status $code: $(head -c 200 /tmp/resp4.json | mask)"

step "C: the factory's opencode runtime, in a container (pinned opencode, provider block, strict result block)"
mkdir -p /tmp/oc/home /tmp/oc/checkout /tmp/oc/state
cat > /tmp/oc/state/opencode.json <<EOF
{
 "autoupdate": false, "share": "disabled", "snapshot": false,
 "provider": { "corp": { "npm": "@ai-sdk/openai-compatible",
   "options": { "baseURL": "$BASE", "apiKey": "{env:LLM_KEY}" },
   "models": { "$MODEL": { "limit": { "context": 128000, "output": 8192 } } } } },
 "small_model": "corp/$MODEL",
 "agent": { "factory-probe": { "mode": "primary",
   "prompt": "You are a test agent. Do exactly what the user asks, using your tools. End your final message with this block, and nothing after it:\n<factory-result>\ndecision: <one of: doing, question>\nentry:\n<your journal entry, without its number or your name: one sentence on what you did>\n</factory-result>",
   "tools": {"bash":true,"edit":true,"write":true,"read":true,"grep":true,"glob":true,"list":true,"patch":false,"todowrite":false,"todoread":false,"webfetch":false,"task":false},
   "permission": {"edit":"allow","bash":{"*":"allow"}} } }
}
EOF
chmod -R a+rwX /tmp/oc
IMG=docker.io/library/node:22-slim
PODMAN="podman --runtime=runc --storage-driver=vfs --cgroup-manager=cgroupfs --root /tmp/ps --runroot /tmp/pr"  # a variable, not a function: timeout cannot call a function
echo "node image pull:"; $PODMAN pull -q $IMG 2>&1 | grep -v "level=warning" | tail -2 | mask
NP="localhost,127.0.0.1,${PROBE_NO_PROXY:-}"
CRUN="$PODMAN run --rm --http-proxy=false --network=host --cap-drop=all --security-opt=no-new-privileges --pids-limit=512 --memory=3g -v /tmp/oc:/work -e HOME=/work/home -e LLM_KEY -e OPENCODE_CONFIG=/work/state/opencode.json -e http_proxy=$PROBE_PROXY -e https_proxy=$PROBE_PROXY -e HTTP_PROXY=$PROBE_PROXY -e HTTPS_PROXY=$PROBE_PROXY -e no_proxy=$NP -e NO_PROXY=$NP --workdir /work/checkout $IMG"
step "C1: install the pinned opencode through the proxy (npm)"
s=$(date +%s); $CRUN sh -c 'npm install --global --prefix /work/npm opencode-ai@1.19.3 2>&1 | tail -4; ls /work/npm/bin' 2>&1 | grep -v "level=warning" | mask | head -12; echo "install took $(( $(date +%s)-s )) s"
run $CRUN sh -c '/work/npm/bin/opencode --version'
step "C2: opencode run with the factory's flags: one tiny task, tool use, strict result block"
s=$(date +%s)
timeout 300 $CRUN sh -c '/work/npm/bin/opencode run --format json --auto --model corp/'"$MODEL"' --agent factory-probe "Create a file named hello.txt in the current directory containing exactly the word hello. Then say what you did."' > /tmp/oc.out 2>/tmp/oc.err; rc=$?
echo "opencode exit $rc after $(( $(date +%s)-s )) s; stdout lines $(wc -l < /tmp/oc.out); stderr lines $(wc -l < /tmp/oc.err)"
echo "--- stderr (first lines, masked)"; head -12 /tmp/oc.err | mask | cut -c1-260
echo "--- the file the agent was to create:"; ls -la /tmp/oc/checkout 2>&1 | head -5; cat /tmp/oc/checkout/hello.txt 2>&1 | head -2
echo "--- events summary"
python3 - <<'PY' 2>&1 | mask
import json,re
ev=[]
for line in open("/tmp/oc.out",errors="replace"):
    try: ev.append(json.loads(line))
    except Exception: pass
from collections import Counter
print("event types:",dict(Counter(e.get("type") for e in ev)))
cost=0.0; toks={"input":0,"output":0,"read":0,"write":0}; steps=0
for e in ev:
    if e.get("type")=="step_finish":
        p=e.get("part",e); steps+=1
        cost+=float(p.get("cost",0) or 0)
        t=p.get("tokens",{}) or {}
        toks["input"]+=t.get("input",0) or 0; toks["output"]+=(t.get("output",0) or 0)+(t.get("reasoning",0) or 0)
        c=t.get("cache",{}) or {}; toks["read"]+=c.get("read",0) or 0; toks["write"]+=c.get("write",0) or 0
print("steps:",steps,"cost reported:",cost,"tokens:",toks)
tools=[]
for e in ev:
    if e.get("type")=="tool_use":
        p=e.get("part",e); st=p.get("state",{}) or {}
        tools.append((p.get("tool"),st.get("status")))
print("tool calls:",tools)
texts=[ (e.get("part",e).get("text") or "") for e in ev if e.get("type")=="text"]
last=texts[-1] if texts else ""
print("last text (first 500 chars):",last[:500].replace("\n","\\n"))
m=re.search(r"<factory-result>\s*\n\s*decision:\s*(\w+)\s*\n\s*entry:\s*\n(.+?)\n</factory-result>\s*$",last.strip(),re.S)
print("STRICT RESULT BLOCK PARSES:",bool(m), ("decision="+m.group(1)) if m else "")
errs=[e for e in ev if e.get("type")=="error"]
print("error events:",len(errs), json.dumps(errs[:2])[:400])
sids={ (e.get("sessionID")) for e in ev if e.get("sessionID")}
print("session ids seen:",len(sids))
PY
step "C3: what did opencode try to reach? (it writes its own log)"
sh_run 'find /tmp/oc/home -name "*.log" 2>/dev/null | head -3'
for f in $(find /tmp/oc/home -name '*.log' 2>/dev/null | head -2); do echo "--- $f"; grep -i -E "error|fail|models.dev|fetch|proxy|ECONN|ENOTFOUND|timeout" "$f" | mask | head -15 | cut -c1-240; done
step "C4: opencode run without NO_PROXY for the API host (does the proxy path break the internal API?)"
CRUN2=$(echo "$CRUN" | sed -e "s#-e no_proxy=$NP#-e no_proxy=localhost#" -e "s#-e NO_PROXY=$NP#-e NO_PROXY=localhost#")
rm -f /tmp/oc/checkout/hello.txt
s=$(date +%s)
timeout 120 $CRUN2 sh -c '/work/npm/bin/opencode run --format json --auto --model corp/'"$MODEL"' --agent factory-probe "Say pong." ' > /tmp/oc2.out 2>/tmp/oc2.err; rc=$?
echo "exit $rc after $(( $(date +%s)-s )) s; events: $(wc -l < /tmp/oc2.out); first stderr lines:"; head -5 /tmp/oc2.err | mask | cut -c1-240
echo; echo "PROBE DONE"
