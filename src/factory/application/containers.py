"""The interface through which the factory runs one command in a fresh container on the dataset."""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import timedelta

from factory.domain.containers import ContainerLaunch, ContainerResult, Mount


class ContainerRuns(ABC):
    """One command at a time in a fresh container on the dataset, which is mounted at `/work`."""

    @abstractmethod
    def launch(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerLaunch:
        """The words, environment and time limit that start `command` in a container.

        `ValueError` for a mount whose target is `/work` or lies under it, or for no command words.
        """

    @abstractmethod
    def run(
        self,
        command: Sequence[str],
        *,
        mounts: Sequence[Mount],
        environment: Mapping[str, str],
        time_limit: timedelta,
        working_directory: str,
    ) -> ContainerResult:
        """Run `command` in a container until it ends or reaches `time_limit`; its output merged.

        A failing or timed-out command is a result; `ContainerError` means it could not start.
        `ValueError` as for `launch`.
        """
