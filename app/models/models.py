# app/models/models.py
# ============================================================
# PURPOSE: Ye file Python classes ke through database tables define
# karti hai. SQLAlchemy ORM inhe SQL queries mein translate karta hai.
# Har class = ek table, har attribute = ek column.
# ============================================================

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey,
    String, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Teacher(Base):
    """
    teachers table.
    Face recognition system use karne wale teachers.
    username unique hoga, password bcrypt hash hoga.
    """
    __tablename__ = "teachers"

    teacher_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)  # bcrypt hash
    name: Mapped[str] = mapped_column(Text, nullable=False)

    # Ek teacher ke multiple subjects ho sakte hain
    subjects: Mapped[List["Subject"]] = relationship(
        "Subject", back_populates="teacher", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Teacher id={self.teacher_id} username={self.username}>"


class Student(Base):
    """
    students table.
    face_embedding aur voice_embedding JSONB mein store hoti hain
    kyunki ye numpy arrays/lists hoti hain jo PostgreSQL JSONB mein
    efficiently store ho sakti hain.
    """
    __tablename__ = "students"

    student_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)

    # JSONB: Face recognition model ka 128-dimension embedding vector
    # Example: [0.123, -0.456, 0.789, ...]
    face_embedding: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # JSONB: Voice recognition ka embedding (future use)
    voice_embedding: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Many-to-many: ek student kai subjects mein ho sakta hai
    subject_enrollments: Mapped[List["SubjectStudent"]] = relationship(
        "SubjectStudent", back_populates="student"
    )
    attendance_logs: Mapped[List["AttendanceLog"]] = relationship(
        "AttendanceLog", back_populates="student"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.student_id} name={self.name}>"


class Subject(Base):
    """
    subjects table.
    Har subject ka ek teacher hota hai. Teacher delete ho to
    teacher_id NULL ho jata hai (SET NULL behavior).
    """
    __tablename__ = "subjects"

    subject_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    subject_code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    section: Mapped[str] = mapped_column(Text, nullable=False, default="n/a")

    # ForeignKey: Teacher delete hone par SET NULL (subject remain karta hai)
    teacher_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("teachers.teacher_id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    teacher: Mapped[Optional["Teacher"]] = relationship(
        "Teacher", back_populates="subjects"
    )
    student_enrollments: Mapped[List["SubjectStudent"]] = relationship(
        "SubjectStudent", back_populates="subject"
    )
    attendance_logs: Mapped[List["AttendanceLog"]] = relationship(
        "AttendanceLog", back_populates="subject"
    )

    def __repr__(self) -> str:
        return f"<Subject id={self.subject_id} code={self.subject_code}>"


class SubjectStudent(Base):
    """
    subject_students table (Junction/Association Table).
    Students aur Subjects ke beech many-to-many relationship handle karta hai.
    Composite primary key: (subject_id, student_id).
    """
    __tablename__ = "subject_students"

    subject_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subjects.subject_id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.student_id", ondelete="CASCADE"), primary_key=True
    )

    # Back references
    subject: Mapped["Subject"] = relationship("Subject", back_populates="student_enrollments")
    student: Mapped["Student"] = relationship("Student", back_populates="subject_enrollments")

    def __repr__(self) -> str:
        return f"<SubjectStudent subject={self.subject_id} student={self.student_id}>"


class AttendanceLog(Base):
    """
    attendance_logs table.
    Har entry ek student ka ek subject mein ek specific time pe 
    attendance record hai. is_present default True (present).
    timestamp automatically Supabase server time se set hoti hai.
    """
    __tablename__ = "attendance_logs"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    # server_default: DB server se timestamp aata hai (Python se nahi)
    # Isse timezone consistent rehti hai
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    subject_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("subjects.subject_id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False
    )
    is_present: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    subject: Mapped["Subject"] = relationship("Subject", back_populates="attendance_logs")
    student: Mapped["Student"] = relationship("Student", back_populates="attendance_logs")

    def __repr__(self) -> str:
        return f"<AttendanceLog id={self.id} student={self.student_id} present={self.is_present}>"