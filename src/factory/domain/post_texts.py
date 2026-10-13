"""The texts the factory writes on the hosting service."""

from factory.domain.identifiers import WorkItemId


def opened_for_stop_description(work_item: WorkItemId) -> str:
    """The description of a draft pull request the factory opened to report a stop."""
    return (
        f"The factory opened this draft pull request to report a stop on {work_item}."
        " The stop is the comment below."
    )
