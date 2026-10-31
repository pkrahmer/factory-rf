# P20: can a job reach a private repository on github.com with a token, as the factory's runtime must?
# The factory talks to GitHub twice: git over HTTPS (clone, fetch, push) and the REST API (PyGithub, pull
# requests). This probe checks both from a job, through the proxy, without writing anything: DNS, the API
# unauthenticated, the API and git with a token, and a shallow clone, with timings.
# Inputs: PROBE_PROXY and PROBE_NO_PROXY as for every probe; GIT_TOKEN, a mounted secret (never printed);
# PROBE_LLM_BASE_URL, reused here as the repository to check, written <owner>/<repo> (run_probe.sh passes no
# other free variable). The repository's name and the token's owner are never printed. Needs no model.
setup_env
apt_install curl git ca-certificates jq python3 procps
echo "=====BEGIN-RESULTS====="
since() { echo "$(( $(date +%s) - $1 )) s"; }
R=${PROBE_LLM_BASE_URL:-}

step "inputs (presence only)"
echo "GIT_TOKEN set: $([ -n "${GIT_TOKEN:-}" ] && echo yes || echo NO); repository given: $([ -n "$R" ] && echo yes || echo NO); proxy given: $([ -n "${PROBE_PROXY:-}" ] && echo yes || echo no)"
[ -n "${GIT_TOKEN:-}" ] && [ -n "$R" ] || { echo "missing input: stopping"; echo "PROBE DONE"; exit 0; }
echo "token kind: $(printf %s "$GIT_TOKEN" | cut -d_ -f1)_"

step "1: the host, through the proxy and directly"
getent hosts github.com | head -1 | awk '{print "DNS github.com resolves: yes"}'; getent hosts github.com >/dev/null || echo "DNS github.com resolves: NO"
echo "api.github.com unauthenticated via proxy: $(curl -sS -m 20 -o /dev/null -w '%{http_code}' https://api.github.com/rate_limit 2>&1 | tail -1)"
echo "api.github.com unauthenticated, no proxy: $(env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY curl -sS -m 10 -o /dev/null -w '%{http_code}' https://api.github.com/rate_limit 2>&1 | tail -1 | cut -c1-100)"

step "2: the API with the token (names, status and permissions only)"
curl -sS -m 30 -o /tmp/u.json -w 'GET /user: %{http_code}\n' -H "Authorization: Bearer $GIT_TOKEN" -H "Accept: application/vnd.github+json" https://api.github.com/user 2>&1 | tail -1
echo "token user present: $(jq -r 'if .login then "yes" else "no" end' /tmp/u.json 2>/dev/null)"
curl -sS -m 30 -o /tmp/r.json -w 'GET /repos/<repo>: %{http_code}\n' -H "Authorization: Bearer $GIT_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$R" 2>&1 | tail -1
jq -r '"private \(.private), default branch \(.default_branch), merge commits allowed \(.allow_merge_commit), delete head branches \(.delete_branch_on_merge), permissions \(.permissions)"' /tmp/r.json 2>/dev/null | head -2
jq -r '.message // empty' /tmp/r.json 2>/dev/null | sed "s|$R|<repo>|g" | cut -c1-200
rm -f /tmp/u.json /tmp/r.json

step "3: git over HTTPS with the token"
AUTH="Authorization: Basic $(printf 'x-access-token:%s' "$GIT_TOKEN" | base64 | tr -d '\n')"
s=$(date +%s)
GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c http.extraHeader="$AUTH" ls-remote "https://github.com/$R.git" 2>&1 | sed "s|$R|<repo>|g" | awk '{print substr($0,1,12), $2}' | head -3
echo "ls-remote exit ${?} after $(since $s)"
s=$(date +%s)
GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c http.extraHeader="$AUTH" clone -q --depth 1 "https://github.com/$R.git" /tmp/clone 2>&1 | sed "s|$R|<repo>|g" | tail -2
echo "shallow clone after $(since $s): $(git -C /tmp/clone ls-files 2>/dev/null | wc -l) files, $(du -sk /tmp/clone 2>/dev/null | cut -f1) KiB"
rm -rf /tmp/clone

step "4: the pull-request API is readable"
curl -sS -m 30 -o /tmp/p.json -w 'GET /pulls: %{http_code}\n' -H "Authorization: Bearer $GIT_TOKEN" -H "Accept: application/vnd.github+json" "https://api.github.com/repos/$R/pulls?state=all&per_page=1" 2>&1 | tail -1
jq -r 'if type=="array" then "pull requests listed: \(length)" else (.message // "") end' /tmp/p.json 2>/dev/null | sed "s|$R|<repo>|g" | cut -c1-160
rm -f /tmp/p.json

echo
echo "VERDICT: a job can run the factory against a github.com repository if the API and git both answer 200 with the token through the proxy, the clone works, and the repository's permissions show push."
echo "PROBE DONE"
