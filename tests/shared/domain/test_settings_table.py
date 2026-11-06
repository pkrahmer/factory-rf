"""The table of the settings names every variable `read_settings` reads, once."""

from collections.abc import Iterator, Mapping
from pathlib import Path

from factory.shared.domain.settings import SETTINGS, read_settings
from support.settings_support import BASE


class _RecordingEnviron(Mapping[str, str]):
    """An environment that notes every key looked up in it."""

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)
        self.looked_up: set[str] = set()

    def __getitem__(self, key: str) -> str:
        self.looked_up.add(key)
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)


def _image_id(_path: Path) -> str:
    return "sha256:" + "a" * 64


def test_settings_table_names_what_read_settings_reads() -> None:
    environ = _RecordingEnviron({**BASE, "FACTORY_IMAGE_ID_FILE": "/srv/factory/image-id"})

    read_settings(environ, _image_id)

    names = [setting.name for setting in SETTINGS]
    assert len(names) == len(set(names))
    assert set(names) == environ.looked_up
