from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Table
from sqlalchemy.orm import relationship
from backend.database.connection import Base

# Association table for Faculty and Sections (Many-to-Many)
faculty_sections = Table(
    "faculty_sections",
    Base.metadata,
    Column("faculty_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("section_id", Integer, ForeignKey("sections.id", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)  # Admin, HOD, Professor, Student
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sections = relationship("Section", secondary=faculty_sections, back_populates="faculty")
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    approved_reports = relationship("AnalysisResult", back_populates="approver")

class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    section_name = Column(String(20), unique=True, index=True, nullable=False)  # e.g., A, B, C, D

    # Relationships
    faculty = relationship("User", secondary=faculty_sections, back_populates="sections")
    submissions = relationship("Submission", back_populates="section", cascade="all, delete-orphan")

class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(Integer, primary_key=True, index=True)
    course = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)
    due_date = Column(DateTime, nullable=False)

    # Relationships
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"

    submission_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.assignment_id", ondelete="CASCADE"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(100), nullable=False)
    language = Column(String(20), nullable=False)
    raw_code = Column(Text, nullable=False)
    status = Column(String(30), default="Uploaded")  # Uploaded, Queued, Analyzing, Completed, Faculty Review, Approved, Visible to Student
    submitted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
    section = relationship("Section", back_populates="submissions")
    analysis_result = relationship("AnalysisResult", back_populates="submission", uselist=False, cascade="all, delete-orphan")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    submission_id = Column(Integer, ForeignKey("submissions.submission_id", ondelete="CASCADE"), primary_key=True)
    plagiarism = Column(Text, nullable=True)  # Can store JSON string
    ai_score = Column(Float, nullable=True)
    quality_score = Column(Text, nullable=True)  # Can store JSON string
    report_visible = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="analysis_result")
    approver = relationship("User", back_populates="approved_reports")

class SimilarityPair(Base):
    __tablename__ = "similarity_pairs"

    submission1 = Column(Integer, ForeignKey("submissions.submission_id", ondelete="CASCADE"), primary_key=True)
    submission2 = Column(Integer, ForeignKey("submissions.submission_id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(Float, nullable=True)
    tree_edit = Column(Float, nullable=True)
    jaccard = Column(Float, nullable=True)
    fusion = Column(Float, nullable=True)
