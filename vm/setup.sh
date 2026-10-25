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
as_factory() {
  runuser -u factory -- env HOME=/home/factory "$@"
}

packages="zfsutils-linux podman uidmap slirp4netns git make python3.12-venv"
missing=
for package in $packages; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
    missing="$missing $package"
  fi
done
if [ -z "$missing" ]; then
  echo "setup: packages: found every package installed"
else
  apt-get update -q
  # Unquoted on purpose: one word per missing package.
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $missing
  echo "setup: packages: installed$missing"
fi

if zpool list -H -o name "$pool" >/dev/null 2>&1; then
  echo "setup: pool: found $pool"
else
  zpool create -o ashift=12 -O compression=lz4 -O atime=off "$pool" "$device"
  echo "setup: pool: made $pool on $device"
fi

if id factory >/dev/null 2>&1; then
  echo "setup: user: found factory"
else
  useradd --create-home --shell /bin/bash factory
  echo "setup: user: made factory"
fi
if ! grep -q '^factory:' /etc/subuid || ! grep -q '^factory:' /etc/subgid; then
  echo "setup: user: no subuid and subgid range for factory; add one with usermod --add-subuids and --add-subgids" >&2
  exit 1
fi
echo "setup: user: found the subuid and subgid ranges of factory"

if [ -e /var/lib/systemd/linger/factory ]; then
  echo "setup: linger: found linger for factory"
else
  loginctl enable-linger factory
  echo "setup: linger: enabled linger for factory"
fi

if zfs list -H -o name "$pool/factory" >/dev/null 2>&1; then
  echo "setup: datasets: found $pool/factory"
else
  zfs create "$pool/factory"
  echo "setup: datasets: made $pool/factory"
fi
zfs set compression=lz4 atime=off "$pool/factory"
if zfs list -H -o name "$dataset" >/dev/null 2>&1; then
  echo "setup: datasets: found $dataset"
else
  zfs create -o mountpoint="$base/work" "$dataset"
  echo "setup: datasets: made $dataset at $base/work"
fi
zfs set quota="$quota" "$dataset"
chown factory:factory "$base/work"
echo "setup: datasets: $dataset has the quota $quota and its mount point is factory's"

if zfs allow "$dataset" | grep -q 'user factory diff,destroy,mount,rollback,snapshot'; then
  echo "setup: delegation: found the delegation to factory on $dataset"
else
  zfs allow -u factory snapshot,destroy,rollback,diff,mount "$dataset"
  echo "setup: delegation: delegated snapshot, destroy, rollback, diff and mount on $dataset to factory"
fi

zfs_command=zfs
if [ "$sudoers" = yes ]; then
  zfs_command=/usr/local/bin/zfs-factory
  stage <<EOF
factory ALL=(root) NOPASSWD: /usr/sbin/zfs snapshot $dataset@base, /usr/sbin/zfs destroy $dataset@base, /usr/sbin/zfs rollback -r $dataset@base, /usr/sbin/zfs diff -FH $dataset@base
EOF
  if unchanged /etc/sudoers.d/factory-zfs; then
    echo "setup: sudoers: found /etc/sudoers.d/factory-zfs unchanged"
  else
    cp "$staged" /etc/sudoers.d/factory-zfs
    chmod 0440 /etc/sudoers.d/factory-zfs
    if ! visudo -cf /etc/sudoers.d/factory-zfs >/dev/null; then
      rm -f /etc/sudoers.d/factory-zfs
      echo "setup: sudoers: visudo -cf refused /etc/sudoers.d/factory-zfs; removed it" >&2
      exit 1
    fi
    echo "setup: sudoers: wrote /etc/sudoers.d/factory-zfs"
  fi
  stage <<'EOF'
#!/bin/sh
case "$1" in
  rollback|destroy|snapshot|diff) exec sudo -n /usr/sbin/zfs "$@" ;;
  *) exec /usr/sbin/zfs "$@" ;;
esac
EOF
  if unchanged /usr/local/bin/zfs-factory; then
    echo "setup: sudoers: found /usr/local/bin/zfs-factory unchanged"
  else
    install -m 0755 "$staged" /usr/local/bin/zfs-factory
    echo "setup: sudoers: wrote /usr/local/bin/zfs-factory"
  fi
else
  echo "setup: sudoers: not asked; the factory reaches zfs through zfs allow, and neither file is touched"
fi

