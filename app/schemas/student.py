from pydantic import BaseModel


class StudentLoginRequest(BaseModel):
    """React webcam se captured frame — base64 encoded PNG/JPEG."""
    image_b64: str  # data:image/png;base64,XXXX  OR  raw base64


class StudentCreateRequest(BaseModel):
    """Naya student banane ke liye name + face image + optional voice."""
    name: str
    image_b64: str              # base64 image (same format as login)
    audio_b64: str | None = None  # base64 encoded WAV/WebM audio (optional)


class StudentOut(BaseModel):
    """Student response schema."""
    student_id: int
    name: str


class StudentLoginResponse(BaseModel):
    found: bool
    student: StudentOut | None
    message: str | None = None


class StudentCreateResponse(BaseModel):
    student: StudentOut
    message: str