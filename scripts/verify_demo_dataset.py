"""
Comprehensive Demonstration Dataset Verification Script
Extracts all metrics for the 15-point verification report.
"""
import os
import sys
import json
import sqlite3

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database.connection import SessionLocal
from backend.database.models import User, Section, Assignment, Submission, AnalysisResult, SimilarityPair

def verify_dataset():
    db = SessionLocal()
    try:
        print("=== 1. BACKUP VERIFICATION ===")
        backup_dir = r"c:\Users\mbgra\Desktop\codeguard_backups"
        backups = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith(".db")]
        latest_backup = sorted(backups)[-1]
        print(f"Backup File: {latest_backup} ({os.path.getsize(latest_backup):,} bytes)")
        b_conn = sqlite3.connect(latest_backup)
        b_cur = b_conn.cursor()
        b_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        b_tables = [r[0] for r in b_cur.fetchall()]
        print(f"Backup Tables: {b_tables}")
        b_conn.close()

        print("\n=== 2. USER COUNTS BY ROLE ===")
        users = db.query(User).all()
        by_role = {}
        for u in users:
            by_role[u.role] = by_role.get(u.role, 0) + 1
        for role, count in sorted(by_role.items()):
            print(f"  {role}: {count}")
        print(f"Total Users: {len(users)}")

        print("\n=== 3. SECTION COUNTS ===")
        sections = db.query(Section).all()
        for s in sections:
            print(f"  ID {s.id}: Section {s.section_name}")
        print(f"Total Sections: {len(sections)}")

        print("\n=== 4. ASSIGNMENT LIST ===")
        asgns = db.query(Assignment).all()
        for a in asgns:
            print(f"  ID {a.assignment_id}: {a.title} ({a.course})")
        print(f"Total Assignments: {len(asgns)}")

        print("\n=== 5. SUBMISSIONS BY ASSIGNMENT AND SECTION ===")
        for a in asgns:
            print(f"  Assignment {a.assignment_id} ({a.title}):")
            for s in sections:
                cnt = db.query(Submission).filter(
                    Submission.assignment_id == a.assignment_id,
                    Submission.section_id == s.id
                ).count()
                print(f"    Section {s.section_name}: {cnt} submissions")
        total_subs = db.query(Submission).count()
        print(f"Total Submissions: {total_subs}")

        print("\n=== 6. ANALYSIS RESULTS CREATED ===")
        ar_count = db.query(AnalysisResult).count()
        print(f"Total Analysis Results: {ar_count}")

        print("\n=== 7. SIMILARITY COMPARISONS CREATED ===")
        sim_count = db.query(SimilarityPair).count()
        print(f"Total Similarity Pairs: {sim_count}")

        print("\n=== 8. SUBMISSIONS WITH FAILED ANALYSIS ===")
        failed_subs = db.query(Submission).filter(Submission.status == "Failed").count()
        print(f"Failed Submissions: {failed_subs}")

        print("\n=== 9. AI DETECTOR OUTPUT DISTRIBUTION ===")
        ai_scores = [r.ai_score for r in db.query(AnalysisResult).all() if r.ai_score is not None]
        print(f"Scores Count: {len(ai_scores)}")
        print(f"Min AI Score: {min(ai_scores):.4f}")
        print(f"Max AI Score: {max(ai_scores):.4f}")
        print(f"Mean AI Score: {sum(ai_scores)/len(ai_scores):.4f}")
        high_ai = sum(1 for s in ai_scores if s >= 0.54)
        med_ai = sum(1 for s in ai_scores if 0.27 <= s < 0.54)
        low_ai = sum(1 for s in ai_scores if s < 0.27)
        print(f"Tiers (Threshold=0.54):")
        print(f"  Flagged for Review (>= 0.54): {high_ai}")
        print(f"  Optional Review (0.27 - 0.54): {med_ai}")
        print(f"  Routine Structure (< 0.27): {low_ai}")

        print("\n=== 10. PLAGIARISM SIMILARITY DISTRIBUTION ===")
        fusions = [p.fusion for p in db.query(SimilarityPair).all() if p.fusion is not None]
        print(f"Pairs Count: {len(fusions)}")
        print(f"Min Fusion: {min(fusions):.4f}")
        print(f"Max Fusion: {max(fusions):.4f}")
        print(f"Mean Fusion: {sum(fusions)/len(fusions):.4f}")
        high_plag = sum(1 for f in fusions if f >= 0.75)
        med_plag = sum(1 for f in fusions if 0.50 <= f < 0.75)
        low_plag = sum(1 for f in fusions if f < 0.50)
        print(f"Tiers (Threshold=0.75):")
        print(f"  High Similarity / Flagged (>= 0.75): {high_plag}")
        print(f"  Moderate Similarity (0.50 - 0.75): {med_plag}")
        print(f"  Baseline / Low Similarity (< 0.50): {low_plag}")

        print("\n=== 11. CODE QUALITY RESULTS AVAILABILITY ===")
        valid_quality = 0
        for r in db.query(AnalysisResult).all():
            if r.quality_score:
                try:
                    q = json.loads(r.quality_score)
                    if "maintainability_index" in q or "overall_score" in q or "cyclomatic_complexity" in q:
                        valid_quality += 1
                except Exception:
                    pass
        print(f"Submissions with Valid Quality Metrics: {valid_quality} / {total_subs}")

        print("\n=== 12. PENDING IDENTIFICATION COUNT ===")
        pending = db.query(Submission).filter(
            (Submission.student_id.is_(None)) | (Submission.status == "Awaiting Student Identification")
        ).count()
        print(f"Pending Identification Submissions: {pending}")

        print("\n=== 13. RBAC & STUDENT OWNERSHIP ===")
        prof = db.query(User).filter(User.username == "professor").first()
        prof_sec_ids = [s.id for s in prof.sections] if prof else []
        print(f"Professor assigned section IDs: {prof_sec_ids} (Section {[s.section_name for s in prof.sections]})")
        # Check that all student submissions are correctly owned by their corresponding student
        mismatched = 0
        for sub in db.query(Submission).all():
            if not sub.student or sub.student.role != "Student":
                mismatched += 1
        print(f"Mismatched or Unowned Submissions: {mismatched}")

    finally:
        db.close()

if __name__ == "__main__":
    verify_dataset()
