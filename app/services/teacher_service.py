# app/services/teacher_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from fastapi import HTTPException, status

from app.models.models import Teacher
from app.schemas.teacher import TeacherSignup
from app.core.security import hash_password, verify_password


def get_by_username(db: Session, username: str) -> Optional[Teacher]:
    try:
        return db.scalar(select(Teacher).where(Teacher.username == username))
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching teacher: {str(e)}"
        )


def create_teacher(db: Session, data: TeacherSignup) -> Teacher:
    # ── 1. Username already exists? ──────────────────────────
    existing = get_by_username(db, data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken. Please choose a different username."
        )

    # ── 2. Username validation ────────────────────────────────
    username = data.username.strip()
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be at least 3 characters long."
        )
    if len(username) > 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must not exceed 50 characters."
        )
    if not username.replace("_", "").replace(".", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username can only contain letters, numbers, underscores (_) and dots (.)."
        )

    # ── 3. Name validation ────────────────────────────────────
    name = data.name.strip()
    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name must be at least 2 characters long."
        )
    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name must not exceed 100 characters."
        )
    if not all(c.isalpha() or c.isspace() for c in name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name can only contain letters and spaces."
        )

    # ── 4. Password validation ────────────────────────────────
    password = data.password
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long."
        )
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter."
        )
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter."
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one number."
        )

    # ── 5. Save to DB ─────────────────────────────────────────
    try:
        teacher = Teacher(
            name=name,
            username=username,
            password=hash_password(password),  # kabhi plain text save mat karo
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher

    except SQLAlchemyError as e:
        db.rollback()  # Koi bhi partial write undo ho jaye
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create teacher. Database error: {str(e)}"
        )


def authenticate(db: Session, username: str, password: str) -> Optional[Teacher]:
    # ── 1. Input empty check ──────────────────────────────────
    if not username or not username.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username cannot be empty."
        )
    if not password or not password.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password cannot be empty."
        )

    # ── 2. Teacher dhundho ────────────────────────────────────
    teacher = get_by_username(db, username.strip())
    if not teacher:
        # Security: "username not found" mat batao, generic message do
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    # ── 3. Password verify karo ───────────────────────────────
    if not verify_password(password, teacher.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    return teacher