# app/services/attendance_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import Subject, SubjectStudent, Student, AttendanceLog


def get_subject_or_403(db: Session, subject_id: int, teacher_id: int) -> Subject:
    subject = db.scalar(select(Subject).where(Subject.subject_id == subject_id))
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Not your subject")
    return subject


def get_enrolled_students(db: Session, subject_id: int) -> list[Student]:
    """All students enrolled in a subject."""
    return list(db.scalars(
        select(Student)
        .join(SubjectStudent, SubjectStudent.student_id == Student.student_id)
        .where(SubjectStudent.subject_id == subject_id)
    ))


def save_attendance_logs(
    db: Session,
    subject_id: int,
    enrolled: list[Student],
    present_ids: set[int],
) -> None:
    """Write one AttendanceLog row per enrolled student."""
    for student in enrolled:
        log = AttendanceLog(
            subject_id=subject_id,
            student_id=student.student_id,
            is_present=student.student_id in present_ids,
        )
        db.add(log)
    db.commit()


def build_attendance_results(
    enrolled: list[Student],
    present_ids: set[int],
) -> list[dict]:
    return [
        {
            "student_id":   s.student_id,
            "student_name": s.name,
            "present":      s.student_id in present_ids,
        }
        for s in sorted(enrolled, key=lambda x: x.name)
    ]


def run_face_attendance(
    db: Session,
    subject_id: int,
    teacher_id: int,
    images_b64: list[str],
) -> dict:
    from pipelines.face_pipeline import predict_attendace
    from app.services.student_service import decode_image

    get_subject_or_403(db, subject_id, teacher_id)
    enrolled = get_enrolled_students(db, subject_id)

    if not enrolled:
        raise HTTPException(status_code=400, detail="No students enrolled in this subject yet")
    if not images_b64:
        raise HTTPException(status_code=400, detail="Send at least one image")

    present_ids: set[int] = set()

    for img_b64 in images_b64:
        try:
            img_np = decode_image(img_b64)
            detected, _, _ = predict_attendace(img_np)
            present_ids.update(detected.keys())
        except Exception as e:
            # skip bad images — don't fail the whole request
            print(f"[face_attendance] skipped image: {e}")
            continue

    save_attendance_logs(db, subject_id, enrolled, present_ids)

    return {
        "subject_id": subject_id,
        "results": build_attendance_results(enrolled, present_ids),
    }


def run_voice_attendance(
    db: Session,
    subject_id: int,
    teacher_id: int,
    audio_b64: str,
) -> dict:
    from pipelines.voice_pipeline import process_bulk_audio
    from app.services.student_service import decode_audio

    get_subject_or_403(db, subject_id, teacher_id)
    enrolled = get_enrolled_students(db, subject_id)

    if not enrolled:
        raise HTTPException(status_code=400, detail="No students enrolled in this subject yet")

    # Build candidates dict: { student_id: voice_embedding_list }
    candidates: dict[int, list] = {}
    for s in enrolled:
        v = s.voice_embedding
        if v:
            emb = v.get("embedding") if isinstance(v, dict) else v
            if emb:
                candidates[s.student_id] = emb

    if not candidates:
        raise HTTPException(
            status_code=400,
            detail="No enrolled students have voice profiles. Students need to record voice during registration.",
        )

    try:
        audio_bytes = decode_audio(audio_b64)
        identified  = process_bulk_audio(audio_bytes, candidates)  # { student_id: score }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice analysis error: {str(e)}")

    present_ids = set(identified.keys())
    save_attendance_logs(db, subject_id, enrolled, present_ids)

    return {
        "subject_id": subject_id,
        "results": build_attendance_results(enrolled, present_ids),
    }