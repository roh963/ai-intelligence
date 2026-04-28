# app/core/security.py
# ============================================================
# PURPOSE: Password hashing aur JWT token generation/verification
# ka kaam yahan hota hai. Ye functions auth routes use karte hain.
# ============================================================

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db

from app.core.config import settings

# bcrypt algorithm se password hash hoga
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    from app.models.models import Teacher
    from sqlalchemy import select

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)   # tumhari existing function
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    teacher = db.scalar(select(Teacher).where(Teacher.username == username))
    if not teacher:
        raise credentials_exception
    return teacher


def hash_password(password: str) -> str:
    """Plain text password ko bcrypt hash mein convert karo."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Login ke waqt entered password ko stored hash se compare karo."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT access token banao.
    data: token mein kya encode karna hai (e.g. {"sub": "username"})
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# app/core/security.py

def decode_access_token(token: str) -> dict:          # ← returns dict, not str
    """Verify token and return full payload dict."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload                                  # ← return whole payload
    except JWTError:
        return {}                                       # ← empty dict on failure


def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    from app.models.models import Teacher
    from sqlalchemy import select

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    username: str = payload.get("sub")          # ← now .get("sub") works correctly
    if not username:
        raise credentials_exception

    teacher = db.scalar(select(Teacher).where(Teacher.username == username))
    if not teacher:
        raise credentials_exception
    return teacher


