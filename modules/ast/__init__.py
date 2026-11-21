from modules.ast.parser import parse_code, ast_to_dict, ParserError
from modules.ast.normalizer import normalize_ast, normalize_code
from modules.ast.fingerprint import generate_fingerprint, hash_fingerprint
from modules.ast.utils import count_nodes, get_functions, get_classes

from modules.quality import validate_python_code

def parse_code_to_ast(code: str) -> dict:
    """
    Parses code into an AST and extracts structure metadata.
    Provides backward compatibility for frontend and verify scripts.
    """
    valid, err_msg = validate_python_code(code)
    if not valid:
        return {
            "success": False,
            "error": err_msg,
            "num_nodes": 0,
            "functions": [],
            "classes": []
        }

    try:
        # Parse original code
        tree = parse_code(code, language="python")
        
        # We can also compute normalized properties
        normalized_tree = normalize_ast(tree)
        norm_code = normalize_code(code, language="python")
        fprint = generate_fingerprint(tree, exclude_context=True, language="python")
        fprint_hash = hash_fingerprint(fprint)
        
        return {
            "success": True,
            "num_nodes": count_nodes(tree, language="python"),
            "functions": get_functions(tree, language="python"),
            "classes": get_classes(tree, language="python"),
            "ast_json": ast_to_dict(tree, language="python"),
            "normalized_code": norm_code,
            "fingerprint": fprint,
            "fingerprint_hash": fprint_hash
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "num_nodes": 0,
            "functions": [],
            "classes": []
        }
