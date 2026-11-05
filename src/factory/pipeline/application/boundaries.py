"""The interfaces that wiring hands to the services, held together in one place."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from factory.agents.application.agent_runtime import AgentDefinitionReader, AgentRuntime
from factory.hosting.application.git import Git
from factory.hosting.application.hosting import HostingService
from factory.machine.application.containers import ContainerRuns
from factory.machine.application.project_commands import ProjectCommands
from factory.machine.application.snapshots import Snapshots
from factory.machine.domain.containers import SYSTEM_PATH
from factory.machine.domain.disk import DiskRecord
from factory.pipeline.domain.known_results import ResultRecord
from factory.pipeline.domain.stops import StopRecord
from factory.shared.application.files import (
    CostRecordReader,
    CostRecordWriter,
    PipelineDefinitionReader,
    RecordLog,
    WorkItemReader,
    WorkItemWriter,
)
from factory.shared.domain.settings import InstanceSettings
from factory.watching.application.machine import (
    Clock,
    DiskSpace,
    FactoryLog,
    HealthStatusStore,
    MachineReadings,
    Waiter,
)
from factory.watching.application.transcripts import TranscriptStore


# Keyword-only so that a field added later never shifts the meaning of an argument.
@dataclass(frozen=True, kw_only=True)
class Boundaries:
    """The outside world as the services see it: one implementation per interface."""

    git: Git
    hosting: HostingService
    agent_runtime: AgentRuntime
    project_commands: ProjectCommands
    work_item_reader: WorkItemReader
    work_item_writer: WorkItemWriter
    cost_reader: CostRecordReader
    cost_writer: CostRecordWriter
    pipeline_reader: PipelineDefinitionReader
    agent_definitions: AgentDefinitionReader
    clock: Clock
    log: FactoryLog
    health: HealthStatusStore
    checkout: Path
    settings: InstanceSettings
    disk: DiskSpace
    disk_records: RecordLog[DiskRecord]
    stop_records: RecordLog[StopRecord]
    waiter: Waiter
    result_records: RecordLog[ResultRecord]
    snapshots: Snapshots
    containers: ContainerRuns
    # What the operator adds to every container's environment, read once from the host.
    container_extra_environment: Mapping[str, str] = field(default_factory=dict)
    # The `PATH` the image every container runs in configures.
    image_path: str = SYSTEM_PATH
    # The kernel's counts of the containers' user; `None` where the machine gives none.
    machine: MachineReadings | None = None
    # The sizes of the image the containers run in, measured when it was built or chosen.
    base_image_bytes: int | None = None
    project_layer_bytes: int | None = None
    # The folder of the image store, whose free space the cost records show.
    image_store: Path | None = None
    # Whether the factory's own shutdown has been asked for: a command it cut off is not judged.
    stop_requested: Callable[[], bool] = lambda: False
    # The folder each run's transcript is kept in; `None` keeps none.
    transcripts: TranscriptStore | None = None
