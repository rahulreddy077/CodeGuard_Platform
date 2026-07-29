import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("Starting Phase 2 verification script...\n")
    
    # 1. Test Login for Student
    print("[Test 1] Logging in as student...")
    payload = {"username": "student", "password": "stud123"}
    res = requests.post(f"{BASE_URL}/login", data=payload)
    assert res.status_code == 200, f"Failed student login: {res.text}"
    student_data = res.json()
    student_token = student_data["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("OK: Logged in as student.")

    # 2. Test Login for Professor
    print("\n[Test 2] Logging in as professor...")
    payload = {"username": "professor", "password": "prof123"}
    res = requests.post(f"{BASE_URL}/login", data=payload)
    assert res.status_code == 200, f"Failed prof login: {res.text}"
    prof_data = res.json()
    prof_token = prof_data["access_token"]
    prof_headers = {"Authorization": f"Bearer {prof_token}"}
    print("OK: Logged in as professor.")

    # 3. Test Student Uploading Code
    print("\n[Test 3] Uploading code as student...")
    upload_payload = {
        "assignment_id": 1,
        "section_id": 1, # Section A
        "file_name": "solution.py",
        "language": "python",
        "raw_code": "def calculate_factorial(n):\n    return 1 if n <= 1 else n * calculate_factorial(n-1)"
    }
    res = requests.post(f"{BASE_URL}/upload", json=upload_payload, headers=student_headers)
    assert res.status_code == 200, f"Failed code upload: {res.text}"
    upload_res = res.json()
    sub_id = upload_res["submission_id"]
    print(f"OK: Code uploaded successfully. Submission ID: {sub_id}, Status: {upload_res['status']}")

    # 4. Test Student viewing own submissions list
    print("\n[Test 4] Fetching own submissions list as student...")
    res = requests.get(f"{BASE_URL}/my-submissions", headers=student_headers)
    assert res.status_code == 200, f"Failed my-submissions: {res.text}"
    my_subs = res.json()
    assert len(my_subs) >= 1, "Expected at least 1 submission"
    print(f"OK: Student can view own submissions list. Found {len(my_subs)} submissions.")

    # 5. Test Student viewing submission details (before approval)
    print("\n[Test 5] Fetching submission details as student before faculty approval...")
    res = requests.get(f"{BASE_URL}/submission/{sub_id}", headers=student_headers)
    assert res.status_code == 200, f"Failed submission detail fetch: {res.text}"
    sub_detail = res.json()
    assert sub_detail["report"] is None, "Report should be hidden from student before approval"
    print(f"OK: Report is correctly hidden. Message: '{sub_detail['message']}'")

    # 6. Test Professor viewing submission details
    print("\n[Test 6] Fetching submission details as professor...")
    res = requests.get(f"{BASE_URL}/submission/{sub_id}", headers=prof_headers)
    assert res.status_code == 200, f"Failed prof submission detail fetch: {res.text}"
    prof_sub_detail = res.json()
    assert prof_sub_detail["report"] is not None, "Professor should see the analysis report"
    print(f"OK: Professor can view full report. AI Probability: {prof_sub_detail['report']['ai_score']}")

    # 7. Test Student trying to approve their own report (RBAC Violations check)
    print("\n[Test 7] Verifying student cannot approve reports (RBAC protection test)...")
    res = requests.post(f"{BASE_URL}/approve-report/{sub_id}", headers=student_headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    print("OK: Student is correctly blocked with HTTP 403 Forbidden.")

    # 8. Test Student trying to access global analytics (RBAC Violations check)
    print("\n[Test 8] Verifying student cannot access HOD analytics...")
    res = requests.get(f"{BASE_URL}/hod/analytics", headers=student_headers)
    assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
    print("OK: Student is correctly blocked from HOD analytics.")

    # 9. Test Professor approving the report
    print("\n[Test 9] Approving submission report as professor...")
    res = requests.post(f"{BASE_URL}/approve-report/{sub_id}", headers=prof_headers)
    assert res.status_code == 200, f"Failed report approval: {res.text}"
    print("OK: Report approved successfully.")

    # 10. Test Student viewing details after approval
    print("\n[Test 10] Fetching submission details as student after faculty approval...")
    res = requests.get(f"{BASE_URL}/submission/{sub_id}", headers=student_headers)
    assert res.status_code == 200, f"Failed submission detail fetch: {res.text}"
    sub_detail_approved = res.json()
    assert sub_detail_approved["report"] is not None, "Report should be visible to student after approval"
    assert sub_detail_approved["metadata"]["status"] == "Approved", f"Expected Approved status, got {sub_detail_approved['metadata']['status']}"
    print("OK: Report is now fully visible to student and status is 'Approved'.")

    # 11. Test HOD Login & analytics
    print("\n[Test 11] Logging in as HOD and viewing analytics...")
    payload = {"username": "hod", "password": "hod123"}
    res = requests.post(f"{BASE_URL}/login", data=payload)
    assert res.status_code == 200, f"Failed HOD login: {res.text}"
    hod_token = res.json()["access_token"]
    hod_headers = {"Authorization": f"Bearer {hod_token}"}
    
    res = requests.get(f"{BASE_URL}/hod/analytics", headers=hod_headers)
    assert res.status_code == 200, f"Failed HOD analytics fetch: {res.text}"
    analytics = res.json()
    print(f"OK: HOD has access to analytics. Total submissions: {analytics['total_system_submissions']}")

    print("\nAll 11 authentication, upload, approval, and RBAC tests passed successfully!")

if __name__ == "__main__":
    run_tests()
