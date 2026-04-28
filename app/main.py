# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import create_tables
from app.api.routes import auth, student, subject

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],  # exact frontend origin
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",   # ✅ allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
def on_startup():
    create_tables()

app.include_router(auth.router, prefix="/api")
app.include_router(student.router, prefix="/api")
app.include_router(subject.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}