"""The root of `tests/` holds only `conftest.py`, its `README.md` and packages, sorted by kind."""

import ast
from fnmatch import fnmatch
from pathlib import Path

import pytest

TESTS = Path(__file__).parents[1]

FORMER_ROOT_HELPERS = (
    "acceptance_support",
    "acceptance_walk",
    "agent_definition_support",
    "agent_login_support",
    "agent_run_support",
    "bill_support",
    "branch_reading",
    "check_documents_support",
    "claude_reply_support",
    "claude_resume_support",
    "claude_stand_in",
    "command_words_support",
    "container_extra_support",
    "container_runtime_support",
    "container_support",
    "contract_login_support",
    "contract_support",
    "cost_image_support",
    "cost_records_support",
    "crash_support",
    "definition_support",
    "disk_support",
    "dockerfile_support",
    "document_texts",
    "evaluation_support",
    "function_support",
    "git_interface_support",
    "git_support",
    "hosting_interface_support",
    "human_clone",
    "known_results_support",
    "log_support",
    "machine_readings_support",
    "module_names",
    "observing_runtime",
    "opencode_events_support",
    "opencode_provider_support",
    "opencode_resume_support",
    "opencode_stand_in",
    "operator_job_support",
    "operator_skill_support",
    "operator_support",
    "podman_support",
    "power_support",
    "preflight_support",
    "probe_login_support",
    "probe_support",
    "process_support",
    "project_command_support",
    "proof_support",
    "push_retry_support",
    "pygithub_stand_ins",
    "record_support",
    "recording_log",
    "recording_stand_in_support",
    "remote_outage_support",
    "root_support",
    "run_layout_support",
    "run_process_recorder",
    "scripted_tick_support",
    "search_support",
    "sections_support",
    "settings_support",
    "shipped_agents",
    "site_check_support",
    "sized_images",
    "source_search",
    "stage_image_support",
    "stage_run_support",
    "stall_support",
    "story_form_support",
    "take_support",
    "template_make_support",
    "tick_support",
    "time_limits",
    "tmp_path_support",
    "token_support",
    "tool_use_support",
    "torn_record_support",
    "transcript_support",
    "undo_support",
    "vm_support",
    "watch_support",
    "wiring_support",
    "work_item_support",
    "write_path_support",
    "zfs_support",
)

FORMER_ROOT_TEST_MODULES = (
    "test_acceptance_reviewer_disk.py",
    "test_agent_home_wiring.py",
    "test_agent_launch_search.py",
    "test_agent_run_request_search.py",
    "test_approval_description.py",
    "test_areas.py",
    "test_atomic_replace_search.py",
    "test_checkout_hygiene_removed.py",
    "test_claim_ownership.py",
    "test_claude_agent_no_hook.py",
    "test_claude_agent_refusal.py",
    "test_claude_agent_skills.py",
    "test_claude_agent_texts.py",
    "test_claude_agent_texts_decision_log.py",
    "test_claude_agent_texts_description.py",
    "test_claude_agent_texts_docs_slip.py",
    "test_claude_agent_texts_mutants.py",
    "test_claude_agent_texts_review_groups.py",
    "test_claude_agent_texts_review_leave.py",
    "test_claude_agent_texts_smoke_pytest.py",
    "test_claude_files.py",
    "test_claude_settings_git.py",
    "test_contract_login.py",
    "test_contract_provider_limit.py",
    "test_demo_makefile_secrets.py",
    "test_demos.py",
    "test_docker_path_removed.py",
    "test_fault_paths.py",
    "test_fault_paths_7_to_13.py",
    "test_fault_paths_table.py",
    "test_git_credential_helper.py",
    "test_git_support.py",
    "test_home_reset_removed.py",
    "test_hook_removed.py",
    "test_hosting_fake_search.py",
    "test_hosting_search.py",
    "test_human_clone.py",
    "test_kernel_guard_removed.py",
    "test_kill_points.py",
    "test_layers.py",
    "test_left_branch_removed.py",
    "test_leftovers_program_removed.py",
    "test_make_search.py",
    "test_model_configuration.py",
    "test_mount_program_search.py",
    "test_no_agent_login.py",
    "test_no_journal_reading.py",
    "test_no_state_copies.py",
    "test_no_untyped_dicts.py",
    "test_old_layer_packages_removed.py",
    "test_one_stage_environment.py",
    "test_opencode_limit_wait_on_stderr.py",
    "test_opencode_resume_session.py",
    "test_opencode_runtime_search.py",
    "test_opencode_runtime_transcript.py",
    "test_opencode_shared_steps.py",
    "test_operator_hosting.py",
    "test_operator_job.py",
    "test_operator_job_log.py",
    "test_operator_merge_reset.py",
    "test_operator_python_isolation.py",
    "test_operator_sanitise.py",
    "test_operator_site.py",
    "test_operator_site_check.py",
    "test_operator_site_example.py",
    "test_operator_skill_name.py",
    "test_operator_skill_scripts.py",
    "test_operator_skill_signature.py",
    "test_operator_texts.py",
    "test_pins.py",
    "test_pipeline_stage_moves.py",
    "test_process_search.py",
    "test_proof_support.py",
    "test_removed_layer_names.py",
    "test_retrying_wording.py",
    "test_round_cap_answer.py",
    "test_run_module.py",
    "test_second_user_removed.py",
    "test_shared_bodies.py",
    "test_shared_branch_helpers.py",
    "test_shared_constants.py",
    "test_shared_definition.py",
    "test_shared_environments.py",
    "test_shared_fixtures.py",
    "test_shared_imports.py",
    "test_shared_stage_constants.py",
    "test_shared_test_helpers.py",
    "test_shipped_agents_r14.py",
    "test_single_project.py",
    "test_stage_image.py",
    "test_stop_table.py",
    "test_suite_fixtures.py",
    "test_suite_held_once.py",
    "test_suite_leftovers.py",
    "test_suite_old_names.py",
    "test_template_makefile.py",
    "test_template_makefile_header.py",
    "test_template_sync.py",
    "test_test_children.py",
    "test_test_names.py",
    "test_tests_run_under_the_starting_umask.py",
    "test_time_limits.py",
    "test_tmp_path_reopening.py",
    "test_undo_removed.py",
    "test_vm_credential_helper_host.py",
    "test_vm_job_start.py",
    "test_vm_job_start_environment.py",
    "test_vm_job_start_image.py",
    "test_vm_job_start_instance.py",
    "test_vm_job_start_transcripts.py",
    "test_vm_local_environment.py",
    "test_vm_service.py",
    "test_vm_service_stop.py",
    "test_vm_setup.py",
    "test_vm_setup_caches.py",
    "test_vm_setup_code_ref.py",
    "test_vm_setup_code_url.py",
    "test_vm_setup_first_base.py",
    "test_vm_setup_idle_shutdown.py",
    "test_vm_setup_install_hint.py",
    "test_vm_setup_text.py",
    "test_vm_setup_transcripts.py",
    "test_vm_setup_writes.py",
    "test_wrapper_out_of_the_call_path.py",
    "test_wrapper_search.py",
)

