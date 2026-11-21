import os
import sys
import logging
from collections import defaultdict

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import SessionLocal
from backend.database.models import Submission, SimilarityPair
from backend.services.similarity import SimilarityService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("delete_older_submissions")

def delete_older_submissions():
    db = SessionLocal()
    try:
        logger.info("=== Starting removal of duplicate/older student submissions ===")
        all_subs = db.query(Submission).order_by(Submission.submitted_at.desc(), Submission.submission_id.desc()).all()
        
        # Group submissions by (student_id, assignment_id)
        grouped = defaultdict(list)
        for s in all_subs:
            grouped[(s.student_id, s.assignment_id)].append(s)
            
        kept_count = 0
        deleted_count = 0
        
        for key, subs in grouped.items():
            # Latest submission is index 0
            latest = subs[0]
            kept_count += 1
            older_subs = subs[1:]
            
            for old_sub in older_subs:
                logger.info(f"Deleting older submission #{old_sub.submission_id} (Student #{old_sub.student_id}, Assignment #{old_sub.assignment_id}, Submitted: {old_sub.submitted_at})")
                db.delete(old_sub)
                deleted_count += 1
                
        db.commit()
        logger.info(f"Removed {deleted_count} older submissions. Retained {kept_count} latest student submissions.")
        
        # Clean up any remaining invalid or self/cross-assignment similarity pairs
        logger.info("=== Cleaning up similarity pairs table ===")
        all_pairs = db.query(SimilarityPair).all()
        valid_sub_ids = {s.submission_id for s in db.query(Submission).all()}
        
        deleted_pairs_count = 0
        for pair in all_pairs:
            if pair.submission1 not in valid_sub_ids or pair.submission2 not in valid_sub_ids:
                db.delete(pair)
                deleted_pairs_count += 1
                
        db.commit()
        logger.info(f"Cleaned up {deleted_pairs_count} orphaned similarity pairs.")
        
        # Re-verify and sync similarity pairs for the remaining latest submissions
        logger.info("=== Re-evaluating similarity pairs for remaining latest submissions ===")
        assignments_with_subs = set(s.assignment_id for s in db.query(Submission).all())
        recomputed_count = 0
        
        for asgn_id in assignments_with_subs:
            latest_subs = db.query(Submission).filter(Submission.assignment_id == asgn_id).all()
            for i in range(len(latest_subs)):
                for j in range(i + 1, len(latest_subs)):
                    if latest_subs[i].student_id == latest_subs[j].student_id:
                        continue
                    try:
                        SimilarityService.compare_submissions(db, latest_subs[i], latest_subs[j])
                        recomputed_count += 1
                    except Exception as e:
                        logger.error(f"Error comparing sub #{latest_subs[i].submission_id} vs #{latest_subs[j].submission_id}: {e}")
                        
        db.commit()
        print(f"[SUCCESS] Deleted {deleted_count} older submissions across {len(grouped)} student-assignment pairs.")
        print(f"[SUCCESS] Retained {kept_count} latest submissions. Recomputed {recomputed_count} pairwise similarity records.")
        
    finally:
        db.close()

    # Re-index remaining submissions starting from 1 continuously
    from scripts.reindex_submissions import reindex_submissions
    reindex_submissions()

if __name__ == "__main__":
    delete_older_submissions()
