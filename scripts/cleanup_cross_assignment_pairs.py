import os
import sys
import logging

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import SessionLocal
from backend.database.models import Submission, SimilarityPair, Assignment
from backend.services.similarity import SimilarityService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup_script")

def cleanup_and_recompute_pairs():
    db = SessionLocal()
    try:
        logger.info("Starting database audit for cross-assignment similarity pairs...")
        all_pairs = db.query(SimilarityPair).all()
        
        deleted_count = 0
        valid_pair_count = 0
        
        for p in all_pairs:
            sub1 = db.query(Submission).filter(Submission.submission_id == p.submission1).first()
            sub2 = db.query(Submission).filter(Submission.submission_id == p.submission2).first()
            
            # Delete if missing submission or different assignment_ids
            if not sub1 or not sub2 or sub1.assignment_id != sub2.assignment_id:
                logger.warning(
                    f"Deleting invalid cross-assignment pair: "
                    f"sub1={p.submission1} (asgn={sub1.assignment_id if sub1 else 'N/A'}) vs "
                    f"sub2={p.submission2} (asgn={sub2.assignment_id if sub2 else 'N/A'})"
                )
                db.delete(p)
                deleted_count += 1
            else:
                valid_pair_count += 1
                
        db.commit()
        logger.info(f"Database cleanup complete: Deleted {deleted_count} invalid cross-assignment pairs. {valid_pair_count} valid pairs retained.")

        # Recompute intra-assignment similarity pairs for all assignments
        assignments = db.query(Assignment).all()
        recomputed_count = 0
        
        for asgn in assignments:
            subs = db.query(Submission).filter(
                Submission.assignment_id == asgn.assignment_id,
                Submission.status != "Failed"
            ).all()
            
            logger.info(f"Recomputing similarity pairs for Assignment #{asgn.assignment_id} ({asgn.title}) - {len(subs)} submissions...")
            
            for i in range(len(subs)):
                for j in range(i + 1, len(subs)):
                    try:
                        SimilarityService.compare_submissions(db, subs[i], subs[j])
                        recomputed_count += 1
                    except Exception as e:
                        logger.error(f"Error recomputing sub #{subs[i].submission_id} vs #{subs[j].submission_id}: {str(e)}")
                        
        db.commit()
        print(f"[CLEANUP SUCCESS] Deleted {deleted_count} invalid cross-assignment similarity pairs.")
        print(f"[CLEANUP SUCCESS] Recomputed {recomputed_count} intra-assignment pairs across {len(assignments)} assignments.")
        
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_and_recompute_pairs()
