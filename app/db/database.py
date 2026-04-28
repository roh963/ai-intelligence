# app/db/database.py
# ============================================================
# PURPOSE: SQLAlchemy engine aur session factory yahan setup hoti hai.
# Engine = Supabase PostgreSQL se actual connection.
# SessionLocal = har request ke liye naya DB session banata hai.
# Base = saare ORM models isse inherit karte hain.
# create_tables() = server start hote hi naye tables automatically ban jaate hain.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


# Engine: Supabase se ek baar connect hota hai, pool manage karta hai
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,   # Connection alive check (network issues handle karta hai)
    echo=settings.DEBUG,  # DEBUG=True ho to SQL queries terminal mein dikhti hain
)

# SessionLocal: har HTTP request ke liye ek naya DB session
SessionLocal = sessionmaker(
    autocommit=False,  # Explicit commit chahiye - accidental writes se bachata hai
    autoflush=False,   # Manually flush karo jab zaroorat ho
    bind=engine,
)


class Base(DeclarativeBase):
    """
    Saare SQLAlchemy ORM models iss class ko inherit karte hain.
    Base ke andar metadata hota hai jisme saare table definitions
    store hote hain - create_tables() issi ko use karta hai.
    """
    pass


def get_db():
    """
    FastAPI Dependency Injection ke liye DB session generator.

    Har request pe ek fresh session milta hai aur request khatam
    hone par - chahe success ho ya exception - session automatically
    close ho jata hai (finally block ki wajah se).

    Usage in routes:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    TypeORM ke create_all jaisa behavior - sirf naye tables banata hai.

    - Server start hote hi call hoti hai (main.py startup event)
    - Agar table already exist karta hai to skip karta hai (safe hai)
    - Naya model/table add karo models.py mein, restart karo - ban jayega

    LIMITATION: Existing table mein naya column add kiya models.py mein
    to wo automatically nahi add hoga. Uske liye Supabase dashboard mein
    manually SQL run karo:
        ALTER TABLE students ADD COLUMN IF NOT EXISTS phone TEXT;
    Ya Alembic use karo (production ke liye recommended).
    """
    # models import karna zaroori hai taaki Base ko pata chale
    # ki kaun kaun se tables create karne hain
    from app.models import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("✅ Tables checked/created in Supabase!")