"""S3-compatible cloud storage."""
import logging
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)


class S3Storage:
    def __init__(self):
        import boto3
        self.client = boto3.client(
            "s3",
            endpoint_url=Config.S3_ENDPOINT or None,
            aws_access_key_id=Config.S3_ACCESS_KEY,
            aws_secret_access_key=Config.S3_SECRET_KEY,
            region_name=Config.S3_REGION,
        )
        self.bucket = Config.S3_BUCKET

    def upload(self, local_path: str, book_id: str, filename: str):
        key = f"books/{book_id}/{filename}"
        self.client.upload_file(local_path, self.bucket, key)
        return "s3", f"s3://{self.bucket}/{key}"

    def download(self, location: str, local_path: str) -> str:
        key = location.split(f"s3://{self.bucket}/")[-1]
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket, key, local_path)
        return local_path

    def get_bytes(self, location: str) -> bytes:
        key = location.split(f"s3://{self.bucket}/")[-1]
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()