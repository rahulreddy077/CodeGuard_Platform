import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.connection import Base, engine, get_db
from backend.database import crud
from backend.database.models import User, Submission, AnalysisResult, SimilarityPair
from backend.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    RoleChecker
)
from backend.services.analysis import AnalysisService
from backend.extraction import extract_text_from_file, ExtractionError, read_bounded_file_bytes
from backend.config import PLAGIARISM_FLAG_THRESHOLD

# Import analysis modules
from modules.quality import compute_quality_metrics
from modules.plagiarism import detect_plagiarism
from modules.ai_detection import check_ai_generated, get_model_data
from modules.ast import parse_code_to_ast

# Startup database initialization and schema migration
def _ensure_sqlite_columns():
    """Safely adds missing columns to existing SQLite tables when model definitions evolve."""
    try:
        with engine.connect() as conn:
            # Check users table
            res = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
            cols = {row[1] for row in res}
            if cols and "registration_number" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN registration_number VARCHAR(50)")
                conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_registration_number ON users (registration_number)")
            
            # Check submissions table
            res_sub = conn.exec_driver_sql("PRAGMA table_info(submissions)").fetchall()
            sub_cols = {row[1] for row in res_sub}
            if sub_cols and "unassigned_reason" not in sub_cols:
                conn.exec_driver_sql("ALTER TABLE submissions ADD COLUMN unassigned_reason VARCHAR(200)")
            conn.commit()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Schema check error: {e}")

def _safe_username(user_obj, user_id=None):
    if user_obj and hasattr(user_obj, "username") and user_obj.username:
        return user_obj.username
    return f"Student #{user_id}" if user_id else "Unassigned"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create tables in SQLite
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()
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

class StudentAssignPayload(BaseModel):
    student_id: int

class AssignmentCreate(BaseModel):
    title: str
    course: Optional[str] = "CS101"
    due_date: Optional[datetime] = None

class CodeSubmissionPayload(BaseModel):
    assignment_id: int
    section_id: int
    file_name: str
    language: str
    raw_code: str

class CodePayload(BaseModel):
    code: str

class PlagiarismPayload(BaseModel):
    code_a: str
    code_b: str

# Standalone Analysis Endpoints
@app.post("/api/quality")
def api_quality(payload: CodePayload):
    res = compute_quality_metrics(payload.code)
    if res.get("success") == False:
        return {"success": False, "error": res.get("error")}
    return {"success": True, "metrics": res}

@app.post("/api/plagiarism")
def api_plagiarism(payload: PlagiarismPayload):
    res = detect_plagiarism(payload.code_a, payload.code_b)
    return {"success": True, "report": res}

@app.post("/api/ai-detection")
def api_ai_detection(payload: CodePayload):
    res = check_ai_generated(payload.code)
    if res.get("success") == False:
        return {"success": False, "error": res.get("error")}
    return {"success": True, "result": res}

