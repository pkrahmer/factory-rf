# A local VM for v1.2 on this PC: a runbook (2026-10-24)

The GCP VM of `planning/overnight/gcp-runbook-2026-10-24.md`, played locally: an Ubuntu 24.04 VM under Hyper-V, managed by Multipass, with a ZFS pool on a file. It lets the prototype (the rollback through `zfs allow`, the timings) and, after F0043, the first stage on a VM happen on this PC, before GCP. What it cannot test: GCP's NAT, IAP, the VM without a service account and the metadata server; those stay for the GCP machine.

**Who does what.** The steps marked **you** need admin rights, a download or a secret, which Claude may not do. The steps marked **Claude** Claude can run from the session once the VM exists (`multipass exec`), because they need no secret and no admin right on Windows.

**When.** Step 1 reboots the PC, which stops Docker and `self`. Do it between two stories: Claude says when no stage is running.

## 1. Hyper-V (you, once, as admin)

In a PowerShell window opened with "Run as administrator":

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

Then reboot. Docker Desktop on WSL2 keeps working beside Hyper-V. After the reboot, start Docker Desktop; Claude restarts `self`.

## 2. Multipass (you, once)

Download the Windows installer from <https://canonical.com/multipass/install> (Canonical's own page) and install it; choose **Hyper-V** as the driver when it asks. Check in a normal PowerShell:

```powershell
multipass version
```

## 3. The VM (you or Claude)

```powershell
multipass launch 24.04 --name factory-vm --cpus 4 --memory 8G --disk 60G
multipass info factory-vm
```

The PC has 20 cores and 63 GB, so 4 cores and 8 GB leave `self` enough room. Stop it when not used: `multipass stop factory-vm`.

## 4. ZFS, Podman, the user, the dataset (Claude, through `multipass exec`)

As the GCP runbook's section 4, with one difference: the pool lies on a file instead of a second disk.

```bash
sudo apt-get update
sudo apt-get install -y zfsutils-linux podman uidmap slirp4netns git make curl python3.12-venv
sudo truncate -s 30G /var/lib/factory-pool.img
sudo zpool create -o ashift=12 -O compression=lz4 -O atime=off tank /var/lib/factory-pool.img
sudo useradd --create-home --shell /bin/bash factory
grep factory /etc/subuid /etc/subgid
sudo loginctl enable-linger factory
sudo zfs create tank/factory
sudo zfs create -o mountpoint=/srv/factory/vm/work tank/factory/vm
sudo chown factory:factory /srv/factory/vm/work
sudo zfs allow -u factory snapshot,destroy,rollback,diff,mount tank/factory/vm
```

## 5. The prototype (Claude)

The GCP runbook's sections 5 and 6 word for word, as `factory` (`sudo -iu factory`), including the `sudoers` fallback and the routing wrapper if the rollback is refused. Claude writes the results into `planning/overnight/gcp-prototype-results-local-<date>.md`, marked "local Hyper-V VM, not GCP", and commits it.

## 6. The first stage on the VM (after F0043 is merged)

- **Claude:** runs `vm/setup.sh` as F0043's chapter "The machine" says, with `--device /var/lib/factory-pool.img` (or skips the pool step, which finds the pool done).
- **You:** place the secret files by hand. From the PC: `multipass transfer <file> factory-vm:/tmp/<name>`, then in the VM `sudo install -m 0600 -o factory -g factory /tmp/<name> /home/factory/.secrets/<name>` and `rm /tmp/<name>`. Claude never copies them.
- **Claude:** builds the stage image, starts the service, follows the board, and logs the timings in the night log, as F0043's precondition of its acceptance asks.

While the VM instance builds, `self` must not claim the same work item; the plan's order (`planning/v1.2-plan.md`, "Both instances for a short while") holds: `self` idles.

## What differs from GCP

| | GCP | local |
|---|---|---|
| the pool's device | `/dev/disk/by-id/google-factory-data` | `/var/lib/factory-pool.img` (a file) |
| access | SSH through IAP | `multipass shell` / `multipass exec` |
| outbound network | Cloud NAT | the PC's |
| metadata server | present, no service account | absent |
| cost | about $55 to $60 a month | none |
