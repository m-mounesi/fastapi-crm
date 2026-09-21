from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_EXPIRE_DAYS: int = 7
    ADMIN_USERNAME: str = Field(min_length=1)
    ADMIN_PASSWORD: str = Field(min_length=8)
    CORS_ORIGINS: str = Field(default="http://localhost:3000")
    DATABASE_URL: str = "sqlite:///./database.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    def get_cors_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()  # type: ignore[call-arg]
