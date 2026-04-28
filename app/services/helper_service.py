# app/services/student_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.models import Student
from app.db.database import SessionLocal


# ── Pipeline-compatible version (no db arg) ────────────────────────────────────
# face_pipeline.py calls get_all_students() with NO arguments — same as Streamlit.
# We open a short-lived session internally so the pipeline doesn't need to change.

def get_all_students() -> list[dict]:
    """
    Called by face_pipeline.get_trained_model() — no db argument, returns list of dicts
    (same shape the Streamlit/Supabase version returned).
    """
    db = SessionLocal()
    try:
        students = list(db.scalars(select(Student)))
        result = []
        for s in students:
            emb = s.face_embedding
            # stored as {"embedding": [...]} — pipeline expects the raw list
            face_emb = emb.get("embedding") if isinstance(emb, dict) else emb

            v_emb = s.voice_embedding
            voice_emb = v_emb.get("embedding") if isinstance(v_emb, dict) else v_emb

            result.append({
                "student_id":       s.student_id,
                "name":             s.name,
                "face_embedding":   face_emb,
                "voice_embedding":  voice_emb,
            })
        return result
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching students: {str(e)}"
        )
    finally:
        db.close()


# ── Route-compatible version (with db arg) ─────────────────────────────────────
# Used by FastAPI routes via Depends(get_db).

def get_all_students_db(db: Session) -> list[Student]:
    try:
        return list(db.scalars(select(Student)))
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching students: {str(e)}"
        )


def create_student(
    db: Session,
    name: str,
    face_embedding: list[float] | None = None,
    voice_embedding: list[float] | None = None,
) -> Student:
    try:
        student = Student(
            name=name,
            face_embedding={"embedding": face_embedding} if face_embedding else None,
            voice_embedding={"embedding": voice_embedding} if voice_embedding else None,
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        return student

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create student: {str(e)}"
        )