"""Abstraction over GridFS and cloud storage."""
import logging
from typing import Dict, Tuple
from config import Config
from Storage.gridfs_storage import GridFSStorage
from Storage.cloud_storage import S3Storage

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self):
        prov = Config.STORAGE_PROVIDER
        if prov == "s3" and Config.S3_BUCKET:
            self.backend = S3Storage()
            self.name = "s3"
        else:
            self.backend = GridFSStorage()
            self.name = "gridfs"

    def upload(self, local_path: str, book_id: str, filename: str) -> Tuple[str, str]:
        """Returns (storage_name, location_uri)."""
        return self.backend.upload(local_path, book_id, filename)

    def download(self, location: str, local_path: str) -> str:
        return self.backend.download(location, local_path)

    def get_bytes(self, location: str) -> bytes:
        return self.backend.get_bytes(location)


_manager = None


def get_storage() -> StorageManager:
    global _manager
    if _manager is None:
        _manager = StorageManager()
    return _manager