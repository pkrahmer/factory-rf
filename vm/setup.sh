#!/bin/sh
# Prepares a fresh Ubuntu 24.04 machine for the factory and installs its service: the packages,
# the ZFS pool and datasets, the user factory, the service's folders, the factory's checkout
# with its virtual environment, the environment file and the systemd unit. Run as root; every
# step does only what is missing, so a second run changes nothing. The checkout needs the
# hosting token, so a first run without it ends at that step and a second run completes it.
set -eu

usage() {
  cat <<'EOF'
usage: setup.sh --device <path> --repository-url <url> [--instance <name>] [--pool <name>] [--quota <size>] [--ref <git ref>] [--image <tag>] [--runtime claude|opencode] [--sudoers] [--help]
  --device <path>           the disk or file the pool is made on, when it does not exist yet
  --repository-url <url>    the repository the factory works on and runs from
  --instance <name>         the instance's name (default vm)
  --pool <name>             the ZFS pool (default tank)
  --quota <size>            the quota of the instance's dataset (default 30G)
  --ref <git ref>           the factory's git ref to check out (default main)
  --image <tag>             the stage image (default factory-stage:<instance>)
  --runtime claude|opencode the agent runtime (default claude)
  --sudoers                 reach zfs through sudo where the delegation does not suffice
  --help                    print this text
EOF
}

fault() {
  printf 'setup.sh: %s\n' "$1" >&2
  usage >&2
  exit 2
}

need_value() {
  if [ $# -lt 2 ]; then
    fault "$1 needs a value"
  fi
  case "$2" in
    --*) fault "$1 needs a value" ;;
  esac
}

device=
repository_url=
instance=vm
pool=tank
quota=30G
ref=main
image=
runtime=claude
sudoers=no

while [ $# -gt 0 ]; do
  case "$1" in
    --help) usage; exit 0 ;;
    --sudoers) sudoers=yes; shift ;;
    --device) need_value "$@"; device=$2; shift 2 ;;
    --repository-url) need_value "$@"; repository_url=$2; shift 2 ;;
    --instance) need_value "$@"; instance=$2; shift 2 ;;
    --pool) need_value "$@"; pool=$2; shift 2 ;;
    --quota) need_value "$@"; quota=$2; shift 2 ;;
    --ref) need_value "$@"; ref=$2; shift 2 ;;
    --image) need_value "$@"; image=$2; shift 2 ;;
    --runtime) need_value "$@"; runtime=$2; shift 2 ;;
    *) fault "unknown word: $1" ;;
  esac
done

if [ -z "$device" ]; then
  fault "--device is required"
fi
if [ -z "$repository_url" ]; then
  fault "--repository-url is required"
fi
case "$runtime" in
  claude|opencode) ;;
  *) fault "--runtime is claude or opencode, not $runtime" ;;
esac
if [ -z "$image" ]; then
  image=factory-stage:$instance
fi

if [ "$(id -u)" != 0 ]; then
  echo "setup.sh: run as root" >&2
  exit 2
fi

base=/srv/factory/$instance
dataset=$pool/factory/$instance
checkout=$base/factory
askpass=$base/askpass
tools=$base/tools
staged=$(mktemp)
trap 'rm -f "$staged"' EXIT

# A file's new text goes to the staging file first, so it is written only when it differs.
stage() {
  cat > "$staged"
}

unchanged() {
  [ -f "$1" ] && cmp -s "$staged" "$1"
}

owned_with_mode() {
  [ -d "$3" ] && [ "$(stat -c '%U:%G %a' "$3")" = "$1 $2" ]
}

# runuser keeps root's environment; git and uv must read and write factory's home instead.
# Every file under $base is written through it: $base is factory's, so a link planted there
# reaches only what factory may write anyway. The text comes through a pipe, since factory
# may not open root's staging file.
as_factory() {
  runuser -u factory -- env HOME=/home/factory "$@"
}

# cat reads the inherited standard input itself: a process runuser started may not open
# root's standard input again by name.
write_as_factory() {
  as_factory sh -c 'cat > "$2" && chmod "$1" "$2"' sh "$1" "$2"
}

# Each step gathers what it changed and prints it as its one line, or what it found done.
changed() {
  changes="$changes; $1"
}

said() {
  if [ -n "$changes" ]; then
    printf '%s' "${changes#; }"
  else
    printf '%s' "$1"
  fi
}

