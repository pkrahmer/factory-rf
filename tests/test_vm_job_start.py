"""The job start script, run with stand-ins for every tool it calls."""

import os
import re
from pathlib import Path

import pytest

from dockerfile_support import _uncommented
from factory.domain.containers import JOB_PODMAN_OPTIONS
from vm_support import (
    HIDDEN_TEXT,
    JOB_CLAUDE_VERSION,
    JOB_CODE_REF,
    JOB_CODE_URL,
    JOB_INSTANCE,
    JOB_OPENCODE_VERSION,
    JOB_START,
    MISSING_REF,
    JobRun,
    StandInCall,
    run_job_start,
)

STEPS = [
    "inputs",
    "proxy",
    "packages",
    "runc",
    "metadata",
    "directories",
    "storage",
    "code",
    "tools",
    "image",
    "token",
    "start",
]
PACKAGES = [
    "podman",
    "uidmap",
    "nftables",
    "git",
    "make",
    "curl",
    "ca-certificates",
    "rsync",
    "python3",
    "python3-venv",
]
REQUIRED = [
    "FACTORY_INSTANCE",
    "FACTORY_REPOSITORY_URL",
    "FACTORY_CODE_URL",
    "FACTORY_CODE_REF",
    "FACTORY_TOKEN_FILE",
]
PROXY = "http://proxy.invalid:3128"
OTHER_PROXY = "http://other-proxy.invalid:8080"
REFRESH_ENDPOINT = "http://token.invalid/token"
RUNC_VERSION = "1.5.2"
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
RUNC_URL = "https://github.com/opencontainers/runc/releases/download/v{}/runc.amd64"
REFRESHER = ["-m", "factory.entry.refresh_token"]
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
RULE = "ip daddr 169.254.169.254 tcp dport 80 reject"
CHAIN = re.compile(r"chain\s+(\w+)\s*\{([^{}]*)\}")
UNREADABLE = "an unreadable file"
UV_REQUIREMENT = re.compile(r"^uv(?:[=<>~!].*)?$")
UNTOUCHED = ["FACTORY_CONTAINER_ENV", "FACTORY_CA_BUNDLE", "FACTORY_IDLE_SHUTDOWN_MINUTES"]


def _derived(root: Path) -> dict[str, str]:
    return {
        "FACTORY_SNAPSHOTS": "copy",
        "FACTORY_SNAPSHOT_BASE": f"{root}/base",
        "FACTORY_WORKSPACE": f"{root}/work",
        "FACTORY_CHECKOUT": f"{root}/repo",
        "FACTORY_STATE": f"{root}/state",
        "FACTORY_CLAUDE_HOME": f"{root}/factory/claude",
        "FACTORY_IMAGE_ID_FILE": f"{root}/image-id",
        "FACTORY_CONTAINER_PROFILE": "job",
        "FACTORY_AGENT_RUNTIME": "opencode",
        "FACTORY_IDLE_SHUTDOWN_ACTION": "exit",
        "FACTORY_CLAUDE_VERSION": JOB_CLAUDE_VERSION,
        "FACTORY_OPENCODE_VERSION": JOB_OPENCODE_VERSION,
    }


def _given(tmp_path: Path) -> dict[str, str]:
    given = tmp_path / "given"
    return {
        "FACTORY_SNAPSHOTS": "zfs",
        "FACTORY_SNAPSHOT_BASE": f"{given}/base",
        "FACTORY_WORKSPACE": f"{given}/work",
        "FACTORY_CHECKOUT": f"{given}/repo",
        "FACTORY_STATE": f"{given}/state",
        "FACTORY_CLAUDE_HOME": f"{given}/claude",
        "FACTORY_IMAGE_ID_FILE": f"{given}/image-id",
        "FACTORY_CONTAINER_PROFILE": "vm",
        "FACTORY_AGENT_RUNTIME": "claude",
        "FACTORY_IDLE_SHUTDOWN_ACTION": "poweroff",
        "FACTORY_CLAUDE_VERSION": "1.2.3",
        "FACTORY_OPENCODE_VERSION": "4.5.6",
        "FACTORY_CONTAINER_ENV": "ONE=1",
        "FACTORY_CA_BUNDLE": f"{given}/ca.pem",
        "FACTORY_IDLE_SHUTDOWN_MINUTES": "30",
    }


def _first(run: JobRun, name: str) -> int:
    return next(index for index, call in enumerate(run.calls) if call.name == name)


def _downloaded(call: StandInCall) -> str:
    flag = next(word for word in ("-o", "--output") if word in call.argv)
    return call.argv[call.argv.index(flag) + 1]


