# app/api/routes/attendance.py

import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_teacher
from app.models.models import Teacher
from app.schemas.attendance import FaceAttendanceRequest, VoiceAttendanceRequest
from app.services.attendance_service import run_face_attendance, run_voice_attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/face")
async def face_attendance(
    req: FaceAttendanceRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    """
    Run face recognition on one or more classroom photos.
    dlib CPU-heavy hai — thread pool mein chalao.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: run_face_attendance(db, req.subject_id, teacher.teacher_id, req.images_b64)
    )


@router.post("/voice")
async def voice_attendance(
    req: VoiceAttendanceRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher),
):
    """
    Run voice recognition on a classroom audio recording.
    resemblyzer CPU-heavy hai — thread pool mein chalao.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: run_voice_attendance(db, req.subject_id, teacher.teacher_id, req.audio_b64)
    )