"""The paths of a work item moved from one lifecycle folder of its feature to another."""

from factory.domain.paths import LifecycleFolder, folder_of


def destination_path(path: str, folder: LifecycleFolder) -> str:
    """Return the same file in `folder` of the same feature; `ValueError` outside the folders."""
    if folder_of(path) is None:
        raise ValueError(f"not a work item in a lifecycle folder: {path!r}")
    feature_directory, _, file_name = path.rsplit("/", 2)
    return f"{feature_directory}/{folder}/{file_name}"
