import os
import shutil
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, status

router = APIRouter(prefix="/uploads", tags=["Uploads"])

MEDIA_DIR = "app/media"
ALLOW_MIME = ["image/jpeg", "image/png"]
MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
CHUNK_SIZE = 1024 * 1024  # 1 MB


def ensure_media_dir() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)


def save_uploaded_image(file: UploadFile) -> dict:
    if file.content_type not in ["image/jpeg", "image/png"]:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten archivos JPEG o PNG"
        )

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(MEDIA_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer, length=CHUNK_SIZE)

    size = os.path.getsize(file_path)
    if size > MAX_MB * 1024 * 1024:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo de {MAX_MB} MB"
        )

    return {
        "filename": filename,
        "content_type": file.content_type,
        "url": f"/media/{filename}"

    }
