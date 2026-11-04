"""The wired boundaries read the machine from the user's cgroup slice and podman's image store."""

from pathlib import Path

from factory.adapters.fake_hosting import FakeHostingService
from factory.adapters.machine_files import CgroupMachineReadings
from factory.domain.settings import InstanceSettings
from factory.entry.wiring import build_boundaries
from podman_support import IMAGE
from sized_images import SizedImages, sized_by_tag
from wiring_support import CREDENTIAL


def test_the_built_boundaries_read_the_image_store_and_the_cgroup_slice(
    local_settings: InstanceSettings, tmp_path: Path
) -> None:
    store = tmp_path / "image-store"
    store.mkdir()
    settings = local_settings.model_copy(update={"stage_image": IMAGE})

    boundaries = build_boundaries(
        settings,
        CREDENTIAL,
        hosting=FakeHostingService(),
        images=SizedImages(sized_by_tag, store=store),
    )

    assert boundaries.image_store == store
    assert isinstance(boundaries.machine, CgroupMachineReadings)