changes=
packages="zfsutils-linux podman uidmap slirp4netns git make python3.12-venv"
missing=
for package in $packages; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    missing="$missing $package"
  fi
done
if [ -n "$missing" ]; then
  apt-get update -q
  # Unquoted on purpose: one word per missing package.
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $missing
  changed "installed$missing"
fi
echo "setup: packages: $(said "found every package installed")"

changes=
if ! zpool list -H -o name "$pool" >/dev/null 2>&1; then
  zpool create -o ashift=12 -O compression=lz4 -O atime=off "$pool" "$device"
  changed "made $pool on $device"
fi
echo "setup: pool: $(said "found $pool")"

changes=
if ! id factory >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash factory
  changed "made factory"
fi
if ! grep -q '^factory:' /etc/subuid || ! grep -q '^factory:' /etc/subgid; then
  echo "setup: user: no subuid and subgid range for factory; add one with usermod --add-subuids and --add-subgids" >&2
  exit 1
fi
echo "setup: user: $(said "found factory with its subuid and subgid ranges")"

changes=
if [ ! -e /var/lib/systemd/linger/factory ]; then
  loginctl enable-linger factory
  changed "enabled linger for factory"
fi
echo "setup: linger: $(said "found linger for factory")"

changes=
if ! zfs list -H -o name "$pool/factory" >/dev/null 2>&1; then
  zfs create "$pool/factory"
  changed "made $pool/factory"
fi
if [ "$(zfs get -H -o value compression,atime "$pool/factory" | tr '\n' ' ')" != "lz4 off " ]; then
  zfs set compression=lz4 atime=off "$pool/factory"
  changed "set compression=lz4 atime=off on $pool/factory"
fi
if ! zfs list -H -o name "$dataset" >/dev/null 2>&1; then
  zfs create -o mountpoint="$base/work" "$dataset"
  changed "made $dataset at $base/work"
fi
if [ "$(zfs get -H -o value quota "$dataset")" != "$quota" ]; then
  zfs set quota="$quota" "$dataset"
  changed "set the quota $quota on $dataset"
fi
if [ "$(stat -c '%U:%G' "$base/work")" != factory:factory ]; then
  install -d -o factory -g factory -m 0755 "$base/work"
  changed "gave $base/work to factory"
fi
echo "setup: datasets: $(said "found $pool/factory and $dataset at $base/work with the quota $quota")"

# zfs allow lists each user's permissions comma-separated, in an order of its own.
# Defined here, after the datasets it reads, so the script's text keeps the order of its steps.
delegated() {
  permissions=$(zfs allow "$dataset" | sed -n 's/^[[:space:]]*user factory //p' | tr '\n' ',')
  for permission in snapshot destroy rollback diff mount; do
    case ",$permissions," in
      *",$permission,"*) ;;
      *) return 1 ;;
    esac
  done
}

changes=
if ! delegated; then
  zfs allow -u factory snapshot,destroy,rollback,diff,mount "$dataset"
  changed "delegated snapshot, destroy, rollback, diff and mount on $dataset to factory"
fi
echo "setup: delegation: $(said "found the delegation to factory on $dataset")"

changes=
zfs_command=zfs
if [ "$sudoers" = yes ]; then
  zfs_command=/usr/local/bin/zfs-factory
  stage <<EOF
factory ALL=(root) NOPASSWD: /usr/sbin/zfs snapshot $dataset@base, /usr/sbin/zfs destroy $dataset@base, /usr/sbin/zfs rollback -r $dataset@base, /usr/sbin/zfs diff -FH $dataset@base
EOF
  if ! unchanged /etc/sudoers.d/factory-zfs; then
    cp "$staged" /etc/sudoers.d/factory-zfs
    chmod 0440 /etc/sudoers.d/factory-zfs
    if ! visudo -cf /etc/sudoers.d/factory-zfs >/dev/null; then
      rm -f /etc/sudoers.d/factory-zfs
      echo "setup: sudoers: visudo -cf refused /etc/sudoers.d/factory-zfs; removed it" >&2
      exit 1
    fi
    changed "wrote /etc/sudoers.d/factory-zfs"
  fi
  stage <<'EOF'
#!/bin/sh
case "$1" in
  rollback|destroy|snapshot|diff) exec sudo -n /usr/sbin/zfs "$@" ;;
  *) exec /usr/sbin/zfs "$@" ;;
