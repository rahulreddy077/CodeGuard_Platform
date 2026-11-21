"""
tests/test_review_queue_ux.py
=============================
Tests for Review Queue UX Redesign:
- Assignment filtering
- Section filtering
- Combined assignment & section filtering
- Status filtering
- Search by student reg #, username, filename, submission ID
- Sorting by date, AI score, similarity
- Pagination, page size, total counts
- Empty results
- Professor authorization and cross-section access (403)
- HOD/Admin permissions across all sections
- Strict exclusion of unassigned submissions from review queue
- Pending identification count endpoint and mapping
- Existing approval safeguards
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal, Base, engine
from backend.database import crud
from backend.database.models import User, Section, Assignment, Submission, AnalysisResult, SimilarityPair


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    crud.seed_data(db)
    yield db
    db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _login(client, username, password):
    res = client.post("/login", data={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# 1. Assignment Filtering
def test_assignment_filtering(db_session, client):
    prof_h = _login(client, "professor", "prof123")
    asgns = client.get("/assignments", headers=prof_h).json()
    assert len(asgns) > 0
    target_asgn_id = asgns[0]["assignment_id"]

    res = client.get(f"/faculty/submissions?page=1&page_size=50&assignment_id={target_asgn_id}", headers=prof_h)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert all(item["assignment_id"] == target_asgn_id for item in data["items"])


# 2. Section Filtering
def test_section_filtering(db_session, client):
    prof_h = _login(client, "professor", "prof123")
    sec_res = client.get("/faculty/sections", headers=prof_h).json()
    assert len(sec_res) > 0
    target_sec_id = sec_res[0]["id"]

    res = client.get(f"/faculty/submissions?page=1&page_size=50&section_id={target_sec_id}", headers=prof_h)
    assert res.status_code == 200
    data = res.json()
    assert all(item["section_id"] == target_sec_id for item in data["items"])


# 3. Combined Assignment and Section Filtering
def test_combined_assignment_and_section_filtering(db_session, client):
    prof_h = _login(client, "professor", "prof123")
    asgns = client.get("/assignments", headers=prof_h).json()
    target_asgn_id = asgns[0]["assignment_id"]
    sec_res = client.get("/faculty/sections", headers=prof_h).json()
    target_sec_id = sec_res[0]["id"]

    res = client.get(
        f"/faculty/submissions?page=1&page_size=50&assignment_id={target_asgn_id}&section_id={target_sec_id}",
        headers=prof_h
    )
    assert res.status_code == 200
    data = res.json()
    assert all(item["assignment_id"] == target_asgn_id and item["section_id"] == target_sec_id for item in data["items"])


# 4. Status Filtering
def test_status_filtering(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    # Faculty Review filter
    res_fr = client.get("/faculty/submissions?page=1&status=Faculty Review", headers=prof_h)
    assert res_fr.status_code == 200
    data_fr = res_fr.json()
    assert all(item["status"] == "Faculty Review" for item in data_fr["items"])

    # Approved filter
    res_app = client.get("/faculty/submissions?page=1&status=Approved", headers=prof_h)
    assert res_app.status_code == 200
    data_app = res_app.json()
    assert all(item["status"] in ["Approved", "Completed"] for item in data_app["items"])

    # Flagged filter
    res_flag = client.get("/faculty/submissions?page=1&status=Flagged", headers=prof_h)
    assert res_flag.status_code == 200
    data_flag = res_flag.json()
    for item in data_flag["items"]:
        ai = item.get("ai_score") or 0.0
        sim = item.get("similarity_score") or 0.0
        assert ai >= 0.54 or sim >= 0.75 or item["is_flagged"] is True


# 5. Search Filtering
def test_search(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    # Search by known registration number
    res_reg = client.get("/faculty/submissions?page=1&search=22BCE1234", headers=prof_h)
    assert res_reg.status_code == 200
    data_reg = res_reg.json()
    if data_reg["total"] > 0:
        assert any(item["registration_number"] == "22BCE1234" or "22BCE1234" in item["file_name"] for item in data_reg["items"])

    # Search by student username
    res_user = client.get("/faculty/submissions?page=1&search=student", headers=prof_h)
    assert res_user.status_code == 200
    assert "items" in res_user.json()

    # Search by filename extension
    res_file = client.get("/faculty/submissions?page=1&search=.py", headers=prof_h)
    assert res_file.status_code == 200
    data_file = res_file.json()
    if data_file["total"] > 0:
        assert all(".py" in item["file_name"].lower() for item in data_file["items"])


# 6. Sorting
def test_sorting(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    # Sort by AI score descending
    res_ai_desc = client.get("/faculty/submissions?page=1&page_size=20&sort_by=ai_score&sort_order=desc", headers=prof_h)
    assert res_ai_desc.status_code == 200
    scores_desc = [item["ai_score"] for item in res_ai_desc.json()["items"] if item["ai_score"] is not None]
    assert scores_desc == sorted(scores_desc, reverse=True)

    # Sort by AI score ascending
    res_ai_asc = client.get("/faculty/submissions?page=1&page_size=20&sort_by=ai_score&sort_order=asc", headers=prof_h)
    assert res_ai_asc.status_code == 200
    scores_asc = [item["ai_score"] for item in res_ai_asc.json()["items"] if item["ai_score"] is not None]
    assert scores_asc == sorted(scores_asc)

    # Sort by date descending
    res_date = client.get("/faculty/submissions?page=1&page_size=20&sort_by=date&sort_order=desc", headers=prof_h)
    assert res_date.status_code == 200


# 7. Pagination and Total Counts
def test_pagination_and_total_counts(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    p1 = client.get("/faculty/submissions?page=1&page_size=20", headers=prof_h).json()
    assert p1["page"] == 1
    assert p1["page_size"] == 20
    assert len(p1["items"]) <= 20
    assert "metrics" in p1

    if p1["total_pages"] > 1:
        p2 = client.get("/faculty/submissions?page=2&page_size=20", headers=prof_h).json()
        assert p2["page"] == 2
        p1_ids = {item["submission_id"] for item in p1["items"]}
        p2_ids = {item["submission_id"] for item in p2["items"]}
        # Pages must not overlap
        assert len(p1_ids.intersection(p2_ids)) == 0

    # Test page_size 50
    p50 = client.get("/faculty/submissions?page=1&page_size=50", headers=prof_h).json()
    assert p50["page_size"] == 50
    assert len(p50["items"]) <= 50


# 8. Empty Results
def test_empty_results(db_session, client):
    prof_h = _login(client, "professor", "prof123")
    res = client.get("/faculty/submissions?page=1&search=nonexistent_file_xyz_12345", headers=prof_h)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


# 9. Professor Authorization and Cross-Section Access
def test_professor_authorization_and_cross_section_access(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    # Section 3 is not assigned to professor
    res_unauth = client.get("/faculty/submissions?section_id=3", headers=prof_h)
    assert res_unauth.status_code == 403
    assert "do not teach" in res_unauth.json()["detail"].lower()


# 10. HOD/Admin Permissions Across All Sections
def test_hod_admin_permissions(db_session, client):
    hod_h = _login(client, "hod", "hod123")

    # HOD can access section 1, section 2, section 3
    for s_id in [1, 2, 3]:
        res = client.get(f"/faculty/submissions?section_id={s_id}", headers=hod_h)
        assert res.status_code == 200

    # Invalid section returns 400
    res_bad_sec = client.get("/faculty/submissions?section_id=99999", headers=hod_h)
    assert res_bad_sec.status_code == 400


# 11. Strict Exclusion of Unassigned Submissions
def test_exclusion_of_unassigned_submissions(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    # Backward compatible list call
    res_list = client.get("/faculty/submissions", headers=prof_h)
    assert res_list.status_code == 200
    subs = res_list.json()
    assert isinstance(subs, list)
    assert all(s["status"] != "Awaiting Student Identification" for s in subs)

    # Paginated call
    res_paged = client.get("/faculty/submissions?page=1&page_size=100", headers=prof_h)
    assert res_paged.status_code == 200
    p_subs = res_paged.json()["items"]
    assert all(s["status"] != "Awaiting Student Identification" for s in p_subs)
    assert all(s["student_id"] is not None for s in p_subs)


# 12. Pending Identification Count and Mapping
def test_pending_identification_count_and_mapping(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    # Check unassigned count endpoint
    res_count = client.get("/faculty/unassigned-count", headers=prof_h)
    assert res_count.status_code == 200
    count_data = res_count.json()
    assert "count" in count_data
    assert isinstance(count_data["count"], int)

    # Check unassigned submissions endpoint
    res_unassigned = client.get("/faculty/unassigned-submissions", headers=prof_h)
    assert res_unassigned.status_code == 200
    unassigned_items = res_unassigned.json()
    assert len(unassigned_items) == count_data["count"]


# 13. Existing Approval Safeguards
def test_existing_approval_safeguards(db_session, client):
    prof_h = _login(client, "professor", "prof123")

    # Find pending submission
    pending_sub = db_session.query(Submission).filter(Submission.status == "Awaiting Student Identification").first()
    if pending_sub:
        res = client.post(f"/approve-report/{pending_sub.submission_id}?approve=true", headers=prof_h)
        assert res.status_code == 400
        assert "cannot approve or release" in res.json()["detail"].lower()
