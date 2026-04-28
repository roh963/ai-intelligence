# app/schemas/teacher.py
from pydantic import BaseModel, model_validator


class TeacherSignup(BaseModel):
    name:             str
    username:         str
    password:         str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class TeacherLogin(BaseModel):
    username: str
    password: str


class TeacherResponse(BaseModel):
    teacher_id: int
    username:   str
    name:       str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"