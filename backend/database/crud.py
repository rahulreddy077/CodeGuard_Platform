from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import User, Section, Assignment, Submission, AnalysisResult, SimilarityPair, faculty_sections, SubmissionAST, SubmissionEmbedding

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, username: str, email: str, password_raw: str, role: str, registration_number: str = None, active: bool = True):
    from backend.auth import get_password_hash
    password_hash = get_password_hash(password_raw)
    db_user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
        registration_number=registration_number,
        active=active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_section(db: Session, section_name: str):
    db_section = Section(section_name=section_name)
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

def get_section_by_name(db: Session, section_name: str):
    return db.query(Section).filter(Section.section_name == section_name).first()

def get_sections(db: Session):
    return db.query(Section).all()

def assign_section_to_faculty(db: Session, faculty_id: int, section_id: int):
    # Insert directly into faculty_sections association table
    stmt = faculty_sections.insert().values(faculty_id=faculty_id, section_id=section_id)
    db.execute(stmt)
    db.commit()

def create_assignment(db: Session, course: str, title: str, due_date: datetime):
    db_assignment = Assignment(course=course, title=title, due_date=due_date)
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

def get_assignment_by_id(db: Session, assignment_id: int):
    return db.query(Assignment).filter(Assignment.assignment_id == assignment_id).first()

def get_assignments(db: Session):
    return db.query(Assignment).all()

def create_submission(db: Session, student_id: int, assignment_id: int, section_id: int, file_name: str, language: str, raw_code: str, status: str = "Uploaded", unassigned_reason: str = None):
    db_submission = Submission(
        student_id=student_id,
        assignment_id=assignment_id,
        section_id=section_id,
        file_name=file_name,
        language=language,
        raw_code=raw_code,
        status=status,
        unassigned_reason=unassigned_reason
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

def get_submission_by_id(db: Session, submission_id: int):
    return db.query(Submission).filter(Submission.submission_id == submission_id).first()

def get_submissions_by_student(db: Session, student_id: int):
    return db.query(Submission).filter(Submission.student_id == student_id).all()

def get_submissions_for_sections(db: Session, section_ids: list):
    return db.query(Submission).filter(
        Submission.section_id.in_(section_ids),
        Submission.student_id.isnot(None),
        Submission.status != "Awaiting Student Identification"
    ).all()

def get_all_submissions(db: Session):
    return db.query(Submission).filter(
        Submission.student_id.isnot(None),
        Submission.status != "Awaiting Student Identification"
    ).all()

def get_latest_submissions(db: Session, assignment_id: int):
    """
    Returns exactly one submission per student for the specified assignment_id —
    the submission with the maximum submitted_at timestamp (and maximum submission_id as tiebreaker),
    excluding all older drafts by that student for that assignment.
    """
    submissions = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id.isnot(None),
        Submission.status != "Failed",
        Submission.status != "Awaiting Student Identification"
    ).order_by(Submission.submitted_at.desc(), Submission.submission_id.desc()).all()

    latest_by_student = {}
    for sub in submissions:
        if sub.student_id not in latest_by_student:
            latest_by_student[sub.student_id] = sub

    return list(latest_by_student.values())

def create_or_update_analysis_result(db: Session, submission_id: int, plagiarism: str = None, ai_score: float = None, quality_score: str = None):
    result = db.query(AnalysisResult).filter(AnalysisResult.submission_id == submission_id).first()
    if not result:
        result = AnalysisResult(submission_id=submission_id)
        db.add(result)
    
    if plagiarism is not None:
        result.plagiarism = plagiarism
    if ai_score is not None:
        result.ai_score = ai_score
    if quality_score is not None:
        result.quality_score = quality_score
        
    db.commit()
    db.refresh(result)
    return result

def approve_report(db: Session, submission_id: int, approved_by_id: int, approve: bool = True):
    result = db.query(AnalysisResult).filter(AnalysisResult.submission_id == submission_id).first()
    if not result:
        result = AnalysisResult(submission_id=submission_id)
        db.add(result)
    
    submission = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    
    if approve:
        result.approved_by = approved_by_id
        if not result.approved_at:
            result.approved_at = datetime.utcnow()
        result.report_visible = True
        if submission:
            submission.status = "Approved"
    else:
        result.approved_by = None
        result.approved_at = None
        if submission:
            if result.report_visible:
                submission.status = "Released"
            else:
                submission.status = "Faculty Review"
            
    db.commit()
    db.refresh(result)
    return result

def release_report(db: Session, submission_id: int, approved_by_id: int, release: bool = True):
    result = db.query(AnalysisResult).filter(AnalysisResult.submission_id == submission_id).first()
    if not result:
        result = AnalysisResult(submission_id=submission_id)
        db.add(result)
        
    submission = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    
    if release:
        result.report_visible = True
        if not result.approved_by:
            result.approved_by = approved_by_id
            result.approved_at = datetime.utcnow()
        if submission:
            submission.status = "Released"
    else:
        result.report_visible = False
        if submission:
            if result.approved_by:
                submission.status = "Approved"
            else:
                submission.status = "Faculty Review"
                
    db.commit()
    db.refresh(result)
    return result


def seed_data(db: Session):
    try:
        from backend.database.migrations import migrate_submissions_student_id_nullable
        migrate_submissions_student_id_nullable()
    except Exception:
        pass

    # 1. Create default sections
    sections_list = ["A", "B", "C"]
    created_sections = {}
    for sec_name in sections_list:
        sec = get_section_by_name(db, sec_name)
        if not sec:
            sec = create_section(db, sec_name)
        created_sections[sec_name] = sec

    # 2. Create default users if not present
    default_users = [
        ("admin", "admin@codeguard.local", "admin123", "Admin", None),
        ("hod", "hod@codeguard.local", "hod123", "HOD", None),
        ("professor", "prof@codeguard.local", "prof123", "Professor", None),
        ("student", "stud@codeguard.local", "stud123", "Student", "22BCE1234"),
    ]
    
    created_users = {}
    for username, email, pwd, role, reg_no in default_users:
        user = get_user_by_username(db, username)
        if not user:
            user = create_user(db, username, email, pwd, role, registration_number=reg_no)
        elif reg_no and not user.registration_number:
            user.registration_number = reg_no
            db.commit()
        created_users[role] = user

    # 3. Associate professor with Section A and B
    prof = created_users["Professor"]
    if prof and not prof.sections:
        assign_section_to_faculty(db, prof.id, created_sections["A"].id)
        assign_section_to_faculty(db, prof.id, created_sections["B"].id)

    # 4. Create a default assignment if none exist
    assignments = get_assignments(db)
    if not assignments:
        create_assignment(
            db, 
            course="CS101", 
            title="Factorial Checker", 
            due_date=datetime(2026, 12, 31, 23, 59)
        )


def get_user_by_registration_number(db: Session, reg_no: str):
    if not reg_no:
        return None
    return db.query(User).filter(User.registration_number == reg_no, User.active == True).first()

def get_student_users(db: Session):
    return db.query(User).filter(User.role == "Student", User.active == True).all()

def get_unassigned_submissions(db: Session, assignment_id: int = None, section_ids: list = None):
    q = db.query(Submission).filter(
        (Submission.student_id.is_(None)) | (Submission.status == "Awaiting Student Identification")
    )
    if assignment_id:
        q = q.filter(Submission.assignment_id == assignment_id)
    if section_ids is not None:
        q = q.filter(Submission.section_id.in_(section_ids))
    return q.order_by(Submission.submitted_at.desc()).all()
