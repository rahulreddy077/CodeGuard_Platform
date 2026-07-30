import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.connection import Base, engine, get_db
from backend.database import crud
from backend.database.models import User, Submission, AnalysisResult
from backend.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    RoleChecker
)
from backend.services.analysis import AnalysisService

# Import analysis modules
from modules.quality import compute_quality_metrics
from modules.plagiarism import detect_plagiarism
from modules.ai_detection import check_ai_generated
from modules.ast import parse_code_to_ast

# Startup database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create tables in SQLite
    Base.metadata.create_all(bind=engine)
    # Seed mock data (users, sections, assignment)
    db = next(get_db())
    try:
        crud.seed_data(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="CodeGuard API",
    description="Backend API for CodeGuard - Code Quality, Plagiarism, AST, and AI Generation analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str  # Admin, HOD, Professor, Student

class AssignSection(BaseModel):
    faculty_id: int
    section_id: int

class CodeSubmissionPayload(BaseModel):
    assignment_id: int
    section_id: int
    file_name: str
    language: str
    raw_code: str

# Existing simple endpoints
@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "CodeGuard API",
        "endpoints": [
            "/login",
            "/upload",
            "/my-submissions",
            "/submission/{id}",
            "/approve-report/{id}",
            "/dashboard",
            "/faculty/submissions",
            "/hod/analytics"
        ]
    }

# 1. Login Endpoint
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username
    }