@app.post("/api/ast")
def api_ast(payload: CodePayload):
    res = parse_code_to_ast(payload.code)
    if res.get("success") == False:
        return {"success": False, "error": res.get("error")}
    return {"success": True, "ast": res}

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
    
    # Run text extraction layer & syntax validation if needed
    try:
        raw_code = extract_text_from_file(payload.file_name, payload.raw_code.encode("utf-8"))
    except ExtractionError as ee:
        raise HTTPException(status_code=400, detail=str(ee))
    except Exception as e:
        raw_code = payload.raw_code

    submission = crud.create_submission(
        db=db,
        student_id=current_user.id,
        assignment_id=payload.assignment_id,
        section_id=payload.section_id,
        file_name=payload.file_name,
        language=payload.language,
        raw_code=raw_code
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

# 2b. Multi-Format File Upload (Protected - Student)
@app.post("/upload-file")
async def upload_file(
    assignment_id: int = Form(...),
    section_id: int = Form(1),
    file: UploadFile = File(...),
    current_user: User = Depends(RoleChecker(["Student"])),
    db: Session = Depends(get_db)
):
    assignment = crud.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
        
    try:
        file_bytes = await read_bounded_file_bytes(file)
        extracted_code = extract_text_from_file(file.filename, file_bytes)
    except ExtractionError as ee:
        raise HTTPException(status_code=400, detail=str(ee))

    submission = crud.create_submission(
        db=db,
        student_id=current_user.id,
        assignment_id=assignment_id,
        section_id=section_id,
        file_name=file.filename,
        language="Python",
        raw_code=extracted_code
    )

    try:
        AnalysisService.analyze_submission(db, submission)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")

    return {
        "success": True,
        "submission_id": submission.submission_id,
        "file_name": file.filename,
        "status": submission.status
    }

# 2c. Get List of Assignments (Protected - All Authenticated Roles)
@app.get("/assignments")
def get_all_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assignments = crud.get_assignments(db)
    return [
        {
            "assignment_id": a.assignment_id,
            "title": a.title,
            "course": a.course,
            "due_date": a.due_date
        } for a in assignments
    ]

@app.post("/assignments")
def create_new_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Assignment title cannot be empty")
    course = payload.course.strip() if payload.course else "CS101"
    due_date = payload.due_date or (datetime.utcnow() + timedelta(days=14))
    
    assignment = crud.create_assignment(db, course=course, title=title, due_date=due_date)
    return {
        "success": True,
        "assignment_id": assignment.assignment_id,
        "title": assignment.title,
        "course": assignment.course,
        "due_date": assignment.due_date
    }

# PROMPT 1: All-vs-All Plagiarism Report Endpoint (Protected - Professor/HOD/Admin)
@app.get("/assignments/{assignment_id}/plagiarism-report")
def get_plagiarism_report(
    assignment_id: int,
    threshold: float = PLAGIARISM_FLAG_THRESHOLD,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    assignment = crud.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submissions = crud.get_latest_submissions(db, assignment_id)

    sub_map = {s.submission_id: s for s in submissions}
    sub_ids = list(sub_map.keys())

    if not sub_ids:
        return {
            "assignment_id": assignment_id,
            "assignment_title": assignment.title,
            "total_submissions": 0,
            "total_pairs_analyzed": 0,
            "flagged_pairs_count": 0,
            "clusters_count": 0,
            "clusters": [],
            "all_pairs": [],
            "students": []
        }

    pairs = db.query(SimilarityPair).filter(
        SimilarityPair.submission1.in_(sub_ids),
        SimilarityPair.submission2.in_(sub_ids)
    ).all()

    formatted_pairs = []
    student_comparisons = {s_id: [] for s_id in sub_ids}

    for p in pairs:
        s1 = sub_map.get(p.submission1)
        s2 = sub_map.get(p.submission2)
        if not s1 or not s2:
            continue
        if s1.student_id == s2.student_id:
            # Same student self-comparison rejected
            continue
        if s1.assignment_id != assignment_id or s2.assignment_id != assignment_id or s1.assignment_id != s2.assignment_id:
            continue

        fusion = round(p.fusion or 0.0, 4)
        semantic = round(p.embedding or 0.0, 4)
        structural = round(p.jaccard or 0.0, 4)

        pair_data = {
            "submission1_id": s1.submission_id,
            "student1_id": s1.student_id,
            "student1_username": _safe_username(s1.student, s1.student_id),
            "submission2_id": s2.submission_id,
            "student2_id": s2.student_id,
            "student2_username": _safe_username(s2.student, s2.student_id),
            "semantic_score": semantic,
            "structural_score": structural,
            "fused_score": fusion
        }
        formatted_pairs.append(pair_data)

        # Student 1's list
        student_comparisons[s1.submission_id].append({
            "other_submission_id": s2.submission_id,
            "other_student_id": s2.student_id,
            "other_student_username": _safe_username(s2.student, s2.student_id),
            "other_file_name": s2.file_name,
            "semantic_score": semantic,
            "structural_score": structural,
            "fused_score": fusion
        })

        # Student 2's list
        student_comparisons[s2.submission_id].append({
            "other_submission_id": s1.submission_id,
            "other_student_id": s1.student_id,
            "other_student_username": _safe_username(s1.student, s1.student_id),
            "other_file_name": s1.file_name,
            "semantic_score": semantic,
            "structural_score": structural,
            "fused_score": fusion
        })

    formatted_pairs.sort(key=lambda x: x["fused_score"], reverse=True)
    flagged_pairs_count = sum(1 for p in formatted_pairs if p["fused_score"] >= threshold)

    students_output = []
    for s in submissions:
        comps = student_comparisons.get(s.submission_id, [])
        comps.sort(key=lambda x: x["fused_score"], reverse=True)
        top_match = comps[0] if comps else None

        students_output.append({
            "submission_id": s.submission_id,
            "student_id": s.student_id,
            "student_username": _safe_username(s.student, s.student_id),
            "file_name": s.file_name,
            "section": s.section.section_name if s.section else "N/A",
            "submitted_at": s.submitted_at,
            "top_match": top_match,
            "comparisons": comps
        })

    import networkx as nx
    G = nx.Graph()
    for s_id in sub_ids:
        G.add_node(s_id)

    for p in formatted_pairs:
        if p["fused_score"] >= threshold:
            G.add_edge(p["submission1_id"], p["submission2_id"], weight=p["fused_score"])

    raw_components = list(nx.connected_components(G))
    clusters_output = []
    
    for comp in raw_components:
        if len(comp) < 2:
            continue
        comp_sub_ids = list(comp)
        member_subs = [
            {
                "submission_id": sub_map[s_id].submission_id,
                "student_id": sub_map[s_id].student_id,
                "student_username": _safe_username(sub_map[s_id].student, sub_map[s_id].student_id),
                "file_name": sub_map[s_id].file_name,
                "section": sub_map[s_id].section.section_name if sub_map[s_id].section else "N/A"
            }
            for s_id in comp_sub_ids if s_id in sub_map
        ]
        
        internal_pairs = [
            p for p in formatted_pairs
            if p["submission1_id"] in comp and p["submission2_id"] in comp
        ]
        
        avg_score = round(sum(p["fused_score"] for p in internal_pairs) / len(internal_pairs), 4) if internal_pairs else 0.0
        max_score = round(max((p["fused_score"] for p in internal_pairs), default=0.0), 4)
        
        clusters_output.append({
            "cluster_id": 0,
            "submission_count": len(member_subs),
            "avg_fused_score": avg_score,
            "max_fused_score": max_score,
            "submissions": member_subs,
            "internal_pairs": internal_pairs
        })

    clusters_output.sort(key=lambda c: (c["submission_count"], c["avg_fused_score"]), reverse=True)
    for idx, clus in enumerate(clusters_output, 1):
        clus["cluster_id"] = idx

    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "total_submissions": len(submissions),
        "total_pairs_analyzed": len(formatted_pairs),
        "flagged_pairs_count": flagged_pairs_count,
        "clusters_count": len(clusters_output),
        "clusters": clusters_output,
        "all_pairs": formatted_pairs,
        "students": students_output
    }

# Endpoint: Assignment AI Detection Report (Protected - Professor/HOD/Admin)
@app.get("/assignments/{assignment_id}/ai-report")
def get_assignment_ai_report(
    assignment_id: int,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    assignment = crud.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submissions = crud.get_latest_submissions(db, assignment_id)
    
    sub_list = []
    high_ai_count = 0
    moderate_ai_count = 0
    low_ai_count = 0

    thresh = float(get_model_data().get("threshold", 0.54))

    for s in submissions:
        result = s.analysis_result
        ai_score = round(result.ai_score if (result and result.ai_score is not None) else 0.0, 4)

        if ai_score >= thresh:
            high_ai_count += 1
            risk_level = "Flagged for Faculty Review"
        elif ai_score >= 0.5 * thresh:
            moderate_ai_count += 1
            risk_level = "Optional Review"
        else:
            low_ai_count += 1
            risk_level = "Routine Code Structure"

        sub_list.append({
            "submission_id": s.submission_id,
            "student_id": s.student_id,
            "student_username": _safe_username(s.student, s.student_id),
            "assignment": assignment.title,
            "section": s.section.section_name if s.section else "A",
            "file_name": s.file_name,
            "status": s.status,
            "submitted_at": s.submitted_at,
            "ai_score": ai_score,
            "ai_percentage": f"{ai_score * 100:.1f}%",
            "risk_level": risk_level
        })

    sub_list.sort(key=lambda x: x["ai_score"], reverse=True)

    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "total_submissions": len(submissions),
        "threshold_used": thresh,
        "high_ai_count": high_ai_count,
        "moderate_ai_count": moderate_ai_count,
        "low_ai_count": low_ai_count,
        "submissions": sub_list
    }

# Faculty sections discovery endpoint
@app.get("/faculty/sections")
def get_faculty_sections(
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns sections that the current user is authorized to manage.
    Professors see only their own sections; HOD and Admin see all sections.
    """
    if current_user.role == "Professor":
        sections = current_user.sections
    else:
        sections = crud.get_sections(db)
    return [
        {"id": s.id, "section_name": s.section_name}
        for s in sections
    ]

# PROMPT 3: Bulk Upload Endpoint (Protected - Professor/HOD/Admin)
@app.post("/assignments/{assignment_id}/bulk-upload")
async def bulk_upload_submissions(
    assignment_id: int,
    section_id: int = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    assignment = crud.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Validate that the section exists
    from backend.database.models import Section
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=400, detail=f"Section ID {section_id} does not exist")

    # Professor section authorization
    if current_user.role == "Professor":
        assigned_section_ids = [sec.id for sec in current_user.sections]
        if section_id not in assigned_section_ids:
            raise HTTPException(status_code=403, detail="You do not teach this section")

    successful_submissions = []
    unassigned_submissions = []
    failed_files = []
    seen_filenames = set()
    ALLOWED_EXTENSIONS = {"py", "pdf", "docx", "doc", "png", "jpg", "jpeg", "bmp", "tiff", "webp"}

    from backend.identification import identify_student_from_filename
    eligible_students = db.query(User).filter(User.role == "Student", User.active == True).all()

    for file_obj in files:
        filename = file_obj.filename
        
        # Extension validation
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            failed_files.append({
                "filename": filename,
                "reason": f"Unsupported file extension '.{ext}'. Supported formats: .py, .pdf, .docx, .png, .jpg"
            })
            continue

        # Duplicate filename validation within upload batch
        if filename in seen_filenames:
            failed_files.append({
                "filename": filename,
                "reason": f"Duplicate filename '{filename}' in bulk upload batch."
            })
            continue
        seen_filenames.add(filename)

        # 1. Extraction step with 10MB size limit guard
        try:
            file_bytes = await read_bounded_file_bytes(file_obj)
            extracted_code = extract_text_from_file(filename, file_bytes)
        except Exception as e:
            failed_files.append({
                "filename": filename,
                "reason": str(e)
            })
            continue

        # 2. Intelligent Student ID identification step
        target_student, fail_reason = identify_student_from_filename(filename, db, eligible_students=eligible_students)
        is_ocr = ext in {"png", "jpg", "jpeg", "bmp", "tiff", "webp"}

        if target_student is not None:
            # 3a. Exactly one student identified: create submission & run analysis
            try:
                sub = crud.create_submission(
                    db=db,
                    student_id=target_student.id,
                    assignment_id=assignment_id,
                    section_id=section_id,
                    file_name=filename,
                    language="Python",
                    raw_code=extracted_code
                )
                AnalysisService.analyze_submission(db, sub)
                successful_submissions.append({
                    "submission_id": sub.submission_id,
                    "file_name": filename,
                    "student": target_student.username,
                    "student_username": target_student.username,
                    "registration_number": target_student.registration_number,
                    "status": sub.status,
                    "is_ocr": is_ocr,
                    "identified": True
                })
            except Exception as e:
                failed_files.append({
                    "filename": filename,
                    "reason": f"Analysis failed: {str(e)}"
                })
        else:
            # 3b. Unrecognized or ambiguous: retain safely with 'Awaiting Student Identification'
            try:
                sub = crud.create_submission(
                    db=db,
                    student_id=None,
                    assignment_id=assignment_id,
                    section_id=section_id,
                    file_name=filename,
                    language="Python",
                    raw_code=extracted_code
                )
                sub.status = "Awaiting Student Identification"
                sub.unassigned_reason = fail_reason
                db.commit()
                unassigned_submissions.append({
                    "submission_id": sub.submission_id,
                    "file_name": filename,
                    "status": sub.status,
                    "unassigned_reason": fail_reason,
                    "is_ocr": is_ocr,
                    "identified": False
                })
            except Exception as e:
                failed_files.append({
                    "filename": filename,
                    "reason": f"Failed to save unassigned submission: {str(e)}"
                })

    return {
        "success": True,
        "assignment_id": assignment_id,
        "total_files": len(files),
        "processed_count": len(successful_submissions) + len(unassigned_submissions),
        "identified_count": len(successful_submissions),
        "unassigned_count": len(unassigned_submissions),
        "failed_count": len(failed_files),
        "successful_submissions": successful_submissions,
        "unassigned_submissions": unassigned_submissions,
        "failed_files": failed_files
    }

@app.get("/faculty/unassigned-count")
def get_faculty_unassigned_count(
    assignment_id: Optional[int] = None,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    """Returns the count of submissions awaiting student identification within user's authorized scope."""
    from sqlalchemy import func
    query = db.query(func.count(Submission.submission_id)).filter(
        Submission.student_id.is_(None),
        Submission.status == "Awaiting Student Identification"
    )
    if current_user.role == "Professor":
        sec_ids = [s.id for s in current_user.sections]
        query = query.filter(Submission.section_id.in_(sec_ids))
    if assignment_id:
        query = query.filter(Submission.assignment_id == assignment_id)
    return {"count": query.scalar() or 0}

# Unassigned Submissions & Manual Identification Endpoints
@app.get("/faculty/unassigned-submissions")
def get_faculty_unassigned_submissions(
    assignment_id: Optional[int] = None,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    if current_user.role == "Professor":
        sec_ids = [s.id for s in current_user.sections]
        submissions = crud.get_unassigned_submissions(db, assignment_id=assignment_id, section_ids=sec_ids)
    else:
        submissions = crud.get_unassigned_submissions(db, assignment_id=assignment_id)

    return [
        {
            "submission_id": s.submission_id,
            "file_name": s.file_name,
            "assignment_id": s.assignment_id,
            "assignment_title": s.assignment.title if s.assignment else "Unknown Assignment",
            "section_id": s.section_id,
            "section_name": s.section.section_name if s.section else "N/A",
            "status": s.status,
            "unassigned_reason": s.unassigned_reason or "Awaiting student identification",
            "submitted_at": s.submitted_at,
            "raw_code": s.raw_code
        }
        for s in submissions
    ]

@app.get("/faculty/eligible-students")
def get_eligible_students(
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    students = crud.get_student_users(db)
    return [
        {
            "id": s.id,
            "username": s.username,
            "email": s.email,
            "registration_number": s.registration_number
        }
        for s in students
    ]

@app.post("/submissions/{submission_id}/assign-student")
def manual_assign_student(
    submission_id: int,
    payload: StudentAssignPayload,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    submission = crud.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Professor section authorization
    if current_user.role == "Professor":
        assigned_section_ids = [s.id for s in current_user.sections]
        if submission.section_id not in assigned_section_ids:
            raise HTTPException(status_code=403, detail="You do not teach this section")

    # 1. Validate selected student
    student = crud.get_user_by_id(db, payload.student_id)
    if not student or student.role != "Student":
        raise HTTPException(status_code=400, detail="Invalid student selection: Selected student does not exist or is not a registered student.")

    # 2. Verify student eligibility for the assignment
    if not student.active:
        raise HTTPException(status_code=400, detail="Student not eligible for the assignment: Student account is inactive or restricted.")

    # Duplicate submission prevention
    dup = db.query(Submission).filter(
        Submission.assignment_id == submission.assignment_id,
        Submission.student_id == student.id,
        Submission.file_name == submission.file_name,
        Submission.submission_id != submission.submission_id
    ).first()
    if dup:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate submission rejected: Student '{student.username}' already has a submission with file name '{submission.file_name}' for this assignment."
        )

    # Associate student and move into existing submission workflow
    submission.student_id = student.id
    submission.unassigned_reason = None
    submission.status = "Analyzing"
    db.commit()

    try:
        AnalysisService.analyze_submission(db, submission)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed after manual mapping: {str(e)}")

    return {
        "success": True,
        "message": f"Successfully mapped '{submission.file_name}' to student '{student.username}' ({student.registration_number or 'No Reg No'}). Analysis completed.",
        "submission_id": submission.submission_id,
        "student_id": student.id,
        "student": student.username,
        "student_username": student.username,
        "status": submission.status
    }

@app.get("/assignments/{assignment_id}/bulk-approve-preview")
def bulk_approve_preview(
    assignment_id: int,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    assignment = crud.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submissions = crud.get_latest_submissions(db, assignment_id)
    latest_ids = {s.submission_id for s in submissions}

    prof_sec_ids = {sec.id for sec in current_user.sections} if current_user.role == "Professor" else None

    ai_threshold = float(get_model_data().get("threshold", 0.54))
    plag_threshold = PLAGIARISM_FLAG_THRESHOLD

    eligible_count = 0
    flagged_count = 0
    incomplete_count = 0
    out_of_scope_count = 0

    for s in submissions:
        if prof_sec_ids is not None and s.section_id not in prof_sec_ids:
            out_of_scope_count += 1
            continue

        if s.status == "Failed":
            incomplete_count += 1
            continue

        result = s.analysis_result
        if not result or result.ai_score is None or not result.quality_score:
            incomplete_count += 1
            continue

        if result.ai_score >= ai_threshold:
            flagged_count += 1
            continue

        pairs = db.query(SimilarityPair).filter(
            (SimilarityPair.submission1 == s.submission_id) |
            (SimilarityPair.submission2 == s.submission_id)
        ).all()
        max_sim = max(
            (p.fusion or 0.0 for p in pairs if (p.submission1 in latest_ids and p.submission2 in latest_ids)),
            default=0.0
        )
        if max_sim >= plag_threshold:
            flagged_count += 1
            continue

        eligible_count += 1

    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "total_submissions": len(submissions),
        "eligible_count": eligible_count,
        "flagged_count": flagged_count,
        "incomplete_count": incomplete_count,
        "out_of_scope_count": out_of_scope_count
    }

@app.post("/assignments/{assignment_id}/bulk-approve")
def bulk_approve_assignment_submissions(
    assignment_id: int,
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    assignment = crud.get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submissions = crud.get_latest_submissions(db, assignment_id)
    latest_ids = {s.submission_id for s in submissions}

    prof_sec_ids = {sec.id for sec in current_user.sections} if current_user.role == "Professor" else None

    ai_threshold = float(get_model_data().get("threshold", 0.54))
    plag_threshold = PLAGIARISM_FLAG_THRESHOLD

    approved_count = 0
    held_flagged_count = 0
    held_incomplete_count = 0
    out_of_scope_count = 0

    for s in submissions:
        if prof_sec_ids is not None and s.section_id not in prof_sec_ids:
            out_of_scope_count += 1
            continue

        if s.status == "Failed":
            held_incomplete_count += 1
            continue

        result = s.analysis_result
        if not result or result.ai_score is None or not result.quality_score:
            held_incomplete_count += 1
            continue

        if result.ai_score >= ai_threshold:
            held_flagged_count += 1
            continue

        pairs = db.query(SimilarityPair).filter(
            (SimilarityPair.submission1 == s.submission_id) |
            (SimilarityPair.submission2 == s.submission_id)
        ).all()
        max_sim = max(
            (p.fusion or 0.0 for p in pairs if (p.submission1 in latest_ids and p.submission2 in latest_ids)),
            default=0.0
        )
        if max_sim >= plag_threshold:
            held_flagged_count += 1
            continue

        crud.approve_report(db, submission_id=s.submission_id, approved_by_id=current_user.id, approve=True)
        crud.release_report(db, submission_id=s.submission_id, approved_by_id=current_user.id, release=True)
        approved_count += 1

    return {
        "success": True,
        "message": f"Bulk approval complete for '{assignment.title}': {approved_count} clean submissions approved & released, {held_flagged_count} flagged submissions held for manual review, {held_incomplete_count} incomplete/failed submissions excluded.",
        "assignment_id": assignment_id,
        "approved_count": approved_count,
        "held_flagged_count": held_flagged_count,
        "held_incomplete_count": held_incomplete_count,
        "out_of_scope_count": out_of_scope_count
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
            "assignment": s.assignment.title if s.assignment else "Unknown Assignment",
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

    # Ensure submission has an analysis result for faculty audit
    result = submission.analysis_result
    if not result:
        try:
            from backend.services.analysis import AnalysisService
            AnalysisService.analyze_submission(db, submission)
            db.refresh(submission)
            result = submission.analysis_result
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"On-demand analysis error for sub #{id}: {e}")

    # Query ALL comparisons for this submission within the same assignment
    latest_subs = crud.get_latest_submissions(db, submission.assignment_id)
    latest_ids = {s.submission_id for s in latest_subs}

    pairs = db.query(SimilarityPair).filter(
        (SimilarityPair.submission1 == submission.submission_id) |
        (SimilarityPair.submission2 == submission.submission_id)
    ).all()

    # If no pairs exist yet but other student submissions exist in this assignment, compute on-the-fly!
    other_student_subs = [s for s in latest_subs if s.student_id != submission.student_id and s.assignment_id == submission.assignment_id]
    if not pairs and other_student_subs:
        for other_sub in other_student_subs:
            try:
                from backend.services.similarity import SimilarityService
                p = SimilarityService.compare_submissions(db, submission, other_sub)
                if p:
                    pairs.append(p)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"On-demand comparison error: {e}")
        pairs = db.query(SimilarityPair).filter(
            (SimilarityPair.submission1 == submission.submission_id) |
            (SimilarityPair.submission2 == submission.submission_id)
        ).all()

    comparisons = []
    for p in pairs:
        other_id = p.submission2 if p.submission1 == submission.submission_id else p.submission1
        other_sub = crud.get_submission_by_id(db, other_id)
        if not other_sub or other_sub.student_id == submission.student_id or other_sub.assignment_id != submission.assignment_id:
            continue

        fusion = round(p.fusion or 0.0, 4)
        semantic = round(p.embedding or 0.0, 4)
        structural = round(p.jaccard or 0.0, 4)
        u_name = _safe_username(other_sub.student, other_sub.student_id)

        comparisons.append({
            "other_submission_id": other_sub.submission_id,
            "target_sub_id": other_sub.submission_id,
            "other_student_username": u_name,
            "student_username": u_name,
            "other_file_name": other_sub.file_name,
            "file_name": other_sub.file_name,
            "fused_score": fusion,
            "semantic_score": semantic,
            "structural_score": structural,
            "flagged": fusion >= PLAGIARISM_FLAG_THRESHOLD
        })

    comparisons.sort(key=lambda c: c["fused_score"], reverse=True)
    max_fused = max((c["fused_score"] for c in comparisons), default=0.0)
    top_match = comparisons[0] if comparisons else None

    # Construct complete report
    fallback_quality = {
        "lines_of_code": len(submission.raw_code.splitlines()) if submission.raw_code else 0,
        "complexity_level": "Low",
        "cyclomatic_complexity": 1,
        "maintainability_index": 100.0,
        "security_score": 100,
        "vulnerabilities": []
    }
    ai_check = check_ai_generated(submission.raw_code) if submission.raw_code else {}
    ai_heuristics = ai_check.get("heuristics", {})

    report_dict = {
        "plagiarism": {
            "similarity_score": max_fused,
            "max_similarity_score": max_fused,
            "total_comparisons": len(comparisons),
            "comparisons": comparisons,
            "top_match": top_match,
            "flagged": max_fused >= PLAGIARISM_FLAG_THRESHOLD
        },
        "ai_score": (result.ai_score if (result and result.ai_score is not None) else ai_check.get("ai_probability", 0.0)),
        "ai_heuristics": ai_heuristics,
        "heuristics": ai_heuristics,
        "threshold_used": float(get_model_data().get("threshold", 0.54)),
        "quality": json.loads(result.quality_score) if (result and result.quality_score) else fallback_quality,
        "report_visible": result.report_visible if result else False,
        "approved_by": result.approver.username if (result and result.approver) else None,
        "approved_at": result.approved_at if (result and result.approved_at) else None
    } if (result or current_user.role != "Student") else None

    return {
        "metadata": {
            "submission_id": submission.submission_id,
            "student_username": _safe_username(submission.student, submission.student_id),
            "assignment": submission.assignment.title if submission.assignment else "Unknown Assignment",
            "assignment_id": submission.assignment_id,
            "section": submission.section.section_name if submission.section else "A",
            "file_name": submission.file_name,
            "language": submission.language,
            "status": submission.status,
            "submitted_at": submission.submitted_at
        },
        "raw_code": submission.raw_code,
        "comparisons": comparisons,
        "top_match": top_match,
        "report": report_dict
    }

# 5. Approve Report (Protected - Professor/HOD/Admin)
@app.post("/approve-report/{id}")
def approve_submission_report(
    id: int,
    approve: bool = Query(True),
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    submission = crud.get_submission_by_id(db, id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.status == "Awaiting Student Identification" or submission.student_id is None:
        raise HTTPException(status_code=400, detail="Cannot approve or release a submission awaiting student identification")

    if current_user.role == "Professor":
        assigned_section_ids = [sec.id for sec in current_user.sections]
        if submission.section_id not in assigned_section_ids:
            raise HTTPException(status_code=403, detail="You do not teach this section")

    crud.approve_report(db, submission_id=id, approved_by_id=current_user.id, approve=approve)
    msg = "Report approved" if approve else "Report approval removed"
    return {"success": True, "message": msg}

@app.post("/release-report/{id}")
def release_submission_report(
    id: int,
    release: bool = Query(True),
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    submission = crud.get_submission_by_id(db, id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if submission.status == "Awaiting Student Identification" or submission.student_id is None:
        raise HTTPException(status_code=400, detail="Cannot approve or release a submission awaiting student identification")

    if current_user.role == "Professor":
        assigned_section_ids = [sec.id for sec in current_user.sections]
        if submission.section_id not in assigned_section_ids:
            raise HTTPException(status_code=403, detail="You do not teach this section")

    crud.release_report(db, submission_id=id, approved_by_id=current_user.id, release=release)
    msg = "Report released to student" if release else "Report release revoked"
    return {"success": True, "message": msg}

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
        unassigned_subs = crud.get_unassigned_submissions(db, section_ids=sec_ids)
        return {
            "role": "Professor",
            "sections": [s.section_name for s in current_user.sections],
            "total_submissions": len(submissions),
            "pending_reviews": sum(1 for s in submissions if s.status == "Faculty Review"),
            "unassigned_count": len(unassigned_subs)
        }
        
    else:  # HOD or Admin
        submissions = crud.get_all_submissions(db)
        sections = crud.get_sections(db)
        unassigned_subs = crud.get_unassigned_submissions(db)
        return {
            "role": current_user.role,
            "total_submissions": len(submissions),
            "total_sections": len(sections),
            "global_pending_reviews": sum(1 for s in submissions if s.status == "Faculty Review"),
            "unassigned_count": len(unassigned_subs)
        }

# 7. Faculty Submissions List (Protected - Professor/HOD/Admin)
@app.get("/faculty/submissions")
def get_faculty_submissions(
    assignment_id: Optional[int] = Query(None),
    section_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("date"),
    sort_order: Optional[str] = Query("desc"),
    page: Optional[int] = Query(None),
    page_size: Optional[int] = Query(20),
    current_user: User = Depends(RoleChecker(["Professor", "HOD", "Admin"])),
    db: Session = Depends(get_db)
):
    import math
    from sqlalchemy import select, func, desc, asc, case, or_
    from sqlalchemy.orm import joinedload
    from backend.database.models import Section

    # 1. Section authorization and resolution
    if current_user.role == "Professor":
        assigned_sec_ids = [s.id for s in current_user.sections]
        if section_id is not None:
            if section_id not in assigned_sec_ids:
                raise HTTPException(status_code=403, detail="You do not teach this section")
            target_sec_ids = [section_id]
        else:
            target_sec_ids = assigned_sec_ids
    else:  # HOD or Admin
        if section_id is not None:
            sec = db.query(Section).filter(Section.id == section_id).first()
            if not sec:
                raise HTTPException(status_code=400, detail=f"Section ID {section_id} does not exist")
            target_sec_ids = [section_id]
        else:
            target_sec_ids = None

    # 2. Assignment validation
    if assignment_id is not None:
        asgn = crud.get_assignment_by_id(db, assignment_id)
        if not asgn:
            raise HTTPException(status_code=404, detail="Assignment not found")

    # 3. Base similarity scalar subquery
    sim_subq = (
        select(func.max(SimilarityPair.fusion))
        .where(
            (SimilarityPair.submission1 == Submission.submission_id)
            | (SimilarityPair.submission2 == Submission.submission_id)
        )
        .scalar_subquery()
    )

    # 4. Base query: strictly exclude unassigned / pending files
    base_query = db.query(Submission, sim_subq.label("max_sim")).outerjoin(AnalysisResult).join(
        User, Submission.student_id == User.id
    ).filter(
        Submission.student_id.isnot(None),
        Submission.status != "Awaiting Student Identification"
    )

    if target_sec_ids is not None:
        base_query = base_query.filter(Submission.section_id.in_(target_sec_ids))
    if assignment_id is not None:
        base_query = base_query.filter(Submission.assignment_id == assignment_id)

    # 5. Compute scope metrics before status/search filters
    metrics_query = db.query(
        func.count(Submission.submission_id).label("total_in_scope"),
        func.count(case((Submission.status == "Faculty Review", 1))).label("awaiting_review"),
        func.count(case((
            (AnalysisResult.ai_score >= 0.54) | (sim_subq >= PLAGIARISM_FLAG_THRESHOLD), 1
        ))).label("flagged"),
        func.count(case((
            (Submission.status.in_(["Approved", "Released", "Visible to Student"]))
            | (AnalysisResult.report_visible == True), 1
        ))).label("approved_released")
    ).select_from(Submission).outerjoin(AnalysisResult).filter(
        Submission.student_id.isnot(None),
        Submission.status != "Awaiting Student Identification"
    )
    if target_sec_ids is not None:
        metrics_query = metrics_query.filter(Submission.section_id.in_(target_sec_ids))
    if assignment_id is not None:
        metrics_query = metrics_query.filter(Submission.assignment_id == assignment_id)

    metrics_res = metrics_query.first()
    metrics_dict = dict(metrics_res._mapping) if metrics_res else {
        "total_in_scope": 0, "awaiting_review": 0, "flagged": 0, "approved_released": 0
    }

    # 6. Apply status filter
    filtered_query = base_query
    if status and status.strip().lower() not in ["", "all", "all statuses", "all applicable statuses"]:
        st_clean = status.strip()
        if st_clean == "Faculty Review":
            filtered_query = filtered_query.filter(Submission.status == "Faculty Review")
        elif st_clean == "Approved":
            filtered_query = filtered_query.filter(Submission.status.in_(["Approved", "Completed"]))
        elif st_clean in ["Released", "Visible to Student"]:
            filtered_query = filtered_query.filter(
                (Submission.status.in_(["Released", "Visible to Student"]))
                | (AnalysisResult.report_visible == True)
            )
        elif st_clean in ["Flagged", "Flagged for Review", "flagged"]:
            filtered_query = filtered_query.filter(
                (AnalysisResult.ai_score >= 0.54) | (sim_subq >= PLAGIARISM_FLAG_THRESHOLD)
            )
        else:
            filtered_query = filtered_query.filter(Submission.status == st_clean)

    # 7. Apply search filter
    if search and search.strip():
        term = f"%{search.strip()}%"
        search_filter = or_(
            User.username.ilike(term),
            User.registration_number.ilike(term),
            Submission.file_name.ilike(term)
        )
        if search.strip().isdigit():
            search_filter = or_(search_filter, Submission.submission_id == int(search.strip()))
        filtered_query = filtered_query.filter(search_filter)

    # 8. Apply sorting
    is_asc = (sort_order or "desc").lower() == "asc"
    if sort_by in ["ai_score", "ai"]:
        sort_expr = func.coalesce(AnalysisResult.ai_score, -1.0 if not is_asc else 999.0)
        filtered_query = filtered_query.order_by(sort_expr.asc() if is_asc else sort_expr.desc(), Submission.submission_id.desc())
    elif sort_by in ["similarity", "plagiarism"]:
        sort_expr = func.coalesce(sim_subq, -1.0 if not is_asc else 999.0)
        filtered_query = filtered_query.order_by(sort_expr.asc() if is_asc else sort_expr.desc(), Submission.submission_id.desc())
    else:  # "date" or default
        sort_expr = Submission.submitted_at
        filtered_query = filtered_query.order_by(sort_expr.asc() if is_asc else sort_expr.desc(), Submission.submission_id.desc())

    # Add eager loads for fast serialization
    filtered_query = filtered_query.options(
        joinedload(Submission.student),
        joinedload(Submission.assignment),
        joinedload(Submission.section),
        joinedload(Submission.analysis_result)
    )

    # 9. Format item helper
    def _format_row(s, max_sim):
        ai = round(s.analysis_result.ai_score, 4) if (s.analysis_result and s.analysis_result.ai_score is not None) else None
        sim = round(max_sim, 4) if max_sim is not None else 0.0
        is_app = bool((s.status in ["Approved", "Released", "Visible to Student"]) or (s.analysis_result and s.analysis_result.approved_by is not None))
        rep_vis = bool(s.analysis_result.report_visible if s.analysis_result else False)
        return {
            "submission_id": s.submission_id,
            "student_id": s.student_id,
            "student_username": s.student.username if s.student else "Unknown",
            "student_name": s.student.username if s.student else "Unknown",
            "registration_number": s.student.registration_number if s.student else None,
            "assignment_id": s.assignment_id,
            "assignment": s.assignment.title if s.assignment else "Unknown Assignment",
            "section_id": s.section_id,
            "section": s.section.section_name if s.section else "N/A",
            "file_name": s.file_name,
            "status": s.status,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "is_approved": is_app,
            "report_visible": rep_vis,
            "ai_score": ai,
            "similarity_score": sim,
            "is_flagged": bool((ai is not None and ai >= 0.54) or (sim >= PLAGIARISM_FLAG_THRESHOLD))
        }

    # 10. Backward-compatible return if page is None
    if page is None:
        rows = filtered_query.all()
        return [_format_row(s, sim) for s, sim in rows]

    # 11. Paginated return
    if page < 1:
        page = 1
    if page_size not in [20, 50, 100]:
        page_size = 20

    total_count = filtered_query.count()
    total_pages = max(1, math.ceil(total_count / page_size)) if total_count > 0 else 1
    offset = (page - 1) * page_size
    page_rows = filtered_query.offset(offset).limit(page_size).all()

    return {
        "items": [_format_row(s, sim) for s, sim in page_rows],
        "submissions": [_format_row(s, sim) for s, sim in page_rows],
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "metrics": metrics_dict
    }

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
