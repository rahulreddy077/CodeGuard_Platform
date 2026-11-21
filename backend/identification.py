"""
CodeGuard - Intelligent Student Identification Service
=====================================================
Extracts and matches student registration numbers from filenames during bulk upload.
Handles ambiguous or unrecognized filenames without guessing.
"""

import os
import re
import logging
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from backend.database.models import User

logger = logging.getLogger(__name__)


def extract_candidate_reg_numbers(filename: str) -> List[str]:
    """
    Extracts candidate registration number tokens from a filename stem.
    Looks for alphanumeric tokens with mixed letters and numbers or standard university formats.
    """
    stem = os.path.splitext(filename)[0]
    # Split on common delimiters: _, -, space, ., [, ], (, )
    tokens = re.split(r'[^A-Za-z0-9]+', stem)
    candidates = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        # Tokens with at least 4 characters containing both digits and letters (e.g., 22BCE1234, RA211100, CS2024)
        if len(token) >= 4 and re.search(r'[0-9]', token) and re.search(r'[A-Za-z]', token):
            candidates.append(token)
    return candidates


def identify_student_from_filename(
    filename: str,
    db: Session,
    eligible_students: Optional[List[User]] = None
) -> Tuple[Optional[User], Optional[str]]:
    """
    Identifies a single student from a filename based on registration number (primary)
    or username (secondary).

    Returns:
        (User, None) if exactly one student is unambiguously identified.
        (None, reason_str) if identification failed (unrecognized, ambiguous, or no students).
    """
    if eligible_students is None:
        eligible_students = db.query(User).filter(User.role == "Student", User.active == True).all()

    if not eligible_students:
        return None, "No active student records found in database"

    stem = os.path.splitext(filename)[0]

    # --- Pass 1: Match by Registration Number ---
    matched_by_reg = []
    for student in eligible_students:
        if not student.registration_number:
            continue
        reg = student.registration_number.strip()
        # Word boundary / non-alphanumeric delimiter match
        pattern = r'(?<![A-Za-z0-9])' + re.escape(reg) + r'(?![A-Za-z0-9])'
        if re.search(pattern, stem, re.IGNORECASE):
            matched_by_reg.append(student)

    if len(matched_by_reg) == 1:
        logger.info(f"[Identification] Unambiguously matched '{filename}' to student '{matched_by_reg[0].username}' via registration number '{matched_by_reg[0].registration_number}'")
        return matched_by_reg[0], None
    elif len(matched_by_reg) > 1:
        reg_list = ", ".join(s.registration_number for s in matched_by_reg)
        reason = f"Ambiguous filename: matches multiple student registration numbers ({reg_list})"
        logger.warning(f"[Identification] '{filename}' is ambiguous: {reason}")
        return None, reason

    # --- Pass 2: Match by Student Username ---
    matched_by_user = []
    for student in eligible_students:
        if not student.username:
            continue
        uname = student.username.strip()
        pattern = r'(?<![A-Za-z0-9])' + re.escape(uname) + r'(?![A-Za-z0-9])'
        if re.search(pattern, stem, re.IGNORECASE):
            matched_by_user.append(student)

    if len(matched_by_user) == 1:
        logger.info(f"[Identification] Matched '{filename}' to student '{matched_by_user[0].username}' via username")
        return matched_by_user[0], None
    elif len(matched_by_user) > 1:
        user_list = ", ".join(s.username for s in matched_by_user)
        reason = f"Ambiguous filename: matches multiple student usernames ({user_list})"
        logger.warning(f"[Identification] '{filename}' is ambiguous: {reason}")
        return None, reason

    # --- Pass 3: Diagnosis of failure ---
    candidate_tokens = extract_candidate_reg_numbers(filename)
    if candidate_tokens:
        token = candidate_tokens[0]
        any_user = db.query(User).filter(User.registration_number.ilike(token)).first()
        if any_user:
            if not any_user.active:
                reason = f"Student '{any_user.username}' ({token}) is inactive and not eligible for this assignment"
            elif any_user.role != "Student":
                reason = f"Registration number '{token}' belongs to a non-student user ({any_user.role})"
            else:
                reason = f"Student '{any_user.username}' ({token}) is not eligible for this assignment"
        else:
            reason = f"Unknown registration number '{token}': no matching student record found in database"
    else:
        reason = "No recognizable student registration number found in filename"

    logger.info(f"[Identification] '{filename}' flagged: {reason}")
    return None, reason
