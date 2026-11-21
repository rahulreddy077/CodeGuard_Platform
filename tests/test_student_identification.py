import io
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.database.connection import SessionLocal, Base, engine
from backend.database.models import User, Section, Assignment, Submission, AnalysisResult, SubmissionAST, SubmissionEmbedding
import backend.database.crud as crud
from backend.auth import get_password_hash
from backend.main import app

@pytest.fixture(scope="module")
def setup_test_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    crud.seed_data(db)

    # Ensure sections 1 and 2 exist
    sec1 = db.query(Section).filter(Section.id == 1).first()
    if not sec1:
        sec1 = Section(id=1, section_name="A")
        db.add(sec1)
    sec2 = db.query(Section).filter(Section.id == 2).first()
    if not sec2:
        sec2 = Section(id=2, section_name="B")
        db.add(sec2)

    # Ensure test students with specific registration numbers exist
    stud1 = db.query(User).filter(User.registration_number == "22BCE1234").first()
    if not stud1:
        stud1 = db.query(User).filter(User.username == "student").first()
        if stud1:
            stud1.registration_number = "22BCE1234"
            stud1.active = True
        else:
            stud1 = User(
                username="student_reg1",
                email="reg1@university.edu",
                password_hash=get_password_hash("pass123"),
                role="Student",
                registration_number="22BCE1234",
                active=True
            )
            db.add(stud1)
    else:
        stud1.active = True

    stud2 = db.query(User).filter(User.registration_number == "22BCE1235").first()
    if not stud2:
        stud2 = User(
            username="student_reg2",
            email="reg2@university.edu",
            password_hash=get_password_hash("pass123"),
            role="Student",
            registration_number="22BCE1235",
            active=True
        )
        db.add(stud2)
    else:
        stud2.active = True

    stud3 = db.query(User).filter(User.registration_number == "22BCE1236").first()
    if not stud3:
        stud3 = User(
            username="student_reg3",
            email="reg3@university.edu",
            password_hash=get_password_hash("pass123"),
            role="Student",
            registration_number="22BCE1236",
            active=True
        )
        db.add(stud3)
    else:
        stud3.active = True

    # Inactive student for eligibility testing
    stud_inactive = db.query(User).filter(User.registration_number == "22BCE9998").first()
    if not stud_inactive:
        stud_inactive = User(
            username="student_inactive",
            email="inactive@university.edu",
            password_hash=get_password_hash("pass123"),
            role="Student",
            registration_number="22BCE9998",
            active=False
        )
        db.add(stud_inactive)
    else:
        stud_inactive.active = False

    # Professor teaching only Section 1
    prof1 = db.query(User).filter(User.username == "professor").first()
    if prof1:
        prof1.sections = [sec1]

    # Create a fresh isolated test assignment
    import uuid
    asgn = Assignment(
        title=f"Identification Lab Test {uuid.uuid4().hex[:8]}",
        course="CS102",
        due_date=datetime(2027, 1, 1)
    )
    db.add(asgn)
    db.commit()
    db.refresh(asgn)
    asgn_id = asgn.assignment_id

    yield {
        "db": db,
        "asgn_id": asgn_id,
        "stud1_id": stud1.id,
        "stud1_username": stud1.username,
        "stud2_id": stud2.id,
        "stud2_username": stud2.username,
        "stud3_id": stud3.id,
        "stud3_username": stud3.username,
        "stud_inactive_id": stud_inactive.id
    }
    db.close()

