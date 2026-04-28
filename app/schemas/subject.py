from pydantic import BaseModel
from typing import Optional


class SubjectCreate(BaseModel):
    subject_code: str
    name: str
    section: str


class SubjectUpdate(BaseModel):
    subject_code: Optional[str] = None
    name: Optional[str] = None
    section: Optional[str] = None


class SubjectResponse(BaseModel):
    subject_id: int
    subject_code: str
    name: str
    section: str
    teacher_id: Optional[int] = None

    model_config = {"from_attributes": True}


class EnrollResponse(BaseModel):
    message: str
    subject_id: int
    student_id: int