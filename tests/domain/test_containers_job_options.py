"""The job profile's global podman options."""

from factory.domain.containers import JOB_PODMAN_OPTIONS


def test_the_job_options_store_images_with_the_native_overlay() -> None:
    assert JOB_PODMAN_OPTIONS == (
        "--runtime=runc",
        "--cgroup-manager=cgroupfs",
        "--storage-driver=overlay",
    )