@pytest.fixture(scope="module")
def prof_client(setup_test_data):
    client = TestClient(app)
    login_res = client.post("/login", data={"username": "professor", "password": "prof123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

# 1. Recognized registration number in a filename
def test_1_recognized_reg_number_in_filename(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    code = b"def solution():\n    return 'recognized'\n"
    files = [("files", ("22BCE1234.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["identified_count"] == 1
    assert data["unassigned_count"] == 0
    assert len(data["successful_submissions"]) == 1
    sub = data["successful_submissions"][0]
    assert sub["student"] == setup_test_data["stud1_username"]
    assert sub["identified"] is True
    assert sub["status"] in ["Completed", "Faculty Review"]

# 2. Registration number with a filename prefix or suffix
def test_2_reg_number_with_prefix_and_suffix(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    code1 = b"def test_prefix():\n    return 1\n"
    code2 = b"def test_suffix():\n    return 2\n"
    files = [
        ("files", ("22BCE1235_Assignment1.py", code1, "text/plain")),
        ("files", ("Assignment2_22BCE1236.py", code2, "text/plain")),
    ]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["identified_count"] == 2
    assert data["unassigned_count"] == 0
    matched_students = {s["student"] for s in data["successful_submissions"]}
    assert setup_test_data["stud2_username"] in matched_students
    assert setup_test_data["stud3_username"] in matched_students

# 3. Unknown registration number
def test_3_unknown_registration_number(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    code = b"def unknown():\n    return 'whoami'\n"
    files = [("files", ("22BCE9999_Solution.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["identified_count"] == 0
    assert data["unassigned_count"] == 1
    unassigned = data["unassigned_submissions"][0]
    assert unassigned["status"] == "Awaiting Student Identification"
    assert "Unknown registration number" in unassigned["unassigned_reason"]
    assert "22BCE9999" in unassigned["unassigned_reason"]

# 4. Filename with no recognizable registration number
def test_4_filename_with_no_recognizable_registration_number(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    code = b"def binary_search(arr, x):\n    return -1\n"
    files = [("files", ("binary_search.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["unassigned_count"] == 1
    unassigned = data["unassigned_submissions"][0]
    assert unassigned["status"] == "Awaiting Student Identification"
    assert "No recognizable student registration number found" in unassigned["unassigned_reason"]

# 5. Ambiguous student identification
def test_5_ambiguous_student_identification(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    code = b"def collab():\n    return 'ambiguous'\n"
    files = [("files", ("22BCE1234_22BCE1235_project.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["unassigned_count"] == 1
    unassigned = data["unassigned_submissions"][0]
    assert unassigned["status"] == "Awaiting Student Identification"
    assert "Ambiguous filename" in unassigned["unassigned_reason"]

# 6. Pending file retained without student assignment
def test_6_pending_file_retained_safely(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    code = b"def solution_v2():\n    pass\n"
    files = [("files", ("solution_v2.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    assert res.status_code == 200
    sub_id = res.json()["unassigned_submissions"][0]["submission_id"]

    db = setup_test_data["db"]
    sub_record = db.query(Submission).filter(Submission.submission_id == sub_id).first()
    assert sub_record is not None
    assert sub_record.student_id is None
    assert sub_record.status == "Awaiting Student Identification"
    assert sub_record.file_name == "solution_v2.py"
    assert sub_record.assignment_id == asgn_id

# 7. Manual mapping to a valid student
def test_7_manual_mapping_to_valid_student(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    stud2_id = setup_test_data["stud2_id"]
    code = b"def manual_map():\n    return 42\n"
    files = [("files", ("unmapped_script.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    sub_id = res.json()["unassigned_submissions"][0]["submission_id"]

    # Assign to student_reg2
    assign_res = prof_client.post(f"/submissions/{sub_id}/assign-student", json={"student_id": stud2_id})
    assert assign_res.status_code == 200
    data = assign_res.json()
    assert data["student"] == setup_test_data["stud2_username"]
    assert data["status"] in ["Completed", "Faculty Review"]

    db = setup_test_data["db"]
    sub_record = db.query(Submission).filter(Submission.submission_id == sub_id).first()
    assert sub_record.student_id == stud2_id
    assert sub_record.status in ["Completed", "Faculty Review"]
    assert sub_record.unassigned_reason is None

# 8. Invalid student selection
def test_8_invalid_student_selection(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    code = b"def err_check():\n    return 1\n"
    files = [("files", ("err_check.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    sub_id = res.json()["unassigned_submissions"][0]["submission_id"]

    # Non-existent student ID
    res_bad_id = prof_client.post(f"/submissions/{sub_id}/assign-student", json={"student_id": 999999})
    assert res_bad_id.status_code == 400
    assert "Invalid student selection" in res_bad_id.json()["detail"]

    # User who is a Professor, not a Student
    db = setup_test_data["db"]
    prof_user = db.query(User).filter(User.username == "professor").first()
    res_prof_id = prof_client.post(f"/submissions/{sub_id}/assign-student", json={"student_id": prof_user.id})
    assert res_prof_id.status_code == 400
    assert "is not a registered student" in res_prof_id.json()["detail"]

# 9. Student not eligible for the assignment (inactive student)
def test_9_student_not_eligible_for_assignment(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    stud_inactive_id = setup_test_data["stud_inactive_id"]
    code = b"def inactive_test():\n    return 0\n"
    files = [("files", ("inactive_test.py", code, "text/plain"))]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    sub_id = res.json()["unassigned_submissions"][0]["submission_id"]

    res_inactive = prof_client.post(f"/submissions/{sub_id}/assign-student", json={"student_id": stud_inactive_id})
    assert res_inactive.status_code == 400
    assert "Student not eligible for the assignment" in res_inactive.json()["detail"]

# 10. Duplicate-submission prevention
def test_10_duplicate_submission_prevention(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    stud1_id = setup_test_data["stud1_id"]
    # Upload first file for student_reg1
    files1 = [("files", ("dup_target.py", b"def f(): return 1\n", "text/plain"))]
    r1 = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files1)
    s1_id = r1.json()["unassigned_submissions"][0]["submission_id"]
    # Assign to student_reg1
    a1 = prof_client.post(f"/submissions/{s1_id}/assign-student", json={"student_id": stud1_id})
    assert a1.status_code == 200

    # Upload second unassigned file with identical filename
    files2 = [("files", ("dup_target.py", b"def f(): return 2\n", "text/plain"))]
    r2 = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files2)
    s2_id = r2.json()["unassigned_submissions"][0]["submission_id"]

    # Attempting to assign second submission with same filename to same student must fail
    a2 = prof_client.post(f"/submissions/{s2_id}/assign-student", json={"student_id": stud1_id})
    assert a2.status_code == 400
    assert "Duplicate submission rejected" in a2.json()["detail"]

# 11. Professor section authorization
def test_11_professor_section_authorization(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    stud3_id = setup_test_data["stud3_id"]
    # Professor teaches section 1 only. Uploading to Section 2 must be 403 Forbidden
    files = [("files", ("sec2_file.py", b"def sec2(): pass\n", "text/plain"))]
    res_upload = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 2}, files=files)
    assert res_upload.status_code == 403
    assert "You do not teach this section" in res_upload.json()["detail"]

    # Also test manual assignment to a submission that belongs to section 2
    db = setup_test_data["db"]
    sub_sec2 = Submission(
        student_id=None,
        assignment_id=asgn_id,
        section_id=2,
        file_name="outside_section.py",
        language="python",
        raw_code="def outside(): pass",
        status="Awaiting Student Identification"
    )
    db.add(sub_sec2)
    db.commit()
    db.refresh(sub_sec2)

    res_assign = prof_client.post(f"/submissions/{sub_sec2.submission_id}/assign-student", json={"student_id": stud3_id})
    assert res_assign.status_code == 403
    assert "You do not teach this section" in res_assign.json()["detail"]

# 12. Pending files excluded from student-specific analysis
def test_12_pending_files_excluded_from_plagiarism_and_reports(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    # Plagiarism report should only include active student submissions
    plag_res = prof_client.get(f"/assignments/{asgn_id}/plagiarism-report?threshold=0.75")
    assert plag_res.status_code == 200
    rep = plag_res.json()
    student_usernames = [s["student_username"] for s in rep.get("students", [])]
    # No student username should be None or "Unknown"
    assert all(u is not None for u in student_usernames)

    # Pending submissions endpoint returns pending files, while regular review queue excludes them
    unassigned_res = prof_client.get(f"/faculty/unassigned-submissions?assignment_id={asgn_id}")
    assert unassigned_res.status_code == 200
    pending_list = unassigned_res.json()
    assert all(p["status"] == "Awaiting Student Identification" for p in pending_list)

    # Regular review queue does not contain pending files
    rev_res = prof_client.get("/faculty/submissions")
    assert rev_res.status_code == 200
    rev_subs = rev_res.json()
    assert all(s.get("status") != "Awaiting Student Identification" for s in rev_subs)

# 13. Pending files cannot be approved or released
def test_13_pending_files_cannot_be_approved_or_released(setup_test_data, prof_client):
    db = setup_test_data["db"]
    pending_sub = db.query(Submission).filter(Submission.status == "Awaiting Student Identification").first()
    assert pending_sub is not None
    sub_id = pending_sub.submission_id

    # Approve attempt must fail
    app_res = prof_client.post(f"/approve-report/{sub_id}?approve=true")
    assert app_res.status_code == 400
    assert "awaiting student identification" in app_res.json()["detail"].lower()

    # Release attempt must fail
    rel_res = prof_client.post(f"/release-report/{sub_id}?release=true")
    assert rel_res.status_code == 400
    assert "awaiting student identification" in rel_res.json()["detail"].lower()

# 14. Successful analysis after manual identification
def test_14_successful_analysis_after_manual_identification(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    stud3_id = setup_test_data["stud3_id"]
    code = b"def calculate_total(items):\n    # Computes sum of item prices\n    total = sum(item.price for item in items)\n    return total\n"
    files = [("files", ("calc_total_unknown.py", code, "text/plain"))]
    r = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    sub_id = r.json()["unassigned_submissions"][0]["submission_id"]

    # Map to student_reg3
    assign_res = prof_client.post(f"/submissions/{sub_id}/assign-student", json={"student_id": stud3_id})
    assert assign_res.status_code == 200

    db = setup_test_data["db"]
    # Check that AST record was created
    ast_rec = db.query(SubmissionAST).filter(SubmissionAST.submission_id == sub_id).first()
    assert ast_rec is not None
    assert ast_rec.ast_json is not None

    # Check that Embedding record was created
    emb_rec = db.query(SubmissionEmbedding).filter(SubmissionEmbedding.submission_id == sub_id).first()
    assert emb_rec is not None
    assert emb_rec.embedding_vector is not None

    # Check that AnalysisResult was created
    analysis_rec = db.query(AnalysisResult).filter(AnalysisResult.submission_id == sub_id).first()
    assert analysis_rec is not None
    assert analysis_rec.quality_score is not None
    assert analysis_rec.ai_score is not None

# 15. Existing file-size and extension protections
def test_15_file_size_and_extension_protections(setup_test_data, prof_client):
    asgn_id = setup_test_data["asgn_id"]
    # 1. Reject > 10MB
    oversized_data = b"X" * (10 * 1024 * 1024 + 100)
    files = [
        ("files", ("huge_file.py", oversized_data, "text/plain")),
        ("files", ("unsupported_script.sh", b"#!/bin/bash\necho hello", "application/x-sh")),
    ]
    res = prof_client.post(f"/assignments/{asgn_id}/bulk-upload", data={"section_id": 1}, files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["failed_count"] == 2
    failed_reasons = [f["reason"] for f in data["failed_files"]]
    assert any("exceeds maximum allowable size limit" in r for r in failed_reasons)
    assert any("Unsupported file extension" in r for r in failed_reasons)
