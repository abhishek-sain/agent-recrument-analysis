import os
import uuid
from abc import ABC, abstractmethod

from fastapi import UploadFile

from app.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file: UploadFile, folder: str) -> str:
        """Persist the file and return a publicly resolvable URL/path."""


class LocalStorage(StorageBackend):
    def save(self, file: UploadFile, folder: str) -> str:
        dir_path = os.path.join(settings.UPLOAD_DIR, folder)
        os.makedirs(dir_path, exist_ok=True)

        ext = os.path.splitext(file.filename or "")[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        full_path = os.path.join(dir_path, filename)

        with open(full_path, "wb") as out:
            out.write(file.file.read())

        # Served via StaticFiles mount at /files (see main.py)
        return f"/files/{folder}/{filename}"


class S3Storage(StorageBackend):
    def __init__(self):
        import boto3

        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket = settings.S3_BUCKET

    def save(self, file: UploadFile, folder: str) -> str:
        ext = os.path.splitext(file.filename or "")[1]
        key = f"{folder}/{uuid.uuid4().hex}{ext}"

        self.client.upload_fileobj(file.file, self.bucket, key, ExtraArgs={"ContentType": file.content_type})

        return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage()
