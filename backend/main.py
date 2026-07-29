from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional

# Import modules from the modules directory
from modules.quality import compute_quality_metrics
from modules.plagiarism import detect_plagiarism
from modules.ai_detection import check_ai_generated
from modules.ast import parse_code_to_ast

app = FastAPI(
    title="CodeGuard API",
    description="Backend API for CodeGuard - Code Quality, Plagiarism, AST, and AI Generation analysis",
    version="1.0.0"
)

class CodeSubmission(BaseModel):
    code: str

class PlagiarismSubmission(BaseModel):
    code_a: str
    code_b: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "CodeGuard API",
        "endpoints": [
            "/api/quality",
            "/api/plagiarism",
            "/api/ai-detection",
            "/api/ast"
        ]
    }

@app.post("/api/quality")
def analyze_quality(submission: CodeSubmission):
    try:
        metrics = compute_quality_metrics(submission.code)
        return {"success": True, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plagiarism")
def analyze_plagiarism(submission: PlagiarismSubmission):
    try:
        report = detect_plagiarism(submission.code_a, submission.code_b)
        return {"success": True, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-detection")
def analyze_ai_generation(submission: CodeSubmission):
    try:
        result = check_ai_generated(submission.code)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ast")
def analyze_ast(submission: CodeSubmission):
    try:
        result = parse_code_to_ast(submission.code)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Syntax Error"))
        return {"success": True, "ast": result}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
