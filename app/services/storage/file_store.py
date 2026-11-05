"""Stockage des fichiers sources : MinIO (production/démo Docker) ou dossier local (développement sans Docker).

Stockage adressé par contenu : la clé est dérivée du sha256, donc un doublon exact n'est stocké qu'une fois.
"""
import hashlib
from pathlib import Path
from typing import Protocol


def object_key(sha256: str, suffix: str = ".pdf") -> str:
    return f"{sha256[:2]}/{sha256}{suffix}"


class FileStore(Protocol):
    def put(self, path: Path) -> str: ...
    def get(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...


class LocalFileStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, path: Path) -> str:
        data = Path(path).read_bytes()
        key = object_key(hashlib.sha256(data).hexdigest(), Path(path).suffix.lower() or ".bin")
        target = self.root / key
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()


class MinioFileStore:
    """Même contrat que LocalFileStore, au-dessus d'un serveur MinIO (client `minio`)."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False, client=None):
        if client is None:
            from minio import Minio

            client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self.client, self.bucket = client, bucket
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def put(self, path: Path) -> str:
        import io

        data = Path(path).read_bytes()
        key = object_key(hashlib.sha256(data).hexdigest(), Path(path).suffix.lower() or ".bin")
        if not self.exists(key):
            self.client.put_object(self.bucket, key, io.BytesIO(data), length=len(data), content_type="application/pdf")
        return key

    def get(self, key: str) -> bytes:
        resp = self.client.get_object(self.bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:  # S3Error NoSuchKey
            return False


def build_file_store(settings) -> FileStore:
    if settings.minio_endpoint:
        if "CHANGE_ME" in (settings.minio_access_key, settings.minio_secret_key):
            raise RuntimeError("Identifiants MinIO par défaut interdits : renseigner .env")
        return MinioFileStore(settings.minio_endpoint, settings.minio_access_key, settings.minio_secret_key,
                              settings.minio_bucket, settings.minio_secure)
    return LocalFileStore(settings.local_store_dir)
