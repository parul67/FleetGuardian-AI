import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, BeforeValidator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated

# Root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_db_url(cls, v):
        if isinstance(v, str) and "$" in v:
            import re
            def replace_env(match):
                var_name = match.group(1) or match.group(2)
                return os.getenv(var_name, "")
            v = re.sub(r"\$\{(\w+)\}|\$(\w+)", replace_env, v)
        return v

    PROJECT_NAME: str = "FleetGuardian AI"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "fleetguardian-super-secure-secret-key-for-jwt-token-auth"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    GOOGLE_CLIENT_ID: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite:///./fleetguardian.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CV & ML Directories
    DATASET_DIR: str = str(ROOT_DIR / "datasets")
    MODEL_DIR: str = str(ROOT_DIR / "models")
    LOG_DIR: str = str(ROOT_DIR / "logs")

    # CV & ML Model Paths
    PHONE_MODEL_PATH: str = "yolo11n.pt"
    SEATBELT_MODEL_PATH: str = "yolo11n.pt"
    FACE_LANDMARKER_PATH: str = "face_landmarker.task"
    ACCIDENT_MODEL_PATH: str = "models/risk_predictor.pkl"
    
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def create_dirs(self):
        """Creates output folders if they do not exist."""
        for d in [self.DATASET_DIR, self.MODEL_DIR, self.LOG_DIR]:
            os.makedirs(d, exist_ok=True)

    @property
    def ROOT_DIR(self) -> Path:
        return ROOT_DIR

settings = Settings()
settings.create_dirs()
