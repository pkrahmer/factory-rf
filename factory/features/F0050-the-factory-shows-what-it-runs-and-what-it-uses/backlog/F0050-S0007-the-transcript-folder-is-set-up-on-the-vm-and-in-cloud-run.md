# The transcript folder is set up on the VM and in Cloud Run

## Description

S0005 keeps transcripts in the folder `FACTORY_TRANSCRIPT_DIR` names; this story gives each kind of site that folder. On a VM, `vm/setup.sh` makes `/srv/factory/<instance>/transcripts`, owned by the factory's user with mode `0700`, and writes the two settings into the instance's environment file, with 30 days. In a Cloud Run job the folder is a Cloud Storage bucket of the site's own project, mounted into the job as a volume; the operator creates the bucket, its lifecycle rule and the mount, and `vm/job-start.sh` only checks that the folder it is given can be written. The bucket stays inside the site, readable only by the job's service account and the people the site allows; the factory needs no Cloud Storage client and no new right.

## Interface

- `vm/setup.sh`: a step `transcripts` that makes the folder (owner `factory`, mode `0700`), and two lines in `factory.env`: `FACTORY_TRANSCRIPT_DIR=/srv/factory/<instance>/transcripts` and `FACTORY_TRANSCRIPT_DAYS=30`. A second run of the script finds both done and changes nothing. A new option `--transcript-days <n>` sets another number; `--transcript-days 0` writes neither line and keeps no transcript.
- `vm/job-start.sh`: when `FACTORY_TRANSCRIPT_DIR` is set, it checks before the factory starts that the folder exists and a file can be written and removed there; a failure ends the start with the message `transcript folder <path> cannot be written` and a status that is not 0. When it is unset, nothing changes.
- No change to `src/` beyond what S0005 built.

## Acceptance criteria

1. A run of `vm/setup.sh` makes the folder with owner `factory` and mode `0700` and writes the two lines; a second run changes nothing. Rows: the default, `--transcript-days 7`, `--transcript-days 0` (no lines, no folder), `--transcript-days x` (refused with the option's name).
2. `vm/job-start.sh` with a writable folder starts as before; with a folder that does not exist or cannot be written it ends with the message and a status that is not 0; with the setting unset it starts as before.
3. `make check` stays green. No test creates anything in a cloud.
4. docs: `docs/operator-guide.md`: in *Transcripts*, the VM's folder and the option; for Cloud Run, the steps the operator takes once: a bucket in the job's project and region, uniform access, no public access, a lifecycle rule that deletes objects after 30 days, the job's service account with `roles/storage.objectUser` on that bucket only, and the job's volume mount (`gcloud run jobs update <job> --add-volume name=transcripts,type=cloud-storage,bucket=<bucket> --add-volume-mount volume=transcripts,mount-path=<path>`), with `FACTORY_TRANSCRIPT_DIR=<path>` and no `FACTORY_TRANSCRIPT_DAYS`; and that a bucket costs a few cents a month at these sizes (about 5 MB per feature). `docs/decisions.md`: none beyond S0005's. `README.md` and the project guide: none.

## Smoke test

```bash
grep -c 'FACTORY_TRANSCRIPT_DIR=/srv/factory/' vm/setup.sh
grep -c 'cannot be written' vm/job-start.sh
uv run pytest tests/test_vm_setup.py tests/test_vm_job_start.py 2>&1 | tail -1
```

Expect: a number of at least `1`, a number of at least `1`, then a line that ends in `passed` with no `failed`.

## Journal
