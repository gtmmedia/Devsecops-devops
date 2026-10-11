"""Application settings, read from environment variables (12-factor style)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "postgresql+psycopg2://quickdesk:quickdesk@localhost:5432/quickdesk"
    # Comma separated list of origins allowed to call the API from a browser.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    # Enables /api/debug/burn, a CPU-burning endpoint used for the HPA demo.
    enable_debug_endpoints: bool = False
    app_version: str = "1.0.0"
    git_sha: str = "dev"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