PLACEMENTS = (
    ("test_*_search.py", "guards"),
    ("test_*_removed.py", "guards"),
    ("test_shared_*.py", "guards"),
    ("test_no_*.py", "guards"),
    ("test_suite_*.py", "guards"),
    ("test_layers.py", "guards"),
    ("test_areas.py", "guards"),
    ("test_test_names.py", "guards"),
    ("test_tests_run_under_the_starting_umask.py", "guards"),
    ("test_model_configuration.py", "guards"),
    ("test_operator_*.py", "operator_scripts"),
    ("test_vm_*.py", "vm"),
    ("test_stage_image*.py", "vm"),
    ("test_claude_*.py", "agent_files"),
    ("test_shipped_agents*.py", "agent_files"),
    ("test_template_*.py", "agent_files"),
)


def _folders(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_dir() and "__pycache__" not in path.parts and not path.name.startswith(".")
    )


def test_the_root_holds_only_conftest_and_packages() -> None:
    entries = [
        path
        for path in TESTS.iterdir()
        if path.name != "__pycache__" and not path.name.startswith(".")
    ]
    files = sorted(path.name for path in entries if not path.is_dir())
    assert files == ["README.md", "conftest.py"]
    not_packages = [
        path.relative_to(TESTS).as_posix()
        for path in _folders(TESTS)
        if not (path / "__init__.py").is_file()
    ]
    assert not_packages == []


@pytest.mark.parametrize("name", FORMER_ROOT_HELPERS)
def test_a_former_root_helper_lives_only_in_support(name: str) -> None:
    places = sorted(path.relative_to(TESTS).as_posix() for path in TESTS.rglob(f"{name}.py"))
    assert places == [f"support/{name}.py"]


def _bare_helper_imports(tree: ast.Module) -> list[str]:
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                alias.name
                for alias in node.names
                if alias.name.split(".")[0] in FORMER_ROOT_HELPERS
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
            and node.module.split(".")[0] in FORMER_ROOT_HELPERS
        ):
            found.append(node.module)
    return found


def test_no_module_imports_a_helper_by_its_bare_name() -> None:
    offenders = sorted(
        f"{path.relative_to(TESTS).as_posix()}: {name}"
        for path in TESTS.rglob("*.py")
        if "__pycache__" not in path.parts
        for name in _bare_helper_imports(
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        )
    )
    assert offenders == []


def _first_folder(name: str) -> str | None:
    return next((folder for pattern, folder in PLACEMENTS if fnmatch(name, pattern)), None)


@pytest.mark.parametrize(
    ("pattern", "folder"), PLACEMENTS, ids=[pattern for pattern, _ in PLACEMENTS]
)
def test_a_root_test_module_fitting_a_pattern_sits_in_its_folder(pattern: str, folder: str) -> None:
    fitting = [
        name
        for name in FORMER_ROOT_TEST_MODULES
        if fnmatch(name, pattern) and _first_folder(name) == folder
    ]
    assert fitting
    misplaced = sorted(
        name for name in fitting if not (TESTS / folder / name).is_file() or (TESTS / name).exists()
    )
    assert misplaced == []
