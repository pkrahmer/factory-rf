"""The opencode runtime makes its state directory before it writes a run's files."""

from pathlib import Path

from adapters.claude_stand_in import Step, read_calls
from adapters.opencode_stand_in import MODELS, REPLY_EVENTS, opencode_request, write_opencode
from factory.adapters.opencode_runtime import CONFIG_VARIABLE, OpencodeRuntime


def test_a_run_makes_its_missing_state_directory_and_writes_its_configuration_there(
    tmp_path: Path,
) -> None:
    executable = write_opencode(tmp_path / "bin", [Step(stdout=REPLY_EVENTS)])
    state = tmp_path / "empty-state" / "runs"
    runtime = OpencodeRuntime(str(executable), state, models=MODELS)

    runtime.run(opencode_request(tmp_path / "work"))

    [call] = read_calls(tmp_path / "bin")
    config = call.environment[CONFIG_VARIABLE]
    assert state.is_dir()
    assert Path(config).parent == state
    assert config in call.files
