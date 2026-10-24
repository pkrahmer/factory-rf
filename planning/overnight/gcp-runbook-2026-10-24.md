# The GCP machine for v1.2: a runbook for the work machine (2026-10-24)

Written for the human working on a machine without this session, with opencode or by hand. It stands alone: everything needed is in this file and in `planning/v1.2-plan.md`. It prepares the VM and runs the **prototype that settles the plan's open risk** (whether the `factory` user can roll a mounted ZFS dataset back without root) and measures the plan's timings. The factory itself is not installed yet: F0042 and F0043 build the code; the install steps come with F0043's chapter of the operator guide.

The human's decisions this follows (`planning/v1.2-plan.md`, "The human's decisions"): instance `vm`, `e2-standard-2`, `europe-west3`, budget cap $120 a month, the factory as a systemd service under the user `factory`, rootless Podman, `zfs allow` with a `sudoers` line as the fallback, no service account on the VM.

**Rules for whoever runs this.** Never paste a token or key into a chat with an agent; create the secret files by hand. Nothing here needs a secret: the prototype uses public images and no repository. Create no GCP resource beyond the ones listed; the budget alert comes first.

## 1. The project and the budget (console or `gcloud`, once)

```bash
gcloud auth login
gcloud projects create <project-id> --name="factory"
gcloud config set project <project-id>
gcloud billing accounts list
gcloud billing projects link <project-id> --billing-account=<account-id>
gcloud services enable compute.googleapis.com iap.googleapis.com
gcloud billing budgets create --billing-account=<account-id> --display-name="factory" \
  --budget-amount=120USD --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
```

## 2. The network: no inbound port, outbound through NAT, SSH through IAP

The VM gets no external address. It reaches the internet (apt, npm, the Anthropic API, GitHub) through Cloud NAT (about $1 a month plus traffic), and the operator reaches it through IAP's TCP tunnel, which needs one firewall rule for IAP's range only.

```bash
gcloud compute routers create factory-router --network=default --region=europe-west3
gcloud compute routers nats create factory-nat --router=factory-router --region=europe-west3 \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
gcloud compute firewall-rules create allow-iap-ssh --network=default --direction=INGRESS \
  --allow=tcp:22 --source-ranges=35.235.240.0/20
```

The simpler alternative, if NAT is not wanted: give the VM an external address (drop `--no-address` below) and keep the default `default-allow-ssh` rule; port 22 is then open to the world, key-only. The plan prefers the first way.

## 3. The VM and its data disk

```bash
gcloud compute disks create factory-data --size=50GB --type=pd-balanced --zone=europe-west3-a
gcloud compute instances create factory-vm --zone=europe-west3-a --machine-type=e2-standard-2 \
  --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud --boot-disk-size=20GB \
  --no-service-account --no-scopes --no-address \
  --disk=name=factory-data,device-name=factory-data,mode=rw,auto-delete=no
gcloud compute ssh factory-vm --zone=europe-west3-a --tunnel-through-iap
```

`--no-service-account --no-scopes` is the plan's answer to the metadata server: it hands out no token worth having. Costs: about $50 to $55 a month for the VM, $5 for the disk, $1 plus traffic for NAT. Stop the VM when it is not used (`gcloud compute instances stop factory-vm --zone=europe-west3-a`): a stopped VM costs only its disks.

## 4. On the VM: ZFS, Podman, the user, the dataset

```bash
sudo apt-get update
sudo apt-get install -y zfsutils-linux podman uidmap slirp4netns git make curl python3.12-venv
sudo zpool create -o ashift=12 -O compression=lz4 -O atime=off tank /dev/disk/by-id/google-factory-data
sudo useradd --create-home --shell /bin/bash factory
grep factory /etc/subuid /etc/subgid        # rootless podman needs a range for the user; Ubuntu's useradd adds one
sudo loginctl enable-linger factory          # the user's podman and services live without a login session
sudo zfs create tank/factory
sudo zfs create -o mountpoint=/srv/factory/vm/work tank/factory/vm
sudo chown factory:factory /srv/factory/vm/work
sudo zfs allow -u factory snapshot,destroy,rollback,diff,mount tank/factory/vm
sudo zfs allow tank/factory/vm               # shows the delegation
```

Ubuntu's kernel ships the ZFS module signed, so Secure Boot is no obstacle. If `zpool create` says the device is missing, `ls -l /dev/disk/by-id/ | grep google` shows the name.

## 5. The prototype: the rights and the timings, as the user `factory`

Everything below runs as `factory` (`sudo -iu factory`), never as root. Write every output into a file `~/prototype.txt` and bring it back into the repository (section 7).

