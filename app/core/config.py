import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Text-to-Video AI API"
    APP_VERSION: str = "1.0.0"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "app" / "model" / "outputs"
    VIEW_DIR: Path = BASE_DIR / "app" / "view"
    
    # HuggingFace & PyTorch
    HF_TOKEN: str | None = None
    PYTORCH_CUDA_ALLOC_CONF: str | None = None
    
    # Hybrid Architecture: Google Colab URL
    COLAB_API_URL: str | None = None
    
    # Database Settings
    DB_URL: str = "mysql+aiomysql://root:@localhost:3306/vax_dev"
    
    # Model Settings
    MODEL_CACHE_DIR: Path = BASE_DIR / "models"
    
    # Default Video Settings
    DEFAULT_WIDTH: int = 320
    DEFAULT_HEIGHT: int = 240
    MAX_QUEUE_SIZE: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure output directory exists
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
