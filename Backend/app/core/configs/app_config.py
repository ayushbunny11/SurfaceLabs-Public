import os
import re
import yaml
from yaml.nodes import ScalarNode
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ReqioIQ"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api"
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()


# Pattern to match ${VAR_NAME} or ${VAR_NAME:default}
ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z0-9_]+)(?::([^}]*))?\}")

def env_constructor(loader: yaml.SafeLoader, node: ScalarNode) -> str:
    """
    Construct a YAML scalar and substitute environment variables.
    Only replaces ${VAR} or ${VAR:default}.
    """
    raw_value = loader.construct_scalar(node)

    def substitute(match: re.Match) -> str:
        var_name, default = match.groups()
        return os.getenv(var_name, default or "")

    # Replace all matches in the scalar
    return ENV_VAR_PATTERN.sub(substitute, raw_value)

# Register our custom tag for SafeLoader
yaml.SafeLoader.add_constructor("!Env", env_constructor)

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