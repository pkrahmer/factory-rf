"""Reading the top-level functions of a source text and their statements with `ast`."""

import ast


def functions(source: str) -> list[ast.FunctionDef]:
    """Return the functions at the top level of `source`."""
    return [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)]


def without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    """Return the statements of `body`, a leading docstring left aside."""
    match body[0]:
        case ast.Expr(value=ast.Constant(value=str())):
            return body[1:]
        case _:
            return body
