from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    google_client_id: str
    google_client_secret: str
    spreadsheet_id: str
    gmail_label: str = "transactions"
    anthropic_api_key: str


settings = Settings()  # type: ignore[call-arg]
