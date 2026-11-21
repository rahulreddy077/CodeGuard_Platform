import io
import pytest
from datetime import datetime
from backend.database.connection import SessionLocal, Base, engine
from backend.database.models import User, Section, Assignment, Submission, AnalysisResult, SimilarityPair
import backend.database.crud as crud
from backend.services.similarity import SimilarityService
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    crud.seed_data(db)
    yield db
    db.close()

def test_bulk_upload_validation_and_ocr_tagging(db_session):
    client = TestClient(app)
    
    # 1. Login as Professor
    login_res = client.post("/login", data={"username": "professor", "password": "prof123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get assignment
    asgns = client.get("/assignments", headers=headers).json()
    assert len(asgns) > 0
    asgn_id = asgns[0]["assignment_id"]
    
    # 3. Test bulk upload with valid .py file, duplicate file, and invalid extension
    files = [
        ("files", ("student_sol.py", b"def add(a, b):\n    return a + b\n", "text/plain")),
        ("files", ("student_sol.py", b"def add(a, b):\n    return a + b\n", "text/plain")),  # Duplicate in batch
        ("files", ("invalid_exec.exe", b"binary content", "application/octet-stream"))         # Unsupported extension
    ]
    
    res = client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    assert data["total_files"] == 3
    assert data["processed_count"] == 1
    assert data["failed_count"] == 2
    
    failed_reasons = [f["reason"] for f in data["failed_files"]]
    assert any("Unsupported file extension" in r for r in failed_reasons)
    assert any("Duplicate filename" in r for r in failed_reasons)

def test_oversized_file_rejection_no_db_record(db_session):
    client = TestClient(app)
    login_res = client.post("/login", data={"username": "professor", "password": "prof123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    asgns = client.get("/assignments", headers=headers).json()
    asgn_id = asgns[0]["assignment_id"]
    
    # Create 11 MB dummy file
    oversized_bytes = b"def big():\n    pass\n" + (b"#" * (11 * 1024 * 1024))
    
    initial_sub_count = len(crud.get_all_submissions(db_session))
    
    files = [
        ("files", ("oversized_code.py", oversized_bytes, "text/plain"))
    ]
    
    res = client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    assert data["failed_count"] == 1
    assert "exceeds maximum allowable size limit" in data["failed_files"][0]["reason"]
    
    # Confirm no DB record was created
    final_sub_count = len(crud.get_all_submissions(db_session))
    assert final_sub_count == initial_sub_count

def test_safe_bulk_approval_and_section_scope(db_session):
    client = TestClient(app)
    
    # Seed custom assignment safely with ID 9999 to avoid collision with 8888
    asgn = db_session.query(Assignment).filter(Assignment.assignment_id == 9999).first()
    if not asgn:
        asgn = Assignment(assignment_id=9999, course="CS101", title="Bulk Approve Scope Test 9999", due_date=datetime.utcnow())
        db_session.add(asgn)
    
    # Create Section A (Assigned to Prof) and Section C (NOT assigned to Prof)
    sec_a = crud.get_section_by_name(db_session, "A")
    sec_c = crud.get_section_by_name(db_session, "C")
    
    prof = crud.get_user_by_username(db_session, "professor")
    student_a = crud.get_user_by_username(db_session, "student")
    
    # Create Student C
    student_c = crud.get_user_by_username(db_session, "student_c_test")
    if not student_c:
        student_c = crud.create_user(db_session, username="student_c_test", email="c@test.com", password_raw="pwd", role="Student")
        
    db_session.commit()
    
    # Clean old test submissions for 9999 if any
    db_session.query(Submission).filter(Submission.assignment_id == 9999).delete()
    db_session.commit()
    
    # 1. Clean submission in Section A (Prof manages Section A)
    sub_clean = Submission(
        student_id=student_a.id, assignment_id=9999, section_id=sec_a.id,
        file_name="clean.py", language="python", raw_code="def clean(): pass", status="Faculty Review"
    )
    # 2. High AI Flagged submission in Section A
    sub_ai_flag = Submission(
        student_id=student_a.id + 100, assignment_id=9999, section_id=sec_a.id,
        file_name="ai_flag.py", language="python", raw_code="def ai(): pass", status="Faculty Review"
    )
    # 3. Clean submission in Section C (Prof does NOT manage Section C)
    sub_sec_c = Submission(
        student_id=student_c.id, assignment_id=9999, section_id=sec_c.id,
        file_name="sec_c.py", language="python", raw_code="def sec_c(): pass", status="Faculty Review"
    )
    db_session.add(sub_clean)
    db_session.add(sub_ai_flag)
    db_session.add(sub_sec_c)
    db_session.commit()
    
    # Add Analysis Results: clean score vs AI flagged score
    crud.create_or_update_analysis_result(db_session, submission_id=sub_clean.submission_id, ai_score=0.10, quality_score='{"loc": 5}')
    crud.create_or_update_analysis_result(db_session, submission_id=sub_ai_flag.submission_id, ai_score=0.85, quality_score='{"loc": 5}')
    crud.create_or_update_analysis_result(db_session, submission_id=sub_sec_c.submission_id, ai_score=0.10, quality_score='{"loc": 5}')
    
    # Login as Professor
    login_res = client.post("/login", data={"username": "professor", "password": "prof123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test Preview Endpoint
    prev_res = client.get(f"/assignments/9999/bulk-approve-preview", headers=headers)
    assert prev_res.status_code == 200
    p_data = prev_res.json()
    assert p_data["eligible_count"] == 1
    assert p_data["flagged_count"] == 1
    assert p_data["out_of_scope_count"] == 1
    
    # Execute Bulk Approve as Professor
    app_res = client.post(f"/assignments/9999/bulk-approve", headers=headers)
    assert app_res.status_code == 200
    a_data = app_res.json()
    
    assert a_data["approved_count"] == 1
    assert a_data["held_flagged_count"] == 1
    assert a_data["out_of_scope_count"] == 1
    
    # Verify sub_clean is approved, sub_ai_flag is NOT approved, sub_sec_c is NOT approved by Professor
    db_session.refresh(sub_clean.analysis_result)
    db_session.refresh(sub_ai_flag.analysis_result)
    db_session.refresh(sub_sec_c.analysis_result)
    
    assert sub_clean.analysis_result.report_visible == True
    assert sub_ai_flag.analysis_result.report_visible == False
    assert sub_sec_c.analysis_result.report_visible == False
    
    # Repeated Bulk Approve calls are safe
    app_res_repeat = client.post(f"/assignments/9999/bulk-approve", headers=headers)
    assert app_res_repeat.status_code == 200
    assert app_res_repeat.json()["approved_count"] == 1
