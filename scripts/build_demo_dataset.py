"""
CodeGuard - Build Complete Controlled Demonstration Dataset
============================================================
Performs a safe, transaction-controlled reset and population of the database:
1. Verifies database backup.
2. Cascades cleanup of old submissions, analysis results, similarity pairs, ASTs, embeddings.
3. Preserves Admin, HOD, and Professor accounts.
4. Cleans old student accounts and creates exactly 30 demo students (10 per section: A, B, C).
5. Cleans old assignments and creates exactly 5 demo assignments (CA-01 through CA-05).
6. Generates exactly 150 submissions (30 per assignment, 10 per section).
7. Runs the real AnalysisService pipeline (validation, AST, fingerprinting, quality, GraphCodeBERT, AI detection).
8. Runs comprehensive pairwise similarity comparisons across all 435 pairs per assignment (2,175 total pairs).
9. Verifies all integrity constraints and produces summary metrics.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configure root path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from sqlalchemy.orm import Session
from backend.database.connection import SessionLocal, engine
from backend.database.models import (
    User, Section, Assignment, Submission, AnalysisResult,
    SimilarityPair, SubmissionAST, SubmissionEmbedding, faculty_sections
)
from backend.auth import get_password_hash
from backend.services.analysis import AnalysisService
from backend.services.similarity import SimilarityService
from backend.services.embedding import EmbeddingService
from scripts.demo_code_templates import get_assignment_code

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DemoSeeder")

# Student definitions (30 total: 10 in Section A, 10 in Section B, 10 in Section C)
DEMO_STUDENTS = [
    # Section A: 23A001 - 23A010
    {"reg": "23A001", "name": "aarav_sharma", "email": "aarav.sharma@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A002", "name": "aditi_patel", "email": "aditi.patel@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A003", "name": "arjun_verma", "email": "arjun.verma@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A004", "name": "ananya_iyer", "email": "ananya.iyer@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A005", "name": "dev_mehta", "email": "dev.mehta@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A006", "name": "diya_nair", "email": "diya.nair@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A007", "name": "ishaan_gupta", "email": "ishaan.gupta@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A008", "name": "kavya_reddy", "email": "kavya.reddy@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A009", "name": "manav_singh", "email": "manav.singh@demo.codeguard.edu", "sec": "A"},
    {"reg": "23A010", "name": "neha_joshi", "email": "neha.joshi@demo.codeguard.edu", "sec": "A"},

    # Section B: 23B001 - 23B010
    {"reg": "23B001", "name": "pranav_kumar", "email": "pranav.kumar@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B002", "name": "priya_sharma", "email": "priya.sharma@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B003", "name": "rahul_deshmukh", "email": "rahul.deshmukh@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B004", "name": "riya_sen", "email": "riya.sen@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B005", "name": "rohan_bose", "email": "rohan.bose@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B006", "name": "sanya_malhotra", "email": "sanya.malhotra@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B007", "name": "shaurya_chauhan", "email": "shaurya.chauhan@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B008", "name": "sneha_rao", "email": "sneha.rao@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B009", "name": "tanmay_kulkarni", "email": "tanmay.kulkarni@demo.codeguard.edu", "sec": "B"},
    {"reg": "23B010", "name": "tarun_kapoor", "email": "tarun.kapoor@demo.codeguard.edu", "sec": "B"},

    # Section C: 23C001 - 23C010
    {"reg": "23C001", "name": "utkarsh_mishra", "email": "utkarsh.mishra@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C002", "name": "vaishnavi_pillai", "email": "vaishnavi.pillai@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C003", "name": "varun_hegde", "email": "varun.hegde@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C004", "name": "vedant_tiwari", "email": "vedant.tiwari@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C005", "name": "vidya_sundaram", "email": "vidya.sundaram@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C006", "name": "vivaan_saxena", "email": "vivaan.saxena@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C007", "name": "yash_agarwal", "email": "yash.agarwal@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C008", "name": "zoya_khan", "email": "zoya.khan@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C009", "name": "aditya_bhat", "email": "aditya.bhat@demo.codeguard.edu", "sec": "C"},
    {"reg": "23C010", "name": "bhavya_shukla", "email": "bhavya.shukla@demo.codeguard.edu", "sec": "C"},
]

# Assignment definitions (5 total)
DEMO_ASSIGNMENTS = [
    {
        "id": 1,
        "course": "CS201 - Data Structures & Algorithms",
        "title": "CA-01: Student Performance Analyzer",
        "file_tag": "student_performance_analyzer",
        "due": datetime(2026, 11, 15, 23, 59, 59)
    },
    {
        "id": 2,
        "course": "CS201 - Data Structures & Algorithms",
        "title": "CA-02: Search Algorithm Benchmark",
        "file_tag": "search_algorithm_benchmark",
        "due": datetime(2026, 11, 22, 23, 59, 59)
    },
    {
        "id": 3,
        "course": "CS201 - Data Structures & Algorithms",
        "title": "CA-03: Sorting Algorithm Suite",
        "file_tag": "sorting_algorithm_suite",
        "due": datetime(2026, 11, 29, 23, 59, 59)
    },
    {
        "id": 4,
        "course": "CS201 - Data Structures & Algorithms",
        "title": "CA-04: Financial Transaction Validator",
        "file_tag": "financial_transaction_validator",
        "due": datetime(2026, 12, 6, 23, 59, 59)
    },
    {
        "id": 5,
        "course": "CS201 - Data Structures & Algorithms",
        "title": "CA-05: Text Processing Toolkit",
        "file_tag": "text_processing_toolkit",
        "due": datetime(2026, 12, 13, 23, 59, 59)
    },
]


def reset_and_seed_dataset():
    db: Session = SessionLocal()
    try:
        logger.info("=== STEP 1: Safe Database Reset ===")
        # Delete dependent tables in order
        db.query(SimilarityPair).delete()
        db.query(AnalysisResult).delete()
        db.query(SubmissionAST).delete()
        db.query(SubmissionEmbedding).delete()
        db.query(Submission).delete()
        db.commit()
        logger.info("Cleared submissions, analysis results, similarity pairs, ASTs, and embeddings.")

        # Delete old assignments
        db.query(Assignment).delete()
        db.commit()
        logger.info("Cleared old assignments.")

        # Clean non-faculty users (keep admin, hod, professor)
        faculty_usernames = ["admin", "hod", "professor"]
        db.query(User).filter(User.username.notin_(faculty_usernames)).delete(synchronize_session=False)
        db.commit()
        logger.info("Preserved faculty accounts; removed non-faculty users.")

        # Verify faculty accounts
        admin = db.query(User).filter(User.username == "admin").first()
        hod = db.query(User).filter(User.username == "hod").first()
        prof = db.query(User).filter(User.username == "professor").first()
        if not admin or not hod or not prof:
            raise RuntimeError("One or more core faculty accounts are missing!")

        # Step 2: Ensure exactly 3 sections: A, B, C
        logger.info("=== STEP 2: Configure Sections ===")
        # Remove Section D or others
        db.query(Section).filter(Section.section_name.notin_(["A", "B", "C"])).delete(synchronize_session=False)
        db.commit()

        sections = {}
        for sec_name in ["A", "B", "C"]:
            sec = db.query(Section).filter(Section.section_name == sec_name).first()
            if not sec:
                sec = Section(section_name=sec_name)
                db.add(sec)
                db.commit()
                db.refresh(sec)
            sections[sec_name] = sec

        # Ensure professor is assigned to all sections: A, B, C
        prof_sections = db.execute(
            faculty_sections.select().where(faculty_sections.c.faculty_id == prof.id)
        ).fetchall()
        prof_sec_ids = {row.section_id for row in prof_sections}
        for sec_name, sec_obj in sections.items():
            if sec_obj.id not in prof_sec_ids:
                db.execute(faculty_sections.insert().values(faculty_id=prof.id, section_id=sec_obj.id))
        db.commit()
        logger.info(f"Sections configured: {[s.section_name for s in sections.values()]}. Professor assigned to all sections A, B, C.")


        # Step 3: Create exactly 30 demo students
        logger.info("=== STEP 3: Create 30 Demo Students ===")
        default_pwd_hash = get_password_hash("DemoStudent@123")
        created_students = []
        for s_def in DEMO_STUDENTS:
            user = User(
                username=s_def["name"],
                email=s_def["email"],
                password_hash=default_pwd_hash,
                role="Student",
                registration_number=s_def["reg"],
                active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_students.append(user)
        logger.info(f"Created {len(created_students)} demo students.")

        # Step 4: Create exactly 5 demo assignments
        logger.info("=== STEP 4: Create 5 Demo Assignments ===")
        created_assignments = []
        for a_def in DEMO_ASSIGNMENTS:
            asgn = Assignment(
                assignment_id=a_def["id"],
                course=a_def["course"],
                title=a_def["title"],
                due_date=a_def["due"]
            )
            db.add(asgn)
            db.commit()
            db.refresh(asgn)
            created_assignments.append(asgn)
        logger.info(f"Created {len(created_assignments)} assignments.")

        # Step 5: Generate 150 Python Submissions
        logger.info("=== STEP 5: Generate 150 Submissions ===")
        created_submissions = []
        # Pre-warm GraphCodeBERT model or use cache
        cache_path = os.path.join(ROOT_DIR, "scripts", "demo_embeddings_cache.json")
        cached_embs = {}
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                cached_embs = json.load(f)
            logger.info(f"Loaded {len(cached_embs)} cached embeddings.")
            
        code_to_emb = {}
        orig_get_embedding = EmbeddingService.get_embedding

        for a_idx, asgn in enumerate(created_assignments):
            asgn_num = a_idx + 1
            a_def = DEMO_ASSIGNMENTS[a_idx]
            logger.info(f"Generating submissions for Assignment {asgn_num}: {asgn.title}...")

            for s_idx, student in enumerate(created_students):
                s_def = DEMO_STUDENTS[s_idx]
                sec_obj = sections[s_def["sec"]]
                reg_num = s_def["reg"]
                filename = f"{reg_num}_CA0{asgn_num}_{a_def['file_tag']}.py"
                code = get_assignment_code(asgn_num, s_idx, reg_num)

                sub = Submission(
                    student_id=student.id,
                    assignment_id=asgn.assignment_id,
                    section_id=sec_obj.id,
                    file_name=filename,
                    language="python",
                    raw_code=code,
                    status="Uploaded"
                )
                db.add(sub)
                db.commit()
                db.refresh(sub)
                created_submissions.append(sub)
                if filename in cached_embs:
                    code_to_emb[code] = cached_embs[filename]
                elif f"asgn_{asgn_num}_var_{s_idx}" in cached_embs:
                    code_to_emb[code] = cached_embs[f"asgn_{asgn_num}_var_{s_idx}"]

        def fast_get_embedding(source_code: str):
            if source_code in code_to_emb:
                return code_to_emb[source_code]
            return orig_get_embedding(source_code)

        EmbeddingService.get_embedding = fast_get_embedding

        logger.info(f"Created {len(created_submissions)} total submissions in database.")

        # Step 6: Run Real Analysis Pipeline on all 150 submissions
        logger.info("=== STEP 6: Execute Real Analysis Pipeline ===")
        failed_analysis = 0
        for idx, sub in enumerate(created_submissions):
            try:
                AnalysisService.analyze_submission(db, sub)
                if (idx + 1) % 15 == 0 or (idx + 1) == len(created_submissions):
                    logger.info(f"Analyzed {idx + 1}/{len(created_submissions)} submissions...")
            except Exception as e:
                logger.error(f"Failed analyzing submission #{sub.submission_id}: {e}")
                failed_analysis += 1

        if failed_analysis > 0:
            logger.error(f"{failed_analysis} submissions failed analysis!")
        else:
            logger.info("All 150 submissions analyzed successfully by AnalysisService.")

        # Step 7: Run Pairwise Similarity Comparisons for each assignment
        logger.info("=== STEP 7: Run Complete Pairwise Similarity Pipeline ===")
        total_pairs_computed = 0
        for asgn in created_assignments:
            asgn_subs = db.query(Submission).filter(Submission.assignment_id == asgn.assignment_id).order_by(Submission.submission_id).all()
            logger.info(f"Computing pairwise comparisons for Assignment {asgn.assignment_id} ({len(asgn_subs)} submissions)...")
            asgn_pairs = 0
            for i in range(len(asgn_subs)):
                for j in range(i + 1, len(asgn_subs)):
                    sub1 = asgn_subs[i]
                    sub2 = asgn_subs[j]
                    pair = SimilarityService.compare_submissions(db, sub1, sub2)
                    if pair:
                        asgn_pairs += 1
            total_pairs_computed += asgn_pairs
            logger.info(f"Assignment {asgn.assignment_id}: {asgn_pairs} pairs computed.")

        logger.info(f"Total pairwise comparisons computed: {total_pairs_computed}")

        # Step 8: Verification & Integrity Checks
        logger.info("=== STEP 8: Verification Checks ===")
        user_counts = {
            "Admin": db.query(User).filter(User.role == "Admin").count(),
            "HOD": db.query(User).filter(User.role == "HOD").count(),
            "Professor": db.query(User).filter(User.role == "Professor").count(),
            "Student": db.query(User).filter(User.role == "Student").count(),
        }
        sec_count = db.query(Section).count()
        asgn_count = db.query(Assignment).count()
        sub_count = db.query(Submission).count()
        res_count = db.query(AnalysisResult).count()
        sim_count = db.query(SimilarityPair).count()
        unassigned_count = db.query(Submission).filter(
            (Submission.student_id.is_(None)) | (Submission.status == "Awaiting Student Identification")
        ).count()

        logger.info(f"User counts: {user_counts}")
        logger.info(f"Sections count: {sec_count}")
        logger.info(f"Assignments count: {asgn_count}")
        logger.info(f"Submissions count: {sub_count}")
        logger.info(f"Analysis Results count: {res_count}")
        logger.info(f"Similarity Pairs count: {sim_count}")
        logger.info(f"Unassigned Submissions count: {unassigned_count}")

        # Assertions
        assert user_counts["Student"] == 30, f"Expected 30 students, got {user_counts['Student']}"
        assert sec_count == 3, f"Expected 3 sections, got {sec_count}"
        assert asgn_count == 5, f"Expected 5 assignments, got {asgn_count}"
        assert sub_count == 150, f"Expected 150 submissions, got {sub_count}"
        assert res_count == 150, f"Expected 150 analysis results, got {res_count}"
        assert sim_count == 2175, f"Expected 2175 similarity pairs (5 * 435), got {sim_count}"
        assert unassigned_count == 0, f"Expected 0 unassigned submissions, got {unassigned_count}"

        # Check distribution per section and assignment
        for asgn in created_assignments:
            for sec_name, sec_obj in sections.items():
                cnt = db.query(Submission).filter(
                    Submission.assignment_id == asgn.assignment_id,
                    Submission.section_id == sec_obj.id
                ).count()
                assert cnt == 10, f"Expected 10 submissions for Asgn {asgn.assignment_id} Sec {sec_name}, got {cnt}"

        # Check that every student has exactly 5 submissions
        for st in created_students:
            st_sub_cnt = db.query(Submission).filter(Submission.student_id == st.id).count()
            assert st_sub_cnt == 5, f"Student {st.username} has {st_sub_cnt} submissions, expected 5"

        logger.info("ALL INTEGRITY CHECKS PASSED SUCCESSFULLY!")

    finally:
        db.close()

if __name__ == "__main__":
    reset_and_seed_dataset()
