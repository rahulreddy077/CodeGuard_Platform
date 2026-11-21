"""
CodeGuard - Code Quality & Vulnerability Analysis Module
==========================================================
Computes:
 1. Cyclomatic Complexity & Maintainability Index via Radon
 2. Security Vulnerabilities & CWE IDs via Bandit
 3. Basic code metric statistics (lines, comments, blank lines)
"""

import json
import logging
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

def validate_python_code(code: str):
    if not code or not code.strip():
        return False, "Code snippet cannot be empty."
    import ast
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Invalid Python syntax at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Syntax Error: {str(e)}"
        
    if not tree.body:
        return False, "Invalid code: No executable statements or definitions found."
        
    has_real_statements = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assign, ast.AugAssign, 
                            ast.For, ast.While, ast.If, ast.With, ast.Try, ast.Import, ast.ImportFrom, ast.Call, ast.Return)):
            has_real_statements = True
            break
            
    if not has_real_statements:
        return False, "Input appears to be plain text or prose rather than Python code. Please input valid Python source code."
        
    return True, ""

def compute_quality_metrics(code: str) -> dict:
    """
    Computes quality, complexity, and security audit metrics for a given Python code snippet.
    Validates Python syntax and structure upfront.
    """
    valid, err_msg = validate_python_code(code)
    if not valid:
        return {
            "success": False,
            "error": err_msg
        }

    lines = code.splitlines()
    total_lines = len(lines)
    comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
    blank_lines = sum(1 for line in lines if not line.strip())
    code_lines = total_lines - comment_lines - blank_lines
    
    # 1. Radon Metrics
    cyclomatic_complexity = 1
    maintainability_index = 100.0
    
    try:
        from radon.complexity import cc_visit
        from radon.metrics import mi_visit
        
        blocks = cc_visit(code)
        if blocks:
            cyclomatic_complexity = max(b.complexity for b in blocks)
        else:
            cyclomatic_complexity = 1
            
        maintainability_index = round(mi_visit(code, multi=True), 2)
    except Exception as e:
        logger.warning(f"Radon analysis fallback: {e}")
        # Simple fallback complexity calculation
        cyclomatic_complexity = 1 + code.count("if ") + code.count("for ") + code.count("while ") + code.count("except ")

    # 2. Bandit Security Vulnerability Scanning (SAST)
    vulnerabilities = []
    cwe_findings = []
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name
            
        import sys
        cmd = [sys.executable, "-m", "bandit", "-f", "json", "-q", temp_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.stdout:
            bandit_data = json.loads(res.stdout)
            for item in bandit_data.get("results", []):
                vuln = {
                    "issue_text": item.get("issue_text"),
                    "severity": item.get("issue_severity"),
                    "confidence": item.get("issue_confidence"),
                    "line": item.get("line_number"),
                    "cwe": item.get("issue_cwe", {}).get("id") or "CWE-Unknown",
                    "cwe_link": item.get("issue_cwe", {}).get("link")
                }
                vulnerabilities.append(vuln)
                if vuln["cwe"] not in cwe_findings:
                    cwe_findings.append(vuln["cwe"])
                    
        os.remove(temp_path)
    except Exception as e:
        logger.warning(f"Bandit security scan fallback: {e}")

    # Determine security score (100 = safe, deducted per severity)
    sec_deductions = {"HIGH": 30, "MEDIUM": 15, "LOW": 5}
    security_score = max(0, 100 - sum(sec_deductions.get(v.get("severity", "LOW").upper(), 5) for v in vulnerabilities))
    comment_ratio = round(comment_lines / total_lines, 4) if total_lines > 0 else 0.0

    if cyclomatic_complexity >= 11 or maintainability_index < 50:
        complexity_level = "High"
    elif cyclomatic_complexity >= 6 or maintainability_index < 75:
        complexity_level = "Medium"
    else:
        complexity_level = "Low"

    return {
        "loc": total_lines,
        "lines_of_code": code_lines,
        "total_lines": total_lines,
        "comment_lines": comment_lines,
        "empty_lines": blank_lines,
        "blank_lines": blank_lines,
        "comment_ratio": comment_ratio,
        "complexity_level": complexity_level,
        "cyclomatic_complexity": cyclomatic_complexity,
        "maintainability_index": maintainability_index,
        "security_score": security_score,
        "vulnerabilities_count": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
        "cwe_findings": cwe_findings
    }
