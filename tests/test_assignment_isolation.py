import pytest
from datetime import datetime
from backend.database.connection import SessionLocal, Base, engine
from backend.database.models import User, Assignment, Submission, SimilarityPair
from backend.services.similarity import SimilarityService

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_cross_assignment_similarity_rejection(db_session):
    # 1. Create two distinct assignments
    asgn1 = db_session.query(Assignment).filter(Assignment.assignment_id == 9001).first()
    if not asgn1:
        asgn1 = Assignment(assignment_id=9001, course="CS101", title="Lab 1 - Recursion", due_date=datetime.utcnow())
        db_session.add(asgn1)

    asgn2 = db_session.query(Assignment).filter(Assignment.assignment_id == 9002).first()
    if not asgn2:
        asgn2 = Assignment(assignment_id=9002, course="CS101", title="Lab 2 - Trees", due_date=datetime.utcnow())
        db_session.add(asgn2)

    # 2. Create Student 1 and Student 2
    student1 = db_session.query(User).filter(User.username == "test_iso_student1").first()
    if not student1:
        student1 = User(username="test_iso_student1", email="iso1@test.com", password_hash="dummy", role="Student")
        db_session.add(student1)

    student2 = db_session.query(User).filter(User.username == "test_iso_student2").first()
    if not student2:
        student2 = User(username="test_iso_student2", email="iso2@test.com", password_hash="dummy", role="Student")
        db_session.add(student2)
        
    db_session.commit()

    # 3. Create Submission A (Student 1, Assignment 9001) and Submission B (Student 2, Assignment 9002)
    sub_a = Submission(
        student_id=student1.id,
        assignment_id=asgn1.assignment_id,
        section_id=1,
        file_name="lab1_sol.py",
        language="python",
        raw_code="def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)\n",
        status="Completed"
    )
    sub_b = Submission(
        student_id=student2.id,
        assignment_id=asgn2.assignment_id,
        section_id=1,
        file_name="lab2_sol.py",
        language="python",
        raw_code="def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)\n",  # Identical code, different assignment
        status="Completed"
    )
    db_session.add(sub_a)
    db_session.add(sub_b)
    db_session.commit()

    # 4. Assert direct compare_submissions raises ValueError
    with pytest.raises(ValueError) as exc_info:
        SimilarityService.compare_submissions(db_session, sub_a, sub_b)
    assert "Cross-assignment similarity comparison rejected" in str(exc_info.value)

    # 5. Assert run_similarity_checks skips cross-assignment comparisons
    SimilarityService.run_similarity_checks(db_session, sub_a)
    
    id1, id2 = min(sub_a.submission_id, sub_b.submission_id), max(sub_a.submission_id, sub_b.submission_id)
    pair = db_session.query(SimilarityPair).filter(
        SimilarityPair.submission1 == id1,
        SimilarityPair.submission2 == id2
    ).first()
    
    assert pair is None, "SimilarityPair must NEVER be created across different assignments!"

    # 6. Create Submission C for Assignment 9001 under Student 2 and assert similarity pair IS created
    sub_c = Submission(
        student_id=student2.id,
        assignment_id=asgn1.assignment_id,
        section_id=1,
        file_name="lab1_peer.py",
        language="python",
        raw_code="def fibonacci(n):\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)\n",
        status="Completed"
    )
    db_session.add(sub_c)
    db_session.commit()

    SimilarityService.run_similarity_checks(db_session, sub_c)

    id_ac_1, id_ac_2 = min(sub_a.submission_id, sub_c.submission_id), max(sub_a.submission_id, sub_c.submission_id)
    valid_pair = db_session.query(SimilarityPair).filter(
        SimilarityPair.submission1 == id_ac_1,
        SimilarityPair.submission2 == id_ac_2
    ).first()

    assert valid_pair is not None, "Intra-assignment similarity pair should be created for same assignment!"
