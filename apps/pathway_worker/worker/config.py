from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class WorkerConfig:
    database_url: str
    streams_dir: str
    static_dir: str
    outputs_dir: str
    poll_interval_ms: int

    def postgres_settings(self) -> dict:
        # Supports SQLAlchemy-style URL: postgresql+psycopg://user:pass@host:port/db
        u = self.database_url.replace("postgresql+psycopg://", "postgresql://")
        p = urlparse(u)
        return {
            "host": p.hostname or "localhost",
            "port": str(p.port or 5432),
            "dbname": (p.path or "/carbon_intel").lstrip("/"),
            "user": p.username or "carbon",
            "password": p.password or "carbon",
        }


def load_config() -> WorkerConfig:
    return WorkerConfig(
        database_url=os.getenv("DATABASE_URL", "postgresql+psycopg://carbon:carbon@postgres:5432/carbon_intel"),
        streams_dir=os.getenv("STREAMS_DIR", "/data/streams"),
        static_dir=os.getenv("STATIC_DIR", "/data/static"),
        outputs_dir=os.getenv("OUTPUTS_DIR", "/data/outputs"),
        poll_interval_ms=int(os.getenv("PATHWAY_POLL_INTERVAL_MS", "1000")),
    )