@pytest.fixture
def full_run(tmp_path: Path) -> JobRun:
    """A run with every input given: a proxy, a token endpoint and a stage image."""
    return run_job_start(
        tmp_path,
        {
            "HTTPS_PROXY": PROXY,
            "FACTORY_TOKEN_URL": REFRESH_ENDPOINT,
            "FACTORY_STAGE_IMAGE": "stage:given",
        },
        background=True,
    )


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        *[pytest.param(name, None, f"job-start: {name} is not set", id=name) for name in REQUIRED],
        pytest.param(
            "FACTORY_TOKEN_FILE",
            "/",
            "job-start: FACTORY_TOKEN_FILE is not a file",
            id="token-file-a-directory",
        ),
        pytest.param(
            "FACTORY_TOKEN_FILE",
            UNREADABLE,
            "job-start: FACTORY_TOKEN_FILE is not a file",
            id="token-file-unreadable",
            marks=pytest.mark.skipif(os.geteuid() == 0, reason="root reads every file"),
        ),
    ],
)
def test_a_missing_input_stops_the_script_before_any_call(
    tmp_path: Path, name: str, value: str | None, message: str
) -> None:
    if value == UNREADABLE:
        unreadable = tmp_path / "unreadable-token"
        unreadable.write_text("text\n", encoding="utf-8")
        unreadable.chmod(0)
        value = str(unreadable)
    run = run_job_start(tmp_path, {name: value})

    assert run.result.exit_status == 2
    assert message in run.result.stderr.splitlines()
    assert run.calls == []


def test_the_steps_run_in_order_and_factory_run_replaces_the_script(full_run: JobRun) -> None:
    printed = [
        line for line in full_run.result.stdout.splitlines() if line.startswith("job-start:")
    ]
    order = ["apt-get", "curl", "sha256sum", "install", "nft", "mount", "git", "uv", "podman"]
    once = next(
        index
        for index, call in enumerate(full_run.calls)
        if call.name == "factory-python" and "--once" in call.argv
    )
    started = [index for index, call in enumerate(full_run.calls) if call.name == "factory-run"]

    assert full_run.result.exit_status == 0, full_run.result.stderr
    assert printed == [f"job-start: {step}" for step in STEPS]
    assert [_first(full_run, name) for name in order] == sorted(
        _first(full_run, name) for name in order
    )
    assert _first(full_run, "podman") < once < started[0]
    assert started == [len(full_run.calls) - 1] or (
        len(started) == 1 and full_run.calls[-1].name == "factory-python"
    )
    assert full_run.calls[started[0]].ppid == os.getpid()


@pytest.mark.parametrize("proxy", [PROXY, None], ids=["proxy", "no-proxy"])
def test_apt_goes_through_the_proxy_only_when_one_is_set(tmp_path: Path, proxy: str | None) -> None:
    run = run_job_start(tmp_path, {"HTTPS_PROXY": proxy})
    written = run.prefix / "etc" / "apt" / "apt.conf.d" / "99proxy"

    assert run.result.exit_status == 0, run.result.stderr
    if proxy is None:
        assert not written.exists()
    else:
        lines = written.read_text(encoding="utf-8").splitlines()
        for key in ("Acquire::http::Proxy", "Acquire::https::Proxy"):
            assert [line for line in lines if key in line and proxy in line] != []


def test_the_packages_are_one_install_by_name_alone(tmp_path: Path) -> None:
    run = run_job_start(tmp_path)
    calls = run.named("apt-get")
    installs = [call.argv for call in calls if "install" in call.argv]
    updates = [index for index, call in enumerate(calls) if "update" in call.argv]
    words = installs[0] if len(installs) == 1 else []

    assert len(installs) == 1
    assert updates != [] and updates[0] < [c.argv for c in calls].index(words)
    assert {"-y", "--no-install-recommends"} <= set(words)
    assert sorted(
        word for word in words[words.index("install") + 1 :] if not word.startswith("-")
    ) == (sorted(PACKAGES))
    assert [word for word in words if "=" in word] == []


