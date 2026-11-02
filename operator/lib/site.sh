# The operator's site file: one place for a site's own values, read and never executed.
# Sourced by the operator's scripts; prints nothing of its own on success.
#   site_path             print the site file's path
#   site_load             export every SITE_ value of the file; return 0, 1 (missing), 2 (fault), 3 (in a repository)
#   site_require NAME...  return 0, or 2 naming every NAME that is unset or empty
#   site_value NAME       print the variable's value, nothing when it is unset
#   site_refuse_repository PATH  return 3 with a message when PATH lies in a git work tree

site_path() {
  if [ -n "${FACTORY_SITE:-}" ]; then
    printf '%s\n' "$FACTORY_SITE"
  elif [ -n "${XDG_CONFIG_HOME:-}" ]; then
    printf '%s\n' "$XDG_CONFIG_HOME/kumpel/site.env"
  else
    printf '%s\n' "$HOME/.config/kumpel/site.env"
  fi
}

# The site file holds company values, so it must never land in a repository's history.
site_refuse_repository() {
  if _site_in_work_tree "$1"; then
    echo "site: $1 lies in a git repository; keep the site file outside every repository" >&2
    return 3
  fi
}

site_load() {
  _site_file=$(site_path)
  if [ ! -f "$_site_file" ]; then
    echo "site: no site file at $_site_file; run: site init" >&2
    return 1
  fi
  site_refuse_repository "$_site_file" || return 3
  # Check every line before exporting any, so a faulty file leaves the environment as it was.
  _site_read check "$_site_file" || return 2
  _site_read export "$_site_file"
}

# The name reaches eval only once it is known to be a plain variable name.
site_value() {
  _site_is_name "$1" || return 1
  eval "printf '%s' \"\${$1:-}\""
}

site_require() {
  _site_missing=
  for _site_name in "$@"; do
    case $_site_name in
      SITE_*) ;;
      *) _site_name=SITE_$_site_name ;;
    esac
    if [ -z "$(site_value "$_site_name")" ]; then
      _site_missing="${_site_missing:+$_site_missing, }$_site_name"
    fi
  done
  if [ -n "$_site_missing" ]; then
    echo "site: missing $_site_missing in $(site_path)" >&2
    return 2
  fi
}

# A path's folder may not exist yet (site init), so ask git from its nearest existing ancestor.
_site_in_work_tree() {
  _site_folder=$(dirname "$1")
  while [ ! -d "$_site_folder" ]; do
    _site_folder=$(dirname "$_site_folder")
  done
  [ "$(git -C "$_site_folder" rev-parse --is-inside-work-tree 2>/dev/null)" = true ]
}

# Runs over every line of the file: `check` reports the first fault, `export` exports the values.
_site_read() {
  _site_number=0
  while IFS= read -r _site_line || [ -n "$_site_line" ]; do
    _site_number=$((_site_number + 1))
    _site_parse_line "$2" || return 2
    if [ "$1" = export ] && [ -n "$_site_key" ]; then
      _site_export "$_site_key" "$_site_value"
    fi
  done < "$2"
}

# Sets _site_key and _site_value from _site_line; an empty _site_key is a blank or comment line.
_site_parse_line() {
  _site_key=
  case $(_site_trim_leading "$_site_line") in
    '' | '#'*) return 0 ;;
  esac
  case $_site_line in
    *=*) ;;
    *) _site_fault "$1" "not a KEY=value line"; return 1 ;;
  esac
  _site_key=${_site_line%%=*}
  if ! _site_is_name "$_site_key"; then
    _site_fault "$1" "not a KEY=value line"
    return 1
  fi
  case $_site_key in
    SITE_?*) ;;
    *) _site_fault "$1" "$_site_key is not a SITE_ key"; return 1 ;;
  esac
  _site_value=$(_site_unquote "$(_site_trim_trailing "${_site_line#*=}")")
}

_site_fault() {
  echo "site: $1:$_site_number: $2" >&2
}

_site_is_name() {
  case $1 in
    '' | *[!ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_]*) return 1 ;;
  esac
}

# The value reaches eval only as a variable reference, so its text is never run.
_site_export() {
  eval "_site_is_set=\${$1+set}"
  if [ -z "$_site_is_set" ]; then
    eval "$1=\$2"
    export "$1"
  fi
}

_site_trim_leading() {
  _site_text=$1
  while :; do
    case $_site_text in
      [[:space:]]*) _site_text=${_site_text#?} ;;
      *) break ;;
    esac
  done
  printf '%s' "$_site_text"
}

_site_trim_trailing() {
  _site_text=$1
  while :; do
    case $_site_text in
      *[[:space:]]) _site_text=${_site_text%?} ;;
      *) break ;;
    esac
  done
  printf '%s' "$_site_text"
}

# One pair of matching quotes around the whole value goes; a lone quote stays.
_site_unquote() {
  case $1 in
    \"*\" | \'*\')
      _site_text=${1#?}
      printf '%s' "${_site_text%?}"
      ;;
    *) printf '%s' "$1" ;;
  esac
}
