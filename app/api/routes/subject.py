import io
import segno
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_teacher   # JWT dependency — neeche banate hain
from app.models.models import Teacher
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, EnrollResponse
from app.services import subject_service

router = APIRouter(prefix="/subject", tags=["Subject"])


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[SubjectResponse])
def list_subjects(
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    return subject_service.get_teacher_subjects(db, teacher.teacher_id)


@router.post("/", response_model=SubjectResponse, status_code=201)
def create_subject(
    data: SubjectCreate,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    return subject_service.create_subject(db, data, teacher.teacher_id)


@router.patch("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    return subject_service.update_subject(db, subject_id, teacher.teacher_id, data)


@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    subject_service.delete_subject(db, subject_id, teacher.teacher_id)


# ── QR Code — Segno ───────────────────────────────────────────────────────────

# subject.py route mein qr endpoint update karo
@router.get("/{subject_id}/qr")
def get_subject_qr(
    subject_id: int,
    base_url: str,
    token: str,              # <-- query param se token
    db: Session = Depends(get_db),
):
    from app.core.security import decode_access_token
    from app.models.models import Teacher
    from sqlalchemy import select

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        teacher = db.scalar(select(Teacher).where(Teacher.username == username))
        if not teacher:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    subject = subject_service.get_subject_by_id(db, subject_id)
    if subject.teacher_id != teacher.teacher_id:
        raise HTTPException(status_code=403, detail="Not your subject")

    join_url = f"{base_url}/student-login?join={subject_id}"
    qr = segno.make(join_url, error="h")

    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=8, border=2, dark="#2d2060", light="#f5f0ff")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")

# ── Enroll (student QR scan ke baad call karega) ──────────────────────────────

@router.post("/{subject_id}/enroll", response_model=EnrollResponse)
def enroll_student(
    subject_id: int,
    student_id: int,        # body ya query — simple rakhte hain query param
    db: Session = Depends(get_db),
):
    """
    Public endpoint — no teacher auth needed.
    Student login ke baad frontend yahan call karega.
    """
    enrollment = subject_service.enroll_student(db, subject_id, student_id)
    return EnrollResponse(
        message="Enrolled successfully!",
        subject_id=enrollment.subject_id,
        student_id=enrollment.student_id,
    )


# ── Attendance Records ────────────────────────────────────────────────────────

@router.get("/attendance/records")
def attendance_records(
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    return subject_service.get_attendance_records(db, teacher.teacher_id)