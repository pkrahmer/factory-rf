# The operator's hosting client: the code host's API and git over HTTPS, with a token from the site.
# Sourced after site.sh. The token never reaches an argument list, where ps shows it to every user.
#   hosting_token                        print the token; return 0, or 4 when its source fails
#   hosting_api METHOD PATH [BODY]       the API call; print the body; return 0, 4 or 22
#   hosting_repo_api METHOD PATH [BODY]  hosting_api on /repos/$SITE_REPOSITORY$PATH; also 2
#   hosting_git ARG...                   git with the token for https remotes; git's status

_hosting_newline='
'

hosting_token() {
  if ! _hosting_output=$(_hosting_token_source 2>/dev/null); then
    _hosting_no_token
    return 4
  fi
  _hosting_output=${_hosting_output%%"$_hosting_newline"*}
  _hosting_output=$(_site_trim_trailing "$(_site_trim_leading "$_hosting_output")")
  if [ -z "$_hosting_output" ]; then
    _hosting_no_token
    return 4
  fi
  printf '%s\n' "$_hosting_output"
}

hosting_api() {
  _hosting_bearer=$(hosting_token) || return 4
  _hosting_status_file=$(mktemp) || return 22
  # The sentinel keeps the body's trailing newlines, which the substitution would strip.
  _hosting_body=$(_hosting_curl_config "$@" | curl --silent --show-error --max-time 40 --config -
    echo .)
  _hosting_body=${_hosting_body%.}
  _hosting_status=$(cat "$_hosting_status_file")
  rm -f "$_hosting_status_file"
  case $_hosting_status in
    2[0-9][0-9])
      printf '%s' "$_hosting_body"
      ;;
    '' | 000)
      echo "hosting: $1 $2: no answer" >&2
      return 22
      ;;
    *)
      _hosting_message=$(_hosting_error_message "$_hosting_body")
      echo "hosting: $1 $2: $_hosting_status${_hosting_message:+ $_hosting_message}" >&2
      return 22
      ;;
  esac
}

hosting_repo_api() {
  site_require SITE_REPOSITORY || return 2
  _hosting_method=$1
  _hosting_path=/repos/$SITE_REPOSITORY$2
  shift 2
  hosting_api "$_hosting_method" "$_hosting_path" "$@"
}

# git reads its configuration from the environment, so the header is in no argument; the empty
# helper keeps a stored credential from answering instead.
hosting_git() {
  _hosting_secret=$(hosting_token) || return 4
  _hosting_basic=$(printf 'x-access-token:%s' "$_hosting_secret" | base64 | tr -d '\n')
  GIT_CONFIG_COUNT=2 \
    GIT_CONFIG_KEY_0=credential.helper GIT_CONFIG_VALUE_0= \
    GIT_CONFIG_KEY_1=http.extraHeader GIT_CONFIG_VALUE_1="Authorization: Basic $_hosting_basic" \
    GIT_TERMINAL_PROMPT=0 \
    git "$@"
}

_hosting_token_source() {
  if [ -n "${SITE_TOKEN_CMD:-}" ]; then
    sh -c "$SITE_TOKEN_CMD"
  elif command -v gh >/dev/null 2>&1; then
    gh auth token
  else
    return 1
  fi
}

# The source's output may be an error text that holds a secret, so it is never repeated.
_hosting_no_token() {
  echo "hosting: the token command failed; see SITE_TOKEN_CMD in the site file" >&2
}

# Prints curl's configuration for METHOD PATH [BODY]; printf is a builtin, so the token it
# writes is in no process's arguments.
_hosting_curl_config() {
  _hosting_base=${SITE_API_URL:-https://api.github.com}
  printf 'url = "%s"\n' "$(_hosting_quote "${_hosting_base%/}$2")"
  printf 'request = "%s"\n' "$(_hosting_quote "$1")"
  printf 'header = "Authorization: Bearer %s"\n' "$_hosting_bearer"
  printf 'header = "Accept: application/vnd.github+json"\n'
  printf 'header = "X-GitHub-Api-Version: 2022-11-28"\n'
  printf 'write-out = "%%output{%s}%%{http_code}"\n' "$(_hosting_quote "$_hosting_status_file")"
  if [ "$#" -ge 3 ]; then
    printf 'data = "%s"\n' "$(_hosting_quote "$3")"
  fi
}

# The quoted form of curl's configuration: backslash and double quote escaped, a newline as \n.
_hosting_quote() {
  printf '%s\n' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' |
    awk 'NR > 1 { printf "%s", "\\n" } { printf "%s", $0 }'
}

# The JSON message of the body when it has one, else its first 100 characters on one line.
_hosting_error_message() {
  _hosting_flat=$(printf '%s' "$1" | tr '\r\n' '  ')
  _hosting_json=$(printf '%s\n' "$_hosting_flat" |
    sed -n -E 's/.*"message"[[:space:]]*:[[:space:]]*"(([^"\\]|\\.)*)".*/\1/p')
  if [ -n "$_hosting_json" ]; then
    printf '%s' "$_hosting_json"
  else
    _site_trim_trailing "$(printf '%s' "$_hosting_flat" | cut -c1-100)"
  fi
}

# A script that sourced site.sh without loading it gets the site file's values here.
# A failing load has said why; the token source may still be gh, so sourcing goes on.
if ! env | grep -q '^SITE_'; then
  site_load || :
fi
