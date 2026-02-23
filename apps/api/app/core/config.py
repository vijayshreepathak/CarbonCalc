from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str = "postgresql+psycopg://carbon:carbon@localhost:5432/carbon_intel"
    cors_origins: str = "http://localhost:3000"

    streams_dir: str = "/data/streams"
    static_dir: str = "/data/static"
    outputs_dir: str = "/data/outputs"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()  # type: ignore[call-arg]

