"""
CodeGuard - Teacher (Professor) Dashboard & RBAC Workflow Test
===============================================================
1. Student 1 logs in and submits Code 1 (Bubble Sort)
2. Student 2 logs in and submits Code 2 (Obfuscated Bubble Sort)
3. Professor logs in and accesses Teacher Dashboard (/faculty/submissions)
4. Professor inspects full analysis report (AI score, AST, Similarity Pairs)
5. Professor approves the submission for Student 1.
6. Verifies Student 1 can now view approved report.
"""

import sys
import os
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_teacher_dashboard_test():
    print("=== 1. Student 1 Login & Code Submission ===")
    res = requests.post(f"{BASE_URL}/login", data={"username": "student", "password": "stud123"})
    assert res.status_code == 200, f"Student 1 login failed: {res.text}"
    s1_token = res.json()["access_token"]
    s1_headers = {"Authorization": f"Bearer {s1_token}"}
    
    code1 = """def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr"""
    
    sub1_payload = {
        "assignment_id": 1,
        "section_id": 1,
        "file_name": "student1_bubblesort.py",
        "language": "python",
        "raw_code": code1
    }
    res = requests.post(f"{BASE_URL}/upload", json=sub1_payload, headers=s1_headers)
    assert res.status_code == 200, f"Student 1 upload failed: {res.text}"
    sub1_id = res.json()["submission_id"]
    print(f"OK: Student 1 uploaded code. Submission ID: {sub1_id}")

    print("\n=== 2. Student 2 (demo_student_2) Login & Code Submission ===")
    res = requests.post(f"{BASE_URL}/login", data={"username": "demo_student_2", "password": "password123"})
    assert res.status_code == 200, f"Student 2 login failed: {res.text}"
    s2_token = res.json()["access_token"]
    s2_headers = {"Authorization": f"Bearer {s2_token}"}
    
    code2 = """def sort_array(data_list):
    size_n = len(data_list)
    for idx_i in range(size_n):
        for idx_j in range(0, size_n - idx_i - 1):
            if data_list[idx_j] > data_list[idx_j + 1]:
                temp_val = data_list[idx_j]
                data_list[idx_j] = data_list[idx_j + 1]
                data_list[idx_j + 1] = temp_val
    return data_list"""
    
    sub2_payload = {
        "assignment_id": 1,
        "section_id": 1,
        "file_name": "student2_obfuscated_sort.py",
        "language": "python",
        "raw_code": code2
    }
    res = requests.post(f"{BASE_URL}/upload", json=sub2_payload, headers=s2_headers)
    assert res.status_code == 200, f"Student 2 upload failed: {res.text}"
    sub2_id = res.json()["submission_id"]
    print(f"OK: Student 2 uploaded code. Submission ID: {sub2_id}")

    print("\n=== 3. Professor (Teacher) Login ===")
    res = requests.post(f"{BASE_URL}/login", data={"username": "professor", "password": "prof123"})
    assert res.status_code == 200, f"Professor login failed: {res.text}"
    prof_data = res.json()
    prof_token = prof_data["access_token"]
    prof_headers = {"Authorization": f"Bearer {prof_token}"}
    print(f"OK: Logged in as Professor (Role: {prof_data['role']})")

    print("\n=== 4. Fetching Teacher Dashboard Submissions (/faculty/submissions) ===")
    res = requests.get(f"{BASE_URL}/faculty/submissions", headers=prof_headers)
    assert res.status_code == 200, f"Failed faculty submissions fetch: {res.text}"
    faculty_subs = res.json()
    print(f"OK: Teacher Dashboard retrieved {len(faculty_subs)} total submissions across assigned sections.")
    
    for s in faculty_subs:
        if s["submission_id"] in (sub1_id, sub2_id):
            print(f"  - Sub ID: {s['submission_id']} | Student: {s['student_username']} | File: {s['file_name']} | Status: {s['status']}")

    print("\n=== 5. Teacher Inspecting Submission Details & Analysis Report ===")
    res = requests.get(f"{BASE_URL}/submission/{sub1_id}", headers=prof_headers)
    assert res.status_code == 200, f"Failed submission detail fetch: {res.text}"
    detail = res.json()
    report = detail["report"]
    print(f"OK: Professor accessed Submission {sub1_id} report:")
    print(f"  AI Probability Score: {report['ai_score']}")
    print(f"  Quality Metrics: {report['quality']}")
    print(f"  Plagiarism Matches / Pairs: {report['plagiarism']}")

    print("\n=== 6. Teacher Approving Report for Student 1 ===")
    res = requests.post(f"{BASE_URL}/approve-report/{sub1_id}", headers=prof_headers)
    assert res.status_code == 200, f"Report approval failed: {res.text}"
    print(f"OK: Professor approved report for Submission {sub1_id}.")

    print("\n=== 7. Verifying Student 1 Access Post-Approval ===")
    res = requests.get(f"{BASE_URL}/submission/{sub1_id}", headers=s1_headers)
    assert res.status_code == 200, f"Student detail fetch failed: {res.text}"
    s1_detail = res.json()
    assert s1_detail["report"] is not None, "Report should be unlocked for student after approval"
    assert s1_detail["metadata"]["status"] == "Approved", f"Expected Approved, got {s1_detail['metadata']['status']}"
    print("OK: Student 1 can now view the unlocked report and status is 'Approved'.")

    print("\nTeacher Dashboard & RBAC Workflow Test Completed Successfully!")

if __name__ == "__main__":
    run_teacher_dashboard_test()
