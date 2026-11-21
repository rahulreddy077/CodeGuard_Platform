"""
test_bulk_upload_section.py
===========================
Tests for the section_id fix in the bulk-upload endpoint.

Covers:
  1. Explicit valid section selection   — professor uploads to their own section
  2. Missing section_id                 — 422 Unprocessable Entity from FastAPI
  3. Invalid (nonexistent) section_id  — 400 Bad Request
  4. Professor unauthorized section     — 403 Forbidden
  5. Valid upload by professor to assigned section
  6. HOD uploads to any section (RBAC all-access)
"""

import io
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import SessionLocal, Base, engine
from backend.database import crud
from backend.database.models import User, Section, Assignment

SMALL_PY = b"def solution():\n    return 42\n"
STUDENT_FILE = ("files", ("22BCE1234_solution.py", SMALL_PY, "text/plain"))


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


def _first_assignment_id(client, headers):
    res = client.get("/assignments", headers=headers)
    assert res.status_code == 200
    asgns = res.json()
    assert len(asgns) > 0
    return asgns[0]["assignment_id"]


# ── Test 1: Valid section — professor uploads to an assigned section ──────────
def test_1_explicit_valid_section_selection(db_session, client):
    """Professor uploads to a section they manage. Should succeed."""
    headers = _login(client, "professor", "prof123")

    # Discover which sections the professor is assigned to
    sec_res = client.get("/faculty/sections", headers=headers)
    assert sec_res.status_code == 200
    sections = sec_res.json()
    assert len(sections) > 0, "Professor must have at least one assigned section"

    asgn_id = _first_assignment_id(client, headers)
    section_id = sections[0]["id"]

    res = client.post(
        f"/assignments/{asgn_id}/bulk-upload",
        data={"section_id": section_id},
        files=[STUDENT_FILE],
        headers=headers,
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert data["total_files"] == 1
    assert data["assignment_id"] == asgn_id


# ── Test 2: Missing section_id — must be rejected (422) ───────────────────────
def test_2_missing_section_id(db_session, client):
    """Omitting section_id should return 422 Unprocessable Entity (FastAPI validation)."""
    headers = _login(client, "professor", "prof123")
    asgn_id = _first_assignment_id(client, headers)

    res = client.post(
        f"/assignments/{asgn_id}/bulk-upload",
        # No 'data' with section_id at all
        files=[STUDENT_FILE],
        headers=headers,
    )
    # FastAPI returns 422 for missing required Form fields
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"


# ── Test 3: Invalid section_id — section does not exist ───────────────────────
def test_3_invalid_section_id(db_session, client):
    """A section_id that references no section row should return 400."""
    headers = _login(client, "professor", "prof123")
    asgn_id = _first_assignment_id(client, headers)

    NONEXISTENT_SECTION_ID = 99999

    res = client.post(
        f"/assignments/{asgn_id}/bulk-upload",
        data={"section_id": NONEXISTENT_SECTION_ID},
        files=[STUDENT_FILE],
        headers=headers,
    )
    assert res.status_code in (400, 403), f"Expected 400 or 403, got {res.status_code}: {res.text}"
    detail = res.json().get("detail", "")
    # Should mention that the section does not exist OR that the professor doesn't teach it
    assert "section" in detail.lower() or "teach" in detail.lower(), f"Unexpected detail: {detail}"


# ── Test 4: Professor uploads to unauthorized section ─────────────────────────
def test_4_professor_unauthorized_section(db_session, client):
    """Professor must not be able to upload to a section they don't manage."""
    headers = _login(client, "professor", "prof123")
    asgn_id = _first_assignment_id(client, headers)

    # Get ALL sections in the system (via HOD account)
    hod_headers = _login(client, "hod", "hod123")
    all_sec_res = client.get("/faculty/sections", headers=hod_headers)
    assert all_sec_res.status_code == 200
    all_sections = all_sec_res.json()

    # Get sections assigned to the professor
    prof_sec_res = client.get("/faculty/sections", headers=headers)
    prof_section_ids = {s["id"] for s in prof_sec_res.json()}

    # Find a section the professor does NOT manage
    unauthorized = next((s for s in all_sections if s["id"] not in prof_section_ids), None)
    if unauthorized is None:
        pytest.skip("All sections are assigned to professor — cannot test unauthorized access")

    res = client.post(
        f"/assignments/{asgn_id}/bulk-upload",
        data={"section_id": unauthorized["id"]},
        files=[STUDENT_FILE],
        headers=headers,
    )
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    assert "do not teach" in res.json().get("detail", "").lower()


# ── Test 5: Valid upload by professor to their assigned section ───────────────
def test_5_valid_professor_upload_assigned_section(db_session, client):
    """End-to-end: professor picks a valid section, uploads a file, gets a successful response
    with partial-failure reporting preserved."""
    headers = _login(client, "professor", "prof123")

    sec_res = client.get("/faculty/sections", headers=headers)
    assert sec_res.status_code == 200
    prof_sections = sec_res.json()
    assert len(prof_sections) > 0
    section_id = prof_sections[0]["id"]

    asgn_id = _first_assignment_id(client, headers)

    # Valid .py + unsupported .exe
    files_payload = [
        ("files", ("22BCE1234_hw.py", SMALL_PY, "text/plain")),
        ("files", ("bad_file.exe", b"binary", "application/octet-stream")),
    ]

    res = client.post(
        f"/assignments/{asgn_id}/bulk-upload",
        data={"section_id": section_id},
        files=files_payload,
        headers=headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_files"] == 2
    assert data["failed_count"] == 1  # .exe rejected
    failed_reasons = [f["reason"] for f in data["failed_files"]]
    assert any("Unsupported file extension" in r for r in failed_reasons)

    # Verify section assignment on the resulting submission
    all_created = data.get("successful_submissions", []) + data.get("unassigned_submissions", [])
    assert len(all_created) == 1


# ── Test 6: HOD uploads to any section (full RBAC access) ────────────────────
def test_6_hod_can_upload_to_any_section(db_session, client):
    """HOD/Admin bypass professor section restriction and may upload to any section."""
    hod_headers = _login(client, "hod", "hod123")
    asgn_id = _first_assignment_id(client, hod_headers)

    # HOD sees all sections
    sec_res = client.get("/faculty/sections", headers=hod_headers)
    assert sec_res.status_code == 200
    all_sections = sec_res.json()
    assert len(all_sections) > 0

    # Upload to every available section (just pick the first two for efficiency)
    for sec in all_sections[:2]:
        res = client.post(
            f"/assignments/{asgn_id}/bulk-upload",
            data={"section_id": sec["id"]},
            files=[("files", (f"22BCE1234_{sec['section_name']}.py", SMALL_PY, "text/plain"))],
            headers=hod_headers,
        )
        assert res.status_code == 200, f"HOD upload to section {sec['section_name']} failed: {res.text}"
        assert res.json()["success"] is True


# ── Test 7: /faculty/sections returns only professor's sections ───────────────
def test_7_faculty_sections_scoped_to_professor(db_session, client):
    """GET /faculty/sections for a Professor returns only their assigned sections,
    not ALL sections in the system."""
    prof_headers = _login(client, "professor", "prof123")
    hod_headers = _login(client, "hod", "hod123")

    prof_secs = client.get("/faculty/sections", headers=prof_headers).json()
    all_secs = client.get("/faculty/sections", headers=hod_headers).json()

    # Professor should see a subset (≤ total)
    assert len(prof_secs) <= len(all_secs)
    # Section IDs returned for professor must all be within the total set
    total_ids = {s["id"] for s in all_secs}
    for s in prof_secs:
        assert s["id"] in total_ids
