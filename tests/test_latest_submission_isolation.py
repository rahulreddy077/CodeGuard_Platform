import pytest
from datetime import datetime, timedelta
from backend.database.connection import SessionLocal, Base, engine
from backend.database.models import User, Assignment, Submission, SimilarityPair
from backend.database import crud
from backend.services.similarity import SimilarityService

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_latest_submission_and_self_pair_isolation(db_session):
    # 1. Create a dedicated assignment
    asgn = db_session.query(Assignment).filter(Assignment.assignment_id == 8888).first()
    if not asgn:
        asgn = Assignment(assignment_id=8888, course="CS101", title="Draft Isolation Test Lab", due_date=datetime.utcnow())
        db_session.add(asgn)

    # 2. Create Student 1 and Student 2
    s1 = db_session.query(User).filter(User.username == "draft_student_1").first()
    if not s1:
        s1 = User(username="draft_student_1", email="s1@test.com", password_hash="dummy", role="Student")
        db_session.add(s1)

    s2 = db_session.query(User).filter(User.username == "draft_student_2").first()
    if not s2:
        s2 = User(username="draft_student_2", email="s2@test.com", password_hash="dummy", role="Student")
        db_session.add(s2)
        
    db_session.commit()

    # Clean existing submissions for assignment 8888 to ensure test isolation
    db_session.query(Submission).filter(Submission.assignment_id == 8888).delete()
    db_session.commit()

    now = datetime.utcnow()
    t1 = now - timedelta(hours=3)
    t2 = now - timedelta(hours=2)
    t3 = now - timedelta(hours=1)
    t4 = now

    # 3. Create 3 submissions for Student 1 at t1, t2, t3 (drafts history)
    sub_s1_draft1 = Submission(
        student_id=s1.id,
        assignment_id=asgn.assignment_id,
        section_id=1,
        file_name="draft1.py",
        language="python",
        raw_code="def calc(x):\n    return x + 1\n",
        status="Completed",
        submitted_at=t1
    )
    sub_s1_draft2 = Submission(
        student_id=s1.id,
        assignment_id=asgn.assignment_id,
        section_id=1,
        file_name="draft2.py",
        language="python",
        raw_code="def calc(x):\n    return x + 2\n",
        status="Completed",
        submitted_at=t2
    )
    sub_s1_latest = Submission(
        student_id=s1.id,
        assignment_id=asgn.assignment_id,
        section_id=1,
        file_name="final_solution.py",
        language="python",
        raw_code="def calc(x):\n    return x * 10\n",
        status="Completed",
        submitted_at=t3
    )

    # 4. Create 1 submission for Student 2 at t4
    sub_s2 = Submission(
        student_id=s2.id,
        assignment_id=asgn.assignment_id,
        section_id=1,
        file_name="s2_solution.py",
        language="python",
        raw_code="def calc(x):\n    return x * 10\n",  # Identical to Student 1's latest
        status="Completed",
        submitted_at=t4
    )

    db_session.add(sub_s1_draft1)
    db_session.add(sub_s1_draft2)
    db_session.add(sub_s1_latest)
    db_session.add(sub_s2)
    db_session.commit()

    # 5. Verify get_latest_submissions helper
    latest_subs = crud.get_latest_submissions(db_session, asgn.assignment_id)
    latest_ids = {s.submission_id for s in latest_subs}

    assert len(latest_subs) == 2, f"Expected 2 latest submissions (1 for Student 1, 1 for Student 2), got {len(latest_subs)}"
    assert sub_s1_latest.submission_id in latest_ids, "Student 1's latest submission must be selected"
    assert sub_s2.submission_id in latest_ids, "Student 2's latest submission must be selected"
    assert sub_s1_draft1.submission_id not in latest_ids, "Student 1's draft 1 must be excluded"
    assert sub_s1_draft2.submission_id not in latest_ids, "Student 1's draft 2 must be excluded"

    # 6. Verify self-comparison rejection logic
    with pytest.raises(ValueError) as exc_info:
        SimilarityService.compare_submissions(db_session, sub_s1_draft1, sub_s1_latest)
    assert "Self-comparison similarity rejected" in str(exc_info.value)
