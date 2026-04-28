from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.models import Subject, SubjectStudent, Student
from app.schemas.subject import SubjectCreate, SubjectUpdate


def get_teacher_subjects(db: Session, teacher_id: int) -> list[Subject]:
    try:
        return list(db.scalars(
            select(Subject).where(Subject.teacher_id == teacher_id)
        ))
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_subject_by_id(db: Session, subject_id: int) -> Subject:
    subject = db.scalar(select(Subject).where(Subject.subject_id == subject_id))
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


def create_subject(db: Session, data: SubjectCreate, teacher_id: int) -> Subject:
    # Duplicate check: same teacher ka same code+section combo
    existing = db.scalar(
        select(Subject).where(
            Subject.teacher_id == teacher_id,
            Subject.subject_code == data.subject_code.strip(),
            Subject.section == data.section.strip(),
        )
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Subject with this code and section already exists."
        )

    try:
        subject = Subject(
            subject_code=data.subject_code.strip(),
            name=data.name.strip(),
            section=data.section.strip(),
            teacher_id=teacher_id,
        )
        db.add(subject)
        db.commit()
        db.refresh(subject)
        return subject
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def update_subject(db: Session, subject_id: int, teacher_id: int, data: SubjectUpdate) -> Subject:
    subject = get_subject_by_id(db, subject_id)

    if subject.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Not your subject")

    if data.subject_code is not None:
        subject.subject_code = data.subject_code.strip()
    if data.name is not None:
        subject.name = data.name.strip()
    if data.section is not None:
        subject.section = data.section.strip()

    try:
        db.commit()
        db.refresh(subject)
        return subject
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def delete_subject(db: Session, subject_id: int, teacher_id: int) -> None:
    subject = get_subject_by_id(db, subject_id)
    if subject.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Not your subject")
    try:
        # Pehle manually children delete karo
        from sqlalchemy import delete as sql_delete
        from app.models.models import SubjectStudent, AttendanceLog

        db.execute(sql_delete(AttendanceLog).where(AttendanceLog.subject_id == subject_id))
        db.execute(sql_delete(SubjectStudent).where(SubjectStudent.subject_id == subject_id))
        db.delete(subject)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def enroll_student(db: Session, subject_id: int, student_id: int) -> SubjectStudent:
    """Student ko subject mein enroll karo — student_login ke baad call hoga."""
    # Subject exist karta hai?
    get_subject_by_id(db, subject_id)

    # Student exist karta hai?
    student = db.scalar(select(Student).where(Student.student_id == student_id))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Already enrolled?
    already = db.scalar(
        select(SubjectStudent).where(
            SubjectStudent.subject_id == subject_id,
            SubjectStudent.student_id == student_id,
        )
    )
    if already:
        raise HTTPException(status_code=400, detail="Student already enrolled in this subject")

    try:
        enrollment = SubjectStudent(subject_id=subject_id, student_id=student_id)
        db.add(enrollment)
        db.commit()
        return enrollment
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


def get_attendance_records(db: Session, teacher_id: int) -> list[dict]:
    """
    Teacher ke saare subjects ki attendance — subject name, student name, time, present/absent.
    """
    from app.models.models import AttendanceLog

    try:
        logs = list(db.scalars(
            select(AttendanceLog)
            .join(Subject, AttendanceLog.subject_id == Subject.subject_id)
            .where(Subject.teacher_id == teacher_id)
            .order_by(AttendanceLog.timestamp.desc())
        ))

        result = []
        for log in logs:
            result.append({
                "log_id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "is_present": log.is_present,
                "subject_id": log.subject_id,
                "subject_name": log.subject.name if log.subject else "Unknown",
                "subject_code": log.subject.subject_code if log.subject else "",
                "section": log.subject.section if log.subject else "",
                "student_id": log.student_id,
                "student_name": log.student.name if log.student else "Unknown",
            })
        return result
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))