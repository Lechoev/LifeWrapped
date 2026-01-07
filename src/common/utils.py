import os
from uuid import uuid4

from src.common.exceptions import InvalidImageError

AVATARS_DIR = "static/avatars"
os.makedirs(AVATARS_DIR, exist_ok=True)


async def upload_img(img, user_id):
    """
    Загружает аватар пользователя и возвращает URL.
    """
    if not img.content_type.startswith("image/"):
        raise InvalidImageError("Файл должен быть изображением (jpeg, png, gif и т.д.)")

    contents = await img.read()

    extension = img.filename.split(".")[-1].lower() if "." in img.filename else "jpg"
    unique_filename = f"{user_id}_{uuid4().hex}.{extension}"
    file_path = os.path.join(AVATARS_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    return f"/static/avatars/{unique_filename}"
