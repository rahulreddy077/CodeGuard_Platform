import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import get_db, Base, engine
from backend.database import crud
from backend.auth import create_access_token

client = TestClient(app)

def get_auth_header(username: str):
    token = create_access_token(data={"sub": username})
    return {"Authorization": f"Bearer {token}"}

def test_extraction_unit():
    from backend.extraction import extract_from_docx, extract_text_from_file, ExtractionError
    import docx
    
    doc = docx.Document()
    doc.add_paragraph("def double(x):\n    return x * 2")
    buf = io.BytesIO()
    doc.save(buf)
    
    text = extract_text_from_file("double.docx", buf.getvalue())
    assert "def double" in text

def test_all_vs_all_plagiarism_report_rbac():
    # Student login token
    student_headers = get_auth_header("student")
    prof_headers = get_auth_header("professor")

    # 1. Student should be blocked (HTTP 403)
    res_student = client.get("/assignments/1/plagiarism-report", headers=student_headers)
    assert res_student.status_code == 403, f"Expected 403 for Student, got {res_student.status_code}"

    # 2. Professor should succeed (HTTP 200)
    res_prof = client.get("/assignments/1/plagiarism-report", headers=prof_headers)
    assert res_prof.status_code == 200, f"Expected 200 for Professor, got {res_prof.status_code}"
    data = res_prof.json()
    assert "all_pairs" in data
    assert "students" in data
    assert "flagged_pairs_count" in data
    assert "clusters" in data
    assert "clusters_count" in data

def test_connected_components_clustering():
    prof_headers = get_auth_header("professor")
    # Upload 3 identical files to ensure they get grouped into 1 connected component cluster
    file1 = ("files", ("studA_same.py", b"def same(x):\n    return x * 10\n", "text/plain"))
    file2 = ("files", ("studB_same.py", b"def same(x):\n    return x * 10\n", "text/plain"))
    file3 = ("files", ("studC_same.py", b"def same(x):\n    return x * 10\n", "text/plain"))
    
    upload_res = client.post(
        "/assignments/1/bulk-upload",
        data={"section_id": 1},
        files=[file1, file2, file3],
        headers=prof_headers
    )
    assert upload_res.status_code == 200
    
    report_res = client.get("/assignments/1/plagiarism-report?threshold=0.50", headers=prof_headers)
    assert report_res.status_code == 200
    rep_data = report_res.json()
    assert rep_data["clusters_count"] >= 1
    top_cluster = rep_data["clusters"][0]
    assert top_cluster["submission_count"] >= 3
    assert len(top_cluster["internal_pairs"]) >= 3

def test_bulk_upload_endpoint():
    prof_headers = get_auth_header("professor")
    
    # Prepare 2 sample python code files
    file1 = ("files", ("student1_sol.py", b"def add(a, b):\n    return a + b\n", "text/plain"))
    file2 = ("files", ("student2_sol.py", b"def sum_two(x, y):\n    return x + y\n", "text/plain"))
    
    res = client.post(
        "/assignments/1/bulk-upload",
        data={"section_id": 1},
        files=[file1, file2],
        headers=prof_headers
    )
    assert res.status_code == 200, f"Bulk upload failed: {res.text}"
    data = res.json()
    assert data["success"] == True
    assert data["processed_count"] == 2
    assert data["failed_count"] == 0

if __name__ == "__main__":
    test_extraction_unit()
    print("[SUCCESS] Extraction unit test passed!")
    test_all_vs_all_plagiarism_report_rbac()
    print("[SUCCESS] All-vs-All Plagiarism Report RBAC test passed!")
    test_bulk_upload_endpoint()
    print("[SUCCESS] Bulk Upload API test passed!")
    print("[SUCCESS] ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
