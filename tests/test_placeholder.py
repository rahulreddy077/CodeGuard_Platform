import pytest
from modules.quality import compute_quality_metrics
from modules.plagiarism import detect_plagiarism
from modules.ai_detection import check_ai_generated
from modules.ast import parse_code_to_ast

def test_quality_metrics():
    code = "# line 1\n\nprint('hello')\n"
    res = compute_quality_metrics(code)
    assert res["loc"] == 3
    assert res["comment_lines"] == 1
    assert res["empty_lines"] == 1
    assert res["comment_ratio"] == round(1/3, 4)

def test_plagiarism_detection():
    code_a = "def foo(): return 42"
    code_b = "def foo(): return 42"
    res = detect_plagiarism(code_a, code_b)
    assert res["similarity_score"] == 1.0
    assert "foo():" in res["matches"]

def test_ai_detection():
    code = "def bar():\n    '''docstring'''\n    pass"
    res = check_ai_generated(code)
    assert "ai_probability" in res
    assert "heuristics" in res
    assert res["heuristics"]["has_docstring"] is True

def test_ast_parsing():
    code = "class A:\n    def f(self):\n        pass"
    res = parse_code_to_ast(code)
    assert res["success"] is True
    assert "A" in res["classes"]
    assert "f" in res["functions"]
