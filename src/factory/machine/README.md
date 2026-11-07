# The machine area

Containers, images, snapshots, disks, the project's commands and the preflight. [The guide page](../../../docs/project-guide/machine.md) explains it.

- `adapters/` The ZFS, podman and make implementations, the copy snapshots, the fakes, the disk reading and the power-off.
- `application/` The interfaces of the stage environment, containers, images, snapshots and the project's commands, and the preflight.
- `domain/` The data of container runs, command records, the disk and the preflight.