esac
EOF
  if ! unchanged /usr/local/bin/zfs-factory; then
    install -m 0755 "$staged" /usr/local/bin/zfs-factory
    changed "wrote /usr/local/bin/zfs-factory"
  fi
  echo "setup: sudoers: $(said "found /etc/sudoers.d/factory-zfs and /usr/local/bin/zfs-factory unchanged")"
else
  echo "setup: sudoers: not asked; the factory reaches zfs through zfs allow, and neither file is touched"
fi

changes=
# A page written through mmap survives zfs rollback in the page cache; the factory drops
# the clean cache after every reset through this helper, whichever way it reaches zfs.
stage <<'EOF'
#!/bin/sh
sync
echo 1 > /proc/sys/vm/drop_caches
EOF
if ! unchanged /usr/local/bin/factory-drop-caches; then
  install -m 0755 "$staged" /usr/local/bin/factory-drop-caches
  changed "wrote /usr/local/bin/factory-drop-caches"
fi
stage <<'EOF'
factory ALL=(root) NOPASSWD: /usr/local/bin/factory-drop-caches
EOF
if ! unchanged /etc/sudoers.d/factory-drop-caches; then
  cp "$staged" /etc/sudoers.d/factory-drop-caches
  chmod 0440 /etc/sudoers.d/factory-drop-caches
  if ! visudo -cf /etc/sudoers.d/factory-drop-caches >/dev/null; then
    rm -f /etc/sudoers.d/factory-drop-caches
    echo "setup: caches: visudo -cf refused /etc/sudoers.d/factory-drop-caches; removed it" >&2
    exit 1
  fi
  changed "wrote /etc/sudoers.d/factory-drop-caches"
fi
echo "setup: caches: $(said "found /usr/local/bin/factory-drop-caches and /etc/sudoers.d/factory-drop-caches unchanged")"

changes=
# install -d as root on a link factory planted there would reach the link's target.
if [ -L "$base/state" ] || [ -L "$base/repo" ] || [ -L /home/factory/.secrets ]; then
  echo "setup: folders: $base/state, $base/repo or /home/factory/.secrets is a link; remove it and run this script again" >&2
  exit 1
fi
if ! owned_with_mode factory:factory 755 "$base" \
  || ! owned_with_mode factory:factory 755 "$base/state" \
  || ! owned_with_mode factory:factory 755 "$base/repo"; then
  install -d -o factory -g factory -m 0755 "$base" "$base/state" "$base/repo"
  changed "made $base, its state and its repo factory's"
fi
if ! owned_with_mode factory:factory 700 /home/factory/.secrets; then
  install -d -o factory -g factory -m 0700 /home/factory/.secrets
  changed "made /home/factory/.secrets factory's alone"
fi
echo "setup: folders: $(said "found $base, its state, its repo and /home/factory/.secrets")"

changes=
if [ ! -s "$base/image-id" ]; then
  write_as_factory 0644 "$base/image-id" < /proc/sys/kernel/random/uuid
  changed "wrote $base/image-id"
fi
echo "setup: image-id: $(said "found $base/image-id")"

changes=
if [ ! -f /home/factory/.secrets/hosting-token ]; then
  echo "setup: checkout: waiting for /home/factory/.secrets/hosting-token; place the secrets and run this script again"
  exit 0
fi
# The token stays in its file; git asks this script for it, so no other file holds it.
stage <<'EOF'
#!/bin/sh
case "$1" in
  Username*) echo x-access-token ;;
  *) cat /home/factory/.secrets/hosting-token ;;
esac
EOF
if ! unchanged "$askpass"; then
  cat "$staged" | write_as_factory 0755 "$askpass"
  changed "wrote $askpass"
fi
# Root's git refuses a repository another user owns, so the clone writes its own askPass.
# Only a fresh clone holds the remote's text before the service ever ran, so only then are
# files of the checkout installed as root.
cloned=no
if [ ! -d "$checkout/.git" ]; then
  as_factory GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 git clone -q --branch "$ref" --config core.askPass="$askpass" "$repository_url" "$checkout"
  cloned=yes
  changed "cloned $ref into $checkout"
fi
echo "setup: checkout: $(said "found $askpass unchanged and $checkout")"

