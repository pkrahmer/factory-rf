"""The container's first process: the runtime's init, which starts the factory and reaps orphans."""

from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).parent.parent
COMPOSE = ROOT / "image" / "compose.yml"
ENTRYPOINT = ROOT / "image" / "entrypoint.sh"


def test_the_container_runs_the_runtimes_init_as_its_first_process() -> None:
    compose = YAML(typ="safe").load(COMPOSE.read_text(encoding="utf-8"))
    assert isinstance(compose, dict)
    factory = compose["services"]["factory"]
    assert isinstance(factory, dict)

    assert factory.get("init") is True


def test_the_entrypoint_hands_over_to_the_factory_with_exec() -> None:
    lines = ENTRYPOINT.read_text(encoding="utf-8").splitlines()
    filled = [line for line in lines if line.strip()]

    assert filled[-1] == "exec python -m factory.entry.run"
