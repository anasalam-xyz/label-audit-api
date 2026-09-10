from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "LabelAudit API"

    JWT_SECRET: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.6-flash"

    DATABASE_URL: str
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://label-audit.vercel.app",
    ]


settings = Settings()  # pyright: ignore
