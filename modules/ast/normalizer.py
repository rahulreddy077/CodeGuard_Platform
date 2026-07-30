import ast
import copy
from modules.ast.parser import parse_code

class DocstringRemover(ast.NodeTransformer):
    """
    AST Transformer that removes docstrings from modules, classes, and functions.
    """
    def _remove_docstring(self, body):
        if not body:
            return body
        first = body[0]
        is_doc = False
        
        # Check for Python Constant strings
        if isinstance(first, ast.Expr):
            if isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                is_doc = True
        
        if is_doc:
            return body[1:]
        return body

    def visit_Module(self, node):
        node.body = self._remove_docstring(node.body)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        node.body = self._remove_docstring(node.body)
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        node.body = self._remove_docstring(node.body)
        return self.generic_visit(node)

    def visit_ClassDef(self, node):
        node.body = self._remove_docstring(node.body)
        return self.generic_visit(node)


class VariableNormalizer(ast.NodeTransformer):
    """
    AST Transformer that normalizes user-defined variable names and parameters
    to VAR_1, VAR_2, VAR_3 sequentially.
    Preserves built-ins, standard self/cls, function names, and class names.
    """
    def __init__(self, func_names=None, class_names=None):
        super().__init__()
        self.var_map = {}
        self.var_count = 0
        self.func_names = func_names or set()
        self.class_names = class_names or set()

    def _get_normalized_name(self, original_name: str) -> str:
        import builtins
        # Do not rename built-ins, common keywords, self/cls, or defined function/class names
        if (original_name in dir(builtins) or
            original_name in {"self", "cls"} or
            original_name in self.func_names or
            original_name in self.class_names):
            return original_name

        if original_name not in self.var_map:
            self.var_count += 1
            self.var_map[original_name] = f"VAR_{self.var_count}"
        return self.var_map[original_name]

    def visit_Name(self, node):
        node.id = self._get_normalized_name(node.id)
        return self.generic_visit(node)

    def visit_arg(self, node):
        node.arg = self._get_normalized_name(node.arg)
        if node.annotation:
            self.visit(node.annotation)
        return node


def normalize_ast(node: ast.AST) -> ast.AST:
    """
    Returns a normalized AST with docstrings removed, variables normalized,
    and missing locations fixed.
    """
    node_copy = copy.deepcopy(node)
    
    # 1. Remove docstrings
    remover = DocstringRemover()
    clean_tree = remover.visit(node_copy)
    
    # 2. Extract function and class names to preserve
    func_names = {n.name for n in ast.walk(clean_tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    class_names = {n.name for n in ast.walk(clean_tree) if isinstance(n, ast.ClassDef)}
    
    # 3. Normalize variables
    var_normalizer = VariableNormalizer(func_names=func_names, class_names=class_names)
    normalized_tree = var_normalizer.visit(clean_tree)
    
    ast.fix_missing_locations(normalized_tree)
    return normalized_tree


def normalize_code(code: str, language: str = "python") -> str:
    """
    Parses code, removes comments, docstrings, blank lines, and unnecessary
    formatting, returning a clean canonical variable-normalized code string.
    """
    if language.lower() == "python":
        try:
            tree = parse_code(code, language="python")
            clean_tree = normalize_ast(tree)
            return ast.unparse(clean_tree)
        except Exception:
            # Fallback text-based normalization if AST parsing fails
            lines = []
            for line in code.splitlines():
                # Strip single-line comments
                clean_line = line.split('#')[0].rstrip()
                if clean_line:
                    lines.append(clean_line)
            return "\n".join(lines)
    else:
        # Generic text-based normalization for other languages (C++, Java, JS comments)
        import re
        # Remove multi-line comments
        no_multiline = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove single-line comments
        lines = []
        for line in no_multiline.splitlines():
            clean_line = line.split('//')[0].rstrip()
            if clean_line:
                lines.append(clean_line)
        return "\n".join(lines)
