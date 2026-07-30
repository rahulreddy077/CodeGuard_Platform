import ast
from typing import Any, List

def count_nodes(node: Any, language: str = "python") -> int:
    """
    Counts the total number of nodes in the AST.
    """
    if language.lower() == "python":
        if not isinstance(node, ast.AST):
            return 0
        return len(list(ast.walk(node)))
    return 0

def get_functions(node: Any, language: str = "python") -> List[str]:
    """
    Extracts a list of all function names defined in the AST.
    """
    if language.lower() == "python":
        if not isinstance(node, ast.AST):
            return []
        # Include both sync and async function definitions
        return [n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return []

def get_classes(node: Any, language: str = "python") -> List[str]:
    """
    Extracts a list of all class names defined in the AST.
    """
    if language.lower() == "python":
        if not isinstance(node, ast.AST):
            return []
        return [n.name for n in ast.walk(node) if isinstance(n, ast.ClassDef)]
    return []
