from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Setu API credentials — backend only, NEVER exposed to the frontend.
    # WARNING: Do not prefix these with NEXT_PUBLIC_ or place them in any frontend file.
    SETU_CLIENT_ID: str = ""
    SETU_CLIENT_SECRET: str = ""
    SETU_PRODUCT_INSTANCE_ID: str = ""
    SETU_BASE_URL: str = "https://dg-sandbox.setu.co"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/signflow"

    # CORS — only this origin is allowed to call the backend. Never use wildcard (*).
    FRONTEND_URL: str = "http://localhost:3000"

    # File validation
    MAX_UPLOAD_SIZE_MB: int = 10

    # Environment — controls verbose errors and other env-specific behaviour.
    # Valid values: development | production
    ENVIRONMENT: str = "development"

    # Clerk — backend session verification
    CLERK_SECRET_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
