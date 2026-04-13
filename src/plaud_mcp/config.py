from __future__ import annotations

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    plaud_token: str | None = None
    plaud_token_file: str | None = None
    plaud_device_id: str
    plaud_base_url: str = "https://api.plaud.ai"
    plaud_app_version: str = "5.3.9"

    # Auto-refresh credentials (email/password mode).
    plaud_email: str | None = None
    plaud_password: str | None = None
    plaud_auto_refresh: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def validate_token_source(self) -> "Settings":
        if self.plaud_auto_refresh:
            if not (self.plaud_email and self.plaud_password):
                raise ValueError(
                    "PLAUD_AUTO_REFRESH=true requires PLAUD_EMAIL and PLAUD_PASSWORD"
                )
            if not self.plaud_token_file:
                raise ValueError(
                    "PLAUD_AUTO_REFRESH=true requires PLAUD_TOKEN_FILE "
                    "(where the refreshed token will be persisted)"
                )
            return self

        if not self.plaud_token and not self.plaud_token_file:
            raise ValueError(
                "Either PLAUD_TOKEN, PLAUD_TOKEN_FILE, or PLAUD_AUTO_REFRESH=true must be set"
            )
        return self

    def _read_token_file(self) -> str:
        if not self.plaud_token_file:
            raise RuntimeError("PLAUD_TOKEN_FILE is not configured")

        path = Path(self.plaud_token_file).expanduser()
        try:
            token = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"Failed to read PLAUD_TOKEN_FILE at {path}") from exc

        if not token:
            raise RuntimeError(f"PLAUD_TOKEN_FILE at {path} is empty")

        return token

    def get_token(self) -> str:
        if self.plaud_token_file:
            return self._read_token_file()
        if self.plaud_token:
            return self.plaud_token
        raise RuntimeError("No Plaud token source configured")


settings = Settings()
