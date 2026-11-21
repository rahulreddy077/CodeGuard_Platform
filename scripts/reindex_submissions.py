import os
import sys
import sqlite3
import logging

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.connection import BASE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reindex_submissions")

def reindex_submissions(db_path=None):
    if db_path is None:
        db_path = os.path.join(BASE_DIR, "codeguard.db")
        
    logger.info(f"Connecting to database at {db_path} to re-index submission_ids starting from 1...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Fetch current submission IDs ordered by submission_id
        cursor.execute("SELECT submission_id FROM submissions ORDER BY submission_id ASC;")
        rows = cursor.fetchall()
        old_ids = [r[0] for r in rows]

        if not old_ids:
            logger.info("No submissions found in database.")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
            if cursor.fetchone():
                cursor.execute("INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('submissions', 0);")
            conn.commit()
            return

        logger.info(f"Found {len(old_ids)} submissions with IDs: {old_ids}")

        # Step 1: Temporarily negate all IDs in all tables to prevent primary key conflicts
        cursor.execute("UPDATE submissions SET submission_id = -submission_id;")
        cursor.execute("UPDATE submission_asts SET submission_id = -submission_id;")
        cursor.execute("UPDATE submission_embeddings SET submission_id = -submission_id;")
        cursor.execute("UPDATE analysis_results SET submission_id = -submission_id;")
        cursor.execute("UPDATE similarity_pairs SET submission1 = -submission1;")
        cursor.execute("UPDATE similarity_pairs SET submission2 = -submission2;")

        # Step 2: Map old negative IDs to continuous new IDs (1, 2, 3... N)
        id_map = {}
        for new_id, old_id in enumerate(old_ids, start=1):
            neg_id = -old_id
            id_map[neg_id] = new_id

            cursor.execute("UPDATE submissions SET submission_id = ? WHERE submission_id = ?;", (new_id, neg_id))
            cursor.execute("UPDATE submission_asts SET submission_id = ? WHERE submission_id = ?;", (new_id, neg_id))
            cursor.execute("UPDATE submission_embeddings SET submission_id = ? WHERE submission_id = ?;", (new_id, neg_id))
            cursor.execute("UPDATE analysis_results SET submission_id = ? WHERE submission_id = ?;", (new_id, neg_id))
            cursor.execute("UPDATE similarity_pairs SET submission1 = ? WHERE submission1 = ?;", (new_id, neg_id))
            cursor.execute("UPDATE similarity_pairs SET submission2 = ? WHERE submission2 = ?;", (new_id, neg_id))

        max_new_id = len(old_ids)

        # Step 3: Reset sqlite_sequence auto-increment counter if sqlite_sequence exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
        if cursor.fetchone():
            cursor.execute("INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ('submissions', ?);", (max_new_id,))

        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

        # Fetch and log new submission IDs
        cursor.execute("SELECT submission_id FROM submissions ORDER BY submission_id ASC;")
        new_rows = cursor.fetchall()
        new_ids = [r[0] for r in new_rows]

        logger.info(f"[REINDEX SUCCESS] Successfully re-indexed {len(new_ids)} submissions.")
        logger.info(f"New submission IDs range from 1 to {max_new_id}: {new_ids}")
        print(f"[REINDEX SUCCESS] Re-indexed {len(new_ids)} submissions to continuous range 1..{max_new_id}.")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to re-index submissions: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    reindex_submissions()