@pytest.mark.parametrize(
    ("inputs", "version", "checksum"),
    [
        pytest.param({}, RUNC_VERSION, None, id="defaults"),
        pytest.param(
            {"RUNC_VERSION": "1.4.0", "RUNC_SHA256": "b" * 64}, "1.4.0", "b" * 64, id="given"
        ),
    ],
)
def test_runc_is_downloaded_checked_against_its_checksum_and_installed(
    tmp_path: Path, inputs: dict[str, str | None], version: str, checksum: str | None
) -> None:
    run = run_job_start(tmp_path, inputs)
    downloads = run.named("curl")
    runc = [call for call in downloads if RUNC_URL.format(version) in call.argv]
    target = _downloaded(runc[0]) if len(runc) == 1 else ""
    checks = run.named("sha256sum")
    installs = [
        index
        for index, call in enumerate(run.calls)
        if call.name == "install" and str(run.prefix / "usr/local/bin/runc") in call.argv
    ]

    assert run.result.exit_status == 0, run.result.stderr
    assert len(runc) == 1
    assert [call for call in downloads if any("sha256" in word for word in call.argv)] == []
    fed = [call.checked.strip() for call in checks if "-c" in call.argv]
    sums = [line.partition("  ")[0] for line in fed]

    assert fed == [f"{sums[0] if sums else ''}  {target}"]
    assert HEX_64.match(sums[0]) if checksum is None else sums == [checksum]
    assert len(installs) == 1
    assert target in run.calls[installs[0]].argv
    assert _first(run, "sha256sum") < installs[0]


@pytest.mark.parametrize(
    ("inputs", "failing", "status", "message"),
    [
        pytest.param(
            {"RUNC_VERSION": "1.4.0"},
            frozenset[str](),
            2,
            "job-start: RUNC_SHA256 is not set",
            id="version-without-checksum",
        ),
        pytest.param(
            {},
            frozenset({"sha256sum"}),
            1,
            "job-start: runc: checksum does not match",
            id="mismatch",
        ),
    ],
)
def test_runc_without_a_matching_checksum_stops_the_script(
    tmp_path: Path,
    inputs: dict[str, str | None],
    failing: frozenset[str],
    status: int,
    message: str,
) -> None:
    run = run_job_start(tmp_path, inputs, failing=failing)

    assert run.result.exit_status == status
    assert message in run.result.stderr.splitlines()
    assert [call.name for call in run.calls if call.name in {"install", "git", "podman"}] == []
    assert run.named("factory-run") == []
    if status == 2:
        assert run.calls == []


def test_the_metadata_address_is_rejected_on_output_and_forward(tmp_path: Path) -> None:
    run = run_job_start(tmp_path)
    rules = run.root / "metadata-block.nft"
    text = rules.read_text(encoding="utf-8")
    chains = dict(CHAIN.findall(text))
    loads = [call.argv for call in run.named("nft")]

    assert re.search(r"table\s+inet\s+factory_block\b", text)
    assert sorted(chains) == ["blockfwd", "blockout"]
    assert re.search(r"hook\s+output\b", chains["blockout"])
    assert re.search(r"hook\s+forward\b", chains["blockfwd"])
    assert all(RULE in " ".join(body.split()) for body in chains.values())
    assert [argv for argv in loads if "-f" in argv and argv[argv.index("-f") + 1] == str(rules)]


@pytest.mark.parametrize(
    ("ref", "askpass"),
    [
        pytest.param(JOB_CODE_REF, None, id="tag"),
        pytest.param("a" * 40, None, id="commit"),
        pytest.param(JOB_CODE_REF, "/usr/local/bin/askpass-helper", id="job-askpass"),
    ],
)
def test_the_directories_are_made_and_the_code_is_fetched_at_its_ref_without_a_credential(
    tmp_path: Path, ref: str, askpass: str | None
) -> None:
    run = run_job_start(tmp_path, {"FACTORY_CODE_REF": ref, "GIT_ASKPASS": askpass})
    code = str(run.root / "factory")
    clones = [call for call in run.named("git") if "clone" in call.argv]
    checkouts = [call for call in run.named("git") if "checkout" in call.argv]

    assert run.result.exit_status == 0, run.result.stderr
    for name in ("work", "repo", "state", "base"):
        assert (run.root / name).is_dir()
    assert list((run.root / "base").iterdir()) == []
    assert len(clones) == 1
    assert {"--no-checkout", JOB_CODE_URL, code} <= set(clones[0].argv)
    assert len(checkouts) == 1
    words = checkouts[0].argv
    assert words[words.index("-C") + 1] == code
    assert words[words.index("checkout") :] == ["checkout", "--detach", ref]
    for call in run.named("git"):
        assert call.env.get("GIT_TERMINAL_PROMPT") == "0"
        assert "GIT_ASKPASS" not in call.env
        texts = [*call.argv, *call.env.values()]
        assert [text for text in texts if "askpass" in text.lower()] == []


