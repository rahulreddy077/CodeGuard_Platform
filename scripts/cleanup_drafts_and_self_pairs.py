import os
import sys
import logging

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import SessionLocal
from backend.database.models import Submission, SimilarityPair, Assignment
from backend.database import crud
from backend.services.similarity import SimilarityService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("draft_cleanup")

def cleanup_drafts_and_self_pairs():
    db = SessionLocal()
    try:
        logger.info("=== 1. Starting database cleanup for self-pairs and non-latest draft pairs ===")
        all_pairs = db.query(SimilarityPair).all()
        
        deleted_self_count = 0
        deleted_draft_count = 0
        deleted_cross_asgn_count = 0
        
        # Build lookup table of latest submission IDs for every (student_id, assignment_id) pair
        assignments = db.query(Assignment).all()
        latest_sub_id_set = set()
        for asgn in assignments:
            latest_subs = crud.get_latest_submissions(db, asgn.assignment_id)
            for s in latest_subs:
                latest_sub_id_set.add(s.submission_id)

        for p in all_pairs:
            sub1 = db.query(Submission).filter(Submission.submission_id == p.submission1).first()
            sub2 = db.query(Submission).filter(Submission.submission_id == p.submission2).first()
            
            if not sub1 or not sub2:
                db.delete(p)
                deleted_draft_count += 1
                continue
                
            # 1. Self-comparison check (same student)
            if sub1.student_id == sub2.student_id:
                db.delete(p)
                deleted_self_count += 1
                continue
                
            # 2. Cross-assignment check
            if sub1.assignment_id != sub2.assignment_id:
                db.delete(p)
                deleted_cross_asgn_count += 1
                continue
                
            # 3. Non-latest draft check (must be latest for both students)
            if sub1.submission_id not in latest_sub_id_set or sub2.submission_id not in latest_sub_id_set:
                db.delete(p)
                deleted_draft_count += 1
                continue
                
        db.commit()
        logger.info(
            f"Database cleanup complete: "
            f"Deleted {deleted_self_count} self-pairs, "
            f"Deleted {deleted_draft_count} older draft pairs, "
            f"Deleted {deleted_cross_asgn_count} cross-assignment pairs."
        )

        logger.info("=== 2. Recomputing pairwise similarity across latest student submissions ===")
        recomputed_count = 0
        
        for asgn in assignments:
            latest_subs = crud.get_latest_submissions(db, asgn.assignment_id)
            logger.info(f"Assignment #{asgn.assignment_id} ({asgn.title}) - Recomputing across {len(latest_subs)} latest student submissions...")
            
            for i in range(len(latest_subs)):
                for j in range(i + 1, len(latest_subs)):
                    if latest_subs[i].student_id == latest_subs[j].student_id:
                        continue
                    try:
                        SimilarityService.compare_submissions(db, latest_subs[i], latest_subs[j])
                        recomputed_count += 1
                    except Exception as e:
                        logger.error(f"Error recomputing sub #{latest_subs[i].submission_id} vs #{latest_subs[j].submission_id}: {str(e)}")
                        
        db.commit()
        print(f"[CLEANUP SUCCESS] Deleted {deleted_self_count} self-pairs, {deleted_draft_count} draft pairs, and {deleted_cross_asgn_count} cross-assignment pairs.")
        print(f"[CLEANUP SUCCESS] Recomputed {recomputed_count} clean pairwise similarity records across latest student submissions.")
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_drafts_and_self_pairs()