```bash
sudo -iu factory
cd /srv/factory/vm/work
podman run --rm docker.io/library/alpine:3.20 echo rootless-ok
# a first base
mkdir -p checkout home && echo one > checkout/a
zfs snapshot tank/factory/vm@base
# a container writes, deletes and adds, as the agent would (keep-id: the files belong to factory on the host)
podman run --rm --userns=keep-id -v /srv/factory/vm/work:/work docker.io/library/alpine:3.20 \
  sh -c 'echo two > /work/checkout/b; rm /work/checkout/a; echo three > /work/home/c'
ls -l checkout home                              # b and c belong to factory?
zfs diff -FH tank/factory/vm@base                # expected: - .../checkout/a, + .../checkout/b, + .../home/c
# THE TEST THAT DECIDES: the rollback of a mounted dataset, as a user, through zfs allow
time zfs rollback -r tank/factory/vm@base
ls checkout home                                 # expected: a is back, b and c are gone
# the base moves forward
time sh -c 'zfs destroy tank/factory/vm@base && zfs snapshot tank/factory/vm@base'
# podman's own time limit: the container must end after about 3 s with status 137 (or podman's own code; write it down)
time podman run --rm --timeout 3 docker.io/library/alpine:3.20 sleep 30; echo "status $?"
# container start time, cold and warm
time podman run --rm docker.io/library/alpine:3.20 true
time podman run --rm docker.io/library/alpine:3.20 true
# a read-only mount cannot be written (expected: "Read-only file system")
mkdir -p /tmp/ro && podman run --rm --userns=keep-id -v /tmp/ro:/upstream:ro docker.io/library/alpine:3.20 sh -c 'touch /upstream/x'
```

**If `zfs rollback` is refused** (`permission denied`, or a message about unmounting): that is the Linux limit the plan names. The fallback is one `sudoers` file, as root:

```bash
sudo tee /etc/sudoers.d/factory-zfs >/dev/null <<'EOF'
factory ALL=(root) NOPASSWD: /usr/sbin/zfs snapshot tank/factory/vm@base, /usr/sbin/zfs destroy tank/factory/vm@base, /usr/sbin/zfs rollback -r tank/factory/vm@base, /usr/sbin/zfs diff -FH tank/factory/vm@base
EOF
sudo chmod 0440 /etc/sudoers.d/factory-zfs && sudo visudo -cf /etc/sudoers.d/factory-zfs
```

Then, as `factory`, repeat the rollback as `sudo -n zfs rollback -r tank/factory/vm@base`. The factory's setting `FACTORY_ZFS` is one executable (F0042, decision 14), so on this machine it names a one-line wrapper script that the operator writes once, as root:

```bash
sudo tee /usr/local/bin/zfs-factory >/dev/null <<'EOF'
#!/bin/sh
# The four commands that need root go through sudo; list and --version run plain.
case "$1" in
  snapshot|destroy|rollback|diff) exec sudo -n /usr/sbin/zfs "$@" ;;
  *) exec /usr/sbin/zfs "$@" ;;
esac
EOF
sudo chmod 0755 /usr/local/bin/zfs-factory
```

and `FACTORY_ZFS=/usr/local/bin/zfs-factory`. Four exact commands on one dataset is all the `sudoers` line allows, whatever the wrapper is asked; the adapter's `list` and `--version` need no root (F0043's `setup.sh` writes this wrapper for you later; by hand it is the prototype's).

## 6. A closer prototype of the cycle (optional, with git)

This measures the sync step with a real repository and the read-only upstream mount. It uses a public repository, so no token is needed; the private factory-rf comes with F0043.

```bash
sudo -iu factory
mkdir -p /srv/factory/vm && cd /srv/factory/vm
git clone --bare https://github.com/pkrahmer/factory-timeline.git repo.git   # any small public repository
cd /srv/factory/vm/work
zfs rollback -r tank/factory/vm@base
time podman run --rm --userns=keep-id -v /srv/factory/vm/work:/work -v /srv/factory/vm/repo.git:/upstream:ro \
  docker.io/alpine/git:v2.45.2 sh -c 'cd /work && ([ -d checkout/.git ] || git init -q checkout) && cd checkout && git fetch -q /upstream main && git checkout -qf FETCH_HEAD && git log --oneline -1'
time sh -c 'zfs destroy tank/factory/vm@base && zfs snapshot tank/factory/vm@base'
time podman run --rm --userns=keep-id -v /srv/factory/vm/work:/work docker.io/alpine/git:v2.45.2 \
  sh -c 'cd /work/checkout && echo x > y && git -c user.email=a@b -c user.name=a commit -qam junk; git status --short | head'
zfs diff -FH tank/factory/vm@base | head
time zfs rollback -r tank/factory/vm@base
```

The second sync (after the rollback, fetching nothing new) is the plan's "warm base" case; write its time down. The plan's target for the whole start of a stage is under 20 s.

## 7. What to bring back

A file `planning/overnight/gcp-prototype-results-<date>.md` in the repository, committed and pushed on `main` (pull first), with: the Ubuntu, kernel, zfs and podman versions (`uname -r; zfs version; podman --version`); whether the rollback worked through `zfs allow` or needed the `sudoers` line; the `--timeout` exit status; the times of rollback, snapshot, container start, sync (cold and warm); anything that refused. The plan's F0043 story 2 writes its `setup.sh` from these facts, and F0042 story 2's `FACTORY_ZFS` default follows the rollback's answer.

Leave the VM as section 4 left it (the pool, the user, the dataset, the delegation). Stop it when done.
