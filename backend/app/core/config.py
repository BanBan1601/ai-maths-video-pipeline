from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    database_url: str
    redis_url: str
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    local_asset_root: str = "/data/assets"
    local_render_root: str = "/data/renders"
    tts_provider: str = "piper"


settings = Settings()