def test_a_ref_that_does_not_exist_stops_the_script(tmp_path: Path) -> None:
    run = run_job_start(tmp_path, {"FACTORY_CODE_REF": MISSING_REF})

    assert run.result.exit_status == 1
    assert f"job-start: code: no ref {MISSING_REF} in {JOB_CODE_URL}" in (
        run.result.stderr.splitlines()
    )
    assert run.named("factory-run") == []


@pytest.mark.parametrize(
    ("image", "expected"),
    [
        ("registry.invalid/stage:1", "registry.invalid/stage:1"),
        (None, f"factory-stage:{JOB_INSTANCE}"),
    ],
    ids=["given", "default"],
)
def test_the_stage_image_is_built_on_a_tmpfs_with_the_job_options(
    tmp_path: Path, image: str | None, expected: str
) -> None:
    run = run_job_start(tmp_path, {"FACTORY_STAGE_IMAGE": image})
    storage = f"{run.prefix}/var/lib/containers"
    mounts = [
        index
        for index, call in enumerate(run.calls)
        if call.name == "mount"
        and storage in call.argv
        and any(call.argv[i : i + 2] == ["-t", "tmpfs"] for i in range(len(call.argv)))
    ]
    builds = [call.argv for call in run.named("podman") if "build" in call.argv]

    assert run.result.exit_status == 0, run.result.stderr
    assert len(mounts) == 1
    assert mounts[0] < _first(run, "podman")
    assert builds == [
        [
            *JOB_PODMAN_OPTIONS,
            "build",
            "--network=host",
            "-f",
            "vm/Dockerfile",
            "--build-arg",
            f"FACTORY_IMAGE={JOB_CODE_REF}",
            "-t",
            expected,
            str(run.root / "factory"),
        ]
    ]
    assert UUID.match((run.root / "image-id").read_text(encoding="utf-8").strip())


def test_a_failed_mount_stops_the_script_before_podman(tmp_path: Path) -> None:
    run = run_job_start(tmp_path, failing=frozenset({"mount"}))
    storage = f"{run.prefix}/var/lib/containers"

    assert run.result.exit_status == 1
    assert f"job-start: storage: cannot mount a tmpfs at {storage}" in (
        run.result.stderr.splitlines()
    )
    assert run.named("podman") == []
    assert run.named("factory-run") == []


@pytest.mark.parametrize(
    ("token_url", "failing", "refresher_calls", "status"),
    [
        pytest.param(
            REFRESH_ENDPOINT, frozenset[str](), [[*REFRESHER, "--once"], REFRESHER], 0, id="set"
        ),
        pytest.param(
            REFRESH_ENDPOINT,
            frozenset({"factory-python"}),
            [[*REFRESHER, "--once"]],
            1,
            id="once-fails",
        ),
        pytest.param(None, frozenset[str](), [], 0, id="unset"),
    ],
)
def test_the_refresher_runs_from_the_factory_environment_when_a_token_url_is_set(
    tmp_path: Path,
    token_url: str | None,
    failing: frozenset[str],
    refresher_calls: list[list[str]],
    status: int,
) -> None:
    run = run_job_start(
        tmp_path,
        {"FACTORY_TOKEN_URL": token_url},
        failing=failing,
        background=refresher_calls == [[*REFRESHER, "--once"], REFRESHER],
    )

    assert run.result.exit_status == status, run.result.stderr
    assert sorted(call.argv for call in run.named("factory-python")) == sorted(refresher_calls)
    assert [c for c in run.named("python3") if "factory.entry.refresh_token" in c.argv] == []
    assert len(run.named("factory-run")) == (1 if status == 0 else 0)


@pytest.mark.parametrize("given", [False, True], ids=["derived", "given"])
def test_factory_run_gets_the_derived_settings_where_the_job_gave_none(
    tmp_path: Path, given: bool
) -> None:
    values = _given(tmp_path)
    run = run_job_start(tmp_path, dict(values) if given else {})
    started = run.named("factory-run")
    expected = values if given else _derived(tmp_path / "root")

    assert run.result.exit_status == 0, run.result.stderr
    assert len(started) == 1
    assert {name: started[0].env.get(name) for name in expected} == expected
    if not given:
        assert [name for name in UNTOUCHED if name in started[0].env] == []


def test_the_token_is_never_printed_written_or_passed_on_a_command_line(
    tmp_path: Path, full_run: JobRun
) -> None:
    written = [
        path
        for folder in (full_run.root, full_run.prefix, tmp_path / "home")
        for path in folder.rglob("*")
        if path.is_file() and HIDDEN_TEXT in path.read_text(encoding="utf-8", errors="replace")
    ]

    assert full_run.result.exit_status == 0, full_run.result.stderr
    assert HIDDEN_TEXT not in full_run.result.stdout + full_run.result.stderr
    assert written == []
    assert [call for call in full_run.calls if HIDDEN_TEXT in " ".join(call.argv)] == []


