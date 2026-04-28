from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.database import get_db
from app.schemas.student import StudentLoginRequest, StudentCreateRequest
from app.services.student_service import (
    handle_student_login,
    handle_create_student,
)
from app.models.models import Subject, SubjectStudent

router = APIRouter(prefix="/student", tags=["Student"])


@router.post("/login")
def student_login(req: StudentLoginRequest):
    """
    Face se student login.
    Returns: found/not found + student info or message
    """
    return handle_student_login(req.image_b64)


@router.post("/create", status_code=201)
def create_student_profile(req: StudentCreateRequest, db: Session = Depends(get_db)):
    """
    Naya student register karo — face + optional voice embedding.
    """
    return handle_create_student(
        db=db,
        name=req.name,
        image_b64=req.image_b64,
        audio_b64=req.audio_b64,
    )


@router.get("/{student_id}/subjects")
def get_student_subjects(student_id: int, db: Session = Depends(get_db)):
    """
    Student ke enrolled subjects return karo.
    StudentDashboard mein cards dikhane ke liye.
    """
    rows = list(db.scalars(
        select(Subject)
        .join(SubjectStudent, SubjectStudent.subject_id == Subject.subject_id)
        .where(SubjectStudent.student_id == student_id)
        .order_by(Subject.subject_code)
    ))

    return [
        {
            "subject_id":   s.subject_id,
            "subject_code": s.subject_code,
            "name":         s.name,
            "section":      s.section,
        }
        for s in rows
    ]