# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from concurrent.futures import ThreadPoolExecutor
from app.db.database import create_tables
from app.api.routes import auth, student, subject, attendance
from app.pipelines.face_pipeline import load_dlib_models, get_trained_model
from app.pipelines.voice_pipeline import load_voice_encoder
import asyncio


app = FastAPI(title=settings.APP_NAME, version="1.0.0")
FRONTEND_URL = settings.FRONTEND_URL
print("Frontend url",FRONTEND_URL)

origins = [url.strip() for url in FRONTEND_URL.split(",") if url.strip()]

if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # ✅ parsed list use ho rahi hai
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=".*",   # ✅ allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

executor = ThreadPoolExecutor(max_workers=4)
@app.on_event("startup")
def on_startup():
    create_tables()
    loop = asyncio.get_event_loop()
    loop.set_default_executor(executor)
    
    # ✅ Models startup pe hi load kar do — pehli request slow nahi hogi
    print("⏳ Preloading AI models...")
    
    load_dlib_models()      # dlib detector + shape predictor + face encoder
    load_voice_encoder()    # resemblyzer voice encoder
    get_trained_model()     # SVM classifier students ka
    
    print(f"✅ Allowed origins: {origins}")
    print("✅ ThreadPool(4) ready")
    print("✅ AI models preloaded — requests fast hongi!")

app.include_router(auth.router, prefix="/api")
app.include_router(student.router, prefix="/api")
app.include_router(subject.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok"}