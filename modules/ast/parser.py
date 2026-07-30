import ast
from typing import Any, Dict

class ParserError(Exception):
    """Custom exception for syntax or parsing errors."""
    pass

# Registry of language-specific parsers
_PARSER_REGISTRY = {}

def register_parser(language: str):
    def decorator(cls):
        _PARSER_REGISTRY[language.lower()] = cls()
        return cls
    return decorator

class BaseLanguageParser:
    def parse(self, code: str) -> Any:
        raise NotImplementedError("Subclasses must implement parse method")

    def to_dict(self, node: Any) -> Any:
        raise NotImplementedError("Subclasses must implement to_dict method")

@register_parser("python")
class PythonParser(BaseLanguageParser):
    def parse(self, code: str) -> ast.AST:
        try:
            return ast.parse(code)
        except SyntaxError as e:
            # Re-raise standard syntax errors as ParserError with context details
            raise ParserError(f"Python Syntax Error: {e.msg} at line {e.lineno}, col {e.offset}") from e
        except Exception as e:
            raise ParserError(f"Failed to parse Python code: {str(e)}") from e

    def to_dict(self, node: Any) -> Any:
        if not isinstance(node, ast.AST):
            if isinstance(node, list):
                return [self.to_dict(x) for x in node]
            if isinstance(node, bytes):
                return node.decode('utf-8', errors='replace')
            if isinstance(node, complex):
                return str(node)
            if node is Ellipsis:
                return "..."
            if node is not None and not isinstance(node, (str, int, float, bool)):
                return str(node)
            return node

        result = {
            "_type": node.__class__.__name__
        }
        for field, value in ast.iter_fields(node):
            result[field] = self.to_dict(value)
        return result

def parse_code(code: str, language: str = "python") -> Any:
    """
    Parses code of a given language into an AST tree object.
    Raises ParserError if code is invalid or language is unsupported.
    """
    lang_key = language.lower()
    if lang_key not in _PARSER_REGISTRY:
        raise ParserError(f"Unsupported language: {language}")
    return _PARSER_REGISTRY[lang_key].parse(code)

def ast_to_dict(node: Any, language: str = "python") -> Any:
    """
    Recursively converts an AST node for a given language into a serializable dict.
    """
    lang_key = language.lower()
    if lang_key not in _PARSER_REGISTRY:
        raise ParserError(f"Unsupported language: {language}")
    return _PARSER_REGISTRY[lang_key].to_dict(node)
