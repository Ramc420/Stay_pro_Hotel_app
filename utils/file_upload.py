import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException, status
from config import settings


def save_upload_file(
    upload_file: UploadFile,
    subfolder: str = "general",
    allowed_extensions: list = None
) -> str:
    """
    Validates and saves an uploaded file to the specified subfolder inside uploads/.
    Returns relative URL path (e.g. /uploads/avatars/abc.jpg).
    """
    if allowed_extensions is None:
        allowed_extensions = settings.ALLOWED_IMAGE_EXTENSIONS + settings.ALLOWED_DOC_EXTENSIONS

    original_name = upload_file.filename or ""
    ext = original_name.split(".")[-1].lower() if "." in original_name else ""

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '.{ext}'. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Prepare destination directory
    target_dir = os.path.join(settings.UPLOAD_DIR, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    # Unique filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(target_dir, unique_filename)

    # Read and check size
    file_content = upload_file.file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    with open(file_path, "wb") as f:
        f.write(file_content)

    # Reset file pointer
    upload_file.file.seek(0)

    # Return relative URL path
    return f"/uploads/{subfolder}/{unique_filename}"