if owned_with_mode factory:factory 755 "$base" \
  && owned_with_mode factory:factory 755 "$base/state" \
  && owned_with_mode factory:factory 755 "$base/repo"; then
  echo "setup: folders: found $base, its state and its repo"
else
  install -d -o factory -g factory -m 0755 "$base" "$base/state" "$base/repo"
  echo "setup: folders: made $base, its state and its repo factory's"
fi
if owned_with_mode factory:factory 700 /home/factory/.secrets; then
  echo "setup: folders: found /home/factory/.secrets"
else
  install -d -o factory -g factory -m 0700 /home/factory/.secrets
  echo "setup: folders: made /home/factory/.secrets factory's alone"
fi

if [ -s "$base/image-id" ]; then
  echo "setup: image-id: found $base/image-id"
else
  cat /proc/sys/kernel/random/uuid > "$base/image-id"
  chown factory:factory "$base/image-id"
  chmod 0644 "$base/image-id"
  echo "setup: image-id: wrote $base/image-id"
fi

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
if unchanged "$askpass"; then
  echo "setup: checkout: found $askpass unchanged"
else
  install -m 0755 -o factory -g factory "$staged" "$askpass"
  echo "setup: checkout: wrote $askpass"
fi
# Root's git refuses a repository another user owns, so the clone writes its own askPass.
if [ -d "$checkout/.git" ]; then
  echo "setup: checkout: found $checkout"
else
  as_factory GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 git clone -q --branch "$ref" --config core.askPass="$askpass" "$repository_url" "$checkout"
  echo "setup: checkout: cloned $ref into $checkout"
fi

dockerfile=$checkout/vm/Dockerfile
uv_version=$(sed -n 's/^ARG UV_VERSION=//p' "$dockerfile")
if [ -d "$tools" ]; then
  echo "setup: tools: found $tools"
else
  as_factory python3 -m venv "$tools"
  echo "setup: tools: made $tools"
fi
if [ "$(as_factory $tools/bin/uv --version 2>/dev/null || true)" = "uv $uv_version" ]; then
  echo "setup: tools: found uv $uv_version"
else
  as_factory $tools/bin/pip install -q "uv==$uv_version"
  echo "setup: tools: installed uv $uv_version"
fi
(cd "$checkout" && as_factory $tools/bin/uv sync --frozen --no-dev)
echo "setup: tools: synced the virtual environment of $checkout"
# The factory's own git reaches the token only through this helper.
if cmp -s "$checkout/image/git-credential-factory" /usr/local/bin/git-credential-factory; then
  echo "setup: tools: found /usr/local/bin/git-credential-factory unchanged"
else
  install -m 0755 "$checkout/image/git-credential-factory" /usr/local/bin/git-credential-factory
  echo "setup: tools: installed /usr/local/bin/git-credential-factory"
fi

env_file=$base/factory.env
claude_version=$(sed -n 's/^ARG CLAUDE_CODE_VERSION=//p' "$dockerfile")
opencode_version=$(sed -n 's/^ARG OPENCODE_VERSION=//p' "$dockerfile")
opencode_models=$(sed -n 's/^ENV FACTORY_OPENCODE_MODELS=//p' "$dockerfile")
stage <<EOF
# Written by vm/setup.sh from its arguments and vm/Dockerfile; change those and run it again.
FACTORY_INSTANCE=$instance
FACTORY_REPOSITORY_URL=$repository_url
FACTORY_AGENT_RUNTIME=$runtime
FACTORY_STAGE_ENVIRONMENT=container
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
if unchanged "$env_file"; then
  echo "setup: environment: found $env_file unchanged"
else
  install -m 0644 "$staged" "$env_file"
  echo "setup: environment: wrote $env_file"
fi

if cmp -s "$checkout/vm/factory.service" /etc/systemd/system/factory@.service; then
  echo "setup: service: found /etc/systemd/system/factory@.service unchanged"
else
  install -m 0644 "$checkout/vm/factory.service" /etc/systemd/system/factory@.service
  echo "setup: service: installed /etc/systemd/system/factory@.service"
fi
systemctl daemon-reload
if systemctl is-enabled --quiet factory@"$instance"; then
  echo "setup: service: found factory@$instance enabled"
else
  systemctl enable factory@"$instance"
  echo "setup: service: enabled factory@$instance; it is not started"
fi

printf 'setup: done: build the stage image and start factory@%s; see the operator guide, "The machine"\n' "$instance"
