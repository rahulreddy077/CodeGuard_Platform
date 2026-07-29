import sys
import os

# Ensure modules directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.quality import compute_quality_metrics
from modules.plagiarism import detect_plagiarism
from modules.ai_detection import check_ai_generated
from modules.ast import parse_code_to_ast

def test_all():
    print("Verifying CodeGuard setup...")
    
    # 1. Quality metrics
    code = "# line 1\n\nprint('hello')\n"
    res = compute_quality_metrics(code)
    assert res["loc"] == 3, f"Expected LOC=3, got {res['loc']}"
    print("[OK] Quality metrics verified")
    
    # 2. Plagiarism
    code_a = "def foo(): return 42"
    code_b = "def foo(): return 42"
    res = detect_plagiarism(code_a, code_b)
    assert res["similarity_score"] == 1.0
    print("[OK] Plagiarism checker verified")
    
    # 3. AI detection
    code = "def bar():\n    '''docstring'''\n    pass"
    res = check_ai_generated(code)
    assert res["heuristics"]["has_docstring"] is True
    print("[OK] AI detection verified")
    
    # 4. AST
    code = "class A:\n    def f(self):\n        pass"
    res = parse_code_to_ast(code)
    assert res["success"] is True
    assert "A" in res["classes"]
    print("[OK] AST parser verified")
    
    print("\nAll skeleton modules imported and executed successfully!")

if __name__ == "__main__":
    test_all()
