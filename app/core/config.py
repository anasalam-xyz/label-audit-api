from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "LabelAudit API"

    JWT_SECRET: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Fallback extraction path when Gemini's free tier is rate-limited.
    # Optional: leave GROQ_API_KEY unset and the app runs Gemini-only,
    # same as before (a failed Gemini call just raises, as it always did).
    GROQ_API_KEY: str | None = None
    GROQ_VISION_MODEL: str = "qwen/qwen3.6-27b"

    DATABASE_URL: str
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://label-audit.vercel.app",
    ]

    # Object storage for scan photos (Supabase Storage REST API).
    # Create the bucket in your Supabase project and set these in .env —
    # not provided here.
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_BUCKET: str = "scan-photos"


settings = Settings()  # pyright: ignore
