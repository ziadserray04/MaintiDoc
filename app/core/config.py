from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev-cpu"
    jwt_secret: str = "CHANGE_ME"
    approval_hmac_secret: str = "CHANGE_ME"
    database_url: str = "sqlite:///./data/maintidoc.db"
    qdrant_url: str = ""
    minio_endpoint: str = ""  # vide = stockage de fichiers local
    minio_access_key: str = "CHANGE_ME"
    minio_secret_key: str = "CHANGE_ME"
    minio_bucket: str = "maintidoc-corpus"
    minio_secure: bool = False
    local_store_dir: str = "data/store"
    vlm_backend: str = "fake"
    device: str = "auto"  # auto | cpu | cuda
    embedding_backend: str = "hashing"
    max_model_calls: int = 6
    max_mcp_calls: int = 3
    max_pipeline_seconds: int = 60
    max_image_bytes: int = 8_000_000

    def assert_safe_for_prod(self) -> None:
        if self.app_env != "dev-cpu" and "CHANGE_ME" in (self.jwt_secret, self.approval_hmac_secret):
            raise RuntimeError("Secrets par défaut interdits hors dev-cpu")


def resolve_device(requested: str = "auto") -> str:
    """Renvoie 'cuda' si demandé ou si auto et GPU disponible, sinon 'cpu'. N'échoue jamais sans torch."""
    if requested in ("cpu", "cuda"):
        return requested
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


@lru_cache
def get_settings() -> Settings:
    return Settings()
