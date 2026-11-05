"""The service unit's stop of the instance's containers after every end of the service."""

from support.vm_support import SERVICE

STOP = "ExecStopPost=-/usr/bin/podman stop --filter label=factory.instance=%i"
EARLIER_LINES = [
    "# The factory as a system service, one instance per name: factory@vm runs the instance vm.",
    "# vm/setup.sh installs it as factory@.service and enables it; the operator starts it.",
    "[Unit]",
    "Description=The factory, instance %i",
    "After=network-online.target zfs.target",
    "Wants=network-online.target",
    "",
    "[Service]",
    "User=factory",
    "Group=factory",
    "WorkingDirectory=/srv/factory/%i",
    "EnvironmentFile=/srv/factory/%i/factory.env",
    "EnvironmentFile=-/srv/factory/%i/factory.local.env",
    "ExecStart=/srv/factory/%i/factory/.venv/bin/factory-run",
    "Restart=always",
    "RestartSec=15",
    "",
    "[Install]",
    "WantedBy=multi-user.target",
]


def test_the_unit_stops_the_instances_containers_after_its_start_line() -> None:
    lines = SERVICE.read_text(encoding="utf-8").splitlines()

    assert lines.count(STOP) == 1
    start = next(index for index, line in enumerate(lines) if line.startswith("ExecStart="))
    assert start < lines.index(STOP)
    assert [line for line in lines if line != STOP] == EARLIER_LINES
