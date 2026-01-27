import os
import re
import yaml
from yaml.nodes import ScalarNode
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "SurfaceLabs"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api"
    ALLOWED_ORIGINS: list[str] = ["*"]
    
    GOOGLE_API_KEY: str = ""
    ANALYSIS_MODEL: str = ""
    FLASH_MODEL: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

def load_yaml_config(file_path: str) -> dict:
    """
    Load a YAML config file and resolve !Env tags safely.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


BASE_DIR = Path(__file__).resolve().parents[3]

system_config_path = str(BASE_DIR / "app" / "core" / "configs" / "system_config.yaml")
prompt_config_path = str(BASE_DIR / "app" / "core" / "configs" / "prompts_config.yaml")
query_config_path = str(BASE_DIR / "app" / "core" / "configs" / "query_config.yaml")
helper_config_path = str(BASE_DIR / "app" / "core" / "configs" / "helper_config.yaml")

system_config = load_yaml_config(system_config_path)
prompt_config = load_yaml_config(prompt_config_path)
query_config = load_yaml_config(query_config_path)
helper_config = load_yaml_config(helper_config_path)


REPO_STORAGE = BASE_DIR / "app" / "storage" / "repos"
REPO_STORAGE.mkdir(parents=True, exist_ok=True)

INDEX_STORAGE_DIR = BASE_DIR / "app" / "storage" / "faiss_index"
INDEX_STORAGE_DIR.mkdir(parents=True, exist_ok=True)