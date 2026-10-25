"""The interfaces that wiring hands to the services, held together in one place."""

from dataclasses import dataclass
from pathlib import Path

from factory.application.agent_runtime import AgentDefinitionReader, AgentRuntime
from factory.application.containers import ContainerRuns
from factory.application.files import (
    CostRecordReader,
    CostRecordWriter,
    PipelineDefinitionReader,
    RecordLog,
    WorkItemReader,
    WorkItemWriter,
)
from factory.application.git import Git
from factory.application.hosting import HostingService
from factory.application.machine import Clock, DiskSpace, FactoryLog, HealthStatusStore, Waiter
from factory.application.project_commands import ProjectCommands
from factory.application.snapshots import Snapshots
from factory.domain.disk import DiskRecord
from factory.domain.known_results import ResultRecord
from factory.domain.settings import InstanceSettings
from factory.domain.stops import StopRecord


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
