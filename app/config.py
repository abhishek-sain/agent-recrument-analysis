from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "mssql+pymssql://sa:password@localhost:1433/user-management"

    FRONTEND_BASE_URL: str = "https://pibspartners.com"
    CORS_ORIGINS: str = "http://localhost:3000"

    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "./uploads"

    S3_BUCKET: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"

    # Public base URL this API is served at (used only to populate the
    # OpenAPI "servers" list, so /docs "Try it out" hits the right host).
    API_PUBLIC_URL: str = "https://pibspartners.com"

    # Tells FastAPI it's being served behind a reverse-proxy path prefix
    # that gets STRIPPED before the request reaches this app. Currently
    # served at the domain root (no path prefix), so this stays blank.
    ROOT_PATH: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
