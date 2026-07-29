from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import User, Section, Assignment, Submission, AnalysisResult, SimilarityPair, faculty_sections

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, username: str, email: str, password_raw: str, role: str, active: bool = True):
    from backend.auth import get_password_hash
    password_hash = get_password_hash(password_raw)
    db_user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
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

def create_submission(db: Session, student_id: int, assignment_id: int, section_id: int, file_name: str, language: str, raw_code: str):
    db_submission = Submission(
        student_id=student_id,
        assignment_id=assignment_id,
        section_id=section_id,
        file_name=file_name,
        language=language,
        raw_code=raw_code,
        status="Uploaded"
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
    return db.query(Submission).filter(Submission.section_id.in_(section_ids)).all()

def get_all_submissions(db: Session):
    return db.query(Submission).all()

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

def approve_report(db: Session, submission_id: int, approved_by_id: int):
    result = db.query(AnalysisResult).filter(AnalysisResult.submission_id == submission_id).first()
    if not result:
        result = AnalysisResult(submission_id=submission_id)
        db.add(result)
    
    result.report_visible = True
    result.approved_by = approved_by_id
    result.approved_at = datetime.utcnow()
    
    # Also update submission status
    submission = db.query(Submission).filter(Submission.submission_id == submission_id).first()
    if submission:
        submission.status = "Approved"
        
    db.commit()
    db.refresh(result)
    return result

def seed_data(db: Session):
    # 1. Create default sections
    sections_list = ["A", "B", "C", "D"]
    created_sections = {}
    for sec_name in sections_list:
        sec = get_section_by_name(db, sec_name)
        if not sec:
            sec = create_section(db, sec_name)
        created_sections[sec_name] = sec

    # 2. Create default users if not present
    default_users = [
        ("admin", "admin@codeguard.local", "admin123", "Admin"),
        ("hod", "hod@codeguard.local", "hod123", "HOD"),
        ("professor", "prof@codeguard.local", "prof123", "Professor"),
        ("student", "stud@codeguard.local", "stud123", "Student"),
    ]
    
    created_users = {}
    for username, email, pwd, role in default_users:
        user = get_user_by_username(db, username)
        if not user:
            user = create_user(db, username, email, pwd, role)
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
