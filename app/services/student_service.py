# ============================================================
# Student service — image/audio decode + business logic.
# Streamlit wala pipeline bilkul same rehta hai,
# sirf base64 decode ka extra step hai.
# ============================================================

import base64
import io

import numpy as np
from PIL import Image
from pydub import AudioSegment
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.helper_service import get_all_students, create_student
from app.pipelines.face_pipeline import predict_attendace, get_face_embeddings, train_classifier
from app.pipelines.voice_pipeline import get_voice_embedding


# ── Image Decoder ─────────────────────────────────────────────────────────────

def decode_image(image_b64: str) -> np.ndarray:
    """
    React/browser se aaya base64 image decode karta hai.

    Streamlit mein camera_input automatically PIL Image → np.array karta tha.
    Yahan hum wahi manually karte hain:
      1. data:image/...;base64, prefix hata do (agar ho)
      2. base64 decode karo → bytes
      3. PIL se open karo → RGB convert karo
      4. np.array banao — dlib ke liye uint8 owned C-contiguous array
    """
    # Step 1: prefix strip
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    # Step 2: base64 → bytes
    try:
        img_bytes = base64.b64decode(image_b64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 image data"
        )

    # Step 3: PIL → RGB → numpy
    try:
        pil_img = Image.open(io.BytesIO(img_bytes))
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        img_np = np.array(pil_img, dtype=np.uint8)

        # Safety: dlib ko exactly 3 channels chahiye
        if img_np.ndim == 2:
            img_np = np.stack([img_np] * 3, axis=-1)   # grayscale → RGB
        elif img_np.shape[2] != 3:
            img_np = img_np[:, :, :3]                  # RGBA → RGB

        img_np = np.ascontiguousarray(img_np, dtype=np.uint8).copy()
        img_np.flags.writeable = True

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode image — send PNG or JPEG"
        )

    return img_np


# ── Audio Decoder ─────────────────────────────────────────────────────────────

def decode_audio(audio_b64: str) -> bytes:
    """
    WebM base64 audio → WAV bytes.
    librosa seedha WAV bytes read karega.
    """
    if "," in audio_b64:
        audio_b64 = audio_b64.split(",", 1)[1]

    try:
        webm_bytes = base64.b64decode(audio_b64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 audio data"
        )

    # WebM → WAV convert (16kHz mono — voice model ke liye)
    audio = AudioSegment.from_file(io.BytesIO(webm_bytes), format="webm")
    audio = audio.set_frame_rate(16000).set_channels(1)

    wav_buffer = io.BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)

    return wav_buffer.read()


# ── Business Logic ────────────────────────────────────────────────────────────

def handle_student_login(image_b64: str) -> dict:
    """
    Face se student identify karo.

    Streamlit flow (wahi yahan replicate hai):
      camera_input → np.array(Image.open()) → predict_attendace()
    """
    img_np = decode_image(image_b64)
    detected, all_ids, num_faces = predict_attendace(img_np)

    if num_faces == 0:
        return {"found": False, "student": None, "message": "no_face"}

    if num_faces > 1:
        return {"found": False, "student": None, "message": "multi_face"}

    if not detected:
        return {"found": False, "student": None, "message": "unrecognized"}

    student_id = list(detected.keys())[0]
    all_students = get_all_students()
    student = next((s for s in all_students if s["student_id"] == student_id), None)

    if not student:
        return {"found": False, "student": None, "message": "unrecognized"}

    return {
        "found": True,
        "student": {
            "student_id": student["student_id"],
            "name": student["name"],
        },
    }


def handle_create_student(
    db: Session,
    name: str,
    image_b64: str,
    audio_b64: str | None,
) -> dict:
    """
    Naya student register karo — face embedding + optional voice embedding.

    Streamlit flow (wahi yahan replicate hai):
      name + camera photo → get_face_embeddings() → create_student() → train_classifier()
      + optional: audio_input.read() → get_voice_embedding()
    """
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required"
        )

    img_np = decode_image(image_b64)

    # Face embeddings nikalo
    encodings = get_face_embeddings(img_np)
    if not encodings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not capture facial features — try again with better lighting"
        )

    face_emb = encodings[0].tolist()  # 128-dim list

    # Voice embedding (optional)
    voice_emb = None
    if audio_b64:
        audio_bytes = decode_audio(audio_b64)
        voice_emb = get_voice_embedding(audio_bytes)

    # DB mein save karo
    new_student = create_student(
        db,
        name=name.strip(),
        face_embedding=face_emb,
        voice_embedding=voice_emb,
    )

    # Classifier retrain (lru_cache clear + rebuild)
    train_classifier()

    return {
        "student": {
            "student_id": new_student.student_id,
            "name": new_student.name,
        },
        "message": "Profile created successfully!",
    }