import ast
import hashlib
from typing import Any

def generate_fingerprint(node: Any, exclude_context: bool = True, language: str = "python") -> str:
    """
    Traverses the AST in pre-order DFS and returns a sequence of node type class names
    as a space-separated string.
    
    If exclude_context is True, it filters out low-level syntax-context nodes like
    Load, Store, Del (which don't reflect program structure changes).
    """
    if language.lower() == "python":
        if not isinstance(node, ast.AST):
            return ""
            
        sequence = []
        
        # Low-level Python context node types to ignore if exclude_context is True
        context_nodes = {"Load", "Store", "Del"}
        
        def dfs(curr):
            if not isinstance(curr, ast.AST):
                return
            node_name = curr.__class__.__name__
            if not (exclude_context and node_name in context_nodes):
                sequence.append(node_name)
            for child in ast.iter_child_nodes(curr):
                dfs(child)
                
        dfs(node)
        return " ".join(sequence)
    else:
        return ""

def hash_fingerprint(fingerprint_str: str) -> str:
    """
    Computes the SHA256 hash of a structural fingerprint.
    """
    if not fingerprint_str:
        return ""
    return hashlib.sha256(fingerprint_str.encode('utf-8')).hexdigest()
