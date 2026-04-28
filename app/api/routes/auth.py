# app/api/routes/auth.py
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.database import get_db
from app.schemas.teacher import TeacherSignup, TeacherLogin, TeacherResponse, Token
from app.services import teacher_service
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=TeacherResponse, status_code=201)
def signup(data: TeacherSignup, db: Session = Depends(get_db)):
    # Username already exists?
    if teacher_service.get_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    return teacher_service.create_teacher(db, data)


@router.post("/login", response_model=Token)
def login(data: TeacherLogin, db: Session = Depends(get_db)):
    teacher = teacher_service.authenticate(db, data.username, data.password)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    token = create_access_token(data={"sub": teacher.username})
    return Token(access_token=token)