changes=
dockerfile=$checkout/vm/Dockerfile
uv_version=$(sed -n 's/^ARG UV_VERSION=//p' "$dockerfile")
if [ ! -d "$tools" ]; then
  as_factory python3 -m venv "$tools"
  changed "made $tools"
fi
if [ "$(as_factory $tools/bin/uv --version 2>/dev/null || true)" != "uv $uv_version" ]; then
  as_factory $tools/bin/pip install -q "uv==$uv_version"
  changed "installed uv $uv_version"
fi
# uv sync changes nothing when the virtual environment already matches the lockfile.
(cd "$checkout" && as_factory $tools/bin/uv sync --frozen --no-dev)
# The factory's own git reaches the token only through this helper.
if ! cmp -s "$checkout/vm/git-credential-factory" /usr/local/bin/git-credential-factory; then
  if [ "$cloned" = yes ] || [ ! -e /usr/local/bin/git-credential-factory ]; then
    install -m 0755 "$checkout/vm/git-credential-factory" /usr/local/bin/git-credential-factory
    changed "installed /usr/local/bin/git-credential-factory"
  else
    echo 'setup: tools: /usr/local/bin/git-credential-factory differs from the checkout; not installed; install it from your own copy of vm/git-credential-factory (operator guide, "The rebuild after a merge")' >&2
  fi
fi
echo "setup: tools: $(said "found $tools with uv $uv_version, the virtual environment of $checkout in sync and /usr/local/bin/git-credential-factory in place")"

changes=
env_file=$base/factory.env
claude_version=$(sed -n 's/^ARG CLAUDE_CODE_VERSION=//p' "$dockerfile")
opencode_version=$(sed -n 's/^ARG OPENCODE_VERSION=//p' "$dockerfile")
opencode_models=$(sed -n 's/^ENV FACTORY_OPENCODE_MODELS=//p' "$dockerfile")
stage <<EOF
# Written by vm/setup.sh from its arguments and vm/Dockerfile; change those and run it again.
FACTORY_INSTANCE=$instance
FACTORY_REPOSITORY_URL=$repository_url
FACTORY_AGENT_RUNTIME=$runtime
FACTORY_DATASET=$pool/factory/$instance
FACTORY_WORKSPACE=$base/work
FACTORY_STAGE_IMAGE=$image
FACTORY_ZFS=$zfs_command
FACTORY_CHECKOUT=$base/repo
FACTORY_STATE=$base/state
FACTORY_IMAGE_ID_FILE=$base/image-id
FACTORY_CLAUDE_HOME=$base/factory/claude
FACTORY_TOKEN_FILE=/home/factory/.secrets/hosting-token
FACTORY_CLAUDE_LOGIN_FILE=/home/factory/.secrets/claude-token
FACTORY_API_LOGIN_FILE=/home/factory/.secrets/anthropic-api-key
FACTORY_CLAUDE_VERSION=$claude_version
FACTORY_OPENCODE_VERSION=$opencode_version
FACTORY_OPENCODE_MODELS=$opencode_models
PATH=/srv/factory/$instance/tools/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
XDG_RUNTIME_DIR=/run/user/$(id -u factory)
EOF
if ! unchanged "$env_file"; then
  cat "$staged" | write_as_factory 0644 "$env_file"
  changed "wrote $env_file"
fi
echo "setup: environment: $(said "found $env_file unchanged")"

changes=
if ! cmp -s "$checkout/vm/factory.service" /etc/systemd/system/factory@.service; then
  if [ "$cloned" = yes ] || [ ! -e /etc/systemd/system/factory@.service ]; then
    install -m 0644 "$checkout/vm/factory.service" /etc/systemd/system/factory@.service
    changed "installed /etc/systemd/system/factory@.service"
  else
    echo 'setup: service: /etc/systemd/system/factory@.service differs from the checkout; not installed; install it from your own copy of vm/factory.service (operator guide, "The rebuild after a merge")' >&2
  fi
fi
systemctl daemon-reload
if ! systemctl is-enabled --quiet factory@"$instance"; then
  systemctl enable factory@"$instance"
  changed "enabled factory@$instance; it is not started"
fi
echo "setup: service: $(said "found /etc/systemd/system/factory@.service in place and factory@$instance enabled")"

printf 'setup: done: build the stage image and start factory@%s; see the operator guide, "The machine"\n' "$instance"
printf 'setup: local: %s/factory.local.env is yours: the script never writes it; the unit reads it after factory.env\n' "$base"
