"""MongoDB GridFS storage."""
import logging
from pathlib import Path
import gridfs
from Database.mongodb import get_db

logger = logging.getLogger(__name__)


class GridFSStorage:
    def __init__(self):
        self.fs = gridfs.GridFS(get_db(), collection="generated_file_blobs")

    def upload(self, local_path: str, book_id: str, filename: str):
        with open(local_path, "rb") as f:
            file_id = self.fs.put(
                f,
                filename=filename,
                metadata={"book_id": book_id},
            )
        return "gridfs", f"gridfs://{file_id}"

    def download(self, location: str, local_path: str) -> str:
        file_id = location.replace("gridfs://", "")
        from bson import ObjectId
        f = self.fs.get(ObjectId(file_id))
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as out:
            out.write(f.read())
        return local_path

    def get_bytes(self, location: str) -> bytes:
        file_id = location.replace("gridfs://", "")
        from bson import ObjectId
        return self.fs.get(ObjectId(file_id)).read()