import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Forest Fire Prediction System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

    FIREBASE_CREDENTIALS_PATH: str = "app/core/config/firebase-credentials.json"
    FIREBASE_DATABASE_URL: str = "https://forest-fire-prediction-default-rtdb.firebaseio.com/"
    SQLITE_DB_PATH: str = "app.db"

    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "my-token"
    INFLUXDB_ORG: str = "my-org"
    INFLUXDB_BUCKET: str = "forest_fire_data"

    WEATHER_API_KEY: str = ""
    NASA_API_KEY: str = ""

    EMAIL_SENDER: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_SERVER: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587

    MQTT_BROKER_URL: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_TOPIC_PREFIX: str = "forest_fire"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_STORAGE_BUCKET_NAME: str = "forest-fire-data"
    AWS_REGION: str = "us-east-1"

    MODEL_DIR: str = "app/models/trained"
    DEFAULT_FIRE_RISK_THRESHOLD: float = 0.7

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"sqlite:///{self.SQLITE_DB_PATH}"

settings = Settings()
