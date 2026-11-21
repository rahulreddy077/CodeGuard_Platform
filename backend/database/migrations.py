import sqlite3
import logging
import os

logger = logging.getLogger("codeguard.migrations")

def migrate_submissions_student_id_nullable(db_path: str = "codeguard.db"):
    """
    Safely migrates the submissions table to make student_id nullable.
    Preserves all existing data, records, and relationships.
    Safe to rerun (idempotent).
    """
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if submissions table exists
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='submissions'")
        table_sql = cursor.fetchone()
        if not table_sql:
            conn.close()
            return

        # Check table_info for submissions
        cursor.execute("PRAGMA table_info(submissions)")
        cols = cursor.fetchall()
        # col tuple: (cid, name, type, notnull, dflt_value, pk)
        student_id_col = None
        has_unassigned_reason = False
        for c in cols:
            if c[1] == "student_id":
                student_id_col = c
            elif c[1] == "unassigned_reason":
                has_unassigned_reason = True

        # If student_id is already nullable and unassigned_reason exists, no migration needed
        if student_id_col and student_id_col[3] == 0 and has_unassigned_reason:
            logger.info("[Migration] submissions table already has nullable student_id and unassigned_reason.")
            conn.close()
            return

        logger.info("[Migration] Migrating submissions table to allow nullable student_id...")

        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("BEGIN TRANSACTION;")

        # Create temporary table with nullable student_id
        cursor.execute("""
        CREATE TABLE submissions_new (
            submission_id INTEGER NOT NULL, 
            student_id INTEGER, 
            assignment_id INTEGER NOT NULL, 
            section_id INTEGER NOT NULL, 
            file_name VARCHAR(100) NOT NULL, 
            language VARCHAR(20) NOT NULL, 
            raw_code TEXT NOT NULL, 
            status VARCHAR(45) DEFAULT 'Uploaded', 
            submitted_at DATETIME, 
            unassigned_reason VARCHAR(200), 
            PRIMARY KEY (submission_id), 
            FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE, 
            FOREIGN KEY(assignment_id) REFERENCES assignments (assignment_id) ON DELETE CASCADE, 
            FOREIGN KEY(section_id) REFERENCES sections (id) ON DELETE CASCADE
        );
        """)

        # Copy data
        if has_unassigned_reason:
            cursor.execute("""
            INSERT INTO submissions_new (
                submission_id, student_id, assignment_id, section_id, file_name, 
                language, raw_code, status, submitted_at, unassigned_reason
            )
            SELECT 
                submission_id, student_id, assignment_id, section_id, file_name, 
                language, raw_code, status, submitted_at, unassigned_reason
            FROM submissions;
            """)
        else:
            cursor.execute("""
            INSERT INTO submissions_new (
                submission_id, student_id, assignment_id, section_id, file_name, 
                language, raw_code, status, submitted_at, unassigned_reason
            )
            SELECT 
                submission_id, student_id, assignment_id, section_id, file_name, 
                language, raw_code, status, submitted_at, NULL
            FROM submissions;
            """)

        cursor.execute("DROP TABLE submissions;")
        cursor.execute("ALTER TABLE submissions_new RENAME TO submissions;")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_submissions_submission_id ON submissions (submission_id);")

        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")
        logger.info("[Migration] Migration completed successfully. Existing records preserved.")
    except Exception as e:
        conn.rollback()
        logger.error(f"[Migration] Migration failed: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_submissions_student_id_nullable()
