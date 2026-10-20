"""Processes are started in one module only, by no other route, with no other suppressions."""

import ast
import re

from source_search import SRC, imports, modules

OS_PREFIXES = ("exec", "spawn", "posix_spawn")
OS_NAMES = ("system", "popen")
ASYNCIO_NAMES = ("create_subprocess_exec", "create_subprocess_shell")
MARKER = re.compile(r"(?:noqa|nosec|nosemgrep|pragma: allowlist secret)[^#]*")


def _forbidden(module: str, name: str) -> bool:
    if module == "os":
        return name in OS_NAMES or name.startswith(OS_PREFIXES)
    return module == "asyncio" and name in ASYNCIO_NAMES


def _route(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Call):
        return {
            "shell=True"
            for keyword in node.keywords
            if keyword.arg == "shell"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value
        }
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and _forbidden(node.value.id, node.attr)
    ):
        return {f"{node.value.id}.{node.attr}"}
    if isinstance(node, ast.ImportFrom) and node.module:
        module = node.module
        return {f"{module}.{alias.name}" for alias in node.names if _forbidden(module, alias.name)}
    return set()


def routes_to_a_process(tree: ast.Module) -> set[str]:
    """The routes to a process other than `factory.adapters.process` that `tree` uses."""
    return {route for node in ast.walk(tree) for route in _route(node)}


def test_only_the_process_wrapper_imports_subprocess() -> None:
    importers = {name for name, tree in modules().items() if imports(tree, "subprocess")}

    assert importers == {"factory.adapters.process"}


def test_no_module_uses_another_route_to_a_process() -> None:
    snippet = ast.parse('import os\nos.system("true")\n')
    users = {
        name: routes for name, tree in modules().items() if (routes := routes_to_a_process(tree))
    }

    assert routes_to_a_process(snippet) == {"os.system"}
    assert users == {"factory.adapters.process": {"os.execvpe"}}


def test_the_only_suppression_markers_are_the_four_in_the_process_wrapper() -> None:
    markers: dict[str, dict[int, set[str]]] = {}
    for path in sorted(SRC.rglob("*.py")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            found = {match.strip() for match in MARKER.findall(line)}
            if found:
                markers.setdefault(path.relative_to(SRC).as_posix(), {})[number] = found
    process_lines = (SRC / "adapters" / "process.py").read_text(encoding="utf-8").splitlines()
    import_line = next(
        number
        for number, line in enumerate(process_lines, start=1)
        if line.split("#")[0].strip() == "import subprocess"
    )
    popen_line = next(
        number
        for number, line in enumerate(process_lines, start=1)
        if "subprocess.Popen(" in line.split("#")[0]
    )
    exec_line = next(
        number
        for number, line in enumerate(process_lines, start=1)
        if "os.execvpe(" in line.split("#")[0]
    )
    confinement_lines = (SRC / "domain" / "confinement.py").read_text(encoding="utf-8").splitlines()
    shm_line = next(
        number
        for number, line in enumerate(confinement_lines, start=1)
        if '"/dev/shm"' in line.split("#")[0]
    )

    assert markers == {
        "adapters/process.py": {
            import_line: {"noqa: S404", "nosec B404"},
            popen_line: {"noqa: S603", "nosec B603"},
            exec_line: {"noqa: S606", "nosec B606"},
        },
        "domain/confinement.py": {shm_line: {"noqa: S108", "nosec B108"}},
        "entry/leftovers.py": {32: {"noqa: PLR0913"}},
    }
