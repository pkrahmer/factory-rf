# SPDX-License-Identifier: Apache-2.0
"""The labels of a pull request, a projection of its work item's stage that is never read back."""

from factory.shared.domain.paths import LABEL_PREFIX
from factory.work.domain.work_item import WorkItemState


def labels_for(state: WorkItemState) -> list[str]:
    """The factory's labels for a work item in `state`: its stage label alone."""
    return [LABEL_PREFIX + state.stage]
