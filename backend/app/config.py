from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    db_path: str = "/data/badping.db"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    default_interval: float = 1.0
    default_packet_size: int = 64
    default_retention_days: int = 14

    degraded_loss_pct: float = 5.0
    degraded_window_seconds: int = 300
    offline_loss_seconds: int = 30
    recovery_count: int = 3

    batch_write_interval: float = 1.0
    cleanup_interval: int = 3600

    model_config = {"env_prefix": "BADPING_"}

    @property
    def database_url(self) -> str:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{self.db_path}"


settings = Settings()