@pytest.mark.parametrize(
    ("inputs", "seen"),
    [
        pytest.param({"HTTPS_PROXY": PROXY}, PROXY, id="upper"),
        pytest.param({"https_proxy": PROXY}, PROXY, id="lower"),
        pytest.param({"HTTPS_PROXY": PROXY, "https_proxy": OTHER_PROXY}, PROXY, id="both"),
        pytest.param({}, None, id="neither"),
    ],
)
def test_the_proxy_reaches_curl_and_git_under_both_names(
    tmp_path: Path, inputs: dict[str, str | None], seen: str | None
) -> None:
    run = run_job_start(tmp_path, inputs)
    calls = run.named("curl") + run.named("git")

    assert run.result.exit_status == 0, run.result.stderr
    assert run.named("curl") != [] and run.named("git") != []
    for call in calls:
        assert call.env.get("HTTPS_PROXY") == seen
        assert call.env.get("https_proxy") == seen


def test_the_script_holds_the_job_podman_options_of_the_domain() -> None:
    assignments = re.findall(
        r"""^\s*JOB_PODMAN_OPTIONS=(["'])(.*?)\1\s*$""",
        _uncommented(JOB_START.read_text(encoding="utf-8")),
        re.MULTILINE,
    )

    assert len(assignments) == 1
    assert tuple(assignments[0][1].split()) == JOB_PODMAN_OPTIONS


def test_the_default_root_is_written_once_under_srv_factory() -> None:
    lines = [
        line
        for line in _uncommented(JOB_START.read_text(encoding="utf-8")).splitlines()
        if "/srv/factory/" in line
    ]

    assert len(lines) == 1
    assert "FACTORY_JOB_ROOT" in lines[0]
    assert re.search(r"/srv/factory/\$\{?\w+\}?", lines[0])


def test_the_default_prefix_is_written_once_and_empty() -> None:
    code = _uncommented(JOB_START.read_text(encoding="utf-8"))
    defaults = re.findall(r"\$\{FACTORY_JOB_PREFIX:?[-=]([^}]*)\}", code)

    assert defaults == [""]


@pytest.mark.parametrize(
    ("failing", "step"),
    [("curl", "runc"), ("nft", "metadata"), ("apt-get", "packages")],
)
def test_a_failing_step_stops_the_script_before_factory_run(
    tmp_path: Path, failing: str, step: str
) -> None:
    run = run_job_start(tmp_path, failing=frozenset({failing}))

    assert run.result.exit_status == 1
    assert f"job-start: {step}: failed" in run.result.stderr.splitlines()
    assert run.named("factory-run") == []


@pytest.mark.parametrize(
    ("image", "expected"),
    [
        ("registry.invalid/stage:1", "registry.invalid/stage:1"),
        (None, f"factory-stage:{JOB_INSTANCE}"),
    ],
    ids=["given", "default"],
)
def test_factory_run_gets_the_stage_image_the_image_step_built(
    tmp_path: Path, image: str | None, expected: str
) -> None:
    run = run_job_start(tmp_path, {"FACTORY_STAGE_IMAGE": image})
    started = run.named("factory-run")

    assert run.result.exit_status == 0, run.result.stderr
    assert len(started) == 1
    assert started[0].env.get("FACTORY_STAGE_IMAGE") == expected


def test_the_tools_step_installs_uv_in_its_own_environment_and_syncs_the_code(
    tmp_path: Path,
) -> None:
    run = run_job_start(tmp_path)
    tools = run.root / "tools"
    venvs = [
        index
        for index, call in enumerate(run.calls)
        if call.name == "python3" and call.argv == ["-m", "venv", str(tools)]
    ]
    pips = [
        index
        for index, call in enumerate(run.calls)
        if call.program == str(tools / "bin" / "pip")
        and "install" in call.argv
        and any(UV_REQUIREMENT.match(word) for word in call.argv)
    ]
    syncs = [
        (index, call)
        for index, call in enumerate(run.calls)
        if call.program == str(tools / "bin" / "uv") and "sync" in call.argv
    ]

    assert run.result.exit_status == 0, run.result.stderr
    assert len(venvs) == 1
    assert len(pips) == 1
    assert len(syncs) == 1
    assert syncs[0][1].argv == ["sync", "--frozen", "--no-dev"]
    assert Path(syncs[0][1].cwd).resolve() == (run.root / "factory").resolve()
    assert venvs[0] < pips[0] < syncs[0][0] < _first(run, "podman")