# 2. Upload Endpoint (Protected - Student)
@app.post("/upload")
def upload_code(
    payload: CodeSubmissionPayload,
    current_user: User = Depends(RoleChecker(["Student"])),
    db: Session = Depends(get_db)
):
    assignment = crud.get_assignment_by_id(db, payload.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Create submission (State: Uploaded)
    submission = crud.create_submission(
        db=db,
        student_id=current_user.id,
        assignment_id=payload.assignment_id,
        section_id=payload.section_id,
        file_name=payload.file_name,
        language=payload.language,
        raw_code=payload.raw_code
    )

    try:
        AnalysisService.analyze_submission(db, submission)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")

    return {
        "success": True,
        "submission_id": submission.submission_id,
        "status": submission.status
    }

# 3. View Own Submissions (Protected - Student)
@app.get("/my-submissions")
def get_my_submissions(
    current_user: User = Depends(RoleChecker(["Student"])),
    db: Session = Depends(get_db)
):
    submissions = crud.get_submissions_by_student(db, current_user.id)
    return [
        {
            "submission_id": s.submission_id,
            "assignment": s.assignment.title,
            "file_name": s.file_name,
            "language": s.language,
            "status": s.status,
            "submitted_at": s.submitted_at
        } for s in submissions
    ]

# 4. View Submission Details (Protected - All Roles with RBAC filter)
@app.get("/submission/{id}")
def get_submission_details(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    submission = crud.get_submission_by_id(db, id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    # RBAC logic
    if current_user.role == "Student":
        if submission.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied to this submission")
        
        # Check if report is approved (report_visible = True)
        result = submission.analysis_result
        if not result or not result.report_visible:
            return {
                "metadata": {
                    "submission_id": submission.submission_id,
                    "file_name": submission.file_name,
                    "language": submission.language,
                    "status": submission.status,
                    "submitted_at": submission.submitted_at
                },
                "report": None,
                "message": "Report is pending review by faculty."
            }
            
    elif current_user.role == "Professor":
        # Check if section is assigned to professor
        assigned_section_ids = [sec.id for sec in current_user.sections]
        if submission.section_id not in assigned_section_ids:
            raise HTTPException(status_code=403, detail="Access denied to this section's submissions")

    # If authorized (or HOD/Admin), return complete details
    result = submission.analysis_result
    return {
        "metadata": {
            "submission_id": submission.submission_id,
            "student_username": submission.student.username,
            "assignment": submission.assignment.title,
            "section": submission.section.section_name,
            "file_name": submission.file_name,
            "language": submission.language,
            "status": submission.status,
            "submitted_at": submission.submitted_at
        },
        "raw_code": submission.raw_code,
        "report": {
            "plagiarism": json.loads(result.plagiarism) if result and result.plagiarism else None,
            "ai_score": result.ai_score if result else None,
            "quality": json.loads(result.quality_score) if result and result.quality_score else None,
            "report_visible": result.report_visible if result else False,
            "approved_by": result.approver.username if result and result.approver else None,
            "approved_at": result.approved_at if result else None
        } if result else None
    }

# 5. Approve Report (Protected - Professor/HOD/Admin)
@app.post("/approve-report/{id}")
def approve_submission_report(
    id: int,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    submission = crud.get_submission_by_id(db, id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if current_user.role == "Professor":
        assigned_section_ids = [sec.id for sec in current_user.sections]
        if submission.section_id not in assigned_section_ids:
            raise HTTPException(status_code=403, detail="You do not teach this section")

    crud.approve_report(db, submission_id=id, approved_by_id=current_user.id)
    return {"success": True, "message": "Report approved and made visible to the student"}

# 6. Dashboard Metrics (Protected - All)
@app.get("/dashboard")
def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "Student":
        submissions = crud.get_submissions_by_student(db, current_user.id)
        return {
            "role": "Student",
            "total_submissions": len(submissions),
            "status_counts": {
                "Uploaded": sum(1 for s in submissions if s.status == "Uploaded"),
                "Analyzing": sum(1 for s in submissions if s.status == "Analyzing"),
                "Faculty Review": sum(1 for s in submissions if s.status == "Faculty Review"),
                "Approved": sum(1 for s in submissions if s.status == "Approved")
            }
        }
        
    elif current_user.role == "Professor":
        sec_ids = [s.id for s in current_user.sections]
        submissions = crud.get_submissions_for_sections(db, sec_ids)
        return {
            "role": "Professor",
            "sections": [s.section_name for s in current_user.sections],
            "total_submissions": len(submissions),
            "pending_reviews": sum(1 for s in submissions if s.status == "Faculty Review")
        }
        
    else:  # HOD or Admin
        submissions = crud.get_all_submissions(db)
        sections = crud.get_sections(db)
        return {
            "role": current_user.role,
            "total_submissions": len(submissions),
            "total_sections": len(sections),
            "global_pending_reviews": sum(1 for s in submissions if s.status == "Faculty Review")
        }

# 7. Faculty Submissions List (Protected - Professor/HOD/Admin)
@app.get("/faculty/submissions")
def get_faculty_submissions(
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    if current_user.role == "Professor":
        sec_ids = [s.id for s in current_user.sections]
        submissions = crud.get_submissions_for_sections(db, sec_ids)
    else:
        submissions = crud.get_all_submissions(db)

    return [
        {
            "submission_id": s.submission_id,
            "student_username": s.student.username,
            "assignment": s.assignment.title,
            "section": s.section.section_name,
            "file_name": s.file_name,
            "status": s.status,
            "submitted_at": s.submitted_at
        } for s in submissions
    ]

# 8. HOD Analytics (Protected - HOD/Admin)
@app.get("/hod/analytics")
def get_hod_analytics(
    current_user: User = Depends(RoleChecker(["HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    submissions = crud.get_all_submissions(db)
    sections = crud.get_sections(db)
    
    section_stats = {}
    for sec in sections:
        sec_subs = [s for s in submissions if s.section_id == sec.id]
        section_stats[sec.section_name] = {
            "total_submissions": len(sec_subs),
            "average_ai_score": sum(
                s.analysis_result.ai_score for s in sec_subs if s.analysis_result and s.analysis_result.ai_score
            ) / len(sec_subs) if sec_subs else 0.0
        }

    return {
        "generated_at": datetime.utcnow(),
        "total_system_submissions": len(submissions),
        "section_breakdown": section_stats
    }

# Admin Management endpoints
@app.post("/admin/users")
def register_user(
    payload: UserCreate,
    current_user: User = Depends(RoleChecker(["Admin"])),
    db: Session = Depends(get_db)
):
    existing = crud.get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = crud.create_user(
        db=db,
        username=payload.username,
        email=payload.email,
        password_raw=payload.password,
        role=payload.role
    )
    return {"success": True, "user_id": user.id}

@app.post("/admin/assign-section")
def assign_faculty_section(
    payload: AssignSection,
    current_user: User = Depends(RoleChecker(["Admin"])),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, payload.faculty_id)
    if not user or user.role != "Professor":
        raise HTTPException(status_code=400, detail="Invalid faculty ID")
        
    crud.assign_section_to_faculty(db, payload.faculty_id, payload.section_id)
    return {"success": True}
