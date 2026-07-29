import ast

def parse_code_to_ast(code: str) -> dict:
    """
    Parses code into an AST and extracts structure metadata.
    """
    try:
        tree = ast.parse(code)
        num_nodes = len(list(ast.walk(tree)))
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        return {
            "success": True,
            "num_nodes": num_nodes,
            "functions": functions,
            "classes": classes
        }
    except SyntaxError as e:
        return {
            "success": False,
            "error": str(e),
            "num_nodes": 0,
            "functions": [],
            "classes": []
        }
