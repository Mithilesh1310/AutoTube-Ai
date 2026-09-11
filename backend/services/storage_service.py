import os
import shutil
import logging
from abc import ABC, abstractmethod
from typing import Optional
from backend.config import settings

logger = logging.getLogger(__name__)

class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, source_path: str, destination_key: str) -> str:
        pass

    @abstractmethod
    async def get_url(self, destination_key: str) -> str:
        pass

    @abstractmethod
    def cleanup_temp_assets(self, target_path: str):
        pass

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or settings.STORAGE_LOCAL_DIR
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, source_path: str, destination_key: str) -> str:
        target_path = os.path.join(self.base_dir, destination_key)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if os.path.abspath(source_path) != os.path.abspath(target_path):
            shutil.copy2(source_path, target_path)
        return target_path

    async def get_url(self, destination_key: str) -> str:
        clean_key = destination_key.replace("\\", "/").lstrip("/")
        return f"/storage/{clean_key}"

    def cleanup_temp_assets(self, target_path: str):
        if not target_path or not os.path.exists(target_path):
            return
        try:
            if os.path.isdir(target_path):
                shutil.rmtree(target_path, ignore_errors=True)
            elif os.path.isfile(target_path):
                os.remove(target_path)
            logger.info(f"[StorageCleanup] Safely deleted temporary asset '{target_path}'.")
        except Exception as e:
            logger.warning(f"[StorageCleanup] Could not clean '{target_path}': {e}")

class S3StorageProvider(StorageProvider):
    """
    Production Object Storage Provider for AWS S3 and Cloudflare R2.
    """
    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.endpoint = settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY

    async def save_file(self, source_path: str, destination_key: str) -> str:
        if not self.access_key or not self.secret_key:
            # Fallback to local storage if credentials missing
            local = LocalStorageProvider()
            return await local.save_file(source_path, destination_key)

        try:
            import boto3
            client_kwargs = {
                "aws_access_key_id": self.access_key,
                "aws_secret_access_key": self.secret_key
            }
            if self.endpoint:
                client_kwargs["endpoint_url"] = self.endpoint

            s3 = boto3.client("s3", **client_kwargs)
            clean_key = destination_key.replace("\\", "/").lstrip("/")
            s3.upload_file(source_path, self.bucket, clean_key)
            logger.info(f"[S3StorageProvider] Uploaded '{source_path}' -> 's3://{self.bucket}/{clean_key}'.")
            return await self.get_url(clean_key)
        except Exception as e:
            logger.error(f"[S3StorageProvider] S3 upload error: {e}. Falling back to local.")
            local = LocalStorageProvider()
            return await local.save_file(source_path, destination_key)

    async def get_url(self, destination_key: str) -> str:
        clean_key = destination_key.replace("\\", "/").lstrip("/")
        if self.endpoint:
            return f"{self.endpoint.rstrip('/')}/{self.bucket}/{clean_key}"
        return f"https://{self.bucket}.s3.amazonaws.com/{clean_key}"

    def cleanup_temp_assets(self, target_path: str):
        LocalStorageProvider().cleanup_temp_assets(target_path)

def get_storage_provider() -> StorageProvider:
    provider_type = (settings.STORAGE_PROVIDER or "").lower()
    if provider_type in ["s3", "r2"]:
        return S3StorageProvider()
    return LocalStorageProvider()

storage_service = get_storage_provider()
