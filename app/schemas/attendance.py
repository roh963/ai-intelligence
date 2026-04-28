# app/api/schemas/attendance.py

from pydantic import BaseModel


class FaceAttendanceRequest(BaseModel):
    subject_id: int
    images_b64: list[str]          # one or more classroom photos


class VoiceAttendanceRequest(BaseModel):
    subject_id: int
    audio_b64: str                 # base64 webm recording